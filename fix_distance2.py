with open('server.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the tool_get_distance function definition (around line 7728)
# and the TOOLS dict (around line 7661)
# Move tool_get_distance before TOOLS

# Find TOOLS = {
tools_start = None
for i, line in enumerate(lines):
    if line.strip() == 'TOOLS = {':
        tools_start = i
        break

# Find def tool_get_distance
dist_start = None
dist_end = None
for i, line in enumerate(lines):
    if line.strip().startswith('def tool_get_distance'):
        dist_start = i
        break

# Find the end of tool_get_distance (next def or class at column 0)
for i in range(dist_start + 1, len(lines)):
    if lines[i].startswith('def ') or lines[i].startswith('class '):
        dist_end = i
        break
if dist_end is None:
    dist_end = dist_start + 1

print(f'TOOLS dict at line {tools_start+1}')
print(f'tool_get_distance at line {dist_start+1} to {dist_end}')

# Extract the tool_get_distance function
func_lines = lines[dist_start:dist_end]

# Remove it from its current position
new_lines = lines[:dist_start] + lines[dist_end:]

# Insert it before TOOLS = {
new_lines = new_lines[:tools_start] + func_lines + ['\n'] + new_lines[tools_start:]

with open('server.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Done - tool_get_distance moved before TOOLS dict')