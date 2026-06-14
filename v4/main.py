# 필요한 라이브러리 설치: pip install python-binance asyncio aiohttp websockets aiodns
# 윈도우 환경에서 aiodns 호환성을 위해 pywin32가 필요할 수 있음: pip install pywin32
from binance import AsyncClient # AsyncClient 사용 (BinanceSocketManager는 직접 사용 안 함)
from binance.enums import *
import os
import time # time.time() 등 일부 동기 함수는 사용 가능
import logging
import sys
import asyncio # 비동기 라이브러리
import json
from decimal import Decimal, ROUND_DOWN # 정확한 숫자 계산 및 내림 처리
import platform # 운영체제 확인용
import threading # GUI와 비동기 로직 분리용
import tkinter as tk # GUI 라이브러리
from tkinter import ttk
import websockets # 직접 웹소켓 연결용
import math # ceil 함수 사용

# --- 로깅 설정 ---
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(message)s')) # 스레드 이름 포함
console_handler.setLevel(logging.INFO)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
# 기존 핸들러 제거 (중복 로깅 방지)
if logger.hasHandlers():
    logger.handlers.clear()
logger.addHandler(console_handler)

# --- 윈도우 asyncio 이벤트 루프 설정 ---
if platform.system() == "Windows":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        logging.info("윈도우 환경 감지: asyncio 이벤트 루프 정책을 WindowsSelectorEventLoopPolicy로 설정했습니다.")
    except AttributeError:
        logging.warning("WindowsSelectorEventLoopPolicy를 찾을 수 없습니다. 기본 루프를 사용합니다.")


# --- 설정 ---
API_KEY = "DOS5hez0wz1CaKkkbhGrQW6h1YOdRfAW6ftB44m8EtfgAuvmQaAVteuEtnPr7klO"  # 실제 API 키로 교체
API_SECRET = "9xgKcSaok0qh8Cd2dEGrM1FfdGhgj8ws7LBsqtNp960OJBDeCsvDlte8C9qsHcPQ"  # 실제 시크릿 키로 교체
SYMBOL = 'XRPUSDT' # 거래할 심볼
KLINE_INTERVAL = KLINE_INTERVAL_1MINUTE # 캔들스틱 간격
TARGET_LEVERAGE = 20 # 목표 레버리지
RECONNECT_DELAY = 30 # 웹소켓 재연결 시도 간격 (초)
BALANCE_ASSET = 'USDT' # 잔고 조회할 자산

# --- 상태 및 정보 변수 ---
# 심볼 정보 관련
quantity_precision = None # 수량 소수점 자릿수 (LOT_SIZE)
step_size = None          # 수량 단계 (LOT_SIZE)
min_lot_size_qty = None   # 최소 주문 수량 (LOT_SIZE)
min_notional_value = None # 최소 주문 금액 (MIN_NOTIONAL)
calculated_min_order_qty = None # 계산된 최종 최소 주문 가능 수량
symbol_info_loaded = False # 심볼 정보 로드 여부

# 기타 상태
current_balance = 0.0 # 현재 잔고 (숫자형)
leverage_set = False     # 레버리지 설정 여부

# GUI 업데이트용 문자열 변수 (초기값 설정)
leverage_str = "N/A"
symbol_info_str = "N/A"
calculated_min_qty_str = "N/A" # 계산된 최소 수량 표시용
current_balance_str = "N/A"

# --- 웹소켓 및 클라이언트 관리 ---
client: AsyncClient = None # AsyncClient 객체 (초기화 필요)
listen_key = None
keep_alive_task = None # Listen Key 갱신 태스크
main_waiting_future: asyncio.Future = None # 메인 루프 대기용 Future
websocket_connection_task = None # 웹소켓 처리 태스크(gather) 저장용
main_app_running = True # 전체 애플리케이션 실행 플래그 (threading.Event로 변경 고려)
asyncio_loop = None # 비동기 루프 객체 저장용

# --- GUI 관리 클래스 ---
class GuiManager:
    def __init__(self, root):
        self.root = root
        self.root.title("자동매매 봇 상태")
        self.root.geometry("450x450") # 창 크기 확장
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 스타일 설정
        style = ttk.Style()
        style.configure("TLabel", padding=3, font=('Helvetica', 9))
        style.configure("Value.TLabel", font=('Helvetica', 9), foreground="blue")
        style.configure("Status.TLabel", font=('Helvetica', 10, 'bold'))
        style.configure("WsStatus.TLabel", font=('Helvetica', 9, 'italic'))
        style.configure("WsData.TLabel", font=('Helvetica', 8), foreground="gray")

        # 메인 프레임
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)

        # --- 기본 정보 섹션 ---
        info_frame = ttk.LabelFrame(main_frame, text="기본 정보", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        info_frame.columnconfigure(1, weight=1) # 값 표시 컬럼 확장

        row_idx = 0
        ttk.Label(info_frame, text="심볼:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.symbol_var = tk.StringVar(value=SYMBOL)
        ttk.Label(info_frame, textvariable=self.symbol_var, style="Value.TLabel").grid(column=1, row=row_idx-1, sticky=tk.W)

        ttk.Label(info_frame, text="레버리지:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.leverage_var = tk.StringVar(value="로딩 중...")
        ttk.Label(info_frame, textvariable=self.leverage_var, style="Value.TLabel").grid(column=1, row=row_idx-1, sticky=tk.W)

        ttk.Label(info_frame, text="심볼 정보:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.symbol_info_var = tk.StringVar(value="로딩 중...")
        ttk.Label(info_frame, textvariable=self.symbol_info_var, style="Value.TLabel", wraplength=300).grid(column=1, row=row_idx-1, sticky=tk.W)

        # 계산된 최소 주문 수량 표시 추가
        ttk.Label(info_frame, text="계산된 최소수량:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.min_qty_var = tk.StringVar(value="N/A")
        ttk.Label(info_frame, textvariable=self.min_qty_var, style="Value.TLabel").grid(column=1, row=row_idx-1, sticky=tk.W)

        ttk.Label(info_frame, text=f"{BALANCE_ASSET} 잔고:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.balance_var = tk.StringVar(value="로딩 중...")
        ttk.Label(info_frame, textvariable=self.balance_var, style="Value.TLabel").grid(column=1, row=row_idx-1, sticky=tk.W)

        ttk.Label(info_frame, text="봇 상태:").grid(column=0, row=row_idx, sticky=tk.W); row_idx += 1
        self.status_var = tk.StringVar(value="초기화 중...")
        ttk.Label(info_frame, textvariable=self.status_var, style="Status.TLabel").grid(column=1, row=row_idx-1, sticky=tk.W)

        # --- 웹소켓 상태 섹션 ---
        ws_frame = ttk.LabelFrame(main_frame, text="웹소켓 상태", padding="10")
        ws_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        ws_frame.columnconfigure(1, weight=1) # 상태/데이터 컬럼 확장

        # Kline
        ttk.Label(ws_frame, text="Kline 상태:").grid(column=0, row=0, sticky=tk.W)
        self.kline_status_var = tk.StringVar(value="대기 중...")
        ttk.Label(ws_frame, textvariable=self.kline_status_var, style="WsStatus.TLabel").grid(column=1, row=0, sticky=tk.W)
        self.kline_data_var = tk.StringVar(value="-")
        ttk.Label(ws_frame, textvariable=self.kline_data_var, style="WsData.TLabel", wraplength=300).grid(column=0, row=1, columnspan=2, sticky=tk.W)

        # Trade/Ticker
        ttk.Label(ws_frame, text="Trade 상태:").grid(column=0, row=2, sticky=tk.W, pady=(5,0))
        self.trade_status_var = tk.StringVar(value="대기 중...")
        ttk.Label(ws_frame, textvariable=self.trade_status_var, style="WsStatus.TLabel").grid(column=1, row=2, sticky=tk.W, pady=(5,0))
        self.trade_data_var = tk.StringVar(value="-")
        ttk.Label(ws_frame, textvariable=self.trade_data_var, style="WsData.TLabel", wraplength=300).grid(column=0, row=3, columnspan=2, sticky=tk.W)

        # User Data
        ttk.Label(ws_frame, text="User 상태:").grid(column=0, row=4, sticky=tk.W, pady=(5,0))
        self.user_status_var = tk.StringVar(value="대기 중...")
        ttk.Label(ws_frame, textvariable=self.user_status_var, style="WsStatus.TLabel").grid(column=1, row=4, sticky=tk.W, pady=(5,0))
        self.user_data_var = tk.StringVar(value="-")
        ttk.Label(ws_frame, textvariable=self.user_data_var, style="WsData.TLabel", wraplength=300).grid(column=0, row=5, columnspan=2, sticky=tk.W)


    def _safe_update(self, var, value):
        """스레드 안전하게 StringVar 업데이트"""
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.after(0, lambda: var.set(value))
        else:
            logging.debug("GUI 업데이트 시도 실패: root 창이 없거나 파괴됨.")

    # 기본 정보 업데이트 메서드
    def update_leverage(self, leverage_text): self._safe_update(self.leverage_var, leverage_text)
    def update_symbol_info(self, info_text): self._safe_update(self.symbol_info_var, info_text)
    def update_min_qty(self, qty_text): self._safe_update(self.min_qty_var, qty_text) # 최소 수량 업데이트 메서드 추가
    def update_balance(self, balance_text): self._safe_update(self.balance_var, balance_text)
    def update_status(self, status_text): self._safe_update(self.status_var, status_text)

    # 웹소켓 상태/데이터 업데이트 메서드
    def update_kline_status(self, status): self._safe_update(self.kline_status_var, status)
    def update_kline_data(self, data): self._safe_update(self.kline_data_var, data)
    def update_trade_status(self, status): self._safe_update(self.trade_status_var, status)
    def update_trade_data(self, data): self._safe_update(self.trade_data_var, data)
    def update_user_status(self, status): self._safe_update(self.user_status_var, status)
    def update_user_data(self, data): self._safe_update(self.user_data_var, data)

    def on_closing(self):
        """창 닫기 버튼 클릭 시"""
        logging.info("GUI 창 닫기 요청됨. 애플리케이션 종료 시작...")
        stop_bot_logic() # 비동기 로직 종료 신호 보내기
        if hasattr(self, 'root') and self.root:
             self.root.after(100, self.root.destroy)

gui: GuiManager = None # 전역 GUI 객체

# --- 유틸리티 함수 ---
def count_decimal_places(number_str):
    """문자열 형태의 숫자의 소수점 이하 자릿수를 반환"""
    try:
        d = Decimal(str(number_str))
        if d.as_tuple().exponent < 0:
            return abs(d.as_tuple().exponent)
        else:
            return 0
    except Exception:
        return 0 # 오류 발생 시 기본값

# --- 비동기 함수 정의 ---
async def check_futures_connection(client: AsyncClient):
    try:
        await client.futures_ping()
        await client.futures_time()
        logging.info("선물 서버 연결 성공.")
        return True
    except Exception as e:
        logging.error(f"선물 서버 연결 실패: {e}")
        return False

async def get_futures_balance(client: AsyncClient, asset='USDT'):
    global current_balance, current_balance_str, gui
    try:
        balances = await client.futures_account_balance()
        balance_found = False
        for balance in balances:
            if balance['asset'] == asset:
                balance_val = balance['balance']
                logging.info(f"{asset} 선물 잔고: {balance_val}")
                current_balance = float(balance_val)
                current_balance_str = str(balance_val)
                balance_found = True
                break
        if not balance_found:
            logging.warning(f"{asset} 자산을 찾을 수 없습니다.")
            current_balance = 0.0
            current_balance_str = "찾을 수 없음"
        if gui:
            gui.update_balance(current_balance_str) # GUI 업데이트
        return current_balance
    except Exception as e:
        logging.error(f"선물 잔고 확인 실패: {e}")
        current_balance = 0.0
        current_balance_str = "조회 실패"
        if gui:
            gui.update_balance(current_balance_str)
        return 0.0

async def check_position_mode(client: AsyncClient):
    try:
        position_mode = await client.futures_get_position_mode()
        is_hedge_mode = position_mode.get('dualSidePosition', False)
        mode_str = '헤지 모드' if is_hedge_mode else '단방향 모드'
        logging.info(f"현재 포지션 모드: {mode_str}")
        if not is_hedge_mode:
            logging.warning("계정이 헤지 모드로 설정되어 있지 않습니다.")
        return is_hedge_mode
    except Exception as e:
        logging.error(f"포지션 모드 확인 실패: {e}")
        return False

async def check_all_open_positions(client: AsyncClient):
    try:
        all_positions = await client.futures_position_information()
        open_positions = [p for p in all_positions if float(p.get('positionAmt', 0)) != 0]
        if open_positions:
            logging.warning(f"경고: {len(open_positions)}개 오픈 포지션 발견.")
            for p in open_positions:
                 logging.warning(f"  - {p['symbol']}, {p['positionSide']}, {p['positionAmt']}")
            return True
        else:
            logging.info("현재 오픈된 선물 포지션 없음.")
            return False
    except Exception as e:
        logging.error(f"전체 포지션 정보 확인 실패: {e}")
        return True

async def check_and_cancel_pending_orders(client: AsyncClient):
    try:
        open_orders = await client.futures_get_open_orders()
        if not open_orders:
            logging.info("현재 미체결 주문 없음.")
            return True
        logging.warning(f"경고: {len(open_orders)}개 미체결 주문 발견. 취소 시도...")
        cancelled_count = 0
        failed_count = 0
        cancel_tasks = [client.futures_cancel_order(symbol=order['symbol'], orderId=order['orderId']) for order in open_orders]
        results = await asyncio.gather(*cancel_tasks, return_exceptions=True)
        for i, result in enumerate(results):
            order = open_orders[i]
            if isinstance(result, Exception):
                logging.error(f"  - 주문 취소 실패: {order.get('symbol', 'N/A')}, ID={order.get('orderId', 'N/A')}, 오류: {result}")
                failed_count += 1
            else:
                logging.info(f"  - 주문 취소 성공: {order['symbol']}, ID={order['orderId']}")
                cancelled_count += 1
        if failed_count > 0:
            logging.error(f"{failed_count}개 주문 취소 실패.")
            return False
        else:
            logging.info(f"{cancelled_count}개 주문 성공적으로 취소.")
            return True
    except Exception as e:
        logging.error(f"미체결 주문 처리 중 오류: {e}")
        return False

async def set_leverage(client: AsyncClient, symbol, leverage):
    global leverage_set, leverage_str, gui
    try:
        logging.info(f"{symbol} 레버리지 {leverage}배 설정 시도...")
        response = await client.futures_change_leverage(symbol=symbol, leverage=leverage)
        leverage_val = response.get('leverage', 'N/A')
        logging.info(f"{symbol} 레버리지 설정(확인) 완료: {leverage_val}x")
        leverage_set = True
        leverage_str = f"{leverage_val}x"
        if gui:
            gui.update_leverage(leverage_str) # GUI 업데이트
        return True
    except Exception as e:
        logging.error(f"{symbol} 레버리지 설정 실패: {e}")
        leverage_set = False
        leverage_str = "설정 실패"
        if gui:
            gui.update_leverage(leverage_str)
        return False

async def get_symbol_info(client: AsyncClient, symbol):
    """exchangeInfo 조회하여 필요한 필터 정보 저장"""
    global quantity_precision, min_lot_size_qty, step_size, min_notional_value, symbol_info_loaded, symbol_info_str, gui
    try:
        logging.info(f"{symbol} 거래 규칙 정보 조회 시도...")
        exchange_info = await client.futures_exchange_info()
        info_found = False
        symbol_info_loaded = False # 초기화

        for item in exchange_info['symbols']:
            if item['symbol'] == symbol:
                logging.info(f"{symbol} 정보 찾음.")
                info_found = True
                quantity_precision = item.get('quantityPrecision')
                min_lot_size_qty = None
                step_size = None
                min_notional_value = None

                for f in item['filters']:
                    if f.get('filterType') == 'LOT_SIZE':
                        min_lot_size_qty = f.get('minQty')
                        step_size = f.get('stepSize')
                    elif f.get('filterType') == 'MIN_NOTIONAL':
                        min_notional_value = f.get('notional')

                if quantity_precision is not None and min_lot_size_qty is not None and step_size is not None and min_notional_value is not None:
                    info_text = f"정밀도:{quantity_precision}, 최소수량(Lot):{min_lot_size_qty}, Step:{step_size}, 최소금액:{min_notional_value}"
                    logging.info(f" - {info_text}")
                    symbol_info_loaded = True
                    symbol_info_str = info_text
                else:
                    err_msg = f"{symbol} 필수 필터 정보 누락."
                    logging.error(err_msg)
                    symbol_info_str = err_msg
                break # 심볼 찾았으므로 루프 종료

        if not info_found:
             err_msg = f"{symbol} 정보 없음."
             logging.error(err_msg)
             symbol_info_str = err_msg

        if gui:
            gui.update_symbol_info(symbol_info_str) # GUI 업데이트
        return symbol_info_loaded
    except Exception as e:
        logging.error(f"{symbol} 정보 조회 실패: {e}")
        symbol_info_loaded = False
        symbol_info_str = "조회 실패"
        if gui:
            gui.update_symbol_info(symbol_info_str)
        return False

async def calculate_effective_min_qty(client: AsyncClient, symbol: str):
    """조회된 필터 정보와 현재 가격으로 실제 최소 주문 가능 수량 계산"""
    global calculated_min_order_qty, calculated_min_qty_str, gui
    calculated_min_order_qty = None # 초기화
    calculated_min_qty_str = "N/A"

    if not symbol_info_loaded or min_lot_size_qty is None or step_size is None or min_notional_value is None:
        logging.error("최소 주문 수량 계산 불가: 심볼 정보 부족.")
        if gui: gui.update_min_qty(calculated_min_qty_str)
        return None

    try:
        # Mark Price 사용 (Notional 계산에 더 적합)
        logging.debug(f"{symbol} Mark Price 조회 시도...")
        mark_price_data = await client.futures_mark_price(symbol=symbol)
        mark_price = float(mark_price_data.get('markPrice'))
        logging.info(f"{symbol} 현재 Mark Price: {mark_price}")

        if mark_price <= 0:
             logging.error("Mark Price가 0 또는 음수입니다. 최소 수량 계산 불가.")
             if gui: gui.update_min_qty("가격오류")
             return None

        # MIN_NOTIONAL 기준 필요 수량 계산
        notional_qty = float(min_notional_value) / mark_price
        logging.debug(f"Min Notional 기준 필요 수량: {notional_qty}")

        # stepSize에 맞춰 수량 올림 (ceil)
        step_size_f = float(step_size)
        adjusted_notional_qty = math.ceil(notional_qty / step_size_f) * step_size_f
        logging.debug(f"Step Size 적용 후 Notional 수량: {adjusted_notional_qty}")

        # LOT_SIZE의 minQty와 비교하여 더 큰 값 선택
        min_lot_f = float(min_lot_size_qty)
        effective_min_qty = max(min_lot_f, adjusted_notional_qty)
        logging.debug(f"최종 유효 최소 수량 (Max(Lot, Notional)): {effective_min_qty}")

        # 최종 수량을 stepSize의 소수점 자릿수에 맞춰 반올림 (또는 내림/올림)
        decimals = count_decimal_places(step_size)
        final_min_qty = round(effective_min_qty, decimals)

        # 최종 수량이 minQty보다 작아지는 경우 방지 (round로 인해 발생 가능)
        if final_min_qty < min_lot_f:
             final_min_qty = min_lot_f # 최소한 minQty는 만족하도록

        calculated_min_order_qty = final_min_qty
        calculated_min_qty_str = str(final_min_qty)
        logging.info(f"계산된 최종 최소 주문 수량: {calculated_min_order_qty}")

        if gui:
            gui.update_min_qty(calculated_min_qty_str) # GUI 업데이트
        return calculated_min_order_qty

    except Exception as e:
        logging.error(f"최소 주문 수량 계산 중 오류: {e}", exc_info=True)
        if gui: gui.update_min_qty("계산오류")
        return None


async def place_futures_order(client: AsyncClient, symbol, side, position_side, quantity, order_type=FUTURE_ORDER_TYPE_MARKET):
    global calculated_min_order_qty # 계산된 최소 수량 사용
    if not symbol_info_loaded:
        logging.error("주문 불가: 심볼 정보 없음")
        return None
    if calculated_min_order_qty is None:
         logging.error("주문 불가: 계산된 최소 주문 수량 없음")
         return None

    try:
        order_qty = float(quantity)
        # 주문 수량이 계산된 최소 수량보다 작은지 확인
        if order_qty < calculated_min_order_qty:
             logging.warning(f"주문 수량({order_qty})이 계산된 최소 주문 수량({calculated_min_order_qty})보다 작습니다. 주문하지 않습니다.")
             return None

        # 주문 수량을 stepSize에 맞게 포맷팅 (Decimal 사용 권장)
        decimals = count_decimal_places(step_size)
        formatted_qty = f"{order_qty:.{decimals}f}" # 간단 round 방식 (정확도 문제 가능성 있음)
        logging.info(f"주문 수량 포맷팅: {order_qty} -> {formatted_qty}")


        logging.info(f"주문 시도: {symbol}, {side}, {position_side}, Qty:{formatted_qty}, Type:{order_type}")
        order = await client.futures_create_order(symbol=symbol, side=side, positionSide=position_side, type=order_type, quantity=formatted_qty)
        logging.info(f"주문 성공: {order}")
        return order
    except Exception as e:
        logging.error(f"주문 실패: {e}")
        return None

# --- 웹소켓 콜백 함수 정의 ---
def cancel_main_future(reason="WebSocket error detected"):
    global main_waiting_future
    if main_waiting_future and not main_waiting_future.done():
        logging.warning(f"메인 Future 취소 요청: {reason}")
        if asyncio_loop and asyncio_loop.is_running():
             asyncio.run_coroutine_threadsafe(main_waiting_future.cancel(), asyncio_loop)
        else:
             logging.warning("취소 요청 시 비동기 루프가 실행 중이지 않음.")


async def process_kline(msg):
    """캔들스틱(Kline) 데이터 처리 콜백"""
    global gui
    try:
        if msg.get('e') == 'error':
            logging.error(f"Kline 웹소켓 오류: {msg}")
            cancel_main_future("Kline error")
            if gui:
                gui.update_kline_status("오류")
                gui.update_kline_data(str(msg))
            return

        kline = msg.get('k', {})
        is_closed = kline.get('x', False)
        kline_time = time.strftime('%H:%M:%S', time.localtime(kline.get('T', 0)/1000))

        # === GUI 업데이트 로직 수정 ===
        # 캔들 완성 여부와 관계없이 현재 정보 표시 (선택적)
        open_price = kline.get('o')
        high_price = kline.get('h')
        low_price = kline.get('l')
        close_price = kline.get('c')
        volume = kline.get('v')
        data_str = f"{kline_time} O:{open_price} H:{high_price} L:{low_price} C:{close_price} V:{volume}"
        if is_closed:
            data_str += " (완료)"
            logging.debug(f"Kline 수신 ({msg.get('s','N/A')} {kline.get('i','N/A')}): {data_str}")
        else:
            # 완성되지 않은 캔들도 로그 및 GUI 업데이트 (필요 없다면 이 부분 제거)
            logging.log(logging.DEBUG - 1, f"Kline 업데이트 ({msg.get('s','N/A')} {kline.get('i','N/A')}): {data_str}") # DEBUG보다 낮은 레벨

        if gui:
            gui.update_kline_data(data_str) # GUI에 OHLCV 정보 업데이트
        # === 수정 끝 ===

        # --- Kline 데이터 기반 거래 로직 (주로 is_closed 조건 하에서) ---
        if is_closed:
             # 여기에 거래 로직 추가
             pass

    except Exception as e:
        logging.error(f"process_kline 처리 중 오류: {e}", exc_info=True)
        cancel_main_future("Kline processing error")
        if gui:
            gui.update_kline_status("처리 오류")

async def process_ticker(msg):
    """현재가(Ticker/Trade) 데이터 처리 콜백"""
    global gui
    try:
        if msg.get('e') == 'error':
            logging.error(f"Ticker(Trade) 웹소켓 오류: {msg}")
            cancel_main_future("Ticker error")
            if gui:
                gui.update_trade_status("오류")
                gui.update_trade_data(str(msg))
            return

        last_price = msg.get('p')
        trade_time = time.strftime('%H:%M:%S', time.localtime(msg.get('T', 0)/1000))
        if last_price:
            data_str = f"{trade_time} 가격: {last_price}"
            logging.debug(f"Trade 수신 ({msg.get('s','N/A')}): {data_str}")
            if gui:
                gui.update_trade_data(data_str) # 실시간 가격 GUI 업데이트
        # --- Ticker/Trade 데이터 기반 거래 로직 ---

    except Exception as e:
        logging.error(f"process_ticker(Trade) 처리 중 오류: {e}", exc_info=True)
        cancel_main_future("Ticker processing error")
        if gui:
            gui.update_trade_status("처리 오류")

async def process_user_data(msg):
    """사용자 데이터 스트림 처리 콜백"""
    global current_balance, current_balance_str, gui
    try:
        event_type = msg.get('e')
        event_time = time.strftime('%H:%M:%S', time.localtime(msg.get('E', 0)/1000))
        data_summary = f"{event_time} 이벤트: {event_type}" # 기본 요약

        if event_type == 'ACCOUNT_UPDATE':
            logging.debug("사용자 데이터 수신 (ACCOUNT_UPDATE)")
            account_info = msg.get('a', {})
            balances = account_info.get('B', [])
            balance_updated = False
            for bal in balances:
                 if bal['a'] == BALANCE_ASSET:
                      new_balance = bal.get('wb', 'N/A')
                      logging.info(f"  - 잔고 업데이트 ({BALANCE_ASSET}): {new_balance}")
                      try:
                          current_balance = float(new_balance)
                          current_balance_str = str(new_balance)
                          if gui:
                              gui.update_balance(current_balance_str) # 실시간 잔고 GUI 업데이트
                          data_summary += f", 잔고({BALANCE_ASSET}): {new_balance}" # 요약에 추가
                          balance_updated = True
                      except ValueError:
                          logging.warning(f"잔고 업데이트 값 변환 실패: {new_balance}")
                      except Exception as e:
                          logging.error(f"잔고 업데이트 처리 중 오류: {e}")

            # positions = account_info.get('P', []) # 포지션 정보 로깅은 DEBUG 레벨로 충분할 수 있음
            # for pos in positions: logging.debug(f"  - 포지션 업데이트: {pos['s']}, 수량={pos['pa']}, 진입가={pos['ep']}")
            if not balance_updated:
                data_summary += " (잔고 변경 없음)"

        elif event_type == 'ORDER_TRADE_UPDATE':
            order_info = msg.get('o', {})
            order_id = order_info.get('i') # 주문 ID
            symbol = order_info.get('s') # 심볼
            status = order_info.get('X') # 주문 상태
            filled_qty = order_info.get('l', '0') # 마지막 체결 수량 (기본값 '0')
            last_filled_price = order_info.get('L', '0') # 마지막 체결 가격 (기본값 '0')

            log_msg = f"사용자 데이터 수신 (ORDER_TRADE_UPDATE): {symbol}, ID:{order_id}, 상태:{status}, 체결량:{filled_qty}, 체결가:{last_filled_price}"
            logging.info(log_msg)
            # === GUI 표시 내용 수정 ===
            data_summary = f"{event_time} 주문({symbol} ID:{order_id}): 상태={status}"
            # 체결 정보가 있을 때만 추가 (FILLED, PARTIALLY_FILLED)
            if status in ["FILLED", "PARTIALLY_FILLED"] and filled_qty and float(filled_qty) > 0:
                 data_summary += f", 체결량:{filled_qty}, 체결가:{last_filled_price}"
            # === 수정 끝 ===

        elif event_type == 'listenKeyExpired':
             logging.warning("Listen Key 만료됨. 재연결 필요.")
             cancel_main_future("Listen Key Expired")
             if gui:
                 gui.update_user_status("Listen Key 만료")
             data_summary = "Listen Key 만료됨" # 상태만 표시

        if gui:
            # 사용자 데이터는 이벤트 발생 시 업데이트
            gui.update_user_data(data_summary) # 요약된 정보 GUI 업데이트

    except Exception as e:
        logging.error(f"process_user_data 처리 중 오류: {e}", exc_info=True)
        cancel_main_future("User data processing error")
        if gui:
            gui.update_user_status("처리 오류")


# --- Listen Key 갱신 태스크 ---
async def keep_alive_listen_key(client: AsyncClient):
    global listen_key
    logging.info("Listen Key 갱신 태스크 시작됨.")
    while main_app_running:
        try:
            if listen_key:
                await client.futures_stream_keepalive(listenKey=listen_key)
                logging.info("Listen Key 갱신 성공")
            else:
                logging.warning("Listen Key 없음, 갱신 건너<0xEB><0x9B><0x84>.")
            await asyncio.sleep(30 * 60) # 30분 대기
        except asyncio.CancelledError:
            logging.info("Listen Key 갱신 태스크 취소됨.")
            break
        except Exception as e:
            logging.error(f"Listen Key 갱신 오류: {e}")
            await asyncio.sleep(60) # 1분 후 재시도
    logging.info("Listen Key 갱신 태스크 종료됨.")

# --- 웹소켓 시작 및 관리 함수 ---
async def start_websockets(client: AsyncClient):
    """웹소켓 연결 설정 및 시작 (직접 연결 방식)"""
    global listen_key, keep_alive_task, websocket_connection_task, gui
    await stop_websockets() # 이전 연결 정리
    listen_key = None; keep_alive_task = None; websocket_connection_task = None # 초기화

    try:
        if gui: gui.update_status("Listen Key 발급 중...")
        logging.info("Listen Key 발급 시도 (직접 연결용)..."); listen_key = await client.futures_stream_get_listen_key()
        if not listen_key:
            logging.error("Listen Key 발급 실패!")
            if gui: gui.update_status("Listen Key 발급 실패")
            return False
        logging.info(f"Listen Key 발급 성공: {listen_key[:10]}...")
        keep_alive_task = asyncio.create_task(keep_alive_listen_key(client))

        kline_stream_url = f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@kline_{KLINE_INTERVAL}"
        trade_stream_url = f"wss://fstream.binance.com/ws/{SYMBOL.lower()}@trade"
        user_stream_url = f"wss://fstream.binance.com/ws/{listen_key}"

        if gui: gui.update_status("웹소켓 연결 중...")
        logging.info("웹소켓 처리 태스크 생성 시도...")
        ks_task = asyncio.create_task(handle_stream(kline_stream_url, process_kline, "Kline"), name="KlineStream") # 스트림 타입 전달
        ts_task = asyncio.create_task(handle_stream(trade_stream_url, process_ticker, "Trade"), name="TradeStream")
        us_task = asyncio.create_task(handle_stream(user_stream_url, process_user_data, "User"), name="UserStream")

        logging.info("모든 웹소켓 스트림 처리 태스크 시작 요청 완료.")
        websocket_connection_task = asyncio.gather(ks_task, ts_task, us_task) # 태스크 그룹화 및 결과 저장

        return True # 시작 요청 성공

    except asyncio.CancelledError:
        logging.info("웹소켓 시작 중 취소됨.")
        await stop_websockets()
        return False
    except Exception as e:
        logging.error(f"웹소켓 시작 중 예외 발생: {e}", exc_info=True)
        await stop_websockets()
        return False


# 웹소켓 직접 연결 및 메시지 처리 함수
async def handle_stream(url, callback_func, stream_type): # stream_type 인자 추가
    """주어진 URL에 직접 연결하고 메시지를 처리하는 코루틴"""
    import websockets
    global main_waiting_future, gui
    reconnect_attempts = 0
    max_reconnect_attempts = 5

    logging.info(f"{stream_type} 스트림 핸들러 시작: {url}")
    update_status_func = getattr(gui, f'update_{stream_type.lower()}_status', None) if gui else None

    if update_status_func:
        update_status_func("연결 중...")

    while main_app_running and reconnect_attempts < max_reconnect_attempts:
        try:
            logging.debug(f"웹소켓 연결 시도: {url}")
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as websocket:
                logging.info(f"웹소켓 연결 성공: {url}")
                reconnect_attempts = 0
                if update_status_func:
                    update_status_func("연결됨") # 연결 성공 상태 업데이트

                async for message in websocket:
                    logging.debug(f"메시지 수신 ({url}): {message[:100]}...")
                    try:
                        data = json.loads(message)
                        if not main_app_running: break
                        await callback_func(data)
                    except json.JSONDecodeError:
                        logging.warning(f"JSON 디코딩 오류: {message}")
                    except Exception as e:
                        logging.error(f"메시지 처리 중 오류 ({callback_func.__name__}): {e}", exc_info=True)

        except websockets.exceptions.ConnectionClosedError as e:
            logging.warning(f"웹소켓 연결 종료됨 ({url}): {e}. 재연결 시도 ({reconnect_attempts + 1}/{max_reconnect_attempts})...")
            if update_status_func:
                update_status_func(f"연결 끊김 - 재연결({reconnect_attempts+1})")
        except asyncio.CancelledError:
            logging.info(f"스트림 핸들러 취소됨: {url}")
            if update_status_func:
                update_status_func("취소됨")
            break
        except Exception as e:
            logging.error(f"웹소켓 연결/처리 중 오류 ({url}): {e}", exc_info=True)
            if update_status_func:
                update_status_func("연결 오류")

        reconnect_attempts += 1
        if main_app_running and reconnect_attempts < max_reconnect_attempts:
            wait_time = min(RECONNECT_DELAY, 2**(reconnect_attempts))
            logging.info(f"{url} - {wait_time}초 후 재연결 시도...")
            try:
                 await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                 logging.info(f"대기 중 스트림 핸들러 취소됨: {url}")
                 break

    logging.warning(f"스트림 핸들러 종료: {url} (최대 재연결 시도 도달 또는 앱 종료)")
    if update_status_func:
        update_status_func("종료됨 / 오류")
    cancel_main_future(f"Stream handler stopped: {url}")


async def stop_websockets():
    """웹소켓 연결 및 관련 태스크 정리 (비동기, 직접 연결 방식)"""
    global listen_key, keep_alive_task, websocket_connection_task
    logging.info("웹소켓 정리 시작...")
    # Keepalive 태스크 취소
    if keep_alive_task and not keep_alive_task.done():
        keep_alive_task.cancel()
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            logging.info("Keepalive 태스크 정상 취소됨.")
        except Exception as e: # Handle potential other exceptions during await
            logging.error(f"Keepalive 태스크 대기 중 오류: {e}")
        keep_alive_task = None # Reset after handling

    # 웹소켓 처리 태스크(gather) 취소
    if websocket_connection_task and not websocket_connection_task.done():
        logging.info("웹소켓 처리 태스크(gather) 취소 시도...")
        websocket_connection_task.cancel()
        try:
            await websocket_connection_task # gather 내부 태스크들이 취소될 때까지 대기
        except asyncio.CancelledError:
            logging.info("웹소켓 처리 태스크(gather) 정상 취소됨.")
        except Exception as e:
            logging.error(f"웹소켓 처리 태스크(gather) 대기 중 오류: {e}")
        websocket_connection_task = None # Reset after handling
    else:
        logging.info("웹소켓 처리 태스크(gather)가 없거나 이미 완료됨.")

    listen_key = None
    logging.info("웹소켓 정리 완료.")


# --- 봇 메인 로직 함수 (비동기) ---
async def run_bot_logic():
    global client, main_app_running, main_waiting_future, gui, calculated_min_order_qty # calculated_min_order_qty 추가
    logging.info("run_bot_logic 시작")
    if gui: gui.update_status("클라이언트 생성 중...")
    try:
        client = await AsyncClient.create(API_KEY, API_SECRET)
        logging.info("AsyncClient 생성 완료.")
    except Exception as e:
        logging.critical(f"AsyncClient 생성 실패: {e}", exc_info=True)
        if gui:
            gui.update_status("클라이언트 생성 실패")
        main_app_running = False
        return

    if gui: gui.update_status("서버 연결 확인 중...")
    if not await check_futures_connection(client):
        main_app_running = False
        if gui:
            gui.update_status("서버 연결 실패")
        if client:
            await client.close_connection()
        return

    if gui: gui.update_status("포지션 확인 중...")
    if await check_all_open_positions(client):
        main_app_running = False
        if gui:
            gui.update_status("기존 포지션 감지됨 - 종료")
        if client:
            await client.close_connection()
        return

    if gui: gui.update_status("미체결 주문 확인/취소 중...")
    if not await check_and_cancel_pending_orders(client):
        main_app_running = False
        if gui:
            gui.update_status("미체결 주문 처리 실패 - 종료")
        if client:
            await client.close_connection()
        return

    if gui: gui.update_status("잔고/모드 확인 중...")
    await get_futures_balance(client, BALANCE_ASSET)
    await check_position_mode(client); logging.info("초기 설정 확인 완료.")

    while main_app_running:
        main_waiting_future = asyncio.Future()
        connection_started = False
        try:
            if gui: gui.update_status("웹소켓 연결 시도 중...")
            connection_started = await start_websockets(client)

            if connection_started:
                logging.info("웹소켓 연결 성공.")
                if gui: gui.update_status("연결 후 초기화 중...")
                # --- 연결 성공 후 작업 ---
                await set_leverage(client, SYMBOL, TARGET_LEVERAGE)
                if not await get_symbol_info(client, SYMBOL):
                    # 심볼 정보 로드 실패 시 재연결 시도
                    logging.error(f"{SYMBOL} 정보 조회 실패. 재연결 시도...")
                    if gui: gui.update_status("심볼 정보 조회 실패")
                    # Future를 취소하여 재연결 로직으로 이동
                    cancel_main_future("Symbol info fetch failed")
                    await main_waiting_future # 취소될 때까지 대기
                    continue # 다음 재연결 루프 반복으로

                # 심볼 정보 로드 성공 후 최소 주문 수량 계산
                if gui: gui.update_status("최소 주문 수량 계산 중...")
                await calculate_effective_min_qty(client, SYMBOL)
                if calculated_min_order_qty is None:
                    logging.error(f"{SYMBOL} 최소 주문 수량 계산 실패. 재연결 시도...")
                    if gui: gui.update_status("최소 수량 계산 실패")
                    cancel_main_future("Min qty calculation failed")
                    await main_waiting_future
                    continue

                await get_futures_balance(client, BALANCE_ASSET) # 잔고 재확인
                logging.info("연결 후 초기화 완료. 메시지 대기 중...")
                # 상태 업데이트는 handle_stream 내부에서 처리
                # if gui: gui.update_status("실행 중") # handle_stream에서 처리

                await main_waiting_future # 웹소켓 연결 유지 및 오류/종료 대기

            else: # start_websockets 실패 시
                logging.error("웹소켓 시작 실패.")
                if gui:
                    gui.update_status("웹소켓 시작 실패")

            # Future가 완료/취소되거나 start_websockets 실패 시 여기까지 도달
            logging.warning("현재 웹소켓 세션 종료됨. 재연결 준비...")
            if gui:
                gui.update_status("연결 종료됨 - 재연결 준비")

        except asyncio.CancelledError:
             logging.info("메인 봇 로직 태스크 취소됨 (CancelledError).")
             main_app_running = False # 앱 종료
        except Exception as e:
             logging.error(f"봇 로직 메인 루프 오류: {e}", exc_info=True)
             if gui:
                 gui.update_status("오류 발생 - 재연결 시도")
        finally:
             logging.info("재연결 전 웹소켓 정리 시작...")
             if gui:
                 gui.update_status("웹소켓 정리 중...")
             await stop_websockets()
             logging.info("재연결 전 웹소켓 정리 완료.")
             if main_app_running: # 앱 종료 신호가 아니면 재연결 시도
                  logging.info(f"{RECONNECT_DELAY}초 후 재연결 시도...")
                  if gui:
                      gui.update_status(f"{RECONNECT_DELAY}초 후 재연결 시도")
                  try:
                       await asyncio.sleep(RECONNECT_DELAY)
                  except asyncio.CancelledError:
                       logging.info("재연결 대기 중 취소됨.")
                       main_app_running = False # 앱 종료

    logging.info("봇 로직 종료 중...");
    if gui:
        gui.update_status("종료 중...")
    await stop_websockets() # 최종 정리
    if client:
        try:
            await client.close_connection()
            logging.info("AsyncClient 연결 종료됨.")
        except Exception as e:
            logging.error(f"AsyncClient 종료 중 오류: {e}")
    logging.info("봇 로직 태스크 완전히 종료됨.")

def stop_bot_logic():
    """봇 로직 및 웹소켓 종료"""
    global main_app_running, websocket_connection_task, keep_alive_task, main_waiting_future, asyncio_loop
    if not main_app_running: return
    logging.info("봇 로직 종료 신호 수신.")
    main_app_running = False

    loop_to_use = asyncio_loop
    if loop_to_use and loop_to_use.is_running():
        logging.info("비동기 태스크 취소 시도...")
        if main_waiting_future and not main_waiting_future.done():
            loop_to_use.call_soon_threadsafe(main_waiting_future.cancel, "Application shutting down")
        if keep_alive_task and not keep_alive_task.done():
            loop_to_use.call_soon_threadsafe(keep_alive_task.cancel)
        if websocket_connection_task and not websocket_connection_task.done():
            logging.info("웹소켓 처리 태스크(gather) 취소 시도 (stop_bot_logic)...")
            loop_to_use.call_soon_threadsafe(websocket_connection_task.cancel)
        logging.info("비동기 태스크 취소 요청 완료.")
    else:
         logging.warning("비동기 루프가 실행 중이지 않아 태스크를 취소할 수 없습니다.")


# --- 메인 실행 부분 ---
def start_asyncio_loop():
    """비동기 이벤트 루프를 시작하고 메인 로직을 실행하는 함수 (별도 스레드에서 실행)"""
    global asyncio_loop
    logging.info("비동기 루프 시작...")
    try:
        asyncio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(asyncio_loop)
        asyncio_loop.run_until_complete(run_bot_logic())
    except Exception as e:
        logging.error(f"비동기 루프 실행 중 오류 발생: {e}", exc_info=True)
    finally:
        logging.info("비동기 루프 run_until_complete 종료됨.")
        try:
            if asyncio_loop and not asyncio_loop.is_closed():
                 pending = asyncio.all_tasks(loop=asyncio_loop)
                 if pending:
                      logging.info(f"남아있는 {len(pending)}개 비동기 태스크 취소 시도...")
                      for task in pending:
                          # 이미 완료된 태스크는 cancel() 호출 시 에러 발생 안 함
                          task.cancel()
                 # 루프 종료 전에 취소된 태스크가 처리될 시간을 약간 줌 (선택적)
                 # asyncio_loop.run_until_complete(asyncio.sleep(0.1))
                 asyncio_loop.close()
                 logging.info("비동기 이벤트 루프 닫힘.")
        except Exception as e:
            logging.error(f"비동기 루프 정리 중 오류: {e}")
        asyncio_loop = None


if __name__ == "__main__":
    logging.info("__main__ 블록 시작")
    gui = None
    bot_logic_thread = None

    try:
        try:
            import websockets
            logging.info(f"websockets 라이브러리 로드됨 (버전: {websockets.__version__})")
        except ImportError:
            print("오류: 'websockets' 라이브러리가 설치되지 않았습니다. pip install websockets 를 실행해주세요.")
            sys.exit(1)

        logging.info("자동매매 프로그램 시작 (Asyncio + GUI)...")
        main_app_running = True

        root = tk.Tk()
        gui = GuiManager(root)

        logging.info("봇 로직 스레드 시작 시도...")
        bot_logic_thread = threading.Thread(target=start_asyncio_loop, name="AsyncioBotThread", daemon=True)
        bot_logic_thread.start()
        logging.info("봇 로직 스레드 시작됨.")

        logging.info("Tkinter 메인 루프 시작...")
        root.mainloop() # 메인 스레드는 여기서 대기
        logging.info("Tkinter 메인 루프 종료됨.") # 창이 닫히면 여기로 옴

    except KeyboardInterrupt:
        logging.info("KeyboardInterrupt 감지됨. 프로그램 종료 중...")
    except Exception as e:
        logging.critical(f"메인 스레드에서 처리되지 않은 예외 발생: {e}", exc_info=True)
    finally:
        logging.info("자동매매 프로그램을 완전히 종료합니다.")
        stop_bot_logic() # 비동기 로직 종료 신호
        if bot_logic_thread and bot_logic_thread.is_alive():
             logging.info("봇 로직 스레드 종료 대기 (최대 5초)...")
             bot_logic_thread.join(timeout=5)
             if bot_logic_thread.is_alive():
                 logging.warning("봇 로직 스레드가 시간 내에 종료되지 않았습니다.")
             else:
                 logging.info("봇 로직 스레드 정상 종료됨.")
        logging.info("프로그램 실행 완료.")

