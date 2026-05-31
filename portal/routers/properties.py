from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from portal.db import (
    get_properties, create_property, update_property, delete_property,
    get_assignments, set_assignment, delete_assignment,
)

router = APIRouter(prefix="/api", tags=["properties"])


class PropertyIn(BaseModel):
    name: str


class PropertyOut(BaseModel):
    id: int
    name: str


class AssignmentIn(BaseModel):
    property_id: int | None


@router.get("/properties", response_model=list[PropertyOut])
async def list_properties() -> list[PropertyOut]:
    return [PropertyOut(**p) for p in get_properties()]


@router.post("/properties", response_model=PropertyOut, status_code=201)
async def create(body: PropertyIn) -> PropertyOut:
    return PropertyOut(**create_property(body.name.strip()))


@router.patch("/properties/{prop_id}", response_model=PropertyOut)
async def update(prop_id: int, body: PropertyIn) -> PropertyOut:
    return PropertyOut(**update_property(prop_id, body.name.strip()))


@router.delete("/properties/{prop_id}", status_code=204)
async def delete(prop_id: int) -> None:
    delete_property(prop_id)


@router.put("/assignments/{service}/{meter_id}", status_code=204)
async def assign(service: str, meter_id: str, body: AssignmentIn) -> None:
    if body.property_id is None:
        delete_assignment(service, meter_id)
    else:
        set_assignment(service, meter_id, body.property_id)
