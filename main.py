import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import summariser
import poster
import scraper

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")

# Sample viral tweet used in test mode — bypasses scraper entirely
TEST_TWEET = {
    "text": "The biggest skill no one teaches you: how to think clearly under pressure. Most people freeze. The ones who don't have practiced one thing — separating what they can control from what they can't.",
    "author": "naval",
    "url": "https://twitter.com/naval/status/1167928560906993664",
    "tweet_id": "1167928560906993664",
    "likes": 42000,
    "views": 3200000,
    "retweets": 8900,
    "replies": 1100,
    "engagement_score": 999999,
}


def main():
    test_mode = "--test" in sys.argv
    hour_utc = datetime.now(timezone.utc).hour

    if test_mode:
        logger.info("=== Wise Brief pipeline starting [TEST MODE] ===")
        logger.info("Skipping scraper — using hardcoded sample tweet.")
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


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
