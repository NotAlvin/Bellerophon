import streamlit as st

st.set_page_config(
    page_title="Portfolio News Fetcher",
    page_icon="📈",
)

st.write("# Welcome to Bellerophon! 📈")

st.sidebar.success("Select **Portfolio Creation or Selection** page to start!")

st.markdown(
    """
    This application allows you to manage a portfolio of equities, fetch recent news, and generate narratives and recommendations based on the news content.
    
    **👈 Select the Create Portfolio page from the sidebar** to get started.
    
    ### Key Features:
    - Add universe-wide equities to your portfolio
    - Review recent news articles for your equities
    - Generate narratives and recommendations based on recent performance of the equity, it's latest relevant news and compare it with what our internal house view says!
    
    ### How to Use:
    1. Go to the **Portfolio Creation** page to add equities.
    2. Proceed to the **Visualise Portfolio** page to add in details and visualise your portfolio performance.
    2. Move on to the **News Review** page to fetch and review recent news on your selected portfolio.
    3. Finally, visit the **New Analysis** page to view the generated narratives and recommendations.
    """
)

