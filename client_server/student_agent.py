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
import math

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

def is_opponent_score_area(x: int, y: int, player: str, rows: int, cols: int) -> bool:
    """Check if a cell is in the opponent's scoring area."""
    score_cols = score_cols_for(cols)
    if player == "circle":
        return (y == get_bottom_score_row(rows)) and (x in score_cols)
    else:
        return (y == get_top_score_row()) and (x in score_cols)

def is_own_score_area(x: int, y: int, player: str, rows: int, cols: int) -> bool:
    """Check if a cell is in the player's own scoring area."""
    score_cols = score_cols_for(cols)
    if player == "circle":
        return (y == get_top_score_row()) and (x in score_cols)
    else:
        return (y == get_bottom_score_row(rows)) and (x in score_cols)

def get_top_score_row() -> int:
    """Get the row index for Circle's scoring area (top)."""
    return 2

def get_bottom_score_row(rows: int) -> int:
    """Get the row index for Square's scoring area (bottom)."""
    return rows - 3

# ---------- helpers for "home SA" and guard row (outside SA) ----------
def home_sa_row(player: str, rows: int) -> int:
    """
    Player's OWN scoring area row (the goal they defend).
    - Square defends TOP SA.
    - Circle defends BOTTOM SA.
    """
    return top_score_row() if player == "square" else bottom_score_row(rows)

def my_scoring_row(player: str, rows: int) -> int:
    """
    The row where *I* must score (i.e., opponent's SA).
    circle scores at bottom; square scores at top.
    """
    return top_score_row() if player == "circle" else bottom_score_row(rows)

def guard_row_outside(player: str, rows: int) -> int:
    """
    Row where horizontal guards sit: ONE CELL OUTSIDE (away from the center/opponent)
    of the player's OWN scoring area.
    - If top SA -> guard row = SA - 1
    - If bottom SA -> guard row = SA + 1
    """
    sa = home_sa_row(player, rows)
    if sa == top_score_row():
        return sa - 1  # just above the top SA
    else:
        return sa + 1  # just below the bottom SA

# ==================== MOVE GENERATION HELPERS ====================

def get_river_flow_path(board, start_x, start_y, player, rows, cols, came_x, came_y):
    destinations = []
    visited = set()
    
    def explore_from_river(river_x, river_y, came_from):
        if (river_x, river_y) in visited:
            return
        visited.add((river_x, river_y))
        
        river_piece = board[river_y][river_x]
        if not river_piece or river_piece.side != "river":
            return
            
        if river_piece.orientation == "horizontal":
            directions = [(1, 0), (-1, 0)]
            next_x_1, next_y_1 = river_x + 0, river_y + 1
            next_x_2, next_y_2 = river_x + 0, river_y + -1
            if in_bounds(next_x_1, next_y_1, rows, cols) and not is_opponent_score_area(next_x_1, next_y_1, player, rows, cols):
                piece = board[next_y_1][next_x_1]
                if piece and piece.side == "river" and piece.orientation == "vertical":
                        directions.append((0, 1))  # Fixed: use append instead of extend for single element
            if in_bounds(next_x_2, next_y_2, rows, cols) and not is_opponent_score_area(next_x_2, next_y_2, player, rows, cols):
                piece = board[next_y_2][next_x_2]
                if piece and piece.side == "river" and piece.orientation == "vertical":
                        directions.append((0, -1))  # Fixed: use append instead of extend
        else:
            directions = [(0, 1), (0, -1)]
            next_x_1, next_y_1 = river_x + 1, river_y + 0
            next_x_2, next_y_2 = river_x + -1, river_y + 0
            if in_bounds(next_x_1, next_y_1, rows, cols) and not is_opponent_score_area(next_x_1, next_y_1, player, rows, cols):
                piece = board[next_y_1][next_x_1]
                if piece and piece.side == "river" and piece.orientation == "horizontal":  # Fixed: should be horizontal, not vertical
                        directions.append((1, 0))
            if in_bounds(next_x_2, next_y_2, rows, cols) and not is_opponent_score_area(next_x_2, next_y_2, player, rows, cols):
                piece = board[next_y_2][next_x_2]
                if piece and piece.side == "river" and piece.orientation == "horizontal":  # Fixed: should be horizontal, not vertical
                        directions.append((-1, 0))
            
        for dx, dy in directions:
            next_x, next_y = river_x + dx, river_y + dy
            
            # CRITICAL: Don't go back where we came from
            if (next_x, next_y) == came_from:
                continue
                
            while in_bounds(next_x, next_y, rows, cols) and (next_x, next_y) not in visited:
                
                if is_opponent_score_area(next_x, next_y, player, rows, cols):
                    break
                    
                cell = board[next_y][next_x]
                if next_y == came_y and next_x == came_x:
                    cell = None
                
                if cell is None:
                    visited.add((next_x, next_y))
                elif cell.side == "stone":
                    visited.add((next_x, next_y))
                
                if cell is None:
                    destinations.append((next_x, next_y))
                    next_x += dx
                    next_y += dy
                    continue
                    
                if cell.side == "stone":
                    break
                    
                if cell.side == "river":
                    explore_from_river(next_x, next_y, (river_x, river_y))
                    break
                    
                break
    
    explore_from_river(start_x, start_y, (-1, -1))  # Start with no previous position
    return destinations

def get_stone_push_targets(board: List[List[Any]], push_x: int, push_y: int, 
                          push_dx: int, push_dy: int, player: str, rows: int, cols: int) -> List[Tuple[int, int]]:
    """
    Get valid push targets for stone pushing.
    Stone can push exactly one space in the same direction.
    """
    targets = []
    
    # Calculate push destination
    dest_x, dest_y = push_x + push_dx, push_y + push_dy
    
    # Check if push is valid
    if (in_bounds(dest_x, dest_y, rows, cols) and
        board[dest_y][dest_x] is None and
        not is_opponent_score_area(dest_x, dest_y, player, rows, cols)):
        targets.append((dest_x, dest_y))
    
    return targets

def get_river_push_targets(board: List[List[Any]], push_x: int, push_y: int,
                          pusher_x: int, pusher_y: int, player: str, rows: int, cols: int) -> List[Tuple[int, int]]:
    """
    Get valid push targets for river pushing.
    River can push any distance along its flow direction.
    IMPORTANT: Rivers can only push STONES, not other rivers.
    """
    targets = []
    
    # Get the piece being pushed - MUST BE A STONE
    pushed_piece = board[push_y][push_x]
    if not pushed_piece or pushed_piece.side != "stone":
        return targets  # Only stones can be pushed by rivers
    
    # Get the pushing river piece
    river_piece = board[pusher_y][pusher_x]
    if not river_piece or river_piece.side != "river":
        return targets
    
    # Determine push direction based on river orientation
    if river_piece.orientation == "horizontal":
        # Can push left or right
        directions = [(1, 0), (-1, 0)]
    else:  # vertical
        # Can push up or down
        directions = [(0, 1), (0, -1)]
    
    for dx, dy in directions:
        current_x, current_y = push_x + dx, push_y + dy
        
        while in_bounds(current_x, current_y, rows, cols):
            # Stop if entering opponent's scoring area for the pushed piece
            if is_opponent_score_area(current_x, current_y, pushed_piece.owner, rows, cols):
                break
                
            # If cell is empty, valid push destination
            if board[current_y][current_x] is None:
                targets.append((current_x, current_y))
                current_x += dx
                current_y += dy
            else:
                # Hit another piece - stop
                break
    
    return targets

def generate_regular_moves(board: List[List[Any]], piece_x: int, piece_y: int,
                          player: str, rows: int, cols: int) -> List[Dict[str, Any]]:
    """Generate all regular movement moves for a piece."""
    moves = []
    piece = board[piece_y][piece_x]
    if not piece:
        return moves
    
    # Check all adjacent cells
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        target_x, target_y = piece_x + dx, piece_y + dy
        
        if not in_bounds(target_x, target_y, rows, cols):
            continue
            
        # Cannot move into opponent's scoring area
        if is_opponent_score_area(target_x, target_y, player, rows, cols):
            continue
            
        target_cell = board[target_y][target_x]
        
        if target_cell is None:
            # Empty cell - regular 1-step move
            moves.append({
                "action": "move",
                "from": [piece_x, piece_y],
                "to": [target_x, target_y]
            })
        elif target_cell.side == "river":
            # River movement - can slide along ANY adjacent river
            river_destinations = get_river_flow_path(board, target_x, target_y, player, rows, cols, piece_x, piece_y)
            for dest_x, dest_y in river_destinations:
                # Include the destination even if it's multiple spaces away
                moves.append({
                    "action": "move", 
                    "from": [piece_x, piece_y],
                    "to": [dest_x, dest_y]
                })
    print(moves)
    return moves

def generate_push_moves(board: List[List[Any]], piece_x: int, piece_y: int,
                       player: str, rows: int, cols: int) -> List[Dict[str, Any]]:
    """Generate all push moves for a piece."""
    pushes = []
    piece = board[piece_y][piece_x]
    if not piece:
        return pushes
    
    # Check all adjacent cells for pieces to push
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        push_x, push_y = piece_x + dx, piece_y + dy
        
        if not in_bounds(push_x, push_y, rows, cols):
            continue
            
        target_piece = board[push_y][push_x]
        if not target_piece:
            continue
            
        # Stone pushing (can push any piece type)
        if piece.side == "stone":
            push_targets = get_stone_push_targets(board, push_x, push_y, dx, dy, 
                                                 target_piece.owner, rows, cols)
            for target_x, target_y in push_targets:
                pushes.append({
                    "action": "push",
                    "from": [piece_x, piece_y],
                    "to": [push_x, push_y],
                    "pushed_to": [target_x, target_y]
                })
        
        # River pushing - can only push STONES
        elif piece.side == "river" and target_piece.side == "stone":
            push_targets = get_river_push_targets(board, push_x, push_y, piece_x, piece_y,
                                                 player, rows, cols)
            for target_x, target_y in push_targets:
                pushes.append({
                    "action": "push",
                    "from": [piece_x, piece_y],
                    "to": [push_x, push_y],
                    "pushed_to": [target_x, target_y]
                })
    
    return pushes

def generate_flip_moves(board: List[List[Any]], piece_x: int, piece_y: int) -> List[Dict[str, Any]]:
    """Generate all flip moves for a piece."""
    flips = []
    piece = board[piece_y][piece_x]
    if not piece:
        return flips
    
    if piece.side == "stone":
        # Stone can flip to river with either orientation
        for orientation in ["horizontal", "vertical"]:
            flips.append({
                "action": "flip",
                "from": [piece_x, piece_y],
                "orientation": orientation
            })
    else:  # river
        # River can flip to stone (no orientation needed)
        flips.append({
            "action": "flip",
            "from": [piece_x, piece_y]
        })
    
    return flips

def generate_rotate_moves(board: List[List[Any]], piece_x: int, piece_y: int) -> List[Dict[str, Any]]:
    """Generate rotate moves for a river piece."""
    rotates = []
    piece = board[piece_y][piece_x]
    
    if piece and piece.side == "river":
        rotates.append({
            "action": "rotate",
            "from": [piece_x, piece_y]
        })
    
    return rotates

def generate_moves_for_piece(board: List[List[Any]], piece_x: int, piece_y: int,
                            player: str, rows: int, cols: int) -> List[Dict[str, Any]]:
    """Generate all valid moves for a specific piece."""
    piece = board[piece_y][piece_x]
    if not piece or piece.owner != player:
        return []
    
    all_moves = []
    
    # Generate different types of moves
    all_moves.extend(generate_regular_moves(board, piece_x, piece_y, player, rows, cols))
    all_moves.extend(generate_push_moves(board, piece_x, piece_y, player, rows, cols))
    all_moves.extend(generate_flip_moves(board, piece_x, piece_y))
    all_moves.extend(generate_rotate_moves(board, piece_x, piece_y))
    
    return all_moves

def generate_all_valid_moves(board: List[List[Any]], player: str, rows: int, cols: int) -> List[Dict[str, Any]]:
    """
    Generate ALL valid moves for the current player on the given board.
    """
    all_moves = []
    
    # Iterate through all board positions
    for y in range(rows):
        for x in range(cols):
            piece_moves = generate_moves_for_piece(board, x, y, player, rows, cols)
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
        self._def_setup_done = False
        self._def_setup_plan = []
        self._def_setup_idx = 0
        self._atk_plan = None
        self._atk_idx = 0
        self._atk_printed = False
        self.defense = None
        self.restore_queue = deque() 
        self.move_history = []
        self.total_moves = 0

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

        # helper to both return and count the move
        def _return(m):
            if m is not None:
                self.total_moves += 1
            return m

        # 0B) ABSOLUTE HIGHEST PRIORITY when move count is large
        # Flip any of *my* rivers already sitting in opponent SA to stones.
        if self.total_moves >= 490:
            m = self.endgame_force_flip_in_opp_sa(board, rows, cols, score_cols)
            if m:
                return _return(m)

        # 0A) HIGHEST PRIORITY: if opponent SA is fully occupied by *my* pieces,
        # flip the first river-side-up to a stone to lock the point.
        m = self.finish_scoring_if_full(board, rows, cols, score_cols)
        if m:
            return _return(m)

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
                self._def_setup_plan = self.get_initial_defense_moves(rows, cols)
                self._def_setup_idx = 0

            if self._def_setup_idx < len(self._def_setup_plan):
                m = self._def_setup_plan[self._def_setup_idx]
                if self.check_if_move_applicable(board, self.player, m, rows, cols):
                    self._def_setup_idx += 1
                    return _return(m)

            self._def_setup_done = True

        # 2) HIGH PRIORITY: REACTIVE DEFENSE
        dm = self.get_defensive_move(board, rows, cols, score_cols)
        if dm:
            return _return(dm)

        # 3) PREDEFINED ATTACK SCRIPT
        if self._def_setup_done:
            if self._atk_plan is None:
                if hasattr(self, "get_initial_attack_moves"):
                    self._atk_plan = self.get_initial_attack_moves(rows, cols)
                else:
                    self._atk_plan = []
                self._atk_idx = 0
                self._atk_printed = True

            if self._atk_plan and self._atk_idx < len(self._atk_plan):
                am = self._atk_plan[self._atk_idx]
                if self.check_if_move_applicable(board, self.player, am, rows, cols):
                    self._atk_idx += 1
                    return _return(am)
                # else:
                #     print("Attack Move Not possible, invoking minimax =", am)

        # 4) Fallback: minimax else random
        best_move = get_minimax_move(board, self.player, rows, cols, score_cols, self.move_history)
        if best_move:
            self.move_history.append(best_move)
            return _return(best_move)

        all_moves = generate_all_valid_moves(board, self.player, rows, cols)
        if all_moves:
            return _return(random.choice(all_moves))
        return None

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
    def check_if_move_applicable(board, player: str, move: Dict[str, Any], rows, cols) -> bool:
        score_cols = score_cols_for(cols)
        all_moves = generate_all_valid_moves(board, player, rows, cols)
        if move in all_moves: 
            return True
        return False


    # ---------- layout: two horizontal guard cells outside our SA ----------
    def init_defense_layout(self, board, rows, cols, score_cols):
        """
        Place/track two horizontal guard cells ONE ROW OUTSIDE our OWN SA.
        - Square defends TOP SA (guards on row = top SA - 1)
        - Circle defends BOTTOM SA (guards on row = bottom SA + 1)
        - Choose the inner pair of SA columns when possible (len>=4),
        otherwise best available.
        """
        sa_row = home_sa_row(self.player, rows)
        guard_row = guard_row_outside(self.player, rows)
        sa_cols_sorted = sorted(score_cols)

        # Choose guard columns:
        if len(sa_cols_sorted) >= 4:
            # Inner pair (middle two) defend best for 4+ width SAs
            guard_cols = [sa_cols_sorted[1], sa_cols_sorted[-2]]
        elif len(sa_cols_sorted) == 3:
            # One central; duplicate to try to keep two guards if both spots get used
            guard_cols = [sa_cols_sorted[1], sa_cols_sorted[1]]
        elif len(sa_cols_sorted) == 2:
            guard_cols = [sa_cols_sorted[0], sa_cols_sorted[1]]
        elif len(sa_cols_sorted) == 1:
            guard_cols = [sa_cols_sorted[0], sa_cols_sorted[0]]
        else:
            guard_cols = []

        horiz_guards = [(c, guard_row) for c in guard_cols if 0 <= c < cols and 0 <= guard_row < rows]

        self.defense = {
            "sa_row": sa_row,                    # our OWN SA row (goal to defend)
            "guard_row": guard_row,              # row just outside SA
            "horiz_guards": horiz_guards,        # expected horizontal rivers
        }
        if not hasattr(self, "restore_queue"):
            self.restore_queue = deque()

        # print(f"[DEF:init] me={self.player} sa_row={sa_row} guard_row={guard_row} sa_cols={sa_cols_sorted} guards={horiz_guards}")


    # ---------- simple adjacent-push defense with queued restore ----------
    def get_defensive_move(self, board, rows, cols, score_cols):
        """
        Defensive logic (robust to guards moving from home):

        • Square defends TOP SA:    guard_row = top_SA_row - 1
        • Circle defends BOTTOM SA: guard_row = bottom_SA_row + 1

        Homes (for 4-wide SA): (sa_cols[0], guard_row) and (sa_cols[-2], guard_row)
        We *track homes*, but every turn we *scan the guard_row* over all SA columns
        to find our *current guard positions* (wherever they currently are).

        Priority:
        1) Execute queued restore if applicable (else don't pop; return None).
        2) Ensure current guards we own are horizontal rivers (flip if needed).
        3) If adjacent (left/right) IN SA COLUMNS there is an OPPONENT **STONE**,
            push it horizontally as far as possible, then queue flip-back + move-back to home.
        4) If on the row just *between SA and guards* there’s any OPPONENT **RIVER**
            in a scoring column, move the *nearest current guard* to that column (if free).
        """
        # ---------- layout & constants ----------
        if self.defense is None:
            self.init_defense_layout(board, rows, cols, score_cols)

        me  = self.player
        opp = get_opponent(me)

        # SA rows by side (remember: each side defends ITS OWN SA)
        sa_row = top_score_row() if me == "square" else bottom_score_row(rows)
        guard_row = sa_row - 1 if me == "square" else sa_row + 1

        sa_cols_sorted = sorted(score_cols)
        sa_cols_set = set(sa_cols_sorted)

        # define *home* columns (as you requested)
        if len(sa_cols_sorted) >= 4:
            guard_homes = [(sa_cols_sorted[0], guard_row), (sa_cols_sorted[-2], guard_row)]
        elif len(sa_cols_sorted) >= 2:
            guard_homes = [(sa_cols_sorted[0], guard_row), (sa_cols_sorted[-1], guard_row)]
        else:
            guard_homes = [(sa_cols_sorted[0], guard_row)]

        # stash in defense for reference/prints
        self.defense["sa_row"] = sa_row
        self.defense["guard_row"] = guard_row
        self.defense["guard_homes"] = guard_homes

        # print(f"[DEF] me={me} sa_row={sa_row} guard_row={guard_row} sa_cols={sa_cols_sorted} homes={guard_homes}")

        # ---------- helpers ----------
        def inb(x, y): 
            return 0 <= x < cols and 0 <= y < rows

        def ok_push_dest(x, y, pushed_owner):
            if not inb(x, y): return False
            if board[y][x] is not None: return False
            return not is_opponent_score_cell(x, y, pushed_owner, rows, cols, score_cols)

        def is_applicable(move):
            if hasattr(self, "check_if_move_applicable"):
                return self.check_if_move_applicable(board, me, move, rows, cols)
            fr = move.get("from")
            if not fr: return True
            fx, fy = fr
            return inb(fx, fy) and board[fy][fx] is not None and getattr(board[fy][fx], "owner", None) == me

        def nearest_home(x_now):
            # choose the home with minimum |x_now - home_x|
            hx, hy = min(guard_homes, key=lambda h: abs(h[0] - x_now))
            return hx, hy

        def queue_restore(cur_x, cur_y):
            # after push our guard is a STONE at (cur_x,cur_y). Flip back to horizontal river, then go home.
            self.restore_queue.append({"action": "flip", "from": [cur_x, cur_y], "orientation": "horizontal"})
            hx, hy = nearest_home(cur_x)
            if (cur_x, cur_y) != (hx, hy):
                self.restore_queue.append({"action": "move", "from": [cur_x, cur_y], "to": [hx, hy]})
            # print(f"[DEF] queued restore: flip@{(cur_x,cur_y)} → move→{(hx,hy)}")

        # ---------- if there is any todo left in the queue make those moves ----------
        if self.restore_queue:
            nxt = self.restore_queue[0]
            if is_applicable(nxt):
                # print("[DEF] executing queued restore:", nxt)
                return self.restore_queue.popleft()
            else:
                # print("[DEF] queued restore NOT applicable yet; keep queued:", nxt)
                return None

        # ---------- find all the guards positions ----------
        current_guards = []
        if 0 <= guard_row < rows:
            for cx in sa_cols_sorted:
                p = board[guard_row][cx]
                dbg = "none" if p is None else f"{p.owner}:{p.side}:{getattr(p,'orientation',None)}"
                # print(f"[DEF] scan guard_row cell {(cx,guard_row)} -> {dbg}")
                if p and p.owner == me:
                    # This is one of "our guards" (could be temporarily a stone after push)
                    current_guards.append((cx, guard_row))

        # print(f"[DEF] current_guards={current_guards}")

        # ---------- IF any guards are not in horizontaal orientation rotate them ----------
        for (gx, gy) in current_guards:
            p = board[gy][gx]
            if p and (p.side != "river" or p.orientation != "horizontal"):
                # print("[DEF] flipping current guard to horizontal river at", (gx, gy))
                return {"action": "flip", "from": [gx, gy], "orientation": "horizontal"}

        # ---------- Push away the stones ----------
        for (gx, gy) in current_guards:
            p = board[gy][gx]
            if not (p and p.owner == me and p.side == "river" and p.orientation == "horizontal"):
                # can only push from a horizontal river; otherwise flip stage will handle above
                continue

            for dx in (-1, 1):
                nx, ny = gx + dx, gy
                if nx not in sa_cols_set:
                    continue  # protect only SA columns
                if not inb(nx, ny):
                    continue
                t = board[ny][nx]
                if not (t and t.owner == opp and t.side == "stone"):
                    continue  # push is only for stones

                # print(f"[DEF] intruding OPP STONE at {(nx,ny)} — pushing dx={dx}")

                # farthest legal destination along dx
                px, py = nx + dx, ny
                last_ok = None
                while inb(px, py) and ok_push_dest(px, py, t.owner):
                    last_ok = (px, py)
                    px += dx
                if last_ok is None:
                    px, py = nx + dx, ny
                    if not ok_push_dest(px, py, t.owner):
                        # print("[DEF] no legal destination to push; skip")
                        continue
                    pushed_to = (px, py)
                else:
                    pushed_to = last_ok

                push_move = {
                    "action": "push",
                    "from": [gx, gy],
                    "to": [nx, ny],
                    "pushed_to": [pushed_to[0], pushed_to[1]],
                }
                # print("[DEF] issuing PUSH:", push_move)
                # after push, our river becomes a stone at (nx,ny) → queue restore back to nearest home
                queue_restore(nx, ny)
                return push_move

        # ---------- If opponent river has entered from behind shift nearest guard to that column ----------
        scan_row = guard_row - 1  # row between SA and guards
        if 0 <= scan_row < rows and current_guards:
            threat_cols = []
            for cx in sa_cols_sorted:
                t = board[scan_row][cx]
                if t and t.owner == opp and t.side == "river":
                    threat_cols.append(cx)

            if threat_cols:
                # choose the nearest current guard to each threatened column (first viable move wins)
                for cx in threat_cols:
                    # pick nearest guard (by x-distance)
                    g = min(current_guards, key=lambda gpos: abs(gpos[0] - cx))
                    gx, gy = g
                    # only move if destination free
                    if board[guard_row][cx] is None:
                        mv = {"action": "move", "from": [gx, gy], "to": [cx, guard_row]}
                        # print(f"[DEF] river seen at {(cx,scan_row)} → shift guard {g} → {(cx,guard_row)}")
                        return mv
                    # else:
                        # print(f"[DEF] wanted to shift to {(cx,guard_row)} but occupied; skipping")

        # print("[DEF] no defensive action")
        return None
    
    # ---------- PRIORITY 0A: if all cells in opponent SA are mine, flip first river to stone ----------
    def finish_scoring_if_full(self, board, rows, cols, score_cols) -> Optional[Dict[str, Any]]:
        opp_sa_row = my_scoring_row(self.player, rows)

        # Check that each scoring column on opponent SA is occupied by MY piece
        for x in score_cols:
            if not in_bounds(x, opp_sa_row, rows, cols):
                return None  # board malformed
            cell = board[opp_sa_row][x]
            if not cell or getattr(cell, "owner", None) != self.player:
                return None  # not fully filled by me

        # All filled by me → flip the first river-side-up to stone
        for x in score_cols:
            cell = board[opp_sa_row][x]
            if getattr(cell, "side", "") == "river":
                # flip to stone (no orientation field needed)
                return {"action": "flip", "from": [x, opp_sa_row]}
        return None  # already all stones

    # ---------- PRIORITY 0B (highest when triggered): after many moves, flip any of my rivers in opp SA ----------
    def endgame_force_flip_in_opp_sa(self, board, rows, cols, score_cols) -> Optional[Dict[str, Any]]:
        opp_sa_row = my_scoring_row(self.player, rows)
        for x in score_cols:
            if not in_bounds(x, opp_sa_row, rows, cols):
                continue
            cell = board[opp_sa_row][x]
            if cell and getattr(cell, "owner", None) == self.player and getattr(cell, "side", "") == "river":
                return {"action": "flip", "from": [x, opp_sa_row]}
        return None


# ==================== MINIMAX IMPLEMENTATION ====================

def manhattan_distance(a, b):
    """Calculate Manhattan distance between two points."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def min_manhattan_to_score(x, y, player, rows, cols, score_cols):
    """Get min distance from (x,y) to that player's scoring area."""
    if player == "circle":
        score_y = top_score_row()
    else:
        score_y = bottom_score_row(rows)
    return min(abs(y - score_y) + abs(x - sc) for sc in score_cols)

def minimax_evaluate_board(board, player, rows, cols, score_cols):
    """Full evaluation function as per specification."""
    opponent = get_opponent(player)
    score = 0

    # Pieces in scoring area
    player_scoring_stones = count_stones_in_scoring_area(board, player, rows, cols, score_cols)
    opponent_scoring_stones = count_stones_in_scoring_area(board, opponent, rows, cols, score_cols)
    
    score += player_scoring_stones * 1000
    score -= opponent_scoring_stones * 1000

    # Proximity counts
    my_close, opp_close = 0, 0
    my_to_opp, opp_to_me = 0, 0
    
    for y in range(rows):
        for x in range(cols):
            piece = board[y][x]
            if not piece:
                continue
                
            if piece.owner == player:
                d_own = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                d_opp = min_manhattan_to_score(x, y, opponent, rows, cols, score_cols)
                if d_own <= 2: 
                    my_close += 1
                if d_opp <= 2: 
                    my_to_opp += 1
            else:
                d_opp = min_manhattan_to_score(x, y, opponent, rows, cols, score_cols)
                d_me = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                if d_opp <= 2: 
                    opp_close += 1
                if d_me <= 2: 
                    opp_to_me += 1

    score += my_close * 500
    score -= opp_close * 500
    score += my_to_opp * 50
    score -= opp_to_me * 50

    return score

def selective_action_generation(board, player, rows, cols, score_cols):
    """Selective action generator as per the strategy document."""
    moves = []
    all_moves = generate_all_valid_moves(board, player, rows, cols)
    opponent = get_opponent(player)

    for move in all_moves:
        from_pos = move.get("from")
        if not from_pos:
            continue
        x, y = from_pos

        # Region restrictions - handle deterministically
        if player == "circle" and y >= rows - 2:
            continue
        if player == "square" and y <= 2:
            continue

        # Skip if piece is in own score area
        if is_own_score_cell(x, y, player, rows, cols, score_cols):
            continue

        piece = board[y][x]
        if not piece or piece.owner != player:
            continue

        # ---- Stone pieces ----
        if piece.side == "stone":
            # Find moves that go directly to score area
            sa_moves = [m for m in all_moves 
                    if m["action"] == "move" and m["from"] == [x, y] 
                    and is_own_score_cell(m["to"][0], m["to"][1], player, rows, cols, score_cols)]
            
            if sa_moves:
                chosen = random.choice(sa_moves)
                moves.append(chosen)
                # Add flip to horizontal after moving to score area
                moves.append({
                    "action": "flip", 
                    "from": chosen["to"], 
                    "orientation": "horizontal"
                })
            else:
                # No direct score moves - flip to horizontal river
                moves.append({
                    "action": "flip", 
                    "from": [x, y], 
                    "orientation": "horizontal"
                })

        # ---- Vertical river pieces ----
        elif piece.side == "river" and piece.orientation == "vertical":
            # Find moves that go directly to score area
            sa_moves = [m for m in all_moves 
                    if m["action"] == "move" and m["from"] == [x, y] 
                    and is_own_score_cell(m["to"][0], m["to"][1], player, rows, cols, score_cols)]
            
            if sa_moves:
                chosen = random.choice(sa_moves)
                moves.append(chosen)
                # Add rotate after moving to score area
                moves.append({
                    "action": "rotate", 
                    "from": chosen["to"]
                })
            else:
                # No direct score moves - rotate to horizontal
                moves.append({
                    "action": "rotate", 
                    "from": [x, y]
                })

        # ---- Horizontal river pieces ----
        elif piece.side == "river" and piece.orientation == "horizontal":
            # Find moves that go directly to score area
            sa_moves = [m for m in all_moves 
                    if m["action"] == "move" and m["from"] == [x, y] 
                    and is_own_score_cell(m["to"][0], m["to"][1], player, rows, cols, score_cols)]
            
            if sa_moves:
                moves.extend(sa_moves)
            else:
                # Distance-based filtering for other moves
                filtered = []
                for m in all_moves:
                    if m["from"] != [x, y] or m["action"] != "move":
                        continue
                    
                    from_d = min_manhattan_to_score(x, y, player, rows, cols, score_cols)
                    to_d = min_manhattan_to_score(m["to"][0], m["to"][1], player, rows, cols, score_cols)
                    delta = to_d - from_d
                    
                    if delta < 0:
                        # Distance decreased
                        filtered.append((m, abs(delta)))
                    elif delta <= 2:
                        # Small distance increase
                        filtered.append((m, 0))
                
                if filtered:
                    # Sort by distance decrease (best first)
                    filtered.sort(key=lambda t: (-t[1]))
                    # Take top 2 moves
                    top_moves = [mv for mv, _ in filtered[:2]]
                    moves.extend(top_moves)

            # Push moves - only the one that pushes opponent farthest
            push_moves = [m for m in all_moves 
                        if m["action"] == "push" and m["from"] == [x, y]]
            
            if push_moves:
                # Find push that creates greatest distance between push start and end
                best_push = max(push_moves, 
                            key=lambda m: manhattan_distance(m["to"], m["pushed_to"]))
                moves.append(best_push)

    # Move ordering
    moves_to_SA = [m for m in moves 
                if m["action"] == "move" 
                and is_own_score_cell(m["to"][0], m["to"][1], player, rows, cols, score_cols)]
    
    push_moves = [m for m in moves if m["action"] == "push"]
    other_moves = [m for m in moves if m not in moves_to_SA and m not in push_moves]

    # Sort push moves by how close they push opponent to their score area
    def push_score(move):
        return -min_manhattan_to_score(
            move["pushed_to"][0], move["pushed_to"][1], 
            opponent, rows, cols, score_cols
        )
    
    push_moves.sort(key=push_score)
    
    # Final ordered list
    ordered_moves = moves_to_SA + push_moves + other_moves
    return ordered_moves

def minimax_search(board, depth, alpha, beta, maximizing_player, player, rows, cols, score_cols, history):
    """Alpha-beta minimax recursive search."""
    if depth == 0:
        return minimax_evaluate_board(board, player, rows, cols, score_cols), None

    current_player = player if maximizing_player else get_opponent(player)
    moves = selective_action_generation(board, current_player, rows, cols, score_cols)

    if not moves:
        return minimax_evaluate_board(board, player, rows, cols, score_cols), None

    best_move = None

    if maximizing_player:
        max_eval = -math.inf
        for move in moves:
            success, new_board = simulate_move(board, move, current_player, rows, cols, score_cols)
            if not success:
                continue
                
            eval_val, _ = minimax_search(
                new_board, depth - 1, alpha, beta, False, 
                player, rows, cols, score_cols, history + [move]
            )
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
                
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
                
        return max_eval, best_move

    else:
        min_eval = math.inf
        for move in moves:
            success, new_board = simulate_move(board, move, current_player, rows, cols, score_cols)
            if not success:
                continue
                
            eval_val, _ = minimax_search(
                new_board, depth - 1, alpha, beta, True, 
                player, rows, cols, score_cols, history + [move]
            )
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
                
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
                
        return min_eval, best_move

def get_minimax_move(board, player, rows, cols, score_cols, history, depth=2):
    """Top-level helper to call minimax and prevent oscillations."""
    # Import math if not already imported
    import math
    
    eval_val, best_move = minimax_search(
        board, depth, -math.inf, math.inf, True, 
        player, rows, cols, score_cols, history
    )

    # Prevent oscillation: if best_move is same as two moves ago, use second best
    if len(history) >= 2 and best_move and history[-2] == best_move:
        all_moves = selective_action_generation(board, player, rows, cols, score_cols)
        if len(all_moves) > 1:
            # Find second best move
            second_best_score = -math.inf
            second_best_move = None
            
            for move in all_moves:
                if move == best_move:
                    continue
                    
                success, new_board = simulate_move(board, move, player, rows, cols, score_cols)
                if not success:
                    continue
                    
                move_score = minimax_evaluate_board(new_board, player, rows, cols, score_cols)
                if move_score > second_best_score:
                    second_best_score = move_score
                    second_best_move = move
            
            if second_best_move:
                best_move = second_best_move

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
