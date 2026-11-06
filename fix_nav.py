import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Use the navigation fix script
expr = """(function(){
  // The navigation fix script should already be injected
  // Let's try to use it to fix the URL
  if(typeof window.__ssaNavfix!=='undefined'){
    return 'navfix already loaded'
  }
  
  // Try to fix the form submission
  var f=document.forms[0];
  if(!f) return 'no form';
  
  // Override the form submission
  var origSubmit=f.submit;
  f.submit=function(){
    var action=f.action||window.location.href;
    var fixed=action.replace('gw1proc','gw1view');
    f.action=fixed;
    return origSubmit.call(f)
  };
  
  // Click the Next button
  var btn=document.getElementById('oapNextBtn2');
  if(btn){
    btn.disabled=false;
    btn.click();
    return 'clicked Next with fixed submit'
  }
  return 'Next button not found'
})()"""

result = d.evaluate_js(expr)
print(result)
