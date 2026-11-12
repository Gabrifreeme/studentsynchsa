import io
path = r"C:\Users\chris\LipSyncStudent\server.py"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

# Find the heartbeat loop that sends to the terminal (look for "frames = ")
heartbeat_idx = None
for i, line in enumerate(lines):
    if "frames = " in line and "|" in line:
        heartbeat_idx = i
        break

if heartbeat_idx is None:
    print("Could not find heartbeat frames line")
else:
    eol = "\r\n" if lines[heartbeat_idx].endswith("\r\n") else "\n"
    
    # Print out the 20 lines around it so we can see what it is doing
    for n in range(heartbeat_idx - 5, heartbeat_idx + 15):
        if n < len(lines):
            print(f"{n+1:5}: |{lines[n].rstrip()}|")

print("INSPECT COMPLETE")
