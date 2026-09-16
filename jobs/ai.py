import json
import httpx
from django.conf import settings

URL = "https://openrouter.ai/api/v1/chat/completions"


def ask(prompt: str) -> str | None:
    key = settings.OPENROUTER_API_KEY
    if not key:
        return None
    payload = {"model": settings.OPENROUTER_MODEL, "messages": [{"role": "user", "content": prompt + " Return only a JSON object with summary, experience, and projects fields."}], "temperature": 0.2}
    try:
        response = httpx.post(URL, json=payload, headers={"Authorization": f"Bearer {key}"}, timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError, json.JSONDecodeError):
        return None
