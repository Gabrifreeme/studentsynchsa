import io
path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"

with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()

eol = "\r\n" if lines[0].endswith("\r\n") else "\n"

# Find the file rendering block (starts with if (m.text.startsWith('[FILE]')))
for i, line in enumerate(lines):
    if "m.text.startsWith('[FILE]')" in line:
        start_idx = i
        break
else:
    print("WARNING: Could not find FILE rendering")
    start_idx = None

if start_idx is not None:
    # Find the closing of the Row (search for "],\n" then ")" then "else")
    end_idx = start_idx
    for i in range(start_idx, start_idx + 20):
        if "else if (m.text.startsWith('[AUDIO]'))" in lines[i]:
            end_idx = i
            break

    # Replace the Row with one that has an open button
    new_block = (
        "                                      if (m.text.startsWith('[FILE]'))" + eol +
        "                                        Row(" + eol +
        "                                          mainAxisSize: MainAxisSize.min," + eol +
        "                                          children: [" + eol +
        "                                            const Icon(Icons.insert_drive_file, color: AppColors.primary, size: 18)," + eol +
        "                                            const SizedBox(width: 6)," + eol +
        "                                            Flexible(" + eol +
        "                                              child: Text(" + eol +
        "                                                m.text.replaceFirst('[FILE] ', '')," + eol +
        "                                                style: const TextStyle(color: AppColors.primary, fontSize: 13, fontWeight: FontWeight.bold)," + eol +
        "                                                overflow: TextOverflow.ellipsis," + eol +
        "                                              )," + eol +
        "                                            )," + eol +
        "                                            const SizedBox(width: 6)," + eol +
        "                                            GestureDetector(" + eol +
        "                                              onTap: () async {" + eol +
        "                                                if (m.fileData == null) {" + eol +
        "                                                  if (!context.mounted) return;" + eol +
        "                                                  ScaffoldMessenger.of(context).showSnackBar(" + eol +
        "                                                    const SnackBar(content: Text('File data not stored'), backgroundColor: AppColors.error)," + eol +
        "                                                  );" + eol +
        "                                                  return;" + eol +
        "                                                }" + eol +
        "                                                final bytes = base64Decode(m.fileData!);" + eol +
        "                                                final uri = Uri.dataFromBytes(bytes, mimeType: m.mimeType ?? 'application/octet-stream');" + eol +
        "                                                await launchUrl(uri, mode: LaunchMode.externalApplication);" + eol +
        "                                              }," + eol +
        "                                              child: const Icon(Icons.download, color: AppColors.primary, size: 18)," + eol +
        "                                            )," + eol +
        "                                          ]," + eol +
        "                                        )" + eol
    )

    lines[start_idx:end_idx] = [new_block]
    print(f"PATCHED: file rendering with download button at line {start_idx+1}")

with io.open(path, "w", encoding="utf-8", newline="") as f:
    f.writelines(lines)

print("PATCH COMPLETE")
