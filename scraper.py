import os
import time
import logging
import feedparser
from supabase import create_client

logger = logging.getLogger(__name__)

NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.1d4.us",
]


def get_db():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def get_theme_for_slot(hour_utc: int) -> dict:
    db = get_db()
    result = db.table("themes").select("*").eq("post_hour_utc", hour_utc).eq("active", True).execute()
    if not result.data:
        nearest = (hour_utc // 2) * 2
        logger.info(f"No theme for hour {hour_utc}, falling back to hour {nearest}")
        result = db.table("themes").select("*").eq("post_hour_utc", nearest).eq("active", True).execute()
    if not result.data:
        raise ValueError(f"No active theme found for UTC hour {hour_utc}")
    return result.data[0]


def get_accounts_for_theme(theme_id: int) -> list[str]:
    db = get_db()
    result = db.table("theme_accounts").select("twitter_handle").eq("theme_id", theme_id).execute()
    return [row["twitter_handle"] for row in result.data]


def _fetch_rss(handle: str) -> list[dict]:
    """Try each Nitter instance until one returns tweets for this handle."""
    for instance in NITTER_INSTANCES:
        url = f"{instance}/{handle}/rss"
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                tweets = []
                for entry in feed.entries[:5]:
                    text = entry.get("summary", "") or entry.get("title", "")
                    # Strip HTML tags
                    import re
                    text = re.sub(r"<[^>]+>", "", text).strip()
                    link = entry.get("link", f"https://twitter.com/{handle}")
                    if text:
                        tweets.append({
                            "text": text,
                            "author": handle,
                            "url": link,
                            "likes": 0,
                            "views": 0,
                            "retweets": 0,
                            "replies": 0,
                            "engagement_score": 0,
                        })
                return tweets
        except Exception as e:
            logger.warning(f"Nitter instance {instance} failed for @{handle}: {e}")
            continue
    return []


def scrape_tweets_for_accounts(handles: list[str]) -> list[dict]:
    """Fetch recent tweets from all accounts via Nitter RSS."""
    all_tweets = []

    for handle in handles:
        tweets = _fetch_rss(handle)
        all_tweets.extend(tweets)
        time.sleep(0.3)

    logger.info(f"Fetched {len(all_tweets)} tweets total.")
    return all_tweets


def get_most_viral_tweet(tweets: list[dict]) -> dict:
    """
    Since RSS has no engagement data, pick the longest/most substantive tweet
    as a proxy for content quality. Claude will do the real curation.
    """
    if not tweets:
        raise ValueError("No tweets found to rank.")
    best = max(tweets, key=lambda t: len(t["text"]))
    logger.info(f"Selected tweet from @{best['author']} ({len(best['text'])} chars)")
    return best


def scrape(hour_utc: int) -> tuple[dict, dict]:
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")

    handles = get_accounts_for_theme(theme["id"])
    logger.info(f"Loaded {len(handles)} accounts.")

    tweets = scrape_tweets_for_accounts(handles)
    viral_tweet = get_most_viral_tweet(tweets)

    return theme, viral_tweet
