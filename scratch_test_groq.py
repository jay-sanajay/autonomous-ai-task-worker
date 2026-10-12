import os
import requests
import json
from dotenv import load_dotenv

load_dotenv("d:/ai-project/.env")
key = os.environ.get("GROQ_API_KEY", "")
print("Using Key:", key[:8] + "..." + key[-4:])

# List models
r = requests.get("https://api.groq.com/openai/v1/models", headers={"Authorization": f"Bearer {key}"})
print("Models status:", r.status_code)
models = [m["id"] for m in r.json().get("data", [])]
print("Available Models:", models)

# Test prompt with openai/gpt-oss-20b or openai/gpt-oss-120b
for test_model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]:
    if test_model in models:
        payload = {
            "model": test_model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant. Always respond with a JSON object."},
                {"role": "user", "content": "Return a JSON object with keys: thought, tool_name, is_finished."}
            ],
            "response_format": {"type": "json_object"}
        }
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json=payload,
            timeout=10
        )
        print(f"Model {test_model} status:", res.status_code)
        if res.status_code == 200:
            print("Content:", res.json()["choices"][0]["message"]["content"])
        else:
            print("Error:", res.text)
