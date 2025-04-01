"""
섹터 분석 노드

시장 내 다양한 섹터를 분석하고 강세 섹터를 식별하는 LangGraph 노드입니다.
시장 분석 노드의 결과를 활용하여 섹터 분석을 진행합니다.
"""
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from .graph_state import InvestmentState, NodeOutput


class SectorAnalystNode:
    """섹터 분석 노드"""
    
    def __init__(self, llm, yahoo_finance_tool):
        """
        섹터 분석 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
            yahoo_finance_tool: 야후 파이낸스 MCP 도구
        """
        self.llm = llm
        self.yahoo_finance_tool = yahoo_finance_tool
    
    def _fetch_sector_data(self) -> Dict[str, Any]:
        """야후 파이낸스에서 섹터 데이터 가져오기"""
        try:
            # 섹터 성과, 섹터 로테이션 데이터 가져오기
            sector_performance = self.yahoo_finance_tool.get_sector_performance(timeframe="1m")
            
            # 실제 구현에서는 다음과 같은 추가 정보도 가져올 수 있음
            # sector_rotation = self.yahoo_finance_tool.analyze_sector_rotation()
            # sector_fundamentals = self.yahoo_finance_tool.get_sector_fundamentals()
            
            return sector_performance
        except Exception as e:
            # 오류 발생 시 기본 데이터 반환
            return {
                "error": str(e),
                "sectors": {
                    "Technology": {"performance": 0},
                    "Healthcare": {"performance": 0},
                    "Financial": {"performance": 0},
                    "Energy": {"performance": 0},
                    "Consumer": {"performance": 0}
                },
                "market_performance": 0
            }
    
    def _analyze_sectors_with_llm(self, state: InvestmentState) -> Dict[str, Any]:
        """LLM을 사용하여 섹터 데이터 분석"""
        sector_data = state.raw_sector_data
        market_analysis = state.market_analysis
        market_condition = market_analysis.get("market_condition", "unknown")
        
        # LLM에게 제공할 섹터 정보 요약
        sector_info = []
        for name, data in sector_data.get("sectors", {}).items():
            performance = data.get("performance", 0)
            momentum = data.get("momentum", "neutral")
            top_performers = ", ".join(data.get("top_performers", []))
            sector_info.append(f"{name}: {performance:+.2f}% (모멘텀: {momentum}, 상위 종목: {top_performers})")
        
        sector_summary = "\n".join(sector_info)
        
        # 사용자 선호 섹터 확인
        preferred_sectors = state.user_profile.get("preferred_sectors", [])
        preferred_sectors_str = ", ".join(preferred_sectors) if preferred_sectors else "없음"
        
        # 섹터 분석 프롬프트
        prompt = f"""
        # 섹터 분석 작업
        
        ## 시장 분석 결과
        시장 상태: {market_condition}
        시장 분석: {market_analysis.get('analysis', '정보 없음')}
        
        ## 섹터 성과 데이터
        {sector_summary}
        
        ## 시장 평균 성과
        시장 평균: {sector_data.get('market_performance', 0):+.2f}%
        
        ## 사용자 정보
        선호 섹터: {preferred_sectors_str}
        투자 성향: {state.user_profile.get('risk_preference', '정보 없음')}
        투자 목적: {state.user_profile.get('investment_goal', '정보 없음')}
        
        ## 사용자 질문/요청
        {state.user_input}
        
        ---
        
        당신은 섹터 분석 전문가로서, 위 데이터를 분석하고 다음 정보를 제공해야 합니다:
        
        1. 현재 가장 강세를 보이는 상위 3개 섹터와 약세를 보이는 하위 2개 섹터를 선정하고, 각각에 대한 간략한 이유를 설명하세요.
        
        2. 현재 시장 상태({market_condition})에서 투자하기 적합한 섹터를 3개 추천하고, 각각에 대한 이유를 1-2문장으로 설명하세요.
        
        3. 사용자의 선호 섹터, 투자 성향, 투자 목적을 고려하여 가장 적합한 섹터 2개를 추천하세요.
        
        4. 섹터 로테이션 관점에서 향후 3-6개월 내 강세가 예상되는 섹터 2개를 예측하고 그 이유를 설명하세요.
        
        각 항목에 대해 명확하고 간결하게 응답해주세요.
        """
        
        # LLM 호출
        messages = [
            SystemMessage(content="당신은 주식 시장의 섹터 분석 전문가로서, 현재 섹터별 성과와 추세를 분석하고 투자에 적합한 섹터를 추천합니다. 객관적인 데이터에 기반하여 분석하세요."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        # 간단한 결과 파싱
        analysis_text = response.content
        
        # 강세 섹터 추출 (실제로는 더 정교한 파싱이 필요할 수 있음)
        strong_sectors = []
        sectors = sector_data.get("sectors", {})
        
        # 성과 기준으로 정렬
        sorted_sectors = sorted(
            [(name, data.get("performance", 0)) for name, data in sectors.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # 상위 3개 섹터 추출
        strong_sectors = [name for name, _ in sorted_sectors[:3]]
        
        return {
            "strong_sectors": strong_sectors,
            "analysis": analysis_text,
            "sorted_sectors": sorted_sectors
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
            # 이전 노드의 결과 확인
            if not new_state.market_analysis:
                raise ValueError("시장 분석 결과가 없습니다. 시장 분석을 먼저 수행해야 합니다.")
            
            # 1. 야후 파이낸스에서 섹터 데이터 가져오기
            sector_data = self._fetch_sector_data()
            
            # 2. 원시 데이터를 상태에 저장 (다른 노드가 재사용할 수 있도록)
            new_state.raw_sector_data = sector_data
            
            # 3. LLM으로 섹터 분석 수행
            sector_analysis = self._analyze_sectors_with_llm(new_state)
            
            # 4. 분석 결과를 상태에 저장
            new_state.sector_analysis = sector_analysis
            
            # 5. 메시지에 분석 결과 추가
            strong_sectors = ", ".join(sector_analysis.get("strong_sectors", []))
            new_state.messages.append({
                "role": "sector_analyst",
                "content": f"섹터 분석 완료: 강세 섹터는 {strong_sectors}"
            })
            
            # 6. 다음 노드 결정 - 사용자 질문 유형에 따라 분기
            if state.user_query_type == "sector":
                # 섹터 관련 질문인 경우 바로 결과 노드로
                new_state.current_node = "result_compiler"
                return {"state": new_state, "next": "result_compiler"}
            else:
                # 그 외의 경우 주식 스크리닝 노드로
                new_state.current_node = "stock_screener"
                return {"state": new_state, "next": "stock_screener"}
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 추가 및 종료
            new_state.errors.append(f"섹터 분석 오류: {str(e)}")
            new_state.current_node = "error"
            
            return {"state": new_state, "next": "error"}