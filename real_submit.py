import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Use the real submit function
expr = """(function(){
  var f=document.forms[0];
  if(!f) return 'no form';
  
  // Check if __ssaRealSubmit is available
  if(typeof __ssaRealSubmit==='function'){
    __ssaRealSubmit(f);
    return 'used __ssaRealSubmit'
  }
  
  // Try to submit directly
  f.submit();
  return 'used f.submit()'
})()"""

result = d.evaluate_js(expr)
print(result)
