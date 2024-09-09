from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd

from utils.agent.agent_utils import (
    SummaryAgent, scorer, summarizer, narrative_generator, 
    recommendation_generator, ComparisonAgent, trend_description, comparison_generator
)
from utils.base_templates import Portfolio, RelatedArticles
from utils.agent.db_connector import get_equity_context_text

from langgraph.graph import START, END, StateGraph

app = FastAPI()

class RunAgentWorkflowRequest(BaseModel):
    portfolio: Portfolio
    related_articles: RelatedArticles
    threshold: float

class ComparisonAgentWorkflowRequest(BaseModel):
    portfolio: Portfolio
    news_narrative: dict[str, dict]

@app.get("/")
def read_root():
    return {"message": "Hello from agent_model!"}

@app.post("/run-news-workflow/")
def news_agent_workflow(request: RunAgentWorkflowRequest) -> dict[str, dict]:
    storage = {}
    for name, equity in request.portfolio.equities.items():
        state = SummaryAgent(
            threshold=request.threshold,
            equity=equity,
            articles=request.related_articles.articles[name],
            scores=[],
            summaries=[],
            narrative='',
            recommendation=''
        )
        
        workflow = StateGraph(SummaryAgent)
        
        workflow.add_node("summarizer", summarizer)
        workflow.add_node("scorer", scorer)
        workflow.add_node("narrative_generator", narrative_generator)
        workflow.add_node("recommendation_generator", recommendation_generator)
        
        workflow.add_edge(START, "summarizer")
        workflow.add_edge("summarizer", "scorer")
        workflow.add_edge("scorer", "narrative_generator")
        workflow.add_edge("narrative_generator", "recommendation_generator")
        workflow.add_edge("recommendation_generator", END)
        
        graph = workflow.compile()
        events = graph.invoke(state)
        storage[name] = events
    return storage

@app.post("/comparison-agent-workflow/")
def comparison_agent_workflow(request: ComparisonAgentWorkflowRequest) -> dict[str, dict]:
    storage = {}
    for name, equity in request.portfolio.equities.items():
        equity_context = get_equity_context_text(equity)
        if 'free_text' in equity_context.document_information and equity_context.document_information['free_text'] == f'No information for equity {name} was found in our research database.':
            storage[name] = {}
        else:
            # Convert the dictionary with epoch timestamps back to a pandas Series
            historical_prices_series = pd.Series(
                data=equity.historical_prices.values(),
                index=pd.to_datetime(list(equity.historical_prices.keys()), unit='s')
            )
            state = ComparisonAgent(
                equity=equity,
                house_view_meta=f"this document type is {equity_context.series} and was published on {equity_context.publication_date}",
                house_view="/n".join(f'{k}: {v}' for k, v in equity_context.document_information.items()),
                news_narrative=request.news_narrative[name]['narrative'],
                prices=list(historical_prices_series.iloc[-7:]),
                recent_trend="",
                comparison_narrative=""
            )
            
            workflow = StateGraph(ComparisonAgent)
            
            workflow.add_node("trend_describer", trend_description)
            workflow.add_node("comparison_generator", comparison_generator)
            
            workflow.add_edge(START, "trend_describer")
            workflow.add_edge("trend_describer", "comparison_generator")
            workflow.add_edge("comparison_generator", END)
            
            graph = workflow.compile()
            events = graph.invoke(state)
            storage[name] = events
    return storage

# To run the application, you can use the command:
# uvicorn app:app --reload
