import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')
import devtools_service as d

# Use CDP network events to inspect what the WebView actually requested
print("Network requests:", d.get_network_requests())
print("Console logs:", d.get_console_logs())
