import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Clear cookies and cache
result = d.evaluate_js("""
(function(){
  try { localStorage.clear(); } catch(e) {}
  try { sessionStorage.clear(); } catch(e) {}
  try { document.cookie.split(';').forEach(function(c) {
    document.cookie = c.trim().split('=')[0] + '=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;domain=' + window.location.hostname;
  }); } catch(e) {}
  return 'cleared'
})()
""")
print("Clear result:", result)
