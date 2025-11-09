from app.llm_connector import NemotronClient
client = NemotronClient()
print('base', client.base_url)
print('model', client.model)
print('timeout', client.timeout)
print('has_key', bool(client.api_key))
print('key_prefix', client.api_key[:8])
