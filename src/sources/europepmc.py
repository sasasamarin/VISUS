"""Клиент Europe PMC — второй источник (шире PubMed, есть препринты)."""
from datetime import date, timedelta

import httpx

from src.config import settings
from src.db import Document

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


async def search(client: httpx.AsyncClient, term: str, page_size: int, lookback_days: int) -> list[Document]:
    since = (date.today() - timedelta(days=lookback_days)).isoformat()
    today = date.today().isoformat()
    query = f"({term}) AND (FIRST_PDATE:[{since} TO {today}])"
    params = {
        "query": query, "format": "json", "pageSize": page_size,
        "resultType": "core", "sort": "P_PDATE_D desc",
    }
    r = await client.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    results = r.json().get("resultList", {}).get("result", [])

    docs: list[Document] = []
    for it in results:
        pmid = it.get("pmid", "") or ""
        doi = (it.get("doi", "") or "").lower()
        src = it.get("source", "")
        eid = it.get("id", "")
        if pmid:
            uid, url = f"pmid:{pmid}", f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        elif doi:
            uid, url = f"doi:{doi}", f"https://doi.org/{doi}"
        else:
            uid, url = f"epmc:{src}:{eid}", f"https://europepmc.org/article/{src}/{eid}"
        docs.append(Document(
            uid=uid, source="europepmc", pmid=pmid, doi=doi,
            title=it.get("title", ""), abstract=it.get("abstractText", ""),
            authors=it.get("authorString", ""), journal=it.get("journalTitle", ""),
            pubdate=it.get("firstPublicationDate", ""), url=url,
        ))
    return docs
