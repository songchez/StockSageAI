"""
종목 분석 노드

선별된 종목 또는 사용자가 지정한 특정 종목에 대한 심층 분석을 수행하는 LangGraph 노드입니다.
기술적 분석과 기본적 분석을 결합하여 종합적인 투자 판단을 제공합니다.
"""
from typing import Dict, List, Any
from langchain_core.messages import SystemMessage, HumanMessage
from .graph_state import InvestmentState, NodeOutput


class StockAnalystNode:
    """종목 분석 노드"""
    
    def __init__(self, llm, yahoo_finance_tool):
        """
        종목 분석 노드 초기화
        
        Args:
            llm: LLM 모델 (예: ChatAnthropic)
            yahoo_finance_tool: 야후 파이낸스 MCP 도구
        """
        self.llm = llm
        self.yahoo_finance_tool = yahoo_finance_tool
    
    def _get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """야후 파이낸스에서 특정 종목의 상세 데이터 가져오기"""
        try:
            # 기본 종목 정보
            stock_data = self.yahoo_finance_tool.get_stock_data(symbol)
            
            # 기술적 분석 데이터
            technical_analysis = self.yahoo_finance_tool.get_technical_analysis(symbol)
            
            # 과거 가격 데이터 (차트용)
            historical_data = self.yahoo_finance_tool.get_historical_data(symbol, period="6mo")
            
            # 애널리스트 추천 정보
            recommendations = self.yahoo_finance_tool.get_recommendations(symbol)
            
            # 모든 데이터 통합
            combined_data = {
                "basic_info": stock_data,
                "technical": technical_analysis,
                "historical": historical_data,
                "recommendations": recommendations
            }
            
            return combined_data
            
        except Exception as e:
            # 오류 발생 시 기본 정보만 담은 데이터 반환
            return {"error": str(e), "symbol": symbol}
    
    def _analyze_stock_with_llm(self, state: InvestmentState, stock_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """LLM을 사용하여 종목 데이터 분석"""
        # 시장 및 섹터 분석 정보
        market_condition = state.market_analysis.get("market_condition", "unknown")
        
        # 기본 종목 정보 추출
        basic_info = stock_data.get("basic_info", {})
        name = basic_info.get("name", "")
        sector = basic_info.get("sector", "")
        industry = basic_info.get("industry", "")
        current_price = basic_info.get("current_price", 0)
        change_percent = basic_info.get("percent_change", 0)
        pe_ratio = basic_info.get("pe_ratio", 0)
        
        # 기술적 분석 정보 추출
        technical = stock_data.get("technical", {})
        technical_score = technical.get("technical_score", 0)
        
        # 지표 정보
        indicators = technical.get("indicators", {})
        trend_indicators = indicators.get("trend", {})
        momentum_indicators = indicators.get("momentum", {})
        
        # 신호 추출
        signals = technical.get("signals", [])
        signal_summary = []
        for signal in signals:
            signal_type = signal.get("type", "")
            signal_direction = signal.get("signal", "")
            signal_desc = signal.get("description", "")
            signal_summary.append(f"{signal_type} ({signal_direction}): {signal_desc}")
        
        signals_text = "\n".join(signal_summary) if signal_summary else "주요 신호 없음"
        
        # 애널리스트 추천 정보
        recommendations = stock_data.get("recommendations", {}).get("summary", {})
        avg_target = recommendations.get("avg_target", 0)
        target_upside = recommendations.get("target_upside", 0)
        
        # 사용자 프로필 정보
        risk_preference = state.user_profile.get("risk_preference", 5)
        investment_period = state.user_profile.get("investment_period", "중기 (1-6개월)")
        
        # 종목 분석 프롬프트
        prompt = f"""
        # 종목 분석 작업: {symbol} ({name})
        
        ## 기본 정보
        - 섹터: {sector}
        - 산업: {industry}
        - 현재 가격: ${current_price:.2f} ({change_percent:+.2f}%)
        - PER: {pe_ratio}
        
        ## 기술적 분석
        - 기술적 점수: {technical_score}/100
        - 20일 이동평균선 대비: {trend_indicators.get("price_vs_sma_20", 0):+.2f}%
        - 50일 이동평균선 대비: {trend_indicators.get("price_vs_sma_50", 0):+.2f}%
        - RSI: {momentum_indicators.get("rsi", 0):.1f} ({momentum_indicators.get("rsi_zone", "중립")})
        - MACD: {trend_indicators.get("macd_trend", "중립")}
        
        ## 기술적 신호
        {signals_text}
        
        ## 애널리스트 의견
        - 평균 목표가: ${avg_target:.2f} (상승여력: {target_upside:.2f}%)
        
        ## 시장 상황
        - 시장 상태: {market_condition}
        
        ## 사용자 프로필
        - 위험 선호도: {risk_preference}/10
        - 투자 기간: {investment_period}
        
        ---
        
        당신은 주식 분석 전문가로서, 위 데이터를 기반으로 {symbol} 종목에 대한 종합적인 분석과 투자 전략을 제시해야 합니다:
        
        1. 현재 이 종목의 기술적/기본적 강점과 약점을 각각 2-3가지씩 분석하세요.
        
        2. 현재 주가가 저평가/고평가/적정 평가 중 어떤 상태인지 판단하고, 그 이유를 설명하세요.
        
        3. 현재 시장 상황({market_condition})에서 이 종목에 투자하는 것이 적합한지 판단하고 이유를 설명하세요.
        
        4. 사용자의 위험 선호도({risk_preference}/10)와 투자 기간({investment_period})을 고려하여, 이 종목이 적합한지 판단하세요.
        
        5. 투자 권장 여부(강력 매수/매수/중립/매도/강력 매도)를 제시하고, 그 이유를 1-2문장으로 설명하세요.
        
        6. 투자하기로 결정했다면, 다음 정보를 제공하세요:
           - 적정 진입 가격 또는 가격대
           - 목표 가격 (상승 여력 %와 함께)
           - 손절매 가격 (하락 위험 %와 함께)
           - 투자 비중 제안 (전체 포트폴리오의 %)
           - 보유 기간 추천
        
        분석은 객관적이고 균형 잡힌 시각을 유지하며, 종목의 장점과 위험 요소를 모두 명확히 설명해주세요.
        """
        
        # LLM 호출
        messages = [
            SystemMessage(content="당신은 주식 분석 전문가로서, 기술적 분석과 기본적 분석을 결합하여 종합적인 투자 판단을 제공합니다. 객관적인 데이터에 기반하되, 현실적이고 실용적인 조언을 제공하세요."),
            HumanMessage(content=prompt)
        ]
        
        response = self.llm.invoke(messages)
        analysis_text = response.content
        
        # 종목 추천 등급 추출 (실제로는 더 정교한 파싱이 필요할 수 있음)
        recommendation = "중립"  # 기본값
        if "강력 매수" in analysis_text:
            recommendation = "강력 매수"
        elif "매수" in analysis_text:
            recommendation = "매수"
        elif "매도" in analysis_text:
            recommendation = "매도"
        elif "강력 매도" in analysis_text:
            recommendation = "강력 매도"
        
        # 결과 반환
        return {
            "symbol": symbol,
            "name": name,
            "analysis": analysis_text,
            "recommendation": recommendation,
            "technical_score": technical_score,
            "price": current_price,
            "target_price": avg_target
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
            # 분석할 종목 결정
            target_symbol = None
            
            # 사용자 쿼리가 특정 종목에 관한 것인지 확인
            if state.user_query_type == "specific_stock":
                # 사용자 입력에서 티커 심볼 추출 (실제 구현에서는 더 정교한 방법 필요)
                import re
                symbols = re.findall(r'[A-Z]{1,5}', state.user_input.upper())
                if symbols:
                    target_symbol = symbols[0]
            
            # 티커 심볼을 찾지 못했다면 스크리닝된 종목 중 첫 번째 사용
            if not target_symbol and state.screened_stocks:
                target_symbol = state.screened_stocks[0].get("symbol")
            
            # 여전히 종목이 없으면 오류
            if not target_symbol:
                raise ValueError("분석할 종목을 찾을 수 없습니다.")
            
            # 1. 야후 파이낸스에서 종목 데이터 가져오기
            stock_data = self._get_stock_data(target_symbol)
            
            # 2. 원시 데이터를 상태에 저장
            if target_symbol not in new_state.raw_stock_data:
                new_state.raw_stock_data[target_symbol] = stock_data
            
            # 3. LLM으로 종목 분석 수행
            stock_analysis = self._analyze_stock_with_llm(new_state, stock_data, target_symbol)
            
            # 4. 분석 결과를 상태에 저장
            new_state.stock_analysis = stock_analysis
            
            # 5. 메시지에 분석 결과 추가
            new_state.messages.append({
                "role": "stock_analyst",
                "content": f"{target_symbol} 분석 완료: 추천 등급은 {stock_analysis.get('recommendation')}"
            })
            
            # 6. 다음 노드로 이동 - 투자 전략 노드
            new_state.current_node = "strategy_advisor"
            
            return {"state": new_state, "next": "strategy_advisor"}
            
        except Exception as e:
            # 오류 발생 시 오류 메시지 추가 및 종료
            new_state.errors.append(f"종목 분석 오류: {str(e)}")
            new_state.current_node = "error"
            
            return {"state": new_state, "next": "error"}