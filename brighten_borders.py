import io
path = r"C:\Users\chris\LipSyncStudent\lib\core\theme\app_theme.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# Brighten divider
content = content.replace(
    "static const divider = Color(0xFF333333);",
    "static const divider = Color(0xFFFF9D00);"
)

# Make sure border is full amber (already is, but double-check)
content = content.replace(
    "static const border = Color(0xFFFF9D00);",
    "static const border = Color(0xFFFF9D00);"
)

# Increase divider thickness from 1 to 1
content = content.replace(
    "dividerTheme: const DividerThemeData(\n        color: AppColors.divider,\n        thickness: 1,\n      ),",
    "dividerTheme: const DividerThemeData(\n        color: AppColors.primary,\n        thickness: 1,\n      ),"
)

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE: Brightened dividers to amber")
