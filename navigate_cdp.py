import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Try to use Page.navigate via CDP directly
result = d._get_session()
print("Session:", result)
if result:
    mid = result._send("Page.navigate", {"url": "https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view"})
    print("Navigate sent, id:", mid)
    resp = result._wait(mid, timeout=15)
    print("Navigate response:", resp)
