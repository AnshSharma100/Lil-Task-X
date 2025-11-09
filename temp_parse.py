from app.llm_connector import _parse_llm_json
import importlib, app.llm_connector as connector
importlib.reload(connector)
from app.llm_connector import _parse_llm_json
text = '`json\n{\n  "score": 0.8,\n  "summary": "Test"\n}\n`\n'
print(connector._parse_llm_json(text))
