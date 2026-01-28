# Cleans up crypto text before feeding it to the AI - converts emojis to words, expands slang like "hodl" and "wagmi", removes URLs and junk.

import re
from app.core.config import settings

CRYPTO_SLANG = {
    "hodl": "hold long term",
    "mooning": "price increasing dramatically",
    "moon": "price increase",
    "bullish": "positive outlook",
    "bearish": "negative outlook",
    "pump": "price increase",
    "dump": "price decrease",
    "rekt": "significant loss",
    "fomo": "fear of missing out",
    "fud": "fear uncertainty doubt",
    "ath": "all time high",
    "atl": "all time low",
    "dyor": "do your own research",
    "wagmi": "optimistic we will succeed",
    "ngmi": "pessimistic will fail",
    "gm": "good morning positive",
    "lfg": "lets go excited",
    "dip": "price decrease",
    "btd": "buy the dip",
    "btfd": "buy the dip",
    "diamond hands": "holding strong despite losses",
    "paper hands": "selling quickly weak",
    "whale": "large holder",
    "shitcoin": "low quality cryptocurrency",
    "altcoin": "alternative cryptocurrency",
    "defi": "decentralized finance",
    "nft": "non fungible token",
    "rugpull": "scam exit",
    "rug": "scam",
}

EMOJI_SENTIMENTS = {
    "🚀": " bullish rocket ",
    "🌙": " moon bullish ",
    "💎": " diamond hands hold ",
    "🐂": " bullish ",
    "📈": " price up ",
    "💰": " money profit ",
    "🔥": " hot trending ",
    "💪": " strong ",
    "✅": " positive ",
    "👍": " positive ",
    "🎉": " celebration positive ",
    "🐻": " bearish ",
    "📉": " price down ",
    "💀": " dead loss ",
    "😢": " sad negative ",
    "😭": " crying loss ",
    "🤮": " disgust negative ",
    "👎": " negative ",
    "❌": " negative ",
    "⚠️": " warning caution ",
    "🤔": " thinking uncertain ",
    "👀": " watching ",
    "🧐": " analyzing ",
}


class TextPreprocessor:
    def __init__(self, max_length: int = 512):
        self.max_length = max_length
        self._url_pattern = re.compile(r"https?://\S+|www\.\S+")
        self._mention_pattern = re.compile(r"@\w+")
        self._hashtag_pattern = re.compile(r"#(\w+)")
        self._whitespace_pattern = re.compile(r"\s+")
        self._ticker_pattern = re.compile(r"\$([A-Z]{2,5})\b")

    def _replace_emojis(self, text: str) -> str:
        for emoji, replacement in EMOJI_SENTIMENTS.items():
            text = text.replace(emoji, replacement)
        return text

    def _expand_slang(self, text: str) -> str:
        text_lower = text.lower()
        for slang, expansion in CRYPTO_SLANG.items():
            pattern = rf"\b{re.escape(slang)}\b"
            text_lower = re.sub(pattern, expansion, text_lower, flags=re.IGNORECASE)
        return text_lower

    def _clean_text(self, text: str) -> str:
        text = self._url_pattern.sub(" ", text)
        text = self._mention_pattern.sub(" ", text)
        text = self._hashtag_pattern.sub(r"\1", text)
        text = self._ticker_pattern.sub(r"\1", text)
        text = self._whitespace_pattern.sub(" ", text)
        return text.strip()

    def preprocess(self, text: str) -> str:
        if not text:
            return ""

        text = self._replace_emojis(text)
        text = self._clean_text(text)
        text = self._expand_slang(text)

        if len(text) > self.max_length * 4:
            text = text[: self.max_length * 4]

        return text

    def preprocess_batch(self, texts: list[str]) -> list[str]:
        return [self.preprocess(text) for text in texts if text]


text_preprocessor = TextPreprocessor()
