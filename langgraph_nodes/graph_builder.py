"""
투자 의사결정 그래프 빌더

LangGraph를 사용하여 주식투자 의사결정 그래프를 구성합니다.
모든 노드를 연결하고 워크플로우를 정의합니다.
"""
from langgraph.graph import StateGraph, END
from .graph_state import InvestmentState
from .market_analysis_node import MarketAnalystNode
from .sector_analysis_node import SectorAnalystNode
from .stock_screening_node import StockScreenerNode
from .stock_analysis_node import StockAnalystNode
from .strategy_advisor_node import StrategyAdvisorNode
from .result_compiler_node import ResultCompilerNode


def build_investment_graph(
    llm,
    yahoo_finance_tool
) -> StateGraph:
    """
    주식투자 의사결정 그래프 구성
    
    Args:
        llm: LLM 모델 (예: ChatAnthropic)
        yahoo_finance_tool: 야후 파이낸스 MCP 도구
        
    Returns:
        StateGraph: 구성된 LangGraph
    """
    # 노드 인스턴스 생성
    market_analyst = MarketAnalystNode(llm, yahoo_finance_tool)
    sector_analyst = SectorAnalystNode(llm, yahoo_finance_tool)
    stock_screener = StockScreenerNode(llm, yahoo_finance_tool)
    stock_analyst = StockAnalystNode(llm, yahoo_finance_tool)
    strategy_advisor = StrategyAdvisorNode(llm, yahoo_finance_tool)
    result_compiler = ResultCompilerNode(llm)
    
    # 그래프 초기화
    graph = StateGraph(InvestmentState)
    
    # 노드 추가
    graph.add_node("market_analyst", market_analyst)
    graph.add_node("sector_analyst", sector_analyst)
    graph.add_node("stock_screener", stock_screener)
    graph.add_node("stock_analyst", stock_analyst)
    graph.add_node("strategy_advisor", strategy_advisor)
    graph.add_node("result_compiler", result_compiler)
    
    # 에지 정의 (노드 간 전환 규칙)
    
    # 시작 노드 (무조건 시장 분석부터 시작)
    graph.set_entry_point("market_analyst")
    
    # 시장 분석 → 섹터 분석
    graph.add_edge("market_analyst", "sector_analyst")
    
    # 섹터 분석 이후 분기
    graph.add_conditional_edges(
        "sector_analyst",
        # 조건 함수: 사용자 쿼리 유형에 따른 분기
        lambda state: state["state"].current_node
    )
    
    # 주식 스크리닝 이후 분기
    graph.add_conditional_edges(
        "stock_screener",
        # 조건 함수: 사용자 쿼리 유형에 따른 분기
        lambda state: state["state"].current_node
    )
    
    # 주식 분석 → 투자 전략
    graph.add_edge("stock_analyst", "strategy_advisor")
    
    # 투자 전략 → 결과 컴파일러
    graph.add_edge("strategy_advisor", "result_compiler")
    
    # 결과 컴파일러 → 종료
    graph.add_edge("result_compiler", END)
    
    # 오류 처리 노드 (모든 노드에서 오류 발생 시 종료)
    graph.add_edge("error", END)
    
    # 그래프 컴파일
    return graph.compile()


def query_classifier(user_input: str, llm) -> str:
    """
    사용자 쿼리 유형 분류 (이 함수는 그래프 외부에서 사용)
    
    Args:
        user_input: 사용자 입력 텍스트
        llm: LLM 모델
        
    Returns:
        쿼리 유형 (market, sector, specific_stock, strategy, general)
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    
    # 쿼리 분류 프롬프트
    prompt = f"""
    다음 사용자 질문을 분석하여 어떤 유형의 투자 관련 질문인지 분류하세요:
    
    사용자 질문: "{user_input}"
    
    다음 카테고리 중 하나를 선택하여 답변하세요:
    1. market - 전체 시장 상황이나 추세에 관한 질문
    2. sector - 특정 섹터나 산업군에 관한 질문
    3. specific_stock - 특정 주식이나 종목에 관한 질문
    4. strategy - 투자 전략이나 접근법에 관한 질문
    5. general - 위 카테고리에 명확히 속하지 않는 일반적인 투자 질문
    
    답변은 카테고리 이름만 작성하세요 (예: "market", "specific_stock" 등).
    """
    
    # LLM 호출
    messages = [
        SystemMessage(content="당신은 투자 관련 질문을 분류하는 전문가입니다. 사용자의 질문을 정확하게 분석하여 가장 적합한 카테고리로 분류하세요."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages)
    
    # 응답에서 카테고리 추출
    category = response.content.strip().lower()
    
    # 유효한 카테고리인지 확인
    valid_categories = ["market", "sector", "specific_stock", "strategy", "general"]
    if category in valid_categories:
        return category
    else:
        # 유효하지 않은 응답이면 일반(general) 카테고리로 처리
        return "general"