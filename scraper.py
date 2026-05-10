import os
import time
import logging
from datetime import datetime, timezone
import tweepy
from supabase import create_client

logger = logging.getLogger(__name__)

MAX_TWEETS_PER_ACCOUNT = 5


def get_db():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def get_theme_for_slot(hour_utc: int) -> dict:
    """Return the theme whose post_hour_utc matches the current UTC hour.
    If no exact match, round down to nearest even hour."""
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


def _twitter_client() -> tweepy.Client:
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
        wait_on_rate_limit=True,
    )


def scrape_tweets_for_accounts(handles: list[str]) -> list[dict]:
    """Fetch recent tweets from all accounts using Twitter API v2."""
    client = _twitter_client()
    tweets = []

    # Batch resolve all usernames to user IDs in one call
    logger.info(f"Resolving {len(handles)} user IDs ...")
    try:
        response = client.get_users(usernames=handles, user_fields=["id", "username"])
        users = response.data or []
    except Exception as e:
        logger.error(f"Failed to resolve user IDs: {e}")
        return []

    logger.info(f"Resolved {len(users)} users. Fetching timelines ...")

    for user in users:
        try:
            resp = client.get_users_tweets(
                id=user.id,
                max_results=MAX_TWEETS_PER_ACCOUNT,
                tweet_fields=["public_metrics", "created_at", "text"],
                exclude=["retweets", "replies"],
            )
            if not resp.data:
                continue

            for tweet in resp.data:
                m = tweet.public_metrics or {}
                likes    = m.get("like_count", 0)
                retweets = m.get("retweet_count", 0)
                replies  = m.get("reply_count", 0)
                quotes   = m.get("quote_count", 0)
                views    = m.get("impression_count", 0)
                engagement = likes + (views // 100) + (retweets * 3) + (replies * 2) + (quotes * 2)

                tweets.append({
                    "text": tweet.text,
                    "author": user.username,
                    "url": f"https://twitter.com/{user.username}/status/{tweet.id}",
                    "likes": likes,
                    "views": views,
                    "retweets": retweets,
                    "replies": replies,
                    "engagement_score": engagement,
                })

            time.sleep(0.5)  # avoid hitting rate limits

        except tweepy.TweepyException as e:
            logger.warning(f"Failed to fetch tweets for @{user.username}: {e}")
            continue

    logger.info(f"Fetched {len(tweets)} tweets total.")
    return tweets


def get_most_viral_tweet(tweets: list[dict]) -> dict:
    if not tweets:
        raise ValueError("No tweets found to rank.")
    best = max(tweets, key=lambda t: t["engagement_score"])
    logger.info(f"Most viral: @{best['author']} — {best['likes']} likes, {best['views']} views")
    return best


def scrape(hour_utc: int) -> tuple[dict, dict]:
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")

    handles = get_accounts_for_theme(theme["id"])
    logger.info(f"Loaded {len(handles)} accounts.")

    tweets = scrape_tweets_for_accounts(handles)
    viral_tweet = get_most_viral_tweet(tweets)

    return theme, viral_tweet
