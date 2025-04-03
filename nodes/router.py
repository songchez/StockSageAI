from graph_state import State

# 라우팅 함수 - 주식 분석이 필요한지 여부에 따라 경로 결정
def router(state: State) -> str:
    if state["stock_analysis_needed"]:
        return "technical_analysis"
    else:
        return "generate_response"