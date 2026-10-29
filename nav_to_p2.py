import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate to page 2
expr = """(function(){
  // Set the startup fields and submit
  var oldNew=document.getElementById('oapOldNew');
  if(oldNew){oldNew.value='N';oldNew.dispatchEvent(new Event('change',{bubbles:true}));}
  
  var returnYesNo=document.getElementById('oapReturnYesNo');
  if(returnYesNo){returnYesNo.value='N';returnYesNo.dispatchEvent(new Event('change',{bubbles:true}));}
  
  var acceptPopi=document.getElementById('oapAcceptPopi');
  if(acceptPopi&&!acceptPopi.checked){acceptPopi.checked=true;acceptPopi.dispatchEvent(new Event('change',{bubbles:true}));}
  
  var nextBtn=document.getElementById('oapNextBtn1');
  if(nextBtn){nextBtn.disabled=false;nextBtn.click();return 'submitted'}
  return 'not found'
})()"""

result = d.evaluate_js(expr)
print(result)
