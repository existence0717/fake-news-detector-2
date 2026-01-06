import requests

# PASTE YOUR KEY HERE
API_KEY = "AIzaSyC59_IhLRb0JwSOTQk_8wDCNHGUzYi9e2M"

def list_models():
    print(" 🔍 Checking available Google AI Models...")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Error: {response.text}")
            return

        data = response.json()
        print("\n✅ You have access to these models:")
        for model in data.get('models', []):
            if 'generateContent' in model['supportedGenerationMethods']:
                print(f" - {model['name']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_models()
