import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Look at the Quick Link area
expr = """(function(){
  var div=document.getElementById('ITS_OAP');
  var children=div.children;
  var result=[];
  for(var i=0;i<Math.min(children.length,15);i++){
    var child=children[i];
    result.push({
      tag:child.tagName,
      id:child.id,
      cls:child.className.substring(0,100),
      text:child.textContent.trim().substring(0,300),
      vis:child.offsetWidth>0,
      childCount:child.children.length
    });
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
