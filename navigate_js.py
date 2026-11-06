import websocket
import json
import time

# Connect to the Android WebView
ws_url = "ws://127.0.0.1:9229/devtools/page/3602013F4570DC00F75D3FB4BCE95B5F"
ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)

msg_id = [0]
def send_cmd(method, params=None):
    msg_id[0] += 1
    cmd = {"id": msg_id[0], "method": method}
    if params:
        cmd["params"] = params
    ws.send(json.dumps(cmd))
    return msg_id[0]

def recv_all(timeout=3):
    ws.settimeout(timeout)
    deadline = time.time() + timeout
    responses = []
    while time.time() < deadline:
        try:
            resp = ws.recv()
            responses.append(json.loads(resp))
        except websocket.WebSocketTimeoutException:
            break
    return responses

def recv_until(target_id, timeout=10):
    ws.settimeout(timeout)
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = ws.recv()
            data = json.loads(resp)
            if data.get("id") == target_id:
                return data
        except websocket.WebSocketTimeoutException:
            break
    return None

# Enable Runtime
send_cmd("Runtime.enable")
send_cmd("Page.enable")
time.sleep(0.5)
recv_all(2)

# Navigate using JavaScript instead of Page.navigate
print("Navigating to UNIVEN portal via JS...")
mid = send_cmd("Runtime.evaluate", {"expression": "window.location.href = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view'"})
resp = recv_until(mid, timeout=10)
print("Navigate response:", resp)

# Wait for page to load
print("Waiting for page to load...")
time.sleep(20)

# Check page state
mid = send_cmd("Runtime.evaluate", {"expression": "document.readyState + '|' + window.location.href + '|' + document.title"})
resp = recv_until(mid, timeout=5)
if resp:
    val = resp.get("result", {}).get("result", {}).get("value", "")
    print("Page state:", val)

ws.close()
