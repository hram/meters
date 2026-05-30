import os
os.environ.setdefault("PESC_API_URL", "http://localhost:8003")
os.environ.setdefault("GAZ_API_URL", "http://localhost:8004")

from portal.main import app  # noqa: F401
from portal.routers.dashboard import router as dashboard_router  # noqa: F401
from portal.routers.submit import router as submit_router  # noqa: F401
from portal.routers.settings import router as settings_router  # noqa: F401
from src.adapters import PescAdapter, GazAdapter  # noqa: F401


def test_imports() -> None:
    assert app is not None
    assert PescAdapter is not None
    assert GazAdapter is not None
