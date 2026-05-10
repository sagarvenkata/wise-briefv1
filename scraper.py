import os
import logging
from supabase import create_client

logger = logging.getLogger(__name__)


def get_db():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def get_theme_for_slot(hour_utc: int) -> dict:
    """Return the theme whose post_hour_utc matches the current UTC hour.
    If no exact match, round down to nearest even hour."""
    db = get_db()
    result = db.table("themes").select("*").eq("post_hour_utc", hour_utc).eq("active", True).execute()
    if not result.data:
        # Round down to nearest scheduled hour (even hours 0,2,4...22)
        nearest = (hour_utc // 2) * 2
        logger.info(f"No theme for hour {hour_utc}, falling back to hour {nearest}")
        result = db.table("themes").select("*").eq("post_hour_utc", nearest).eq("active", True).execute()
    if not result.data:
        raise ValueError(f"No active theme found for UTC hour {hour_utc}")
    return result.data[0]


def get_accounts_for_theme(theme_id: int) -> list[str]:
    """Return list of twitter handles for a theme."""
    db = get_db()
    result = db.table("theme_accounts").select("twitter_handle").eq("theme_id", theme_id).execute()
    return [row["twitter_handle"] for row in result.data]


def scrape_tweets_for_accounts(handles: list[str]) -> list[dict]:
    """Use Apify Twitter scraper to fetch recent tweets from all 20 accounts."""
    from apify_client import ApifyClient
    client = ApifyClient(os.environ["APIFY_API_TOKEN"])

    logger.info(f"Scraping tweets from {len(handles)} accounts via Apify ...")

    all_tweets = []

    for handle in handles:
        try:
            run = client.actor("quacker/twitter-scraper").call(
                run_input={
                    "handle": handle,
                    "tweetsDesired": 5,
                }
            )
            items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        except Exception as e:
            logger.warning(f"Apify failed for @{handle}: {e}")
            continue

        for item in items:
            likes = item.get("favorite_count", 0) or item.get("likeCount", 0) or 0
            views = item.get("views", {}).get("count", 0) if isinstance(item.get("views"), dict) else item.get("viewCount", 0) or 0
            retweets = item.get("retweet_count", 0) or item.get("retweetCount", 0) or 0
            replies = item.get("reply_count", 0) or item.get("replyCount", 0) or 0
            engagement = likes + (views // 100) + (retweets * 3) + (replies * 2)

            text = item.get("full_text", "") or item.get("text", "")
            url = f"https://twitter.com/{handle}/status/{item.get('id_str', item.get('id', ''))}"

            if text:
                all_tweets.append({
                    "text": text,
                    "author": handle,
                    "url": url,
                    "likes": likes,
                    "views": views,
                    "retweets": retweets,
                    "replies": replies,
                    "engagement_score": engagement,
                })

    logger.info(f"Fetched {len(all_tweets)} tweets total.")
    return all_tweets


def get_most_viral_tweet(tweets: list[dict]) -> dict:
    """Return the single tweet with the highest engagement score."""
    if not tweets:
        raise ValueError("No tweets found to rank.")
    best = max(tweets, key=lambda t: t["engagement_score"])
    logger.info(f"Most viral tweet: @{best['author']} — {best['likes']} likes, {best['views']} views")
    return best


def scrape(hour_utc: int) -> tuple[dict, dict]:
    """
    Main entry point.
    Returns (theme, viral_tweet).
    """
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")

    handles = get_accounts_for_theme(theme["id"])
    logger.info(f"Loaded {len(handles)} accounts for this theme.")

    tweets = scrape_tweets_for_accounts(handles)
    viral_tweet = get_most_viral_tweet(tweets)

    return theme, viral_tweet
