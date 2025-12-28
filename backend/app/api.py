from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


class MarketOption(BaseModel):
    label: str
    probability: float  # 0-1 fraction
    type: Literal["yes", "no", "outcome"]


class Market(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    category: str
    tags: List[str]
    image: Optional[str] = None
    probability: float  # headline probability to feature on the card
    volume_usd: float
    settlement: Optional[str] = None
    cadence: Optional[str] = None
    options: List[MarketOption]


app = FastAPI(title="Crypto Prediction Market API")

origins = ["http://localhost:5173", "localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Prediction market backend is running."}


@app.get("/markets", response_model=List[Market], tags=["markets"])
async def list_markets() -> List[Market]:
    """
    Serve a static set of markets to keep the front-end unblocked.
    Swap this with a database or real data feed later.
    """
    return [
        Market(
            id="daycare-charge",
            title="Will anyone be charged over Daycare?",
            description="Track potential charges in the daycare investigation.",
            category="Trending",
            tags=["All", "Breaking", "Politics"],
            image="https://images.unsplash.com/photo-1520607162513-77705c0f0d4a?auto=format&fit=crop&w=400&q=60",
            probability=0.56,
            volume_usd=21000,
            settlement=None,
            cadence=None,
            options=[
                MarketOption(label="Yes", probability=0.56, type="yes"),
                MarketOption(label="No", probability=0.44, type="no"),
            ],
        ),
        Market(
            id="fed-decision-jan",
            title="Fed decision in January?",
            description="Rate change decision at the January meeting.",
            category="Finance",
            tags=["All", "Finance", "Economy"],
            image="https://images.unsplash.com/photo-1554224154-22dec7ec8818?auto=format&fit=crop&w=400&q=60",
            probability=0.86,
            volume_usd=72000,
            settlement="Monthly",
            cadence="Monthly",
            options=[
                MarketOption(label="No change", probability=0.86, type="outcome"),
                MarketOption(label="25+ bps increase", probability=0.01, type="outcome"),
            ],
        ),
        Market(
            id="superbowl-2026",
            title="Super Bowl Champion 2026",
            description="Winner of the 2026 Super Bowl.",
            category="Sports",
            tags=["All", "Sports"],
            image="https://images.unsplash.com/photo-1518609878373-06d740f60d8b?auto=format&fit=crop&w=400&q=60",
            probability=0.16,
            volume_usd=636000,
            settlement=None,
            cadence=None,
            options=[
                MarketOption(label="Los Angeles R", probability=0.16, type="outcome"),
                MarketOption(label="Seattle", probability=0.13, type="outcome"),
            ],
        ),
        Market(
            id="russia-ukraine-ceasefire",
            title="Russia x Ukraine ceasefire by January 31?",
            description="Whether a ceasefire is agreed by end of January.",
            category="Geopolitics",
            tags=["All", "Geopolitics", "Ukraine"],
            image="https://images.unsplash.com/photo-1477949331575-2763034b5fb5?auto=format&fit=crop&w=400&q=60",
            probability=0.10,
            volume_usd=3000,
            settlement="Jan 31",
            cadence=None,
            options=[
                MarketOption(label="Yes", probability=0.10, type="yes"),
                MarketOption(label="No", probability=0.90, type="no"),
            ],
        ),
        Market(
            id="lsu-vs-houston",
            title="LSU vs Houston halftime winner",
            description="College football halftime markets.",
            category="Sports",
            tags=["All", "Sports"],
            image="https://images.unsplash.com/photo-1502877828070-33c90e4b7f2c?auto=format&fit=crop&w=400&q=60",
            probability=0.23,
            volume_usd=670000,
            settlement="HT",
            cadence=None,
            options=[
                MarketOption(label="Tigers", probability=0.23, type="outcome"),
                MarketOption(label="Cougars", probability=0.77, type="outcome"),
            ],
        ),
        Market(
            id="stranger-things",
            title="Who will die in Stranger Things: Season 5?",
            description="Character death predictions.",
            category="Culture",
            tags=["All", "Culture", "Entertainment"],
            image="https://images.unsplash.com/photo-1464375117522-1311d6a5b81f?auto=format&fit=crop&w=400&q=60",
            probability=0.05,
            volume_usd=1000000,
            settlement=None,
            cadence=None,
            options=[
                MarketOption(label="Holly Wheeler", probability=0.05, type="outcome"),
                MarketOption(label="Mike Wheeler", probability=0.04, type="outcome"),
            ],
        ),
        Market(
            id="ukraine-ceasefire-framework",
            title="Ukraine agrees to US-backed ceasefire framework?",
            description="Whether the framework is officially agreed.",
            category="Geopolitics",
            tags=["All", "Geopolitics", "Ukraine"],
            image="https://images.unsplash.com/photo-1509099836639-18ba02e2e9c5?auto=format&fit=crop&w=400&q=60",
            probability=0.17,
            volume_usd=462000,
            settlement="Dec 31",
            cadence=None,
            options=[
                MarketOption(label="December 31", probability=0.17, type="outcome"),
                MarketOption(label="January 31", probability=0.35, type="outcome"),
            ],
        ),
        Market(
            id="trump-meet-zelenskyy",
            title="Will Trump meet with Zelenskyy?",
            description="Meeting by specific December dates.",
            category="Politics",
            tags=["All", "Trump", "Ukraine"],
            image="https://images.unsplash.com/photo-1508672019048-805c876b67e2?auto=format&fit=crop&w=400&q=60",
            probability=0.99,
            volume_usd=3000,
            settlement="Dec 28",
            cadence=None,
            options=[
                MarketOption(label="December 27", probability=0.01, type="outcome"),
                MarketOption(label="December 28", probability=0.99, type="outcome"),
            ],
        ),
    ]
