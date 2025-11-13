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
    
    - Generate pre-computed attack moves
    """

    def __init__(self, player: str, edge: str = "right"):
        super().__init__(player)
        self.edge = edge
        self._plan: Optional[List[Dict[str, Any]]] = None
        self._i: int = 0
        self._plan_printed = False

    def choose(
        self,
        board: List[List[Any]],
        rows: int,
        cols: int,
        score_cols: List[int],
        current_player_time: float,
        opponent_time: float,
    ) -> Optional[Dict[str, Any]]:

        if self._plan is None:
            edge = self.edge
            self._plan, total = self.generate_initial_attacking_plan(
                self.player, rows, cols, score_cols, edge=edge
            )
            if not self._plan_printed:
                print(f"[{self.player}] Opening plan (edge={edge}, steps={total}):")
                for i, m in enumerate(self._plan, 1):
                    print(f"{i:02d}. {m}")
                self._plan_printed = True
            self._i = 0

        # play next applicable move from attack-plan; skip stale ones
        while self._plan is not None and self._i < len(self._plan):
            m = self._plan[self._i]
            if self.check_if_move_applicable(board, self.player, m):
                self._i += 1
                return m
            self._i += 1

        # fallback
        moves = generate_all_moves(board, self.player, rows, cols, score_cols)
        if not moves:
            return None
        flips = [m for m in moves if m["action"] == "flip"]
        return random.choice(flips or moves)

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

    # ---------------- Generate opening attack moves ----------------
    @staticmethod
    def generate_initial_attacking_plan(
        player: str, rows: int, cols: int, score_cols: List[int], edge: str = "right"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
         - Single-flank rush with finally flip the rivers to stones for any rivers that enter SA.
         - Mirrors for left/right flanks
        """
        # geometry
        p = cols
        x_anchor = int(cols/2 + p/4 - 1)  # anchor
        right_flank = (edge == "right")
        edge_x = (cols - 1) if right_flank else 0

        # Row layout
        # circle (Bottom Up)
        if player == "circle":
            horiz_row = rows - 4
            vert_row  = rows - 5
            board_edge_row = 0
        else:  # square (Top Down)
            horiz_row = 3
            vert_row  = 4
            board_edge_row = rows - 1

        sa_row = top_score_row() if player == "circle" else bottom_score_row(rows)

        # SA cells (enter scoring area from left->right)
        sa_cols_sorted = sorted(score_cols)
        k = min(len(sa_cols_sorted), 6)
        sa_targets = [(sa_cols_sorted[i], sa_row) for i in range(k)]

        def lane(off_from_anchor_toward_flank: int) -> int:
            return x_anchor + (off_from_anchor_toward_flank * (+1 if right_flank else -1))

        # Three horizontals on the back (horiz_row): D, E, F (closest to flank)
        D = lane(-2)
        E = lane(-1)
        F = lane(0)

        # Two verticals on the upper row (vert_row): V1 above E, V2 above F
        V1 = lane(-1)
        V2 = lane(0)

        # Extra anchor pieces for larger boards
        extra1 = lane(-3)   # when k>=4
        extra2 = lane(+1)   # when k>=6

        moves: List[Dict[str, Any]] = []
        sa_river_to_flip: List[Tuple[int, int]] = []  # store the SA cells that will contain rivers to needs to be flip later

        def flip_h(col: int, row: int):
            moves.append({"action": "flip", "from": [col, row], "orientation": "horizontal"})

        def flip_v(col: int, row: int):
            moves.append({"action": "flip", "from": [col, row], "orientation": "vertical"})

        def rotate_here(xy: Tuple[int, int]):
            moves.append({"action": "rotate", "from": [xy[0], xy[1]]})

        def mv(fr: Tuple[int, int], to: Tuple[int, int]):
            moves.append({"action": "move", "from": [fr[0], fr[1]], "to": [to[0], to[1]]})

        # ---- Phase A: flips ----
        flip_h(D, horiz_row)
        flip_h(E, horiz_row)
        flip_h(F, horiz_row)
        flip_v(V1, vert_row)
        flip_v(V2, vert_row)

        # ---- Phase B: setup river flow on the flank ----
        # V2 -> flank contact on horizontal row
        mv((V2, vert_row), (edge_x, horiz_row))
        # F  -> board edge row (trunk far end)
        mv((F, horiz_row), (edge_x, board_edge_row))
        # V1 -> its own column at the board edge row, then rotate to keep as feeder (not SA yet)
        mv((V1, vert_row), (V1, board_edge_row))
        rotate_here((V1, board_edge_row))

        # ---- Phase C: feed into SA ----
        idx_near_flank = 1 if right_flank else (k - 2)
        if 0 <= idx_near_flank < k:
            tgt = sa_targets[idx_near_flank]
            mv((E, horiz_row), tgt)
            sa_river_to_flip.append(tgt)    # mark for final stone flip

        # inner-most from extra1 (usually stone, doesn't require flip)
        if k >= 4:
            inner_idx = 0 if right_flank else (k - 1)
            mv((extra1, horiz_row), sa_targets[inner_idx])

        from_col = E - 1 if right_flank else E + 1
        if 0 <= from_col < cols:
            far_inner_idx = 0 if right_flank else (k - 1)
            if k >= 5 or far_inner_idx != inner_idx:
                mv((from_col, vert_row), sa_targets[far_inner_idx])

        # nudge D sideways on H-row, then use V-row partner into flankmost SA (stone -> no flip)
        d_step = D - 1 if right_flank else D + 1
        if 0 <= d_step < cols:
            mv((D, horiz_row), (d_step, horiz_row))
        flankmost_idx = (k - 1) if right_flank else 0
        mv((d_step if 0 <= d_step < cols else D, vert_row), sa_targets[flankmost_idx])

        # fill remaining SA with the flank contact (edge_x, horiz_row) -> river => flip,
        # then far edge river (edge_x, board_edge_row) -> river => flip
        remaining = set(sa_targets)
        for m in moves:
            if m["action"] == "move":
                to = tuple(m["to"])
                if to in remaining and to[1] == sa_row:
                    remaining.discard(to)
        remaining = list(remaining)

        if remaining:
            tgt_trunk = sorted(remaining, key=lambda t: (abs(t[0] - edge_x), abs(t[0] - x_anchor)))[0]
            mv((edge_x, horiz_row), tgt_trunk)    # source is V2 river at flank contact
            sa_river_to_flip.append(tgt_trunk)    # flip later to stone
            remaining.remove(tgt_trunk)

        if remaining:
            tgt_far = sorted(remaining, key=lambda t: abs(t[0] - edge_x))[0]
            mv((edge_x, board_edge_row), tgt_far)
            sa_river_to_flip.append(tgt_far)
            remaining.remove(tgt_far)

        if k >= 6 and remaining:
            mv((extra2, horiz_row), remaining[0])
            remaining.pop(0)

        # ---- Phase D: FINALIZE — flip any rivers that entered SA to STONE ----
        for (fx, fy) in sa_river_to_flip:
            moves.append({"action": "flip", "from": [fx, fy]})

        return moves, len(moves)

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
