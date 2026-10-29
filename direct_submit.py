import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Direct form submission
expr = """(function(){
  var f=document.forms[0];
  // Create a temporary form to submit
  var tempForm=document.createElement('form');
  tempForm.method='POST';
  tempForm.action=f.action||window.location.href;
  
  // Copy all form elements
  for(var i=0;i<f.elements.length;i++){
    var e=f.elements[i];
    if(e.name){
      var input=document.createElement('input');
      input.type='hidden';
      input.name=e.name;
      input.value=e.value;
      tempForm.appendChild(input)
    }
  }
  
  document.body.appendChild(tempForm);
  tempForm.submit();
  return 'submitted'
})()"""

result = d.evaluate_js(expr)
print(result)
