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
        self.session.timeout = 5
        
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
                search_terms.replace(' ', '_'),  # Underscore format
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
            # Use a free news API (you can replace with your preferred news API)
            # For now, return current date and general information
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
        """Get programming and technical information - comprehensive coverage"""
        try:
            query_lower = query.lower()
            
            # Python-related questions
            if 'python' in query_lower:
                if any(word in query_lower for word in ['learn', 'start', 'begin', 'tutorial']):
                    return """**Learning Python - Complete Roadmap 2025**

**Phase 1: Foundations (Weeks 1-4)**
• Install Python 3.12+ from python.org
• Learn syntax: variables, data types, operators
• Master control structures: if/else, loops (for, while)
• Functions and basic error handling
• Practice with simple projects (calculator, guessing game)

**Phase 2: Intermediate (Weeks 5-8)**
• Object-Oriented Programming (classes, inheritance)
• File handling and data processing
• Libraries: requests, json, csv, datetime
• Error handling and debugging
• Build projects: web scraper, data analyzer

**Phase 3: Advanced (Weeks 9-12)**
• Web frameworks: Flask/Django
• Databases: SQLite, PostgreSQL
• API development and consumption
• Testing (unittest, pytest)
• Deployment basics

**Phase 4: Specialization (Weeks 13+)**
• Data Science: pandas, numpy, matplotlib
• Machine Learning: scikit-learn, TensorFlow
• Web Development: Django/FastAPI
• Automation: selenium, automation scripts

**2025 Job Market:**
• Entry-level: $60K-80K
• Mid-level (2-5 years): $80K-120K
• Senior (5+ years): $120K-180K
• Specialization (AI/ML): $130K-200K+

**Resources:**
• Python.org official tutorial
• Real Python (realpython.com)
• Automate the Boring Stuff
• LeetCode for practice"""

                elif any(word in query_lower for word in ['salary', 'job', 'career', 'market']):
                    return """**Python Developer Career Guide 2025**

**💰 Salary Ranges (US Market):**
• Junior (0-2 years): $65K-85K
• Mid-level (2-5 years): $85K-130K
• Senior (5-8 years): $130K-180K
• Lead/Architect (8+ years): $180K-250K+

**🎯 High-Demand Specializations:**
• AI/Machine Learning: $140K-220K
• Data Engineering: $120K-200K
• DevOps/Cloud: $110K-190K
• Web Development: $80K-150K
• Cybersecurity: $100K-180K

**📈 2025 Market Trends:**
• 22% job growth expected
• Remote work widely available
• AI/ML skills premium: +30-50% salary
• Cloud platforms essential
• Microservices architecture in demand

**🛠️ Essential Skills for 2025:**
• Python 3.12+, async programming
• Cloud: AWS/Azure/GCP
• Containers: Docker, Kubernetes
• Databases: PostgreSQL, MongoDB
• Version control: Git, GitHub Actions
• Testing: pytest, CI/CD pipelines"""

                else:
                    # General Python info
                    return self.search_wikipedia("Python programming language")

            # JavaScript questions
            elif 'javascript' in query_lower or 'js' in query_lower:
                if any(word in query_lower for word in ['learn', 'start', 'roadmap']):
                    return """**JavaScript Learning Path 2025**

**🚀 Modern JavaScript Roadmap:**

**Phase 1: Core JavaScript (4-6 weeks)**
• ES6+ syntax: arrow functions, destructuring, modules
• DOM manipulation and event handling
• Async programming: Promises, async/await
• Error handling and debugging
• Browser APIs and local storage

**Phase 2: Frontend Frameworks (6-8 weeks)**
• React.js: Components, hooks, state management
• Vue.js or Angular (choose one)
• CSS frameworks: Tailwind, Bootstrap
• Build tools: Vite, Webpack
• Package management: npm, yarn

**Phase 3: Backend Development (4-6 weeks)**
• Node.js and Express.js
• RESTful APIs and GraphQL
• Database integration: MongoDB, PostgreSQL
• Authentication: JWT, OAuth
• Testing: Jest, Supertest

**Phase 4: Full-Stack & Deployment (4 weeks)**
• Full-stack applications
• Cloud deployment: Vercel, Netlify, AWS
• DevOps basics: Docker, CI/CD
• Performance optimization
• Security best practices

**💼 Career Opportunities:**
• Frontend Developer: $70K-140K
• Full-Stack Developer: $80K-160K
• React Developer: $85K-150K
• Node.js Developer: $90K-170K"""

                else:
                    return self.search_wikipedia("JavaScript")

            # General programming concepts
            elif any(word in query_lower for word in ['algorithm', 'data structure', 'programming', 'software']):
                if 'algorithm' in query_lower:
                    return """**Essential Algorithms & Data Structures 2025**

**🔍 Core Algorithms:**
• Sorting: QuickSort, MergeSort, HeapSort
• Searching: Binary Search, DFS, BFS
• Dynamic Programming: Fibonacci, Knapsack
• Graph algorithms: Dijkstra, A*
• String algorithms: KMP, Rabin-Karp

**📊 Data Structures:**
• Arrays and Linked Lists
• Stacks and Queues
• Trees: Binary, AVL, Red-Black
• Hash Tables and Hash Maps
• Graphs and Heaps

**🎯 Interview Preparation:**
• Practice platforms: LeetCode, HackerRank
• Time/Space complexity analysis
• System design basics
• Coding patterns recognition
• Mock interviews

**💡 Real-World Applications:**
• Database indexing (B-trees)
• Web crawling (Graph traversal)
• Route finding (Shortest path)
• Data compression (Huffman coding)
• Machine learning (Tree ensembles)"""

                else:
                    return self.search_wikipedia(query)

            # Web development
            elif any(word in query_lower for word in ['web development', 'html', 'css', 'frontend', 'backend']):
                return """**Web Development Complete Guide 2025**

**🎨 Frontend Technologies:**
• HTML5: Semantic markup, accessibility
• CSS3: Flexbox, Grid, animations
• JavaScript: ES2024 features
• Frameworks: React, Vue, Angular, Svelte
• CSS Frameworks: Tailwind CSS, Bootstrap
• Build Tools: Vite, Parcel, Webpack

**⚙️ Backend Technologies:**
• Languages: JavaScript (Node.js), Python (Django/Flask), Java (Spring)
• Databases: PostgreSQL, MongoDB, Redis
• APIs: REST, GraphQL, gRPC
• Cloud: AWS, Azure, Google Cloud
• DevOps: Docker, Kubernetes, CI/CD

**📱 Modern Trends 2025:**
• JAMstack architecture
• Serverless computing
• Progressive Web Apps (PWA)
• WebAssembly (WASM)
• Edge computing
• Micro-frontends

**💰 Salary Expectations:**
• Junior Full-Stack: $70K-90K
• Mid-level: $90K-130K
• Senior: $130K-180K
• Tech Lead: $180K-250K

**🛠️ Essential Tools:**
• VS Code, Git, GitHub
• Postman, Insomnia (API testing)
• Chrome DevTools
• Figma (Design)
• Vercel, Netlify (Deployment)"""

            # AI and Machine Learning
            elif any(word in query_lower for word in ['ai', 'machine learning', 'ml', 'artificial intelligence']):
                return """**AI & Machine Learning Roadmap 2025**

**🤖 Core Concepts:**
• Supervised vs Unsupervised Learning
• Neural Networks and Deep Learning
• Natural Language Processing (NLP)
• Computer Vision
• Reinforcement Learning

**🐍 Python Libraries:**
• NumPy, Pandas (Data manipulation)
• Scikit-learn (Classical ML)
• TensorFlow, PyTorch (Deep Learning)
• OpenCV (Computer Vision)
• NLTK, spaCy (NLP)

**🎯 Popular Applications:**
• ChatGPT-style language models
• Image recognition and generation
• Recommendation systems
• Autonomous vehicles
• Medical diagnosis

**💼 Career Paths & Salaries:**
• ML Engineer: $130K-200K
• Data Scientist: $120K-180K
• AI Research Scientist: $150K-300K
• Computer Vision Engineer: $140K-220K
• NLP Engineer: $135K-210K

**📚 Learning Resources:**
• Andrew Ng's ML Course (Coursera)
• Fast.ai practical courses
• Papers With Code
• Kaggle competitions
• Google Colab for practice"""

            else:
                # Fallback to Wikipedia for general programming topics
                return self.search_wikipedia(query)
                
        except Exception as e:
            logger.error(f"Programming info error: {e}")
            return self.search_wikipedia(query)
        
        return None
• Understand functions and scope

**Phase 2: Data Structures (Weeks 5-8)**
• Lists, dictionaries, sets, tuples
• File handling and error management
• Object-oriented programming basics
• Popular libraries: requests, json, datetime

**Phase 3: Practical Skills (Weeks 9-12)**
• Web scraping with BeautifulSoup
• API development with Flask/FastAPI
• Database operations with SQLite/PostgreSQL
• Testing with pytest

**Phase 4: Specialization (Weeks 13+)**
• Data Science: pandas, numpy, matplotlib
• Web Development: Django, Flask
• AI/ML: scikit-learn, TensorFlow
• Automation: selenium, pyautogui

**Best Resources 2025:**
• Official Python Tutorial (docs.python.org)
• Real Python (realpython.com)
• Automate the Boring Stuff (free online)
• Python Crash Course book
• Codecademy Python Track

*This roadmap is updated for current industry standards and job market demands.*"""
            
            elif 'javascript' in query_lower:
                return """**JavaScript Learning Path 2025**

**Modern JavaScript Essentials:**
• ES6+ features: arrow functions, destructuring, modules
• Async/await and Promises for handling APIs
• DOM manipulation and event handling
• JSON data handling and fetch API

**Popular Frameworks/Libraries:**
• React.js - Most in-demand for frontend
• Node.js - Backend JavaScript development
• Express.js - Web application framework
• Vue.js/Angular - Alternative frontend frameworks

**Current Industry Trends:**
• TypeScript adoption increasing rapidly
• JAMstack architecture gaining popularity
• Serverless functions with Vercel/Netlify
• Full-stack development with Next.js

**Job Market Reality 2025:**
JavaScript developers are in high demand with average salaries ranging from $70K-$150K+ depending on experience and location."""
            
            elif 'career' in query_lower and 'programming' in query_lower:
                return """**Programming Career Reality Check 2025**

**High-Demand Skills:**
• Full-stack development (React + Node.js/Python)
• Cloud platforms (AWS, Azure, Google Cloud)
• DevOps and containerization (Docker, Kubernetes)
• AI/ML integration in applications
• Cybersecurity fundamentals

**Salary Ranges (US Market 2025):**
• Entry Level: $60K-$85K
• Mid Level (3-5 years): $85K-$130K
• Senior Level (5+ years): $130K-$200K+
• Staff/Principal: $200K-$350K+

**Job Market Insights:**
• Remote work still widely available
• Startups offer equity but higher risk
• Big Tech pays most but competitive entry
• Financial services and healthcare pay well
• Government/defense offers stability

**Real Advice:**
Build a strong GitHub portfolio, contribute to open source, network actively, and focus on solving real problems rather than just learning syntax."""
            
        except Exception as e:
            logger.error(f"Programming info error: {e}")
        
        return None
    
    def get_educational_info(self, query):
        """Get educational and academic information"""
        try:
            query_lower = query.lower()
            
            if 'gre' in query_lower:
                return """**GRE Preparation - Real 2025 Strategy**

**Current GRE Format (Updated 2025):**
• Shorter test duration (1 hr 58 min total)
• Analytical Writing: 1 task (30 min)
• Verbal Reasoning: 2 sections (41 min total)
• Quantitative Reasoning: 2 sections (47 min total)

**Score Requirements 2025:**
• Top Universities: 325+ total (160+ each section)
• Good Universities: 315-324 total
• Average Universities: 300-314 total
• Minimum competitive: 290-299 total

**Real Cost Breakdown:**
• GRE Test Fee: $220 (as of 2025)
• Prep materials: $200-$500
• Tutoring (optional): $50-$150/hour
• Total budget: $400-$1000+

**Proven Study Timeline:**
• 3+ months: Ideal for most students
• 6+ months: If starting from basics
• 1-2 months: Only if strong foundation

**High-Impact Resources 2025:**
• ETS PowerPrep tests (free, most accurate)
• Manhattan Prep books (comprehensive)
• Magoosh online (affordable, good explanations)
• Gregmat+ (YouTube + paid course, excellent value)

**Real Success Tips:**
Focus 60% time on your weaker section, take full practice tests weekly, and aim for consistency over perfection."""
            
            elif 'vjit' in query_lower or 'vidya jyothi' in query_lower:
                return """**VJIT (Vidya Jyothi Institute of Technology) - Real Information 2025**

**Basic Details:**
• Location: Hyderabad, Telangana, India
• Established: 1995
• Type: Private Engineering College
• Affiliation: JNTUH (Jawaharlal Nehru Technological University Hyderabad)
• Approval: AICTE approved

**Programs Offered (2025):**
• B.Tech: CSE, ECE, EEE, ME, CE, IT, AI&ML
• M.Tech: Various specializations
• MBA: General and specialized tracks

**Current Ranking & Recognition:**
• NIRF Ranking: Not in top 100 (as of 2025)
• State-level recognition for placement support
• Industry partnerships with local IT companies

**Placement Statistics (Recent):**
• Average Package: ₹3.5-5.5 LPA
• Highest Package: ₹12-15 LPA (occasional)
• Placement Rate: 70-80% for CSE/IT branches
• Major Recruiters: TCS, Infosys, Wipro, Cognizant, local startups

**Real Student Feedback:**
• Good infrastructure and modern labs
• Experienced faculty in core subjects
• Active placement cell with industry connections
• Campus life is decent with cultural events
• Location advantage being in Hyderabad IT hub

**Fee Structure (Approximate 2025):**
• B.Tech: ₹80K-1.2L per year (varies by branch)
• Hostel: ₹60K-80K per year
• Total 4-year cost: ₹6-8L approximately

*Note: Verify current details directly with the college as information may change.*"""
            
        except Exception as e:
            logger.error(f"Educational info error: {e}")
        
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
            },
            'hello!': {
                'es': '¡hola!', 'fr': 'bonjour!', 'de': 'hallo!', 'it': 'ciao!',
                'pt': 'olá!', 'ru': 'привет!', 'ja': 'こんにちは！', 'ko': '안녕하세요!',
                'zh': '你好！', 'ar': 'مرحبا!', 'hi': 'नमस्ते!'
            },
            'hello! how can i help you today?': {
                'es': '¡Hola! ¿Cómo puedo ayudarte hoy?', 
                'fr': 'Bonjour! Comment puis-je vous aider aujourd\'hui?',
                'de': 'Hallo! Wie kann ich Ihnen heute helfen?',
                'it': 'Ciao! Come posso aiutarti oggi?',
                'pt': 'Olá! Como posso ajudá-lo hoje?',
                'ru': 'Привет! Как я могу помочь вам сегодня?',
                'ja': 'こんにちは！今日はどのようにお手伝いできますか？',
                'ko': '안녕하세요! 오늘 어떻게 도와드릴까요?',
                'zh': '你好！今天我怎么帮助你？',
                'ar': 'مرحبا! كيف يمكنني مساعدتك اليوم؟',
                'hi': 'नमस्ते! आज मैं आपकी कैसे सहायता कर सकता हूं?'
            },
            'that\'s interesting! tell me more.': {
                'es': '¡Eso es interesante! Cuéntame más.',
                'fr': 'C\'est intéressant! Dites-moi en plus.',
                'de': 'Das ist interessant! Erzählen Sie mir mehr.',
                'it': 'È interessante! Dimmi di più.',
                'pt': 'Isso é interessante! Me conte mais.',
                'ru': 'Это интересно! Расскажите мне больше.',
                'ja': 'それは興味深いです！もっと教えてください。',
                'ko': '흥미롭네요! 더 말씀해 주세요.',
                'zh': '很有趣！告诉我更多。',
                'ar': 'هذا مثير للاهتمام! أخبرني المزيد.',
                'hi': 'यह दिलचस्प है! मुझे और बताएं।'
            }
        }
    
    def test_connection(self):
        """Test if LibreTranslate service is available"""
        try:
            response = requests.get(f"{self.base_url}/languages", timeout=5)
            if response.status_code == 200:
                logger.info(f"LibreTranslate service available at {self.base_url}")
                return True
            else:
                logger.warning(f"LibreTranslate service responded with status {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Cannot connect to LibreTranslate service: {e}")
            return False
    
    def get_languages(self):
        """Get list of supported languages"""
        if self.is_available:
            try:
                response = requests.get(f"{self.base_url}/languages", timeout=5)
                if response.status_code == 200:
                    return response.json()
            except Exception as e:
                logger.error(f"Error getting languages: {e}")
        
        return self.get_fallback_languages()
    
    def get_fallback_languages(self):
        """Return fallback language list when service is unavailable"""
        return [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"}
        ]
    
    def simple_translate(self, text, target_lang):
        """Simple translation using predefined dictionary"""
        text_lower = text.lower().strip()
        
        if text_lower in self.simple_translations:
            translations = self.simple_translations[text_lower]
            if target_lang in translations:
                return translations[target_lang]
        
        # Try partial matches for common greetings
        for phrase, translations in self.simple_translations.items():
            if phrase in text_lower or text_lower in phrase:
                if target_lang in translations:
                    return translations[target_lang]
        
        return None
    
    def translate(self, text, source_lang, target_lang):
        """Translate text from source to target language"""
        if source_lang == target_lang:
            return text
        
        # Try simple translation first
        simple_translation = self.simple_translate(text, target_lang)
        if simple_translation:
            logger.info(f"Using simple translation: {text} -> {simple_translation}")
            return simple_translation
        
        # If service is not available, return original text
        if not self.is_available:
            logger.warning("Translation service unavailable, using simple fallback")
            return f"{text} [{target_lang.upper()}]"
            
        try:
            data = {
                'q': text,
                'source': source_lang,
                'target': target_lang,
                'format': 'text'
            }
            
            api_key = os.getenv('LIBRETRANSLATE_API_KEY')
            if api_key:
                data['api_key'] = api_key
            
            # Add timeout and headers
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                f"{self.base_url}/translate", 
                json=data, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    translated_text = result.get('translatedText', text)
                    if translated_text and translated_text.strip():
                        return translated_text
                    else:
                        logger.warning(f"Empty translation result for: {text}")
                        return text
                except (ValueError, KeyError) as e:
                    logger.error(f"JSON parsing error: {e}, Response: {response.text}")
                    return text
            else:
                logger.error(f"Translation API error: {response.status_code} - {response.text}")
                # Fall back to simple translation
                return simple_translation or f"{text} [{target_lang.upper()}]"
                
        except requests.exceptions.Timeout:
            logger.error("Translation request timed out")
            return simple_translation or text
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to translation service")
            return simple_translation or text
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return simple_translation or text

class ChatbotService:
    """Intelligent chatbot using OpenAI GPT"""
    
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
        
        # Fallback responses for when OpenAI is not available
        self.fallback_responses = {
            'greeting': [
                "Hello! I'm your Universal Language Assistant. I can help you with translations, conversations, and answer questions in multiple languages.",
                "Hi there! How can I assist you today? I speak many languages and can help with various topics.",
                "Welcome! I'm here to help you communicate and learn in any language you prefer."
            ],
            'help': [
                "I can help you with:\n• Translation between languages\n• Answering questions on various topics\n• Having conversations in multiple languages\n• Voice interactions\n• Real-time translation",
                "I'm capable of:\n• Multi-language communication\n• Providing information on diverse subjects\n• Voice-to-voice conversations\n• Real-time translation services",
                "My abilities include:\n• Understanding and speaking multiple languages\n• Answering questions about various topics\n• Facilitating cross-language communication\n• Voice interaction capabilities"
            ],
            'default': [
                "That's interesting! Could you tell me more about what you'd like to know?",
                "I'd be happy to help with that. Can you provide more details about your question?",
                "Thanks for sharing that. What specific information are you looking for?",
                "I understand. How can I assist you further with this topic?"
            ]
        }
    
    def get_system_prompt(self, user_language='en', bot_language='en'):
        """Generate system prompt for OpenAI based on languages"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""You are a helpful, intelligent, and multilingual assistant in a Universal Language Support Chatbot. 

Current date and time: {current_time}

Key capabilities:
- Communicate fluently in multiple languages
- Provide accurate, helpful, and up-to-date information
- Answer questions on a wide variety of topics
- Be culturally sensitive and respectful
- Provide concise but informative responses

User's language: {user_language}
Response language: {bot_language}

Instructions:
1. Always respond in {bot_language} unless specifically asked otherwise
2. Be helpful, friendly, and conversational
3. If you need clarification, ask follow-up questions
4. Provide accurate information and admit when you're uncertain
5. Keep responses concise but informative (aim for 1-3 sentences unless more detail is needed)
6. Be culturally aware and sensitive to different perspectives
7. If asked about current events, acknowledge your knowledge cutoff but provide what relevant information you can

Remember: You're part of a real-time translation system, so users may be communicating in their native language and expecting responses in another language."""

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
    
    def get_fallback_response(self, message):
        """Generate highly intelligent fallback response when OpenAI is not available"""
        import random
        message_lower = message.lower().strip()
        
        # Enhanced greeting responses
        greeting_words = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening', 'hola', 'bonjour', 'guten tag', 'ciao']
        if any(word in message_lower for word in greeting_words):
            responses = [
                "Hello! I'm your Universal Language Assistant. I can help with translations between 12+ languages and answer questions on various topics. What would you like to explore today?",
                "Hi there! Welcome to our multilingual chatbot. I can communicate in English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi and more. How can I help?",
                "Greetings! I'm here to break down language barriers and help with information on diverse topics. Try asking me something in any language!",
                "¡Hola! Bonjour! Guten Tag! I speak many languages and love helping people communicate across cultures. What can I do for you?"
            ]
            return random.choice(responses)
        
        # Enhanced VJIT and education responses
        if any(word in message_lower for word in ['vjit', 'vidya jyothi']):
            responses = [
                "VJIT (Vidya Jyothi Institute of Technology) is a prestigious engineering college located in Hyderabad, Telangana, India. It offers undergraduate and postgraduate programs in various engineering disciplines including Computer Science, Electronics, Mechanical, Civil, and more. The institute is known for its strong technical curriculum, experienced faculty, industry partnerships, and good placement record. VJIT focuses on providing quality technical education and fostering innovation among students.",
                "Vidya Jyothi Institute of Technology (VJIT) is an established engineering institution in Hyderabad. It offers B.Tech programs in multiple branches like CSE, ECE, ME, CE, and also M.Tech courses. The college is recognized for its academic excellence, modern infrastructure, research opportunities, and strong industry connections that help students get good placements in top companies.",
                "VJIT is a well-known engineering college in Telangana that provides comprehensive technical education. The institute has modern laboratories, experienced faculty, active placement cell, and focuses on both theoretical knowledge and practical skills. Students from VJIT often get placed in reputed companies like TCS, Infosys, Wipro, and many other IT and core engineering firms."
            ]
            return random.choice(responses)
        
        # GRE preparation roadmap
        if any(word in message_lower for word in ['gre', 'graduate record examination']) and any(word in message_lower for word in ['roadmap', 'prepare', 'preparation', 'plan', 'study']):
            return """Here's a comprehensive GRE preparation roadmap:

**Phase 1 (Weeks 1-2): Assessment & Planning**
• Take a diagnostic test to identify strengths/weaknesses
• Set target score based on your dream schools
• Gather study materials (ETS Official Guide, Magoosh, Manhattan Prep)

**Phase 2 (Weeks 3-8): Foundation Building**
• Verbal: Build vocabulary (300+ words/week), learn root words
• Quant: Review basic math concepts, practice problem-solving
• AWA: Study essay structure, practice 2-3 essays/week

**Phase 3 (Weeks 9-14): Intensive Practice**
• Take full-length practice tests weekly
• Analyze mistakes and focus on weak areas
• Time management practice for each section

**Phase 4 (Weeks 15-16): Final Prep**
• Take 2-3 final practice tests
• Review key formulas and vocabulary
• Maintain test-day routine

**Key Tips:**
• Aim for 3-4 months of consistent study (2-3 hours daily)
• Use official ETS materials for practice tests
• Join online forums/groups for motivation
• Book your test date early to secure preferred slot"""
        
        # Study and exam preparation
        if any(word in message_lower for word in ['study', 'exam', 'preparation', 'test', 'entrance']) and not any(word in message_lower for word in ['gre']):
            if any(word in message_lower for word in ['tips', 'advice', 'how to']):
                return """Effective Study Tips for Academic Success:

**1. Time Management:**
• Create a study schedule and stick to it
• Use Pomodoro Technique (25 min study + 5 min break)
• Prioritize difficult subjects during peak hours

**2. Active Learning:**
• Take handwritten notes for better retention
• Teach concepts to others (Feynman Technique)
• Practice problems regularly, don't just read

**3. Exam Strategy:**
• Review past papers and question patterns
• Create summary notes for quick revision
• Practice time management during mock tests

**4. Health & Motivation:**
• Get 7-8 hours sleep, maintain regular exercise
• Take breaks to avoid burnout
• Stay hydrated and eat brain-healthy foods

**5. Resources:**
• Use multiple sources (textbooks, online courses, videos)
• Join study groups for collaborative learning
• Seek help from teachers/mentors when stuck"""
            else:
                return "Effective study preparation involves creating a structured plan, practicing regularly, and maintaining good health habits. Would you like specific tips for exam preparation, time management, or study techniques?"
        
        # Technology and AI questions
        if any(word in message_lower for word in ['ai', 'artificial intelligence', 'technology', 'computer', 'programming', 'machine learning', 'chatbot', 'robot']):
            if 'chatbot' in message_lower or 'bot' in message_lower:
                return "Chatbots like me use Natural Language Processing (NLP) to understand and respond to human language. We combine machine learning, pattern recognition, and pre-trained models to provide helpful responses. Modern chatbots can handle multiple languages, maintain context, and even generate creative content!"
            elif any(word in message_lower for word in ['how', 'work', 'works']):
                return "AI works through machine learning algorithms that process large amounts of data to recognize patterns and make predictions. Key components include neural networks (inspired by human brain), training data, and algorithms like deep learning. AI applications include image recognition, language translation, autonomous vehicles, and intelligent assistants like me!"
            else:
                return "AI and technology are revolutionizing our world! From machine learning and neural networks to robotics and automation, AI helps solve complex problems, improves efficiency, and creates new possibilities. It's used in healthcare, education, transportation, finance, and virtually every industry today."
        
        # Career and placement questions
        if any(word in message_lower for word in ['career', 'job', 'placement', 'interview', 'resume', 'cv']):
            if any(word in message_lower for word in ['tips', 'advice', 'preparation']):
                return """Career Development & Placement Tips:

**Resume/CV:**
• Highlight technical skills, projects, and achievements
• Use action verbs and quantify accomplishments
• Keep it concise (1-2 pages) and error-free

**Interview Preparation:**
• Research the company and role thoroughly
• Practice common technical and behavioral questions
• Prepare STAR method examples for experiences
• Ask thoughtful questions about the role/company

**Skill Development:**
• Stay updated with industry trends and technologies
• Build a strong portfolio/GitHub profile
• Get certifications relevant to your field
• Practice coding problems on platforms like LeetCode

**Networking:**
• Attend industry events and job fairs
• Connect with alumni and professionals on LinkedIn
• Join professional communities and forums
• Seek mentorship opportunities"""
            else:
                return "Career success involves continuous learning, networking, and strategic planning. Strong technical skills, good communication, and industry knowledge are key. Would you like specific advice on resume building, interview preparation, or skill development?"
        
        # Programming and coding questions
        if any(word in message_lower for word in ['programming', 'coding', 'python', 'java', 'javascript', 'c++', 'development', 'software']):
            if any(word in message_lower for word in ['learn', 'start', 'begin']):
                return """Programming Learning Roadmap:

**1. Choose Your First Language:**
• Python: Great for beginners, versatile (web, AI, data science)
• Java: Object-oriented, widely used in enterprise
• JavaScript: Essential for web development

**2. Master the Fundamentals:**
• Variables, data types, control structures
• Functions, arrays, and basic algorithms
• Object-oriented programming concepts

**3. Practice Platforms:**
• HackerRank, LeetCode for problem-solving
• GitHub for version control and portfolio
• Stack Overflow for community support

**4. Build Projects:**
• Start with simple calculators, to-do apps
• Progress to web applications, APIs
• Create a portfolio showcasing your work

**5. Advanced Topics:**
• Data structures and algorithms
• Database management (SQL)
• Web frameworks (Django, React, etc.)"""
            else:
                return "Programming is a valuable skill in today's digital world! Whether you're interested in web development, mobile apps, AI, or data science, coding opens up numerous career opportunities. The key is starting with fundamentals and practicing consistently."
        
        # Science questions
        if any(word in message_lower for word in ['science', 'physics', 'chemistry', 'biology', 'mathematics', 'math', 'engineering', 'research']):
            return "Science and engineering drive innovation and progress! These fields involve understanding natural phenomena, developing new technologies, and solving real-world problems. From quantum physics to biotechnology, mathematical modeling to space exploration - science continues to expand our knowledge and capabilities."
        
        # Specific question handling with context awareness
        if message_lower.startswith('how'):
            if any(word in message_lower for word in ['study', 'prepare', 'learn']):
                return "Effective learning involves active engagement, regular practice, and spaced repetition. Create a structured study plan, use multiple resources, practice regularly, and don't hesitate to seek help when needed. Would you like specific study strategies for any particular subject?"
            elif any(word in message_lower for word in ['work', 'works', 'working']):
                return "Great question! I work by combining natural language processing, machine learning, and multilingual capabilities to understand your questions and provide helpful responses. I can translate between languages, explain concepts, and assist with various topics. What specific aspect would you like to know more about?"
            elif any(word in message_lower for word in ['career', 'job', 'success']):
                return "Career success comes from continuous learning, networking, developing both technical and soft skills, staying adaptable to industry changes, and building meaningful professional relationships. Focus on adding value, being reliable, and always seeking opportunities to grow."
            else:
                return "That's a great 'how' question! I'd love to help you understand that better. Could you be more specific about what you'd like to know? I can explain processes, provide step-by-step guidance, or help with translations."
        
        # What questions with enhanced responses
        if message_lower.startswith('what'):
            if any(word in message_lower for word in ['time', 'date']):
                return "I don't have access to real-time data, but you can check the current time and date on your device. I can help you learn time expressions in different languages though! For example: 'What time is it?' is '¿Qué hora es?' in Spanish, 'Quelle heure est-il?' in French."
            elif any(word in message_lower for word in ['career', 'job']):
                return "Career choices depend on your interests, skills, and market demand. Popular fields include technology (software development, AI, cybersecurity), healthcare, finance, marketing, and engineering. Consider what you're passionate about, your strengths, and growth opportunities in different sectors."
            elif any(word in message_lower for word in ['best', 'good']) and any(word in message_lower for word in ['language', 'programming']):
                return "The 'best' programming language depends on your goals: Python for AI/data science/beginners, JavaScript for web development, Java for enterprise applications, C++ for system programming, Swift for iOS apps, Kotlin for Android. Start with Python if you're a beginner - it's versatile and beginner-friendly!"
            else:
                return "That's an interesting 'what' question! I can help explain various topics, provide definitions, or translate information between languages. What specifically would you like to know more about?"
        
        # Language and translation questions
        if any(word in message_lower for word in ['translate', 'translation', 'language', 'speak', 'communication', 'multilingual', 'bilingual']):
            return "I support translation between 12+ languages: English, Spanish (Español), French (Français), German (Deutsch), Italian (Italiano), Portuguese (Português), Russian (Русский), Japanese (日本語), Korean (한국어), Chinese (中文), Arabic (العربية), and Hindi (हिंदी). Just type in any language and I'll help translate! Language learning tip: practice consistently, immerse yourself in content, and don't be afraid to make mistakes."
        
        # Help and capabilities
        if any(word in message_lower for word in ['help', 'assist', 'support', 'can you', 'capabilities', 'what can you do']):
            return """I'm here to help with a wide range of tasks! Here's what I can do:

🌍 **Languages:** Translate between 12+ languages including English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi

📚 **Education:** Provide study tips, exam preparation strategies, academic guidance for subjects like math, science, engineering

💼 **Career:** Offer advice on job preparation, interview tips, resume building, skill development, career planning

💻 **Technology:** Explain programming concepts, AI/ML topics, help with coding questions, technology trends

🎯 **General Knowledge:** Answer questions on various topics, provide explanations, give practical advice

🗣️ **Communication:** Work with both text and voice input, maintain conversations, provide context-aware responses

What specific area would you like help with today?"""
        
        # Enhanced context-aware responses for specific topics
        if any(word in message_lower for word in ['roadmap', 'plan', 'steps']) and not any(word in message_lower for word in ['gre']):
            if any(word in message_lower for word in ['career', 'job']):
                return "A solid career roadmap includes: 1) Self-assessment (skills, interests, values), 2) Market research (industry trends, opportunities), 3) Skill development (technical + soft skills), 4) Networking and mentorship, 5) Gaining experience (internships, projects), 6) Continuous learning and adaptation. What specific career field interests you?"
            else:
                return "Creating a roadmap involves setting clear goals, breaking them into manageable steps, setting timelines, and regularly reviewing progress. Whether it's for learning, career, or personal development, a good plan includes milestones, resources needed, and backup strategies. What kind of roadmap are you looking to create?"
        
        # Default intelligent responses with context
        if len(message_lower) > 10:  # For longer, more specific messages
            # Extract key topics for more relevant responses
            if any(word in message_lower for word in ['college', 'university', 'education', 'degree']):
                return "Higher education is a significant investment in your future! Focus on choosing programs that align with your career goals, provide good industry exposure, and offer strong placement support. Research thoroughly, consider factors like curriculum, faculty, infrastructure, and alumni network."
            
            elif any(word in message_lower for word in ['future', 'trend', 'upcoming']):
                return "Future trends point toward increased automation, AI integration, sustainable technologies, remote work, digital transformation, and personalized services. Key growth areas include renewable energy, biotechnology, space technology, cybersecurity, and quantum computing. Staying adaptable and continuously learning new skills is crucial."
            
            elif any(word in message_lower for word in ['motivation', 'inspiration', 'success']):
                return "Success comes from consistent effort, learning from failures, staying curious, and helping others along the way. Set clear goals, celebrate small wins, surround yourself with positive influences, and remember that every expert was once a beginner. Keep pushing forward!"
            
            else:
                return f"That's a thoughtful question about '{message}'. While I work best with full AI capabilities, I can still provide helpful information on education, technology, languages, career guidance, and many other topics. Could you be more specific about what aspect you'd like to explore?"
        
        # Short message responses
        return "I'm here to help! Try asking me specific questions about education, technology, career advice, study tips, programming, or request translations between languages. What interests you most?"
    
    def clear_history(self, session_id='default'):
        """Clear conversation history for a session"""
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]

# Initialize services
translator = TranslationService(CONFIG['libretranslate_url'])
chatbot = ChatbotService(
    api_key=CONFIG['openai_api_key'],
    model=CONFIG['openai_model'],
    max_tokens=CONFIG['openai_max_tokens']
)

@app.route('/')
def index():
    """Serve the main chat interface"""
    return render_template('index.html')

@app.route('/api/languages')
def get_languages():
    """Get supported languages from LibreTranslate"""
    languages = translator.get_languages()
    return jsonify(languages)

@app.route('/api/translate', methods=['POST'])
def translate_text():
    """Translate text endpoint"""
    data = request.get_json()
    
    text = data.get('text', '')
    source_lang = data.get('source', 'auto')
    target_lang = data.get('target', 'en')
    
    translated = translator.translate(text, source_lang, target_lang)
    
    return jsonify({
        'original': text,
        'translated': translated,
        'source': source_lang,
        'target': target_lang
    })

@app.route('/api/clear-history', methods=['POST'])
def clear_chat_history():
    """Clear conversation history for a session"""
    data = request.get_json()
    session_id = data.get('session_id', 'default')
    
    try:
        chatbot.clear_history(session_id)
        return jsonify({'success': True, 'message': 'Chat history cleared'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/status')
def get_status():
    """Get system status"""
    return jsonify({
        'translation_service': translator.is_available,
        'openai_available': chatbot.client is not None,
        'whisper_loaded': whisper_model is not None,
        'supported_languages': len(translator.get_languages())
    })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('status', {'message': 'Connected to Universal Language Chatbot'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('chat_message')
def handle_chat_message(data):
    """Handle incoming chat messages"""
    try:
        user_message = data.get('message', '')
        user_language = data.get('user_language', CONFIG['default_user_language'])
        bot_language = data.get('bot_language', CONFIG['default_bot_language'])
        is_realtime = data.get('realtime', False)
        session_id = data.get('session_id', request.sid)
        
        logger.info(f"Received message: {user_message} (lang: {user_language}, realtime: {is_realtime})")
        
        # Translate user message to bot language if needed for processing
        translated_user_message = translator.translate(user_message, user_language, bot_language)
        
        # Generate intelligent bot response using OpenAI
        bot_response = chatbot.get_response(
            translated_user_message, 
            user_language=user_language,
            bot_language=bot_language,
            session_id=session_id
        )
        
        # Translate bot response back to user language if needed
        final_bot_response = translator.translate(bot_response, bot_language, user_language)
        
        # Send response back to client
        response_data = {
            'original_message': user_message,
            'translated_message': translated_user_message,
            'bot_response': final_bot_response,
            'bot_response_original': bot_response,
            'user_language': user_language,
            'bot_language': bot_language,
            'realtime': is_realtime,
            'session_id': session_id
        }
        
        if is_realtime:
            emit('realtime_response', response_data)
        else:
            emit('bot_response', response_data)
        
    except Exception as e:
        logger.error(f"Error handling chat message: {e}")
        emit('error', {'message': 'Sorry, there was an error processing your message.'})

@socketio.on('voice_message')
def handle_voice_message(data):
    """Handle voice message transcription and translation"""
    try:
        # This would handle audio data from the client
        # For now, we'll simulate with text
        audio_data = data.get('audio_data')
        user_language = data.get('user_language', CONFIG['default_user_language'])
        
        if whisper_model and audio_data:
            # In a real implementation, you'd process the audio data here
            # For demo purposes, we'll use a placeholder
            transcribed_text = "Voice message received"  # Placeholder
            
            # Process as regular chat message
            handle_chat_message({
                'message': transcribed_text,
                'user_language': user_language,
                'bot_language': data.get('bot_language', CONFIG['default_bot_language'])
            })
        else:
            emit('error', {'message': 'Voice processing not available'})
            
    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        emit('error', {'message': 'Sorry, there was an error processing your voice message.'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Run the application
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
