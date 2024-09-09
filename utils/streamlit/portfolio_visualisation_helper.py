import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.base_templates import Portfolio

def calculate_portfolio_value(portfolio: Portfolio) -> pd.DataFrame:
    """Calculate the portfolio value over time based on the historical prices and shares held."""
    data = {}

    # Iterate over each equity in the portfolio
    for equity in portfolio.equities.values():
        ticker = equity.ticker
        historical_prices = equity.historical_prices  # Assuming this is stored as a dict with epoch timestamps
        shares_held = equity.shares_held

        # Convert the dictionary with epoch timestamps back to a pandas Series
        historical_prices_series = pd.Series(
            data=historical_prices.values(),
            index=pd.to_datetime(list(historical_prices.keys()), unit='s')
        )

        # Forward fill, backward fill, and interpolate the prices
        data[ticker] = historical_prices_series.ffill().bfill().interpolate()

    # Create a DataFrame of all equities' historical prices
    portfolio_df = pd.DataFrame(data)

    # Multiply the historical prices by the shares held for each equity
    for equity in portfolio.equities.values():
        ticker = equity.ticker
        shares_held = equity.shares_held
        portfolio_df[ticker] = portfolio_df[ticker] * shares_held

    # Calculate the total portfolio value over time
    portfolio_df['Total'] = portfolio_df.sum(axis=1)

    return portfolio_df

def plot_allocation(portfolio: Portfolio):
    """Plot pie chart of portfolio allocation."""
    allocation = {e.name: e.shares_held * e.latest_price for e in portfolio.equities.values()}
    total_value = sum(allocation.values())
    allocation_percent = {k: v / total_value for k, v in allocation.items()}
    
    fig = px.pie(names=allocation_percent.keys(), values=allocation_percent.values(), title="Portfolio Allocation")
    st.plotly_chart(fig)

def plot_performance(portfolio_df: pd.DataFrame):
    """Plot line chart of portfolio performance with dual y-axes."""
    fig = go.Figure()

    # Plot individual equities on the left y-axis
    for ticker in portfolio_df.columns[:-1]:  # Exclude the 'Total' column
        fig.add_trace(go.Scatter(
            x=portfolio_df.index, 
            y=portfolio_df[ticker], 
            mode='lines', 
            name=ticker,
            yaxis="y1"  # Left y-axis
        ))
    
    # Plot total portfolio on the right y-axis
    fig.add_trace(go.Scatter(
        x=portfolio_df.index, 
        y=portfolio_df['Total'], 
        mode='lines', 
        name='Total Portfolio', 
        line=dict(width=4, color='white'), 
        yaxis="y2"  # Right y-axis
    ))

    # Update layout for dual y-axes
    fig.update_layout(
        title="Portfolio Performance over Time",
        xaxis_title="Date",
        yaxis_title="Equity Value",
        yaxis2=dict(
            title="Total Portfolio Value",
            overlaying='y',
            side='right',
            showgrid=False
        ),
        yaxis=dict(
            title="Individual Equity Value",
            showgrid=True
        ),
        legend=dict(
            x=1.2,  # Move the legend to the right of the plot
            y=1,  # Align legend at the top
            orientation="v",  # Vertical legend
            bgcolor='rgba(255, 255, 255, 0.5)',  # Optional: add a white background with transparency
        ),
        margin=dict(l=0, r=50, t=50, b=0)  # Add more margin to the right to fit the legend
    )

    st.plotly_chart(fig)

def display_equity_details(portfolio: Portfolio):
    """Main function to display equity details and plots."""
    portfolio_df = calculate_portfolio_value(portfolio)
    
    plot_allocation(portfolio)
    plot_performance(portfolio_df)
