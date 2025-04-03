from langgraph.prebuilt import ToolNode
from langchain_anthropic import ChatAnthropic
from tools.search_tools import search_news, search_DDG
from graph_state import State

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
    last_message = messages[-1].content
    stock_data = state.get("stock_data", {})
    
    # AI 시스템 프롬프트
    system_prompt = """
    당신은 투자 전문가 AI 비서입니다. 사용자의 투자 의사결정을 도와주세요.
    주식 데이터가 있는 경우, 이를 활용하여 객관적인 정보를 제공하고 
    중요한 기술적/기본적 지표에 대해 설명해주세요.
    """
    
    # 주식 데이터가 있다면 메시지에 추가
    if stock_data and "error" not in stock_data:
        ticker = stock_data.get("ticker", "")
        stock_info = f"""
        ### {stock_data.get('name', 'N/A')} ({ticker}) 분석
        
        **현재가**: ${stock_data.get('current_price', 'N/A')}
        **전일종가**: ${stock_data.get('previous_close', 'N/A')}
        **시가총액**: ${stock_data.get('market_cap', 'N/A'):,}
        **P/E 비율**: {stock_data.get('pe_ratio', 'N/A')}
        **배당수익률**: {stock_data.get('dividend_yield', 'N/A')}%
        **52주 최고가**: ${stock_data.get('52w_high', 'N/A')}
        **52주 최저가**: ${stock_data.get('52w_low', 'N/A')}
        
        위 데이터를 바탕으로 분석해드리겠습니다.
        """
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message},
            {"role": "assistant", "content": stock_info}
        ]
    elif stock_data and "error" in stock_data:
        error_message = stock_data["error"]
        
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message},
            {"role": "assistant", "content": f"주식 데이터를 가져오는 중 문제가 발생했습니다: {error_message}"}
        ]
    else:
        llm_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": last_message}
        ]
    
    # AI 응답 생성
    response = llm.invoke(llm_messages)
    
    # 주식 차트가 있으면 응답에 추가
    if stock_data and "chart_image" in stock_data and "error" not in stock_data:
        chart_markdown = f"\n\n![{stock_data.get('ticker')} 주가 차트]({stock_data['chart_image']})"
        response_content = response.content + chart_markdown
    else:
        response_content = response.content
    
    # 새 메시지 추가
    new_messages = [("assistant", response_content)]
    
    return {"messages": new_messages}
