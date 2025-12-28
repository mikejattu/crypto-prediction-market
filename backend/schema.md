# MarketPulse Database Schema
# ALL ARE SUBJECT TO CHANGE, THIS DOCUMENT TO SERVE A REFERENCE STARTING POINT
## 1. Core Market Data

### `platforms`

**Purpose:** Reference table for prediction market platforms.

**Schema:**
```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
name              VARCHAR(50) UNIQUE NOT NULL
api_base_url      VARCHAR(255) NOT NULL
is_active         BOOLEAN DEFAULT true
created_at        TIMESTAMP DEFAULT NOW()
updated_at        TIMESTAMP DEFAULT NOW()
```

**Example Data:**
- Kalshi
- Polymarket

---

### `crypto_categories`

**Purpose:** Cryptocurrency/token categories for market organization.

**Schema:**
```sql
id                UUID PRIMARY KEY DEFAULT gen_random_uuid()
name              VARCHAR(100) UNIQUE NOT NULL
slug              VARCHAR(100) UNIQUE NOT NULL
description       TEXT
symbol            VARCHAR(20)
coingecko_id      VARCHAR(100)
created_at        TIMESTAMP DEFAULT NOW()
```

**Example Data:**
- Bitcoin (BTC)
- Ethereum (ETH)
- Solana (SOL)
- Memecoins

---

### `markets`

**Purpose:** Individual prediction markets/events related to cryptocurrency.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
platform_id             UUID REFERENCES platforms(id) NOT NULL
platform_market_id      VARCHAR(255) NOT NULL
crypto_category_id      UUID REFERENCES crypto_categories(id)
title                   VARCHAR(500) NOT NULL
description             TEXT
question                TEXT NOT NULL
tags                    JSONB
market_type             VARCHAR(20) NOT NULL  -- 'binary', 'categorical'
status                  VARCHAR(20) NOT NULL  -- 'active', 'closed', 'resolved', 'cancelled'
created_at              TIMESTAMP DEFAULT NOW()
close_time              TIMESTAMP NOT NULL
resolution_time         TIMESTAMP
resolved_outcome_id     UUID REFERENCES contracts(id)
total_volume            DECIMAL(20, 2)
last_updated            TIMESTAMP DEFAULT NOW()

CONSTRAINT unique_platform_market UNIQUE(platform_id, platform_market_id)
```


### `contracts`

**Purpose:** Tradeable outcomes within markets (Yes/No or multiple choice options).

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
market_id               UUID REFERENCES markets(id) ON DELETE CASCADE NOT NULL
platform_contract_id    VARCHAR(255) NOT NULL
outcome_label           VARCHAR(255) NOT NULL
is_winner               BOOLEAN
current_price           DECIMAL(10, 4) NOT NULL
current_probability     DECIMAL(5, 4) NOT NULL
last_trade_time         TIMESTAMP
created_at              TIMESTAMP DEFAULT NOW()
updated_at              TIMESTAMP DEFAULT NOW()

CONSTRAINT unique_market_contract UNIQUE(market_id, platform_contract_id)
```
---

## 2. Time-Series Data (TimescaleDB Hypertables)

### `market_snapshots` ⏱️

**Purpose:** Periodic captures of contract prices and trading activity.

**Schema:**
```sql
timestamp               TIMESTAMP NOT NULL
contract_id             UUID REFERENCES contracts(id) NOT NULL
price                   DECIMAL(10, 4) NOT NULL
probability             DECIMAL(5, 4) NOT NULL
volume_24h              DECIMAL(20, 2)
liquidity               DECIMAL(20, 2)
bid                     DECIMAL(10, 4)
ask                     DECIMAL(10, 4)
spread                  DECIMAL(10, 4)

PRIMARY KEY (timestamp, contract_id)
```

---

### `technical_indicators` ⏱️

**Purpose:** Computed technical analysis indicators (SMA, RSI, volatility, etc.).

**Schema:**
```sql
timestamp               TIMESTAMP NOT NULL
contract_id             UUID REFERENCES contracts(id) NOT NULL
indicator_type          VARCHAR(50) NOT NULL  -- 'SMA_7', 'SMA_30', 'RSI', 'VOLATILITY'
value                   DECIMAL(10, 4) NOT NULL
metadata                JSONB

PRIMARY KEY (timestamp, contract_id, indicator_type)
```
---

### `sentiment_snapshots` ⏱️

**Purpose:** Social media sentiment analysis aggregated from Twitter, Reddit, and news.

**Schema:**
```sql
timestamp               TIMESTAMP NOT NULL
market_id               UUID REFERENCES markets(id) NOT NULL
source                  VARCHAR(50) NOT NULL  -- 'twitter', 'reddit', 'news'
sentiment_score         DECIMAL(3, 2) NOT NULL  -- -1.00 to 1.00
mention_volume          INTEGER NOT NULL
positive_count          INTEGER DEFAULT 0
negative_count          INTEGER DEFAULT 0
neutral_count           INTEGER DEFAULT 0
top_keywords            JSONB

PRIMARY KEY (timestamp, market_id, source)
```

---

### `model_forecasts` ⏱️

**Purpose:** Model predictions over time with confidence intervals.

**Schema:**
```sql
timestamp                       TIMESTAMP NOT NULL
contract_id                     UUID REFERENCES contracts(id) NOT NULL
model_version_id                UUID REFERENCES model_versions(id) NOT NULL
predicted_probability           DECIMAL(5, 4) NOT NULL
confidence_interval_lower       DECIMAL(5, 4)
confidence_interval_upper       DECIMAL(5, 4)
market_price_at_forecast        DECIMAL(10, 4) NOT NULL
time_to_close_hours             DECIMAL(10, 2) NOT NULL

PRIMARY KEY (timestamp, contract_id, model_version_id)
```

---

### `accuracy_metrics` ⏱️

**Purpose:** Pre-aggregated model performance metrics for dashboard queries.

**Schema:**
```sql
timestamp                TIMESTAMP NOT NULL
model_version_id         UUID REFERENCES model_versions(id) NOT NULL
aggregation_level        VARCHAR(50) NOT NULL  -- 'overall', 'by_platform', 'by_category', 'by_time_bucket'
aggregation_key          VARCHAR(100) NOT NULL
num_predictions          INTEGER NOT NULL
avg_brier_score          DECIMAL(6, 4)
avg_log_loss             DECIMAL(6, 4)
accuracy                 DECIMAL(5, 4)
avg_divergence           DECIMAL(5, 4)

PRIMARY KEY (timestamp, model_version_id, aggregation_level, aggregation_key)
```
---


## 3. User & Authentication

### `users`

**Purpose:** User accounts for authentication and social features.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
email                   VARCHAR(255) UNIQUE NOT NULL
username                VARCHAR(50) UNIQUE NOT NULL
hashed_password         VARCHAR(255) NOT NULL
display_name            VARCHAR(100)
avatar_url              VARCHAR(500)
is_active               BOOLEAN DEFAULT true
email_verified          BOOLEAN DEFAULT false
created_at              TIMESTAMP DEFAULT NOW()
last_login              TIMESTAMP
```
---

### `user_sessions`

**Purpose:** Active login sessions (optional if using JWT).

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id                 UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL
token_hash              VARCHAR(255) UNIQUE NOT NULL
created_at              TIMESTAMP DEFAULT NOW()
expires_at              TIMESTAMP NOT NULL
last_activity           TIMESTAMP DEFAULT NOW()
```

---

## 4. Social Features

### `comments`

**Purpose:** User comments and analysis on specific markets.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
market_id               UUID REFERENCES markets(id) ON DELETE CASCADE NOT NULL
user_id                 UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL
content                 TEXT NOT NULL
is_edited               BOOLEAN DEFAULT false
created_at              TIMESTAMP DEFAULT NOW()
updated_at              TIMESTAMP
```


---

### `watchlists`

**Purpose:** User-saved favorite markets for tracking.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
user_id                 UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL
market_id               UUID REFERENCES markets(id) ON DELETE CASCADE NOT NULL
added_at                TIMESTAMP DEFAULT NOW()
notes                   TEXT

CONSTRAINT unique_user_market_watch UNIQUE(user_id, market_id)
```

---

## 5. Forecasting & Models

### `model_versions`

**Purpose:** Track different model iterations and configurations.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
version_name            VARCHAR(100) UNIQUE NOT NULL
model_type              VARCHAR(50) NOT NULL  -- 'logistic_regression', 'random_forest', 'lstm', 'ensemble'
description             TEXT
hyperparameters         JSONB
feature_set             JSONB
training_metrics        JSONB
is_active               BOOLEAN DEFAULT false
created_at              TIMESTAMP DEFAULT NOW()
deployed_at             TIMESTAMP
```

---

## 6. Analytics & Backtesting

### `backtest_runs`

**Purpose:** Metadata for backtesting experiments.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
model_version_id        UUID REFERENCES model_versions(id) NOT NULL
run_name                VARCHAR(255) NOT NULL
data_start_date         TIMESTAMP NOT NULL
data_end_date           TIMESTAMP NOT NULL
num_markets             INTEGER DEFAULT 0
num_predictions         INTEGER DEFAULT 0
overall_metrics         JSONB
created_at              TIMESTAMP DEFAULT NOW()
completed_at            TIMESTAMP
status                  VARCHAR(20) NOT NULL  -- 'running', 'completed', 'failed'
```

---

### `backtest_results`

**Purpose:** Individual prediction outcomes from backtests.

**Schema:**
```sql
id                              UUID PRIMARY KEY DEFAULT gen_random_uuid()
backtest_run_id                 UUID REFERENCES backtest_runs(id) ON DELETE CASCADE NOT NULL
market_id                       UUID REFERENCES markets(id) NOT NULL
contract_id                     UUID REFERENCES contracts(id) NOT NULL
prediction_timestamp            TIMESTAMP NOT NULL
predicted_probability           DECIMAL(5, 4) NOT NULL
actual_outcome                  DECIMAL(5, 4) NOT NULL
market_probability_at_prediction DECIMAL(5, 4) NOT NULL
time_to_resolution_hours        DECIMAL(10, 2) NOT NULL
brier_score                     DECIMAL(6, 4) NOT NULL
log_loss                        DECIMAL(6, 4) NOT NULL
category                        VARCHAR(100)
platform                        VARCHAR(50)
```

---

## 7. System Monitoring

### `ingestion_jobs`

**Purpose:** Log data pipeline runs for monitoring and debugging.

**Schema:**
```sql
id                      UUID PRIMARY KEY DEFAULT gen_random_uuid()
platform_id             UUID REFERENCES platforms(id)
job_type                VARCHAR(50) NOT NULL  -- 'metadata_sync', 'snapshot_batch', 'sentiment_scrape'
started_at              TIMESTAMP DEFAULT NOW()
completed_at            TIMESTAMP
status                  VARCHAR(20) NOT NULL  -- 'running', 'success', 'failed'
items_processed         INTEGER DEFAULT 0
errors                  JSONB
```

---

**Document Version:** 1.0  
**Maintained By:** Aryan  
**Last Review:** December 2025