import streamlit as st
import pandas as pd
import os
from datetime import datetime

from utils.scraping.news_fetcher import create_related_articles
from utils.streamlit.session_state_helper import PORTFOLIOS_JSON_PATH, load_portfolios_from_json
from utils.agent.agent_model import RunAgentWorkflowRequest, ComparisonAgentWorkflowRequest, news_agent_workflow, comparison_agent_workflow
from utils.base_templates import Equity, Portfolio

st.set_page_config(page_title="Narratives", page_icon="📖")

def generate_markdown(results: dict, portfolio: Portfolio):
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Initialize the markdown report
    markdown_report = f"# {portfolio.name} Equity Report - {date}\n\n"
    
    # Iterate over each equity in the results
    for equity, content in results.items():
        # Add a section for each equity
        markdown_report += f"## {equity}\n\n"
        
        # Section 1: Stock Information
        markdown_report += "### 1. Stock Information\n\n"
        markdown_report += f"**Ticker:** {portfolio.equities[equity].ticker}\n"
        markdown_report += f"**ISIN:** {portfolio.equities[equity].isin}\n"
        markdown_report += f"**Name:** {portfolio.equities[equity].name}\n"
        markdown_report += f"**Currency:** {portfolio.equities[equity].currency}\n\n"

        # Section 2: News Information and Narrative
        markdown_report += "### 2. News Information and Narrative\n\n"
        markdown_report += f"**Narrative:** {content['narrative']}\n"
        markdown_report += f"**Recommendation:** {content['recommendation']}\n"
        
        # Section 3: News Summaries
        markdown_report += "### 3. News Summaries\n\n"
        if 'summaries' in content:
            for i, summary in enumerate(content['summaries']):
                markdown_report += f"**Article {i+1}:**\n{summary}\n\n"
        
        # Optional Comparison Narrative
        markdown_report += "### 4. Comparison Narratives\n\n"
        if 'comparison_narrative' in content:
            markdown_report += f"**Comparison Narrative:** \n{content['comparison_narrative']}\n\n"

    # Save the markdown report to a file
    path = 'results/'
    os.makedirs(path, exist_ok=True)
    markdown_file_path = f'{path}{portfolio.name}_equity_report_{date}.md'
    
    with open(markdown_file_path, 'w') as f:
        f.write(markdown_report)
    
    print("Markdown report generated successfully!")
    return True

def generate_narratives(portfolio: Portfolio):

    portfolio = Portfolio(
        name=portfolio.name,
        equities={equity.name: Equity(**equity.dict()) for equity in portfolio.equities.values()}
    )
    news_workflow = RunAgentWorkflowRequest(
        portfolio = portfolio,
        related_articles = create_related_articles(portfolio),
        threshold = 0.7
    )
    news_narrative = news_agent_workflow(news_workflow)

    comparison_workflow = ComparisonAgentWorkflowRequest(
         portfolio = portfolio,
         news_narrative = news_narrative
    )
    overall_comparison = comparison_agent_workflow(comparison_workflow)
    
    results = {}
    for equity in portfolio.equities:
        results[equity] = {
            'narrative': news_narrative[equity]['narrative'],
            'recommendation': news_narrative[equity]['recommendation'],
            'comparison_narrative': overall_comparison[equity]['comparison_narrative'],
            'summaries': news_narrative[equity]['summaries']
        }
        
    generate_markdown(results, portfolio)
    return results

st.title("Equity Narratives 📖")
st.write("Generate narratives and comparison narratives for your selected equities.")

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
    results = {}
    if st.button("Analyse News"):
        results = generate_narratives(st.session_state.current_portfolio)
        for equity, content in results.items():
            if content['recommendation']:
                with st.expander(f"{equity} - **Recommendation:** {content['recommendation']}", expanded=False):
                    temp = content['comparison_narrative'].replace('$', '\$')
                    st.markdown(f"{temp}", unsafe_allow_html=True)
            else:
                st.expander(f"{equity} - There was no news to analyze over the given timeframe")
                
        # with st.expander(f"Generated Report for Portfolio: {st.session_state.current_portfolio.name}"):
        #     date = datetime.now().strftime('%Y-%m-%d')
        #     path = 'results/'
        #     os.makedirs(path, exist_ok=True)
        #     markdown_file_path = f'{path}{st.session_state.current_portfolio.name}_equity_report_{date}.md'
        #     with open(markdown_file_path, "r") as file:
        #         markdown_content = file.read()

        #     # Display the Markdown content in Streamlit
        #     st.markdown(markdown_content, unsafe_allow_html=True)
