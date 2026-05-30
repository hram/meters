from fastapi import APIRouter
from pydantic import BaseModel

from portal.db import get_auto_submit, set_auto_submit
from portal.scheduler import run_auto_submit

router = APIRouter(prefix="/api/services", tags=["settings"])


class ServiceSettingsOut(BaseModel):
    service: str
    auto_submit: bool


class ServiceSettingsPatch(BaseModel):
    auto_submit: bool


@router.get("/{service}/settings", response_model=ServiceSettingsOut)
async def get_settings(service: str) -> ServiceSettingsOut:
    return ServiceSettingsOut(service=service, auto_submit=get_auto_submit(service))


@router.patch("/{service}/settings", response_model=ServiceSettingsOut)
async def update_settings(service: str, body: ServiceSettingsPatch) -> ServiceSettingsOut:
    set_auto_submit(service, body.auto_submit)
    return ServiceSettingsOut(service=service, auto_submit=body.auto_submit)


@router.post("/trigger", status_code=204)
async def trigger(force: bool = False) -> None:
    """Запустить автоподачу вручную. force=true игнорирует окно подачи."""
    await run_auto_submit(force=force)
