# MarketPulse Database Schema

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
