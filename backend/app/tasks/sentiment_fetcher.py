# The main job that runs every hour - grabs posts from Reddit and news sites, runs them through FinBERT, and saves the aggregated scores to the database.

import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.database import AsyncSessionLocal
from app.db.models import CryptoCategory, SentimentScore
from app.services.sentiment.reddit_client import reddit_client
from app.services.sentiment.news_client import news_client
from app.services.sentiment.text_preprocessor import text_preprocessor
from app.services.sentiment.finbert_service import finbert_service
from app.services.sentiment.aggregator import sentiment_aggregator, WeightedText
from app.services.sentiment.exceptions import SentimentServiceError, RateLimitError

logger = logging.getLogger(__name__)

CRYPTO_KEYWORDS = {
    "BTC": ["bitcoin", "BTC", "$BTC"],
    "ETH": ["ethereum", "ETH", "$ETH", "ether"],
    "SOL": ["solana", "SOL", "$SOL"],
    "XRP": ["ripple", "XRP", "$XRP"],
    "ADA": ["cardano", "ADA", "$ADA"],
    "DOGE": ["dogecoin", "DOGE", "$DOGE"],
    "DOT": ["polkadot", "DOT", "$DOT"],
    "AVAX": ["avalanche", "AVAX", "$AVAX"],
    "LINK": ["chainlink", "LINK", "$LINK"],
    "MATIC": ["polygon", "MATIC", "$MATIC"],
}


async def _fetch_reddit_for_crypto(
    symbol: str, window_start: datetime, window_end: datetime
) -> list[WeightedText]:
    keywords = CRYPTO_KEYWORDS.get(symbol, [symbol.lower()])

    try:
        posts = await reddit_client.fetch_posts(
            keywords=keywords, time_filter="hour", limit=50
        )

        weighted_texts = []
        for post in posts:
            if window_start <= post.created_utc <= window_end:
                preprocessed = text_preprocessor.preprocess(post.full_text)
                if preprocessed:
                    weight = sentiment_aggregator.calculate_reddit_weight(
                        post.score, post.num_comments
                    )
                    weighted_texts.append(WeightedText(text=preprocessed, weight=weight))

        return weighted_texts

    except SentimentServiceError as e:
        logger.warning(f"Reddit fetch failed for {symbol}: {e}")
        return []


async def _fetch_news_for_crypto(
    symbol: str, window_start: datetime
) -> tuple[list[WeightedText], list[WeightedText]]:
    cryptopanic_texts = []
    newsapi_texts = []

    try:
        articles = await news_client.fetch_cryptopanic(
            currencies=[symbol], filter_type="rising"
        )

        for article in articles:
            preprocessed = text_preprocessor.preprocess(article.full_text)
            if preprocessed:
                weight = sentiment_aggregator.calculate_news_weight("cryptopanic")
                cryptopanic_texts.append(WeightedText(text=preprocessed, weight=weight))

    except SentimentServiceError as e:
        logger.warning(f"CryptoPanic fetch failed for {symbol}: {e}")

    try:
        keywords = CRYPTO_KEYWORDS.get(symbol, [symbol.lower()])
        articles = await news_client.fetch_newsapi(
            keywords=keywords[:2], from_date=window_start
        )

        for article in articles:
            preprocessed = text_preprocessor.preprocess(article.full_text)
            if preprocessed:
                weight = sentiment_aggregator.calculate_news_weight("newsapi")
                newsapi_texts.append(WeightedText(text=preprocessed, weight=weight))

    except RateLimitError:
        logger.warning(f"NewsAPI rate limit reached, skipping for {symbol}")
    except SentimentServiceError as e:
        logger.warning(f"NewsAPI fetch failed for {symbol}: {e}")

    return cryptopanic_texts, newsapi_texts


async def _run_sentiment_analysis(
    weighted_texts: list[WeightedText],
) -> list[WeightedText]:
    if not weighted_texts:
        return []

    texts = [wt.text for wt in weighted_texts]

    try:
        results = await finbert_service.analyze_batch(texts)

        for wt, result in zip(weighted_texts, results):
            wt.sentiment = result

        return weighted_texts

    except SentimentServiceError as e:
        logger.error(f"FinBERT analysis failed: {e}")
        return []


async def _store_sentiment_score(
    crypto_category_id, source: str, aggregated
) -> None:
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                pg_insert(SentimentScore)
                .values(
                    crypto_category_id=crypto_category_id,
                    source=source,
                    window_start=aggregated.window_start,
                    window_end=aggregated.window_end,
                    positive_score=aggregated.positive_score,
                    negative_score=aggregated.negative_score,
                    neutral_score=aggregated.neutral_score,
                    composite_score=aggregated.composite_score,
                    sample_count=aggregated.sample_count,
                )
                .on_conflict_do_update(
                    constraint="uq_sentiment_crypto_source_window",
                    set_={
                        "positive_score": aggregated.positive_score,
                        "negative_score": aggregated.negative_score,
                        "neutral_score": aggregated.neutral_score,
                        "composite_score": aggregated.composite_score,
                        "sample_count": aggregated.sample_count,
                    },
                )
            )

            await db.execute(stmt)
            await db.commit()

        except Exception as e:
            logger.error(f"Failed to store sentiment: {e}")
            await db.rollback()
            raise


async def fetch_and_store_sentiment() -> dict:
    now = datetime.now(timezone.utc)
    window_end = now.replace(minute=0, second=0, microsecond=0)
    window_start = window_end - timedelta(hours=1)

    logger.info(f"Starting sentiment analysis for window: {window_start} - {window_end}")

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(CryptoCategory).where(CryptoCategory.symbol.isnot(None))
            )
            categories = result.scalars().all()

            if not categories:
                logger.warning("No crypto categories found with symbols")
                return {"status": "skipped", "reason": "no_categories"}

            stats = {
                "processed": 0,
                "reddit_scores": 0,
                "cryptopanic_scores": 0,
                "newsapi_scores": 0,
                "errors": 0,
            }

            for category in categories:
                symbol = category.symbol.upper()
                logger.info(f"Processing sentiment for {symbol}")

                try:
                    reddit_texts = await _fetch_reddit_for_crypto(
                        symbol, window_start, window_end
                    )
                    cryptopanic_texts, newsapi_texts = await _fetch_news_for_crypto(
                        symbol, window_start
                    )

                    all_texts = reddit_texts + cryptopanic_texts + newsapi_texts
                    if all_texts:
                        all_texts = await _run_sentiment_analysis(all_texts)

                    reddit_count = len(reddit_texts)
                    cryptopanic_count = len(cryptopanic_texts)

                    if reddit_texts:
                        analyzed_reddit = all_texts[:reddit_count]
                        reddit_agg = sentiment_aggregator.aggregate(
                            analyzed_reddit, window_start, window_end
                        )
                        if reddit_agg:
                            await _store_sentiment_score(
                                category.id, "reddit", reddit_agg
                            )
                            stats["reddit_scores"] += 1

                    if cryptopanic_texts:
                        analyzed_cp = all_texts[
                            reddit_count : reddit_count + cryptopanic_count
                        ]
                        cp_agg = sentiment_aggregator.aggregate(
                            analyzed_cp, window_start, window_end
                        )
                        if cp_agg:
                            await _store_sentiment_score(
                                category.id, "cryptopanic", cp_agg
                            )
                            stats["cryptopanic_scores"] += 1

                    if newsapi_texts:
                        analyzed_news = all_texts[reddit_count + cryptopanic_count :]
                        news_agg = sentiment_aggregator.aggregate(
                            analyzed_news, window_start, window_end
                        )
                        if news_agg:
                            await _store_sentiment_score(
                                category.id, "newsapi", news_agg
                            )
                            stats["newsapi_scores"] += 1

                    stats["processed"] += 1

                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    stats["errors"] += 1

            logger.info(f"Sentiment analysis complete: {stats}")
            return {"status": "success", **stats}

        except Exception as e:
            logger.exception(f"Unexpected error in sentiment task: {e}")
            return {"status": "error", "error": str(e)}
