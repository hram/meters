import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from portal.db import get_auto_submit, get_log, get_properties, get_assignments
from portal.infrastructure.config import settings
from src.adapters import PescAdapter, GazAdapter

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


def _datetimeformat(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M")


templates.env.filters["datetimeformat"] = _datetimeformat


def _canonical(service: str) -> str:
    """Map pesc_water / pesc_electricity → pesc."""
    return "pesc" if service.startswith("pesc") else service


@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    (water, electricity), gaz_data = await asyncio.gather(
        PescAdapter(settings.pesc_api_url).fetch_split(),
        GazAdapter(settings.gaz_api_url).fetch(),
    )

    # ── "По типу" view ────────────────────────────────────────────────────────
    services = [
        {**_to_dict(water),       "auto_submit": get_auto_submit("pesc")},
        {**_to_dict(electricity), "auto_submit": get_auto_submit("pesc")},
        {**_to_dict(gaz_data),    "auto_submit": get_auto_submit("gaz")},
    ]

    # ── "По объекту" view ─────────────────────────────────────────────────────
    properties = get_properties()
    assignments = get_assignments()  # {(canonical_service, meter_id): property_id}

    all_meters = []
    for svc_data in [water, electricity, gaz_data]:
        if not svc_data.error:
            all_meters.extend(svc_data.meters)

    prop_map: dict[int, dict] = {
        p["id"]: {"id": p["id"], "name": p["name"], "meters": []}
        for p in properties
    }
    unassigned: list = []

    for meter in all_meters:
        prop_id = assignments.get((_canonical(meter.service), meter.meter_id))
        if prop_id and prop_id in prop_map:
            prop_map[prop_id]["meters"].append(meter)
        else:
            unassigned.append(meter)

    props_view = list(prop_map.values())
    if unassigned:
        props_view.append({"id": None, "name": "Без объекта", "meters": unassigned})

    return templates.TemplateResponse(request, "index.html", {
        "request": request,
        "services": services,
        "props_view": props_view,
    })


@router.get("/log", response_class=HTMLResponse)
async def log_page(request: Request) -> HTMLResponse:
    entries = get_log()
    return templates.TemplateResponse(request, "log.html", {"request": request, "entries": entries})


@router.get("/properties", response_class=HTMLResponse)
async def properties_page(request: Request) -> HTMLResponse:
    properties = get_properties()
    assignments = get_assignments()
    return templates.TemplateResponse(request, "properties.html", {
        "request": request,
        "properties": properties,
        "assignments": {f"{s}:{m}": p for (s, m), p in assignments.items()},
    })


def _to_dict(sd) -> dict:
    return {
        "service": sd.service,
        "label": sd.label,
        "account_id": sd.account_id,
        "balance_text": sd.balance_text,
        "meters": sd.meters,
        "error": sd.error,
    }
