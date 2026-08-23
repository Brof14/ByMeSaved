import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str = os.environ["BOT_TOKEN"]
    openrouter_api_key: str = os.environ["OPENROUTER_API_KEY"]
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-ultra-550b-a55b:free")
    openrouter_embed_model: str = os.getenv("OPENROUTER_EMBED_MODEL", "nvidia/nemotron-3-embed-1b:free")
    database_url: str = os.getenv("DATABASE_URL", "postgresql://knowledge:knowledge@postgres:5432/knowledge")
    export_dir: str = os.getenv("EXPORT_DIR", "/data/exports")
    max_search_results: int = int(os.getenv("MAX_SEARCH_RESULTS", "8"))

settings = Settings()
