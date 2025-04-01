from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

class StockScreenerNode:
    """주식 스크리닝 노드"""
    
    def __init__(self, llm, yahoo_finance_tool):
        """
        주식 스크리닝 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
            yahoo_finance_tool: 야후 파이낸스 MCP 도구
        """
        self.llm = llm
        self.yahoo_finance_tool = yahoo_finance_tool
    
    def screen_stocks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        주식 스크리닝 노드의 메인 실행 메서드
        
        Args:
            state: 현재 그래프의 상태 딕셔너리
        
        Returns:
            업데이트된 상태 딕셔너리
        """
        # 1. 주식 스크리닝 수행
        screened_stocks = self._screen_stocks(state)
        
        # 2. LLM을 사용한 추가 필터링 및 순위 지정
        final_stock_picks = self._filter_stocks_with_llm(state, screened_stocks)
        
        # 3. 상태 업데이트
        return {
            **state,
            "stock_candidates": final_stock_picks
        }
    
    def _screen_stocks(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        주식 스크리닝 수행
        
        이전 노드에서 분석한 시장 상태와 강세 섹터 정보를 활용해
        야후 파이낸스 API로 주식을 스크리닝합니다.
        """
        try:
            # 시장 상태 및 강세 섹터 정보 가져오기
            market_condition = state.get("market_analysis", {}).get("market_condition", "unknown")
            strong_sectors = state.get("sector_analysis", {}).get("strong_sectors", [])
            
            # 사용자 프로필 정보
            user_profile = state.get("user_profile", {})
            risk_preference = user_profile.get("risk_preference", 5)
            investment_period = user_profile.get("investment_period", "중기 (1-6개월)")
            
            # 기술적/기본적 점수 최소값 설정 (리스크 선호도에 따라 조정)
            min_technical_score = 70 - (risk_preference - 5) * 5  # 리스크 선호도가 높을수록 낮은 점수도 허용
            min_fundamental_score = 70 - (risk_preference - 5) * 3  # 기본적 분석은 덜 완화
            
            # 시장 상태에 따른 스크리닝 전략 조정
            if market_condition == "bear_market":
                # 약세장에서는 더 보수적인 기준 적용
                min_technical_score += 5
                min_fundamental_score += 5
            
            # 섹터 필터 설정
            sector_filter = strong_sectors[0] if strong_sectors else ""
            
            # 야후 파이낸스 API를 통한 주식 스크리닝
            screening_results = self.yahoo_finance_tool.screen_stocks(
                market_cap="large",  # 대형주 기본값
                sector=sector_filter,
                min_technical_score=min_technical_score,
                min_fundamental_score=min_fundamental_score,
                max_results=10  # 최대 10개 종목
            )
            
            return screening_results.get("results", [])
            
        except Exception as e:
            # 오류 발생 시 빈 리스트 반환
            print(f"Stock screening error: {e}")
            return []
    
    def _filter_stocks_with_llm(self, state: Dict[str, Any], screened_stocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """LLM을 사용하여 스크리닝된 주식을 필터링하고 순위 지정"""
        # 이전 분석 결과 가져오기
        market_analysis = state.get("market_analysis", {}).get("analysis", "")
        sector_analysis = state.get("sector_analysis", {}).get("analysis", "")
        
        # 스크리닝된 주식 정보 요약
        stocks_info = []
        for stock in screened_stocks:
            symbol = stock.get("symbol", "")
            name = stock.get("name", "")
            sector = stock.get("sector", "")
            price = stock.get("price", 0)
            change = stock.get("change_percent", 0)
            tech_score = stock.get("technical_score", 0)
            fund_score = stock.get("fundamental_score", 0)
            combined_score = stock.get("combined_score", 0)
            
            stocks_info.append(f"{symbol} ({name}): ${price:.2f} ({change:+.2f}%), 섹터: {sector}, 기술점수: {tech_score}, 기본점수: {fund_score}, 종합점수: {combined_score:.1f}")
        
        stocks_summary = "\n".join(stocks_info)
        
        # 사용자 프로필 요약
        user_profile = state.get("user_profile", {})
        risk_profile = user_profile.get("risk_preference", 5)
        risk_text = "보수적" if risk_profile <= 3 else "공격적" if risk_profile >= 8 else "중립적"
        
        investment_period = user_profile.get("investment_period", "중기 (1-6개월)")
        investment_goal = user_profile.get("investment_goal", "균형")
        
        # LLM에 보낼 메시지 준비
        messages = [
            SystemMessage(content="당신은 주식 선별 전문가입니다. 시장 상황, 섹터 분석, 사용자 프로필을 고려하여 최적의 주식을 선택하세요."),
            HumanMessage(content=f"""
            # 주식 필터링 작업
            
            ## 스크리닝된 주식 목록
            {stocks_summary}
            
            ## 시장 분석 요약
            {market_analysis}
            
            ## 섹터 분석 요약
            {sector_analysis}
            
            ## 사용자 프로필
            위험 선호도: {risk_profile}/10 ({risk_text})
            투자 기간: {investment_period}
            투자 목적: {investment_goal}
            
            ## 사용자 질문/요청
            {state.get("user_input", "")}
            
            ---
            
            위 내용을 바탕으로 현재 시장 상황과 사용자 프로필에 가장 적합한 종목을 선별하세요:
            
            1. 주식 목록에서 상위 3-5개 종목을 선택하세요.
            2. 각 종목별로 선택한 이유를 1-2문장으로 간략히 설명하세요.
            3. 결과를 JSON 형식으로 반환하세요: 
               {{"top_stocks": [
                   {{"symbol": "SYMBOL", "name": "Name", "reason": "선택 이유"}},
                   ...
               ]}}
            """)
        ]
        
        # LLM 호출
        try:
            response = self.llm.invoke(messages)
            
            # JSON 파싱 시도 (LLM의 응답이 JSON 형식일 것으로 예상)
            import json
            return json.loads(response.content).get("top_stocks", [])
        except Exception as e:
            print(f"LLM filtering error: {e}")
            # 오류 발생 시 원본 스크리닝 결과의 상위 3개 반환
            return screened_stocks[:3]

    @classmethod
    def create_node(cls, llm, yahoo_finance_tool):
        """
        LangGraph 노드 생성을 위한 클래스 메서드
        
        Args:
            llm: 사용할 언어 모델
            yahoo_finance_tool: 야후 파이낸스 도구
        
        Returns:
            노드 함수
        """
        screener = cls(llm, yahoo_finance_tool)
        return screener.screen_stocks