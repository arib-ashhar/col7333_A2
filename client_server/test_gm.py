# test_gm.py
# Visualizes all legal moves for each piece of `my_side` on a randomized board.
# Uses generate_moves.generate_all_possible_moves (with river riding).
# Usage: python python_files/test_gm.py circle | python python_files/test_gm.py square

import os, sys
import random
from typing import List, Dict, Any, Tuple, Optional

# --- PATHS: allow running from project root ---
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "client_server"))

# --- Engine & move generator imports ---
import gameEngine as eng
from gameEngine import Piece, draw_board, score_cols_for
from generate_moves import generate_all_possible_moves  # <-- use the rich generator

try:
    import pygame
except Exception:
    pygame = None


ROWS = 13
COLS = 12


def make_random_start_board(rows: int, cols: int) -> List[List[Optional[Piece]]]:
    """
    Matches your default piece placement bands but randomizes side/orientation.
    - 'square' pieces on rows 3,4
    - 'circle' pieces on rows rows-5, rows-4
    - columns are centered (same as default_start_board)
    - each piece is randomly stone OR river; if river, orientation is random H/V
    Returns a board of Piece objects for drawing.
    """
    width = min(6, max(2, cols - 6))
    start_cols = list(range((cols - width) // 2, (cols - width) // 2 + width))
    top_rows = [3, 4]
    bot_rows = [rows - 5, rows - 4]

    board: List[List[Optional[Piece]]] = [[None for _ in range(cols)] for _ in range(rows)]

    def rnd_piece(owner: str) -> Piece:
        if random.random() < 0.5:
            return Piece(owner=owner, side="stone", orientation="horizontal")
        else:
            return Piece(owner=owner, side="river", orientation=random.choice(["horizontal", "vertical"]))

    for r in top_rows:
        for c in start_cols:
            board[r][c] = rnd_piece("square")
    for r in bot_rows:
        for c in start_cols:
            board[r][c] = rnd_piece("circle")

    return board


def piece_board_to_dict_board(board: List[List[Optional[Piece]]]) -> List[List[Dict[str, str]]]:
    """Convert Piece objects to the dict schema expected by generate_all_possible_moves."""
    out: List[List[Dict[str, str]]] = []
    for y in range(len(board)):
        row: List[Dict[str, str]] = []
        for x in range(len(board[0])):
            p = board[y][x]
            if not p:
                row.append({})
            else:
                row.append({"owner": p.owner, "side": p.side, "orientation": p.orientation})
        out.append(row)
    return out


def build_move_highlights_by_piece(
    all_moves: List[Dict[str, Any]]
) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """
    Groups legal destinations by the origin piece coordinate.
    - 'move'  -> highlight 'to'
    - 'push'  -> highlight the landing of the pushed piece ('pushed_to')
    - 'flip' / 'rotate' -> not highlighted (listed in right pane instead)
    """
    highlights: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for m in all_moves:
        fx, fy = m["from"]
        key = (fx, fy)
        act = m.get("action", "")
        if act == "move" and "to" in m:
            tx, ty = m["to"]
            highlights.setdefault(key, []).append((tx, ty))
        elif act == "push" and m.get("pushed_to"):
            px, py = m["pushed_to"]
            highlights.setdefault(key, []).append((px, py))
    # de-dup
    for k in list(highlights.keys()):
        highlights[k] = sorted(set(highlights[k]))
    return highlights


def build_flip_rotate_lists_by_piece(
    all_moves: List[Dict[str, Any]]
) -> Dict[Tuple[int, int], Dict[str, List[str]]]:
    """Collect textual flip/rotate options per origin square to display in the right pane."""
    fr: Dict[Tuple[int, int], Dict[str, List[str]]] = {}
    for m in all_moves:
        fx, fy = m["from"]
        key = (fx, fy)
        act = m.get("action", "")
        if act == "flip":
            label = m.get("orientation", "")
            label = f"flip {label}" if label else "flip"
            fr.setdefault(key, {"flip": [], "rotate": []})["flip"].append(label)
        elif act == "rotate":
            label = m.get("orientation", "")
            label = f"rotate → {label}" if label else "rotate"
            fr.setdefault(key, {"flip": [], "rotate": []})["rotate"].append(label)
    for k, v in fr.items():
        v["flip"] = sorted(set(v["flip"]))
        v["rotate"] = sorted(set(v["rotate"]))
    return fr


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("circle", "square"):
        print("Usage: python python_files/test_gm.py <my_side>\n  <my_side> = circle | square")
        sys.exit(1)

    my_side = sys.argv[1]

    # 4 centered scoring columns (same as engine)
    score_cols = score_cols_for(COLS)

    # Build Piece-board for drawing + dict-board for the generator
    piece_board = make_random_start_board(ROWS, COLS)
    dict_board = piece_board_to_dict_board(piece_board)

    # Get all legal moves using the rich generator (supports full river riding)
    all_moves = generate_all_possible_moves(dict_board, my_side, score_cols, score_cols)

    # Group targets per origin piece
    hl_by_piece = build_move_highlights_by_piece(all_moves)
    fr_by_piece = build_flip_rotate_lists_by_piece(all_moves)

    if not pygame:
        print("pygame is not available in this environment.")
        print("Computed moves via generate_moves.generate_all_possible_moves:")
        print(f"my_side={my_side}, pieces with moves={len(hl_by_piece)}")
        for origin, targets in list(hl_by_piece.items())[:10]:
            flips = ", ".join(fr_by_piece.get(origin, {}).get("flip", []))
            rots  = ", ".join(fr_by_piece.get(origin, {}).get("rotate", []))
            print(f"  from {origin} -> {targets[:8]}{'...' if len(targets)>8 else ''} | flips: [{flips}] rotates: [{rots}]")
        sys.exit(0)

    # --- Pygame window (board + right pane) ---
    window_width  = max(900, COLS * eng.CELL + eng.MARGIN * 2 + 240)
    window_height = max(600, ROWS * eng.CELL + eng.MARGIN * 2 + 100)
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Stones & Rivers — Move Highlighter")

    clock = pygame.time.Clock()

    # Iterate through each of my_side's pieces and highlight moves
    my_piece_list: List[Tuple[int, int]] = []
    for y in range(ROWS):
        for x in range(COLS):
            cell = piece_board[y][x]
            if cell and cell.owner == my_side:
                my_piece_list.append((x, y))

    idx = 0
    autoplay = True  # automatically cycle; press SPACE to toggle step-by-step

    timers = {"circle": 9 * 60 + 45, "square": 10 * 60}
    msg = "SPACE: next | A: autoplay | ESC: quit"

    pygame.font.init()
    font_title = pygame.font.SysFont(None, 22, bold=True)
    font_line  = pygame.font.SysFont(None, 20)

    # Right pane geometry
    board_px_w = COLS * eng.CELL
    board_px_h = ROWS * eng.CELL
    board_left = eng.MARGIN
    board_top  = eng.MARGIN
    right_pane_left = board_left + board_px_w + 16
    right_pane_top  = board_top
    right_pane_w    = window_width - right_pane_left - eng.MARGIN
    right_pane_h    = board_px_h

    running = True
    last_switch = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    autoplay = False
                    idx = (idx + 1) % max(1, len(my_piece_list))
                elif event.key == pygame.K_a:
                    autoplay = not autoplay

        now = pygame.time.get_ticks()
        if autoplay and (now - last_switch > 900) and my_piece_list:
            idx = (idx + 1) % len(my_piece_list)
            last_switch = now

        selected = my_piece_list[idx] if my_piece_list else None
        highlights = hl_by_piece.get(selected, []) if selected else []

        # draw board
        draw_board(
            screen=screen,
            board=piece_board,
            rows=ROWS,
            cols=COLS,
            score_cols=score_cols,
            selected=selected,
            highlights=highlights,
            msg=msg,
            timers=timers,
            current=my_side,
        )

        # Right pane with Flip/Rotate list
        pygame.draw.rect(screen, (20, 20, 24),
                         pygame.Rect(right_pane_left, right_pane_top, right_pane_w, right_pane_h),
                         border_radius=8)
        pygame.draw.rect(screen, (60, 60, 70),
                         pygame.Rect(right_pane_left, right_pane_top, right_pane_w, right_pane_h),
                         width=2, border_radius=8)

        ycursor = right_pane_top + 12
        title = f"{my_side.title()} piece actions"
        screen.blit(font_title.render(title, True, (220, 220, 230)), (right_pane_left + 12, ycursor))
        ycursor += 28

        if selected is not None:
            sx, sy = selected
            screen.blit(font_line.render(f"Selected: ({sx},{sy})", True, (200, 200, 210)),
                        (right_pane_left + 12, ycursor))
            ycursor += 22

            fr_lists = fr_by_piece.get(selected, {"flip": [], "rotate": []})

            screen.blit(font_title.render("Flips", True, (235, 235, 245)),
                        (right_pane_left + 12, ycursor))
            ycursor += 22
            if fr_lists["flip"]:
                for txt in fr_lists["flip"]:
                    screen.blit(font_line.render(f"• {txt}", True, (210, 210, 220)),
                                (right_pane_left + 18, ycursor))
                    ycursor += 20
            else:
                screen.blit(font_line.render("— none —", True, (140, 140, 150)),
                            (right_pane_left + 18, ycursor))
                ycursor += 20

            ycursor += 8

            screen.blit(font_title.render("Rotations", True, (235, 235, 245)),
                        (right_pane_left + 12, ycursor))
            ycursor += 22
            if fr_lists["rotate"]:
                for txt in fr_lists["rotate"]:
                    screen.blit(font_line.render(f"• {txt}", True, (210, 210, 220)),
                                (right_pane_left + 18, ycursor))
                    ycursor += 20
            else:
                screen.blit(font_line.render("— none —", True, (140, 140, 150)),
                            (right_pane_left + 18, ycursor))
                ycursor += 20

        pygame.display.flip()
        clock.tick(eng.FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
