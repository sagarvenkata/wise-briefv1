import os
import time
import logging
from datetime import datetime, timezone
import tweepy
from supabase import create_client

logger = logging.getLogger(__name__)

RETRY_WAIT = 60


def _twitter():
    return tweepy.Client(
        consumer_key=os.environ["TWITTER_API_KEY"],
        consumer_secret=os.environ["TWITTER_API_SECRET"],
        access_token=os.environ["TWITTER_ACCESS_TOKEN"],
        access_token_secret=os.environ["TWITTER_ACCESS_SECRET"],
    )


def _db():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])


def _post_with_retry(client: tweepy.Client, text: str, reply_to: str = None) -> str:
    """Post a single tweet, retry once on failure. Returns tweet ID."""
    for attempt in range(1, 3):
        try:
            kwargs = {"text": text}
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to
            response = client.create_tweet(**kwargs)
            return response.data["id"]
        except tweepy.TweepyException as e:
            logger.error(f"Twitter error (attempt {attempt}): {e}")
            if attempt == 1:
                logger.info(f"Retrying in {RETRY_WAIT}s ...")
                time.sleep(RETRY_WAIT)
            else:
                raise


def _log(theme_id: int, viral_tweet: dict, tweet_id: str, status: str, error: str = None):
    try:
        _db().table("posts").insert({
            "theme_id": theme_id,
            "source_tweet_url": viral_tweet.get("url", ""),
            "source_tweet_text": viral_tweet.get("text", "")[:500],
            "source_likes": viral_tweet.get("likes", 0),
            "source_views": viral_tweet.get("views", 0),
            "tweet_id": tweet_id,
            "run_date": datetime.now(timezone.utc).date().isoformat(),
            "status": status,
            "error_message": error,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.info("Logged to Supabase.")
    except Exception as e:
        logger.error(f"Supabase log failed (non-fatal): {e}")


def post(theme: dict, viral_tweet: dict, content: dict):
    """
    Post hook tweet, then reply with expansion + sources.
    content = {hook, expansion, reply}
    """
    client = _twitter()

    # Tweet 1: hook
    logger.info("Posting hook tweet ...")
    hook_id = _post_with_retry(client, content["hook"])
    logger.info(f"Hook posted: {hook_id}")

    # Tweet 2: expansion as reply to hook
    logger.info("Posting expansion ...")
    expansion_id = _post_with_retry(client, content["expansion"], reply_to=hook_id)
    logger.info(f"Expansion posted: {expansion_id}")

    # Tweet 3: reply with sources
    logger.info("Posting sources reply ...")
    _post_with_retry(client, content["reply"], reply_to=expansion_id)
    logger.info("Sources posted.")

    _log(theme["id"], viral_tweet, hook_id, "success")
