import subprocess, os, time, json, urllib.request, websocket
PORT = 9230
cp = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
u = r"C:\Users\chris\AppData\Local\Temp\chr_dbg2"
os.makedirs(u, exist_ok=True)
html = "data:text/html,<script>console.log('ACE-CDP self-test ready');document.title='ACETEST'</script>"
flags = ["--headless=new","--disable-gpu","--remote-debugging-port=%d" % PORT,
         "--remote-allow-origins=*","--no-first-run","--user-data-dir="+u, html]
subprocess.Popen([cp]+flags, stdout=open(r"C:\Users\chris\AppData\Local\Temp\chr2.log","w"),
                 stderr=subprocess.STDOUT, creationflags=subprocess.DETACHED_PROCESS)
print("launched")
for i in range(25):
    time.sleep(1)
    try:
        r = urllib.request.urlopen("http://[::1]:%d/json/version" % PORT, timeout=2)
        print("version OK:", json.loads(r.read()).get("Browser")); break
    except Exception as e:
        print("poll", i, str(e)[:100])
try:
    r = urllib.request.urlopen("http://[::1]:%d/json/list" % PORT, timeout=3)
    d = json.loads(r.read())
    pages = [t for t in d if t.get("type") == "page"]
    url = pages[0]["webSocketDebuggerUrl"] if pages else None
    print("page ws:", url)
    ws = websocket.create_connection(url, timeout=10)
    print("WS OK recv:", ws.recv()[:80])
    ws.close()
except Exception as e:
    import traceback; traceback.print_exc()
print("DONE")
