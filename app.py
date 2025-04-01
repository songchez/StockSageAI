"""
StockSage AI - 주식투자 의사결정을 위한 AI 에이전트
메인 애플리케이션 진입점
"""
import streamlit as st
import asyncio
import nest_asyncio
import json
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_teddynote import logging


load_dotenv()

logging.langsmith("pr-dear-ratepayer-64")

# 중첩 비동기 호출 허용 (LangChain과 함께 사용 시 필요)
nest_asyncio.apply()

# 전역 이벤트 루프 생성 및 재사용
if "event_loop" not in st.session_state:
    loop = asyncio.new_event_loop()
    st.session_state.event_loop = loop
    asyncio.set_event_loop(loop)

# 필요한 모듈 임포트
from ui.chat_interface import render_chat_interface
from ui.dashboard import render_dashboard
from ui.profile_ui import render_profile_ui
from utils.config_manager import load_config, sync_session_to_config, sync_config_to_session

# 환경 변수 로드
load_dotenv(override=True)

def initialize_agent(mcp_config=None):
    """
    StockSage AI 에이전트 초기화
    
    Args:
        mcp_config: MCP 서버 구성 설정 (기본값 사용 시 None)
    """
    try:
        # MCP 클라이언트 생성
        client = MultiServerMCPClient(mcp_config)
        # MCP 클라이언트 초기화 (비동기 함수를 동기적으로 호출)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(client.__aenter__())
        
        # 야후 파이낸스 MCP 도구 가져오기 (예시 - 실제 구현에서는 정확한 도구 이름 필요)
        tools = client.get_tools()
        
        # LLM 모델 생성
        model = ChatGoogleGenerativeAI(
            model="Gemini 2.5 Pro Experimental 03-25",
            temperature=0.1,
            max_tokens=20000
        )
        
        return model,tools
        
    except Exception as e:
        st.error(f"에이전트 초기화 오류: {str(e)}")
        return None

def create_streamlit_callback(text_placeholder, analysis_placeholder):
    """
    Streamlit 스트리밍 콜백 함수 생성
    
    Args:
        text_placeholder: 텍스트 응답을 표시할 Streamlit 컴포넌트
        analysis_placeholder: 분석 정보를 표시할 Streamlit 컴포넌트
        
    Returns:
        콜백 함수
    """
    # 상태를 추적하기 위한 클로저 변수
    progress = {"current_node": "", "messages": []}
    
    def callback(chunk):
        """LangGraph 스트리밍 콜백 함수"""
        if "state" in chunk:
            state = chunk["state"]
            
            # 현재 노드 표시
            current_node = state.current_node
            if current_node != progress["current_node"]:
                progress["current_node"] = current_node
                analysis_placeholder.markdown(f"🔄 현재 분석 단계: **{current_node}**")
            
            # 메시지 표시
            messages = state.messages
            if len(messages) > len(progress["messages"]):
                new_messages = messages[len(progress["messages"]):]
                progress["messages"] = messages
                
                for msg in new_messages:
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    analysis_placeholder.markdown(f"**{role}**: {content}")
            
            # 최종 답변이 있으면 표시
            if state.final_answer:
                text_placeholder.markdown(state.final_answer)
    
    return callback

def process_query_in_streamlit(query, user_profile, agent):
    """
    Streamlit에서 쿼리 처리 및 UI 표시
    
    Args:
        query: 사용자 질문/요청
        user_profile: 사용자 투자 프로필 정보
        agent: QueryProcessor 인스턴스
        
    Returns:
        처리 결과
    """
    with st.chat_message("assistant"):
        analysis_placeholder = st.empty()
        text_placeholder = st.empty()
        
        analysis_placeholder.markdown("🔍 **분석 중...**")
        
        # 콜백 함수 생성
        callback = create_streamlit_callback(text_placeholder, analysis_placeholder)
        
        # 비동기 처리 (Streamlit에서는 asyncio 루프를 직접 실행)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            agent.process_query(query, user_profile, callback)
        )
        
        # 오류 확인
        if "error" in result:
            text_placeholder.error(f"처리 중 오류가 발생했습니다: {result['error']}")
            return None
        
        # 분석 완료 표시
        analysis_placeholder.markdown("✅ **분석 완료**")
        with analysis_placeholder.expander("분석 과정 보기", expanded=False):
            for msg in result.get("messages", []):
                role = msg.get("role", "")
                content = msg.get("content", "")
                st.markdown(f"**{role}**: {content}")
        
        # 이미 표시되지 않았다면 최종 답변 표시
        if not result.get("answer") in text_placeholder.markdown:
            text_placeholder.markdown(result.get("answer", "응답을 생성할 수 없습니다."))
        
        return result

# MCP 서버 구성 로드
def load_mcp_config():
    """MCP 서버 구성을 로드합니다."""
    config_path = os.path.join('mcp_servers', 'mcp_server_config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

# 세션 초기화 함수
async def initialize_session():
    """에이전트와 MCP 클라이언트를 초기화합니다."""
    try:
        with st.spinner("🔄 StockSage AI 초기화 중..."):
            # MCP 서버 구성 로드
            mcp_config = load_mcp_config()
            
            # 에이전트 초기화
            agent = initialize_agent(mcp_config)
            
            if agent:
                st.session_state.agent = agent
                st.session_state.session_initialized = True
                return True
            else:
                return False
                
    except Exception as e:
        import traceback
        st.error(f"초기화 중 오류 발생: {str(e)}")
        st.error(traceback.format_exc())
        return False

# Streamlit 앱 설정
st.set_page_config(
    page_title="StockSage AI",
    page_icon="📈",
    layout="wide"
)

# 세션 상태 초기화
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False
    st.session_state.agent = None
    st.session_state.history = []
    st.session_state.mcp_client = None
    st.session_state.page = "dashboard"
    st.session_state.config = load_config()
    st.session_state.thread_id = "stocksage-" + os.urandom(8).hex()

# 사이드바 메뉴
with st.sidebar:
    st.title("StockSage AI")
    st.caption("주식투자 의사결정 AI 어시스턴트")
    
    # 메뉴 선택
    selected = st.radio(
        "메뉴",
        ["대시보드", "투자자 프로필", "기술적 분석 설정", "도움말"],
        key="menu"
    )
    
    # 선택에 따라 페이지 상태 변경
    if selected == "대시보드":
        st.session_state.page = "dashboard"
    elif selected == "투자자 프로필":
        st.session_state.page = "profile"
    elif selected == "기술적 분석 설정":
        st.session_state.page = "weights"
    elif selected == "도움말":
        st.session_state.page = "help"
    
    # 시스템 정보 표시
    st.divider()
    st.subheader("🔧 시스템 정보")
    st.write("🧠 모델: Gemini 2.0 Pro")
    st.write("📊 데이터: Yahoo Finance")
    
    # 대화 초기화 버튼
    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.thread_id = "stocksage-" + os.urandom(8).hex()
        st.session_state.history = []
        st.success("✅ 대화가 초기화되었습니다.")
        st.rerun()

# 기본 세션 초기화 (초기화되지 않은 경우)
if not st.session_state.session_initialized:
    st.info("🔄 StockSage AI를 초기화합니다. 잠시만 기다려주세요...")
    success = st.session_state.event_loop.run_until_complete(initialize_session())
    if success:
        st.success("✅ 초기화 완료!")
    else:
        st.error("❌ 초기화에 실패했습니다. 페이지를 새로고침해 주세요.")

# 사용자 설정을 세션으로 로드
if st.session_state.session_initialized and "config_loaded" not in st.session_state:
    sync_config_to_session()
    st.session_state.config_loaded = True

# 선택된 페이지 표시
if st.session_state.page == "dashboard":
    render_dashboard()
    
    # 채팅 인터페이스 표시
    st.markdown("### 💬 StockSage AI와 대화")
    
    # 대화 기록 표시
    for message in st.session_state.history:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("assistant").markdown(message["content"])
    
    # 사용자 입력 처리
    user_query = st.chat_input("💬 주식 투자에 대해 물어보세요...")
    if user_query:
        if st.session_state.session_initialized:
            # 사용자 메시지 표시
            st.chat_message("user").markdown(user_query)
            
            # 사용자 프로필 정보 수집
            user_profile = {
                "risk_preference": st.session_state.get("risk_preference", 5),
                "investment_period": st.session_state.get("investment_period", "중기 (1-6개월)"),
                "investment_amount": st.session_state.get("investment_amount", 10000),
                "preferred_sectors": st.session_state.get("preferred_sectors", []),
                "investment_goal": st.session_state.get("investment_goal", "균형"),
                "trading_style": st.session_state.get("trading_style", "스윙 트레이딩"),
                "technical_weights": {
                    "trend": st.session_state.get("trend_weight", 0.4),
                    "momentum": st.session_state.get("momentum_weight", 0.2),
                    "volatility": st.session_state.get("volatility_weight", 0.2),
                    "volume": st.session_state.get("volume_weight", 0.2)
                }
            }
            
            # 쿼리 처리 및 응답
            result = process_query_in_streamlit(user_query, user_profile, st.session_state.agent)
            
            if result:
                # 대화 기록 업데이트
                st.session_state.history.append({"role": "user", "content": user_query})
                st.session_state.history.append({"role": "assistant", "content": result.get("answer", "")})
                
                # 대화 기록이 너무 길어지면 오래된 항목 제거
                max_history = 10
                if len(st.session_state.history) > max_history * 2:
                    st.session_state.history = st.session_state.history[-max_history * 2:]
                
                st.rerun()
        else:
            st.warning("⏳ 시스템이 아직 초기화 중입니다. 잠시 후 다시 시도해주세요.")

elif st.session_state.page == "profile":
    render_profile_ui()
    # 프로필 변경 후 설정 파일에 저장
    sync_session_to_config()

elif st.session_state.page == "help":
    st.title("❓ 도움말")
    st.markdown("StockSage AI 사용 가이드")
    with st.expander("시작하기", expanded=True):
        st.markdown("""
        ### 시작하기
        
        1. **투자자 프로필 설정**: 먼저 사이드바의 '투자자 프로필' 메뉴에서 자신의 투자 성향과 목표를 설정하세요.
        
        2. **AI와 대화**: 대시보드의 채팅 인터페이스를 통해 AI 어드바이저와 대화할 수 있습니다.
        
        3. **분석 설정 조정**: '기술적 분석 설정' 메뉴에서 분석에 사용되는 가중치를 자신의 투자 스타일에 맞게 조정할 수 있습니다.
        """)
    
    with st.expander("기능 소개", expanded=True):
        st.markdown("""
        ### 주요 기능
        
        - **시장 분석**: 현재 시장 상황(강세/약세/횡보)을 분석하고 투자 기회와 위험 요소를 파악합니다.
        
        - **섹터 분석**: 강세를 보이는 섹터를 식별하고 섹터 로테이션 관점에서의 투자 기회를 제시합니다.
        
        - **종목 스크리닝**: 시장 상황과 사용자 프로필에 적합한 종목을 선별합니다.
        
        - **종목 심층 분석**: 특정 종목의 기술적/기본적 분석을 수행하고 투자 적합성을 평가합니다.
        
        - **투자 전략 제안**: 진입점, 목표가, 손절가, 투자 비중 등 구체적인 투자 전략을 제시합니다.
        """)
    
    with st.expander("자주 묻는 질문", expanded=False):
        st.markdown("""
        ### 자주 묻는 질문
        
        **Q: StockSage AI의 추천은 얼마나 정확한가요?**
        
        A: AI는 다양한 기술적/기본적 지표와 시장 데이터를 분석하여 추천을 제공하지만, 모든 투자에는 위험이 따릅니다. AI의 추천은 참고 자료로만 활용하고, 최종 투자 결정은 본인이 신중하게 내려야 합니다.
        
        **Q: 기술적 분석 가중치를 어떻게 설정해야 할까요?**
        
        A: 자신의 투자 스타일에 맞게 조정하는 것이 좋습니다. 추세 추종 전략을 선호한다면 추세 요소의 가중치를, 단기 변동성을 활용하는 전략이라면 변동성 요소의 가중치를 높이는 것이 효과적입니다.
        
        **Q: 어떤 종류의 질문을 할 수 있나요?**
        
        A: 시장 상황, 섹터 분석, 특정 종목 분석, 투자 전략 등 다양한 주식 투자 관련 질문을 할 수 있습니다. 예를 들어:
        - "현재 시장 상황은 어떤가요?"
        - "기술 섹터에서 추천 종목이 있나요?"
        - "애플(AAPL) 주식에 대한 분석을 보여주세요."
        - "현재 시장에서 어떤 투자 전략이 좋을까요?"
        """)

# 메인 앱 실행 시 필요한 추가 로직
if __name__ == "__main__":
    pass