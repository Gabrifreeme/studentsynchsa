import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check current URL and forms
expr = """(function(){
  return JSON.stringify({
    url: window.location.href,
    title: document.title,
    forms: document.forms.length,
    bodyText: document.body ? document.body.innerText.substring(0, 500) : 'no body'
  })
})()"""

result = d.evaluate_js(expr)
print(result)
