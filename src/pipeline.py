"""Конвейер: источники -> дедуп -> проверка/перевод (GPT) -> эмбеддинги -> база.
Ненаучное (scientific=false) отбрасывается. Возвращает статистику."""
import asyncio

import httpx

from src.config import settings
from src import db
from src.sources import pubmed, europepmc, crossref, cyberleninka
from src.ai import embed, enrich_ru


async def _collect() -> dict[str, db.Document]:
    collected: dict[str, db.Document] = {}
    seen_doi: set[str] = set()
    maxn = settings.max_results_per_term
    lookback = settings.lookback_days

    def absorb(docs: list[db.Document]):
        for d in docs:
            if not d.title or d.uid in collected:
                continue
            if d.doi and d.doi in seen_doi:
                continue
            collected[d.uid] = d
            if d.doi:
                seen_doi.add(d.doi)

    async with httpx.AsyncClient() as client:
        for term in settings.search_terms:
            if settings.enable_pubmed:
                try:
                    ids = await pubmed.search_ids(client, term, maxn, lookback)
                    absorb(await pubmed.fetch_details(client, ids))
                except Exception as e:  # noqa: BLE001
                    print(f"[pubmed] '{term}': {e}")
            if settings.enable_europepmc:
                try:
                    absorb(await europepmc.search(client, term, maxn, lookback))
                except Exception as e:  # noqa: BLE001
                    print(f"[europepmc] '{term}': {e}")
            if settings.enable_crossref:
                try:
                    absorb(await crossref.search(client, term, maxn, lookback))
                except Exception as e:  # noqa: BLE001
                    print(f"[crossref] '{term}': {e}")
            await asyncio.sleep(0.2)  # вежливость к API

        if settings.enable_cyberleninka:
            for term in settings.search_terms_ru:
                try:
                    absorb(await cyberleninka.search(client, term, maxn, lookback))
                except Exception as e:  # noqa: BLE001
                    print(f"[cyberleninka] '{term}': {e}")
                await asyncio.sleep(0.2)

    return collected


async def ingest() -> dict:
    collected = await _collect()
    new_docs = [d for d in collected.values() if not db.exists(d)]

    stored: list[db.Document] = []
    rejected = 0

    # 1) проверка + перевод (батчами по 20)
    kept: list[db.Document] = []
    EB = 20
    for i in range(0, len(new_docs), EB):
        batch = new_docs[i:i + EB]
        items = [
            {"i": j, "title": d.title, "abstract": d.abstract,
             "source": d.source, "ptypes": d.ptypes}
            for j, d in enumerate(batch)
        ]
        try:
            meta = await asyncio.to_thread(enrich_ru, items)
        except Exception as e:  # noqa: BLE001
            print(f"[enrich] {e}")
            meta = {}
        for j, d in enumerate(batch):
            m = meta.get(str(j)) or {}
            if m.get("scientific") is False:  # антифейк: отсекаем ненаучное
                rejected += 1
                continue
            d.ru_title = (m.get("ru_title") or d.ru_title or d.title)
            ev = m.get("evidence") or "other"
            flag = m.get("flag") or ""
            d.evidence = f"{ev}|{flag}" if flag else ev
            kept.append(d)

    # 2) эмбеддинги + сохранение (батчами по 64)
    for i in range(0, len(kept), 64):
        batch = kept[i:i + 64]
        texts = [f"{d.title}\n{d.abstract}" for d in batch]
        try:
            vecs = await asyncio.to_thread(embed, texts)
        except Exception as e:  # noqa: BLE001
            print(f"[embed] {e}")
            continue
        for d, v in zip(batch, vecs):
            db.insert_document(d, v)
            stored.append(d)

    return {"found": len(collected), "new": len(new_docs),
            "stored": len(stored), "rejected": rejected}
