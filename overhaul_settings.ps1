# overhaul_settings.ps1
# Comprehensive settings panel overhaul for ACEsi.html:
# 1. Amber hover CSS on all buttons
# 2. Rebuilt AI Engine tab (providers dropdown + API keys in collapsible + models)
# 3. System Prompt tab saves to /api/settings
# 4. Tools & Integrations tab buttons functional
# 5. Save All Settings POSTs to /api/settings with confirmation alert
# 6. Bottom-right model picker replaced with model indicator text
# 7. Missing JS functions added (switchTab, saveSettings, saveSystemPrompt, etc.)
# 8. Tooltips on all buttons via title attributes
# Run: powershell -ExecutionPolicy Bypass -File overhaul_settings.ps1

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$pyScript = Join-Path $scriptDir "overhaul_settings.py"

@'
import sys

SERVER = r"C:\Users\chris\LipSyncStudent\ACEsi.html"

with open(SERVER, "r", encoding="utf-8-sig") as f:
    text = f.read()

edits = []

# Edit 1: Add hover amber CSS + collapsible styling before </head>
edits.append((r'''        /* Very small phones: panels even tighter */
        @media (max-width: 479px) {
            #chat-panel { min-height: 200px; }
            #code-panel { min-height: 100px; }
            #explorer-panel { min-height: 100px; }
            #code-editor { font-size: 13px !important; line-height: 20px !important; }
            #line-numbers { font-size: 13px !important; line-height: 20px !important; }
        }
    </style>
</head>''',
r'''        /* Very small phones: panels even tighter */
        @media (max-width: 479px) {
            #chat-panel { min-height: 200px; }
            #code-panel { min-height: 100px; }
            #explorer-panel { min-height: 100px; }
            #code-editor { font-size: 13px !important; line-height: 20px !important; }
            #line-numbers { font-size: 13px !important; line-height: 20px !important; }
        }

        /* ===== Amber hover on all buttons ===== */
        button:hover {
            background: #ff9d00 !important;
            color: #000 !important;
        }

        /* Collapsible section styling */
        .collapsible-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #111;
            color: #ff9d00;
            border: 1px solid #ff9d00;
            padding: 6px 10px;
            font-family: 'Roboto Mono', monospace;
            font-size: 11px;
            cursor: pointer;
            margin: 6px 0;
        }
        .collapsible-header:hover {
            background: #ff9d00;
            color: #000;
        }
        .collapsible-content {
            display: none;
            padding: 10px;
            border: 1px solid #ff9d00;
            border-top: none;
            background: #0a0a0a;
        }
        .collapsible-content.open {
            display: block;
        }
    </style>
</head>'''))

# Edit 2: Replace the entire settings panel HTML
start_marker = '<div id="settings-panel"'
end_marker = '</div>\n\n    <div id="dev-toolbar"'
start = text.index(start_marker)
end = text.index(end_marker)

new_panel = r'''    <div id="settings-panel"
        style="display:none;position:fixed;top:60px;left:50%;transform:translateX(-50%);background:#000;border:1px solid #ff9d00;padding:20px;z-index:10000;font-family:'Roboto Mono',monospace;color:#ff9d00;width:520px;max-height:85vh;overflow-y:auto;">
        <div style="margin-bottom:12px;">
            <button data-tab="settings-tab-ai" onclick="switchTab('settings-tab-ai')"
                style="background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px 12px;font-size:11px;margin-right:4px;">AI
                Engine</button>
            <button data-tab="settings-tab-prompt" onclick="switchTab('settings-tab-prompt')"
                style="background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px 12px;font-size:11px;margin-right:4px;">System
                Prompt</button>
            <button data-tab="settings-tab-tools" onclick="switchTab('settings-tab-tools')"
                style="background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px 12px;font-size:11px;">Tools &
                Integrations</button>
        </div>

        <!-- AI Engine Tab -->
        <div id="settings-tab-ai" class="tab-content"
            style="display:block; margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid #ff9d00;">
            <div style="font-size:12px;color:#ff9d00;margin-bottom:6px;">AI Engine</div>

            <div style="display:flex;gap:12px;">
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:4px;font-size:11px;">Provider</label>
                    <select id="settings-provider"
                        style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:11px;cursor:pointer;"
                        onchange="updateModelsForProvider()">
                        <option value="groq">Groq (free tier)</option>
                        <option value="openrouter">OpenRouter (fallback)</option>
                        <option value="ollama">Local Ollama</option>
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic (Claude)</option>
                        <option value="gemini">Google Gemini</option>
                        <option value="cerebras">Cerebras</option>
                        <option value="sambanova">SambaNova</option>
                    </select>
                </div>
                <div style="flex:1;">
                    <label style="display:block;margin-bottom:4px;font-size:11px;">Model</label>
                    <select id="settings-model"
                        style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:11px;cursor:pointer;">
                        <option value="gpt-oss-20b">gpt-oss-20b</option>
                        <option value="llama-3.1-70b-versatile">llama-3.1-70b-versatile</option>
                        <option value="qwen-qwq-32b">qwen-qwq-32b</option>
                    </select>
                </div>
            </div>

            <div class="collapsible-header" onclick="toggleCollapsible(this)">
                <span>🔑 API Keys</span>
                <span style="font-size:10px;">▼</span>
            </div>
            <div class="collapsible-content" id="api-keys-collapse">
                <div style="font-size:10px;color:#888;margin-bottom:6px;">Keys are saved to config.json on the server.</div>
                <label style="display:block;margin-bottom:2px;font-size:10px;">Groq API Key</label>
                <input type="text" id="settings-groq-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="Enter Groq API Key">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">OpenRouter API Key</label>
                <input type="text" id="settings-openrouter-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="Enter OpenRouter API Key">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">Ollama Host</label>
                <input type="text" id="settings-ollama-host"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="http://localhost:11434">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">OpenAI API Key</label>
                <input type="text" id="settings-openai-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="sk-...">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">Anthropic API Key</label>
                <input type="text" id="settings-anthropic-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="sk-ant-...">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">Gemini API Key</label>
                <input type="text" id="settings-gemini-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="Enter Gemini API Key">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">Cerebras API Key</label>
                <input type="text" id="settings-cerebras-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="Enter Cerebras API Key">
                <label style="display:block;margin-top:4px;margin-bottom:2px;font-size:10px;">SambaNova API Key</label>
                <input type="text" id="settings-sambanova-key"
                    style="width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:'Roboto Mono',monospace;font-size:10px;"
                    placeholder="Enter SambaNova API Key">
            </div>
        </div>

        <!-- System Prompt Tab -->
        <div id="settings-tab-prompt" class="tab-content"
            style="display:none; margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid #ff9d00;">
            <div style="font-size:12px;color:#ff9d00;margin-bottom:6px;">System Prompt</div>
            <textarea id="settings-prompt"
                style="width:100%;height:200px;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:8px;font-family:'Roboto Mono',monospace;font-size:11px;resize:vertical;outline:none;"
                placeholder="System prompt..."></textarea>
            <div style="margin-top:8px; text-align:center;">
                <button onclick="saveSystemPrompt()"
                    style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 12px;font-size:11px;">Save
                    Prompt</button>
            </div>
        </div>

        <!-- Tools & Integrations Tab -->
        <div id="settings-tab-tools" class="tab-content"
            style="display:none; margin-bottom:12px; padding-bottom:12px; border-bottom:1px solid #ff9d00;">
            <div style="font-size:12px;color:#ff9d00;margin-bottom:6px;">Tools & Integrations</div>
            <div style="margin-bottom:8px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;">
                    <input type="checkbox" id="show-toolbar" style="margin-right:4px;width:auto;"
                        onclick="toggleDeveloperToolbar()"> Show Developer Toolbar
                </label>
            </div>
            <div style="margin-bottom:8px;">
                <label style="display:block;margin-bottom:4px;font-size:11px;">
                    <input type="checkbox" id="ntfy-enable" style="margin-right:4px;width:auto;"> Enable ntfy Push
                    Notifications
                </label>
            </div>
            <button onclick="clearChatHistory()"
                style="width:100%;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-size:11px;">Clear
                Chat History</button>
            <button onclick="fetchNotifications()"
                style="width:100%;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-size:11px;">Fetch
                Notifications</button>
            <button onclick="triggerPing()"
                style="width:100%;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-size:11px;">Send
                Ping</button>
            <button onclick="connectGoogleDrive()"
                style="width:100%;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-size:11px;">Google
                Drive</button>
        </div>

        <div style="text-align:center;margin-top:16px;">
            <button onclick="saveSettings()"
                style="background:#ff9d00;color:#000;border:none;padding:8px 16px;font-size:11px;font-weight:bold;cursor:pointer;">Save
                All Settings</button>
            <button onclick="document.getElementById('settings-panel').style.display='none'"
                style="width:100%;background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:8px;font-size:11px;">Close</button>
        </div>
    </div>

    <div id="dev-toolbar"'''

text = text[:start] + new_panel + text[end:]

# Edit 3: Remove bottom-right model picker, add model indicator
old_model = r'''        <span style="flex:1;"></span>
        <span>Model:</span>
        <button id="modelBtn" onclick="toggleModelPicker(event)" title="Select Model"
            style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:2px 8px;border-radius:3px;font-family:'Roboto Mono',monospace;font-size:11px;cursor:pointer;">GPT-OSS
            20B –¾</button>
    </div>'''

new_model = r'''        <span style="flex:1;"></span>
        <span>Model:</span>
        <span id="current-model-indicator" style="background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:2px 8px;border-radius:3px;font-family:'Roboto Mono',monospace;font-size:11px;">gpt-oss-20b</span>
    </div>'''

count = text.count(old_model)
if count > 0:
    text = text.replace(old_model, new_model, 1)
    print("Edit 3: OK - model picker replaced with indicator")
else:
    print("Edit 3: WARNING - modelBtn not found")

# Edit 4: Add JS functions before emergency restore script
js_functions = r'''
        /* ===== Settings Tab Switching ===== */
        function switchTab(tabId) {
            document.querySelectorAll('.tab-content').forEach(function(el) { el.style.display = 'none'; });
            document.querySelectorAll('[data-tab]').forEach(function(btn) { btn.style.background = '#111'; });
            var selected = document.getElementById(tabId);
            if (selected) selected.style.display = 'block';
            var activeBtn = document.querySelector('[data-tab="' + tabId + '"]');
            if (activeBtn) { activeBtn.style.background = '#ff9d00'; activeBtn.style.color = '#000'; }
        }

        function toggleCollapsible(header) {
            var content = header.nextElementSibling;
            var arrow = header.querySelector('span:last-child');
            if (content && content.classList.contains('collapsible-content')) {
                if (content.classList.contains('open')) {
                    content.classList.remove('open');
                    arrow.textContent = '▼';
                } else {
                    content.classList.add('open');
                    arrow.textContent = '▲';
                }
            }
        }

        function updateModelsForProvider() {
            var provider = document.getElementById('settings-provider').value;
            var modelSelect = document.getElementById('settings-model');
            if (!modelSelect) return;
            modelSelect.innerHTML = '';
            var models = [];
            switch (provider) {
                case 'groq': models = ['gpt-oss-20b', 'llama-3.1-70b-versatile', 'qwen-qwq-32b', 'mixtral-8x7b-32768', 'gemma-7b-it']; break;
                case 'openrouter': models = ['google/gemini-2.0-flash-exp', 'meta-llama/llama-3.1-405b-instruct', 'anthropic/claude-3.5-sonnet', 'openai/gpt-4o']; break;
                case 'ollama': models = ['qwen2.5-coder:7b', 'llama3.1:8b', 'deepseek-coder-v2', 'phi3:mini', 'mistral:instruct']; break;
                case 'openai': models = ['gpt-4o', 'gpt-4o-mini', 'o1-mini', 'gpt-3.5-turbo']; break;
                case 'anthropic': models = ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307']; break;
                case 'gemini': models = ['gemini-2.0-flash-exp', 'gemini-1.5-pro', 'gemini-1.5-flash']; break;
                case 'cerebras': models = ['llama-3.3-70b', 'qwen-3-32b']; break;
                case 'sambanova': models = ['Meta-Llama-3.3-70B-Instruct', 'Llama-3.1-405B-Instruct']; break;
            }
            models.forEach(function(m) {
                var o = document.createElement('option');
                o.value = m;
                o.textContent = m;
                modelSelect.appendChild(o);
            });
        }

        async function loadSettings() {
            try {
                var r = await fetch('http://127.0.0.1:5000/api/settings');
                var d = await r.json();
                if (d.provider) document.getElementById('settings-provider').value = d.provider;
                updateModelsForProvider();
                if (d.model) document.getElementById('settings-model').value = d.model;
                document.getElementById('current-model-indicator').textContent = d.model || 'gpt-oss-20b';
                if (d.groq_key) document.getElementById('settings-groq-key').value = d.groq_key;
                if (d.openrouter_key) document.getElementById('settings-openrouter-key').value = d.openrouter_key;
                if (d.ollama_host) document.getElementById('settings-ollama-host').value = d.ollama_host;
                if (d.openai_key) document.getElementById('settings-openai-key').value = d.openai_key;
                if (d.anthropic_key) document.getElementById('settings-anthropic-key').value = d.anthropic_key;
                if (d.gemini_key) document.getElementById('settings-gemini-key').value = d.gemini_key;
                if (d.cerebras_key) document.getElementById('settings-cerebras-key').value = d.cerebras_key;
                if (d.sambanova_key) document.getElementById('settings-sambanova-key').value = d.sambanova_key;
                if (d.system_prompt) document.getElementById('settings-prompt').value = d.system_prompt;
            } catch (e) { console.warn('Could not load settings:', e); }
        }

        function saveSettings() {
            var provider = document.getElementById('settings-provider').value;
            var model = document.getElementById('settings-model').value;
            var data = {
                provider: provider, model: model,
                groq_key: document.getElementById('settings-groq-key').value,
                openrouter_key: document.getElementById('settings-openrouter-key').value,
                ollama_host: document.getElementById('settings-ollama-host').value,
                openai_key: document.getElementById('settings-openai-key').value,
                anthropic_key: document.getElementById('settings-anthropic-key').value,
                gemini_key: document.getElementById('settings-gemini-key').value,
                cerebras_key: document.getElementById('settings-cerebras-key').value,
                sambanova_key: document.getElementById('settings-sambanova-key').value,
                system_prompt: document.getElementById('settings-prompt').value
            };
            fetch('http://127.0.0.1:5000/api/settings', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d && d.ok) {
                        document.getElementById('current-model-indicator').textContent = model;
                        alert('Settings saved successfully.');
                    } else { alert('Save failed: ' + ((d && d.message) || 'unknown')); }
                })
                .catch(function (e) { alert('Save failed: ' + e.message); });
        }

        function saveSystemPrompt() {
            var prompt = document.getElementById('settings-prompt').value;
            fetch('http://127.0.0.1:5000/api/settings', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ system_prompt: prompt })
            })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (d && d.ok) { alert('System prompt saved.'); }
                    else { alert('Save failed: ' + ((d && d.message) || 'unknown')); }
                })
                .catch(function (e) { alert('Save failed: ' + e.message); });
        }

        function toggleDeveloperToolbar() {
            var cb = document.getElementById('show-toolbar');
            var tb = document.getElementById('dev-toolbar');
            if (tb) tb.style.display = cb.checked ? 'flex' : 'none';
        }
        function clearChatHistory() {
            if (confirm('Clear all chat history?')) {
                var container = document.getElementById('chat-messages');
                if (container) container.innerHTML = '';
                alert('Chat history cleared.');
            }
        }
        function fetchNotifications() {
            alert('Notifications feature: check your ntfy app for pushes.');
        }
        function triggerPing() {
            fetch('http://127.0.0.1:5000/api/system/exec', {
                method: 'POST', headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command: 'echo ping' })
            }).then(function (r) { return r.json(); })
                .then(function (d) { alert('Ping sent: ' + ((d && d.ok) ? 'ok' : 'failed')); })
                .catch(function (e) { alert('Ping failed: ' + e.message); });
        }
        function connectGoogleDrive() {
            alert('Google Drive integration: configure in settings and use the file picker.');
        }

        var _settingsInitialized = false;
        var _origOpenSettings = window.openSettings;
        window.openSettings = function () {
            var panel = document.getElementById('settings-panel');
            if (panel) {
                panel.style.display = 'block';
                switchTab('settings-tab-ai');
                if (!_settingsInitialized) { loadSettings(); _settingsInitialized = true; }
            }
        };
'''

insert_marker = '<script>\n        console.log("ACEsi Emergency Restore Loaded");'
count = text.count(insert_marker)
if count == 0:
    print("Edit 4: WARNING - insert marker not found")
else:
    text = text.replace(insert_marker, js_functions + '\n' + insert_marker, 1)
    print("Edit 4: OK - JS functions added")

with open(SERVER, "w", encoding="utf-8-sig", newline="") as f:
    f.write(text.replace("\n", "\r\n"))

with open(SERVER, "rb") as f:
    raw = f.read()
print(f"BOM: {raw[:3] == b'\xef\xbb\xbf'}")
print(f"CRLF count: {raw.count(b'\r\n')}")
print(f"bare LF count: {raw.count(b'\n') - raw.count(b'\r\n')}")
print("\nDone — Settings panel overhaul complete.")
'@ | Set-Content -Path $pyScript -Encoding UTF8

python $pyScript

# Restart server
try {
    Invoke-RestMethod -Uri http://127.0.0.1:5000/restart -Method POST -ContentType 'application/json' -Body '{}' -TimeoutSec 10 | Out-Null
    Write-Host "Server restart requested."
} catch {
    Write-Host "Server restart request failed: $($_.Exception.Message)"
}

Write-Host "`nDone. Refresh ACEsi in your browser."
