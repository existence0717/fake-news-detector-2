import sqlite3

def view_data():
    conn = sqlite3.connect('fake_news.db')
    cursor = conn.cursor()
    
    # Get the last 5 things saved
    cursor.execute("SELECT * FROM content_log ORDER BY id DESC LIMIT 5")
    rows = cursor.fetchall()
    
    print(f"\n--- 📂 DATABASE CONTENTS ({len(rows)} recent items) ---")
    
    if not rows:
        print("Database is empty! (Wait for the bot to find news...)")
    
    for row in rows:
        # row structure depends on your DB, but usually:
        # id, platform, title, url, views, tags, panic_score...
        print(f"\nID: {row[0]} | Platform: {row[1]}")
        print(f"Title: {row[2]}")
        print(f"Verdict: {row[9]}") # Assuming verdict is the 10th column
        print("-" * 30)

    conn.close()

if __name__ == "__main__":
    view_data()
