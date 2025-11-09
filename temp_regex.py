import re
text = '`json\n{\n  "score": 0.8,\n  "summary": "Test"\n}\n`\n'
match = re.search(r"`(?:json)?\s*(.*?)\s*`", text, flags=re.DOTALL | re.IGNORECASE)
print('matched', bool(match))
if match:
    print('content:', match.group(1))
