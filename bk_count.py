import sys
lines = open(r"C:\Users\chris\StudentSyncSA\server.py", encoding="utf-8").read().split(chr(10))
tr = 0; im = 0; ofs = 0
for i in range(4010, 4049):
    s = lines[i-1].strip()
    if s.startswith("try:") or s.startswith("try\n"):
        tr += 1; im = i
    elif s.startswith("except ") or s == "except:":
        tr -= 1; im = i
    elif s.startswith("except Exception as e:") or s == "except Exception as e:":
        tr -= 1; im = i
    elif s.startswith("elif") or s.startswith("else:"):
        ofs += 1; im = i
now = tr
print("net-try balance 4010-4048:", now, "last marked line:", im)
print("dangling except at 4046 present:", lines[4045].strip().startswith("except"))
# locate the try that 4046's except must pair with, by counting backwards to an UNPAIRED col-0 'try:'
openers = []
for i in range(4010, 4047):
    s = lines[i-1].strip()
    if s.startswith("try:"):
        openers.append(i)
print("try: openers 4010-4046:", openers)
# now find how many excepts exist 4012..4046
exs = []
for i in range(4012, 4047):
    if lines[i-1].strip().startswith("except"):
        exs.append(i)
print("except lines 4012-4046:", exs)
