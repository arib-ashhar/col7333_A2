from typing import List, Dict, Tuple, Any

# ---------- Move factory (same shape as before) ----------
def make_move(action: str,
              from_xy: List[int],
              to_xy: List[int],
              pushed_to_xy: List[int] = None,
              orientation: str = "") -> Dict[str, Any]:
    return {
        "action": action,
        "from": from_xy,
        "to": to_xy,
        "pushed_to": pushed_to_xy or [],
        "orientation": orientation,
    }

# ---------- Cell helpers ----------
def get(m: Dict[str, str], k: str, default: str = "") -> str:
    return m.get(k, default)

def in_bounds(b: List[List[Dict[str, str]]], x: int, y: int) -> bool:
    rows = len(b)
    cols = len(b[0]) if rows else 0
    return 0 <= x < cols and 0 <= y < rows

def empty_cell(b: List[List[Dict[str, str]]], x: int, y: int) -> bool:
    return in_bounds(b, x, y) and (len(b[y][x]) == 0)

def side_at(board: List[List[Dict[str, str]]], x: int, y: int) -> str:
    if not in_bounds(board, x, y) or len(board[y][x]) == 0:
        return ""
    return get(board[y][x], "side")

def owner_at(board: List[List[Dict[str, str]]], x: int, y: int) -> str:
    if not in_bounds(board, x, y) or len(board[y][x]) == 0:
        return ""
    return get(board[y][x], "owner")

def orient_at(board: List[List[Dict[str, str]]], x: int, y: int) -> str:
    if not in_bounds(board, x, y) or len(board[y][x]) == 0:
        return ""
    return get(board[y][x], "orientation")

def is_river(b: List[List[Dict[str, str]]], x: int, y: int) -> bool:
    return side_at(b, x, y) == "river"

def is_stone(b: List[List[Dict[str, str]]], x: int, y: int) -> bool:
    return side_at(b, x, y) == "stone"

# Score-area check (cell-aware)
def is_opp_score_cell(x: int, y: int, my_side: str, rows: int, opp_score_cols: List[int]) -> bool:
    # Circle's opponent (Square) scores on bottom row rows-3; Square's opponent (Circle) scores on row 2
    if my_side == "circle":
        return (y == rows - 3) and (x in opp_score_cols)
    else:
        return (y == 2) and (x in opp_score_cols)

# ---------- River utilities ----------
def outgoing_dirs_from_river(board: List[List[Dict[str, str]]], x: int, y: int) -> List[Tuple[int, int]]:
    o = orient_at(board, x, y)
    return [(-1, 0), (1, 0)] if o == "horizontal" else [(0, -1), (0, 1)]

def farthest_empty_in_line(board: List[List[Dict[str, str]]],
                           start_x: int, start_y: int, dx: int, dy: int,
                           my_side: str, opp_score_cols: List[int]) -> Tuple[bool, Tuple[int, int]]:
    rows = len(board)
    x, y = start_x, start_y
    if not in_bounds(board, x, y) or not empty_cell(board, x, y):
        return (False, (0, 0))
    last_ok = (x, y)
    while True:
        if is_opp_score_cell(x, y, my_side, rows, opp_score_cols):
            break
        last_ok = (x, y)
        nx, ny = x + dx, y + dy
        if not in_bounds(board, nx, ny) or not empty_cell(board, nx, ny):
            break
        x, y = nx, ny
    return (True, last_ok)

# ---- Full river ride: allows continuing across empties and chaining rivers ----
def river_ride_full(board: List[List[Dict[str, str]]],
                    start_rx: int, start_ry: int,
                    from_x: int, from_y: int,
                    my_side: str,
                    opp_score_cols: List[int]) -> List[Tuple[int, int]]:
    """
    Start: we STEP ONTO a river at (start_rx,start_ry) from (from_x,from_y).
    we may:
      - stop on any river cell encountered,
      - continue along flow, traversing any number of empty cells (each of them added to lsi tof possible moves),
      - if another river is reached, branch in its allowed direction(s) (excluding back-edge),
      - repeat until blocked (stone/board-edge/SA).
    """
    rows = len(board)
    if (not in_bounds(board, start_rx, start_ry)) or (not is_river(board, start_rx, start_ry)) \
       or is_opp_score_cell(start_rx, start_ry, my_side, rows, opp_score_cols):
        return []

    landings: List[Tuple[int, int]] = []
    # Visiting river edges: (prev_x,prev_y,curr_x,curr_y)
    seen_edges = set()
    stack: List[Tuple[int, int, int, int]] = [(from_x, from_y, start_rx, start_ry)]

    # Stepping onto the first river is a legal stop
    landings.append((start_rx, start_ry))

    while stack:
        px, py, cx, cy = stack.pop()
        edge_key = (px, py, cx, cy)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)

        back_vec = (px - cx, py - cy)
        for dx, dy in outgoing_dirs_from_river(board, cx, cy):
            if (dx, dy) == back_vec:
                continue

            # Advance one step in this flow, then keep going through empties
            nx, ny = cx + dx, cy + dy

            # If the very next cell is illegal, we can only stop on current river
            if not in_bounds(board, nx, ny) or is_opp_score_cell(nx, ny, my_side, rows, opp_score_cols):
                if (cx, cy) not in landings:
                    landings.append((cx, cy))
                continue

            # If immediate stone blocks, stop on current river
            if (not empty_cell(board, nx, ny)) and is_stone(board, nx, ny):
                if (cx, cy) not in landings:
                    landings.append((cx, cy))
                continue

            # Walk forward; every empty is a landing; if we encounter a river, stop the walk
            # (we can land on that river and then branch from it).
            walk_x, walk_y = nx, ny
            while in_bounds(board, walk_x, walk_y) and (not is_opp_score_cell(walk_x, walk_y, my_side, rows, opp_score_cols)):
                # Stone ahead: last legal landing is the previous square (already added if empty or river)
                if (not empty_cell(board, walk_x, walk_y)) and is_stone(board, walk_x, walk_y):
                    # if the blocked cell is stone, the square before it (either the river cx,cy or last empty) is already listed
                    break

                if empty_cell(board, walk_x, walk_y):
                    # Empty squares along the flow are all possible moves
                    if (walk_x, walk_y) not in landings:
                        landings.append((walk_x, walk_y))
                    # keep walking straight
                    walk_x += dx
                    walk_y += dy
                    continue

                if is_river(board, walk_x, walk_y):
                    # landing on the new river, then branch from it
                    if (walk_x, walk_y) not in landings:
                        landings.append((walk_x, walk_y))
                    stack.append((walk_x - dx, walk_y - dy, walk_x, walk_y))
                    break

                # any other case -> stop
                break

    # stable de-dup
    out, seenp = [], set()
    for p in landings:
        if p not in seenp:
            out.append(p); seenp.add(p)
    return out

# ---------- helpers for push moves ----------
def push_landings_for_stone_displacement(board: List[List[Dict[str, str]]],
                                         start_after: Tuple[int, int],
                                         dir_vec: Tuple[int, int],
                                         my_side: str,
                                         opp_score_cols: List[int]) -> List[Tuple[int, int]]:
    """
    - When pushing a stone add all legal cells that stone can land on from where it starts
    - If it reaches a river, use river_ride_full() to ride in the river direction (Used DFS to ride combinations of river on the path).
    """
    rows = len(board)
    dx, dy = dir_vec
    cx, cy = start_after
    landings: List[Tuple[int, int]] = []

    if not in_bounds(board, cx, cy) or is_opp_score_cell(cx, cy, my_side, rows, opp_score_cols):
        return []
    if (not empty_cell(board, cx, cy)) and is_stone(board, cx, cy):
        return []

    # Straight empties first
    while in_bounds(board, cx, cy) and empty_cell(board, cx, cy) \
          and (not is_opp_score_cell(cx, cy, my_side, rows, opp_score_cols)):
        landings.append((cx, cy))
        cx, cy = cx + dx, cy + dy

    # If a river is next, branch from it
    prev = (cx - dx, cy - dy)
    if in_bounds(board, cx, cy) and is_river(board, cx, cy) \
       and (not is_opp_score_cell(cx, cy, my_side, rows, opp_score_cols)):
        extra = river_ride_full(board, cx, cy, prev[0], prev[1], my_side, opp_score_cols)
        for p in extra:
            if p not in landings:
                landings.append(p)

    return landings


def generate_all_possible_moves(
    board: List[List[Dict[str, str]]],
    my_side: str,
    my_score_cols: List[int],
    opp_score_cols: List[int]
) -> List[Dict[str, Any]]:
    moves: List[Dict[str, Any]] = []

    rows = len(board)
    cols = len(board[0]) if rows else 0
    if rows == 0 or cols == 0:
        return moves

    dirs: Tuple[Tuple[int, int], ...] = ((1,0), (-1,0), (0,1), (0,-1))

    for y in range(rows):
        for x in range(cols):
            if len(board[y][x]) == 0:
                continue
            if owner_at(board, x, y) != my_side:
                continue  # only my pieces

            mine_is_stone = is_stone(board, x, y)
            mine_is_river = is_river(board, x, y)

            # --------- MOVEMENT (exactly 1 step; ride only if we step onto a river) ---------
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                if not in_bounds(board, nx, ny):
                    continue
                if is_opp_score_cell(nx, ny, my_side, rows, opp_score_cols):
                    continue  # cannot enter opponent SA

                # Adjacent EMPTY non-river -> single 1-step move
                if empty_cell(board, nx, ny) and (not is_river(board, nx, ny)):
                    moves.append(make_move("move", [x, y], [nx, ny]))
                    continue

                # Adjacent is a RIVER -> step onto it and enumerate full ride landings
                if is_river(board, nx, ny):
                    landings = river_ride_full(board, nx, ny, x, y, my_side, opp_score_cols)
                    for lx, ly in landings:
                        moves.append(make_move("move", [x, y], [lx, ly]))
                    continue

            # --------------------- PUSHING ---------------------
            for dx, dy in dirs:
                ax, ay = x + dx, y + dy
                if not in_bounds(board, ax, ay):
                    continue
                if empty_cell(board, ax, ay):
                    continue  # nothing to push
                if is_opp_score_cell(ax, ay, my_side, rows, opp_score_cols):
                    continue  # cannot enter SA to push

                target_is_stone = is_stone(board, ax, ay)

                # Stone push: exactly one, target must be stone, next must be empty & legal
                if mine_is_stone and target_is_stone:
                    bx, by = ax + dx, ay + dy
                    if in_bounds(board, bx, by) and empty_cell(board, bx, by) \
                       and (not is_opp_score_cell(bx, by, my_side, rows, opp_score_cols)):
                        moves.append(make_move("push", [x, y], [ax, ay], [bx, by]))
                    continue

                # River push: mover is river, target must be stone; push any distance along dir
                if mine_is_river and target_is_stone: 
                    # the displaced stone must follow river riding rules and cannot pass another stone.
                    start_after = (ax + dx, ay + dy)
                    landings = push_landings_for_stone_displacement(
                        board, start_after, (dx, dy), my_side, opp_score_cols
                    )
                    for lx, ly in landings:
                        moves.append(make_move("push", [x, y], [ax, ay], [lx, ly]))
                    continue

            # --------------------- FLIP & ROTATE ---------------------
            if mine_is_stone:
                # flip into a river (choose orientation)
                moves.append(make_move("flip", [x, y], [x, y], orientation="horizontal"))
                moves.append(make_move("flip", [x, y], [x, y], orientation="vertical"))
            if mine_is_river:
                # flip into a stone
                moves.append(make_move("flip", [x, y], [x, y]))
                # rotate to the other orientation
                curr = orient_at(board, x, y)
                new_orientation = "horizontal" if curr == "vertical" else "vertical"
                moves.append(make_move("rotate", [x, y], [x, y], orientation=new_orientation))

    return moves
