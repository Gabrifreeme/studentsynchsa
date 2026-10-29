import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Look at the breadcrumbs area in detail
expr = """(function(){
  var bc=document.getElementById('breadCrumbs');
  if(!bc) return 'breadCrumbs not found';
  var children=bc.querySelectorAll('*');
  var result=[];
  for(var i=0;i<children.length;i++){
    var child=children[i];
    result.push({
      tag:child.tagName,
      id:child.id,
      cls:child.className.substring(0,100),
      text:child.textContent.trim().substring(0,100),
      vis:child.offsetWidth>0,
      rect:JSON.stringify(child.getBoundingClientRect())
    });
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
