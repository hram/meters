"""Adapter for the pesc portal REST API."""

from typing import Any

import httpx

from .models import Meter, Scale, ServiceData

LABEL_WATER = "Вода"
LABEL_ELECTRICITY = "Электричество"
LABEL = "Вода и электричество"  # fallback

_WATER_KEYWORDS = ["водоснабжение", "вода", "хвс", "гвс"]


def is_water_meter(name: str) -> bool:
    return any(k in name.lower() for k in _WATER_KEYWORDS)

_NAME_MAP = {
    "ГВС": "Горячее водоснабжение",
    "ХВС": "Холодное водоснабжение",
}


def _expand(name: str | None) -> str | None:
    if not name:
        return name
    for abbr, full in _NAME_MAP.items():
        name = name.replace(abbr, full)
    return name


class PescAdapter:
    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    async def fetch(self) -> ServiceData:
        """Fetch account info and meters in one auth flow; return ServiceData (never raises)."""
        try:
            async with httpx.AsyncClient() as http:
                data = await _get(http, f"{self._base}/api/dashboard")
            return _build(data.get("account"), data.get("meters") or [])
        except Exception as exc:
            return ServiceData(
                service="pesc",
                label=LABEL,
                account_id="?",
                balance_text=None,
                error=str(exc),
            )

    async def fetch_split(self) -> tuple[ServiceData, ServiceData]:
        """Fetch and return (water, electricity) as separate ServiceData objects."""
        full = await self.fetch()
        if full.error:
            err_water = ServiceData(service="pesc_water", label=LABEL_WATER, account_id="?", balance_text=None, error=full.error)
            err_elec  = ServiceData(service="pesc_electricity", label=LABEL_ELECTRICITY, account_id="?", balance_text=None, error=full.error)
            return err_water, err_elec

        water_meters = [m for m in full.meters if is_water_meter(m.name)]
        elec_meters  = [m for m in full.meters if not is_water_meter(m.name)]

        for m in water_meters:
            m.service = "pesc_water"
        for m in elec_meters:
            m.service = "pesc_electricity"

        water = ServiceData(service="pesc_water", label=LABEL_WATER,
                            account_id=full.account_id, balance_text=None, meters=water_meters)
        elec  = ServiceData(service="pesc_electricity", label=LABEL_ELECTRICITY,
                            account_id=full.account_id, balance_text=full.balance_text, meters=elec_meters)
        return water, elec

    async def submit_same(self) -> None:
        """Submit current values for all accounts (calls per-account submit endpoint)."""
        async with httpx.AsyncClient() as http:
            meters_raw = await _get(http, f"{self._base}/api/meters")
            account_ids = {m["account_id"] for m in meters_raw}
            for account_id in account_ids:
                res = await http.post(f"{self._base}/api/meters/{account_id}/submit")
                _raise(res, f"POST /api/meters/{account_id}/submit")

    async def submit_values(self, body: Any) -> Any:
        """Proxy submit-values payload directly to the pesc portal."""
        async with httpx.AsyncClient() as http:
            res = await http.post(
                f"{self._base}/api/meters/submit-values",
                json=body,
            )
            _raise(res, "POST /api/meters/submit-values")
            return res.json()


def _build(acc: Any, meters_raw: list[dict]) -> ServiceData:
    balance_text = acc.get("balance_text") if acc else None
    account_id = str(acc.get("account_id", "?")) if acc else "?"

    meters = []
    for m in meters_raw:
        scales = [
            Scale(
                id=str(ind["meter_scale_id"]),
                name=_expand(ind.get("scale_name")) or "Показание",
                value=ind.get("previous_reading"),
                unit=ind.get("unit"),
            )
            for ind in m.get("indications") or []
        ]
        meters.append(Meter(
            service="pesc",
            account_id=str(m["account_id"]),
            meter_id=m["registration"],
            name=_expand(m.get("name")) or m["registration"],
            scales=scales,
            extra={
                "account_id": m["account_id"],
                "registration": m["registration"],
            },
        ))

    return ServiceData(
        service="pesc",
        label=LABEL,
        account_id=account_id,
        balance_text=balance_text,
        meters=meters,
    )


async def _get(http: httpx.AsyncClient, url: str) -> Any:
    res = await http.get(url)
    _raise(res, f"GET {url}")
    return res.json()


def _raise(res: httpx.Response, label: str) -> None:
    if not res.is_success:
        raise RuntimeError(f"{label} → HTTP {res.status_code}: {res.text[:200]}")
