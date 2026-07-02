import requests

url = "http://localhost:3001/api/v1/workspace/my-workspace/chat"

headers = {
    "Authorization": "Bearer 4HF5GRQ-DNB4CT8-QDNFZRK-9ARM0MF",
    "Content-Type": "application/json"
}

data = {
    "message": "Hello, can you help me?",
    "mode": "chat"
}

# Make the POST request
response = requests.post(url, json=data, headers=headers)

# Print the response
print(response.json())