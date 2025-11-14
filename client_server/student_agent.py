"""
Student Agent Implementation for River and Stones Game

This file contains the essential utilities and template for implementing your AI agent.
Your task is to complete the StudentAgent class with intelligent move selection.

Game Rules:
- Goal: Get 4 of your stones into the opponent's scoring area
- Pieces can be stones or rivers (horizontal/vertical orientation)  
- Actions: move, push, flip (stone↔river), rotate (river orientation)
- Rivers enable flow-based movement across the board

Your Task:
Implement the choose() method in the StudentAgent class to select optimal moves.
You may add any helper methods and modify the evaluation function as needed.
"""

import random
import copy
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from collections import deque

# ==================== GAME UTILITIES ====================
# Essential utility functions for game state analysis

def in_bounds(x: int, y: int, rows: int, cols: int) -> bool:
    """Check if coordinates are within board boundaries."""
    return 0 <= x < cols and 0 <= y < rows

def score_cols_for(cols: int) -> List[int]:
    """Get the column indices for scoring areas."""
    w = 4
    start = max(0, (cols - w) // 2)
    return list(range(start, start + w))

def top_score_row() -> int:
    """Get the row index for Circle's scoring area."""
    return 2

def bottom_score_row(rows: int) -> int:
    """Get the row index for Square's scoring area."""
    return rows - 3

def is_opponent_score_cell(x: int, y: int, player: str, rows: int, cols: int, score_cols: List[int]) -> bool:
    """Check if a cell is in the opponent's scoring area."""
    if player == "circle":
        return (y == bottom_score_row(rows)) and (x in score_cols)
    else:
        return (y == top_score_row()) and (x in score_cols)

def is_own_score_cell(x: int, y: int, player: str, rows: int, cols: int, score_cols: List[int]) -> bool:
    """Check if a cell is in the player's own scoring area."""
    if player == "circle":
        return (y == top_score_row()) and (x in score_cols)
    else:
        return (y == bottom_score_row(rows)) and (x in score_cols)

def get_opponent(player: str) -> str:
    """Get the opponent player identifier."""
    return "square" if player == "circle" else "circle"

# ==================== MOVE GENERATION HELPERS ====================

def get_valid_moves_for_piece(board, x: int, y: int, player: str, rows: int, cols: int, score_cols: List[int]) -> List[Dict[str, Any]]:
    """
    Generate all valid moves for a specific piece.
    
    Args:
        board: Current board state
        x, y: Piece position
        player: Current player
        rows, cols: Board dimensions
        score_cols: Scoring column indices
    
    Returns:
        List of valid move dictionaries
    """
    moves = []
    piece = board[y][x]
    
    if piece is None or piece.owner != player:
        return moves
    
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    
    if piece.side == "stone":
        # Stone movement
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if not in_bounds(nx, ny, rows, cols):
                continue
            
            if is_opponent_score_cell(nx, ny, player, rows, cols, score_cols):
                continue
            
            if board[ny][nx] is None:
                # Simple move
                moves.append({"action": "move", "from": [x, y], "to": [nx, ny]})
            elif board[ny][nx].owner != player:
                # Push move
                px, py = nx + dx, ny + dy
                if (in_bounds(px, py, rows, cols) and 
                    board[py][px] is None and 
                    not is_opponent_score_cell(px, py, player, rows, cols, score_cols)):
                    moves.append({"action": "push", "from": [x, y], "to": [nx, ny], "pushed_to": [px, py]})
        
        # Stone to river flips
        for orientation in ["horizontal", "vertical"]:
            moves.append({"action": "flip", "from": [x, y], "orientation": orientation})
    
    else:  # River piece
        # River to stone flip
        moves.append({"action": "flip", "from": [x, y]})
        
        # River rotation
        moves.append({"action": "rotate", "from": [x, y]})
    
    return moves

def generate_all_moves(board: List[List[Any]], player: str, rows: int, cols: int, score_cols: List[int]) -> List[Dict[str, Any]]:
    """
    Generate all legal moves for the current player.
    
    Args:
        board: Current board state
        player: Current player ("circle" or "square")
        rows, cols: Board dimensions
        score_cols: Scoring column indices
    
    Returns:
        List of all valid move dictionaries
    """
    all_moves = []
    
    for y in range(rows):
        for x in range(cols):
            piece = board[y][x]
            if piece and piece.owner == player:
                piece_moves = get_valid_moves_for_piece(board, x, y, player, rows, cols, score_cols)
                all_moves.extend(piece_moves)
    
    return all_moves

# ==================== BOARD EVALUATION ====================

def count_stones_in_scoring_area(board: List[List[Any]], player: str, rows: int, cols: int, score_cols: List[int]) -> int:
    """Count how many stones a player has in their scoring area."""
    count = 0
    
    if player == "circle":
        score_row = top_score_row()
    else:
        score_row = bottom_score_row(rows)
    
    for x in score_cols:
        if in_bounds(x, score_row, rows, cols):
            piece = board[score_row][x]
            if piece and piece.owner == player and piece.side == "stone":
                count += 1
    
    return count

def basic_evaluate_board(board: List[List[Any]], player: str, rows: int, cols: int, score_cols: List[int]) -> float:
    """
    Basic board evaluation function.
    
    Returns a score where higher values are better for the given player.
    Students can use this as a starting point and improve it.
    """
    score = 0.0
    opponent = get_opponent(player)
    
    # Count stones in scoring areas
    player_scoring_stones = count_stones_in_scoring_area(board, player, rows, cols, score_cols)
    opponent_scoring_stones = count_stones_in_scoring_area(board, opponent, rows, cols, score_cols)
    
    score += player_scoring_stones * 100  
    score -= opponent_scoring_stones * 100  
    
    # Count total pieces and positional factors
    for y in range(rows):
        for x in range(cols):
            piece = board[y][x]
            if piece and piece.owner == player and piece.side == "stone":
                # Basic positional scoring
                if player == "circle":
                    score += (rows - y) * 0.1
                else:
                    score += y * 0.1
    
    return score

def simulate_move(board: List[List[Any]], move: Dict[str, Any], player: str, rows: int, cols: int, score_cols: List[int]) -> Tuple[bool, Any]:
    """
    Simulate a move on a copy of the board.
    
    Args:
        board: Current board state
        move: Move to simulate
        player: Player making the move
        rows, cols: Board dimensions
        score_cols: Scoring column indices
    
    Returns:
        (success: bool, new_board_state or error_message)
    """
    # Import the game engine's move validation function
    try:
        from gameEngine import validate_and_apply_move
        board_copy = copy.deepcopy(board)
        success, message = validate_and_apply_move(board_copy, move, player, rows, cols, score_cols)
        return success, board_copy if success else message
    except ImportError:
        # Fallback to basic simulation if game engine not available
        return True, copy.deepcopy(board)

# ==================== BASE AGENT CLASS ====================

class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    """
    
    def __init__(self, player: str):
        """Initialize agent with player identifier."""
        self.player = player
        self.opponent = get_opponent(player)
    
    @abstractmethod
    def choose(self, board: List[List[Any]], rows: int, cols: int, score_cols: List[int], current_player_time: float, opponent_time: float) -> Optional[Dict[str, Any]]:
        """
        Choose the best move for the current board state.
        
        Args:
            board: 2D list representing the game board
            rows, cols: Board dimensions
            score_cols: List of column indices for scoring areas
        
        Returns:
            Dictionary representing the chosen move, or None if no moves available
        """
        pass

# ==================== STUDENT AGENT IMPLEMENTATION ====================

class StudentAgent(BaseAgent):
    """
    - Defensive-first agent
    - Starts with a hard-coded defensive setup (for testing), then runs reactive defense.
    """

    def __init__(self, player: str, edge: str = "right"):
        super().__init__(player)
        self.edge = edge

        # --- (keep fields but we won't use the attack plan for now) ---
        self._plan: Optional[List[Dict[str, Any]]] = None
        self._i: int = 0
        self._plan_printed = False

        # defense state
        self.defense = None               # layout info (sa_row, guards, etc.)
        self.restore_queue = deque()      # flips to restore guards after push
        self._def_setup_done = False      # whether we ran the initial scripted defense plan
        self._def_setup_plan: List[Dict[str, Any]] = []
        self._def_setup_idx = 0

    # -------------------- PUBLIC: CHOOSE --------------------
    def choose(
        self,
        board: List[List[Any]],
        rows: int,
        cols: int,
        score_cols: List[int],
        current_player_time: float,
        opponent_time: float,
    ) -> Optional[Dict[str, Any]]:

        # ---- lazy init holders ----
        if not hasattr(self, "_def_setup_done"):
            self._def_setup_done = False
        if not hasattr(self, "_def_setup_plan"):
            self._def_setup_plan = []
        if not hasattr(self, "_def_setup_idx"):
            self._def_setup_idx = 0

        if not hasattr(self, "_atk_plan"):
            self._atk_plan = None
        if not hasattr(self, "_atk_idx"):
            self._atk_idx = 0
        if not hasattr(self, "_atk_printed"):
            self._atk_printed = False

        # 0) Ensure defense geometry is initialized
        if self.defense is None:
            self.init_defense_layout(board, rows, cols, score_cols)

        # 1) INITIAL DEFENSE SCRIPT (one-time)
        if not self._def_setup_done:
            if not self._def_setup_plan:
                # Your precomputed defensive opener (already implemented by you)
                self._def_setup_plan = self.get_initial_defense_moves(rows, cols)
                self._def_setup_idx = 0
                if self._def_setup_plan:
                    print(f"[{self.player}] Initial DEF plan ({rows}x{cols}, steps={len(self._def_setup_plan)}):")
                    for i, m in enumerate(self._def_setup_plan, 1):
                        print(f"{i:02d}. {m}")

            # Play next applicable scripted defense move; skip stale ones
            while self._def_setup_idx < len(self._def_setup_plan):
                m = self._def_setup_plan[self._def_setup_idx]
                if self.check_if_move_applicable(board, self.player, m):
                    self._def_setup_idx += 1
                    return m
                self._def_setup_idx += 1

            # Finished scripted defense
            self._def_setup_done = True

        # 2) HIGH PRIORITY: REACTIVE DEFENSE (includes restores / pushes / alignments)
        dm = self.get_defensive_move(board, rows, cols, score_cols)
        if dm:
            return dm

        # 3) PREDEFINED ATTACK SCRIPT (runs only after initial defense is done)
        if self._def_setup_done:
            # Lazy init attack plan
            if self._atk_plan is None:
                # Use your predefined attack book
                if hasattr(self, "get_initial_attack_moves"):
                    self._atk_plan = self.get_initial_attack_moves(rows, cols)
                else:
                    # If you wrapped it differently, swap the call here
                    self._atk_plan = []
                self._atk_idx = 0
                if self._atk_plan and not self._atk_printed:
                    print(f"[{self.player}] Initial ATK plan ({rows}x{cols}, steps={len(self._atk_plan)}):")
                    for i, m in enumerate(self._atk_plan, 1):
                        print(f"{i:02d}. {m}")
                    self._atk_printed = True

            # While there are scripted attack moves left
            if self._atk_plan:
                # Before executing each attack step, re-check reactive defense (still higher priority)
                dm2 = self.get_defensive_move(board, rows, cols, score_cols)
                if dm2:
                    return dm2

                # Try current attack step ONLY; if not applicable -> return None (per requirement)
                if self._atk_idx < len(self._atk_plan):
                    am = self._atk_plan[self._atk_idx]
                    if self.check_if_move_applicable(board, self.player, am):
                        self._atk_idx += 1
                        return am
                    else:
                        # TODO: attack step not currently feasible; handle re-planning/escalation later.
                        print("Attack Move Not possible, invoking minimax =", am)
                        if not hasattr(self, "move_history"):
                            self.move_history = []
                        best_move = get_minimax_move(board, self.player, rows, cols, score_cols, self.move_history)
                        if best_move:
                            self.move_history.append(best_move)
                            return best_move
                        return None
                # Attack plan exhausted -> fall through to fallback random

        # 4) FALLBACK: any legal move (prefer flips)
        # moves = generate_all_moves(board, self.player, rows, cols, score_cols)
        # if not moves:
        #     return None
        # flips = [m for m in moves if m["action"] == "flip"]
        # return random.choice(flips or moves)

        best_move = get_minimax_move(board, self.player, rows, cols, score_cols, getattr(self, "move_history", []))
        if best_move:
            self.move_history.append(best_move)
            return best_move
        return random.choice(flips or moves)

    # -------------------- DEFENSE: get the precomputed defense moves based on piece type and board size --------------------
    def get_initial_defense_moves(self, rows: int, cols: int) -> List[Dict[str, Any]]:
        """
        Returns precomputed defensive setup moves based on board size and player.
        Handles circle/square for 13x12, 15x14, and 17x16 boards.

        Falls back to [] if not defined.
        """

        PREDEFINED_MOVES_DEFENCE = {
            "square": {
                13: [
                    {"action": "flip", "from": [3, 3], "orientation": "vertical"},
                    {"action": "move", "from": [3, 3], "to": [3, 2]},
                    {"action": "flip", "from": [8, 3], "orientation": "vertical"},
                    {"action": "move", "from": [8, 3], "to": [8, 2]},
                    {"action": "flip", "from": [4, 3], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [5, 3], "to": [3, 3]},
                    {"action": "move", "from": [4, 3], "to": [3, 1]},
                    {"action": "move", "from": [3, 3], "to": [6, 1]},
                    {"action": "move", "from": [3, 1], "to": [4, 1]},
                ],
                15: [
                    {"action": "flip", "from": [3, 3], "orientation": "vertical"},
                    {"action": "move", "from": [3, 3], "to": [3, 2]},
                    {"action": "flip", "from": [9, 3], "orientation": "vertical"},
                    {"action": "move", "from": [9, 3], "to": [9, 2]},
                    {"action": "flip", "from": [4, 3], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [5, 3], "to": [3, 3]},
                    {"action": "move", "from": [4, 3], "to": [3, 1]},
                    {"action": "move", "from": [3, 3], "to": [7, 1]},
                    {"action": "move", "from": [3, 1], "to": [4, 1]},
                    {"action": "move", "from": [4, 1], "to": [5, 1]},
                ],
                17: [
                    {"action": "flip", "from": [4, 3], "orientation": "vertical"},
                    {"action": "move", "from": [4, 3], "to": [4, 2]},
                    {"action": "flip", "from": [11, 3], "orientation": "vertical"},
                    {"action": "move", "from": [11, 3], "to": [11, 2]},
                    {"action": "flip", "from": [5, 3], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 3], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [7, 3], "to": [4, 3]},
                    {"action": "move", "from": [6, 3], "to": [4, 1]},
                    {"action": "move", "from": [5, 3], "to": [9, 1]},
                    {"action": "move", "from": [4, 3], "to": [7, 1]},
                    {"action": "move", "from": [4, 1], "to": [5, 1]},
                ],
            },
            "circle": {
                13: [
                    {"action": "flip", "from": [3, 9], "orientation": "vertical"},
                    {"action": "move", "from": [3, 9], "to": [3, 10]},
                    {"action": "flip", "from": [8, 9], "orientation": "vertical"},
                    {"action": "move", "from": [8, 9], "to": [8, 10]},
                    {"action": "flip", "from": [4, 9], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 9], "orientation": "horizontal"},
                    {"action": "move", "from": [5, 9], "to": [3, 9]},
                    {"action": "move", "from": [4, 9], "to": [3, 11]},
                    {"action": "move", "from": [3, 9], "to": [6, 11]},
                    {"action": "move", "from": [3, 11], "to": [4, 11]},
                ],
                15: [
                    {"action": "flip", "from": [3, 11], "orientation": "vertical"},
                    {"action": "move", "from": [3, 11], "to": [3, 12]},
                    {"action": "flip", "from": [9, 11], "orientation": "vertical"},
                    {"action": "move", "from": [9, 11], "to": [9, 12]},
                    {"action": "flip", "from": [4, 11], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 11], "orientation": "horizontal"},
                    {"action": "move", "from": [5, 11], "to": [3, 11]},
                    {"action": "move", "from": [4, 11], "to": [3, 13]},
                    {"action": "move", "from": [3, 11], "to": [7, 13]},
                    {"action": "move", "from": [3, 13], "to": [4, 13]},
                    {"action": "move", "from": [4, 13], "to": [5, 13]},
                ],
                17: [
                    {"action": "flip", "from": [4, 13], "orientation": "vertical"},
                    {"action": "move", "from": [4, 13], "to": [4, 14]},
                    {"action": "flip", "from": [11, 13], "orientation": "vertical"},
                    {"action": "move", "from": [11, 13], "to": [11, 14]},
                    {"action": "flip", "from": [5, 13], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 13], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 13], "orientation": "horizontal"},
                    {"action": "move", "from": [7, 13], "to": [4, 13]},
                    {"action": "move", "from": [6, 13], "to": [4, 15]},
                    {"action": "move", "from": [5, 13], "to": [9, 15]},
                    {"action": "move", "from": [4, 13], "to": [7, 15]},
                    {"action": "move", "from": [4, 15], "to": [5, 15]},
                ],
            },
        }

        # Return precomputed plan if available
        plan = PREDEFINED_MOVES_DEFENCE.get(self.player, {}).get(rows, [])
        return plan.copy()  # defensive copy
    
    # -------- ATTACK: predefined moves for attack
    def get_initial_attack_moves(self, rows: int, cols: int) -> List[Dict[str, Any]]:
        """
        Returns precomputed ATTACK setup moves based on board size and player.
        Supports circle/square for 13x12, 15x14, and 17x16 boards.
        Falls back to [] if not defined.
        """
        PREDEFINED_MOVES_ATTACK = {
            "square": {
                13: [
                    {"action": "flip", "from": [7, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 4], "orientation": "vertical"},
                    {"action": "move", "from": [8, 4], "to": [10, 4]},
                    {"action": "flip", "from": [6, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [3, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [7, 3], "to": [10, 12]},
                    {"action": "move", "from": [6, 3], "to": [7, 12]},
                    {"action": "flip", "from": [7, 12], "orientation": "vertical"},
                    {"action": "move", "from": [3, 4], "to": [7, 10]},
                    {"action": "move", "from": [4, 4], "to": [4, 10]},
                    {"action": "move", "from": [5, 4], "to": [5, 10]},
                    {"action": "move", "from": [6, 4], "to": [6, 10]},
                    {"action": "flip", "from": [7, 10]},
                    {"action": "flip", "from": [6, 10]},
                    {"action": "flip", "from": [5, 10]},
                    {"action": "flip", "from": [4, 10]},
                ],
                15: [
                    {"action": "flip", "from": [8, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [9, 4], "orientation": "vertical"},
                    {"action": "move", "from": [9, 4], "to": [12, 4]},
                    {"action": "flip", "from": [7, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [3, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [8, 3], "to": [12, 14]},
                    {"action": "move", "from": [7, 3], "to": [8, 14]},
                    {"action": "flip", "from": [8, 14], "orientation": "vertical"},
                    {"action": "move", "from": [3, 4], "to": [8, 12]},
                    {"action": "move", "from": [4, 4], "to": [4, 12]},
                    {"action": "move", "from": [5, 4], "to": [5, 12]},
                    {"action": "move", "from": [6, 4], "to": [6, 12]},
                    {"action": "move", "from": [7, 4], "to": [7, 12]},
                    {"action": "flip", "from": [4, 12]},
                    {"action": "flip", "from": [5, 12]},
                    {"action": "flip", "from": [6, 12]},
                    {"action": "flip", "from": [7, 12]},
                    {"action": "flip", "from": [8, 12]},
                ],
                17: [
                    {"action": "flip", "from": [10, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [11, 4], "orientation": "vertical"},
                    {"action": "move", "from": [11, 4], "to": [14, 4]},
                    {"action": "flip", "from": [9, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 4], "orientation": "horizontal"},
                    {"action": "flip", "from": [10, 3], "orientation": "horizontal"},
                    {"action": "move", "from": [10, 3], "to": [14, 16]},
                    {"action": "move", "from": [9, 3], "to": [9, 16]},
                    {"action": "flip", "from": [9, 16], "orientation": "vertical"},
                    {"action": "move", "from": [4, 4], "to": [9, 14]},
                    {"action": "move", "from": [5, 4], "to": [5, 14]},
                    {"action": "move", "from": [6, 4], "to": [6, 14]},
                    {"action": "move", "from": [7, 4], "to": [7, 14]},
                    {"action": "move", "from": [8, 4], "to": [8, 14]},
                    {"action": "move", "from": [9, 4], "to": [10, 14]},
                    {"action": "flip", "from": [5, 14]},
                    {"action": "flip", "from": [6, 14]},
                    {"action": "flip", "from": [7, 14]},
                    {"action": "flip", "from": [8, 14]},
                    {"action": "flip", "from": [9, 14]},
                    {"action": "flip", "from": [10, 14]},
                ],
            },
            "circle": {
                13: [
                    {"action": "flip", "from": [7, 8], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 8], "orientation": "vertical"},
                    {"action": "move", "from": [8, 8], "to": [10, 8]},
                    {"action": "flip", "from": [6, 8], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 8], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 8], "orientation": "horizontal"},
                    {"action": "flip", "from": [3, 8], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 9], "orientation": "horizontal"},
                    {"action": "move", "from": [7, 9], "to": [10, 0]},
                    {"action": "move", "from": [6, 9], "to": [7, 0]},
                    {"action": "flip", "from": [7, 0], "orientation": "vertical"},
                    {"action": "move", "from": [3, 8], "to": [7, 2]},
                    {"action": "move", "from": [4, 8], "to": [4, 2]},
                    {"action": "move", "from": [5, 8], "to": [5, 2]},
                    {"action": "move", "from": [6, 8], "to": [6, 2]},
                    {"action": "flip", "from": [7, 2]},
                    {"action": "flip", "from": [6, 2]},
                    {"action": "flip", "from": [5, 2]},
                    {"action": "flip", "from": [4, 2]},
                ],
                15: [
                    {"action": "flip", "from": [8, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [9, 10], "orientation": "vertical"},
                    {"action": "move", "from": [9, 10], "to": [12, 10]},
                    {"action": "flip", "from": [7, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [3, 10], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 11], "orientation": "horizontal"},
                    {"action": "move", "from": [8, 11], "to": [12, 0]},
                    {"action": "move", "from": [7, 11], "to": [8, 0]},
                    {"action": "flip", "from": [8, 0], "orientation": "vertical"},
                    {"action": "move", "from": [3, 10], "to": [8, 2]},
                    {"action": "move", "from": [4, 10], "to": [4, 2]},
                    {"action": "move", "from": [5, 10], "to": [5, 2]},
                    {"action": "move", "from": [6, 10], "to": [6, 2]},
                    {"action": "move", "from": [7, 10], "to": [7, 2]},
                    {"action": "flip", "from": [4, 2]},
                    {"action": "flip", "from": [5, 2]},
                    {"action": "flip", "from": [6, 2]},
                    {"action": "flip", "from": [7, 2]},
                    {"action": "flip", "from": [8, 2]},
                ],
                17: [
                    {"action": "flip", "from": [10, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [11, 12], "orientation": "vertical"},
                    {"action": "move", "from": [11, 12], "to": [14, 12]},
                    {"action": "flip", "from": [9, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [8, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [7, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [6, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [5, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [4, 12], "orientation": "horizontal"},
                    {"action": "flip", "from": [10, 13], "orientation": "horizontal"},
                    {"action": "move", "from": [10, 13], "to": [14, 0]},
                    {"action": "move", "from": [9, 13], "to": [9, 0]},
                    {"action": "flip", "from": [9, 0], "orientation": "vertical"},
                    {"action": "move", "from": [4, 12], "to": [9, 2]},
                    {"action": "move", "from": [5, 12], "to": [5, 2]},
                    {"action": "move", "from": [6, 12], "to": [6, 2]},
                    {"action": "move", "from": [7, 12], "to": [7, 2]},
                    {"action": "move", "from": [8, 12], "to": [8, 2]},
                    {"action": "move", "from": [9, 12], "to": [10, 2]},
                    {"action": "flip", "from": [5, 2]},
                    {"action": "flip", "from": [6, 2]},
                    {"action": "flip", "from": [7, 2]},
                    {"action": "flip", "from": [8, 2]},
                    {"action": "flip", "from": [9, 2]},
                    {"action": "flip", "from": [10, 2]},
                ],
            },
        }

        return PREDEFINED_MOVES_ATTACK.get(self.player, {}).get(rows, []).copy()

    @staticmethod
    def check_if_move_applicable(board, player: str, move: Dict[str, Any]) -> bool:
        fr = move.get("from")
        if not fr or not isinstance(fr, (list, tuple)) or len(fr) != 2:
            return True
        fy = fr[1]; fx = fr[0]
        if not in_bounds(fx, fy, len(board), len(board[0])):
            return False
        p = board[fy][fx]
        return bool(p and p.owner == player)

    

    # ------ Defense mechanism for guarding rivers ---------------
    def init_defense_layout(self, board, rows, cols, score_cols):
        """
        Decide guard placement based on board size and player.
        - Horizontal guards sit one row beyond the SA (toward the opponent).
        * circle: SA at top -> guards on sa_row+1
        * square: SA at bottom -> guards on sa_row-1
        - We choose alternating SA cells:
            small/medium (k=4/5): indices [0,2]  (2 guards)
            large (k=6):          indices [0,2,4] (3 guards)
        - Also return side vertical guard columns (optional to use).
        """
        sa_row = top_score_row() if self.player == "circle" else bottom_score_row(rows)
        k = len(score_cols)
        k = min(k, 6)
        sa_cols_sorted = sorted(score_cols)

        # horizontal guard row (front line)
        guard_row = sa_row + 1 if self.player == "circle" else sa_row - 1

        # which SA columns to guard (alternating)
        if k <= 5:
            idxs = [0, 2] if k >= 3 else [0, 1]  # fallback if weird k
        else:
            idxs = [0, 2, 4]

        horiz_guards = [(sa_cols_sorted[i], guard_row) for i in idxs if 0 <= i < k]

        # optional side-guards (vertical) just outside SA
        left_col  = sa_cols_sorted[0] - 1
        right_col = sa_cols_sorted[-1] + 1
        side_guards = []
        if 0 <= left_col < cols:
            side_guards.append((left_col, guard_row))   # vertical
        if 0 <= right_col < cols:
            side_guards.append((right_col, guard_row))  # vertical

        self.defense = {
            "sa_row": sa_row,
            "horiz_guards": horiz_guards,   # expect horizontal rivers here
            "side_guards": side_guards,     # expect vertical rivers here
        }
        if not hasattr(self, "restore_queue"):
            self.restore_queue = deque()


    def get_defensive_move(self, board, rows, cols, score_cols):
        """
        Advanced zone-based defense logic.

        - Side guards (vertical) are untouched.
        - Horizontal guards (below/above SA) protect SA cells in zones of 3 (or remaining).
        - Each guard handles intrusions (stones/rivers) within its assigned SA zone.
        """
        if self.defense is None:
            self.init_defense_layout(board, rows, cols, score_cols)

        # 1️⃣ Any pending restore action first
        if self.restore_queue:
            return self.restore_queue.popleft()

        sa_row = self.defense["sa_row"]
        horiz_guards = list(self.defense.get("horiz_guards", []))
        me = self.player
        opp = get_opponent(me)

        # guard row location
        guard_row = sa_row + 1 if me == "circle" else sa_row - 1
        sa_cols_sorted = sorted(score_cols)
        k = len(sa_cols_sorted)

        # ---- Build ZONES each guard protects (3 columns or remainder) ----
        zone_map = {}  # guard (gx,gy) → dict(zone_cols, center_col)
        if k >= 4:
            if k == 4:
                zones = [sa_cols_sorted[0:3], sa_cols_sorted[3:4]]
            elif k == 5:
                zones = [sa_cols_sorted[0:3], sa_cols_sorted[3:5]]
            else:  # k==6 or more
                zones = [sa_cols_sorted[0:3], sa_cols_sorted[3:6]]
        else:
            zones = [sa_cols_sorted]

        for i, (gx, gy) in enumerate(horiz_guards):
            if i < len(zones):
                zone_cols = zones[i]
                center_col = zone_cols[len(zone_cols)//2]
                zone_map[(gx, gy)] = {"zone_cols": zone_cols, "center_col": center_col}

        # helper: can push destination accept the piece?
        def ok_push_dest(x, y, pushed_player):
            if not in_bounds(x, y, rows, cols):
                return False
            if board[y][x] is not None:
                return False
            return not is_opponent_score_cell(x, y, pushed_player, rows, cols, score_cols)

        def queue_restore(gx, gy, center_col):
            # restore flip and move back
            self.restore_queue.append({"action": "flip", "from": [gx, gy], "orientation": "horizontal"})
            if gx != center_col:
                self.restore_queue.append({"action": "move", "from": [gx, gy], "to": [center_col, guard_row]})

        # 2️⃣ Restore guards if they are our stones or misoriented rivers
        for (gx, gy), zone in zone_map.items():
            if not in_bounds(gx, gy, rows, cols):
                continue
            p = board[gy][gx]
            if p and p.owner == me and (p.side != "river" or p.orientation != "horizontal"):
                return {"action": "flip", "from": [gx, gy], "orientation": "horizontal"}

        # 3️⃣ Intruder (opponent stone) detection and push inside zone
        for (gx, gy), zone in zone_map.items():
            if not in_bounds(gx, gy, rows, cols):
                continue
            guard_piece = board[gy][gx]
            if not (guard_piece and guard_piece.owner == me and guard_piece.side == "river" and guard_piece.orientation == "horizontal"):
                continue

            zone_cols = zone["zone_cols"]
            center_col = zone["center_col"]

            for cx in zone_cols:
                # check SA row and guard row for enemy pieces
                for ry in (sa_row, guard_row):
                    if not in_bounds(cx, ry, rows, cols):
                        continue
                    target = board[ry][cx]
                    if not target or target.owner != opp:
                        continue

                    # choose push direction away from center
                    dx = 1 if cx >= center_col else -1
                    tx, ty = gx, gy
                    pushed_from = (cx, ry)
                    px, py = cx + dx, ry
                    last_ok = None
                    while in_bounds(px, py, rows, cols) and ok_push_dest(px, py, target.owner):
                        last_ok = (px, py)
                        px += dx
                    if last_ok is None:
                        px, py = cx + dx, ry
                        if not ok_push_dest(px, py, target.owner):
                            continue
                        pushed_to = (px, py)
                    else:
                        pushed_to = last_ok

                    move = {
                        "action": "push",
                        "from": [tx, ty],
                        "to": [pushed_from[0], pushed_from[1]],
                        "pushed_to": [pushed_to[0], pushed_to[1]],
                    }
                    queue_restore(cx, ry, center_col)
                    return move

        # 4️⃣ Opponent’s vertical river check (just above/below SA)
        check_row = sa_row - 1 if me == "circle" else sa_row + 1
        for (gx, gy), zone in zone_map.items():
            zone_cols = zone["zone_cols"]
            center_col = zone["center_col"]
            for cx in zone_cols:
                if not in_bounds(cx, check_row, rows, cols):
                    continue
                p = board[check_row][cx]
                if p and p.owner == opp and p.side == "river" and p.orientation == "vertical":
                    # if our guard not already there, move under that column
                    if gx != cx or gy != guard_row:
                        return {"action": "move", "from": [gx, gy], "to": [cx, guard_row]}
                    # once there, queue move back after a turn
                    queue_restore(gx, gy, center_col)
                    return None

        # 5️⃣ Nothing to do
        return None

    # -------------------- MINIMAX WITH ALPHA-BETA --------------------
    def manhattan_distance(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def min_manhattan_to_score(x, y, player, rows, cols, score_cols):
        """Get min distance from (x,y) to that player's scoring area."""
        if player == "circle":
            score_y = top_score_row()
        else:
            score_y = bottom_score_row(rows)
        return min(abs(y - score_y) + abs(x - sc) for sc in score_cols)

    def evaluate_board(board, player, rows, cols, score_cols):
        """Full evaluation function per your specification."""
        opponent = get_opponent(player)
        score = 0

        # pieces in scoring area
        score += count_stones_in_scoring_area(board, player, rows, cols, score_cols) * 1000
        score -= count_stones_in_scoring_area(board, opponent, rows, cols, score_cols) * 1000

        # proximity counts
        my_close, opp_close = 0, 0
        my_to_opp, opp_to_me = 0, 0
        for y in range(rows):
            for x in range(cols):
                p = board[y][x]
                if not p:
                    continue
                if p.owner == player:
                    d_own = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                    d_opp = min_manhattan_to_score(x, y, opponent, rows, cols, score_cols)
                    if d_own <= 2: my_close += 1
                    if d_opp <= 2: my_to_opp += 1
                else:
                    d_opp = min_manhattan_to_score(x, y, opponent, rows, cols, score_cols)
                    d_me  = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                    if d_opp <= 2: opp_close += 1
                    if d_me <= 2: opp_to_me += 1

        score += my_close * 100
        score -= opp_close * 100
        score += my_to_opp * 50
        score -= opp_to_me * 50

        return score


    def select_actions(board, player, rows, cols, score_cols):
        """Selective action generator as per your detailed rules."""
        moves = []
        all_moves = generate_all_moves(board, player, rows, cols, score_cols)
        opponent = get_opponent(player)

        for m in all_moves:
            fr = m.get("from")
            if not fr: continue
            x, y = fr

            # region restrictions
            if player == "circle" and y >= rows - 2: 
                continue
            if player == "square" and y <= 2:
                continue

            # skip if piece is in own SA
            if is_own_score_cell(x, y, player, rows, cols, score_cols):
                continue

            p = board[y][x]
            if not p or p.owner != player:
                continue

            # ---- stone ----
            if p.side == "stone":
                sa_moves = [mv for mv in all_moves if mv["action"] == "move" and mv["from"] == [x, y] and is_own_score_cell(mv["to"][0], mv["to"][1], player, rows, cols, score_cols)]
                if sa_moves:
                    chosen = random.choice(sa_moves)
                    moves.append(chosen)
                    moves.append({"action": "flip", "from": chosen["to"], "orientation": "horizontal"})
                else:
                    moves.append({"action": "flip", "from": [x, y], "orientation": "horizontal"})

            # ---- river vertical ----
            elif p.side == "river" and p.orientation == "vertical":
                sa_moves = [mv for mv in all_moves if mv["action"] == "move" and mv["from"] == [x, y] and is_own_score_cell(mv["to"][0], mv["to"][1], player, rows, cols, score_cols)]
                if sa_moves:
                    chosen = random.choice(sa_moves)
                    moves.append(chosen)
                    moves.append({"action": "rotate", "from": chosen["to"]})
                else:
                    moves.append({"action": "rotate", "from": [x, y]})

            # ---- river horizontal ----
            elif p.side == "river" and p.orientation == "horizontal":
                sa_moves = [mv for mv in all_moves if mv["action"] == "move" and mv["from"] == [x, y] and is_own_score_cell(mv["to"][0], mv["to"][1], player, rows, cols, score_cols)]
                if sa_moves:
                    moves.extend(sa_moves)
                else:
                    # distance-based filtering
                    filtered = []
                    for mv in all_moves:
                        if mv["from"] != [x, y] or mv["action"] != "move":
                            continue
                        fr_d = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                        to_d = min_manhattan_to_score(mv["to"][0], mv["to"][1], player, rows, cols, score_cols)
                        delta = to_d - fr_d
                        if delta < 0:
                            filtered.append((mv, abs(delta)))
                        elif delta <= 2:
                            filtered.append((mv, 0))
                    if filtered:
                        filtered.sort(key=lambda t: (-t[1]))  # best distance decrease first
                        top_moves = [mv for mv, _ in filtered[:2]]
                        moves.extend(top_moves)

                # push moves — only if pushes opponent farthest
                push_moves = [mv for mv in all_moves if mv["action"] == "push" and mv["from"] == [x, y]]
                if push_moves:
                    best = max(push_moves, key=lambda mv: manhattan_distance(mv["to"], mv["pushed_to"]))
                    moves.append(best)

        # Move ordering
        moves_to_SA = [m for m in moves if m["action"] == "move" and is_own_score_cell(m["to"][0], m["to"][1], player, rows, cols, score_cols)]
        push_moves = [m for m in moves if m["action"] == "push"]
        others = [m for m in moves if m not in moves_to_SA and m not in push_moves]

        def push_score(mv):
            return -min_manhattan_to_score(mv["pushed_to"][0], mv["pushed_to"][1], get_opponent(player), rows, cols, score_cols)

        push_moves.sort(key=push_score)
        ordered = moves_to_SA + push_moves + others
        return ordered


    def minimax(board, depth, alpha, beta, maximizing_player, player, rows, cols, score_cols, history):
        """Alpha-beta minimax recursive search."""
        if depth == 0:
            return evaluate_board(board, player, rows, cols, score_cols), None

        current_player = player if maximizing_player else get_opponent(player)
        moves = select_actions(board, current_player, rows, cols, score_cols)

        if not moves:
            return evaluate_board(board, player, rows, cols, score_cols), None

        best_move = None

        if maximizing_player:
            max_eval = -math.inf
            for mv in moves:
                success, new_board = simulate_move(board, mv, current_player, rows, cols, score_cols)
                if not success:
                    continue
                eval_val, _ = minimax(new_board, depth - 1, alpha, beta, False, player, rows, cols, score_cols, history + [mv])
                if eval_val > max_eval:
                    max_eval = eval_val
                    best_move = mv
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval, best_move

        else:
            min_eval = math.inf
            for mv in moves:
                success, new_board = simulate_move(board, mv, current_player, rows, cols, score_cols)
                if not success:
                    continue
                eval_val, _ = minimax(new_board, depth - 1, alpha, beta, True, player, rows, cols, score_cols, history + [mv])
                if eval_val < min_eval:
                    min_eval = eval_val
                    best_move = mv
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval, best_move


    def get_minimax_move(board, player, rows, cols, score_cols, history, depth=2):
        """Top-level helper to call minimax and prevent oscillations."""
        val, best_move = minimax(board, depth, -math.inf, math.inf, True, player, rows, cols, score_cols, history)

        if len(history) >= 2 and best_move and history[-2] == best_move:
            # oscillation detected, re-run with 2nd best
            all_moves = select_actions(board, player, rows, cols, score_cols)
            if len(all_moves) > 1:
                best_move = all_moves[1]
        return best_move



# ==================== TESTING HELPERS ====================

def test_student_agent():
    """
    Basic test to verify the student agent can be created and make moves.
    """
    print("Testing StudentAgent...")
    
    try:
        from gameEngine import default_start_board, DEFAULT_ROWS, DEFAULT_COLS
        
        rows, cols = DEFAULT_ROWS, DEFAULT_COLS
        score_cols = score_cols_for(cols)
        board = default_start_board(rows, cols)
        
        agent = StudentAgent("circle")
        move = agent.choose(board, rows, cols, score_cols,1.0,1.0)
        
        if move:
            print("✓ Agent successfully generated a move")
        else:
            print("✗ Agent returned no move")
    
    except ImportError:
        agent = StudentAgent("circle")
        print("✓ StudentAgent created successfully")

if __name__ == "__main__":
    # Run basic test when file is executed directly
    test_student_agent()
