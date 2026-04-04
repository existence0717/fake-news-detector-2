"""
I2C3 Configuration - Centralize all settings, keywords, and thresholds
Edit this file to tune the system without touching core logic.
"""

import os
from dotenv import load_dotenv

load_dotenv("keys.env")

# --- API KEYS (from env) ---
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_FACTCHECK_API_KEY = os.getenv("GOOGLE_FACTCHECK_API_KEY")

# --- AI ---
MODEL_NAME = "llama-3.1-8b-instant"

# --- FEEDS ---
TRENDS_RSS_URL = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=IN"

RSS_FEEDS = {
    "Times of India": "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "The Hindu": "https://www.thehindu.com/news/national/feeder/default.rss",
    "NDTV": "https://feeds.feedburner.com/ndtvnews-top-stories",
    "India Today": "https://www.indiatoday.in/rss/1206514",
}

HN_TOP_STORIES = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

# News API query terms (India-focused)
NEWS_API_QUERIES = [
    "India fake news",
    "India deepfake",
    "India scam",
    "India breaking news",
]

# --- RISK KEYWORDS (per PRD) ---
RISK_KEYWORDS = [
    "huge", "fake", "political", "blast", "burst", "explosion", "death", "evacuate",
    "terrorist", "attack", "flood", "earthquake", "fire", "shootout", "accident", "crime",
    "scam", "urgent", "virus", "riot", "protest", "deepfake", "AI generated",
    "leaked", "scandal", "exposed", "hack", "cyber", "war", "market crash",
]
# --- HINDI RISK KEYWORDS ---
HINDI_RISK_KEYWORDS = [
    # Fake/Scam
    "फर्जी",  # Fake
    "नकली",  # Fake/counterfeit
    "घोटाला",  # Scam
    "धोखाधड़ी",  # Fraud
    
    # Violence/Danger
    "धमाका",  # Blast/explosion
    "विस्फोट",  # Explosion
    "मौत",  # Death
    "मृत्यु",  # Death (formal)
    "हमला",  # Attack
    "आतंकी",  # Terrorist
    "आतंकवाद",  # Terrorism
    
    # Disaster
    "आग",  # Fire
    "बाढ़",  # Flood
    "भूकंप",  # Earthquake
    "दंगा",  # Riot
    
    # Urgent/Breaking
    "तत्काल",  # Urgent
    "जरूरी",  # Important/urgent
    "ब्रेकिंग",  # Breaking (borrowed)
    "अलर्ट",  # Alert (borrowed)
    
    # Political
    "भ्रष्ट",  # Corrupt
    "देशद्रोही",  # Traitor
    "साजिश",  # Conspiracy
]

# Combined keywords for comprehensive detection
ALL_RISK_KEYWORDS = RISK_KEYWORDS + HINDI_RISK_KEYWORDS
# Keywords to check for HN/tech (broader)
TECH_RISK_KEYWORDS = RISK_KEYWORDS + ["ai", "gpt", "crypto", "attack", "bug", "data", "leak"]

# --- VIRALITY / SPIKE THRESHOLDS ---
# Views per hour above this = "spike" (high priority)
SPIKE_VD_THRESHOLD = 5000
# Total views above this = viral
SPIKE_VIEWS_THRESHOLD = 100_000
# SpikeTracker: baseline = avg items/hour over last N hours
SPIKE_BASELINE_HOURS = 24
# True spike = recent rate > (baseline * this multiplier)
SPIKE_MULTIPLIER = 2.0
# Min items required before baseline is considered meaningful
SPIKE_MIN_BASELINE_ITEMS = 3
# YouTube: process if views/hr > this OR total views > 50k
YOUTUBE_VD_MIN = 100
YOUTUBE_VIEWS_MIN = 50_000

# --- SOURCE POPULARITY (for RSS view estimates) ---
RSS_VIEW_ESTIMATES = {
    "Times of India": 100_000,
    "The Hindu": 80_000,
    "NDTV": 90_000,
    "India Today": 85_000,
}

# --- LISTENER ---
SCAN_INTERVAL_SECONDS = 20
NEWS_API_ARTICLE_LIMIT = 5
RSS_ENTRIES_PER_FEED = 3
YOUTUBE_SEARCH_LIMIT = 5
