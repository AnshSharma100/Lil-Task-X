import requests
from app.llm_connector import NemotronClient
client = NemotronClient()
payload = {
    'model': client.model,
    'messages': [
        {'role': 'system', 'content': 'Hi'},
        {'role': 'user', 'content': 'Hello'},
    ]
}
resp = requests.post(f"{client.base_url}/chat/completions", json=payload, headers=client._make_headers(), timeout=client.timeout)
print('status', resp.status_code)
print('headers', resp.headers)
print('body', resp.text)
