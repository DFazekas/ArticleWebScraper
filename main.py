"""
Main module for the Article Scraper Utility.

This script runs the article scraper, JWT generator, and appends articles to Google Sheets.
"""
import sys
from article_scraper import run_scraper
from generate_jwt import generate_jwt
from append_articles_in_google_sheets import run_append_articles


def main(date_filter):
    """
    Executes the main workflow of the application.

    Args:
        filter_date (str): Date in YYYY-MM-DD format; only articles on or after
        this date are processed.
    """
    try:
        print("Running article scraper ...")
        run_scraper(date_filter)
    except RuntimeError as e:
        print(f"Error running article scraper: {e}")
        sys.exit(1)

    try:
        print("\nRunning JWT generator ...")
        generate_jwt()
    except (RuntimeError, IOError) as e:
        print(f"Error generating JWT: {e}")
        sys.exit(1)

    try:
        print("\nAppending articles to Google Sheets ...")
        run_append_articles()
    except RuntimeError as e:
        print(f"Error appending articles to Google Sheets: {e}")
        sys.exit(1)

    print("All scripts executed successfully.")


if __name__ == "__main__":
    # Only fetch articles on or after this date
    DATE_FILTER = "2025-04-10" # April 10, 2025

    main(DATE_FILTER)
