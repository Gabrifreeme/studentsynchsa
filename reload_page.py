import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Try to reload the page
result = d.evaluate_js("location.reload()")
print("Reload result:", result)
