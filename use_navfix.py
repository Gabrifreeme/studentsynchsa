import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check if navfix is loaded and try to use it
expr = """(function(){
  // Check if navfix is loaded
  if(typeof __ssaNavfix!=='undefined'){
    // Run navfix to set up form interception
    __ssaNavfix();
    
    // Get the form
    var f=document.forms[0];
    if(!f) return 'no form';
    
    // Use submitViaFetch to submit the form
    if(typeof submitViaFetch==='function'){
      submitViaFetch(f);
      return 'submitted via fetch'
    }
    
    return 'navfix loaded but submitViaFetch not found'
  }
  return 'navfix not loaded'
})()"""

result = d.evaluate_js(expr)
print(result)
