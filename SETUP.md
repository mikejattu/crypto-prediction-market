# MarketPulse Backend Setup Guide

> Quick setup guide for getting the database and backend running locally

## What You're Building

The backend has two main pieces:
- **Database layer** - PostgreSQL + TimescaleDB for storing market data, with models and migrations
- **API layer** - FastAPI REST endpoints for CRUD operations on platforms, markets, contracts, and crypto categories

Everything talks to each other like this:
```
Frontend (port 5173) → FastAPI (port 8000) → PostgreSQL (port 5432)
                                            → Redis (port 6379)
```

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app - registers all the routes
│   ├── core/
│   │   └── config.py        # Settings loaded from .env.local
│   ├── db/
│   │   ├── database.py      # Database connection pool and session factory
│   │   └── models.py        # SQLAlchemy models (Platform, Market, Contract, etc.)
│   ├── api/
│   │   └── routes/          # API endpoints organized by domain
│   │       ├── platforms.py
│   │       ├── markets.py
│   │       ├── contracts.py
│   │       └── crypto_categories.py
│   └── schemas/             # Pydantic models for request/response validation
│       ├── platform.py
│       ├── market.py
│       ├── contract.py
│       └── crypto_category.py
├── alembic/                 # Database migration files
│   ├── versions/            # Each migration is a timestamped file here
│   └── env.py               # Alembic config (tells it how to connect to DB)
├── scripts/
│   └── seed_data.py         # Populates database with initial test data
├── requirements.txt         # Python dependencies
└── main.py                  # Entry point - starts the uvicorn server
```

---

## Database Schema (Current Tables)

**platforms** - Prediction market platforms like Kalshi, Polymarket
- Fields: id, name, api_base_url, is_active, timestamps
- One platform has many markets

**crypto_categories** - Bitcoin, Ethereum, Solana, etc.
- Fields: id, name, slug, symbol, coingecko_id
- Used to tag markets by cryptocurrency

**markets** - Individual prediction markets/events
- Fields: id, platform_id, title, question, status, close_time, etc.
- Example: "Will Bitcoin reach $100k by Dec 31, 2025?"
- One market has many contracts

**contracts** - Tradeable outcomes within markets
- Fields: id, market_id, outcome_label, current_price, current_probability
- Example: "Yes" contract at 68.5 cents = 68.5% implied probability

---

## Setup Commands

### Step 1: Start the Database Containers

```bash
# From project root
docker-compose -f docker-compose.dev.yml up -d
```

This spins up TimescaleDB (PostgreSQL + time-series extensions) and Redis.
Wait about 10 seconds for the database to initialize.

**Verify it worked:**
```bash
docker ps
```
You should see `timescaledb_dev` and `marketpulse-redis` running.

---

### Step 2: Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `sqlalchemy` - ORM for talking to PostgreSQL
- `asyncpg` - Async PostgreSQL driver
- `alembic` - Database migration tool
- `fastapi` - Web framework
- `pydantic-settings` - Loads config from .env files

---

### Step 3: Configure Environment Variables

Make sure you have a `.env.local` file in `backend/` with your database credentials:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=marketpulse
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/marketpulse
REDIS_URL=redis://localhost:6379

ENVIRONMENT=development
DEBUG=True
```

The backend reads this file on startup to know how to connect to the database.

---

### Step 4: Run Database Migrations

Migrations are like Git commits for your database schema. They track changes to table structure over time.

```bash
# Generate migration from your SQLAlchemy models
alembic revision --autogenerate -m "Create initial tables"

# Apply the migration (actually creates the tables in PostgreSQL)
alembic upgrade head
```

**What just happened:**
- Alembic looked at your `models.py` file
- Generated SQL CREATE TABLE statements
- Executed them in the database

**Verify tables exist:**
```bash
docker exec timescaledb_dev psql -U postgres -d marketpulse -c "\dt"
```

You should see: `platforms`, `crypto_categories`, `markets`, `contracts`, `alembic_version`

---

### Step 5: Seed the Database with Test Data

```bash
python3 scripts/seed_data.py
```

This adds:
- 2 platforms (Kalshi, Polymarket)
- 3 crypto categories (Bitcoin, Ethereum, Solana)
- 1 sample market ("Will Bitcoin reach $100k by Dec 31, 2025?")
- 2 contracts (Yes at 68.5¢, No at 31.5¢)

Now you have realistic data to test your API against.

---

### Step 6: Start the Backend Server

```bash
python3 main.py
```

The FastAPI server starts on **http://localhost:8000**

**Check if it's working:**
```bash
curl http://localhost:8000/health
```

Should return: `{"status": "healthy", "environment": "development"}`

---

## Testing Your API

### Option 1: Interactive Docs (Easiest)

Open **http://localhost:8000/docs** in your browser.

You'll see Swagger UI with all your endpoints. Click on any endpoint, hit "Try it out", and execute it right in the browser.

Try:
- `GET /api/v1/platforms/` - Should return Kalshi and Polymarket
- `GET /api/v1/markets/` - Should return the Bitcoin market
- `GET /api/v1/contracts/` - Should return Yes/No contracts

### Option 2: curl Commands

```bash
# List platforms
curl http://localhost:8000/api/v1/platforms/

# Create a new platform
curl -X POST http://localhost:8000/api/v1/platforms/ \
  -H "Content-Type: application/json" \
  -d '{"name": "PredictIt", "api_base_url": "https://api.predictit.org"}'

# List markets filtered by status
curl "http://localhost:8000/api/v1/markets/?status=active"

# Get contracts for a specific market (replace with actual market ID)
curl "http://localhost:8000/api/v1/contracts/?market_id=<uuid-here>"
```

---

## Common Issues & Fixes

### "ModuleNotFoundError: No module named 'pydantic_settings'"
**Fix:** You forgot to install dependencies.
```bash
pip install -r requirements.txt
```

### "database 'marketpulse' does not exist"
**Fix:** Docker container isn't running or database wasn't created.
```bash
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
# Wait 10 seconds, then try migrations again
```

### "Can't load plugin: sqlalchemy.dialects:driver"
**Fix:** Your `alembic/env.py` isn't configured for async. Make sure it imports your models and uses `async_engine_from_config`.

### Alembic says "there are unresolvable cycles"
**Fix:** This is a warning about circular dependencies between tables. It's safe to ignore as long as the migration completes. We removed the FK constraint on `resolved_outcome_id` to break the cycle.

### Port 5432 already in use
**Fix:** You have another PostgreSQL instance running.
```bash
lsof -i :5432
# Kill the other process, or change the port in docker-compose.dev.yml
```

---

## What's Next?

Once everything is running, you can:
1. **Add more models** - Implement time-series tables like `market_snapshots` for historical price data
2. **Add authentication** - User accounts, JWT tokens, sessions
3. **Build ingestion pipelines** - Fetch real data from Kalshi/Polymarket APIs
4. **Add forecasting** - ML models that predict market outcomes
5. **Deploy to your remote PC** - Set up Cloudflare Tunnel and go live

For now, you have a fully functional CRUD API for prediction markets. All endpoints support create, read, update, and delete operations with proper validation and error handling.

---

## Quick Reference: All Commands in Order

```bash
# Start database
docker-compose -f docker-compose.dev.yml up -d

# Install dependencies
cd backend
pip install -r requirements.txt

# Run migrations
alembic revision --autogenerate -m "Create initial tables"
alembic upgrade head

# Seed database
python3 scripts/seed_data.py

# Start backend
python3 main.py

# Open browser to http://localhost:8000/docs
```

That's it! You now have a working backend with a database, migrations, and REST API.
