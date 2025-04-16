import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import abc


class Article:
    def __init__(self, title, link, date):
        """
        Initializes an Article instance.
        Args:
            title (str): The title of the article.
            link (str): The URL link to the article.
            date (datetime): The publication date of the article.
        """
        self.title = title
        self.link = link
        self.date = date  # Expected to be a naive datetime

    def to_dict(self):
        """Returns a dictionary representation of the article with a formatted date."""
        return {
            "title": self.title,
            "link": self.link,
            "date": self.date.strftime("%Y-%m-%d")
        }

    def __repr__(self):
        return f"Article(title='{self.title}', link='{self.link}', date='{self.date.strftime('%Y-%m-%d')}')"


class BaseScraper(abc.ABC):
    def __init__(self, url):
        self.url = url

    def fetch_html(self):
        """Fetch HTML content from self.url using a custom User-Agent."""
        headers = {
            "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                           "Chrome/85.0.4183.102 Safari/537.36")
        }
        try:
            response = requests.get(self.url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {self.url}: {e}")
            return None

    @abc.abstractmethod
    def scrape(self, threshold_date):
        """
        Fetch and parse articles from the website,
        then filter them by threshold_date.
        Must be implemented by each subclass.
        """
        pass


class BetaKitScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)

    def parse_article(self, article_elem):
        """Parses a single BetaKit <article> element and returns an Article instance."""
        date_elem = article_elem.find("span", class_="entry-date")
        if not date_elem:
            return None
        date_text = date_elem.get_text(strip=True)  # e.g., "April 14, 2025"
        try:
            art_date = datetime.strptime(date_text, '%B %d, %Y')
        except ValueError:
            return None

        title_elem = article_elem.find("h2", class_="entry-title")
        if title_elem:
            a_tag = title_elem.find("a")
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag.get("href", "")
            else:
                title, link = "No Title", ""
        else:
            title, link = "No Title", ""
        return Article(title, link, art_date)

    def scrape(self, threshold_date):
        """Fetch and parse BetaKit articles, returning those on/after threshold_date."""
        html = self.fetch_html()
        if html is None:
            return []
        soup = BeautifulSoup(html, "html.parser")
        section = soup.find("section", class_="section__latest-posts")
        if not section:
            print("BetaKit: 'Latest' section not found.")
            return []
        articles = []
        for article_elem in section.find_all("article"):
            article = self.parse_article(article_elem)
            if article is not None and article.date >= threshold_date:
                articles.append(article)
        return articles


class FinSMEsScraper(BaseScraper):
    def __init__(self, url):
        super().__init__(url)

    def parse_article(self, article_elem):
        """Parses a single FinSMEs article container and returns an Article instance."""
        time_elem = article_elem.find("time", class_="entry-date")
        if not time_elem:
            return None
        datetime_attr = time_elem.get("datetime", "").strip()
        if not datetime_attr:
            return None
        try:
            art_date = datetime.fromisoformat(datetime_attr)
            art_date = art_date.replace(tzinfo=None)
        except Exception:
            date_text = time_elem.get_text(strip=True)
            try:
                art_date = datetime.strptime(date_text, "%B %d, %Y")
            except Exception:
                return None

        title_elem = article_elem.find("h3", class_="entry-title")
        if title_elem:
            a_tag = title_elem.find("a")
            if a_tag:
                title = a_tag.get_text(strip=True)
                link = a_tag.get("href", "")
            else:
                title, link = "No Title", ""
        else:
            title, link = "No Title", ""
        return Article(title, link, art_date)

    def scrape(self, threshold_date):
        """Fetch and parse FinSMEs articles, filtering by threshold_date."""
        html = self.fetch_html()
        if html is None:
            return []
        soup = BeautifulSoup(html, "html.parser")
        containers = soup.find_all("div", class_="td-cpt-post")
        articles = []
        for container in containers:
            module_container = container.find("div", class_="td-module-container")
            if module_container is None:
                continue
            article = self.parse_article(module_container)
            if article is not None and article.date >= threshold_date:
                articles.append(article)
        return articles


def save_articles(articles, output_filename):
    """
    Writes a list of Article objects (using their dictionary representation)
    to a file.
    """
    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            for art in articles:
                art_dict = art.to_dict()
                f.write(f"Title: {art_dict['title']}\n")
                f.write(f"Date:  {art_dict['date']}\n")
                f.write(f"Link:  {art_dict['link']}\n")
                f.write("-" * 40 + "\n")
        print(f"Saved {len(articles)} articles to '{output_filename}'.")
    except IOError as e:
        print("Error writing to file:", e)

def run_scraper(threshold_date_str, output_filename="articles.txt"):
    """
    Runs all scrapers using the given threshold date (YYYY-MM-DD) and saves the articles.
    
    Args:
        threshold_date_str (str): The threshold date in 'YYYY-MM-DD' format.
        output_filename (str): The file to write the scraped articles.
    
    Returns:
        list: A list of Article objects that were saved.
    """
    try:
        threshold_date = datetime.strptime(threshold_date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    scrapers = [
        BetaKitScraper("https://betakit.com/"),
        FinSMEsScraper("https://www.finsmes.com/category/canada")
    ]

    all_articles = []
    for scraper in scrapers:
        articles = scraper.scrape(threshold_date)
        all_articles.extend(articles)

    save_articles(all_articles, output_filename)
    return all_articles


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python 'article_scraper.py' <threshold_date (YYYY-MM-DD)>")
        sys.exit(1)

    threshold_str = sys.argv[1]
    run_scraper(threshold_str)
