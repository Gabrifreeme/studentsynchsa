import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (1-indexed 273-275 -> 0-indexed 272-274)
assert "base64Decode(m.fileData!)" in lines[272], f"L273 mismatch: {lines[272]!r}"
assert "Uri.dataFromBytes" in lines[273], f"L274 mismatch: {lines[273]!r}"
assert "launchUrl" in lines[274], f"L275 mismatch: {lines[274]!r}"

new_block = (
    "                                                final bytes = base64Decode(m.fileData!);" + eol +
    "                                                final fileName = m.text.replaceFirst('[FILE] ', '');" + eol +
    "                                                final mime = m.mimeType ?? 'application/octet-stream';" + eol +
    "                                                await saveFileOnPlatform(bytes, fileName, mime);" + eol
)

# Replace lines 273-275 (0-indexed 272-274)
new_lines = lines[:272] + [new_block] + lines[275:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: download handler uses saveFileOnPlatform")
