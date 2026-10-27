
from langchain.globals import set_llm_cache
from langchain_community.cache import InMemoryCache, SQLiteCache


def setup_caching(cache_type: str):
    if cache_type == "SQLiteCache":
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))
    else:
        set_llm_cache(InMemoryCache())
