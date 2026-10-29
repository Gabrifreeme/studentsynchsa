import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Enable Next button
expr = """(function(){
  var btn=document.getElementById('oapNextBtn1');
  if(!btn) return 'not found';
  btn.disabled=false;
  return 'enabled'
})()"""

result = d.evaluate_js(expr)
print(result)
