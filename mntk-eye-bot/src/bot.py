"""Telegram-бот МНТК «Микрохирургия глаза» v2:
дайджесты с проверкой достоверности, кнопки Сохранить/Поделиться, /saved, AI-Q&A."""
import asyncio
import logging
import time
from datetime import time as dtime
from urllib.parse import quote

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters,
)

from src.config import settings
from src import db
from src.pipeline import ingest
from src.ai import embed, answer_ru

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO
)
log = logging.getLogger("mntk-bot")

WELCOME = (
    "👁 Бот МНТК «Микрохирургия глаза»\n\n"
    "Слежу за мировой научной литературой по микрохирургии глаза "
    "(PubMed, Europe PMC, Crossref, CyberLeninka), перевожу на русский, "
    "проверяю достоверность и отсекаю сенсации/фейки.\n\n"
    "Команды:\n"
    "/digest — свежий проверенный дайджест\n"
    "/saved — мои сохранённые статьи\n"
    "/stats — размер базы\n\n"
    "Под каждой статьёй: 👍 сохранить и ↪️ поделиться.\n"
    "Просто напиши вопрос — отвечу по базе со ссылками на источники."
)

# evidence -> (подпись, ранг сортировки)
EVIDENCE = {
    "meta": ("🟢 Высокий: мета-анализ/обзор", 5),
    "rct": ("🟢 Высокий: РКИ", 5),
    "observational": ("🟡 Средний: наблюдательное", 3),
    "case": ("🟠 Низкий: клинический случай", 2),
    "preprint": ("⏳ Препринт (не рецензирован)", 1),
    "other": ("⚪ Прочее", 1),
}


def _parse_evidence(evidence: str):
    base, _, flag = (evidence or "other").partition("|")
    label, rank = EVIDENCE.get(base, EVIDENCE["other"])
    extra = ""
    if flag == "sensational":
        extra = "\n⚠️ Громкое заявление — требует подтверждения."
        rank = min(rank, 1)
    elif flag == "preprint":
        label, rank = EVIDENCE["preprint"]
    return label, rank, extra


def _chunk(text: str, size: int = 3900) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)] or [""]


def _item_text(d: db.Document) -> str:
    label, _rank, extra = _parse_evidence(d.evidence)
    title = d.ru_title or d.title
    orig = f"\n({d.title})" if d.ru_title and d.ru_title != d.title else ""
    retr = "⚠️ ОТОЗВАНА. " if d.retracted else ""
    meta = " · ".join(x for x in [d.journal, d.pubdate, d.source] if x)
    return (f"{label}{extra}\n\n{retr}{title}{orig}\n\n"
            f"{meta}\n🔗 {d.url}")


def _item_kb(d: db.Document, saved: bool = False) -> InlineKeyboardMarkup:
    rid = db.rowid_of(d.uid)
    share = ("https://t.me/share/url?url=" + quote(d.url, safe="")
             + "&text=" + quote((d.ru_title or d.title)[:200], safe=""))
    save_btn = (InlineKeyboardButton("✅ Сохранено", callback_data=f"u:{rid}")
                if saved else
                InlineKeyboardButton("👍 Сохранить", callback_data=f"s:{rid}"))
    return InlineKeyboardMarkup([[save_btn, InlineKeyboardButton("↪️ Поделиться", url=share)]])


def _rank_docs(docs: list[db.Document]) -> list[db.Document]:
    return sorted(docs, key=lambda d: _parse_evidence(d.evidence)[1], reverse=True)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(WELCOME)


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    n = await asyncio.to_thread(db.count)
    await update.message.reply_text(f"В базе знаний: {n} проверенных публикаций.")


async def _send_digest(send, docs: list[db.Document], stats: dict | None = None) -> None:
    docs = _rank_docs(docs)[: settings.digest_max_items]
    if stats:
        await send(
            f"📚 Дайджест: микрохирургия глаза\n"
            f"Найдено: {stats['found']} · новых: {stats['new']} · "
            f"отсеяно ненаучных/фейков: {stats['rejected']}\n"
            f"Показываю топ-{len(docs)} по достоверности."
        )
    if not docs:
        await send("Новых проверенных публикаций за период не найдено.")
        return
    for d in docs:
        await send(_item_text(d), reply_markup=_item_kb(d), disable_web_page_preview=True)


async def cmd_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Собираю и проверяю свежие публикации… ~1–2 мин.")
    stats = await ingest()
    since = time.time() - settings.lookback_days * 86400
    docs = await asyncio.to_thread(db.recent, since)

    async def send(text, **kw):
        await update.message.reply_text(text, **kw)

    await _send_digest(send, docs, stats)


async def cmd_saved(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    docs = await asyncio.to_thread(db.list_saved, update.effective_user.id)
    if not docs:
        await update.message.reply_text("Пока ничего не сохранено. Жми 👍 под статьёй в дайджесте.")
        return
    await update.message.reply_text(f"⭐ Сохранено: {len(docs)}")
    for d in docs:
        await update.message.reply_text(
            _item_text(d), reply_markup=_item_kb(d, saved=True), disable_web_page_preview=True
        )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    action, _, rid = (query.data or "").partition(":")
    doc = await asyncio.to_thread(db.get_by_rowid, int(rid)) if rid.isdigit() else None
    if not doc:
        await query.answer("Статья не найдена.")
        return
    user_id = query.from_user.id
    if action == "s":
        await asyncio.to_thread(db.save_article, user_id, doc.uid)
        await query.answer("Сохранено ⭐")
        await query.edit_message_reply_markup(reply_markup=_item_kb(doc, saved=True))
    elif action == "u":
        await asyncio.to_thread(db.unsave, user_id, doc.uid)
        await query.answer("Убрано из сохранённых")
        await query.edit_message_reply_markup(reply_markup=_item_kb(doc, saved=False))
    else:
        await query.answer()


async def on_question(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = (update.message.text or "").strip()
    if not q:
        return
    await update.message.chat.send_action("typing")
    n = await asyncio.to_thread(db.count)
    if n == 0:
        await update.message.reply_text(
            "База пока пустая. Запусти /digest, чтобы наполнить её проверенными публикациями."
        )
        return
    vec = (await asyncio.to_thread(embed, [q]))[0]
    hits = await asyncio.to_thread(db.search, vec, 6)
    contexts = [(i + 1, d) for i, (d, _s) in enumerate(hits)]
    answer = await asyncio.to_thread(answer_ru, q, contexts)
    sources = "\n".join(f"[{i}] {(d.ru_title or d.title)} — {d.url}" for i, d in contexts)
    await update.message.reply_text(
        f"{answer}\n\nИсточники:\n{sources}", disable_web_page_preview=True
    )


async def daily_digest(context: ContextTypes.DEFAULT_TYPE) -> None:
    if not settings.digest_chat_id:
        return
    stats = await ingest()
    since = time.time() - settings.lookback_days * 86400
    docs = await asyncio.to_thread(db.recent, since)

    async def send(text, **kw):
        await context.bot.send_message(chat_id=settings.digest_chat_id, text=text, **kw)

    await _send_digest(send, docs, stats)


def main() -> None:
    if not settings.telegram_token:
        raise SystemExit("TELEGRAM_BOT_TOKEN не задан (см. .env)")
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY не задан (см. .env)")

    db.init_db()
    app = Application.builder().token(settings.telegram_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("digest", cmd_digest))
    app.add_handler(CommandHandler("saved", cmd_saved))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_question))

    if settings.digest_chat_id:
        app.job_queue.run_daily(daily_digest, time=dtime(hour=settings.digest_hour, minute=0))
        log.info("Авто-дайджест: %02d:00 -> chat %s", settings.digest_hour, settings.digest_chat_id)

    log.info("Бот запущен (polling).")
    app.run_polling()


if __name__ == "__main__":
    main()
