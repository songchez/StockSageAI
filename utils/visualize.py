import random
import base64
import streamlit as st
from dataclasses import dataclass
from langgraph.graph.state import CompiledStateGraph
from typing import Optional


@dataclass
class NodeStyles:
    default: str = (
        "fill:#45C4B0, fill-opacity:0.3, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:bold, line-height:1.2"  # 기본 색상
    )
    first: str = (
        "fill:#45C4B0, fill-opacity:0.1, color:#23260F, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"  # 점선 테두리
    )
    last: str = (
        "fill:#45C4B0, fill-opacity:1, color:#000000, stroke:#45C4B0, stroke-width:1px, font-weight:normal, font-style:italic, stroke-dasharray:2,2"  # 점선 테두리
    )


def visualize_graph_in_streamlit(graph: CompiledStateGraph, xray: bool = False, width: Optional[int] = None) -> None:
    """
    Streamlit에서 CompiledStateGraph 객체를 시각화하여 표시합니다.
    
    Args:
        graph: 시각화할 그래프 객체. CompiledStateGraph 인스턴스여야 합니다.
        xray: X-ray 모드로 그래프를 볼지 여부 (노드와 엣지에 대한 자세한 정보 표시)
        width: 이미지 너비 (None인 경우 기본값 사용)
    """
    try:
        if isinstance(graph, CompiledStateGraph):
            # 그래프 PNG 바이너리 데이터 가져오기
            png_data = graph.get_graph(xray=xray).draw_mermaid_png(
                background_color="white",
                node_colors=NodeStyles(),
            )
            
            # 바이너리 데이터를 base64로 인코딩
            b64_data = base64.b64encode(png_data).decode()
            
            # HTML 이미지 태그로 표시
            img_html = f'<img src="data:image/png;base64,{b64_data}" alt="Graph Visualization" '
            if width:
                img_html += f'width="{width}" '
            img_html += '/>'
            
            st.markdown(img_html, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"그래프 시각화 오류: {e}")


def generate_random_hash():
    """무작위 16진수 해시를 생성합니다."""
    return f"{random.randint(0, 0xffffff):06x}"