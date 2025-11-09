import json
import re
text = '`json\n{\n  "score": 0.8,\n  "summary": "Test"\n}\n`\n'
candidate = text.strip()
match = re.search(r"`(?:json)?\s*(.*?)\s*`", candidate, flags=re.DOTALL | re.IGNORECASE)
if match:
    candidate = match.group(1)
print('candidate repr:', repr(candidate))
print(json.loads(candidate))
