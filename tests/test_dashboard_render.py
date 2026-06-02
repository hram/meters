from fastapi.testclient import TestClient

from src.adapters.models import ServiceData


def test_dashboard_page_renders(monkeypatch):
    monkeypatch.setenv("PESC_API_URL", "http://pesc:8000")
    monkeypatch.setenv("GAZ_API_URL", "http://gaz:8000")

    from portal.main import app
    from src.adapters.gaz import GazAdapter
    from src.adapters.pesc import PescAdapter

    async def fake_fetch_split(self):
        return (
            ServiceData(service="pesc_water", label="Вода", account_id="1", balance_text=None),
            ServiceData(service="pesc_electricity", label="Электричество", account_id="1", balance_text=None),
        )

    async def fake_fetch_gaz(self):
        return ServiceData(service="gaz", label="Газ", account_id="2", balance_text=None)

    monkeypatch.setattr(PescAdapter, "fetch_split", fake_fetch_split)
    monkeypatch.setattr(GazAdapter, "fetch", fake_fetch_gaz)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "Показания счётчиков" in response.text
