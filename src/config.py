import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _list(env: str, default: str) -> list[str]:
    raw = os.getenv(env, default)
    return [x.strip() for x in raw.split(",") if x.strip()]


def _bool(env: str, default: str = "false") -> bool:
    return os.getenv(env, default).strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ncbi_email: str = os.getenv("NCBI_EMAIL", "")
    ncbi_api_key: str = os.getenv("NCBI_API_KEY", "")
    chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    digest_chat_id: str = os.getenv("DIGEST_CHAT_ID", "")
    digest_hour: int = int(os.getenv("DIGEST_HOUR", "8"))
    lookback_days: int = int(os.getenv("DIGEST_LOOKBACK_DAYS", "7"))
    digest_max_items: int = int(os.getenv("DIGEST_MAX_ITEMS", "12"))

    db_path: str = os.getenv("DB_PATH", "data/knowledge.db")
    max_results_per_term: int = int(os.getenv("MAX_RESULTS_PER_TERM", "15"))

    # Источники
    enable_pubmed: bool = _bool("ENABLE_PUBMED", "true")
    enable_europepmc: bool = _bool("ENABLE_EUROPEPMC", "true")
    enable_crossref: bool = _bool("ENABLE_CROSSREF", "true")
    enable_cyberleninka: bool = _bool("ENABLE_CYBERLENINKA", "false")  # экспериментальный

    search_terms: list = field(
        default_factory=lambda: _list(
            "SEARCH_TERMS",
            "cataract surgery,vitreoretinal surgery,glaucoma surgery,"
            "refractive surgery,keratoplasty,phacoemulsification",
        )
    )
    # Дополнительные русскоязычные запросы (для CyberLeninka и др.)
    search_terms_ru: list = field(
        default_factory=lambda: _list(
            "SEARCH_TERMS_RU",
            "микрохирургия глаза,катаракта,глаукома,витреоретинальная хирургия,кератопластика",
        )
    )


settings = Settings()
