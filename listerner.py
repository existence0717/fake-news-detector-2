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

# --- 🔑 CONFIGURATION ---
NEWS_API_KEY = "news" 
YOUTUBE_API_KEY = "yt"
GROQ_API_KEY = "groq"

MODEL_NAME = "llama-3.3-70b-versatile"

# 🌍 GOOGLE SEARCH TRENDS (India)
TRENDS_RSS_URL = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"

# 💻 HACKER NEWS API
HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

RISK_KEYWORDS = [
    "huge", "fake", "political", "blast", "explosion", "arrest",
    "scam", "urgent", "virus", "riot", "protest", "deepfake", "AI generated",
    "leaked", "scandal", "exposed", "hack", "cyber", "war", "market crash"
]

class SocialListener:
    def __init__(self):
        print(f" 🧠 INITIALIZING: Advanced Classification Engine ({MODEL_NAME})...")
        self.client = Groq(api_key=GROQ_API_KEY)
        self.db_name = 'fake_news.db'
        self.init_db()
        self.youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    def init_db(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT,
                title TEXT,
                url TEXT,
                image_url TEXT,
                views INTEGER,
                tags TEXT,
                panic_score REAL,
                verdict TEXT,
                virality_vd REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def ask_ai(self, text):
        try:
            # --- 🧠 THE NEW "STRICT" BRAIN ---
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
                temperature=0.3 # Slightly higher creativity to catch nuances
            )
            data = json.loads(completion.choices[0].message.content)
            return {"verdict": data.get("category", "UNVERIFIED").upper(), "risk": data.get("score", 0)/100}
        except: return {"verdict": "ERROR", "risk": 0}

    def save_to_db(self, data):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM content_log WHERE url=?", (data['url'],))
            if cursor.fetchone(): return

            cursor.execute('''
                INSERT INTO content_log (platform, title, url, image_url, views, tags, panic_score, verdict, virality_vd) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data['platform'], data['title'], data['url'], data.get('image_url'), data['views'], data['tags'], data['risk'], data['verdict'], data['vd']))
            conn.commit()
            # Print the NEW diverse verdicts in the terminal
            print(f"   💾 SAVED [{data['verdict']}]: {data['title'][:30]}...")
        except Exception as e: print(f"DB Error: {e}")
        finally: conn.close()

    def process_item(self, platform, title, url, views, tag, image_url, vd_score):
        analysis = self.ask_ai(title)
        if "IRRELEVANT" in analysis['verdict']: return
        self.save_to_db({
            "platform": platform, "title": title, "url": url, "image_url": image_url,
            "views": views, "tags": tag, "risk": analysis['risk'], "verdict": analysis['verdict'],
            "vd": vd_score
        })
        time.sleep(1)

    # --- 📈 GOOGLE TRENDS SCANNER ---
    def scan_google_trends(self):
        print(f"\n 📈 Google Trends Scan (India)...")
        try:
            feed = feedparser.parse(TRENDS_RSS_URL)
            for entry in feed.entries[:3]:
                traffic = int(getattr(entry, 'ht_approx_traffic', '10000').replace(',', '').replace('+', ''))
                vd = traffic / 24.0
                img = None
                if 'ht_picture' in entry: img = entry.ht_picture
                self.process_item("Google Trends", entry.title, entry.link, traffic, "viral-trend", img, vd)
        except Exception as e: print(f"Trends Error: {e}")

    # --- 💻 HACKER NEWS SCANNER ---
    def scan_hacker_news(self):
        print(f"\n 💻 Hacker News Scan...")
        try:
            top_ids = requests.get(HN_TOP_STORIES).json()[:5]
            for item_id in top_ids:
                item = requests.get(HN_ITEM_URL.format(item_id)).json()
                if not item or 'title' not in item: continue
                title = item['title']
                # Broader keywords to catch more tech scams/AI news
                if any(k in title.lower() for k in RISK_KEYWORDS + ['ai', 'gpt', 'crypto', 'attack', 'bug', 'data', 'leak']):
                    reach = (item.get('score', 0) * 100)
                    self.process_item("Hacker News", title, item.get('url', 'https://news.ycombinator.com'), reach, "tech", None, reach/10)
        except Exception as e: print(f"HN Error: {e}")

    # --- 🌍 GOOGLE NEWS RSS SCANNER ---
    def scan_google_rss(self, tag):
        print(f"\n 📰 Google News Scan: '{tag}'...")
        rss_url = f"https://news.google.com/rss/search?q={tag}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries[:2]:
                self.process_item("Google News", entry.title, entry.link, 50000, tag, None, 5000)
        except: pass

    # --- 📺 YOUTUBE SCANNER ---
    def search_youtube_free(self, query, limit=5):
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(f"https://www.youtube.com/results?search_query={query}", headers=headers)
            video_ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', response.text)
            return list(set(video_ids))[:limit]
        except: return []

    def scan_youtube(self, tag):
        print(f"\n 📺 YouTube Scan: '{tag}'...")
        ids = self.search_youtube_free(f"{tag} -gaming", limit=5)
        if not ids: return

        try:
            stats = self.youtube.videos().list(id=','.join(ids), part='statistics,snippet').execute()
            for item in stats.get('items', []):
                R = int(item['statistics'].get('viewCount', 0))
                upload_time = datetime.fromisoformat(item['snippet']['publishedAt'].replace('Z', '+00:00'))
                T = (datetime.now(timezone.utc) - upload_time).total_seconds() / 3600
                T = max(T, 0.1)
                Vd = R / T

                if Vd > 100 or R > 50000:
                    img = item['snippet']['thumbnails']['medium']['url']
                    self.process_item("YouTube", item['snippet']['title'], f"https://youtu.be/{item['id']}", R, tag, img, Vd)
        except Exception as e: print(f"YT Error: {e}")

if __name__ == "__main__":
    bot = SocialListener()
    while True:
        tag = random.choice(RISK_KEYWORDS)
        bot.scan_google_trends()
        bot.scan_hacker_news()
        bot.scan_google_rss(tag)
        bot.scan_youtube(tag)
        print("\n 💤 Resting...")
        time.sleep(10)
