import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Try direct URL navigation to page 3
expr = """(function(){
  // Try different URL patterns for page 3
  window.location.href='https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p_proc=ITS_OAP03&p_page=3';
  return 'navigating to gw1view with p_proc=ITS_OAP03'
})()"""

result = d.evaluate_js(expr)
print(result)
