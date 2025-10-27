# Kung Fu Chess 
A fast, keyboard‑driven **“Kung Fu Chess”** engine and UI implemented in Python.  
Unlike classic turn-based chess, **pieces can move concurrently**, each following its own **movement delay** and physics rules.
This means that after making a move, each piece must wait a short, individual recovery period before it can move again — creating a real-time flow instead of alternating turns.
Rendering is done with **OpenCV**, sound effects with **pygame**, and the system is built around a **clean, testable architecture** (commands, states, physics, graphics, pub/sub events).

---

## Highlights

- **Real‑time, simultaneous moves** with per‑piece cooldowns and motion.
- **Keyboard‑first gameplay**: select pieces and issue actions using configurable keymaps.
- **OpenCV graphics** with sprite animations (per‑piece states and frames).
- **Sound effects** (move / capture / start / end) via `pygame`.
- **Event‑driven design** using a lightweight message broker and typed events.
- **Command history & scoring**: per‑player move logs, scores by captured piece values, and a summary table.
- **Extensive tests** (`pytest`) with headless rendering and sound mocks for CI‑friendly runs.
- **Animation utilities** to prepare sprite sheets and remove green screens.

---

## Repository Structure

```
.
├── setup.py
├── constants.py                 # Global timing/speed constants
├── KFC_Py/
│   ├── main.py                  # Entry point (runs a full local game)
│   ├── Game.py                  # Game loop: input → update → draw → resolve
│   ├── GameFactory.py           # Wiring: board, pieces, UI, sounds, history
│   ├── GameUI.py                # OpenCV-based UI composition & overlays
│   ├── Board.py                 # Board geometry, px↔m and cell conversions
│   ├── Piece.py                 # Piece wrapper (State + Physics + Graphics)
│   ├── State.py                 # State machine glue (moves/graphics/physics)
│   ├── Physics.py               # Physics strategies (static, moving, rest)
│   ├── Graphics.py              # Sprite loading & frame animation
│   ├── GraphicsFactory.py       # Injection for real vs mock image loaders
│   ├── KeyboardInput.py         # Key handling, cursoring, selection, actions
│   ├── Moves.py                 # Move parsing & rule checks, path clearance
│   ├── Command.py               # Command object (timestamp, piece, action,…)
│   ├── CommandHistoryManager.py # Per‑player history + formatting
│   ├── GameHistoryDisplay.py    # Dual‑history + UI integration & summary
│   ├── ScoreManager.py          # Score bookkeeping using capture values
│   ├── SoundManager.py          # Event‑driven SFX with pygame
│   ├── MessageBroker.py         # Publish/subscribe bus
│   ├── EventType.py             # Strongly‑typed events
│   ├── PlayerNamesManager.py    # Simple name input overlay
│   ├── img.py / mock_img.py     # OpenCV image ops and a headless mock
│   └── Tests/                   # 30+ pytest files (unit + integration)
├── KFC_AnimationUtils/          # Scripts for sprite prep & green‑screen
└── pieces/                      # Assets: sprites, states/, sounds/, board.*
```

---

## Installation

> Python **3.10+** is recommended. On Windows, `keyboard` may require admin privileges for global hotkeys.

### 1) Create & activate a virtual environment

```bash
python -m venv .venv
# Windows
. .venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -e .
# or explicitly:
pip install numpy keyboard pytest pytest-cov pygame opencv-python
```

> If you do not need sound, you can skip `pygame` or let tests mock it automatically.

---

## Quick Start

Run the game locally (windowed OpenCV UI):

```bash
python -m KFC_Py.main
```

- **Exit**: press `ESC` while the window is focused.
- On first run, you will be prompted for **player names** (use `ENTER` to confirm, `ESC` for defaults).
- Sprites and sounds are loaded from the `pieces/` directory by default.

---

## Controls (Default)

The keyboard processor keeps a **cursor** on the board:
- **Arrow keys / WASD**: move the cursor over cells.
- **Select**: choose a piece on the cursor cell.
- **Move / Jump / Action**: dispatch a `Command` for that piece.
- The exact mapping is defined in `KeyboardInput.py` and can be adapted.

> Internally, input is turned into `Command` objects (with timestamps) and pushed onto a thread‑safe queue the game loop consumes.

---

## Game Loop & Architecture

The loop in `Game.run()` advances the simulation in phases:

1. **Update states** – each `Piece.state` ticks:
   - `Physics.update(now_ms)` (movement, cooldowns, “done” events)
   - `Graphics.update(now_ms)` (frame selection)
2. **Consume input** – dequeue `Command` objects and pass to the relevant `Piece` via `State.on_command(...)`.
3. **Render** – draw board and pieces (`Graphics.get_img()` → `Img.draw_on(...)`), overlay messages and history.
4. **Resolve collisions** – capture logic, score updates, event publishing.

### Key Modules

- **State / Physics / Graphics**: a clean separation of concerns for behavior, motion, and visuals.
- **Moves**: parses move rules and performs **path clearance** checks against `cell2piece` maps.
- **MessageBroker / EventType**: decoupled pub/sub. `ScoreManager`, `MessageDisplay`, and history subscribers react to events like `PIECE_MOVED`, `PIECE_CAPTURED`.
- **CommandHistoryManager / GameHistoryDisplay**: per‑player logs, pretty tables, and end‑of‑game summaries.
- **GraphicsFactory & Img**: injectable image loader so tests can run **headless** with `MockImg`.

A simplified class/flow view:

```
Keyboard → Command → Game.queue
   └─> Game.run(): update → draw → show → resolve
        ├─ Pieces[State(Physics, Graphics)]
        ├─ MessageBroker.publish(EventType, data)
        └─ UI overlays (history, names, messages)
```

---

## Assets

- **`pieces/`** contains per‑piece folders with `states/` (sprite frames), a `board.*` image, and **sounds** under `pieces/sound/`.
- Modify frame rate, looping, and other animation settings via `Graphics` arguments (see `GraphicsFactory`).

Utilities under **`KFC_AnimationUtils/`** can help convert video frames to sprite sequences and remove green backgrounds.

---

## Configuration

Global timing and speeds are centralized in [`constants.py`](constants.py):

```python
SHORT_REST_MS = 5000
LONG_REST_MS  = 10000
SPEED_M_PER_SEC_LONG  = 1.5
SPEED_M_PER_SEC_SHORT = 1.0
```

Board cell sizes and pixel→meter scaling are configured in `GameFactory.py` via `CELL_PX` and `Board(...)` construction.  

---

## Testing

Run the full suite (mocks make it safe for CI/headless servers):

```bash
pytest -q
```

Notes:
- Tests **mock** `pygame`, `cv2`, and GUI input where appropriate.
- Integration tests simulate end‑to‑end runs without opening windows.
- See `KFC_Py/Tests/` for examples of injecting `MockImg` and verifying trajectories and history.

---

## Troubleshooting

- **Windows + `keyboard`**: global hooks may require running the shell as **Administrator**.
- **OpenCV window not closing**: press **ESC** in the game window; we raise a `KeyboardInterrupt` to exit cleanly.
- **No sound**: ensure `pygame.mixer` is initialized; in CI/tests, sound is mocked automatically.
- **Assets not found**: verify the working directory so `pieces/` is discovered by `GameFactory.create_game(...)`.
