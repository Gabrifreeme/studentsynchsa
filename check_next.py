import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check Next button status
expr = """(function(){
  var btn=document.getElementById('oapNextBtn1');
  if(!btn) return 'not found';
  return JSON.stringify({disabled:btn.disabled,visible:btn.offsetWidth>0})
})()"""

result = d.evaluate_js(expr)
print(result)
