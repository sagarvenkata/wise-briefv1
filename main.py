import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import summariser
import scraper
import mailer
import buffer_poster

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

# Sample viral tweet used in test mode — bypasses scraper entirely
TEST_TWEET = {
    "text": "how do they even install these in the middle of the freaking ocean..",
    "author": "AMAZlNGNATURE",
    "url": "https://x.com/AMAZlNGNATURE/status/1967823367903277258",
    "tweet_id": "1967823367903277258",
    "likes": 4700,
    "views": 58000000,
    "retweets": 24000,
    "replies": 0,
    "engagement_score": 999999,
}


def run_digest():
    """Scrape + summarise all 12 themes and email a daily digest."""
    logger.info("=== Wise Brief DIGEST mode starting ===")
    themes = scraper.get_all_active_themes()
    logger.info(f"Found {len(themes)} active themes.")

    client = scraper.ApifyClient(os.environ["APIFY_API_TOKEN"])
    results = []

    for theme in themes:
        logger.info(f"--- {theme['emoji']} {theme['name']} ---")
        search_term = theme.get("search_term") or theme["name"]

        try:
            tweet = scraper.get_top_tweet_for_theme(client, theme["name"], search_term)
            if tweet is None:
                logger.warning(f"No tweet found for {theme['name']} — skipping.")
                continue

            content = summariser.summarise(theme, tweet)
            results.append({"theme": theme, "tweet": tweet, "content": content})
            logger.info(f"Done: {theme['name']}")
        except Exception as e:
            logger.error(f"Failed for {theme['name']}: {e} — skipping.")
            continue

    if not results:
        logger.error("No results to email — aborting.")
        sys.exit(1)

    logger.info(f"Pushing {len(results)} posts to Buffer queue ...")
    buffer_poster.queue_all(results)

    logger.info(f"Sending digest email with {len(results)}/{len(themes)} themes ...")
    mailer.send_digest(results)
    logger.info("=== Digest complete ===")


def run_single():
    """Post one tweet for the current UTC hour's theme (original live-post mode)."""
    import poster
    test_mode = "--test" in sys.argv
    hour_utc = datetime.now(timezone.utc).hour

    if test_mode:
        logger.info("=== Wise Brief pipeline starting [TEST MODE] ===")
        theme = scraper.get_theme_for_slot(hour_utc)
        viral_tweet = TEST_TWEET
    else:
        logger.info(f"=== Wise Brief pipeline starting | UTC hour: {hour_utc} ===")
        logger.info("--- Stage 1: Scraping ---")
        theme, viral_tweet = scraper.scrape(hour_utc)

    logger.info(f"Theme: {theme['emoji']} {theme['name']}")
    logger.info(f"Viral tweet: @{viral_tweet['author']} | {viral_tweet['likes']} likes | {viral_tweet['views']} views")

    logger.info("--- Stage 2: Summarising ---")
    content = summariser.summarise(theme, viral_tweet)

    logger.info("--- Stage 3: Posting ---")
    poster.post(theme, viral_tweet, content)

    logger.info("=== Wise Brief pipeline complete ===")


def main():
    if "--digest" in sys.argv:
        run_digest()
    else:
        run_single()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
