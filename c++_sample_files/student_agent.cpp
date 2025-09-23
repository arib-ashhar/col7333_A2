#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <vector>
#include <map>
#include <random>

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

// ---- Student Agent ----
class StudentAgent {
public:
    explicit StudentAgent(std::string side) : side(std::move(side)), gen(rd()) {}

    Move choose(const std::vector<std::vector<std::map<std::string, std::string>>>& board, int row, int col, const std::vector<int>& score_cols, float current_player_time, float opponent_time) {
        int rows = board.size();
        int cols = board[0].size();

        std::vector<Move> moves = generate_all_possible_moves(board, side, score_cols, score_cols);

        // // Directions
        // std::vector<std::pair<int,int>> dirs = {{1,0},{-1,0},{0,1},{0,-1}};

        // // Iterate over board
        // for (int y = 0; y < rows; y++) {
        //     for (int x = 0; x < cols; x++) {
        //         const auto &cell = board[y][x];
        //         if (cell.empty()) continue;

        //         if (cell.at("owner") != side) continue; // only my pieces

        //         std::string side_type = cell.at("side");

        //         // ---- MOVES ----
        //         for (auto [dx,dy] : dirs) {
        //             int nx = x+dx, ny = y+dy;
        //             if (nx < 0 || nx >= cols || ny < 0 || ny >= rows) continue;

        //             if (board[ny][nx].empty()) {
        //                 moves.push_back({"move", {x,y}, {nx,ny}, {}, ""});
        //             }
        //         }

        //         // ---- PUSHES ----
        //         for (auto [dx,dy] : dirs) {
        //             int nx = x+dx, ny = y+dy;
        //             int nx2 = x+2*dx, ny2 = y+2*dy;
        //             if (nx<0||ny<0||nx>=cols||ny>=rows) continue;
        //             if (nx2<0||ny2<0||nx2>=cols||ny2>=rows) continue;

        //             if (!board[ny][nx].empty() && board[ny][nx].at("owner") != side
        //                 && board[ny2][nx2].empty()) {
        //                 moves.push_back({"push", {x,y}, {nx,ny}, {nx2,ny2}, ""});
        //             }
        //         }

        //         // ---- FLIP ----
        //         if (side_type == "stone") {
        //             moves.push_back({"flip", {x,y}, {x,y}, {}, "horizontal"});
        //             moves.push_back({"flip", {x,y}, {x,y}, {}, "vertical"});
        //         }

        //         // ---- ROTATE ----
        //         if (side_type == "river") {
        //             moves.push_back({"rotate", {x,y}, {x,y}, {}, ""});
        //         }
        //     }
        // }

        if (moves.empty()) {
            return {"move", {0,0}, {0,0}, {}, ""}; // fallback
        }

        std::uniform_int_distribution<> dist(0, moves.size()-1);
        return moves[dist(gen)];
    }

private:
    std::string side;
    std::random_device rd;
    std::mt19937 gen;


    // Helper Functions
    static inline bool has(const std::map<std::string,std::string>& m, const char* k) {
        return m.find(k) != m.end();
    }
    static inline std::string get(const std::map<std::string,std::string>& m, const char* k, const std::string& def="") {
        auto it = m.find(k); return it==m.end()? def : it->second;
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

        auto in_bounds = [&](int x,int y){ return x>=0 && x<cols && y>=0 && y<rows; };
        auto empty_cell = [&](int x,int y){ return in_bounds(x,y) && board[y][x].empty(); };
        auto side_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || board[y][x].empty()) return "";
            return get(board[y][x], "side");
        };
        auto owner_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || board[y][x].empty()) return "";
            return get(board[y][x], "owner");
        };
        auto orient_at = [&](int x,int y)->std::string {
            if (!in_bounds(x,y) || board[y][x].empty()) return "";
            return get(board[y][x], "orientation");
        };
        auto is_river = [&](int x,int y){ return side_at(x,y) == "river"; };
        auto is_stone = [&](int x,int y){ return side_at(x,y) == "stone"; };

        auto is_opp_score_col = [&](int x)->bool {
            return std::find(opp_score_cols.begin(), opp_score_cols.end(), x) != opp_score_cols.end();
        };

        // Directions (dx,dy)
        const std::pair<int,int> dirs[4] = {{1,0},{-1,0},{0,1},{0,-1}};

        // Whether a direction aligns with a river cell's orientation
        auto aligns_with_river = [&](int x,int y, int dx,int dy)->bool {
            if (!is_river(x,y)) return false;
            std::string o = orient_at(x,y); // "horizontal" or "vertical"
            if (o == "horizontal") return (dy == 0 && dx != 0);
            if (o == "vertical")   return (dx == 0 && dy != 0);
            return false;
        };

        // Find the farthest empty landing for pushing a stone along a straight line (dx,dy)
        auto farthest_empty_in_line = [&](int start_x,int start_y, int dx,int dy)->std::pair<bool,std::pair<int,int>> {
            int x = start_x, y = start_y;
            if (!in_bounds(x,y) || !empty_cell(x,y)) return {false, {0,0}};
            // Walk forward collecting empties; we choose the furthest legal empty
            int last_ok_x = x, last_ok_y = y;
            while (true) {
                if (is_opp_score_col(x)) break; // do not allow landing inside opponent score area
                last_ok_x = x; last_ok_y = y;
                int nx = x + dx, ny = y + dy;
                if (!in_bounds(nx,ny) || !empty_cell(nx,ny)) break;
                x = nx; y = ny;
            }
            return {true, {last_ok_x, last_ok_y}};
        };

        auto next_step_from_river = [&](int cx,int cy, int px,int py)->std::pair<bool,std::pair<int,int>> {
            // Given we're ON a river at (cx,cy) and we CAME FROM (px,py),
            // continue in the river's orientation AWAY from where we came.
            std::string o = orient_at(cx,cy);
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
            if (!in_bounds(rx,ry) || !is_river(rx,ry) || is_opp_score_col(rx)) return {false, {0,0}};

            int px = sx, py = sy;     // previous (where we came from)
            int cx = rx, cy = ry;     // current river cell

            while (true) {
                // Decide the next square to move into based on current river orientation
                auto [okNext, nxt] = next_step_from_river(cx,cy, px,py);
                if (!okNext) return {false, {0,0}};
                int nx = nxt.first, ny = nxt.second;

                // If next is out of bounds: we STOP on current river cell
                if (!in_bounds(nx,ny)) {
                    return {true, {cx,cy}};
                }

                // If next is opponent's scoring area
                if (is_opp_score_col(nx)) {
                    return {true, {cx,cy}};
                }

                // If next square has a STONE: we STOP on current river cell (cannot enter the stone)
                if (!empty_cell(nx,ny) && is_stone(nx,ny)) {
                    return {true, {cx,cy}};
                }

                // If next square is EMPTY and NOT a river: that's our landing
                if (empty_cell(nx,ny) && !is_river(nx,ny)) {
                    return {true, {nx,ny}};
                }

                // If next square is a RIVER (mine or opponent's), we CONTINUE riding.
                if (is_river(nx,ny)) {
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
                if (owner_at(x,y) != my_side) continue;  // only generate my moves

                const bool mine_is_stone = is_stone(x,y);
                const bool mine_is_river = is_river(x,y);

                // ---------- Basic 1-step moves into empty cell or ride in river direction ----------
                for (auto [dx,dy] : dirs) {
                    int nx = x + dx, ny = y + dy;
                    if (!in_bounds(nx,ny) || is_opp_score_col(nx)) continue;

                    // Case A: Adjacent is EMPTY and not a river
                    if (empty_cell(nx,ny) && !is_river(nx,ny)) {
                        moves.push_back({"move", {x,y}, {nx,ny}, {}, ""});
                        continue;
                    }

                    // Case B: Adjacent is a RIVER
                    if (is_river(nx,ny)) {
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
                    if (!in_bounds(ax,ay)) continue;
                    if (board[ay][ax].empty()) continue;     // nothing to push

                    bool target_is_opp = owner_at(ax,ay) != "" && owner_at(ax,ay) != my_side;
                    if (!target_is_opp) continue;

                    // Stone push: 1 cell
                    int bx = ax + dx, by = ay + dy;         // landing for the pushed piece (1 step)
                    if (in_bounds(bx,by) && empty_cell(bx,by) && !is_opp_score_col(bx)) {
                        moves.push_back({"push", {x,y}, {ax,ay}, {bx,by}, ""});
                    }

                    // River push: multi-cell (only if my FROM is a river aligned with dx,dy AND target is a STONE)
                    if (mine_is_river && aligns_with_river(x,y,dx,dy) && is_stone(ax,ay)) {
                        // Find farthest empty cell for the pushed stone starting from (bx,by)
                        if (in_bounds(bx,by) && empty_cell(bx,by)) {
                            auto [ok, far] = farthest_empty_in_line(bx,by,dx,dy);
                            if (ok) {
                                // far.first, far.second = final pushed landing
                                if (!is_opp_score_col(far.first)) {
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
                    std::string current_orientation = orient_at(x, y);
                    std::string new_orientation = current_orientation == "horizontal" ? "vertical" : "horizontal";
                    moves.push_back({"rotate", {x,y}, {x,y}, {}, new_orientation});
                }
            }
        }

        return moves;
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