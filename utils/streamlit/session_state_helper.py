import json

import streamlit as st

from utils.base_templates import Equity, Portfolio


PORTFOLIOS_JSON_PATH = 'data/portfolios.json'

def save_portfolios_to_json(portfolios: dict[str, Portfolio], file_path: str) -> None:
    # Convert the dictionary of Portfolio objects to a dictionary of dictionaries
    portfolios_data = {name: portfolio.dict() for name, portfolio in portfolios.items()}
    
    # Write the dictionary of portfolios to a JSON file
    with open(file_path, 'w') as json_file:
        json.dump(portfolios_data, json_file, indent=4)

def load_portfolios_from_json(file_path: str) -> dict[str, Portfolio]:
    # Load portfolios from a JSON file
    with open(file_path, 'r') as json_file:
        portfolios_data = json.load(json_file)
    
    # Convert dictionaries back to Portfolio instances
    return {name: Portfolio(**data) for name, data in portfolios_data.items()}

def refresh_state(hard_refresh: bool = False) -> None:
    if hard_refresh:
        st.session_state.created_portfolio = Portfolio(name = '', equities = {})
        st.session_state.portfolios = load_portfolios_from_json(PORTFOLIOS_JSON_PATH)
        st.rerun()
    else:
        if 'created_portfolio' not in st.session_state:
            st.session_state.created_portfolio = Portfolio(name = '', equities = {})
        if 'portfolios' not in st.session_state:
            st.session_state.portfolios = load_portfolios_from_json(PORTFOLIOS_JSON_PATH)

def add_equity(equity: Equity) -> None:
    if equity.name not in st.session_state.created_portfolio.equities:
        st.session_state.created_portfolio.equities[equity.name] = equity

def remove_equity(equity: Equity) -> None:
    if equity.name in st.session_state.created_portfolio.equities:
        del st.session_state.created_portfolio.equities[equity.name]

def update_equity(shares_held: float, selected_portfolio: str, equity: Equity):
    st.session_state.portfolios[selected_portfolio].equities[equity.name].shares_held = shares_held
    save_portfolios_to_json(st.session_state.portfolios, PORTFOLIOS_JSON_PATH)

def add_portfolio(portfolio: Portfolio) -> None:
    st.session_state.portfolios[portfolio.name] = portfolio
    save_portfolios_to_json(st.session_state.portfolios, PORTFOLIOS_JSON_PATH)

def remove_portfolio(portfolio: Portfolio) -> None:
    if portfolio.name in st.session_state.portfolios:
        del st.session_state.portfolios[portfolio.name]
    if 'current_portfolio' in st.session_state:
        del st.session_state.current_portfolio

def toggle_display() -> None:
    st.session_state.display = not st.session_state.display
