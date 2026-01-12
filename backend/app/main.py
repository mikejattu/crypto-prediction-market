import asyncio
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.routes import platforms, markets, contracts, crypto_categories
from app.db.database import Base, engine, get_db
from app.db.models import MarketSnapshot
from app.services.poller import poller_loop

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="Real-time prediction market analytics and forecasting platform",
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(platforms.router, prefix=settings.API_V1_PREFIX)
app.include_router(markets.router, prefix=settings.API_V1_PREFIX)
app.include_router(contracts.router, prefix=settings.API_V1_PREFIX)
app.include_router(crypto_categories.router, prefix=settings.API_V1_PREFIX)

poller_task: Optional[asyncio.Task] = None


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    global poller_task
    if settings.ENABLE_POLLER:
        poller_task = asyncio.create_task(poller_loop())


@app.on_event("shutdown")
async def shutdown_event():
    if poller_task:
        poller_task.cancel()


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "healthy", "environment": settings.ENVIRONMENT}


@app.get(f"{settings.API_V1_PREFIX}/health/data-freshness", tags=["health"])
async def data_freshness(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.max(MarketSnapshot.timestamp)))
    latest = result.scalar_one_or_none()
    if not latest:
        return {
            "fresh": False,
            "last_snapshot_at": None,
            "max_allowed_lag_seconds": settings.FRESHNESS_WARNING_SECONDS,
        }
    lag = (datetime.now(timezone.utc) - latest).total_seconds()
    return {
        "fresh": lag <= settings.FRESHNESS_WARNING_SECONDS,
        "last_snapshot_at": latest,
        "max_allowed_lag_seconds": settings.FRESHNESS_WARNING_SECONDS,
    }
