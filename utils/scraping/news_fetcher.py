import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import yfinance as yf
import re
from dateutil import parser as date_parser
import os

from serpapi.google_search import GoogleSearch

from utils.config import SERP_API_KEY
from utils.base_templates import Equity, Portfolio, NewsArticle, RelatedArticles

def parse_relative_date(date_str: str) -> datetime:
    # Parse strings like "2 days ago", "1 month ago", "4 weeks ago"
    if "second" in date_str:
        seconds = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(seconds=seconds)
    elif "minute" in date_str:
        minutes = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(minutes=minutes)
    elif "hour" in date_str:
        hours = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(hours=hours)
    elif "day" in date_str:
        days = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(days=days)
    elif "week" in date_str:
        weeks = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(weeks=weeks)
    elif "month" in date_str:
        months = int(re.search(r'\d+', date_str).group())
        return datetime.now() - timedelta(days=30 * months)
    else:
        raise ValueError(f"Unknown relative date format: {date_str}")

def parse_date(date_str: str) -> datetime:
    # Handle specific date formats like "Sep 7, 2023"
    try:
        return date_parser.parse(date_str)
    except ValueError:
        # If date is in relative format (e.g., "2 days ago")
        return parse_relative_date(date_str)

def scrape_news_info(url) -> str:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Edg/116.0.1938.54'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else ""
        # print(f"Successfully scraped: {title}")
        # Extract the content
        content = []
        for paragraph in soup.select('p'):
            content.append(paragraph.get_text(strip=False))
        content_text = "\n\n".join(content) if content else ""

        return content_text

    except Exception as e:
        print(e)
        return ""

def fetch_equity_prices(equity: Equity, lookback: int = 7) -> list[float]:
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback)

    data = yf.download(equity.ticker, start=start_date, end=end_date)['Close'].tolist()
    return data
    
def fetch_yahoo_news(equity: Equity, lookback: int, max_len: int) -> list[NewsArticle]:
    news = yf.Ticker(equity.ticker).news
    recent_news = []
    cutoff_date = datetime.now() - timedelta(days=lookback)
    if news:
        for article in news:
            publication_date = datetime.fromtimestamp(article['providerPublishTime'])
            if publication_date >= cutoff_date and len(recent_news) < max_len:
                related_article = NewsArticle(
                    headline = article['title'],
                    content = scrape_news_info(article['link']),
                    summary = None,
                    sentiment = None,
                    link = article['link'],
                    source = article['publisher'],
                    publication_date = publication_date
                )
                recent_news.append(related_article)
    return recent_news

def fetch_google_news(equity: Equity, lookback: int, max_len: int) -> list[NewsArticle]:
    # Filter only the news that appears within the requested lookback
    mapping = {
        1: 'qdr:d', #(Last 24 hours)
        7: 'qdr:w', #(Last week)
        30: 'qdr:m', #(Last month)
        365: 'qdr:y', #(Last year)
    }
    tbs = mapping[max(mapping.keys())]
    for key in mapping:
        if lookback <= key:
            tbs = mapping[key]
            break

    cutoff_date = datetime.now() - timedelta(days=lookback)

    query = f'{equity.name} financial news AND ({equity.ticker} OR {equity.isin})'
    params = {
        "engine": "google",
        "q": query,
        "google_domain": "google.com",
        "tbm": "nws", # Search in news
        "num": 10, # Number of results to fetch (up to 100 per page)
        "tbs": tbs, # Time range for the search, e.g., 'qdr:d' for past day
        "api_key": SERP_API_KEY,
    }
    search = GoogleSearch(params)
    news = search.get_dict().get('news_results', {})
    recent_news = []
    
    for article in news:
        publication_date = parse_date(article['date'])
        if publication_date >= cutoff_date and len(recent_news) < max_len:
            related_article = NewsArticle(
                headline = article['title'],
                content = scrape_news_info(article['link']),
                summary = article['snippet'],
                sentiment = None,
                link = article['link'],
                source = article['source'],
                publication_date = publication_date
            )
            recent_news.append(related_article)
    return recent_news

def create_related_articles(portfolio: Portfolio, source: str = 'google', lookback: int = 1, max_len: int = 5) -> RelatedArticles:
    articles = RelatedArticles(
        articles = {}
    )
    date_str = pd.Timestamp.now().strftime("%Y-%m-%d")
    save_dir = f"data/yfinance/{date_str}"

    for name, equity in portfolio.equities.items():
        file_path = os.path.join(save_dir, f"{equity}.csv")
        if not os.path.exists(file_path): # Fetch news if not already saved
            if source == 'yahoo':
                news = fetch_yahoo_news(equity, lookback = lookback, max_len = max_len)
            elif source == 'google':
                news = fetch_google_news(equity, lookback = lookback, max_len = max_len)
            else:
                news = fetch_google_news(equity, lookback = lookback, max_len = max_len)
        articles.articles[name] = news
    articles.to_csv()
    return articles

# def load_or_create_news_dataframes(portfolio: Portfolio, lookback: int = 1, max_len: int = 5) -> dict[str, pd.DataFrame]:
#     """
#     Create a dictionary where the keys are equity names and the values are DataFrames of their related news articles.
    
#     Args:
#         portfolio (Portfolio): The portfolio containing equities and related news.
#         lookback (int, optional): Number of days to look back for fetching news articles. Defaults to 1.
#         max_len (int, optional): Maximum number of articles to fetch per equity. Defaults to 5.

#     Returns:
#         Dict[str, pd.DataFrame]: A dictionary where keys are equity names and values are DataFrames of related news.
#     """
#     # Initialize an empty dictionary to hold the DataFrames
#     news_dataframes = {}
    
#     # Create related articles for each equity in the portfolio
#     date_str = pd.Timestamp.now().strftime("%Y-%m-%d")
#     save_dir = f"data/yfinance/{date_str}"
#     for equity in portfolio.equities:
#         file_path = os.path.join(save_dir, f"{equity}.csv")
#         if not os.path.exists(file_path): # Refresh
#             create_related_articles(portfolio=portfolio, lookback=lookback, max_len=max_len)
#         news_df = pd.read_csv(file_path)
            
#         # Add the DataFrame to the dictionary using the equity name as the key
#         news_dataframes[equity] = news_df
#     return news_dataframes