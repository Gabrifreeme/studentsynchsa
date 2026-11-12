import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Replace Star references with ACEsi
content = content.replace("Star is working on it", "ACEsi is working on it")
content = content.replace("Star is", "ACEsi is")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE: Community Chat text - Star -> ACEsi")
