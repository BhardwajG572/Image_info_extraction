import requests
payload = {
    'image_id': 'test',
    'image_b64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8Xw8AAgMBg6q9j7EAAAAASUVORK5CYII=',
    'model_key': 'Google Gemma 4 (31B-It)'
}
try:
    r = requests.post('http://127.0.0.1:8000/extract', json=payload, timeout=120)
    print('STATUS', r.status_code)
    print('TEXT', r.text)
except Exception as e:
    print('ERROR', e)
