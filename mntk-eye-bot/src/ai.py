"""OpenAI: эмбеддинги, обогащение (перевод + TL;DR + проверка на фейк), ответы Q&A."""
import json

import numpy as np
from openai import OpenAI

from src.config import settings

client = OpenAI(api_key=settings.openai_api_key)


def embed(texts: list[str]) -> list[np.ndarray]:
    resp = client.embeddings.create(model=settings.embed_model, input=texts)
    return [np.array(d.embedding, dtype=np.float32) for d in resp.data]


def enrich_ru(items: list[dict]) -> dict:
    """Перевод + краткая выжимка + проверка достоверности за один вызов.

    items: [{'i':0,'title':...,'abstract':...,'source':...,'ptypes':...}]
    Возвращает {'0': {ru_title, tldr, scientific(bool), evidence, flag}, ...}
      evidence ∈ meta|rct|observational|case|preprint|other
      flag     ∈ '' | sensational | preprint
    """
    if not items:
        return {}
    payload = "\n\n".join(
        f'[{it["i"]}] source={it.get("source","")} ptypes={it.get("ptypes","")}\n'
        f'TITLE: {it["title"]}\nABSTRACT: {(it.get("abstract") or "")[:1400]}'
        for it in items
    )
    sys = (
        "Ты научный редактор и фактчекер МНТК «Микрохирургия глаза». Твоя задача — "
        "отделять настоящие научные работы (оригинальные исследования, РКИ, мета-анализы, "
        "обзоры, клинические исследования с данными) от ненаучного и сенсационного "
        "(новости, пресс-релизы, научпоп, рекламные и непроверяемые заявления вроде "
        "«учёные полностью излечили близорукость»). Работай строго по предоставленному тексту."
    )
    user = (
        "Для каждой статьи верни СТРОГО JSON-объект, ключ — индекс в квадратных скобках, "
        "значение — объект с полями:\n"
        '  "ru_title": заголовок на русском (перевод, если оригинал не на русском),\n'
        '  "tldr": выжимка на русском, 1-2 предложения (суть + клиническая значимость),\n'
        '  "scientific": true если это научная работа с данными/обзор, false если новость/'
        "научпоп/реклама/непроверяемое заявление,\n"
        '  "evidence": один из "meta","rct","observational","case","preprint","other",\n'
        '  "flag": "" обычно; "sensational" если заголовок/выводы громкие и не подтверждены '
        "масштабными данными; \"preprint\" если это препринт без рецензирования.\n"
        "Без markdown и пояснений, только JSON.\n\n" + payload
    )
    resp = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except (json.JSONDecodeError, TypeError):
        return {}


def answer_ru(question: str, contexts: list[tuple]) -> str:
    """contexts: [(n, Document), ...]"""
    ctx = "\n\n".join(
        f"[{n}] {d.ru_title or d.title}. {d.journal} {d.pubdate}.\n{(d.abstract or '')[:1500]}"
        for n, d in contexts
    )
    sys = (
        "Ты AI-ассистент научной библиотеки МНТК «Микрохирургия глаза». "
        "Отвечай на русском, опираясь ТОЛЬКО на предоставленные источники. "
        "Ссылайся на источники в квадратных скобках [n]. Если данных недостаточно — "
        "честно скажи об этом. Не выдумывай факты и ссылки. "
        "Это обзор литературы, а не медицинская рекомендация."
    )
    user = f"Вопрос: {question}\n\nИсточники:\n{ctx}"
    resp = client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "system", "content": sys}, {"role": "user", "content": user}],
        temperature=0.2,
    )
    return resp.choices[0].message.content or ""
