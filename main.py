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
    "text": "The entire Roman Empire ran on a currency backed by nothing but trust in the state. Sound familiar? The moment that trust broke in 270 AD, inflation hit 1000% in a decade. Every empire since has made the same mistake.",
    "author": "historyinmemes",
    "url": "https://twitter.com/historyinmemes/status/1234567890",
    "likes": 48200,
    "views": 2100000,
    "retweets": 9400,
    "replies": 1200,
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
