import subprocess, time, requests, sys, os

proc = subprocess.Popen(
    [sys.executable, "server.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    stdout=sys.stdout,  # Change DEVNULL to sys.stdout
    stderr=sys.stderr,  # Change DEVNULL to sys.stderr
)

try:
    for i in range(20):
        try:
            r = requests.get("http://127.0.0.1:8000", timeout=3)
            print("Server ready!")
            break
        except Exception:
            time.sleep(3)
    else:
        print("Server failed to start")
        exit(1)

    prompts = [
        "What's the weather like in London?",
        "What's on npr.org right now?",
        "Weather in Tokyo and a snippet from wikipedia.org",
    ]
    for p in prompts:
        print(f"\n=== {p} ===", flush=True)
        try:
            r = requests.post("http://127.0.0.1:8000/predict",
                json={"prompt": p}, timeout=120)
            print(r.text, flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)
finally:
    proc.kill()
