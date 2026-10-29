import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find star button
expr = """(function(){
  var all=document.querySelectorAll('*');
  var stars=[];
  for(var i=0;i<all.length;i++){
    var el=all[i];
    var text=el.textContent.trim();
    var cls=el.className||'';
    var id=el.id||'';
    if(text.includes('star')||text.includes('Star')||cls.includes('star')||id.includes('star')||cls.includes('Star')||id.includes('Star')){
      stars.push({tag:el.tagName,text:text.substring(0,50),id:id,cls:cls.substring(0,100),vis:el.offsetWidth>0});
    }
  }
  return JSON.stringify(stars);
})()"""

result = d.evaluate_js(expr)
print(result)
