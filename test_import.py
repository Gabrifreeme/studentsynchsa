import sys
sys.path.insert(0, r'C:\Users\chris\StudentSyncSA')

# Try to import the module and see what happens
try:
    import server
    print(f"TOOLS_SCHEMA length: {len(server.TOOLS_SCHEMA)}")
    names = [t['function']['name'] for t in server.TOOLS_SCHEMA]
    print(f"run_command in TOOLS_SCHEMA: {'run_command' in [t['function']['name'] for t in server.TOOLS_SCHEMA]}")
except Exception as e:
    print(f"Error importing: {e}")
    import traceback
    traceback.print_exc()