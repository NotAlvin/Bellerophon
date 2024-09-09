# Equity Narrative Generation

This document provides a comprehensive guide to generating equity narratives using a systematic approach. The process involves gathering relevant news, filtering and summarizing it, and generating actionable recommendations based on the findings.

---

## Overview

The equity narrative generation process is designed to offer a detailed understanding of an equity's current position by analyzing recent news, internal house view documents, and recent price trends. The final output is a narrative that can be used to inform investment decisions.

## Workflow Steps

### 1. Get Ticker Information

- **Input**: The user searches for the ticker symbol or the name of the equity.
- **Action**: The system fetches the relevant ISIN (International Securities Identification Number) and associated ticker.
- **Purpose**: This step ensures that the correct equity is being analyzed by obtaining standardized identifiers.

### 2. Search for News

- **Action**: Utilize search engines (e.g., SERP API) to gather news articles related to the equity.
- **Filter**: Focus on news from the last several days to ensure relevance.
- **Purpose**: Collect up-to-date information to inform the narrative.

### 3. Scrape and Save Content

- **Action**: Scrape the content from the retrieved news article links.
- **Filter**: Evaluate the relevance of each article, discarding those that do not provide useful information.
- **Purpose**: Curate a set of pertinent articles for further analysis.

### 4. Summarize News

- **Action**: Assign a score to each article based on its relevance and informational value.
- **Summarization**: Condense the key points from each relevant article.
- **Combine**: Merge the summaries to create a cohesive narrative.
- **Purpose**: Generate a concise overview of the equity's recent news coverage.

### 5. Generate Recommendations

- **Action**: Based on the summarized news, generate a recommendation for the equity.
- **Scoring**: Assign a score reflecting the severity or positivity of the news.
- **Purpose**: Provide an actionable recommendation derived from the news analysis.

### 6. Fetch Internal House View Documents

- **Action**: Use the ISIN, ticker, and name to locate internal house view documents with matching metadata.
- **Document Selection**: Focus on the latest document for the most current house view.
- **Purpose**: Incorporate internal perspectives to enhance the analysis.

### 7. Comparison and Final Narrative

- **Price Trend Analysis**: Retrieve the past week's price data using the Yahoo Finance API to gauge recent trends.
- **Comparison**: Contrast the house view with external news sources to develop a comprehensive narrative.
- **Final Narrative**: Synthesize the information into a final narrative that reflects both internal and external perspectives.
- **Purpose**: Ensure that the narrative is well-rounded and considers all relevant factors.

## Notes

- The process is structured to offer a thorough and accurate understanding of the equity's standing based on recent events.
- Each step refines and filters information to produce a reliable narrative that can guide investment decisions.
- This workflow aims to balance external news with internal views, ensuring a comprehensive analysis.

---
