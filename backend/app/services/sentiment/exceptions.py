# Custom errors for when things go wrong in sentiment analysis - each service has its own error type so we know what broke.


class SentimentServiceError(Exception):
    pass


class RedditClientError(SentimentServiceError):
    pass


class NewsClientError(SentimentServiceError):
    pass


class FinBERTError(SentimentServiceError):
    pass


class RateLimitError(SentimentServiceError):
    pass
