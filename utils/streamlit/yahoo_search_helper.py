import os
from datetime import datetime
from functools import partial

import pandas as pd
import requests
import yfinance as yf
import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_searchbox import st_searchbox

from utils.base_templates import Equity
from utils.streamlit.session_state_helper import add_equity, remove_equity


def make_search_callout(search_string: str) -> str:
    url = 'https://query1.finance.yahoo.com/v1/finance/search'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.109 Safari/537.36',
    }
    params = dict(
        q=search_string,
        quotesCount=10,
        newsCount=0,
        listsCount=0,
        quotesQueryId='tss_match_phrase_query'
    )
    resp = requests.get(url=url, headers=headers, params=params)
    data = resp.json()
    if "quotes" not in data: # No results found
        return {}
    return data["quotes"]

def search_yahoo_finance(search_term: str) -> list[tuple[str, str]]:
    candidates = make_search_callout(search_term)
    formatted_results = []
    for candidate in candidates:
        ticker = candidate["symbol"]
        try:
            name = candidate["shortname"] if "shortname" in candidate else candidate["longname"]
            if candidate["isYahooFinance"]:
                formatted_results.append(
                    (
                        f"{name} ({ticker})", 
                        ticker
                    ))
        except Exception as e:
            print(f'Error {e} with search for {candidate}')
    return formatted_results

def search_functionality(key: str,) -> None:
    with stylable_container(
        key=f"container_equity_searchbox_{key}",
        css_styles="""
            {
                width: 90%;
            }
            """,
    ):
        selected_value = st_searchbox(
            search_yahoo_finance,
            key="equity_searchbox_" + key,
            clear_on_submit=True,
            placeholder="Search Equities...",
        )
    
    if selected_value is not None:
        selected_equity = get_equity_from_ticker(selected_value)
        add_equity(selected_equity)

def get_equity_from_ticker(ticker_str: str) -> Equity:
    ticker = yf.Ticker(ticker_str)
    
    # Fetch historical data for the last 1 month
    history = ticker.history(period="1mo")  # 'Close' prices for 1 month
    
    # Convert historical close prices to a pandas Series with dates as index
    historical_prices_series = history['Close']
    
    equity = Equity(
        isin=ticker.isin,
        ticker=ticker_str,
        name=ticker.info.get("shortName") or ticker.info.get("longName", None),
        currency=ticker.info.get('currency', None),
        latest_price=historical_prices_series.iloc[-1],  # Last available close price
        historical_prices=historical_prices_series.rename_axis('Date').rename(lambda x: int(x.timestamp())).to_dict(),  # Series of close prices for 1 month
        shares_held=0  # Placeholder for number of shares
    )
    return equity

def get_information_table(ticker_list: list) -> pd.DataFrame: 
    # Fetch data
    data = yf.download(ticker_list, period="5d", group_by="ticker")  # Fetch 5 days for comparison

    # Extract relevant data for the table
    table = []
    for ticker in ticker_list:
        info = yf.Ticker(ticker).info
        today_close = data[ticker]['Close'].iloc[-1]
        yesterday_close = data[ticker]['Close'].iloc[-2]
        change = today_close - yesterday_close
        percent_change = (change / yesterday_close) * 100
        table.append([
            ticker,
            info['shortName'] or info['longName'],
            round(today_close, 2),
            change,
            percent_change,
        ])

    # Create DataFrame
    columns = ['Ticker', 'Company', 'Price', 'Change', '% Change']
    df = pd.DataFrame(table, columns=columns)
    return df.round(2)

def fetch_or_pull_daily_tickers(requested: str) -> pd.DataFrame:
    ticker_types = ['financial', 'tech']
    for ticker_type in ticker_types:
        if ticker_type == 'financial':
            tickers = [
                        "BAC", "BBVA", "BCS", "BMO", "BNPQY", "BNS", "BSBR", "C", "DB", "GS", "HDB", 
                        "HSBC", "IBKR", "IBN", "ING", "ITUB", "JPM", "MS", "MUFG", "NU", "NWG", "PNC", 
                        "RY", "SCHW", "SMFG", "TFC", "TD", "UBS", "USB", "WFC"
                    ]
        elif ticker_type == 'tech':
            tickers = [
                        "AAPL", "AMD", "AMZN", "BABA", "CRM", "EA", "GOOG", "INTC", "META", "MSFT", 
                        "MTCH", "NVDA", "PYPL", "TSLA", "TTD", "YELP", "ZG"
                    ]
        # Define path
        today_date = datetime.today().strftime('%Y-%m-%d')
        path = os.path.join('data', 'yfinance', today_date)
        os.makedirs(path, exist_ok=True)

        # Define file path
        file_path = os.path.join(path, f'{today_date}_{ticker_type}_tickers.csv')

        # Check if file exists before saving
        if not os.path.exists(file_path):
            df = get_information_table(tickers)
            df.to_csv(file_path, index=False)

    requested_file_path = os.path.join(path, f'{today_date}_{requested}_tickers.csv')
    return pd.read_csv(requested_file_path)

def handle_checkbox_change(ticker_str: str) -> None:
    equity = get_equity_from_ticker(ticker_str)
    
    # Toggle the equity in the portfolio based on its presence
    if equity.name in st.session_state.created_portfolio.equities:
        remove_equity(equity)
    else:
        add_equity(equity)

def display_equities(category: str) -> None:
    with st.expander(f"**Select from Top {category} Tickers**"):
        ticker_df = fetch_or_pull_daily_tickers(category)
        headers = ['Ticker', 'Company', 'Price', 'Change', '% Change', 'Select']
        col_widths = [1, 2.5, 1, 1, 1, 1]
        
        cols = st.columns(col_widths)
        for i in range(len(headers)):
            cols[i].write(f'**{headers[i]}**')
        st.write('---')
        for index, row in ticker_df.iterrows():
            cols = st.columns(col_widths)
            for col, value in zip(cols, row.values):
                col.write(str(value))
            
            # Determine if the equity is already in the portfolio
            is_checked = row['Company'] in st.session_state.created_portfolio.equities

            # Use functools.partial to pass arguments to the callback
            cols[-1].checkbox(
                label=row['Company'],
                label_visibility='hidden',
                value=is_checked, 
                on_change=partial(handle_checkbox_change, row['Ticker']), 
                key=row['Company']
            )