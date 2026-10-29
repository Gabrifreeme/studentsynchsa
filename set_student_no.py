import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Set oapOldNew to No
expr = """(function(){
  var sel=document.getElementById('oapOldNew');
  if(!sel) return 'not found';
  sel.value='N';
  sel.dispatchEvent(new Event('change',{bubbles:true}));
  sel.dispatchEvent(new Event('input',{bubbles:true}));
  return 'set to: '+sel.value
})()"""

result = d.evaluate_js(expr)
print(result)
