import json
import os
import sys

# PyInstaller --onefile 패키징 시 __file__은 임시 추출 폴더(_MEIPASS)를 가리킴
# exe 옆의 config 파일을 읽으려면 sys.executable 기준으로 경로 설정 필요
if getattr(sys, 'frozen', False):
    SCRIPT_DIR = os.path.dirname(sys.executable)
else:
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "api_config.json")

def get_default_strategy_settings():
    """전략 설정 기본값을 반환합니다."""
    return {
        "STEPS": 10,
        "ENTRY_START": 0.45,
        "ENTRY_END": 0.66,
        "ENTRY_EXPONENT": 3.0,
        "BALANCE_USAGE_PERCENTAGE": 70.0, # (0.7이 아닌 70.0%로 저장)
        "TARGET_LEVERAGE": 15,
        "HEDGE_EMERGENCY_START_RATIO": 50.0,  # Break Even과 청산가 사이 시작 지점 (%)
        "UPTREND_THRESHOLD_2_MULTIPLIER": 2.0,  # 2차 임계값 거리 배수 (1차 임계값의 N배)
        "HEDGE_EXPONENT": 3.0,  # 헷지 곡선 지수 (1.0=선형, 2.0=완만, 3.0=균형, 4.0=가파름)
        "HEDGE_PROTOCOL_ENABLED": True,  # 헷지 프로토콜 활성화 여부
        "HEDGE_PROTOCOL_RETRACEMENT": 50.0,  # 되돌림 비율 (최저가 대비 헷지 진입평균가의 N%)
        "HEDGE_PROTOCOL_TAKE_PROFIT_RATIO": 50.0,  # 익절하는 헷지 수량 비율 (%)
        "MAIN_LIQUIDATION_SAFETY_MARGIN": 0.5,  # 메인 포지션 청산가 안전 마진 (%)
        "HEDGE_LIQUIDATION_SAFETY_MARGIN": 0.5,  # 헷지 포지션 청산가 안전 마진 (%)
        "HEDGE_FRONTLOAD_FINAL_STEP": False,  # 최종단계-1에서 헷지 종료% 도달
        "RESERVE_FUND_RATIO": 0.0,  # 사이클 완료 시 순수익금의 비축금 이체 비율 (%)
        "RESERVE_FUND_USAGE_LOSS_THRESHOLD": 10.0  # 비축금 전액 투입 손실 기준 (%)
    }

def load_config_data():
    """'api_config.json'에서 계정 정보 및 앱 설정을 읽어옵니다."""
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            
            # 이전 버전 호환
            if "accounts" not in data and "app_settings" not in data:
                print("이전 버전 config 감지. 'accounts' 키 하위로 마이그레이션합니다.")
                data = {"accounts": data, "app_settings": {}}
            
            # [추가] 전략 설정 로드
            if "strategy_settings" not in data:
                data["strategy_settings"] = get_default_strategy_settings()
                
            return data
            
    except (FileNotFoundError, json.JSONDecodeError):
        # 기본 구조 생성 후 파일로 저장
        default_data = {
            "accounts": {},
            "app_settings": {},
            "strategy_settings": get_default_strategy_settings()
        }
        save_config_data(default_data)
        print(f"기본 설정 파일 생성: {CONFIG_FILE}")
        return default_data

def save_config_data(config_data):
    """계정 정보 및 앱 설정을 'api_config.json'에 저장합니다."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
        # 저장 완료 (로그 제거)
    except Exception as e:
        print(f"Config 정보 저장 오류: {e}")