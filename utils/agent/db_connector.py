from datetime import datetime
import pandas as pd
from datetime import datetime
import bson
from pymongo import MongoClient, collection

from utils.config import DATABASE_CONNECTION_URL, DB_NAME
from utils.base_templates import Equity, EquityContext, Optional

EQUITY_COLLECTIONS = ["equity_research", "equity_top_picks", "equity_switch", "market_opportunity"]

def get_db_client() -> MongoClient:
    return MongoClient(DATABASE_CONNECTION_URL)

def get_db_collection(
        db_name: str,
        collection_name: str
    ) -> collection.Collection:
    client = get_db_client()
    return client[db_name][collection_name]

def get_db_client_and_collection(
        db_name: str, 
        collection_name: str
    ) -> tuple[MongoClient, collection.Collection]:
    client = get_db_client()
    collection = get_db_collection(db_name, collection_name)
    return client, collection

def update_single_document_in_collection(
        db_name: str, 
        collection_name: str,
        document_id: bson.Binary,
        update_dict: dict,
        upsert: bool = False,
    ) -> None:
    client, collection = get_db_client_and_collection(db_name, collection_name)
    collection.update_one({"_id": document_id}, {"$set": update_dict}, upsert=upsert)
    client.close()

def get_entire_collection_from_date(collection_name, from_date: str = None):
    df = pd.DataFrame(list(get_db_collection(DB_NAME, collection_name).find()))
    if len(df)>0:
        df[["publication_date", "added_date"]] = df[["publication_date", "added_date"]].apply(pd.to_datetime)
        df.drop(columns = ["_id"], inplace = True)
        if from_date: 
            from_date = datetime.strptime(from_date,  "%Y-%m-%d")
            df = df.loc[df.publication_date >= from_date]
    return df

def extract_equity_entries_in_collection(
        collection_name: str,
        equity: Equity, 
        only_latest= False):
        
    collection = get_db_collection(DB_NAME, collection_name)
    equity_entries = collection.find({"$or" : [{"isin": equity.isin}, {"bbg_ticker": equity.ticker}, {"equity": equity.name}]}, sort=[( "publication_date", -1 )])
    equity_entries = pd.DataFrame(list(equity_entries))

    if only_latest and len(equity_entries)>0: 
        equity_entries = equity_entries.iloc[0]    
    return equity_entries


def extract_latest_equity_entry_in_db(equity: Equity):
    latest_publication_date, latest_entry = None, None
    
    for collec in EQUITY_COLLECTIONS:
        entry = extract_equity_entries_in_collection(collec, equity, only_latest = True)
        if len(entry)>0: 
            if latest_publication_date is None:
                latest_entry = entry
                latest_publication_date = entry["publication_date"]
            elif entry["publication_date"]> latest_publication_date:
                latest_entry = entry
                latest_publication_date = entry["publication_date"]
    return latest_entry


def get_equity_context_text(equity) -> Optional[EquityContext]:
    equity_info = extract_latest_equity_entry_in_db(equity)
    if equity_info is None:
        return EquityContext(
            name=equity.name,
            isin=equity.isin,
            ticker=equity.ticker,
            publication_date=None,
            series=None,
            document_name=None,
            document_information={'free_text': f'No information for equity {equity.name} was found in our research database.'}
        )
    
    excluded_keys = {'_id', 'id', 'publication_date', 'source_document', 'series', 'document_name', 'added_date', 'equity', 'isin', 'bbg_ticker'}
    equity_context_dict = {
        key: (", ".join(value) if isinstance(value, list) else value or "Not specified").strip()
        for key, value in equity_info.items() if key not in excluded_keys
    }
    
    return EquityContext(
        name=equity.name,
        isin=equity.isin,
        ticker=equity.ticker,
        publication_date=equity_info.get("publication_date", "").strip() or 'Unknown',
        series=equity_info.get("series"),
        document_name=equity_info.get("document_name"),
        document_information=equity_context_dict
    )