from PIL import Image, ExifTags
import requests
from io import BytesIO

def scan_image_for_editing(image_url):
    if not image_url:
        return 0.0

    print(f" > 🔍 Downloading image from {image_url}...")
    
    try:
        # --- THE FIX IS HERE ---
        # We add 'headers' to pretend to be a web browser (Mozilla/Chrome)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(image_url, headers=headers, timeout=10)
        
        # Check if the website actually gave us an image (Status Code 200)
        if response.status_code != 200:
            print(f" > ❌ Download failed. Status Code: {response.status_code}")
            return 0.0

        image = Image.open(BytesIO(response.content))
        
        # Check for hidden data
        exif_data = image._getexif()
        if not exif_data:
            print(" > No metadata found.")
            return 0.3 

        # Look for editing tools
        exif_string = str(exif_data)
        suspicious_tools = ["Photoshop", "GIMP", "Adobe", "Canva"]
        
        for tool in suspicious_tools:
            if tool in exif_string:
                print(f" > ⚠️ DETECTED: Image processed with {tool}!")
                return 0.95 
        
        print(" > Metadata looks clean.")
        return 0.1 

    except Exception as e:
        print(f" > Error scanning image: {e}")
        return 0.0
