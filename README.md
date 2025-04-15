# Article Scraper Utility

This repository contains a simple web scraping utility that collects articles from multiple websites. It uses Python modules such as
`requests` and `beautifulsoup4` (bs4) to fetch and parse web pages.

## Table of Contents

- [Article Scraper Utility](#article-scraper-utility)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Extending the Functionality](#extending-the-functionality)
  - [Contributing](#contributing)
  - [License](#license)

## Installation

1. Clone the Repository

    Open your terminal and run:

    ```bash
    git clone <repository_url>
    cd article_scraper
    ```
  
2. Install Dependencies

    The project relies on external modules which are listed in the `requirements.txt` file. Install them by running:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the web scraper by executing the main file:

```bash
python article_scraper.py
```

The script will scrape the configured websites, filter articles based on a threshold date, and save the output to a file (e.g., `articles.txt`).

## Extending the Functionality

The code is designed to be easily extendable. Each website-specific scraper is encapsulated into its own class inheriting from the
`BaseScraper` abstract class. To add new website scraping functionality:

1. Create a New Scraper Class

    - Define a new class (for example, `ExampleSiteScraper`) that inherits from `BaseScraper`.

    - Implement the `scrape()` method which should:

      - Call `fetch_html()` to retrieve the HTML content.

      - Use `BeautifulSoup` to parse the HTML.

      - Locate and extract article elements according to the website’s layout.

      - Filter articles by your desired criteria (like publication date).

    **Example: Adding a New Website Scraper**

    Below is a simple example of how you might implement a new scraper for a site called "ExampleSite":

    ```python
    class ExampleSiteScraper(BaseScraper):
        def __init__(self, url):
            super().__init__(url)
        
        def parse_article(self, article_elem):
          """Parses a single article element and returns an Article instance."""
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
            html = self.fetch_html()
            if html is None:
                return []
            soup = BeautifulSoup(html, "html.parser")
            section = soup.find("section", class_="section__latest-posts")
            if not section:
                print("Website Name: 'Latest' section not found.")
                return []
            articles = []
            for article_elem in section.find_all("article"):
                article = self.parse_article(article_elem)
                if article is not None and article.date >= threshold_date:
                    articles.append(article)
            return articles
    ```

2. Integrate Your New Scraper

    Once you've created your new scraper class, add an instance of it to the scraper list in your main module (e.g., in webscrape.py):

    ```python
    if __name__ == "__main__":     
        
        # ... existing code ...
        
        scrapers = [
            BetaKitScraper("https://betakit.com/"),
            FinSMEsScraper("https://www.finsmes.com/category/canada"),
            ExampleSiteScraper("https://www.examplesite.com/")  # Your new scraper added here
        ]
        
        # ... existing code ...
    ```

    This design keeps your code modular and makes it easy to add or update scraping logic for additional websites without touching the
    core logic of the project.

## Contributing

Contributions are welcome! Feel free to fork the repository, create new scraper classes, and suggest improvements. When making contributions,
please follow standard GitHub procedures and add appropriate documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
