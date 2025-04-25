import requests

def test_api():
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    headers = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {response.headers}")
        print(f"Data: {data[:2]}")  # Print first 2 items only
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api() 