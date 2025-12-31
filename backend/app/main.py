from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import platforms, markets, contracts, crypto_categories

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
