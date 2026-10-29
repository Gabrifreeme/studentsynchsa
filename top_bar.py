import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Look at the top bar area
expr = """(function(){
  var body=document.body;
  var children=body.children;
  var result=[];
  for(var i=0;i<Math.min(children.length,10);i++){
    var child=children[i];
    result.push({
      tag:child.tagName,
      id:child.id,
      cls:child.className.substring(0,100),
      text:child.textContent.trim().substring(0,200),
      vis:child.offsetWidth>0,
      childCount:child.children.length
    });
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
