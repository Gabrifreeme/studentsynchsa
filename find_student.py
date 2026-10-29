import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Find student number select
expr = """(function(){
  var sel=document.querySelector('select[name*="student"]');
  if(!sel){
    var all=document.querySelectorAll('select');
    var info=[];
    for(var i=0;i<all.length;i++){info.push(all[i].name)}
    return 'selects: '+info.join(', ')
  }
  return 'found: '+sel.name
})()"""

result = d.evaluate_js(expr)
print(result)
