import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Verify (0-indexed 89-95 = lines 90-96)
assert "FilePicker.pickFiles()" in lines[89], f"L90 mismatch: {lines[89]!r}"
assert "_sendMessage(tag)" in lines[95], f"L96 mismatch: {lines[95]!r}"

new_block = (
    "      final result = await FilePicker.pickFiles(withData: true);" + eol +
    "      if (result.isEmpty) return;" + eol +
    "      final file = result.first;" + eol +
    "      final fileName = file.name;" + eol +
    "      final bytes = file.bytes;" + eol +
    "      String? base64Data;" + eol +
    "      String? mimeType;" + eol +
    "      if (bytes != null) {" + eol +
    "        base64Data = base64Encode(bytes);" + eol +
    "        final ext = fileName.split('.').last.toLowerCase();" + eol +
    "        mimeType = ext == 'png' ? 'image/png'" + eol +
    "            : ext == 'jpg' || ext == 'jpeg' ? 'image/jpeg'" + eol +
    "            : ext == 'pdf' ? 'application/pdf'" + eol +
    "            : ext == 'txt' ? 'text/plain'" + eol +
    "            : 'application/octet-stream';" + eol +
    "      }" + eol +
    "      final message = ChatMessage(" + eol +
    "        id: const Uuid().v4()," + eol +
    "        room: widget.room," + eol +
    "        sender: 'You'," + eol +
    "        text: '[FILE] ' + fileName," + eol +
    "        timestamp: DateTime.now()," + eol +
    "        fileData: base64Data," + eol +
    "        mimeType: mimeType," + eol +
    "      );" + eol +
    "      await ChatStorage.addMessage(message);" + eol +
    "      _controller.clear();" + eol +
    "      if (!mounted) return;" + eol +
    "      setState(() => _messages = [..._messages, message]);" + eol +
    "      _scrollToBottom();" + eol
)

# Replace lines 90-96 (7 lines, 0-indexed 89-95)
new_lines = lines[:89] + [new_block] + lines[96:]

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(new_lines)

print("SPLICE OK: _pickFile rewritten with bytes storage")
