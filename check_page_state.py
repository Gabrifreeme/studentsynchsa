import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check document readyState and try to get more info
expr = """(function(){
  return JSON.stringify({
    readyState: document.readyState,
    url: window.location.href,
    documentElement: document.documentElement ? 'exists' : 'null',
    body: document.body ? 'exists' : 'null',
    html: document.documentElement ? document.documentElement.outerHTML.substring(0, 1000) : 'none'
  })
})()"""

result = d.evaluate_js(expr)
print(result)
