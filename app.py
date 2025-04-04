
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.graph import StateGraph, END,START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_teddynote import logging
import streamlit as st
from dotenv import load_dotenv
from langgraph.prebuilt import tools_condition
from utils.visualize import visualize_graph_in_streamlit
from graph_state import State
from nodes.superviser import tool_node, superviser
# from nodes.determine_intent import determine_intent, router


# 환경 변수 로드
load_dotenv()

# LangSmith 로깅 설정
logging.langsmith("pr-dear-ratepayer-64")

memory = MemorySaver()
workflow = StateGraph(State)
# 노드 추가
workflow.add_node("superviser", superviser)
workflow.add_node("tools", tool_node)
# workflow.add_node("determine_intent", determine_intent)

# 엣지 추가
workflow.add_edge(START, "superviser")
workflow.add_conditional_edges("superviser", tools_condition)

# 도구 노드에서 에이전트 노드로 순환 연결
workflow.add_edge("tools", "superviser")

workflow.add_edge("superviser", END)

# 그래프 컴파일
graph = workflow.compile(checkpointer=memory)




config = RunnableConfig(
    recursion_limit=10,  # 최대 10개의 노드까지 방문. 그 이상은 RecursionError 발생
    configurable={"thread_id": "1"},  # 스레드 ID 설정
)

# Streamlit UI


# 사이드바에 그래프 시각화 추가
with st.sidebar:
    st.title("🔺 주식투자를 위한 LangGraph 챗봇")
    st.header("Structure of LangGraph")
    visualize_graph_in_streamlit(graph, xray=False)


# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.title("StockSageAI")
    st.subheader("주식투자를 위한 챗봇입니다. AI에게 투자결정에 도움받을 수 있는 다양한 분석을 요청해보세요!")

# # 스레드 ID 관리 (사용자별로 고유한 대화 스레드)
# if "thread_id" not in st.session_state:
#     import uuid
#     st.session_state.thread_id = str(uuid.uuid4())

# 이전 메시지 표시
for message in st.session_state.messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user"):
            st.write(message.content)
    else:
        with st.chat_message("assistant"):
            st.write(message.content)

# 사용자 입력 처리
if prompt := st.chat_input("메시지를 입력하세요"):
    # 사용자 메시지 표시
    with st.chat_message("user"):
        st.write(prompt)
    # 사용자 메시지 저장
    st.session_state.messages.append(HumanMessage(content=prompt))

    # 응답 준비
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        TOOL_STATUS = None

        with st.spinner("생각중..."):
            # 스트리밍 응답 처리
            for event in graph.stream(
                input={"messages": [("user", prompt)]},
                config=config,
            ):
                for key, value in event.items():
                    if "messages" in value:
                        # 새로운 메시지 내용 추출
                        new_content = value["messages"][-1]
                        tool_call_message = st.empty()
                        # 화면에 메시지 업데이트
                        # tool_call 시작시 알림
                        if hasattr(new_content, 'tool_calls') and new_content.tool_calls:
                            for call in new_content.tool_calls:
                                TOOL_STATUS = f"{call["args"]["query"]}에 관련한 자료 {call["name"]}하는 중..."               
                        elif isinstance(new_content, ToolMessage):
                            if TOOL_STATUS:
                                with st.status(TOOL_STATUS):
                                    st.write(new_content.content)
                        else:
                            message_placeholder.markdown(new_content.content)
                            # 결과에서 AI 응답 추출 및 표시
                            ai_message = new_content
                            st.session_state.messages.append(ai_message)
    
