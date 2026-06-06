"""Клиент PubMed (NCBI E-utilities): поиск свежих статей + загрузка деталей."""
import xml.etree.ElementTree as ET

import httpx

from src.config import settings
from src.db import Document

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def _params(extra: dict) -> dict:
    p = dict(extra)
    p["tool"] = "mntk-eye-bot"
    if settings.ncbi_email:
        p["email"] = settings.ncbi_email
    if settings.ncbi_api_key:
        p["api_key"] = settings.ncbi_api_key
    return p


async def search_ids(client: httpx.AsyncClient, term: str, retmax: int, reldate: int) -> list[str]:
    params = _params({
        "db": "pubmed", "term": term, "retmax": retmax, "retmode": "json",
        "sort": "date", "datetype": "pdat", "reldate": reldate,
    })
    r = await client.get(f"{EUTILS}/esearch.fcgi", params=params, timeout=30)
    r.raise_for_status()
    return r.json().get("esearchresult", {}).get("idlist", [])


async def fetch_details(client: httpx.AsyncClient, ids: list[str]) -> list[Document]:
    if not ids:
        return []
    params = _params({"db": "pubmed", "id": ",".join(ids), "retmode": "xml", "rettype": "abstract"})
    r = await client.get(f"{EUTILS}/efetch.fcgi", params=params, timeout=60)
    r.raise_for_status()
    return _parse_articles(r.text)


def _parse_articles(xml_text: str) -> list[Document]:
    docs: list[Document] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return docs

    for art in root.findall(".//PubmedArticle"):
        medline = art.find(".//MedlineCitation")
        if medline is None:
            continue
        pmid = (medline.findtext("PMID") or "").strip()
        article = medline.find("Article")
        if article is None:
            continue

        title_el = article.find("ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""

        abs_parts = []
        for ab in article.findall(".//Abstract/AbstractText"):
            label = ab.get("Label")
            text = "".join(ab.itertext()).strip()
            abs_parts.append(f"{label}: {text}" if label else text)
        abstract = "\n".join(p for p in abs_parts if p)

        authors = []
        for a in article.findall(".//AuthorList/Author"):
            ln, ini = a.findtext("LastName"), a.findtext("Initials")
            if ln:
                authors.append(f"{ln} {ini or ''}".strip())
        authors_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")

        journal = article.findtext(".//Journal/Title") or ""

        pd = article.find(".//Journal/JournalIssue/PubDate")
        pubdate = ""
        if pd is not None:
            ymd = [pd.findtext("Year"), pd.findtext("Month"), pd.findtext("Day")]
            pubdate = " ".join(x for x in ymd if x) or (pd.findtext("MedlineDate") or "")

        doi = ""
        for eid in art.findall(".//ArticleIdList/ArticleId"):
            if eid.get("IdType") == "doi":
                doi = (eid.text or "").lower().strip()

        ptypes = [pt.text or "" for pt in article.findall(".//PublicationTypeList/PublicationType")]
        retracted = any("Retract" in p for p in ptypes)

        if not pmid:
            continue
        docs.append(Document(
            uid=f"pmid:{pmid}", source="pubmed", pmid=pmid, doi=doi, title=title,
            abstract=abstract, authors=authors_str, journal=journal, pubdate=pubdate,
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/", retracted=retracted,
            ptypes="; ".join(p for p in ptypes if p),
        ))
    return docs
