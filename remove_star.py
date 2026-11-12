import io

files = [
    r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart",
    r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\profile\profile_onboarding_screen.dart",
]

for path in files:
    with io.open(path, "r", encoding="utf-8", newline="") as f:
        content = f.read()
    original = content
    # Remove the star emoji (and any trailing space) after ACEsi
    content = content.replace("I'm ACEsi ⭐", "I'm ACEsi")
    content = content.replace("I'm ACEsi \u2b50", "I'm ACEsi")
    if content != original:
        with io.open(path, "w", encoding="utf-8", newline="") as f:
            f.write(content)
        print(f"UPDATED: {path.split(chr(92))[-1]}")
    else:
        print(f"SKIPPED: {path.split(chr(92))[-1]}")

print("PATCH COMPLETE")
