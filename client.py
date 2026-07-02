import requests, json, sys

URL = "http://127.0.0.1:8000/predict"

def ask(prompt):
    resp = requests.post(URL, json={"prompt": prompt}, timeout=120)
    return resp.text

if __name__ == "__main__":
    for p in [
        "What's the weather like in London?",
        "What's on npr.org right now?",
        "Weather in Tokyo and a snippet from wikipedia.org",
    ]:
        print(f"\n=== {p} ===", flush=True)
        try:
            print(ask(p), flush=True)
        except Exception as e:
            print(f"Error: {e}", flush=True)
