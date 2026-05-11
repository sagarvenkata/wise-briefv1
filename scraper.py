import os
import asyncio
import logging
from datetime import datetime, timezone, timedelta

from twscrape import API, gather
from supabase import create_client

logger = logging.getLogger(__name__)

MIN_LIKES = 10_000
MIN_IMPRESSIONS = 1_000_000
MIN_REPLIES = 5

TWSCRAPE_DB = ".twscrape/accounts.db"


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


def _is_within_24h(dt: datetime) -> bool:
    if dt is None:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - dt <= timedelta(hours=24)


def _score(tweet) -> float:
    return (
        (tweet.likeCount or 0) * 3
        + (tweet.viewCount or 0) * 0.001
        + (tweet.replyCount or 0) * 2
        + (tweet.retweetCount or 0) * 1.5
    )


def _to_dict(tweet) -> dict:
    return {
        "text": tweet.rawContent or "",
        "url": str(tweet.url),
        "author": tweet.user.username if tweet.user else "",
        "tweet_id": str(tweet.id),
        "likes": tweet.likeCount or 0,
        "views": tweet.viewCount or 0,
        "retweets": tweet.retweetCount or 0,
        "replies": tweet.replyCount or 0,
        "engagement_score": _score(tweet),
        "createdAt": tweet.date.isoformat() if tweet.date else "",
    }


async def _setup_api() -> API:
    os.makedirs(os.path.dirname(TWSCRAPE_DB), exist_ok=True)
    api = API(TWSCRAPE_DB)
    cookies = f"auth_token={os.environ['TWSCRAPE_AUTH_TOKEN']}; ct0={os.environ['TWSCRAPE_CT0']}"
    await api.pool.add_account(
        username=os.environ["TWSCRAPE_USERNAME"],
        password=os.environ["TWSCRAPE_PASSWORD"],
        email=os.environ["TWSCRAPE_EMAIL"],
        email_password=os.environ["TWSCRAPE_EMAIL_PASSWORD"],
        cookies=cookies,
    )
    await api.pool.login_all()
    return api


async def _get_top_tweet(api: API, theme_name: str, search_term: str) -> dict | None:
    tweets = await gather(api.search(search_term, limit=20, kv={"product": "Top"}))

    if not tweets:
        logger.warning(f"No tweets found for theme: {theme_name}")
        return None

    strict = [
        t for t in tweets
        if (t.likeCount or 0) >= MIN_LIKES
        and (t.viewCount or 0) >= MIN_IMPRESSIONS
        and (t.replyCount or 0) >= MIN_REPLIES
        and _is_within_24h(t.date)
    ]

    if strict:
        best = max(strict, key=_score)
        logger.info(f"[{theme_name}] STRICT — @{best.user.username} — {best.likeCount:,} likes")
    else:
        best = max(tweets, key=lambda t: t.likeCount or 0)
        logger.info(f"[{theme_name}] FALLBACK — @{best.user.username} — {best.likeCount:,} likes")

    return _to_dict(best)


async def _scrape_all_async(themes: list[dict]) -> list[tuple[dict, dict]]:
    api = await _setup_api()
    results = []
    for theme in themes:
        search_term = theme.get("search_term") or theme["name"]
        try:
            tweet = await _get_top_tweet(api, theme["name"], search_term)
            if tweet:
                results.append((theme, tweet))
            else:
                logger.warning(f"Skipping {theme['name']} — no usable tweet.")
        except Exception as e:
            logger.error(f"Failed for {theme['name']}: {e}")
    return results


def scrape_all(themes: list[dict]) -> list[tuple[dict, dict]]:
    """Scrape top tweet for each theme. Returns list of (theme, tweet) pairs."""
    return asyncio.run(_scrape_all_async(themes))


def scrape(hour_utc: int) -> tuple[dict, dict]:
    """Single-theme scrape for the given UTC hour (used by run_single mode)."""
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")
    results = scrape_all([theme])
    if not results:
        raise ValueError(f"No usable tweet found for theme: {theme['name']}")
    return results[0]
