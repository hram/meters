import asyncio
from typing import Any

from fastapi import APIRouter

from portal.infrastructure.config import settings
from src.adapters import PescAdapter, GazAdapter

router = APIRouter(prefix="/api", tags=["submit"])


@router.post("/services/pesc/submit", status_code=204)
async def pesc_submit() -> None:
    """Submit same values for all pesc accounts."""
    await PescAdapter(settings.pesc_api_url).submit_same()


@router.post("/services/gaz/submit", status_code=204)
async def gaz_submit() -> None:
    """Submit same values for the gaz account."""
    await GazAdapter(settings.gaz_api_url).submit_same()


@router.post("/services/pesc/submit-values")
async def pesc_submit_values(body: list[Any]) -> Any:
    """Proxy custom values to the pesc portal."""
    return await PescAdapter(settings.pesc_api_url).submit_values(body)


@router.post("/services/gaz/submit-values")
async def gaz_submit_values(body: list[Any]) -> Any:
    """Proxy custom values to the gaz portal."""
    return await GazAdapter(settings.gaz_api_url).submit_values(body)


@router.post("/submit-all", status_code=204)
async def submit_all() -> None:
    """Submit same values for all services simultaneously."""
    await asyncio.gather(
        PescAdapter(settings.pesc_api_url).submit_same(),
        GazAdapter(settings.gaz_api_url).submit_same(),
    )
