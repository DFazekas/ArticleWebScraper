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
    self.date = date # Expected to be a naive datetime
    
  def to_dict(self):
    """
    Returns a dictionary representation of the article with formatted date.
    """
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
  def parse_articles(self, soup):
    """
    Given a BeautifulSoup object, return a list of Article instances.
    Must be implemented by subclasses."""
    pass
  
  def scrape(self, threshold_date):
    """
    Fetches HTML, parses articles, and returns a filtered list of Article instances.
    """
    html = self.fetch_html()
    if html is None:
      return []
    soup = BeautifulSoup(html, "html.parser")
    articles = self.parse_articles(soup)
    return filter_articles(articles, threshold_date)


# ------------------ SITE-SPECIFIC SCRAPERS ------------------

class BetaKitScraper(BaseScraper):
  def parse_articles(self, soup):
    """Parses BetaKit articles from the 'section__latest-posts' element."""
    section = soup.find("section", class_="section__latest-posts")
    if not section:
        print("BetaKit: 'Latest' section not found.")
        return []
    article_elems = section.find_all("article")
    articles = []
    for elem in article_elems:
        article = parse_betakit_article(elem)
        if article is not None:
            articles.append(article)
    return articles
  
class FinSMEsScraper(BaseScraper):
  def parse_articles(self, soup):
      """
      Parses FinSMEs articles by finding all elements with class 'td-cpt-post'.
      For each container, it uses the nested 'td-module-container' element.
      """
      containers = soup.find_all("div", class_="td-cpt-post")
      articles = []
      for container in containers:
          module_container = container.find("div", class_="td-module-container")
          if module_container is None:
              continue
          article = parse_finsmes_article(module_container)
          if article is not None:
              articles.append(article)
      return articles


# ------------------ SITE-SPECIFIC PARSING FUNCTIONS ------------------

def parse_betakit_article(article_elem):
    """
    Parses a BetaKit <article> element and returns an Article instance.
    Returns None if required fields cannot be extracted.
    """
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

def parse_finsmes_article(article_elem):
    """
    Parses a FinSMEs article container (the element with class 'td-module-container')
    and returns an Article instance.
    Returns None if required fields cannot be extracted.
    """
    if article_elem is None:
        return None

    # Extract publication date from the <time class="entry-date"> element
    time_elem = article_elem.find("time", class_="entry-date")
    if not time_elem:
        return None
    datetime_attr = time_elem.get("datetime", "").strip()
    if not datetime_attr:
        return None
    try:
        art_date = datetime.fromisoformat(datetime_attr)
        art_date = art_date.replace(tzinfo=None)  # convert to naive datetime
    except Exception:
        date_text = time_elem.get_text(strip=True)
        try:
            art_date = datetime.strptime(date_text, "%B %d, %Y")
        except Exception:
            return None

    # Extract title and link from the <h3 class="entry-title"> element
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


# ------------------ HELPER FUNCTIONS ------------------

def filter_articles(articles, threshold_date):
    """
    Filters a list of Article objects and returns a list with articles whose
    publication date is on or after threshold_date.
    """
    return [article for article in articles if article.date >= threshold_date]

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


# ------------------ MAIN FUNCTION ------------------

if __name__ == "__main__":
    given_date = "2025-04-10"  # Only fetch articles on or after this date
    threshold_date = datetime.strptime(given_date, "%Y-%m-%d")
    
    # List all scrapers; to add a new website, create a new subclass of BaseScraper and add it here.
    scrapers = [
        BetaKitScraper("https://betakit.com/"),
        FinSMEsScraper("https://www.finsmes.com/category/canada")
    ]
    
    all_articles = []
    for scraper in scrapers:
        all_articles.extend(scraper.scrape(threshold_date))
    
    save_articles(all_articles, "articles.txt")
