import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Run validation function
expr = """(function(){
  if(typeof changeToNameValuePairs==='function'){
    var f=document.forms[0];
    var result=changeToNameValuePairs(f);
    return JSON.stringify({result:result})
  }
  return 'function not found'
})()"""

result = d.evaluate_js(expr)
print(result)
