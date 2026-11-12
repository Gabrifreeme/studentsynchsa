p = r'C:\Users\chris\LipSyncStudent\server.py'
src = open(p, 'r', encoding='utf-8').read()

old = """        def read_output():
            while terminal_process.isalive():
                try:
                    data = terminal_process.read(1024)
                    if data:
                        socketio.emit('terminal_output', data)
                except EOFError:
                    break
                except Exception:
                    break

        socketio.start_background_task(read_output)"""

new = """        def read_output():
            print("[terminal] read thread started")
            while True:
                try:
                    if not terminal_process or not terminal_process.isalive():
                        print("[terminal] PTY is not alive, exiting")
                        break
                    data = terminal_process.read(1024)
                    if data:
                        print(f"[terminal] read {len(data)} bytes")
                        socketio.emit('terminal_output', data)
                except EOFError:
                    print("[terminal] EOF")
                    break
                except Exception as e:
                    print(f"[terminal] read error: {e}")
                    break
            print("[terminal] read thread ended")

        socketio.start_background_task(read_output)"""

if old in src:
    src = src.replace(old, new)
    open(p, 'w', encoding='utf-8').write(src)
    print("DEBUG LOGGING ADDED")
else:
    print("BLOCK NOT FOUND")
