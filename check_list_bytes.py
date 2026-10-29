with open(r'C:\Users\chris\StudentSyncSA\server.py', 'rb') as f:
    content = f.read()

# Find TOOLS_SCHEMA
start = content.find(b'TOOLS_SCHEMA = [')
if start == -1:
    print("TOOLS_SCHEMA not found")
else:
    eq_pos = content.find(b'=', start)
    list_start = content.find(b'[', start)
    
    bracket_count = 0
    in_string = False
    escape = False
    quote_char = None
    end = start
    for i, ch in enumerate(content[list_start:], start=list_start):
        if not in_string:
            if ch in (ord(b'"'), ord(b"'")):
                in_string = True
                quote_char = ch
            elif ch == ord('['):
                bracket_count += 1
            elif ch == ord(']'):
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
        else:
            if escape:
                escape = False
            elif ch == ord(b'\\'):
                escape = True
            elif ch == quote_char:
                in_string = False
                quote_char = None

    list_bytes = content[list_start:end]
    
    # Find run_command in the list bytes
    idx = list_bytes.find(b'run_command')
    if idx >= 0:
        print(f'Found run_command at list byte index {idx}')
        print(repr(list_bytes[max(0,idx-100):idx+100]))
    else:
        print('run_command NOT found in list bytes')
        
    # Check the total list length
    print(f'List byte length: {len(list_bytes)}')
    print(f'List start byte: {list_start}, end byte: {end}')
    
    # Check what's at the end of the list
    print('Last 200 bytes of list:')
    print(repr(list_bytes[-200:]))