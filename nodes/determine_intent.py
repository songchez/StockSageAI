from graph_state import State

# 사용자 의도 파악 노드
def determine_intent(state: State) -> State:
    '''판단하는 함수'''
    messages = state["messages"]
    last_message = messages[-1].content
    
    # 투자, 주식, 종목, 분석 등의 키워드가 있는지 확인
    investment_keywords = ["투자", "주식", "종목", "분석", "stock", "invest", "market", "주가", "price"]
    stock_analysis_needed = any(keyword in last_message.lower() for keyword in investment_keywords)
    return {"stock_analysis_needed": stock_analysis_needed}

# 라우팅 함수 - 주식 분석이 필요한지 여부에 따라 경로 결정
def router(state: State):
    if state["stock_analysis_needed"]:
        return "technical_analysis"
    else:
        return "superviser"