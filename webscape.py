import requests
from bs4 import BeautifulSoup
from datetime import datetime


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

# ------------------ HELPER FUNCTIONS ------------------

def fetch_html(url):
    """
    Fetch HTML content from the given URL using a custom User-Agent.
    Returns the HTML text or None if a request error occurs.
    """
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/85.0.4183.102 Safari/537.36")
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def filter_articles(articles, threshold_date):
    """
    Filters a list of Article objects.
    Returns a new list with articles whose publication date is on or after threshold_date.
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

# ------------------ SITE-SPECIFIC PARSING FUNCTIONS ------------------

def parse_betakit_article(article_elem):
    """
    Parses a BetaKit article and returns an Article instance.
    Returns None if required fields cannot be extracted.
    """
    
    # Parse publication date from the article.
    date_elem = article_elem.find("span", class_="entry-date")
    if not date_elem:
        return None
    date_text = date_elem.get_text(strip=True)  # e.g., "April 14, 2025"
    try:
        art_date = datetime.strptime(date_text, '%B %d, %Y') # e.g., "2025-04-10 00:00:00"
    except ValueError:
        return None

    # Parse the title and hyperlink from the article.
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
    Parses a FinSMEs article and returns an Article instance.
    Returns None if required fields cannot be extracted. 
    """
    if article_elem is None:
        return None

    # Parse publication date from the article.
    time_elem = article_elem.find("time", class_="entry-date")
    if not time_elem:
      return None
    
    datetime_attr = time_elem.get("datetime", "").strip()
    if not datetime_attr:
        return None
    
    try:
        # Parse the ISO formatted date-time string.
        art_date = datetime.fromisoformat(datetime_attr) # e.g., "2025-04-02 09:31:46+01:00"
        
        # Convert to naive datetime by stripping timezone info.
        art_date = art_date.replace(tzinfo=None) # e.g., "2025-04-02 09:31:46"
    except Exception:
        return None
    
    # Parse the title and hyperlink from the article.
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


# ------------------ SITE-SPECIFIC SCRAPER FUNCTIONS ------------------

def scrape_betakit(url, threshold_date):
    """
    Scrapes Betakit articles from the specified URL.
    Returns a list of Article instances meeting the threshold_date.
    """
    html = fetch_html(url)
    if html is None:
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find all articles.
    article_containers = soup.find("section", class_="section__latest-posts")
    if not article_containers:
        print("Betakit: 'Latest' section not found.")
        return []
    
    articles = article_containers.find_all("article")
    
    # Parse each article.
    parsed_articles = [
      parse_betakit_article(article) 
      for article in articles
    ]
    
    # Remove any articles that failed to parse (i.e. are None).
    parsed_articles = [
      article 
      for article in parsed_articles 
      if article is not None
    ]
    
    # Filter the parsed articles based on the threshold_date.
    return filter_articles(parsed_articles, threshold_date)

def scrape_finsmes(url, threshold_date):
    """
    Scrapes FinSMEs articles from the specified URL.
    Returns a list of Article instances meeting the threshold_date.
    """
    html = fetch_html(url)
    if html is None:
        return []
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Find all articles.
    articles = soup.find_all("div", class_="td-cpt-post")
    
    # Parse each article.
    parsed_articles = [
        parse_finsmes_article(article.find("div", class_="td-module-container"))
        for article in articles
        if article.find("div", class_="td-module-container") is not None
    ]
    
    # Remove any articles that failed to parse (i.e. are None).
    parsed_articles = [art for art in parsed_articles if art is not None]
    
    # Filter the parsed articles based on the threshold_date.
    return filter_articles(parsed_articles, threshold_date)

# ------------------ MAIN FUNCTION ------------------

if __name__ == "__main__":
    given_date = "2025-04-10"  # Only fetch articles on or after this date
    threshold_date = datetime.strptime(given_date, "%Y-%m-%d")
    
    # Scrape articles from each website and store all results in one variable
    all_articles = []
    all_articles.extend(scrape_betakit("https://betakit.com/", threshold_date))
    all_articles.extend(scrape_finsmes("https://www.finsmes.com/category/canada", threshold_date))
    
    # Save all the extracted articles to a local file
    save_articles(all_articles, "articles.txt")
