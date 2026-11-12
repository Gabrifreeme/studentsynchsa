import io
path = r"C:\Users\chris\LipSyncStudent\lib\core\theme\app_theme.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

content = content.replace(
    "static const surface = Color(0xFF111111);",
    "static const surface = Color(0xFF000000);"
)
content = content.replace(
    "static const card = Color(0xFF111111);",
    "static const card = Color(0xFF000000);"
)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE: surface and card set to pure black")
