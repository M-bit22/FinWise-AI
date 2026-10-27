import langchain
from langchain.cache import InMemoryCache, SQLiteCache

def setup_caching(cache_type: str):
    if cache_type == "SQLiteCache":
        langchain.llm_cache = SQLiteCache(database_path=".langchain.db")
    else:
        langchain.llm_cache = InMemoryCache()