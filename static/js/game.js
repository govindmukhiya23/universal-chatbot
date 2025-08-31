class TicTacToeGame {
    constructor(chatbot) {
        this.chatbot = chatbot;
        this.gameActive = false;
        this.boardState = Array(9).fill(' ');
        this.currentPlayer = 'X';
        
        this.initializeElements();
        this.initializeEventListeners();
        this.initializeSocketHandlers();
    }
    
    initializeElements() {
        // Create game container if it doesn't exist
        if (!document.getElementById('ticTacToeContainer')) {
            const container = document.createElement('div');
            container.id = 'ticTacToeContainer';
            container.className = 'tic-tac-toe-container';
            container.innerHTML = `
                <div class="difficulty-select">
                    <select id="gameDifficulty">
                        <option value="easy">Easy Mode</option>
                        <option value="hard">Hard Mode</option>
                    </select>
                </div>
                <div class="game-board">
                    ${Array(9).fill('').map((_, i) => 
                        `<div class="game-cell" data-index="${i}"></div>`
                    ).join('')}
                </div>
                <div class="game-status"></div>
                <div class="game-controls">
                    <button class="new-game">New Game</button>
                    <button class="close-game">Close</button>
                </div>
            `;
            document.body.appendChild(container);
        }
        
        this.elements = {
            container: document.getElementById('ticTacToeContainer'),
            board: document.querySelector('.game-board'),
            cells: document.querySelectorAll('.game-cell'),
            status: document.querySelector('.game-status'),
            newGameBtn: document.querySelector('.new-game'),
            closeGameBtn: document.querySelector('.close-game'),
            difficultySelect: document.getElementById('gameDifficulty')
        };
    }
    
    initializeEventListeners() {
        // Cell click handler
        this.elements.cells.forEach(cell => {
            cell.addEventListener('click', () => {
                if (this.gameActive && cell.textContent === '') {
                    const index = parseInt(cell.dataset.index);
                    this.makeMove(index);
                }
            });
        });
        
        // New game button
        this.elements.newGameBtn.addEventListener('click', () => this.startNewGame());
        
        // Close game button
        this.elements.closeGameBtn.addEventListener('click', () => this.closeGame());
        
        // Listen for game command in chat
        this.chatbot.elements.messageInput.addEventListener('keyup', (e) => {
            const message = e.target.value.toLowerCase();
            if (message.includes('play tic tac toe') || message.includes('start game')) {
                e.target.value = '';
                this.startNewGame();
            }
        });
    }
    
    initializeSocketHandlers() {
        this.chatbot.socket.on('game_state', (data) => {
            this.updateGameState(data);
        });
        
        this.chatbot.socket.on('game_error', (data) => {
            this.showError(data.error);
        });
    }
    
    startNewGame() {
        this.elements.container.classList.add('active');
        this.gameActive = true;
        this.boardState = Array(9).fill(' ');
        this.currentPlayer = 'X';
        
        // Clear board
        this.elements.cells.forEach(cell => {
            cell.textContent = '';
            cell.classList.remove('x', 'o', 'filled');
        });
        
        // Start game with selected difficulty
        this.chatbot.socket.emit('start_game', {
            difficulty: this.elements.difficultySelect.value
        });
        
        // Update status
        this.updateStatus('Game started! You are X, make your move!');
    }
    
    closeGame() {
        this.elements.container.classList.remove('active');
        this.gameActive = false;
    }
    
    makeMove(position) {
        if (!this.gameActive) return;
        
        this.chatbot.socket.emit('make_move', {
            move: position,
            userLanguage: this.chatbot.settings.userLanguage
        });
    }
    
    updateGameState(data) {
        // Update board
        data.board.forEach((mark, index) => {
            const cell = this.elements.cells[index];
            if (mark !== ' ') {
                cell.textContent = mark;
                cell.classList.add(mark.toLowerCase(), 'filled');
            }
        });
        
        // Update status message
        this.updateStatus(data.message);
        
        // Handle game over
        if (data.gameOver) {
            this.gameActive = false;
            // Add replay option
            this.elements.status.innerHTML += '<br><em>Say "play again" or click New Game to start another match!</em>';
        }
    }
    
    updateStatus(message) {
        this.elements.status.textContent = message;
    }
    
    showError(message) {
        this.chatbot.showError(message);
    }
    
    processVoiceCommand(text) {
        text = text.toLowerCase();
        
        // Game start commands
        if (text.includes('play tic tac toe') || text.includes('start game')) {
            this.startNewGame();
            return true;
        }
        
        // Move commands
        if (this.gameActive) {
            // Convert voice command to move position
            if (text.includes('top') || text.includes('middle') || text.includes('bottom')) {
                this.chatbot.socket.emit('make_move', {
                    move: text,
                    userLanguage: this.chatbot.settings.userLanguage
                });
                return true;
            }
        }
        
        return false; // Not a game command
    }
}
