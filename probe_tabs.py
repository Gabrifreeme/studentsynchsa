import json, urllib.request
r = urllib.request.urlopen("http://127.0.0.1:9230/json/list", timeout=3)
tabs = json.load(r)
for t in tabs:
    if t.get("type") == "page":
        print("TAB:", t.get("title"), "|", t.get("url"))
