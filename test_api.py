import urllib.request
import json

url = "http://127.0.0.1:8001/openapi.json"
try:
    with urllib.request.urlopen(url) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(f"Paths: {list(result['paths'].keys())}")
except Exception as e:
    print(f"Error: {e}")
