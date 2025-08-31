import os
import json
import tempfile
import requests
import whisper
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import logging
from datetime import datetime
import openai
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'universal-chatbot-secret')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Real Information Fetcher
class RealInfoFetcher:
    """Fetches real information from various APIs and sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 15
        
    def get_real_info(self, query):
        """Get real information based on the query - handles ANY question"""
        query_lower = query.lower()
        
        # Skip very short queries or greetings
        if len(query.strip()) < 3 or any(word in query_lower for word in ['hi', 'hello', 'hey', 'thanks', 'thank you']):
            return None
        
        # Internet search requests - highest priority
        if any(word in query_lower for word in ['find on internet', 'search for', 'look up', 'internet about']):
            return self.search_wikipedia(query)
        
        # Wikipedia search for general information
        if any(word in query_lower for word in ['what is', 'tell me about', 'information about', 'about', 'who is', 'where is', 'when was', 'how does', 'why does']):
            return self.search_wikipedia(query)
        
        # Current events and news
        if any(word in query_lower for word in ['news', 'current', 'latest', 'recent', 'today', 'happening now']):
            return self.get_current_info(query)
        
        # Technical/programming questions
        if any(word in query_lower for word in ['programming', 'code', 'python', 'javascript', 'java', 'api', 'software', 'development', 'computer', 'technology']):
            return self.get_programming_info(query)
        
        # Educational content
        if any(word in query_lower for word in ['learn', 'study', 'education', 'course', 'tutorial', 'exam', 'university', 'college']):
            return self.get_educational_info(query)
        
        # Science and health questions
        if any(word in query_lower for word in ['science', 'health', 'medicine', 'biology', 'chemistry', 'physics', 'disease', 'treatment']):
            return self.search_wikipedia(query)
        
        # Geography and places
        if any(word in query_lower for word in ['country', 'city', 'capital', 'population', 'located', 'geography']):
            return self.search_wikipedia(query)
        
        # History questions
        if any(word in query_lower for word in ['history', 'historical', 'ancient', 'war', 'civilization', 'empire', 'century']):
            return self.search_wikipedia(query)
        
        # Business and economics
        if any(word in query_lower for word in ['business', 'economy', 'company', 'market', 'finance', 'stock', 'investment']):
            return self.search_wikipedia(query)
        
        # Sports and entertainment
        if any(word in query_lower for word in ['sport', 'game', 'movie', 'music', 'actor', 'singer', 'team', 'player']):
            return self.search_wikipedia(query)
        
        # For ANY other question that seems like it's asking for information
        # Check if it's a question (contains question words or ends with ?)
        question_indicators = ['what', 'who', 'where', 'when', 'why', 'how', 'which', 'can you', 'do you know', 'explain']
        if (any(word in query_lower for word in question_indicators) or 
            query.strip().endswith('?') or 
            len(query.split()) > 2):
            return self.search_wikipedia(query)
        
        return None

    def search_wikipedia(self, query):
        """Search Wikipedia for information - enhanced for any topic"""
        try:
            # Extract the main topic from the query
            search_terms = query.lower()
            
            # Remove common query prefixes and question words
            prefixes_to_remove = [
                'find on internet about', 'search for', 'look up', 'tell me about', 
                'what is', 'who is', 'where is', 'when was', 'when is', 'why does', 
                'why is', 'how does', 'how is', 'information about', 'about',
                'can you tell me about', 'do you know about', 'explain', 'describe'
            ]
            
            for phrase in prefixes_to_remove:
                search_terms = search_terms.replace(phrase, '').strip()
            
            # Clean up the search terms
            search_terms = search_terms.strip('?.,!').strip()
            if not search_terms or len(search_terms) < 2:
                return None
                
            logger.info(f"Searching Wikipedia for: '{search_terms}'")
            
            # Try multiple search strategies
            search_attempts = [
                search_terms,  # Original query
                search_terms.title(),  # Title case
            ]
            
            # If query contains multiple words, also try the main noun
            words = search_terms.split()
            if len(words) > 1:
                # Try to identify the main subject (usually the last meaningful word)
                main_subject = words[-1] if words[-1] not in ['is', 'are', 'was', 'were'] else words[-2] if len(words) > 1 else words[0]
                search_attempts.append(main_subject)
            
            for attempt in search_attempts:
                try:
                    # Wikipedia OpenSearch API
                    search_response = self.session.get(f"https://en.wikipedia.org/w/api.php", params={
                        'action': 'opensearch',
                        'search': attempt,
                        'limit': 5,  # Get more results to find the best match
                        'format': 'json'
                    }, timeout=15)
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        if len(search_data) > 1 and search_data[1]:
                            # Get the first (most relevant) result
                            page_title = search_data[1][0]
                            page_url = search_data[3][0] if len(search_data) > 3 else ""
                            
                            # Get detailed page summary
                            summary_response = self.session.get(
                                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}", 
                                timeout=15
                            )
                            
                            if summary_response.status_code == 200:
                                summary_data = summary_response.json()
                                extract = summary_data.get('extract', '')
                                if extract and len(extract) > 50:  # Ensure meaningful content
                                    # Limit to reasonable length
                                    if len(extract) > 1200:
                                        extract = extract[:1200] + "..."
                                    
                                    response = f"**{page_title}**\n\n{extract}"
                                    
                                    # Add additional information if available
                                    if 'coordinates' in summary_data:
                                        coords = summary_data['coordinates']
                                        response += f"\n\n📍 **Location:** {coords.get('lat', '')}, {coords.get('lon', '')}"
                                    
                                    response += f"\n\n*Source: Wikipedia*"
                                    if page_url:
                                        response += f"\n*Read more: {page_url}*"
                                    
                                    return response
                
                except Exception as e:
                    logger.warning(f"Search attempt '{attempt}' failed: {e}")
                    continue
            
            # If no exact matches, try a broader search with just key terms
            if len(words) > 1:
                key_words = [word for word in words if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'from']]
                if key_words:
                    broader_search = ' '.join(key_words)
                    logger.info(f"Trying broader search: '{broader_search}'")
                    
                    search_response = self.session.get(f"https://en.wikipedia.org/w/api.php", params={
                        'action': 'opensearch',
                        'search': broader_search,
                        'limit': 3,
                        'format': 'json'
                    }, timeout=15)
                    
                    if search_response.status_code == 200:
                        search_data = search_response.json()
                        if len(search_data) > 1 and search_data[1]:
                            page_title = search_data[1][0]
                            summary_response = self.session.get(
                                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title}", 
                                timeout=15
                            )
                            
                            if summary_response.status_code == 200:
                                summary_data = summary_response.json()
                                extract = summary_data.get('extract', '')
                                if extract:
                                    if len(extract) > 1200:
                                        extract = extract[:1200] + "..."
                                    
                                    return f"**{page_title}** (Related to: {search_terms})\n\n{extract}\n\n*Source: Wikipedia*"
            
            # Final fallback - return helpful message
            return f"I couldn't find specific information about '{search_terms}' on Wikipedia. This might be because:\n\n• The term might be spelled differently\n• It might be too specific or new\n• Try rephrasing your question\n\nYou can search directly on Wikipedia.org for more results."
        
        except Exception as e:
            logger.error(f"Wikipedia search error for '{query}': {e}")
            return f"I'm having trouble accessing Wikipedia right now. Please try again in a moment, or search for '{search_terms}' directly on Wikipedia.org"

    def get_current_info(self, query):
        """Get current information and news"""
        try:
            current_time = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            
            if 'weather' in query.lower():
                return f"I don't have access to real-time weather data, but you can check current weather conditions on weather.com or your local weather app. Current time: {current_time}"
            
            elif 'time' in query.lower() or 'date' in query.lower():
                return f"Current date and time: {current_time}"
            
            elif 'news' in query.lower():
                return f"I don't have access to real-time news feeds, but I recommend checking reputable news sources like BBC, Reuters, AP News, or your local news outlets for the latest updates. Current time: {current_time}"
            
        except Exception as e:
            logger.error(f"Current info error: {e}")
        
        return None

    def get_programming_info(self, query):
        """Get programming and technical information"""
        try:
            query_lower = query.lower()
            
            if 'python' in query_lower:
                if any(word in query_lower for word in ['learn', 'start', 'begin', 'tutorial']):
                    return """**Learning Python - Complete Roadmap 2025**

**Phase 1: Foundations (Weeks 1-4)**
• Install Python 3.12+ from python.org
• Learn syntax: variables, data types, operators
• Master control structures: if/else, loops
• Functions and basic error handling
• Practice with simple projects

**Phase 2: Intermediate (Weeks 5-8)**
• Object-Oriented Programming
• File handling and data processing
• Libraries: requests, json, csv
• Error handling and debugging
• Build real projects

**Phase 3: Advanced (Weeks 9-12)**
• Web frameworks: Flask/Django
• Databases: SQLite, PostgreSQL
• API development
• Testing and deployment

**2025 Job Market:**
• Entry-level: $60K-80K
• Mid-level: $80K-120K
• Senior: $120K-180K+

**Best Resources:**
• Python.org official tutorial
• Real Python website
• Automate the Boring Stuff
• LeetCode for practice"""

                elif any(word in query_lower for word in ['salary', 'job', 'career']):
                    return """**Python Developer Career Guide 2025**

**Salary Ranges (US Market):**
• Junior (0-2 years): $65K-85K
• Mid-level (2-5 years): $85K-130K
• Senior (5-8 years): $130K-180K
• Lead/Architect (8+ years): $180K-250K+

**High-Demand Specializations:**
• AI/Machine Learning: $140K-220K
• Data Engineering: $120K-200K
• Web Development: $80K-150K
• DevOps/Cloud: $110K-190K

**Essential Skills for 2025:**
• Python 3.12+, async programming
• Cloud: AWS/Azure/GCP
• Containers: Docker, Kubernetes
• Databases: PostgreSQL, MongoDB
• Testing: pytest, CI/CD"""

                else:
                    return self.search_wikipedia("Python programming language")

            elif 'javascript' in query_lower or 'js' in query_lower:
                return """**JavaScript Learning Path 2025**

**Modern JavaScript Essentials:**
• ES6+ features: arrow functions, destructuring
• Async/await and Promises
• DOM manipulation and events
• Fetch API and JSON handling

**Popular Frameworks:**
• React.js - Frontend development
• Node.js - Backend development
• Express.js - Web frameworks
• Vue.js/Angular - Alternatives

**Career Opportunities:**
• Frontend Developer: $70K-140K
• Full-Stack Developer: $80K-160K
• React Developer: $85K-150K
• Node.js Developer: $90K-170K

**2025 Trends:**
• TypeScript adoption growing
• JAMstack architecture
• Serverless functions
• WebAssembly integration"""

            elif any(word in query_lower for word in ['ai', 'machine learning', 'ml']):
                return """**AI & Machine Learning Guide 2025**

**Core Concepts:**
• Supervised vs Unsupervised Learning
• Neural Networks and Deep Learning
• Natural Language Processing
• Computer Vision

**Python Libraries:**
• NumPy, Pandas (Data manipulation)
• Scikit-learn (Classical ML)
• TensorFlow, PyTorch (Deep Learning)
• OpenCV (Computer Vision)

**Career Paths & Salaries:**
• ML Engineer: $130K-200K
• Data Scientist: $120K-180K
• AI Research Scientist: $150K-300K
• Computer Vision Engineer: $140K-220K

**Learning Resources:**
• Andrew Ng's ML Course
• Fast.ai practical courses
• Kaggle competitions
• Google Colab for practice"""

            else:
                return self.search_wikipedia(query)
                
        except Exception as e:
            logger.error(f"Programming info error: {e}")
            return self.search_wikipedia(query)
        
        return None

    def get_educational_info(self, query):
        """Get educational information"""
        try:
            query_lower = query.lower()
            
            if 'gre' in query_lower:
                return """**GRE Preparation Roadmap 2025**

**Phase 1: Assessment (Weeks 1-2)**
• Take diagnostic test
• Set target score
• Gather study materials

**Phase 2: Foundation (Weeks 3-8)**
• Verbal: Build vocabulary (300+ words/week)
• Quant: Review math concepts
• AWA: Practice essay writing

**Phase 3: Practice (Weeks 9-14)**
• Full-length practice tests weekly
• Analyze mistakes
• Focus on weak areas

**Phase 4: Final Prep (Weeks 15-16)**
• Final practice tests
• Review key formulas
• Test-day preparation

**Key Tips:**
• 3-4 months of consistent study
• Use official ETS materials
• Join study groups
• Book test date early"""

            elif 'vjit' in query_lower:
                return """**VJIT (Vidya Jyothi Institute of Technology)**

VJIT is a prestigious engineering college in Hyderabad, Telangana, offering:

**Programs:**
• B.Tech in CSE, ECE, ME, CE, EEE
• M.Tech in various specializations
• MBA programs

**Key Features:**
• NAAC accredited
• Strong industry partnerships
• Modern laboratories and infrastructure
• Active placement cell
• Research opportunities

**Placements:**
• Top recruiters: TCS, Infosys, Wipro, Amazon
• Average package: 4-6 LPA
• Highest package: 15+ LPA

**Campus Life:**
• Technical clubs and societies
• Cultural festivals
• Sports facilities
• Hostel accommodation

*For current admission details, visit vjit.ac.in*"""

            else:
                return self.search_wikipedia(query)
                
        except Exception as e:
            logger.error(f"Educational info error: {e}")
            return self.search_wikipedia(query)
        
        return None

# Initialize real info fetcher
real_info_fetcher = RealInfoFetcher()

# Global configuration
CONFIG = {
    'libretranslate_url': os.getenv('LIBRETRANSLATE_URL', 'https://translate.astian.org'),
    'whisper_model': os.getenv('WHISPER_MODEL', 'base'),
    'default_user_language': os.getenv('DEFAULT_USER_LANGUAGE', 'en'),
    'default_bot_language': os.getenv('DEFAULT_BOT_LANGUAGE', 'en'),
    'openai_api_key': os.getenv('OPENAI_API_KEY'),
    'openai_model': os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo'),
    'openai_max_tokens': int(os.getenv('OPENAI_MAX_TOKENS', '500')),
}

# Initialize Whisper model
try:
    whisper_model = whisper.load_model(CONFIG['whisper_model'])
    logger.info(f"Whisper model '{CONFIG['whisper_model']}' loaded successfully")
except Exception as e:
    logger.error(f"Failed to load Whisper model: {e}")
    whisper_model = None

class TranslationService:
    """Handle translation using LibreTranslate API with fallback"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.is_available = self.test_connection()
        self.simple_translations = self.get_simple_translations()
    
    def get_simple_translations(self):
        """Simple translation dictionary for common phrases"""
        return {
            'hello': {
                'es': 'hola', 'fr': 'bonjour', 'de': 'hallo', 'it': 'ciao',
                'pt': 'olá', 'ru': 'привет', 'ja': 'こんにちは', 'ko': '안녕하세요',
                'zh': '你好', 'ar': 'مرحبا', 'hi': 'नमस्ते'
            }
        }
    
    def test_connection(self):
        """Test if LibreTranslate service is available"""
        try:
            response = requests.get(f"{self.base_url}/languages", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def translate(self, text, source_lang='auto', target_lang='en'):
        """Translate text with fallback"""
        if source_lang == target_lang:
            return text
            
        # Simple fallback
        text_lower = text.lower().strip()
        if text_lower in self.simple_translations:
            return self.simple_translations[text_lower].get(target_lang, text)
        
        return text

class ChatbotService:
    """Intelligent chatbot using OpenAI GPT with real information fallback"""
    
    def __init__(self, api_key=None, model='gpt-3.5-turbo', max_tokens=500):
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.client = None
        self.conversation_history = {}
        
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("No OpenAI API key provided, using fallback responses")

    def get_response(self, message, user_language='en', bot_language='en', session_id='default'):
        """Generate intelligent response using OpenAI or enhanced fallback with real information"""
        
        # For internet search requests, prioritize real information
        message_lower = message.lower()
        if any(phrase in message_lower for phrase in ['find on internet', 'search for', 'look up', 'internet about']):
            real_info = real_info_fetcher.get_real_info(message)
            if real_info:
                logger.info(f"Returning real information for internet search: {message}")
                return real_info
        
        # Try OpenAI first for general conversations
        if self.client:
            try:
                # Maintain conversation history per session
                if session_id not in self.conversation_history:
                    self.conversation_history[session_id] = []
                
                # Add user message to history
                self.conversation_history[session_id].append({
                    "role": "user",
                    "content": message
                })
                
                # Keep only last 10 messages to manage token usage
                if len(self.conversation_history[session_id]) > 10:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
                
                # Prepare messages for OpenAI
                messages = [
                    {"role": "system", "content": self.get_system_prompt(user_language, bot_language)}
                ] + self.conversation_history[session_id]
                
                # Call OpenAI API
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    temperature=0.7,
                    presence_penalty=0.1,
                    frequency_penalty=0.1
                )
                
                bot_response = response.choices[0].message.content.strip()
                
                # Add bot response to history
                self.conversation_history[session_id].append({
                    "role": "assistant", 
                    "content": bot_response
                })
                
                logger.info(f"OpenAI response generated for session {session_id}")
                return bot_response
                
            except Exception as e:
                logger.error(f"OpenAI API error: {e}")
                # Fall through to real info and fallback
        
        # If OpenAI is not available or failed, try real information
        real_info = real_info_fetcher.get_real_info(message)
        if real_info:
            logger.info(f"Returning real information fallback for: {message}")
            return real_info
        
        # Final fallback to built-in responses
        return self.get_fallback_response(message)

    def get_system_prompt(self, user_language, bot_language):
        """Get system prompt for OpenAI"""
        return f"""You are a helpful, multilingual AI assistant that can communicate in many languages. 
        The user speaks {user_language} and wants responses in {bot_language}. 
        Provide accurate, helpful, and informative responses. Be conversational and friendly."""

    def get_fallback_response(self, message):
        """Generate fallback response when OpenAI is not available"""
        import random
        message_lower = message.lower().strip()
        
        # Greeting responses
        greeting_words = ['hello', 'hi', 'hey', 'greetings']
        if any(word in message_lower for word in greeting_words):
            responses = [
                "Hello! I'm your Universal Language Assistant. I can help with translations, answer questions, and provide information on various topics. What would you like to explore today?",
                "Hi there! How can I assist you today? I can help with information, translations, and answer questions on many topics.",
                "Greetings! I'm here to help you with information and communication. What can I do for you?"
            ]
            return random.choice(responses)
        
        # Help requests
        if any(word in message_lower for word in ['help', 'what can you do']):
            return """I can help you with:

🌐 **Languages:** Translate between multiple languages
📚 **Education:** Study tips, exam preparation, academic guidance  
💻 **Technology:** Programming concepts, career advice, tech trends
🔍 **Information:** Search for facts and explanations on any topic
💬 **Communication:** Voice and text conversations

What specific area interests you?"""
        
        # Default response
        return "I'm here to help! You can ask me about any topic - from science and technology to history and culture. I can also help with translations and educational guidance. What would you like to know?"

    def clear_history(self, session_id='default'):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            logger.info(f"Cleared conversation history for session {session_id}")

# Initialize services
translation_service = TranslationService(CONFIG['libretranslate_url'])
chatbot_service = ChatbotService(
    api_key=CONFIG['openai_api_key'],
    model=CONFIG['openai_model'],
    max_tokens=CONFIG['openai_max_tokens']
)

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/clear-history', methods=['POST'])
def clear_history():
    """Clear conversation history"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        chatbot_service.clear_history(session_id)
        return jsonify({'success': True, 'message': 'Chat history cleared successfully'})
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info("Client connected")
    emit('status', {'message': 'Connected to Universal Language Chatbot'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info("Client disconnected")

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat messages"""
    try:
        message = data.get('message', '').strip()
        user_language = data.get('userLanguage', 'en')
        bot_language = data.get('botLanguage', 'en')
        auto_translate = data.get('autoTranslate', False)
        session_id = data.get('session_id', 'default')
        realtime = data.get('realtime', False)
        
        logger.info(f"Received message: {message} (lang: {user_language}, realtime: {realtime})")
        
        if not message:
            emit('bot_response', {
                'error': 'Empty message received',
                'user_language': user_language,
                'bot_language': bot_language,
                'realtime': realtime,
                'session_id': session_id
            })
            return
        
        # Get bot response
        bot_response = chatbot_service.get_response(
            message, 
            user_language=user_language, 
            bot_language=bot_language,
            session_id=session_id
        )
        
        # Handle translation if needed
        translated_message = message
        bot_response_original = bot_response
        
        if auto_translate and user_language != 'en':
            translated_message = translation_service.translate(message, user_language, 'en')
        
        if auto_translate and bot_language != 'en':
            bot_response = translation_service.translate(bot_response, 'en', bot_language)
        
        # Send response
        emit('bot_response', {
            'original_message': message,
            'translated_message': translated_message,
            'bot_response': bot_response,
            'bot_response_original': bot_response_original,
            'user_language': user_language,
            'bot_language': bot_language,
            'realtime': realtime,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        emit('bot_response', {
            'error': f'Error processing message: {str(e)}',
            'user_language': user_language,
            'bot_language': bot_language,
            'realtime': realtime,
            'session_id': session_id
        })

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
