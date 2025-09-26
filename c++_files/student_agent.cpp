#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <map>
#include <random>
#include <algorithm>
#include <climits>
#include <iostream>

namespace py = pybind11;


/*
=========================================================
 STUDENT AGENT FOR STONES & RIVERS GAME
---------------------------------------------------------
 The Python game engine passes the BOARD state into C++.
 Each board cell is represented as a dictionary in Python:

    {
        "owner": "circle" | "square",          // which player owns this piece
        "side": "stone" | "river",             // piece type
        "orientation": "horizontal" | "vertical"  // only relevant if side == "river"
    }

 In C++ with pybind11, this becomes:

    std::vector<std::vector<std::map<std::string, std::string>>>

 Meaning:
   - board[y][x] gives the cell at (x, y).
   - board[y][x].empty() → true if the cell is empty (no piece).
   - board[y][x].at("owner") → "circle" or "square".
   - board[y][x].at("side") → "stone" or "river".
   - board[y][x].at("orientation") → "horizontal" or "vertical".

=========================================================
*/

// ---- Move struct ----
struct Move {
    std::string action;
    std::vector<int> from;
    std::vector<int> to;
    std::vector<int> pushed_to;
    std::string orientation;
};

struct MinMaxNode {
    int value;
    Move bestMove;
};


// ---- Student Agent ----
class StudentAgent {
    private:
        int movesCount = 0;
public:
    explicit StudentAgent(std::string side) : side(std::move(side)), gen(rd()) {}

    Move choose(const std::vector<std::vector<std::map<std::string, std::string>>>& board, int row, int col, const std::vector<int>& score_cols, float current_player_time, float opponent_time) {
        int rows = board.size();
        int cols = board[0].size();

        
        const std::string me = side;
        const std::vector<int> my_score_cols  = score_cols;
        const std::vector<int> opp_score_cols = {};

        const int alpha = INT_MIN;
        const int beta = INT_MAX;
        
        // time constraint, MOve Strategy
        constexpr float TOTAL_TIME = 60.0f;
        constexpr float MINMAX_TIME_LIMIT = 0.7f * TOTAL_TIME;

        //Set the DePTH based on the time left
        const int DEPTH = current_player_time < 0.4f * TOTAL_TIME ? 3 : current_player_time < 0.6f * TOTAL_TIME ? 2 : 1;


        auto openingMove = generate_opening_move(board, me, my_score_cols, opp_score_cols);
        if (openingMove.has_value()) {
            movesCount++;
            //std::cout<<"MovesCount="<<movesCount<<" Opening MOve played="<<std::endl;
            return openingMove.value();
        }

        if(current_player_time > MINMAX_TIME_LIMIT && current_player_time > opponent_time) {
            auto result = minMaxWithAlphaBeta(board, DEPTH, alpha, beta, me, me, my_score_cols, opp_score_cols);
            if (!result.bestMove.action.empty()) {
                //std::cout<<"MovesCount="<<movesCount<<" MinMax MOve played="<<std::endl;
                movesCount++;
                return result.bestMove;
            }
        }

        auto moves = generate_all_possible_moves(board, side, score_cols, score_cols);
        movesCount++;
        if (moves.empty()) return {"move", {0,0}, {0,0}, {}, ""};
        std::uniform_int_distribution<> dist(0, moves.size()-1);
        return moves[dist(gen)];
    }


private:
    std::string side;
    std::random_device rd;
    std::mt19937 gen;


    //Helper Functions
    static inline bool has(const std::map<std::string,std::string>& m, const char* k) {
        return m.find(k) != m.end();
    }
    static inline std::string get(const std::map<std::string,std::string>& m, const char* k, const std::string& def="") {
        auto it = m.find(k); return it==m.end()? def : it->second;
    }

    static bool in_bounds(const std::vector<std::vector<std::map<std::string, std::string>>>& b, int x, int y) {
        const int rows = (int)b.size();
        const int cols = rows ? (int)b[0].size() : 0;
        return x >= 0 && x < cols && y >= 0 && y < rows;
    }
    static inline bool empty_cell(const std::vector<std::vector<std::map<std::string, std::string>>>& b, int x, int y) {
        return in_bounds(b, x, y) && b[y][x].empty();
    }
    static std::string side_at(const std::vector<std::vector<std::map<std::string, std::string>>>& board,int x,int y) {
        if (!in_bounds(board,x,y) || board[y][x].empty()) return "";
        return get(board[y][x], "side");
    };
    static std::string owner_at(const std::vector<std::vector<std::map<std::string, std::string>>>& board,int x,int y) {
        if (!in_bounds(board,x,y) || board[y][x].empty()) return "";
        return get(board[y][x], "owner");
    };
    static std::string orient_at(const std::vector<std::vector<std::map<std::string, std::string>>>& board,int x,int y) {
        if (!in_bounds(board,x,y) || board[y][x].empty()) return "";
        return get(board[y][x], "orientation");
    };
    static bool is_river(const std::vector<std::vector<std::map<std::string, std::string>>>& b, int x, int y) { return side_at(b,x,y) == "river"; }
    static bool is_stone(const std::vector<std::vector<std::map<std::string, std::string>>>& b, int x, int y) { return side_at(b,x,y) == "stone"; }

    static bool is_opp_score_col(int x, const std::vector<int>& cols) {
        return std::find(cols.begin(), cols.end(), x) != cols.end();
    }

    // ---- Generate all legal moves for `my_side` ----
    // board[y][x] cell schema:
    //   "owner": "circle" | "square"
    //   "side":  "stone"  | "river"
    //   "orientation": "horizontal" | "vertical"    (only for river)
    //
    // Parameters:
    //   my_side         : "circle" or "square" (whose moves to generate)
    //   my_score_cols   : columns that count as my scoring area 
    //   opp_score_cols  : columns that are the opponent's scoring area 
    static std::vector<Move> generate_all_possible_moves(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& my_side,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        std::vector<Move> moves;

        const int rows = (int)board.size();
        const int cols = rows ? (int)board[0].size() : 0;
        if (rows == 0 || cols == 0) return moves;

        // Directions (dx,dy)
        const std::pair<int,int> dirs[4] = {{1,0},{-1,0},{0,1},{0,-1}};

        // Whether a direction aligns with a river cell's orientation
        auto aligns_with_river = [&](int x,int y, int dx,int dy)->bool {
            if (!is_river(board,x,y)) return false;
            std::string o = orient_at(board,x,y); // "horizontal" or "vertical"
            if (o == "horizontal") return (dy == 0 && dx != 0);
            if (o == "vertical")   return (dx == 0 && dy != 0);
            return false;
        };

        // Find the farthest empty landing for pushing a stone along a straight line (dx,dy)
        auto farthest_empty_in_line = [&](int start_x,int start_y, int dx,int dy)->std::pair<bool,std::pair<int,int>> {
            int x = start_x, y = start_y;
            if (!in_bounds(board,x,y) || !empty_cell(board,x,y)) return {false, {0,0}};
            // Walk forward collecting empties; we choose the furthest legal empty
            int last_ok_x = x, last_ok_y = y;
            while (true) {
                if (is_opp_score_col(x, opp_score_cols)) break; // do not allow landing inside opponent score area
                last_ok_x = x; last_ok_y = y;
                int nx = x + dx, ny = y + dy;
                if (!in_bounds(board,nx,ny) || !empty_cell(board,nx,ny)) break;
                x = nx; y = ny;
            }
            return {true, {last_ok_x, last_ok_y}};
        };

        auto next_step_from_river = [&](int cx,int cy, int px,int py)->std::pair<bool,std::pair<int,int>> {
            // Given we're ON a river at (cx,cy) and we CAME FROM (px,py),
            // continue in the river's orientation AWAY from where we came.
            std::string o = orient_at(board,cx,cy);
            std::vector<std::pair<int,int>> outs;
            if(o == "horizontal") outs = {{-1,0},{+1,0}};
            else outs = {{0,-1},{0,+1}};

            for (auto [dx,dy] : outs) {
                int nx = cx + dx, ny = cy + dy;
                // Don't go back to where we came from
                if (nx == px && ny == py) continue;
                return {true, {nx,ny}};
            }
            return {false, {0,0}};
        };

        // Follow river network starting from the first river cell (rx,ry) we step onto.
        // We entered from (sx,sy) (the square we were originally on before stepping into (rx,ry)).
        // Returns:
        //  - ok=false if ride is impossible (e.g., immediate out-of-bounds).
        //  - ok=true, landing=(lx,ly) which is either:
        //      * the first NON-RIVER empty square after the ride, OR
        //      * the last river cell before a stone/off-board (forced stop on river).
        auto river_ride_chain = [&](int rx,int ry, int sx,int sy)
            -> std::pair<bool,std::pair<int,int>>
        {
            if (!in_bounds(board,rx,ry) || !is_river(board,rx,ry) || is_opp_score_col(rx, opp_score_cols)) return {false, {0,0}};

            int px = sx, py = sy;     // previous (where we came from)
            int cx = rx, cy = ry;     // current river cell

            while (true) {
                // Decide the next square to move into based on current river orientation
                auto [okNext, nxt] = next_step_from_river(cx,cy, px,py);
                if (!okNext) return {false, {0,0}};
                int nx = nxt.first, ny = nxt.second;

                // If next is out of bounds: we STOP on current river cell
                if (!in_bounds(board,nx,ny)) {
                    return {true, {cx,cy}};
                }

                // If next is opponent's scoring area
                if (is_opp_score_col(nx, opp_score_cols)) {
                    return {true, {cx,cy}};
                }

                // If next square has a STONE: we STOP on current river cell (cannot enter the stone)
                if (!empty_cell(board,nx,ny) && is_stone(board,nx,ny)) {
                    return {true, {cx,cy}};
                }

                // If next square is EMPTY and NOT a river: that's our landing
                if (empty_cell(board,nx,ny) && !is_river(board,nx,ny)) {
                    return {true, {nx,ny}};
                }

                // If next square is a RIVER (mine or opponent's), we CONTINUE riding.
                if (is_river(board,nx,ny)) {
                    // current becomes previous, next becomes current
                    px = cx; py = cy;
                    cx = nx; cy = ny;
                    continue;
                }
                return {true, {cx,cy}};
            }
        };

        for (int y = 0; y < rows; ++y) {
            for (int x = 0; x < cols; ++x) {
                if (board[y][x].empty()) continue;
                if (owner_at(board,x,y) != my_side) continue;  // only generate my moves

                const bool mine_is_stone = is_stone(board,x,y);
                const bool mine_is_river = is_river(board,x,y);

                // ---------- Basic 1-step moves into empty cell or ride in river direction ----------
                for (auto [dx,dy] : dirs) {
                    int nx = x + dx, ny = y + dy;
                    if (!in_bounds(board,nx,ny) || is_opp_score_col(nx, opp_score_cols)) continue;

                    // Case A: Adjacent is EMPTY and not a river
                    if (empty_cell(board,nx,ny) && !is_river(board,nx,ny)) {
                        moves.push_back({"move", {x,y}, {nx,ny}, {}, ""});
                        continue;
                    }

                    // Case B: Adjacent is a RIVER
                    if (is_river(board,nx,ny)) {
                        auto [ok, land] = river_ride_chain(nx,ny, x,y);
                        if (ok) {
                            moves.push_back({"move", {x,y}, {land.first, land.second}, {}, ""});
                        }
                        continue;
                    }
                }


                // ---------- Pushes ----------
                //  - Stone push: push adjacent opponent piece by 1 if next cell empty/legal
                //  - River push: if my piece is a RIVER and the direction aligns with its flow and
                //                the adjacent is an opponent STONE, then push it *any distance*
                //                to the farthest empty in that line (landing not in opp score cols).
                for (auto [dx,dy] : dirs) {
                    int ax = x + dx, ay = y + dy;           // adjacent target piece
                    if (!in_bounds(board,ax,ay)) continue;
                    if (board[ay][ax].empty()) continue;     // nothing to push

                    bool target_is_opp = owner_at(board,ax,ay) != "" && owner_at(board,ax,ay) != my_side;
                    if (!target_is_opp) continue;

                    // Stone push: 1 cell
                    int bx = ax + dx, by = ay + dy;         // landing for the pushed piece (1 step)
                    if (in_bounds(board,bx,by) && empty_cell(board,bx,by) && !is_opp_score_col(bx, opp_score_cols)) {
                        moves.push_back({"push", {x,y}, {ax,ay}, {bx,by}, ""});
                    }

                    // River push: multi-cell (only if my FROM is a river aligned with dx,dy AND target is a STONE)
                    if (mine_is_river && aligns_with_river(x,y,dx,dy) && is_stone(board,ax,ay)) {
                        // Find farthest empty cell for the pushed stone starting from (bx,by)
                        if (in_bounds(board,bx,by) && empty_cell(board,bx,by)) {
                            auto [ok, far] = farthest_empty_in_line(bx,by,dx,dy);
                            if (ok) {
                                // far.first, far.second = final pushed landing
                                if (!is_opp_score_col(far.first, opp_score_cols)) {
                                    moves.push_back({"push", {x,y}, {ax,ay}, {far.first, far.second}, ""});
                                }
                            }
                        }
                    }
                }

                // ---------- Flips ----------
                if (mine_is_stone) {
                    moves.push_back({"flip", {x,y}, {x,y}, {}, "horizontal"});
                    moves.push_back({"flip", {x,y}, {x,y}, {}, "vertical"});
                }
                if (mine_is_river) {
                    moves.push_back({"flip", {x,y}, {x,y}, {}, ""});
                }

                // ---------- Rotation ----------
                if (mine_is_river) {
                    std::string current_orientation = orient_at(board,x, y);
                    std::string new_orientation = current_orientation == "horizontal" ? "vertical" : "horizontal";
                    moves.push_back({"rotate", {x,y}, {x,y}, {}, new_orientation});
                }
            }
        }

        return moves;
    }


    // ---------------- EVALUATION FUNCTIONs   -------------------------------

    // Count how many of `side`’s stones are already in its scoring columns
    static int scoredCount(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& side,
        const std::vector<int>& score_cols
    ) {
        int count = 0;
        for(int y=0;y < (int)board.size(); y++) {
            for(int x=0;x < (int)board[0].size(); x++) {
                if(empty_cell(board,x, y)) continue;
                if(owner_at(board,x, y) == side && is_stone(board,x, y) && 
                    std::find(score_cols.begin(), score_cols.end(), x) != score_cols.end())
                        count++;
            }
        }
        return count;
    }

    // Count how many stones of `side` can reach their scoring columns in ONE legal move
    static int oneMoveReachables(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& side,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        int count = 0;
        // TODO: we can cache the 1 moves from calling function
        auto moves = generate_all_possible_moves(board, side, my_score_cols, opp_score_cols);
        for (const auto& m : moves) {
            if (m.action == "move" || m.action == "push") {
                int tx = m.to[0], ty = m.to[1];
                if (std::find(my_score_cols.begin(), my_score_cols.end(), tx) != my_score_cols.end()) {
                    count++;
                }
                // if pushed_to score area
                if (!m.pushed_to.empty()) {
                    int px = m.pushed_to[0], py = m.pushed_to[1];
                    if (std::find(my_score_cols.begin(), my_score_cols.end(), px) != my_score_cols.end()) {
                        count++;
                    }
                }
            }
        }
        return count;
    }

    // Estimate minimal number of moves needed for side to reach 4 stones in score area
    static int minMovesToFinish(
        const int scoredCount,
        const int oneMoveReachableCount
    ) {
        int need = std::max(0, 4 - scoredCount);
        if (need == 0) return 0;

        // number of stones needed except those that are reachable in 1 move
        int effectiveNeed = std::max(0, need - oneMoveReachableCount);

        // assuming each remaining stone costs at least 2 plies to set up in heuristic
        return effectiveNeed * 2 + (need - effectiveNeed);
    }

    // Count potential lanes: number of river chains that point into (or just before) my scoring cols
    static int riverLanePotentialTowardScore(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& side,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        int score = 0;
        for (int y = 0; y < (int)board.size(); ++y) {
            for (int x = 0; x < (int)board[0].size(); ++x) {
                if (empty_cell(board,x, y) || is_stone(board,x, y)) continue;

                // if this river is oriented horizontally and next cell is a scoring col
                if (orient_at(board,x, y) == "horizontal") {
                    if (std::find(my_score_cols.begin(), my_score_cols.end(), x+1) != my_score_cols.end() ||
                        std::find(my_score_cols.begin(), my_score_cols.end(), x-1) != my_score_cols.end()) {
                        score++;
                    }
                }
                if (orient_at(board,x, y) == "vertical") {
                    // check above/below
                    if (std::find(my_score_cols.begin(), my_score_cols.end(), x) != my_score_cols.end()) {
                        score++;
                    }
                }
            }
        }
        return score;
    }

    int evaluate(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& me,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        std::string opp = (me == "circle" ? "square" : "circle");

        // number of stones scored
        int nself = scoredCount(board, me,  my_score_cols);
        int nopp  = scoredCount(board, opp, opp_score_cols);

        if (nself >= 4) return  1000000;    // won
        if (nopp  >= 4) return -1000000;    // lost

        // number of stones that can be scored with 1 move
        int mself = oneMoveReachables(board, me,  my_score_cols, opp_score_cols);
        int mopp  = oneMoveReachables(board, opp, opp_score_cols, my_score_cols);

        // minimum number of moves required to win the game
        int dself = minMovesToFinish(nself, mself);
        int dopp  = minMovesToFinish(nopp, mopp);

        // number of river lanes present to the scoring area in the current board
        int laneSelf = riverLanePotentialTowardScore(board, me,  my_score_cols, opp_score_cols);
        int laneOpp  = riverLanePotentialTowardScore(board, opp, opp_score_cols, my_score_cols);

        int score = 
            1000 * (nself - nopp) +
            180 * (mself - mopp) +
            -15 * (dself - dopp) +
            40 * (laneSelf - laneOpp);

        return score;
    }


    std::optional<Move> generate_opening_move(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const std::string& my_side,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        int rows = (int)board.size();
        int cols = rows ? (int)board[0].size() : 0;
        if (rows == 0 || cols == 0) return std::nullopt;

        int dy = (my_side == "circle" ? -1 : +1);

        auto path_clear = [&](int x, int y, int nx, int ny) {
            if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) return false;
            if (!board[ny][nx].empty()) return false;
            if (std::find(opp_score_cols.begin(), opp_score_cols.end(), nx) != opp_score_cols.end())
                return false;
            return true;
        };

        int central_left  = cols / 2 - 1;
        int central_right = cols / 2;
        for (int x : {central_left, central_right}) {
            for (int y = 0; y < rows; y++) {
                if (owner_at(board, x, y) == my_side && is_stone(board, x, y)) {
                    int ny = y + dy;
                    if (path_clear(x, y, x, ny)) {
                        return Move{"move", {x, y}, {x, ny}, {}, ""};
                    }
                }
            }
        }

        int outer_left  = central_left - 2;
        int outer_right = central_right + 2;
        for (int x : {outer_left, outer_right}) {
            if (x < 0 || x >= cols) continue;
            for (int y = 0; y < rows; y++) {
                if (owner_at(board, x, y) == my_side && is_stone(board, x, y)) {
                    int ny = y + dy;
                    if (path_clear(x, y, x, ny)) {
                        return Move{"move", {x, y}, {x, ny}, {}, ""};
                    }
                }
            }
        }

        int sec_left  = central_left - 1;
        int sec_right = central_right + 1;
        for (int x : {sec_left, sec_right}) {
            if (x < 0 || x >= cols) continue;
            for (int y = 0; y < rows; y++) {
                if (owner_at(board, x, y) == my_side && is_stone(board, x, y)) {
                    // flip to horizontal river
                    return Move{"flip", {x, y}, {x, y}, {}, "horizontal"};
                }
                if (owner_at(board, x, y) == my_side && is_river(board, x, y)) {
                    int ny = y + dy;
                    if (path_clear(x, y, x, ny)) {
                        return Move{"move", {x, y}, {x, ny}, {}, ""};
                    }
                }
            }
        }

        return std::nullopt;
    }


    // ------------------------- Min Max Tree Implementation ---------------------

    //apply move for min max tree so that board gets updated in place.
    static std::vector<std::vector<std::map<std::string, std::string>>> apply_move(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        const Move& m
    ) {
        std::vector<std::vector<std::map<std::string, std::string>>> nextBoard = board;

        auto rows = (int)board.size();
        auto cols = rows ? (int)board[0].size() : 0;

        auto in_bounds = [&](int x,int y){ return x>=0 && x<cols && y>=0 && y<rows; };
        auto empty_cell = [&](int x,int y){ return in_bounds(x,y) && nextBoard[y][x].empty(); };
        auto side_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || nextBoard[y][x].empty()) return "";
            return get(nextBoard[y][x], "side");
        };
        auto owner_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || nextBoard[y][x].empty()) return "";
            return get(nextBoard[y][x], "owner");
        };
        auto orient_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || nextBoard[y][x].empty()) return "";
            return get(nextBoard[y][x], "orientation");
        };
        auto set_empty = [&](int x,int y){
            if (in_bounds(x,y)) nextBoard[y][x].clear();
        };
        auto set_piece = [&](int x,int y,
                            const std::string& owner,
                            const std::string& side,
                            const std::string& orientation){
            if (!in_bounds(x,y)) return;
            nextBoard[y][x].clear();
            nextBoard[y][x]["owner"] = owner;
            nextBoard[y][x]["side"]  = side;
            if (side == "river") nextBoard[y][x]["orientation"] = orientation;
        };

        const int fx = m.from[0], fy = m.from[1];
        const int tx = m.to[0], ty = m.to[1];

        if(m.action == "move") {
            const std::string me = owner_at(fx,fy);
            const std::string side = side_at(fx,fy);
            const std::string orientation = orient_at(fx,fy);
            set_empty(fx,fy);
            set_piece(tx,ty, me, side, (side=="river" ? orientation : ""));
            return nextBoard;
        }
        else if(m.action == "push") {
            const int px = m.pushed_to[0], py = m.pushed_to[1];

            const std::string pusherOwner = owner_at(fx,fy);
            const std::string pusherSide  = side_at(fx,fy);
            const std::string pusherOrientation   = orient_at(fx,fy);

            const std::string pushedOwner = owner_at(tx,ty);
            const std::string pushedSide  = side_at(tx,ty);
            const std::string pushedOrientation   = orient_at(tx,ty);

            // move pushed piece
            set_empty(tx,ty);
            set_piece(px,py, pushedOwner, pushedSide, (pushedSide=="river" ? pushedOrientation : ""));

            // move pusher into the vacated square
            set_empty(fx,fy);
            if (pusherSide == "river") {
                // river that pushed becomes stone
                set_piece(tx,ty, pusherOwner, "stone", "");
            } else {
                set_piece(tx,ty, pusherOwner, pusherSide, (pusherSide=="river" ? pusherOrientation : ""));
            }
            return nextBoard;
        }
        else if(m.action == "flip") {
            const std::string me   = owner_at(fx,fy);
            const std::string side = side_at(fx,fy);
            if (side == "stone") {
                set_piece(fx,fy, me, "river", m.orientation);
            } else {
                set_piece(fx,fy, me, "stone", "");
            }
            return nextBoard;
        }
        else if(m.action == "rotate") {
            const std::string me   = owner_at(fx,fy);
            const std::string side = side_at(fx,fy);
            if (side == "river") {
                std::string newOrientation = m.orientation;
                set_piece(fx,fy, me, "river", newOrientation);
            }
            return nextBoard;
        }
        return nextBoard;
    }

    // Order min-max nodes in the order push > move > flip > rotate
    static void order_moves(std::vector<Move>& moves) {
        auto key = [&](const Move& m)->int {
            if (m.action=="move") return 3;
            if (m.action=="push") return 2;
            if (m.action=="flip" || m.action=="rotate") return 1;
            return 0;
        };
        std::stable_sort(moves.begin(), moves.end(), [&](const Move& a, const Move& b){
            return key(a) > key(b);
        });
    }

    MinMaxNode minMaxWithAlphaBeta(
        const std::vector<std::vector<std::map<std::string, std::string>>>& board,
        int depth, int alpha, int beta,
        const std::string& side_to_move,
        const std::string& me,
        const std::vector<int>& my_score_cols,
        const std::vector<int>& opp_score_cols
    ) {
        const std::string opp = (me=="circle" ? "square" : "circle");
        if (depth == 0) {
            return { evaluate(board, me, my_score_cols, opp_score_cols), {} };
        }

        const bool myTurn = (side_to_move == me);
        const auto& cur_my_cols  = myTurn ? my_score_cols  : opp_score_cols;
        const auto& cur_opp_cols = myTurn ? opp_score_cols : my_score_cols;

        auto moves = generate_all_possible_moves(board, side_to_move, cur_my_cols, cur_opp_cols);
        if (moves.empty()) {
            return { evaluate(board, me, my_score_cols, opp_score_cols), {} };
        }
        order_moves(moves);

        if (myTurn) {
            // Max Nodes
            MinMaxNode bestNode{ std::numeric_limits<int>::min(), {} };
            for (const auto& m : moves) {
                std::vector<std::vector<std::map<std::string, std::string>>> newBoard = apply_move(board, m);
                auto result = minMaxWithAlphaBeta(newBoard, depth-1, alpha, beta, opp, me, my_score_cols, opp_score_cols);
                if (result.value > bestNode.value) { bestNode.value = result.value; bestNode.bestMove = m; }
                alpha = std::max(alpha, result.value);
                if (alpha >= beta) break; // prune
            }
            return bestNode;
        } else {
            // Min Nodes
            MinMaxNode bestNode{ std::numeric_limits<int>::max(), {} };
            for (const auto& m : moves) {
                std::vector<std::vector<std::map<std::string, std::string>>> newBoard = apply_move(board, m);
                auto result = minMaxWithAlphaBeta(newBoard, depth-1, alpha, beta, me, me, my_score_cols, opp_score_cols);
                if (result.value < bestNode.value) { bestNode.value = result.value; bestNode.bestMove = m; }
                beta = std::min(beta, result.value);
                if (beta <= alpha) break; // prune
            }
            return bestNode;
        }
    }

};

// ---- PyBind11 bindings ----
PYBIND11_MODULE(student_agent_module, m) {
    py::class_<Move>(m, "Move")
        .def_readonly("action", &Move::action)
        .def_readonly("from_pos", &Move::from)
        .def_readonly("to_pos", &Move::to)
        .def_readonly("pushed_to", &Move::pushed_to)
        .def_readonly("orientation", &Move::orientation);

    py::class_<StudentAgent>(m, "StudentAgent")
        .def(py::init<std::string>())
        .def("choose", &StudentAgent::choose);
}