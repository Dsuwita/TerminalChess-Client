#!/usr/bin/env python3
"""Terminal Chess Python client

Connects to the Java server, registers a name, prints incoming server messages,
displays BOARD blocks, and allows sending MOVE commands.
"""
import socket
import threading
import sys
import os

try:
    from colorama import Fore, Back, Style, init as colorama_init
    colorama_init()
except Exception:
    class Dummy:
        def __getattr__(self, name):
            return ""
    Fore = Back = Style = Dummy()

UNICODE_MAP = {
    'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
    'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
}

def parse_algebraic(move_str):
    """Convert algebraic notation like Nc3 or Nbd7 to coordinate notation like b1c3 or b8d7.
    Returns coordinate string or None if unparseable."""
    move_str = move_str.strip()
    if not move_str:
        return None
    
    # Already coordinate notation (e2e4)
    if len(move_str) >= 4 and move_str[0] in 'abcdefgh' and move_str[1] in '12345678' and move_str[2] in 'abcdefgh':
        return move_str
    
    # Remove capture notation and check/mate symbols
    move_str = move_str.replace('x', '').replace('+', '').replace('#', '').replace('=Q', '').replace('=R', '').replace('=B', '').replace('=N', '')
    
    # Pawn moves: e4 or e2e4
    if len(move_str) == 2 and move_str[0] in 'abcdefgh' and move_str[1] in '12345678':
        file = move_str[0]
        dest_rank = move_str[1]
        start_rank = '2' if dest_rank in '34' else '7' if dest_rank in '56' else '2'
        return f"{file}{start_rank}{file}{dest_rank}"
    
    # Piece moves: Nc3, Nbd7, Nb1d7, etc.
    piece_chars = {'K': 'king', 'Q': 'queen', 'R': 'rook', 'B': 'bishop', 'N': 'knight'}
    if move_str[0].upper() in piece_chars:
        piece = move_str[0].upper()
        rest = move_str[1:]
        
        # Extract destination (last 2 chars should be file+rank)
        if len(rest) >= 2 and rest[-2] in 'abcdefgh' and rest[-1] in '12345678':
            dest = rest[-2:]
            disambig = rest[:-2] if len(rest) > 2 else ''
            
            # If we have full disambiguation (like b1 in Nb1c3)
            if len(disambig) == 2 and disambig[0] in 'abcdefgh' and disambig[1] in '12345678':
                return disambig + dest
            
            # Partial disambiguation or none - we can't determine source without board state
            # For now, return None and let server handle or user use full notation
            return None
    
    return None

def render_board(ascii_lines, use_unicode=True, colorize=True, flip=False):
    """Render the BOARD block with optional unicode and colored squares.
    Expects ascii_lines including rank lines and the final file-label line.
    flip: if True, render from black's perspective (rank 1 at top)
    Returns a string ready to print."""
    out_lines = []
    
    # Separate board lines from file labels
    board_rows = ascii_lines[:-1] if len(ascii_lines) == 9 else ascii_lines
    file_labels = ascii_lines[-1] if len(ascii_lines) == 9 else '  a b c d e f g h'
    
    # Reverse if viewing from black's perspective
    if flip:
        board_rows = list(reversed(board_rows))
    
    for raw in board_rows:
        parts = raw.split()
        if len(parts) < 9:
            out_lines.append(raw)  # fallback
            continue
        rank = parts[0]
        pieces = parts[1:]
        
        # Reverse pieces if flipped
        if flip:
            pieces = list(reversed(pieces))
        
        rendered_row = []
        for file_index, piece in enumerate(pieces):
            # Determine square color (a1 dark). Our ranks are top to bottom; convert rank to int.
            # Dark if (file_index + rank_number) % 2 == 1
            try:
                rank_num = int(rank)
            except ValueError:
                rank_num = 0
            
            # Adjust file_index if flipped for correct coloring
            actual_file = (7 - file_index) if flip else file_index
            dark = (actual_file + rank_num) % 2 == 1
            cell_bg = Back.BLUE if dark else Back.WHITE if colorize else ''
            fg = Fore.YELLOW if piece.islower() else Fore.BLACK if piece != '.' else Fore.GREEN
            symbol = piece
            if use_unicode and piece in UNICODE_MAP:
                symbol = UNICODE_MAP[piece]
            elif piece == '.':
                symbol = ' '  # Empty space instead of dot
            cell = f"{cell_bg}{fg} {symbol} {Style.RESET_ALL if colorize else ''}" if colorize else f" {symbol} "
            rendered_row.append(cell)
        out_lines.append(rank + ' ' + ''.join(rendered_row))
    
    # Add file labels (reversed if flipped)
    if flip:
        out_lines.append('  h g f e d c b a')
    else:
        out_lines.append(file_labels if file_labels.strip() else '  a b c d e f g h')
    
    return '\n'.join(out_lines)


def read_loop(sock_file, stop_event, name, state):
    """Read lines from server and print, handling BOARD blocks."""
    try:
        while not stop_event.is_set():
            line = sock_file.readline()
            if not line:
                print(Fore.YELLOW + "[connection closed by server]" + Style.RESET_ALL)
                stop_event.set()
                break
            line = line.rstrip("\n\r")
            if line == "BOARD":
                # Clear screen before showing board
                os.system('clear' if os.name != 'nt' else 'cls')
                
                # read next 9 lines (8 ranks + file labels)
                board_lines = []
                for _ in range(9):
                    l = sock_file.readline()
                    if not l:
                        break
                    board_lines.append(l.rstrip("\n\r"))
                
                # Determine if we should flip (we're black)
                flip = state.get('player_color') == 'BLACK'
                
                if state['ascii_only']:
                    rendered = '\n'.join(board_lines)
                else:
                    rendered = render_board(board_lines, use_unicode=True, colorize=True, flip=flip)
                state['last_board'] = rendered
                print(rendered)
                continue
            if line.startswith("ROOM "):
                key = line.split(" ", 1)[1]
                print(Fore.CYAN + "\n[room created]" + Style.RESET_ALL)
                print(Fore.CYAN + f"  key: {key}" + Style.RESET_ALL)
                print(Fore.CYAN + f"  share with: python3 client.py --name <yourname> --room {key}\n" + Style.RESET_ALL)
                continue
            if line.startswith("QUEUE "):
                print(Fore.YELLOW + "[queued]" + Style.RESET_ALL, line[6:])
                continue
            if line.startswith("ROOM_EXPIRED "):
                key = line.split(" ", 1)[1]
                print(Fore.YELLOW + f"[room expired] {key}" + Style.RESET_ALL)
                continue
            if line.startswith("CANCELLED "):
                key = line.split(" ", 1)[1]
                print(Fore.YELLOW + f"[room cancelled] {key}" + Style.RESET_ALL)
                continue
            # print other messages with small formatting
            if line.startswith("START "):
                # Extract color (START WHITE opponent or START BLACK opponent)
                parts = line.split()
                if len(parts) >= 2:
                    state['player_color'] = parts[1].upper()
                print(Fore.CYAN + "[match started]" + Style.RESET_ALL, line)
            elif line == "YOURMOVE":
                print(Fore.GREEN + "[your move]" + Style.RESET_ALL)
            elif line.startswith("OPPONENT_MOVE "):
                print(Fore.MAGENTA + "[opponent]" + Style.RESET_ALL, line[len("OPPONENT_MOVE "):])
            elif line.startswith("ERROR "):
                print(Fore.RED + "[error]" + Style.RESET_ALL, line[len("ERROR "):])
            elif line.startswith("END "):
                print(Fore.YELLOW + "[game ended]" + Style.RESET_ALL, line[len("END "):])
                # do not exit immediately; let user decide
            else:
                print(line)
    except Exception as e:
        if not stop_event.is_set():
            print(Fore.RED + "[read loop error]" + Style.RESET_ALL, e)
            stop_event.set()


def main():
    print(Fore.CYAN + "=== Terminal Chess ===" + Style.RESET_ALL)
    
    # Get player name
    name = input("Enter your name: ").strip()
    if not name:
        name = "Player"
    
    # Ask game mode
    print("\n" + Fore.YELLOW + "Game modes:" + Style.RESET_ALL)
    print("  1. Quick match (auto-pair with waiting player)")
    print("  2. Create private room")
    print("  3. Join private room")
    print("  4. Play against computer")
    
    mode = input("Choose mode (1/2/3/4) [1]: ").strip()
    if not mode:
        mode = "1"
    
    room_key = None
    create_room = None
    play_computer = False
    
    if mode == "2":
        custom_key = input("Enter room key (leave empty for random): ").strip()
        create_room = custom_key if custom_key else 'auto'
    elif mode == "3":
        room_key = input("Enter room key: ").strip()
        if not room_key:
            print(Fore.RED + "Room key required!" + Style.RESET_ALL)
            sys.exit(1)
    elif mode == "4":
        play_computer = True
    
    print("\n" + Fore.GREEN + "Connecting to server..." + Style.RESET_ALL)
    
    host = "localhost"
    port = 5000
    stop_event = threading.Event()

    try:
        s = socket.create_connection((host, port))
    except Exception as e:
        print(Fore.RED + "Failed to connect:" + Style.RESET_ALL, e)
        sys.exit(1)

    sock_file = s.makefile("r")
    sock_out = s.makefile("w")

    # start reader thread
    state = {'last_board': None, 'ascii_only': False}
    reader = threading.Thread(target=read_loop, args=(sock_file, stop_event, name, state), daemon=True)
    reader.start()

    # send name registration
    sock_out.write(f"NAME {name}\n")
    sock_out.flush()

    # send game mode command
    if room_key:
        sock_out.write(f"JOIN {room_key}\n")
        sock_out.flush()
    elif create_room:
        if create_room == 'auto':
            sock_out.write("CREATE\n")
        else:
            sock_out.write(f"CREATE {create_room}\n")
        sock_out.flush()
    elif play_computer:
        sock_out.write("COMPUTER\n")
        sock_out.flush()
    else:
        sock_out.write("FIND\n")
        sock_out.flush()

    try:
        while not stop_event.is_set():
            try:
                line = input().strip()
            except EOFError:
                break
            if not line:
                continue
            cmd = line
            if line.lower() in ("quit", "exit"):
                break
            if line.lower() in ('ff', 'forfeit'):
                cmd = 'FF'
            elif line.lower() == 'ascii':
                state['ascii_only'] = True
                print(Fore.YELLOW + '[display] switched to plain ASCII' + Style.RESET_ALL)
                if state['last_board']:
                    print(state['last_board'].replace('\x1b', ''))  # crude strip if colored
                continue
            if line.lower() == 'unicode':
                state['ascii_only'] = False
                print(Fore.YELLOW + '[display] switched to colored unicode' + Style.RESET_ALL)
                if state['last_board']:
                    # re-render from stored ascii? We only stored rendered version; skip
                    print(state['last_board'])
                continue
            if line.lower() == 'redraw':
                if state['last_board']:
                    print(state['last_board'])
                else:
                    print('[no board yet]')
                continue
            if not (line.upper().startswith("MOVE ") or line.upper().startswith("NAME ") or line.upper() == 'FF'):
                # Try to parse as algebraic or coordinate notation
                parsed = parse_algebraic(line)
                if parsed:
                    cmd = f"MOVE {parsed}"
                else:
                    # If can't parse and looks like a move attempt, send as-is and let server reject
                    if any(c in line.lower() for c in 'abcdefgh12345678'):
                        print(Fore.YELLOW + "[hint] Use full notation: e2e4 or with piece: Nb1c3" + Style.RESET_ALL)
            # send command
            try:
                sock_out.write(cmd + "\n")
                sock_out.flush()
            except Exception as e:
                print(Fore.RED + "Send failed:" + Style.RESET_ALL, e)
                break

    except KeyboardInterrupt:
        pass
    finally:
        stop_event.set()
        try:
            sock_out.write("QUIT\n")
            sock_out.flush()
        except Exception:
            pass
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        s.close()


if __name__ == "__main__":
    main()
