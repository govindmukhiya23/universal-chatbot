# Universal Language Support Chatbot - Utilities

import os
import json
import logging
from typing import List, Dict, Optional
import requests
from datetime import datetime

class LanguageDetector:
    """Detect language of input text using various methods"""
    
    def __init__(self, libretranslate_url: str):
        self.libretranslate_url = libretranslate_url.rstrip('/')
    
    def detect_language(self, text: str) -> str:
        """Detect language of given text"""
        try:
            response = requests.post(
                f"{self.libretranslate_url}/detect",
                json={"q": text}
            )
            if response.status_code == 200:
                result = response.json()
                return result[0]['language'] if result else 'en'
        except Exception as e:
            logging.error(f"Language detection error: {e}")
        
        return 'en'  # Default to English

class AudioProcessor:
    """Handle audio processing for voice input/output"""
    
    @staticmethod
    def validate_audio_format(audio_data: bytes) -> bool:
        """Validate if audio data is in supported format"""
        # Check for common audio format headers
        wav_header = b'RIFF'
        mp3_header = b'ID3'
        
        return audio_data.startswith(wav_header) or audio_data.startswith(mp3_header)
    
    @staticmethod
    def get_audio_duration(audio_file_path: str) -> float:
        """Get duration of audio file in seconds"""
        try:
            import librosa
            y, sr = librosa.load(audio_file_path)
            return len(y) / sr
        except Exception as e:
            logging.error(f"Error getting audio duration: {e}")
            return 0.0

class MessageHistory:
    """Manage conversation history and context"""
    
    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict]] = {}
    
    def add_message(self, session_id: str, message: Dict):
        """Add message to conversation history"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        message['timestamp'] = datetime.now().isoformat()
        self.conversations[session_id].append(message)
        
        # Keep only recent messages
        if len(self.conversations[session_id]) > self.max_history:
            self.conversations[session_id] = self.conversations[session_id][-self.max_history:]
    
    def get_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent conversation history"""
        if session_id not in self.conversations:
            return []
        
        return self.conversations[session_id][-limit:]
    
    def clear_history(self, session_id: str):
        """Clear conversation history for session"""
        if session_id in self.conversations:
            del self.conversations[session_id]

class LanguageCache:
    """Cache translations to improve performance"""
    
    def __init__(self, max_cache_size: int = 1000):
        self.cache: Dict[str, str] = {}
        self.max_cache_size = max_cache_size
    
    def _make_cache_key(self, text: str, source: str, target: str) -> str:
        """Create cache key for translation"""
        return f"{source}_{target}_{hash(text)}"
    
    def get_translation(self, text: str, source: str, target: str) -> Optional[str]:
        """Get cached translation if available"""
        key = self._make_cache_key(text, source, target)
        return self.cache.get(key)
    
    def set_translation(self, text: str, source: str, target: str, translation: str):
        """Cache translation result"""
        key = self._make_cache_key(text, source, target)
        
        # Clear old entries if cache is full
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest 20% of entries
            items_to_remove = len(self.cache) // 5
            for _ in range(items_to_remove):
                self.cache.pop(next(iter(self.cache)))
        
        self.cache[key] = translation

class RateLimiter:
    """Simple rate limiting for API calls"""
    
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed based on rate limit"""
        now = datetime.now().timestamp()
        
        if identifier not in self.requests:
            self.requests[identifier] = []
        
        # Remove old requests outside time window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.time_window
        ]
        
        # Check if under limit
        if len(self.requests[identifier]) < self.max_requests:
            self.requests[identifier].append(now)
            return True
        
        return False

class ConfigManager:
    """Manage application configuration"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load configuration from file"""
        default_config = {
            'supported_languages': {
                'en': 'English',
                'es': 'Spanish', 
                'fr': 'French',
                'de': 'German',
                'it': 'Italian',
                'pt': 'Portuguese',
                'ru': 'Russian',
                'ja': 'Japanese',
                'ko': 'Korean',
                'zh': 'Chinese',
                'ar': 'Arabic',
                'hi': 'Hindi'
            },
            'whisper_models': ['tiny', 'base', 'small', 'medium', 'large'],
            'default_settings': {
                'user_language': 'en',
                'bot_language': 'en',
                'voice_response': True,
                'auto_translate': True,
                'whisper_model': 'base'
            },
            'rate_limits': {
                'translation': {'max_requests': 100, 'time_window': 3600},
                'voice': {'max_requests': 50, 'time_window': 3600}
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Merge with defaults
                    return {**default_config, **config}
            except Exception as e:
                logging.error(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving config: {e}")
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value):
        """Set configuration value"""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        self.save_config()

class Logger:
    """Custom logger for the application"""
    
    @staticmethod
    def setup_logging(log_level: str = 'INFO', log_file: str = None):
        """Setup application logging"""
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Setup file handler if specified
        handlers = [console_handler]
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=level,
            handlers=handlers,
            force=True
        )

# Utility functions
def validate_language_code(lang_code: str, supported_languages: List[str]) -> bool:
    """Validate if language code is supported"""
    return lang_code in supported_languages

def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize input text"""
    if not isinstance(text, str):
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()

def format_language_name(lang_code: str, lang_names: Dict[str, str]) -> str:
    """Format language code to human-readable name"""
    return lang_names.get(lang_code, lang_code.upper())

def estimate_processing_time(text_length: int, operation: str = 'translation') -> float:
    """Estimate processing time based on text length and operation"""
    base_times = {
        'translation': 0.1,  # seconds per character
        'speech_to_text': 0.5,  # seconds per second of audio
        'text_to_speech': 0.2   # seconds per character
    }
    
    base_time = base_times.get(operation, 0.1)
    return max(0.5, text_length * base_time)  # Minimum 0.5 seconds
