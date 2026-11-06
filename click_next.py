import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Click Next button
expr = """(function(){
  var nextBtn=document.getElementById('oapNextBtn1');
  if(nextBtn){
    nextBtn.disabled=false;
    nextBtn.click();
    return 'clicked Next'
  }
  return 'Next button not found'
})()"""

result = d.evaluate_js(expr)
print(result)
