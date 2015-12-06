import requests

requests.post('http://127.0.0.1:5000/get_shipping_rate', data={'destination_zip':'78749', 'origin_zip': '60660', 'weight': 1.2})