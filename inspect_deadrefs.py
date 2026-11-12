import io
path = r"C:\Users\chris\LipSyncStudent\ACEsi.html"
with io.open(path, "r", encoding="utf-8", newline="") as f:
    lines = f.readlines()
for n in [2688, 2689, 2690, 2691, 2692, 2693, 2694,
          3355, 3356, 3357, 3358, 3359, 3360, 3361,
          5138, 5139, 5140, 5141, 5142, 5143, 5144]:
    raw = lines[n-1].rstrip("\n").rstrip("\r")
    print(f"{n:5}: |{raw}|")
