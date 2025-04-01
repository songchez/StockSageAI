# StockSage AI

StockSage AI는 주식투자 의사결정을 돕는 인공지능 에이전트입니다. 기술적 분석과 기본적 분석을 결합하여 투자자에게 맞춤형 주식 추천과 투자 전략을 제공합니다.

## 주요 기능

- 시장 상태(강세/약세/횡보) 분석 및 판별
- 기술적/기본적 분석을 통합한 종목 스크리닝 및 심화 분석
- 최적 진입점, 목표가, 손절가 설정 제안
- 사용자 투자 성향에 맞는 맞춤형 추천
- 투자 전략 및 액션 플랜 제시

## 기술 스택

- **백엔드**: Python, LangChain, LangGraph
- **프론트엔드**: Streamlit
- **데이터 분석**: pandas, numpy, ta, yfinance
- **시각화**: plotly, matplotlib
- **AI 모델**: Claude 3.7 Sonnet
- **MCP 도구**: Sequential Thinking, Think MCP, Yahoo Finance, Fetch

## 설치 방법

### 사전 요구사항

- Python 3.10 이상
- [uv](https://github.com/astral-sh/uv) 패키지 관리자
- Anthropic API 키

### 설치 단계

1. 저장소 클론:

```bash
git clone https://github.com/yourusername/stocksage-ai.git
cd stocksage-ai
```

2. 가상 환경 생성 및 활성화:

```bash
uv venv
source .venv/bin/activate  # Linux/Mac
# 또는
.venv\Scripts\activate  # Windows
```

3. 의존성 설치:

```bash
uv pip install -r requirements.txt
```

4. 환경 변수 설정:

```bash
cp .env.template .env
# .env 파일을 편집하여 API 키 추가
```

5. MCP 서버 도구 설치:

```bash
uvx install mcp-server-sequential-thinking
uvx install mcp-server-think
uvx install mcp-server-fetch
```

## 실행 방법

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속하여 애플리케이션을 사용할 수 있습니다.

## 사용자 가이드

### 1. 투자자 프로필 설정

첫 사용 시 사이드바에서 '투자자 프로필' 메뉴를 선택하여 다음 항목을 설정하세요:

- 리스크 선호도 (1-10)
- 투자 기간
- 투자 가능 금액
- 선호 섹터 (선택사항)
- 투자 목적
- 매매 스타일

### 2. 기술적 분석 설정

'기술적 분석 설정' 메뉴에서 다음 항목의 가중치를 조정할 수 있습니다:

- 추세 요소
- 모멘텀 요소
- 변동성 요소
- 거래량 요소

### 3. AI와 대화

대시보드의 채팅 인터페이스를 통해 StockSage AI와 대화하세요. 다음과 같은 질문을 할 수 있습니다:

- "오늘 투자하기 가장 좋은 주식은 무엇인가요?"
- "기술 섹터에서 추천 종목이 있나요?"
- "현재 시장 상황에 맞는 투자 전략은 무엇인가요?"
- "애플(AAPL) 주식에 대한 기술적 분석을 보여주세요."
- "테슬라(TSLA)의 적정 진입점과 목표가를 알려주세요."

## 주의사항

- 이 애플리케이션의 투자 추천은 참고용으로만 사용하세요.
- 투자에는 항상 위험이 따릅니다. 최종 투자 결정은 본인의 판단에 따라 내려야 합니다.
- API 호출 한도에 따라 사용량이 제한될 수 있습니다.

## 라이선스

MIT License
