import yfinance as yf
import re
from graph_state import State


def technical_analysis(state: State) -> State:
    '''기술적 분석 툴'''
    messages = state["messages"]
    last_message = messages[-1][1]
    
    # 티커 심볼 추출 (대문자 1-5글자)
    ticker_pattern = r'\b[A-Z]{1,5}\b'
    potential_tickers = re.findall(ticker_pattern, last_message.upper())
    
    stock_data = {}
    
    if not potential_tickers:
        return {"stock_data": {"error": "주식 심볼을 식별할 수 없습니다. 예: AAPL, MSFT, GOOGL"}}
    
    try:
        # 첫 번째 발견된 티커 사용
        ticker = potential_tickers[0]
        
        # yfinance로 데이터 가져오기
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 기본 정보 구성
        basic_info = {
            "ticker": ticker,
            "name": info.get("shortName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", "N/A")),
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": info.get("trailingPE", "N/A"),
            "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else 0,
        }
        
        # 과거 데이터 가져오기 (200일 이상으로 충분한 기간)
        hist = stock.history(period="1y")
        
        if len(hist) < 30:
            return {**state, "stock_data": {**basic_info, "error": "충분한 과거 데이터가 없습니다."}}
        
        # ---- 기술적 지표 계산 ----
        
        # 이동평균선
        ma_periods = [10, 20, 50, 200]
        for period in ma_periods:
            if len(hist) >= period:
                hist[f'MA_{period}'] = hist['Close'].rolling(window=period).mean()
        
        # RSI 계산 (14일)
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD 계산
        hist['EMA_12'] = hist['Close'].ewm(span=12, adjust=False).mean()
        hist['EMA_26'] = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
        hist['Signal_Line'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        hist['MACD_Histogram'] = hist['MACD'] - hist['Signal_Line']
        
        # 볼린저 밴드 (20일)
        std_period = 20
        std_multiplier = 2
        hist['BB_Middle'] = hist['Close'].rolling(window=std_period).mean()
        hist['BB_StdDev'] = hist['Close'].rolling(window=std_period).std()
        hist['BB_Upper'] = hist['BB_Middle'] + (hist['BB_StdDev'] * std_multiplier)
        hist['BB_Lower'] = hist['BB_Middle'] - (hist['BB_StdDev'] * std_multiplier)
        
        # 스토캐스틱 오실레이터
        k_period = 14
        d_period = 3
        hist['Lowest_Low'] = hist['Low'].rolling(window=k_period).min()
        hist['Highest_High'] = hist['High'].rolling(window=k_period).max()
        hist['%K'] = 100 * ((hist['Close'] - hist['Lowest_Low']) / (hist['Highest_High'] - hist['Lowest_Low']))
        hist['%D'] = hist['%K'].rolling(window=d_period).mean()
        
        # OBV (On-Balance Volume)
        hist['OBV'] = (hist['Volume'] * (
            (hist['Close'] - hist['Close'].shift(1)) / abs(hist['Close'] - hist['Close'].shift(1)))
            .fillna(0)).cumsum()
        
        # ---- 기술적 지표를 점수로 변환 (-100 ~ 100) ----
        
        current_price = hist['Close'].iloc[-1]
        indicators_score = {}
        
        # 1. 이동평균선 점수 (-100 ~ 100)
        ma_scores = {}
        ma_weights = {10: 0.15, 20: 0.25, 50: 0.3, 200: 0.3}  # 가중치
        total_ma_score = 0
        
        for period in ma_periods:
            if len(hist) >= period:
                ma_value = hist[f'MA_{period}'].iloc[-1]
                # 가격이 이동평균보다 높으면 양수, 낮으면 음수
                deviation_pct = ((current_price - ma_value) / ma_value) * 100
                # -10% ~ +10% 범위를 -100 ~ 100 점수로 변환
                ma_score = max(min(deviation_pct * 10, 100), -100)
                ma_scores[period] = ma_score
                total_ma_score += ma_score * ma_weights.get(period, 0.25)
        
        indicators_score['moving_averages'] = round(total_ma_score, 2)
        
        # 2. RSI 점수 (0-100 -> -100 ~ 100)
        # RSI < 30: 과매도 (매수신호), RSI > 70: 과매수 (매도신호)
        rsi_value = hist['RSI'].iloc[-1]
        if rsi_value < 30:
            # 0-30 범위를 0 ~ -100으로 변환 (매수신호)
            rsi_score = ((30 - rsi_value) / 30) * -100
        elif rsi_value > 70:
            # 70-100 범위를 0 ~ 100으로 변환 (매도신호)
            rsi_score = ((rsi_value - 70) / 30) * 100
        else:
            # 30-70 범위를 -50 ~ 50으로 선형 변환
            rsi_score = ((rsi_value - 30) / 40 * 100) - 50
        
        indicators_score['rsi'] = round(rsi_score, 2)
        
        # 3. MACD 점수 (-100 ~ 100)
        macd_value = hist['MACD'].iloc[-1]
        signal_value = hist['Signal_Line'].iloc[-1]
        hist_value = hist['MACD_Histogram'].iloc[-1]
        
        # MACD와 시그널의 교차 방향
        if macd_value > signal_value:
            # MACD > 시그널 (매수신호)
            macd_cross_score = -50
            # 히스토그램 증가 속도에 따라 강도 조절
            hist_change = hist_value - hist['MACD_Histogram'].iloc[-2]
            macd_momentum_score = max(min((hist_change / abs(hist_value) * 100) * -0.5, -50), 0)
        else:
            # MACD < 시그널 (매도신호)
            macd_cross_score = 50
            # 히스토그램 감소 속도에 따라 강도 조절
            hist_change = hist_value - hist['MACD_Histogram'].iloc[-2]
            macd_momentum_score = max(min((hist_change / abs(hist_value) * 100) * 0.5, 50), 0)
        
        indicators_score['macd'] = round(macd_cross_score + macd_momentum_score, 2)
        
        # 4. 볼린저 밴드 점수 (-100 ~ 100)
        bb_upper = hist['BB_Upper'].iloc[-1]
        bb_lower = hist['BB_Lower'].iloc[-1]
        
        # %B 계산 (0~1 범위)
        percent_b = (current_price - bb_lower) / (bb_upper - bb_lower)
        
        # %B를 -100 ~ 100 점수로 변환
        # 0.5가 중간(0점), 0이 하단(-100점), 1이 상단(100점)
        bb_score = (percent_b - 0.5) * 200
        
        indicators_score['bollinger_bands'] = round(bb_score, 2)
        
        # 5. 스토캐스틱 점수 (-100 ~ 100)
        k_value = hist['%K'].iloc[-1]
        d_value = hist['%D'].iloc[-1]
        
        # 스토캐스틱 값 기반 점수 (80-100: 과매수, 0-20: 과매도)
        if k_value < 20:
            # 0-20 범위를 0 ~ -100으로 변환 (매수신호)
            stoch_level_score = ((20 - k_value) / 20) * -100
        elif k_value > 80:
            # 80-100 범위를 0 ~ 100으로 변환 (매도신호)
            stoch_level_score = ((k_value - 80) / 20) * 100
        else:
            # 20-80 범위를 -40 ~ 40으로 선형 변환
            stoch_level_score = ((k_value - 20) / 60 * 80) - 40
        
        # K선과 D선의 교차 방향 (±60점)
        if k_value > d_value:
            # K > D (매수신호)
            stoch_cross_score = -60
        else:
            # K < D (매도신호)
            stoch_cross_score = 60
        
        # 스토캐스틱 점수는 레벨(70%)과 교차(30%)를 합산
        indicators_score['stochastic'] = round(stoch_level_score * 0.7 + stoch_cross_score * 0.3, 2)
        
        # 6. OBV (On-Balance Volume) 변화 점수 (-100 ~ 100)
        obv_current = hist['OBV'].iloc[-1]
        obv_prev = hist['OBV'].iloc[-6]  # 약 1주일 전
        obv_change = ((obv_current - obv_prev) / abs(obv_prev)) * 100
        
        # OBV 변화를 -100 ~ 100 점수로 변환
        obv_score = max(min(obv_change * 5, 100), -100)
        indicators_score['volume_momentum'] = round(obv_score, 2)
        
        # 7. 가격 모멘텀 점수 (-100 ~ 100)
        price_change_periods = {
            "1d": 1,
            "1w": 5,
            "1m": 21,
            "3m": 63
        }
        
        momentum_scores = {}
        for period_name, days in price_change_periods.items():
            if len(hist) > days:
                change_pct = ((current_price / hist['Close'].iloc[-days-1]) - 1) * 100
                # 변화율을 -100 ~ 100 점수로 변환 (±10% 범위를 ±100점으로)
                momentum_score = max(min(change_pct * 10, 100), -100)
                momentum_scores[period_name] = round(momentum_score, 2)
        
        indicators_score['price_momentum'] = momentum_scores
        
        # 모든 지표의 가중 평균 계산 (종합 점수)
        indicator_weights = {
            'moving_averages': 0.25,
            'rsi': 0.15,
            'macd': 0.15,
            'bollinger_bands': 0.15,
            'stochastic': 0.15,
            'volume_momentum': 0.15
        }
        
        composite_score = 0
        for indicator, score in indicators_score.items():
            if indicator != 'price_momentum':  # 가격 모멘텀은 별도로 계산
                composite_score += score * indicator_weights.get(indicator, 0)
        
        # 추가적으로 단기 가격 모멘텀을 종합 점수에 반영
        if 'price_momentum' in indicators_score and '1w' in indicators_score['price_momentum']:
            composite_score += indicators_score['price_momentum']['1w'] * 0.15
            # 가중치 합을 1.0으로 맞추기 위해 조정
            composite_score = composite_score / 1.15
        
        # 종합 점수 반올림
        composite_score = round(composite_score, 2)
        
        # 점수 해석
        score_interpretation = ""
        if composite_score <= -80:
            score_interpretation = "매우 강한 매수 신호"
        elif composite_score <= -50:
            score_interpretation = "강한 매수 신호"
        elif composite_score <= -20:
            score_interpretation = "약한 매수 신호"
        elif composite_score < 20:
            score_interpretation = "중립적 신호"
        elif composite_score < 50:
            score_interpretation = "약한 매도 신호"
        elif composite_score < 80:
            score_interpretation = "강한 매도 신호"
        else:
            score_interpretation = "매우 강한 매도 신호"
        
        # 최종 분석 결과
        analysis_result = {
            **basic_info,
            "current_price": current_price,
            "technical_scores": indicators_score,
            "composite_score": composite_score,
            "signal": score_interpretation,
            "price_changes": {
                period: f"{((current_price / hist['Close'].iloc[-days-1] if len(hist) > days else 1) - 1) * 100:.2f}%" 
                for period, days in price_change_periods.items()
            }
        }
        
        stock_data = analysis_result
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        stock_data = {"error": f"분석 중 오류 발생: {str(e)}", "error_details": error_details}
    
    return {"stock_data": stock_data}