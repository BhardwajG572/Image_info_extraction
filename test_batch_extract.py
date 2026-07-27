import requests

BACKEND_URL = "http://127.0.0.1:8000"

def test_extract_batch():
    payload = {
        "images": [
            {
                "image_id": "t1",
                "image_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAgMBg6q9j7EAAAAASUVORK5CYII=",
                "model_key": "Google Gemma 4 (31B-It)",
                "temperature": 0.1,
            },
            {
                "image_id": "t2",
                "image_b64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAgMBg6q9j7EAAAAASUVORK5CYII=",
                "model_key": "Google Gemma 4 (31B-It)",
                "temperature": 0.1,
            },
        ]
    }
    resp = requests.post(f"{BACKEND_URL}/extract_batch", json=payload, timeout=120)
    print(resp.status_code)
    print(resp.text)


if __name__ == "__main__":
    test_extract_batch()
