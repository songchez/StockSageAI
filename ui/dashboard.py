"""
대시보드 UI 모듈

메인 대시보드 UI 요소를 제공합니다.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

def render_dashboard():
    """
    대시보드 UI를 렌더링합니다.
    """
    # 2단 레이아웃
    col1, col2 = st.columns([1, 2])
    
    with col1:
        render_user_profile_summary()
        render_market_overview()
    
    with col2:
        render_top_picks()

def render_user_profile_summary():
    """
    사용자 투자자 프로필 요약을 표시합니다.
    """
    with st.expander("📝 투자자 프로필", expanded=True):
        # 세션 상태에서 사용자 프로필 정보 가져오기
        risk_preference = st.session_state.get("risk_preference", 5)
        investment_period = st.session_state.get("investment_period", "중기 (1-6개월)")
        investment_amount = st.session_state.get("investment_amount", 10000)
        preferred_sectors = st.session_state.get("preferred_sectors", [])
        
        # 프로필 요약 표시
        st.markdown(f"**리스크 선호도:** {risk_preference}/10")
        
        # 리스크 선호도 시각화
        risk_color = get_risk_color(risk_preference)
        st.markdown(
            f"""
            <div style="
                background: linear-gradient(to right, #4CAF50, #FFC107, #F44336);
                height: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
                position: relative;
            ">
                <div style="
                    position: absolute;
                    width: 12px;
                    height: 12px;
                    background-color: {risk_color};
                    border-radius: 50%;
                    top: -1px;
                    left: {(risk_preference-1) * 11.1}%;
                    border: 2px solid white;
                "></div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown(f"**투자 기간:** {investment_period}")
        st.markdown(f"**투자 가능 금액:** ${investment_amount:,}")
        
        if preferred_sectors:
            st.markdown(f"**선호 섹터:** {', '.join(preferred_sectors)}")
        else:
            st.markdown("**선호 섹터:** 지정되지 않음")
        
        # 기술적 분석 스타일
        tech_style = "기본값"
        if "trend_weight" in st.session_state:
            weights = {
                "추세": st.session_state.trend_weight * 100,
                "모멘텀": st.session_state.momentum_weight * 100,
                "변동성": st.session_state.volatility_weight * 100,
                "거래량": st.session_state.volume_weight * 100
            }
            tech_style = "사용자 정의"
            
            # 가장 비중이 높은 요소 확인
            max_weight = max(weights.items(), key=lambda x: x[1])
            if max_weight[1] >= 40:
                tech_style = f"{max_weight[0]} 중심"
        
        st.markdown(f"**기술적 분석 스타일:** {tech_style}")
        
        # 프로필 수정 버튼
        if st.button("프로필 수정", key="edit_profile_btn", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()

def render_market_overview():
    """
    시장 개요 섹션을 렌더링합니다.
    """
    with st.expander("🌎 시장 개요", expanded=True):
        # 예시 데이터 (실제로는 API에서 가져올 것)
        # 오늘 날짜 기준으로 생성된 임시 데이터
        indices = {
            "S&P 500": {"value": "4,783.35", "change": "+0.22%", "color": "green"},
            "NASDAQ": {"value": "15,265.94", "change": "+0.65%", "color": "green"},
            "DOW": {"value": "38,045.78", "change": "-0.11%", "color": "red"},
            "VIX": {"value": "16.24", "change": "-3.45%", "color": "red"}
        }
        
        # 시장 상태
        market_condition = "강세장"  # 실제로는 알고리즘으로 판단
        condition_color = {"강세장": "green", "약세장": "red", "횡보장": "orange"}
        
        # 주요 지수 표시
        st.markdown("### 주요 지수")
        
        for idx, data in indices.items():
            st.markdown(f"{idx}: **{data['value']}** "
                       f"<span style='color:{data['color']}'>{data['change']}</span>", 
                       unsafe_allow_html=True)
        
        # 시장 상태 표시
        st.markdown(f"### 시장 상태: "
                   f"<span style='color:{condition_color[market_condition]}'>"
                   f"{market_condition}</span>", unsafe_allow_html=True)
        
        # 섹터 성과 요약
        st.markdown("### 섹터 성과 (주간)")
        
        # 예시 섹터 데이터
        sectors = {
            "기술": "+2.4%", 
            "의료": "+1.5%", 
            "금융": "-0.8%", 
            "에너지": "+3.2%", 
            "소비재": "+0.3%"
        }
        
        # 섹터별 성과 시각화
        sector_values = [float(v.replace('%', '')) for v in sectors.values()]
        sector_colors = ['green' if v > 0 else 'red' for v in sector_values]
        
        # 섹터 성과 차트
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=list(sectors.keys()),
            y=sector_values,
            marker_color=sector_colors,
            text=[f"{v}" for v in sectors.values()],
            textposition='auto'
        ))
        
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=0, b=0),
            yaxis=dict(
                showgrid=False,
                showticklabels=False
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

def render_top_picks():
    """
    상위 추천 종목을 렌더링합니다.
    """
    st.markdown("## 🏆 오늘의 추천 종목")
    
    # 예시 추천 종목 데이터
    top_picks = [
        {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "price": 185.36,
            "change": 1.24,
            "technical_score": 78,
            "fundamental_score": 82,
            "entry_price": "182.50 - 186.00",
            "target_price": 205.00,
            "stop_loss": 175.00,
            "recommendation": "매수",
            "timeframe": "중기",
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft Corporation",
            "price": 417.82,
            "change": 0.68,
            "technical_score": 82,
            "fundamental_score": 85,
            "entry_price": "410.00 - 420.00",
            "target_price": 450.00,
            "stop_loss": 395.00,
            "recommendation": "매수",
            "timeframe": "중기",
        },
        {
            "symbol": "NVDA",
            "name": "NVIDIA Corporation",
            "price": 107.65,
            "change": -1.35,
            "technical_score": 73,
            "fundamental_score": 80,
            "entry_price": "105.00 - 108.00",
            "target_price": 125.00,
            "stop_loss": 98.00,
            "recommendation": "관망",
            "timeframe": "단기",
        }
    ]
    
    # 추천 종목 탭
    tabs = st.tabs([f"{pick['symbol']} ({pick['name']})" for pick in top_picks])
    
    for i, tab in enumerate(tabs):
        with tab:
            pick = top_picks[i]
            
            # 1행: 기본 정보 및 점수
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                change_color = "green" if pick["change"] > 0 else "red"
                change_sign = "+" if pick["change"] > 0 else ""
                
                st.markdown(f"### ${pick['price']:.2f} "
                          f"<span style='color:{change_color}'>{change_sign}{pick['change']}%</span>", 
                          unsafe_allow_html=True)
                st.markdown(f"**추천:** {pick['recommendation']} ({pick['timeframe']})")
            
            with col2:
                st.markdown("**기술적 점수**")
                render_score_gauge(pick["technical_score"])
            
            with col3:
                st.markdown("**기본적 점수**")
                render_score_gauge(pick["fundamental_score"])
            
            # 2행: 매매 계획
            st.markdown("### 매매 계획")
            
            trade_cols = st.columns(3)
            with trade_cols[0]:
                st.metric("진입 가격", pick["entry_price"])
            with trade_cols[1]:
                upside = ((pick["target_price"] / pick["price"]) - 1) * 100
                st.metric("목표 가격", f"${pick['target_price']:.2f}", f"+{upside:.1f}%")
            with trade_cols[2]:
                downside = ((pick["stop_loss"] / pick["price"]) - 1) * 100
                st.metric("손절 가격", f"${pick['stop_loss']:.2f}", f"{downside:.1f}%")
            
            # 3행: 간단한 차트
            st.markdown("### 차트")
            render_stock_chart(pick["symbol"])
            
            # 4행: 투자 근거 요약
            with st.expander("투자 근거", expanded=False):
                st.markdown(f"""
                **기술적 분석:**
                - 20일 이동평균선 위에서 거래 중 (+)
                - RSI 지표 58로 적정 수준 (+)
                - MACD 지표 상향 교차 신호 (+)
                
                **기본적 분석:**
                - 최근 분기 실적 예상치 상회 (+)
                - 연간 성장률 12% 유지 중 (+)
                - 업계 평균 대비 밸류에이션 합리적 (+)
                
                **주요 이벤트:**
                - 2주 후 신규 제품 발표 예정 (+)
                - 주주환원 정책 강화 발표 (+)
                """)
            
            # 5행: 리스크 요약
            with st.expander("리스크 요인", expanded=False):
                st.markdown(f"""
                - 업계 경쟁 심화로 마진 압박 가능성 (-)
                - 규제 리스크 존재 (-)
                - 단기적 기술적 저항선 근처에서 거래 중 (-)
                """)

def render_score_gauge(score):
    """
    점수를 게이지 차트로 표시합니다.
    
    매개변수:
        score: 0-100 사이의 점수
    """
    # 색상 결정
    if score >= 80:
        color = "#4CAF50"  # 녹색
    elif score >= 60:
        color = "#FFC107"  # 노란색
    else:
        color = "#F44336"  # 빨간색
    
    # 게이지 차트
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': color},
            'steps': [
                {'range': [0, 40], 'color': "#F1F1F1"},
                {'range': [40, 60], 'color': "#F1F1F1"},
                {'range': [60, 80], 'color': "#F1F1F1"},
                {'range': [80, 100], 'color': "#F1F1F1"}
            ]
        }
    ))
    
    fig.update_layout(
        height=100,
        margin=dict(l=0, r=0, t=0, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render_stock_chart(symbol):
    """
    주식 차트를 렌더링합니다.
    
    매개변수:
        symbol: 주식 심볼
    """
    # 예시 데이터 생성 (실제로는 API에서 가져올 것)
    dates = pd.date_range(end=datetime.now(), periods=60, freq='D')
    
    # 예시 가격 데이터 생성 (임의의 추세와 변동성)
    np.random.seed(42)  # 재현 가능한 결과를 위해
    
    if symbol == "AAPL":
        base = 180
        trend = 0.1
    elif symbol == "MSFT":
        base = 400
        trend = 0.15
    else:  # NVDA
        base = 100
        trend = -0.05
    
    prices = [base]
    for i in range(1, len(dates)):
        daily_return = trend/len(dates) + np.random.normal(0, 0.01)
        prices.append(prices[-1] * (1 + daily_return))
    
    # 이동평균 계산
    prices_series = pd.Series(prices)
    sma_20 = prices_series.rolling(window=20).mean()
    
    # 차트 생성
    fig = go.Figure()
    
    # 캔들스틱 대신 선 차트 사용 (간략화)
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=symbol,
        line=dict(color='royalblue', width=2)
    ))
    
    # 20일 이동평균선 추가
    fig.add_trace(go.Scatter(
        x=dates,
        y=sma_20,
        mode='lines',
        name='20일 MA',
        line=dict(color='orange', width=1.5, dash='dash')
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=0, b=30),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            zeroline=False
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(230, 230, 230, 0.5)'
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

def get_risk_color(risk_level):
    """
    리스크 수준에 따른 색상을 반환합니다.
    
    매개변수:
        risk_level: 1-10 사이의 리스크 수준
    
    반환값:
        색상 코드 (HEX)
    """
    if risk_level <= 3:
        return "#4CAF50"  # 녹색 (보수적)
    elif risk_level <= 7:
        return "#FFC107"  # 노란색 (중립적)
    else:
        return "#F44336"  # 빨간색 (공격적)