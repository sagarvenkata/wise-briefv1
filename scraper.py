import os
import time
import logging
import requests
from datetime import datetime, timezone, timedelta

from supabase import create_client

logger = logging.getLogger(__name__)

MIN_LIKES = 10_000
MIN_IMPRESSIONS = 1_000_000
MIN_REPLIES = 5

SEARCH_URL = "https://api.twitterapi.io/twitter/tweet/advanced_search"


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


def _score(t: dict) -> float:
    m = t.get("public_metrics", {})
    return (
        m.get("like_count", 0) * 3
        + m.get("impression_count", 0) * 0.001
        + m.get("reply_count", 0) * 2
        + m.get("retweet_count", 0) * 1.5
    )


def _to_dict(t: dict) -> dict:
    m = t.get("public_metrics", {})
    author = t.get("author", {})
    url = f"https://x.com/{author.get('userName', '')}/status/{t.get('id', '')}"
    return {
        "text": t.get("text", ""),
        "url": url,
        "author": author.get("userName", ""),
        "tweet_id": t.get("id", ""),
        "likes": m.get("like_count", 0),
        "views": m.get("impression_count", 0),
        "retweets": m.get("retweet_count", 0),
        "replies": m.get("reply_count", 0),
        "engagement_score": _score(t),
        "createdAt": t.get("createdAt", ""),
    }


def _search(query: str) -> list[dict]:
    headers = {"X-API-Key": os.environ["TWITTERAPI_IO_KEY"]}
    params = {"query": query, "queryType": "Top"}
    for attempt in range(3):
        response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
        if response.status_code == 429:
            wait = 10 * (attempt + 1)
            logger.warning(f"Rate limited by twitterapi.io — waiting {wait}s before retry")
            time.sleep(wait)
            continue
        response.raise_for_status()
        return response.json().get("tweets", [])
    response.raise_for_status()
    return []


def get_top_tweet_for_theme(theme_name: str, search_term: str) -> dict | None:
    try:
        tweets = _search(search_term)

        if not tweets:
            logger.warning(f"No tweets found for theme: {theme_name}")
            return None

        strict = [
            t for t in tweets
            if t.get("public_metrics", {}).get("like_count", 0) >= MIN_LIKES
            and t.get("public_metrics", {}).get("impression_count", 0) >= MIN_IMPRESSIONS
            and t.get("public_metrics", {}).get("reply_count", 0) >= MIN_REPLIES
            and _is_within_24h(t.get("createdAt", ""))
        ]

        if strict:
            best = max(strict, key=_score)
            logger.info(f"[{theme_name}] STRICT — @{best.get('author', {}).get('userName', '')} — {best.get('public_metrics', {}).get('like_count', 0):,} likes")
        else:
            # Fallback — must have at least some engagement
            candidates = [t for t in tweets if t.get("public_metrics", {}).get("like_count", 0) >= 100]
            if not candidates:
                logger.warning(f"[{theme_name}] No tweet with 100+ likes — skipping.")
                return None
            best = max(candidates, key=lambda t: t.get("public_metrics", {}).get("like_count", 0))
            logger.info(f"[{theme_name}] FALLBACK — @{best.get('author', {}).get('userName', '')} — {best.get('public_metrics', {}).get('like_count', 0):,} likes")

        return _to_dict(best)

    except Exception as e:
        logger.error(f"Error fetching tweets for [{theme_name}]: {e}")
        return None


def scrape_all(themes: list[dict]) -> list[tuple[dict, dict]]:
    results = []
    for i, theme in enumerate(themes):
        if i > 0:
            time.sleep(5)
        search_term = theme.get("search_term") or theme["name"]
        tweet = get_top_tweet_for_theme(theme["name"], search_term)
        if tweet:
            results.append((theme, tweet))
        else:
            logger.warning(f"Skipping {theme['name']} — no usable tweet.")
    return results


def scrape(hour_utc: int) -> tuple[dict, dict]:
    theme = get_theme_for_slot(hour_utc)
    logger.info(f"Theme for slot {hour_utc}: {theme['emoji']} {theme['name']}")
    results = scrape_all([theme])
    if not results:
        raise ValueError(f"No usable tweet found for theme: {theme['name']}")
    return results[0]
