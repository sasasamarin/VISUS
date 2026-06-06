"""Crossref — мировой индекс DOI. Берём только journal-article (отсекает препринты/новости)."""
import re
from datetime import date, timedelta

import httpx

from src.config import settings
from src.db import Document

BASE = "https://api.crossref.org/works"
_TAG = re.compile(r"<[^>]+>")


def _strip(text: str) -> str:
    if not text:
        return ""
    text = _TAG.sub(" ", text)
    text = re.sub(r"\s+", " ", text).replace("Abstract", "", 1).strip()
    return text.lstrip(":：. ").strip()


async def search(client: httpx.AsyncClient, term: str, rows: int, lookback_days: int) -> list[Document]:
    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    params = {
        "query": term,
        "filter": f"from-pub-date:{since},type:journal-article",
        "rows": rows,
        "sort": "published",
        "order": "desc",
        "select": "DOI,title,abstract,author,container-title,published,subject",
    }
    if settings.ncbi_email:
        params["mailto"] = settings.ncbi_email
    r = await client.get(BASE, params=params, timeout=30,
                         headers={"User-Agent": "mntk-eye-bot/1.0"})
    r.raise_for_status()
    items = r.json().get("message", {}).get("items", [])

    docs: list[Document] = []
    for it in items:
        doi = (it.get("DOI") or "").lower()
        title = (it.get("title") or [""])[0]
        if not title or not doi:
            continue
        authors = []
        for a in it.get("author", []):
            fam, giv = a.get("family"), a.get("given", "")
            if fam:
                authors.append(f"{fam} {giv[:1]}".strip())
        authors_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        parts = (it.get("published", {}).get("date-parts") or [[]])[0]
        pubdate = "-".join(str(p) for p in parts) if parts else ""
        docs.append(Document(
            uid=f"doi:{doi}", source="crossref", doi=doi, title=title,
            abstract=_strip(it.get("abstract", "")), authors=authors_str,
            journal=(it.get("container-title") or [""])[0], pubdate=pubdate,
            url=f"https://doi.org/{doi}",
        ))
    return docs
