import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Check all mandatory fields including hidden
expr = """(function(){
  var f=document.forms[0];
  var missing=[];
  for(var i=0;i<f.elements.length;i++){
    var e=f.elements[i];
    if(e.getAttribute('mandatory')==='Y'&&(e.value==='-1'||e.value===''||e.value===' ')){
      missing.push({name:e.name,id:e.id,type:e.type,value:e.value,visible:e.offsetWidth>0})
    }
  }
  return JSON.stringify(missing)
})()"""

result = d.evaluate_js(expr)
print(result)
