import requests
import base64

def chat_with_media(infer_url, media_files, query: str, stream: bool = False):
    headers = {
        "Authorization": "Bearer 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",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if stream:
        headers["Accept"] = "text/event-stream"

    system_prompt = "/think"
    messages = [
        {
            "role": "system",
            "content": system_prompt,
        },
        {
            "role": "user",
            "content": query,
        }
    ]
    payload = {
        "max_tokens": 4096,
        "temperature": 1,
        "top_p": 1,
        "frequency_penalty": 0,
        "presence_penalty": 0,
        "messages": messages,
        "stream": stream,
        "model": "nvidia/nemotron-nano-12b-v2-vl",
    }
    response = requests.post(infer_url, headers=headers, json=payload, stream=stream)
    print(response.status_code)
    print(response.text[:200])

chat_with_media("https://integrate.api.nvidia.com/v1/chat/completions", [], "Describe the scene")
