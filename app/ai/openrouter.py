import json
import httpx

from app.config import settings

BASE = "https://openrouter.ai/api/v1"

class OpenRouter:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=90, headers={
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "X-Title": "Personal Knowledge Bot",
        })

    async def close(self):
        await self.client.aclose()

    async def embed(self, text: str) -> list[float]:
        r = await self.client.post(f"{BASE}/embeddings", json={
            "model": settings.openrouter_embed_model,
            "input": text[:30000],
            "encoding_format": "float",
        })
        r.raise_for_status()
        return r.json()["data"][0]["embedding"]

    async def analyze(self, text: str) -> dict:
        prompt = """Analyze the user's saved knowledge item. Return ONLY valid JSON with keys:
 title (short string), summary (1-3 sentences), category (programming/business/education/ai/ideas/tools/other),
 note_type (knowledge/guide/code/article/idea/resource/quote/video/other), tags (array of 2-8 lowercase strings).
 Preserve factual meaning and do not invent information.

TEXT:
""" + text[:18000]
        r = await self.client.post(f"{BASE}/chat/completions", json={
            "model": settings.openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 500,
            "reasoning": {"enabled": False},
        })
        r.raise_for_status()
        raw = r.json()["choices"][0]["message"]["content"]
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        data = json.loads(raw)
        return data

    async def answer(self, query: str, notes: list[dict]) -> str:
        context = "\n\n".join(
            f"[{n['id']}] {n.get('title') or 'Без названия'}\n{n['content'][:5000]}"
            for n in notes
        )
        prompt = f"""Answer the user's question using ONLY the saved materials below. If they don't contain enough information, say so. Be concise.

QUESTION:
{query}

SAVED MATERIALS:
{context}
"""
        r = await self.client.post(f"{BASE}/chat/completions", json={
            "model": settings.openrouter_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 900,
            "reasoning": {"enabled": False},
        })
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
