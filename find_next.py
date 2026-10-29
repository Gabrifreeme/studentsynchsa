import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find Next button
expr = """(function(){
  var btns=document.querySelectorAll('button, input[type=button], input[type=submit]');
  var result=[];
  for(var i=0;i<btns.length;i++){
    var b=btns[i];
    var text=b.textContent.trim()||b.value;
    if(text){
      result.push({text:text,id:b.id,cls:b.className,disabled:b.disabled})
    }
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
