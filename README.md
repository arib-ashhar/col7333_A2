# Stones and Rivers Game

This repository contains the code for Adversarial agent and game Engine for the River and Stones.

Here is the demo of agent playing against another adversarial agent:



## Details
This is a course assignment for the graduate-level Artificial Intelligence course taught by [**Prof. Mausam**](https://www.cse.iitd.ac.in/~mausam/). The assignment documentation can be found on the Course website.

## Rules
You can find the documentation to get all the rules of the game.

### 🎯 Objective

A player wins if:

 - They place all required Stone sides (face-up) in their Score Area (SA) — located near the opponent’s starting side — before the opponent does.
 - Or, if the opponent runs out of time, and neither player has completed their score area.

### Board Sizes:
The game is played on three board configurations — small (13 × 12), medium (15 × 14), and large (17 × 16) — with the scoring area (SA) containing 4, 5, and 6 spaces respectively.
 – Small Board (13×12): Includes 24 starting positions (12 for each player) and two score areas. Each score area (SA) contains 4 spaces where stones must be placed to achieve victory.
 – Medium Board (15×14): Includes 28 starting positions (14 for each player) and two score areas. Each score area (SA) contains 5 spaces where stones must be placed to achieve victory
 - Large Board (17×16): Includes 32 starting positions (16 for each player) and two score areas. Each score area (SA) contains 6 spaces where stones must be placed to achieve victory

### 🧩 Types of Pieces

 - Stone: Plain circular/square piece — used to score.
 - River: Piece with a thin line through it — represents the flow direction.
Line direction = River flow (horizontal or vertical).

### 🔁 Actions per Turn

On each turn, a player can choose one of the following actions:

1. Move a piece (Stone or River)
2. Push a piece (using a Stone or River)
3. Flip & Rotate a piece (Stone ↔ River)
4. Rotate a River (change its flow direction by 90°)

### 🧭 Movement Rules
General Movement
 - Both Stones and Rivers can move exactly one step up, down, left, or right.
 - Pieces move on grid intersections only — no diagonal or mid-cell moves.
 - You cannot:
    - Enter or pass through the opponent’s Score Area.
    - Leave the board.
    - Stack two pieces on the same point.


### River Movement
 - If a piece steps onto a River, it may travel any number of spaces along that River’s flow direction.
 - Movement continues until:
    - Another Stone blocks the path, or
    - The board edge is reached.
 - Rivers (of both players) can be used for flow.
 - Landing on another River continues movement along the new River’s direction.
 - Movement cannot enter or cross the opponent’s Score Area.

### 💪 Pushing Rules
#### Pushing with a Stone
 - A Stone can push exactly one piece forward by one step if:
    - The next space is empty, on board, and not inside opponent’s SA.
 - Cannot push a chain of pieces.
 - Cannot push if doing so would move a piece off-board or into restricted area.

#### Pushing with a River
 - A River can push a Stone any number of spaces along one of its flow directions.
 - The pushed Stone must follow normal movement restrictions.
 - After pushing, the River flips into its Stone side.
 - You can push both your own and opponent’s Stones.
 - Push is invalid if it results in an identical board state to the previous turn.

### 🔄 Rotating & Flipping

####Rotate River (R):
 - Rotate one of your Rivers 90° (horizontal ↔ vertical). Cannot rotate by 180° or skip rotation.

#### Flip Piece (F):
 - Flip Stone → River, then choose H (horizontal) or V (vertical) orientation.
 - Flip River → Stone to turn it into a scoring piece.
 - Takes the entire turn.

### 1️⃣ Game Ending Conditions
A game ends when:
 - A player fills all SA slots (wins immediately), or
 - The timer expires for both → Draw, or
 - Both players reach the move cap (500 moves) → Draw, or
 - One player’s timer expires → Other player wins.

 
## Updates
[15-09-2025] Uploaded the sample files for the C++ users. Please checkout the [Read ME](./c++_sample_files/README.md) for further details. Seperate Submission details will be updated for C++ users.
[19-09-2025] Providing the Self and Opponents time left as an argument to the function from the Game Engine.

## Dependencies
- Python 3.9
- Pygame
- Numpy 
- Scipy


## Setting up the Environment
```sh
conda create --name stones_river python=3.9
conda activate stones_river
pip install -r requirements.txt
```

## Run Instructions
Here are the instructions used to match ai or human players against each other.


## Main Files
- `gameEngine.py`: It is an instance of the game. It can be run locally on your environment. You can run in GUI or CLI mode.
- `agent.py`: It consists of the implementations of the Random Agent. 
- `student_agent.py` : You need to implement your agent here. Some predefined function has been given.

Note: Details for running the C++ agent will be shared later. The same game will be used in the second phase in Assigment 5. And seperate details will be shared for the Assigment 5.

### Human vs Human
```sh
python gameEngine.py --mode hvh
```
### Human vs AI

```sh
python gameEngine.py --mode hvai --circle random
```
### AI vs AI

```sh
python gameEngine.py --mode aivai --circle random --square student
```

### No GUI
```sh
python gameEngine.py --mode aivai --circle random --square student --nogui
```
