import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import scraper
import summariser
import poster

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("main")


def main():
    hour_utc = datetime.now(timezone.utc).hour
    logger.info(f"=== Wise Brief pipeline starting | UTC hour: {hour_utc} ===")

    # Stage 1: Identify theme + scrape most viral tweet
    logger.info("--- Stage 1: Scraping ---")
    theme, viral_tweet = scraper.scrape(hour_utc)
    logger.info(f"Theme: {theme['emoji']} {theme['name']}")
    logger.info(f"Viral tweet: @{viral_tweet['author']} | {viral_tweet['likes']} likes | {viral_tweet['views']} views")

    # Stage 2: Generate content with Claude
    logger.info("--- Stage 2: Summarising ---")
    content = summariser.summarise(theme, viral_tweet)

    # Stage 3: Post to X
    logger.info("--- Stage 3: Posting ---")
    poster.post(theme, viral_tweet, content)

    logger.info("=== Wise Brief pipeline complete ===")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)
