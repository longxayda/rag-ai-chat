from ..llm.ollama import call_ollama
from ..prompts.entity_link import build_entity_link_prompt


async def confirm_entity_link(text, name_a, name_b):
    prompt = build_entity_link_prompt(text, name_a, name_b)
    return await call_ollama(prompt)
