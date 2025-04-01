"""
결과 컴파일러 노드

모든 분석 결과를 종합하여 최종 답변을 생성하는 LangGraph 노드입니다.
사용자 쿼리 유형에 따라 적절한 형식으로 응답을 구성합니다.
"""
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from .graph_state import InvestmentState, NodeOutput


class ResultCompilerNode:
    """결과 컴파일러 노드"""
    
    def __init__(self, llm):
        """
        결과 컴파일러 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
        """
        self.llm = llm
    
    def _compile_final_answer(self, state: InvestmentState) -> str:
        """
        모든 분석 결과를 종합하여 최종 응답 생성
        
        Args:
            state: 현재 그래프 상태
            
        Returns:
            최종 응답 텍스트
        """
        # 쿼리 유형 확인
        query_type = state.user_query_type
        
        # 분석 결과 가져오기
        market_analysis = state.market_analysis.get("analysis", "") if state.market_analysis else ""
        sector_analysis = state.sector_analysis.get("analysis", "") if state.sector_analysis else ""
        
        # 종목 분석 결과 (개별 분석 또는 스크리닝 결과)
        stock_info = ""
        if state.stock_analysis:
            stock_analysis = state.stock_analysis
            symbol = stock_analysis.get("symbol", "")
            name = stock_analysis.get("name", "")
            recommendation = stock_analysis.get("recommendation", "")
            analysis = stock_analysis.get("analysis", "")
            
            stock_info = f"""
            개별 종목 분석 결과:
            {symbol} ({name}) - 추천: {recommendation}
            {analysis}
            """
        elif state.screened_stocks:
            stock_list = []
            for stock in state.screened_stocks:
                symbol = stock.get("symbol", "")
                name = stock.get("name", "")
                tech_score = stock.get("technical_score", 0)
                fund_score = stock.get("fundamental_score", 0)
                
                stock_list.append(f"{symbol} ({name}) - 기술점수: {tech_score}, 기본점수: {fund_score}")
            
            stock_info = "선별된 종목 목록:\n" + "\n".join(stock_list)
        
        # 투자 전략
        strategy = state.investment_strategy.get("strategy", "") if state.investment_strategy else ""
        
        # 프롬프트 구성 - 쿼리 유형에 따라 다른 지침 제공
        if query_type == "market":
            # 시장 상황에 대한 질문
            focus = "시장 분석에 중점을 두고, 현재 시장 상황과 투자자가 고려해야 할 사항을 중심으로 답변하세요."
        elif query_type == "sector":
            # 섹터 분석에 대한 질문
            focus = "섹터 분석에 중점을 두고, 현재 강세/약세 섹터와 섹터 로테이션 관점에서의 투자 기회를 중심으로 답변하세요."
        elif query_type == "specific_stock":
            # 특정 종목에 대한 질문
            focus = "해당 종목 분석에 중점을 두고, 종목의 현재 기술적/기본적 상태, 투자 적합성, 매수/매도 전략을 중심으로 답변하세요."
        elif query_type == "strategy":
            # 투자 전략에 대한 질문
            focus = "투자 전략에 중점을 두고, 현재 시장 상황에 맞는 구체적인 투자 접근법, 종목 선택, 자산 배분, 진입/퇴출 전략을 중심으로 답변하세요."
        else:
            # 일반적인 질문
            focus = "사용자의 질문에 가장 적합한 정보를 중심으로 답변하세요. 시장 상황, la 종목 추천, 투자 전략 등 관련된 모든 정보를 균형 있게 포함시키세요."
        
        # 최종 응답 생성 프롬프트
        prompt = f"""
        # 투자 자문 최종 답변 작성
        
        ## 사용자 질문/요청
        {state.user_input}
        
        ## 분석 데이터
        
        ### 시장 분석
        {market_analysis}
        
        ### 섹터 분석
        {sector_analysis}
        
        ### 종목 정보
        {stock_info}
        
        ### 투자 전략
        {strategy}
        
        ---
        
        당신은 주식투자 AI 어시스턴트로서, 위 분석 결과를 바탕으로 사용자의 질문에 명확하고 유용한 최종 답변을 작성해야 합니다.
        
        ## 답변 지침
        - {focus}
        - 모든 주요 분석 결과를 통합하여 일관되고 논리적인 답변을 구성하세요.
        - 실행 가능한 구체적인 조언을 제공하세요 (관련 있는 경우).
        - 시장 분석, 종목 추천, 투자 전략에 관한 핵심 정보를 명확하게 제시하세요.
        - 투자의 위험성을 언급하고, 모든 투자 결정은 사용자 본인의 판단에 따라야 함을 상기시키세요.
        - 필요한 경우 명료한 리스트나 표 형식을 사용하여 정보를 구조화하세요.
        - 사용자에게 실질적인 가치를 제공하는 답변을 작성하세요.
        
        답변은 자연스럽고 대화체로 작성하되, 전문성을 유지하세요. 불필요한 소개 문구나 결론을 반복하지 말고, 핵심 내용에 집중하세요.
        """
        
        # LLM 호출
        messages = [
            SystemMessage(content="당신은 StockSage AI라는 주식투자 AI 어시스턴트로서, 사용자의 투자 의사결정을 돕기 위한 분석과 조언을 제공합니다. 항상 유용하고 명확하며 실행 가능한 조언을 제공하되, 투자에는 위험이 따름을 알려주세요."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        
        return response.content
    
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
            # 최종 응답 생성
            final_answer = self._compile_final_answer(new_state)
            
            # 결과를 상태에 저장
            new_state.final_answer = final_answer
            
            # 메시지에 결과 추가
            new_state.messages.append({
                "role": "result_compiler",
                "content": "최종 응답이 준비되었습니다."
            })
            
            # 종료 노드로 이동
            new_state.current_node = "end"
            
            return {"state": new_state, "next": "end"}
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 추가 및 종료
            new_state.errors.append(f"결과 컴파일 오류: {str(e)}")
            new_state.current_node = "error"
            
            return {"state": new_state, "next": "error"}