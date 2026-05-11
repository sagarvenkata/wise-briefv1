import os
import logging
import requests

logger = logging.getLogger(__name__)

BUFFER_API = "https://api.bufferapp.com/1/updates/create.json"


def _queue_post(text: str, access_token: str, profile_id: str) -> str:
    """Add a single post to the end of the Buffer queue. Returns the update ID."""
    response = requests.post(
        BUFFER_API,
        data={
            "access_token": access_token,
            "profile_ids[]": profile_id,
            "text": text,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("success"):
        raise RuntimeError(f"Buffer rejected post: {data}")
    update_id = data["updates"][0]["id"]
    return update_id


def queue_all(results: list[dict]):
    """
    Push all generated posts into the Buffer queue in theme order.
    Buffer drains them at the preset schedule slots automatically.

    results: list of dicts with keys: theme, tweet, content
    """
    access_token = os.environ["BUFFER_ACCESS_TOKEN"]
    profile_id = os.environ["BUFFER_PROFILE_ID"]

    queued = 0
    for r in results:
        theme = r["theme"]
        tweet = r["tweet"]
        content = r["content"]

        # Embed original tweet URL so X auto-previews images/video
        post_text = content["content"] + f"\n\n{tweet.get('url', '')}"

        try:
            update_id = _queue_post(post_text, access_token, profile_id)
            queued += 1
            logger.info(f"Queued [{theme['name']}] → Buffer ID {update_id}")
        except Exception as e:
            logger.error(f"Failed to queue [{theme['name']}]: {e}")

    logger.info(f"Buffer: {queued}/{len(results)} posts queued successfully.")
    if queued == 0:
        raise RuntimeError("No posts were queued — check BUFFER_ACCESS_TOKEN and BUFFER_PROFILE_ID.")
