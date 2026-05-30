import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from portal.db import get_auto_submit, get_log
from portal.infrastructure.config import settings
from src.adapters import PescAdapter, GazAdapter

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


def _datetimeformat(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")


templates.env.filters["datetimeformat"] = _datetimeformat


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    (water, electricity), gaz_data = await asyncio.gather(
        PescAdapter(settings.pesc_api_url).fetch_split(),
        GazAdapter(settings.gaz_api_url).fetch(),
    )
    services = [
        {**_to_dict(water),       "auto_submit": get_auto_submit("pesc")},
        {**_to_dict(electricity), "auto_submit": get_auto_submit("pesc")},
        {**_to_dict(gaz_data),    "auto_submit": get_auto_submit("gaz")},
    ]
    return templates.TemplateResponse("index.html", {"request": request, "services": services})


@router.get("/log", response_class=HTMLResponse)
async def log_page(request: Request) -> HTMLResponse:
    entries = get_log()
    return templates.TemplateResponse("log.html", {"request": request, "entries": entries})


def _to_dict(sd) -> dict:
    return {
        "service": sd.service,
        "label": sd.label,
        "account_id": sd.account_id,
        "balance_text": sd.balance_text,
        "meters": sd.meters,
        "error": sd.error,
    }
