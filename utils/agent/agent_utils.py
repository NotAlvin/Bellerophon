from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from utils.config import OPENAI_API_KEY, OPENAI_MODEL
from utils.base_templates import Equity, NewsArticle

app = FastAPI()

# API Key from environment variable
api_key = OPENAI_API_KEY
model = OPENAI_MODEL
if not api_key:
    raise HTTPException(status_code=500, detail="API key not found")

llm = ChatOpenAI(
    model=model,
    api_key=api_key,
    temperature=1,
)

# Define Pydantic models
class Score(BaseModel):
    """Score indicating how relevant a newspaper article is to an equity product or class of products"""
    score: float = Field(
        description="Float between 0 and 1.",
        enum=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
    )

class Summary(BaseModel):
    """Newsworthy piece of text containing information relevant to one or more equity products"""
    summary: str = Field(
        description="Text string containing up-to-date, true, and relevant news."
    )

class Narrative(BaseModel):
    """A detailed narrative that explains how the news affects each equity product"""
    narrative: str = Field(
        description="Text string containing a detailed narrative that explains how the news affects each equity product"
    )

class Action(BaseModel):
    """Actionable recommendations based on the narrative of how the news affects an equity in the portfolio"""
    recommendation: int = Field(
        description="A score based on the recent news narrative about an equity.",
        enum=[1, 2, 3, 4],
    )

# Define Prompt Templates
article_relevancy_prompt = ChatPromptTemplate(
    [
        ("system", "You are a seasoned newspaper editor with deep knowledge of the financial markets."),
        ("human",
            '''
                **Task**: Your job is to determine how relevant a newspaper article is to a specific equity product or a class of equity products.

                To do this, use a Chain-of-Thought approach:

                1. **Assess Relevance**: Based on the key points mentioned in the article summary, determine the how relevant the article is to {equity}. Consider aspects like market sentiment, specific mentions of companies or products, economic indicators, and any other information that could influence the equity market.
                2. **Logical Deduction**: Think through the reasoning process in detail. Why do you believe these details are or are not relevant to {equity}?
                3. **Score Assignment**: Finally, based on your assessment, assign a relevance score between 0 and 1, where 0 indicates no relevance and 1 indicates extremely high relevance.

                **Here is the article summary to score**: 
                {summary}

                The relevancy score of the given summary is:
            ''')
    ]
)

article_summary_prompt = ChatPromptTemplate(
    [
        ("system", "You are a financial analyst with expertise in filtering out relevant information from and summarizing market-relevant news."),
        ("human",
            '''
                **Task**: Summarize the key points of the following newspaper article. Focus particularly on extracting and retaining ONLY information that is directly relevant and up-to-date concerning {equity}.
                
                To do this, use a Chain-of-Thought approach:

                1. **Identify Relevant Content**: Carefully read through the article and identify all information that pertains to the {equity}.
                2. **Summarize Key Points**: Create a concise summary that includes all relevant information. Ensure that any financial metrics, corporate actions, economic indicators, or market sentiments related to the equity are highlighted.
                3. **Ensure Timeliness**: Make sure to include only the most current and impactful information that is related to {equity}, omitting any outdated or irrelevant details.
                4. **Maintain Clarity**: The summary should be clear, precise, and easy to understand for someone with a financial background.

                **Here is the article to summarize**: 
                {article}

                Provide the final summary below:
            ''')
    ]
)

narrative_generation_prompt = ChatPromptTemplate(
    [
        ("system", "You are a market strategist responsible for analyzing how recent news impacts various equity products."),
        ("human",
            '''
                **Task**: Based on the provided list of article summaries, generate a detailed narrative that explains how you expect the news to affect {equity}.

                To do this, use a Chain-of-Thought approach:

                1. **Synthesize Key Insights**: Review the summaries and extract the most important insights related to {equity}.
                2. **Establish Connections**: Clearly link the cause (news events) with the effect (impact on {equity}). Provide logical reasoning for why certain news is likely to drive specific outcomes.
                3. **Create a Short and Coherent Narrative**: Present the analysis in a well-structured, logical narrative within 300 words. Ensure that the narrative is clear, concise, and flows smoothly.
                4. **Cite the link of the news article that was used to create each part**

                **Here is the list of article summaries**: 
                {summaries}

                Generate the narrative below:
            ''')
    ]
)

recommendation_generation_prompt = ChatPromptTemplate(
    [
        ("system", "You are an investment advisor providing strategic recommendations for a portfolio equity."),
        ("human", 
            '''
                **Task**: Evaluate the impact of the recent news on {equity} and assign an impact score.

                To do this, use a Chain-of-Thought process:

                1. **Assess Impact**: Analyze the news to determine its potential effect on {equity}—minimal, moderate, or significant.
                2. **Assign Score**: Based on your assessment, assign an impact score from the following scale:

                - **1**: Minimal or no impact.
                - **2**: Moderate impact, suggesting portfolio reassessment.
                - **3**: Potential future volatility or significant developments.
                - **4**: Major event or events with extreme potential impact.

                **Recent News Summary**:
                {narrative}

                **Impact Score**:
            '''
        )
    ]
)

# Define the agents using the templates
scorer_agent = article_relevancy_prompt | llm.with_structured_output(Score)
summary_agent = article_summary_prompt | llm.with_structured_output(Summary)
narrative_agent = narrative_generation_prompt | llm.with_structured_output(Narrative)
recommendation_agent = recommendation_generation_prompt | llm.with_structured_output(Action)

class SummaryAgent(BaseModel):
    threshold: float
    equity: Equity
    articles: list[NewsArticle]
    summaries: list[str] = []
    scores: list[float] = []
    narrative: str = ""
    recommendation: str = ""

def summarizer(state: SummaryAgent):
    equity = state.equity
    articles = state.articles
    
    for article in articles:
        summary_ = summary_agent.invoke({'equity': equity.name, 'article': article.content})
        state.summaries.append(f'Article link: {article.link} \n {summary_.summary}')
    
    return {'summaries': state.summaries}

def scorer(state: SummaryAgent):
    equity = state.equity
    summaries = state.summaries
    scores = []
    
    for summary in summaries:
        score_ = scorer_agent.invoke({'equity': equity.name, 'summary': summary})
        scores.append(score_.score)
    
    state.scores = scores
    return {'scores': state.scores}

def narrative_generator(state: SummaryAgent):
    summaries = state.summaries
    scores = state.scores
    threshold = state.threshold
    
    filtered_summaries = [summaries[i] for i, score in enumerate(scores) if score > threshold]
    
    if filtered_summaries:
        summaries_text = "\n".join(filtered_summaries)
        narrative_ = narrative_agent.invoke({'equity': state.equity.name, 'summaries': summaries_text})
        state.narrative = narrative_.narrative
        return {'narrative': state.narrative}
    else:
        state.narrative = ""
        return {'narrative': state.narrative}

def recommendation_generator(state: SummaryAgent):
    equity = state.equity
    narrative = state.narrative
    
    if narrative:
        recommendation_ = recommendation_agent.invoke({'equity': equity.name, 'narrative': narrative})
        mapping = {
            1: "**Nothing to Note**",
            2: "**Review Allocation**",
            3: "**Monitor Developments**",
            4: "**Contact Relationship Manager**"
        }
        state.recommendation = mapping[recommendation_.recommendation]
        return {'recommendation': state.recommendation}
    else:
        state.recommendation = "**Nothing to Note** - No relevant news"
        return {'recommendation': state.recommendation}

class PriceTrendAnalysis(BaseModel):
    """
    Analyzes a list of floats representing the past week's equity prices and generates a string description of the recent price trend.
    """
    trend: str = Field(
        description="Text string describing the recent price trend based on the provided list of prices. It should summarize whether the trend is upward, downward, or neutral, and provide any additional relevant observations."
    )

class Comparison(BaseModel):
    """
    A detailed comparison of recent equity trends, internal house view, and generated news narrative.
    This comparison will evaluate which perspective is more accurate and timely.
    """

    comparison: str = Field(
        description="Text string containing a detailed comparison between the recent equity trend, house view, and news narrative. It should identify which perspective is more aligned with the current market conditions."
    )

price_trend_prompt = ChatPromptTemplate(
    [
        ("system", "You are a financial analyst responsible for identifying and describing price trends based on historical data."),
        ("human",
            '''
            **Task**: Analyze the provided list of daily closing prices for {equity} over the past week and generate a string description of the recent price trend.

            Follow these steps:

            1. **Evaluate Price Movement**: Analyze the list of prices to determine the overall direction of the trend (e.g., upward, downward, neutral). Consider the magnitude and consistency of the price changes.
            
            2. **Summarize the Trend**: Provide a concise description of the trend. Mention whether the trend is positive (upward), negative (downward), or neutral. Include any significant observations, such as volatility or any notable price spikes or drops.

            3. **Consider the Context**: If applicable, briefly consider any external factors or market conditions that might explain the observed trend (e.g., earnings reports, market-wide events).

            **Input Data**:
            - **Prices**: {prices}

            Provide your trend analysis below:
            ''')
    ]
)

comparison_prompt = ChatPromptTemplate(
    [
        ("system", "You are a financial analyst responsible for assessing the accuracy and timeliness of different viewpoints on equity performance. You avoid being too judgemental and temper your advice given the uncertainty in the markets."),
        ("human",
            '''
            **Task**: Evaluate the recent performance of {equity} by comparing three different perspectives: the recent trend in equity price, the house view from our internal team, and the narrative generated from recent news. Your goal is to determine which perspective is most accurate and timely.

            Use a step-by-step approach:

            1. **Assess Recent Trend**: Begin by summarizing the recent trend in {equity}'s price over the past week as described in the provided data. Determine if the trend is positive, negative, or neutral.
            
            2. **Evaluate House View**: Analyze the house view provided by our internal team, keeping in mind that {house_view_meta}. Is the house view now out of date? How well does this view align with the recent trend? Is the house view forward-looking and does it account for current market conditions?

            3. **Analyze News Narrative**: Review the news narrative generated from recent articles. Does this narrative explain the recent price trend? Is it more aligned with the current market movements than the house view?

            4. **Comparison and Conclusion**: Compare the house view and the news narrative with the recent trend in equity price. Determine which of these two perspectives is more accurate and timely given the recent trend.

            5. **Final Recommendation**: Based on your analysis, provide a recommendation whether the perspectives differ with regards to future considerations of {equity}. Explain your reasoning clearly.

            **Input Data**:
            - **Recent Trend**: {recent_trend}
            - **House View**: {house_view}
            - **News Narrative**: {news_narrative}

            Provide your analysis below:
            ''')
    ]
)

trend_agent = price_trend_prompt | llm.with_structured_output(PriceTrendAnalysis)
comparison_agent = comparison_prompt | llm.with_structured_output(Comparison)

class ComparisonAgent(TypedDict):
    equity: str
    house_view_meta: str
    house_view: str
    news_narrative: str
    prices: list[float]
    recent_trend: str
    comparison_narrative: str

def trend_description(state: ComparisonAgent):
    equity = state['equity']
    prices = state['prices']
    
    recent_trend_ = trend_agent.invoke({'equity': equity, 'prices': prices})
    return {'recent_trend': recent_trend_.trend}

def comparison_generator(state: ComparisonAgent):
    equity = state['equity']
    recent_trend = state['recent_trend']
    house_view = state['house_view']
    house_view_meta = state['house_view_meta']
    news_narrative = state['news_narrative']
    
    comparison_ = comparison_agent.invoke({
        'equity': equity,
        'recent_trend': recent_trend,
        'house_view_meta': house_view_meta,
        'house_view': house_view,
        'news_narrative': news_narrative
    })
    
    return {'comparison_narrative': comparison_.comparison}


