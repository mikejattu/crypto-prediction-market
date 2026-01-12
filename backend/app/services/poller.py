import asyncio
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import AsyncSessionLocal
from app.db.models import Contract, Market, MarketSnapshot, Platform


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


async def ensure_polymarket_platform(session: AsyncSession) -> Platform:
    result = await session.execute(select(Platform).where(Platform.name == "Polymarket"))
    platform = result.scalar_one_or_none()
    if platform:
        return platform
    platform = Platform(
        name="Polymarket",
        api_base_url=settings.POLYMARKET_API_BASE,
        is_active=True,
    )
    session.add(platform)
    await session.commit()
    await session.refresh(platform)
    return platform


async def fetch_polymarket_markets() -> List[Dict[str, Any]]:
    """
    Fetch markets from Polymarket. Handles both list and {"markets": [...]} shapes.
    """
    url = f"{settings.POLYMARKET_API_BASE.rstrip('/')}/markets"
    params = {"limit": 50}
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "markets" in data:
            return data["markets"]  # type: ignore[index]
        if isinstance(data, list):
            return data
        raise ValueError("Unexpected Polymarket response shape")


def _normalize_outcomes(raw_market: Dict[str, Any]) -> List[Dict[str, Any]]:
    outcomes = raw_market.get("outcomes") or raw_market.get("contracts") or []
    normalized: List[Dict[str, Any]] = []
    for outcome in outcomes:
        price = outcome.get("price") or outcome.get("last_price") or outcome.get("p_yes") or 0
        probability = float(outcome.get("implied_prob", price) or 0)
        volume = outcome.get("volume") or outcome.get("volume_24h")
        liquidity = outcome.get("liquidity") or outcome.get("liquidity_usd")
        bid = outcome.get("best_bid") or outcome.get("bid")
        ask = outcome.get("best_ask") or outcome.get("ask")
        spread = None
        if bid is not None and ask is not None:
            spread = float(ask) - float(bid)
        normalized.append(
            {
                "platform_contract_id": str(outcome.get("id") or outcome.get("token_id") or uuid.uuid4()),
                "label": outcome.get("name") or outcome.get("outcome") or "Outcome",
                "probability": float(probability),
                "price": float(price or 0),
                "volume_24h": float(volume) if volume is not None else None,
                "liquidity": float(liquidity) if liquidity is not None else None,
                "bid": float(bid) if bid is not None else None,
                "ask": float(ask) if ask is not None else None,
                "spread": float(spread) if spread is not None else None,
            }
        )
    return normalized


async def upsert_market_and_contracts(
    session: AsyncSession, platform: Platform, raw_market: Dict[str, Any]
) -> List[Contract]:
    platform_market_id = str(raw_market.get("id") or raw_market.get("slug") or uuid.uuid4())
    title = raw_market.get("title") or raw_market.get("question") or "Untitled market"
    question = raw_market.get("question") or title
    tags = raw_market.get("tags") or []
    market_type = "categorical" if len(raw_market.get("outcomes", [])) > 2 else "binary"
    status = raw_market.get("status") or "active"
    close_time_raw = raw_market.get("end_date") or raw_market.get("close_time")
    try:
        close_time = datetime.fromisoformat(close_time_raw).replace(tzinfo=timezone.utc) if close_time_raw else None
    except Exception:
        close_time = None
    if not close_time:
        close_time = datetime.now(timezone.utc) + timedelta(days=30)

    result = await session.execute(
        select(Market).where(
            Market.platform_id == platform.id, Market.platform_market_id == platform_market_id
        )
    )
    market = result.scalar_one_or_none()
    if not market:
        market = Market(
            platform_id=platform.id,
            platform_market_id=platform_market_id,
            title=title,
            description=raw_market.get("description"),
            question=question,
            tags=tags,
            market_type=market_type,
            status=status,
            close_time=close_time,
            total_volume=raw_market.get("volume"),
        )
        session.add(market)
        await session.flush()
    else:
        market.title = title
        market.description = raw_market.get("description") or market.description
        market.question = question
        market.tags = tags
        market.market_type = market_type
        market.status = status
        market.close_time = close_time
        market.total_volume = raw_market.get("volume") or market.total_volume
        market.last_updated = datetime.now(timezone.utc)

    outcomes = _normalize_outcomes(raw_market)
    contracts: List[Contract] = []
    for outcome in outcomes:
        res = await session.execute(
            select(Contract).where(
                Contract.market_id == market.id,
                Contract.platform_contract_id == outcome["platform_contract_id"],
            )
        )
        contract = res.scalar_one_or_none()
        if not contract:
            contract = Contract(
                market_id=market.id,
                platform_contract_id=outcome["platform_contract_id"],
                outcome_label=outcome["label"],
                current_price=outcome["price"],
                current_probability=outcome["probability"],
            )
            session.add(contract)
            await session.flush()
        else:
            contract.outcome_label = outcome["label"]
            contract.current_price = outcome["price"]
            contract.current_probability = outcome["probability"]
            contract.updated_at = datetime.now(timezone.utc)
        contract._outcome_payload = outcome  # type: ignore[attr-defined]
        contracts.append(contract)

    await session.commit()
    return contracts


async def store_snapshots(session: AsyncSession, contracts: List[Contract]) -> int:
    inserted = 0
    for contract in contracts:
        outcome = contract._outcome_payload  # type: ignore[attr-defined]
        payload = {
            "probability": float(outcome["probability"]),
            "price": float(outcome["price"]),
            "volume_24h": outcome.get("volume_24h"),
            "liquidity": outcome.get("liquidity"),
            "bid": outcome.get("bid"),
            "ask": outcome.get("ask"),
            "spread": outcome.get("spread"),
        }
        result = await session.execute(
            select(MarketSnapshot)
            .where(MarketSnapshot.contract_id == contract.id)
            .order_by(MarketSnapshot.timestamp.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()

        def payload_from_snapshot(s: MarketSnapshot) -> Dict[str, Any]:
            return {
                "probability": float(s.probability),
                "price": float(s.price),
                "volume_24h": float(s.volume_24h) if s.volume_24h is not None else None,
                "liquidity": float(s.liquidity) if s.liquidity is not None else None,
                "bid": float(s.bid) if s.bid is not None else None,
                "ask": float(s.ask) if s.ask is not None else None,
                "spread": float(s.spread) if s.spread is not None else None,
            }

        if last and _hash_payload(payload) == _hash_payload(payload_from_snapshot(last)):
            continue

        snapshot = MarketSnapshot(
            timestamp=datetime.now(timezone.utc),
            contract_id=contract.id,
            price=payload["price"],
            probability=payload["probability"],
            volume_24h=payload["volume_24h"],
            liquidity=payload["liquidity"],
            bid=payload["bid"],
            ask=payload["ask"],
            spread=payload["spread"],
        )
        session.add(snapshot)
        inserted += 1

    await session.commit()
    return inserted


async def collect_and_store() -> Dict[str, int]:
    async with AsyncSessionLocal() as session:
        platform = await ensure_polymarket_platform(session)
        markets = await fetch_polymarket_markets()
        total_contracts = 0
        total_snapshots = 0
        for raw_market in markets:
            contracts = await upsert_market_and_contracts(session, platform, raw_market)
            total_contracts += len(contracts)
            total_snapshots += await store_snapshots(session, contracts)
        return {
            "markets_seen": len(markets),
            "contracts_seen": total_contracts,
            "snapshots_inserted": total_snapshots,
        }


async def poller_loop():
    while True:
        try:
            await collect_and_store()
        except Exception as exc:  # noqa: BLE001
            # Lightweight logging to stderr; replace with structured logging later
            print(f"[poller] error: {exc}")
        await asyncio.sleep(settings.POLL_INTERVAL_SECONDS)

