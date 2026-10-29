import websocket
import json
import time

ws_url = "ws://127.0.0.1:9229/devtools/page/9E568445615CFD43A60BDF424BCC2807"
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
    while time.time() < deadline:
        try:
            resp = ws.recv()
            data = json.loads(resp)
            if data.get("id") == target_id:
                return data
        except websocket.WebSocketTimeoutException:
            break
    return None

# Enable
send_cmd("Runtime.enable")
send_cmd("Page.enable")
time.sleep(1)

# Navigate via JS
print("Navigating via JS...")
mid = send_cmd("Runtime.evaluate", {"expression": "window.location.href = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p_proc=ITS_OAP02&p_page=2'"})
resp = recv_until(mid, timeout=10)
print("Nav response:", resp)

# Wait
time.sleep(20)

# Check
mid = send_cmd("Runtime.evaluate", {"expression": "document.readyState + '|' + window.location.href + '|' + document.title"})
resp = recv_until(mid, timeout=5)
print("After nav:", resp)

ws.close()
