import requests
from app.llm_connector import NemotronClient
client = NemotronClient()
payload = {
    'model': client.model,
    'messages': [
        {'role': 'system', 'content': 'Testing'},
        {'role': 'user', 'content': 'Hello'},
    ]
}
resp = requests.post(f"{client.base_url}/chat/completions", json=payload, headers=client._make_headers(), timeout=client.timeout)
print('request body', resp.request.body)
print('status', resp.status_code)
print('text', resp.text)
