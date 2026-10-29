import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Look at the H1 and surrounding area for the Star
expr = """(function(){
  var h1=document.querySelector('h1');
  if(!h1) return 'h1 not found';
  var parent=h1.parentElement;
  var children=parent.children;
  var result=[];
  for(var i=0;i<children.length;i++){
    var child=children[i];
    var rect=child.getBoundingClientRect();
    result.push({
      tag:child.tagName,
      id:child.id,
      cls:child.className.substring(0,100),
      text:child.textContent.trim().substring(0,100),
      vis:child.offsetWidth>0,
      right:rect.right,
      top:rect.top
    });
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
