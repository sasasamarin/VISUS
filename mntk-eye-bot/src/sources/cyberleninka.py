"""CyberLeninka — русскоязычная научная библиотека.

ВНИМАНИЕ: публичного документированного API нет. Ниже — обращение к внутреннему
поисковому эндпоинту; формат ответа может меняться, поэтому всё обёрнуто аккуратно,
а источник по умолчанию ВЫКЛЮЧЕН (ENABLE_CYBERLENINKA=false). Если включишь и формат
не совпадёт — поправь разбор полей здесь, остальной конвейер не сломается."""
import re

import httpx

from src.db import Document

SEARCH_URL = "https://cyberleninka.ru/api/search"
_TAG = re.compile(r"<[^>]+>")


def _strip(text: str) -> str:
    return re.sub(r"\s+", " ", _TAG.sub(" ", text or "")).strip()


async def search(client: httpx.AsyncClient, term: str, size: int, lookback_days: int) -> list[Document]:
    payload = {"mode": "articles", "q": term, "size": size, "from": 0}
    r = await client.post(SEARCH_URL, json=payload, timeout=30,
                          headers={"User-Agent": "mntk-eye-bot/1.0"})
    r.raise_for_status()
    data = r.json()
    articles = data.get("articles") or data.get("results") or []

    docs: list[Document] = []
    for it in articles:
        link = it.get("link") or it.get("url") or ""
        if not link:
            continue
        url = link if link.startswith("http") else f"https://cyberleninka.ru{link}"
        title = _strip(it.get("name") or it.get("title") or "")
        if not title:
            continue
        docs.append(Document(
            uid=f"cyberleninka:{link}", source="cyberleninka", title=title,
            ru_title=title,  # уже на русском
            abstract=_strip(it.get("annotation") or it.get("abstract") or ""),
            authors=_strip(", ".join(it.get("authors", [])) if isinstance(it.get("authors"), list) else it.get("authors", "")),
            journal=_strip(it.get("journal") or ""),
            pubdate=str(it.get("year") or ""), url=url,
        ))
    return docs
