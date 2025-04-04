from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from tools.search_tools import search_news, search_DDG
from tools.technical_analysis import technical_analysis
from tools.scrape_finviz_stocks import scrape_finviz_stocks
from graph_state import State
from langchain_core.messages import SystemMessage


# Tools초기화
tools = [search_news, search_DDG, technical_analysis, scrape_finviz_stocks]
tool_node = ToolNode(tools)

# Gemini 모델 사용
llm = ChatAnthropic(
    model="claude-3-5-haiku-20241022",
    temperature=0.1,
    max_tokens=2048
).bind_tools(tools)

# AI 응답 생성 노드
def superviser(state: State) -> State:
    '''Superviser Agent for Final answer'''
    messages = state["messages"]
    
    # AI 시스템 프롬프트
    system_prompt = """
    당신은 투자 전문가 AI 비서입니다. 당신에게 제공된 다양한 툴을 활용해서, 사용자의 투자 의사결정을 도와주세요.
    주식 데이터가 있는 경우, 이를 활용하여 객관적인 정보를 제공하고
    중요한 기술적/기본적 지표에 대해 설명해주세요. 되도록 한국어로 답변해주세요
    """
    
    # AI 응답 생성
    response = llm.invoke([SystemMessage(content=system_prompt)]+messages)
    
    return {"messages": [response]}
