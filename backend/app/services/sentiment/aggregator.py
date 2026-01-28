# Crunches individual sentiment scores into hourly averages - weights by engagement (upvotes, comments) so viral posts count more.

import math
import logging
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional

from app.services.sentiment.finbert_service import SentimentResult

logger = logging.getLogger(__name__)


@dataclass
class WeightedText:
    text: str
    weight: float
    sentiment: Optional[SentimentResult] = None


@dataclass
class AggregatedSentiment:
    positive_score: Decimal
    negative_score: Decimal
    neutral_score: Decimal
    composite_score: Decimal
    sample_count: int
    window_start: datetime
    window_end: datetime


class SentimentAggregator:
    def __init__(self, min_weight: float = 0.1, max_weight: float = 10.0):
        self.min_weight = min_weight
        self.max_weight = max_weight

    def calculate_reddit_weight(self, score: int, num_comments: int) -> float:
        weight = 1.0

        if score > 0:
            weight += math.log10(score + 1) * 0.5

        if num_comments > 0:
            weight += math.log10(num_comments + 1) * 0.3

        return max(self.min_weight, min(self.max_weight, weight))

    def calculate_news_weight(self, source: str) -> float:
        if source == "cryptopanic":
            return 1.5
        return 1.0

    def aggregate(
        self,
        weighted_texts: list[WeightedText],
        window_start: datetime,
        window_end: datetime,
    ) -> Optional[AggregatedSentiment]:
        valid_texts = [wt for wt in weighted_texts if wt.sentiment is not None]

        if not valid_texts:
            return None

        total_weight = sum(wt.weight for wt in valid_texts)

        weighted_positive = (
            sum(wt.sentiment.positive * wt.weight for wt in valid_texts) / total_weight
        )

        weighted_negative = (
            sum(wt.sentiment.negative * wt.weight for wt in valid_texts) / total_weight
        )

        weighted_neutral = (
            sum(wt.sentiment.neutral * wt.weight for wt in valid_texts) / total_weight
        )

        weighted_composite = (
            sum(wt.sentiment.composite_score * wt.weight for wt in valid_texts)
            / total_weight
        )

        return AggregatedSentiment(
            positive_score=Decimal(str(round(weighted_positive, 4))),
            negative_score=Decimal(str(round(weighted_negative, 4))),
            neutral_score=Decimal(str(round(weighted_neutral, 4))),
            composite_score=Decimal(str(round(weighted_composite, 4))),
            sample_count=len(valid_texts),
            window_start=window_start,
            window_end=window_end,
        )


sentiment_aggregator = SentimentAggregator()
