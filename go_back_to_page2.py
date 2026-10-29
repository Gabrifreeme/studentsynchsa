import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate back to page 2
nav_expr = "window.location.href = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p_proc=ITS_OAP02&p_page=2'"
result = d.evaluate_js(nav_expr)
print("Navigate result:", result)
