import json
import re

import httpx

from config import settings


async def call_llm(system: str, user: str, temperature: float = 0.1, max_tokens: int = 4096) -> str:
    """调用DeepSeek LLM，返回响应文本"""
    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{settings.llm_api_base}/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


def parse_llm_json(response: str) -> list[dict]:
    """从LLM响应中提取JSON数组，兼容markdown代码块包裹"""
    text = response.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    else:
        start = text.find("[")
        end = text.rfind("]")
        if start != -1 and end > start:
            text = text[start : end + 1]

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        items = re.findall(r"\{[^{}]*\}", text)
        result = []
        for item in items:
            try:
                result.append(json.loads(item))
            except json.JSONDecodeError:
                continue
        return result
