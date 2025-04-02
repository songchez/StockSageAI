from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END,START
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_teddynote import logging
import streamlit as st
from dotenv import load_dotenv
from tools.search_tools import search_news, search_DDG
from langgraph.prebuilt import ToolNode, tools_condition

tools = [search_news, search_DDG]
tool_node = ToolNode(tools)


# 환경 변수 로드
load_dotenv()

# LangSmith 로깅 설정
logging.langsmith("pr-dear-ratepayer-64")

# LangGraph를 위한 상태 타입 정의
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 채팅 노드 정의
def chatbot(state: State):
    # Gemini 모델 사용
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-pro-exp-03-25",
        temperature=0.1,
        max_output_tokens=2048
    ).bind_tools(tools)

    # 응답 메시지 추가
    return {
        "messages": [llm.invoke(state["messages"])]
    }



memory = MemorySaver()
workflow = StateGraph(State)
# 노드 추가
workflow.add_node("agent", chatbot)
workflow.add_node("tools", tool_node)

# 엣지 추가
workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", tools_condition)

# 도구 노드에서 에이전트 노드로 순환 연결
workflow.add_edge("tools", "agent")

workflow.add_edge("agent", END)

# 그래프 컴파일
graph = workflow.compile(checkpointer=memory)

from utils.visualize import visualize_graph_in_streamlit



config = RunnableConfig(
    recursion_limit=10,  # 최대 10개의 노드까지 방문. 그 이상은 RecursionError 발생
    configurable={"thread_id": "1"},  # 스레드 ID 설정
)

# Streamlit UI


# 사이드바에 그래프 시각화 추가
with st.sidebar:
    st.title("🤖 간단한 LangGraph 챗봇")
    st.header("📊 LangGraph 시각화")
    xray_mode = st.checkbox("X-ray 모드 (상세 정보 표시)", value=False)
    st.write("챗봇 그래프 구조")
    visualize_graph_in_streamlit(graph, xray=xray_mode)


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

    # 그래프 실행
    with st.spinner("생각 중..."):
        result = graph.invoke({"messages": [("user", prompt)]}, config=config)
        
    
    # 결과에서 AI 응답 추출 및 표시
    ai_message = result["messages"][-1]
    st.session_state.messages.append(ai_message)
    
    with st.chat_message("assistant"):
        st.write(ai_message.content)