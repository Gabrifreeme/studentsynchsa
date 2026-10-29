with open('C:/Users/chris/LipSyncStudent/ACEsi.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
checks = {
    'Memory tab': 'settings-tab-memory' in content,
    'Save Memory button': 'saveMemory()' in content,
    'loadSettings': 'function loadSettings' in content,
    'showSettingsTab': 'function showSettingsTab' in content,
    'saveSystemPrompt': 'function saveSystemPrompt' in content,
    'clearChatHistory': 'function clearChatHistory' in content,
    'fetchNotifications': 'function fetchNotifications' in content,
    'triggerPing': 'function triggerPing' in content,
    'saveMemory function': 'function saveMemory' in content,
    'Memory textarea': 'settings-memory' in content,
    'Memory tab in tabs': 'id="settings-tab-memory"' in content,
}
for name, result in checks.items():
    print(f'{name}: {result}')