# Universal Language Support Chatbot - Setup Guide

## Overview
This Universal Language Support Chatbot provides real-time multilingual communication with intelligent AI responses powered by OpenAI GPT, speech-to-text using Whisper, and translation via LibreTranslate.

## Features
- **Multilingual Support**: 12+ languages including English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Arabic, Hindi
- **Intelligent Responses**: Powered by OpenAI GPT-4 for contextual, intelligent conversations
- **Real-time Speech**: Voice input/output with Web Speech API and Whisper
- **Live Translation**: Automatic translation between languages
- **Real-time Conversation**: Live voice chat mode with instant transcription
- **Conversation History**: Persistent chat history with context awareness
- **Offline Fallback**: Works with basic translations even when services are unavailable

## Prerequisites
1. **Python 3.8+** installed
2. **OpenAI API Key** (for intelligent responses)
3. **Internet connection** (for LibreTranslate service)

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure OpenAI API Key
To enable intelligent chatbot responses, you need to set up your OpenAI API key:

#### Option A: Environment File (.env)
1. Open the `.env` file in the project root
2. Add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

#### Option B: Environment Variable
Set the environment variable in your system:
```bash
# Windows
set OPENAI_API_KEY=your_openai_api_key_here

# Linux/Mac
export OPENAI_API_KEY=your_openai_api_key_here
```

#### Option C: Direct Configuration
You can also set the API key directly in the `app.py` file (not recommended for production):
```python
CONFIG['openai']['api_key'] = 'your_openai_api_key_here'
```

### 3. Get OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in to your account
3. Navigate to "API Keys" section
4. Click "Create new secret key"
5. Copy the generated key and use it in your configuration

## Running the Application

### Start the Server
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

### System Status
- ✅ **OpenAI Available**: Intelligent responses enabled
- ✅ **Whisper Loaded**: Speech-to-text working
- ⚠️ **LibreTranslate**: May be unavailable (fallback translations used)

## Usage Guide

### Basic Chat
1. Type your message in any supported language
2. The bot will respond intelligently using OpenAI GPT
3. Messages are automatically translated based on your language settings

### Voice Input
1. Click the microphone button to start voice recording
2. Speak your message clearly
3. The speech will be transcribed and sent automatically

### Real-time Conversation
1. Click "Start Real-time Chat" button
2. Hold the "Hold to Speak" button while talking
3. Release to send your message
4. The bot will respond in real-time

### Settings Configuration
1. Click the settings gear icon
2. Configure:
   - **User Language**: Your preferred input language
   - **Bot Language**: Bot's response language
   - **Voice Response**: Enable text-to-speech for bot responses
   - **Auto-translate**: Automatically translate messages

### Clear Chat History
1. Open Settings
2. Click "Clear History" button
3. Confirm to remove all conversation history

## API Endpoints

### POST `/api/translate`
Translate text between languages
```json
{
  "text": "Hello world",
  "source": "en",
  "target": "es"
}
```

### POST `/api/clear-history`
Clear conversation history for a session
```json
{
  "session_id": "session_123"
}
```

### GET `/api/status`
Get system status information

## Troubleshooting

### OpenAI Integration Issues
- **No API Key**: Check if `OPENAI_API_KEY` is properly set
- **Invalid API Key**: Verify your OpenAI API key is correct and active
- **Rate Limits**: OpenAI has usage limits; check your account quota
- **Fallback Mode**: Without OpenAI, the bot uses simple predetermined responses

### Translation Issues
- **LibreTranslate Unavailable**: The app uses offline fallback translations
- **Network Issues**: Check internet connection for online translation
- **Language Support**: Ensure the selected languages are supported

### Speech Recognition Issues
- **Browser Support**: Use Chrome/Edge for best speech recognition support
- **Microphone Access**: Grant microphone permissions when prompted
- **Audio Quality**: Ensure clear audio input for better recognition

### General Issues
- **Port Conflicts**: If port 5000 is occupied, modify the port in `app.py`
- **Dependencies**: Ensure all packages from `requirements.txt` are installed
- **File Permissions**: Check read/write permissions for the application directory

## Configuration Options

### Language Codes
- `en`: English
- `es`: Spanish
- `fr`: French
- `de`: German
- `it`: Italian
- `pt`: Portuguese
- `ru`: Russian
- `ja`: Japanese
- `ko`: Korean
- `zh`: Chinese
- `ar`: Arabic
- `hi`: Hindi

### OpenAI Configuration
The application uses GPT-4 model by default. You can modify the configuration in `app.py`:
```python
CONFIG = {
    'openai': {
        'model': 'gpt-4',  # or 'gpt-3.5-turbo' for faster/cheaper responses
        'max_tokens': 150,
        'temperature': 0.7
    }
}
```

### Conversation Context
- The bot maintains conversation history for context-aware responses
- Each session has a unique ID for history tracking
- System prompts guide the bot's behavior and response style

## Development

### Project Structure
```
hack29/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── templates/
│   └── index.html        # Main chat interface
├── static/
│   ├── css/
│   │   └── style.css     # Application styling
│   └── js/
│       └── app.js        # Frontend JavaScript
└── SETUP.md              # This setup guide
```

### Key Components
- **TranslationService**: Handles LibreTranslate integration with fallbacks
- **ChatbotService**: Manages OpenAI GPT integration and conversation history
- **WebSocket Events**: Real-time communication between frontend and backend
- **Speech Integration**: Whisper for speech-to-text, Web Speech API for text-to-speech

## Security Notes
- Keep your OpenAI API key secure and never commit it to version control
- Use environment variables for sensitive configuration
- Consider implementing rate limiting for production deployment
- Monitor OpenAI usage to avoid unexpected charges

## License
This project is for educational and development purposes. Ensure compliance with OpenAI's usage policies and terms of service.

## Support
For issues and questions:
1. Check the troubleshooting section above
2. Verify your OpenAI API key setup
3. Ensure all dependencies are correctly installed
4. Check the browser console for JavaScript errors
