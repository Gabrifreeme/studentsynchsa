import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()
for n, l in enumerate(lines):
    if "openAceTerminal" in l and "function" in l:
        start = max(0, n - 2)
        end = min(len(lines), n + 25)
        for i in range(start, end):
            print(f"{i+1:5}: |{lines[i].rstrip()}|")
        print("---")
