import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Fill in all mandatory fields
expr = """(function(){
  // Set oapOldNew to N (new student)
  var oldNew=document.getElementById('oapOldNew');
  if(oldNew){oldNew.value='N';oldNew.dispatchEvent(new Event('change',{bubbles:true}));}
  
  // Set oapReturnYesNo to N (not returning)
  var returnYesNo=document.getElementById('oapReturnYesNo');
  if(returnYesNo){returnYesNo.value='N';returnYesNo.dispatchEvent(new Event('change',{bubbles:true}));}
  
  // Set oapTokenYesNo to N (no token)
  var tokenYesNo=document.getElementById('oapTokenYesNo');
  if(tokenYesNo){tokenYesNo.value='N';tokenYesNo.dispatchEvent(new Event('change',{bubbles:true}));}
  
  // Check oapAcceptPopi checkbox
  var acceptPopi=document.getElementById('oapAcceptPopi');
  if(acceptPopi&&!acceptPopi.checked){acceptPopi.checked=true;acceptPopi.dispatchEvent(new Event('change',{bubbles:true}));}
  
  // Enable Next button
  var nextBtn=document.getElementById('oapNextBtn1');
  if(nextBtn)nextBtn.disabled=false;
  
  return 'fields set'
})()"""

result = d.evaluate_js(expr)
print(result)
