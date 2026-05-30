"""Adapter for the gaz portal REST API."""

from typing import Any

import httpx

from .models import Meter, Scale, ServiceData

LABEL = "Газ"

_RATE_NAMES = {"day": "Показание", "night": "Ночь", "middle": "Полупик"}


class GazAdapter:
    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")

    async def fetch(self) -> ServiceData:
        """Fetch account info and meters; return ServiceData (never raises)."""
        try:
            async with httpx.AsyncClient() as http:
                acc = await _get(http, f"{self._base}/api/account")
                meters_raw = await _get(http, f"{self._base}/api/meters")
            return _build(acc, meters_raw)
        except Exception as exc:
            return ServiceData(
                service="gaz",
                label=LABEL,
                account_id="?",
                balance_text=None,
                error=str(exc),
            )

    async def submit_same(self) -> None:
        """Fetch current values and re-submit them."""
        async with httpx.AsyncClient() as http:
            meters_raw = await _get(http, f"{self._base}/api/meters")
            payload = []
            for m in meters_raw:
                val = m.get("last_value") or {}
                if val.get("value_day") is None:
                    raise RuntimeError(f"Counter {m['uuid']}: no previous reading")
                payload.append({
                    "uuid": m["uuid"],
                    "service_id": m.get("service_link_id") or 0,
                    "value_day": val["value_day"],
                    "value_night": val.get("value_night"),
                    "value_middle": val.get("value_middle"),
                })
            res = await http.post(f"{self._base}/api/meters/submit-values", json=payload)
            _raise(res, "POST /api/meters/submit-values")

    async def submit_values(self, body: Any) -> Any:
        """Proxy submit-values payload directly to the gaz portal."""
        async with httpx.AsyncClient() as http:
            res = await http.post(
                f"{self._base}/api/meters/submit-values",
                json=body,
            )
            _raise(res, "POST /api/meters/submit-values")
            return res.json()


def _build(acc: Any, meters_raw: list[dict]) -> ServiceData:
    balance = acc.get("balance") if acc else None
    account_id = str(acc.get("account_id", "?")) if acc else "?"

    if balance is not None:
        try:
            b = float(balance)
            if b < 0:
                balance_text = f"переплата {abs(b):.2f} руб"
            elif b > 0:
                balance_text = f"задолженность {b:.2f} руб"
            else:
                balance_text = "расчёты без долга"
        except (TypeError, ValueError):
            balance_text = str(balance)
    else:
        balance_text = None

    meters = []
    for m in meters_raw:
        val = m.get("last_value") or {}
        n_rates = m.get("number_of_rates") or 1
        rate_keys = ["day"] + (["night"] if n_rates >= 2 else []) + (["middle"] if n_rates >= 3 else [])

        scales = [
            Scale(
                id=rate,
                name=_RATE_NAMES.get(rate, rate),
                value=val.get(f"value_{rate}"),
                unit=m.get("measure") or "м³",
            )
            for rate in rate_keys
        ]
        meters.append(Meter(
            service="gaz",
            account_id=account_id,
            meter_id=m["uuid"],
            name=m.get("name") or m["uuid"],
            scales=scales,
            extra={
                "uuid": m["uuid"],
                "service_id": m.get("service_link_id") or 0,
                "number_of_rates": n_rates,
            },
        ))

    return ServiceData(
        service="gaz",
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
