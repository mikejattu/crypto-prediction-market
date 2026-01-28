# Grabs posts from Reddit using PRAW - since PRAW is sync, we wrap it in asyncio.to_thread so it doesn't block everything.

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
import praw

from app.core.config import settings
from app.services.sentiment.exceptions import RedditClientError

logger = logging.getLogger(__name__)


class RedditPost:
    def __init__(
        self,
        title: str,
        selftext: str,
        score: int,
        created_utc: datetime,
        subreddit: str,
        num_comments: int,
    ):
        self.title = title
        self.selftext = selftext
        self.score = score
        self.created_utc = created_utc
        self.subreddit = subreddit
        self.num_comments = num_comments

    @property
    def full_text(self) -> str:
        if self.selftext:
            return f"{self.title}. {self.selftext}"
        return self.title


class RedditClient:
    def __init__(self):
        self._reddit: Optional[praw.Reddit] = None

    def _get_reddit(self) -> praw.Reddit:
        if self._reddit is None:
            if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
                raise RedditClientError("Reddit credentials not configured")

            self._reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
        return self._reddit

    def _fetch_posts_sync(
        self,
        subreddits: list[str],
        keywords: list[str],
        limit: int = 100,
        time_filter: str = "hour",
    ) -> list[RedditPost]:
        reddit = self._get_reddit()
        posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)

                for keyword in keywords:
                    try:
                        submissions = subreddit.search(
                            keyword,
                            time_filter=time_filter,
                            limit=limit // len(keywords),
                        )

                        for submission in submissions:
                            post = RedditPost(
                                title=submission.title,
                                selftext=submission.selftext or "",
                                score=submission.score,
                                created_utc=datetime.fromtimestamp(
                                    submission.created_utc, tz=timezone.utc
                                ),
                                subreddit=subreddit_name,
                                num_comments=submission.num_comments,
                            )
                            posts.append(post)
                    except Exception as e:
                        logger.warning(
                            f"Error searching {keyword} in r/{subreddit_name}: {e}"
                        )

            except Exception as e:
                logger.error(f"Error fetching from r/{subreddit_name}: {e}")

        return posts

    async def fetch_posts(
        self,
        keywords: list[str],
        subreddits: Optional[list[str]] = None,
        limit: int = 100,
        time_filter: str = "hour",
    ) -> list[RedditPost]:
        if subreddits is None:
            subreddits = settings.REDDIT_SUBREDDITS

        try:
            posts = await asyncio.to_thread(
                self._fetch_posts_sync, subreddits, keywords, limit, time_filter
            )
            logger.info(f"Fetched {len(posts)} Reddit posts for keywords: {keywords}")
            return posts

        except Exception as e:
            logger.error(f"Reddit fetch error: {e}")
            raise RedditClientError(f"Failed to fetch Reddit posts: {e}")


reddit_client = RedditClient()
