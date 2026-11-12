import io

new_screen = """import 'dart:async';
import 'dart:io';
import 'package:emoji_picker_flutter/emoji_picker_flutter.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:lipsyncstudent/core/theme/app_theme.dart';
import 'package:lipsyncstudent/data/datasources/local/chat_storage.dart';
import 'package:lipsyncstudent/data/models/chat_message.dart';
import 'package:record/record.dart';
import 'package:uuid/uuid.dart';

class RoomChatScreen extends StatefulWidget {
  final String room;
  final String roomName;
  const RoomChatScreen({super.key, required this.room, required this.roomName});

  @override
  State<RoomChatScreen> createState() => _RoomChatScreenState();
}

class _RoomChatScreenState extends State<RoomChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scroll = ScrollController();
  final FocusNode _inputFocus = FocusNode();
  final AudioRecorder _recorder = AudioRecorder();

  List<ChatMessage> _messages = [];
  bool _loading = true;
  bool _showEmojiPicker = false;
  bool _isRecording = false;
  String? _recordingPath;
  DateTime? _recordingStart;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final messages = await ChatStorage.getMessages(widget.room);
    if (!mounted) return;
    setState(() {
      _messages = messages;
      _loading = false;
    });
    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scroll.hasClients) {
        _scroll.animateTo(
          _scroll.position.maxScrollExtent,
          duration: const Duration(milliseconds: 200),
          curve: Curves.easeOut,
        );
      }
    });
  }

  Future<void> _sendMessage(String text) async {
    if (text.trim().isEmpty) return;
    final message = ChatMessage(
      id: const Uuid().v4(),
      room: widget.room,
      sender: 'You',
      text: text.trim(),
      timestamp: DateTime.now(),
    );
    await ChatStorage.addMessage(message);
    _controller.clear();
    if (!mounted) return;
    setState(() {
      _messages = [..._messages, message];
      _showEmojiPicker = false;
    });
    _scrollToBottom();
  }

  Future<void> _send() async {
    await _sendMessage(_controller.text);
  }

  // ============= FILE PICKER =============
  Future<void> _pickFile() async {
    try {
      final result = await FilePicker.platform.pickFiles();
      if (result == null || result.files.isEmpty) return;
      final file = result.files.first;
      final fileName = file.name;
      final filePath = file.path ?? '';
      final tag = filePath.isNotEmpty ? '[FILE] $fileName' : '[FILE] $fileName';
      await _sendMessage(tag);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Could not pick file: $e'), backgroundColor: AppColors.error),
      );
    }
  }

  // ============= EMOJI PICKER =============
  void _toggleEmoji() {
    setState(() => _showEmojiPicker = !_showEmojiPicker);
    if (!_showEmojiPicker) _inputFocus.requestFocus();
  }

  void _onEmojiSelected(Emoji emoji) {
    _controller.text += emoji.emoji;
    _controller.selection = TextSelection.fromPosition(
      TextPosition(offset: _controller.text.length),
    );
  }

  // ============= MIC / RECORDING =============
  Future<void> _toggleRecording() async {
    if (_isRecording) {
      // Stop recording
      final path = await _recorder.stop();
      _isRecording = false;
      setState(() {});
      if (path != null && mounted) {
        final duration = _recordingStart != null
            ? DateTime.now().difference(_recordingStart!)
            : Duration.zero;
        await _sendMessage('[AUDIO] Voice message ${duration.inSeconds}s at $path');
        _recordingStart = null;
      }
    } else {
      // Start recording
      try {
        if (await _recorder.hasPermission()) {
          final dir = Directory.systemTemp;
          final path = '${dir.path}/ace_audio_${DateTime.now().millisecondsSinceEpoch}.m4a';
          await _recorder.start(const RecordConfig(), path: path);
          _recordingStart = DateTime.now();
          setState(() => _isRecording = true);
        } else {
          if (!mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Microphone permission denied'), backgroundColor: AppColors.error),
          );
        }
      } catch (e) {
        if (!mounted) return;
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Recording failed: $e'), backgroundColor: AppColors.error),
        );
      }
    }
  }

  @override
  void dispose() {
    _controller.dispose();
    _scroll.dispose();
    _inputFocus.dispose();
    _recorder.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.black,
      child: Scaffold(
        backgroundColor: Colors.black,
        appBar: AppBar(
          title: Text(widget.roomName),
          centerTitle: true,
          backgroundColor: Colors.black,
          elevation: 0,
        ),
        body: _loading
            ? const Center(
                child: CircularProgressIndicator(color: AppColors.primary))
            : Column(
                children: [
                  Expanded(
                    child: _messages.isEmpty
                        ? const Center(
                            child: Text(
                              'No messages yet. Say hi!',
                              style: TextStyle(color: AppColors.textMuted),
                            ),
                          )
                        : ListView.builder(
                            controller: _scroll,
                            padding: const EdgeInsets.all(12),
                            itemCount: _messages.length,
                            itemBuilder: (ctx, i) {
                              final m = _messages[i];
                              final isMe = m.sender == 'You';
                              return Align(
                                alignment: isMe
                                    ? Alignment.centerRight
                                    : Alignment.centerLeft,
                                child: Container(
                                  margin: const EdgeInsets.symmetric(vertical: 4),
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 12, vertical: 8),
                                  decoration: BoxDecoration(
                                    color: isMe
                                        ? AppColors.primary.withValues(alpha: 0.2)
                                        : AppColors.surface,
                                    border: Border.all(
                                        color: AppColors.primary, width: 1),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        m.sender,
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 2),
                                      Text(
                                        m.text,
                                        style: const TextStyle(
                                          color: AppColors.primary,
                                          fontSize: 14,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              );
                            },
                          ),
                  ),
                  if (_showEmojiPicker)
                    SizedBox(
                      height: 240,
                      child: EmojiPicker(
                        onEmojiSelected: (category, emoji) => _onEmojiSelected(emoji),
                        config: Config(
                          height: 240,
                          checkPlatformCompatibility: true,
                          emojiViewConfig: EmojiViewConfig(
                            backgroundColor: Colors.black,
                            emojiSizeMax: 24,
                          ),
                          categoryViewConfig: const CategoryViewConfig(
                            backgroundColor: Colors.black,
                            iconColor: AppColors.primary,
                            iconColorSelected: AppColors.primary,
                            indicatorColor: AppColors.primary,
                          ),
                        ),
                      ),
                    ),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: const BoxDecoration(
                      color: Colors.black,
                      border: Border(
                          top: BorderSide(color: AppColors.primary, width: 1)),
                    ),
                    child: Column(
                      children: [
                        if (_isRecording)
                          const Padding(
                            padding: EdgeInsets.only(bottom: 6),
                            child: Text(
                              '🔴 Recording... Tap mic to stop.',
                              style: TextStyle(color: AppColors.error, fontSize: 12),
                            ),
                          ),
                        Row(
                          children: [
                            IconButton(
                              onPressed: _pickFile,
                              icon: const Icon(Icons.attach_file, color: AppColors.primary),
                              tooltip: 'Attach file',
                            ),
                            IconButton(
                              onPressed: _toggleEmoji,
                              icon: Icon(
                                _showEmojiPicker ? Icons.keyboard : Icons.emoji_emotions_outlined,
                                color: AppColors.primary,
                              ),
                              tooltip: 'Emoji',
                            ),
                            Expanded(
                              child: TextField(
                                controller: _controller,
                                focusNode: _inputFocus,
                                style: const TextStyle(
                                    color: AppColors.primary, fontSize: 14),
                                decoration: const InputDecoration(
                                  hintText: 'Type a message...',
                                  hintStyle: TextStyle(color: AppColors.textMuted),
                                  border: OutlineInputBorder(
                                    borderRadius: BorderRadius.zero,
                                    borderSide: BorderSide(color: AppColors.primary),
                                  ),
                                  enabledBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.zero,
                                    borderSide: BorderSide(color: AppColors.primary),
                                  ),
                                  focusedBorder: OutlineInputBorder(
                                    borderRadius: BorderRadius.zero,
                                    borderSide: BorderSide(color: AppColors.primary, width: 2),
                                  ),
                                  contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                                ),
                                onSubmitted: (_) => _send(),
                              ),
                            ),
                            const SizedBox(width: 4),
                            IconButton(
                              onPressed: _toggleRecording,
                              icon: Icon(
                                _isRecording ? Icons.stop_circle : Icons.mic,
                                color: _isRecording ? AppColors.error : AppColors.primary,
                              ),
                              tooltip: _isRecording ? 'Stop recording' : 'Record voice',
                            ),
                            const SizedBox(width: 4),
                            IconButton(
                              onPressed: _send,
                              icon: const Icon(Icons.send, color: AppColors.primary),
                              style: IconButton.styleFrom(
                                backgroundColor: AppColors.surface,
                                shape: const RoundedRectangleBorder(
                                  borderRadius: BorderRadius.zero,
                                  side: BorderSide(color: AppColors.primary),
                                ),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
"""

path = r"C:\Users\chris\LipSyncStudent\lib\presentation\screens\chat\room_chat_screen.dart"
with io.open(path, "w", encoding="utf-8", newline="\r\n") as f:
    f.write(new_screen)

print("PATCH COMPLETE: room_chat_screen.dart rewritten with file/emoji/mic")
