import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find elements on the right side of the page (x > 600)
expr = """(function(){
  var all=document.querySelectorAll('*');
  var result=[];
  for(var i=0;i<all.length;i++){
    var el=all[i];
    var rect=el.getBoundingClientRect();
    if(rect.right>900&&rect.top<100&&rect.width>0){
      result.push({
        tag:el.tagName,
        id:el.id,
        cls:el.className.substring(0,100),
        text:el.textContent.trim().substring(0,100),
        x:Math.round(rect.x),
        y:Math.round(rect.y),
        w:Math.round(rect.width),
        h:Math.round(rect.height)
      });
    }
  }
  return JSON.stringify(result);
})()"""

result = d.evaluate_js(expr)
print(result)
