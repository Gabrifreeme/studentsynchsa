import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Get all form fields
expr = """(function(){
  var f=document.forms[0];
  if(!f) return 'no form';
  var fields=[];
  for(var i=0;i<f.elements.length;i++){
    var e=f.elements[i];
    fields.push({name:e.name,id:e.id,type:e.type,value:e.value,mandatory:e.getAttribute('mandatory'),disabled:e.disabled,visible:e.offsetWidth>0})
  }
  return JSON.stringify(fields);
})()"""

result = d.evaluate_js(expr)
print(result)
