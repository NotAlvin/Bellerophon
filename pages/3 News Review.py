import os
import pandas as pd
import streamlit as st
from utils.streamlit.session_state_helper import PORTFOLIOS_JSON_PATH, load_portfolios_from_json
from utils.scraping.news_fetcher import create_related_articles

st.set_page_config(page_title="News Review", page_icon="📰")

st.title("News Review 📰")
st.write("Review news for your selected equities and generate narratives.")

# Initialize session state variables
if 'load_news' not in st.session_state:
    st.session_state.load_news = False
if 'portfolios' not in st.session_state:
    st.session_state.portfolios = load_portfolios_from_json(PORTFOLIOS_JSON_PATH)
if 'current_portfolio' not in st.session_state:
    st.session_state.current_portfolio = None

# Get list of portfolios
candidates = list(st.session_state.portfolios.keys())
if candidates:
    selected_portfolio = st.selectbox("Select a portfolio to manage", candidates)
else:
    selected_portfolio = ''
    st.write("No portfolios found. Please create a portfolio first.")

# Handle selected portfolio
if selected_portfolio:
    st.session_state.current_portfolio = st.session_state.portfolios[selected_portfolio]
    st.session_state.load_news = True
    # Display portfolio details
    st.write(f"Selected portfolio: **{selected_portfolio}**")


if st.session_state.load_news:
    for equity in st.session_state.portfolios[selected_portfolio].equities.values():
        with st.expander(f"News for {equity.name}"):
            date_str = pd.Timestamp.now().strftime("%Y-%m-%d")
            save_dir = f"data/yfinance/{date_str}"
            file_path = os.path.join(save_dir, f"{equity.name}.csv")

            # Check if the file exists
            if not os.path.exists(file_path):
                create_related_articles(portfolio=st.session_state.portfolios[selected_portfolio])
            existing_df = pd.read_csv(file_path)
            # Check if DataFrame is not empty
            if not existing_df.empty:
                row_count = min(len(existing_df), 10)
                tab_titles = [f"News item {i + 1}" for i in range(row_count)]
                tabs = st.tabs(tab_titles)
                counter = 0
                for i, row in existing_df.head(20).iterrows():
                    if counter >= 10:
                        break
                    if row.get('content') and len(row['content'].strip()) > 0:
                        with tabs[counter]:
                            st.write(f"**Headline:** {row['headline']}")
                            summary = row['summary'].strip().replace('$', '\$')
                            st.write(f"**Summary:** {summary}")
                            st.write(f"[Read more]({row['link']})")
                        counter += 1
    st.success(f"News loaded successfully - Proceed to news analysis page")
