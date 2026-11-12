import io
print("=== FRONTEND (term.onData) ===")
with io.open(r"C:\Users\chris\LipSyncStudent\ACEsi.html", "r", encoding="utf-8") as f:
    lines = f.readlines()
for n in range(len(lines)):
    if "term.onData" in lines[n]:
        start = max(0, n-2)
        end = min(len(lines), n+10)
        for i in range(start, end):
            print(f"{i+1:5}: |{lines[i].rstrip()}|")
        break

print("\n=== BACKEND (terminal_input) ===")
with io.open(r"C:\Users\chris\LipSyncStudent\server.py", "r", encoding="utf-8") as f:
    lines = f.readlines()
for n in range(len(lines)):
    if "def handle_terminal_input" in lines[n]:
        start = max(0, n-2)
        end = min(len(lines), n+20)
        for i in range(start, end):
            print(f"{i+1:5}: |{lines[i].rstrip()}|")
        break
