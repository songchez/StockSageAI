"""
채팅 인터페이스 UI 모듈

사용자와 AI 어시스턴트 간의 대화 인터페이스를 제공합니다.
"""
import asyncio
import streamlit as st
from langchain_core.messages import HumanMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.messages.tool import ToolMessage
from langchain_teddynote.messages import astream_graph
from langchain_core.runnables import RunnableConfig

def render_chat_interface():
    """
    채팅 인터페이스를 렌더링합니다.
    """
    st.markdown("### 💬 StockSage AI와 대화")
    
    # 대화 기록 표시
    display_chat_history()
    
    # 제안 프롬프트
    with st.expander("💡 이런 질문을 해보세요", expanded=False):
        suggested_questions = [
            "오늘 투자하기 가장 좋은 주식은 무엇인가요?",
            "기술 섹터에서 추천 종목이 있나요?",
            "현재 시장 상황에 맞는 투자 전략은 무엇인가요?",
            "애플(AAPL) 주식에 대한 기술적 분석을 보여주세요.",
            "테슬라(TSLA)의 적정 진입점과 목표가를 알려주세요.",
            "제 투자 성향에 맞는 포트폴리오를 구성해주세요."
        ]
        
        col1, col2 = st.columns(2)
        for i, q in enumerate(suggested_questions):
            if i % 2 == 0:
                if col1.button(q, key=f"prompt_{i}", use_container_width=True):
                    # 세션 상태에 클릭한 질문 저장
                    st.session_state.clicked_question = q
                    st.rerun()
            else:
                if col2.button(q, key=f"prompt_{i}", use_container_width=True):
                    # 세션 상태에 클릭한 질문 저장
                    st.session_state.clicked_question = q
                    st.rerun()
    
    # 클릭한 질문이 있으면 처리
    if hasattr(st.session_state, 'clicked_question') and st.session_state.clicked_question:
        question = st.session_state.clicked_question
        st.session_state.clicked_question = None  # 처리 후 초기화
        
        if st.session_state.session_initialized:
            st.chat_message("user").markdown(question)
            with st.chat_message("assistant"):
                tool_placeholder = st.empty()
                text_placeholder = st.empty()
                resp, final_text, final_tool = st.session_state.event_loop.run_until_complete(
                    process_query(question, text_placeholder, tool_placeholder)
                )
            
            if "error" not in resp:
                st.session_state.history.append({"role": "user", "content": question})
                st.session_state.history.append(
                    {"role": "assistant", "content": final_text}
                )
                if final_tool.strip():
                    st.session_state.history.append(
                        {"role": "assistant_tool", "content": final_tool}
                    )
                st.rerun()
            else:
                st.error(resp["error"])

def display_chat_history():
    """
    저장된 대화 기록을 표시합니다.
    """
    for message in st.session_state.history:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("assistant").markdown(message["content"])
        elif message["role"] == "assistant_tool":
            with st.chat_message("assistant").expander("🔧 분석 정보", expanded=False):
                st.markdown(message["content"])

def get_streaming_callback(text_placeholder, tool_placeholder):
    """
    스트리밍 콜백 함수를 생성합니다.
    
    매개변수:
        text_placeholder: 텍스트 응답을 표시할 Streamlit 컴포넌트
        tool_placeholder: 도구 호출 정보를 표시할 Streamlit 컴포넌트
    
    반환값:
        callback_func: 스트리밍 콜백 함수
        accumulated_text: 누적된 텍스트 응답을 저장하는 리스트
        accumulated_tool: 누적된 도구 호출 정보를 저장하는 리스트
    """
    accumulated_text = []
    accumulated_tool = []

    def callback_func(message: dict):
        nonlocal accumulated_text, accumulated_tool
        message_content = message.get("content", None)

        if isinstance(message_content, AIMessageChunk):
            content = message_content.content
            if isinstance(content, list) and len(content) > 0:
                message_chunk = content[0]
                if message_chunk["type"] == "text":
                    accumulated_text.append(message_chunk["text"])
                    text_placeholder.markdown("".join(accumulated_text))
                elif message_chunk["type"] == "tool_use":
                    if "partial_json" in message_chunk:
                        accumulated_tool.append(message_chunk["partial_json"])
                    else:
                        tool_call_chunks = message_content.tool_call_chunks
                        tool_call_chunk = tool_call_chunks[0]
                        accumulated_tool.append(
                            "\n```json\n" + str(tool_call_chunk) + "\n```\n"
                        )
                    with tool_placeholder.expander("🔧 분석 정보", expanded=True):
                        st.markdown("".join(accumulated_tool))
        elif isinstance(message_content, ToolMessage):
            accumulated_tool.append(
                "\n```json\n" + str(message_content.content) + "\n```\n"
            )
            with tool_placeholder.expander("🔧 분석 정보", expanded=True):
                st.markdown("".join(accumulated_tool))
        return None

    return callback_func, accumulated_text, accumulated_tool

async def process_query(query, text_placeholder, tool_placeholder, timeout_seconds=60):
    """
    사용자 질문을 처리하고 응답을 생성합니다.
    
    매개변수:
        query: 사용자가 입력한 질문 텍스트
        text_placeholder: 텍스트 응답을 표시할 Streamlit 컴포넌트
        tool_placeholder: 도구 호출 정보를 표시할 Streamlit 컴포넌트
        timeout_seconds: 응답 생성 제한 시간(초)
    
    반환값:
        response: 에이전트의 응답 객체
        final_text: 최종 텍스트 응답
        final_tool: 최종 도구 호출 정보
    """
    try:
        if st.session_state.agent:
            streaming_callback, accumulated_text_obj, accumulated_tool_obj = (
                get_streaming_callback(text_placeholder, tool_placeholder)
            )
            try:
                response = await asyncio.wait_for(
                    astream_graph(
                        st.session_state.agent,
                        {"messages": [HumanMessage(content=query)]},
                        callback=streaming_callback,
                        config=RunnableConfig(
                            recursion_limit=100, thread_id=st.session_state.thread_id
                        ),
                    ),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                error_msg = f"⏱️ 요청 시간이 {timeout_seconds}초를 초과했습니다. 나중에 다시 시도해 주세요."
                return {"error": error_msg}, error_msg, ""

            final_text = "".join(accumulated_text_obj)
            final_tool = "".join(accumulated_tool_obj)
            return response, final_text, final_tool
        else:
            return (
                {"error": "🚫 에이전트가 초기화되지 않았습니다."},
                "🚫 에이전트가 초기화되지 않았습니다.",
                "",
            )
    except Exception as e:
        import traceback

        error_msg = f"❌ 쿼리 처리 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
        return {"error": error_msg}, error_msg, ""