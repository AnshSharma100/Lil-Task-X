from app.llm_connector import NemotronClient
feature = {
    'name': 'Test Feature',
    'description': 'Say hello',
    'tags': ['sample']
}
client = NemotronClient()
res = client.evaluate_feature_match(feature, 'dummy.py', 'print("hello")')
print(res)
