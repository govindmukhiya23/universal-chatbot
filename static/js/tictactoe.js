document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    const board = document.getElementById('board');
    const cells = document.querySelectorAll('.cell');
    const status = document.getElementById('status');
    const newGameBtn = document.getElementById('newGameBtn');
    const difficultySelect = document.getElementById('difficulty');
    const languageSelect = document.getElementById('language');
    const voiceCommandBtn = document.getElementById('voiceCommandBtn');
    const playerScore = document.getElementById('player-score');
    const computerScore = document.getElementById('computer-score');
    const tiesScore = document.getElementById('ties-score');
    const winAnimation = document.getElementById('winAnimation');
    const winMessage = document.getElementById('winMessage');

    let scores = {
        player: 0,
        computer: 0,
        ties: 0
    };

    // Language translations
    const translations = {
        en: {
            yourTurn: 'Your turn (X)',
            computerTurn: 'Computer\'s turn (O)',
            youWin: 'You win! 🎉',
            computerWins: 'Computer wins!',
            tie: 'It\'s a tie!',
            speakMove: 'Speak your move...',
            invalidMove: 'Invalid move, try again'
        },
        es: {
            yourTurn: 'Tu turno (X)',
            computerTurn: 'Turno de la computadora (O)',
            youWin: '¡Has ganado! 🎉',
            computerWins: '¡La computadora gana!',
            tie: '¡Es un empate!',
            speakMove: 'Di tu movimiento...',
            invalidMove: 'Movimiento inválido, intenta de nuevo'
        },
        // Add more languages as needed
    };

    function updateScoreDisplay() {
        playerScore.textContent = scores.player;
        computerScore.textContent = scores.computer;
        tiesScore.textContent = scores.ties;
    }

    function showWinAnimation(message) {
        winMessage.textContent = message;
        winAnimation.classList.add('active');
        createConfetti();
        setTimeout(() => {
            winAnimation.classList.remove('active');
        }, 3000);
    }

    function createConfetti() {
        const confetti = document.querySelector('.confetti');
        confetti.innerHTML = '';
        for (let i = 0; i < 50; i++) {
            const piece = document.createElement('div');
            piece.className = 'confetti-piece';
            piece.style.left = Math.random() * 100 + 'vw';
            piece.style.animationDelay = Math.random() * 3 + 's';
            piece.style.backgroundColor = `hsl(${Math.random() * 360}, 100%, 50%)`;
            piece.style.animation = 'confettiRain 3s linear forwards';
            confetti.appendChild(piece);
        }
    }

    function updateStatus(message) {
        status.textContent = translations[languageSelect.value]?.[message] || translations.en[message];
    }

    function handleCellClick(index) {
        socket.emit('make_move', {
            move: index,
            difficulty: difficultySelect.value,
            userLanguage: languageSelect.value
        });
    }

    cells.forEach(cell => {
        cell.addEventListener('click', () => {
            const index = parseInt(cell.dataset.index);
            handleCellClick(index);
        });
    });

    newGameBtn.addEventListener('click', () => {
        socket.emit('start_game', {
            difficulty: difficultySelect.value
        });
    });

    // Voice command handling
    if ('webkitSpeechRecognition' in window) {
        const recognition = new webkitSpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;

        voiceCommandBtn.addEventListener('click', () => {
            recognition.lang = languageSelect.value;
            recognition.start();
            updateStatus('speakMove');
        });

        recognition.onresult = (event) => {
            const command = event.results[0][0].transcript.toLowerCase();
            socket.emit('process_game_command', {
                command: command,
                language: languageSelect.value
            });
        };

        recognition.onend = () => {
            updateStatus('yourTurn');
        };
    } else {
        voiceCommandBtn.style.display = 'none';
    }

    // Socket event handlers
    socket.on('game_state', (data) => {
        // Update board
        data.board.forEach((mark, index) => {
            cells[index].textContent = mark;
            cells[index].className = 'cell' + (mark === 'X' ? ' x' : mark === 'O' ? ' o' : '');
        });

        // Update status
        if (data.winner) {
            if (data.winner === 'X') {
                scores.player++;
                showWinAnimation(translations[languageSelect.value]?.youWin || translations.en.youWin);
            } else {
                scores.computer++;
                showWinAnimation(translations[languageSelect.value]?.computerWins || translations.en.computerWins);
            }
            updateScoreDisplay();
        } else if (data.gameOver) {
            scores.ties++;
            updateScoreDisplay();
            showWinAnimation(translations[languageSelect.value]?.tie || translations.en.tie);
        } else {
            updateStatus(data.currentPlayer === 'X' ? 'yourTurn' : 'computerTurn');
        }

        // Highlight winning combination
        if (data.winningCombination) {
            data.winningCombination.forEach(index => {
                cells[index].classList.add('winner');
            });
        }
    });

    socket.on('game_error', (data) => {
        updateStatus('invalidMove');
    });

    // Start initial game
    socket.emit('start_game', {
        difficulty: difficultySelect.value
    });
});
