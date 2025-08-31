import random
from enum import Enum

class GameDifficulty(Enum):
    EASY = "easy"
    HARD = "hard"

class TicTacToe:
    def __init__(self, difficulty=GameDifficulty.EASY):
        self.board = [" " for _ in range(9)]  # 3x3 grid
        self.difficulty = difficulty
        self.current_player = "X"  # X always starts
        self.winner = None
        self.game_over = False
        self.translations = {
            "top_left": 0, "top_middle": 1, "top_right": 2,
            "middle_left": 3, "middle": 4, "middle_right": 5, 
            "bottom_left": 6, "bottom_middle": 7, "bottom_right": 8,
            "top row left": 0, "top row center": 1, "top row right": 2,
            "middle row left": 3, "middle row center": 4, "middle row right": 5,
            "bottom row left": 6, "bottom row center": 7, "bottom row right": 8,
            "top left": 0, "top center": 1, "top right": 2,
            "middle left": 3, "center": 4, "middle right": 5,
            "bottom left": 6, "bottom center": 7, "bottom right": 8,
            "upper left": 0, "upper middle": 1, "upper right": 2,
            "left": 3, "middle center": 4, "right": 5,
            "lower left": 6, "lower middle": 7, "lower right": 8,
            "top": 1, "bottom": 7, "corner": 0
        }
        
        # Support for various languages (position translations)
        self.multilingual_positions = {
            "hi": {  # Hindi
                "ऊपर बाएं": 0, "ऊपर मध्य": 1, "ऊपर दाएं": 2,
                "मध्य बाएं": 3, "मध्य": 4, "मध्य दाएं": 5,
                "नीचे बाएं": 6, "नीचे मध्य": 7, "नीचे दाएं": 8,
                "बाएं": [0, 3, 6], "दाएं": [2, 5, 8],
                "ऊपर": [0, 1, 2], "नीचे": [6, 7, 8],
                "कोना": [0, 2, 6, 8]
            },
            "te": {  # Telugu
                "పై ఎడమ": 0, "పై మధ్య": 1, "పై కుడి": 2,
                "మధ్య ఎడమ": 3, "మధ్య": 4, "మధ్య కుడి": 5,
                "క్రింద ఎడమ": 6, "క్రింద మధ్య": 7, "క్రింద కుడి": 8,
                "ఎడమ": [0, 3, 6], "కుడి": [2, 5, 8],
                "పై": [0, 1, 2], "క్రింద": [6, 7, 8],
                "మూల": [0, 2, 6, 8]
            },
            "es": {  # Spanish
                "arriba izquierda": 0, "arriba centro": 1, "arriba derecha": 2,
                "medio izquierda": 3, "centro": 4, "medio derecha": 5,
                "abajo izquierda": 6, "abajo centro": 7, "abajo derecha": 8,
                "izquierda": [0, 3, 6], "derecha": [2, 5, 8],
                "arriba": [0, 1, 2], "abajo": [6, 7, 8],
                "esquina": [0, 2, 6, 8]
            },
            "fr": {  # French
                "haut gauche": 0, "haut centre": 1, "haut droite": 2,
                "milieu gauche": 3, "centre": 4, "milieu droite": 5,
                "bas gauche": 6, "bas centre": 7, "bas droite": 8,
                "gauche": [0, 3, 6], "droite": [2, 5, 8],
                "haut": [0, 1, 2], "bas": [6, 7, 8],
                "coin": [0, 2, 6, 8]
            },
            "de": {  # German
                "oben links": 0, "oben mitte": 1, "oben rechts": 2,
                "mitte links": 3, "mitte": 4, "mitte rechts": 5,
                "unten links": 6, "unten mitte": 7, "unten rechts": 8,
                "links": [0, 3, 6], "rechts": [2, 5, 8],
                "oben": [0, 1, 2], "unten": [6, 7, 8],
                "ecke": [0, 2, 6, 8]
            },
            "zh": {  # Chinese
                "左上": 0, "上中": 1, "右上": 2,
                "左中": 3, "中间": 4, "右中": 5,
                "左下": 6, "下中": 7, "右下": 8,
                "左": [0, 3, 6], "右": [2, 5, 8],
                "上": [0, 1, 2], "下": [6, 7, 8],
                "角": [0, 2, 6, 8]
            },
            "ja": {  # Japanese
                "左上": 0, "上中": 1, "右上": 2,
                "左中": 3, "中央": 4, "右中": 5,
                "左下": 6, "下中": 7, "右下": 8,
                "左": [0, 3, 6], "右": [2, 5, 8],
                "上": [0, 1, 2], "下": [6, 7, 8],
                "角": [0, 2, 6, 8]
            },
            "ko": {  # Korean
                "왼쪽위": 0, "위중앙": 1, "오른쪽위": 2,
                "왼쪽중앙": 3, "중앙": 4, "오른쪽중앙": 5,
                "왼쪽아래": 6, "아래중앙": 7, "오른쪽아래": 8,
                "왼쪽": [0, 3, 6], "오른쪽": [2, 5, 8],
                "위": [0, 1, 2], "아래": [6, 7, 8],
                "모서리": [0, 2, 6, 8]
            },
            "ru": {  # Russian
                "верхний левый": 0, "верхний центр": 1, "верхний правый": 2,
                "средний левый": 3, "центр": 4, "средний правый": 5,
                "нижний левый": 6, "нижний центр": 7, "нижний правый": 8,
                "левый": [0, 3, 6], "правый": [2, 5, 8],
                "верхний": [0, 1, 2], "нижний": [6, 7, 8],
                "угол": [0, 2, 6, 8]
            }
        }
    
    def make_move(self, position):
        """Make a move on the board. Returns (success, game_state_message)"""
        if self.game_over:
            return False, "Game is already over!"
        
        # Convert position to index if it's a text position
        if isinstance(position, str):
            position = position.lower().strip()
            position = self.translations.get(position, -1)
        
        if not (0 <= position <= 8):
            return False, "Invalid position!"
            
        if self.board[position] != " ":
            return False, "Position already taken!"
            
        # Make the move
        self.board[position] = self.current_player
        
        # Check win conditions
        if self.check_winner():
            self.game_over = True
            self.winner = self.current_player
            return True, f"Player {self.current_player} wins!"
            
        # Check draw
        if " " not in self.board:
            self.game_over = True
            return True, "It's a draw!"
            
        # Switch players
        self.current_player = "O" if self.current_player == "X" else "X"
        return True, "Move successful"
    
    def bot_move(self):
        """Make a bot move based on difficulty"""
        if self.game_over or "O" not in [self.current_player]:
            return False, "Not bot's turn!"
            
        # Get empty positions
        empty_positions = [i for i, mark in enumerate(self.board) if mark == " "]
        if not empty_positions:
            return False, "No moves available!"
            
        # Choose move based on difficulty
        if self.difficulty == GameDifficulty.EASY:
            position = random.choice(empty_positions)
        else:  # HARD - Use minimax
            position = self.get_best_move()
            
        return self.make_move(position)
    
    def check_winner(self):
        """Check if there's a winner"""
        # Define winning combinations
        wins = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]
        
        return any(
            self.board[a] == self.board[b] == self.board[c] != " "
            for a, b, c in wins
        )
    
    def get_best_move(self):
        """Find the best move using minimax algorithm"""
        best_score = float('-inf')
        best_move = None
        
        for i in range(9):
            if self.board[i] == " ":
                self.board[i] = "O"
                score = self.minimax(0, False)
                self.board[i] = " "
                
                if score > best_score:
                    best_score = score
                    best_move = i
        
        return best_move
    
    def minimax(self, depth, is_maximizing):
        """Minimax algorithm for optimal moves"""
        # Terminal states
        if self.check_winner():
            return 1 if is_maximizing else -1
        if " " not in self.board:
            return 0
            
        if is_maximizing:
            best_score = float('-inf')
            for i in range(9):
                if self.board[i] == " ":
                    self.board[i] = "O"
                    score = self.minimax(depth + 1, False)
                    self.board[i] = " "
                    best_score = max(score, best_score)
            return best_score
        else:
            best_score = float('inf')
            for i in range(9):
                if self.board[i] == " ":
                    self.board[i] = "X"
                    score = self.minimax(depth + 1, True)
                    self.board[i] = " "
                    best_score = min(score, best_score)
            return best_score
    
    def parse_move(self, user_input, language="en"):
        """Parse user input in different languages to get the board position"""
        user_input = user_input.lower().strip()
        
        # Extract move description from full command
        move_words = []
        for word in user_input.split():
            if word in ['move', 'place', 'put', 'mark', 'choose', 'select', 'make', 'play']:
                continue
            move_words.append(word)
        
        move_text = ' '.join(move_words)
        
        # Try direct position lookup
        position = self.translations.get(move_text, -1)
        if position != -1:
            return position
        
        # Try language-specific translations
        if language in self.multilingual_positions:
            lang_translations = self.multilingual_positions[language]
            for key, pos in lang_translations.items():
                if key in move_text:
                    return pos
        
        # Try positional words
        position_words = {
            'top': [0, 1, 2],
            'middle': [3, 4, 5],
            'center': [4],
            'bottom': [6, 7, 8],
            'left': [0, 3, 6],
            'right': [2, 5, 8],
            'corner': [0, 2, 6, 8]
        }
        
        # Look for position combinations
        found_positions = []
        for word, positions in position_words.items():
            if word in move_text:
                found_positions.append(positions)
        
        if len(found_positions) > 1:
            # Find intersection of position lists
            intersection = set(found_positions[0])
            for positions in found_positions[1:]:
                intersection &= set(positions)
            
            if intersection:
                # Return the first valid empty position from intersection
                for pos in intersection:
                    if self.board[pos] == " ":
                        return pos
        
        elif len(found_positions) == 1:
            # Return first valid empty position from single list
            for pos in found_positions[0]:
                if self.board[pos] == " ":
                    return pos
        
        # Try to extract numerical position (0-8)
        try:
            position = int(user_input)
            if 0 <= position <= 8:
                return position
        except ValueError:
            pass
        
        return -1  # Invalid move
    
    def get_board_state(self):
        """Get current board state as a 3x3 grid"""
        return [self.board[i:i+3] for i in range(0, 9, 3)]
    
    def get_game_state(self):
        """Get current game state for frontend"""
        return {
            "board": self.board,
            "currentPlayer": self.current_player,
            "winner": self.winner,
            "gameOver": self.game_over,
            "boardGrid": self.get_board_state()
        }
