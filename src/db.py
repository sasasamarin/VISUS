"""Хранилище: публикации + эмбеддинги + сохранённые пользователями статьи (SQLite).
Векторный поиск — косинус через numpy. На рост базы — мигрировать на pgvector."""
import os
import time
import sqlite3
from dataclasses import dataclass

import numpy as np

from src.config import settings


@dataclass
class Document:
    uid: str
    source: str            # pubmed | europepmc | crossref | cyberleninka
    pmid: str = ""
    doi: str = ""
    title: str = ""
    ru_title: str = ""     # перевод заголовка (GPT)
    abstract: str = ""
    authors: str = ""
    journal: str = ""
    pubdate: str = ""
    url: str = ""
    retracted: bool = False
    evidence: str = ""     # "rct" / "meta" / ... возможно с флагом "rct|sensational"
    ptypes: str = ""       # типы публикации PubMed (для оценки достоверности; не хранится)


_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        path = settings.db_path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        _conn = sqlite3.connect(path, check_same_thread=False)
        _conn.row_factory = sqlite3.Row
    return _conn


def _ensure_column(conn, table, col, decl):
    cols = {r["name"] for r in conn.execute(f"PRAGMA table_info({table})")}
    if col not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def init_db() -> None:
    conn = _get_conn()
    conn.execute(
        """CREATE TABLE IF NOT EXISTS documents(
            uid TEXT PRIMARY KEY, source TEXT, pmid TEXT, doi TEXT,
            title TEXT, ru_title TEXT, abstract TEXT, authors TEXT, journal TEXT,
            pubdate TEXT, url TEXT, retracted INTEGER DEFAULT 0,
            evidence TEXT, embedding BLOB, added_ts REAL)"""
    )
    # миграции для старых баз
    _ensure_column(conn, "documents", "ru_title", "TEXT")
    _ensure_column(conn, "documents", "evidence", "TEXT")
    conn.execute(
        """CREATE TABLE IF NOT EXISTS saved(
            user_id INTEGER, uid TEXT, ts REAL,
            PRIMARY KEY(user_id, uid))"""
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doi ON documents(doi)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_added ON documents(added_ts)")
    conn.commit()


def _row_to_doc(r: sqlite3.Row) -> Document:
    return Document(
        uid=r["uid"], source=r["source"], pmid=r["pmid"], doi=r["doi"],
        title=r["title"], ru_title=(r["ru_title"] or ""), abstract=r["abstract"],
        authors=r["authors"], journal=r["journal"], pubdate=r["pubdate"],
        url=r["url"], retracted=bool(r["retracted"]), evidence=(r["evidence"] or ""),
    )


def exists(doc: Document) -> bool:
    conn = _get_conn()
    if conn.execute("SELECT 1 FROM documents WHERE uid=? LIMIT 1", (doc.uid,)).fetchone():
        return True
    if doc.doi and conn.execute(
        "SELECT 1 FROM documents WHERE doi=? AND doi!='' LIMIT 1", (doc.doi,)
    ).fetchone():
        return True
    return False


def insert_document(doc: Document, emb: np.ndarray) -> None:
    conn = _get_conn()
    conn.execute(
        """INSERT OR REPLACE INTO documents
           (uid,source,pmid,doi,title,ru_title,abstract,authors,journal,pubdate,
            url,retracted,evidence,embedding,added_ts)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (doc.uid, doc.source, doc.pmid, doc.doi, doc.title, doc.ru_title, doc.abstract,
         doc.authors, doc.journal, doc.pubdate, doc.url, int(doc.retracted),
         doc.evidence, emb.astype(np.float32).tobytes(), time.time()),
    )
    conn.commit()


def recent(since_ts: float) -> list[Document]:
    conn = _get_conn()
    cur = conn.execute(
        "SELECT * FROM documents WHERE added_ts>=? ORDER BY added_ts DESC", (since_ts,)
    )
    return [_row_to_doc(r) for r in cur.fetchall()]


def count() -> int:
    return _get_conn().execute("SELECT COUNT(*) FROM documents").fetchone()[0]


def get_by_uid(uid: str) -> Document | None:
    r = _get_conn().execute("SELECT * FROM documents WHERE uid=?", (uid,)).fetchone()
    return _row_to_doc(r) if r else None


def get_by_rowid(rid: int) -> Document | None:
    r = _get_conn().execute("SELECT * FROM documents WHERE rowid=?", (rid,)).fetchone()
    return _row_to_doc(r) if r else None


def rowid_of(uid: str) -> int | None:
    r = _get_conn().execute("SELECT rowid FROM documents WHERE uid=?", (uid,)).fetchone()
    return int(r[0]) if r else None


def search(query_vec: np.ndarray, k: int = 6) -> list[tuple[Document, float]]:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT uid, embedding FROM documents WHERE embedding IS NOT NULL"
    ).fetchall()
    if not rows:
        return []
    mat = np.stack([np.frombuffer(r["embedding"], dtype=np.float32) for r in rows])
    uids = [r["uid"] for r in rows]
    q = query_vec.astype(np.float32)
    mat_n = mat / (np.linalg.norm(mat, axis=1, keepdims=True) + 1e-8)
    qn = q / (np.linalg.norm(q) + 1e-8)
    scores = mat_n @ qn
    out: list[tuple[Document, float]] = []
    for i in np.argsort(-scores)[:k]:
        d = get_by_uid(uids[int(i)])
        if d:
            out.append((d, float(scores[int(i)])))
    return out


# --- сохранённые статьи пользователей ---

def save_article(user_id: int, uid: str) -> None:
    _get_conn().execute(
        "INSERT OR IGNORE INTO saved(user_id, uid, ts) VALUES (?,?,?)",
        (user_id, uid, time.time()),
    )
    _get_conn().commit()


def unsave(user_id: int, uid: str) -> None:
    _get_conn().execute("DELETE FROM saved WHERE user_id=? AND uid=?", (user_id, uid))
    _get_conn().commit()


def list_saved(user_id: int) -> list[Document]:
    conn = _get_conn()
    rows = conn.execute(
        """SELECT d.* FROM saved s JOIN documents d ON d.uid=s.uid
           WHERE s.user_id=? ORDER BY s.ts DESC""",
        (user_id,),
    ).fetchall()
    return [_row_to_doc(r) for r in rows]
