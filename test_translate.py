#!/usr/bin/env python3
import requests
import json

def test_libretranslate():
    """Test LibreTranslate API directly"""
    
    # Test servers
    servers = [
        "https://libretranslate.com",
        "https://translate.argosopentech.com", 
        "https://libretranslate.de"
    ]
    
    test_text = "hello"
    
    for server in servers:
        print(f"\n=== Testing {server} ===")
        
        try:
            # Test languages endpoint
            print("Testing /languages endpoint...")
            response = requests.get(f"{server}/languages", timeout=10)
            print(f"Languages status: {response.status_code}")
            
            if response.status_code == 200:
                languages = response.json()
                print(f"Available languages: {len(languages)}")
                
                # Test translation
                print(f"Testing translation: '{test_text}' en->hi")
                
                translate_data = {
                    'q': test_text,
                    'source': 'en',
                    'target': 'hi',
                    'format': 'text'
                }
                
                # Try JSON
                response = requests.post(
                    f"{server}/translate",
                    json=translate_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=15
                )
                
                print(f"Translation status: {response.status_code}")
                if response.status_code == 200:
                    result = response.json()
                    translated = result.get('translatedText', 'No translation')
                    print(f"SUCCESS: '{test_text}' -> '{translated}'")
                else:
                    print(f"Translation failed: {response.text}")
            
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_libretranslate()