import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find star button
expr = """(function(){
  var buttons=document.querySelectorAll('button, a, input[type=button], input[type=submit]');
  var result=[];
  for(var i=0;i<buttons.length;i++){
    var b=buttons[i];
    result.push({text:b.textContent.trim().substring(0,50),id:b.id,cls:b.className,vis:b.offsetWidth>0});
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
