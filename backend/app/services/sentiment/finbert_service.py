# Runs FinBERT (a finance-tuned AI model) to figure out if text is bullish, bearish, or neutral - lazy loads the model so startup isn't slow.

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from app.core.config import settings
from app.services.sentiment.exceptions import FinBERTError

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    positive: float
    negative: float
    neutral: float

    @property
    def composite_score(self) -> float:
        return self.positive - self.negative

    def to_decimal(self) -> dict:
        return {
            "positive_score": Decimal(str(round(self.positive, 4))),
            "negative_score": Decimal(str(round(self.negative, 4))),
            "neutral_score": Decimal(str(round(self.neutral, 4))),
            "composite_score": Decimal(str(round(self.composite_score, 4))),
        }


class FinBERTService:
    def __init__(self):
        self._model = None
        self._tokenizer = None
        self._device = None
        self._initialized = False
        self._lock = asyncio.Lock()

    def _load_model_sync(self) -> None:
        if self._initialized:
            return

        logger.info(f"Loading FinBERT model: {settings.FINBERT_MODEL_NAME}")

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL_NAME)
            self._model = AutoModelForSequenceClassification.from_pretrained(
                settings.FINBERT_MODEL_NAME
            )

            self._device = torch.device(
                "cuda" if torch.cuda.is_available() else "cpu"
            )
            self._model.to(self._device)
            self._model.eval()

            self._initialized = True
            logger.info(f"FinBERT loaded on device: {self._device}")

        except Exception as e:
            logger.error(f"Failed to load FinBERT: {e}")
            raise FinBERTError(f"Model loading failed: {e}")

    async def _ensure_loaded(self) -> None:
        if self._initialized:
            return

        async with self._lock:
            if not self._initialized:
                await asyncio.to_thread(self._load_model_sync)

    def _infer_batch_sync(self, texts: list[str]) -> list[SentimentResult]:
        if not texts:
            return []

        results = []
        batch_size = settings.FINBERT_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i : i + batch_size]

            try:
                inputs = self._tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=settings.FINBERT_MAX_LENGTH,
                    return_tensors="pt",
                )
                inputs = {k: v.to(self._device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = self._model(**inputs)
                    probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

                for prob in probs:
                    result = SentimentResult(
                        positive=prob[0].item(),
                        negative=prob[1].item(),
                        neutral=prob[2].item(),
                    )
                    results.append(result)

            except Exception as e:
                logger.error(f"FinBERT inference error: {e}")
                for _ in batch_texts:
                    results.append(
                        SentimentResult(
                            positive=0.33,
                            negative=0.33,
                            neutral=0.34,
                        )
                    )

        return results

    async def analyze(self, text: str) -> SentimentResult:
        await self._ensure_loaded()
        results = await asyncio.to_thread(self._infer_batch_sync, [text])
        return results[0] if results else SentimentResult(0.33, 0.33, 0.34)

    async def analyze_batch(self, texts: list[str]) -> list[SentimentResult]:
        await self._ensure_loaded()

        if not texts:
            return []

        return await asyncio.to_thread(self._infer_batch_sync, texts)


finbert_service = FinBERTService()
