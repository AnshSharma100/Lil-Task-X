import requests
headers = {
    'Authorization': 'Bearer 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',
    'Accept': 'application/json'
}
resp = requests.get('https://integrate.api.nvidia.com/v1/models', headers=headers)
print(resp.status_code)
print(resp.text[:200])
