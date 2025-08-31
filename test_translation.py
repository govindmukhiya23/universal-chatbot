#!/usr/bin/env python3
"""
Test script for Universal Language Support Chatbot translation service
"""

import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_libretranslate():
    """Test LibreTranslate service connectivity and basic translation"""
    base_url = os.getenv('LIBRETRANSLATE_URL', 'https://libretranslate.com')
    api_key = os.getenv('LIBRETRANSLATE_API_KEY', '')
    
    print(f"Testing LibreTranslate at: {base_url}")
    print("-" * 50)
    
    # Test 1: Check if service is available
    try:
        print("1. Testing service availability...")
        response = requests.get(f"{base_url}/languages", timeout=10)
        if response.status_code == 200:
            languages = response.json()
            print(f"✅ Service is available! Found {len(languages)} languages")
            print(f"Sample languages: {[lang.get('code', 'unknown') for lang in languages[:5]]}")
        else:
            print(f"❌ Service returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        return False
    
    # Test 2: Simple translation test
    try:
        print("\n2. Testing simple translation (English to Spanish)...")
        data = {
            'q': 'Hello, how are you?',
            'source': 'en',
            'target': 'es',
            'format': 'text'
        }
        
        if api_key:
            data['api_key'] = api_key
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{base_url}/translate", 
            json=data, 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            translated = result.get('translatedText', 'No translation')
            print(f"✅ Translation successful!")
            print(f"Original: {data['q']}")
            print(f"Translated: {translated}")
        else:
            print(f"❌ Translation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Translation test failed: {e}")
        return False
    
    # Test 3: Test with different language pairs
    try:
        print("\n3. Testing multiple language pairs...")
        test_pairs = [
            ('en', 'fr', 'Hello world'),
            ('en', 'de', 'Good morning'),
            ('en', 'hi', 'Thank you'),
        ]
        
        for source, target, text in test_pairs:
            data = {
                'q': text,
                'source': source,
                'target': target,
                'format': 'text'
            }
            
            if api_key:
                data['api_key'] = api_key
            
            response = requests.post(
                f"{base_url}/translate", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                translated = result.get('translatedText', 'No translation')
                print(f"✅ {source}→{target}: {text} → {translated}")
            else:
                print(f"❌ {source}→{target}: Failed ({response.status_code})")
                
    except Exception as e:
        print(f"❌ Multi-language test failed: {e}")
    
    print("\n" + "=" * 50)
    print("Translation service test completed!")
    return True

def test_fallback_mode():
    """Test application fallback when translation service is unavailable"""
    print("\n4. Testing fallback mode...")
    
    # Simulate offline service
    from app import TranslationService
    
    # Test with invalid URL
    translator = TranslationService("http://invalid-url:9999")
    
    if not translator.is_available:
        print("✅ Correctly detected unavailable service")
        
        # Test fallback translation
        result = translator.translate("Hello", "en", "es")
        if "[Translation unavailable" in result:
            print("✅ Fallback message works correctly")
        else:
            print("❌ Fallback message not working")
        
        # Test fallback languages
        languages = translator.get_languages()
        if len(languages) > 0:
            print(f"✅ Fallback languages available: {len(languages)} languages")
        else:
            print("❌ Fallback languages not working")
    else:
        print("❌ Should have detected unavailable service")

if __name__ == "__main__":
    print("Universal Language Support Chatbot - Translation Test")
    print("=" * 60)
    
    success = test_libretranslate()
    
    if success:
        test_fallback_mode()
        print("\n🎉 All tests completed! Your translation service should work now.")
        print("\nTo fix the current error:")
        print("1. Stop the running application (Ctrl+C)")
        print("2. Restart it: python app.py")
        print("3. Try sending messages again")
    else:
        print("\n⚠️  Translation service has issues. Consider:")
        print("1. Using a different LibreTranslate instance")
        print("2. Setting up a local LibreTranslate server")
        print("3. The app will work but without translation")
        print("\nSee LIBRETRANSLATE_SETUP.md for setup instructions.")
