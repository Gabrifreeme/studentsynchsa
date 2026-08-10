# Regression test: /chat must NOT misroute UI instructions as file paths.
# Run with: python -m unittest test_file_request -v   (or python -m pytest)
import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import server

UI_INSTRUCTIONS = [
    "open the app",
    "open the app and tap login",
    "read the notifications",
    "open settings",
    "Open WhatsApp",
    "read my messages",
    "open the camera",
    "read the latest email",
    "open the profile screen",
    "please open the settings page",
    "can you open the app?",
    "tap the button",
    "swipe up",
    "open the file manager",
    "open the files app",
    "read the notification shade",
    "open the settings screen",
    "read my calendar",
]

FILE_REQUESTS = [
    "read file C:\\Users\\x\\notes.txt",
    "open lib/services/its_url_fixer.dart",
    "read test/widgets/widget_test.dart",
    "open the file",
    "read file",
    "please open settings.json",
    "open C:\\temp\\a.pdf",
    "read the README.md file",
    "open my notes file",
    "read file: diary.txt",
    "open .gitignore",
    "read pubspec.yaml",
]


class FileRequestTest(unittest.TestCase):
    def test_ui_instructions_are_not_files(self):
        for text in UI_INSTRUCTIONS:
            is_file, candidate, _ = server._match_file_request(text)
            self.assertFalse(is_file,
                             "UI instruction hijacked as file: %r -> %r" % (text, candidate))

    def test_file_requests_still_match(self):
        for text in FILE_REQUESTS:
            is_file, _, _ = server._match_file_request(text)
            self.assertTrue(is_file, "genuine file request missed: %r" % text)

    def test_open_the_file_uses_last_path(self):
        # "open the file" alone should be vague (uses LAST_FILE_PATH), not error
        is_file, candidate, vague = server._match_file_request("open the file")
        self.assertTrue(is_file)
        self.assertTrue(vague)


if __name__ == "__main__":
    unittest.main()
