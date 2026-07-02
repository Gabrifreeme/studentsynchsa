import requests

# Test POST requests to different endpoints
endpoints = [
    "http://localhost:8000/",
    "http://localhost:8000/predict",
]

# Sample data to send
data = {
    "message": "Hello, can you help me?",
    "mode": "chat"
}

print("Testing POST requests...")
print("-" * 50)

for url in endpoints:
    try:
        response = requests.post(url, json=data)
        print(f"✓ POST {url}")
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                print(f"  Response: {response.json()}")
            except:
                print(f"  Response: {response.text[:200]}...")
        else:
            print(f"  Error: {response.text[:200]}...")
        print("-" * 50)
        
    except requests.exceptions.ConnectionError:
        print(f"✗ {url}")
        print(f"  Error: Can't connect to server")
        print("-" * 50)
    except Exception as e:
        print(f"✗ {url}")
        print(f"  Error: {e}")
        print("-" * 50)

# Also test if the root endpoint works with a GET (the 405 suggests it's POST only)
print("\nTesting with different data formats...")
print("-" * 50)

# Try with the Authorization header from your original code
headers = {
    "Authorization": "Bearer 4HF5GRQ-DNB4CT8-QDNFZRK-9ARM0MF",
    "Content-Type": "application/json"
}

try:
    response = requests.post("http://localhost:8000/", json=data, headers=headers)
    print(f"✓ POST / with auth header")
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text[:200]}")
except Exception as e:
    print(f"✗ Error: {e}")