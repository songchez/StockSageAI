"""
주식투자 의사결정 그래프 상태 정의

LangGraph 노드들이 공유하는 상태 구조를 정의합니다.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, TypedDict, Union
from pydantic import BaseModel, Field

# 시장 상태 정의
class MarketCondition(str, Enum):
    BULL = "bull_market"
    BEAR = "bear_market"
    SIDEWAYS = "sideways_market"
    UNKNOWN = "unknown"

# 투자 그래프 상태 정의
class InvestmentState(BaseModel):
    """
    LangGraph 노드들이 공유하는 상태 클래스
    모든 노드는 이 상태를 통해 정보를 공유합니다.
    """
    # 사용자 관련 정보
    user_input: str = Field(default="")
    user_query_type: str = Field(default="general")  # general, specific_stock, sector, strategy
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    
    # 야후 파이낸스 원시 데이터 (모든 노드가 공유)
    raw_market_data: Dict[str, Any] = Field(default_factory=dict)  # 시장 데이터
    raw_sector_data: Dict[str, Any] = Field(default_factory=dict)  # 섹터 데이터
    raw_stock_data: Dict[str, Dict[str, Any]] = Field(default_factory=dict)  # 종목별 데이터
    
    # 각 분석 단계의 결과 (각 노드의 출력)
    market_analysis: Dict[str, Any] = Field(default_factory=dict)
    sector_analysis: Dict[str, Any] = Field(default_factory=dict)
    screened_stocks: List[Dict[str, Any]] = Field(default_factory=list)
    stock_analysis: Dict[str, Any] = Field(default_factory=dict)
    investment_strategy: Dict[str, Any] = Field(default_factory=dict)
    
    # 최종 추천 및 결과
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    final_answer: str = Field(default="")
    
    # 그래프 실행 제어
    current_node: str = Field(default="start")
    errors: List[str] = Field(default_factory=list)
    
    # 메시지 히스토리 (노드 간 대화 기록)
    messages: List[Dict[str, str]] = Field(default_factory=list)

# 노드의 출력을 위한 타입 정의
class NodeOutput(TypedDict, total=False):
    state: InvestmentState
    next: str