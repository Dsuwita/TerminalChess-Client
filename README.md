# Terminal Chess Client

Interactive Python CLI client for Terminal Chess with Unicode pieces, colored board rendering, and algebraic notation support.

## Features

- **Interactive Prompts**: No command-line arguments needed - just run and play
- **Unicode Chess Pieces**: Beautiful colored rendering with piece symbols
- **Smart Board Display**: Auto-flips for black player, clears screen between moves
- **Algebraic Notation**: Type `e4` instead of `e2e4`, or full notation like `Nb1c3`
- **Game Modes**: Quick match, private rooms, or join by key
- **Forfeit Support**: Type `ff` to concede
- **Display Toggles**: Switch between ASCII/Unicode, redraw board anytime

## Quick Start

### Prerequisites
- Python 3.7+
- Optional: `colorama` for colored output (auto-detected)

### Install Dependencies (Optional)
```bash
pip install -r requirements.txt
```

### Run
```bash
python3 client.py
```

## Usage

1. **Enter your name** when prompted
2. **Choose game mode**:
   - `1` - Quick match (auto-pair)
   - `2` - Create private room
   - `3` - Join room by key
3. **Play**: Type moves like `e4`, `e2e4`, or `Nb1c3`
4. **Commands**:
   - `ff` or `forfeit` - Concede game
   - `ascii` - Switch to plain text board
   - `unicode` - Switch to colored Unicode
   - `redraw` - Refresh current board
   - `quit` - Exit

## Move Notation

### Pawn Moves
- `e4` → automatically expands to `e2e4`
- `d5` → automatically expands to `d7d5` (for black)

### Piece Moves
- Full notation: `Nb1c3` (knight from b1 to c3)
- Coordinate: `e2e4` (always works)

### Special
- Captures: `exd5` or just `e4d5`
- Promotions: Automatic to queen

## Display

- **White player**: Rank 8 at top, rank 1 at bottom
- **Black player**: Board flips - rank 1 at top, rank 8 at bottom
- **Empty squares**: Blank spaces with alternating colors
- **Pieces**: Unicode symbols (♔♕♖♗♘♙)

## Connecting to Custom Server

Edit `host` variable in `client.py`:
```python
host = "your.server.ip"  # Default: 209.38.75.155
port = 5000
```

## Requirements

- Python 3.7+
- `colorama` (optional, for colors)

## Server Protocol

Communicates via TCP text protocol. See [server repository](https://github.com/yourusername/terminalChess-server) for protocol details.

## License

MIT
