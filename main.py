from article_scraper import run_scraper
from generate_jwt import generate_jwt
from append_articles_in_google_sheets import run_append_articles

def main(date_filter):
    try:
        print("Running article scraper ...")
        run_scraper(date_filter)
    except Exception as e:
        print(f"Error running article scraper: {e}")
        exit(1)
    
    try:
        print("\nRunning JWT generator ...")
        generate_jwt()
    except Exception as e:
        print(f"Error generating JWT: {e}")
        exit(1)
    
    # Once 'generate_jwt.py' completes, run 'append_articles_in_google_sheets.py'.
    try:
        print("\nAppending articles to Google Sheets ...")
        run_append_articles()
    except Exception as e:
        print(f"Error appending articles to Google Sheets: {e}")
        exit(1)
    
    print("All scripts executed successfully.")

if __name__ == "__main__":
    # Only fetch articles on or after this date
    date_filter = "2025-04-10" # April 10, 2025
    
    main(date_filter)
