# Article Scraper Utility

This repository contains a web scraping utilities that collects articles from multiple websites, and optionally appends them
to a Google Sheets page (if credentials are configured).

## Table of Contents

- [Article Scraper Utility](#article-scraper-utility)
  - [Table of Contents](#table-of-contents)
  - [Installation](#installation)
  - [Minimal Usage](#minimal-usage)
  - [Extending the Functionality to Add New Websites](#extending-the-functionality-to-add-new-websites)
  - [Setup Google API Credentials and Google Sheets (Optional)](#setup-google-api-credentials-and-google-sheets-optional)
  - [Usage with Google Sheets](#usage-with-google-sheets)
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

## Minimal Usage

To simply perform web scrapping of articles and store the results into a text file on your machine, run the following command:

```bash
python article_scraper.py
```

The script will scrape the configured websites, filter articles based on a threshold date, and save the output to a file (e.g., `articles.txt`).

## Extending the Functionality to Add New Websites

The code in `article_scraper.py` is designed to be easily extendable. Each website-specific scraper is encapsulated into its own
class inheriting from the `BaseScraper` abstract class. To add new website scraping functionality:

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

## Setup Google API Credentials and Google Sheets (Optional)

For the scripts to work with Google Sheets, you need to create a service account in Google Cloud Console and configure your Google
Sheet. Follow these steps:

1. **Create a Google Cloud Project & Enable the Sheets API**

    - Go to [Google Cloud Console](https://console.cloud.google.com/) and sign in with your Google account.
    - Click the project drop-down in the top bar and select **New Project**.
    - Give your project a name (for example, "ArticleScraperProject") and click **Create**.
    - With the project selected, navigate to **APIs & Services** > **Library**.
    - Search for "Google Sheets API" and click **Enable**.

2. **Create a Service Account**

    - In the Google Cloud Console, go to **APIs & Services** > **Credentials**.
    - Click **Create Credentials** and choose **Service Account**.
    - Give your service account a name (for example, "ArticleScraperService") and click **Create and Continue**.
    - For now, skip granting additional service account permissions and click **Done**.
    - Locate your new service account in the list and click on its email to view details.
    - Under the **Keys** section, click **Add Key** > **Create New Key**.
    - Select **JSON** as the key type and click **Create**. A JSON file will be downloaded to your computer.
    This is your service account file.

3. **Configure Your Scripts with the Service Account**

    - Place the downloaded JSON file in the project folder and rename it to `service_account_file.json`.
    - Open the JSON file and make a note of the `client_email`. You will need it for the next step.

4. **Set Up Your Google Sheet**

    - Create a new Google Sheet (or open an existing one) that will serve as your destination.
    - Click the **Share** button in the upper-right corner.
    - In the "Add people and groups" field, enter the `client_email` from your service account JSON file. Make sure to give it
    **Editor** permissions.
    - In the project directory, create a `.env` file (if one doesn't exist) with the following environment variables. Replace the
    placeholders with your actual values from the Google Sheet:

    ```env
    SPREADSHEET_ID=your_google_sheet_id
    SPREADSHEET_SHEET_NAME=Sheet1
    SPREADSHEET_CELL_RANGE=A1:D1
    ```

    - To get the `SPREADSHEET_ID`, open your Google Sheet in a browser and look at the URL. It is the long string between `/d/` and `/edit`.

These steps will allow the scripts to authenticate with Google, obtain an access token via the service account, and append articles
to your specified Google Sheet.

## Usage with Google Sheets

To automate the process of appending the scraped articles to a Google Sheet, you can now run the command:

```bash
python main.py
```

The script will:

- Scrape the configured websites (filtering articles based on a threshold date),
- Generate a JWT token using your service account,
- Exchange the JWT for an access token,
- Append the scraped articles to your Google Sheet.

## Contributing

Contributions are welcome! Feel free to fork the repository, create new scraper classes, and suggest improvements. When making contributions,
please follow standard GitHub procedures and add appropriate documentation.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
