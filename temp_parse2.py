import app.llm_connector as mod
text = """```json
{
  \"score\": 0.8,
  \"summary\": \"Test\"
}
```
"""
print(mod._parse_llm_json(text))
