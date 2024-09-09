from datetime import datetime
import os
from typing import Optional
import pandas as pd
from pydantic import BaseModel, Field


class Equity(BaseModel):
    isin: Optional[str] = Field(
        default=None, description='ISIN of the equity', example='US9311421039'
    )
    ticker: Optional[str] = Field(
        default=None, description='Ticker of the equity', example='WMT'
    )
    name: Optional[str] = Field(
        default=None, description='Name of the equity', example='Walmart'
    )
    currency: Optional[str] = Field(
        default=None, description='Currency of the equity', example='USD'
    )
    latest_price: Optional[float] = Field(
        default=None, description='Latest market price of the equity', example=150.25
    )
    historical_prices: Optional[dict] = Field(
        default=None, description='Dictionary representation of historical prices of the equity'
    )
    shares_held: Optional[float] = Field(
        default=None, description='Number of shares held for this equity', example=100.0
    )

class Portfolio(BaseModel):
    name: str = Field(
        default = None,
        description='Name of the portfolio'
    )
    equities: dict[str, Equity] = Field(
        default_factory=dict, 
        description='Dictionary of equities with ticker as key'
    )
    def to_json(self):
        return self.json(indent=4)  # Converts the portfolio to a JSON string with indentation for readability

class NewsArticle(BaseModel):
    headline: str = Field(
        description="The headline of the news article", 
        example="Apple Inc. Reports Record Quarterly Earnings"
    )
    content: Optional[str] = Field(
        default = None,
        description="The full content of the news article", 
        example="Apple Inc. has reported record earnings for the quarter, with revenue up by 20%..."
    )
    summary: Optional[str] = Field(
        default = None,
        description="A brief summary of the news article", 
        example="Apple's quarterly earnings have exceeded expectations, driven by strong iPhone sales."
    )
    sentiment: Optional[float] = Field(
        default = None,
        description="The sentiment score of the article, typically between -1 (negative) and 1 (positive)", 
        example=0.85
    )
    link: Optional[str] = Field(
        default = None,
        description="The URL link to the full news article", 
        example="https://example.com/news/apple-earnings-report"
    )
    source: Optional[str] = Field(
        default = None,
        description="The source of the news article", 
        example="Bloomberg"
    )
    publication_date: Optional[datetime] = Field(
        default=None,
        description="The publication date and time of the news article", 
        example="2024-09-02T15:45:00Z"
    )

class RelatedArticles(BaseModel):
    articles: dict[str, list[NewsArticle]] = Field(
        default_factory=dict, 
        description="Dictionary of related news articles with the related equity name as the key"
    )
    def to_csv(self) -> None:
        for equity_name, articles_list in self.articles.items():
            date_str = datetime.now().strftime("%Y-%m-%d")
            directory = f"data/yfinance/{date_str}"
            os.makedirs(directory, exist_ok=True)
            # Create a DataFrame from the list of NewsArticle objects
            articles_data = [article.dict() for article in articles_list]
            df = pd.DataFrame(articles_data)
            
            # Define the path for the CSV file
            file_path = os.path.join(directory, f"{equity_name}.csv")
            
            # Save the DataFrame to a CSV file
            df.to_csv(file_path, index=False)

class EquityContext(BaseModel):
    name: Optional[str] = Field(
        default=None,
        description="Name of the equity",
        example="HEINEKEN"
    )
    isin: Optional[str] = Field(
        default=None,
        description="ISIN of the equity",
        example="NL0000009165"
    )
    ticker: Optional[str] = Field(
        default=None,
        description="Bloomberg ticker of the equity, if available",
        example="HEIA NA"
    )
    publication_date: Optional[str] = Field(
        default=None,
        description="The publication date and time of the internal document", 
        example="2024-09-02T15:45:00Z"
    )
    series: Optional[str] = Field(
        default=None,
        description="Series to which the document belongs",
        example="Equity Deep Dive"
    )
    document_name: Optional[str] = Field(
        default=None,
        description="Name of the document",
        example="Heineken (Maintain Hold, Price_Target_ EUR 79.90_85.00)-en"
    )
    document_information: dict[str, str] = Field(
        description="Rest of the information found in the document, key being the section header"
    )