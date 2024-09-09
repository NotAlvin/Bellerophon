import streamlit as st
from functools import partial

from utils.streamlit.portfolio_visualisation_helper import display_equity_details
from utils.streamlit.session_state_helper import (
    PORTFOLIOS_JSON_PATH,
    load_portfolios_from_json,
    remove_equity,
    update_equity,
    remove_portfolio,
    toggle_display
)

# UI: Manage Existing Portfolios
st.title("Manage Existing Portfolios 📂")

# Initialize session state variables
if 'display' not in st.session_state:
    st.session_state.display = False
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
    # Display portfolio details
    st.write(f"Selected portfolio: **{selected_portfolio}**")

    # Show equities in the selected portfolio
    st.write("**Equities in this portfolio:**")
    for equity_name, equity in st.session_state.current_portfolio.equities.items():
        with st.expander(f"{equity_name} Details:"):
            col1, col2, col3 = st.columns([3, 2, 1])
            # Show equity details in a dataframe
            with col1:
                ordered_equity_rows = ['name', 'ticker', 'isin', 'currency', 'latest_price', 'shares_held']
                equity_details = {k: equity.dict()[k] for k in ordered_equity_rows}
                st.table(equity_details)

            # Input to update number of shares held
            with col2:
                shares_held = st.text_input(
                    'Number of shares', 
                    key=f"value_{equity_name}", 
                    placeholder='0000', 
                    value=str(equity.shares_held) if equity.shares_held else ''
                )

                # Update equity only if the shares held value has changed
                if shares_held and shares_held != str(equity.shares_held):
                    try:
                        shares_held_value = float(shares_held)
                        update_equity(shares_held_value, st.session_state.current_portfolio.name, equity)
                    except ValueError:
                        st.error(f"Invalid value for shares: {shares_held}")

            # Button to remove the equity
            with col3:
                st.button(
                    "Remove", 
                    key=f"remove_{equity_name}", 
                    on_click=partial(remove_equity, equity=equity, portfolio=st.session_state.current_portfolio)
                )

    # Button to delete the entire portfolio
    col4, col5, col6 = st.columns([1, 1.5, 5])
    with col4:
        if st.button("Refresh", key="refresh_button"):
            st.rerun()  # Refresh the page to update the list of portfolios

    with col5:
        if st.button("Delete Portfolio", key="delete_button"):
            remove_portfolio(st.session_state.current_portfolio)
            st.success(f"Portfolio '{selected_portfolio}' deleted successfully!")
    # Toggle display of portfolio data
    with col6:
        st.button(
            "Toggle displaying of portfolio data", 
            on_click=toggle_display, key="display_button"
        )

    # Optional: Display portfolio allocation if toggled
    if st.session_state.display:
        with st.expander('Portfolio Allocation'):
            display_equity_details(st.session_state.current_portfolio)
else:
    st.write("No portfolios found. Please create a portfolio first.")
