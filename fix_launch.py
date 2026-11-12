import io
path = r"C:\Users\chris\LipSyncStudent\Launch.ps1"
content = r"""# Start the Flask server in the background
Start-Process powershell -ArgumentList '-WindowStyle', 'Hidden', '-Command', 'cd C:\Users\chris\LipSyncStudent; python server.py *> server.log'

# Wait 6 seconds for the server to fully boot
Start-Sleep -Seconds 6

# Launch the desktop app window (pywebview) pointing to the Chat UI
python -c "import webview; webview.create_window('ACESi', 'http://127.0.0.1:5000/', width=1200, height=800); webview.start()"
"""
with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)
print("RESTORED: Launch.ps1 with log redirection")
