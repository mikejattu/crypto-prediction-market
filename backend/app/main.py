from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.core.config import settings
from app.api.routes import platforms, markets, contracts, crypto_categories, prices, sentiment
from app.tasks.price_fetcher import fetch_and_store_prices
from app.tasks.sentiment_fetcher import fetch_and_store_sentiment

logger = logging.getLogger(__name__)

# Set up the scheduler for background jobs
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown.
    On startup: starts the price fetcher scheduler.
    On shutdown: stops the scheduler cleanly.
    """
    # === STARTUP ===
    if settings.PRICE_FETCH_ENABLED:
        scheduler.add_job(
            fetch_and_store_prices,
            trigger=IntervalTrigger(hours=settings.PRICE_FETCH_INTERVAL_HOURS),
            id="price_fetcher",
            name="Fetch crypto prices from CoinGecko",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            f"Price fetcher scheduled to run every {settings.PRICE_FETCH_INTERVAL_HOURS} hours"
        )

        # Also fetch prices right away on startup
        asyncio.create_task(fetch_and_store_prices())

    if settings.SENTIMENT_FETCH_ENABLED:
        scheduler.add_job(
            fetch_and_store_sentiment,
            trigger=IntervalTrigger(minutes=settings.SENTIMENT_FETCH_INTERVAL_MINUTES),
            id="sentiment_fetcher",
            name="Fetch and analyze crypto sentiment",
            replace_existing=True,
        )
        if not scheduler.running:
            scheduler.start()
        logger.info(
            f"Sentiment fetcher scheduled to run every {settings.SENTIMENT_FETCH_INTERVAL_MINUTES} minutes"
        )

        asyncio.create_task(fetch_and_store_sentiment())

    yield

    # === SHUTDOWN ===
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")


app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    version="1.0.0",
    description="Real-time prediction market analytics and forecasting platform",
    lifespan=lifespan,
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
app.include_router(prices.router, prefix=settings.API_V1_PREFIX)
app.include_router(sentiment.router, prefix=settings.API_V1_PREFIX)


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
