import sqlite3
import time
import random
import requests
import re
import json
import feedparser
from datetime import datetime, timezone
from groq import Groq
from googleapiclient.discovery import build

from utils import setup_logging
from risk_scoring import RiskScorer
from config import (
    NEWS_API_KEY, YOUTUBE_API_KEY, GROQ_API_KEY,
    MODEL_NAME, TRENDS_RSS_URL, RSS_FEEDS, RSS_VIEW_ESTIMATES,
    HN_TOP_STORIES, HN_ITEM_URL, NEWS_API_QUERIES,
    RISK_KEYWORDS, TECH_RISK_KEYWORDS,
    SPIKE_VD_THRESHOLD, SPIKE_VIEWS_THRESHOLD, YOUTUBE_VD_MIN, YOUTUBE_VIEWS_MIN,
    NEWS_API_ARTICLE_LIMIT, RSS_ENTRIES_PER_FEED, YOUTUBE_SEARCH_LIMIT,
    SCAN_INTERVAL_SECONDS,
)

# Validate API keys
print("Loading API keys...")
print(f"   News API Key: {'Found' if NEWS_API_KEY else 'Missing'}")
print(f"   YouTube API Key: {'Found' if YOUTUBE_API_KEY else 'Missing'}")
print(f"   Groq API Key: {'Found' if GROQ_API_KEY else 'Missing'}")

if not all([YOUTUBE_API_KEY, GROQ_API_KEY]):
    print("\n ERROR: YouTube and Groq keys required. Check keys.env")
    exit(1)
print("Keys OK\n")

class SocialListener:
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info(f" INITIALIZING: Advanced Classification Engine ({MODEL_NAME})")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.risk_scorer = RiskScorer()
        self.db_name = 'fake_news.db'
        self.init_db()
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def init_db(self):
        conn = sqlite3.connect(self.db_name, timeout=10)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=5000')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                title TEXT,
                url TEXT UNIQUE,
                image_url TEXT,
                views INTEGER,
                tags TEXT,
                panic_score REAL,
                verdict TEXT,
                virality_vd REAL,
                ai_explanation TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Add ai_explanation column if DB existed before
        try:
            cursor.execute("ALTER TABLE content_log ADD COLUMN ai_explanation TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
        conn.close()

    def ask_ai(self, text):
        try:
            system_prompt = """
            Analyze the headline and classify it into ONE of these categories. 
            Be specific. Do not just say "Clickbait" if it is actually a Scam or Political.

            CATEGORIES & RULES:
            1. DEEPFAKE: Mentions "leaked audio", "AI video", or impossible behavior by public figures.
            2. SCAM: Mentions "free money", "crypto giveaway", "urgent investment", or "hack trick".
            3. POLITICAL BIAS: Highly opinionated, attacking a party, or using charged words like "destroy", "traitor".
            4. MISLEADING: Factually doubtful, missing context, or cherry-picked facts.
            5. CLICKBAIT: Exaggerated ("You won't believe", "Shocking") but harmless.
            6. SATIRE: clearly a joke or meme.
            7. LIKELY REAL: Neutral news reporting (e.g., "Sensex down 200 points").

            Output strictly valid JSON:
            {"score": 0-100, "category": "CATEGORY_NAME", "reason": "short explanation"}
            (Score 100 = Dangerous/Fake, Score 0 = Safe/Real)
            """
            
            completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": f"Classify this: '{text}'"}
                ],
                model=MODEL_NAME, 
                response_format={"type": "json_object"}, 
                temperature=0.1
            )
            data = json.loads(completion.choices[0].message.content)
            return {
                "verdict": data.get("category", "UNVERIFIED").upper(),
                "risk": data.get("score", 0) / 100,
                "reason": data.get("reason", "No explanation")[:500]
            }
        except Exception as e:
            self.logger.error(f"AI ERROR: {e}", exc_info=True)
            return {"verdict": "ERROR", "risk": 0, "reason": str(e)[:200]}

    def save_to_db(self, data):
        conn = sqlite3.connect(self.db_name, timeout=10)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM content_log WHERE url=?", (data['url'],))
            if cursor.fetchone(): 
                return

            cursor.execute('''
                INSERT INTO content_log (platform, title, url, image_url, views, tags, panic_score, verdict, virality_vd, ai_explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['platform'], data['title'], data['url'], data.get('image_url'), data['views'], data['tags'], data['risk'], data['verdict'], data['vd'], data.get('ai_explanation', '')))
            conn.commit()
            self.logger.info(f"SAVED [{data['verdict']}]: {data['title'][:30]}...")
        except Exception as e:
            self.logger.error(f"DB Error: {e}", exc_info=True)
        finally: 
            conn.close()

    def is_spike(self, views, vd_score):
        """Detect spike: high velocity or high total views (per PRD)"""
        return vd_score >= SPIKE_VD_THRESHOLD or views >= SPIKE_VIEWS_THRESHOLD

    def process_item(self, platform, title, url, views, tag, image_url, vd_score):
        analysis = self.ask_ai(title)
        if "IRRELEVANT" in analysis.get("verdict", ""): 
            return
        
        risk_analysis = self.risk_scorer.calculate_composite_risk(
            title=title,
            platform=platform,
            url=url,
            views=views,
            virality_vd=vd_score,
            tags=tag,
            ai_score=analysis['risk']
        )
        composite = risk_analysis['composite_risk']
        if composite > 0.7:
            self.logger.warning(f"HIGH RISK: {title[:50]} (Risk: {composite:.2f})")
        if self.is_spike(views, vd_score):
            self.logger.info(f"SPIKE DETECTED: vd={vd_score:.0f}, views={views} | {title[:40]}...")
    
        self.save_to_db({
            "platform": platform, 
            "title": title, 
            "url": url, 
            "image_url": image_url,
            "views": views, 
            "tags": tag, 
            "risk": composite, 
            "verdict": analysis['verdict'],
            "vd": vd_score,
            "ai_explanation": analysis.get("reason", "")
        })
        time.sleep(1)
    

    def scan_google_trends(self):
        self.logger.info("Google Trends Scan (India)")
        try:
            feed = feedparser.parse(TRENDS_RSS_URL)
            for entry in feed.entries[:3]:
                traffic = int(getattr(entry, 'ht_approx_traffic', '10000').replace(',', '').replace('+', ''))
                vd = traffic / 24.0
                img = None
                if 'ht_picture' in entry: 
                    img = entry.ht_picture
                self.process_item("Google Trends", entry.title, entry.link, traffic, "viral-trend", img, vd)
        except Exception as e: 
            self.logger.error(f"Trends Error: {e}")

    def scan_hacker_news(self):
        self.logger.info("Hacker News Scan")
        try:
            top_ids = requests.get(HN_TOP_STORIES).json()[:5]
            for item_id in top_ids:
                item = requests.get(HN_ITEM_URL.format(item_id)).json()
                if not item or 'title' not in item: 
                    continue
                title = item['title']
                if any(k in title.lower() for k in TECH_RISK_KEYWORDS):
                    reach = (item.get('score', 0) * 100)
                    self.process_item("Hacker News", title, item.get('url', 'https://news.ycombinator.com'), reach, "tech", None, reach/10)
        except Exception as e: 
            self.logger.error(f"HN Error: {e}")

    def scan_google_rss(self, tag):
        self.logger.info(f" Google News Scan: '{tag}'")
        rss_url = f"https://news.google.com/rss/search?q={tag}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:
                self.process_item("Google News", entry.title, entry.link, 50000, tag, None, 5000)
        except Exception as e:
            self.logger.error(f"Google RSS Error: {e}")

    def scan_rss_feeds(self):
        for source_name, feed_url in RSS_FEEDS.items():
            self.logger.info(f"RSS Feed Scan: {source_name}")
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:RSS_ENTRIES_PER_FEED]:
                    title = entry.title
                    url = entry.link
                    views = RSS_VIEW_ESTIMATES.get(source_name, 50000)
                    self.process_item(
                        platform=source_name,
                        title=title,
                        url=url,
                        views=views,
                        tag='news',
                        image_url=None,
                        vd_score=views / 12
                    )
                    
            except Exception as e:
                self.logger.error(f"RSS Error ({source_name}): {e}")

    def search_youtube_free(self, query, limit=None):
        limit = limit or YOUTUBE_SEARCH_LIMIT
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(f"https://www.youtube.com/results?search_query={query}", headers=headers)
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
            return list(set(video_ids))[:limit]
        except: 
            return []

    def scan_youtube(self, tag):
        self.logger.info(f" YouTube Scan: '{tag}'")
        ids = self.search_youtube_free(f"{tag} -gaming")
        if not ids: 
            return

        try:
            stats = self.youtube.videos().list(id=','.join(ids), part='statistics,snippet').execute()
            for item in stats.get('items', []):
                R = int(item['statistics'].get('viewCount', 0))
                upload_time = datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                T = (datetime.now(timezone.utc) - upload_time).total_seconds() / 3600
                T = max(T, 0.1)
                Vd = R / T

                if Vd > YOUTUBE_VD_MIN or R > YOUTUBE_VIEWS_MIN:
                    img = item['snippet']['thumbnails']['medium']['url']
                    self.process_item("YouTube", item['snippet']['title'], f"https://youtu.be/{item['id']}", R, tag, img, Vd)
        except Exception as e: 
            self.logger.error(f"YT Error: {e}")

    def scan_news_api(self):
        """NewsAPI.org - verified + diverse news sources (India focus)"""
        if not NEWS_API_KEY:
            return
        self.logger.info("News API Scan")
        for query in NEWS_API_QUERIES[:2]:
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    "q": query,
                    "apiKey": NEWS_API_KEY,
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": min(NEWS_API_ARTICLE_LIMIT, 5),
                }
                resp = requests.get(url, params=params, timeout=10)
                data = resp.json()
                if data.get("status") != "ok":
                    self.logger.warning(f"News API: {data.get('message', 'Unknown error')}")
                    continue
                for art in data.get("articles", [])[:NEWS_API_ARTICLE_LIMIT]:
                    title = art.get("title") or ""
                    url_link = art.get("url") or ""
                    if not title or not url_link:
                        continue
                    # Rough virality: newer = higher vd
                    views = 50000
                    vd = 5000
                    self.process_item(
                        platform="News API",
                        title=title,
                        url=url_link,
                        views=views,
                        tag=query.replace(" ", "-")[:20],
                        image_url=art.get("urlToImage"),
                        vd_score=vd
                    )
            except Exception as e:
                self.logger.error(f"News API Error: {e}")

if __name__ == "__main__":
    bot = SocialListener()
    while True:
        tag = random.choice(RISK_KEYWORDS)
        bot.scan_google_trends()
        bot.scan_hacker_news()
        bot.scan_google_rss(tag)
        bot.scan_youtube(tag)
        bot.scan_rss_feeds()
        bot.scan_news_api()
        bot.logger.info(f" Resting for {SCAN_INTERVAL_SECONDS}s...")
        time.sleep(SCAN_INTERVAL_SECONDS)  
