import os


def test_app_imports_with_required_settings(monkeypatch):
    monkeypatch.setenv("PESC_API_URL", "http://pesc:8000")
    monkeypatch.setenv("GAZ_API_URL", "http://gaz:8000")
    monkeypatch.setenv("DATA_DIR", os.devnull)

    from portal.main import app

    assert app.title == "Meters — общий дашборд показаний"
