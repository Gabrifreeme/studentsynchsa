import requests

url = "http://localhost:8000/predict"
data = {"prompt": "What's the weather like in London?"}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    if response.status_code == 200:
        print("✅ Success!")
        print("Response:", response.json())
    else:
        print("❌ Error:", response.text)
except Exception as e:
    print(f"❌ Error: {e}")