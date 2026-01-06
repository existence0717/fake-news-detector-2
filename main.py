import sqlite3
from textblob import TextBlob
from forensics import scan_image_for_editing
# --- CONFIGURATION ---
# These are the "trigger words" the AI looks for
HIGH_RISK_KEYWORDS = ["blast", "explosion", "terrorist", "attack", "death", "urgent", "forward"]

class FakeNewsDetector:
    def __init__(self):
        self.db_name = 'fake_news.db'

    def analyze_text(self, text):
        """Checks for panic-inducing words and negative sentiment."""
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity # -1.0 (Negative) to 1.0 (Positive)
        
        # Count how many scary words are in the text
        keyword_hits = sum(1 for word in HIGH_RISK_KEYWORDS if word in text.lower())
        
        # Logic: High panic if sentiment is negative AND keywords are present
        panic_score = 0.0
        if keyword_hits > 0:
            panic_score = 0.5 + (keyword_hits * 0.1)
        
        # Adjust based on sentiment (scary news usually has negative sentiment)
        if sentiment < -0.2:
            panic_score += 0.2

        return min(panic_score, 1.0) # Cap score at 1.0

    def analyze_media(self, media_url):
        """
        Connects to the Forensics Module to scan for Photoshop/Editing traces.
        """
        if not media_url:
            return 0.0
        
        # Call our new forensics tool
        suspicion_score = scan_image_for_editing(media_url)
        return suspicion_score

    def get_source_credibility(self, domain):
        """Fetches the trust score of the website/source from our DB."""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        # Check if we know this source
        cursor.execute("SELECT credibility_score FROM sources WHERE domain=?", (domain,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            return 0.5 # Default neutral score if unknown

    def process_content(self, text, media_url, source_domain):
        print(f"\n--- Analyzing: {text[:40]}... ---")
        
        # 1. Run Analysis
        panic_score = self.analyze_text(text)
        deepfake_score = self.analyze_media(media_url)
        credibility = self.get_source_credibility(source_domain)
        
        # 2. Calculate Risk (The Formula)
        # We trust credible sources (1-credibility) reduces risk
        # We fear panic and deepfakes
        source_risk = 1.0 - credibility
        
        final_risk = (panic_score * 0.3) + (deepfake_score * 0.4) + (source_risk * 0.3)
        
        # 3. Determine Verdict
        if final_risk > 0.7:
            verdict = "❌ FAKE / DANGEROUS"
        elif final_risk > 0.4:
            verdict = "⚠️ UNVERIFIED"
        else:
            verdict = "✅ LIKELY TRUE"
            
        print(f"Results -> Panic: {panic_score:.2f} | Deepfake Risk: {deepfake_score:.2f} | Source Trust: {credibility}")
        print(f"FINAL VERDICT: {verdict}")
        
        # 4. Save to Database
        self.save_log(text, media_url, final_risk, verdict)

    def save_log(self, text, media, risk, verdict):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO content_log (text_content, media_url, risk_score, verdict) VALUES (?, ?, ?, ?)", 
                       (text, media, risk, verdict))
        conn.commit()
        conn.close()
        print(" > Logged to Database.")

# # --- SIMULATION ---
if __name__ == "__main__":
    system = FakeNewsDetector()
    print("Running AI Forensics Simulation...\n")

    # TEST: A fake message with a real image we want to scan
    system.process_content(
        text="URGENT!! Terrorist attack in market. Forward to everyone!!",
        # This is a sample image that exists online
        media_url="https://upload.wikimedia.org/wikipedia/commons/3/3a/Cat03.jpg", 
        source_domain="random-whatsapp-forward"
    )
