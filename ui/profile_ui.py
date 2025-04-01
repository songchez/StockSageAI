"""
투자자 프로필 설정 UI 모듈

사용자의 투자 성향과 목표를 설정하는 UI를 제공합니다.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

def render_profile_ui():
    """
    투자자 프로필 설정 UI를 렌더링합니다.
    """
    st.title("👤 투자자 프로필 설정")
    st.markdown("투자 성향과 목표에 맞게 프로필을 설정하세요. 이 정보는 맞춤형 투자 추천에 사용됩니다.")
    
    # 프로필 설정 폼
    with st.form("profile_form"):
        # 1. 리스크 선호도
        st.subheader("리스크 선호도")
        risk_preference = st.slider(
            "투자 위험을 감수하는 정도",
            min_value=1,
            max_value=10,
            value=st.session_state.get("risk_preference", 5),
            help="1: 매우 보수적, 10: 매우 공격적"
        )
        
        # 리스크 선호도 설명
        risk_descriptions = {
            "1-3": "**보수적**: 원금 보존을 중시하며 안정적인 수익을 추구합니다.",
            "4-7": "**중립적**: 적절한 위험과 수익의 균형을 추구합니다.",
            "8-10": "**공격적**: 높은 수익을 위해 높은 위험을 감수할 수 있습니다."
        }
        
        for range_str, desc in risk_descriptions.items():
            range_start, range_end = map(int, range_str.split("-"))
            if range_start <= risk_preference <= range_end:
                st.info(desc)
        
        # 2. 투자 기간
        st.subheader("투자 기간")
        investment_period = st.selectbox(
            "주로 고려하는 투자 기간",
            options=[
                "초단기 (1주일 이내)",
                "단기 (1개월 이내)",
                "중기 (1-6개월)",
                "장기 (6개월 이상)"
            ],
            index=["초단기 (1주일 이내)", "단기 (1개월 이내)", "중기 (1-6개월)", "장기 (6개월 이상)"].index(
                st.session_state.get("investment_period", "중기 (1-6개월)")
            )
        )
        
        # 3. 투자 금액
        st.subheader("투자 가능 금액")
        investment_amount = st.number_input(
            "투자 가능한 총 금액 ($)",
            min_value=100,
            max_value=10000000,
            value=st.session_state.get("investment_amount", 10000),
            step=1000,
            help="이 금액을 기준으로 포지션 크기와 종목 수를 추천합니다."
        )
        
        # 4. 선호 섹터
        st.subheader("선호 섹터 (선택사항)")
        preferred_sectors = st.multiselect(
            "관심 있는 산업 섹터를 선택하세요",
            options=[
                "기술", "의료", "금융", "에너지", "소비재", 
                "통신", "산업재", "원자재", "유틸리티"
            ],
            default=st.session_state.get("preferred_sectors", []),
            help="특정 섹터에 집중하고 싶을 때 선택하세요. 비워두면 모든 섹터를 고려합니다."
        )
        
        # 5. 투자 목적
        st.subheader("투자 목적")
        investment_goal = st.radio(
            "주요 투자 목적은 무엇인가요?",
            options=["성장", "가치", "배당", "균형"],
            index=["성장", "가치", "배당", "균형"].index(
                st.session_state.get("investment_goal", "균형")
            ),
            help="성장: 빠른 성장 기업, 가치: 저평가 기업, 배당: 배당 수익, 균형: 다양한 요소 고려"
        )
        
        # 6. 매매 스타일
        st.subheader("선호하는 매매 스타일")
        trading_style = st.radio(
            "주로 선호하는 매매 스타일은 무엇인가요?",
            options=["스윙 트레이딩", "추세 추종", "역추세 매매", "알고리즘 매매"],
            index=["스윙 트레이딩", "추세 추종", "역추세 매매", "알고리즘 매매"].index(
                st.session_state.get("trading_style", "스윙 트레이딩")
            ),
            help="각 스타일에 맞는 진입/퇴출 전략을 제안합니다"
        )
        
        # 저장 버튼
        submit_button = st.form_submit_button("프로필 저장", use_container_width=True)
        
        if submit_button:
            # 설정 저장
            st.session_state.risk_preference = risk_preference
            st.session_state.investment_period = investment_period
            st.session_state.investment_amount = investment_amount
            st.session_state.preferred_sectors = preferred_sectors
            st.session_state.investment_goal = investment_goal
            st.session_state.trading_style = trading_style
            
            st.success("✅ 투자자 프로필이 저장되었습니다!")
            
            # 저장한 프로필에 맞는 추천 전략 업데이트
            update_recommended_strategy()
    
    # 하단에 프로필 기반 시각화 표시
    st.divider()
    render_profile_visualization()
    
    # 추천 투자 전략
    render_recommended_strategy()

def update_recommended_strategy():
    """
    사용자 프로필에 기반한 추천 투자 전략을 업데이트합니다.
    """
    # 프로필 정보에 기반하여 추천 전략 생성
    risk = st.session_state.risk_preference
    period = st.session_state.investment_period
    goal = st.session_state.get("investment_goal", "균형")
    style = st.session_state.get("trading_style", "스윙 트레이딩")
    
    # 리스크 수준에 따른 자산 배분
    if risk <= 3:  # 보수적
        stock_allocation = 40
        cash_allocation = 30
        bond_allocation = 30
    elif risk <= 7:  # 중립적
        stock_allocation = 60
        cash_allocation = 20
        bond_allocation = 20
    else:  # 공격적
        stock_allocation = 80
        cash_allocation = 15
        bond_allocation = 5
    
    # 주식 선택 전략
    if goal == "성장":
        stock_strategy = "높은 성장률과 기술적 모멘텀을 가진 종목 위주로 선택"
    elif goal == "가치":
        stock_strategy = "저평가된 종목과 안정적인 재무구조를 가진 종목 위주로 선택"
    elif goal == "배당":
        stock_strategy = "높은 배당수익률과 안정적인 배당 성장률을 가진 종목 위주로 선택"
    else:  # 균형
        stock_strategy = "성장, 가치, 배당 요소를 균형 있게 고려한 종목 선택"
    
    # 기간에 따른 매매 전략
    if period == "초단기 (1주일 이내)":
        trading_strategy = "기술적 지표와 차트 패턴에 집중하여 단기 모멘텀 활용"
        position_size = "전체 자금의 5-10%를 한 종목에 배분"
    elif period == "단기 (1개월 이내)":
        trading_strategy = "단기 추세와 섹터 로테이션을 고려한 스윙 트레이딩"
        position_size = "전체 자금의 10-15%를 한 종목에 배분"
    elif period == "중기 (1-6개월)":
        trading_strategy = "주요 추세를 따르되 기본적 분석을 함께 고려"
        position_size = "전체 자금의 15-20%를 한 종목에 배분"
    else:  # 장기
        trading_strategy = "기본적 분석 중심으로 장기 성장 모멘텀 고려"
        position_size = "전체 자금의 20-25%를 한 종목에 배분"
    
    # 손절매 전략
    if risk <= 3:  # 보수적
        stop_loss = "진입가 대비 5-7% 손절매"
    elif risk <= 7:  # 중립적
        stop_loss = "진입가 대비 7-10% 손절매"
    else:  # 공격적
        stop_loss = "진입가 대비 10-15% 손절매"
    
    # 추천 전략 저장
    st.session_state.recommended_strategy = {
        "asset_allocation": {
            "stocks": stock_allocation,
            "bonds": bond_allocation,
            "cash": cash_allocation
        },
        "stock_strategy": stock_strategy,
        "trading_strategy": trading_strategy,
        "position_size": position_size,
        "stop_loss": stop_loss
    }

def render_profile_visualization():
    """
    사용자 프로필을 시각화합니다.
    """
    # 프로필이 설정되었는지 확인
    if "risk_preference" not in st.session_state:
        return
    
    st.subheader("📊 프로필 시각화")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 자산 배분 파이 차트
        if "recommended_strategy" in st.session_state:
            allocation = st.session_state.recommended_strategy["asset_allocation"]
            
            fig = go.Figure(data=[go.Pie(
                labels=list(allocation.keys()),
                values=list(allocation.values()),
                hole=.4,
                marker_colors=['#4CAF50', '#2196F3', '#FFC107']
            )])
            
            fig.update_layout(
                title='추천 자산 배분',
                height=300,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 리스크-수익 스펙트럼 상의 위치
        risk = st.session_state.risk_preference
        
        # 리스크-수익 커브 데이터
        x = np.linspace(1, 10, 100)
        y = 2 * np.log(x) + x/2  # 로그 커브로 리스크-수익 관계 표현
        
        fig = px.line(x=x, y=y, labels={'x': '리스크', 'y': '기대 수익'})
        
        # 현재 위치 표시
        fig.add_trace(go.Scatter(
            x=[risk],
            y=[2 * np.log(risk) + risk/2],
            mode='markers',
            marker=dict(size=12, color='red'),
            name='현재 프로필'
        ))
        
        fig.update_layout(
            title='리스크-수익 스펙트럼 상의 위치',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_recommended_strategy():
    """
    추천 투자 전략을 표시합니다.
    """
    if "recommended_strategy" not in st.session_state:
        update_recommended_strategy()
    
    strategy = st.session_state.recommended_strategy
    
    st.subheader("📋 맞춤형 투자 전략")
    
    with st.expander("추천 전략 보기", expanded=True):
        st.markdown("### 자산 배분")
        st.markdown(f"- 주식: **{strategy['asset_allocation']['stocks']}%**")
        st.markdown(f"- 채권: **{strategy['asset_allocation']['bonds']}%**")
        st.markdown(f"- 현금성 자산: **{strategy['asset_allocation']['cash']}%**")
        
        st.markdown("### 종목 선택 전략")
        st.markdown(f"- {strategy['stock_strategy']}")
        
        st.markdown("### 매매 전략")
        st.markdown(f"- **트레이딩 방식**: {strategy['trading_strategy']}")
        st.markdown(f"- **포지션 크기**: {strategy['position_size']}")
        st.markdown(f"- **손절매 전략**: {strategy['stop_loss']}")
        
        st.markdown("### 추천 포트폴리오 구성")
        # 실제로는 API에서 사용자 프로필에 맞는 종목을 추천
        risk = st.session_state.risk_preference
        goal = st.session_state.get("investment_goal", "균형")
        
        if risk <= 3:  # 보수적
            if goal == "배당":
                st.markdown("- 배당 중심: VYM, SCHD, JNJ, PG, KO")
            else:
                st.markdown("- 안정 중심: VTI, BRK.B, MSFT, PG, JNJ")
        elif risk <= 7:  # 중립적
            if goal == "성장":
                st.markdown("- 성장 중심: QQQ, AAPL, MSFT, GOOGL, V")
            elif goal == "가치":
                st.markdown("- 가치 중심: VTV, JPM, BRK.B, UNH, HD")
            else:
                st.markdown("- 균형 중심: VTI, AAPL, MSFT, JNJ, PG")
        else:  # 공격적
            if goal == "성장":
                st.markdown("- 고성장 중심: ARKK, TSLA, NVDA, AMD, SHOP")
            else:
                st.markdown("- 공격 중심: QQQ, NVDA, TSLA, AMZN, META")