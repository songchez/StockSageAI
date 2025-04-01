"""
투자 전략 조언 노드

이전 분석 결과를 종합하여 구체적인 투자 전략을 수립하는 LangGraph 노드입니다.
진입점, 목표가, 손절가, 투자 비중 등을 제안합니다.
"""
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from .graph_state import InvestmentState, NodeOutput


class StrategyAdvisorNode:
    """투자 전략 조언 노드"""
    
    def __init__(self, llm, yahoo_finance_tool):
        """
        투자 전략 조언 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
            yahoo_finance_tool: 야후 파이낸스 MCP 도구
        """
        self.llm = llm
        self.yahoo_finance_tool = yahoo_finance_tool
    
    def _get_support_resistance_levels(self, symbol: str) -> Dict[str, Any]:
        """특정 종목의 지지/저항 수준 분석"""
        try:
            # 실제 구현에서는 야후 파이낸스 데이터를 분석하여 지지/저항선 계산
            # 여기서는 예시 데이터 반환
            historical_data = self.yahoo_finance_tool.get_historical_data(symbol, period="6mo")
            
            # 현재 가격
            current_price = 0
            if historical_data.get("data"):
                current_price = historical_data["data"][-1].get("Close", 0)
            
            # 예시 지지/저항선 (실제로는 알고리즘으로 계산)
            support_levels = [
                current_price * 0.95,
                current_price * 0.92,
                current_price * 0.88
            ]
            
            resistance_levels = [
                current_price * 1.05,
                current_price * 1.08,
                current_price * 1.12
            ]
            
            return {
                "current_price": current_price,
                "support_levels": support_levels,
                "resistance_levels": resistance_levels
            }
            
        except Exception as e:
            # 오류 발생 시 기본 데이터 반환
            return {"error": str(e)}
    
    def _create_investment_strategy(self, state: InvestmentState) -> Dict[str, Any]:
        """모든 분석 결과를 종합하여 투자 전략 수립"""
        # 시장 및 섹터 분석 정보
        market_analysis = state.market_analysis
        market_condition = market_analysis.get("market_condition", "unknown")
        
        sector_analysis = state.sector_analysis
        strong_sectors = sector_analysis.get("strong_sectors", [])
        
        # 선별된 종목 정보
        screened_stocks = state.screened_stocks
        
        # 특정 종목 분석 결과 (있는 경우)
        stock_analysis = state.stock_analysis
        
        # 사용자 프로필
        user_profile = state.user_profile
        risk_preference = user_profile.get("risk_preference", 5)
        investment_period = user_profile.get("investment_period", "중기 (1-6개월)")
        investment_amount = user_profile.get("investment_amount", 10000)
        
        # 투자 전략 수립을 위한 기본 정보 준비
        stocks_info = []
        
        # 특정 종목 분석 결과가 있는 경우
        if stock_analysis:
            symbol = stock_analysis.get("symbol", "")
            name = stock_analysis.get("name", "")
            price = stock_analysis.get("price", 0)
            
            # 지지/저항 레벨 가져오기
            levels = self._get_support_resistance_levels(symbol)
            
            # 타겟 종목 정보 추가
            stocks_info.append({
                "symbol": symbol,
                "name": name,
                "price": price,
                "analysis": stock_analysis.get("analysis", ""),
                "recommendation": stock_analysis.get("recommendation", "중립"),
                "support_levels": levels.get("support_levels", []),
                "resistance_levels": levels.get("resistance_levels", [])
            })
        
        # 스크리닝된 종목들 정보
        elif screened_stocks:
            for stock in screened_stocks[:3]:  # 상위 3개만 처리
                symbol = stock.get("symbol", "")
                name = stock.get("name", "")
                price = stock.get("price", 0)
                
                # 지지/저항 레벨 가져오기
                levels = self._get_support_resistance_levels(symbol)
                
                # 종목 정보 추가
                stocks_info.append({
                    "symbol": symbol,
                    "name": name,
                    "price": price,
                    "technical_score": stock.get("technical_score", 0),
                    "fundamental_score": stock.get("fundamental_score", 0),
                    "support_levels": levels.get("support_levels", []),
                    "resistance_levels": levels.get("resistance_levels", [])
                })


# 투자 전략 프롬프트 구성
        stocks_summary = ""
        for idx, stock in enumerate(stocks_info, 1):
            symbol = stock.get("symbol", "")
            name = stock.get("name", "")
            price = stock.get("price", 0)
            
            supports = [f"${level:.2f}" for level in stock.get("support_levels", [])]
            resistances = [f"${level:.2f}" for level in stock.get("resistance_levels", [])]
            
            stocks_summary += f"""
            {idx}. {symbol} ({name}) - 현재 가격: ${price:.2f}
               - 지지선: {', '.join(supports)}
               - 저항선: {', '.join(resistances)}
            """
            
            # 특정 종목 분석이 있으면 추가
            if "analysis" in stock:
                stocks_summary += f"   - 분석 요약: {stock.get('recommendation')}\n"
            else:
                stocks_summary += f"   - 기술점수: {stock.get('technical_score')}, 기본점수: {stock.get('fundamental_score')}\n"
        
        # 투자 전략 프롬프트
        prompt = f"""
        # 투자 전략 수립 작업
        
        ## 시장 상황
        - 시장 상태: {market_condition}
        - 강세 섹터: {', '.join(strong_sectors)}
        
        ## 대상 종목
        {stocks_summary}
        
        ## 사용자 프로필
        - 위험 선호도: {risk_preference}/10
        - 투자 기간: {investment_period}
        - 투자 가능 금액: ${investment_amount:,}
        
        ## 사용자 질문/요청
        {state.user_input}
        
        ---
        
        당신은 투자 전략 전문가로서, 위 정보를 바탕으로 구체적인 투자 전략을 수립해야 합니다:
        
        1. 현재 시장 상황({market_condition})에서 가장 적합한 전반적인 투자 접근법(공격적/방어적/선별적)을 추천하고, 1-2문장으로 설명하세요.
        
        2. 각 종목별로 다음 정보를 포함한 구체적인 투자 전략을 제시하세요:
           - **진입 전략**: 적정 매수 가격 또는 가격대, 진입 방식(즉시, 지정가, 분할매수 등)
           - **목표가**: 1차, 2차 목표가(상승여력 %와 함께)
           - **손절가**: 명확한 손절매 가격(하락위험 %와 함께)
           - **투자 비중**: 전체 포트폴리오에서 차지할 비중(%)
           - **보유 기간**: 예상 보유 기간
        
        3. 종목별 투자 우선순위를 정하고, 각각에 대한 매력도를 상/중/하로 평가하세요.
        
        4. 현재 시장 상황에서 고려해야 할 주요 위험 요소와 이에 대한 대응 방안을 2-3가지 제시하세요.
        
        5. 투자 모니터링 계획: 각 종목의 주요 체크포인트와 재평가 시점을 제안하세요.
        
        전략은 명확하고 실행 가능하며, 사용자의 위험 선호도와 투자 기간에 적합해야 합니다. 투자 금액을 고려한 현실적인 조언을 제공하세요.
        """
        
        # LLM 호출
        messages = [
            SystemMessage(content="당신은 투자 전략 전문가로서, 시장 분석과 주식 분석을 바탕으로 구체적이고 실행 가능한 투자 전략을 수립합니다. 명확하고 실용적인 조언으로 투자자가 바로 행동으로 옮길 수 있도록 안내하세요."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        strategy_text = response.content
        
        # 결과 반환
        return {
            "market_condition": market_condition,
            "strategy": strategy_text,
            "stocks": stocks_info
        }
    
    def __call__(self, state: InvestmentState) -> NodeOutput:
        """
        노드 실행 함수
        
        Args:
            state: 현재 그래프 상태
            
        Returns:
            업데이트된 상태와 다음 노드
        """
        # 상태 복사
        new_state = state.copy()
        
        try:
            # 이전 노드 결과 확인
            if not new_state.market_analysis:
                raise ValueError("시장 분석 결과가 없습니다. 먼저 분석을 수행해야 합니다.")
            
            # 종목 정보 확인 (개별 분석 또는 스크리닝 결과 중 하나는 있어야 함)
            if not new_state.stock_analysis and not new_state.screened_stocks:
                raise ValueError("분석할 종목 정보가 없습니다.")
            
            # 1. 투자 전략 수립
            strategy = self._create_investment_strategy(new_state)
            
            # 2. 전략 결과를 상태에 저장
            new_state.investment_strategy = strategy
            
            # 3. 메시지에 전략 결과 추가
            new_state.messages.append({
                "role": "strategy_advisor",
                "content": "투자 전략 수립 완료"
            })
            
            # 4. 다음 노드로 이동 - 최종 결과 컴파일러
            new_state.current_node = "result_compiler"
            
            return {"state": new_state, "next": "result_compiler"}
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 추가 및 종료
            new_state.errors.append(f"투자 전략 수립 오류: {str(e)}")
            new_state.current_node = "error"
            
            return {"state": new_state, "next": "error"}