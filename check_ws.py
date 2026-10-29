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
time.sleep(1)

# Check page state
mid = send_cmd("Runtime.evaluate", {"expression": "document.readyState + '|' + window.location.href"})
resp, all_resp = recv_until(mid, timeout=10)
print("All responses:", json.dumps(all_resp, indent=2)[:2000])
if resp:
    print("Page state:", resp.get("result", {}).get("result", {}).get("value", ""))

ws.close()
