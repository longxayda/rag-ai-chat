import httpx
import json5
import re
from .prompt import build_heritage_prompt, build_people_prompt

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:1b"


def strip_code_block(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text

async def call_ollama(prompt: str, num_ctx=2048) -> str:
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0, "num_ctx": num_ctx}
    }
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(OLLAMA_URL, json=payload)
    if res.status_code != 200:
        print("❌ Ollama error:", res.text)
        return ""
    return res.json().get("response", "").strip()

async def extract_heritages_from_chunks(chunks: list[str]) -> list[dict]:
    if not chunks:
        return []

    prompt = build_heritage_prompt(chunks)
    text = await call_ollama(prompt)
    if not text:
        return []

    # Lọc JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        print("⚠️ No JSON array found in heritage extraction")
        print(text)
        return []

    try:
        heritages = json5.loads(match.group(0))
    except Exception as e:
        print("⚠️ Failed to parse JSON (heritages):", e)
        print(text)
        return []

    # Chuẩn hóa
    for h in heritages:
        if "year" in h and isinstance(h["year"], str) and h["year"].isdigit():
            h["year"] = int(h["year"])
        if "category" in h and h["category"] not in ["cultural", "natural", "mixed"]:
            h["category"] = "cultural"

    return heritages


async def extract_people_from_chunks(chunks: list[str]) -> list[dict]:
    if not chunks:
        return []

    prompt = build_people_prompt(chunks)
    text = await call_ollama(prompt)
    if not text:
        return []

    text = strip_code_block(text)
    # Lọc JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        print("⚠️ No JSON array found in people extraction")
        print(text)
        return []

    try:
        people = json5.loads(match.group(0))
    except Exception as e:
        print("⚠️ Failed to parse JSON (people):", e)
        print(text)
        return []

    # Chuẩn hóa
    for p in people:
        if "birth_year" in p and isinstance(p["birth_year"], str) and p["birth_year"].isdigit():
            p["birth_year"] = int(p["birth_year"])
        if "death_year" in p and isinstance(p["death_year"], str) and p["death_year"].isdigit():
            p["death_year"] = int(p["death_year"])

    return people
