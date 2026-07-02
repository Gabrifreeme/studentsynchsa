import subprocess, time, requests, os, sys

proc = subprocess.Popen(
    [sys.executable, "app.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

try:
    for i in range(30):
        line = proc.stdout.readline().decode(errors="replace")
        print(line, end="", flush=True)
        if "Running on local URL" in line or "localhost" in line or "Uvicorn" in line:
            print("\n--- Gradio app is running! ---", flush=True)
            break
        if i == 29:
            print("\n--- Timed out waiting for startup ---", flush=True)
finally:
    proc.kill()
