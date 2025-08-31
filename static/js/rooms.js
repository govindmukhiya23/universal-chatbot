// Virtual Rooms JavaScript
class VirtualRooms {
    constructor(socket) {
        this.socket = socket;
        this.currentRoom = null;
        this.currentUser = null;
        this.isInRoom = false;
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeSocketEvents();
    }
    
    initializeElements() {
        this.elements = {
            // Modal elements
            roomsBtn: document.getElementById('roomsBtn'),
            roomsModal: document.getElementById('roomsModal'),
            closeRooms: document.getElementById('closeRooms'),
            
            // Room selection
            roomSelection: document.getElementById('roomSelection'),
            createRoomBtn: document.getElementById('createRoomBtn'),
            joinRoomBtn: document.getElementById('joinRoomBtn'),
            
            // Create room form
            createRoomForm: document.getElementById('createRoomForm'),
            createRoomName: document.getElementById('createRoomName'),
            createRoomLanguage: document.getElementById('createRoomLanguage'),
            confirmCreateRoom: document.getElementById('confirmCreateRoom'),
            cancelCreateRoom: document.getElementById('cancelCreateRoom'),
            
            // Join room form
            joinRoomForm: document.getElementById('joinRoomForm'),
            joinRoomPin: document.getElementById('joinRoomPin'),
            joinRoomName: document.getElementById('joinRoomName'),
            joinRoomLanguage: document.getElementById('joinRoomLanguage'),
            confirmJoinRoom: document.getElementById('confirmJoinRoom'),
            cancelJoinRoom: document.getElementById('cancelJoinRoom'),
            
            // Room chat
            roomChat: document.getElementById('roomChat'),
            currentRoomPin: document.getElementById('currentRoomPin'),
            roomUsers: document.getElementById('roomUsers'),
            roomMessages: document.getElementById('roomMessages'),
            roomMessageInput: document.getElementById('roomMessageInput'),
            sendRoomMessage: document.getElementById('sendRoomMessage'),
            leaveRoomBtn: document.getElementById('leaveRoomBtn')
        };
    }
    
    initializeEventListeners() {
        // Modal controls
        this.elements.roomsBtn.addEventListener('click', () => this.openRoomsModal());
        this.elements.closeRooms.addEventListener('click', () => this.closeRoomsModal());
        
        // Room selection
        this.elements.createRoomBtn.addEventListener('click', () => this.showCreateRoomForm());
        this.elements.joinRoomBtn.addEventListener('click', () => this.showJoinRoomForm());
        
        // Create room form
        this.elements.confirmCreateRoom.addEventListener('click', () => this.createRoom());
        this.elements.cancelCreateRoom.addEventListener('click', () => this.hideAllForms());
        
        // Join room form
        this.elements.confirmJoinRoom.addEventListener('click', () => this.joinRoom());
        this.elements.cancelJoinRoom.addEventListener('click', () => this.hideAllForms());
        
        // Room chat
        this.elements.sendRoomMessage.addEventListener('click', () => this.sendMessage());
        this.elements.roomMessageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        this.elements.leaveRoomBtn.addEventListener('click', () => this.leaveRoom());
        
        // PIN input formatting
        this.elements.joinRoomPin.addEventListener('input', (e) => {
            e.target.value = e.target.value.replace(/[^0-9]/g, '').substring(0, 6);
        });
        
        // Modal backdrop click
        this.elements.roomsModal.addEventListener('click', (e) => {
            if (e.target === this.elements.roomsModal) this.closeRoomsModal();
        });
    }
    
    initializeSocketEvents() {
        // Remove any existing listeners to prevent duplicates
        this.socket.off('room_message_received');
        this.socket.off('room_joined');
        this.socket.off('room_error');
        
        // Test socket connectivity
        console.log('Setting up room socket listeners...');
        
        this.socket.on('room_message_received', (data) => {
            console.log('🔥 ROOM MESSAGE RECEIVED:', data);
            console.log('Current room:', this.currentRoom);
            console.log('Data room:', data.room_pin);
            
            // Always try to display for debugging
            if (this.currentRoom === data.room_pin) {
                console.log('✅ Room match - displaying message');
                this.displayRoomMessage(data);
            } else {
                console.log('❌ Room mismatch or not in room');
            }
        });
        
        // Test event
        this.socket.on('test_event', (data) => {
            console.log('Test event received:', data);
        });
        
        this.socket.on('room_joined', (data) => {
            this.handleRoomJoined(data);
        });
        
        this.socket.on('room_error', (data) => {
            this.showError(data.error);
        });
    }
    
    openRoomsModal() {
        this.elements.roomsModal.style.display = 'flex';
        if (this.isInRoom) {
            this.showRoomChat();
        } else {
            this.showRoomSelection();
        }
    }
    
    closeRoomsModal() {
        this.elements.roomsModal.style.display = 'none';
    }
    
    showCreateRoomForm() {
        this.hideAllForms();
        this.elements.createRoomForm.style.display = 'block';
        this.elements.createRoomName.focus();
    }
    
    showJoinRoomForm() {
        this.hideAllForms();
        this.elements.joinRoomForm.style.display = 'block';
        this.elements.joinRoomPin.focus();
    }
    
    hideAllForms() {
        this.elements.createRoomForm.style.display = 'none';
        this.elements.joinRoomForm.style.display = 'none';
    }
    
    showRoomSelection() {
        this.elements.roomSelection.style.display = 'block';
        this.elements.roomChat.style.display = 'none';
        this.hideAllForms();
    }
    
    showRoomChat() {
        this.elements.roomSelection.style.display = 'none';
        this.elements.roomChat.style.display = 'block';
    }
    
    async createRoom() {
        const name = this.elements.createRoomName.value.trim();
        const language = this.elements.createRoomLanguage.value;
        
        if (!name) {
            this.showError('Please enter your name');
            return;
        }
        
        try {
            this.setLoading(this.elements.confirmCreateRoom, true);
            
            const response = await fetch('/api/rooms/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, language })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentRoom = data.room_pin;
                this.currentUser = { name, language };
                this.isInRoom = true;
                
                // Store user info in localStorage for persistence
                localStorage.setItem('roomUser', JSON.stringify(this.currentUser));
                console.log('Room created - User info:', this.currentUser);
                
                // Show success with PIN
                this.showRoomCreated(data.room_pin);
                
                // Join socket room and initialize
                console.log('Joining socket room:', data.room_pin);
                this.socket.emit('join_room_socket', { room_pin: data.room_pin });
                
                setTimeout(() => {
                    this.showRoomChat();
                    this.elements.currentRoomPin.textContent = data.room_pin;
                    this.updateRoomUsers([{ name, language }]);
                }, 2000);
                
            } else {
                this.showError(data.error || 'Failed to create room');
            }
        } catch (error) {
            console.error('Create room error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setLoading(this.elements.confirmCreateRoom, false);
        }
    }
    
    async joinRoom() {
        const pin = this.elements.joinRoomPin.value.trim();
        const name = this.elements.joinRoomName.value.trim();
        const language = this.elements.joinRoomLanguage.value;
        
        if (!pin || pin.length !== 6) {
            this.showError('Please enter a valid 6-digit PIN');
            return;
        }
        
        if (!name) {
            this.showError('Please enter your name');
            return;
        }
        
        try {
            this.setLoading(this.elements.confirmJoinRoom, true);
            
            const response = await fetch('/api/rooms/join', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pin, name, language })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentRoom = pin;
                this.currentUser = { name, language };
                this.isInRoom = true;
                
                // Store user info in localStorage for persistence
                localStorage.setItem('roomUser', JSON.stringify(this.currentUser));
                console.log('Room joined - User info:', this.currentUser);
                
                // Join socket room
                console.log('Joining socket room:', pin);
                this.socket.emit('join_room_socket', { room_pin: pin });
                
                this.showRoomChat();
                this.elements.currentRoomPin.textContent = pin;
                this.updateRoomUsers(data.room_info.users);
                
                this.showSuccess(`Joined room ${pin} successfully!`);
                
            } else {
                this.showError(data.error || 'Failed to join room');
            }
        } catch (error) {
            console.error('Join room error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setLoading(this.elements.confirmJoinRoom, false);
        }
    }
    
    async leaveRoom() {
        if (!this.isInRoom) return;
        
        try {
            const response = await fetch('/api/rooms/leave', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentRoom = null;
                this.currentUser = null;
                this.isInRoom = false;
                
                // Clear localStorage
                localStorage.removeItem('roomUser');
                
                this.showRoomSelection();
                this.clearRoomMessages();
                this.showSuccess('Left room successfully');
                
                // Reset forms
                this.elements.createRoomName.value = '';
                this.elements.joinRoomPin.value = '';
                this.elements.joinRoomName.value = '';
                
            } else {
                this.showError(data.error || 'Failed to leave room');
            }
        } catch (error) {
            console.error('Leave room error:', error);
            this.showError('Network error. Please try again.');
        }
    }
    
    sendMessage() {
        const message = this.elements.roomMessageInput.value.trim();
        
        if (!message || !this.isInRoom) {
            console.log('Cannot send message:', { message, isInRoom: this.isInRoom });
            return;
        }
        
        console.log('Sending room message:', message);
        
        // Send message via socket
        this.socket.emit('room_message', { 
            message: message,
            room_pin: this.currentRoom
        });
        
        // Clear input
        this.elements.roomMessageInput.value = '';
    }
    
    displayRoomMessage(data) {
        console.log('Displaying room message:', data);
        
        // Get current user info from memory or localStorage
        if (!this.currentUser) {
            const stored = localStorage.getItem('roomUser');
            if (stored) {
                this.currentUser = JSON.parse(stored);
                console.log('Restored user from localStorage:', this.currentUser);
            }
        }
        
        // Ensure we have current user info
        if (!this.currentUser || !this.currentUser.language) {
            console.error('No current user language found');
            return;
        }
        
        const userLang = this.currentUser.language;
        console.log('User language:', userLang);
        console.log('Available translations:', data.translations);
        
        // Check if this is the sender's own message
        const isOwnMessage = data.sender_name === this.currentUser.name;
        console.log('Is own message:', isOwnMessage, 'Sender:', data.sender_name, 'Current user:', this.currentUser.name);
        
        // Get the message in user's language - FIXED LOGIC
        let translatedMessage;
        if (data.translations && data.translations[userLang]) {
            translatedMessage = data.translations[userLang];
            console.log('Using translation for', userLang, ':', translatedMessage);
        } else {
            translatedMessage = data.original_message;
            console.log('No translation found, using original:', translatedMessage);
        }
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `room-message ${isOwnMessage ? 'own' : 'other'}`;
        
        const senderDiv = document.createElement('div');
        senderDiv.className = 'message-sender';
        senderDiv.textContent = isOwnMessage ? 'You' : data.sender_name;
        
        const textDiv = document.createElement('div');
        textDiv.className = 'message-text';
        textDiv.textContent = translatedMessage;
        
        messageDiv.appendChild(senderDiv);
        messageDiv.appendChild(textDiv);
        
        // Show translation info if message was translated and not own message
        if (translatedMessage !== data.original_message && !isOwnMessage) {
            const translationDiv = document.createElement('div');
            translationDiv.className = 'message-translation';
            translationDiv.textContent = `Original (${data.sender_language.toUpperCase()}): ${data.original_message}`;
            messageDiv.appendChild(translationDiv);
        }
        
        this.elements.roomMessages.appendChild(messageDiv);
        this.elements.roomMessages.scrollTop = this.elements.roomMessages.scrollHeight;
    }
    
    updateRoomUsers(users) {
        this.elements.roomUsers.innerHTML = '';
        
        users.forEach(user => {
            const userBadge = document.createElement('div');
            userBadge.className = 'user-badge';
            userBadge.textContent = `${user.name} (${user.language.toUpperCase()})`;
            this.elements.roomUsers.appendChild(userBadge);
        });
    }
    
    clearRoomMessages() {
        this.elements.roomMessages.innerHTML = '';
    }
    
    showRoomCreated(pin) {
        // Create temporary success display
        const successDiv = document.createElement('div');
        successDiv.className = 'room-pin-display';
        successDiv.innerHTML = `
            <h3>🎉 Room Created Successfully!</h3>
            <div class="pin-code">${pin}</div>
            <div class="pin-instructions">
                Share this PIN with others to join your room.<br>
                Entering room chat in 2 seconds...
            </div>
        `;
        
        // Replace form with success message
        this.elements.createRoomForm.innerHTML = '';
        this.elements.createRoomForm.appendChild(successDiv);
    }
    
    handleRoomJoined(data) {
        if (data.recent_messages) {
            // Display recent messages
            data.recent_messages.forEach(msg => {
                // Convert message format for display
                const displayData = {
                    sender_name: msg.sender_name,
                    message: msg.translations[this.currentUser.language] || msg.original_text,
                    original_message: msg.original_text,
                    sender_language: msg.original_language,
                    is_own_message: false // Will be determined by sender_id if available
                };
                this.displayRoomMessage(displayData);
            });
        }
        
        if (data.users) {
            this.updateRoomUsers(data.users);
        }
    }
    
    setLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<div class="loading-spinner"></div> Loading...';
        } else {
            button.disabled = false;
            // Restore original text based on button ID
            if (button.id === 'confirmCreateRoom') {
                button.innerHTML = '<i class="fas fa-plus"></i> Create Room';
            } else if (button.id === 'confirmJoinRoom') {
                button.innerHTML = '<i class="fas fa-sign-in-alt"></i> Join Room';
            }
        }
    }
    
    showError(message) {
        // Use the main chatbot's notification system if available
        if (window.chatbot && window.chatbot.showError) {
            window.chatbot.showError(message);
        } else {
            alert('Error: ' + message);
        }
    }
    
    showSuccess(message) {
        // Use the main chatbot's notification system if available
        if (window.chatbot && window.chatbot.showSuccess) {
            window.chatbot.showSuccess(message);
        } else {
            alert('Success: ' + message);
        }
    }
    
    getCurrentUserId() {
        // Get current user ID from session or generate one
        if (!this.currentUserId) {
            this.currentUserId = 'user_' + Math.random().toString(36).substr(2, 9);
        }
        return this.currentUserId;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait for main chatbot to initialize, then add rooms
    setTimeout(() => {
        if (window.chatbot && window.chatbot.socket) {
            window.virtualRooms = new VirtualRooms(window.chatbot.socket);
            console.log('Virtual Rooms initialized');
        } else {
            console.error('Main chatbot not found, retrying...');
            // Retry after another second
            setTimeout(() => {
                if (window.chatbot && window.chatbot.socket) {
                    window.virtualRooms = new VirtualRooms(window.chatbot.socket);
                    console.log('Virtual Rooms initialized (retry)');
                }
            }, 1000);
        }
    }, 500);
});