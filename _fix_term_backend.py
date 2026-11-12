p = r'C:\Users\chris\LipSyncStudent\server.py'
src = open(p, 'r', encoding='utf-8').read()

# Replace the entire terminal block with a more robust version
old_block = """@socketio.on('terminal_input')
def handle_terminal_input(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        terminal_process.write(data)

@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            terminal_process.setwinsize(int(data['rows']), int(data['cols']))
        except Exception:
            pass

@socketio.on('connect')
def handle_connect():
    global terminal_process
    if not terminal_process or not terminal_process.isalive():
        # Spawn PowerShell on Windows
        terminal_process = PtyProcess.spawn('powershell.exe')

        def read_output():
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

new_block = """@socketio.on('terminal_input')
def handle_terminal_input(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            terminal_process.write(data)
        except Exception as e:
            print(f'[terminal] input write error: {e}')

@socketio.on('terminal_resize')
def handle_terminal_resize(data):
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            terminal_process.setwinsize(int(data['rows']), int(data['cols']))
        except Exception as e:
            print(f'[terminal] resize error: {e}')

@socketio.on('connect')
def handle_connect():
    global terminal_process
    if not terminal_process or not terminal_process.isalive():
        try:
            # Spawn PowerShell on Windows
            terminal_process = PtyProcess.spawn('powershell.exe')
            print(f'[terminal] spawned pid {terminal_process.pid}')

            def read_output():
                global terminal_process
                while True:
                    try:
                        if not terminal_process or not terminal_process.isalive():
                            break
                        data = terminal_process.read(1024)
                        if data:
                            socketio.emit('terminal_output', data)
                    except EOFError:
                        print('[terminal] EOF from PTY')
                        break
                    except Exception as e:
                        print(f'[terminal] read error: {e}')
                        break
                print('[terminal] read thread ending')

            socketio.start_background_task(read_output)
        except Exception as e:
            print(f'[terminal] spawn error: {e}')

@socketio.on('disconnect')
def handle_disconnect():
    global terminal_process
    if terminal_process and terminal_process.isalive():
        try:
            terminal_process.terminate()
            print('[terminal] PTY terminated on disconnect')
        except Exception:
            pass
    terminal_process = None"""

if old_block in src:
    src = src.replace(old_block, new_block)
    open(p, 'w', encoding='utf-8').write(src)
    print("TERMINAL HANDLERS UPGRADED")
else:
    print("BLOCK NOT FOUND - CHECK MANUALLY")
