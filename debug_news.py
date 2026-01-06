import requests

# Paste your API Key here
NEWS_API_KEY = "b7a8d9e792a449af8fcc60438a850864" 

def check_news():
    print("--- 🕵️ DEBUGGING NEWS API ---")
    
    # 1. Try fetching Top Headlines for India
    url = f"https://newsapi.org/v2/top-headlines?country=in&category=general&apiKey={NEWS_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"API Status: {data.get('status')}")
        
        if data.get('status') == 'error':
            print(f"❌ ERROR MESSAGE: {data.get('message')}")
        else:
            article_count = data.get('totalResults', 0)
            print(f"✅ Total Articles Found: {article_count}")
            
            if article_count == 0:
                print("⚠️ The API returned 0 articles. This is why your DB is empty!")
            else:
                print("First Article Title:", data['articles'][0]['title'])

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    check_news()
