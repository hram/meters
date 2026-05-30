import os
from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required but not set")
    return value


class Settings:
    pesc_api_url: str = _require("PESC_API_URL")
    gaz_api_url: str = _require("GAZ_API_URL")
    data_dir: str = os.environ.get("DATA_DIR") or "data"
    scheduler_hour: int = int(os.environ.get("SCHEDULER_HOUR") or 12)
    scheduler_minute: int = int(os.environ.get("SCHEDULER_MINUTE") or 0)


settings = Settings()
