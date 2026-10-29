import websocket
import json
import time

# Connect to the local Chrome ITS Wizard page
ws_url = "ws://127.0.0.1:9230/devtools/page/228CCE5CF318D60A674FC4907085F1D1"
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
time.sleep(0.5)
recv_all(2)

# Check page body
mid = send_cmd("Runtime.evaluate", {"expression": "document.body ? document.body.innerText.substring(0, 1000) : 'no body'"})
resp = recv_until(mid, timeout=5)
if resp:
    print("Page body:", resp.get("result", {}).get("result", {}).get("value", ""))

# Check all forms on the page
mid = send_cmd("Runtime.evaluate", {"expression": """
(function(){
  var forms = document.forms;
  var result = [];
  for (var i = 0; i < forms.length; i++) {
    var f = forms[i];
    result.push({
      id: f.id,
      name: f.name,
      action: f.action,
      method: f.method,
      elements: f.elements.length
    });
  }
  return JSON.stringify(result);
})()
"""})
resp = recv_until(mid, timeout=5)
if resp:
    print("Forms:", resp.get("result", {}).get("result", {}).get("value", ""))

# Check all links on the page
mid = send_cmd("Runtime.evaluate", {"expression": """
(function(){
  var links = document.querySelectorAll('a');
  var result = [];
  for (var i = 0; i < Math.min(links.length, 20); i++) {
    result.push({
      href: links[i].href,
      text: links[i].innerText.trim().substring(0, 50)
    });
  }
  return JSON.stringify(result);
})()
"""})
resp = recv_until(mid, timeout=5)
if resp:
    print("Links:", resp.get("result", {}).get("result", {}).get("value", ""))

ws.close()
