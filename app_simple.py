import os
import json
import tempfile
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import logging
from datetime import datetime
import openai
from openai import OpenAI
import wikipedia
import requests
import google.generativeai as genai
from io import BytesIO
import base64

from local_models import LocalModelHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure OpenAI
openai_api_key = os.getenv('OPENAI_API_KEY')
if openai_api_key:
    openai.api_key = openai_api_key

# Configure Google Gemini API
gemini_api_key = "AIzaSyBt7l_hasZ7bR_1LkJxEMpFKuLxq4M990o"
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# In-memory chat history per session
from collections import defaultdict, deque
import uuid
chat_histories = defaultdict(lambda: deque(maxlen=50))

def get_session_id():
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    return session['chat_session_id']

class RealInfoFetcher:
    def __init__(self):
        self.session = requests.Session()
        
    def get_real_info(self, query):
        query_lower = query.lower()
        logger.info(f"RealInfoFetcher called with: '{query}'")
        
        if len(query.strip()) < 3 or any(word in query_lower for word in ['hi', 'hello', 'hey', 'thanks']):
            return None
        
        if any(word in query_lower for word in ['what is', 'tell me about', 'who is', 'where is']):
            return self.search_wikipedia(query)
        
        return None

    def search_wikipedia(self, query):
        try:
            clean_query = query.lower()
            clean_query = clean_query.replace('what is', '').replace('tell me about', '').strip()
            
            page = wikipedia.page(clean_query)
            summary = page.summary[:500] + "..." if len(page.summary) > 500 else page.summary
            return f"Here's what I found about {clean_query}:\n\n{summary}\n\nSource: Wikipedia"
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return None

real_info_fetcher = RealInfoFetcher()

class ChatbotService:
    def __init__(self):
        self.openai_client = None
        self.gemini_model = None
        
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                logger.error(f"OpenAI client error: {e}")
        
        if gemini_api_key:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini model initialized")
            except Exception as e:
                logger.error(f"Gemini error: {e}")
    
    def get_response(self, message, target_lang='en'):
        language_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi'
        }
        
        target_language_name = language_names.get(target_lang, 'English')
        
        if self.gemini_model:
            try:
                if target_lang == 'en':
                    prompt = f"You are a helpful AI assistant. Respond professionally to: {message}"
                else:
                    prompt = f"You are a helpful AI assistant. Respond ONLY in {target_language_name} to: {message}"
                
                response = self.gemini_model.generate_content(prompt)
                if response.text:
                    return response.text
            except Exception as e:
                logger.error(f"Gemini error: {e}")
        
        if self.openai_client:
            try:
                system_content = f"You are a helpful assistant. Respond in {target_language_name}."
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=500
                )
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI error: {e}")
        
        real_info = real_info_fetcher.get_real_info(message)
        if real_info:
            return real_info
        
        return self.get_fallback_response(message, target_lang)
    
    def get_fallback_response(self, message, target_lang='en'):
        responses = {
            'en': "Hello! I'm here to help you with any questions. What would you like to know?",
            'hi': "नमस्ते! मैं आपकी सहायता के लिए यहाँ हूँ। आप क्या जानना चाहेंगे?",
            'es': "¡Hola! Estoy aquí para ayudarte. ¿Qué te gustaría saber?",
            'fr': "Bonjour! Je suis ici pour vous aider. Que souhaiteriez-vous savoir?"
        }
        return responses.get(target_lang, responses['en'])

chatbot_service = ChatbotService()

class WhisperTranscriber:
    def __init__(self):
        self.local_model = LocalModelHandler()
        
    def transcribe_audio(self, audio_file_path):
        try:
            return self.local_model.transcribe_audio(audio_file_path)
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

class LibreTranslateService:
    def __init__(self):
        self.base_urls = [
            "https://libretranslate.com",
            "https://translate.astian.org",
            "https://libretranslate.de"
        ]
        self.session = requests.Session()
        
    def get_working_url(self):
        for url in self.base_urls:
            try:
                response = self.session.get(f"{url}/languages", timeout=5)
                if response.status_code == 200:
                    return url
            except:
                continue
        return None
    
    def get_languages(self):
        return {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi'
        }
    
    def translate_text(self, text, source_lang, target_lang):
        if source_lang == target_lang:
            return text
            
        working_url = self.get_working_url()
        if not working_url:
            return text
            
        try:
            response = self.session.post(
                f"{working_url}/translate",
                json={
                    'q': text,
                    'source': source_lang,
                    'target': target_lang,
                    'format': 'text'
                },
                timeout=15
            )
            result = response.json()
            return result.get('translatedText', text)
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text

whisper_transcriber = WhisperTranscriber()
translate_service = LibreTranslateService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/languages')
def get_languages():
    languages = translate_service.get_languages()
    return jsonify(languages)

@app.route('/api/transcribe', methods=['POST'])
def transcribe():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400
        
        audio_file = request.files['audio']
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            transcribed_text = whisper_transcriber.transcribe_audio(tmp_file.name)
            os.unlink(tmp_file.name)
            
            if transcribed_text:
                return jsonify({'text': transcribed_text})
            else:
                return jsonify({'error': 'Transcription failed'}), 500
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return jsonify({'error': 'Transcription failed'}), 500

@socketio.on('message')
def handle_message(data):
    try:
        message = data.get('message', '')
        source_lang = data.get('source_lang', 'auto')
        target_lang = data.get('target_lang', 'en')
        
        if not message:
            emit('chat_response', {'error': 'No message'})
            return
        
        response = chatbot_service.get_response(message, target_lang)
        
        emit('chat_response', {
            'message': message,
            'response': response,
            'source_lang': source_lang,
            'target_lang': target_lang
        })
        
        try:
            session_id = get_session_id()
            chat_histories[session_id].append({'role': 'user', 'text': message})
            chat_histories[session_id].append({'role': 'bot', 'text': response})
        except:
            pass
    
    except Exception as e:
        logger.error(f"Message error: {e}")
        emit('chat_response', {'error': 'Failed to process message'})

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('chat_response', {'message': 'Connected to Universal Language Support Chatbot!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')

# Initialize local model handler for image generation
local_model_handler = LocalModelHandler()

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Generate image using local Stable Diffusion
        image = local_model_handler.generate_image(prompt)
        
        if image:
            # Convert PIL Image to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return jsonify({
                'success': True,
                'image': img_str,
                'prompt': prompt
            })
        else:
            return jsonify({'error': 'Failed to generate image'}), 500
            
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice-to-image', methods=['POST'])
def voice_to_image():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio']
        
        # Save audio file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # First transcribe audio to text using local Whisper
            transcription = local_model_handler.transcribe_audio(tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            if not transcription:
                return jsonify({'error': 'Failed to transcribe audio'}), 500
            
            # Generate image from transcribed text using local Stable Diffusion
            image = local_model_handler.generate_image(transcription)
            
            if image:
                # Convert PIL Image to base64
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                return jsonify({
                    'success': True,
                    'image': img_str,
                    'transcription': transcription,
                    'prompt': transcription
                })
            else:
                return jsonify({'error': 'Failed to generate image'}), 500
                
    except Exception as e:
        logger.error(f"Voice-to-image error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("Starting Universal Language Support Chatbot with Local Models...")
    logger.info("Loading Stable Diffusion and Whisper models...")
    # Pre-initialize models
    local_model_handler.init_stable_diffusion()
    local_model_handler.init_voice_recognition()
    logger.info("Visit http://localhost:5000 to use the chatbot")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)