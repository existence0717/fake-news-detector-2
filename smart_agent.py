import requests
import json
import time

# --- 🔑 CONFIGURATION ---
GEMINI_API_KEY = "AIzaSyC59_IhLRb0JwSOTQk_8wDCNHGUzYi9e2M" # <--- PASTE KEY AGAIN

# Using the model we found works for you
MODEL_NAME = "gemini-2.0-flash" 
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"

class AiFactChecker:
    def __init__(self):
        print(f" 🧠 Gemini AI Agent ({MODEL_NAME}) Initialized.")

    def fact_check(self, text):
        if not text: return {"risk": 0.0, "verdict": "UNKNOWN", "reason": "No text"}

        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""
                    Analyze this news headline: "{text}"
                    1. Is it Likely True, Fake, or Misleading?
                    2. Risk Score (0.0 to 1.0).
                    3. One sentence explanation.
                    
                    Format your answer exactly like this:
                    SCORE: 0.9
                    VERDICT: FAKE
                    REASON: This is a known hoax.
                    """
                }]
            }]
        }

        # --- RETRY LOGIC (The Anti-Crash System) ---
        try:
            response = requests.post(URL, headers={'Content-Type': 'application/json'}, json=payload)
            
            # 🛑 TRAP: If Error 429 (Quota Exceeded)
            if response.status_code == 429:
                print(f"   🛑 TOO FAST! Google says wait. Sleeping 60 seconds...")
                time.sleep(60) # Force system pause
                return {"risk": 0.5, "verdict": "ERROR", "reason": "Quota Limit Hit - Cooling Down"}

            # Check for other errors
            if response.status_code != 200:
                print(f" ⚠️ API Error {response.status_code}: {response.text}")
                return {"risk": 0.5, "verdict": "ERROR", "reason": "API Error"}

            data = response.json()
            
            # Handle empty responses
            if 'candidates' not in data or not data['candidates']:
                return {"risk": 0.0, "verdict": "UNKNOWN", "reason": "AI Safety Filter triggered"}

            ai_text = data['candidates'][0]['content']['parts'][0]['text']
            
            # Extract logic
            risk = 0.5
            verdict = "UNVERIFIED"
            reason = "AI processing..."
            
            for line in ai_text.split('\n'):
                if "SCORE:" in line: 
                    try: risk = float(line.split(":")[1].strip())
                    except: pass
                if "VERDICT:" in line: verdict = line.split(":")[1].strip()
                if "REASON:" in line: reason = line.split(":")[1].strip()
            
            return {"risk": risk, "verdict": verdict, "reason": reason}

        except Exception as e:
            print(f" ⚠️ Connection Error: {e}")
            return {"risk": 0.5, "verdict": "ERROR", "reason": "Connection Failed"}
