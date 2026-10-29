import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Navigate to main portal URL to establish session
result = d.evaluate_js("window.location.href = 'https://univenierp01.univen.ac.za/pls/prodi41/gen.gw1pkg.gw1view'")
print("Navigate result:", result)
