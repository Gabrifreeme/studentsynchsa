import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Force reconnect
result = d.connect_cmd()
print("Connect:", result)
