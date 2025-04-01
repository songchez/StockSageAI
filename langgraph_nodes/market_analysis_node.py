"""
시장 분석 노드

전체 시장 상황을 분석하는 LangGraph 노드입니다.
야후 파이낸스에서 시장 데이터를 가져오고, LLM에 프롬프팅하여 시장 상태를 파악합니다.
"""
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from .graph_state import InvestmentState, MarketCondition, NodeOutput


class MarketAnalystNode:
    """시장 분석 노드"""
    
    def __init__(self, llm, yahoo_finance_tool):
        """
        시장 분석 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
            yahoo_finance_tool: 야후 파이낸스 MCP 도구
        """
        self.llm = llm
        self.yahoo_finance_tool = yahoo_finance_tool
    
    def _fetch_market_data(self) -> Dict[str, Any]:
        """야후 파이낸스에서 시장 데이터 가져오기"""
        try:
            # 시장 상태, 주요 지수, 경제 지표 데이터 가져오기
            market_status = self.yahoo_finance_tool.get_market_status()
            
            # 실제 구현에서는 다음과 같은 추가 정보도 가져올 수 있음
            # market_trends = self.yahoo_finance_tool.get_historical_market_data(days=30)
            # economic_indicators = self.yahoo_finance_tool.get_economic_indicators()
            
            return market_status
        except Exception as e:
            # 오류 발생 시 기본 데이터 반환
            return {
                "error": str(e),
                "indices": {
                    "S&P 500": {"price": 0, "change": 0},
                    "NASDAQ": {"price": 0, "change": 0},
                    "DOW": {"price": 0, "change": 0}
                },
                "market_status": {
                    "overall_status": "unknown"
                }
            }
    
    def _analyze_market_with_llm(self, state: InvestmentState) -> Dict[str, Any]:
        """LLM을 사용하여 시장 데이터 분석"""
        market_data = state.raw_market_data
        
        # LLM에게 제공할 시장 정보 요약
        indices_info = []
        for name, data in market_data.get("indices", {}).items():
            price = data.get("price", 0)
            change = data.get("change", 0)
            indices_info.append(f"{name}: {price} ({change:+.2f}%)")
        
        indices_summary = "\n".join(indices_info)
        
        # 시장 상태 분석 프롬프트
        market_status = market_data.get("market_status", {}).get("overall_status", "unknown")
        
        prompt = f"""
        # 시장 분석 작업
        
        ## 현재 시장 데이터
        {indices_summary}
        
        ## 시장 상태 정보
        전체 상태: {market_status}
        
        ## 사용자 정보
        투자 성향: {state.user_profile.get('risk_preference', '정보 없음')}
        투자 기간: {state.user_profile.get('investment_period', '정보 없음')}
        
        ## 사용자 질문/요청
        {state.user_input}
        
        ---
        
        당신은 전문 주식 투자 AI로서, 위 시장 데이터를 전체적으로 분석하고 다음 정보를 제공해야 합니다:
        
        1. 현재 시장이 강세장(bull_market), 약세장(bear_market), 횡보장(sideways_market) 중 어떤 상태인지 판단하고, 그 이유를 간략히 설명하세요.
        
        2. 이러한 시장 상황에서 일반적인 투자 접근법(공격적, 방어적, 선별적)을 제안하세요.
        
        3. 사용자의 투자 성향과 투자 기간을 고려하여, 현재 시장 상황에 맞는 2-3문장의 투자 전략을 제시하세요.
        
        4. 현재 시장 상황에 대한 3가지 핵심 위험 요소와 3가지 기회 요소를 간략히 나열하세요.
        
        각 항목에 대해 명확하고 간결하게 응답해주세요.
        """
        
        # LLM 호출
        messages = [
            SystemMessage(content="당신은 주식 시장 분석 전문가로서, 현재 시장 데이터를 분석하고 시장 상태를 판단합니다. 객관적이고 사실에 기반한 분석을 제공하세요."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # 결과 파싱 (실제 구현에서는 더 정교한 파싱 로직을 사용할 수 있음)
        analysis_text = response.content
        
        # 시장 상태 결정 (기본값은 야후 파이낸스 데이터 사용)
        market_condition = market_status
        
        # 응답에서 시장 상태 키워드를 찾아 결정
        if "강세장" in analysis_text or "bull_market" in analysis_text:
            market_condition = "bull_market"
        elif "약세장" in analysis_text or "bear_market" in analysis_text:
            market_condition = "bear_market"
        elif "횡보장" in analysis_text or "sideways_market" in analysis_text:
            market_condition = "sideways_market"
        
        return {
            "market_condition": market_condition,
            "analysis": analysis_text,
            "indices_data": market_data.get("indices", {})
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
            # 1. 야후 파이낸스에서 시장 데이터 가져오기
            market_data = self._fetch_market_data()
            
            # 2. 원시 데이터를 상태에 저장 (다른 노드가 재사용할 수 있도록)
            new_state.raw_market_data = market_data
            
            # 3. LLM으로 시장 분석 수행
            market_analysis = self._analyze_market_with_llm(new_state)
            
            # 4. 분석 결과를 상태에 저장
            new_state.market_analysis = market_analysis
            
            # 5. 메시지에 분석 결과 추가
            new_state.messages.append({
                "role": "market_analyst",
                "content": f"시장 분석 완료: {market_analysis.get('market_condition')}"
            })
            
            # 6. 다음 노드 결정
            new_state.current_node = "sector_analyst"
            
            return {"state": new_state, "next": "sector_analyst"}
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 추가 및 종료
            new_state.errors.append(f"시장 분석 오류: {str(e)}")
            new_state.current_node = "error"
            
            return {"state": new_state, "next": "error"}