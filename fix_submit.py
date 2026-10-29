import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Fix form action and submit
expr = """(function(){
  var f=document.forms[0];
  // Fix the form action to use gw1view instead of gw1proc
  var action=f.action||window.location.href;
  var fixed=action.replace('gw1proc','gw1view');
  f.action=fixed;
  
  // Also try to fix any truncated URLs
  var elements=f.elements;
  for(var i=0;i<elements.length;i++){
    var e=elements[i];
    if(e.type==='submit'&&e.name===''){
      e.disabled=false
    }
  }
  
  // Submit the form
  f.submit();
  return 'submitted with action: '+fixed
})()"""

result = d.evaluate_js(expr)
print(result)
