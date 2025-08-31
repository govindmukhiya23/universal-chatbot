class UniversalChatbot {
    constructor() {
        this.socket = null;
        this.recognition = null;
        this.isRecording = false;
        this.realtimeRecognition = null;
        this.isRealtimeRecording = false;
        this.currentAudio = null;
        this.conversationActive = false;
        this.autoSpeakEnabled = true;
        this.continuousMode = false;
        this.isGeneratingImage = false;
        this.isRecordingImagePrompt = false;
        this.waitingForUserInput = true; // Track conversation turn-taking
        this.lastProcessedMessage = ''; // Track last processed message
        this.messageTimeout = null; // Debounce mechanism
        this.lastProcessedResultIndex = -1; // Track speech recognition results
        this.currentGame = null; // Track current game state
        this.settings = {
            userLanguage: 'en',
            botLanguage: 'en', 
            voiceResponse: false,
            autoTranslate: true
        };
        
        // Comprehensive language list with 100+ languages including all Indian languages
        this.languages = {
            // Major World Languages
            'en': { name: 'English', flag: '🇺🇸' },
            'es': { name: 'Spanish', flag: '🇪🇸' },
            'fr': { name: 'French', flag: '🇫🇷' },
            'de': { name: 'German', flag: '🇩🇪' },
            'it': { name: 'Italian', flag: '🇮🇹' },
            'pt': { name: 'Portuguese', flag: '🇵🇹' },
            'ru': { name: 'Russian', flag: '🇷🇺' },
            'ja': { name: 'Japanese', flag: '🇯🇵' },
            'ko': { name: 'Korean', flag: '🇰🇷' },
            'zh': { name: 'Chinese (Simplified)', flag: '🇨🇳' },
            'zh-TW': { name: 'Chinese (Traditional)', flag: '🇹🇼' },
            'ar': { name: 'Arabic', flag: '🇸🇦' },
            'nl': { name: 'Dutch', flag: '🇳🇱' },
            'sv': { name: 'Swedish', flag: '🇸🇪' },
            'no': { name: 'Norwegian', flag: '🇳🇴' },
            'da': { name: 'Danish', flag: '🇩🇰' },
            'fi': { name: 'Finnish', flag: '🇫🇮' },
            'pl': { name: 'Polish', flag: '🇵🇱' },
            'cs': { name: 'Czech', flag: '🇨🇿' },
            'sk': { name: 'Slovak', flag: '🇸🇰' },
            'hu': { name: 'Hungarian', flag: '🇭🇺' },
            'ro': { name: 'Romanian', flag: '🇷🇴' },
            'bg': { name: 'Bulgarian', flag: '🇧🇬' },
            'hr': { name: 'Croatian', flag: '🇭🇷' },
            'sr': { name: 'Serbian', flag: '🇷🇸' },
            'sl': { name: 'Slovenian', flag: '🇸🇮' },
            'et': { name: 'Estonian', flag: '🇪🇪' },
            'lv': { name: 'Latvian', flag: '🇱🇻' },
            'lt': { name: 'Lithuanian', flag: '🇱🇹' },
            'el': { name: 'Greek', flag: '🇬🇷' },
            'tr': { name: 'Turkish', flag: '🇹🇷' },
            'he': { name: 'Hebrew', flag: '🇮🇱' },
            'fa': { name: 'Persian', flag: '🇮🇷' },
            'ur': { name: 'Urdu', flag: '🇵🇰' },
            'th': { name: 'Thai', flag: '🇹🇭' },
            'vi': { name: 'Vietnamese', flag: '🇻🇳' },
            'id': { name: 'Indonesian', flag: '🇮🇩' },
            'ms': { name: 'Malay', flag: '🇲🇾' },
            'tl': { name: 'Filipino', flag: '🇵🇭' },
            
            // Indian Languages
            'hi': { name: 'Hindi', flag: '🇮🇳' },
            'te': { name: 'Telugu', flag: '🇮🇳' },
            'ta': { name: 'Tamil', flag: '🇮🇳' },
            'kn': { name: 'Kannada', flag: '🇮🇳' },
            'ml': { name: 'Malayalam', flag: '🇮🇳' },
            'bn': { name: 'Bengali', flag: '🇮🇳' },
            'gu': { name: 'Gujarati', flag: '🇮🇳' },
            'mr': { name: 'Marathi', flag: '🇮🇳' },
            'pa': { name: 'Punjabi', flag: '🇮🇳' },
            'or': { name: 'Odia', flag: '🇮🇳' },
            'as': { name: 'Assamese', flag: '🇮🇳' },
            'bh': { name: 'Bhojpuri', flag: '🇮🇳' },
            'mai': { name: 'Maithili', flag: '🇮🇳' },
            'mag': { name: 'Magahi', flag: '🇮🇳' },
            'ne': { name: 'Nepali', flag: '🇳🇵' },
            'sd': { name: 'Sindhi', flag: '🇮🇳' },
            'ks': { name: 'Kashmiri', flag: '🇮🇳' },
            'doi': { name: 'Dogri', flag: '🇮🇳' },
            'kok': { name: 'Konkani', flag: '🇮🇳' },
            'mni': { name: 'Manipuri', flag: '🇮🇳' },
            'sat': { name: 'Santali', flag: '🇮🇳' },
            'brx': { name: 'Bodo', flag: '🇮🇳' },
            'gom': { name: 'Goan Konkani', flag: '🇮🇳' },
            'raj': { name: 'Rajasthani', flag: '🇮🇳' },
            'bpy': { name: 'Bishnupriya', flag: '🇮🇳' },
            'hne': { name: 'Chhattisgarhi', flag: '🇮🇳' },
            'gon': { name: 'Gondi', flag: '🇮🇳' },
            'kha': { name: 'Khasi', flag: '🇮🇳' },
            'mjz': { name: 'Majhi', flag: '🇮🇳' },
            'new': { name: 'Newari', flag: '🇳🇵' },
            'bho': { name: 'Bhojpuri', flag: '🇮🇳' },
            'awa': { name: 'Awadhi', flag: '🇮🇳' },
            'mag': { name: 'Magadhi', flag: '🇮🇳' },
            
            // African Languages
            'sw': { name: 'Swahili', flag: '🇰🇪' },
            'zu': { name: 'Zulu', flag: '🇿🇦' },
            'xh': { name: 'Xhosa', flag: '🇿🇦' },
            'af': { name: 'Afrikaans', flag: '🇿🇦' },
            'am': { name: 'Amharic', flag: '🇪🇹' },
            'ha': { name: 'Hausa', flag: '🇳🇬' },
            'ig': { name: 'Igbo', flag: '🇳🇬' },
            'yo': { name: 'Yoruba', flag: '🇳🇬' },
            'rw': { name: 'Kinyarwanda', flag: '🇷🇼' },
            'mg': { name: 'Malagasy', flag: '🇲🇬' },
            'sn': { name: 'Shona', flag: '🇿🇼' },
            'so': { name: 'Somali', flag: '🇸🇴' },
            
            // European Languages
            'eu': { name: 'Basque', flag: '🇪🇸' },
            'ca': { name: 'Catalan', flag: '🇪🇸' },
            'gl': { name: 'Galician', flag: '🇪🇸' },
            'cy': { name: 'Welsh', flag: '🏴󠁧󠁢󠁷󠁬󠁳󠁿' },
            'ga': { name: 'Irish', flag: '🇮🇪' },
            'gd': { name: 'Scottish Gaelic', flag: '🏴󠁧󠁢󠁳󠁣󠁴󠁿' },
            'is': { name: 'Icelandic', flag: '🇮🇸' },
            'mt': { name: 'Maltese', flag: '🇲🇹' },
            'sq': { name: 'Albanian', flag: '🇦🇱' },
            'mk': { name: 'Macedonian', flag: '🇲🇰' },
            'bs': { name: 'Bosnian', flag: '🇧🇦' },
            'me': { name: 'Montenegrin', flag: '🇲🇪' },
            
            // Middle Eastern Languages
            'ku': { name: 'Kurdish', flag: '🏴' },
            'az': { name: 'Azerbaijani', flag: '🇦🇿' },
            'ka': { name: 'Georgian', flag: '🇬🇪' },
            'hy': { name: 'Armenian', flag: '🇦🇲' },
            'ps': { name: 'Pashto', flag: '🇦🇫' },
            'tg': { name: 'Tajik', flag: '🇹🇯' },
            'uz': { name: 'Uzbek', flag: '🇺🇿' },
            'kk': { name: 'Kazakh', flag: '🇰🇿' },
            'ky': { name: 'Kyrgyz', flag: '🇰🇬' },
            'tk': { name: 'Turkmen', flag: '🇹🇲' },
            'mn': { name: 'Mongolian', flag: '🇲🇳' },
            
            // Southeast Asian Languages
            'my': { name: 'Myanmar (Burmese)', flag: '🇲🇲' },
            'km': { name: 'Khmer', flag: '🇰🇭' },
            'lo': { name: 'Lao', flag: '🇱🇦' },
            'si': { name: 'Sinhala', flag: '🇱🇰' },
            'dv': { name: 'Maldivian', flag: '🇲🇻' },
            
            // Other Asian Languages
            'ug': { name: 'Uyghur', flag: '🇨🇳' },
            'bo': { name: 'Tibetan', flag: '🏔️' },
            'dz': { name: 'Dzongkha', flag: '🇧🇹' },
            
            // Pacific Languages
            'haw': { name: 'Hawaiian', flag: '🏝️' },
            'mi': { name: 'Maori', flag: '🇳🇿' },
            'sm': { name: 'Samoan', flag: '🇼🇸' },
            'to': { name: 'Tongan', flag: '🇹🇴' },
            'fj': { name: 'Fijian', flag: '🇫🇯' },
            
            // Additional Languages
            'jv': { name: 'Javanese', flag: '🇮🇩' },
            'su': { name: 'Sundanese', flag: '🇮🇩' },
            'ceb': { name: 'Cebuano', flag: '🇵🇭' },
            'hil': { name: 'Hiligaynon', flag: '🇵🇭' },
            'war': { name: 'Waray', flag: '🇵🇭' },
            'bcl': { name: 'Bicolano', flag: '🇵🇭' },
            'pam': { name: 'Kapampangan', flag: '🇵🇭' },
            'lb': { name: 'Luxembourgish', flag: '🇱🇺' },
            'rm': { name: 'Romansh', flag: '🇨🇭' },
            'fo': { name: 'Faroese', flag: '🇫🇴' },
            'kl': { name: 'Greenlandic', flag: '🇬🇱' }
        };
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeSpeechRecognition();
        this.initializeVoices();
        this.initializeImageGeneration();
        this.loadSettings();
        this.loadChatHistory(); // Load chat history on initialization
        this.updateConnectionStatus('Connecting...', 'connecting');
    }

    initializeImageGeneration() {
        // Set up image generation elements and handlers
        const imageGenBtn = document.getElementById('imageGenBtn');
        const imageGenModal = document.getElementById('imageGenModal');
        const closeImageGen = document.getElementById('closeImageGen');
        const genMode = document.getElementById('genMode');
        const textInputSection = document.getElementById('textInputSection');
        const voiceInputSection = document.getElementById('voiceInputSection');
        const imageVoiceBtn = document.getElementById('imageVoiceBtn');
        const imagePrompt = document.getElementById('imagePrompt');
        const generateBtn = document.getElementById('generateBtn');
        const genStatus = document.getElementById('genStatus');
        const imageContainer = document.querySelector('.image-container');
        const downloadBtn = document.getElementById('downloadBtn');
        const shareBtn = document.getElementById('shareBtn');

        if (!imageGenBtn || !imageGenModal) {
            console.error('Image generation elements not found');
            return;
        }

        // Open/close modal
        imageGenBtn.addEventListener('click', () => {
            imageGenModal.style.display = 'flex';
        });

        closeImageGen.addEventListener('click', () => {
            imageGenModal.style.display = 'none';
        });

        // Switch between text/voice input
        genMode.addEventListener('change', () => {
            if (genMode.value === 'text') {
                textInputSection.style.display = 'block';
                voiceInputSection.style.display = 'none';
            } else {
                textInputSection.style.display = 'none';
                voiceInputSection.style.display = 'block';
            }
        });

        // Enable/disable generate button based on input
        imagePrompt.addEventListener('input', () => {
            generateBtn.disabled = !imagePrompt.value.trim();
        });

        // Voice recording for image prompt
        imageVoiceBtn.addEventListener('click', () => {
            if (!this.isRecordingImagePrompt) {
                this.startImageVoiceRecording();
            } else {
                this.stopImageVoiceRecording();
            }
        });

        // Generate image
        generateBtn.addEventListener('click', async () => {
            if (this.isGeneratingImage) return;

            const prompt = genMode.value === 'text' 
                ? imagePrompt.value 
                : document.getElementById('recognizedText').textContent;

            if (!prompt) {
                this.showError('Please provide a description first');
                return;
            }

            this.isGeneratingImage = true;
            generateBtn.disabled = true;
            genStatus.textContent = 'Generating image...';
            imageContainer.innerHTML = '<div class="loading-spinner"></div>';

            try {
                const response = await fetch('/api/generate-image', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ prompt })
                });

                const data = await response.json();

                if (data.success && data.image) {
                    const img = document.createElement('img');
                    img.src = `data:image/png;base64,${data.image}`;
                    imageContainer.innerHTML = '';
                    imageContainer.appendChild(img);

                    downloadBtn.style.display = 'block';
                    shareBtn.style.display = 'block';

                    // Set up download button
                    downloadBtn.onclick = () => {
                        const link = document.createElement('a');
                        link.href = img.src;
                        link.download = 'generated-image.png';
                        link.click();
                    };

                    // Set up share button
                    shareBtn.onclick = () => {
                        this.shareGeneratedImage(img.src, prompt);
                        imageGenModal.style.display = 'none';
                    };
                } else {
                    throw new Error(data.error || 'Failed to generate image');
                }
            } catch (error) {
                console.error('Image generation error:', error);
                this.showError('Failed to generate image: ' + error.message);
                imageContainer.innerHTML = '<div class="error-message">Generation failed</div>';
            } finally {
                this.isGeneratingImage = false;
                generateBtn.disabled = false;
                genStatus.textContent = '';
            }
        });
    }

    async startImageVoiceRecording() {
        if (!this.recognition) {
            this.showError('Speech recognition not supported');
            return;
        }

        // Request microphone permission first if available
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
            } catch (error) {
                console.error('Microphone permission denied:', error);
                this.showError('Microphone access denied. Please allow microphone access and try again.');
                return;
            }
        }

        const imageVoiceBtn = document.getElementById('imageVoiceBtn');
        const imageVoiceIndicator = document.getElementById('imageVoiceIndicator');
        const recognizedText = document.getElementById('recognizedText');
        const generateBtn = document.getElementById('generateBtn');

        this.isRecordingImagePrompt = true;
        imageVoiceBtn.classList.add('active');
        imageVoiceBtn.innerHTML = '<i class="fas fa-stop"></i><span>Stop Recording</span>';
        imageVoiceIndicator.classList.add('active');

        // Set up recognition for image prompt
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = this.settings.userLanguage || 'en-US';

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            recognizedText.textContent = transcript;
            generateBtn.disabled = false;
        };

        this.recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            this.showError('Voice recognition error: ' + event.error);
            this.stopImageVoiceRecording();
        };

        this.recognition.onend = () => {
            this.stopImageVoiceRecording();
        };

        this.recognition.start();
    }

    stopImageVoiceRecording() {
        if (!this.isRecordingImagePrompt) return;

        const imageVoiceBtn = document.getElementById('imageVoiceBtn');
        const imageVoiceIndicator = document.getElementById('imageVoiceIndicator');

        this.isRecordingImagePrompt = false;
        imageVoiceBtn.classList.remove('active');
        imageVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Record Description</span>';
        imageVoiceIndicator.classList.remove('active');

        if (this.recognition) {
            this.recognition.stop();
        }
    }

    shareGeneratedImage(imageUrl, prompt) {
        const chatMessages = document.getElementById('chatMessages');
        
        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Add prompt text
        const promptText = document.createElement('p');
        promptText.textContent = prompt;
        contentDiv.appendChild(promptText);
        
        // Add image
        const img = document.createElement('img');
        img.src = imageUrl;
        img.style.maxWidth = '100%';
        img.style.borderRadius = '8px';
        img.style.marginTop = '10px';
        contentDiv.appendChild(img);
        
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to the new message
        this.scrollToBottom();
        
        // Send to bot for potential response
        this.socket.emit('chat_message', {
            message: `[Generated Image] ${prompt}`,
            userLanguage: this.settings.userLanguage,
            botLanguage: this.settings.botLanguage,
            autoTranslate: this.settings.autoTranslate
        });
    }

    loadChatHistory() {
        fetch('/get_history')
            .then(response => response.json())
            .then(data => {
                if (data.history && data.history.length > 0) {
                    // Clear existing messages first
                    this.elements.chatMessages.innerHTML = '';
                    
                    // Group messages by date
                    let currentDate = '';
                    
                    data.history.forEach(msg => {
                        // Add date separator if date changes
                        const messageDate = new Date().toLocaleDateString();
                        if (messageDate !== currentDate) {
                            currentDate = messageDate;
                            const dateSeparator = document.createElement('div');
                            dateSeparator.className = 'history-date-separator';
                            dateSeparator.innerHTML = `<span>${currentDate}</span>`;
                            this.elements.chatMessages.appendChild(dateSeparator);
                        }
                        
                        // Create and append message
                        const messageElement = this.createProfessionalMessageElement(
                            msg.role,
                            msg.text,
                            msg.metadata
                        );
                        this.elements.chatMessages.appendChild(messageElement);
                    });
                    
                    // Scroll to bottom after loading history
                    this.scrollToBottom();
                }
            })
            .catch(error => {
                console.error('Error loading chat history:', error);
                this.showError('Failed to load chat history');
            });
    }
    
    initializeVoices() {
        if ('speechSynthesis' in window) {
            // Initialize available voices
            this.availableVoices = [];
            
            const loadVoices = () => {
                this.availableVoices = speechSynthesis.getVoices();
                console.log(`Loaded ${this.availableVoices.length} speech synthesis voices`);
                
                // Log available languages for debugging
                const languages = [...new Set(this.availableVoices.map(voice => voice.lang))].sort();
                console.log('Available speech languages:', languages);
                
                // Show notification about voice support
                if (this.availableVoices.length > 0) {
                    this.showNotification(`Text-to-speech ready with ${this.availableVoices.length} voices`, 'success');
                } else {
                    this.showNotification('Text-to-speech may have limited language support', 'warning');
                }
            };
            
            // Load voices immediately if available
            loadVoices();
            
            // Also listen for voices changed event (some browsers load voices asynchronously)
            if (speechSynthesis.addEventListener) {
                speechSynthesis.addEventListener('voiceschanged', loadVoices);
            } else {
                speechSynthesis.onvoiceschanged = loadVoices;
            }
        } else {
            console.warn('Speech synthesis not supported in this browser');
            this.showNotification('Text-to-speech not supported in this browser', 'warning');
        }
    }
    
    initializeSocket() {
        try {
            this.socket = io({
                timeout: 10000,
                transports: ['websocket', 'polling']
            });
            
            this.socket.on('connect', () => {
                console.log('Connected to server');
                this.updateConnectionStatus('Connected', 'connected');
            });
            
            this.socket.on('disconnect', (reason) => {
                console.log('Disconnected from server:', reason);
                this.updateConnectionStatus('Disconnected', 'disconnected');
                
                // Attempt to reconnect for certain reasons
                if (reason === 'io server disconnect') {
                    this.socket.connect();
                }
            });
            
            this.socket.on('connect_error', (error) => {
                console.error('Connection error:', error);
                this.updateConnectionStatus('Connection Error', 'error');
                this.showError('Failed to connect to server. Please check your internet connection and try refreshing the page.');
            });
            
        } catch (error) {
            console.error('Error initializing socket:', error);
            this.updateConnectionStatus('Failed to Connect', 'error');
            this.showError('Failed to initialize connection. Please refresh the page.');
        }
        
        this.socket.on('chat_response', (data) => {
            console.log('Received response:', data);
            this.displayBotMessage(data);
        });
        
        this.socket.on('bot_response', (data) => {
            console.log('Received bot response:', data);
            this.displayBotMessage(data);
        });
        
        this.socket.on('realtime_response', (data) => {
            console.log('Received realtime response:', data);
            
            if (data.error) {
                this.showError('Real-time error: ' + data.error);
            } else {
                this.addRealtimeMessage('bot', data.response);
                
                // Auto-speak if enabled
                if (this.autoSpeakEnabled) {
                    this.speakText(data.response);
                }
                
                // After bot responds, wait for user to manually start next input
                this.waitingForUserInput = true;
            }
            
            // Update bot status to indicate waiting for user
            const botStatus = this.elements.botStatus;
            if (botStatus) {
                botStatus.querySelector('.fa-spin').style.display = 'none';
                botStatus.querySelector('span').textContent = 'Waiting for your input...';
            }
            
            // Make sure user can start recording for next turn
            if (this.elements.userVoiceBtn) {
                this.elements.userVoiceBtn.disabled = false;
                this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Speak</span>';
            }
        });
        
        this.socket.on('translation_error', (data) => {
            console.error('Translation error:', data);
            this.showError('Translation error: ' + data.error);
        });
        
        this.socket.on('error', (data) => {
            console.error('Server error:', data);
            this.showError('Server error: ' + (data.error || 'Unknown error'));
        });
    }
    
    initializeElements() {
        try {
            // DOM elements
            this.elements = {
                chatMessages: document.getElementById('chatMessages'),
                messageInput: document.getElementById('messageInput'),
                sendBtn: document.getElementById('sendBtn'),
                voiceBtn: document.getElementById('voiceBtn'),
                settingsBtn: document.getElementById('settingsBtn'),
                realtimeToggle: document.getElementById('realtimeToggle'),
                connectionStatus: document.getElementById('connectionStatus'),
                voiceIndicator: document.getElementById('voiceIndicator'),
                
                // Settings modal
                settingsModal: document.getElementById('settingsModal'),
                closeSettings: document.getElementById('closeSettings'),
                saveSettings: document.getElementById('saveSettings'),
                clearHistoryBtn: document.getElementById('clearHistoryBtn'),
                userLanguage: document.getElementById('userLanguage'),
                botLanguage: document.getElementById('botLanguage'),
                voiceResponse: document.getElementById('voiceResponse'),
                autoTranslate: document.getElementById('autoTranslate'),
                
                // Language selectors
                userLanguageSearch: document.getElementById('userLanguageSearch'),
                userLanguageDropdown: document.getElementById('userLanguageDropdown'),
                userLanguageSelected: document.getElementById('userLanguageSelected'),
                botLanguageSearch: document.getElementById('botLanguageSearch'),
                botLanguageDropdown: document.getElementById('botLanguageDropdown'),
                botLanguageSelected: document.getElementById('botLanguageSelected'),
                
                // Real-time conversation
                realtimeModal: document.getElementById('realtimeModal'),
                closeRealtime: document.getElementById('closeRealtime'),
                userRealtimeMessages: document.getElementById('userRealtimeMessages'),
                botRealtimeMessages: document.getElementById('botRealtimeMessages'),
                userVoiceBtn: document.getElementById('userVoiceBtn'),
                botStatus: document.querySelector('.bot-status'),
                
                // Enhanced real-time controls
                startConversationBtn: document.getElementById('startConversationBtn'),
                stopConversationBtn: document.getElementById('stopConversationBtn'),
                conversationStatus: document.getElementById('conversationStatus'),
                micStatus: document.getElementById('micStatus'),
                aiStatus: document.getElementById('aiStatus'),
                speechStatus: document.getElementById('speechStatus'),
                autoSpeak: document.getElementById('autoSpeak'),
                continuousMode: document.getElementById('continuousMode'),
                speakResponseBtn: document.getElementById('speakResponseBtn'),
                realtimeVoiceIndicator: document.getElementById('realtimeVoiceIndicator')
            };
            
            // Check for missing critical elements and log warnings
            const criticalElements = [
                'chatMessages', 'messageInput', 'sendBtn', 'voiceBtn', 
                'settingsBtn', 'realtimeToggle', 'connectionStatus'
            ];
            
            const missingElements = [];
            for (const elementName of criticalElements) {
                if (!this.elements[elementName]) {
                    missingElements.push(elementName);
                    console.error(`Critical element missing: ${elementName}`);
                }
            }
            
            if (missingElements.length > 0) {
                console.error('Missing critical UI elements:', missingElements);
                this.showError(`UI Error: Missing elements: ${missingElements.join(', ')}. Please refresh the page.`);
            }
            
            // Initialize language selectors
            this.initializeLanguageSelectors();
            
        } catch (error) {
            console.error('Error initializing elements:', error);
            alert('Failed to initialize UI elements. Please refresh the page.');
        }
    }
    
    initializeLanguageSelectors() {
        try {
            // Initialize both user and bot language selectors
            this.setupLanguageSelector('user');
            this.setupLanguageSelector('bot');
        } catch (error) {
            console.error('Error initializing language selectors:', error);
        }
    }
    
    setupLanguageSelector(type) {
        const searchElement = this.elements[`${type}LanguageSearch`];
        const dropdownElement = this.elements[`${type}LanguageDropdown`];
        const selectedElement = this.elements[`${type}LanguageSelected`];
        const hiddenInput = this.elements[`${type}Language`];
        
        if (!searchElement || !dropdownElement || !selectedElement || !hiddenInput) {
            console.warn(`Language selector elements missing for ${type}`);
            return;
        }
        
        // Populate dropdown with all languages
        this.populateLanguageDropdown(dropdownElement, type);
        
        // Toggle dropdown visibility
        selectedElement.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleLanguageDropdown(type);
        });
        
        // Search functionality
        searchElement.addEventListener('input', (e) => {
            this.filterLanguages(type, e.target.value);
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.language-selector')) {
                this.closeLanguageDropdown(type);
            }
        });
        
        // Handle keyboard navigation
        searchElement.addEventListener('keydown', (e) => {
            this.handleLanguageKeyNavigation(type, e);
        });
    }
    
    populateLanguageDropdown(dropdown, type) {
        dropdown.innerHTML = '';
        
        // Sort languages alphabetically
        const sortedLanguages = Object.entries(this.languages).sort((a, b) => 
            a[1].name.localeCompare(b[1].name)
        );
        
        sortedLanguages.forEach(([code, lang]) => {
            const option = document.createElement('div');
            option.className = 'language-option';
            option.dataset.code = code;
            option.innerHTML = `
                <span>
                    <span class="language-flag">${lang.flag}</span>
                    ${lang.name}
                </span>
                <span class="language-code">${code.toUpperCase()}</span>
            `;
            
            option.addEventListener('click', () => {
                this.selectLanguage(type, code, lang.name);
            });
            
            dropdown.appendChild(option);
        });
    }
    
    toggleLanguageDropdown(type) {
        const dropdown = this.elements[`${type}LanguageDropdown`];
        const selected = this.elements[`${type}LanguageSelected`];
        const search = this.elements[`${type}LanguageSearch`];
        
        if (dropdown.classList.contains('show')) {
            this.closeLanguageDropdown(type);
        } else {
            // Close other dropdowns first
            this.closeAllLanguageDropdowns();
            
            dropdown.classList.add('show');
            selected.classList.add('active');
            search.style.display = 'block';
            search.focus();
            
            // Reset search
            search.value = '';
            this.filterLanguages(type, '');
        }
    }
    
    closeLanguageDropdown(type) {
        const dropdown = this.elements[`${type}LanguageDropdown`];
        const selected = this.elements[`${type}LanguageSelected`];
        const search = this.elements[`${type}LanguageSearch`];
        
        dropdown.classList.remove('show');
        selected.classList.remove('active');
        search.style.display = 'none';
    }
    
    closeAllLanguageDropdowns() {
        ['user', 'bot'].forEach(type => {
            this.closeLanguageDropdown(type);
        });
    }
    
    filterLanguages(type, searchTerm) {
        const dropdown = this.elements[`${type}LanguageDropdown`];
        const options = dropdown.querySelectorAll('.language-option');
        const term = searchTerm.toLowerCase();
        
        options.forEach(option => {
            const langName = option.textContent.toLowerCase();
            const langCode = option.dataset.code.toLowerCase();
            
            if (langName.includes(term) || langCode.includes(term)) {
                option.style.display = 'flex';
            } else {
                option.style.display = 'none';
            }
        });
    }
    
    selectLanguage(type, code, name) {
        const selected = this.elements[`${type}LanguageSelected`];
        const hiddenInput = this.elements[`${type}Language`];
        const lang = this.languages[code];
        
        // Update hidden input value
        hiddenInput.value = code;
        
        // Update displayed selection
        selected.querySelector('span').innerHTML = `
            <span class="language-flag">${lang.flag}</span>
            ${name}
        `;
        
        // Update settings
        this.settings[`${type}Language`] = code;
        
        // Close dropdown
        this.closeLanguageDropdown(type);
        
        // Update speech recognition language if user language changed
        if (type === 'user' && this.recognition) {
            this.recognition.lang = this.getLanguageCode(code);
        }
        if (type === 'user' && this.realtimeRecognition) {
            this.realtimeRecognition.lang = this.getLanguageCode(code);
        }
        
        // Check speech synthesis support for bot language
        if (type === 'bot' && this.availableVoices && this.availableVoices.length > 0) {
            const bestVoice = this.getBestVoiceForLanguage(code);
            if (bestVoice) {
                this.showNotification(`✓ Text-to-speech available for ${name}`, 'success');
            } else if (this.isLanguageSupported(code)) {
                this.showNotification(`⚠ Basic text-to-speech available for ${name}`, 'warning');
            } else {
                this.showNotification(`⚠ Text-to-speech may not work optimally for ${name}. Will use fallback.`, 'warning');
            }
        }
        
        console.log(`${type} language changed to: ${name} (${code})`);
    }
    
    getLanguageCode(code) {
        // Convert some common codes to speech recognition compatible format
        const speechCodes = {
            'zh': 'zh-CN',
            'zh-TW': 'zh-TW',
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'ar': 'ar-SA',
            'hi': 'hi-IN',
            'te': 'te-IN',
            'ta': 'ta-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'bn': 'bn-IN',
            'gu': 'gu-IN',
            'mr': 'mr-IN',
            'pa': 'pa-IN',
            'or': 'or-IN',
            'as': 'as-IN'
        };
        
        return speechCodes[code] || code;
    }
    
    handleLanguageKeyNavigation(type, e) {
        const dropdown = this.elements[`${type}LanguageDropdown`];
        const visibleOptions = dropdown.querySelectorAll('.language-option[style*="flex"]');
        
        if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
            e.preventDefault();
            // Handle arrow key navigation through options
            // This would require more complex state tracking
        } else if (e.key === 'Enter') {
            e.preventDefault();
            // Select first visible option
            if (visibleOptions.length > 0) {
                visibleOptions[0].click();
            }
        } else if (e.key === 'Escape') {
            this.closeLanguageDropdown(type);
        }
    }
    
    initializeEventListeners() {
        // Main chat interface
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });

        // Game button
        const gameBtn = document.getElementById('gameBtn');
        if (gameBtn) {
            gameBtn.addEventListener('click', () => {
                window.location.href = '/tictactoe';
            });
        }

        // Context menu event listeners
        document.addEventListener('mouseup', (e) => {
            console.log('mouseup event triggered'); // Debug log
            this.handleTextSelection(e);
        });
        
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#contextMenu')) {
                this.hideContextMenu();
            }
        });
        
        // Context menu items
        document.getElementById('askFollowUp').addEventListener('click', (e) => {
            e.stopPropagation();
            const selectedText = window.getSelection().toString().trim();
            this.askFollowUpQuestion(selectedText, 'follow-up');
        });
        
        document.getElementById('askForExplanation').addEventListener('click', () => {
            const selectedText = window.getSelection().toString();
            this.askFollowUpQuestion(selectedText, 'explanation');
        });
        
        document.getElementById('askForExample').addEventListener('click', () => {
            const selectedText = window.getSelection().toString();
            this.askFollowUpQuestion(selectedText, 'example');
        });
        
        // History button
        document.getElementById('historyBtn').addEventListener('click', () => this.openHistory());
        document.getElementById('closeHistory').addEventListener('click', () => this.closeHistory());
        document.getElementById('closeHistoryBtn').addEventListener('click', () => this.closeHistory());
        document.getElementById('clearHistoryBtnModal').addEventListener('click', () => this.clearChatHistory());
        this.elements.voiceBtn.addEventListener('click', () => this.toggleVoiceRecording());
        
        // Settings
        this.elements.settingsBtn.addEventListener('click', () => this.openSettings());
        this.elements.closeSettings.addEventListener('click', () => this.closeSettings());
        this.elements.saveSettings.addEventListener('click', () => this.saveSettings());
        this.elements.clearHistoryBtn.addEventListener('click', () => this.clearChatHistory());
        
        // Realtime conversation
        if (this.elements.realtimeToggle) {
            console.log('Adding event listener to realtimeToggle button');
            this.elements.realtimeToggle.addEventListener('click', () => {
                console.log('Real-time toggle button clicked!');
                this.toggleRealtimeMode();
            });
        } else {
            console.error('realtimeToggle button not found!');
        }
        
        this.elements.closeRealtime.addEventListener('click', () => this.toggleRealtimeMode());
        
        // Enhanced real-time conversation controls
        this.elements.startConversationBtn.addEventListener('click', () => this.startRealtimeConversation());
        this.elements.stopConversationBtn.addEventListener('click', () => this.stopRealtimeConversation());
        this.elements.userVoiceBtn.addEventListener('click', () => this.toggleRealtimeListening());
        this.elements.speakResponseBtn.addEventListener('click', () => this.speakLastBotResponse());
        
        // Settings for real-time conversation
        this.elements.autoSpeak.addEventListener('change', (e) => {
            this.autoSpeakEnabled = e.target.checked;
        });
        this.elements.continuousMode.addEventListener('change', (e) => {
            this.continuousMode = e.target.checked;
            if (this.conversationActive) {
                this.updateListeningMode();
            }
        });
        
        // Modal backdrop click
        this.elements.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.settingsModal) this.closeSettings();
        });
        this.elements.realtimeModal.addEventListener('click', (e) => {
            if (e.target === this.elements.realtimeModal) this.closeRealtimeMode();
        });
    }
    
    initializeSpeechRecognition() {
        try {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                // Main speech recognition
                this.recognition = new SpeechRecognition();
                this.recognition.continuous = false;
                this.recognition.interimResults = false;
                this.recognition.lang = this.settings.userLanguage || 'en-US';
                
                this.recognition.onresult = (event) => {
                    try {
                        const transcript = event.results[0][0].transcript;
                        if (this.elements.messageInput) {
                            this.elements.messageInput.value = transcript;
                            this.sendMessage();
                        }
                    } catch (error) {
                        console.error('Error processing speech result:', error);
                        this.showError('Error processing speech input.');
                    }
                };
                
                this.recognition.onerror = (event) => {
                    console.error('Speech recognition error:', event.error);
                    if (event.error === 'not-allowed') {
                        this.showError('Microphone access denied. Please allow microphone access in your browser settings or use HTTPS.');
                    } else if (event.error !== 'no-speech' && event.error !== 'aborted') {
                        this.showError('Voice recognition error: ' + event.error);
                    }
                };
                
                this.recognition.onend = () => {
                    this.isRecording = false;
                    if (this.elements.voiceBtn) {
                        this.elements.voiceBtn.classList.remove('recording');
                    }
                    if (this.elements.voiceIndicator) {
                        this.elements.voiceIndicator.classList.remove('active');
                    }
                };
                
            } else {
                console.warn('Speech recognition not supported');
                if (this.elements.voiceBtn) {
                    this.elements.voiceBtn.style.display = 'none';
                }
            }
            
        } catch (error) {
            console.error('Error initializing speech recognition:', error);
            this.showError('Failed to initialize voice recognition.');
        }
        
        // Initialize real-time recognition separately
        this.initializeRealtimeRecognition();
    }
    
    initializeRealtimeRecognition() {
        try {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                
                // Realtime speech recognition - only create if it doesn't exist
                if (!this.realtimeRecognition) {
                    this.realtimeRecognition = new SpeechRecognition();
                    this.realtimeRecognition.continuous = true;
                    this.realtimeRecognition.interimResults = true;
                    this.realtimeRecognition.lang = this.settings.userLanguage || 'en-US';
                    this.realtimeRecognition.maxAlternatives = 1;
                    
                    // Enhanced tracking for better deduplication
                    this.speechSession = {
                        processedMessages: new Set(),
                        lastFinalResult: '',
                        silenceTimer: null,
                        isProcessing: false
                    };
                    
                    this.realtimeRecognition.onresult = (event) => {
                        if (this.speechSession.isProcessing) return;
                        
                        let latestFinal = '';
                        let latestInterim = '';
                        
                        // Get the latest results
                        for (let i = 0; i < event.results.length; i++) {
                            const transcript = event.results[i][0].transcript.trim();
                            if (event.results[i].isFinal && transcript) {
                                latestFinal = transcript;
                            } else if (!event.results[i].isFinal && transcript) {
                                latestInterim = transcript;
                            }
                        }
                        
                        // Handle final results
                        if (latestFinal && latestFinal !== this.speechSession.lastFinalResult) {
                            this.processFinalSpeechResult(latestFinal);
                        }
                        
                        // Handle interim results
                        if (latestInterim && !latestFinal) {
                            this.showInterimMessage(latestInterim);
                        }
                    };
                    
                    this.realtimeRecognition.onerror = (event) => {
                        console.error('Realtime recognition error:', event.error);
                        if (event.error === 'network') {
                            console.log('Network error, attempting to restart...');
                            this.restartRealtimeRecognition();
                        }
                    };
                    
                    this.realtimeRecognition.onend = () => {
                        console.log('Speech recognition ended');
                        if (this.conversationActive && this.isRealtimeRecording && !this.waitingForUserInput) {
                            setTimeout(() => {
                                if (this.conversationActive && this.isRealtimeRecording && !this.waitingForUserInput) {
                                    this.restartRealtimeRecognition();
                                }
                            }, 100);
                        } else {
                            this.isRealtimeRecording = false;
                            if (this.elements.userVoiceBtn) {
                                this.elements.userVoiceBtn.classList.remove('recording');
                                this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Speak</span>';
                            }
                        }
                    };
                    
                    this.realtimeRecognition.onstart = () => {
                        console.log('Speech recognition started');
                        this.speechSession.processedMessages.clear();
                        this.speechSession.lastFinalResult = '';
                    };
                }
            } else {
                console.warn('Real-time speech recognition not supported');
            }
        } catch (error) {
            console.error('Error initializing real-time speech recognition:', error);
            this.showError('Failed to initialize real-time voice recognition.');
        }
    }
    
    processFinalSpeechResult(transcript) {
        // Normalize transcript for better comparison
        const normalizedTranscript = transcript.toLowerCase().trim();
        
        // Create a hash of the message to prevent exact duplicates
        const messageHash = this.hashMessage(normalizedTranscript);
        
        // Check if we've already processed this exact message
        if (this.speechSession.processedMessages.has(messageHash)) {
            console.log('Duplicate message hash detected, skipping:', transcript);
            return;
        }
        
        // Check against last user message with similarity
        const lastUserMessage = this.getLastUserMessage();
        if (this.isSimilarMessage(transcript, lastUserMessage)) {
            console.log('Similar message detected, skipping:', transcript);
            return;
        }
        
        // Check if message is too short or meaningless
        if (normalizedTranscript.length < 3 || this.isNoisyTranscript(normalizedTranscript)) {
            console.log('Noisy or too short transcript, skipping:', transcript);
            return;
        }
        
        // Mark as processing to prevent concurrent processing
        this.speechSession.isProcessing = true;
        
        console.log('Processing new speech result:', transcript);
        
        // Add to processed set
        this.speechSession.processedMessages.add(messageHash);
        this.speechSession.lastFinalResult = transcript;
        
        // Process the message
        this.addRealtimeMessage('user', transcript);
        this.sendRealtimeMessage(transcript);
        
        // Stop recording after processing user message - wait for bot response
        this.waitingForUserInput = false; // User has provided input, now waiting for bot
        this.stopRealtimeRecording();
        
        // Reset processing flag after a short delay
        setTimeout(() => {
            this.speechSession.isProcessing = false;
        }, 1000); // Increased delay to prevent rapid duplicates
    }
    
    hashMessage(message) {
        // Simple hash function for message deduplication
        let hash = 0;
        const normalized = message.toLowerCase().trim();
        for (let i = 0; i < normalized.length; i++) {
            const char = normalized.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash.toString();
    }
    
    isSimilarMessage(message1, message2) {
        if (!message1 || !message2) return false;
        
        const norm1 = message1.toLowerCase().trim();
        const norm2 = message2.toLowerCase().trim();
        
        // Exact match
        if (norm1 === norm2) return true;
        
        // Check if one message contains the other (for partial matches)
        if (norm1.length > 10 && norm2.length > 10) {
            return norm1.includes(norm2) || norm2.includes(norm1);
        }
        
        // Check similarity for shorter messages
        return this.calculateSimilarity(norm1, norm2) > 0.8;
    }
    
    calculateSimilarity(str1, str2) {
        // Simple Levenshtein distance based similarity
        const longer = str1.length > str2.length ? str1 : str2;
        const shorter = str1.length > str2.length ? str2 : str1;
        
        if (longer.length === 0) return 1.0;
        
        const editDistance = this.levenshteinDistance(longer, shorter);
        return (longer.length - editDistance) / longer.length;
    }
    
    levenshteinDistance(str1, str2) {
        const matrix = [];
        
        for (let i = 0; i <= str2.length; i++) {
            matrix[i] = [i];
        }
        
        for (let j = 0; j <= str1.length; j++) {
            matrix[0][j] = j;
        }
        
        for (let i = 1; i <= str2.length; i++) {
            for (let j = 1; j <= str1.length; j++) {
                if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }
        
        return matrix[str2.length][str1.length];
    }
    
    isNoisyTranscript(transcript) {
        // Filter out common speech recognition noise
        const noisePatterns = [
            /^(um|uh|er|ah|hmm|hm)$/i,
            /^(you|the|and|but|so)$/i,
            /^[^a-zA-Z]*$/,  // Only symbols/numbers
            /^.{1,2}$/       // Too short
        ];
        
        return noisePatterns.some(pattern => pattern.test(transcript));
    }
    
    restartRealtimeRecognition() {
        if (!this.realtimeRecognition || !this.conversationActive) return;
        
        try {
            // Stop current recognition
            this.realtimeRecognition.stop();
            
            // Restart after a brief delay
            setTimeout(() => {
                if (this.conversationActive && this.isRealtimeRecording) {
                    this.realtimeRecognition.start();
                }
            }, 500);
        } catch (error) {
            console.error('Error restarting recognition:', error);
        }
    }
    
    updateConnectionStatus(message, className) {
        this.elements.connectionStatus.textContent = message;
        this.elements.connectionStatus.className = 'connection-status ' + className;
    }
    
    sendMessage() {
        try {
            const message = this.elements.messageInput?.value?.trim();
            if (!message) return;
            
            if (!this.socket || !this.socket.connected) {
                this.showError('Not connected to server. Please refresh the page.');
                return;
            }
            
            this.displayUserMessage(message);
            this.elements.messageInput.value = '';
            
            this.socket.emit('chat_message', {
                message: message,
                userLanguage: this.settings.userLanguage,
                botLanguage: this.settings.botLanguage,
                autoTranslate: this.settings.autoTranslate,
                session_id: this.getSessionId()
            });
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.showError('Failed to send message. Please try again.');
        }
    }
    
    displayUserMessage(message) {
        const messageElement = this.createMessageElement('user', message);
        this.elements.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    displayBotMessage(data) {
        // Handle different response formats
        let content = data.bot_response || data.translated || data.response || data.translated_response;
        let metadata = null;
        
        // Check for original message
        if (data.original_message && data.original_message !== content) {
            metadata = { original: data.original_message };
        } else if (data.original && data.original !== content) {
            metadata = { original: data.original };
        }

        // Check for image response
        let image = null;
        if (data.image) {
            image = `data:image/png;base64,${data.image}`;
            metadata = { ...metadata, image_prompt: data.image_prompt || content };
        }

        const messageElement = this.createProfessionalMessageElement('bot', content, metadata, image);
        this.elements.chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        if (this.settings.voiceResponse && content) {
            this.speakText(content);
        }
    }
    
    createProfessionalMessageElement(type, content, metadata = null, image = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        // Add timestamp
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        // Create header with bot name and timestamp
        if (type === 'bot') {
            const headerDiv = document.createElement('div');
            headerDiv.className = 'message-header';
            headerDiv.innerHTML = `
                <div class="bot-info">
                    <i class="fas fa-robot"></i>
                    <span class="bot-name">AI Assistant</span>
                </div>
                <span class="message-time">${timestamp}</span>
            `;
            messageDiv.appendChild(headerDiv);
        }
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Add image if present
        if (image) {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'message-image-container';
            
            const img = document.createElement('img');
            img.src = image;
            img.className = 'message-image';
            img.alt = metadata?.image_prompt || 'Generated image';
            imgContainer.appendChild(img);
            
            // Add download button
            const downloadBtn = document.createElement('button');
            downloadBtn.className = 'image-action-btn';
            downloadBtn.innerHTML = '<i class="fas fa-download"></i>';
            downloadBtn.title = 'Download Image';
            downloadBtn.onclick = () => {
                const link = document.createElement('a');
                link.href = image;
                link.download = 'generated-image.png';
                link.click();
            };
            imgContainer.appendChild(downloadBtn);
            
            contentDiv.appendChild(imgContainer);
        }
        
        // Format and add text content
        const formattedContent = this.formatBotResponse(content);
        const textContent = document.createElement('div');
        textContent.className = 'message-text';
        textContent.innerHTML = formattedContent;
        contentDiv.appendChild(textContent);
        
        messageDiv.appendChild(contentDiv);
        
        // Add speaker button for bot messages with text
        if (type === 'bot' && content) {
            const speakerBtn = document.createElement('button');
            speakerBtn.className = 'speaker-btn';
            speakerBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            speakerBtn.title = 'Listen to response';
            speakerBtn.onclick = () => this.speakMessage(content, speakerBtn);
            messageDiv.appendChild(speakerBtn);
        }
        
        // Add metadata if present
        if (metadata) {
            const metadataDiv = document.createElement('div');
            metadataDiv.className = 'message-metadata';
            let metadataContent = [];
            if (metadata.original) {
                metadataContent.push(`<small>Original: ${metadata.original}</small>`);
            }
            if (metadata.image_prompt) {
                metadataContent.push(`<small>Image prompt: "${metadata.image_prompt}"</small>`);
            }
            if (metadataContent.length > 0) {
                metadataDiv.innerHTML = metadataContent.join('<br>');
                messageDiv.appendChild(metadataDiv);
            }
        }
        
        return messageDiv;
    }

    formatBotResponse(content) {
        if (!content) return '';
        
        // Convert markdown-style formatting to HTML
        let formatted = content
            // Headers
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // Bold
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Bullet points
            .replace(/^\* (.+)$/gm, '<li>$1</li>')
            // Code blocks
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            // Line breaks
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        // Wrap bullet points in ul tags
        formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Wrap in paragraphs if not already formatted
        if (!formatted.includes('<p>') && !formatted.includes('<ul>')) {
            formatted = `<p>${formatted}</p>`;
        } else if (formatted.includes('</p><p>')) {
            formatted = `<p>${formatted}</p>`;
        }
        
        return formatted;
    }
    
    createMessageElement(type, content, metadata = null) {
        // Fallback for user messages - keep simple
        if (type === 'user') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(contentDiv);
            
            return messageDiv;
        } else {
            // Use professional formatting for bot messages
            return this.createProfessionalMessageElement(type, content, metadata);
        }
        return messageDiv;
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    handleTextSelection(e) {
        try {
            const selection = window.getSelection();
            const selectedText = selection.toString().trim();
            const contextMenu = document.getElementById('contextMenu');
            
            if (!contextMenu) {
                console.error('Context menu element not found');
                return;
            }
            
            // Always hide the menu first
            this.hideContextMenu();
            
            // Only proceed if we have selected text within a message
            if (!selectedText || !e.target.closest('.message-content')) {
                return;
            }
            
            console.log('Text selected:', selectedText);
            
            // Get selection coordinates
            const range = selection.getRangeAt(0);
            const rect = range.getBoundingClientRect();
            
            // Use mouse position if available, otherwise use selection bounds
            const x = typeof e.clientX !== 'undefined' ? e.clientX : rect.right;
            const y = typeof e.clientY !== 'undefined' ? e.clientY : rect.bottom;
            
            // Get viewport and scroll information
            const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
            const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
            const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
            const scrollY = window.pageYOffset || document.documentElement.scrollTop;
            
            // Get menu dimensions
            const menuWidth = 200;  // Approximate width
            const menuHeight = 150; // Approximate height
            
            // Calculate position ensuring menu stays within viewport
            let menuX = x + scrollX;
            let menuY = y + scrollY;
            
            // Adjust if menu would go outside right edge
            if (x + menuWidth > viewportWidth) {
                menuX = viewportWidth - menuWidth + scrollX;
            }
            
            // Adjust if menu would go outside bottom edge
            if (y + menuHeight > viewportHeight) {
                menuY = viewportHeight - menuHeight + scrollY;
            }
            
            // Ensure menu doesn't go outside left or top edges
            menuX = Math.max(scrollX, menuX);
            menuY = Math.max(scrollY, menuY);
            
            // Position and show menu
            contextMenu.style.left = `${menuX}px`;
            contextMenu.style.top = `${menuY}px`;
            contextMenu.classList.add('show');
            
            console.log('Menu positioned at:', menuX, menuY);
            
            // Prevent default context menu
            e.preventDefault();
        } catch (error) {
            console.error('Error handling text selection:', error);
        }
    }
    
    hideContextMenu() {
        const contextMenu = document.getElementById('contextMenu');
        contextMenu.classList.remove('show');
    }
    
    askFollowUpQuestion(selectedText, type) {
        if (!selectedText) return;
        
        let question = '';
        switch (type) {
            case 'follow-up':
                question = `Regarding "${selectedText}", can you tell me more about this?`;
                break;
            case 'explanation':
                question = `Can you explain in detail what "${selectedText}" means?`;
                break;
            case 'example':
                question = `Can you give me an example related to "${selectedText}"?`;
                break;
            default:
                question = `Tell me more about "${selectedText}"`;
        }
        
        // Add the question to the input field
        this.elements.messageInput.value = question;
        this.elements.messageInput.focus();
        
        // Hide context menu
        this.hideContextMenu();
    }
    
    async toggleVoiceRecording() {
        if (!this.recognition) {
            this.showError('Speech recognition not supported');
            return;
        }
        
        if (this.isRecording) {
            this.recognition.stop();
        } else {
            // Check if getUserMedia is available
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                try {
                    await navigator.mediaDevices.getUserMedia({ audio: true });
                } catch (error) {
                    console.error('Microphone permission denied:', error);
                    this.showError('Microphone access denied. Please allow microphone access and try again.');
                    return;
                }
            }
            
            this.isRecording = true;
            this.elements.voiceBtn.classList.add('recording');
            this.elements.voiceIndicator.classList.add('active');
            this.recognition.start();
        }
    }
    
    speakText(text) {
        if (this.currentAudio) {
            this.currentAudio.pause();
        }
        
        if ('speechSynthesis' in window) {
            const cleanText = this.cleanTextForSpeech(text);
            if (cleanText) {
                const utterance = new SpeechSynthesisUtterance(cleanText);
                
                // Get the best available voice for the language
                const bestVoice = this.getBestVoiceForLanguage(this.settings.botLanguage);
                if (bestVoice) {
                    utterance.voice = bestVoice;
                    utterance.lang = bestVoice.lang;
                } else {
                    // Fallback to language code with proper formatting
                    utterance.lang = this.getOptimalSpeechLanguage(this.settings.botLanguage);
                }
                
                // Set speech parameters for better quality
                utterance.rate = 0.9;
                utterance.pitch = 1.0;
                utterance.volume = 1.0;
                
                // Error handling
                utterance.onerror = (event) => {
                    console.error('Speech synthesis error:', event.error);
                    if (event.error !== 'interrupted' && event.error !== 'canceled') {
                        // Try fallback to English if original language fails
                        this.speakTextFallback(cleanText);
                    }
                };
                
                speechSynthesis.speak(utterance);
            }
        }
    }
    
    speakTextFallback(text) {
        try {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'en-US'; // Fallback to English
            utterance.rate = 0.9;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            
            console.log('Using English fallback for speech synthesis');
            speechSynthesis.speak(utterance);
        } catch (error) {
            console.error('Fallback speech synthesis also failed:', error);
            this.showNotification('Text-to-speech not available for this language', 'error');
        }
    }
    
    getBestVoiceForLanguage(languageCode) {
        if (!('speechSynthesis' in window)) return null;
        
        const voices = speechSynthesis.getVoices();
        if (voices.length === 0) {
            // Voices not loaded yet, return null and let it use language code
            return null;
        }
        
        // Map our language codes to common speech synthesis language codes
        const speechLanguageMap = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'it': 'it',
            'pt': 'pt',
            'ru': 'ru',
            'ja': 'ja',
            'ko': 'ko',
            'zh': 'zh',
            'zh-TW': 'zh-TW',
            'ar': 'ar',
            'hi': 'hi',
            'te': 'te',
            'ta': 'ta',
            'kn': 'kn',
            'ml': 'ml',
            'bn': 'bn',
            'gu': 'gu',
            'mr': 'mr',
            'pa': 'pa',
            'or': 'or',
            'as': 'as',
            'nl': 'nl',
            'sv': 'sv',
            'no': 'no',
            'da': 'da',
            'fi': 'fi',
            'pl': 'pl',
            'cs': 'cs',
            'sk': 'sk',
            'hu': 'hu',
            'ro': 'ro',
            'bg': 'bg',
            'hr': 'hr',
            'sr': 'sr',
            'sl': 'sl',
            'et': 'et',
            'lv': 'lv',
            'lt': 'lt',
            'el': 'el',
            'tr': 'tr',
            'he': 'he',
            'fa': 'fa',
            'ur': 'ur',
            'th': 'th',
            'vi': 'vi',
            'id': 'id',
            'ms': 'ms',
            'tl': 'tl'
        };
        
        const targetLang = speechLanguageMap[languageCode] || languageCode;
        
        // First try: exact language match
        let bestVoice = voices.find(voice => 
            voice.lang.toLowerCase().startsWith(targetLang.toLowerCase())
        );
        
        if (bestVoice) {
            console.log(`Found voice for ${languageCode}:`, bestVoice.name, bestVoice.lang);
            return bestVoice;
        }
        
        // Second try: for Indian languages, try common variations
        const indianLanguageVariations = {
            'hi': ['hi-IN', 'hi'],
            'te': ['te-IN', 'te'],
            'ta': ['ta-IN', 'ta'],
            'kn': ['kn-IN', 'kn'],
            'ml': ['ml-IN', 'ml'],
            'bn': ['bn-IN', 'bn-BD', 'bn'],
            'gu': ['gu-IN', 'gu'],
            'mr': ['mr-IN', 'mr'],
            'pa': ['pa-IN', 'pa'],
            'or': ['or-IN', 'or'],
            'as': ['as-IN', 'as'],
            'ur': ['ur-PK', 'ur-IN', 'ur']
        };
        
        if (indianLanguageVariations[languageCode]) {
            for (const variation of indianLanguageVariations[languageCode]) {
                bestVoice = voices.find(voice => 
                    voice.lang.toLowerCase() === variation.toLowerCase()
                );
                if (bestVoice) {
                    console.log(`Found Indian language voice for ${languageCode}:`, bestVoice.name, bestVoice.lang);
                    return bestVoice;
                }
            }
        }
        
        // Third try: language family fallbacks
        const languageFallbacks = {
            'te': ['hi-IN', 'en-IN'],
            'ta': ['hi-IN', 'en-IN'],
            'kn': ['hi-IN', 'en-IN'],
            'ml': ['hi-IN', 'en-IN'],
            'bn': ['hi-IN', 'en-IN'],
            'gu': ['hi-IN', 'en-IN'],
            'mr': ['hi-IN', 'en-IN'],
            'pa': ['hi-IN', 'en-IN'],
            'or': ['hi-IN', 'en-IN'],
            'as': ['hi-IN', 'en-IN'],
            'ur': ['hi-IN', 'en-IN'],
            'ne': ['hi-IN', 'en-IN'],
            'si': ['hi-IN', 'en-IN'],
            'my': ['th-TH', 'en-US'],
            'km': ['th-TH', 'en-US'],
            'lo': ['th-TH', 'en-US'],
            'ka': ['ru-RU', 'en-US'],
            'hy': ['ru-RU', 'en-US'],
            'az': ['tr-TR', 'en-US'],
            'kk': ['ru-RU', 'en-US'],
            'ky': ['ru-RU', 'en-US'],
            'uz': ['ru-RU', 'en-US'],
            'tg': ['ru-RU', 'en-US'],
            'mn': ['zh-CN', 'en-US']
        };
        
        if (languageFallbacks[languageCode]) {
            for (const fallback of languageFallbacks[languageCode]) {
                bestVoice = voices.find(voice => 
                    voice.lang.toLowerCase() === fallback.toLowerCase()
                );
                if (bestVoice) {
                    console.log(`Using fallback voice for ${languageCode}:`, bestVoice.name, bestVoice.lang);
                    return bestVoice;
                }
            }
        }
        
        console.log(`No suitable voice found for ${languageCode}, will use system default`);
        return null;
    }
    
    getOptimalSpeechLanguage(languageCode) {
        // Return optimized language codes for speech synthesis
        const speechCodes = {
            'en': 'en-US',
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-PT',
            'ru': 'ru-RU',
            'ja': 'ja-JP',
            'ko': 'ko-KR',
            'zh': 'zh-CN',
            'zh-TW': 'zh-TW',
            'ar': 'ar-SA',
            'hi': 'hi-IN',
            'te': 'te-IN',
            'ta': 'ta-IN',
            'kn': 'kn-IN',
            'ml': 'ml-IN',
            'bn': 'bn-IN',
            'gu': 'gu-IN',
            'mr': 'mr-IN',
            'pa': 'pa-IN',
            'or': 'or-IN',
            'as': 'as-IN',
            'ur': 'ur-PK',
            'ne': 'ne-NP',
            'si': 'si-LK',
            'th': 'th-TH',
            'vi': 'vi-VN',
            'id': 'id-ID',
            'ms': 'ms-MY',
            'tl': 'tl-PH',
            'nl': 'nl-NL',
            'sv': 'sv-SE',
            'no': 'no-NO',
            'da': 'da-DK',
            'fi': 'fi-FI',
            'pl': 'pl-PL',
            'cs': 'cs-CZ',
            'sk': 'sk-SK',
            'hu': 'hu-HU',
            'ro': 'ro-RO',
            'bg': 'bg-BG',
            'hr': 'hr-HR',
            'sr': 'sr-RS',
            'sl': 'sl-SI',
            'et': 'et-EE',
            'lv': 'lv-LV',
            'lt': 'lt-LT',
            'el': 'el-GR',
            'tr': 'tr-TR',
            'he': 'he-IL',
            'fa': 'fa-IR'
        };
        
        return speechCodes[languageCode] || languageCode;
    }
    
    getSupportedLanguages() {
        if (!('speechSynthesis' in window) || !this.availableVoices) {
            return [];
        }
        
        const supportedLangs = [...new Set(this.availableVoices.map(voice => {
            // Extract language code (remove country code)
            const langCode = voice.lang.split('-')[0].toLowerCase();
            return langCode;
        }))];
        
        return supportedLangs.sort();
    }
    
    isLanguageSupported(languageCode) {
        const supportedLanguages = this.getSupportedLanguages();
        return supportedLanguages.includes(languageCode.toLowerCase());
    }
    
    showLanguageSupport() {
        const supported = this.getSupportedLanguages();
        console.log('Supported speech synthesis languages:', supported);
        
        // Check current bot language support
        if (this.settings.botLanguage) {
            const isSupported = this.isLanguageSupported(this.settings.botLanguage);
            console.log(`Current bot language (${this.settings.botLanguage}) is ${isSupported ? 'supported' : 'not directly supported'}`);
            
            if (!isSupported) {
                this.showNotification(`Text-to-speech may not work optimally for ${this.languages[this.settings.botLanguage]?.name || this.settings.botLanguage}. Consider using a fallback language.`, 'warning');
            }
        }
    }
    
    cleanTextForSpeech(text) {
        if (!text) return '';
        
        let cleanText = text;
        
        // Remove HTML tags
        cleanText = cleanText.replace(/<[^>]*>/g, '');
        
        // Replace HTML entities
        cleanText = cleanText.replace(/&nbsp;/g, ' ')
                           .replace(/&amp;/g, 'and')
                           .replace(/&lt;/g, 'less than')
                           .replace(/&gt;/g, 'greater than')
                           .replace(/&quot;/g, '"')
                           .replace(/&#39;/g, "'")
                           .replace(/&[^;]+;/g, ' ');
        
        // Remove or replace special characters and symbols
        cleanText = cleanText.replace(/[*_~`]/g, '')  // Remove markdown symbols
                           .replace(/#{1,6}\s*/g, '')  // Remove markdown headers
                           .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')  // Convert markdown links to text
                           .replace(/```[^`]*```/g, 'code block')  // Replace code blocks
                           .replace(/`([^`]+)`/g, '$1')  // Remove inline code backticks
                           .replace(/\*\*([^*]+)\*\*/g, '$1')  // Remove bold markdown
                           .replace(/\*([^*]+)\*/g, '$1')  // Remove italic markdown
                           .replace(/__|__([^_]+)__|__/g, '$1')  // Remove underline markdown
                           .replace(/~~([^~]+)~~/g, '$1')  // Remove strikethrough markdown
                           .replace(/[•·▪▫→←↑↓]/g, '')  // Remove bullet points and arrows
                           .replace(/[℃℉°]/g, ' degrees ')  // Replace temperature symbols
                           .replace(/[©®™]/g, '')  // Remove copyright symbols
                           .replace(/[₹$€£¥]/g, '')  // Remove currency symbols
                           .replace(/[#@&%]/g, '')  // Remove hash, at, ampersand, percent
                           .replace(/[{}[\]()]/g, '')  // Remove brackets and parentheses
                           .replace(/[<>]/g, '')  // Remove angle brackets
                           .replace(/[|\\\/]/g, ' ')  // Replace pipes and slashes with space
                           .replace(/[+\-=]/g, ' ')  // Replace math symbols with space
                           .replace(/[!?]{2,}/g, '!')  // Replace multiple exclamation/question marks
                           .replace(/\.{2,}/g, '.')  // Replace multiple dots with single dot
                           .replace(/_{2,}/g, ' ')  // Replace multiple underscores
                           .replace(/\s{2,}/g, ' ')  // Replace multiple spaces with single space
                           .replace(/\n+/g, '. ')  // Replace newlines with periods
                           .replace(/\t+/g, ' ');  // Replace tabs with spaces
        
        // Clean up punctuation spacing
        cleanText = cleanText.replace(/\s+([,.!?;:])/g, '$1')  // Remove space before punctuation
                           .replace(/([,.!?;:])\s{2,}/g, '$1 ')  // Single space after punctuation
                           .replace(/([.!?])\s*([A-Z])/g, '$1 $2');  // Proper sentence spacing
        
        // Remove URLs
        cleanText = cleanText.replace(/https?:\/\/[^\s]+/g, 'link');
        cleanText = cleanText.replace(/www\.[^\s]+/g, 'website');
        
        // Remove email addresses
        cleanText = cleanText.replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, 'email address');
        
        // Clean up and trim
        cleanText = cleanText.trim();
        
        // If text is too short or only punctuation, return empty
        if (cleanText.length < 2 || /^[^\w\s]*$/.test(cleanText)) {
            return '';
        }
        
        return cleanText;
    }
    
    openHistory() {
        const historyModal = document.getElementById('historyModal');
        const historyMessages = document.getElementById('historyMessages');
        
        // Fetch chat history
        fetch('/get_history')
            .then(response => response.json())
            .then(data => {
                historyMessages.innerHTML = ''; // Clear existing messages
                
                if (data.history && data.history.length > 0) {
                    let currentDate = '';
                    
                    data.history.forEach(msg => {
                        // Add date separator if needed
                        const messageDate = new Date(msg.timestamp).toLocaleDateString();
                        if (messageDate !== currentDate) {
                            currentDate = messageDate;
                            const dateSeparator = document.createElement('div');
                            dateSeparator.className = 'history-date-separator';
                            dateSeparator.innerHTML = `<span>${currentDate}</span>`;
                            historyMessages.appendChild(dateSeparator);
                        }
                        
                        // Create message element
                        const messageElement = this.createProfessionalMessageElement(
                            msg.role,
                            msg.text,
                            msg.metadata
                        );
                        historyMessages.appendChild(messageElement);
                    });
                } else {
                    historyMessages.innerHTML = '<div class="message bot-message"><div class="message-content">No chat history available.</div></div>';
                }
            })
            .catch(error => {
                console.error('Error fetching history:', error);
                this.showError('Failed to load chat history');
            });
        
        historyModal.style.display = 'flex';
    }
    
    closeHistory() {
        document.getElementById('historyModal').style.display = 'none';
    }
    
    speakMessage(text, buttonElement) {
        // If this button is currently playing, stop the speech
        if (buttonElement.classList.contains('playing')) {
            if ('speechSynthesis' in window) {
                speechSynthesis.cancel();
            }
            buttonElement.classList.remove('playing');
            buttonElement.innerHTML = '<i class="fas fa-volume-up"></i>';
            buttonElement.title = 'Listen to response';
            // Clear any existing speech check intervals
            if (buttonElement.speechCheck) {
                clearInterval(buttonElement.speechCheck);
                buttonElement.speechCheck = null;
            }
            return;
        }
        
        // Stop any current speech and reset all other speaker buttons
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        
        // Remove playing state from all other speaker buttons
        document.querySelectorAll('.speaker-btn.playing').forEach(btn => {
            btn.classList.remove('playing');
            btn.innerHTML = '<i class="fas fa-volume-up"></i>';
            btn.title = 'Listen to response';
            // Clear any existing speech check intervals
            if (btn.speechCheck) {
                clearInterval(btn.speechCheck);
                btn.speechCheck = null;
            }
        });
        
        if ('speechSynthesis' in window) {
            // Clean the text using our comprehensive cleaning function
            const cleanText = this.cleanTextForSpeech(text);
            
            if (cleanText) {
                // Set button to playing state
                buttonElement.classList.add('playing');
                buttonElement.innerHTML = '<i class="fas fa-stop"></i>';
                buttonElement.title = 'Stop speaking';
                
                const utterance = new SpeechSynthesisUtterance(cleanText);
                
                // Get the best available voice for the language
                const bestVoice = this.getBestVoiceForLanguage(this.settings.botLanguage);
                if (bestVoice) {
                    utterance.voice = bestVoice;
                    utterance.lang = bestVoice.lang;
                } else {
                    utterance.lang = this.getOptimalSpeechLanguage(this.settings.botLanguage);
                }
                
                utterance.rate = 0.9;
                utterance.pitch = 1;
                utterance.volume = 1.0;
                
                utterance.onend = () => {
                    buttonElement.classList.remove('playing');
                    buttonElement.innerHTML = '<i class="fas fa-volume-up"></i>';
                    buttonElement.title = 'Listen to response';
                    // Clear interval when speech ends
                    if (buttonElement.speechCheck) {
                        clearInterval(buttonElement.speechCheck);
                        buttonElement.speechCheck = null;
                    }
                };
                
                utterance.onerror = (event) => {
                    buttonElement.classList.remove('playing');
                    buttonElement.innerHTML = '<i class="fas fa-volume-up"></i>';
                    buttonElement.title = 'Listen to response';
                    // Clear interval on error
                    if (buttonElement.speechCheck) {
                        clearInterval(buttonElement.speechCheck);
                        buttonElement.speechCheck = null;
                    }
                    // Only show error if it's not a user-initiated cancellation
                    if (event.error && event.error !== 'interrupted' && event.error !== 'canceled') {
                        console.error('Speech synthesis error:', event.error);
                        this.showError('Text-to-speech error: ' + event.error);
                    }
                };
                
                // Handle speech interruption (when user stops manually)
                utterance.onstart = () => {
                    // Set up a check to see if speech was cancelled manually
                    buttonElement.speechCheck = setInterval(() => {
                        if (!speechSynthesis.speaking && !speechSynthesis.pending) {
                            buttonElement.classList.remove('playing');
                            buttonElement.innerHTML = '<i class="fas fa-volume-up"></i>';
                            buttonElement.title = 'Listen to response';
                            if (buttonElement.speechCheck) {
                                clearInterval(buttonElement.speechCheck);
                                buttonElement.speechCheck = null;
                            }
                        }
                    }, 100);
                };
                
                try {
                    speechSynthesis.speak(utterance);
                } catch (error) {
                    console.error('Failed to start speech synthesis:', error);
                    buttonElement.classList.remove('playing');
                    buttonElement.innerHTML = '<i class="fas fa-volume-up"></i>';
                    buttonElement.title = 'Listen to response';
                    this.showError('Failed to start text-to-speech');
                }
            } else {
                this.showError('No text to speak');
            }
        } else {
            this.showError('Text-to-speech not supported in this browser');
        }
    }
    
    openSettings() {
        this.loadSettingsToModal();
        this.elements.settingsModal.style.display = 'flex';
    }
    
    closeSettings() {
        this.elements.settingsModal.style.display = 'none';
    }
    
    loadSettingsToModal() {
        // Update language selectors
        if (this.languages[this.settings.userLanguage]) {
            this.selectLanguage('user', this.settings.userLanguage, this.languages[this.settings.userLanguage].name);
        }
        if (this.languages[this.settings.botLanguage]) {
            this.selectLanguage('bot', this.settings.botLanguage, this.languages[this.settings.botLanguage].name);
        }
        
        // Update checkboxes
        if (this.elements.voiceResponse) {
            this.elements.voiceResponse.checked = this.settings.voiceResponse;
        }
        if (this.elements.autoTranslate) {
            this.elements.autoTranslate.checked = this.settings.autoTranslate;
        }
    }
    
    saveSettings() {
        // Get values from hidden inputs (updated by language selectors)
        this.settings.userLanguage = this.elements.userLanguage.value;
        this.settings.botLanguage = this.elements.botLanguage.value;
        
        if (this.elements.voiceResponse) {
            this.settings.voiceResponse = this.elements.voiceResponse.checked;
        }
        if (this.elements.autoTranslate) {
            this.settings.autoTranslate = this.elements.autoTranslate.checked;
        }
        
        // Update speech recognition language
        if (this.recognition) {
            this.recognition.lang = this.getLanguageCode(this.settings.userLanguage);
        }
        if (this.realtimeRecognition) {
            this.realtimeRecognition.lang = this.getLanguageCode(this.settings.userLanguage);
        }
        
        // Save to localStorage
        localStorage.setItem('chatbotSettings', JSON.stringify(this.settings));
        
        this.closeSettings();
        this.showSuccess('Settings saved successfully!');
    }
    
    clearChatHistory() {
        if (confirm('Are you sure you want to clear all chat history? This action cannot be undone.')) {
            // Clear UI
            this.elements.chatMessages.innerHTML = '';
            
            // Clear server-side history
            fetch('/api/clear-history', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.getSessionId()
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showSuccess('Chat history cleared successfully!');
                } else {
                    this.showError('Failed to clear history: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                this.showError('Error clearing history');
            });
        }
    }
    
    loadSettings() {
        const saved = localStorage.getItem('chatbotSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
    }
    
    toggleRealtimeMode() {
        console.log('toggleRealtimeMode called');
        const modal = this.elements.realtimeModal;
        
        if (!modal) {
            console.error('Real-time modal element not found!');
            this.showError('Real-time modal not found. Please refresh the page.');
            return;
        }
        
        console.log('Current modal display:', modal.style.display);
        
        if (modal.style.display === 'flex') {
            // Close the modal
            console.log('Closing real-time modal');
            modal.style.display = 'none';
            document.body.style.overflow = '';
            
            // Stop any active conversation
            if (this.conversationActive) {
                this.stopRealtimeConversation();
            }
        } else {
            // Open the modal
            console.log('Opening real-time modal');
            modal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
            
            // Initialize real-time recognition if not already done
            this.initializeRealTimeRecognition();
            
            this.showSuccess('Real-time conversation mode opened!');
        }
    }
    
    startRealtimeConversation() {
        if (!this.realtimeRecognition) {
            this.showError('Speech recognition not supported');
            return;
        }
        
        this.conversationActive = true;
        this.waitingForUserInput = true; // Start waiting for user input
        this.clearRealtimeMessages();
        
        // Update UI
        this.elements.startConversationBtn.style.display = 'none';
        this.elements.stopConversationBtn.style.display = 'flex';
        this.elements.userVoiceBtn.disabled = false;
        this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Speak</span>';
        this.elements.conversationStatus.textContent = 'Live Conversation';
        this.elements.botStatus.querySelector('span').textContent = 'Ready to listen...';
        
        // Update status lights
        this.updateStatusLight('mic', 'active');
        
        // Add natural welcome message
        const welcomeMessages = [
            '👋 Hello! Let\'s have a conversation. Click the microphone and tell me what\'s on your mind!',
            '🗣️ Hi there! I\'m here to chat. Click the mic button below and start speaking!',
            '💬 Ready to chat! Press the microphone button and say anything you\'d like to talk about.'
        ];
        const randomWelcome = welcomeMessages[Math.floor(Math.random() * welcomeMessages.length)];
        
        this.addRealtimeMessage('bot', randomWelcome);
        
        if (this.autoSpeakEnabled) {
            this.speakText(randomWelcome);
        }
        
        this.showSuccess('Real-time conversation started! Click the microphone to speak.');
    }
    
    stopRealtimeConversation() {
        this.conversationActive = false;
        
        if (this.isRealtimeRecording) {
            this.stopRealtimeRecording();
        }
        
        // Stop any current speech
        if ('speechSynthesis' in window) {
            speechSynthesis.cancel();
        }
        
        // Update UI
        this.elements.startConversationBtn.style.display = 'flex';
        this.elements.stopConversationBtn.style.display = 'none';
        this.elements.userVoiceBtn.disabled = true;
        this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click Start to Enable</span>';
        this.elements.conversationStatus.textContent = 'Conversation Ended';
        this.elements.botStatus.querySelector('span').textContent = 'Waiting to Start';
        
        // Reset status lights
        this.updateStatusLight('mic', 'inactive');
        this.updateStatusLight('ai', 'inactive');
        this.updateStatusLight('speech', 'inactive');
        
        this.addRealtimeMessage('bot', '👋 Conversation ended. Click "Start AI Conversation" to begin again.');
        this.showSuccess('Real-time conversation ended.');
    }
    
    toggleRealtimeListening() {
        if (!this.conversationActive) {
            this.showError('Please start the conversation first');
            return;
        }
        
        // Check if we're in the middle of waiting for bot response
        if (!this.waitingForUserInput && !this.isRealtimeRecording) {
            this.showError('Please wait for the bot to finish responding');
            return;
        }
        
        if (this.isRealtimeRecording) {
            this.stopRealtimeRecording();
        } else {
            // User is starting their turn
            this.waitingForUserInput = false; // User is now providing input
            this.startRealtimeRecording();
        }
    }
    
    updateListeningMode() {
        if (this.continuousMode && this.conversationActive) {
            // In continuous mode, automatically restart listening after processing
            if (!this.isRealtimeRecording) {
                setTimeout(() => {
                    if (this.conversationActive && !this.isRealtimeRecording) {
                        this.startRealtimeRecording();
                    }
                }, 1000);
            }
        }
    }
    
    updateStatusLight(type, status) {
        const light = this.elements[type + 'Status'];
        if (light) {
            light.className = 'status-light';
            if (status === 'active') {
                light.classList.add('active');
            } else if (status === 'processing') {
                light.classList.add('processing');
            } else if (status === 'speaking') {
                light.classList.add('speaking');
            }
        }
    }
    
    speakLastBotResponse() {
        const lastBotMessage = this.elements.botRealtimeMessages.querySelector('.realtime-message:last-child');
        if (lastBotMessage) {
            const text = lastBotMessage.textContent;
            this.speakText(text);
        }
    }
    
    closeRealtimeMode() {
        this.elements.realtimeModal.style.display = 'none';
        if (this.isRealtimeRecording) {
            this.stopRealtimeRecording();
        }
    }
    
    clearRealtimeMessages() {
        this.elements.userRealtimeMessages.innerHTML = '';
        this.elements.botRealtimeMessages.innerHTML = '';
    }
    
    async startRealtimeRecording() {
        if (!this.realtimeRecognition || this.isRealtimeRecording || !this.conversationActive) return;
        
        // Request microphone permission first if available
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
            try {
                await navigator.mediaDevices.getUserMedia({ audio: true });
            } catch (error) {
                console.error('Microphone permission denied:', error);
                this.showError('Microphone access denied. Please allow microphone access in your browser settings.');
                return;
            }
        }
        
        // Initialize/reset speech session
        if (!this.speechSession) {
            this.speechSession = {
                processedMessages: new Set(),
                lastFinalResult: '',
                silenceTimer: null,
                isProcessing: false
            };
        } else {
            this.speechSession.processedMessages.clear();
            this.speechSession.lastFinalResult = '';
            this.speechSession.isProcessing = false;
            if (this.speechSession.silenceTimer) {
                clearTimeout(this.speechSession.silenceTimer);
            }
        }
        
        this.isRealtimeRecording = true;
        this.elements.userVoiceBtn.classList.add('recording');
        this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-stop"></i><span>Recording... Click to Stop</span>';
        this.elements.botStatus.querySelector('span').textContent = 'Listening...';
        this.updateStatusLight('mic', 'processing');
        
        try {
            this.realtimeRecognition.start();
        } catch (error) {
            console.error('Failed to start realtime recording:', error);
            this.isRealtimeRecording = false;
            this.elements.userVoiceBtn.classList.remove('recording');
            this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Speak</span>';
            this.updateStatusLight('mic', 'active');
        }
    }
    
    stopRealtimeRecording() {
        if (!this.isRealtimeRecording) return;
        
        // Clean up speech session
        if (this.speechSession) {
            if (this.speechSession.silenceTimer) {
                clearTimeout(this.speechSession.silenceTimer);
            }
            this.speechSession.isProcessing = false;
        }
        
        this.isRealtimeRecording = false;
        this.elements.userVoiceBtn.classList.remove('recording');
        this.elements.userVoiceBtn.innerHTML = '<i class="fas fa-microphone"></i><span>Click to Speak</span>';
        this.elements.botStatus.querySelector('span').textContent = 'Processing...';
        this.updateStatusLight('mic', 'active');
        
        try {
            this.realtimeRecognition.stop();
        } catch (error) {
            console.log('Recognition already stopped');
        }
    }
    
    addRealtimeMessage(type, message) {
        const container = type === 'user' ? 
            this.elements.userRealtimeMessages : 
            this.elements.botRealtimeMessages;
        
        // Check for duplicate messages in the UI
        const existingMessages = container.querySelectorAll('.realtime-message:not(.interim-message)');
        const lastMessage = existingMessages.length > 0 ? 
            existingMessages[existingMessages.length - 1].textContent.trim() : '';
        
        // Prevent exact duplicate messages
        if (message.trim() === lastMessage) {
            console.log('Preventing duplicate UI message:', message);
            return;
        }
        
        // Additional check for similar messages (for user messages)
        if (type === 'user' && existingMessages.length > 0) {
            for (let i = Math.max(0, existingMessages.length - 3); i < existingMessages.length; i++) {
                const existingText = existingMessages[i].textContent.trim();
                if (this.isSimilarMessage(message, existingText)) {
                    console.log('Preventing similar UI message:', message, 'vs', existingText);
                    return;
                }
            }
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'realtime-message';
        messageDiv.textContent = message;
        
        // Add timestamp and styling for better conversation flow
        const timestamp = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        messageDiv.setAttribute('data-time', timestamp);
        
        container.appendChild(messageDiv);
        container.scrollTop = container.scrollHeight;
        
        // Add a small delay to make conversation feel more natural
        if (type === 'bot') {
            messageDiv.style.opacity = '0';
            setTimeout(() => {
                messageDiv.style.opacity = '1';
                messageDiv.style.transition = 'opacity 0.3s ease-in-out';
            }, 200);
        }
        
        console.log(`Added ${type} message:`, message);
    }
    
    getLastUserMessage() {
        const userMessages = this.elements.userRealtimeMessages.querySelectorAll('.realtime-message:not(.interim-message):not(.welcome-msg)');
        if (userMessages.length > 0) {
            const lastMessage = userMessages[userMessages.length - 1].textContent.trim();
            console.log('Last user message found:', lastMessage);
            return lastMessage;
        }
        console.log('No previous user messages found');
        return '';
    }
    
    showInterimMessage(text) {
        // Remove existing interim message
        const existing = this.elements.userRealtimeMessages.querySelector('.interim-message');
        if (existing) {
            existing.remove();
        }
        
        // Add new interim message
        const messageDiv = document.createElement('div');
        messageDiv.className = 'realtime-message interim-message';
        messageDiv.textContent = text;
        
        this.elements.userRealtimeMessages.appendChild(messageDiv);
        this.elements.userRealtimeMessages.scrollTop = this.elements.userRealtimeMessages.scrollHeight;
    }
    
    sendRealtimeMessage(message) {
        // Update bot status
        const botStatus = this.elements.botStatus;
        if (botStatus) {
            botStatus.querySelector('.fa-spin').style.display = 'inline-block';
            botStatus.querySelector('span').textContent = 'Processing...';
        }
        
        this.socket.emit('realtime_response', {
            message: message,
            userLanguage: this.settings.userLanguage,
            botLanguage: this.settings.botLanguage,
            session_id: this.getSessionId()
        });
    }
    
    getSessionId() {
        let sessionId = localStorage.getItem('chatSessionId');
        if (!sessionId) {
            sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
            localStorage.setItem('chatSessionId', sessionId);
        }
        return sessionId;
    }
    
    showError(message) {
        this.showNotification(message, 'error');
    }
    
    showSuccess(message) {
        this.showNotification(message, 'success');
    }
    
    showNotification(message, type) {
        try {
            // Remove existing notifications
            const existing = document.querySelector('.notification');
            if (existing) {
                existing.remove();
            }
            
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            // Add close button for errors
            if (type === 'error') {
                const closeBtn = document.createElement('button');
                closeBtn.innerHTML = '×';
                closeBtn.className = 'notification-close';
                closeBtn.onclick = () => notification.remove();
                notification.appendChild(closeBtn);
            }
            
            document.body.appendChild(notification);
            
            // Show notification with animation
            setTimeout(() => notification.classList.add('show'), 100);
            
            // Auto-remove after delay (longer for errors)
            const delay = type === 'error' ? 8000 : 3000;
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.classList.remove('show');
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.remove();
                        }
                    }, 300);
                }
            }, delay);
            
        } catch (error) {
            console.error('Error showing notification:', error);
            // Fallback to alert for critical errors
            if (type === 'error') {
                alert(message);
            }
        }
    }
}

// Initialize chatbot when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.chatbot = new UniversalChatbot();
});