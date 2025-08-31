import os
import json
import tempfile
import re
import whisper
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import logging
from datetime import datetime
import openai
from openai import OpenAI
import wikipedia
import requests
from urllib.parse import quote
import speech_recognition as sr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure OpenAI
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    openai.api_key = openai_api_key

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

class RealInfoFetcher:
    def __init__(self):
        self.session = requests.Session()
        
    def get_real_info(self, query):
        """Get real information based on the query - handles ANY question"""
        query_lower = query.lower()
        logger.info(f"DEBUG: RealInfoFetcher.get_real_info called with query: '{query}'")
        logger.info(f"DEBUG: Query lowercase: '{query_lower}'")
        
        # Skip very short queries or greetings
        if len(query.strip()) < 3 or any(word in query_lower for word in ['hi', 'hello', 'hey', 'thanks', 'thank you']):
            logger.info(f"DEBUG: Skipping short query or greeting: {query}")
            return None
        
        # Internet search requests - highest priority
        if any(word in query_lower for word in ['find on internet', 'search for', 'look up', 'internet about']):
            logger.info(f"DEBUG: Matched internet search pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # Wikipedia search for general information
        if any(word in query_lower for word in ['what is', 'tell me about', 'information about', 'about', 'who is', 'where is', 'when was', 'how does', 'why does']):
            logger.info(f"DEBUG: Matched general info pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # Current events and news
        if any(word in query_lower for word in ['news', 'current', 'latest', 'recent', 'today', 'happening now']):
            logger.info(f"DEBUG: Matched news pattern, getting current info for: {query}")
            return self.get_current_info(query)
        
        # Technical/programming questions
        if any(word in query_lower for word in ['programming', 'code', 'python', 'javascript', 'java', 'api', 'software', 'development', 'computer', 'technology']):
            logger.info(f"DEBUG: Matched programming pattern, searching Wikipedia for: {query}")
            return self.get_programming_info(query)
        
        # Educational content
        if any(word in query_lower for word in ['learn', 'study', 'education', 'course', 'tutorial', 'exam', 'university', 'college']):
            logger.info(f"DEBUG: Matched education pattern, getting educational info for: {query}")
            return self.get_educational_info(query)
        
        # Science and health questions
        if any(word in query_lower for word in ['science', 'health', 'medicine', 'biology', 'chemistry', 'physics', 'disease', 'treatment']):
            logger.info(f"DEBUG: Matched science/health pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # Geography and places
        if any(word in query_lower for word in ['country', 'city', 'capital', 'population', 'located', 'geography']):
            logger.info(f"DEBUG: Matched geography pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # History questions
        if any(word in query_lower for word in ['history', 'historical', 'ancient', 'war', 'civilization', 'empire', 'century']):
            logger.info(f"DEBUG: Matched history pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # Business and economics
        if any(word in query_lower for word in ['business', 'economy', 'company', 'market', 'finance', 'stock', 'investment']):
            logger.info(f"DEBUG: Matched business pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # Sports and entertainment
        if any(word in query_lower for word in ['sport', 'game', 'movie', 'music', 'actor', 'singer', 'team', 'player']):
            logger.info(f"DEBUG: Matched sports/entertainment pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        # For ANY other question that seems like it's asking for information
        # Check if it's a question (contains question words or ends with ?)
        question_indicators = ['what', 'who', 'where', 'when', 'why', 'how', 'which', 'can you', 'do you know', 'explain']
        if (any(word in query_lower for word in question_indicators) or 
            query.strip().endswith('?') or 
            len(query.split()) > 2):
            logger.info(f"DEBUG: Matched general question pattern, searching Wikipedia for: {query}")
            return self.search_wikipedia(query)
        
        logger.info(f"DEBUG: No pattern matched, returning None for: {query}")
        return None

    def search_wikipedia(self, query):
        """Search Wikipedia for information - enhanced for any topic"""
        try:
            logger.info(f"Searching Wikipedia for: '{query}'")
            
            # Clean query for better search
            clean_query = query.lower()
            clean_query = re.sub(r'^(what is|who is|tell me about|information about|about|explain|describe)\s*', '', clean_query)
            clean_query = clean_query.strip('?').strip()
            
            logger.info(f"Cleaned query for Wikipedia: '{clean_query}'")
            
            # First try exact search
            try:
                page = wikipedia.page(clean_query)
                summary = page.summary[:800] + "..." if len(page.summary) > 800 else page.summary
                return f"Here's what I found about {clean_query}:\n\n{summary}\n\nSource: Wikipedia"
            except wikipedia.DisambiguationError as e:
                # Try first suggestion
                if e.options:
                    logger.info(f"Disambiguation found, trying: {e.options[0]}")
                    page = wikipedia.page(e.options[0])
                    summary = page.summary[:800] + "..." if len(page.summary) > 800 else page.summary
                    return f"Here's what I found about {e.options[0]}:\n\n{summary}\n\nSource: Wikipedia"
            except wikipedia.PageError:
                # Try search
                search_results = wikipedia.search(clean_query, results=5)
                if search_results:
                    logger.info(f"Page not found, trying search result: {search_results[0]}")
                    page = wikipedia.page(search_results[0])
                    summary = page.summary[:800] + "..." if len(page.summary) > 800 else page.summary
                    return f"Here's what I found about {search_results[0]}:\n\n{summary}\n\nSource: Wikipedia"
        
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return f"I couldn't find specific information about '{query}' right now. Could you try rephrasing your question or being more specific?"
        
        return None

    def get_current_info(self, query):
        """Get current information - fallback to Wikipedia for now"""
        return self.search_wikipedia(query)
    
    def get_programming_info(self, query):
        """Get programming information - fallback to Wikipedia for now"""
        return self.search_wikipedia(query)
    
    def get_educational_info(self, query):
        """Get educational information - fallback to Wikipedia for now"""
        return self.search_wikipedia(query)

# Initialize global instances
real_info_fetcher = RealInfoFetcher()

class ChatbotService:
    def __init__(self):
        self.client = None
        if openai_api_key:
            try:
                self.client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                logger.error(f"OpenAI client initialization error: {e}")
                self.client = None
    
    def get_response(self, message):
        """Get response using OpenAI GPT or fallback to real information"""
        try:
            # Try OpenAI first if available
            if self.client:
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant that can answer questions on any topic with accurate information."},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        # If OpenAI is not available or failed, try real information
        logger.info(f"Trying real information for: {message}")
        real_info = real_info_fetcher.get_real_info(message)
        if real_info:
            logger.info(f"Returning real information fallback for: {message}")
            return real_info
        else:
            logger.info(f"No real information found for: {message}")
        
        # Final fallback to built-in responses
        logger.info(f"Using fallback response for: {message}")
        return self.get_fallback_response(message)
    
    def get_fallback_response(self, message):
        """Provide fallback responses for common queries"""
        message_lower = message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "Hello! I'm your universal language support chatbot. I can help you with translations, answer questions, and provide information on various topics. How can I assist you today?"
        
        # Help requests
        if any(word in message_lower for word in ['help', 'what can you do', 'capabilities']):
            return """I can help you with:
• Text and voice translations between languages
• Answering questions on various topics
• Providing information about places, people, and concepts
• Explaining complex topics
• And much more! Just ask me anything you'd like to know."""
        
        # Generic response for any other query
        return "I understand you're asking about something, but I'm having trouble accessing external information right now. Could you please rephrase your question or try asking about a different topic? I'm here to help with translations, general knowledge, and answering your questions."

# Initialize chatbot service
chatbot_service = ChatbotService()

class WhisperTranscriber:
    def __init__(self):
        self.model = None
        
    def load_model(self):
        try:
            if self.model is None:
                logger.info("Loading Whisper model...")
                self.model = whisper.load_model("base")
                logger.info("Whisper model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise e
    
    def transcribe_audio(self, audio_file_path):
        try:
            self.load_model()
            logger.info(f"Transcribing audio file: {audio_file_path}")
            result = self.model.transcribe(audio_file_path)
            return result["text"]
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return None

class LibreTranslateService:
    def __init__(self):
        self.base_url = "https://libretranslate.de"
        self.session = requests.Session()
    
    def get_languages(self):
        """Get list of supported languages"""
        try:
            response = self.session.get(f"{self.base_url}/languages", timeout=5)
            response.raise_for_status()
            languages = response.json()
            return {lang['code']: lang['name'] for lang in languages}
        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return {
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
            }
    
    def translate_text(self, text, source_lang, target_lang):
        """Translate text from source language to target language"""
        try:
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            response = self.session.post(
                f"{self.base_url}/translate",
                data=data,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            return result.get('translatedText', text)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

# Initialize services
whisper_transcriber = WhisperTranscriber()
translate_service = LibreTranslateService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/languages')
def get_languages():
    """Get supported languages"""
    languages = translate_service.get_languages()
    return jsonify(languages)

@app.route('/api/translate', methods=['POST'])
def translate():
    """Translate text"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'en')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        translated_text = translate_service.translate_text(text, source_lang, target_lang)
        
        return jsonify({
            'original_text': text,
            'translated_text': translated_text,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    
    except Exception as e:
        logger.error(f"Translation endpoint error: {e}")
        return jsonify({'error': 'Translation failed'}), 500

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    """Transcribe audio to text"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # Transcribe audio
            transcribed_text = whisper_transcriber.transcribe_audio(tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            if transcribed_text:
                return jsonify({'text': transcribed_text})
            else:
                return jsonify({'error': 'Transcription failed'}), 500
    
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}")
        return jsonify({'error': 'Transcription failed'}), 500

@socketio.on('message')
def handle_message(data):
    """Handle incoming chat messages"""
    try:
        message = data.get('message', '')
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'en')
        
        logger.info(f"Received message: {message}")
        logger.info(f"Source lang: {source_lang}, Target lang: {target_lang}")
        
        if not message:
            emit('response', {'error': 'No message provided'})
            return
        
        # Get chatbot response
        response = chatbot_service.get_response(message)
        logger.info(f"Chatbot response: {response}")
        
        # Translate response if needed
        if target_lang != 'en' and target_lang != source_lang:
            translated_response = translate_service.translate_text(response, 'en', target_lang)
            logger.info(f"Translated response: {translated_response}")
        else:
            translated_response = response
        
        emit('response', {
            'message': message,
            'response': response,
            'translated_response': translated_response,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
    
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        emit('response', {'error': 'Failed to process message'})

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('response', {'message': 'Connected to Universal Language Support Chatbot!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

if __name__ == '__main__':
    logger.info("Starting Universal Language Support Chatbot...")
    logger.info("Visit http://localhost:5000 to use the chatbot")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
