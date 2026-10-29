import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate directly to page 2
expr = """(function(){
  window.location.href='https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?process_code=ITS_OAP&page_code=ITS_OAP02';
  return 'navigating to page 2'
})()"""

result = d.evaluate_js(expr)
print(result)
