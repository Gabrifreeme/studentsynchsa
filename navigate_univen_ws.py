import websocket
import json
import time

# Connect to the WebView devtools
ws_url = "ws://127.0.0.1:9229/devtools/page/FEF26521AC29CF65F3FD964B30C39BEA"
ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)

msg_id = [0]
def send_cmd(method, params=None):
    msg_id[0] += 1
    cmd = {"id": msg_id[0], "method": method}
    if params:
        cmd["params"] = params
    ws.send(json.dumps(cmd))
    return msg_id[0]

def recv_until(target_id, timeout=10):
    ws.settimeout(timeout)
    deadline = time.time() + timeout
    responses = []
    while time.time() < deadline:
        try:
            resp = ws.recv()
            data = json.loads(resp)
            responses.append(data)
            if data.get("id") == target_id:
                return data, responses
        except websocket.WebSocketTimeoutException:
            break
    return None, responses

# Enable Runtime
send_cmd("Runtime.enable")
time.sleep(0.5)

# Navigate to UNIVEN portal
print("Navigating to UNIVEN portal...")
mid = send_cmd("Page.navigate", {"url": "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view"})
resp, all_resp = recv_until(mid, timeout=15)
print("Navigate response:", resp)

# Wait for page to load
print("Waiting for page to load...")
time.sleep(10)

# Check page state
mid = send_cmd("Runtime.evaluate", {"expression": "document.readyState + '|' + window.location.href"})
resp, _ = recv_until(mid, timeout=10)
if resp:
    val = resp.get("result", {}).get("result", {}).get("value", "")
    print("Page state:", val)

ws.close()
