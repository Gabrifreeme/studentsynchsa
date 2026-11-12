import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify line 223 (0-indexed 222) is the Text(m.text)
assert "Text(" in lines[222] and "m.text" in lines[223], f"L223 mismatch: {lines[222]!r} {lines[223]!r}"

# Replace lines 223-229 (0-indexed 222-228) with conditional rendering
new_block = (
    "                                      if (m.text.startsWith('[FILE]'))" + eol +
    "                                        Row(" + eol +
    "                                          mainAxisSize: MainAxisSize.min," + eol +
    "                                          children: [" + eol +
    "                                            const Icon(Icons.insert_drive_file, color: AppColors.primary, size: 18)," + eol +
    "                                            const SizedBox(width: 6)," + eol +
    "                                            Text(m.text.replaceFirst('[FILE] ', ''), style: const TextStyle(color: AppColors.primary, fontSize: 13, fontWeight: FontWeight.bold))," + eol +
    "                                          ]," + eol +
    "                                        )" + eol +
    "                                      else if (m.text.startsWith('[AUDIO]'))" + eol +
    "                                        Row(" + eol +
    "                                          mainAxisSize: MainAxisSize.min," + eol +
    "                                          children: [" + eol +
    "                                            const Icon(Icons.audiotrack, color: AppColors.primary, size: 18)," + eol +
    "                                            const SizedBox(width: 6)," + eol +
    "                                            const Text('Voice message', style: TextStyle(color: AppColors.primary, fontSize: 13, fontWeight: FontWeight.bold))," + eol +
    "                                          ]," + eol +
    "                                        )" + eol +
    "                                      else" + eol +
    "                                        Text(" + eol +
    "                                          m.text," + eol +
    "                                          style: const TextStyle(" + eol +
    "                                            color: AppColors.primary," + eol +
    "                                            fontSize: 14," + eol +
    "                                          )," + eol +
    "                                        )," + eol
)

# Replace lines 223-229 (7 lines, 0-indexed 222-228) with new block
new_lines = lines[:222] + [new_block] + lines[229:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: file/audio rendering added")
