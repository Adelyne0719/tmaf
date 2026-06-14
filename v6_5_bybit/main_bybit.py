# main.py (Bybit 버전으로 수정됨)
import logging
import sys
import asyncio
import json
import platform
import subprocess
import threading
import tkinter as tk
import websockets # pybit가 내부적으로 사용할 수 있으나, 직접 사용 대신 pybit.WebSocket 사용
import time
import datetime
import configparser
import os
import shutil
import aiohttp # pybit HTTP 클라이언트가 내부적으로 사용

from tkinter import ttk, messagebox
from decimal import Decimal, ROUND_HALF_UP

# === 1. 바이낸스 라이브러리 대신 Bybit 라이브러리 임포트 ===
# pip install pybit
try:
    from pybit.unified_trading import HTTP, WebSocket
    from pybit.exceptions import InvalidRequestError, FailedRequestError
except ImportError:
    logging.critical("pybit 라이브러리가 설치되지 않았습니다. 'pip install pybit'를 실행해주세요.")
    sys.exit(1)

# 모듈 임포트
from gui_bybit import GuiManager # GUI 클래스
# === logic 모듈 임포트 방식 수정 ===
from logic_bybit import *
# (참고: logic.py의 모든 함수는 Bybit API에 맞게 재작성되어야 합니다.)

# <<< 변경: settings.ini 파일의 절대 경로 생성 >>>
# (이 로직은 파일 시스템 기반이므로 변경 없이 동일하게 유지됩니다.)
# --- 핵심 수정: PyInstaller 환경을 고려하여 settings.ini의 영구 경로 설정 ---
def get_persistent_settings_path():
    """
    PyInstaller로 패키징되었는지 여부를 확인하여
    settings.ini 파일의 영구적인 경로를 반환합니다.
    만약 해당 경로에 파일이 없다면, 패키지에 포함된 원본 파일을 복사해줍니다.
    """
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
        source_path = os.path.join(bundle_dir, 'settings_Bybit.ini')
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        source_path = os.path.join(application_path, 'settings_Bybit.ini')

    persistent_path = os.path.join(application_path, 'settings_Bybit.ini')

    if not os.path.exists(persistent_path):
        try:
            logging.info(f"설정 파일이 '{persistent_path}'에 없어 새로 생성합니다.")
            shutil.copy2(source_path, persistent_path)
        except Exception as e:
            logging.critical(f"초기 설정 파일 복사에 실패했습니다! 원본: '{source_path}', 대상: '{persistent_path}'. 오류: {e}")
            
    return persistent_path

SETTINGS_FILE_PATH = get_persistent_settings_path()
# --- 수정 끝 ---

# --- 로깅 설정 --- (변경 없음)
log_format = '%(asctime)s - %(threadName)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
if logger.hasHandlers(): logger.handlers.clear()
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(log_format))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# --- 윈도우 asyncio 이벤트 루프 설정 --- (변경 없음)
if platform.system() == "Windows":
    try: asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except AttributeError: logging.warning("WindowsSelectorEventLoopPolicy 사용 불가")

# --- 전역 상태 변수 ---
client: HTTP = None # AsyncClient -> pybit HTTP
futures_client_global: HTTP = None # BinanceFuturesClient -> pybit HTTP
gui: GuiManager = None
bot_logic_thread = None
asyncio_loop = None
_loop_thread_id = None
main_app_running = False
time_sync_task = None
stop_requested = False

class _ConfigProxy:
    # === 2. Bybit용 KLINE_INTERVAL 맵핑으로 수정 ===
    # (Bybit는 문자열로 1, 3, 5, 15 ... 등을 사용)
    _KMAP = {
        '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
        '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
        '1d': 'D', '1w': 'W', '1M': 'M',
    }
    def __init__(self, source: dict):
        self._src = source
    def __getattr__(self, name: str):
        if name == 'KLINE_INTERVAL':
            v = self._src.get('KLINE_INTERVAL')
            if isinstance(v, str): return self._KMAP.get(v, v)
            return v
        return self._src.get(name)
    
app_config = {} 
config = _ConfigProxy(app_config)
preferred_signal_type = 'LONG'

# 웹소켓 관련
# === 3. Bybit는 listen_key 대신 WebSocket 객체를 직접 관리 ===
ws_client: WebSocket = None # WebSocket 클라이언트 객체
# listen_key, keep_alive_task는 Bybit에서 사용되지 않음
ws_client_public: WebSocket = None # 공용(Public) 웹소켓 클라이언트 (kline, trade)
ws_client_private: WebSocket = None # 사적(Private) 웹소켓 클라이언트 (order, position)

# listen_key, keep_alive_task는 Bybit에서 사용되지 않음
websocket_connection_task = None
open_orders_check_task = None
main_waiting_future: asyncio.Future = None
position_update_task = None

# (거래 상태 관련 전역 변수들은 API와 독립적이므로 대부분 변경 없음)
symbol_info = {}
calculated_min_order_qty = None
leverage_set = False
current_balance = 0.0
last_trigger_order_price = 0.0
nsz_lower_bound = 0.0
nsz_active = False 
nsz_history = {}
last_trade_realized_pnl = 0.0 
last_entry_price = 0.0 
current_step_index = -1
open_orders_state = {}
exit_orders_status = {}
order_type_mapping = {}
order_pnl_accumulator = {}
partial_exit_status = {}
signal_type = None 
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
        'filled_sub_order_count': 0,
        'triggers': [],
        'next_sub_order_to_trigger_index': 0,
        'attempt_key_prefix_internal': None 
    }
}
pending_direct_exit_trigger = {
    'active': False,
    'target_price': 0.0,
    'quantity': 0.0,
    'avg_entry_price_long': 0.0,
    'order_mapping_key_suffix': ""
}
step_profit_handler_info = {
    'active': False,
    'step_index_at_trigger': -1,
    'profit_target_price': Decimal('0'),
    'partial_market_exit_qty': Decimal('0'),
    'main_pos_side': None,
    'tsm_order_id_for_remaining': None,
    'tsm_order_qty': Decimal('0'),
    'tsm_activation_price': Decimal('0'),
    'awaiting_tsm_profitable_fill': False
}
clear_line_exit_handler = {
    'active': False,
    'clear_line': Decimal('0'),
    'price_was_below': False,
    'price_was_above': False,
    'signal_type': None
}
entry_quantity_list = []
cumulative_entry_quantity_list = []
per_step_hedge_quantity_list = []
cumulative_hedge_quantity_list = []
exit_ratio_list = []
last_two_candles = []
partially_filled_log = [] 
logged_missing_locally_ids = set() 
recently_expired_main_exit_ids = set() 



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

# (이 함수들은 logic.py가 Bybit용으로 수정되었다고 가정하고,
# client 객체(pybit HTTP)를 그대로 전달합니다.)
async def update_positions_periodically(client: HTTP, symbol: str, gui: GuiManager, interval_sec: int = 5):
    """주기적으로 REST API를 통해 포지션 정보를 조회하고 GUI 포지션 표시 업데이트"""
    global main_app_running, app_config
    logging.info(f"포지션 정보 주기적 업데이트 시작 (간격: {interval_sec}초)")
    
    category = app_config.get('CATEGORY', 'linear') # 카테고리 정보 필요
    
    while main_app_running:
        try:
            if client and gui and main_app_running:
                logging.debug(f"{symbol} 포지션 정보 REST API 조회 시도 (Category: {category})...")
                # === 4. Bybit API 호출 (logic.py로 위임) ===
                # (logic.py의 get_position_information 함수가 pybit 클라이언트를 사용하도록 수정되어야 함)
                # 여기서는 main.py가 logic.py 함수를 호출하는 대신 직접 호출한다고 가정하고 수정
                #
                # 원본: positions = await client.position_information(symbol=symbol)
                # 수정 (예시):
                response = await asyncio.to_thread(
                    client.get_positions,
                    category=category,
                    symbol=symbol
                )
                positions = response.get('result', {}).get('list', [])
                
                logging.debug(f"{symbol} 포지션 정보 수신 (REST): {positions}")
                # (참고: gui.update_position_display도 Bybit 응답 형식에 맞게 수정 필요)
                gui.update_position_display(positions, symbol)
            else:
                if not main_app_running: break

            await asyncio.sleep(interval_sec)

        except asyncio.CancelledError:
            logging.info("포지션 업데이트 태스크 취소됨.")
            break
        
        except (asyncio.TimeoutError, aiohttp.ClientConnectorError, TimeoutError):
            logging.warning(f"포지션 업데이트 중 네트워크 타임아웃 발생. 잠시 후 재시도합니다.")
            await asyncio.sleep(interval_sec)
        
        except (InvalidRequestError, FailedRequestError) as e:
            # Bybit 예외 처리
            logging.error(f"포지션 업데이트 중 API 오류 발생 (코드: {e.status_code}): {e.message}")
            await asyncio.sleep(interval_sec)
        
        except Exception as e:
            logging.error(f"포지션 정보 업데이트 중 예상치 못한 오류: {e}", exc_info=True)
            await asyncio.sleep(interval_sec * 2) 

    logging.info("포지션 정보 주기적 업데이트 종료됨.")

async def check_open_orders_periodically(client: HTTP, symbol: str, gui: GuiManager, interval_sec: int = 3):
    """ 주기적으로 REST API를 통해 미체결 주문 목록을 조회하고 로컬 상태와 동기화 (Bybit용) """
    global main_app_running, open_orders_state, order_type_mapping, current_step_index, symbol_info, signal_type, pending_entry_info, app_config
    
    logging.info(f"미체결 주문 주기적 동기화 시작 (간격: {interval_sec}초)")
    category = app_config.get('CATEGORY', 'linear')

    while main_app_running:
        await asyncio.sleep(interval_sec)
        if not main_app_running: break
        
        try:
            if not (client and gui): continue

            # === 5. Bybit API 호출 (미체결 주문) ===
            response = await asyncio.to_thread(
                client.get_open_orders,
                category=category,
                symbol=symbol
            )
            actual_orders = response.get('result', {}).get('list', [])
            
            actual_order_ids = {str(o['orderId']) for o in actual_orders}
            local_order_ids = set(open_orders_state.keys())
            stale_ids = local_order_ids - actual_order_ids
            state_changed_this_cycle = False
            grace_period_seconds = 3.0

            if stale_ids:
                logging.info(f"주기적 확인: 로컬에만 존재하는 유령 의심 주문 {len(stale_ids)}개 발견: {stale_ids}")
                for stale_id in list(stale_ids):
                    local_order_data = open_orders_state.get(stale_id, {})
                    creation_time = local_order_data.get('creationTime', 0)
                    custom_type_name = order_type_mapping.get(stale_id)

                    if time.time() - creation_time < grace_period_seconds:
                        logging.debug(f"  - Stale ID {stale_id} ({custom_type_name}) 생성된 지 얼마 안 됨. 제거 보류.")
                        continue

                    try:
                        # === 6. Bybit API 호출 (단일 주문 조회) ===
                        response_ghost = await asyncio.to_thread(
                            client.get_order_history,
                            category=category,
                            orderId=stale_id
                        )
                        ghost_order_list = response_ghost.get('result', {}).get('list', [])
                        if not ghost_order_list:
                            raise Exception("Order does not exist") # Bybit는 오류 대신 빈 리스트 반환
                        
                        ghost_order_details = ghost_order_list[0]
                        status = ghost_order_details.get('orderStatus') # 'orderStatus'
                        
                        # (Bybit 상태: Filled, Cancelled, Rejected, Expired)
                        if status == 'Filled' and custom_type_name and custom_type_name.startswith('EntryAttempt-'):
                            logging.info(f"  -> 유령 주문({stale_id}, {custom_type_name}) FILLED 확인. 후속 처리 시작.")
                            
                            filled_price = float(ghost_order_details.get('avgPrice', '0')) # 'avgPrice'
                            if filled_price <= 0:
                                logging.error(f"    - 체결 가격({filled_price})이 유효하지 않아 후속 처리를 중단합니다.")
                            else:
                                parts = custom_type_name.split('-')
                                filled_step = int(parts[1])

                                if current_step_index < filled_step:
                                    # Bybit는 positionIdx를 사용하므로, positionSide 대신 signal_type 설정
                                    if ghost_order_details.get('side') == 'Buy':
                                        signal_type = 'LONG'
                                    elif ghost_order_details.get('side') == 'Sell':
                                        signal_type = 'SHORT'
                                    logging.info(f"    - 전역 signal_type을 '{signal_type}'으로 설정.")

                                    current_step_index = filled_step
                                    if gui: gui.update_current_step(current_step_index)
                                    logging.info(f"    - 현재 스텝을 {current_step_index}(으)로 업데이트.")

                                    calculate_and_update_nsz(filled_price, symbol_info, gui, signal_type, current_step_index)
                                    
                                    if pending_entry_info.get('active'):
                                        pending_entry_info['active'] = False
                                        logging.info("    - pending_entry_info를 비활성화합니다.")
                                    
                                    state_for_logic_call = {
                                        'symbol': symbol, 'open_orders_state': open_orders_state, 'order_type_mapping': order_type_mapping,
                                        'entry_quantity_list': entry_quantity_list, 'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type,
                                        'per_step_hedge_quantity_list': per_step_hedge_quantity_list, 'cumulative_entry_quantity_list': cumulative_entry_quantity_list
                                    }
                                    logging.info(f"    - 스텝 {current_step_index}의 후속 주문 설정을 위해 logic.place_orders_for_step 호출.")
                                    await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_logic_call, current_step_index, trigger_event='ENTRY_FILL_BY_CHECKER')

                                else: 
                                    logging.warning(f"  -> 유령 주문({stale_id}, {custom_type_name}) 체결 확인. 하지만 현재 스텝({current_step_index})이 이미 높거나 같으므로 후속 처리를 무시합니다.")
                                
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True
                            logging.info(f"    - 후속 처리 완료 후 로컬 상태에서 ID {stale_id} 제거.")

                        elif status in ['Cancelled', 'Expired', 'Rejected', 'Filled']:
                            logging.info(f"  -> 유령 주문({stale_id}, {custom_type_name})의 서버 상태 '{status}' 확인. 로컬에서만 제거합니다.")
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True

                    except Exception as e:
                        # Bybit는 "order not exists" 오류 코드가 다름 (예: 10001)
                        if "Order does not exist" in str(e) or (hasattr(e, 'status_code') and e.status_code == 10001):
                            logging.warning(f"  -> 유령 주문({stale_id})은 서버에 존재하지 않음. 로컬에서 제거.")
                            open_orders_state.pop(stale_id, None)
                            order_type_mapping.pop(stale_id, None)
                            state_changed_this_cycle = True
                        else:
                            logging.error(f"  -> 유령 주문({stale_id}) 상세 정보 조회 중 예외: {e}")

            # 서버에만 있는 주문 동기화 로직
            missing_locally_ids = actual_order_ids - local_order_ids
            if missing_locally_ids:
                logging.warning(f"주기적 확인: 서버에만 존재하는 주문 {len(missing_locally_ids)}개 발견: {missing_locally_ids}")
                for order_id in list(missing_locally_ids):
                    try:
                        # 'actual_orders'에서 해당 주문 정보 찾기
                        order_detail = next((o for o in actual_orders if str(o['orderId']) == order_id), None)
                        if order_detail and order_detail.get('orderStatus') not in ['Filled', 'Cancelled', 'Expired', 'Rejected']:
                             open_orders_state[order_id] = order_detail
                             order_type_mapping.setdefault(order_id, f"SyncedFromServer-{order_detail.get('orderType','?')}")
                             state_changed_this_cycle = True
                             logging.info(f"  - 서버 주문 ID {order_id} 로컬 상태에 추가됨.")
                    except Exception as e:
                        logging.error(f"서버 주문 ID {order_id} 정보 조회/추가 실패: {e}")

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

# (이하 함수들은 API와 직접적인 관련이 적으므로 대부분 유지)
async def check_all_positions_closed_and_finalize(client_param: HTTP, symbol_param: str, final_realized_pnl_str: str):
    global main_app_running, app_config

    if not main_app_running:
        logging.info("봇이 실행 중이 아니므로 포지션 확인 및 사이클 종료 건너뜁니다.")
        return
    
    category = app_config.get('CATEGORY', 'linear')

    try:
        logging.info(f"[{symbol_param}] 모든 포지션 청산 여부 확인 중...")
        # === 7. Bybit API 호출 ===
        response = await asyncio.to_thread(
            client_param.get_positions,
            category=category,
            symbol=symbol_param
        )
        positions = response.get('result', {}).get('list', [])
        
        total_pos_size = Decimal('0')
        
        # Bybit는 L/S 포지션을 size와 side로 구분하여 리스트로 반환
        if positions:
            for p_info in positions:
                size_str = p_info.get('size', '0')
                total_pos_size += Decimal(size_str)
        
        logging.info(f"[{symbol_param}] 현재 포지션 확인 결과: Total Size={total_pos_size}")

        if total_pos_size == Decimal('0'):
            logging.info(f"[{symbol_param}] 모든 관련 포지션 청산 확인됨. 거래 사이클 완료 처리 시작.")
            await finalize_cycle_and_reset(final_realized_pnl_str)
        else:
            logging.info(f"[{symbol_param}] 아직 청산되지 않은 포지션 존재. Total Size: {total_pos_size}. 사이클 종료 대기.")

    except Exception as e:
        logging.error(f"모든 포지션 청산 여부 확인 중 오류 발생: {e}", exc_info=True)
        if gui: gui.update_status("포지션 확인 오류!")

def get_preferred_signal_type():
    try:
        return str(app_config.get('POSITION_BIAS', 'LONG')).upper()
    except Exception:
        try:
            return str(getattr(config, 'POSITION_BIAS', 'LONG')).upper()
        except Exception:
            return 'LONG'

def calculate_and_update_nsz(trigger_price, symbol_info, gui, signal_type: str, step_index_to_save: int):
    global nsz_lower_bound, nsz_active, nsz_history
    
    current_bias_for_nsz = get_preferred_signal_type()
    
    nsz_text = "-"; calculated_bound = 0.0; calculation_success = False
    
    if trigger_price > 0 and config.NO_SIGNAL_ZONE > 0 and symbol_info:
        try:
            bound_dec = Decimal('0')
            label = ""
            
            if current_bias_for_nsz == 'SHORT':
                bound_dec = Decimal(str(trigger_price)) * (Decimal('1.0') + Decimal(str(config.NO_SIGNAL_ZONE)))
                label = "상한선"
            else:
                bound_dec = Decimal(str(trigger_price)) * (Decimal('1.0') - Decimal(str(config.NO_SIGNAL_ZONE)))
                label = "하한선"
            
            # (참고: logic.get_symbol_info가 Bybit용 tickSize를 반환해야 함)
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
    
    nsz_lower_bound = calculated_bound
    nsz_active = calculation_success and calculated_bound > 0
    
    if nsz_active:
        nsz_history[step_index_to_save] = {
            'bound': calculated_bound,
            'text': nsz_text,
            'signal_type': signal_type
        }
        logging.info(f"[NSZ History] 스텝 {step_index_to_save}의 NSZ 저장: {nsz_history[step_index_to_save]}")
        
    if gui: gui.update_nsz_range(nsz_text)
    
    logging.info(f"[NSZ Update] Bias Used: {current_bias_for_nsz}, Cycle Type: {signal_type}, Active: {nsz_active}, Bound: {nsz_lower_bound}")


# === 8. Bybit 웹소켓 메시지 처리 로직 (완전 수정) ===
async def process_kline(msg_data):
    """ Kline 데이터 처리 및 시그널 확인 (Bybit 형식) """
    global gui, last_two_candles, current_step_index, signal_type, symbol_info, client, config
    global pending_entry_info, step_profit_handler_info 
    global entry_quantity_list, open_orders_state, order_type_mapping, per_step_hedge_quantity_list, cumulative_entry_quantity_list, exit_ratio_list
    global last_trigger_order_price, nsz_active, nsz_lower_bound

    try:
        # Bybit kline 데이터는 리스트 형태로 옴
        if not isinstance(msg_data, list) or len(msg_data) == 0:
            logging.warning(f"비정상적인 kline 메시지 수신: {msg_data}")
            return

        kline = msg_data[0] # 첫 번째 (최신) 캔들 데이터 사용
        is_closed = kline.get('confirm', False) # 'confirm' 플래그가 캔들 마감 여부

        if is_closed:
            # --- 1. 캔들 정보 업데이트 (Bybit 키 사용) ---
            open_price_kline = float(kline.get('open', 0))
            close_price_kline = float(kline.get('close', 0))
            high_price_kline = float(kline.get('high', 0))
            low_price_kline = float(kline.get('low', 0))
            volume_kline = float(kline.get('volume', 0))
            kline_time_ms = int(kline.get('start', 0)) # Bybit는 'start' 시간 제공
            kline_time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(kline_time_ms / 1000))
            
            if gui: gui.update_kline_data(f"{kline_time_str} O:{open_price_kline} H:{high_price_kline} L:{low_price_kline} C:{close_price_kline} V:{volume_kline}")

            current_candle_data = {'open': open_price_kline, 'close': close_price_kline, 'high': high_price_kline, 'low': low_price_kline, 'volume': volume_kline, 'time': kline_time_str}
            last_two_candles.append(current_candle_data)
            if len(last_two_candles) > 2:
                last_two_candles.pop(0)

            # --- 2. 타임아웃 처리 (로직 동일) ---
            handling_pending_entry_timeout = False
            if pending_entry_info.get('active', False):
                elapsed_seconds_kline = time.time() - pending_entry_info.get('start_time', 0)
                kline_interval_str = str(config.KLINE_INTERVAL) # config가 Bybit 간격(1, 5, D)을 반환해야 함
                
                # Bybit 간격 문자열에 따른 타임아웃 재설정
                min_wait_seconds_for_timeout = 280 # 기본 (5m)
                if kline_interval_str == '1': min_wait_seconds_for_timeout = 50
                elif kline_interval_str == '3': min_wait_seconds_for_timeout = 170
                
                if elapsed_seconds_kline >= min_wait_seconds_for_timeout:
                    logging.warning(f"진입 시도(pending_entry_info 스텝: {pending_entry_info.get('step')}) 타임아웃. 초기화.")
                    handling_pending_entry_timeout = True
                    pending_entry_info = {'active': False, 'order_ids': [], 'step': -1, 'signal_type': None, 'attempt_key_prefix': None, 'start_time': 0, 'division_status': {}}
                    if gui: gui.update_status(f"스텝 {pending_entry_info.get('step')} 진입 타임아웃.")
            
            # --- 3. 시그널 확인 및 처리 (로직 동일) ---
            if not handling_pending_entry_timeout and len(last_two_candles) == 2:
                signal_status_msg = "대기 중..."
                
                prev_prev_candle_kline = last_two_candles[0]
                prev_candle_kline = last_two_candles[1]
                current_price_for_signal_check = prev_candle_kline['close']
                ignore_signal_due_to_nsz = False
                detected_kline_signal_type = None
                preferred_bias = get_preferred_signal_type()
                if not signal_type: signal_type = preferred_bias

                if nsz_active:
                    if preferred_bias == 'LONG' and current_price_for_signal_check >= nsz_lower_bound:
                        ignore_signal_due_to_nsz = True
                        signal_status_msg = f"{kline_time_str} [NSZ] 시그널 무시(LONG) - 현재가({current_price_for_signal_check}) >= 하한선({nsz_lower_bound})"
                    elif preferred_bias == 'SHORT' and current_price_for_signal_check <= nsz_lower_bound:
                        ignore_signal_due_to_nsz = True
                        signal_status_msg = f"{kline_time_str} [NSZ] 시그널 무시(SHORT) - 현재가({current_price_for_signal_check}) <= 상한선({nsz_lower_bound})"

                if not ignore_signal_due_to_nsz:
                    if preferred_bias == 'LONG':
                        is_prev_prev_bearish = prev_prev_candle_kline['close'] < prev_prev_candle_kline['open']
                        is_prev_bullish = prev_candle_kline['close'] >= prev_candle_kline['open']
                        if is_prev_prev_bearish and is_prev_bullish:
                            denominator = prev_prev_candle_kline['open'] - prev_prev_candle_kline['close']
                            if denominator > 0:
                                ratio = (prev_candle_kline['close'] - prev_candle_kline['open']) / denominator
                                if config.PRICE_RATIO_MIN <= ratio <= config.PRICE_RATIO_MAX:
                                    detected_kline_signal_type = 'LONG'
                    
                    elif preferred_bias == 'SHORT':
                        is_prev_prev_bullish = prev_prev_candle_kline['close'] > prev_prev_candle_kline['open']
                        is_prev_bearish = prev_candle_kline['close'] < prev_candle_kline['open']
                        if is_prev_prev_bullish and is_prev_bearish:
                            denominator = prev_prev_candle_kline['close'] - prev_prev_candle_kline['open']
                            if denominator > 0:
                                ratio = (prev_candle_kline['open'] - prev_candle_kline['close']) / denominator
                                if config.PRICE_RATIO_MIN <= ratio <= config.PRICE_RATIO_MAX:
                                    detected_kline_signal_type = 'SHORT'
                    
                    if detected_kline_signal_type:
                        signal_status_msg = f"{kline_time_str}*** {detected_kline_signal_type} 시그널 발생! ***"
                        logging.info(f"*** {detected_kline_signal_type} 시그널 발생! ***")
                    else:
                        signal_status_msg = f"{kline_time_str}시그널 조건 불충족 (Candle: {prev_candle_kline['time']})"

                if gui:
                    gui.update_signal_status(signal_status_msg)

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
                            futures_client_global, gui, symbol_info, current_state_for_kline_logic_call, 
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

# === 9. Bybit Ticker 처리 로직 (완전 수정) ===
async def process_ticker(msg_data):
    """ Ticker 데이터(실시간 거래 가격) 처리 (Bybit 형식) """
    global gui, client, symbol_info, config, open_orders_state, order_type_mapping, signal_type, current_step_index
    global step_profit_handler_info, per_step_hedge_quantity_list, pending_entry_info, app_config
    global clear_line_exit_handler, futures_client_global

    try:
        if not main_app_running:
            return

        # Bybit trade 데이터는 리스트 형태
        if not isinstance(msg_data, list) or len(msg_data) == 0:
            logging.warning(f"비정상적인 Ticker(trade) 메시지 수신: {msg_data}")
            return

        # 최신 거래 정보 사용
        last_trade = msg_data[0]
        last_price_str = last_trade.get('p') # 'p'가 가격
        if not last_price_str:
            return

        try:
            current_market_price = Decimal(last_price_str)
            app_config['last_price'] = current_market_price
        except ValueError:
            logging.warning(f"Ticker 수신: 유효하지 않은 가격 형식 ({last_price_str}). 처리 건너뜀.")
            return

        if gui:
            gui.update_trade_data(last_price_str)
        
        # (Clear Line 핸들러 로직은 API 독립적이므로 변경 없음)
        if clear_line_exit_handler.get('active'):
            handler_line = clear_line_exit_handler['clear_line']
            handler_signal_type = clear_line_exit_handler['signal_type']
            
            trigger_exit = False
            
            if handler_signal_type == 'LONG':
                if current_market_price < handler_line:
                    clear_line_exit_handler['price_was_below'] = True
                if current_market_price > handler_line and clear_line_exit_handler['price_was_below']:
                    logging.info(f"*** [ClearLine] LONG 포지션 '상방 돌파' 트리거! ***")
                    trigger_exit = True

            elif handler_signal_type == 'SHORT':
                if current_market_price > handler_line:
                    clear_line_exit_handler['price_was_above'] = True
                if current_market_price < handler_line and clear_line_exit_handler['price_was_above']:
                    logging.info(f"*** [ClearLine] SHORT 포지션 '하방 돌파' 트리거! ***")
                    trigger_exit = True
            
            if trigger_exit:
                clear_line_exit_handler['active'] = False
                clear_line_exit_handler['price_was_below'] = False
                clear_line_exit_handler['price_was_above'] = False
                
                if gui: gui.update_status("Clear Line 트리거! 전체 포지션 종료/초기화...")
                
                try:
                    logging.info(f"[ClearLine] {config.SYMBOL} 모든 오픈 포지션 강제 종료 시도...")
                    # (참고: logic.py의 close_all_open_positions_for_symbol이 Bybit용으로 수정되어야 함)
                    close_success = await close_all_open_positions_for_symbol(
                        futures_client_global, 
                        config.SYMBOL, 
                        symbol_info, 
                        open_orders_state, 
                        order_type_mapping
                    )
                    if close_success:
                        logging.info(f"[ClearLine] 모든 포지션 종료 주문 요청 완료.")
                        await asyncio.sleep(2.0)
                    else:
                        logging.error(f"[ClearLine] 포지션 종료에 실패. 수동 확인 필요.")
                
                except Exception as e_close_all:
                    logging.critical(f"[ClearLine] 포지션 전체 종료 중 치명적 오류: {e_close_all}", exc_info=True)

                logging.info("[ClearLine] 포지션 강제 종료 후, 사이클 초기화 (finalize_cycle_and_reset) 호출.")
                await finalize_cycle_and_reset("ClearLineTrigger")
                
                return

        logging.debug(f"Trade 수신 ({config.SYMBOL}): 가격={current_market_price}")

        if current_market_price <= Decimal('0'):
            return

        # (이하 시나리오 핸들러 및 조건부 진입 로직은 API 독립적이므로 변경 없음)
        # --- 1. '부분 헤지 익절 후 TSM' 시나리오 처리 ---
        if step_profit_handler_info.get('active') and \
           step_profit_handler_info.get('scenario') == 'partial_hedge_exit_then_main_tsm' and \
           not step_profit_handler_info.get('waiting_for_hedge_exit_fill'):
            
            target_price_for_hedge_trigger = step_profit_handler_info['profit_target_price_for_hedge_exit']
            main_pos_side_of_handler = step_profit_handler_info['main_pos_side_for_tsm']
            current_step_of_handler = step_profit_handler_info['step_index_at_trigger']

            price_condition_met = False
            if main_pos_side_of_handler == 'LONG' and current_market_price >= target_price_for_hedge_trigger:
                price_condition_met = True
            elif main_pos_side_of_handler == 'SHORT' and current_market_price <= target_price_for_hedge_trigger:
                price_condition_met = True
            
            if price_condition_met:
                logging.info(f"*** Ticker: 스텝 {current_step_of_handler} '부분 헤지 익절' 목표가 {target_price_for_hedge_trigger} 도달! ***")
                
                step_profit_handler_info['waiting_for_hedge_exit_fill'] = True
                
                hedge_qty_to_exit = step_profit_handler_info['hedge_exit_quantity']
                
                state_for_hedge_exit_logic = {
                    'symbol': config.SYMBOL,
                    'open_orders_state': open_orders_state,
                    'order_type_mapping': order_type_mapping
                }
                
                callback_rate = config.CALLBACK_RATE

                # (참고: logic.py의 place_trailing_stop_exit_order가 Bybit용으로 수정되어야 함)
                order_data_hedge_exit, success_hedge_exit, err_code_hedge_exit = await place_trailing_stop_exit_order(
                    client=client,
                    symbol_info_local=symbol_info,
                    state=state_for_hedge_exit_logic,
                    current_step=current_step_of_handler,
                    quantity=float(hedge_qty_to_exit),
                    main_pos_side=main_pos_side_of_handler,
                    callback_rate=callback_rate
                )

                if success_hedge_exit and order_data_hedge_exit:
                    step_profit_handler_info['hedge_exit_order_id'] = str(order_data_hedge_exit.get('orderId'))
                    logging.info(f"부분 헤지 익절 TSM 주문 요청 성공. ID: {step_profit_handler_info['hedge_exit_order_id']}. 발동 대기 중...")
                    if gui: gui.update_status(f"스텝{current_step_of_handler} 헤지 TSM 요청됨")
                else:
                    logging.error(f"부분 헤지 익절 TSM 주문 요청 실패. ErrorCode: {err_code_hedge_exit}. 시나리오 중단 가능성.")
                    step_profit_handler_info['active'] = False 
                    step_profit_handler_info['waiting_for_hedge_exit_fill'] = False
        
        # --- 2. 조건부 시장가 *진입* 주문 트리거 감시 ---
        if pending_entry_info.get('active') and pending_entry_info['division_status'].get('triggers'):
            division_status = pending_entry_info['division_status']
            triggers_list = division_status.get('triggers', [])
            idx_to_watch = division_status.get('next_sub_order_to_trigger_index', 0)
            
            if 0 <= idx_to_watch < len(triggers_list):
                trigger_info = triggers_list[idx_to_watch]
                trigger_price_entry = Decimal(str(trigger_info.get('trigger_price', 0)))
                trigger_qty_entry = Decimal(str(trigger_info.get('quantity', 0)))
                trigger_side_entry = trigger_info.get('side')
                
                entry_condition_met = False
                # (Bybit는 'Buy', 'Sell' 문자열을 사용하지만, 내부 로직은 SIDE_BUY/SELL을 사용한다고 가정)
                if trigger_side_entry == "BUY" and current_market_price <= trigger_price_entry:
                    entry_condition_met = True
                elif trigger_side_entry == "SELL" and current_market_price >= trigger_price_entry:
                    entry_condition_met = True
                    
                if entry_condition_met:
                    logging.info(f"*** Ticker: 조건부 시장가 *진입* 트리거! 스텝 {pending_entry_info.get('step')}, 분할 {idx_to_watch+1}/{division_status.get('num_total_divisions_for_step')} ***")
                    
                    entry_pos_side = pending_entry_info.get('signal_type')
                    attempt_key_prefix_entry = division_status.get('attempt_key_prefix_internal')
                    
                    state_for_triggered_entry = {
                        'symbol': config.SYMBOL,
                        'open_orders_state': open_orders_state,
                        'order_type_mapping': order_type_mapping
                    }
                    # (참고: logic.py의 place_triggered_market_order가 Bybit용으로 수정되어야 함)
                    success_triggered_entry, order_data_triggered_entry = await place_triggered_market_order(
                        client, gui, symbol_info, state_for_triggered_entry,
                        pending_entry_info.get('step'),
                        idx_to_watch,
                        float(trigger_qty_entry),
                        trigger_side_entry,
                        entry_pos_side,
                        attempt_key_prefix_entry
                    )
                    
                    if success_triggered_entry and order_data_triggered_entry:
                        logging.info(f"조건부 시장가 진입 주문(ID: {order_data_triggered_entry.get('orderId')}) 요청 성공. 다음 분할 대기.")
                        division_status['next_sub_order_to_trigger_index'] = idx_to_watch + 1
                    else:
                        logging.error(f"조건부 시장가 진입 주문 요청 실패.")

                    if division_status.get('next_sub_order_to_trigger_index', 0) >= len(triggers_list):
                        logging.info(f"스텝 {pending_entry_info.get('step')}의 모든 조건부 진입 분할 주문이 트리거/요청됨.")

    except asyncio.CancelledError:
        logging.info("Ticker 처리 태스크 취소됨.")
    except Exception as e_ticker:
        logging.error(f"process_ticker 처리 중 예외: {e_ticker}", exc_info=True)
        if step_profit_handler_info:
            step_profit_handler_info['active'] = False
            step_profit_handler_info['waiting_for_hedge_exit_fill'] = False
        if pending_entry_info :
            pending_entry_info['active'] = False
        if clear_line_exit_handler:
            clear_line_exit_handler['active'] = False
        if gui:
            try: gui.update_status("Ticker 처리 오류!")
            except Exception as gui_err_ticker: logging.error(f"Ticker 오류 후 GUI 상태 업데이트 중 추가 오류: {gui_err_ticker}")

# (이 함수는 API와 독립적이므로 변경 없음)
async def handle_step_decrement(filled_step: int, previous_exit_price: float, final_pnl_str: str):
    global current_step_index, gui, futures_client_global, symbol_info, signal_type
    global nsz_lower_bound, nsz_active, nsz_history
    global clear_line_exit_handler
    global open_orders_state, order_type_mapping
    global entry_quantity_list, exit_ratio_list, per_step_hedge_quantity_list, cumulative_entry_quantity_list, app_config

    logging.info(f"스텝 {filled_step}의 부분 익절 완료 (체결가: {previous_exit_price}). 현재 스텝({current_step_index})에서 1을 감소시킵니다.")
    
    current_step_index -= 1
    if gui:
        gui.update_current_step(current_step_index)

    logging.info(f"[NSZ/ClearLine] 스텝다운 후 현재 포지션 평단가 기준으로 재계산 시작...")
    current_avg_price = 0.0
    position_found = False
    
    category = app_config.get('CATEGORY', 'linear')
    
    try:
        if current_step_index >= 0 and signal_type:
            max_retries = config.ORDER_RETRY_ATTEMPTS
            retry_delay = config.ORDER_RETRY_DELAY_SECONDS

            for attempt in range(max_retries):
                try:
                    # === 10. Bybit API 호출 ===
                    response = await asyncio.to_thread(
                        futures_client_global.get_positions,
                        category=category,
                        symbol=config.SYMBOL
                    )
                    positions = response.get('result', {}).get('list', [])
                    
                    # Bybit는 L/S 포지션을 side와 size로 구분
                    current_pos = None
                    for p in positions:
                        if signal_type == 'LONG' and p.get('side') == 'Buy' and Decimal(p.get('size', '0')) > 0:
                            current_pos = p
                            break
                        if signal_type == 'SHORT' and p.get('side') == 'Sell' and Decimal(p.get('size', '0')) > 0:
                            current_pos = p
                            break

                    if current_pos:
                        pos_amt_str = current_pos.get('size', '0')
                        avg_price_str = current_pos.get('avgPrice', '0') # 'avgPrice'
                        
                        if Decimal(pos_amt_str) != Decimal('0') and Decimal(avg_price_str) > Decimal('0'):
                            current_avg_price = float(avg_price_str)
                            position_found = True
                            logging.info(f"[NSZ/ClearLine] 평단가 조회 성공 (시도 {attempt + 1}/{max_retries}): {current_avg_price}")
                            break
                        else:
                            logging.warning(f"[NSZ/ClearLine] 시도 {attempt + 1}/{max_retries}: 포지션은 찾았으나 수량이 0이거나 평단가가 유효하지 않음 (수량: {pos_amt_str}, 평단가: {avg_price_str}).")
                            if Decimal(pos_amt_str) == Decimal('0'):
                                position_found = False
                                break
                    else:
                        logging.warning(f"[NSZ/ClearLine] 시도 {attempt + 1}/{max_retries}: '{signal_type}' 포지션을 찾을 수 없음.")

                except Exception as e:
                    logging.warning(f"[NSZ/ClearLine] 평단가 조회 시도 {attempt + 1}/{max_retries} 실패: {e}")

                if attempt < max_retries - 1:
                    logging.info(f"잠시 후({retry_delay}초) 평단가 조회를 재시도합니다...")
                    await asyncio.sleep(retry_delay)
                else:
                    logging.error(f"[NSZ/ClearLine] 평단가 조회 최종 실패 ({max_retries}회 시도).")
                    position_found = False
            
            # (이하 NSZ/ClearLine 계산 로직은 API 독립적이므로 변경 없음)
            if position_found and current_avg_price > 0:
                logging.info(f"  -> 현재 포지션 평단가({current_avg_price})를 기준으로 NSZ를 새로 설정합니다.")
                calculate_and_update_nsz(current_avg_price, symbol_info, gui, signal_type, current_step_index)
                
                avg_price_at_trigger = Decimal(str(current_avg_price))
                exit_price_at_trigger = Decimal(str(previous_exit_price))
                clear_line_calculated = Decimal('0')

                if signal_type == 'LONG':
                    profit_range = exit_price_at_trigger - avg_price_at_trigger
                    if profit_range > 0:
                        clear_line_calculated = avg_price_at_trigger + (profit_range * Decimal('0.9'))
                elif signal_type == 'SHORT':
                    profit_range = avg_price_at_trigger - exit_price_at_trigger
                    if profit_range > 0:
                        clear_line_calculated = avg_price_at_trigger - (profit_range * Decimal('0.9'))
                
                if clear_line_calculated > 0:
                    clear_line_exit_handler['active'] = True
                    clear_line_exit_handler['clear_line'] = clear_line_calculated
                    clear_line_exit_handler['price_was_below'] = False
                    clear_line_exit_handler['price_was_above'] = False
                    clear_line_exit_handler['signal_type'] = signal_type
                    
                    price_precision_gui = symbol_info.get('pricePrecision', 2)
                    clear_line_str = f"{clear_line_calculated:.{price_precision_gui}f}"
                    logging.info(f"[ClearLine] 'clear_line'이 새로 설정/업데이트되었습니다: {clear_line_str}")
                    if gui: gui.update_status(f"Clear Line 갱신: {clear_line_str}")
                else:
                    logging.warning(f"[ClearLine] 계산 실패. 핸들러를 비활성화합니다.")
                    clear_line_exit_handler['active'] = False
            else:
                nsz_active = False; nsz_lower_bound = 0.0
                if gui: gui.update_nsz_range("-")
                logging.info("[NSZ/ClearLine] 남은 포지션이 없거나 평단가 조회에 실패하여 NSZ/ClearLine을 비활성화합니다.")
                clear_line_exit_handler['active'] = False
        else:
            nsz_active = False; nsz_lower_bound = 0.0
            if gui: gui.update_nsz_range("-")
            logging.info(f"[NSZ/ClearLine] 현재 스텝이 {current_step_index}이므로 NSZ/ClearLine을 비활성화합니다.")
            clear_line_exit_handler['active'] = False
    except Exception as e:
        nsz_active = False; nsz_lower_bound = 0.0
        if gui: gui.update_nsz_range("계산 오류")
        logging.error(f"[NSZ/ClearLine] 재계산 중 최상위 오류 발생: {e}", exc_info=True)
        clear_line_exit_handler['active'] = False

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
        # (참고: logic.py의 place_orders_for_step이 Bybit용으로 수정되어야 함)
        await place_orders_for_step(futures_client_global, gui, symbol_info, current_state_for_logic, current_step_index, trigger_event='STEP_DOWN')


# (이 함수는 API와 독립적이므로 변경 없음, 단지 client 타입 힌트만 변경)
async def _wait_for_position_update(client_param: HTTP, symbol: str, position_side: str, expected_qty: Decimal, timeout_sec: int = 7) -> bool:
    start_time = time.time()
    logging.info(f"[{position_side} 포지션 업데이트 대기 시작] 목표 수량: {expected_qty}, 최대 대기: {timeout_sec}초")
    
    category = app_config.get('CATEGORY', 'linear')
    
    while time.time() - start_time < timeout_sec:
        try:
            # === 11. Bybit API 호출 ===
            response = await asyncio.to_thread(
                client_param.get_positions,
                category=category,
                symbol=symbol
            )
            positions = response.get('result', {}).get('list', [])
            
            current_qty = Decimal('0')
            pos_found = False
            for p in positions:
                side_str = p.get('side') # 'Buy' or 'Sell'
                if (position_side == 'LONG' and side_str == 'Buy') or (position_side == 'SHORT' and side_str == 'Sell'):
                    current_qty = Decimal(p.get('size', '0'))
                    pos_found = True
                    break
            
            if pos_found:
                if abs(current_qty - expected_qty) < Decimal('1e-8'):
                    logging.info(f"✅ 포지션 업데이트 확인 완료! 현재 수량: {current_qty}")
                    return True
                else:
                    logging.debug(f"  - 대기 중... (현재: {current_qty}, 목표: {expected_qty})")
            else:
                 logging.debug(f"  - 대기 중... ({position_side}) 포지션 정보 없음.")
            
            await asyncio.sleep(0.5)

        except Exception as e:
            logging.error(f"포지션 업데이트 대기 중 오류: {e}")
            await asyncio.sleep(1)

    logging.warning(f"⏰ 포지션 업데이트 시간 초과! ({timeout_sec}초) 목표 수량에 도달하지 못했습니다.")
    return False

# === 12. Bybit User Data 처리 로직 (완전 수정) ===
async def process_user_data(topic: str, msg_data):
    """ User Data Stream 처리 (Bybit 형식) """
    global current_balance, gui, config, open_orders_state, order_type_mapping, client, current_step_index, symbol_info, signal_type
    global last_trade_realized_pnl, entry_quantity_list, per_step_hedge_quantity_list, pending_entry_info
    global last_trigger_order_price, cumulative_entry_quantity_list, exit_ratio_list
    global order_pnl_accumulator, recently_expired_main_exit_ids
    global step_profit_handler_info, partial_exit_status, futures_client_global, app_config

    try:
        # Bybit는 토픽별로 데이터가 분리되어 옴
        
        # --- A. 지갑(Balance) 업데이트 ---
        if topic.startswith('wallet'):
            # Bybit 지갑 데이터는 리스트 형태
            if not isinstance(msg_data, list) or len(msg_data) == 0:
                return
            
            wallet_data = msg_data[0] # 첫 번째 항목 (보통 하나)
            account_type = wallet_data.get('accountType') # UNIFIED, CONTRACT, ...
            
            # (중요) 설정된 카테고리에 맞는 지갑 타입을 확인해야 함
            # 예: 'linear' -> 'CONTRACT', 'inverse' -> 'CONTRACT'
            # 예: 'UNIFIED' -> 'UNIFIED'
            # 이 로직은 사용자의 계정 타입(UTA/기존)에 따라 복잡해짐. 여기서는 'UNIFIED'를 가정.
            
            # (단순화된 로직: 'UNIFIED' 계정의 'coin' 리스트를 확인)
            coin_list = wallet_data.get('coin', [])
            for balance_item in coin_list:
                if balance_item.get('coin') == config.BALANCE_ASSET:
                    # 'walletBalance'가 사용 가능한 잔고일 수 있음 (Bybit 문서 확인 필요)
                    new_balance = float(balance_item.get('walletBalance', '0')) 
                    if abs(new_balance - current_balance) > 1e-9:
                        logging.info(f"잔고 업데이트 감지 ({config.BALANCE_ASSET}): {current_balance:.8f} -> {new_balance:.8f}")
                        current_balance = new_balance
                        if gui: gui.update_balance(f"{current_balance:.8f}")
                    break
            return

        # --- B. 포지션 업데이트 ---
        if topic.startswith('position'):
            if not isinstance(msg_data, list) or len(msg_data) == 0:
                return
            
            if gui:
                # Bybit는 심볼별 포지션 정보를 리스트로 전달
                target_positions = [p for p in msg_data if p.get('symbol') == config.SYMBOL]
                if target_positions:
                    logging.debug(f"POSITION_UPDATE (WS): {target_positions}")
                    # (참고: gui.update_position_display가 Bybit 형식에 맞게 수정되어야 함)
                    gui.update_position_display(target_positions, config.SYMBOL)
            return

        # --- C. 주문 업데이트 ---
        if topic.startswith('order'):
            if not isinstance(msg_data, list) or len(msg_data) == 0:
                return
            
            order_info = msg_data[0] # 주문 데이터는 리스트의 첫 번째 항목
            
            order_id_api = order_info.get('orderId')
            client_order_id_ws = order_info.get('orderLinkId') # 'orderLinkId'
            symbol_ws = order_info.get('symbol')
            status = order_info.get('orderStatus') # 'orderStatus' (e.g., New, PartiallyFilled, Filled, Cancelled)
            order_type_ws = order_info.get('orderType') # 'orderType' (e.g., Market, Limit)
            side_ws = order_info.get('side') # 'side' (e.g., Buy, Sell)
            # Bybit는 'positionIdx'로 L/S 헤지모드를 구분 (0=One-Way, 1=Buy/Long, 2=Sell/Short)
            pos_idx = order_info.get('positionIdx') 
            
            # positionIdx를 기반으로 PosSide 재구성 (내부 로직 호환성)
            pos_side_ws = 'LONG' if pos_idx == 1 else ('SHORT' if pos_idx == 2 else 'BOTH')
            
            qty_ws_str = order_info.get('qty', '0')
            filled_qty_this_event_str = order_info.get('lastExecQty', '0') # 'lastExecQty'
            cum_filled_qty_str = order_info.get('cumExecQty', '0') # 'cumExecQty'
            avg_price_str = order_info.get('avgPrice', '0') # 'avgPrice'
            last_filled_price_str = order_info.get('lastExecPrice', '0') # 'lastExecPrice'
            realized_profit_str = order_info.get('realizedPnl', '0') # 'realizedPnl'
            
            logging.info(f"사용자 데이터(주문) 수신: OrderID:{order_id_api}, ClientOID:{client_order_id_ws}, Status:{status}, Type:{order_type_ws}, Symbol:{symbol_ws}, Side:{side_ws}, PosSide(Idx):{pos_side_ws}({pos_idx}), Qty:{qty_ws_str}, Filled(이번):{filled_qty_this_event_str}, CumFilled:{cum_filled_qty_str}, AvgPrice:{avg_price_str}, LastPrice:{last_filled_price_str}, RP:{realized_profit_str}")

            if symbol_ws != config.SYMBOL:
                return 
            
            order_id_str = str(order_id_api)
            state_changed_for_gui_update = False
            reset_cycle_triggered_by_this_event = False
            current_event_pnl = Decimal(realized_profit_str)

            if status in ['PartiallyFilled', 'Filled'] and current_event_pnl != Decimal('0'):
                order_pnl_accumulator.setdefault(order_id_str, Decimal('0'))
                order_pnl_accumulator[order_id_str] += current_event_pnl
                logging.info(f"OrderID {order_id_str} PNL 누적: 현재 이벤트 RP={current_event_pnl}, 주문 총 누적 RP={order_pnl_accumulator[order_id_str]}")
                if gui: gui.update_total_pnl(str(current_event_pnl))

            # (로컬 상태 업데이트 로직은 Binance와 동일하게 유지)
            if status in ['New', 'PartiallyFilled']:
                if order_id_str in open_orders_state:
                    open_orders_state[order_id_str].update(order_info)
                else:
                    open_orders_state[order_id_str] = order_info.copy()
                
                if 'creationTime' not in open_orders_state[order_id_str]:
                    # Bybit는 'createdTime' 사용
                    open_orders_state[order_id_str]['creationTime'] = int(order_info.get('createdTime', time.time() * 1000)) / 1000.0
                
                state_changed_for_gui_update = True
                if status == 'PartiallyFilled':
                     logging.info(f"주문 {order_id_str} 부분 체결: {order_info.get('lastExecQty', '0')}@{order_info.get('lastExecPrice', '0')}")

            elif status in ['Filled', 'Cancelled', 'Expired', 'Rejected']:
                if order_id_str in open_orders_state:
                    open_orders_state.pop(order_id_str, None)
                    state_changed_for_gui_update = True
                
                custom_type_name_on_event = order_type_mapping.get(order_id_str)

                if custom_type_name_on_event:
                    order_total_accumulated_pnl = order_pnl_accumulator.get(order_id_str, Decimal('0'))
                    logging.info(f"주문 {status}: OrderID={order_id_str}, 구분={custom_type_name_on_event}, 주문총누적RP={order_total_accumulated_pnl if status == 'Filled' else 'N/A'}")

                    # (이하 로직은 API 독립적이므로, Bybit 상태값(Filled, Cancelled 등)만 맞으면 동일하게 작동)
                    # === 1. FILLED 상태일 때만 실행되는 블록 ===
                    if status == 'Filled':
                        if custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                            parts = custom_type_name_on_event.split('-')
                            step = int(parts[1])

                            if step != current_step_index:
                                logging.warning(f"수신된 익절 주문(스텝 {step})이 현재 스텝({current_step_index})과 다릅니다. 이벤트를 무시합니다.")
                                order_type_mapping.pop(order_id_str, None)
                                if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]
                                return
                            
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
                                filled_price = float(avg_price_str)
                                final_pnl_for_step = order_pnl_accumulator.get(order_id_str, '0')
                                await handle_step_decrement(step, filled_price, str(final_pnl_for_step))
                                if step in partial_exit_status: del partial_exit_status[step]
                                order_type_mapping.pop(order_id_str, None)
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
                                    order_type_mapping.pop(order_id_str, None)
                                    if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]
                                else:
                                    logging.info(f"[시나리오 1 진행중] 주 포지션 TSM 체결 완료. 헤지 익절(SM) 체결 대기.")
                        
                            elif custom_type_name_on_event.startswith(('MainStopLoss-', 'HedgeTakeProfitTSM-')):
                                logging.info(f"최종 단계 주문(ID: {order_id_str}, Type: {custom_type_name_on_event}) 체결 확인.")
                                final_pnl_for_cycle = str(order_pnl_accumulator.get(order_id_str, '0'))
                                logging.info("모든 포지션 청산 여부 확인 및 사이클 종료/리셋을 시작합니다.")
                                await check_all_positions_closed_and_finalize(futures_client_global, config.SYMBOL, final_pnl_for_cycle)
                                reset_cycle_triggered_by_this_event = True
                        
                        elif custom_type_name_on_event.startswith(('EntryAttempt-', 'Maginot-')):
                            # --- signal_type 결정 (Bybit 기준) ---
                            if pos_side_ws == 'LONG':
                                signal_type = 'LONG'
                            elif pos_side_ws == 'SHORT':
                                signal_type = 'SHORT'
                                
                            if signal_type:
                                logging.info(f"    체결 주문의 PositionSide({signal_type})를 기반으로 전역 signal_type 설정 완료.")
                            elif not signal_type:
                                signal_type = get_preferred_signal_type()
                                logging.warning(f"    체결 주문에 PositionSide 정보가 없어 설정값({signal_type})으로 전역 signal_type 설정.")
                            # --- signal_type 결정 끝 ---

                            is_entry_attempt = custom_type_name_on_event.startswith('EntryAttempt-')
                            prefix_filled = 'EntryAttempt-' if is_entry_attempt else 'Maginot-'
                            parts_filled = custom_type_name_on_event.replace(prefix_filled, '').split('-')
                            filled_step_num = int(parts_filled[0]) if parts_filled and parts_filled[0].isdigit() else -1

                            if filled_step_num != -1:
                                if current_step_index < filled_step_num:
                                    log_prefix_filled = "General(EntryAttempt)" if is_entry_attempt else "Maginot"
                                    logging.info(f"{log_prefix_filled} 주문(스텝 {filled_step_num}, ID: {order_id_str}) 체결.")

                                    try:
                                        filled_price_for_nsz_calc = float(avg_price_str)
                                        if filled_price_for_nsz_calc > 0:
                                            last_trigger_order_price = filled_price_for_nsz_calc
                                            calculate_and_update_nsz(last_trigger_order_price, symbol_info, gui, signal_type, filled_step_num)
                                    except Exception as nsz_err_filled: logging.error(f"NSZ 업데이트 오류 (ID: {order_id_str}): {nsz_err_filled}")

                                    current_step_index = filled_step_num
                                    if gui: gui.update_current_step(current_step_index)
                                    logging.info(f"*** 현재 스텝 업데이트 ({log_prefix_filled} 체결): {current_step_index} ***")

                                    hedge_qty_for_filled_step = per_step_hedge_quantity_list[filled_step_num]
                                    main_side_for_hedge_logic = signal_type

                                    # (참고: logic.py의 place_hedge_order_for_general 함수가 Bybit용으로 수정되어야 함)
                                    if hedge_qty_for_filled_step >= calculated_min_order_qty:
                                        logging.info(f"스텝 {filled_step_num} 체결 후 헤지 주문 실행. 주 방향: {main_side_for_hedge_logic}, 헤지수량: {hedge_qty_for_filled_step}>{calculated_min_order_qty}(최소주문수량)")
                                        state_for_hedge_call = {'symbol': config.SYMBOL, 'open_orders_state': open_orders_state, 'order_type_mapping': order_type_mapping}

                                        order_data_hedge, success_hedge, error_code_hedge = await place_hedge_order_for_general(futures_client_global, gui, symbol_info, state_for_hedge_call, filled_step_num, hedge_qty_for_filled_step, main_side_for_hedge_logic)

                                        if success_hedge:
                                            logging.info(f"스텝 {filled_step_num} 헤지 주문 요청 성공. 헤지 체결 후 다음 주문 설정이 진행됩니다.")
                                        else: 
                                            logging.error(f"스텝 {filled_step_num} 헤지 주문 실패 (Code: {error_code_hedge}). 헤지를 건너뛰고 즉시 익절/마지노 주문을 설정합니다.")
                                            trigger_event_for_orders = 'MAGINOT_FILL_HEDGE_FAIL' if not is_entry_attempt else 'ENTRY_FILL_HEDGE_FAIL'

                                            # Bybit 오류 코드 (예: 110007는 증거금 부족)
                                            is_margin_error = error_code_hedge == 110007 
                                            
                                            if is_margin_error and filled_step_num == config.STEPS - 1:
                                                logging.critical(f"!!!!!!!! 마지막 스텝({filled_step_num})에서 증거금 부족! 헤지를 건너뛰고 즉시 최종 손절(LAST) 주문을 설정합니다. !!!!!!!!!!")
                                                if gui: gui.update_status(f"!!! 스텝 {filled_step_num} 헤지 실패! 최종 손절 설정 시도 !!!")

                                                expected_total_qty_after_entry = Decimal(str(cumulative_entry_quantity_list[filled_step_num]))
                                                update_success = await _wait_for_position_update(futures_client_global, config.SYMBOL, signal_type, expected_total_qty_after_entry)

                                                if update_success:
                                                    state_for_final_orders = {
                                                        'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                                        'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                                        'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type,
                                                        'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                                        'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                                        'previous_exit_price': None
                                                    }
                                                    await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_final_orders, current_step_index, trigger_event='HEDGE_FAILED_LAST_STEP')
                                            else:
                                                logging.info(f"스텝 {filled_step_num} 헤지 주문 실패(Code: {error_code_hedge})로 헤지를 건너뛰고 즉시 익절 주문을 설정합니다.")
                                                state_for_next_orders_call = {
                                                    'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                                    'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                                    'exit_ratio_list': exit_ratio_list, 'signal_type': main_side_for_hedge_logic,
                                                    'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                                    'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                                    'previous_exit_price': None
                                                }
                                                await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_next_orders_call, current_step_index, trigger_event=trigger_event_for_orders)
                                    
                                    # (이하 헤지 0 또는 최소수량 미만 로직은 동일)
                                    elif hedge_qty_for_filled_step == 0:
                                        logging.info(f"스텝 {filled_step_num} 헤지 수량이 0이므로 즉시 다음 익절 주문을 설정합니다.")
                                        state_for_zero_hedge_call = {
                                            'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                            'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                            'exit_ratio_list': exit_ratio_list, 'signal_type': main_side_for_hedge_logic,
                                            'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                            'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                            'previous_exit_price': None
                                        }
                                        trigger = 'MAGINOT_FILL_ZERO_HEDGE' if not is_entry_attempt else 'ENTRY_FILL_ZERO_HEDGE'
                                        await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_zero_hedge_call, current_step_index, trigger_event=trigger)
                                    else:
                                        logging.info(f"스텝 {filled_step_num} 헤지 수량({hedge_qty_for_filled_step})이 최소 주문 수량({calculated_min_order_qty})보다 작아 헤지 주문을 건너뛰고 즉시 익절 주문을 설정합니다.")
                                        state_for_small_hedge_call = {
                                            'symbol': config.SYMBOL, 'open_orders_state': open_orders_state,
                                            'order_type_mapping': order_type_mapping, 'entry_quantity_list': entry_quantity_list,
                                            'exit_ratio_list': exit_ratio_list, 'signal_type': main_side_for_hedge_logic,
                                            'per_step_hedge_quantity_list': per_step_hedge_quantity_list,
                                            'cumulative_entry_quantity_list': cumulative_entry_quantity_list,
                                            'previous_exit_price': None
                                        }
                                        trigger = 'MAGINOT_FILL_SMALL_HEDGE' if not is_entry_attempt else 'ENTRY_FILL_SMALL_HEDGE'
                                        await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_small_hedge_call, current_step_index, trigger_event=trigger)
                                else:
                                    logging.warning(f"중복 체결 이벤트 감지: OrderID={order_id_str}, 스텝={filled_step_num}. 현재 스텝({current_step_index})이 이미 높거나 같으므로 무시합니다.")

                        elif custom_type_name_on_event.startswith('HedgeForGeneral-'):
                            logging.info(f"헤지 주문(ID: {order_id_str}, 구분: {custom_type_name_on_event}) 체결 확인.")
                            parts = custom_type_name_on_event.split('-')
                            hedged_step = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else -1

                            if hedged_step == current_step_index:
                                logging.info(f"스텝 {hedged_step}의 헤지 포지션 생성이 완료되었습니다. API 업데이트를 기다립니다...")
                                expected_main_qty = Decimal(str(cumulative_entry_quantity_list[current_step_index]))
                                update_success = await _wait_for_position_update(futures_client_global, config.SYMBOL, signal_type, expected_main_qty)

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
                                    await place_orders_for_step(futures_client_global, gui, symbol_info, state_for_orders, current_step_index, trigger_event='HEDGE_COMPLETED')
                                else:
                                    logging.error(f"포지션 정보 업데이트 대기 시간 초과! 스텝 {current_step_index}의 익절 주문 설정을 건너뜁니다.")
                                    if gui: gui.update_status(f"오류: 스텝 {current_step_index} 포지션 업데이트 실패!")
                            else:
                                logging.warning(f"체결된 헤지 주문의 스텝({hedged_step})과 현재 스텝({current_step_index})이 일치하지 않아 추가 작업을 건너뜁니다.")

                        elif custom_type_name_on_event.startswith(('SysClosePos-')):
                            logging.info(f"시스템 주문(ID: {order_id_str}, Type: {custom_type_name_on_event}) 체결.")
                            order_type_mapping.pop(order_id_str, None)
                            if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                        else:
                            logging.warning(f"기타 매핑된 주문 '{custom_type_name_on_event}' (ID: {order_id_str}) FILLED.")
                            order_type_mapping.pop(order_id_str, None)
                            if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                    elif status in ['Cancelled', 'Expired', 'Rejected']:
                        logging.info(f"주문 {status}: OrderID={order_id_str}, 구분={custom_type_name_on_event}")
                        
                        if status == 'Expired' and custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                            logging.warning(f"부분 익절 주문(ID:{order_id_str})이 EXPIRED 상태가 되었습니다. (Bybit는 TSM Expired를 지원하지 않을 수 있음)")
                        
                        else:
                            logging.error(f"주문(ID:{order_id_str}, 구분:{custom_type_name_on_event})이 {status} 되었습니다.")
                            if custom_type_name_on_event.startswith(('MainPartialExitTSM-', 'HedgePartialExitSM-')):
                                parts = custom_type_name_on_event.split('-')
                                step = int(parts[1])
                                if step in partial_exit_status:
                                    del partial_exit_status[step]
                            
                            order_type_mapping.pop(order_id_str, None)
                            if order_id_str in order_pnl_accumulator:
                                del order_pnl_accumulator[order_id_str]
                
                else:
                    logging.warning(f"OrderID {order_id_str} (상태: {status})에 대한 로컬 매핑 정보 없음.")
                    if order_id_str in order_pnl_accumulator: del order_pnl_accumulator[order_id_str]

                if state_changed_for_gui_update and gui and not reset_cycle_triggered_by_this_event:
                    gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)

    except Exception as e_user_data_outer:
        logging.error(f"[process_user_data] 외부 처리 중 예외: {e_user_data_outer}", exc_info=True)


# (이 함수는 API 독립적이므로 변경 없음)
async def finalize_cycle_and_reset(realized_pnl_for_cycle_str: str):
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
    # (참고: logic.py의 cancel_orders_by_prefix가 Bybit용으로 수정되어야 함)
    prefixes_to_cancel = ['Maginot-', 'Exit-', 'ExitHedge-', 'EntryAttempt-', 'SubHedge-', 'GeneralHedge-', 'ExitHedgeSub-', 'PartialFillHedge-', 'MainExitTSM-', 'HedgeExitSM-']
    all_cancelled_ids = []
    tasks = [cancel_orders_by_prefix(futures_client_global, config.SYMBOL, open_orders_state, order_type_mapping, prefix) for prefix in prefixes_to_cancel]
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

    if gui and all_cancelled_ids:
         logging.debug(f"취소된 주문({len(all_cancelled_ids)}개) 반영 위해 GUI 미체결 주문 목록 업데이트 시도.")
         await asyncio.sleep(0.1)
         gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
    elif gui:
        logging.debug("취소된 주문이 없어 미체결 주문 목록 GUI 업데이트 건너뜀 (곧 전체 리셋 예정).")

    logging.info("거래 상태 초기화 진행...");
    reset_global_state()
    
    logging.info("settings.ini 파일에서 설정 값을 다시 로드합니다...")
    load_config_from_ini(gui)

    order_pnl_accumulator.clear()
    logging.info("주문별 PNL 누적기 초기화 완료.")

    if gui:
        gui.reset_to_initial_state()
        gui.update_nsz_range("-")
        gui.update_status("재계산 및 재진입 준비 중...")

    apply_trading_mode_settings()
    
    try:
        # (참고: logic.py의 get_futures_balance가 Bybit용으로 수정되어야 함)
        new_current_balance, _ = await get_futures_balance(futures_client_global, config.BALANCE_ASSET, gui)
        current_balance = new_current_balance
    except Exception as e:
        logging.error(f"잔고 재조회 실패: {e}. 이전 잔고로 재계산 시도.")

    try:
        logging.info("사이클 리셋 후 레버리지 재설정 시도...")
        # (참고: logic.py의 set_leverage가 Bybit용으로 수정되어야 함)
        await set_leverage(futures_client_global, config.SYMBOL, config.TARGET_LEVERAGE, gui)
    except Exception as e:
        logging.error(f"리셋 중 레버리지 재설정 실패: {e}")

    recalc_success = await recalculate_all_data(futures_client_global, gui, symbol_info, calculated_min_order_qty, current_balance)

    if gui:
        try:
            if symbol_info:
                 # (참고: Bybit용 symbol_info 키로 수정 필요)
                 info_text = (f"수량(정밀도:{symbol_info.get('qtyPrecision','?')}, 최소:{symbol_info.get('minQty','?')}, 스텝:{symbol_info.get('stepSize','?')}), "
                              f"가격(정밀도:{symbol_info.get('pricePrecision','?')}, 스텝:{symbol_info.get('tickSize','?')})")
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
        stop_bot_logic()
        return

    if recalc_success:
        if config.AUTO_START_ON_RUN:
            await trigger_initial_entry(futures_client_global, gui)
        else:
            logging.info("AUTO_START_ON_RUN이 False이므로 자동 재진입 안 함. GUI에서 시작 필요.")
            if gui: gui.update_status("재계산 완료. 수동 시작 대기.")
    else:
        logging.error("데이터 재계산 실패로 초기 진입 불가.")
        if gui: gui.update_status("재계산 오류. 수동 조치 필요.")

    logging.info(f"사이클 완료 및 재시작 처리 완료 (다음 사이클 준비됨). 현재 누적 PNL(GUI): {gui.cumulative_pnl if gui else 'N/A'}")

# (이 함수는 API 독립적이므로 변경 없음, 단지 client 타입 힌트만 변경)
async def recalculate_all_data(client: HTTP, gui: GuiManager, symbol_info_local: dict, min_order_qty_local: float, current_balance_local: float):
    global entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list, calculated_min_order_qty
    logging.info("데이터 재계산 시작...")
    try:
        if not symbol_info_local or min_order_qty_local is None or current_balance_local <= 0:
             raise ValueError(f"재계산을 위한 사전 조건 부족/오류: symbol_info={bool(symbol_info_local)}, min_order_qty={min_order_qty_local}, current_balance={current_balance_local}")
        
        # (참고: logic.py의 calculate_entry_quantities가 Bybit용으로 수정되어야 함)
        entry_ok, entry_list_new, cumul_entry_list_new = await calculate_entry_quantities(client, config.SYMBOL, symbol_info_local, min_order_qty_local, current_balance_local, gui)
        if not entry_ok: raise Exception("진입 수량 계산 실패")
        entry_quantity_list = entry_list_new; cumulative_entry_quantity_list = cumul_entry_list_new
        
        # (참고: logic.py의 calculate_hedge_quantities가 Bybit용으로 수정되어야 함)
        hedge_ok, step_hedge_list_new, cumul_hedge_list_new = await calculate_hedge_quantities(symbol_info_local, entry_quantity_list, cumulative_entry_quantity_list, min_order_qty_local, gui)
        if not hedge_ok: raise Exception("헷지 수량 계산 실패")
        per_step_hedge_quantity_list = step_hedge_list_new; cumulative_hedge_quantity_list = cumul_hedge_list_new

        for i in range(1, len(per_step_hedge_quantity_list)):
            if per_step_hedge_quantity_list[i] > 0 and per_step_hedge_quantity_list[i] < calculated_min_order_qty:
                warning_msg = f"경고: 스텝 {i}의 헷지 수량({per_step_hedge_quantity_list[i]})이 최소 주문 수량({calculated_min_order_qty})보다 작습니다."
                logging.warning(warning_msg)
                if gui: gui.update_status(warning_msg)

        # (참고: logic.py의 calculate_exit_ratios는 API 비종속적이므로 수정 불필요)
        exit_ok, exit_ratios_new = await calculate_exit_ratios(gui)
        if not exit_ok: raise Exception("Exit 비율 계산 실패")
        exit_ratio_list = exit_ratios_new
        logging.info("데이터 재계산 완료.")
        return True
    except Exception as e:
        logging.error(f"데이터 재계산 중 오류: {e}", exc_info=True)
        entry_quantity_list, cumulative_entry_quantity_list = [], []; per_step_hedge_quantity_list, cumulative_hedge_quantity_list = [], []; exit_ratio_list = []
        return False

# (이 함수는 API 독립적이므로 변경 없음, 단지 client 타입 힌트만 변경)
async def trigger_initial_entry(client_param: HTTP, gui_param: GuiManager):
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

    # (참고: logic.py의 place_general_order_market이 Bybit용으로 수정되어야 함)
    order_data, success, _ = await place_general_order_market(
        client_param, gui_param, symbol_info, current_state_for_logic_call,
        target_step_for_initial_entry,
        quantity_for_step0,
        base_attempt_key_prefix,
        current_signal_type_for_initial_entry
    )

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

# (이 함수는 API 독립적이므로 변경 없음, 단지 client 타입 힌트만 변경)
async def advance_to_next_step(client_param: HTTP, gui_param: GuiManager, symbol_info_local: dict, state_local: dict, filled_maginot_step: int):
    global current_step_index, last_entry_price, entry_quantity_list, cumulative_entry_quantity_list, exit_ratio_list, config, per_step_hedge_quantity_list, exit_orders_status, app_config
    open_orders_state_local = state_local.get('open_orders_state', {}); order_type_mapping_local = state_local.get('order_type_mapping', {})
    symbol_local = state_local.get('symbol'); signal_type_from_state_local = state_local.get('signal_type')
    remaining_maginot_orders = False; maginot_prefix_for_step = f'Maginot-{filled_maginot_step}-'
    
    category = app_config.get('CATEGORY', 'linear')

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
                # === 13. Bybit API 호출 ===
                response = await asyncio.to_thread(
                    client_param.get_positions,
                    category=category,
                    symbol=symbol_local
                )
                positions = response.get('result', {}).get('list', [])
                
                current_pos = None
                for p in positions:
                    if signal_type_from_state_local == 'LONG' and p.get('side') == 'Buy': current_pos = p; break
                    if signal_type_from_state_local == 'SHORT' and p.get('side') == 'Sell': current_pos = p; break

                if current_pos and float(current_pos.get('size', '0')) != 0:
                    new_avg_entry_price = float(current_pos.get('avgPrice', '0')) # 'avgPrice'
                    if new_avg_entry_price > 0: logging.info(f"스텝 {next_step} 진입 후 평균 진입가 업데이트: {new_avg_entry_price}"); last_entry_price = new_avg_entry_price 
                    else: logging.warning(f"스텝 {next_step} 진입 후 유효하지 않은 평균 진입가 수신: {new_avg_entry_price}")
                else: logging.warning(f"스텝 {next_step} 진입 후 포지션 정보 조회 실패 또는 포지션 없음 (Target Side: {signal_type_from_state_local}).")
        except Exception as e: logging.error(f"스텝 {next_step} 진입 후 포지션 정보 조회/처리 오류: {e}")
        
        # (이하 로직은 API 독립적이므로 변경 없음)
        if 0 <= next_step < len(per_step_hedge_quantity_list):
            hedge_qty_for_this_maginot_step = per_step_hedge_quantity_list[next_step]
            if hedge_qty_for_this_maginot_step > 0:
                if signal_type_from_state_local: 
                    logging.info(f"[Maginot 체결 후 헤지] 스텝 {next_step} 진입에 따른 전체 헤지 주문 시도. 수량: {hedge_qty_for_this_maginot_step}, 주 포지션: {signal_type_from_state_local}")
                    state_for_maginot_hedge_call = {'symbol': symbol_local, 'open_orders_state': open_orders_state_local, 'order_type_mapping': order_type_mapping_local}
                    # (참고: logic.py의 place_maginot_step_hedge_order가 Bybit용으로 수정되어야 함)
                    await place_maginot_step_hedge_order(client_param, gui_param, symbol_info_local, state_for_maginot_hedge_call, next_step, hedge_qty_for_this_maginot_step, signal_type_from_state_local)
                else: logging.warning(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 주문 불가: 주 포지션 사이드(signal_type) 알 수 없음.")
            else: logging.info(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 수량이 0입니다. 헤지 주문을 건너뜁니다.")
        else: logging.warning(f"[Maginot 체결 후 헤지] 스텝 {next_step} 헤지 주문 불가: 유효하지 않은 스텝이거나 헤지 수량 목록에 접근할 수 없습니다.")
        
        current_step_index = next_step
        if gui_param: gui_param.update_current_step(current_step_index) 
        logging.info(f"*** 현재 스텝 업데이트: {current_step_index} ***")
        current_state_for_orders = {'symbol': symbol_local, 'current_step_index': current_step_index, 'open_orders_state': open_orders_state_local, 'order_type_mapping': order_type_mapping_local, 'maginot_ratio': config.MAGINOT, 'entry_quantity_list': entry_quantity_list, 'cumulative_entry_quantity_list': cumulative_entry_quantity_list, 'exit_ratio_list': exit_ratio_list, 'signal_type': signal_type_from_state_local}
        logging.debug(f"advance_to_next_step: Calling place_orders_for_step with state: {current_state_for_orders}")
        # (참고: logic.py의 place_orders_for_step이 Bybit용으로 수정되어야 함)
        await place_orders_for_step(client_param, gui_param, symbol_info_local, current_state_for_orders, current_step_index, exit_orders_status, trigger_event='HEDGE_COMPLETED')
    else: logging.debug(f"스텝 {filled_maginot_step}의 Maginot 주문이 아직 남아있어 다음 스텝 진행 대기.")


async def start_websockets(client_param: HTTP):
    global ws_client_public, ws_client_private, websocket_connection_task, gui, config, app_config
    
    await stop_websockets() # 기존 연결 정리
    websocket_connection_task = None
    
    try:
        if gui: gui.update_status("웹소켓 연결 중...")
        
        category = app_config.get('CATEGORY', 'linear')
        testnet = app_config.get('TESTNET', True)
        
        # 1. === 공용(Public) 클라이언트 생성 ===
        channel_type = category # 'linear' 또는 'inverse'
        ws_client_public = WebSocket(
            testnet=testnet,
            channel_type=channel_type,
            # (참고: 공용 클라이언트는 API 키가 필요 없을 수 있으나, pybit에서 요구할 수 있음)
            api_key=config.API_KEY,
            api_secret=config.API_SECRET
        )

        # 2. === 사적(Private) 클라이언트 생성 ===
        ws_client_private = WebSocket(
            testnet=testnet,
            channel_type='private', # <--- 핵심: 'private'로 변경
            api_key=config.API_KEY,
            api_secret=config.API_SECRET
        )
        
        symbol = config.SYMBOL
        kline_interval = config.KLINE_INTERVAL
        
        logging.info(f"Bybit WebSocket 구독 시작 (Testnet: {testnet}, Public Category: {channel_type}, Private: private)...")
        
        # 3. === 공용(Public) 토픽 구독 ===
        # Kline 구독
        logging.info(f"Subscribing to kline.{kline_interval}.{symbol} (Public)")
        ws_client_public.kline_stream(
            interval=kline_interval,
            symbol=symbol,
            callback=handle_websocket_message
        )
        
        # Public Trade 구독
        logging.info(f"Subscribing to publicTrade.{symbol} (Public)")
        ws_client_public.trade_stream(
            symbol=symbol,
            callback=handle_websocket_message
        )
        
        # 4. === 사적(Private) 토픽 구독 ===
        # Order 구독 (Private)
        logging.info("Subscribing to order (Private)")
        ws_client_private.order_stream(
            callback=handle_websocket_message
        )
        
        # Position 구독 (Private)
        logging.info("Subscribing to position (Private)")
        ws_client_private.position_stream(
            callback=handle_websocket_message
        )
        
        # Wallet 구독 (Private)
        logging.info("Subscribing to wallet (Private)")
        ws_client_private.wallet_stream(
            callback=handle_websocket_message
        )
        
        logging.info("웹소켓 구독 요청 완료.")
        if gui:
            gui.update_kline_status("연결됨")
            gui.update_trade_status("연결됨")
            gui.update_user_status("연결됨")
        
        # (이하 코드는 동일하게 유지)
        websocket_connection_task = asyncio.create_task(
            keep_pybit_connection_alive_dummy(), 
            name="Pybit_WS_Dummy_KeepAlive"
        )
        
        logging.info("pybit WebSocket (내부 스레드) 시작 완료 및 asyncio 대기 태스크 생성됨.")
        return True

    except asyncio.CancelledError:
        logging.info("웹소켓 시작 중 취소됨.")
        await stop_websockets()
        return False
    except Exception as e:
        logging.error(f"웹소켓 시작 중 예외 발생: {e}", exc_info=True)
        if gui: gui.update_status(f"웹소켓 연결 오류: {e}")
        await stop_websockets()
        return False

async def keep_pybit_connection_alive_dummy():
    """pybit WebSocket 객체가 내부 스레드에서 실행되는 동안 
    메인 asyncio 루프가 종료되지 않도록 대기하는 더미 태스크입니다."""
    global main_app_running, ws_client
    try:
        while main_app_running:
            # pybit의 ws_client가 살아있는지 (또는 연결 상태인지) 주기적으로 확인할 수 있습니다.
            # ws_client.is_connected()와 같은 메서드가 있다면 활용 (pybit 문서를 확인해야 함)
            # 여기서는 단순히 대기합니다.
            await asyncio.sleep(60) # 1분에 한 번씩 확인
            if not ws_client_public or not ws_client_private:
                logging.warning("[DummyTask] ws_client (public 또는 private)가 존재하지 않아 대기 종료.")
                break
            
            # pybit v5 기준: is_connected() 메서드가 없음.
            # 대신, ws_client.ws_listen()이 종료되었는지 확인하는 것은 어려움.
            # handle_websocket_message에서 연결 종료/오류를 감지하여
            # cancel_main_future()를 호출하는 것이 주된 종료 메커니즘이 됩니다.
            logging.debug("[DummyTask] pybit WebSocket 연결 유지 (대기 중...)")
            
    except asyncio.CancelledError:
        logging.info("pybit WebSocket 더미 대기 태스크 취소됨.")
    except Exception as e:
        logging.error(f"pybit WebSocket 더미 대기 태스크 중 오류: {e}", exc_info=True)
    finally:
        logging.info("pybit WebSocket 더미 대기 태스크 종료.")
        if main_app_running:
            # 이 태스크가 비정상 종료되면 메인 루프도 종료시킴
            cancel_main_future("Pybit Dummy Task Ended")

def handle_websocket_message(message):
    """
    pybit WebSocket으로부터 수신된 모든 메시지를 처리하는 콜백 함수입니다.
    이 함수는 pybit의 내부 스레드에서 실행됩니다.
    """
    global asyncio_loop, main_app_running, _loop_thread_id
    
    if not main_app_running or not asyncio_loop or not asyncio_loop.is_running():
        logging.warning("메시지 수신, (콜백 스레드), 하지만 앱이 실행 중이 아님. 무시.")
        return

    try:
        logging.debug(f"WS 메시지 수신 (콜백 스레드): {message}")
        
        # --- 1. 메시지 기본 파싱 (Bybit 형식) ---
        topic = message.get('topic')
        msg_type = message.get('type') # 'snapshot', 'delta'
        data = message.get('data')
        
        if not topic or not data:
            # 구독 성공/실패 응답 등
            if message.get('op') == 'subscribe':
                success = message.get('success', False)
                if success:
                    logging.info(f"WS 구독 성공: {message.get('ret_msg')}")
                else:
                    logging.error(f"WS 구독 실패: {message.get('ret_msg')}")
                    # 구독 실패 시 메인 루프 종료
                    if _loop_thread_id is not None:
                        # 람다 함수를 사용하여 cancel_main_future를 인자와 함께 전달
                        asyncio.run_coroutine_threadsafe(
                            lambda: cancel_main_future(f"WS 구독 실패: {message.get('ret_msg')}"), 
                            asyncio_loop
                        )
            return

        # --- 2. 비동기 루프로 작업 전달 ---
        # 콜백은 별도 스레드에서 실행되므로, asyncio 함수를 직접 호출(await)할 수 없습니다.
        # run_coroutine_threadsafe를 사용하여 메인 이벤트 루프에서 실행하도록 예약합니다.
        
        if topic.startswith('kline'):
            # kline 데이터(data)는 리스트 형태
            asyncio.run_coroutine_threadsafe(process_kline(data), asyncio_loop)
            
        elif topic.startswith('publicTrade'):
            # trade 데이터(data)는 리스트 형태
            asyncio.run_coroutine_threadsafe(process_ticker(data), asyncio_loop)
            
        elif topic.startswith(('order', 'position', 'wallet')):
            # 사용자 데이터(data)는 리스트 형태
            asyncio.run_coroutine_threadsafe(process_user_data(topic, data), asyncio_loop)
        
        else:
            logging.debug(f"처리되지 않은 WS 토픽: {topic}")

    except Exception as e:
        logging.error(f"웹소켓 메시지 콜백 핸들러(동기) 오류: {e}", exc_info=True)
        # 콜백에서 오류 발생 시 메인 루프 종료 시도
        if _loop_thread_id is not None:
            asyncio.run_coroutine_threadsafe(
                lambda: cancel_main_future(f"WS 콜백 핸들러 오류: {e}"), 
                asyncio_loop
            )

async def stop_websockets():
    """Bybit 웹소켓 연결을 종료합니다."""
    global ws_client_public, ws_client_private, websocket_connection_task
    logging.info("웹소켓 정리 시작...")
    
    if websocket_connection_task and not websocket_connection_task.done():
        websocket_connection_task.cancel()
        try:
            await websocket_connection_task
        except asyncio.CancelledError:
            pass # 정상 취소
    websocket_connection_task = None

    # 공용(Public) 클라이언트 종료
    if ws_client_public:
        try:
            logging.info("pybit Public WebSocket 객체 종료 시도...")
            ws_client_public.exit()
            logging.info("pybit Public WebSocket 객체 종료 완료.")
        except Exception as e:
            logging.error(f"pybit Public WebSocket 종료 중 오류: {e}")
    ws_client_public = None

    # 사적(Private) 클라이언트 종료
    if ws_client_private:
        try:
            logging.info("pybit Private WebSocket 객체 종료 시도...")
            ws_client_private.exit()
            logging.info("pybit Private WebSocket 객체 종료 완료.")
        except Exception as e:
            logging.error(f"pybit Private WebSocket 종료 중 오류: {e}")
    ws_client_private = None
    
    logging.info("웹소켓 정리 완료.")

# === 15. 시간 동기화 (Bybit용으로 수정) ===
async def check_and_sync_time_periodically(client_param: HTTP, gui_param: GuiManager, interval_seconds: int = 3600):
    global main_app_running
    logging.info(f"시간 동기화 확인 태스크 시작 (간격: {interval_seconds}초)")
    max_timeout_retries = 3
    timeout_retry_delay = 5 
    while main_app_running:
        try:
            current_retry = 0
            while current_retry < max_timeout_retries:
                try:
                    # Bybit API 호출 (동기 방식이므로 to_thread 사용)
                    server_time_response = await asyncio.to_thread(client_param.get_server_time)
                    
                    # Bybit 응답 형식: {'result': {'timeSecond': '1676711168', 'timeNano': '1676711168827874227'}, ...}
                    server_time_ms = int(server_time_response.get('result', {}).get('timeNano', 0)) // 1_000_000
                    if server_time_ms == 0:
                        server_time_ms = int(server_time_response.get('result', {}).get('timeSecond', 0)) * 1000
                    
                    if server_time_ms == 0:
                        raise Exception("서버 시간 응답 형식 오류")

                    local_time_ms = int(time.time() * 1000)
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
                    break # 성공 시 루프 탈출
                except asyncio.TimeoutError: # aiohttp 타임아웃은 여기서 잡히지 않을 수 있음
                    current_retry += 1
                    logging.warning(f"서버 시간 조회 중 타임아웃 발생 ({current_retry}/{max_timeout_retries}). {timeout_retry_delay}초 후 재시도...")
                    if current_retry >= max_timeout_retries: logging.error("서버 시간 조회 타임아웃 재시도 모두 실패."); break 
                    await asyncio.sleep(timeout_retry_delay)
                except Exception as e_time_check: 
                    logging.error(f"서버 시간 조회 중 예상치 못한 오류: {e_time_check}", exc_info=True)
                    # Bybit의 동기 클라이언트 타임아웃 처리
                    if "Timeout" in str(e_time_check) or "timed out" in str(e_time_check):
                        current_retry += 1
                        if current_retry >= max_timeout_retries: break
                        await asyncio.sleep(timeout_retry_delay)
                    else:
                        break # 타임아웃 외 오류는 중단
            await asyncio.sleep(interval_seconds) 
        except asyncio.CancelledError: logging.info("시간 동기화 확인 태스크 취소됨"); break
        except Exception as e: logging.error(f"시간 동기화 확인 태스크 외부 루프 오류: {e}", exc_info=True); await asyncio.sleep(interval_seconds) 
    logging.info("시간 동기화 확인 태스크 종료됨")

# (sync_windows_time 함수는 API와 독립적이므로 변경 없음)
async def sync_windows_time():
    """Windows 시간 동기화를 더 강력하게 수행합니다."""
    try:
        logging.info("Windows 시간 동기화 서비스 (w32time) 상태 확인 및 재시작/강제 동기화 시도...")
        
        # 1. 서비스가 실행 중이 아니면 시작
        subprocess.run(['sc', 'config', 'w32time', 'start=', 'auto'], check=True, shell=True)
        subprocess.run(['net', 'start', 'w32time'], capture_output=True, text=True, shell=True) # 이미 실행 중이어도 오류 아님

        # 2. NTP 서버와 강제로 재동기화 (가장 중요한 부분)
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
                    sync_failed = True; break # 중요한 명령어 실패 시 중단
            else:
                logging.info(f"명령어 실행 성공: {' '.join(cmd)}"); await asyncio.sleep(0.5) 
        if not sync_failed: logging.info("Windows 시간 강제 동기화 명령이 성공적으로 완료되었습니다.")
        else: logging.error("Windows 시간 강제 동기화에 실패했습니다.")
        return not sync_failed
    except subprocess.CalledProcessError as e: logging.error(f"Windows 시간 동기화 서비스 설정 중 오류 (관리자 권한 필요): {e}"); return False
    except Exception as e: logging.error(f"Windows 시간 동기화 중 예외 발생: {e}", exc_info=True); return False

# === 16. 봇 메인 로직 (Bybit용으로 수정) ===
async def run_bot_logic():
    """ 봇의 메인 로직을 실행하는 비동기 함수 (Bybit HTTP 클라이언트 사용) """
    global client, futures_client_global, main_app_running, main_waiting_future, gui, symbol_info, calculated_min_order_qty, leverage_set, current_balance, current_step_index, open_orders_state, order_type_mapping
    global entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list
    global position_update_task, signal_type, last_entry_price, open_orders_check_task, time_sync_task, app_config

    if not app_config.get('API_KEY') or not app_config.get('API_SECRET'):
        raise RuntimeError("API 키가 로드되지 않았습니다. settings.ini를 확인하세요.")

    logging.info("run_bot_logic 시작 (Bybit)")
    if gui: gui.update_status("클라이언트 생성 중...")
    try:
        # 1. Bybit HTTP 클라이언트 생성
        client = HTTP(
            testnet=app_config.get('TESTNET', True),
            api_key=config.API_KEY,
            api_secret=config.API_SECRET,
            # (참고: pybit는 내부적으로 aiohttp 세션을 관리. 타임아웃 설정이 필요하면 pybit 문서를 참조)
        )
        logging.info(f"Bybit HTTP 클라이언트 생성 완료 (Testnet: {app_config.get('TESTNET')}).")
        
        # (중요) Bybit는 선물/현물 클라이언트 구분이 명확하지 않음.
        # unified_trading을 사용하므로 client 객체 하나를 공유합니다.
        futures_client_global = client 
        
    except Exception as e:
        logging.critical(f"Bybit HTTP 클라이언트 생성 실패: {e}", exc_info=True)
        if gui:
            gui.update_status("클라이언트 생성 실패")
            gui.set_button_to_start_mode()
        main_app_running = False
        return

    try:
        if gui: gui.update_status("초기화 중...")

        # Bybit API를 사용하도록 logic.py 함수 호출 (모든 함수가 Bybit용으로 수정되었다고 가정)
        # (주의: logic.py의 함수 시그니처가 client: HTTP를 받도록 수정되어야 함)
        
        # (Bybit에는 check_futures_connection 대신 get_server_time 사용)
        try:
            await asyncio.to_thread(client.get_server_time)
            logging.info("Bybit 서버 연결 확인 완료.")
        except Exception as e:
            logging.error(f"Bybit 서버 연결 실패: {e}")
            raise Exception("서버 연결 실패")

        # (이하 logic 함수들이 Bybit API를 호출하도록 수정되었다고 가정)
        # (logic.py의 check_all_open_positions이 Bybit용으로 수정되어야 함)
        if await check_all_open_positions(futures_client_global): raise Exception("기존 포지션 감지됨 - 종료")
        # (logic.py의 check_and_cancel_pending_orders이 Bybit용으로 수정되어야 함)
        if not await check_and_cancel_pending_orders(futures_client_global): raise Exception("미체결 주문 처리 실패 - 종료")
        # (logic.py의 get_futures_balance이 Bybit용으로 수정되어야 함)
        current_balance, _ = await get_futures_balance(futures_client_global, config.BALANCE_ASSET, gui)
        
        # (Bybit는 포지션 모드(헤지/원웨이) 설정이 다름 -> logic.py에서 처리해야 함)
        # (logic.py의 check_position_mode이 Bybit용으로 수정되어야 함)
        if not await check_position_mode(futures_client_global, gui): raise Exception("포지션 모드 확인/설정 실패")
        
        # (logic.py의 set_leverage이 Bybit용으로 수정되어야 함)
        leverage_set, _ = await set_leverage(futures_client_global, config.SYMBOL, config.TARGET_LEVERAGE, gui)
        if not leverage_set: raise Exception("레버리지 설정 실패")
        
        # (logic.py의 get_symbol_info이 Bybit용으로 수정되어야 함)
        symbol_info_loaded, symbol_info_data = await get_symbol_info(futures_client_global, config.SYMBOL, gui)
        if not symbol_info_loaded: raise Exception("심볼 정보 조회 실패")
        symbol_info = symbol_info_data
        
        # (logic.py의 calculate_effective_min_qty이 Bybit용으로 수정되어야 함)
        calculated_min_order_qty, _ = await calculate_effective_min_qty(futures_client_global, config.SYMBOL, symbol_info, gui)
        if calculated_min_order_qty is None: raise Exception("최소 주문 수량 계산 실패")

        # (logic.py의 recalculate_all_data이 Bybit용으로 수정되어야 함)
        initial_recalc_ok = await recalculate_all_data(futures_client_global, gui, symbol_info, calculated_min_order_qty, current_balance)
        if not initial_recalc_ok: raise Exception("초기 데이터 계산 실패")

        try:
            category = app_config.get('CATEGORY', 'linear') # 카테고리 정보 필요

            # --- 수정: pybit 클라이언트 메서드를 to_thread로 직접 호출 ---
            response_orders = await asyncio.to_thread(
                futures_client_global.get_open_orders,
                category=category,
                symbol=config.SYMBOL
            )
            initial_open_orders = response_orders.get('result', {}).get('list', [])
            # --- 수정 끝 ---

            open_orders_state = {str(o['orderId']): o for o in initial_open_orders} # Bybit 응답에 맞게 'orderId' 사용
            order_type_mapping = {} 
            if gui: gui.update_open_orders_display(list(open_orders_state.values()), order_type_mapping)
            logging.info(f"초기 미체결 주문 로드 완료: {len(initial_open_orders)}개")

            # --- 수정: pybit 클라이언트 메서드를 to_thread로 직접 호출 ---
            response_positions = await asyncio.to_thread(
                futures_client_global.get_positions,
                category=category,
                symbol=config.SYMBOL
            )
            initial_positions = response_positions.get('result', {}).get('list', [])
            # --- 수정 끝 ---

            if gui: gui.update_position_display(initial_positions, config.SYMBOL) # GUI도 Bybit 형식에 맞게 수정 필요
            logging.info("초기 포지션 정보 로드 완료.")
        except Exception as e:
            logging.error(f"초기 주문/포지션 조회 실패: {e}")

        position_update_task = asyncio.create_task(update_positions_periodically(futures_client_global, config.SYMBOL, gui, config.POSITION_UPDATE_INTERVAL if hasattr(config, 'POSITION_UPDATE_INTERVAL') else 5))
        open_orders_check_task = asyncio.create_task(check_open_orders_periodically(futures_client_global, config.SYMBOL, gui, config.OPEN_ORDERS_CHECK_INTERVAL if hasattr(config, 'OPEN_ORDERS_CHECK_INTERVAL') else 3))
        if config.PERIODIC_TIME_CHECK_INTERVAL_SECONDS > 0:
            time_sync_task = asyncio.create_task(check_and_sync_time_periodically(futures_client_global, gui, config.PERIODIC_TIME_CHECK_INTERVAL_SECONDS))
            logging.info("시간 동기화 확인 태스크 시작됨")
        
        logging.info("초기화 성공적으로 완료.")

    except Exception as e:
        logging.error(f"초기화 실패: {e}", exc_info=True)
        if gui:
            gui.update_status(f"초기화 실패: {str(e)[:50]}...")
            gui.set_button_to_start_mode()
            gui.show_error_popup("초기화 실패", f"봇 초기화 중 심각한 오류가 발생했습니다.\n\n오류: {e}\n\n프로그램을 확인해주세요.")
        main_app_running = False
        # (Bybit HTTP 클라이언트 종료 메서드가 있다면 호출)
        # if client: client.close_session() # pybit v5는 자동 관리
        return

    while main_app_running:
        main_waiting_future = asyncio.Future()
        connection_started = False
        try:
            if gui: gui.update_status("웹소켓 연결 시도 중...")
            connection_started = await start_websockets(futures_client_global)
            if connection_started:
                logging.info("웹소켓 연결 성공.")
                if gui: gui.update_status("실행 중")
                if current_step_index == -1 and config.AUTO_START_ON_RUN:
                    await trigger_initial_entry(futures_client_global, gui)
                await main_waiting_future
            else:
                logging.error("웹소켓 시작 실패.")
                if main_app_running: # 사용자가 중지하지 않았는데 실패한 경우
                    logging.info(f"{config.RECONNECT_DELAY}초 후 재연결 시도...")
                    await asyncio.sleep(config.RECONNECT_DELAY)
                else:
                    break # 사용자가 중지한 경우 루프 탈출
        except asyncio.CancelledError:
            logging.info("메인 봇 로직 태스크 취소됨 (CancelledError).")
            main_app_running = False
        except Exception as e:
            logging.error(f"봇 로직 메인 루프 오류: {e}", exc_info=True)
        finally:
             logging.info("웹소켓 세션 정리 시도...")
             if gui and main_app_running: gui.update_status("웹소켓 재연결 중...")
             await stop_websockets()
             if main_app_running:
                  logging.info(f"{config.RECONNECT_DELAY}초 후 재연결 시도...")
                  try:
                      await asyncio.sleep(config.RECONNECT_DELAY)
                  except asyncio.CancelledError:
                      logging.info("재연결 대기 중 취소됨.")
                      main_app_running = False

    logging.info("봇 로직 종료 처리 시작...")
    if gui: gui.update_status("종료 중...")
    tasks_to_cancel = [position_update_task, open_orders_check_task, time_sync_task, websocket_connection_task]
    for task in tasks_to_cancel:
        if task and not task.done():
            task.cancel()
    try:
        tasks_to_wait = [t for t in tasks_to_cancel if t]
        if tasks_to_wait:
            await asyncio.wait(tasks_to_wait, timeout=2)
    except asyncio.TimeoutError:
        logging.warning("주기적/웹소켓 태스크 종료 시간 초과.")
    except Exception as e:
        logging.error(f"주기적/웹소켓 태스크 종료 중 오류: {e}")

    await stop_websockets()
    # (Bybit HTTP 클라이언트 종료)
    # if client: client.close_session() # v5는 자동 관리
    logging.info("Bybit HTTP 클라이언트 연결 종료됨 (자동 관리).")

    logging.info("봇 로직 태스크 완전히 종료됨.")
    if gui:
        gui.set_button_to_start_mode()
        gui.update_status("정지됨")

# (이하 함수들은 API와 독립적이므로, 원본 main.py와 동일하게 유지)
# (단지, client: AsyncClient 대신 client: HTTP를 받도록 logic.py가 수정되었다고 가정)

def apply_trading_mode_settings():
    """
    로드된 설정(app_config)을 기반으로 현재 거래 모드에 맞는
    SYMBOL, BALANCE_ASSET, WS_URL, CATEGORY, TESTNET을 일반 키로 설정합니다.
    (Bybit용으로 수정됨)
    """
    global app_config
    
    # Bybit는 'linear', 'inverse', 'option' 등 'category'가 중요
    mode = app_config.get('DEFAULT_TRADING_MODE', 'USDT-M') # USDT-M (linear) 또는 COIN-M (inverse)
    
    prefix = "USDT_M_" if mode == "USDT-M" else "COIN_M_"

    app_config['SYMBOL'] = app_config.get(f"{prefix}SYMBOL")
    app_config['BALANCE_ASSET'] = app_config.get(f"{prefix}BALANCE_ASSET")
    
    # Bybit용 추가 설정
    app_config['TESTNET'] = app_config.get('TESTNET', True)
    if mode == "USDT-M":
        app_config['CATEGORY'] = 'linear'
    elif mode == "COIN-M":
        app_config['CATEGORY'] = 'inverse'
    else:
        app_config['CATEGORY'] = 'linear' # 기본값

    logging.info(f"'{mode}' 모드 적용 (Category: {app_config.get('CATEGORY')}): SYMBOL='{app_config.get('SYMBOL')}', BALANCE_ASSET='{app_config.get('BALANCE_ASSET')}', Testnet={app_config.get('TESTNET')}")

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
            gui.set_button_to_stop_mode()
            gui.update_status("실행 중 (정지 예약 취소됨)")

def stop_bot_logic():
    """봇 로직 및 웹소켓 종료"""
    global main_app_running, websocket_connection_task, main_waiting_future, asyncio_loop, position_update_task, open_orders_check_task, time_sync_task
    if not main_app_running: logging.info("봇이 이미 정지 상태입니다."); return
    logging.info("봇 로직 종료 신호 수신.")
    main_app_running = False
    loop_to_use = asyncio_loop
    if loop_to_use and loop_to_use.is_running():
        logging.info("비동기 태스크 취소 시도...")
        tasks_to_cancel_on_stop = [main_waiting_future, position_update_task, open_orders_check_task, time_sync_task, websocket_connection_task]
        for task_obj in tasks_to_cancel_on_stop:
            if task_obj and not task_obj.done():
                if isinstance(task_obj, asyncio.Future):
                    loop_to_use.call_soon_threadsafe(task_obj.cancel)
                else: 
                    loop_to_use.call_soon_threadsafe(task_obj.cancel)
        logging.info("비동기 태스크 취소 요청 완료.")
    else: logging.warning("비동기 루프가 실행 중이지 않아 태스크를 취소할 수 없습니다.")
    if gui: gui.update_status("정지 중...")

def reset_global_state():
    """전역 상태 변수들 초기화 (Bybit 버전, 변경 없음)"""
    global current_step_index, open_orders_state, order_type_mapping, signal_type, entry_quantity_list, cumulative_entry_quantity_list, per_step_hedge_quantity_list, cumulative_hedge_quantity_list, exit_ratio_list, last_entry_price, last_two_candles, last_trigger_order_price, nsz_lower_bound, nsz_active, pending_entry_info, exit_orders_status, partially_filled_log
    global step_profit_handler_info, nsz_history
    global clear_line_exit_handler
    logging.info("전역 상태 변수 초기화 중...")
    current_step_index = -1; open_orders_state = {}; order_type_mapping = {}; signal_type = None; last_entry_price = 0.0
    last_trigger_order_price = 0.0; nsz_lower_bound = 0.0; nsz_active = False; last_two_candles = []
    nsz_history.clear() 
    entry_quantity_list = []; cumulative_entry_quantity_list = []; per_step_hedge_quantity_list = []; cumulative_hedge_quantity_list = []; exit_ratio_list = []
    clear_line_exit_handler = {'active': False, 'clear_line': Decimal('0'), 'price_was_below': False, 'price_was_above': False, 'signal_type': None}
    pending_entry_info = {'active': False, 'order_ids': [], 'step': -1, 'signal_type': None, 'attempt_key_prefix': None, 'start_time': 0, 'division_status': {'current_sub_order_index_placed': -1, 'num_total_divisions_for_step': 0, 'base_entry_price_for_step': 0.0, 'original_total_quantity_for_step': 0.0, 'placed_total_quantity_so_far': 0.0, 'attempt_key_prefix_internal': None, 'filled_sub_order_count': 0, 'triggers': [], 'next_sub_order_to_trigger_index': 0}}
    step_profit_handler_info = {'active': False, 'scenario': None, 'step_index_at_trigger': -1, 'profit_target_price': Decimal('0'), 'partial_market_exit_qty': Decimal('0'), 'initial_pos_qty_for_step': Decimal('0'), 'main_pos_side': None, 'tsm_order_id_for_remaining': None, 'tsm_order_qty': Decimal('0'), 'tsm_activation_price': Decimal('0'), 'awaiting_tsm_profitable_fill': False, 'display_exit_target': None}
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
        if gui: 
            gui.update_status("오류 발생")
            gui.show_error_popup("치명적 오류", f"비동기 루프 실행 중 예상치 못한 오류가 발생했습니다.\n\n오류: {e}\n\n프로그램을 종료해야 할 수 있습니다.")
    finally:
        logging.info("비동기 루프 run_until_complete 종료됨.")
        try:
            if asyncio_loop and not asyncio_loop.is_closed():
                for task in asyncio.all_tasks(loop=asyncio_loop): task.cancel()
                asyncio_loop.close()
                logging.info("비동기 이벤트 루프 닫힘.")
        except Exception as e: logging.error(f"비동기 루프 정리 중 오류: {e}")
        asyncio_loop = None; _loop_thread_id = None 
        if gui: gui.set_button_to_start_mode(); gui.update_status("정지됨")

def load_initial_config():
    """config.py의 초기값을 app_config 딕셔너리로 로드"""
    # (Bybit 버전에서는 이 함수가 덜 중요함. load_config_from_ini가 주 역할)
    global app_config
    logging.info("config.py에서 초기 설정 값을 로드합니다. (주로 load_config_from_ini 사용)")
    # 이 함수는 이제 거의 사용되지 않지만, 호환성을 위해 남겨둘 수 있습니다.
    # for key in dir(config):
    #     if key.isupper():
    #         app_config[key] = getattr(config, key)

async def trigger_recalculation():
    """GUI 요청에 따른 재계산 비동기 실행"""
    global gui, client, symbol_info, calculated_min_order_qty, current_balance
    logging.info("GUI 요청으로 모든 데이터 재계산을 시작합니다.")
    if gui: gui.update_status("수동 재계산 중...")
    # (logic.py의 recalculate_all_data가 Bybit용으로 수정되어야 함)
    success = await recalculate_all_data(client, gui, symbol_info, calculated_min_order_qty, current_balance)
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
    """GUI로부터 설정 변경 요청을 받아 메모리(app_config)와 파일(settings.ini)에 저장합니다."""
    global app_config, gui
    logging.info(f"GUI로부터 설정 변경 요청 수신: {new_configs}")
    try:
        parser = configparser.ConfigParser(interpolation=None)
        parser.optionxform = str 
        parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig')
        config_updated = False
        actual_changes = {} 
        for section, params in gui.settings_structure.items():
            for unique_key, original_key, _type in params:
                if unique_key in new_configs:
                    new_value = new_configs[unique_key]
                    current_value = app_config.get(unique_key)
                    if current_value != new_value:
                        if parser.has_section(section):
                            parser.set(section, original_key, str(new_value))
                            logging.info(f"'{SETTINGS_FILE_PATH}' 파일 업데이트: [{section}] {original_key} = {new_value}")
                            config_updated = True
                            actual_changes[unique_key] = new_value
        if config_updated:
            with open(SETTINGS_FILE_PATH, 'w', encoding='utf-8') as configfile:
                parser.write(configfile)
            logging.info("변경된 설정을 settings.ini 파일에 성공적으로 저장했습니다.")
        else:
            logging.info("설정 변경 요청을 수신했으나, 실제 값 변경은 없습니다.")
    except Exception as e:
        logging.error(f"settings.ini 파일 저장 중 오류 발생: {e}")
    app_config.update(new_configs)
    if 'TARGET_LEVERAGE' in actual_changes and gui:
        gui.update_leverage(f"{actual_changes['TARGET_LEVERAGE']}x (수동변경)")
    if 'POSITION_BIAS' in actual_changes and gui:
        gui.set_position_bias(actual_changes['POSITION_BIAS'])

def load_config_from_ini(gui_instance: GuiManager):
    """
    GUI 인스턴스의 settings_structure를 기준으로 settings.ini 파일을 읽어
    고유 키를 가진 app_config 딕셔너리를 생성합니다.
    """
    global app_config
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str
    try:
        if not parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig'):
            raise FileNotFoundError(f"{SETTINGS_FILE_PATH} 파일을 찾을 수 없습니다.")
        loaded_config = {}
        for section, params in gui_instance.settings_structure.items():
            for unique_key, original_key, _type in params:
                try:
                    value_str = parser.get(section, original_key)
                    if _type == bool: value = parser.getboolean(section, original_key)
                    elif _type == int: value = parser.getint(section, original_key)
                    elif _type == float: value = parser.getfloat(section, original_key)
                    else: value = value_str.strip('"\'')
                    loaded_config[unique_key] = value
                except (configparser.NoSectionError, configparser.NoOptionError):
                    logging.warning(f"'{SETTINGS_FILE_PATH}'의 [{section}] 섹션에서 '{original_key}'를 찾을 수 없음. 기본값('') 설정.")
                    loaded_config[unique_key] = "" # 값을 못 찾으면 빈 값으로 설정
        app_config.clear()
        app_config.update(loaded_config)
        logging.info("GUI 구조를 기반으로 모든 설정을 성공적으로 로드했습니다.")
    except Exception as e:
        logging.critical(f"{SETTINGS_FILE_PATH} 파일 로드 또는 파싱 실패! 오류: {e}", exc_info=True)
        messagebox.showerror("치명적 오류", f"settings.ini 파일을 읽거나 해석할 수 없습니다.\n오류: {e}\n프로그램을 종료합니다.")
        sys.exit(1)

def save_config_to_ini():
    """현재 app_config의 내용을 settings.ini 파일에 저장합니다."""
    # (이 함수는 Bybit 버전에서 변경될 필요 없음)
    global app_config
    parser = configparser.ConfigParser(interpolation=None)
    parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig')
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
            global current_step_index
            if current_step_index == -1:
                logging.info(f"정지 버튼 클릭됨 - 봇이 유휴 상태(step {current_step_index})이므로 즉시 정지를 실행합니다.")
                stop_bot_logic() 
            else:
                logging.info(f"정지 버튼 클릭됨 - 봇이 활성 상태(step {current_step_index})이므로 예약 정지를 실행합니다.")
                request_graceful_stop() 
        elif action == "cancel_stop":
            cancel_graceful_stop()
            
    try:
        logging.info("자동매매 프로그램 시작 (Asyncio + GUI)...")
        root = tk.Tk()
        
        # 1. GUI 인스턴스 먼저 생성 (Bybit 기본값으로 수정)
        temp_parser = configparser.ConfigParser()
        temp_parser.read(SETTINGS_FILE_PATH, encoding='utf-8-sig')
        # (Bybit는 USDT-M/COIN-M 설정이 다름. GUI가 이를 인지하고 로드해야 함)
        # 우선 USDT-M 기준으로 임시 로드
        temp_symbol = temp_parser.get('USDT-M 설정', 'symbol', fallback='BTCUSDT')
        temp_steps = temp_parser.getint('전략 파라미터', 'steps', fallback=12)
        temp_asset = temp_parser.get('USDT-M 설정', 'balance_asset', fallback='USDT')
        
        gui = GuiManager(root, temp_symbol, temp_steps, temp_asset, SETTINGS_FILE_PATH)
        
        # 2. GUI 구조를 기반으로 모든 설정 로드
        load_config_from_ini(gui)
        
        # 3. (Bybit용) 로드된 설정을 기반으로 현재 모드에 맞는 설정 적용
        apply_trading_mode_settings()

        # 4. 최종 설정값으로 logic.py와 GUI를 업데이트
        # (logic.py의 set_config_source가 Bybit용 config 프록시를 사용하도록 수정되었다고 가정)
        set_config_source(config) 
        gui.load_current_configs(app_config)
        
        # 5. 나머지 콜백 함수들 설정
        gui.set_config_update_callback(handle_config_update)
        gui.set_recalculate_callback(handle_recalculation_request)
        gui.set_toggle_command(handle_toggle_action)
        gui.set_on_closing(stop_bot_logic)

        gui.update_status("대기 중")
        logging.info("Tkinter 메인 루프 시작..."); root.mainloop(); logging.info("Tkinter 메인 루프 종료됨.")
    except Exception as e:
        logging.critical(f"메인 스레드에서 처리되지 않은 예외 발생: {e}", exc_info=True)
    finally:
        logging.info("자동매매 프로그램을 완전히 종료합니다.")
        stop_bot_logic()
        if bot_logic_thread and bot_logic_thread.is_alive():
             bot_logic_thread.join(timeout=5)