with open(r'C:\Users\chris\LipSyncStudent\ACEsi.html', 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Add JavaScript functions after the copyCode function
js_functions = '''

        function loadSettings() {
            fetch('http://127.0.0.1:5000/api/settings')
                .then(r => r.json())
                .then(d => {
                    // Populate provider
                    const providerSelect = document.getElementById('settings-provider');
                    if (d.provider && providerSelect.options[d.provider]) {
                        providerSelect.selectedIndex = providerSelect.options[d.provider];
                    }
                    // Update models based on selected provider
                    updateModels(d.provider || 'groq');
                    // Populate API keys
                    document.getElementById('settings-groq-key').value = d.groq_api_key || '';
                    document.getElementById('settings-openrouter-key').value = d.openrouter_api_key || '';
                    // Populate prompt
                    document.getElementById('settings-prompt').value = d.system_prompt || '';
                    // Populate memory
                    document.getElementById('settings-memory').value = d.memory || '';
                    // Show toolbar toggle
                    document.getElementById('show-toolbar').checked = d.show_toolbar !== false;
                })
                .catch(e => addOutput('❌ Failed to load settings: ' + e.message));
        }

        function saveSystemPrompt() {
            const prompt = document.getElementById('settings-prompt').value;
            fetch('http://127.0.0.1:5000/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: prompt })
            }).then(r => r.json())
            .then(d => {
                addOutput('✅ System prompt saved successfully');
                loadSettings();
            })
            .catch(e => addOutput('❌ Failed to save system prompt: ' + e.message));
        }

        function clearChatHistory() {
            if (confirm('Clear all chat history?')) {
                document.getElementById('chat-messages').innerHTML = '<div style="background:#1a1a1a;padding:8px 12px;border-radius:6px;border:1px solid #ff9d00;margin-bottom:8px;"><b>ACEsi:</b> Hi Chris. I\'m here. Ready to fix your project.</div>';
                addOutput('💬 Chat history cleared');
                // Also tell server to clear
                fetch('http://127.0.0.1:5000/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ clear_chat: true })
                });
            }
        }

        function fetchNotifications() {
            fetch('http://127.0.0.1:5000/api/notifications')
                .then(r => r.json())
                .then(d => {
                    const results = d.notifications || [];
                    addOutput(\`📢 Fetched \${results.length} notifications\`);
                    results.forEach(n => addOutput(\`- \${n}\`));
                })
                .catch(e => addOutput('❌ Failed to fetch notifications: ' + e.message));
        }

        function triggerPing() {
            fetch('http://127.0.0.1:5000/api/ping', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ping: true })
            }).then(r => r.json())
            .then(d => {
                addOutput(\`📡 \${d.status || 'Ping triggered'}\`);
            })
            .catch(e => addOutput('❌ Failed to send ping: ' + e.message));
        }

        function saveMemory() {
            const memory = document.getElementById('settings-memory').value;
            fetch('http://127.0.0.1:5000/api/memory', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ memory: memory })
            }).then(r => r.json())
            .then(d => {
                addOutput(\"✅ Memory saved: \${d.memory || 'unknown'}\");
                // Refresh the memory display
                fetch('http://127.0.0.1:5000/api/memory')
                    .then(r => r.json())
                    .then(d2 => {
                        addOutput(\`💾 Memory loaded: \${d2.memory || 'empty'}\`);
                    });
            })
            .catch(e => addOutput('❌ Failed to save memory: ' + e.message));
        }

        function showSettingsTab(tab) {
            // Hide all tabs
            document.getElementById('settings-tab-ai').style.display = 'none';
            document.getElementById('settings-tab-prompt').style.display = 'none';
            document.getElementById('settings-tab-tools').style.display = 'none';
            document.getElementById('settings-tab-memory').style.display = 'none';
            // Show selected tab
            if (tab === 'ai') {
                document.getElementById('settings-tab-ai').style.display = 'block';
            } else if (tab === 'prompt') {
                document.getElementById('settings-tab-prompt').style.display = 'block';
            } else if (tab === 'tools') {
                document.getElementById('settings-tab-tools').style.display = 'block';
            } else if (tab === 'memory') {
                document.getElementById('settings-tab-memory').style.display = 'block';
            }
        }

        // When provider changes, update model dropdown
        document.getElementById('settings-provider').addEventListener('change', function() {
            updateModels(this.value);
        });

        // On page load, load settings
        window.addEventListener('load', function() {
            loadSettings();
        });
'''

# Find the copyCode function and insert JS after it
idx = content.find('function copyCode()')
if idx > 0:
    # Find the end of copyCode function
    end_idx = content.find('}', idx) + 1
    # Find the // 1. Load the file list comment
    load_idx = content.find('// 1. Load the file list', end_idx)
    if load_idx > 0:
        content = content[:load_idx] + js_functions + '\n\n        // 1. Load the file list into the Explorer\n        window.addEventListener' + content[load_idx:]
        print('JavaScript functions added')
    else:
        print('Could not find load comment position')
else:
    print('Could not find copyCode function position')

with open(r'C:\Users\chris\LipSyncStudent\ACEsi.html', 'w', encoding='utf-8', errors='replace') as f:
    f.write(content)
print('JS update done')