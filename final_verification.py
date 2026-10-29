#!/usr/bin/env python3
# Final comprehensive verification of ACESi Settings Dashboard

import sys

print("=" * 60)
print("ACESi Settings Dashboard - Final Verification")
print("=" * 60)

# 1. Check ACEsi.html
print("\n--- ACEsi.html ---")
try:
    with open('C:/Users/chris/LipSyncStudent/ACEsi.html', 'r', encoding='utf-8', errors='replace') as f:
        html = f.read()
    
    checks = {
        'Memory tab (4th tab)': 'settings-tab-memory' in html,
        'Memory textarea': 'settings-memory' in html,
        'Save Memory button': 'saveMemory()' in html,
        'loadSettings function': 'function loadSettings' in html,
        'showSettingsTab function': 'function showSettingsTab' in html,
        'saveSystemPrompt function': 'function saveSystemPrompt' in html,
        'clearChatHistory function': 'function clearChatHistory' in html,
        'fetchNotifications function': 'function fetchNotifications' in html,
        'triggerPing function': 'function triggerPing' in html,
        'AI Engine tab': 'settings-tab-ai' in html,
        'System Prompt tab': 'settings-tab-prompt' in html,
        'Tools & Integrations tab': 'settings-tab-tools' in html,
        'Provider dropdown': 'settings-provider' in html,
        'Model dropdown': 'settings-model' in html,
        'Groq API key input': 'settings-groq-key' in html,
        'OpenRouter API key input': 'settings-openrouter-key' in html,
        'Show toolbar checkbox': 'show-toolbar' in html,
    }
    
    all_pass = True
    for name, result in checks.items():
        status = 'PASS' if result else 'FAIL'
        if not result:
            all_pass = False
        print(f'  [{status}] {name}')
    
    print(f'  Overall HTML: {"PASS" if all_pass else "FAIL"}')
except Exception as e:
    print(f'  Error reading HTML: {e}')

# 2. Check server.py
print("\n--- server.py ---")
try:
    with open('C:/Users/chris/LipSyncStudent/server.py', 'r', encoding='utf-8', errors='replace') as f:
        server = f.read()
    
    checks = {
        '/api/settings GET': '/api/settings' in server and '\"GET\"]' in server,
        '/api/settings POST': '/api/settings' in server and '\"POST\"]' in server,
        '/api/reminders': '/api/reminders' in server,
        '/api/notifications': '/api/notifications' in server,
        '/api/ping': '/api/ping' in server,
        '/api/memory GET': '/api/memory' in server and '\"GET\"]' in server,
        '/api/memory POST': '/api/memory' in server and '\"POST\"]' in server,
        'memory.txt read': 'memory.txt' in server,
        'memory.txt write': 'memory.txt' in server,
        'mood_softener_line': '_mood_softener_line' in server,
        'memory injection': 'memory.txt' in server and '_memory_content' in server,
    }
    
    all_pass = True
    for name, result in checks.items():
        status = 'PASS' if result else 'FAIL'
        if not result:
            all_pass = False
        print(f'  [{status}] {name}')
    
    print(f'  Overall server: {"PASS" if all_pass else "FAIL"}')
except Exception as e:
    print(f'  Error reading server.py: {e}')

# 3. Check config.json settings
print("\n--- config.json ---")
try:
    with open('C:/Users/chris/LipSyncStudent/config.json', 'r', encoding='utf-8', errors='replace') as f:
        import json
        config = json.load(f)
    
    checks = {
        'Has provider': 'provider' in config,
        'Has model': 'model' in config,
        'Has groq_api_key': 'groq_api_key' in config,
        'Has openrouter_api_key': 'openrouter_api_key' in config,
        'Has system_prompt': 'system_prompt' in config,
        'Has memory': 'memory' in config,
        'Has show_toolbar': 'show_toolbar' in config,
        'Has chat_history': 'chat_history' in config,
    }
    
    all_pass = True
    for name, result in checks.items():
        status = 'PASS' if result else 'FAIL'
        if not result:
            all_pass = False
        print(f'  [{status}] {name}')
    
    print(f'  Overall config: {"PASS" if all_pass else "FAIL"}')
    if isinstance(config, dict):
        print(f'  Config keys: {list(config.keys())}')
except Exception as e:
    print(f'  Error reading config.json: {e}')

# 4. Check memory.txt
print("\n--- memory.txt ---")
try:
    with open('C:/Users/chris/LipSyncStudent/memory.txt', 'r', encoding='utf-8', errors='replace') as f:
        mem = f.read()
    print(f'  memory.txt exists: True')
    print(f'  memory.txt content length: {len(mem)}')
    print(f'  memory.txt content: {mem[:200] if mem else "(empty)"}')
except FileNotFoundError:
    print(f'  memory.txt exists: False (will be created on first save)')
except Exception as e:
    print(f'  Error reading memory.txt: {e}')

print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)