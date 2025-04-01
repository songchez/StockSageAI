"""
설정 관리 유틸리티

사용자 설정 및 앱 설정을 로드하고 저장하는 기능을 제공합니다.
"""
import json
import os
import streamlit as st

# 기본 파일 경로
CONFIG_DIR = "config"
USER_CONFIG_FILE = os.path.join(CONFIG_DIR, "user_config.json")
APP_CONFIG_FILE = os.path.join(CONFIG_DIR, "app_config.json")

def ensure_config_dir():
    """설정 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

def load_config(config_type="user"):
    """
    설정을 로드합니다.
    
    매개변수:
        config_type: "user" 또는 "app"
    
    반환값:
        설정 사전 (dict)
    """
    ensure_config_dir()
    
    file_path = USER_CONFIG_FILE if config_type == "user" else APP_CONFIG_FILE
    
    # 파일이 없으면 기본값 반환
    if not os.path.exists(file_path):
        return get_default_config(config_type)
    
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"설정 로드 중 오류 발생: {str(e)}")
        return get_default_config(config_type)

def save_config(config, config_type="user"):
    """
    설정을 저장합니다.
    
    매개변수:
        config: 저장할 설정 사전 (dict)
        config_type: "user" 또는 "app"
    
    반환값:
        성공 여부 (bool)
    """
    ensure_config_dir()
    
    file_path = USER_CONFIG_FILE if config_type == "user" else APP_CONFIG_FILE
    
    try:
        with open(file_path, "w") as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        st.error(f"설정 저장 중 오류 발생: {str(e)}")
        return False

def get_default_config(config_type="user"):
    """
    기본 설정을 반환합니다.
    
    매개변수:
        config_type: "user" 또는 "app"
    
    반환값:
        기본 설정 사전 (dict)
    """
    if config_type == "user":
        return {
            "risk_preference": 5,
            "investment_period": "중기 (1-6개월)",
            "investment_amount": 10000,
            "preferred_sectors": [],
            "investment_goal": "균형",
            "trading_style": "스윙 트레이딩",
            "technical_weights": {
                "trend": 0.4,
                "momentum": 0.2,
                "volatility": 0.2,
                "volume": 0.2
            }
        }
    else:  # app config
        return {
            "theme": "light",
            "default_market": "US",
            "mcp_timeout": 60,
            "max_history_size": 100,
            "default_model": "claude-3-7-sonnet-latest"
        }

def get_user_setting(key, default_value=None):
    """
    특정 사용자 설정값을 가져옵니다.
    
    매개변수:
        key: 설정 키
        default_value: 설정이 없을 경우 반환할 기본값
    
    반환값:
        설정값
    """
    config = load_config("user")
    return config.get(key, default_value)

def update_user_setting(key, value):
    """
    특정 사용자 설정값을 업데이트합니다.
    
    매개변수:
        key: 설정 키
        value: 새 설정값
    
    반환값:
        성공 여부 (bool)
    """
    config = load_config("user")
    config[key] = value
    return save_config(config, "user")

def sync_session_to_config():
    """
    세션 상태에서 설정 파일로 값을 동기화합니다.
    """
    config = {}
    
    # 사용자 설정 키 목록
    user_keys = [
        "risk_preference", 
        "investment_period", 
        "investment_amount",
        "preferred_sectors",
        "investment_goal",
        "trading_style"
    ]
    
    # 기술적 분석 가중치 키 목록
    weight_keys = [
        "trend_weight",
        "momentum_weight",
        "volatility_weight",
        "volume_weight"
    ]
    
    # 세션에서 값 가져오기
    for key in user_keys:
        if key in st.session_state:
            config[key] = st.session_state[key]
    
    # 가중치 값 확인 및 저장
    weights = {}
    if all(key in st.session_state for key in weight_keys):
        weights = {
            "trend": st.session_state.trend_weight,
            "momentum": st.session_state.momentum_weight,
            "volatility": st.session_state.volatility_weight,
            "volume": st.session_state.volume_weight
        }
        config["technical_weights"] = weights
    
    # 저장
    return save_config(config, "user")

def sync_config_to_session():
    """
    설정 파일에서 세션 상태로 값을 동기화합니다.
    """
    config = load_config("user")
    
    # 사용자 설정 키 목록
    for key, value in config.items():
        if key != "technical_weights":  # 가중치는 별도 처리
            st.session_state[key] = value
    
    # 가중치 값 설정
    if "technical_weights" in config:
        weights = config["technical_weights"]
        st.session_state.trend_weight = weights.get("trend", 0.4)
        st.session_state.momentum_weight = weights.get("momentum", 0.2)
        st.session_state.volatility_weight = weights.get("volatility", 0.2)
        st.session_state.volume_weight = weights.get("volume", 0.2)
    
    return True