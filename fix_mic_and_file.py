import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    content = f.read()

# 1. FIX MIC: Remove Directory.systemTemp (web incompatible), use record's own path
old_mic = """      try {
        if (await _recorder.hasPermission()) {
          final dir = Directory.systemTemp;
          final path = '${dir.path}/ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
          await _recorder.start(const RecordConfig(), path: path);
          _recordingStart = DateTime.now();
          setState(() => _isRecording = true);
        } else {"""

new_mic = """      try {
        if (await _recorder.hasPermission()) {
          final path = kIsWeb
              ? 'ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a'
              : '${Directory.systemTemp.path}/ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
          await _recorder.start(const RecordConfig(), path: path);
          _recordingStart = DateTime.now();
          setState(() => _isRecording = true);
        } else {"""

if old_mic in content:
    content = content.replace(old_mic, new_mic)
    print("MIC: Fixed for web (no Directory.systemTemp)")
else:
    print("MIC: Pattern not found")

# 2. FIX FILE RENDERING: replace the message bubble builder with file/audio detection
old_bubble = """                                      Text(
                                        m.text,
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 14,
                                        ),
                                      ),"""

new_bubble = """                                      if (m.text.startsWith('[FILE]'))
                                        Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            const Icon(Icons.insert_drive_file,
                                                color: AppColors.primary, size: 18),
                                            const SizedBox(width: 6),
                                            Text(
                                              m.text.replaceFirst('[FILE] ', ''),
                                              style: const TextStyle(
                                                color: AppColors.primary,
                                                fontSize: 13,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ],
                                        )
                                      else if (m.text.startsWith('[AUDIO]'))
                                        Row(
                                          mainAxisSize: MainAxisSize.min,
                                          children: [
                                            const Icon(Icons.audiotrack,
                                                color: AppColors.primary, size: 18),
                                            const SizedBox(width: 6),
                                            Text(
                                              'Voice message',
                                              style: const TextStyle(
                                                color: AppColors.primary,
                                                fontSize: 13,
                                                fontWeight: FontWeight.bold,
                                              ),
                                            ),
                                          ],
                                        )
                                      else
                                        Text(
                                          m.text,
                                          style: const TextStyle(
                                            color: AppColors.primary,
                                            fontSize: 14,
                                          ),
                                        ),"""

if old_bubble in content:
    content = content.replace(old_bubble, new_bubble)
    print("BUBBLE: Added file/audio rendering with icons")
else:
    print("BUBBLE: Pattern not found")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("PATCH COMPLETE")
