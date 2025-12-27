# linking/llm/ollama.py

import httpx
import json
import asyncio

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"

DEFAULT_OPTIONS = {
    "temperature": 0,
    "num_ctx": 768,     # ⚠️ thấp để tránh OOM
    "top_p": 0.9
}


async def call_ollama(prompt: str, options: dict | None = None) -> dict:
    """
    Gọi Ollama và BẮT BUỘC trả về JSON dict
    Nếu parse fail → return {"related": False}
    """

    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": options or DEFAULT_OPTIONS
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(OLLAMA_URL, json=payload)

        if res.status_code != 200:
            return {"related": False}

        text = res.json().get("response", "").strip()

        # 🔒 CẮT JSON AN TOÀN
        start = text.find("{")
        end = text.rfind("}") + 1

        if start == -1 or end == -1:
            return {"related": False}

        return json.loads(text[start:end])

    except (json.JSONDecodeError, httpx.HTTPError, asyncio.TimeoutError):
        return {"related": False}
