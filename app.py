import os
import json
import tempfile
import re
import whisper
from flask import Flask, render_template, request, jsonify, session
from flask_socketio import SocketIO, emit, join_room, leave_room
from dotenv import load_dotenv
import logging
from datetime import datetime
import openai
from openai import OpenAI
import wikipedia
import requests
from urllib.parse import quote
import google.generativeai as genai
from io import BytesIO
import base64
from tic_tac_toe import TicTacToe, GameDifficulty
# import torch
# from diffusers import StableDiffusionPipeline
# from transformers import WhisperProcessor, WhisperForConditionalGeneration
# from io import BytesIO
# import base64

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

# In-memory chat history per session (for demo; use DB for production)
from collections import defaultdict, deque
import uuid
chat_histories = defaultdict(lambda: deque(maxlen=50))  # Limit to last 50 messages per session

# Game management
active_games = {}  # {session_id: TicTacToe instance}

# Room management
import random
import time
rooms = {}  # {room_pin: {users: {user_id: {name, language, joined_at}}, messages: [], created_at, last_activity}}
user_rooms = {}  # {user_id: room_pin}

# Utility to get session ID
def get_session_id():
    if 'chat_session_id' not in session:
        session['chat_session_id'] = str(uuid.uuid4())
    return session['chat_session_id']

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

# from local_models import LocalModelHandler
# local_model_handler = LocalModelHandler()

class ImageGenerator:
    def __init__(self):
        # self.model_handler = LocalModelHandler()
        self.model_handler = None
        
    def generate_image(self, prompt):
        """Generate an image from text prompt"""
        logger.info(f"Image generation requested for: {prompt}")
        return None  # Disabled for now
            
    def voice_to_image(self, audio_data):
        """Convert voice to image using transcription and image generation"""
        try:
            # First transcribe the audio
            transcription = self.model_handler.transcribe_audio(audio_data)
            if not transcription:
                return None, None
                
            # Then generate image from transcription
            image = self.model_handler.generate_image(transcription)
            if not image:
                return transcription, None
                
            # Convert PIL Image to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return transcription, img_str
            
        except Exception as e:
            logger.error(f"Voice to image error: {e}")
            return None, None

# Initialize image generator
image_generator = ImageGenerator()

class ChatbotService:
    def __init__(self):
        self.openai_client = None
        self.gemini_model = None
        
        # Initialize OpenAI client
        if openai_api_key:
            try:
                self.openai_client = OpenAI(api_key=openai_api_key)
            except Exception as e:
                logger.error(f"OpenAI client initialization error: {e}")
                self.openai_client = None
        
        # Initialize Gemini model
        if gemini_api_key:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                logger.info("Gemini model initialized successfully")
            except Exception as e:
                logger.error(f"Gemini model initialization error: {e}")
                self.gemini_model = None
    
    def get_response(self, message, target_lang='en'):
        """Get response using Gemini API first, then OpenAI GPT or fallback to real information"""
        
        # Define comprehensive language names for better prompting (100+ languages)
        language_names = {
            # Major World Languages
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese (Simplified)',
            'zh-TW': 'Chinese (Traditional)',
            'ar': 'Arabic',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'cs': 'Czech',
            'sk': 'Slovak',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sr': 'Serbian',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'el': 'Greek',
            'tr': 'Turkish',
            'he': 'Hebrew',
            'fa': 'Persian',
            'ur': 'Urdu',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            
            # Indian Languages
            'hi': 'Hindi',
            'te': 'Telugu',
            'ta': 'Tamil',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'mr': 'Marathi',
            'pa': 'Punjabi',
            'or': 'Odia',
            'as': 'Assamese',
            'bh': 'Bhojpuri',
            'mai': 'Maithili',
            'mag': 'Magahi',
            'ne': 'Nepali',
            'sd': 'Sindhi',
            'ks': 'Kashmiri',
            'doi': 'Dogri',
            'kok': 'Konkani',
            'mni': 'Manipuri',
            'sat': 'Santali',
            'brx': 'Bodo',
            'gom': 'Goan Konkani',
            'raj': 'Rajasthani',
            'bpy': 'Bishnupriya',
            'hne': 'Chhattisgarhi',
            'gon': 'Gondi',
            'kha': 'Khasi',
            'mjz': 'Majhi',
            'new': 'Newari',
            'bho': 'Bhojpuri',
            'awa': 'Awadhi',
            
            # African Languages
            'sw': 'Swahili',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'af': 'Afrikaans',
            'am': 'Amharic',
            'ha': 'Hausa',
            'ig': 'Igbo',
            'yo': 'Yoruba',
            'rw': 'Kinyarwanda',
            'mg': 'Malagasy',
            'sn': 'Shona',
            'so': 'Somali',
            
            # European Languages
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'cy': 'Welsh',
            'ga': 'Irish',
            'gd': 'Scottish Gaelic',
            'is': 'Icelandic',
            'mt': 'Maltese',
            'sq': 'Albanian',
            'mk': 'Macedonian',
            'bs': 'Bosnian',
            'me': 'Montenegrin',
            
            # Middle Eastern Languages
            'ku': 'Kurdish',
            'az': 'Azerbaijani',
            'ka': 'Georgian',
            'hy': 'Armenian',
            'ps': 'Pashto',
            'tg': 'Tajik',
            'uz': 'Uzbek',
            'kk': 'Kazakh',
            'ky': 'Kyrgyz',
            'tk': 'Turkmen',
            'mn': 'Mongolian',
            
            # Southeast Asian Languages
            'my': 'Myanmar (Burmese)',
            'km': 'Khmer',
            'lo': 'Lao',
            'si': 'Sinhala',
            'dv': 'Maldivian',
            
            # Other Asian Languages
            'ug': 'Uyghur',
            'bo': 'Tibetan',
            'dz': 'Dzongkha',
            
            # Pacific Languages
            'haw': 'Hawaiian',
            'mi': 'Maori',
            'sm': 'Samoan',
            'to': 'Tongan',
            'fj': 'Fijian',
            
            # Additional Languages
            'jv': 'Javanese',
            'su': 'Sundanese',
            'ceb': 'Cebuano',
            'hil': 'Hiligaynon',
            'war': 'Waray',
            'bcl': 'Bicolano',
            'pam': 'Kapampangan',
            'lb': 'Luxembourgish',
            'rm': 'Romansh',
            'fo': 'Faroese',
            'kl': 'Greenlandic'
        }
        
        target_language_name = language_names.get(target_lang, 'English')
        
        # Try Gemini API first (best results)
        if self.gemini_model:
            try:
                logger.info(f"Using Gemini API for: {message} (Target language: {target_language_name})")
                
                # Analyze question complexity and determine appropriate response length
                question_length = len(message.split())
                is_simple_question = any(word in message.lower() for word in ['what', 'who', 'when', 'where', 'how old', 'what is'])
                is_greeting = any(word in message.lower() for word in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'namaste', 'hola', 'bonjour'])
                is_yes_no = any(word in message.lower() for word in ['is it', 'are you', 'can you', 'do you', 'will you'])
                
                # Determine response style based on question type
                if is_greeting or question_length <= 2:
                    response_instruction = "Keep your response very brief and friendly (1-2 sentences maximum)."
                elif (is_simple_question or is_yes_no) and question_length <= 6:
                    response_instruction = "Provide a concise but informative answer (2-3 sentences)."
                elif question_length <= 10:
                    response_instruction = "Provide a moderate length response with key details (1-2 short paragraphs)."
                else:
                    response_instruction = "Provide a comprehensive and detailed response with examples and explanations."
                
                # Create language-specific prompt
                if target_lang == 'en':
                    enhanced_prompt = f"""You are a professional AI assistant providing comprehensive and well-structured responses. 

{response_instruction}

Format your response with:
- **Bold text** for important points and headings
- *Italics* for emphasis
- Clear paragraph breaks for readability
- Bullet points when listing items
- Professional, friendly tone

User Question: {message}

Please provide a helpful and well-formatted response:"""
                else:
                    enhanced_prompt = f"""You are a professional AI assistant. The user has requested responses in {target_language_name}.

IMPORTANT: Respond ONLY in {target_language_name}. Do not use English at all.

{response_instruction}

Format your response with:
- **Bold text** for important points and headings
- *Italics* for emphasis
- Clear paragraph breaks for readability
- Bullet points when listing items
- Professional, friendly tone

User Question: {message}

Please provide a helpful and well-formatted response entirely in {target_language_name}:"""
                
                response = self.gemini_model.generate_content(enhanced_prompt)
                if response.text:
                    logger.info(f"Gemini API response successful for: {message}")
                    return response.text
            except Exception as e:
                logger.error(f"Gemini API error: {e}")
        
        # Try OpenAI as backup
        try:
            if self.openai_client:
                logger.info(f"Falling back to OpenAI for: {message}")
                
                # Analyze question complexity for OpenAI fallback
                question_length = len(message.split())
                is_simple_question = any(word in message.lower() for word in ['what', 'who', 'when', 'where', 'how old', 'what is'])
                is_greeting = any(word in message.lower() for word in ['hello', 'hi', 'hey', 'good morning', 'good evening', 'namaste', 'hola', 'bonjour'])
                is_yes_no = any(word in message.lower() for word in ['is it', 'are you', 'can you', 'do you', 'will you'])
                
                # Determine response style
                if is_greeting or question_length <= 2:
                    response_instruction = "Keep your response very brief and friendly (1-2 sentences maximum)."
                elif (is_simple_question or is_yes_no) and question_length <= 6:
                    response_instruction = "Provide a concise but informative answer (2-3 sentences)."
                elif question_length <= 10:
                    response_instruction = "Provide a moderate length response with key details (1-2 short paragraphs)."
                else:
                    response_instruction = "Provide a comprehensive and detailed response with examples and explanations."
                
                # Create language-specific system message
                if target_lang == 'en':
                    system_content = f"You are a helpful assistant that can answer questions on any topic with accurate information. {response_instruction}"
                else:
                    target_language_name = language_names.get(target_lang, 'English')
                    system_content = f"You are a helpful assistant. IMPORTANT: Respond ONLY in {target_language_name}. Do not use English at all. {response_instruction}"
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_content},
                        {"role": "user", "content": message}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
        
        # If both AI APIs failed, try real information
        logger.info(f"Trying real information for: {message}")
        real_info = real_info_fetcher.get_real_info(message)
        if real_info:
            logger.info(f"Returning real information fallback for: {message}")
            return real_info
        else:
            logger.info(f"No real information found for: {message}")
        
        # Final fallback to built-in responses
        logger.info(f"Using fallback response for: {message}")
        return self.get_fallback_response(message, target_lang)
    
    def get_fallback_response(self, message, target_lang='en'):
        """Provide professional fallback responses for common queries in the target language"""
        message_lower = message.lower()
        
        # Analyze question length and complexity for appropriate response length
        question_length = len(message.split())
        is_greeting = any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'नमस्ते', 'hola', 'bonjour'])
        is_help_request = any(word in message_lower for word in ['help', 'what can you do', 'capabilities', 'मदद', 'ayuda', 'aide'])
        
        # For very short questions or greetings, provide brief responses
        if is_greeting or question_length <= 2:
            brief_responses = {
                'en': "Hello! How can I help you today?",
                'hi': "नमस्ते! मैं आपकी कैसे सहायता कर सकता हूँ?",
                'es': "¡Hola! ¿Cómo puedo ayudarte?",
                'fr': "Bonjour! Comment puis-je vous aider?",
                'de': "Hallo! Wie kann ich Ihnen helfen?",
                'pt': "Olá! Como posso ajudá-lo?",
                'ru': "Привет! Как я могу вам помочь?",
                'ja': "こんにちは！どのようにお手伝いできますか？",
                'ko': "안녕하세요! 어떻게 도와드릴까요?",
                'zh': "你好！我能为您做什么？",
                'ar': "مرحبا! كيف يمكنني مساعدتك؟",
                'it': "Ciao! Come posso aiutarti?"
            }
            return brief_responses.get(target_lang, brief_responses['en'])
        
        # For help requests, provide moderate responses
        if is_help_request:
            help_responses = {
                'en': """**🤖 AI Assistant Capabilities**

I can help you with:
• Answering questions on any topic
• Translating between languages  
• Providing detailed explanations

What would you like to know?""",
                'hi': """**🤖 AI सहायक की क्षमताएं**

मैं आपकी इन कामों में मदद कर सकता हूँ:
• किसी भी विषय पर सवालों का जवाब
• भाषाओं के बीच अनुवाद
• विस्तृत जानकारी और व्याख्या

आप मुझसे क्या पूछना चाहेंगे?""",
                'es': """**🤖 Capacidades del Asistente IA**

Puedo ayudarte con:
• Responder preguntas sobre cualquier tema
• Traducir entre idiomas
• Proporcionar explicaciones detalladas

¿En qué te puedo ayudar?""",
                'fr': """**🤖 Capacités de l'Assistant IA**

Je peux vous aider avec:
• Répondre aux questions sur n'importe quel sujet
• Traduire entre plusieurs langues
• Fournir des explications détaillées

Comment puis-je vous aider?"""
            }
            return help_responses.get(target_lang, help_responses['en'])
        
        # For other questions, provide appropriate length responses based on query complexity
        if question_length <= 6:
            # Short questions get concise answers
            short_responses = {
                'en': "I'm here to help! Please ask me any specific question and I'll provide a helpful answer.",
                'hi': "मैं यहाँ आपकी मदद के लिए हूँ! कृपया कोई विशिष्ट सवाल पूछें और मैं सहायक उत्तर दूंगा।",
                'es': "¡Estoy aquí para ayudar! Haz cualquier pregunta específica y te daré una respuesta útil.",
                'fr': "Je suis ici pour vous aider! Posez-moi une question spécifique et je vous donnerai une réponse utile."
            }
            return short_responses.get(target_lang, short_responses['en'])
        
        # For longer/complex questions, provide detailed responses (keeping original structure)
        # Define responses by language
        responses = {
            'en': {
                'greeting': """**Welcome to Your Universal Language Support Chatbot!** 👋

I'm here to assist you with a wide range of tasks including:

• **Language Translation** - Text and voice translation between multiple languages
• **Information Retrieval** - Detailed answers on various topics
• **Real-time Conversations** - Interactive chat with voice support
• **Educational Content** - Learning resources and explanations

**How can I help you today?**""",
                'help': """**🤖 AI Assistant Capabilities**

**Core Features:**
• Answer questions on any topic
• Translate between multiple languages
• Provide detailed explanations
• Assist with research and learning

**How to use:**
• Type your question in any language
• Use voice input for hands-free interaction
• Adjust language settings in the settings panel

**What would you like to know?**""",
                'default': """I'm here to help you with any questions or tasks you might have. Feel free to ask me about:

• **General Information** - Facts, explanations, definitions
• **Language Support** - Translation and language learning
• **Educational Topics** - Science, history, technology, and more
• **Practical Assistance** - Writing, problem-solving, and guidance

What would you like to know more about?"""
            },
            'hi': {
                'greeting': """**आपके यूनिवर्सल भाषा सहायता चैटबॉट में आपका स्वागत है!** 👋

मैं यहां विभिन्न कार्यों में आपकी सहायता के लिए हूं:

• **भाषा अनुवाद** - कई भाषाओं के बीच टेक्स्ट और वॉयस अनुवाद
• **जानकारी प्राप्ति** - विभिन्न विषयों पर विस्तृत उत्तर
• **रीयल-टाइम बातचीत** - वॉयस सपोर्ट के साथ इंटरैक्टिव चैट
• **शैक्षणिक सामग्री** - सीखने के संसाधन और व्याख्याएं

**आज मैं आपकी कैसे मदद कर सकता हूं?**""",
                'help': """**🤖 AI सहायक क्षमताएं**

**मुख्य विशेषताएं:**
• किसी भी विषय पर प्रश्नों के उत्तर
• कई भाषाओं के बीच अनुवाद
• विस्तृत व्याख्याएं प्रदान करना
• अनुसंधान और सीखने में सहायता

**उपयोग कैसे करें:**
• किसी भी भाषा में अपना प्रश्न टाइप करें
• हैंड्स-फ्री इंटरैक्शन के लिए वॉयस इनपुट का उपयोग करें
• सेटिंग्स पैनल में भाषा सेटिंग्स समायोजित करें

**आप क्या जानना चाहेंगे?**""",
                'default': """मैं यहां किसी भी प्रश्न या कार्य में आपकी सहायता के लिए हूं। मुझसे इन विषयों पर पूछें:

• **सामान्य जानकारी** - तथ्य, व्याख्याएं, परिभाषाएं
• **भाषा सहायता** - अनुवाद और भाषा सीखना
• **शैक्षणिक विषय** - विज्ञान, इतिहास, प्रौद्योगिकी, और अधिक
• **व्यावहारिक सहायता** - लेखन, समस्या समाधान, और मार्गदर्शन

आप किस बारे में और जानना चाहेंगे?"""
            },
            'es': {
                'greeting': """**¡Bienvenido a tu Chatbot de Soporte Universal de Idiomas!** 👋

Estoy aquí para ayudarte con una amplia gama de tareas que incluyen:

• **Traducción de Idiomas** - Traducción de texto y voz entre múltiples idiomas
• **Recuperación de Información** - Respuestas detalladas sobre varios temas
• **Conversaciones en Tiempo Real** - Chat interactivo con soporte de voz
• **Contenido Educativo** - Recursos de aprendizaje y explicaciones

**¿Cómo puedo ayudarte hoy?**""",
                'help': """**🤖 Capacidades del Asistente de IA**

**Características Principales:**
• Responder preguntas sobre cualquier tema
• Traducir entre múltiples idiomas
• Proporcionar explicaciones detalladas
• Asistir con investigación y aprendizaje

**Cómo usar:**
• Escribe tu pregunta en cualquier idioma
• Usa entrada de voz para interacción sin manos
• Ajusta la configuración de idioma en el panel de configuración

**¿Qué te gustaría saber?**""",
                'default': """Estoy aquí para ayudarte con cualquier pregunta o tarea que puedas tener. Siéntete libre de preguntarme sobre:

• **Información General** - Hechos, explicaciones, definiciones
• **Soporte de Idiomas** - Traducción y aprendizaje de idiomas
• **Temas Educativos** - Ciencia, historia, tecnología y más
• **Asistencia Práctica** - Escritura, resolución de problemas y orientación

¿Sobre qué te gustaría saber más?"""
            },
            'fr': {
                'greeting': """**Bienvenue dans votre Chatbot de Support Linguistique Universel !** 👋

Je suis ici pour vous aider avec une large gamme de tâches incluant :

• **Traduction Linguistique** - Traduction de texte et voix entre plusieurs langues
• **Récupération d'Informations** - Réponses détaillées sur divers sujets
• **Conversations en Temps Réel** - Chat interactif avec support vocal
• **Contenu Éducatif** - Ressources d'apprentissage et explications

**Comment puis-je vous aider aujourd'hui ?**""",
                'help': """**🤖 Capacités de l'Assistant IA**

**Fonctionnalités Principales :**
• Répondre aux questions sur n'importe quel sujet
• Traduire entre plusieurs langues
• Fournir des explications détaillées
• Assister avec la recherche et l'apprentissage

**Comment utiliser :**
• Tapez votre question dans n'importe quelle langue
• Utilisez l'entrée vocale pour une interaction mains libres
• Ajustez les paramètres de langue dans le panneau des paramètres

**Que souhaiteriez-vous savoir ?**""",
                'default': """Je suis ici pour vous aider avec toutes les questions ou tâches que vous pourriez avoir. N'hésitez pas à me demander sur :

• **Informations Générales** - Faits, explications, définitions
• **Support Linguistique** - Traduction et apprentissage des langues
• **Sujets Éducatifs** - Science, histoire, technologie et plus
• **Assistance Pratique** - Écriture, résolution de problèmes et guidance

Sur quoi aimeriez-vous en savoir plus ?"""
            }
        }
        
        # Get language-specific responses, fallback to English
        lang_responses = responses.get(target_lang, responses['en'])
        
        # Greeting responses
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'नमस्ते', 'hola', 'bonjour']):
            return lang_responses['greeting']
        
        # Help requests
        if any(word in message_lower for word in ['help', 'what can you do', 'capabilities', 'मदद', 'ayuda', 'aide']):
            return lang_responses['help']
        
        # Default response
        return lang_responses['default']
    
    def get_realtime_response(self, message, target_lang='en'):
        """Get conversational response optimized for real-time chat"""
        
        # Make messages more conversational for real-time chat
        message_lower = message.lower().strip()
        
        # Define comprehensive language names for better prompting (100+ languages)
        language_names = {
            # Major World Languages
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese (Simplified)',
            'zh-TW': 'Chinese (Traditional)',
            'ar': 'Arabic',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'pl': 'Polish',
            'cs': 'Czech',
            'sk': 'Slovak',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sr': 'Serbian',
            'sl': 'Slovenian',
            'et': 'Estonian',
            'lv': 'Latvian',
            'lt': 'Lithuanian',
            'el': 'Greek',
            'tr': 'Turkish',
            'he': 'Hebrew',
            'fa': 'Persian',
            'ur': 'Urdu',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'id': 'Indonesian',
            'ms': 'Malay',
            'tl': 'Filipino',
            
            # Indian Languages
            'hi': 'Hindi',
            'te': 'Telugu',
            'ta': 'Tamil',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'bn': 'Bengali',
            'gu': 'Gujarati',
            'mr': 'Marathi',
            'pa': 'Punjabi',
            'or': 'Odia',
            'as': 'Assamese',
            'bh': 'Bhojpuri',
            'mai': 'Maithili',
            'mag': 'Magahi',
            'ne': 'Nepali',
            'sd': 'Sindhi',
            'ks': 'Kashmiri',
            'doi': 'Dogri',
            'kok': 'Konkani',
            'mni': 'Manipuri',
            'sat': 'Santali',
            'brx': 'Bodo',
            'gom': 'Goan Konkani',
            'raj': 'Rajasthani',
            'bpy': 'Bishnupriya',
            'hne': 'Chhattisgarhi',
            'gon': 'Gondi',
            'kha': 'Khasi',
            'mjz': 'Majhi',
            'new': 'Newari',
            'bho': 'Bhojpuri',
            'awa': 'Awadhi',
            
            # African Languages
            'sw': 'Swahili',
            'zu': 'Zulu',
            'xh': 'Xhosa',
            'af': 'Afrikaans',
            'am': 'Amharic',
            'ha': 'Hausa',
            'ig': 'Igbo',
            'yo': 'Yoruba',
            'rw': 'Kinyarwanda',
            'mg': 'Malagasy',
            'sn': 'Shona',
            'so': 'Somali',
            
            # European Languages
            'eu': 'Basque',
            'ca': 'Catalan',
            'gl': 'Galician',
            'cy': 'Welsh',
            'ga': 'Irish',
            'gd': 'Scottish Gaelic',
            'is': 'Icelandic',
            'mt': 'Maltese',
            'sq': 'Albanian',
            'mk': 'Macedonian',
            'bs': 'Bosnian',
            'me': 'Montenegrin',
            
            # Middle Eastern Languages
            'ku': 'Kurdish',
            'az': 'Azerbaijani',
            'ka': 'Georgian',
            'hy': 'Armenian',
            'ps': 'Pashto',
            'tg': 'Tajik',
            'uz': 'Uzbek',
            'kk': 'Kazakh',
            'ky': 'Kyrgyz',
            'tk': 'Turkmen',
            'mn': 'Mongolian',
            
            # Southeast Asian Languages
            'my': 'Myanmar (Burmese)',
            'km': 'Khmer',
            'lo': 'Lao',
            'si': 'Sinhala',
            'dv': 'Maldivian',
            
            # Other Asian Languages
            'ug': 'Uyghur',
            'bo': 'Tibetan',
            'dz': 'Dzongkha',
            
            # Pacific Languages
            'haw': 'Hawaiian',
            'mi': 'Maori',
            'sm': 'Samoan',
            'to': 'Tongan',
            'fj': 'Fijian',
            
            # Additional Languages
            'jv': 'Javanese',
            'su': 'Sundanese',
            'ceb': 'Cebuano',
            'hil': 'Hiligaynon',
            'war': 'Waray',
            'bcl': 'Bicolano',
            'pam': 'Kapampangan',
            'lb': 'Luxembourgish',
            'rm': 'Romansh',
            'fo': 'Faroese',
            'kl': 'Greenlandic'
        }
        
        # Try Gemini API first for conversational responses
        if self.gemini_model:
            try:
                logger.info(f"Using Gemini API for real-time chat: {message} (Target language: {language_names.get(target_lang, 'English')})")
                
                # Create professional conversational system prompt
                if target_lang == 'en':
                    system_prompt = """You are a professional, knowledgeable AI assistant having a natural conversation. 

Guidelines:
- Be professional yet friendly and approachable
- Provide accurate, detailed, and helpful information
- Keep responses conversational but informative (2-4 sentences)
- Use proper formatting when helpful (bullet points, bold text)
- Be engaging and show genuine interest in helping
- If asked about specific topics, provide comprehensive information
- Maintain a warm, professional tone throughout

Respond as a knowledgeable professional who genuinely wants to help."""
                    
                    full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
                else:
                    target_language_name = language_names.get(target_lang, 'English')
                    system_prompt = f"""You are a professional, knowledgeable AI assistant having a natural conversation. 

IMPORTANT: Respond ONLY in {target_language_name}.

Guidelines:
- Be professional yet friendly and approachable
- Provide accurate, detailed, and helpful information
- Keep responses conversational but informative (2-4 sentences)
- Use proper formatting when helpful
- Be engaging and show genuine interest in helping
- If asked about specific topics, provide comprehensive information
- Maintain a warm, professional tone throughout

Respond as a knowledgeable professional who genuinely wants to help."""
                    
                    full_prompt = f"{system_prompt}\n\nUser: {message}\nAssistant:"
                
                response = self.gemini_model.generate_content(full_prompt)
                
                if response and response.text:
                    logger.info("Gemini API response successful for real-time chat")
                    
                    # Clean up the response
                    cleaned_response = response.text.strip()
                    
                    # Ensure professional formatting
                    if not cleaned_response.endswith(('.', '!', '?')):
                        cleaned_response += '.'
                    
                    return cleaned_response
                else:
                    logger.warning("Gemini API returned empty response for real-time chat")
                    
            except Exception as e:
                logger.error(f"Gemini API error in real-time chat: {e}")
        
        # Enhanced fallback responses for common queries
        fallback_responses = {
            'en': {
                'greeting': "Hello! I'm here to help you with any questions or topics you'd like to discuss. What can I assist you with today?",
                'help': "I'm a knowledgeable AI assistant ready to help with a wide range of topics including education, technology, general knowledge, and more. Feel free to ask me anything!",
                'default': "I'd be happy to help you with that. Could you provide a bit more detail about what specific information you're looking for?"
            },
            'hi': {
                'greeting': "नमस्ते! मैं आपकी किसी भी प्रश्न या विषय में सहायता के लिए यहाँ हूँ। आज मैं आपकी कैसे मदद कर सकता हूँ?",
                'help': "मैं एक जानकार AI सहायक हूँ जो शिक्षा, प्रौद्योगिकी, सामान्य ज्ञान और कई अन्य विषयों में आपकी मदद कर सकता हूँ। कृपया मुझसे कुछ भी पूछें!",
                'default': "मुझे आपकी इसमें सहायता करने में खुशी होगी। क्या आप मुझे बता सकते हैं कि आप कौन सी विशेष जानकारी चाहते हैं?"
            }
        }
        
        lang_responses = fallback_responses.get(target_lang, fallback_responses['en'])
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'namaste']):
            return lang_responses['greeting']
        elif any(word in message_lower for word in ['help', 'assist', 'support']):
            return lang_responses['help']
        else:
            return lang_responses['default']

# Initialize services
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
        # Try multiple LibreTranslate servers
        self.base_urls = [
            "https://libretranslate.com",
            "https://translate.astian.org",
            "https://libretranslate.de"
        ]
        self.current_url_index = 0
        self.session = requests.Session()
        
    def get_working_url(self):
        """Test which LibreTranslate server is working"""
        # Use working LibreTranslate instances
        primary_urls = [
            "https://translate.astian.org",
            "https://libretranslate.de"
        ]
        
        for i, url in enumerate(primary_urls):
            try:
                logger.info(f"Testing LibreTranslate server: {url}")
                response = self.session.get(f"{url}/languages", timeout=10)
                if response.status_code == 200:
                    logger.info(f"Working LibreTranslate server found: {url}")
                    self.current_url_index = i
                    return url
            except Exception as e:
                logger.warning(f"LibreTranslate server {url} not working: {e}")
                continue
        
        logger.error("No working LibreTranslate servers found")
        return None
    
    def get_languages(self):
        """Get list of supported languages"""
        working_url = self.get_working_url()
        if not working_url:
            # Return fallback languages if no server is available
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
        
        try:
            response = self.session.get(f"{working_url}/languages", timeout=5)
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
        if source_lang == target_lang:
            return text
        
        # Try simple translation first for common phrases
        simple_result = self.simple_translate(text, target_lang)
        if simple_result != text:
            logger.info(f"Used simple translation: '{text}' -> '{simple_result}'")
            return simple_result
            
        # Get working URL for complex translations
        working_url = self.get_working_url()
        if not working_url:
            logger.error("No working LibreTranslate server available")
            return text
            
        try:
            logger.info(f"LibreTranslate: '{text}' from {source_lang} to {target_lang}")
            
            # Prepare request data
            request_data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            # Try JSON format first
            response = self.session.post(
                f"{working_url}/translate",
                json=request_data,
                headers={'Content-Type': 'application/json'},
                timeout=20
            )
            
            if response.status_code == 200:
                result = response.json()
                translated_text = result.get('translatedText', text)
                logger.info(f"LibreTranslate success: '{translated_text}'")
                return translated_text
            else:
                logger.warning(f"LibreTranslate HTTP {response.status_code}: {response.text}")
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            logger.warning(f"JSON request failed: {e}, trying form data...")
            
            try:
                # Fallback to form data
                logger.info("Trying form data fallback...")
                response = self.session.post(
                    f"{working_url}/translate",
                    data=request_data,
                    timeout=20
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get('translatedText', text)
                    logger.info(f"Form data success: '{translated_text}'")
                    return translated_text
                else:
                    logger.warning(f"Form data failed: HTTP {response.status_code}")
                    raise Exception(f"Form data HTTP {response.status_code}")
                
            except Exception as form_error:
                logger.error(f"Form data error: {form_error}")
                # Return original text if all methods fail
                return text
    
    def simple_translate(self, text, target_lang):
        """Enhanced simple translation with more language support"""
        text_lower = text.lower().strip()
        
        # Common translations by language
        translations = {
            'hi': {  # Hindi
                'hello': 'नमस्ते', 'hi': 'नमस्ते', 'hey': 'अरे',
                'good morning': 'सुप्रभात', 'good evening': 'शुभ संध्या',
                'thank you': 'धन्यवाद', 'thanks': 'धन्यवाद',
                'please': 'कृपया', 'yes': 'हाँ', 'no': 'नहीं',
                'how are you': 'आप कैसे हैं?', 'fine': 'ठीक है',
                'good': 'अच्छा', 'bad': 'बुरा', 'ok': 'ठीक है'
            },
            'es': {  # Spanish
                'hello': 'Hola', 'hi': 'Hola', 'hey': 'Oye',
                'good morning': 'Buenos días', 'good evening': 'Buenas tardes',
                'thank you': 'Gracias', 'thanks': 'Gracias',
                'please': 'Por favor', 'yes': 'Sí', 'no': 'No',
                'how are you': '¿Cómo estás?', 'fine': 'Bien',
                'good': 'Bueno', 'bad': 'Malo', 'ok': 'Vale'
            },
            'fr': {  # French
                'hello': 'Bonjour', 'hi': 'Salut', 'hey': 'Salut',
                'good morning': 'Bonjour', 'good evening': 'Bonsoir',
                'thank you': 'Merci', 'thanks': 'Merci',
                'please': 'S\'il vous plaît', 'yes': 'Oui', 'no': 'Non',
                'how are you': 'Comment allez-vous?', 'fine': 'Bien',
                'good': 'Bon', 'bad': 'Mauvais', 'ok': 'D\'accord'
            },
            'de': {  # German
                'hello': 'Hallo', 'hi': 'Hallo', 'hey': 'Hey',
                'good morning': 'Guten Morgen', 'good evening': 'Guten Abend',
                'thank you': 'Danke', 'thanks': 'Danke',
                'please': 'Bitte', 'yes': 'Ja', 'no': 'Nein',
                'how are you': 'Wie geht es dir?', 'fine': 'Gut',
                'good': 'Gut', 'bad': 'Schlecht', 'ok': 'Okay'
            }
        }
        
        if target_lang in translations:
            return translations[target_lang].get(text_lower, text)
        
        return text

# Image generation disabled due to dependency conflicts
class ImageGenerator:
    def __init__(self):
        self.model = None
        self.image_trigger_phrases = [
            'generate image', 'create image', 'make image', 'draw', 'generate a picture',
            'create a picture', 'make a picture', 'show me', 'visualize', 'generate art',
            'create art', 'make art', 'image of', 'picture of', 'draw me', 'create', 'generate'
        ]
        try:
            import torch
            from diffusers import StableDiffusionPipeline
            logger.info("Initializing Stable Diffusion model...")
            self.model = StableDiffusionPipeline.from_pretrained("CompVis/stable-diffusion-v1-4",
                                                                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32)
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
            logger.info("Stable Diffusion model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load Stable Diffusion model: {e}")
            self.model = None
        
    def detect_image_request(self, message):
        """Check if message is requesting image generation"""
        message_lower = message.lower()
        return any(phrase in message_lower for phrase in self.image_trigger_phrases)
    
    def extract_image_prompt(self, message):
        """Extract the actual image prompt from a message"""
        message_lower = message.lower()
        
        # Remove common image request phrases
        prompt = message_lower
        for phrase in [
            'generate image of', 'create image of', 'make image of',
            'draw a', 'generate a picture of', 'create a picture of',
            'make a picture of', 'show me a', 'visualize a',
            'generate art of', 'create art of', 'make art of',
            'image of', 'picture of', 'draw me', 'create', 'generate'
        ]:
            prompt = prompt.replace(phrase, '').strip()
        
        # Clean up the prompt
        prompt = re.sub(r'\s+', ' ', prompt).strip()
        if not prompt:
            return message  # Return original if nothing left after cleaning
        
        # Enhance the prompt for better results
        prompt = self._enhance_prompt(prompt)
        return prompt
    
    def _enhance_prompt(self, prompt):
        """Add details to improve image generation quality"""
        # Add quality boosting terms if not present
        quality_terms = [
            'highly detailed',
            'intricate details', 
            'professional lighting',
            'vibrant colors',
            'photorealistic',
            'high resolution',
            'trending on artstation',
            'masterpiece'
        ]
        
        # Don't add quality terms if prompt is already long
        if len(prompt.split()) < 10:
            selected_terms = random.sample(quality_terms, 2)
            prompt = f"{prompt}, {', '.join(selected_terms)}"
        
        return prompt
        
    def generate_image(self, prompt):
        """Generate an image from text prompt"""
        try:
            if not self.model:
                logger.warning("Image generation unavailable - model not loaded")
                return None
                
            logger.info(f"Generating image for prompt: {prompt}")
            
            # Safety check - don't generate if prompt is too short
            if len(prompt.strip()) < 3:
                logger.warning(f"Prompt too short: {prompt}")
                return None
            
            # Generate image
            image = self.model(prompt, num_inference_steps=30).images[0]
            
            # Convert PIL Image to base64
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            logger.info(f"Successfully generated image for prompt: {prompt}")
            return img_str
            
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None
    
    def voice_to_image(self, audio_file_path):
        """Generate an image from voice input"""
        try:
            # First transcribe the audio
            transcription = self.transcribe_voice_to_text(audio_file_path)
            if not transcription:
                return None, None
                
            # Extract and enhance the prompt
            prompt = self.extract_image_prompt(transcription)
            
            # Generate the image
            image = self.generate_image(prompt)
            
            return transcription, image
            
        except Exception as e:
            logger.error(f"Voice to image error: {e}")
            return None, None

# Initialize services
whisper_transcriber = WhisperTranscriber()
translate_service = LibreTranslateService()
image_generator = ImageGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/game')
@app.route('/tictactoe')  # Add alias route for /tictactoe
def game():
    return render_template('tictactoe.html')

# Endpoint to get chat history
@app.route('/get_history', methods=['GET'])
def get_history():
    session_id = get_session_id()
    history = list(chat_histories[session_id])
    return jsonify({'history': history})

# Endpoint to summarize conversation
@app.route('/summarize', methods=['GET'])
def summarize():
    session_id = get_session_id()
    history = list(chat_histories[session_id])
    if not history:
        return jsonify({'summary': 'No conversation yet.'})
    # Compose summary prompt
    convo_text = "\n".join([
        f"{msg['role'].capitalize()}: {msg['text']}" for msg in history
    ])
    prompt = f"Summarize the following conversation in 3-5 sentences, in the user's language:\n{convo_text}"
    summary = chatbot_service.get_response(prompt)
    return jsonify({'summary': summary})

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


@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id') or get_session_id()
        if session_id in chat_histories:
            chat_histories.pop(session_id, None)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
        # Handle both frontend formats
        source_lang = data.get('source_lang') or data.get('userLanguage', 'auto')
        target_lang = data.get('target_lang') or data.get('botLanguage', 'en')
        auto_translate = data.get('autoTranslate', False)
        
        logger.info(f"Received message: {message}")
        logger.info(f"Source lang: {source_lang}, Target lang: {target_lang}, Auto translate: {auto_translate}")
        
        if not message:
            emit('chat_response', {'error': 'No message provided'})
            return
            
        # Check for game commands
        message_lower = message.lower()
        
        # Game commands
        if any(cmd in message_lower for cmd in [
            'play game', 'start game', 'play tic tac toe', 'start tic tac toe',
            'begin game', 'new game', 'play', 'tictactoe', 'tic-tac-toe'
        ]):
            # Handle game start
            difficulty = 'hard' if 'hard' in message_lower else 'easy'
            socketio.emit('game_command', {'command': 'start', 'difficulty': difficulty})
            
            # Send initial response
            emit('chat_response', {
                'message': message,
                'response': f"Starting a new Tic-Tac-Toe game in {'hard' if difficulty == 'hard' else 'easy'} mode! Make your moves by saying a position (like 'center', 'top left', etc.)",
                'translated_response': '',
                'source_lang': source_lang,
                'target_lang': target_lang
            })
            return
            
        # Game move commands
        if any(word in message_lower for word in [
            'move', 'place', 'put', 'mark', 'choose', 'select',
            'top', 'middle', 'bottom', 'left', 'right', 'center'
        ]):
            socketio.emit('game_command', {'command': message})
            return
            
        # Check for image generation commands
        message_lower = message.lower()
        image_commands = [
            'draw', 'generate', 'create', 'show me', 'make', 'picture', 'image',
            'visualize', 'illustrate', 'paint', 'sketch'
        ]
        
        if any(cmd in message_lower for cmd in image_commands):
            # Extract image prompt by removing commands and cleanup
            prompt = message_lower
            for cmd in image_commands:
                prompt = re.sub(fr'{cmd}\s+(a|an|the)?\s*', '', prompt, flags=re.IGNORECASE)
            prompt = prompt.strip()
            
            if not prompt:
                explanation = "Please provide a description of what you'd like me to generate. For example: 'generate an image of a sunset over mountains'"
                emit('chat_response', {
                    'message': message,
                    'response': explanation,
                    'source_lang': source_lang,
                    'target_lang': target_lang
                })
                return
                
            try:
                # Try to generate image with local model
                image_response = image_generator.generate_image(prompt)
                if image_response:
                    # Build response based on the original command
                    if 'draw' in message_lower:
                        response = f"Here's my drawing based on your request: '{prompt}'"
                    elif 'paint' in message_lower:
                        response = f"Here's what I painted for you: '{prompt}'"
                    elif 'sketch' in message_lower:
                        response = f"Here's my sketch of: '{prompt}'"
                    else:
                        response = f"I've generated this image based on: '{prompt}'"
                    
                    # Save to chat history
                    session_id = get_session_id()
                    chat_histories[session_id].append({
                        'role': 'user',
                        'text': message,
                        'lang': source_lang,
                        'timestamp': datetime.now().isoformat()
                    })
                    chat_histories[session_id].append({
                        'role': 'bot',
                        'text': response,
                        'lang': target_lang,
                        'image': image_response,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    emit('chat_response', {
                        'message': message,
                        'response': response,
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                        'image': image_response
                    })
                else:
                    emit('chat_response', {
                        'message': message,
                        'response': "I'm having trouble generating that image right now. Could you try again with a different description?",
                        'source_lang': source_lang,
                        'target_lang': target_lang
                    })
                return
                
            except Exception as e:
                logger.error(f"Image generation error: {e}")
                emit('chat_response', {
                    'message': message,
                    'response': "I encountered an error while trying to generate your image. Please try again with a simpler description.",
                    'source_lang': source_lang,
                    'target_lang': target_lang
                })
                return
        
        # Check for image generation requests
        message_lower = message.lower()
        is_image_request = any(phrase in message_lower for phrase in [
            'generate image', 'create image', 'make image', 'draw', 'generate a picture',
            'create a picture', 'make a picture', 'show me', 'visualize', 'generate art',
            'create art', 'make art', 'image of', 'picture of'
        ])
        
        if is_image_request:
            # Extract the image prompt
            prompt = message_lower
            for phrase in ['generate image of', 'create image of', 'make image of', 
                         'draw a', 'generate a picture of', 'create a picture of',
                         'make a picture of', 'show me a', 'visualize a', 
                         'generate art of', 'create art of', 'make art of',
                         'image of', 'picture of']:
                prompt = prompt.replace(phrase, '')
            prompt = prompt.strip()
            
            try:
                # Try to generate image
                image_response = image_generator.generate_image(prompt)
                if image_response:
                    # Save to chat history
                    try:
                        session_id = get_session_id()
                        chat_histories[session_id].append({'role': 'user', 'text': message, 'lang': source_lang})
                        chat_histories[session_id].append({
                            'role': 'bot', 
                            'text': f"I've generated an image based on your request: {prompt}",
                            'lang': target_lang,
                            'image': image_response
                        })
                    except Exception as e:
                        logger.debug(f"Failed to save history: {e}")
                        
                    # Send response with image
                    emit('chat_response', {
                        'message': message,
                        'response': f"I've generated an image based on your request: {prompt}",
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                        'image': image_response
                    })
                    return
                else:
                    response = (f"I apologize, but I'm currently unable to generate images. "
                              f"This could be due to technical limitations or dependency issues. "
                              f"I can still help you with other requests!")
            except Exception as e:
                logger.error(f"Image generation error: {e}")
                response = ("I apologize, but I encountered an error while trying to generate the image. "
                          "I can still help you with other requests!")
        else:
            # Get chatbot response in the target language
            if target_lang != 'en':
                # Generate response directly in target language
                response = chatbot_service.get_response(message, target_lang)
                translated_response = response  # No translation needed since it's already in target language
                logger.info(f"Chatbot response in {target_lang}: {response}")
            else:
                # Generate response in English
                response = chatbot_service.get_response(message)
                logger.info(f"Chatbot response: {response}")
                
                # Translate response if needed and auto_translate is enabled
                translated_response = response
                if auto_translate and target_lang != 'en' and target_lang != source_lang:
                    try:
                        # For very long responses, translate just the first part for demo
                        if len(response) > 500:
                            # Split response into sentences and translate the first few
                            sentences = response.split('. ')
                            short_text = '. '.join(sentences[:3]) + '.'
                            translated_part = translate_service.translate_text(short_text, 'en', target_lang)
                            if translated_part != short_text:
                                translated_response = translated_part + f"\n\n[Full response in English follows...]\n\n{response}"
                            else:
                                translated_response = response
                        else:
                            translated_response = translate_service.translate_text(response, 'en', target_lang)
                            
                        logger.info(f"Translated response: {translated_response[:200]}...")
                    except Exception as e:
                        logger.error(f"Translation error: {e}")
                        translated_response = response
        
        emit('chat_response', {
            'message': message,
            'response': response,
            'translated_response': translated_response,
            'source_lang': source_lang,
            'target_lang': target_lang
        })

        # Save to chat history for English path
        try:
            session_id = get_session_id()
            chat_histories[session_id].append({'role': 'user', 'text': message, 'lang': source_lang})
            chat_histories[session_id].append({'role': 'bot', 'text': response, 'lang': target_lang})
        except Exception as e:
            logger.debug(f"Failed to save history: {e}")
    
    except Exception as e:
        logger.error(f"Message handling error: {e}")
        emit('chat_response', {'error': 'Failed to process message'})

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat messages from frontend"""
    # Call the same handler as 'message'
    handle_message(data)

@socketio.on('realtime_response')
def handle_realtime_response(data):
    """Handle real-time conversation messages"""
    try:
        message = data.get('message', '')
        source_lang = data.get('userLanguage', 'auto')
        target_lang = data.get('botLanguage', 'en')
        session_id = data.get('session_id', '')
        
        # Check for image or voice-to-image requests
        message_lower = message.lower()
        is_image_request = any(phrase in message_lower for phrase in [
            'generate image', 'create image', 'make image', 'draw', 'generate a picture',
            'create a picture', 'make a picture', 'show me', 'visualize', 'generate art',
            'create art', 'make art', 'image of', 'picture of'
        ])
        is_voice_to_image = any(phrase in message_lower for phrase in [
            'voice to image', 'audio to image', 'speech to image', 
            'convert my voice to image', 'convert audio to image'
        ])
        
        logger.info(f"Real-time message: {message}")
        logger.info(f"User lang: {source_lang}, Bot lang: {target_lang}")
        
        if not message:
            emit('realtime_response', {'error': 'No message provided'})
            return
        
        # Get conversational chatbot response in the target language
        if target_lang != 'en':
            # Generate response directly in target language with conversational context
            response = chatbot_service.get_realtime_response(message, target_lang)
            logger.info(f"Real-time response in {target_lang}: {response}")
            # Save to chat history
            try:
                session_key = get_session_id()
                chat_histories[session_key].append({'role': 'user', 'text': message, 'lang': source_lang})
                chat_histories[session_key].append({'role': 'bot', 'text': response, 'lang': target_lang})
            except Exception as e:
                logger.debug(f"Failed to save realtime history: {e}")
        else:
            # Generate response in English with conversational context
            response = chatbot_service.get_realtime_response(message)
            logger.info(f"Real-time response: {response}")
            try:
                session_key = get_session_id()
                chat_histories[session_key].append({'role': 'user', 'text': message, 'lang': source_lang})
                chat_histories[session_key].append({'role': 'bot', 'text': response, 'lang': target_lang})
            except Exception as e:
                logger.debug(f"Failed to save realtime history: {e}")
            
        # Emit the response back to the client
        emit('realtime_response', {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Real-time response error: {e}")
        emit('realtime_response', {'error': f'Error processing real-time message: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    logger.info('Client connected')
    emit('chat_response', {'message': 'Connected to Universal Language Support Chatbot!'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info('Client disconnected')
    session_id = get_session_id()
    if session_id in active_games:
        del active_games[session_id]

@socketio.on('start_game')
def handle_start_game(data):
    """Start a new Tic-Tac-Toe game"""
    try:
        session_id = get_session_id()
        difficulty = data.get('difficulty', 'easy')
        
        # Create new game instance
        game = TicTacToe(GameDifficulty.HARD if difficulty == 'hard' else GameDifficulty.EASY)
        active_games[session_id] = game
        
        emit('game_state', {
            'status': 'started',
            'message': f'Game started! {"Hard" if difficulty == "hard" else "Easy"} mode selected.',
            **game.get_game_state()
        })
    except Exception as e:
        logger.error(f"Start game error: {e}")
        emit('game_error', {'error': 'Failed to start game'})

@socketio.on('process_game_command')
def handle_game_command(data):
    """Process game commands from chat messages"""
    try:
        session_id = get_session_id()
        command = data.get('command', '').lower()
        language = data.get('language', 'en')
        
        # Check for game start commands
        if 'play' in command or 'start game' in command:
            difficulty = 'hard' if 'hard' in command else 'easy'
            handle_start_game({'difficulty': difficulty})
            return

        if session_id not in active_games:
            emit('game_error', {'error': 'No active game'})
            return
            
        game = active_games[session_id]
        
        # Process move command
        position = game.parse_move(command, language)
        if position >= 0:
            success, message = game.make_move(position)
            if success:
                emit('game_state', {
                    'status': 'move_made',
                    'message': message,
                    **game.get_game_state()
                })
                
                # Make bot move if game not over
                if not game.game_over and game.current_player == 'O':
                    success, bot_message = game.bot_move()
                    if success:
                        emit('game_state', {
                            'status': 'bot_moved',
                            'message': bot_message,
                            **game.get_game_state()
                        })
            else:
                emit('game_error', {'error': message})
        else:
            emit('game_error', {'error': 'Invalid command'})
            
    except Exception as e:
        logger.error(f"Game command error: {e}")
        emit('game_error', {'error': 'Failed to process command'})

@socketio.on('start_game')
def handle_start_game(data):
    """Start a new Tic-Tac-Toe game"""
    try:
        session_id = get_session_id()
        difficulty = data.get('difficulty', 'easy')
        
        # Create new game instance
        game = TicTacToe(GameDifficulty.HARD if difficulty == 'hard' else GameDifficulty.EASY)
        active_games[session_id] = game
        
        # Emit initial game state
        emit('game_state', {
            'status': 'started',
            'message': 'Game started! You are X, make your move!',
            **game.get_game_state()
        })
        
    except Exception as e:
        logger.error(f"Start game error: {e}")
        emit('game_error', {'error': 'Failed to start game'})

@socketio.on('make_move')
def handle_make_move(data):
    """Handle player move in Tic-Tac-Toe"""
    try:
        session_id = get_session_id()
        if session_id not in active_games:
            emit('game_error', {'error': 'No active game'})
            return
            
        game = active_games[session_id]
        move = data.get('move')  # Can be position index (0-8) or text description
        user_lang = data.get('userLanguage', 'en')
        
        # Parse and validate move
        if isinstance(move, str):
            position = game.parse_move(move, user_lang)
        else:
            position = move
            
        if position == -1:
            emit('game_error', {'error': 'Invalid move'})
            return
            
        # Make player's move
        success, message = game.make_move(position)
        if not success:
            emit('game_error', {'error': message})
            return
            
        # Send updated state after player's move
        emit('game_state', {
            'status': 'move_made',
            'message': message,
            **game.get_game_state()
        })
        
        # If game is not over and it's bot's turn, make bot move
        if not game.game_over and game.current_player == 'O':
            success, bot_message = game.bot_move()
            if success:
                emit('game_state', {
                    'status': 'bot_moved',
                    'message': bot_message,
                    **game.get_game_state()
                })
        
    except Exception as e:
        logger.error(f"Make move error: {e}")
        emit('game_error', {'error': 'Failed to make move'})

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        
        if not prompt:
            return jsonify({'error': 'No prompt provided'}), 400
        
        # Generate image using Stable Diffusion
        image_base64 = image_generator.generate_image(prompt)
        
        if image_base64:
            return jsonify({
                'success': True,
                'image': image_base64,
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
            
            # First transcribe audio to text
            transcription = image_generator.transcribe_voice_to_text(tmp_file.name)
            
            # Clean up temporary file
            os.unlink(tmp_file.name)
            
            if not transcription:
                return jsonify({'error': 'Failed to transcribe audio'}), 500
            
            # Generate image from transcribed text
            image_base64 = image_generator.generate_image(transcription)
            
            if image_base64:
                return jsonify({
                    'success': True,
                    'image': image_base64,
                    'transcription': transcription,
                    'prompt': transcription
                })
            else:
                return jsonify({'error': 'Failed to generate image'}), 500
                
    except Exception as e:
        logger.error(f"Voice-to-image error: {e}")
        return jsonify({'error': str(e)}), 500

# Room Management Functions
def generate_room_pin():
    """Generate a unique 6-digit room PIN"""
    while True:
        pin = str(random.randint(100000, 999999))
        if pin not in rooms:
            return pin

def cleanup_expired_rooms():
    """Remove rooms that have been inactive for more than 1 hour"""
    current_time = time.time()
    expired_rooms = []
    
    for pin, room in rooms.items():
        if current_time - room['last_activity'] > 3600:  # 1 hour
            expired_rooms.append(pin)
    
    for pin in expired_rooms:
        # Remove users from user_rooms mapping
        for user_id in rooms[pin]['users']:
            user_rooms.pop(user_id, None)
        # Remove room
        rooms.pop(pin, None)
        logger.info(f"Expired room {pin} removed")

# Room API Endpoints
@app.route('/api/rooms/create', methods=['POST'])
def create_room():
    """Create a new chat room"""
    try:
        data = request.get_json() or {}
        user_name = data.get('name', 'Anonymous')
        user_language = data.get('language', 'en')
        user_id = get_session_id()
        
        # Clean up expired rooms first
        cleanup_expired_rooms()
        
        # Generate unique PIN
        room_pin = generate_room_pin()
        
        # Create room
        rooms[room_pin] = {
            'users': {
                user_id: {
                    'name': user_name,
                    'language': user_language,
                    'joined_at': time.time(),
                    'is_creator': True
                }
            },
            'messages': [],
            'created_at': time.time(),
            'last_activity': time.time()
        }
        
        # Map user to room
        user_rooms[user_id] = room_pin
        
        logger.info(f"Room {room_pin} created by {user_name}")
        
        return jsonify({
            'success': True,
            'room_pin': room_pin,
            'user_id': user_id,
            'message': f'Room created successfully! Share PIN {room_pin} with others.'
        })
        
    except Exception as e:
        logger.error(f"Room creation error: {e}")
        return jsonify({'error': 'Failed to create room'}), 500

@app.route('/api/rooms/join', methods=['POST'])
def join_room():
    """Join an existing chat room"""
    try:
        data = request.get_json()
        room_pin = data.get('pin', '').strip()
        user_name = data.get('name', 'Anonymous')
        user_language = data.get('language', 'en')
        user_id = get_session_id()
        
        if not room_pin or len(room_pin) != 6:
            return jsonify({'error': 'Invalid PIN format'}), 400
        
        # Clean up expired rooms first
        cleanup_expired_rooms()
        
        if room_pin not in rooms:
            return jsonify({'error': 'Room not found or expired'}), 404
        
        # Add user to room
        rooms[room_pin]['users'][user_id] = {
            'name': user_name,
            'language': user_language,
            'joined_at': time.time(),
            'is_creator': False
        }
        
        # Update room activity
        rooms[room_pin]['last_activity'] = time.time()
        
        # Map user to room
        user_rooms[user_id] = room_pin
        
        logger.info(f"User {user_name} joined room {room_pin}")
        
        # Get room info
        room_info = {
            'room_pin': room_pin,
            'users': list(rooms[room_pin]['users'].values()),
            'message_count': len(rooms[room_pin]['messages'])
        }
        
        return jsonify({
            'success': True,
            'room_info': room_info,
            'user_id': user_id,
            'message': f'Successfully joined room {room_pin}!'
        })
        
    except Exception as e:
        logger.error(f"Room join error: {e}")
        return jsonify({'error': 'Failed to join room'}), 500

@app.route('/api/rooms/leave', methods=['POST'])
def leave_room():
    """Leave current room"""
    try:
        user_id = get_session_id()
        
        if user_id not in user_rooms:
            return jsonify({'error': 'Not in any room'}), 400
        
        room_pin = user_rooms[user_id]
        
        if room_pin in rooms and user_id in rooms[room_pin]['users']:
            # Remove user from room
            user_name = rooms[room_pin]['users'][user_id]['name']
            rooms[room_pin]['users'].pop(user_id, None)
            rooms[room_pin]['last_activity'] = time.time()
            
            # Remove user from mapping
            user_rooms.pop(user_id, None)
            
            # If room is empty, remove it
            if not rooms[room_pin]['users']:
                rooms.pop(room_pin, None)
                logger.info(f"Empty room {room_pin} removed")
            
            logger.info(f"User {user_name} left room {room_pin}")
        
        return jsonify({
            'success': True,
            'message': 'Left room successfully'
        })
        
    except Exception as e:
        logger.error(f"Leave room error: {e}")
        return jsonify({'error': 'Failed to leave room'}), 500

# Room Socket Events
@socketio.on('room_message')
def handle_room_message(data):
    """Handle messages in chat rooms with translation"""
    try:
        user_id = get_session_id()
        message = data.get('message', '').strip()
        
        logger.info(f"Room message received from {user_id}: {message}")
        
        if not message:
            logger.error('Empty message received')
            emit('room_error', {'error': 'Empty message'})
            return
        
        if user_id not in user_rooms:
            logger.error(f'User {user_id} not in any room')
            emit('room_error', {'error': 'Not in any room'})
            return
        
        room_pin = user_rooms[user_id]
        logger.info(f'User {user_id} sending message to room {room_pin}')
        
        if room_pin not in rooms:
            logger.error(f'Room {room_pin} no longer exists')
            emit('room_error', {'error': 'Room no longer exists'})
            return
        
        # Get sender info
        sender = rooms[room_pin]['users'][user_id]
        sender_language = sender['language']
        
        # Create message object
        message_obj = {
            'id': str(uuid.uuid4()),
            'sender_id': user_id,
            'sender_name': sender['name'],
            'original_text': message,
            'original_language': sender_language,
            'timestamp': time.time(),
            'translations': {}
        }
        
        # Create translations for ALL users in the room
        logger.info(f"Creating translations for {len(rooms[room_pin]['users'])} users")
        
        for uid, user_info in rooms[room_pin]['users'].items():
            target_lang = user_info['language']
            user_name = user_info['name']
            
            logger.info(f"Processing translation for user {user_name} ({uid}) - language: {target_lang}")
            
            if sender_language == target_lang:
                # Same language, no translation needed
                message_obj['translations'][target_lang] = message
                logger.info(f"Same language ({target_lang}), using original: '{message}'")
            else:
                # Translate message
                try:
                    logger.info(f"Translating '{message}' from {sender_language} to {target_lang} for {user_name}")
                    
                    translated = translate_service.translate_text(message, sender_language, target_lang)
                    
                    if translated and translated.strip() and translated != message:
                        message_obj['translations'][target_lang] = translated
                        logger.info(f"Translation success for {user_name}: '{message}' -> '{translated}'")
                    else:
                        # Use simple translation as fallback
                        simple_translated = translate_service.simple_translate(message, target_lang)
                        message_obj['translations'][target_lang] = simple_translated
                        logger.info(f"Simple translation for {user_name}: '{message}' -> '{simple_translated}'")
                        
                except Exception as e:
                    logger.error(f"Translation error for {user_name} ({sender_language}->{target_lang}): {e}")
                    # Use simple translation as final fallback
                    fallback = translate_service.simple_translate(message, target_lang)
                    message_obj['translations'][target_lang] = fallback
                    logger.info(f"Error fallback for {user_name}: '{message}' -> '{fallback}'")
        
        logger.info(f"Final translations created: {message_obj['translations']}")
        
        # Add message to room
        rooms[room_pin]['messages'].append(message_obj)
        rooms[room_pin]['last_activity'] = time.time()
        
        # Keep only last 100 messages per room
        if len(rooms[room_pin]['messages']) > 100:
            rooms[room_pin]['messages'] = rooms[room_pin]['messages'][-100:]
        
        # Broadcast single message to all users (they'll see their translated version)
        logger.info(f'Broadcasting message to {len(rooms[room_pin]["users"])} users in room {room_pin}')
        
        # Create broadcast message with all translations
        broadcast_data = {
            'message_id': message_obj['id'],
            'sender_name': sender['name'],
            'sender_id': user_id,
            'original_message': message,
            'sender_language': sender_language,
            'timestamp': message_obj['timestamp'],
            'room_pin': room_pin,
            'translations': message_obj['translations'],
            'users': {uid: {'language': user_info['language'], 'name': user_info['name']} 
                     for uid, user_info in rooms[room_pin]['users'].items()}
        }
        
        logger.info(f"Broadcasting message with translations: {broadcast_data['translations']}")
        
        # Broadcast to all users with debugging
        logger.info(f'About to broadcast message to room {room_pin}')
        logger.info(f'Message data: {broadcast_data["message_id"]} - {broadcast_data["original_message"]}')
        
        # Broadcast to all connected clients
        socketio.emit('room_message_received', broadcast_data, broadcast=True)
        
        logger.info(f'Message broadcast completed for room {room_pin}')
        
        logger.info(f"Room message sent in {room_pin}: {message[:50]}...")
        
    except Exception as e:
        logger.error(f"Room message error: {e}")
        emit('room_error', {'error': 'Failed to send message'})

@socketio.on('join_room_socket')
def handle_join_room_socket(data):
    """Handle socket room joining for real-time updates"""
    try:
        user_id = get_session_id()
        
        if user_id in user_rooms:
            room_pin = user_rooms[user_id]
            
            # Send room info
            if room_pin in rooms:
                emit('room_joined', {
                    'room_pin': room_pin,
                    'users': list(rooms[room_pin]['users'].values()),
                    'recent_messages': rooms[room_pin]['messages'][-20:]  # Last 20 messages
                })
        
    except Exception as e:
        logger.error(f"Socket room join error: {e}")
        emit('room_error', {'error': 'Failed to join room socket'})

if __name__ == '__main__':
    logger.info("Starting Universal Language Support Chatbot with Virtual Rooms...")
    logger.info("Visit http://localhost:5000 to use the chatbot")
    logger.info("Features: Multilingual Chat, Voice Support, Image Generation, Virtual Rooms")
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
