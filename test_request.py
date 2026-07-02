import requests

url = "http://localhost:8000/predict"

# Your server expects a "prompt" field
data = {
    "prompt": "What's the weather like in London?"
}

try:
    response = requests.post(url, json=data)
    print("Status Code:", response.status_code)
    
    if response.status_code == 200:
        print("✅ Success!")
        print("Response:", response.json())
    else:
        print("❌ Error:", response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ Error: Can't connect to server on port 8000")
    print("   Make sure the server is running!")
except Exception as e:
    print(f"❌ Error: {e}")