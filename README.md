# 간단한 LangGraph 챗봇

이 프로젝트는 LangGraph와 Streamlit을 사용한 간단한 챗봇 구현 예제입니다.

## 기능

- LangGraph를 이용한 상태 관리
- 대화 히스토리 유지
- Streamlit을 통한 사용자 친화적 인터페이스
- 스레드별 대화 세션 관리

## 실행 방법

1. 필요한 패키지 설치하기

```bash
pip install -r requirements.txt
```

2. 필요한 API 키 설정

`.env` 파일을 만들고 다음 값을 설정합니다:

```
GOOGLE_API_KEY=your_google_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_PROJECT=pr-dear-ratepayer-64
LANGCHAIN_TRACING_V2=true
```

또는 Streamlit의 secrets.toml 파일에 설정:

```toml
# .streamlit/secrets.toml
GOOGLE_API_KEY = "your-google-api-key"
LANGCHAIN_API_KEY = "your-langchain-api-key"
LANGCHAIN_PROJECT = "your_langchain_project_key"
LANGCHAIN_TRACING_V2 = "true"
```

3. 애플리케이션 실행하기

```bash
streamlit run app.py
```

## 작동 방식

1. 사용자가 메시지를 입력하면 메시지가 LangGraph 그래프로 전달됩니다.
2. LangGraph는 Google의 Gemini 모델을 사용하여 응답을 생성합니다.
3. 대화 기록은 LangGraph의 MemorySaver를 통해 유지됩니다.
4. 사용자별로 고유한 스레드 ID를 사용하여 별도의 대화 세션을 유지합니다.
5. LangSmith를 통해 모든 실행이 로깅되어 디버깅 및 분석이 가능합니다.

## 윈도우일경우 아래 코드를 활성화 해주세요

```python
# import asyncio
# if hasattr(asyncio, 'WindowsProactorEventLoopPolicy'):
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
```
