
import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("X_BEARER_TOKEN")

if not token:
    print("ERROR: X_BEARER_TOKEN not found in .env")
    raise SystemExit(1)

url = "https://api.x.com/2/tweets/search/recent"

params = {
    "query": "from:XDevelopers",
    "max_results": 10
}

headers = {
    "Authorization": f"Bearer {token}"
}

try:
    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=30
    )

    print("HTTP Status:", response.status_code)

    if response.ok:
        data = response.json()
        posts = data.get("data", [])
        print("X API connection successful!")
        print("Posts received:", len(posts))

        for post in posts[:3]:
            print("-", post["text"][:150])
    else:
        print("X API returned an error:")
        print(response.text[:1500])

except requests.RequestException as error:
    print("Connection error:", error)
