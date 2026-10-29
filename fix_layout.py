path = "C:\\Users\\chris\\LipSyncStudent\\ACESi.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '''<div style="display:flex;gap:8px;padding:8px;border-top:1px solid #ff9d00;background:#000;">
                <textarea id="chat-input" placeholder="Ask ACEsi..." rows="1" style="flex:1;width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:inherit;outline:none;resize:none;overflow-y:auto;"></textarea>
                <button type="button" onclick="sendMessage()" title="Send" style="background:#ff9d00;color:#000;border:none;padding:6px 12px;border-radius:3px;font-family:inherit;font-weight:bold;cursor:pointer;" onmousedown="console.log('Send clicked')">Send</button>
                <button onclick="document.getElementById('chat-input').focus()" title="Mic" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">🎤</button>
                <button onclick="alert('Speaker: audio feedback on')" title="Speaker" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">🔊</button>
                <button onclick="document.getElementById('chat-file').click()" title="Upload" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">➕</button>
                <input id="chat-file" type="file" style="display:none;" onchange="if(this.files[0]) document.getElementById('chat-messages').innerHTML += '<div style=\\'background:#111;padding:6px;border:1px solid #ff9d00;margin-top:4px;\\'>📎 ' + this.files[0].name + '</div>'">
</div>'''

new = '''<div style="display:flex;gap:8px;padding:8px 8px 4px 8px;border-top:1px solid #ff9d00;background:#000;">
                <textarea id="chat-input" placeholder="Ask ACEsi..." rows="1" style="flex:1;width:100%;background:#111;color:#ff9d00;border:1px solid #ff9d00;padding:6px;font-family:inherit;outline:none;resize:none;overflow-y:auto;"></textarea>
                <button type="button" onclick="sendMessage()" title="Send" style="background:#ff9d00;color:#000;border:none;padding:6px 12px;border-radius:3px;font-family:inherit;font-weight:bold;cursor:pointer;" onmousedown="console.log('Send clicked')">Send</button>
</div>
<div style="display:flex;justify-content:center;gap:8px;padding:0 8px 8px 8px;background:#000;">
                <button onclick="document.getElementById('chat-input').focus()" title="Mic" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">🎤</button>
                <button onclick="alert('Speaker: audio feedback on')" title="Speaker" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">🔊</button>
                <button onclick="document.getElementById('chat-file').click()" title="Upload" style="background:#000;color:#ff9d00;border:1px solid #ff9d00;padding:6px 10px;border-radius:3px;cursor:pointer;font-family:inherit;">➕</button>
                <input id="chat-file" type="file" style="display:none;" onchange="if(this.files[0]) document.getElementById('chat-messages').innerHTML += '<div style=\\'background:#111;padding:6px;border:1px solid #ff9d00;margin-top:4px;\\'>📎 ' + this.files[0].name + '</div>'">
</div>'''

if old in content:
    content = content.replace(old, new, 1)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Replacement done")
else:
    print("FAILED: old string not found")
    idx = content.find('display:flex;gap:8px')
    if idx >= 0:
        print("Found at index:", idx)
        print(repr(content[idx:idx+300]))
