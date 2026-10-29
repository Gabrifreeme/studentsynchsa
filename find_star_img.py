import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find all images and clickable elements in the top area
expr = """(function(){
  var all=document.querySelectorAll('img, svg, [class*=icon], [class*=star], [class*=favorite], [data-action], [title*=star], [title*=auto]');
  var result=[];
  for(var i=0;i<all.length;i++){
    var el=all[i];
    var rect=el.getBoundingClientRect();
    if(rect.width>0&&rect.top<150){
      result.push({
        tag:el.tagName,
        id:el.id,
        cls:el.className.substring(0,100),
        src:el.src||'',
        title:el.title||'',
        alt:el.alt||'',
        text:el.textContent.trim().substring(0,50),
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
