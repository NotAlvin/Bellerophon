from functools import partial

import streamlit as st

from utils.streamlit.yahoo_search_helper import search_functionality, display_equities
from utils.streamlit.session_state_helper import refresh_state, remove_equity, add_portfolio


# Set page configuration
st.set_page_config(page_title="Portfolio Setup", page_icon="📝")

st.title("Portfolio Creation 📝")
st.subheader("Add or remove equities from your portfolio.")

refresh_state()

# Add new portfolio
new_portfolio_name = st.text_input("New Portfolio Name")

if new_portfolio_name:
    if new_portfolio_name not in st.session_state.portfolios:
        st.write(f'Add Equities to {new_portfolio_name}')
        st.session_state.created_portfolio.name = new_portfolio_name

        search_functionality("main_search")

        # Display financial and tech tickers with checkboxes
        display_equities("Tech")
        display_equities("Financial")
    

        # Display added equities
        if st.session_state.created_portfolio:
            st.write("Current Equities in Portfolio:")
            if st.session_state.created_portfolio.equities:
                for name, equity in st.session_state.created_portfolio.equities.copy().items():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"- **{equity.name}** ({equity.ticker})")
                    with col2:
                        if st.button("Delete", key=equity.ticker, on_click=partial(remove_equity, equity=equity)):
                            remove_equity(equity)

                # Save Portfolio
                if st.button("Save Portfolio", type='primary', on_click=partial(add_portfolio, portfolio=st.session_state.created_portfolio)):
                    st.success(f"Portfolio '{new_portfolio_name}' created successfully!")
                    refresh_state(True)
    else:
        st.success("This portfolio already exists! Try an alternate name")
