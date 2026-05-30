import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from portal.db import get_enabled_services, add_log_entry
from portal.infrastructure.config import settings
from portal.schedule import should_submit
from src.adapters import PescAdapter, GazAdapter

log = logging.getLogger(__name__)

_ADAPTERS = {
    "pesc": lambda: PescAdapter(settings.pesc_api_url),
    "gaz": lambda: GazAdapter(settings.gaz_api_url),
}

_LABELS = {"pesc": "Вода и электричество", "gaz": "Газ"}


async def run_auto_submit(*, force: bool = False) -> None:
    import zoneinfo
    moscow_today = datetime.now(tz=zoneinfo.ZoneInfo("Europe/Moscow")).date()
    allowed, reason = should_submit(moscow_today)
    if not allowed:
        if force:
            log.info("auto_submit: force=true, игнорируем ограничение (%s)", reason)
        else:
            log.info("auto_submit: пропуск — %s", reason)
            return

    services = get_enabled_services()
    if not services:
        log.info("auto_submit: нет сервисов с включённой автоподачей")
        return

    log.info("auto_submit: запуск для %s", services)
    await asyncio.gather(*[_submit_service(s) for s in services])


async def _submit_service(service: str) -> None:
    adapter = _ADAPTERS[service]()
    try:
        await adapter.submit_same()
        log.info("auto_submit: %s — успешно", _LABELS.get(service, service))
        add_log_entry(service, success=True)
    except Exception as exc:
        log.error("auto_submit: %s — ошибка: %s", _LABELS.get(service, service), exc)
        add_log_entry(service, success=False, error=str(exc))


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(
        run_auto_submit,
        trigger="cron",
        hour=settings.scheduler_hour,
        minute=settings.scheduler_minute,
        id="auto_submit",
        replace_existing=True,
    )
    return scheduler
