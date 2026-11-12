import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Remove the star emoji (and its preceding space) from the greeting
content = content.replace("I'm ACEsi \u2b50", "I'm ACEsi")
# Also handle the encoding-mangled variant that sometimes appears
content = content.replace("I'm ACEsi â­", "I'm ACEsi")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE: removed star emoji from greeting")
