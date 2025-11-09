import requests
from app.llm_connector import NemotronClient
client = NemotronClient()
resp = requests.post(f"{client.base_url}/chat/completions", json={'model': client.model, 'messages': []}, headers=client._make_headers(), timeout=client.timeout)
print(resp.url)
