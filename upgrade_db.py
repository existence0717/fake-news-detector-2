import sqlite3

def upgrade_database():
    conn = sqlite3.connect('fake_news.db')
    cursor = conn.cursor()
    
    print(" 🛠️ Upgrading Database Schema...")

    # 1. Drop the old table (We are rebuilding it better)
    cursor.execute('DROP TABLE IF EXISTS content_log')
    
    # 2. Create the NEW, Advanced Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,          -- "YouTube", "NewsAPI"
        title TEXT,             -- The headline or video title
        url TEXT UNIQUE,        -- Link (Unique so we don't scan twice)
        views INTEGER,          -- "100,000" views (Engagement)
        tags TEXT,              -- "politics, urgent, blast"
        panic_score REAL,       -- AI Score (0.0 - 1.0)
        deepfake_score REAL,    -- AI Score (0.0 - 1.0)
        final_risk REAL,        -- Final Risk Score
        verdict TEXT,           -- "FAKE", "REAL"
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    print(" ✅ Database Upgraded! Ready for Automation.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    upgrade_database()
