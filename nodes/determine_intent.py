from graph_state import State
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

# 사용자 의도 파악 노드
def determine_intent(state: State) -> State:
    '''기술적 분석을 할지말지 판단하는 함수'''

    system_prompt = '''Check user messages to determine if technical stock analysis is needed. Return True if required, False if not.'''

    llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.1,
    max_tokens=1024
    )

    response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])
    
    print(response)
    return {"stock_analysis_needed": response}

# 라우팅 함수 - 주식 분석이 필요한지 여부에 따라 경로 결정
def router(state: State):
    if state["stock_analysis_needed"]:
        return "technical_analysis"
    else:
        return "superviser"