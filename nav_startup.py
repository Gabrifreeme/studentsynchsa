import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate to startup page
expr = """(function(){
  window.location.href='https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1startup?x_processcode=ITS_OAP';
  return 'navigating to startup'
})()"""

result = d.evaluate_js(expr)
print(result)
