from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from tools.search_tools import search_news, search_DDG
from graph_state import State
from langchain_core.messages import SystemMessage


# Tools초기화
tools = [search_news, search_DDG]
tool_node = ToolNode(tools)

# Gemini 모델 사용
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.1,
    max_tokens=2048
).bind_tools(tools)

# AI 응답 생성 노드
def superviser(state: State) -> State:
    '''Superviser Agent for Final answer'''
    messages = state["messages"]
    
    # AI 시스템 프롬프트
    system_prompt = """
    당신은 투자 전문가 AI 비서입니다. 사용자의 투자 의사결정을 도와주세요.
    주식 데이터가 있는 경우, 이를 활용하여 객관적인 정보를 제공하고
    중요한 기술적/기본적 지표에 대해 설명해주세요.
    """
    
    # AI 응답 생성
    response = llm.invoke([SystemMessage(content=system_prompt)]+messages)
    
    return {"messages": [response]}
