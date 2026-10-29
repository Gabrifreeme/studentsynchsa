import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Step 1: Inspect the form and add missing parameters
expr = """(function(){
  var form=document.forms[0];
  if(!form) return 'no form';
  
  // Check current form action
  var info={
    action:form.action,
    method:form.method,
    elements:[]
  };
  
  // Add p_proc parameter
  var procInput=document.createElement('input');
  procInput.type='hidden';
  procInput.name='p_proc';
  procInput.value='ITS_OAP03';
  form.appendChild(procInput);
  
  // Add p_page parameter
  var pageInput=document.createElement('input');
  pageInput.type='hidden';
  pageInput.name='p_page';
  pageInput.value='3';
  form.appendChild(pageInput);
  
  // Submit the form
  form.submit();
  return 'submitted with p_proc=ITS_OAP03 and p_page=3'
})()"""

result = d.evaluate_js(expr)
print(result)
