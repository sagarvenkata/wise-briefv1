import os
import logging
from datetime import datetime, timezone, timedelta

from apify_client import ApifyClient
from supabase import create_client

logger = logging.getLogger(__name__)

MIN_LIKES = 10_000
MIN_IMPRESSIONS = 1_000_000
MIN_REPLIES = 5


def get_db():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def get_all_active_themes() -> list[dict]:
    db = get_db()
    result = db.table("themes").select("*").eq("active", True).order("post_hour_utc").execute()
    return result.data


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


def _is_within_24h(created_at: str) -> bool:
    if not created_at:
        return False
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        return datetime.now(timezone.utc) - dt <= timedelta(hours=24)
    except Exception:
        return False


def _score_tweet(t: dict) -> float:
    return (
        t.get("likeCount", 0) * 3
        + t.get("viewCount", 0) * 0.001
        + t.get("replyCount", 0) * 2
        + t.get("retweetCount", 0) * 1.5
    )


def get_top_tweet_for_theme(client: ApifyClient, theme_name: str, search_term: str) -> dict | None:
    run_input = {
        "customMapFunction": "(object) => { return {...object} }",
        "includeSearchTerms": True,
        "maxItems": 50,
        "onlyVideo": False,
        "searchTerms": [search_term],
        "sort": "Top",
        "tweetLanguage": "en",
    }

    try:
        run = client.actor("apidojo/tweet-scraper").call(run_input=run_input)
        all_tweets = [
            item
            for item in client.dataset(run["defaultDatasetId"]).iterate_items()
            if item.get("text") and item.get("url")
        ]

        if not all_tweets:
            logger.warning(f"No tweets at all for theme: {theme_name}")
            return None

        # Pass 1 — strict: within 24h and all engagement thresholds met
        strict = [
            t for t in all_tweets
            if t.get("likeCount", 0) >= MIN_LIKES
            and t.get("viewCount", 0) >= MIN_IMPRESSIONS
            and t.get("replyCount", 0) >= MIN_REPLIES
            and _is_within_24h(t.get("createdAt", ""))
        ]

        if strict:
            best = max(strict, key=_score_tweet)
            logger.info(f"[{theme_name}] STRICT — @{best.get('author', {}).get('userName', '')} — {best.get('likeCount', 0):,} likes")
        else:
            # Pass 2 — nothing cleared the bar; run a fresh search for trending content
            logger.info(f"[{theme_name}] No tweet cleared thresholds — searching trending fallback")
            trending_term = f"trending {search_term}"
            trending_run = client.actor("apidojo/tweet-scraper").call(run_input={
                **run_input,
                "searchTerms": [trending_term],
                "maxItems": 20,
            })
            trending_tweets = [
                item
                for item in client.dataset(trending_run["defaultDatasetId"]).iterate_items()
                if item.get("text") and item.get("url")
            ]
            pool = trending_tweets or all_tweets
            best = max(pool, key=lambda t: t.get("likeCount", 0))
            logger.info(f"[{theme_name}] TRENDING FALLBACK — @{best.get('author', {}).get('userName', '')} — {best.get('likeCount', 0):,} likes")

        url = best.get("url", "")
        return {
            "text": best.get("text", ""),
            "url": url,
            "author": best.get("author", {}).get("userName", ""),
            "tweet_id": url.split("/")[-1],
            "likes": best.get("likeCount", 0),
            "views": best.get("viewCount", 0),
            "retweets": best.get("retweetCount", 0),
            "replies": best.get("replyCount", 0),
            "engagement_score": _score_tweet(best),
            "createdAt": best.get("createdAt", ""),
        }

    except Exception as e:
        logger.error(f"Apify error for theme [{theme_name}]: {e}")
        return None


def scrape(hour_utc: int) -> tuple[dict, dict]:
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")

    # Use dedicated search_term if set, otherwise fall back to theme name
    search_term = theme.get("search_term") or theme["name"]

    client = ApifyClient(os.environ["APIFY_API_TOKEN"])
    viral_tweet = get_top_tweet_for_theme(client, theme["name"], search_term)

    if viral_tweet is None:
        raise ValueError(f"No usable tweet found for theme: {theme['name']}")

    logger.info(
        f"Selected tweet: @{viral_tweet['author']} | "
        f"{viral_tweet['likes']:,} likes | {viral_tweet['views']:,} views"
    )
    return theme, viral_tweet
