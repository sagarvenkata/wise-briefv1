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


def _post_with_retry(client: tweepy.Client, text: str, reply_to: str = None, quote_tweet_id: str = None) -> str:
    """Post a single tweet, retry once on failure. Returns tweet ID."""
    for attempt in range(1, 3):
        try:
            kwargs = {"text": text}
            if reply_to:
                kwargs["in_reply_to_tweet_id"] = reply_to
            if quote_tweet_id:
                kwargs["quote_tweet_id"] = quote_tweet_id
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
    Quote tweet the original viral tweet with the hook,
    then reply with expansion + sources.
    """
    client = _twitter()
    quote_id = viral_tweet.get("tweet_id") or viral_tweet["url"].split("/")[-1]

    # Tweet 1: hook as a quote tweet of the original
    logger.info(f"Posting hook as quote tweet of {quote_id} ...")
    hook_id = _post_with_retry(client, content["hook"], quote_tweet_id=quote_id)
    logger.info(f"Hook posted: {hook_id}")

    # Tweet 2: expansion as reply to hook
    logger.info("Posting expansion ...")
    expansion_id = _post_with_retry(client, content["expansion"], reply_to=hook_id)
    logger.info(f"Expansion posted: {expansion_id}")

    # Tweet 3: sources as reply to expansion
    logger.info("Posting sources reply ...")
    _post_with_retry(client, content["reply"], reply_to=expansion_id)
    logger.info("Sources posted.")

    _log(theme["id"], viral_tweet, hook_id, "success")
