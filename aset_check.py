import ast, sys
src = open(r"C:\Users\chris\StudentSyncSA\server.py", encoding="utf-8").read()
lines = src.splitlines()
try:
    ast.parse(src)
    print("AST OK")
except SyntaxError as e:
    print("SYNTAXERR line", e.lineno, "offset", e.offset, "msg", e.msg)
    l = e.lineno
    lo = max(1, l - 10); hi = min(l + 8, len(lines))
    for i in range(lo, hi + 1):
        print("%5d |%s|" % (i, lines[i - 1]))
