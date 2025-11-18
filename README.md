# Terminal Chess — Python Client

Simple Python CLI client for the Terminal Chess server. Connects over TCP, registers a name, displays the board (colored Unicode by default), and allows typing moves.

Usage

Install (optional virtualenv) and dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the client (defaults to localhost:5000):

```bash
python3 client.py --host localhost --port 5000 --name Alice
```

Interactive commands
- To make a move: either type MOVE e2e4 or just e2e4
- To quit: type QUIT or press Ctrl+C
- Display controls (local only, not sent to server):
	- `ASCII` switch to plain server board output
	- `UNICODE` switch back to colored Unicode board
	- `REDRAW` re-print last received board

The client prints server messages such as START, BOARD, YOURMOVE, OPPONENT_MOVE, OK, ERROR, END, ROOM, ROOM_EXPIRED, CANCELLED, and QUEUE.
