import io
path = r"C:\Users\chris\LipSyncStudent\Launch.ps1"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Replace the Start-Process command with one that redirects output to a log file
old = "Start-Process powershell -ArgumentList '-WindowStyle', 'Hidden', '-Command', 'cd C:\\Users\\chris\\LipSyncStudent; python server.py'"
new = "Start-Process powershell -ArgumentList '-WindowStyle', 'Hidden', '-Command', 'cd C:\\Users\\chris\\LipSyncStudent; python server.py *> server.log'"

if old in content:
    content = content.replace(old, new)
    print("LAUNCH.PS1: Redirected server output to server.log")
else:
    print("LAUNCH.PS1: WARNING - Could not find the exact Start-Process line")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)
print("PATCH COMPLETE")
