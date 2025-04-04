from langchain_core.tools import tool, StructuredTool
from langchain_teddynote.tools import GoogleNews
from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
from typing import List, Dict


@tool
def search_news(query: str) -> List[Dict[str, str]]:
    """Search Google News"""
    news_tool = GoogleNews()
    return news_tool.search_by_keyword(query, k=5)


# Define a search tool using DuckDuckGo API wrapper
search_DDG = StructuredTool.from_function(
        name="Web_Search",
        func=DuckDuckGoSearchAPIWrapper().run,  # Executes DuckDuckGo search using the provided query
        description="""
        useful for when you need to answer questions about current events. You should ask targeted questions
        """,
        )