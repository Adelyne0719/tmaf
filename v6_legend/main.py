# main.py
import logging
import sys
import asyncio
import json
import platform
import subprocess
import threading
import tkinter as tk
import websockets
import time
import datetime
import configparser
import os
import shutil
import aiohttp
import hashlib
import hmac
import urllib.parse

from tkinter import ttk, messagebox
from decimal import Decimal, ROUND_HALF_UP
from binance import AsyncClient
from binance.exceptions import BinanceAPIException
from binance.enums import *

# 모듈 임포트
from gui import GuiManager # GUI 클래스
# === logic 모듈 임포트 방식 수정 ===
from logic import *

# <<< 변경: settings.ini 파일의 절대 경로 생성 >>>
# <<< ❗ 기존 BASE_DIR, SETTINGS_FILE_PATH 정의를 아래 코드로 완전히 교체하세요. ❗ >>>

# --- 핵심 수정: PyInstaller 환경을 고려하여 settings.ini의 영구 경로 설정 ---
def get_persistent_settings_path():
    """
    PyInstaller로 패키징되었는지 여부를 확인하여
    settings.ini 파일의 영구적인 경로를 반환합니다.
    만약 해당 경로에 파일이 없다면, 패키지에 포함된 원본 파일을 복사해줍니다.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller에 의해 패키징된 경우 (.exe로 실행)
        # sys.executable은 .exe 파일의 전체 경로입니다.
        application_path = os.path.dirname(sys.executable)
        # 번들된 원본 settings.ini가 풀리는 임시 디렉토리 내 경로
        # 이 환경에서 __file__은 임시 디렉토리를 가리킵니다.
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        source_path = os.path.join(bundle_dir, 'settings.ini')
    else:
        # 일반 .py 스크립트로 실행된 경우
        application_path = os.path.dirname(os.path.abspath(__file__))
        source_path = os.path.join(application_path, 'settings.ini')

    # 프로그램이 실제로 읽고 쓸 설정 파일의 최종 경로 (.exe 옆)
    persistent_path = os.path.join(application_path, 'settings.ini')

    # 만약 최종 경로에 settings.ini 파일이 없다면 (최초 실행 시),
    # 번들된 원본 파일을 복사해서 새로 생성해 줍니다.
    if not os.path.exists(persistent_path):
        try:
            logging.info(f"설정 파일이 '{persistent_path}'에 없어 새로 생성합니다.")
            shutil.copy2(source_path, persistent_path)
        except Exception as e:
            logging.critical(f"초기 설정 파일 복사에 실패했습니다! 원본: '{source_path}', 대상: '{persistent_path}'. 오류: {e}")
            # GUI가 뜨기 전이므로, 일단 로깅만 처리합니다.
            
    return persistent_path

# settings.ini 파일의 전체 경로를 새 함수를 통해 결정합니다.
SETTINGS_FILE_PATH = get_persistent_settings_path()
# --- 수정 끝 ---

# --- 로깅 설정 ---
log_format = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if logger.hasHandlers(): logger.handlers.clear()
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# --- 윈도우 asyncio 이벤트 루프 설정 ---
if platform.system() == "Windows":
    try: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError: logging.warning("WindowsSelectorEventLoopPolicy 사용 불가")

# --- 전역 상태 변수 ---
client: AsyncClient = None
gui: GuiManager = None
bot_logic_thread = None
asyncio_loop = None
_loop_thread_id = None # 루프 실행 스레드 ID 저장용 전역 변수
main_app_running = False
time_sync_task = None
stop_requested = False # <<< 🟢 이 줄을 추가하세요

class _ConfigProxy:
    _KMAP = {
        '1m': KLINE_INTERVAL_1MINUTE, '3m': KLINE_INTERVAL_3MINUTE, '5m': KLINE_INTERVAL_5MINUTE,
        '15m': KLINE_INTERVAL_15MINUTE, '30m': KLINE_INTERVAL_30MINUTE, '1h': KLINE_INTERVAL_1HOUR,
        '2h': KLINE_INTERVAL_2HOUR, '4h': KLINE_INTERVAL_4HOUR, '6h': KLINE_INTERVAL_6HOUR,
        '8h': KLINE_INTERVAL_8HOUR, '12h': KLINE_INTERVAL_12HOUR, '1d': KLINE_INTERVAL_1DAY,
        '3d': KLINE_INTERVAL_3DAY, '1w': KLINE_INTERVAL_1WEEK, '1M': KLINE_INTERVAL_1MONTH,
    }
    def __init__(self, source: dict):
        self._src = source
    def __getattr__(self, name: str):
        if name == 'KLINE_INTERVAL':
            v = self._src.get('KLINE_INTERVAL')
            if isinstance(v, str): return self._KMAP.get(v, v)
            return v
        return self._src.get(name)
    
app_config = {} # 중앙 설정 딕셔너리
config = _ConfigProxy(app_config)  # ★ 여기서 즉시 바인딩
preferred_signal_type = 'LONG'

# 웹소켓 관련
listen_key = None
keep_alive_task = None
websocket_connection_task = None
open_orders_check_task = None
main_waiting_future: asyncio.Future = None
position_update_task = None # 포지션 업데이트 태스크 변수 추가

# 거래 상태 관련
symbol_info = {}
calculated_min_order_qty = None
leverage_set = False
current_balance = 0.0
last_trigger_order_price = 0.0
nsz_lower_bound = 0.0
nsz_active = False # NSZ가 유효한지 여부 (last_trigger_order_price 기반)
nsz_history = {}
last_trade_realized_pnl = 0.0 # 마지막 거래 실현 손익 저장 (선택적)
last_entry_price = 0.0 # 마지막 완료된 사이클의 평균 진입가 저장
current_step_index = -1
open_orders_state = {}
exit_orders_status = {}
order_type_mapping = {}
order_pnl_accumulator = {}
partial_exit_status = {} # 시나리오 1의 부분 익절 주문 페어 추적용
signal_type = None # 현재 진행중인 시그널 타입 (LONG/SHORT)
pending_entry_info = {
    'active': False,
    'order_ids': [], 
    'step': -1,
    'signal_type': None,
    'attempt_key_prefix': None, 
    'start_time': 0,
    'division_status': {
        'current_sub_order_index_placed': -1, 
        'num_total_divisions_for_step': 0,    
        'base_entry_price_for_step': 0.0,     
        'original_total_quantity_for_step': 0.0, 
        'placed_total_quantity_so_far': 0.0,
        'filled_sub_order_count': 0, # 조건부 시장가 주문 체결 카운트
        'triggers': [], # 조건부 시장가 주문 트리거 목록
        'next_sub_order_to_trigger_index': 0, # 다음에 감시할 트리거 인덱스
        'attempt_key_prefix_internal': None # 내부적으로 사용하는 attempt_key_prefix
    }
}
pending_direct_exit_trigger = {
    'active': False,
    'target_price': 0.0,         # 이 가격 이상이 되면 Trailing Stop 주문 설정
    'quantity': 0.0,             # 청산할 수량
    'avg_entry_price_long': 0.0, # Trailing Stop의 activationPrice 계산에 사용될 수 있음
    'order_mapping_key_suffix': "" # 예: "StepX_DirectExit"
}
step_profit_handler_info = {
    'active': False,                      # 이 로직이 현재 활성화 상태인지 여부
    'step_index_at_trigger': -1,        # 부분 익절 목표가가 설정된 스텝
    'profit_target_price': Decimal('0'),  # 부분 익절 목표가 (1차 익절 가격)
    'partial_market_exit_qty': Decimal('0'), # 시장가로 부분 익절할 수량 (현재 스텝의 헤지 수량)
    'main_pos_side': None,                # 주 포지션 방향 ('LONG' or 'SHORT')
    'tsm_order_id_for_remaining': None,   # 부분 익절 후 잔여 물량에 대한 TSM 주문 ID
    'tsm_order_qty': Decimal('0'),        # TSM 주문으로 설정된 수량
    'tsm_activation_price': Decimal('0'), # TSM 주문의 발동가 (부분 익절가)
    'awaiting_tsm_profitable_fill': False # TSM 주문의 수익성 있는 체결을 기다리는 중인지 여부
}

# 계산된 목록들
entry_quantity_list = []
cumulative_entry_quantity_list = []
per_step_hedge_quantity_list = []
cumulative_hedge_quantity_list = []
exit_ratio_list = []
last_two_candles = []
partially_filled_log = [] 
logged_missing_locally_ids = set() 
recently_expired_main_exit_ids = set()
# 새로 생성된 Algo 주문 보호 (생성 시각 저장)
recently_created_algo_orders = {}  # {algo_id: creation_timestamp}
ALGO_ORDER_PROTECTION_SECONDS = 300  # 5분간 보호



# --- 웹소켓 처리 및 기타 함수 ---
def cancel_main_future(reason="WebSocket error detected"):
    """main_waiting_future를 안전하게 취소합니다."""
    global main_waiting_future, asyncio_loop, _loop_thread_id
    if main_waiting_future and not main_waiting_future.done():
        logging.warning(f"메인 Future 취소 요청: {reason}")
        if asyncio_loop and asyncio_loop.is_running():
            current_thread_id = threading.get_ident()
            schedule_func = None
            if _loop_thread_id is not None and current_thread_id == _loop_thread_id:
                schedule_func = asyncio_loop.call_soon
                logging.debug(f"루프 스레드({current_thread_id})에서 직접 Future 취소 예약 (call_soon 사용).")
            elif _loop_thread_id is not None and current_thread_id != _loop_thread_id:
                schedule_func = asyncio_loop.call_soon_threadsafe
                logging.debug(f"다른 스레드({current_thread_id})에서 루프 스레드({_loop_thread_id})로 Future 취소 예약 (call_soon_threadsafe 사용).")
            else:
                logging.warning(f"루프 스레드 ID를 알 수 없음 ({_loop_thread_id}). Fallback: call_soon_threadsafe 시도.")
                schedule_func = asyncio_loop.call_soon_threadsafe
            try:
                if schedule_func:
                    schedule_func(main_waiting_future.cancel)
                else:
                    logging.error("취소 스케줄링 함수를 결정할 수 없음.")
            except Exception as e:
                logging.error(f"Future 취소 스케줄링 실패: {e}")
        else:
            logging.warning("취소 요청 시 비동기 루프가 실행 중이지 않음.")
    elif main_waiting_future and main_waiting_future.done():
         logging.debug(f"메인 Future 취소 요청 무시: 이미 완료됨 (Reason: {reason})")

async def update_positions_periodically(client: AsyncClient, symbol: str, gui: GuiManager, interval_sec: int = 5):
    """주기적으로 REST API를 통해 포지션 정보를 조회하고 GUI 포지션 표시 업데이트 (타임아웃 에러 처리 강화)"""
    global main_app_running
    logging.info(f"포지션 정보 주기적 업데이트 시작 (간격: {interval_sec}초)")
    
    while main_app_running:
        try:
            if client and gui and main_app_running:
                logging.debug(f"{symbol} 포지션 정보 REST API 조회 시도...")
                positions = await client.futures_position_information(symbol=symbol)
                logging.debug(f"{symbol} 포지션 정보 수신 (REST): {positions}")
                gui.update_position_display(positions, symbol)
            else:
                if not main_app_running: break

            await asyncio.sleep(interval_sec)

        except asyncio.CancelledError:
            logging.info("포지션 업데이트 태스크 취소됨.")
            break
        
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError, TimeoutError):
            logging.warning(f"포지션 업데이트 중 네트워크 타임아웃 발생. 잠시 후 재시도합니다.")
            await asyncio.sleep(interval_sec) # -1000
        
        except BinanceAPIException as e:
            # 타임아웃(-1007)인 경우, 경고만 기록하고 다음 주기에 정상 재시도
            if e.code == -1007:
                logging.warning(f"포지션 업데이트 타임아웃 (코드: {e.code}). 잠시 후 재시도합니다.")
            # 그 외 다른 API 오류는 에러로 기록
            else:
                logging.error(f"포지션 업데이트 중 API 오류 발생 (코드: {e.code}): {e.message}")
            await asyncio.sleep(interval_sec) # 오류 발생 시에도 기본 주기만큼 대기
        
        except Exception as e:
            logging.error(f"포지션 정보 업데이트 중 예상치 못한 오류: {e}", exc_info=True)
            await asyncio.sleep(interval_sec * 2) # 알 수 없는 오류는 조금 더 길게 대기

    logging.info("포지션 정보 주기적 업데이트 종료됨.")

async def get_open_algo_orders(client: AsyncClient, symbol: str):
    """
    Binance Futures Algo Order API로 미체결 Algo 주문 조회
    GET /fapi/v1/algo/openOrders
    """
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v1/algo/openOrders"  # 🔴 엔드포인트 수정
    
    api_key = client.API_KEY
    api_secret = client.API_SECRET
    
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "timestamp": timestamp,
    }
    
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    
    headers = {"X-MBX-APIKEY": api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # [디버그] 원본 응답 구조 확인
                    logging.info(f"[Algo조회] openOrders API 원본 응답: {data}")
                    
                    # 응답이 {"orders": [...]} 형태일 수 있음
                    if isinstance(data, dict) and 'orders' in data:
                        orders = data['orders']
                        return orders
                    elif isinstance(data, list):
                        return data
                    return []
                else:
                    response_text = await response.text()
                    logging.warning(f"Algo 주문 조회 실패: status={response.status}, response={response_text}")
                    return []
    except Exception as e:
        logging.error(f"Algo 주문 조회 예외: {e}")
        return []

async def get_algo_order(client: AsyncClient, symbol: str, algo_id: str):
    """
    특정 Algo 주문 조회
    GET /fapi/v1/algo/order
    """
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v1/algo/order"  # 🔴 엔드포인트 수정 (algoOrder -> algo/order)
    
    api_key = client.API_KEY
    api_secret = client.API_SECRET
    
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "algoId": algo_id,
        "timestamp": timestamp,
    }
    
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    
    headers = {"X-MBX-APIKEY": api_key}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    logging.debug(f"Algo 주문 상세 조회 실패: status={response.status}, response={response_text}")
                    return None
    except Exception as e:
        logging.error(f"Algo 주문 상세 조회 예외: {e}")
        return None

async def check_open_orders_periodically(client: AsyncClient, symbol: str, gui: GuiManager, interval_sec: int = 3):
    """ 주기적으로 REST API를 통해 미체결 주문 목록을 조회하고 로컬 상태와 동기화 (로직 개선 버전) """
    global main_app_running, open_orders_state, order_type_mapping, current_step_index, symbol_info, signal_type, pending_entry_info, recently_created_algo_orders
    
    logging.info(f"미체결 주문 주기적 동기화 시작 (간격: {interval_sec}초)")
    
    # 반복 로그 방지용 이전 상태 저장
    last_logged_stale_ids = set()
    last_logged_algo_count = -1
    last_logged_comparison = None
    
    # 유령 주문 연속 실패 카운터 (Algo API 지연 문제 대응)
    ghost_order_miss_count = {}

    while main_app_running:
        await asyncio.sleep(interval_sec)
        if not main_app_running: break
        
        try:
            if not (client and gui): continue

            # 일반 미체결 주문 조회
            actual_orders = await client.futures_get_open_orders(symbol=symbol)
            actual_order_ids = {str(o['orderId']) for o in actual_orders}
            
            # Algo 미체결 주문도 조회하여 ID 집합에 추가
            actual_algo_orders = await get_open_algo_orders(client, symbol)
            
            # [디버그] Algo Order 응답 구조 확인 - 변경 시에만 로그 출력
            current_algo_count = len(actual_algo_orders) if actual_algo_orders else 0
            if current_algo_count != last_logged_algo_count:
                if actual_algo_orders:
                    logging.info(f"[Algo주문조회] 결과 ({current_algo_count}개): {[{k: v for k, v in o.items() if k in ['algoId', 'orderId', 'clientAlgoId', 'type', 'algoStatus']} for o in actual_algo_orders]}")
                else:
                    logging.info("[Algo주문조회] 결과: 없음")
                last_logged_algo_count = current_algo_count
            
            # algoId 또는 orderId 중 하나라도 있으면 ID 집합에 추가
            actual_algo_order_ids = set()
            for o in actual_algo_orders:
                algo_id = o.get('algoId')
                order_id = o.get('orderId')
                if algo_id:
                    actual_algo_order_ids.add(str(algo_id))
                if order_id:
                    actual_algo_order_ids.add(str(order_id))
            
            # 모든 서버 주문 ID (일반 + Algo)
            all_actual_order_ids = actual_order_ids | actual_algo_order_ids
            
            # [디버그] 비교되는 ID 집합 출력 - 변경 시에만 로그 출력
            current_comparison = (frozenset(actual_order_ids), frozenset(actual_algo_order_ids), frozenset(open_orders_state.keys()))
            if current_comparison != last_logged_comparison:
                logging.info(f"[주문ID비교] 일반: {actual_order_ids}, Algo: {actual_algo_order_ids}, 로컬: {set(open_orders_state.keys())}")
                last_logged_comparison = current_comparison
            
            local_order_ids = set(open_orders_state.keys())
            stale_ids = local_order_ids - all_actual_order_ids
            state_changed_this_cycle = False
            grace_period_seconds = 60.0  # 일반 주문 유예 기간: 60초
            grace_period_algo_seconds = 180.0  # Algo 주문은 더 긴 유예 기간 (180초 = 3분)
            required_miss_count = 5  # 일반 주문: 연속 5회 이상 조회 실패 시에만 제거
            required_miss_count_algo = 15  # Algo 주문: 연속 15회 이상 조회 실패 시에만 제거
            
            # 만료된 보호 주문 정리 및 보호 대상 제외
            current_time = time.time()
            expired_protection = [aid for aid, ts in recently_created_algo_orders.items() 
                                  if current_time - ts > ALGO_ORDER_PROTECTION_SECONDS]
            for aid in expired_protection:
                recently_created_algo_orders.pop(aid, None)
            
            # 보호 대상 Algo 주문은 stale_ids에서 제외
            protected_algo_ids = set(str(aid) for aid in recently_created_algo_orders.keys())
            originally_stale = stale_ids.copy()
            stale_ids = stale_ids - protected_algo_ids
            if originally_stale != stale_ids:
                protected_count = len(originally_stale) - len(stale_ids)
                if protected_count > 0:
                    logging.debug(f"  - {protected_count}개 Algo 주문이 보호 기간 중이므로 유령 의심에서 제외됨")

            if stale_ids:
                # 변경된 경우에만 로그 출력
                if stale_ids != last_logged_stale_ids:
                    logging.info(f"주기적 확인: 로컬에만 존재하는 유령 의심 주문 {len(stale_ids)}개 발견: {stale_ids}")
                    last_logged_stale_ids = stale_ids.copy()
                
                for stale_id in list(stale_ids):
                    local_order_data = open_orders_state.get(stale_id, {})
                    creation_time = local_order_data.get('creationTime', 0)
                    custom_type_name = order_type_mapping.get(stale_id)
                    is_algo_order = local_order_data.get('isAlgoOrder', False)

                    if time.time() - creation_time < grace_period_seconds:
                        logging.debug(f"  - Stale ID {stale_id} ({custom_type_name}) 생성된 지 얼마 안 됨. 제거 보류.")
                        continue
                    
                    # Algo 주문은 더 긴 유예 기간 적용
                    if is_algo_order and time.time() - creation_time < grace_period_algo_seconds:
                        logging.debug(f"  - Algo 주문 ID {stale_id} ({custom_type_name}) 생성된 지 얼마 안 됨 (Algo 유예). 제거 보류.")
                        continue

                    try:
                        # Algo 주문인 경우 Algo API로 조회
                        if is_algo_order:
                            ghost_order_details = await get_algo_order(client, symbol, stale_id)
                            if ghost_order_details:
                                status = ghost_order_details.get('algoStatus', ghost_order_details.get('status'))
                                # 서버에서 조회 성공 시 miss_count 리셋
                                ghost_order_miss_count.pop(stale_id, None)
                            else:
                                # Algo 주문이 서버에 없음 - 연속 실패 카운터 증가
                                ghost_order_miss_count[stale_id] = ghost_order_miss_count.get(stale_id, 0) + 1
                                current_miss = ghost_order_miss_count[stale_id]
                                
                                # Algo 주문은 더 많은 실패를 허용
                                if current_miss >= required_miss_count_algo:
                                    # 연속 N회 이상 조회 실패 시에만 제거
                                    logging.warning(f"  -> Algo 주문({stale_id}, {custom_type_name})이 서버에서 {current_miss}회 연속 조회 실패. 로컬에서 제거.")
                                    open_orders_state.pop(stale_id, None)
                                    order_type_mapping.pop(stale_id, None)
                                    ghost_order_miss_count.pop(stale_id, None)
                                    state_changed_this_cycle = True
                                else:
                                    logging.info(f"  -> Algo 주문({stale_id}, {custom_type_name}) 서버 조회 실패 ({current_miss}/{required_miss_count_algo}). 제거 보류.")
                                continue
                        else:
                            ghost_order_details = await client.futures_get_order(symbol=symbol, orderId=stale_id)
                            status = ghost_order_details.get('status')
                        
                        # --- 🟢 핵심 로직: 체결된 'EntryAttempt' 주문을 최우선으로 처리 ---
                        if status == 'FILLED' and custom_type_name and custom_type_name.startswith('EntryAttempt-'):
                            logging.info(f"  -> 유령 주문({stale_id}, {custom_type_name}) FILLED 확인. 후속 처리 시작.")
                            
                            filled_price = float(ghost_order_details.get('avgPrice', '0'))
                            if filled_price <= 0:
                                logging.error(f"    - 체결 가격({filled_price})이 유효하지 않아 후속 처리를 중단합니다.")
                            else:
                                # 1. 전역 signal_type 설정
                                pos_side = ghost_order_details.get('positionSide')
                                if pos_side in ['LONG', 'SHORT']:
                                    signal_type = pos_side
                                    logging.info(f"    - 전역 signal_type을 '{signal_type}'으로 설정.")

                                # 2. 스텝 업데이트
                                parts = custom_type_name.split('-')
                                filled_step = int(parts[1])
                                if current_step_index < filled_step:
                                    current_step_index = filled_step
                                    if gui: gui.update_current_step(current_step_index)
                                    logging.info(f"    - 현재 스텝을 {current_step_index}(으)로 업데이트.")

                                # 3. NSZ 업데이트
                                calculate_and_update_nsz(filled_price, symbol_info, gui, signal_type, current_step_index)
                                
                                # 4. pending_entry_info 초기화
                                if pending_entry_info.get('active'):
                                    pending_entry_info['active'] = False
                                    logging.info("    - pending_entry_info를 비활성화합니다.")
                                
                                # 5. 다음 주문(TSM, Maginot 등) 설정 함수 호출
                                state_for_logic_call = {
                                    'symbol': symbol, 'open_orders_state': open_orders_state, 'order_type_mapping': order_type_mapping,
                                    'entry_quantity_list': entry_quantity_list, 'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type,
                                    'per_step_hedge_quantity_list': per_step_hedge_quantity_list, 'cumulative_entry_quantity_list': cumulative_entry_quantity_list
                                }
                                logging.info(f"    - 스텝 {current_step_index}의 후속 주문 설정을 위해 logic.place_orders_for_step 호출.")
                                await place_orders_for_step(client, gui, symbol_info, state_for_logic_call, current_step_index, trigger_event='ENTRY_FILL_BY_CHECKER')

                            # 후속 처리 후 로컬 상태에서 제거
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True
                            logging.info(f"    - 후속 처리 완료 후 로컬 상태에서 ID {stale_id} 제거.")

                        elif status in ['CANCELED', 'EXPIRED', 'REJECTED', 'FILLED', 'TRIGGERED']:
                            # EntryAttempt가 아니거나, 다른 종료 상태의 주문 처리
                            # TRIGGERED: Algo 주문이 발동되어 일반 주문으로 변환됨
                            logging.info(f"  -> 유령 주문({stale_id}, {custom_type_name})의 서버 상태 '{status}' 확인. 로컬에서만 제거합니다.")
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True

                    except Exception as e:
                        if hasattr(e, 'code') and e.code == -2013: # Order does not exist
                            logging.warning(f"  -> 유령 주문({stale_id})은 서버에 존재하지 않음. 로컬에서 제거.")
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True
                        else:
                            logging.error(f"  -> 유령 주문({stale_id}) 상세 정보 조회 중 예외: {e}")

            # 서버에만 있는 주문 동기화 로직 (기존과 유사하게 유지)
            missing_locally_ids = actual_order_ids - local_order_ids
            if missing_locally_ids:
                logging.warning(f"주기적 확인: 서버에만 존재하는 주문 {len(missing_locally_ids)}개 발견: {missing_locally_ids}")
                for order_id in list(missing_locally_ids):
                    try:
                        order_detail = await client.futures_get_order(symbol=symbol, orderId=order_id)
                        if order_detail and order_detail.get('status') not in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']:
                             open_orders_state[order_id] = order_detail
                             order_type_mapping.setdefault(order_id, f"SyncedFromServer-{order_detail.get('type','?')}")
                             state_changed_this_cycle = True
                             logging.info(f"  - 서버 주문 ID {order_id} 로컬 상태에 추가됨.")
                    except Exception as e:
                        logging.error(f"서버 주문 ID {order_id} 정보 조회/추가 실패: {e}")
            
            # 유령 주문이 해결되면 로그 상태 초기화 (다음에 다시 발생하면 로그 출력)
            if not stale_ids and last_logged_stale_ids:
                logging.info("주기적 확인: 유령 의심 주문 모두 해결됨.")
                last_logged_stale_ids = set()
            
            # 더 이상 stale하지 않은 주문의 miss_count 정리
            resolved_ids = set(ghost_order_miss_count.keys()) - stale_ids
            for resolved_id in resolved_ids:
                ghost_order_miss_count.pop(resolved_id, None)

            if state_changed_this_cycle and gui:
                gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
        
        except asyncio.CancelledError:
            logging.info("미체결 주문 동기화 태스크 취소됨.")
            break
        
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError, TimeoutError):
            logging.warning(f"[check_open_orders_periodically] 미체결 주문 동기화 중 네트워크 타임아웃 발생. 잠시 후 재시도합니다.")
            await asyncio.sleep(interval_sec)
        
        except Exception as e:
            logging.error(f"[check_open_orders_periodically] 미체결 주문 동기화 중 예외: {e}", exc_info=True)
            await asyncio.sleep(interval_sec)

    logging.info("미체결 주문 주기적 동기화 종료됨.")

async def check_all_positions_closed_and_finalize(client_param: AsyncClient, symbol_param: str, final_realized_pnl_str: str):
    """ 지정된 심볼의 모든 포지션(LONG, SHORT)이 0인지 확인하고, 그렇다면 사이클 종료 및 리셋을 진행합니다. """
    global main_app_running # main_app_running 상태를 확인하여 불필요한 API 호출 방지

    if not main_app_running:
        logging.info("봇이 실행 중이 아니므로 포지션 확인 및 사이클 종료 건너뜁니다.")
        return

    try:
        logging.info(f"[{symbol_param}] 모든 포지션 청산 여부 확인 중...")
        positions = await client_param.futures_position_information(symbol=symbol_param)
        
        long_pos_qty = Decimal('0')
        short_pos_qty = Decimal('0')

        for p_info in positions:
            pos_side = p_info.get('positionSide')
            amt_str = p_info.get('positionAmt', '0')
            try:
                amt = Decimal(amt_str)
                if pos_side == 'LONG':
                    long_pos_qty = amt
                elif pos_side == 'SHORT':
                    short_pos_qty = abs(amt) # SHORT 포지션은 음수이므로 절대값
            except Exception as e:
                logging.error(f"포지션 수량 파싱 오류: {p_info}, 오류: {e}")
                return # 오류 발생 시 추가 진행 방지

        logging.info(f"[{symbol_param}] 현재 포지션 확인 결과: LONG Qty={long_pos_qty}, SHORT Qty={short_pos_qty}")

        # 두 포지션 모두 수량이 0이어야 완전 청산으로 간주
        if long_pos_qty == Decimal('0') and short_pos_qty == Decimal('0'):
            logging.info(f"[{symbol_param}] 모든 관련 포지션 청산 확인됨. 거래 사이클 완료 처리 시작.")
            # finalize_cycle_and_reset 함수는 main.py의 전역 컨텍스트에서 필요한 변수들을 사용
            await finalize_cycle_and_reset(final_realized_pnl_str)
        else:
            logging.info(f"[{symbol_param}] 아직 청산되지 않은 포지션 존재. LONG: {long_pos_qty}, SHORT: {short_pos_qty}. 사이클 종료 대기.")
            # 선택: 아직 다른 Exit 주문(예: HedgeExit)이 남아있을 수 있으므로, 그 주문의 체결을 기다립니다.
            # 만약 모든 Exit 주문이 발송되었음에도 포지션이 남아있다면 경고/오류 처리 필요.
            # 현재 로직에서는 다른 Exit 주문의 FILLED 이벤트에서 다시 이 함수를 호출하게 됩니다.

    except Exception as e:
        logging.error(f"모든 포지션 청산 여부 확인 중 오류 발생: {e}", exc_info=True)
        if gui: gui.update_status("포지션 확인 오류!")

def get_preferred_signal_type():
    """settings.ini에서 POSITION_BIAS(LONG/SHORT)를 안전하게 읽어 반환"""
    try:
        # app_config가 있으면 우선 사용
        return str(app_config.get('POSITION_BIAS', 'LONG')).upper()
    except Exception:
        # 혹시 app_config가 아직 준비 전이면 config 프록시 시도
        try:
            return str(getattr(config, 'POSITION_BIAS', 'LONG')).upper()
        except Exception:
            return 'LONG'

# main.py의 calculate_and_update_nsz 함수를 아래 코드로 교체하세요.

def calculate_and_update_nsz(trigger_price, symbol_info, gui, signal_type: str, step_index_to_save: int):
    """주어진 가격 기준으로 NSZ 경계선을 계산하고 전역 변수 및 GUI를 업데이트 (LONG/SHORT 지원)"""
    global nsz_lower_bound, nsz_active, nsz_history # 변수명은 nsz_lower_bound를 그대로 사용하되, 의미는 경계값으로 통일
    
    nsz_text = "-"; calculated_bound = 0.0; calculation_success = False
    
    if trigger_price > 0 and config.NO_SIGNAL_ZONE > 0 and symbol_info:
        try:
            bound_dec = Decimal('0')
            label = ""
            
            # --- 🟢 핵심 수정: signal_type에 따라 계산 방식과 문구 변경 ---
            if signal_type == 'SHORT':
                # SHORT일 경우: 상한선 계산 (가격 * (1 + 비율))
                bound_dec = Decimal(str(trigger_price)) * (Decimal('1.0') + Decimal(str(config.NO_SIGNAL_ZONE)))
                label = "상한선"
            else: # LONG 또는 기본값
                # LONG일 경우: 하한선 계산 (가격 * (1 - 비율))
                bound_dec = Decimal(str(trigger_price)) * (Decimal('1.0') - Decimal(str(config.NO_SIGNAL_ZONE)))
                label = "하한선"
            # --- 수정 끝 ---
                
            tick_size = symbol_info.get('tickSize')
            if tick_size:
                precision = count_decimal_places(tick_size) 
                rounded_bound_dec = bound_dec.quantize(Decimal('1e-' + str(precision)), rounding=ROUND_HALF_UP)
                calculated_bound = float(rounded_bound_dec)
                nsz_text = f"{label}: {rounded_bound_dec:.{precision}f}"
                calculation_success = True
            else:
                calculated_bound = float(bound_dec)
                nsz_text = f"{label}: {bound_dec} (반올림X)"; calculation_success = True
        except Exception as nsz_calc_err:
            logging.error(f"[calculate_and_update_nsz] NSZ 계산/반올림 중 오류: {nsz_calc_err}", exc_info=True)
            nsz_text = "계산오류"; calculated_bound = 0.0
    
    nsz_lower_bound = calculated_bound # 변수에는 계산된 경계값이 저장됨
    nsz_active = calculation_success and calculated_bound > 0 
    
    # 🟢 계산 성공 시, nsz_history에 현재 스텝 정보와 함께 저장
    if nsz_active:
        nsz_history[step_index_to_save] = {
            'bound': calculated_bound,
            'text': nsz_text,
            'signal_type': signal_type
        }
        logging.info(f"[NSZ History] 스텝 {step_index_to_save}의 NSZ 저장: {nsz_history[step_index_to_save]}")
        
    
    if gui: gui.update_nsz_range(nsz_text)
    logging.info(f"[NSZ Update] Type: {signal_type}, Active: {nsz_active}, Bound: {nsz_lower_bound}")

async def process_kline(msg):
    """ Kline 데이터 처리 및 시그널 확인 (GUI 시그널 현황판 업데이트 로직 최종 수정) """
    global gui, last_two_candles, current_step_index, signal_type, symbol_info, client, config
    global pending_entry_info, step_profit_handler_info 
    global entry_quantity_list, open_orders_state, order_type_mapping, per_step_hedge_quantity_list, cumulative_entry_quantity_list, exit_ratio_list
    global last_trigger_order_price, nsz_active, nsz_lower_bound

    try:
        if msg.get('e') == 'error':
            logging.error(f"Kline 웹소켓 오류: {msg}")
            cancel_main_future("Kline error")
            return

        kline = msg.get('k', {})
        is_closed = kline.get('x', False)

        if is_closed:
            # --- 1. 캔들 정보 업데이트 ---
            open_price_kline = float(kline.get('o', 0))
            close_price_kline = float(kline.get('c', 0))
            high_price_kline = float(kline.get('h', 0))
            low_price_kline = float(kline.get('l', 0))
            volume_kline = float(kline.get('v', 0))
            kline_time_ms = kline.get('T', 0)
            kline_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(kline_time_ms / 1000))
            
            if gui: gui.update_kline_data(f"{kline_time_str} O:{open_price_kline} H:{high_price_kline} L:{low_price_kline} C:{close_price_kline} V:{volume_kline}")

            current_candle_data = {'open': open_price_kline, 'close': close_price_kline, 'high': high_price_kline, 'low': low_price_kline, 'volume': volume_kline, 'time': kline_time_str}
            last_two_candles.append(current_candle_data)
            if len(last_two_candles) > 2:
                last_two_candles.pop(0)

            # --- 2. 타임아웃 처리 ---
            handling_pending_entry_timeout = False
            if pending_entry_info.get('active', False):
                elapsed_seconds_kline = time.time() - pending_entry_info.get('start_time', 0)
                kline_interval_str = str(config.KLINE_INTERVAL)
                min_wait_seconds_for_timeout = 280
                if kline_interval_str == KLINE_INTERVAL_1MINUTE: min_wait_seconds_for_timeout = 50
                elif kline_interval_str == KLINE_INTERVAL_3MINUTE: min_wait_seconds_for_timeout = 170
                
                if elapsed_seconds_kline >= min_wait_seconds_for_timeout:
                    logging.warning(f"진입 시도(pending_entry_info 스텝: {pending_entry_info.get('step')}) 타임아웃. 초기화.")
                    handling_pending_entry_timeout = True
                    pending_entry_info = {'active': False, 'order_ids': [], 'step': -1, 'signal_type': None, 'attempt_key_prefix': None, 'start_time': 0, 'division_status': {}}
                    if gui: gui.update_status(f"스텝 {pending_entry_info.get('step')} 진입 타임아웃.")
            
            # --- 3. 시그널 확인 및 처리 ---
            if not handling_pending_entry_timeout and len(last_two_candles) == 2:
                
                signal_status_msg = "대기 중..."
                
                prev_prev_candle_kline = last_two_candles[0]
                prev_candle_kline = last_two_candles[1]
                current_price_for_signal_check = prev_candle_kline['close']
                ignore_signal_due_to_nsz = False
                detected_kline_signal_type = None
                preferred_bias = get_preferred_signal_type()
                if not signal_type: signal_type = preferred_bias

                # NSZ 조건 확인
                if nsz_active:
                    if preferred_bias == 'LONG' and current_price_for_signal_check >= nsz_lower_bound:
                        ignore_signal_due_to_nsz = True
                        signal_status_msg = f"{kline_time_str} [NSZ] 시그널 무시(LONG) - 현재가({current_price_for_signal_check}) >= 하한선({nsz_lower_bound})"
                    elif preferred_bias == 'SHORT' and current_price_for_signal_check <= nsz_lower_bound:
                        ignore_signal_due_to_nsz = True
                        signal_status_msg = f"{kline_time_str} [NSZ] 시그널 무시(SHORT) - 현재가({current_price_for_signal_check}) <= 상한선({nsz_lower_bound})"

                # NSZ 통과 시 시그널 확인
                if not ignore_signal_due_to_nsz:
                    # LONG 시그널 확인 (음봉 -> 양봉)
                    if preferred_bias == 'LONG':
                        is_prev_prev_bearish = prev_prev_candle_kline['close'] < prev_prev_candle_kline['open']
                        is_prev_bullish = prev_candle_kline['close'] >= prev_candle_kline['open']
                        if is_prev_prev_bearish and is_prev_bullish:
                            denominator = prev_prev_candle_kline['open'] - prev_prev_candle_kline['close']
                            if denominator > 0:
                                ratio = (prev_candle_kline['close'] - prev_candle_kline['open']) / denominator
                                if config.PRICE_RATIO_MIN <= ratio <= config.PRICE_RATIO_MAX:
                                    detected_kline_signal_type = 'LONG'
                    
                    # SHORT 시그널 확인 (양봉 -> 음봉)
                    elif preferred_bias == 'SHORT':
                        is_prev_prev_bullish = prev_prev_candle_kline['close'] > prev_prev_candle_kline['open']
                        is_prev_bearish = prev_candle_kline['close'] < prev_candle_kline['open']
                        if is_prev_prev_bullish and is_prev_bearish:
                            denominator = prev_prev_candle_kline['close'] - prev_prev_candle_kline['open']
                            if denominator > 0:
                                ratio = (prev_candle_kline['open'] - prev_candle_kline['close']) / denominator
                                if config.PRICE_RATIO_MIN <= ratio <= config.PRICE_RATIO_MAX:
                                    detected_kline_signal_type = 'SHORT'
                    
                    # 시그널 발생 여부에 따라 메시지를 최종 결정
                    if detected_kline_signal_type:
                        signal_status_msg = f"{kline_time_str}*** {detected_kline_signal_type} 시그널 발생! ***"
                        logging.info(f"*** {detected_kline_signal_type} 시그널 발생! ***")
                    else:
                        signal_status_msg = f"{kline_time_str}시그널 조건 불충족 (Candle: {prev_candle_kline['time']})"

                # 모든 메시지 결정이 끝난 후, GUI를 한 번만 업데이트
                if gui:
                    gui.update_signal_status(signal_status_msg)

                # 시그널이 발생했을 경우에만 후속 주문 로직 실행
                if detected_kline_signal_type:
                    target_step_for_kline_signal = -1
                    if current_step_index == -1: target_step_for_kline_signal = 0
                    elif 0 <= current_step_index < config.STEPS - 1: target_step_for_kline_signal = current_step_index + 1
                    
                    proceed_with_signal_processing = False
                    if target_step_for_kline_signal != -1 and not pending_entry_info.get('active', False) and not step_profit_handler_info.get('active', False):
                        proceed_with_signal_processing = True

                    if proceed_with_signal_processing:
                        handle_func_to_call_kline = handle_signal if target_step_for_kline_signal == 0 else handle_step_entry_signal
                        logging.info(f"스텝 {target_step_for_kline_signal}: {handle_func_to_call_kline.__name__} 호출 준비...")
                        if gui: gui.update_status(f"스텝 {target_step_for_kline_signal} 시그널 주문 설정 중...")
                        
                        pending_entry_info.update({'active': True, 'step': target_step_for_kline_signal, 'signal_type': detected_kline_signal_type, 'start_time': time.time()})
                        
                        current_state_for_kline_logic_call = {'signal_type': detected_kline_signal_type, 'entry_quantity_list': entry_quantity_list, 'open_orders_state': open_orders_state, 'order_type_mapping': order_type_mapping}
                        
                        success_kline_setup, num_divs_kline, triggers_kline, actual_total_qty_kline, attempt_prefix_kline = await handle_func_to_call_kline(
                            client, gui, symbol_info, current_state_for_kline_logic_call, 
                            **( {'target_step': target_step_for_kline_signal} if handle_func_to_call_kline == handle_step_entry_signal else {} )
                        )
                        if success_kline_setup and triggers_kline:
                            pending_entry_info['attempt_key_prefix'] = attempt_prefix_kline
                            pending_entry_info['division_status'].update({'num_total_divisions_for_step': num_divs_kline, 'original_total_quantity_for_step': actual_total_qty_kline, 'triggers': triggers_kline, 'attempt_key_prefix_internal': attempt_prefix_kline, 'next_sub_order_to_trigger_index': 0})
                            logging.info(f"시그널: 스텝 {target_step_for_kline_signal} 조건부 주문 {num_divs_kline}개 설정 완료.")
                            if gui: gui.update_status(f"스텝 {target_step_for_kline_signal} 조건부 주문 {num_divs_kline}개 설정됨")
                        else:
                            logging.error(f"시그널: 스텝 {target_step_for_kline_signal} 조건부 주문 설정 실패.")
                            pending_entry_info['active'] = False
                            if gui: gui.update_status(f"스텝 {target_step_for_kline_signal} 설정 실패")

    except asyncio.CancelledError:
        logging.info("Kline 처리 태스크 취소됨.")
    except Exception as e_kline:
        logging.error(f"process_kline 처리 중 오류: {e_kline}", exc_info=True)
        if gui: 
            try: gui.update_status("Kline 처리 오류")
            except Exception: pass

async def process_ticker(msg):
    """ Ticker 데이터(실시간 거래 가격) 처리 """
    global gui, client, symbol_info, config, open_orders_state, order_type_mapping, signal_type, current_step_index
    global step_profit_handler_info # 익절 및 복합 시나리오 관리
    global per_step_hedge_quantity_list # 헤지 수량 접근용
    global pending_entry_info # 조건부 시장가 *진입* 주문 관리

    try:
        if not main_app_running: # 봇이 실행 중이 아니면 아무것도 하지 않음
            return

        if msg.get('e') == 'error':
            logging.error(f"Ticker(Trade) 웹소켓 오류: {msg}")
            cancel_main_future("Ticker error") # 메인 루프에 오류 전파 시도
            return

        event_type = msg.get('e')
        if event_type == 'trade': # 실시간 거래 이벤트만 처리
            last_price_str = msg.get('p') # 현재 체결 가격 문자열
            if not last_price_str:
                return # 가격 정보 없으면 처리 불가

            try:
                current_market_price = Decimal(last_price_str) # Decimal로 변환
            except ValueError:
                logging.warning(f"Ticker 수신: 유효하지 않은 가격 형식 ({last_price_str}). 처리 건너뜀.")
                return

            if gui: # GUI에 현재가 업데이트
                gui.update_trade_data(last_price_str)
            
            logging.debug(f"Trade 수신 ({msg.get('s','N/A')}): 가격={current_market_price}")

            if current_market_price <= Decimal('0'): # 유효하지 않은 가격이면 무시
                # logging.warning(f"Ticker 수신: 유효하지 않은 시장가({current_market_price}). 처리 건너뜀.")
                return

            # --- 1. '부분 헤지 익절 후 TSM' 시나리오 처리 (step_profit_handler_info 기반) ---
            if step_profit_handler_info.get('active') and \
               step_profit_handler_info.get('scenario') == 'partial_hedge_exit_then_main_tsm' and \
               not step_profit_handler_info.get('waiting_for_hedge_exit_fill'): # 아직 헤지 익절 주문 체결을 기다리지 않는 상태일 때
                
                target_price_for_hedge_trigger = step_profit_handler_info['profit_target_price_for_hedge_exit']
                main_pos_side_of_handler = step_profit_handler_info['main_pos_side_for_tsm'] # 주 포지션 방향
                current_step_of_handler = step_profit_handler_info['step_index_at_trigger']

                price_condition_met = False
                if main_pos_side_of_handler == 'LONG' and current_market_price >= target_price_for_hedge_trigger:
                    price_condition_met = True
                elif main_pos_side_of_handler == 'SHORT' and current_market_price <= target_price_for_hedge_trigger:
                    price_condition_met = True
                
                if price_condition_met:
                    logging.info(f"*** Ticker: 스텝 {current_step_of_handler} '부분 헤지 익절' 목표가 {target_price_for_hedge_trigger} 도달! (현재가: {current_market_price}) ***")
                    
                    step_profit_handler_info['waiting_for_hedge_exit_fill'] = True # 중복 실행 방지
                    
                    hedge_qty_to_exit = step_profit_handler_info['hedge_exit_quantity']
                    
                    # logic.py의 place_partial_hedge_exit_market_order 함수 호출
                    state_for_hedge_exit_logic = {
                        'symbol': config.SYMBOL,
                        'open_orders_state': open_orders_state,
                        'order_type_mapping': order_type_mapping
                    }

                    # TSM 주문에 필요한 activation_price와 callback_rate를 준비합니다.
                    callback_rate = config.CALLBACK_RATE # config.py에 정의된 값 사용 (예: 0.1)

                    order_data_hedge_exit, success_hedge_exit, err_code_hedge_exit = await place_trailing_stop_exit_order(
                        client=client,
                        symbol_info_local=symbol_info, # logic 함수가 받을 파라미터명에 맞춰 전달
                        state=state_for_hedge_exit_logic,
                        current_step=current_step_of_handler,
                        quantity=float(hedge_qty_to_exit),
                        main_pos_side=main_pos_side_of_handler,
                        callback_rate=callback_rate
                    )

                    if success_hedge_exit and order_data_hedge_exit:
                        # 이 주문 ID를 저장해두었다가, process_user_data에서 체결 확인 후 TSM 실행
                        step_profit_handler_info['hedge_exit_order_id'] = str(order_data_hedge_exit.get('orderId'))
                        logging.info(f"부분 헤지 익절 TSM 주문 요청 성공. ID: {step_profit_handler_info['hedge_exit_order_id']}. 발동 대기 중...")
                        if gui: gui.update_status(f"스텝{current_step_of_handler} 헤지 TSM 요청됨")
                    else:
                        logging.error(f"부분 헤지 익절 TSM 주문 요청 실패. ErrorCode: {err_code_hedge_exit}. 시나리오 중단 가능성.")
                        step_profit_handler_info['active'] = False 
                        step_profit_handler_info['waiting_for_hedge_exit_fill'] = False
            
            # --- (기존에 step_profit_handler_info를 사용하던 다른 시나리오가 있다면 여기에 else if 로 추가) ---
            # 예: elif step_profit_handler_info.get('active') and step_profit_handler_info.get('scenario') == 'some_other_scenario':
            #        # ... 다른 시나리오 처리 ...


            # --- 2. 조건부 시장가 *진입* 주문 트리거 감시 (pending_entry_info 기반) ---
            # 이 로직은 익절 핸들러와 독립적으로, 또는 상호 배제적으로 실행될 수 있습니다.
            # (예: 익절 핸들러가 활성화된 동안에는 새 진입 시도를 막거나, 그 반대)
            # 현재는 두 로직이 병행 가능하다고 가정 (실제로는 전략에 따라 조정 필요)
            if pending_entry_info.get('active') and pending_entry_info['division_status'].get('triggers'):
                division_status = pending_entry_info['division_status']
                triggers_list = division_status.get('triggers', [])
                idx_to_watch = division_status.get('next_sub_order_to_trigger_index', 0)
                
                if 0 <= idx_to_watch < len(triggers_list):
                    trigger_info = triggers_list[idx_to_watch]
                    trigger_price_entry = Decimal(str(trigger_info.get('trigger_price', 0)))
                    trigger_qty_entry = Decimal(str(trigger_info.get('quantity', 0)))
                    trigger_side_entry = trigger_info.get('side') # 'BUY' or 'SELL'
                    
                    entry_condition_met = False
                    if trigger_side_entry == SIDE_BUY and current_market_price <= trigger_price_entry:
                        entry_condition_met = True
                    elif trigger_side_entry == SIDE_SELL and current_market_price >= trigger_price_entry:
                        entry_condition_met = True
                        
                    if entry_condition_met:
                        logging.info(f"*** Ticker: 조건부 시장가 *진입* 트리거! 스텝 {pending_entry_info.get('step')}, 분할 {idx_to_watch+1}/{division_status.get('num_total_divisions_for_step')} ***")
                        logging.info(f"  - 조건: {trigger_side_entry} at/below {trigger_price_entry if trigger_side_entry == SIDE_BUY else ''}{trigger_price_entry if trigger_side_entry == SIDE_SELL else ''}, 현재가: {current_market_price}")
                        
                        # 해당 트리거 주문 실행
                        entry_pos_side = pending_entry_info.get('signal_type') # 'LONG' or 'SHORT'
                        attempt_key_prefix_entry = division_status.get('attempt_key_prefix_internal')
                        
                        # logic.py의 place_triggered_market_order 함수 호출
                        state_for_triggered_entry = {
                            'symbol': config.SYMBOL,
                            'open_orders_state': open_orders_state,
                            'order_type_mapping': order_type_mapping
                        }
                        success_triggered_entry, order_data_triggered_entry = await place_triggered_market_order(
                            client, gui, symbol_info, state_for_triggered_entry,
                            pending_entry_info.get('step'), # 현재 진행 중인 주 스텝
                            idx_to_watch,                   # 현재 분할 인덱스
                            float(trigger_qty_entry),       # 이번 분할 수량
                            trigger_side_entry,             # BUY or SELL
                            entry_pos_side,                 # LONG or SHORT
                            attempt_key_prefix_entry        # 매핑키 생성용 prefix
                        )
                        
                        if success_triggered_entry and order_data_triggered_entry:
                            logging.info(f"조건부 시장가 진입 주문(ID: {order_data_triggered_entry.get('orderId')}) 요청 성공. 다음 분할 대기.")
                            division_status['next_sub_order_to_trigger_index'] = idx_to_watch + 1
                            # 해당 주문의 체결은 process_user_data에서 처리되어 filled_sub_order_count 증가 등의 로직 수행
                        else:
                            logging.error(f"조건부 시장가 진입 주문 요청 실패. 해당 스텝({pending_entry_info.get('step')}) 진입 재시도 또는 중단 필요.")
                            # 실패 시 pending_entry_info를 어떻게 처리할지 정책 필요 (예: 비활성화)
                            # pending_entry_info['active'] = False

                        # 만약 모든 분할 주문이 트리거/요청되었다면 next_sub_order_to_trigger_index는 triggers_list 길이를 넘게 됨
                        if division_status.get('next_sub_order_to_trigger_index', 0) >= len(triggers_list):
                            logging.info(f"스텝 {pending_entry_info.get('step')}의 모든 조건부 진입 분할 주문이 트리거/요청됨.")
                            # active는 유지하되, 모든 주문이 체결될 때까지 기다림 (process_user_data에서 최종 처리)
                            # 또는, 여기서 active를 false로 하고 user_data에서 filled_sub_order_count로 판단할 수도 있음.
                            # 현재 로직은 user_data에서 filled_sub_order_count가 num_total_divisions와 같아지면 pending_entry_info를 비활성화함.
                # (else: 아직 감시할 다음 트리거가 없거나, 모든 트리거가 이미 처리됨)
            # (else: pending_entry_info가 비활성이거나, 트리거 정보가 없음)

    except asyncio.CancelledError:
        logging.info("Ticker 처리 태스크 취소됨.")
    except Exception as e_ticker:
        logging.error(f"process_ticker 처리 중 예외: {e_ticker}", exc_info=True)
        if step_profit_handler_info: # 오류 발생 시 핸들러 안전하게 비활성화
            step_profit_handler_info['active'] = False
            step_profit_handler_info['waiting_for_hedge_exit_fill'] = False
        if pending_entry_info : # 진입 시도 중 오류 시 비활성화
            pending_entry_info['active'] = False
            
        if gui:
            try: gui.update_status("Ticker 처리 오류!")
            except Exception as gui_err_ticker: logging.error(f"Ticker 오류 후 GUI 상태 업데이트 중 추가 오류: {gui_err_ticker}")
   
# main.py 에 추가할 새로운 헬퍼 함수

# main.py의 기존 handle_step_decrement 함수를 아래 코드로 완전히 교체하세요.

async def handle_step_decrement(filled_step: int, previous_exit_price: float, final_pnl_str: str):
    """
    부분 익절 완료 후 스텝을 감소시키고, 현재 평단가 기준으로 NSZ를 재계산합니다. (API 호출 재시도 로직 포함)
    """
    global current_step_index, gui, client, symbol_info, signal_type
    global nsz_lower_bound, nsz_active, nsz_history

    logging.info(f"스텝 {filled_step}의 부분 익절 완료 (체결가: {previous_exit_price}). 현재 스텝({current_step_index})에서 1을 감소시킵니다.")
    current_step_index -= 1
    if gui:
        gui.update_current_step(current_step_index)

    # <<< 🟢 핵심 로직: NSZ를 복원하지 않고, 현재 평단가 기준으로 새로 계산 >>>
    logging.info(f"[NSZ Recalculate] 스텝다운 후 현재 포지션 평단가 기준으로 NSZ 재계산 시작...")
    try:
        if current_step_index >= 0:
            current_avg_price = 0.0
            position_found = False
            
            # --- 재시도 루프 시작 ---
            max_retries = config.ORDER_RETRY_ATTEMPTS
            retry_delay = config.ORDER_RETRY_DELAY_SECONDS
            for attempt in range(max_retries):
                try:
                    positions = await client.futures_position_information(symbol=config.SYMBOL)
                    current_pos = next((p for p in positions if p.get('positionSide') == signal_type), None)
                    
                    if current_pos and float(current_pos.get('positionAmt', '0')) != 0:
                        current_avg_price = float(current_pos.get('entryPrice', '0'))
                        if current_avg_price > 0:
                            position_found = True
                            break # 성공적으로 평단가를 찾았으므로 루프 종료
                    else:
                        # 포지션이 없는 경우도 성공으로 간주하고 루프 종료
                        position_found = False
                        break

                except Exception as e:
                    logging.warning(f"[NSZ Recalculate] 평단가 조회 시도 {attempt + 1}/{max_retries} 실패: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                    else:
                        logging.error("[NSZ Recalculate] 평단가 조회 최종 실패.")
            # --- 재시도 루프 끝 ---

            if position_found and current_avg_price > 0:
                logging.info(f"  -> 현재 포지션 평단가({current_avg_price})를 기준으로 NSZ를 새로 설정합니다.")
                # 기존 NSZ 계산 함수를 호출하여 실시간으로 업데이트 및 저장
                calculate_and_update_nsz(current_avg_price, symbol_info, gui, signal_type, current_step_index)
            else:
                nsz_active = False; nsz_lower_bound = 0.0
                if gui: gui.update_nsz_range("-")
                logging.info("[NSZ Recalculate] 남은 포지션이 없거나 평단가 조회에 실패하여 NSZ를 비활성화합니다.")
        else:
            # 스텝이 -1이 된 경우 NSZ 비활성화
            nsz_active = False; nsz_lower_bound = 0.0
            if gui: gui.update_nsz_range("-")
            logging.info(f"[NSZ Recalculate] 현재 스텝이 {current_step_index}이므로 NSZ를 비활성화합니다.")

    except Exception as e:
        nsz_active = False; nsz_lower_bound = 0.0
        if gui: gui.update_nsz_range("계산 오류")
        logging.error(f"[NSZ Recalculate] NSZ 재계산 중 최상위 오류 발생: {e}", exc_info=True)
    # <<< 수정 끝 >>>

    if current_step_index < 0:
        logging.info(f"현재 스텝이 {current_step_index}이므로, 전체 사이클 초기화를 진행합니다.")
        await finalize_cycle_and_reset(final_pnl_str)
    else:
        logging.info(f"새로운 현재 스텝({current_step_index})에 대한 익절/마지노 주문을 재설정합니다.")
        
        current_state_for_logic = {
            'symbol': config.SYMBOL,
            'open_orders_state': open_orders_state,
            'order_type_mapping': order_type_mapping,
            'entry_quantity_list': entry_quantity_list,
            'exit_ratio_list': exit_ratio_list,
            'signal_type': signal_type,
            'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
            'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
            'previous_exit_price': previous_exit_price
        }
        await place_orders_for_step(client, gui, symbol_info, current_state_for_logic, current_step_index, trigger_event='STEP_DOWN')


async def _wait_for_position_update(client: AsyncClient, symbol: str, position_side: str, expected_qty: Decimal, timeout_sec: int = 7) -> bool:
    """
    지정된 포지션의 수량이 예상 수량과 일치할 때까지 지정된 시간(초) 동안 기다립니다.
    
    :param client: AsyncClient 객체
    :param symbol: 확인할 심볼 (예: 'XRPUSDT')
    :param position_side: 확인할 포지션 ('LONG' 또는 'SHORT')
    :param expected_qty: 기대하는 포지션의 절대 수량 (Decimal)
    :param timeout_sec: 최대 대기 시간 (초)
    :return: 성공 시 True, 타임아웃 시 False
    """
    start_time = time.time()
    logging.info(f"[{position_side} 포지션 업데이트 대기 시작] 목표 수량: {expected_qty}, 최대 대기: {timeout_sec}초")
    
    while time.time() - start_time < timeout_sec:
        try:
            positions = await client.futures_position_information(symbol=symbol)
            for p in positions:
                if p.get('positionSide') == position_side:
                    current_qty = abs(Decimal(p.get('positionAmt', '0')))
                    # 부동소수점 오차를 감안하여 매우 작은 값(epsilon) 이내로 비교
                    if abs(current_qty - expected_qty) < Decimal('1e-8'):
                        logging.info(f"✅ 포지션 업데이트 확인 완료! 현재 수량: {current_qty}")
                        return True
                    else:
                        logging.debug(f"  - 대기 중... (현재: {current_qty}, 목표: {expected_qty})")
            
            await asyncio.sleep(0.5) # 0.25초 간격으로 확인

        except Exception as e:
            logging.error(f"포지션 업데이트 대기 중 오류: {e}")
            await asyncio.sleep(1) # 오류 발생 시 잠시 더 대기

    logging.warning(f"⏰ 포지션 업데이트 시간 초과! ({timeout_sec}초) 목표 수량에 도달하지 못했습니다.")
    return False

async def process_user_data(msg):
    """ User Data Stream 처리 (신규 스텝다운 익절 시나리오 + 기존 로직 통합) """
    global current_balance, gui, config, open_orders_state, order_type_mapping, client, current_step_index, symbol_info, signal_type
    global last_trade_realized_pnl, entry_quantity_list, per_step_hedge_quantity_list, pending_entry_info
    global last_trigger_order_price, cumulative_entry_quantity_list, exit_ratio_list
    global order_pnl_accumulator, recently_expired_main_exit_ids
    global step_profit_handler_info, partial_exit_status # partial_exit_status 추가

    try:
        event_type = msg.get('e')

        if event_type == 'ACCOUNT_UPDATE':
            update_data = msg.get('a', {})
            balances_update = update_data.get('B', [])
            for balance_item in balances_update:
                if balance_item.get('a') == config.BALANCE_ASSET:
                    new_balance = float(balance_item.get('wb', '0'))
                    if abs(new_balance - current_balance) > 1e-9:
                        logging.info(f"잔고 업데이트 감지 ({config.BALANCE_ASSET}): {current_balance:.8f} -> {new_balance:.8f}")
                        current_balance = new_balance
                        if gui: gui.update_balance(f"{current_balance:.8f}")
                    break
            
            positions_update = update_data.get('P', [])
            if positions_update and gui:
                logging.debug(f"ACCOUNT_UPDATE: 포지션 변경 감지 (데이터: {positions_update}). GUI는 주기적 업데이트에 의존.")
            return

        elif event_type == 'ORDER_TRADE_UPDATE':
            order_info = msg.get('o', {})
            order_id_api = order_info.get('i')
            client_order_id_ws = order_info.get('c')
            symbol_ws = order_info.get('s')
            status = order_info.get('X')
            order_type_ws = order_info.get('o')
            side_ws = order_info.get('S')
            pos_side_ws = order_info.get('ps')
            qty_ws_str = order_info.get('q', '0')
            filled_qty_this_event_str = order_info.get('l', '0')
            cum_filled_qty_str = order_info.get('z', '0')
            avg_price_str = order_info.get('ap', '0')
            last_filled_price_str = order_info.get('L', '0')
            realized_profit_str = order_info.get('rp', '0')
            
            logging.info(f"사용자 데이터 수신: OrderID:{order_id_api}, ClientOID:{client_order_id_ws}, Status:{status}, Type:{order_type_ws}, Symbol:{symbol_ws}, Side:{side_ws}, PosSide:{pos_side_ws}, Qty:{qty_ws_str}, Filled(이번):{filled_qty_this_event_str}, CumFilled:{cum_filled_qty_str}, AvgPrice:{avg_price_str}, LastPrice:{last_filled_price_str}, RP:{realized_profit_str}")

            if symbol_ws != config.SYMBOL:
                return 
            
            order_id_str = str(order_id_api)
            state_changed_for_gui_update = False
            reset_cycle_triggered_by_this_event = False
            current_event_pnl = Decimal(realized_profit_str)

            if status in ['PARTIALLY_FILLED', 'FILLED'] and current_event_pnl != Decimal('0'):
                order_pnl_accumulator.setdefault(order_id_str, Decimal('0'))
                order_pnl_accumulator[order_id_str] += current_event_pnl
                logging.info(f"OrderID {order_id_str} PNL 누적: 현재 이벤트 RP={current_event_pnl}, 주문 총 누적 RP={order_pnl_accumulator[order_id_str]}")
                if gui: gui.update_total_pnl(str(current_event_pnl))

            # --- 💡 핵심 수정: 덮어쓰기 방지 로직 적용 ---
            if status in ['NEW', 'PARTIALLY_FILLED']:
                # 주문이 로컬 상태에 이미 존재하면, 웹소켓 정보로 '업데이트' (덮어쓰기 아님)
                if order_id_str in open_orders_state:
                    open_orders_state[order_id_str].update(order_info)
                    logging.debug(f"OrderID {order_id_str}의 기존 정보에 웹소켓 데이터 업데이트.")
                # 주문이 로컬 상태에 없으면, 새로 추가
                else:
                    open_orders_state[order_id_str] = order_info.copy()
                    logging.debug(f"OrderID {order_id_str}를 로컬 상태에 새로 추가.")
                
                # 생성 시간 정보가 없다면 추가
                if 'creationTime' not in open_orders_state[order_id_str]:
                    open_orders_state[order_id_str]['creationTime'] = order_info.get('T', time.time() * 1000) / 1000.0
                
                state_changed_for_gui_update = True
                if status == 'PARTIALLY_FILLED':
                     logging.info(f"주문 {order_id_str} 부분 체결: {order_info.get('l', '0')}@{order_info.get('L', '0')}")
            # --- 수정 끝 ---

            elif status in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']:
                if order_id_str in open_orders_state:
                    open_orders_state.pop(order_id_str, None)
                    state_changed_for_gui_update = True
                
                # orderId로 먼저 매핑 검색
                custom_type_name_on_event = order_type_mapping.get(order_id_str)
                
                # orderId로 못 찾으면 clientOrderId로 검색 (Algo Order의 TSM이 트리거될 때 새 orderId가 생성되지만 clientOrderId는 유지됨)
                mapping_found_by_client_oid = False
                if not custom_type_name_on_event and client_order_id_ws:
                    custom_type_name_on_event = order_type_mapping.get(client_order_id_ws)
                    if custom_type_name_on_event:
                        mapping_found_by_client_oid = True
                        logging.info(f"OrderID {order_id_str}의 매핑을 ClientOrderId({client_order_id_ws})로 찾음: {custom_type_name_on_event}")

                if custom_type_name_on_event:
                    order_total_accumulated_pnl = order_pnl_accumulator.get(order_id_str, Decimal('0'))
                    logging.info(f"주문 {status}: OrderID={order_id_str}, 구분={custom_type_name_on_event}, 주문총누적RP={order_total_accumulated_pnl if status == 'FILLED' else 'N/A'}")

                    # === 1. FILLED 상태일 때만 실행되는 블록 ===
                    if status == 'FILLED':
                        # 1-1. 부분 익절 주문 처리
                        if custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                            parts = custom_type_name_on_event.split('-')
                            step = int(parts[1])

                            # <<< 핵심 수정: 현재 스텝과 주문의 스텝이 일치하는지 확인 >>>
                            if step != current_step_index:
                                logging.warning(f"수신된 익절 주문(스텝 {step})이 현재 스텝({current_step_index})과 다릅니다. 이벤트를 무시합니다.")
                                # 오래된 주문의 정보는 여기서 정리
                                order_type_mapping.pop(order_id_str, None)
                                if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]
                                return # 여기서 함수 처리를 중단하여 더 이상 진행되지 않도록 함
                            # <<< 수정 끝 >>>                            
                            
                            partial_exit_status.setdefault(step, {'main_filled': False, 'hedge_filled': False})
                            is_main_exit = custom_type_name_on_event.startswith('MainPartialExitTSM-')
                            is_hedge_exit = custom_type_name_on_event.startswith('HedgePartialExitSM-')

                            if is_main_exit:
                                partial_exit_status[step]['main_filled'] = True
                                logging.info(f"[부분 익절] 스텝 {step}의 주 포지션 부분 익절(TSM) 체결 완료.")
                            elif is_hedge_exit:
                                partial_exit_status[step]['hedge_filled'] = True
                                logging.info(f"[부분 익절] 스텝 {step}의 헤지 포지션 부분 익절(SM) 체결 완료.")

                            if is_hedge_exit:
                                logging.info(f"*** [시나리오 1] 헤지 익절(SM) 주문 체결! TSM 체결 여부와 관계없이 스텝을 감소시킵니다. ***")
                                # main_tsm_prefix_to_cancel = f'MainPartialExitTSM-{step}'
                                # await cancel_orders_by_prefix(client, config.SYMBOL, open_orders_state, order_type_mapping, main_tsm_prefix_to_cancel)
                                filled_price = float(avg_price_str)
                                final_pnl_for_step = order_pnl_accumulator.get(order_id_str, '0')
                                await handle_step_decrement(step, filled_price, str(final_pnl_for_step))
                                if step in partial_exit_status: del partial_exit_status[step]
                                # orderId와 clientOrderId 둘 다로 매핑 정리 (Algo Order TSM 트리거 시 대응)
                                order_type_mapping.pop(order_id_str, None)
                                if client_order_id_ws:
                                    order_type_mapping.pop(client_order_id_ws, None)
                                # 원래 algoId도 찾아서 정리
                                algo_keys_to_remove = [k for k, v in order_type_mapping.items() if v == custom_type_name_on_event]
                                for k in algo_keys_to_remove:
                                    order_type_mapping.pop(k, None)
                                    open_orders_state.pop(k, None)
                                if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                            elif is_main_exit:
                                all_mappings = list(order_type_mapping.values())
                                corresponding_hedge_order_exists = any(m.startswith(f'HedgePartialExitSM-{step}') for m in all_mappings)
                                if not corresponding_hedge_order_exists:
                                    logging.info(f"*** [시나리오 2] 부분 익절 완료 (대응 헤지 주문 없음). 스텝을 감소시킵니다. ***")
                                    filled_price = float(avg_price_str)
                                    final_pnl_for_step = order_pnl_accumulator.get(order_id_str, '0')
                                    await handle_step_decrement(step, filled_price, str(final_pnl_for_step))
                                    if step in partial_exit_status: del partial_exit_status[step]
                                    # orderId와 clientOrderId 둘 다로 매핑 정리 (Algo Order TSM 트리거 시 대응)
                                    order_type_mapping.pop(order_id_str, None)
                                    if client_order_id_ws:
                                        order_type_mapping.pop(client_order_id_ws, None)
                                    # 원래 algoId도 찾아서 정리 (mapping 값으로 검색)
                                    algo_keys_to_remove = [k for k, v in order_type_mapping.items() if v == custom_type_name_on_event]
                                    for k in algo_keys_to_remove:
                                        order_type_mapping.pop(k, None)
                                        open_orders_state.pop(k, None)
                                    if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]
                                else:
                                    logging.info(f"[시나리오 1 진행중] 주 포지션 TSM 체결 완료. 헤지 익절(SM) 체결 대기.")
                        
                            # --- 🟢 핵심 수정: 아래 elif 블록 전체를 새로 추가하세요. ---
                            elif custom_type_name_on_event.startswith(('MainStopLoss-', 'HedgeTakeProfitTSM-')):
                                logging.info(f"최종 단계 주문(ID: {order_id_str}, Type: {custom_type_name_on_event}) 체결 확인.")
                                final_pnl_for_cycle = str(order_pnl_accumulator.get(order_id_str, '0'))
                                
                                # 모든 포지션이 청산되었는지 최종 확인 후 사이클 리셋 함수를 호출합니다.
                                logging.info("모든 포지션 청산 여부 확인 및 사이클 종료/리셋을 시작합니다.")
                                await check_all_positions_closed_and_finalize(client, config.SYMBOL, final_pnl_for_cycle)
                                reset_cycle_triggered_by_this_event = True
                            # --- 추가 끝 ---
                        
                        elif custom_type_name_on_event.startswith(('EntryAttempt-', 'Maginot-')):
                            
                            # --- 🟢 핵심 수정: 주문 정보에서 signal_type을 확정하고 전역 변수에 설정 ---
                            order_pos_side = order_info.get('ps') # ps는 웹소켓 데이터에서 positionSide를 의미
                            if order_pos_side in ['LONG', 'SHORT']:
                                signal_type = order_pos_side
                                logging.info(f"    체결 주문의 PositionSide({signal_type})를 기반으로 전역 signal_type 설정 완료.")
                            elif not signal_type:
                                signal_type = get_preferred_signal_type()
                                logging.warning(f"    체결 주문에 PositionSide 정보가 없어 설정값({signal_type})으로 전역 signal_type 설정.")
                            # --- 수정 끝 ---
                            
                            is_entry_attempt = custom_type_name_on_event.startswith('EntryAttempt-')
                            prefix_filled = 'EntryAttempt-' if is_entry_attempt else 'Maginot-'
                            parts_filled = custom_type_name_on_event.replace(prefix_filled, '').split('-')
                            filled_step_num = int(parts_filled[0]) if parts_filled and parts_filled[0].isdigit() else -1
                            
                            if filled_step_num != -1:
                                log_prefix_filled = "General(EntryAttempt)" if is_entry_attempt else "Maginot"
                                logging.info(f"{log_prefix_filled} 주문(스텝 {filled_step_num}, ID: {order_id_str}) 체결.")

                                try:
                                    filled_price_for_nsz_calc = float(avg_price_str)
                                    if filled_price_for_nsz_calc > 0:
                                        last_trigger_order_price = filled_price_for_nsz_calc
                                        calculate_and_update_nsz(last_trigger_order_price, symbol_info, gui, signal_type, filled_step_num)
                                except Exception as nsz_err_filled: logging.error(f"NSZ 업데이트 오류 (ID: {order_id_str}): {nsz_err_filled}")

                                if current_step_index < filled_step_num:
                                    current_step_index = filled_step_num
                                    if gui: gui.update_current_step(current_step_index)
                                    logging.info(f"*** 현재 스텝 업데이트 ({log_prefix_filled} 체결): {current_step_index} ***")

                                hedge_qty_for_filled_step = per_step_hedge_quantity_list[filled_step_num]
                                main_side_for_hedge_logic = signal_type or pos_side_ws

                                if not signal_type:
                                    signal_type = main_side_for_hedge_logic
                                    logging.info(f"전역 signal_type 설정됨: {signal_type}")

                                if hedge_qty_for_filled_step > calculated_min_order_qty:
                                    logging.info(f"스텝 {filled_step_num} 체결 후 헤지 주문 실행. 주 방향: {main_side_for_hedge_logic}, 헤지수량: {hedge_qty_for_filled_step}>{calculated_min_order_qty}(최소주문수량)")
                                    state_for_hedge_call = {'symbol': config.SYMBOL, 'open_orders_state': open_orders_state, 'order_type_mapping': order_type_mapping}
                                    await place_hedge_order_for_general(client, gui, symbol_info, state_for_hedge_call, filled_step_num, hedge_qty_for_filled_step, main_side_for_hedge_logic)
                                    logging.info(f"스텝 {filled_step_num} 다음 익절 주문 설정은 헤지 주문 체결 후 진행됩니다.")
                                else:
                                    # 헤지를 건너뛰는 이유를 명확히 로깅
                                    if hedge_qty_for_filled_step > 0:
                                        logging.info(f"스텝 {filled_step_num} 헤지 수량({hedge_qty_for_filled_step})이 최소 주문 수량({calculated_min_order_qty})보다 작아 헤지 주문을 건너뛰고 즉시 익절 주문을 설정합니다.")
                                    elif hedge_qty_for_filled_step == 0:
                                        logging.info(f"스텝 {filled_step_num} 헤지 수량이 0이므로 즉시 다음 익절 주문을 설정합니다.")
                                    
                                    state_for_next_orders_call = {
                                        'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                        'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                        'exit_ratio_list': exit_ratio_list, 'signal_type': main_side_for_hedge_logic,
                                        'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                        'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                        'previous_exit_price': None
                                    }
                                    trigger = 'MAGINOT_FILL' if custom_type_name_on_event.startswith('Maginot-') else 'ENTRY_FILL'
                                    await place_orders_for_step(client, gui, symbol_info, state_for_next_orders_call, current_step_index, trigger_event=trigger)

                        elif custom_type_name_on_event.startswith('HedgeForGeneral-'):
                            logging.info(f"헤지 주문(ID: {order_id_str}, 구분: {custom_type_name_on_event}) 체결 확인.")
                            parts = custom_type_name_on_event.split('-')
                            hedged_step = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1

                            if hedged_step == current_step_index:
                                logging.info(f"스텝 {hedged_step}의 헤지 포지션 생성이 완료되었습니다. API 업데이트를 기다립니다...")
                                
                                # --- ▼▼▼ 핵심 수정 부분 ▼▼▼ ---
                                # 현재 스텝까지의 예상 누적 진입 수량을 계산
                                expected_total_qty = Decimal(str(cumulative_entry_quantity_list[current_step_index]))
                                
                                # 포지션 정보가 업데이트될 때까지 대기
                                update_success = await _wait_for_position_update(client, config.SYMBOL, signal_type, expected_total_qty)
                                
                                if update_success:
                                    logging.info("정확한 포지션 정보 확인 후, 다음 익절 주문 설정을 시작합니다.")
                                    state_for_orders = {
                                        'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                        'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                        'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type,
                                        'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                        'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                        'previous_exit_price': None
                                    }
                                    await place_orders_for_step(client, gui, symbol_info, state_for_orders, current_step_index, trigger_event='HEDGE_COMPLETED')
                                else:
                                    logging.error(f"포지션 정보 업데이트 대기 시간 초과! 스텝 {current_step_index}의 익절 주문 설정을 건너뜁니다. (수동 조치 필요)")
                                    if gui: gui.update_status(f"오류: 스텝 {current_step_index} 포지션 업데이트 실패!")
                                # --- ▲▲▲ 핵심 수정 부분 ▲▲▲ ---
                            else:
                                logging.warning(f"체결된 헤지 주문의 스텝({hedged_step})과 현재 스텝({current_step_index})이 일치하지 않아 추가 작업을 건너뜁니다.")

                        elif custom_type_name_on_event.startswith(('SysClosePos-')):
                            logging.info(f"시스템 주문(ID: {order_id_str}, Type: {custom_type_name_on_event}) 체결.")
                            order_type_mapping.pop(order_id_str, None)
                            if client_order_id_ws:
                                order_type_mapping.pop(client_order_id_ws, None)
                            if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                        else:
                            logging.warning(f"기타 매핑된 주문 '{custom_type_name_on_event}' (ID: {order_id_str}) FILLED.")
                            order_type_mapping.pop(order_id_str, None)
                            if client_order_id_ws:
                                order_type_mapping.pop(client_order_id_ws, None)
                            # 원래 algoId도 찾아서 정리
                            algo_keys_to_remove = [k for k, v in order_type_mapping.items() if v == custom_type_name_on_event]
                            for k in algo_keys_to_remove:
                                order_type_mapping.pop(k, None)
                                open_orders_state.pop(k, None)
                            if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                    # === 2. CANCELED, EXPIRED, REJECTED 상태일 때 실행되는 블록 ===
                    elif status in ['CANCELED', 'EXPIRED', 'REJECTED']:
                        logging.info(f"주문 {status}: OrderID={order_id_str}, 구분={custom_type_name_on_event}")
                        
                        if status == 'EXPIRED' and custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                            logging.warning(f"부분 익절 주문(ID:{order_id_str})이 EXPIRED 상태가 되었습니다. 후속 FILLED 이벤트를 기다립니다. (매핑 정보 유지)")
                        
                        else:
                            logging.error(f"주문(ID:{order_id_str}, 구분:{custom_type_name_on_event})이 {status} 되었습니다.")
                            if custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                                parts = custom_type_name_on_event.split('-')
                                step = int(parts[1])
                                if step in partial_exit_status:
                                    del partial_exit_status[step]
                            
                            order_type_mapping.pop(order_id_str, None)
                            if client_order_id_ws:
                                order_type_mapping.pop(client_order_id_ws, None)
                            # 원래 algoId도 찾아서 정리
                            algo_keys_to_remove = [k for k, v in order_type_mapping.items() if v == custom_type_name_on_event]
                            for k in algo_keys_to_remove:
                                order_type_mapping.pop(k, None)
                                open_orders_state.pop(k, None)
                            if order_id_str in order_pnl_accumulator:
                                del order_pnl_accumulator[order_id_str]
                
                else: # custom_type_name_on_event is None
                    logging.warning(f"OrderID {order_id_str} (상태: {status})에 대한 로컬 매핑 정보 없음.")
                    if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                if state_changed_for_gui_update and gui and not reset_cycle_triggered_by_this_event:
                    gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
        
        
        elif event_type == 'ACCOUNT_CONFIG_UPDATE':
            update_data_cfg = msg.get('ac', {})
            if update_data_cfg and update_data_cfg.get('s') == config.SYMBOL :
                leverage_val = update_data_cfg.get('l')
                if leverage_val is not None:
                    logging.info(f"ACCOUNT_CONFIG_UPDATE: {config.SYMBOL} 레버리지 변경 감지 -> {leverage_val}x (WS)")
                    if gui: gui.update_leverage(f"{leverage_val}x (WS)")

        elif event_type == 'listenKeyExpired':
            logging.warning("Listen Key 만료됨. 웹소켓 재연결 필요.")
            if gui: gui.update_listen_key_status("만료! 재연결 필요")
            cancel_main_future("Listen Key Expired")

    except Exception as e_user_data_outer:
        logging.error(f"[process_user_data] 외부 처리 중 예외: {e_user_data_outer}", exc_info=True)

async def finalize_cycle_and_reset(realized_pnl_for_cycle_str: str):
    """
    거래 사이클 완료 처리:
    모든 주문 취소 -> (이미 모든 포지션 종료 확인됨) -> 상태 초기화 -> 재계산 -> GUI 업데이트 -> 초기 진입.
    """
    global gui, client, open_orders_state, order_type_mapping, symbol_info, calculated_min_order_qty, current_balance
    global entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list
    global order_pnl_accumulator, last_trade_realized_pnl
    global stop_requested

    logging.info(f"*** 거래 사이클 완료 처리 시작 (마지막 Exit 관련 실현 손익: {realized_pnl_for_cycle_str}) ***")
    
    try:
        pnl_value_from_final_exit = float(realized_pnl_for_cycle_str)
        logging.info(f"이번 사이클 마감에 기여한 실현 손익: {pnl_value_from_final_exit:.4f}")
    except ValueError:
        logging.error(f"실현 손익 값 변환 실패: {realized_pnl_for_cycle_str}")

    logging.info("기존 활성 주문(Maginot, Exit, ExitHedge, EntryAttempt 등) 취소 시도...")
    prefixes_to_cancel = ['Maginot-', 'Exit-', 'ExitHedge-', 'EntryAttempt-', 'SubHedge-', 'GeneralHedge-', 'ExitHedgeSub-', 'PartialFillHedge-', 'MainExitTSM-', 'HedgeExitSM-', 'MainPartialExitTSM-', 'HedgePartialExitSM-']
    all_cancelled_ids = []
    tasks = [cancel_orders_by_prefix(client, config.SYMBOL, open_orders_state, order_type_mapping, prefix) for prefix in prefixes_to_cancel]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        prefix = prefixes_to_cancel[i]
        if isinstance(result, Exception):
            logging.error(f"'{prefix}' 접두사 주문 취소 중 오류 발생: {result}", exc_info=False)
        elif isinstance(result, list):
            if result:
                logging.info(f"'{prefix}' 접두사 주문 {len(result)}개 취소 완료. IDs: {result}")
                all_cancelled_ids.extend(result)
            else:
                logging.debug(f"'{prefix}' 접두사를 가진 취소할 주문 없음.")
        else:
            logging.warning(f"'{prefix}' 접두사 주문 취소 결과 타입 불일치: {type(result)}")

    # GUI의 미체결 주문 목록 업데이트 (취소된 주문들 반영)
    # all_cancelled_ids 리스트가 비어있지 않은 경우, 즉 실제로 취소된 주문이 있을 때만 업데이트합니다.
    if gui and all_cancelled_ids: # <<< 수정된 조건문
         logging.debug(f"취소된 주문({len(all_cancelled_ids)}개) 반영 위해 GUI 미체결 주문 목록 업데이트 시도.")
         await asyncio.sleep(0.1) # API 응답 및 로컬 상태 반영 시간 고려
         # open_orders_state와 order_type_mapping은 cancel_orders_by_prefix 내부에서 이미 업데이트되었어야 함
         gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
    elif gui:
        # 취소된 주문이 없더라도, 만약의 경우를 대비해 현재 상태로 한번 업데이트 해주는 것도 고려할 수 있으나,
        # reset_to_initial_state()가 곧 호출되므로 필수는 아님.
        logging.debug("취소된 주문이 없어 미체결 주문 목록 GUI 업데이트 건너뜀 (곧 전체 리셋 예정).")


    logging.info("거래 상태 초기화 진행...");
    reset_global_state()
    
    logging.info("settings.ini 파일에서 설정 값을 다시 로드합니다...")
    load_config_from_ini()

    order_pnl_accumulator.clear()
    logging.info("주문별 PNL 누적기 초기화 완료.")

    if gui:
        gui.reset_to_initial_state()
        gui.update_nsz_range("-")
        gui.update_status("재계산 및 재진입 준비 중...")

    try:
        new_current_balance, _ = await get_futures_balance(client, config.BALANCE_ASSET, gui)
        current_balance = new_current_balance
    except Exception as e:
        logging.error(f"잔고 재조회 실패: {e}. 이전 잔고로 재계산 시도.")

    try:
        logging.info("사이클 리셋 후 레버리지 재설정 시도...")
        await set_leverage(client, config.SYMBOL, config.TARGET_LEVERAGE, gui)
    except Exception as e:
        logging.error(f"리셋 중 레버리지 재설정 실패: {e}")

    recalc_success = await recalculate_all_data(client, gui, symbol_info, calculated_min_order_qty, current_balance)

    if gui:
        try:
            if symbol_info:
                 info_text = (f"수량(정밀도:{symbol_info.get('quantityPrecision','?')}, 최소:{symbol_info.get('minQty','?')}, 스텝:{symbol_info.get('stepSize','?')}), "
                              f"가격(정밀도:{symbol_info.get('pricePrecision','?')}, 스텝:{symbol_info.get('tickSize','?')}), 최소금액:{symbol_info.get('minNotional','?')}USDT")
                 gui.update_symbol_info(info_text)
            else:
                gui.update_symbol_info("정보 없음 (재조회 필요)")

            if calculated_min_order_qty is not None and symbol_info:
                decimals = count_decimal_places(symbol_info.get('stepSize', '0'))
                min_qty_str_display = f"{calculated_min_order_qty:.{decimals}f}"
                gui.update_min_qty(min_qty_str_display)
            else:
                gui.update_min_qty("N/A (재조회 필요)")

            logging.info("GUI 기본 정보 필드 업데이트 완료 (재계산 후).")
            gui.update_status("재계산 완료, 재진입 준비 중...")
        except Exception as gui_update_err:
            logging.error(f"Reset 후 GUI 기본 정보 업데이트 중 오류: {gui_update_err}")
            if gui: gui.update_status("GUI 업데이트 오류")

    if stop_requested:
        logging.info("예약된 정지 요청에 따라 봇을 완전히 종료합니다.")
        if gui: gui.update_status("예약 정지 실행...")
        stop_bot_logic() # 실제 종료 함수 호출
        return # 더 이상 진행하지 않고 함수를 빠져나감

    if recalc_success:
        if config.AUTO_START_ON_RUN:
            await trigger_initial_entry(client, gui)
        else:
            logging.info("AUTO_START_ON_RUN이 False이므로 자동 재진입 안 함. GUI에서 시작 필요.")
            if gui: gui.update_status("재계산 완료. 수동 시작 대기.")
    else:
        logging.error("데이터 재계산 실패로 초기 진입 불가.")
        if gui: gui.update_status("재계산 오류. 수동 조치 필요.")

    logging.info(f"사이클 완료 및 재시작 처리 완료 (다음 사이클 준비됨). 현재 누적 PNL(GUI): {gui.cumulative_pnl if gui else 'N/A'}")

async def recalculate_all_data(client: AsyncClient, gui: GuiManager, symbol_info_local: dict, min_order_qty_local: float, current_balance_local: float):
    """모든 필요한 수량/비율 목록을 다시 계산하고 전역 변수를 업데이트합니다."""
    global entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list, calculated_min_order_qty
    logging.info("데이터 재계산 시작...")
    try:
        if not symbol_info_local or min_order_qty_local is None or current_balance_local <= 0:
             raise ValueError(f"재계산을 위한 사전 조건 부족/오류: symbol_info={bool(symbol_info_local)}, min_order_qty={min_order_qty_local}, current_balance={current_balance_local}")
        entry_ok, entry_list_new, cumul_entry_list_new = await calculate_entry_quantities(client, config.SYMBOL, symbol_info_local, min_order_qty_local, current_balance_local, gui)
        if not entry_ok: raise Exception("진입 수량 계산 실패")
        entry_quantity_list = entry_list_new; cumulative_entry_quantity_list = cumul_entry_list_new
        
        hedge_ok, step_hedge_list_new, cumul_hedge_list_new = await calculate_hedge_quantities(symbol_info_local, entry_quantity_list, cumulative_entry_quantity_list, min_order_qty_local, gui)
        if not hedge_ok: raise Exception("헷지 수량 계산 실패")
        per_step_hedge_quantity_list = step_hedge_list_new; cumulative_hedge_quantity_list = cumul_hedge_list_new

        # 헷지 수량 최소 주문량 체크 (스텝 0 제외)
        for i in range(1, len(per_step_hedge_quantity_list)):
            if per_step_hedge_quantity_list[i] > 0 and per_step_hedge_quantity_list[i] < calculated_min_order_qty:
                warning_msg = f"경고: 스텝 {i}의 헷지 수량({per_step_hedge_quantity_list[i]})이 최소 주문 수량({calculated_min_order_qty})보다 작습니다. 잔고 부족 또는 설정 오류 가능성."
                logging.warning(warning_msg)
                if gui: gui.update_status(warning_msg) # 상태창에 경고 표시 (일시적)
                # 사용자에게 더 명확한 알림을 원하면 별도의 GUI 요소나 팝업 고려

        exit_ok, exit_ratios_new = await calculate_exit_ratios(gui)
        if not exit_ok: raise Exception("Exit 비율 계산 실패")
        exit_ratio_list = exit_ratios_new
        logging.info("데이터 재계산 완료.")
        return True
    except Exception as e:
        logging.error(f"데이터 재계산 중 오류: {e}", exc_info=True)
        entry_quantity_list, cumulative_entry_quantity_list = [], []; per_step_hedge_quantity_list, cumulative_hedge_quantity_list = [], []; exit_ratio_list = []
        return False

# main.py의 trigger_initial_entry 함수를 아래 코드로 교체하세요.

async def trigger_initial_entry(client_param: AsyncClient, gui_param: GuiManager):
    """ 초기 시그널에 따라 스텝 0 General 주문(시장가)을 즉시 실행 """
    global current_step_index, pending_entry_info, config, symbol_info, entry_quantity_list
    global open_orders_state, order_type_mapping

    if pending_entry_info.get('active', False):
        logging.warning("Initial entry trigger: 이미 다른 진입 시도가 진행 중입니다. 건너뜁니다.")
        return False
    if current_step_index != -1:
        logging.warning(f"이미 거래 진행 중(스텝 {current_step_index}), 초기 진입 건너뛰기.")
        return False

    logging.info("=== 초기 General 주문 (스텝 0, 시장가) 실행 시도 ===")
    if gui_param: gui_param.update_status("초기 시장가 주문 실행 중...")

    target_step_for_initial_entry = 0
    # settings.ini 또는 GUI 토글에서 설정한 값을 가져옵니다.
    current_signal_type_for_initial_entry = get_preferred_signal_type()

    if not entry_quantity_list or target_step_for_initial_entry >= len(entry_quantity_list):
        logging.error(f"초기 진입: 스텝 {target_step_for_initial_entry} 진입 수량 정보 없음.")
        if gui_param: gui_param.update_status("초기 진입 실패 (수량 정보 없음)")
        return False

    quantity_for_step0 = entry_quantity_list[target_step_for_initial_entry]
    if quantity_for_step0 <= 0:
        logging.error(f"초기 진입: 스텝 {target_step_for_initial_entry} 진입 수량이 0 이하입니다.")
        if gui_param: gui_param.update_status("초기 진입 실패 (수량 0)")
        return False

    pending_entry_info['active'] = True
    pending_entry_info['step'] = target_step_for_initial_entry
    pending_entry_info['signal_type'] = current_signal_type_for_initial_entry
    base_attempt_key_prefix = f"EntryAttempt-{target_step_for_initial_entry}-{int(time.time())}"
    pending_entry_info['attempt_key_prefix'] = base_attempt_key_prefix
    pending_entry_info['start_time'] = time.time()
    pending_entry_info['order_id'] = None 

    current_state_for_logic_call = {
        'symbol': config.SYMBOL,
        'open_orders_state': open_orders_state,
        'order_type_mapping': order_type_mapping
    }

    # --- 🟢 핵심 수정: place_general_order_market 함수에 signal_type 전달 ---
    order_data, success, _ = await place_general_order_market(
        client_param, gui_param, symbol_info, current_state_for_logic_call,
        target_step_for_initial_entry,
        quantity_for_step0,
        base_attempt_key_prefix,
        current_signal_type_for_initial_entry # 🟢 포지션 기준을 전달
    )
    # --- 수정 끝 ---

    if success and order_data:
        order_id_for_pending = str(order_data.get('orderId'))
        pending_entry_info['order_id'] = order_id_for_pending
        logging.info(f"초기 General 주문 (스텝 0) 요청 성공. OrderID: {order_id_for_pending}. 체결 대기 중...")
        if gui_param: gui_param.update_status(f"초기 주문(ID:{order_id_for_pending}) 요청됨. 체결 대기.")
        return True
    else:
        logging.error(f"초기 General 주문 (스텝 0) 요청 실패.")
        pending_entry_info['active'] = False
        if gui_param: gui_param.update_status("초기 주문 실패")
        return False
  
async def advance_to_next_step(client_param: AsyncClient, gui_param: GuiManager, symbol_info_local: dict, state_local: dict, filled_maginot_step: int):
    """Maginot 주문 체결 후 다음 스텝으로 진행하는 로직"""
    global current_step_index, last_entry_price, entry_quantity_list, cumulative_entry_quantity_list, exit_ratio_list, config, per_step_hedge_quantity_list, exit_orders_status
    open_orders_state_local = state_local.get('open_orders_state', {}); order_type_mapping_local = state_local.get('order_type_mapping', {})
    symbol_local = state_local.get('symbol'); signal_type_from_state_local = state_local.get('signal_type')
    remaining_maginot_orders = False; maginot_prefix_for_step = f'Maginot-{filled_maginot_step}-'
    for key, custom_type in order_type_mapping_local.items():
        if custom_type.startswith(maginot_prefix_for_step) and key in open_orders_state_local:
            remaining_maginot_orders = True; logging.debug(f"스텝 {filled_maginot_step}의 남은 미체결 Maginot 주문 발견: {key}. 스텝 진행 보류."); break
    if not remaining_maginot_orders:
        logging.info(f"[스텝 {filled_maginot_step}] Maginot 주문 모두 체결/처리 완료 확인.")
        next_step = filled_maginot_step 
        try:
            logging.info(f"[스텝 {next_step}] 포지션 정보 조회 (진입가 업데이트 및 다음 주문 생성용)")
            if not signal_type_from_state_local: logging.error("advance_to_next_step: signal_type을 알 수 없어 포지션 조회 불가.")
            else:
                positions = await client_param.futures_position_information(symbol=symbol_local)
                current_pos = next((p for p in positions if p.get('positionSide') == signal_type_from_state_local), None)
                if current_pos and float(current_pos.get('positionAmt', '0')) != 0:
                    new_avg_entry_price = float(current_pos.get('entryPrice', '0'))
                    if new_avg_entry_price > 0: logging.info(f"스텝 {next_step} 진입 후 평균 진입가 업데이트: {new_avg_entry_price}"); last_entry_price = new_avg_entry_price 
                    else: logging.warning(f"스텝 {next_step} 진입 후 유효하지 않은 평균 진입가 수신: {new_avg_entry_price}")
                else: logging.warning(f"스텝 {next_step} 진입 후 포지션 정보 조회 실패 또는 포지션 없음 (Target Side: {signal_type_from_state_local}).")
        except Exception as e: logging.error(f"스텝 {next_step} 진입 후 포지션 정보 조회/처리 오류: {e}")
        
        if 0 <= next_step < len(per_step_hedge_quantity_list): # Maginot 스텝 헤지 주문
            hedge_qty_for_this_maginot_step = per_step_hedge_quantity_list[next_step]
            if hedge_qty_for_this_maginot_step > 0:
                if signal_type_from_state_local: 
                    logging.info(f"[Maginot 체결 후 헤지] 스텝 {next_step} 진입에 따른 전체 헤지 주문 시도. 수량: {hedge_qty_for_this_maginot_step}, 주 포지션: {signal_type_from_state_local}")
                    state_for_maginot_hedge_call = {'symbol': symbol_local, 'open_orders_state': open_orders_state_local, 'order_type_mapping': order_type_mapping_local}
                    await place_maginot_step_hedge_order(client_param, gui_param, symbol_info_local, state_for_maginot_hedge_call, next_step, hedge_qty_for_this_maginot_step, signal_type_from_state_local)
                else: logging.warning(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 주문 불가: 주 포지션 사이드(signal_type) 알 수 없음.")
            else: logging.info(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 수량이 0입니다. 헤지 주문을 건너뜁니다.")
        else: logging.warning(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 주문 불가: 유효하지 않은 스텝이거나 헤지 수량 목록에 접근할 수 없습니다.")
        
        current_step_index = next_step
        if gui_param: gui_param.update_current_step(current_step_index) 
        logging.info(f"*** 현재 스텝 업데이트: {current_step_index} ***")
        current_state_for_orders = {'symbol': symbol_local, 'current_step_index': current_step_index, 'open_orders_state': open_orders_state_local, 'order_type_mapping': order_type_mapping_local, 'maginot_ratio': config.MAGINOT, 'entry_quantity_list': entry_quantity_list, 'cumulative_entry_quantity_list': cumulative_entry_quantity_list, 'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type_from_state_local}
        logging.debug(f"advance_to_next_step: Calling place_orders_for_step with state: {current_state_for_orders}")
        await place_orders_for_step(client_param, gui_param, symbol_info_local, current_state_for_orders, current_step_index, exit_orders_status, trigger_event='HEDGE_COMPLETED')
    else: logging.debug(f"스텝 {filled_maginot_step}의 Maginot 주문이 아직 남아있어 다음 스텝 진행 대기.")

async def keep_alive_listen_key(client_param: AsyncClient):
    """ Listen Key를 주기적으로 갱신하고, 실패 시 (특히 -1125 오류) 웹소켓 재연결을 트리거합니다. """
    global listen_key, gui, main_app_running
    logging.info("Listen Key 갱신 태스크 시작됨.")
    while main_app_running:
        try:
            # 30분(1800초) 대기
            await asyncio.sleep(30 * 60)
            
            if not main_app_running: break # 대기 후 다시 한번 앱 실행 상태 확인

            if listen_key:
                await client_param.futures_stream_keepalive(listenKey=listen_key)
                now_str = datetime.datetime.now().strftime('%H:%M:%S')
                logging.info(f"Listen Key 갱신 성공 ({now_str})")
                if gui: gui.update_listen_key_status(f"성공 ({now_str})")
            else:
                logging.warning("Listen Key 없음, 갱신 건너뛰기.")

        except asyncio.CancelledError:
            logging.info("Listen Key 갱신 태스크 취소됨.")
            break
            
        except Exception as e:
            now_str = datetime.datetime.now().strftime('%H:%M:%S')
            logging.error(f"Listen Key 갱신 오류 ({now_str}): {e}")
            if gui: gui.update_listen_key_status(f"실패 ({now_str})")

            # <<< 🟢 핵심 수정: -1125 오류 감지 및 재연결 트리거 >>>
            # APIError 객체이고, 코드가 -1125("This listenKey does not exist.")인 경우
            if hasattr(e, 'code') and e.code == -1125:
                logging.warning("Listen Key가 무효화되었습니다. 전체 웹소켓 재연결을 시작합니다.")
                if gui: gui.update_status("Listen Key 무효. 재연결 시도...")
                
                # 메인 루프의 대기를 중단시켜 재연결 절차를 밟도록 함
                cancel_main_future("Listen Key Invalidated (-1125)")
                
                # 재연결이 시작될 때까지 이 태스크는 잠시 대기
                await asyncio.sleep(15)
            else:
                # 그 외의 오류일 경우, 60초 후 다시 시도
                await asyncio.sleep(60)
            # <<< 수정 끝 >>>

    logging.info("Listen Key 갱신 태스크 종료됨.")

async def start_websockets(client_param: AsyncClient):
    global listen_key, keep_alive_task, websocket_connection_task, gui, config
    await stop_websockets(); listen_key = None; keep_alive_task = None; websocket_connection_task = None
    try:
        if gui: gui.update_status("Listen Key 발급 중...")
        logging.info("Listen Key 발급 시도..."); listen_key = await client_param.futures_stream_get_listen_key()
        if not listen_key: logging.error("Listen Key 발급 실패!"); return False
        logging.info(f"Listen Key 발급 성공: {listen_key[:10]}...")
        keep_alive_task = asyncio.create_task(keep_alive_listen_key(client_param))
        kline_stream = f"{config.SYMBOL.lower()}@kline_{config.KLINE_INTERVAL}"; trade_stream = f"{config.SYMBOL.lower()}@trade"; user_stream = listen_key
        streams = [kline_stream, trade_stream, user_stream]; combined_url = f"{config.WS_URL}?streams={'/'.join(streams)}"
        if gui: gui.update_status("웹소켓 연결 중...")
        logging.info("웹소켓 처리 태스크 생성 시도...")
        ws_task = asyncio.create_task(handle_combined_stream(combined_url), name="CombinedStream")
        websocket_connection_task = asyncio.gather(ws_task)
        logging.info("웹소켓 스트림 처리 태스크 시작 요청 완료.")
        return True
    except asyncio.CancelledError: logging.info("웹소켓 시작 중 취소됨."); await stop_websockets(); return False
    except Exception as e: logging.error(f"웹소켓 시작 중 예외 발생: {e}", exc_info=True); await stop_websockets(); return False

async def handle_combined_stream(url):
    global main_waiting_future, gui, main_app_running, listen_key # main_app_running, listen_key 추가
    reconnect_attempts = 0; max_reconnect_attempts = 5
    logging.info(f"Combined 스트림 핸들러 시작: {url}")
    if gui: gui.update_kline_status("연결 중..."); gui.update_trade_status("연결 중..."); gui.update_user_status("연결 중...")
    while main_app_running and reconnect_attempts < max_reconnect_attempts:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                logging.info(f"웹소켓 연결 성공: {url}"); reconnect_attempts = 0
                if gui: gui.update_kline_status("연결됨"); gui.update_trade_status("연결됨"); gui.update_user_status("연결됨")
                
                # 주기적 상태 업데이트를 위한 변수
                last_status_update_time = time.time()
                status_update_interval = 5  # 5초마다 상태 업데이트

                async for message in websocket:
                    # 주기적으로 GUI 상태를 '연결됨'으로 갱신
                    current_time = time.time()
                    if current_time - last_status_update_time > status_update_interval:
                        if gui:
                            # logging.debug("### GUI: 웹소켓 '연결됨' 상태 주기적 갱신 ###") # 디버깅 시 주석 해제하여 사용
                            gui.update_kline_status("연결됨")
                            gui.update_trade_status("연결됨")
                            gui.update_user_status("연결됨")
                        last_status_update_time = current_time
                    
                    logging.debug(f"메시지 수신: {message[:150]}...")
                    try:
                        data = json.loads(message)
                        if 'stream' in data:
                            stream_name = data['stream']; payload = data['data']
                            if not main_app_running: break
                            if 'kline' in stream_name: await process_kline(payload)
                            elif 'trade' in stream_name: await process_ticker(payload)
                            elif listen_key in stream_name: await process_user_data(payload) # listen_key 사용
                        else: logging.warning(f"알 수 없는 메시지 형식: {data}")
                    except json.JSONDecodeError: logging.warning(f"JSON 디코딩 오류: {message}")
                    except Exception as e: logging.error(f"메시지 처리 중 오류: {e}", exc_info=True)
        except websockets.exceptions.ConnectionClosedError as e: logging.warning(f"웹소켓 연결 종료됨: {e}. 재연결 시도 ({reconnect_attempts + 1}/{max_reconnect_attempts})..."); gui.update_kline_status("재연결중"); gui.update_trade_status("재연결중"); gui.update_user_status("재연결중")
        except asyncio.CancelledError: logging.info("스트림 핸들러 취소됨."); break
        except Exception as e: logging.error(f"웹소켓 연결/처리 중 오류: {e}", exc_info=True); gui.update_kline_status("연결 오류"); gui.update_trade_status("연결 오류"); gui.update_user_status("연결 오류")
        reconnect_attempts += 1
        if main_app_running and reconnect_attempts < max_reconnect_attempts:
            wait_time = min(config.RECONNECT_DELAY, 2**(reconnect_attempts))
            logging.info(f"{wait_time}초 후 재연결 시도...")
            try: await asyncio.sleep(wait_time)
            except asyncio.CancelledError: logging.info("대기 중 스트림 핸들러 취소됨."); break
    logging.warning("스트림 핸들러 종료 (최대 재연결 시도 도달 또는 앱 종료)")
    if gui: gui.update_kline_status("종료됨"); gui.update_trade_status("종료됨"); gui.update_user_status("종료됨")
    cancel_main_future("Stream handler stopped")

async def stop_websockets():
    global listen_key, keep_alive_task, websocket_connection_task
    logging.info("웹소켓 정리 시작...")
    if keep_alive_task and not keep_alive_task.done(): keep_alive_task.cancel(); await asyncio.wait([keep_alive_task], timeout=1)
    if websocket_connection_task and not websocket_connection_task.done(): websocket_connection_task.cancel(); await asyncio.wait([websocket_connection_task], timeout=1)
    listen_key = None; keep_alive_task = None; websocket_connection_task = None
    logging.info("웹소켓 정리 완료.")

async def check_and_sync_time_periodically(client_param: AsyncClient, gui_param: GuiManager, interval_seconds: int = 3600):
    global main_app_running
    logging.info(f"시간 동기화 확인 태스크 시작 (간격: {interval_seconds}초)")
    max_timeout_retries = 3; timeout_retry_delay = 5 
    while main_app_running:
        try:
            current_retry = 0
            while current_retry < max_timeout_retries:
                try:
                    server_time_response = await client_param.futures_time()
                    server_time_ms = server_time_response['serverTime']; local_time_ms = int(time.time() * 1000)
                    time_diff_ms = abs(server_time_ms - local_time_ms)
                    logging.info(f"시간 차이 확인: {time_diff_ms}ms (서버: {server_time_ms}, 로컬: {local_time_ms})")
                    if time_diff_ms > config.TIME_DRIFT_THRESHOLD_MS:
                        logging.warning(f"시간 차이 {time_diff_ms}ms 가 임계값 {config.TIME_DRIFT_THRESHOLD_MS}ms 초과")
                        if platform.system() == "Windows": 
                            logging.info("Windows 시간 동기화 시도...")
                            sync_success = await sync_windows_time()
                            if sync_success: logging.info("Windows 시간 동기화 명령 실행 완료.")
                            else: logging.error("Windows 시간 동기화 실패.")
                        else: logging.info("Windows가 아니므로 자동 시간 동기화 건너뜀.")
                    else: logging.debug(f"시간 차이 {time_diff_ms}ms 는 정상 범위 내")
                    break 
                except asyncio.TimeoutError:
                    current_retry += 1
                    logging.warning(f"서버 시간 조회 중 타임아웃 발생 ({current_retry}/{max_timeout_retries}). {timeout_retry_delay}초 후 재시도...")
                    if current_retry >= max_timeout_retries: logging.error("서버 시간 조회 타임아웃 재시도 모두 실패."); break 
                    await asyncio.sleep(timeout_retry_delay)
                except Exception as e_time_check: logging.error(f"서버 시간 조회 중 예상치 못한 오류: {e_time_check}", exc_info=True); break 
            await asyncio.sleep(interval_seconds) 
        except asyncio.CancelledError: logging.info("시간 동기화 확인 태스크 취소됨"); break
        except Exception as e: logging.error(f"시간 동기화 확인 태스크 외부 루프 오류: {e}", exc_info=True); await asyncio.sleep(interval_seconds) 
    logging.info("시간 동기화 확인 태스크 종료됨")

async def sync_windows_time():
    """Windows 시간 동기화를 더 강력하게 수행합니다."""
    try:
        logging.info("Windows 시간 동기화 서비스 (w32time) 상태 확인 및 재시작/강제 동기화 시도...")
        
        # 1. 서비스가 실행 중이 아니면 시작
        subprocess.run(['sc', 'config', 'w32time', 'start=', 'auto'], check=True, shell=True)
        subprocess.run(['net', 'start', 'w32time'], capture_output=True, text=True, shell=True) # 이미 실행 중이어도 오류 아님

        # 2. NTP 서버와 강제로 재동기화 (가장 중요한 부분)
        # /resync 명령어는 서비스가 오류 상태일 때 실패할 수 있으므로, 설정을 업데이트하고 피어를 재탐색하는 과정을 추가합니다.
        commands = [
            ['w32tm', '/config', '/update'],
            ['w32tm', '/resync', '/force'] # /nowait 대신 /force를 사용하여 즉시 동기화를 강제
        ]
        
        sync_failed = False
        for cmd in commands:
            logging.info(f"실행할 동기화 명령어: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
            if result.returncode != 0:
                # '데이터를 사용할 수 없습니다' 오류는 동기화 소스를 찾는 과정에서 일시적으로 발생할 수 있으므로 경고로 처리합니다.
                if '데이터를 사용할 수 없습니다' in result.stderr:
                    logging.warning(f"명령어 실행 중 일시적 경고: {' '.join(cmd)}, 오류: {result.stderr.strip()}")
                else:
                    logging.error(f"명령어 실행 실패: {' '.join(cmd)}, 오류: {result.stderr.strip()}")
                    sync_failed = True
                    break # 중요한 명령어 실패 시 중단
            else:
                logging.info(f"명령어 실행 성공: {' '.join(cmd)}")
                await asyncio.sleep(0.5) # 명령어 간 짧은 딜레이

        if not sync_failed:
            logging.info("Windows 시간 강제 동기화 명령이 성공적으로 완료되었습니다.")
        else:
            logging.error("Windows 시간 강제 동기화에 실패했습니다.")
            
        return not sync_failed
    except subprocess.CalledProcessError as e:
        logging.error(f"Windows 시간 동기화 서비스 설정 중 오류 (관리자 권한 필요): {e}")
        return False
    except Exception as e:
        logging.error(f"Windows 시간 동기화 중 예외 발생: {e}", exc_info=True)
        return False

async def run_bot_logic():
    """ 봇의 메인 로직을 실행하는 비동기 함수 """
    global client, main_app_running, main_waiting_future, gui, symbol_info, calculated_min_order_qty, leverage_set, current_balance, current_step_index, open_orders_state, order_type_mapping
    global entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list
    global position_update_task, signal_type, last_entry_price, open_orders_check_task, time_sync_task # time_sync_task 추가

    if not app_config.get('API_KEY') or not app_config.get('API_SECRET'):
        raise RuntimeError("API 키가 로드되지 않았습니다. settings.ini를 확인하세요.")

    logging.info("run_bot_logic 시작")
    if gui: gui.update_status("클라이언트 생성 중...")
    try:
        timeout = aiohttp.ClientTimeout(total=10)
        requests_params = {'timeout': timeout}
        client = await AsyncClient.create(config.API_KEY, config.API_SECRET, requests_params=requests_params)
        # --- 수정 끝 ---
        logging.info("AsyncClient 생성 완료 (요청 타임아웃 10초).")
    except Exception as e: logging.critical(f"AsyncClient 생성 실패: {e}", exc_info=True); gui.update_status("클라이언트 생성 실패"); gui.set_button_to_start_mode(); main_app_running = False; return

    try:
        if gui: gui.update_status("초기화 중...")
        if not await check_futures_connection(client): raise Exception("서버 연결 실패")
        if await check_all_open_positions(client): raise Exception("기존 포지션 감지됨 - 종료") # 필요시 이 부분 조정 (예: 기존 포지션 종료 후 진행)
        if not await check_and_cancel_pending_orders(client): raise Exception("미체결 주문 처리 실패 - 종료")
        current_balance, _ = await get_futures_balance(client, config.BALANCE_ASSET, gui) 
        if not await check_position_mode(client, gui): raise Exception("헤지 모드 아님 또는 변경 실패")
        leverage_set, _ = await set_leverage(client, config.SYMBOL, config.TARGET_LEVERAGE, gui)
        if not leverage_set: raise Exception("레버리지 설정 실패")
        symbol_info_loaded, symbol_info_data = await get_symbol_info(client, config.SYMBOL, gui)
        if not symbol_info_loaded: raise Exception("심볼 정보 조회 실패")
        symbol_info = symbol_info_data 
        calculated_min_order_qty, _ = await calculate_effective_min_qty(client, config.SYMBOL, symbol_info, gui)
        if calculated_min_order_qty is None: raise Exception("최소 주문 수량 계산 실패")

        initial_recalc_ok = await recalculate_all_data(client, gui, symbol_info, calculated_min_order_qty, current_balance)
        if not initial_recalc_ok: raise Exception("초기 데이터 계산 실패")

        try: # 초기 미체결 주문/포지션 로드
            # 일반 미체결 주문 조회
            initial_open_orders = await client.futures_get_open_orders(symbol=config.SYMBOL)
            open_orders_state = {str(o['orderId']): o for o in initial_open_orders}
            order_type_mapping = {}
            logging.info(f"초기 일반 미체결 주문 로드 완료: {len(initial_open_orders)}개")
            
            # 🟢 Algo 미체결 주문도 조회
            initial_algo_orders = await get_open_algo_orders(client, config.SYMBOL)
            if initial_algo_orders:
                for algo_order in initial_algo_orders:
                    algo_id = str(algo_order.get('algoId', ''))
                    if algo_id:
                        algo_order['isAlgoOrder'] = True
                        algo_order['creationTime'] = algo_order.get('createTime', time.time() * 1000) / 1000.0
                        open_orders_state[algo_id] = algo_order
                        # Algo 주문 타입 추정 (TSM 등)
                        order_type = algo_order.get('orderType', algo_order.get('type', 'UNKNOWN'))
                        order_type_mapping[algo_id] = f"SyncedAlgo-{order_type}"
                        # clientAlgoId도 매핑에 추가
                        client_algo_id = algo_order.get('clientAlgoId')
                        if client_algo_id:
                            order_type_mapping[client_algo_id] = f"SyncedAlgo-{order_type}"
                logging.info(f"초기 Algo 미체결 주문 로드 완료: {len(initial_algo_orders)}개")
            else:
                logging.info("초기 Algo 미체결 주문 없음")
            
            if gui: gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
            logging.info(f"초기 미체결 주문 총합: {len(open_orders_state)}개 (일반: {len(initial_open_orders)}, Algo: {len(initial_algo_orders) if initial_algo_orders else 0})")
            
            initial_positions = await client.futures_position_information(symbol=config.SYMBOL)
            if gui: gui.update_position_display(initial_positions, config.SYMBOL)
            logging.info(f"초기 포지션 정보 로드 완료.")
        except Exception as e: logging.error(f"초기 주문/포지션 조회 실패: {e}")

        position_update_task = asyncio.create_task(update_positions_periodically(client, config.SYMBOL, gui, config.POSITION_UPDATE_INTERVAL if hasattr(config, 'POSITION_UPDATE_INTERVAL') else 5))
        open_orders_check_task = asyncio.create_task(check_open_orders_periodically(client, config.SYMBOL, gui, config.OPEN_ORDERS_CHECK_INTERVAL if hasattr(config, 'OPEN_ORDERS_CHECK_INTERVAL') else 3))
        if config.PERIODIC_TIME_CHECK_INTERVAL_SECONDS > 0:
            time_sync_task = asyncio.create_task(check_and_sync_time_periodically(client, gui, config.PERIODIC_TIME_CHECK_INTERVAL_SECONDS))
            logging.info("시간 동기화 확인 태스크 시작됨")
        logging.info("초기화 성공적으로 완료.")
    except Exception as e:
        logging.error(f"초기화 실패: {e}", exc_info=True)
        if gui:
            gui.update_status(f"초기화 실패: {str(e)[:50]}...")
            gui.set_button_to_start_mode()
            # <<< 🟢 팝업 호출 코드 추가 >>>
            gui.show_error_popup("초기화 실패", f"봇 초기화 중 심각한 오류가 발생했습니다.\n\n오류: {e}\n\n프로그램을 확인해주세요.")
        main_app_running = False 
        if client: await client.close_connection() 
        return 

    while main_app_running:
        main_waiting_future = asyncio.Future() 
        connection_started = False
        try:
            if gui: gui.update_status("웹소켓 연결 시도 중...")
            connection_started = await start_websockets(client)
            if connection_started:
                logging.info("웹소켓 연결 성공.")
                if gui: gui.update_status("실행 중")
                if current_step_index == -1 and config.AUTO_START_ON_RUN: await trigger_initial_entry(client, gui)
                await main_waiting_future
            else: logging.error("웹소켓 시작 실패."); main_app_running = False 
        except asyncio.CancelledError: logging.info("메인 봇 로직 태스크 취소됨 (CancelledError)."); main_app_running = False 
        except Exception as e: logging.error(f"봇 로직 메인 루프 오류: {e}", exc_info=True)
        finally:
             logging.info("웹소켓 세션 정리 시도...")
             if gui and main_app_running: gui.update_status("웹소켓 재연결 중...")
             await stop_websockets() 
             if main_app_running:
                  logging.info(f"{config.RECONNECT_DELAY}초 후 재연결 시도...")
                  try: await asyncio.sleep(config.RECONNECT_DELAY)
                  except asyncio.CancelledError: logging.info("재연결 대기 중 취소됨."); main_app_running = False
    logging.info("봇 로직 종료 처리 시작...")
    if gui: gui.update_status("종료 중...")
    tasks_to_cancel = [position_update_task, open_orders_check_task, time_sync_task, keep_alive_task, websocket_connection_task]
    for task in tasks_to_cancel:
        if task and not task.done(): task.cancel()
    try:
        tasks_to_wait = [t for t in tasks_to_cancel if t] 
        if tasks_to_wait: await asyncio.wait(tasks_to_wait, timeout=2) # 타임아웃 증가
    except asyncio.TimeoutError: logging.warning("주기적/웹소켓 태스크 종료 시간 초과.")
    except Exception as e: logging.error(f"주기적/웹소켓 태스크 종료 중 오류: {e}")
    await stop_websockets() 
    if client:
        try: await client.close_connection(); logging.info("AsyncClient 연결 종료됨.")
        except Exception as e: logging.error(f"AsyncClient 종료 중 오류: {e}")
    logging.info("봇 로직 태스크 완전히 종료됨.")
    if gui: gui.set_button_to_start_mode(); gui.update_status("정지됨")

def request_graceful_stop():
    """정지 요청을 기록하고 GUI 상태를 업데이트합니다."""
    global stop_requested, gui
    if not stop_requested:
        logging.info("정지 요청됨. 현재 사이클 완료 후 종료됩니다.")
        stop_requested = True
        if gui:
            gui.set_button_to_stop_reserved_mode()
            gui.update_status("정지 예약됨. 현재 사이클 완료 후 종료됩니다.")

def cancel_graceful_stop():
    """예약된 정지 요청을 취소하고 GUI 상태를 복원합니다."""
    global stop_requested, gui
    if stop_requested:
        logging.info("정지 예약이 취소되었습니다. 봇은 계속 실행됩니다.")
        stop_requested = False
        if gui:
            # GUI 버튼을 다시 '정지' 상태로 되돌립니다.
            gui.set_button_to_stop_mode()
            # GUI 상태 메시지를 업데이트합니다.
            gui.update_status("실행 중 (정지 예약 취소됨)")

def stop_bot_logic():
    """봇 로직 및 웹소켓 종료"""
    global main_app_running, websocket_connection_task, keep_alive_task, main_waiting_future, asyncio_loop, position_update_task, open_orders_check_task, time_sync_task
    if not main_app_running: logging.info("봇이 이미 정지 상태입니다."); return
    logging.info("봇 로직 종료 신호 수신.")
    main_app_running = False
    loop_to_use = asyncio_loop
    if loop_to_use and loop_to_use.is_running():
        logging.info("비동기 태스크 취소 시도...")
        tasks_to_cancel_on_stop = [main_waiting_future, keep_alive_task, position_update_task, open_orders_check_task, time_sync_task, websocket_connection_task]
        for task_obj in tasks_to_cancel_on_stop:
            if task_obj and not task_obj.done():
                # Future.cancel()은 인자를 받지 않음.
                if isinstance(task_obj, asyncio.Future):
                    loop_to_use.call_soon_threadsafe(task_obj.cancel)
                else: # Task 객체
                    loop_to_use.call_soon_threadsafe(task_obj.cancel)
        logging.info("비동기 태스크 취소 요청 완료.")
    else: logging.warning("비동기 루프가 실행 중이지 않아 태스크를 취소할 수 없습니다.")
    if gui: gui.update_status("정지 중...")

def reset_global_state():
    """전역 상태 변수들 초기화"""
    global current_step_index, open_orders_state, order_type_mapping, signal_type, entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list, last_entry_price, last_two_candles, last_trigger_order_price, nsz_lower_bound, nsz_active, pending_entry_info, exit_orders_status, partially_filled_log
    global step_profit_handler_info, nsz_history
    logging.info("전역 상태 변수 초기화 중...")
    current_step_index = -1; open_orders_state = {}; order_type_mapping = {}; signal_type = None; last_entry_price = 0.0
    last_trigger_order_price = 0.0; nsz_lower_bound = 0.0; nsz_active = False; last_two_candles = []
    nsz_history.clear() # <<< 🟢 nsz_history 초기화 코드 추가
    entry_quantity_list = []; cumulative_entry_quantity_list = []; per_step_hedge_quantity_list = []; cumulative_hedge_quantity_list = []; exit_ratio_list = []
    pending_entry_info = {'active': False, 'order_ids': [], 'step': -1, 'signal_type': None, 'attempt_key_prefix': None, 'start_time': 0, 'division_status': {'current_sub_order_index_placed': -1, 'num_total_divisions_for_step': 0, 'base_entry_price_for_step': 0.0, 'original_total_quantity_for_step': 0.0, 'placed_total_quantity_so_far': 0.0, 'attempt_key_prefix_internal': None, 'filled_sub_order_count': 0, 'triggers': [], 'next_sub_order_to_trigger_index': 0}}
    step_profit_handler_info = {
        'active': False, 'scenario': None, 'step_index_at_trigger': -1,
        'profit_target_price': Decimal('0'), 'partial_market_exit_qty': Decimal('0'),
        'initial_pos_qty_for_step': Decimal('0'), 'main_pos_side': None,
        'tsm_order_id_for_remaining': None, 'tsm_order_qty': Decimal('0'),
        'tsm_activation_price': Decimal('0'), 'awaiting_tsm_profitable_fill': False,
        'display_exit_target': None # GUI 표시용도 초기화
    }
    exit_orders_status = {}; partially_filled_log = []
    logging.info("전역 상태 변수 초기화 완료.")

def start_asyncio_loop():
    """비동기 이벤트 루프를 시작하고 메인 로직을 실행하는 함수 (별도 스레드에서 실행)"""
    global asyncio_loop, main_app_running, _loop_thread_id 
    logging.info("비동기 루프 시작...")
    main_app_running = True; _loop_thread_id = threading.get_ident() 
    logging.info(f"Asyncio loop running in thread ID: {_loop_thread_id}")
    try:
        asyncio_loop = asyncio.SelectorEventLoop(); asyncio.set_event_loop(asyncio_loop)
        asyncio_loop.run_until_complete(run_bot_logic())
    except Exception as e: 
        logging.error(f"비동기 루프 실행 중 오류 발생: {e}", exc_info=True)
        if gui: # <<< 🟢 gui 객체 확인 후 팝업 호출 >>>
            gui.update_status("오류 발생")
            gui.show_error_popup("치명적 오류", f"비동기 루프 실행 중 예상치 못한 오류가 발생했습니다.\n\n오류: {e}\n\n프로그램을 종료해야 할 수 있습니다.")
    finally:
        logging.info("비동기 루프 run_until_complete 종료됨.")
        try:
            if asyncio_loop and not asyncio_loop.is_closed():
                # 루프 내 모든 태스크 취소 및 대기
                for task in asyncio.all_tasks(loop=asyncio_loop): task.cancel()
                # 루프 종료까지 대기 (모든 태스크 정리)
                # asyncio_loop.run_until_complete(asyncio_loop.shutdown_asyncgens()) # Python 3.6+
                # Python 3.9+ 에서는 close() 전에 shutdown_default_executor() 등 필요할 수 있음
                # 여기서는 일단 close()만 호출
                asyncio_loop.close()
                logging.info("비동기 이벤트 루프 닫힘.")
        except Exception as e: logging.error(f"비동기 루프 정리 중 오류: {e}")
        asyncio_loop = None; _loop_thread_id = None 
        if gui: gui.set_button_to_start_mode(); gui.update_status("정지됨")

def load_initial_config():
    """config.py의 초기값을 app_config 딕셔너리로 로드"""
    global app_config
    logging.info("config.py에서 초기 설정 값을 로드합니다.")
    for key in dir(config):
        if key.isupper():
            app_config[key] = getattr(config, key)

def handle_config_update(new_configs: dict):
    """GUI로부터 받은 설정 변경사항을 중앙 app_config에 적용"""
    global app_config, gui
    logging.info(f"GUI로부터 설정 변경 요청 수신: {new_configs}")
    app_config.update(new_configs)
    if 'TARGET_LEVERAGE' in new_configs and gui:
        gui.update_leverage(f"{new_configs['TARGET_LEVERAGE']}x (수동변경)")

async def trigger_recalculation():
    """GUI 요청에 따른 재계산 비동기 실행"""
    global gui, client, symbol_info, calculated_min_order_qty, current_balance, app_config
    logging.info("GUI 요청으로 모든 데이터 재계산을 시작합니다.")
    if gui: gui.update_status("수동 재계산 중...")
    success = await recalculate_all_data(client, gui, symbol_info, calculated_min_order_qty, current_balance, app_config)
    if success:
        if gui: gui.update_status("수동 재계산 완료.")
    else:
        if gui: gui.update_status("수동 재계산 실패!")

def handle_recalculation_request():
    """GUI의 재계산 요청을 비동기 루프에서 실행"""
    if main_app_running and asyncio_loop and asyncio_loop.is_running():
        asyncio.run_coroutine_threadsafe(trigger_recalculation(), asyncio_loop)
    else:
        messagebox.showwarning("재계산 불가", "봇이 실행 중일 때만 재계산할 수 있습니다.")


def handle_config_update(new_configs: dict):
    global app_config, gui
    logging.info(f"GUI로부터 설정 변경 요청 수신: {new_configs}")
    app_config.update(new_configs)
    
    # <<< 변경: 설정 변경 후 파일에 즉시 저장 >>>
    save_config_to_ini()
    
    if 'TARGET_LEVERAGE' in new_configs and gui:
        gui.update_leverage(f"{new_configs['TARGET_LEVERAGE']}x (수동변경)")

# <<< 핵심 수정: ini 파일을 더 안전하고 명확하게 읽도록 함수 재작성 >>>
def load_config_from_ini():
    """settings.ini 파일을 읽어 app_config 딕셔너리를 채웁니다."""
    global app_config
    
    # configparser는 키를 소문자로 다룹니다. interpolation=None은 '%' 문자를 특별하게 해석하지 않도록 합니다.
    parser = configparser.ConfigParser(interpolation=None)
    try:
        # utf-8-sig 인코딩은 파일 시작 부분의 보이지 않는 BOM 문자를 처리해줍니다.
        if not parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig'):
            raise FileNotFoundError(f"{SETTINGS_FILE_PATH} 파일을 찾을 수 없습니다.")

        # 각 섹션의 값을 타입에 맞게 명시적으로 읽어옵니다.
        # ini 파일의 키는 소문자로 접근해야 합니다.
        api_sec = 'API'
        app_config['API_KEY'] = parser.get(api_sec, 'api_key').strip('"\'')
        app_config['API_SECRET'] = parser.get(api_sec, 'api_secret').strip('"\'')

        trade_sec = '거래 기본 설정'
        app_config['SYMBOL'] = parser.get(trade_sec, 'symbol')
        app_config['KLINE_INTERVAL'] = parser.get(trade_sec, 'kline_interval')
        app_config['TARGET_LEVERAGE'] = parser.getint(trade_sec, 'target_leverage')
        app_config['BALANCE_ASSET'] = parser.get(trade_sec, 'balance_asset')
        app_config['BALANCE_USAGE_PERCENTAGE'] = parser.getfloat(trade_sec, 'balance_usage_percentage')
        app_config['PRICE_RATIO_MIN'] = parser.getfloat(trade_sec, 'price_ratio_min')
        app_config['PRICE_RATIO_MAX'] = parser.getfloat(trade_sec, 'price_ratio_max')

        strat_sec = '전략 파라미터'
        app_config['STEPS'] = parser.getint(strat_sec, 'steps')
        app_config['DIVIDE'] = parser.getint(strat_sec, 'divide')
        app_config['NO_SIGNAL_ZONE'] = parser.getfloat(strat_sec, 'no_signal_zone')
        app_config['MAGINOT'] = parser.getfloat(strat_sec, 'maginot')
        app_config['CALLBACK_RATE'] = parser.getfloat(strat_sec, 'callback_rate')
        app_config['CALLBACK_RATE_FOR_LAST'] = parser.getfloat(strat_sec, 'callback_rate_for_last')
        app_config['DIVIDE_RATE'] = parser.getfloat(strat_sec, 'divide_rate')
        app_config['AUTO_START_ON_RUN'] = parser.getboolean(strat_sec, 'auto_start_on_run')
        app_config['POSITION_BIAS'] = parser.get(strat_sec, 'position_bias').upper()

        entry_sec = '수량 파라미터 (Entry)'
        app_config['ENTRY_START'] = parser.getfloat(entry_sec, 'entry_start')
        app_config['ENTRY_END'] = parser.getfloat(entry_sec, 'entry_end')
        app_config['ENTRY_EXPONENT'] = parser.getfloat(entry_sec, 'entry_exponent')

        hedge_sec = '수량 파라미터 (Hedge)'
        app_config['HEDGE_START'] = parser.getfloat(hedge_sec, 'hedge_start')
        app_config['HEDGE_END'] = parser.getfloat(hedge_sec, 'hedge_end')
        app_config['HEDGE_EXPONENT'] = parser.getfloat(hedge_sec, 'hedge_exponent')

        exit_sec = '익절 파라미터 (Exit)'
        app_config['EXIT_FIRST'] = parser.getfloat(exit_sec, 'exit_first')
        app_config['EXIT_LAST'] = parser.getfloat(exit_sec, 'exit_last')
        app_config['EXIT_EXPONENT'] = parser.getfloat(exit_sec, 'exit_exponent')
        app_config['EXIT_DISTANCE_MULTIPLIER'] = parser.getfloat(exit_sec, 'exit_distance_multiplier')
        
        tsm_sec = '익절 파라미터 (TSM)'
        app_config['TSM_EXIT_CALLBACK_RATE'] = parser.getfloat(tsm_sec, 'tsm_exit_callback_rate')
        app_config['TSM_EXIT_ENABLED'] = parser.getboolean(tsm_sec, 'tsm_exit_enabled')
        app_config['TSM_EXIT_CALLBACK_RATE_MAX'] = parser.getfloat(tsm_sec, 'tsm_exit_callback_rate_max')
        app_config['TSM_EXIT_CALLBACK_RATE_MIN'] = parser.getfloat(tsm_sec, 'tsm_exit_callback_rate_min')
        
        other_sec = '기타 설정'
        app_config['WS_URL'] = parser.get(other_sec, 'ws_url')
        app_config['RECONNECT_DELAY'] = parser.getint(other_sec, 'reconnect_delay')
        app_config['POSITION_UPDATE_INTERVAL'] = parser.getint(other_sec, 'position_update_interval')
        app_config['OPEN_ORDERS_CHECK_INTERVAL'] = parser.getint(other_sec, 'open_orders_check_interval')
        app_config['PERIODIC_TIME_CHECK_INTERVAL_SECONDS'] = parser.getint(other_sec, 'periodic_time_check_interval_seconds')
        app_config['TIME_DRIFT_THRESHOLD_MS'] = parser.getint(other_sec, 'time_drift_threshold_ms')
        app_config['ORDER_RETRY_ATTEMPTS'] = parser.getint(other_sec, 'order_retry_attempts')
        app_config['ORDER_RETRY_DELAY_SECONDS'] = parser.getint(other_sec, 'order_retry_delay_seconds')
        
        logging.info(f"{SETTINGS_FILE_PATH} 파일에서 설정을 성공적으로 로드했습니다.")

    except Exception as e:
        logging.critical(f"{SETTINGS_FILE_PATH} 파일 로드 또는 파싱 실패! 오류: {e}", exc_info=True)
        messagebox.showerror("치명적 오류", f"settings.ini 파일을 읽거나 해석할 수 없습니다.\n오류: {e}\n프로그램을 종료합니다.")
        sys.exit(1)

def save_config_to_ini():
    """현재 app_config의 내용을 settings.ini 파일에 저장합니다."""
    global app_config
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig')

    # app_config의 값을 ini 파서 객체에 업데이트 (소문자 키로)
    for section in parser.sections():
        for key, _ in parser.items(section):
            key_upper = key.upper()
            if key_upper in app_config:
                parser.set(section, key, str(app_config[key_upper]))

    try:
        with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as configfile:
            parser.write(configfile)
        logging.info(f"{SETTINGS_FILE_PATH} 파일에 변경된 설정을 저장했습니다.")
    except Exception as e:
        logging.error(f"{SETTINGS_FILE_PATH} 파일 저장 실패! 오류: {e}")

def handle_config_update(new_configs: dict):
    global app_config, gui
    app_config.update(new_configs)
    save_config_to_ini()
    logging.info(f"설정 변경 및 파일 저장 완료: {new_configs}")
    if 'TARGET_LEVERAGE' in new_configs and gui:
        gui.update_leverage(f"{new_configs['TARGET_LEVERAGE']}x (수동변경)")

if __name__ == "__main__":
    logging.info("__main__ 블록 시작")
    gui = None
    bot_logic_thread = None

    def handle_toggle_action(action):
        global bot_logic_thread
        if action == "start":
            if bot_logic_thread and bot_logic_thread.is_alive():
                logging.warning("봇 로직 스레드가 이미 실행 중입니다."); return
            logging.info("봇 로직 스레드 시작 시도...")
            if gui: gui.update_status("시작 중...")
            bot_logic_thread = threading.Thread(target=start_asyncio_loop, name="AsyncioBotThread", daemon=True)
            bot_logic_thread.start()
        elif action == "stop":
            logging.info("정지 버튼 클릭됨 - 예약 정지 로직 시작")
            request_graceful_stop() # ⚠️ 기존 stop_bot_logic() 호출을 이 함수로 변경
        elif action == "cancel_stop":
            cancel_graceful_stop()
            


    try:
        logging.info("자동매매 프로그램 시작 (Asyncio + GUI)...")
        root = tk.Tk()
        
        # 1. settings.ini 파일에서 모든 설정을 로드합니다.
        load_config_from_ini()
        
        # 로드된 설정(config)을 logic.py 모듈이 사용할 수 있도록 전달합니다.
        set_config_source(config)
        
        # 🟢 Algo 주문 보호 콜백 함수 정의 및 전달
        def register_algo_order_for_protection(algo_id):
            """새로 생성된 Algo 주문을 보호 리스트에 등록합니다."""
            global recently_created_algo_orders
            recently_created_algo_orders[str(algo_id)] = time.time()
            logging.debug(f"Algo 주문 {algo_id}이(가) 보호 리스트에 등록됨 (보호 기간: {ALGO_ORDER_PROTECTION_SECONDS}초)")
        
        set_algo_order_protection_callback(register_algo_order_for_protection)
        # --- 수정 끝 ---
        
        # 3. GUI를 생성하고 나머지 초기화를 진행합니다.
        gui = GuiManager(root, app_config['SYMBOL'], app_config['STEPS'], app_config['BALANCE_ASSET'])
        
        gui.load_current_configs(app_config) 
        
        gui.set_config_update_callback(handle_config_update)
        gui.set_recalculate_callback(handle_recalculation_request)
        gui.set_toggle_command(handle_toggle_action)
        gui.set_on_closing(stop_bot_logic)
        
        gui.update_status("대기 중")
        root.mainloop()
        logging.info("Tkinter 메인 루프 시작..."); root.mainloop(); logging.info("Tkinter 메인 루프 종료됨.")
    except Exception as e:
        logging.critical(f"메인 스레드에서 처리되지 않은 예외 발생: {e}", exc_info=True)
    finally:
        logging.info("자동매매 프로그램을 완전히 종료합니다.")
        stop_bot_logic()
        if bot_logic_thread and bot_logic_thread.is_alive():
             bot_logic_thread.join(timeout=5)