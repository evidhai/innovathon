import requests
import json

# Try different possible endpoints
endpoints = [
    "http://localhost:8080/invoke",
    "http://localhost:8080/",
    "http://localhost:8000/invoke",
    "http://localhost:8000/",
]

payload = {
    "input": "What is the pricing for S3 standard storage in us-east-1?",
    "user_id": "12345",
    "context": {
        "timezone": "Asia/Tokyo",
        "language": "en"
    }
}

print(f"Payload: {json.dumps(payload, indent=2)}\n")

for url in endpoints:
    print(f"Trying {url}...")
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 404:
            print(f"✓ Success! Status Code: {response.status_code}")
            print(f"\nResponse:\n{response.text}")
            break
    except requests.exceptions.RequestException as e:
        print(f"✗ Failed: {e}")
        continue
else:
    print("\nAll endpoints failed. Check if the agent is running.")
