from typing import TypedDict, Annotated, Dict, Any
from langgraph.graph.message import add_messages


# LangGraph를 위한 상태 타입 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]