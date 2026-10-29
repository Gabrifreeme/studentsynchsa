import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Enable Next button and submit form
expr = """(function(){
  var btn=document.getElementById('oapNextBtn2');
  if(btn){
    btn.disabled=false;
    btn.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
    return 'dispatched click'
  }
  return 'not found'
})()"""

result = d.evaluate_js(expr)
print(result)
