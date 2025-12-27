from ..llm.ollama import call_ollama
from ..prompts.people_link import build_people_link_prompt


async def confirm_people_link(text, name_a, name_b):
    prompt = build_people_link_prompt(text, name_a, name_b)
    return await call_ollama(prompt)
