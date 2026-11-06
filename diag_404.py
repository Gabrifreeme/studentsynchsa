import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check current 404 page details
expr = """(function(){
  return JSON.stringify({
    url: window.location.href,
    title: document.title,
    bodySnippet: document.body ? document.body.innerText.substring(0, 800) : 'no body',
    forms: document.forms.length
  });
})()"""
print("404 page:", d.evaluate_js(expr))

# Check if navfix loaded at all
expr2 = """(function(){
  return JSON.stringify({
    hasNavfix: typeof __ssaNavfix !== 'undefined',
    hasSubmitViaFetch: typeof submitViaFetch !== 'undefined'
  });
})()"""
print("Navfix state:", d.evaluate_js(expr2))
