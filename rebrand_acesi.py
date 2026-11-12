import io

# File 1: ai_recommendations_screen.dart
path1 = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"
with io.open(path1, "r", encoding="utf-8", newline="") as f:
    content1 = f.read()

if "Hi there! I'm Star" in content1:
    content1 = content1.replace("Hi there! I'm Star", "Hi there! I'm ACEsi")
    with io.open(path1, "w", encoding="utf-8", newline="") as f:
        f.write(content1)
    print("FILE 1: ai_recommendations_screen.dart - updated")
else:
    print("FILE 1: already updated or pattern not found")

# File 2: profile_onboarding_screen.dart
path2 = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\profile\profile_onboarding_screen.dart"
with io.open(path2, "r", encoding="utf-8", newline="") as f:
    content2 = f.read()

if "Hi there! I'm Star" in content2:
    content2 = content2.replace("Hi there! I'm Star", "Hi there! I'm ACEsi")
    with io.open(path2, "w", encoding="utf-8", newline="") as f:
        f.write(content2)
    print("FILE 2: profile_onboarding_screen.dart - updated")
else:
    print("FILE 2: already updated or pattern not found")

print("PATCH COMPLETE")
