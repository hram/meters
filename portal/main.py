from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from portal.db import init_db
from portal.routers.dashboard import router as dashboard_router
from portal.routers.submit import router as submit_router
from portal.routers.settings import router as settings_router
from portal.routers.properties import router as properties_router
from portal.scheduler import create_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    scheduler = create_scheduler()
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    lifespan=lifespan,
    title="Meters — общий дашборд показаний",
    version="0.1.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(submit_router)
app.include_router(settings_router)
app.include_router(properties_router)
app.include_router(dashboard_router)
