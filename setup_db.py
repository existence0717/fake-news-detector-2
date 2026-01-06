import sqlite3

def create_database():
    # This connects to a file. If it doesn't exist, it creates it automatically.
    conn = sqlite3.connect('fake_news.db')
    cursor = conn.cursor()

    print("Creating Database...")

    # 1. Table for Sources
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sources (
        source_id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT UNIQUE,
        credibility_score REAL
    )
    ''')

    # 2. Table for Content Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS content_log (
        content_id INTEGER PRIMARY KEY AUTOINCREMENT,
        text_content TEXT,
        media_url TEXT,
        risk_score REAL,
        verdict TEXT
    )
    ''')

    # Let's add some dummy data to test with
    try:
        cursor.execute("INSERT INTO sources (domain, credibility_score) VALUES ('bbc.com', 0.95)")
        cursor.execute("INSERT INTO sources (domain, credibility_score) VALUES ('random-whatsapp-forward', 0.10)")
        print("Dummy data added!")
    except:
        print("Data already exists.")

    conn.commit()
    conn.close()
    print("Database 'fake_news.db' is ready!")

if __name__ == "__main__":
    create_database()