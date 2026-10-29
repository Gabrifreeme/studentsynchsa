import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate to UNIVEN ITS Portal page 2
result = d.evaluate_js("window.location.href = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view?p_proc=ITS_OAP02&p_page=2'")
print("Navigate result:", result)
