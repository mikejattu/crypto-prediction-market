# MarketPulse 
Real-time **prediction market analytics + forecasting** for markets from **Kalshi** and **Polymarket**.

MarketPulse ingests market metadata and time-series snapshots (implied probabilities/prices), runs forecasting models, and surfaces **Model vs. Market** insights with backtesting and dashboards.

> **Educational project (student capstone).**  
> This app does **not** facilitate betting, does **not** handle real money, and is **not** financial advice.

## What this project does

### Core features
- **Market Explorer**
  - Browse/search/filter markets (by platform, status, time-to-expiry, volume/liquidity when available)
- **Market Detail**
  - Contract info + live implied probability/price chart + indicators
- **Ingestion Pipeline**
  - Market metadata ingestion (events/markets/outcomes)
  - Periodic snapshots for top-N markets (probability/price + volume/liquidity/orderbook when available)
- **Forecasting**
  - Baseline model (MVP) + improved model (final)
  - Forecast endpoint returning model probabilities (and uncertainty once implemented)
- **Model vs. Market**
  - Per-market comparison: implied probability vs model probability + delta
  - Backtested performance summaries
- **Analytics Dashboards**
  - Historical accuracy (Brier score, log loss)
  - Breakdowns by platform, category, and time-to-expiry buckets
  - “Disagreement screener”: markets where model and market diverge most

## Tech stack (current plan)
- **Backend:** Python, FastAPI
- **Frontend:** React + TypeScript
- **Database:** PostgreSQL + TimescaleDB (time-series snapshots)
- **Cache:** Redis (hot endpoints like latest snapshots)
- **Real-time:** SSE or WebSocket
- **Modeling:** scikit-learn / PyTorch (baseline → improved) + evaluation tooling
- **Infra:** Docker + Docker Compose (local); deployment target TBD

## Repository structure (recommended)

.
├── backend/
│   ├── app/
│   │   ├── main.py                # FastAPI entry
│   │   ├── api/                   # REST endpoints
│   │   ├── core/                  # config, logging, utils
│   │   ├── db/                    # models, migrations
│   │   ├── services/
│   │   │   ├── ingest/            # ingestion jobs (kalshi, polymarket)
│   │   │   ├── streaming/         # SSE/WS live updates
│   │   │   ├── forecasting/       # inference endpoints + model loading
│   │   │   └── evaluation/        # backtests + metrics
│   │   └── schemas/               # pydantic DTOs
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── pages/                 # explorer, detail, dashboards
│   │   ├── components/            # charting, filters, cards
│   │   ├── api/                   # typed API client
│   │   └── state/                 # query/cache/store
│   └── tests/
├── infra/
│   ├── docker-compose.yml
│   └── scripts/
└── README.md

