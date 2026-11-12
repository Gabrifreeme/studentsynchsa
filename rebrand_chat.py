import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\ai_recommendations\ai_recommendations_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# 1. Rename all Star -> ACEsi
content = content.replace("I'm Star", "I'm ACEsi")
content = content.replace("'Ask Star anything...'", "'Ask ACEsi anything...'")
content = content.replace("Text('Star')", "Text('ACEsi')")
content = content.replace("You are Star, a friendly", "You are ACEsi, a friendly")
content = content.replace("_ChatMessage(text: '', isUser: false)", "_ChatMessage(text: '', isUser: false)")
content = content.replace("starMsg", "acesiMsg")

# 2. Replace GradientBackground wrapper with plain black Container
old_wrapper = """    return GradientBackground(
      child: Scaffold(
        backgroundColor: Colors.transparent,"""

new_wrapper = """    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,"""

if old_wrapper in content:
    content = content.replace(old_wrapper, new_wrapper)
    print("WRAPPER: GradientBackground -> black Container")
else:
    print("WRAPPER: pattern not found (may have subtle whitespace)")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
