import requests
from app.llm_connector import NemotronClient
client = NemotronClient()
feature = {
    'name': 'Test Feature',
    'description': 'Say hello',
    'tags': ['sample']
}
system_prompt = (
    "You evaluate whether a code snippet implements a feature. "
    "Respond with JSON containing score (0.0 to 1.0) and summary explaining the rationale."
    " Score 1.0 means the code fully delivers the feature; 0.0 means it is unrelated."
)
user_content = (
    f"Feature Name: {feature['name']}\n"
    f"Feature Description: {feature['description']}\n"
    f"Feature Labels/Tags: sample\n"
    f"Repository File Path: dummy.py\n"
    "Provide your JSON response after reviewing the following code snippet:\n"
    "`\n"
    "print(\"hello\")\n"
    "`"
)
payload = {
    'model': client.model,
    'messages': [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_content},
    ]
}
resp = requests.post(f"{client.base_url}/chat/completions", json=payload, headers=client._make_headers(), timeout=client.timeout)
print('status', resp.status_code)
print('text', resp.text)
