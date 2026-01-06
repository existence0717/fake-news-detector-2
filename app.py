import streamlit as st
import sqlite3
from textblob import TextBlob
from forensics import scan_image_for_editing

# --- APP CONFIGURATION ---
st.set_page_config(page_title="AI Misinformation Guard", page_icon="🛡️")

st.title("🛡️ AI Fake News & Deepfake Detector")
st.write("Scan news for panic triggers, deepfakes, and source credibility.")

# --- DATABASE HELPER ---
def get_source_credibility(domain):
    conn = sqlite3.connect('fake_news.db')
    cursor = conn.cursor()
    cursor.execute("SELECT credibility_score FROM sources WHERE domain=?", (domain,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0]
    else:
        return 0.5 # Default if we don't know the source

# --- USER INPUTS ---
col1, col2 = st.columns(2)
with col1:
    source = st.selectbox("Select Source:", ["bbc.com", "random-whatsapp-forward", "cnn.com", "unknown-blog"])
with col2:
    image_url = st.text_input("Paste Image URL (optional):")

news_text = st.text_area("Paste News Headline here:", height=100)

# --- THE BRAIN ---
if st.button("🚀 Analyze Content"):
    if not news_text:
        st.warning("Please enter some text first.")
    else:
        # 1. Text Analysis
        blob = TextBlob(news_text)
        panic_score = 0.0
        keywords = ["blast", "explosion", "terrorist", "attack", "urgent", "forward"]
        word_hits = sum(1 for w in keywords if w in news_text.lower())
        
        if word_hits > 0:
            panic_score = 0.6 + (word_hits * 0.1)
        if blob.sentiment.polarity < -0.2:
            panic_score += 0.2
        panic_score = min(panic_score, 1.0)

        # 2. Image Analysis
        fake_prob = 0.0
        if image_url:
            with st.spinner("Scanning image metadata..."):
                fake_prob = scan_image_for_editing(image_url)
        
        # 3. Source Analysis (New!)
        credibility = get_source_credibility(source)
        source_risk = 1.0 - credibility # Low trust = High risk

        # 4. Final Calculation
        # Weights: Source (30%), Panic (30%), Deepfake (40%)
        final_risk = (source_risk * 0.3) + (panic_score * 0.3) + (fake_prob * 0.4)

        # --- DISPLAY RESULTS ---
        st.divider()
        c1, c2, c3 = st.columns(3)
        c1.metric("Panic Level", f"{panic_score*100:.0f}%")
        c2.metric("Visual Manipulation", f"{fake_prob*100:.0f}%")
        c3.metric("Source Trust", f"{credibility*100:.0f}%")
        
        st.subheader(f"Overall Risk Score: {final_risk*100:.0f}%")
        
        if final_risk > 0.7:
            st.error("❌ VERDICT: HIGH RISK / FAKE CONTENT")
        elif final_risk > 0.4:
            st.warning("⚠️ VERDICT: UNVERIFIED / CAUTION")
        else:
            st.success("✅ VERDICT: LIKELY CREDIBLE")
