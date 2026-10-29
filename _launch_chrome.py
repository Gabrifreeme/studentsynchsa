import subprocess, os, time, json, sys, urllib.request
cp = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
u = r"C:\Users\chris\AppData\Local\Temp\chr_dbg"
os.makedirs(u, exist_ok=True)
log = open(r"C:\Users\chris\AppData\Local\Temp\chr.log", "w")
html = "data:text/html,<script>console.log('ACE-CDP self-test ready');document.title='ACETEST'</script>"
proc = subprocess.Popen([cp, "--headless=new", "--disable-gpu",
    "--remote-debugging-port=9230", "--no-first-run", "--user-data-dir=" + u, html],
    stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.DETACHED_PROCESS)
print("launched pid", proc.pid, flush=True)
for i in range(24):
    time.sleep(1)
    try:
        r = urllib.request.urlopen("http://127.0.0.1:9230/json/version", timeout=2)
        print("version OK:", r.status, flush=True)
        r = urllib.request.urlopen("http://127.0.0.1:9230/json/list", timeout=2)
        d = json.loads(r.read())
        print("targets:", len(d), flush=True)
        for t in d:
            print("  ", t.get("type"), "|", (t.get("url") or "")[:60], "->", (t.get("webSocketDebuggerUrl") or "")[:80], flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"  poll {i}: {e}", flush=True)
print("FAILED to come up; see C:\\Users\\chris\\AppData\\Local\\Temp\\chr.log")
