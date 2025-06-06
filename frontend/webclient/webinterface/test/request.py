import requests

response = requests.get(
            f"http://192.168.1.46:8001/api/account/",
            auth=("test1@test.com", "test1"),
            headers={'Content-Type': 'application/json'}
        )

if response.ok:
    data = response.json()
    print(data)
else:
    print("Authentication failed:", response.status_code, response.text)
    data = {"error": "Authentication failed"}
print("Response data:", data)

