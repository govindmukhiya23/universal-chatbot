class TicTacToe {
    constructor(difficulty = 'easy') {
        this.board = Array(9).fill('');
        this.currentPlayer = 'X';
        this.difficulty = difficulty;
        this.gameOver = false;
        this.winner = null;
    }

    makeMove(position) {
        if (this.board[position] === '' && !this.gameOver) {
            this.board[position] = this.currentPlayer;
            if (this.checkWinner()) {
                this.gameOver = true;
                this.winner = this.currentPlayer;
                return { success: true, gameOver: true, winner: this.winner, board: this.board };
            }
            if (this.isBoardFull()) {
                this.gameOver = true;
                return { success: true, gameOver: true, draw: true, board: this.board };
            }
            this.currentPlayer = this.currentPlayer === 'X' ? 'O' : 'X';
            return { success: true, gameOver: false, board: this.board };
        }
        return { success: false };
    }

    makeBotMove() {
        if (this.gameOver || this.currentPlayer !== 'O') return { success: false };

        let position;
        if (this.difficulty === 'hard') {
            position = this.getBestMove();
        } else {
            position = this.getEasyMove();
        }

        return this.makeMove(position);
    }

    getBestMove() {
        let bestScore = -Infinity;
        let bestMove;

        for (let i = 0; i < 9; i++) {
            if (this.board[i] === '') {
                this.board[i] = 'O';
                let score = this.minimax(this.board, 0, false);
                this.board[i] = '';
                if (score > bestScore) {
                    bestScore = score;
                    bestMove = i;
                }
            }
        }

        return bestMove;
    }

    minimax(board, depth, isMaximizing) {
        const winner = this.checkWinner();
        
        if (winner === 'O') return 1;
        if (winner === 'X') return -1;
        if (this.isBoardFull()) return 0;

        if (isMaximizing) {
            let bestScore = -Infinity;
            for (let i = 0; i < 9; i++) {
                if (board[i] === '') {
                    board[i] = 'O';
                    let score = this.minimax(board, depth + 1, false);
                    board[i] = '';
                    bestScore = Math.max(score, bestScore);
                }
            }
            return bestScore;
        } else {
            let bestScore = Infinity;
            for (let i = 0; i < 9; i++) {
                if (board[i] === '') {
                    board[i] = 'X';
                    let score = this.minimax(board, depth + 1, true);
                    board[i] = '';
                    bestScore = Math.min(score, bestScore);
                }
            }
            return bestScore;
        }
    }

    getEasyMove() {
        const emptyPositions = this.board.reduce((positions, cell, index) => {
            if (cell === '') positions.push(index);
            return positions;
        }, []);
        
        return emptyPositions[Math.floor(Math.random() * emptyPositions.length)];
    }

    checkWinner() {
        const winPatterns = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8], // Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8], // Columns
            [0, 4, 8], [2, 4, 6] // Diagonals
        ];

        for (const pattern of winPatterns) {
            const [a, b, c] = pattern;
            if (this.board[a] && this.board[a] === this.board[b] && this.board[a] === this.board[c]) {
                this.winner = this.board[a];
                return this.board[a];
            }
        }

        return null;
    }

    isBoardFull() {
        return !this.board.includes('');
    }

    reset(difficulty = this.difficulty) {
        this.board = Array(9).fill('');
        this.currentPlayer = 'X';
        this.difficulty = difficulty;
        this.gameOver = false;
        this.winner = null;
    }

    translatePosition(input) {
        // Convert natural language position to board index
        const positionMap = {
            'top left': 0,
            'top center': 1,
            'top right': 2,
            'middle left': 3,
            'center': 4,
            'middle right': 5,
            'bottom left': 6,
            'bottom center': 7,
            'bottom right': 8
        };

        // Clean up input and convert to lowercase
        input = input.toLowerCase().trim();

        // Check direct position mapping
        if (positionMap[input] !== undefined) {
            return positionMap[input];
        }

        // Check for numeric input (1-9)
        if (/^[1-9]$/.test(input)) {
            return parseInt(input) - 1;
        }

        // Additional position patterns
        const patterns = {
            'top': [/^top$/, 1],
            'bottom': [/^bottom$/, 7],
            'left': [/^left$/, 3],
            'right': [/^right$/, 5],
            'middle': [/^middle$/, 4],
            'center': [/^center$/, 4],
            'corner': [/corner/i, [0, 2, 6, 8]]
        };

        for (const [key, [pattern, value]] of Object.entries(patterns)) {
            if (pattern.test(input)) {
                if (Array.isArray(value)) {
                    // For corners, return a random empty corner
                    const availableCorners = value.filter(pos => this.board[pos] === '');
                    if (availableCorners.length > 0) {
                        return availableCorners[Math.floor(Math.random() * availableCorners.length)];
                    }
                } else {
                    return value;
                }
            }
        }

        return -1; // Invalid position
    }

    getBoardDisplay() {
        let display = '';
        for (let i = 0; i < 9; i += 3) {
            display += this.board[i] || ' ';
            display += ' | ';
            display += this.board[i + 1] || ' ';
            display += ' | ';
            display += this.board[i + 2] || ' ';
            if (i < 6) display += '\\n---------\\n';
        }
        return display;
    }
}
