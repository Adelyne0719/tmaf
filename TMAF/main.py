import os
import re
import io
import sys
import time
import math
import json
import hmac
import hashlib
import logging
import asyncio
import requests
import websockets
import pandas as pd
import pandas_ta as ta
import subprocess
import binance
import decorator
import config
from urllib.parse import urlencode
from datetime import datetime, timedelta
from binance.exceptions import BinanceAPIException
from binance.client import Client

if sys.stdout is not None and hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr is not None and hasattr(sys.stderr, 'buffer'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 기존 루트 로거의 모든 핸들러 제거
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

if getattr(sys, 'frozen', False):
    # 패키징된 경우, exe 파일의 디렉토리를 기준으로 함.
    base_dir = os.path.dirname(sys.executable)
else:
    # 개발 중인 경우, 현재 스크립트 파일이 있는 디렉토리를 기준으로 함.
    base_dir = os.path.dirname(os.path.abspath(__file__))

# 파일명 결정: live 모드이면 두 개의 파일명을 설정, 그렇지 않으면 날짜 파일 하나만 사용
if os.environ.get("STRATEGY_MODE") == "live":
    live_log_filename = os.path.join(base_dir, "trading_strategy.log")
    date_log_filename = os.path.join(base_dir, datetime.now().strftime("%Y%m%d_%H%M%S") + ".log")
else:
    live_log_filename = None
    date_log_filename = None

# 기존 파일이 있으면 제거
if live_log_filename and os.path.exists(live_log_filename):
    os.remove(live_log_filename)
if date_log_filename and os.path.exists(date_log_filename):
    os.remove(date_log_filename)

# FlushFileHandler 클래스 정의
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

# NOTI 레벨 및 필터 설정
NOTI = 25
logging.addLevelName(NOTI, "NOTI")

class NotiFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == NOTI

def noti(self, message, *args, **kwargs):
    if self.isEnabledFor(NOTI):
        self._log(NOTI, message, args, **kwargs)
logging.Logger.noti = noti

# 포매터 정의
file_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')

# 핸들러 리스트 생성
handlers = []

# live 모드이면 trading_strategy.log 파일 핸들러 추가
if live_log_filename:
    live_file_handler = FlushFileHandler(live_log_filename, mode="w", encoding="utf8")
    live_file_handler.setLevel(NOTI)
    live_file_handler.setFormatter(file_formatter)
    handlers.append(live_file_handler)

# 날짜 기반 파일 핸들러는 live 모드일 때만 추가
if date_log_filename:
    date_file_handler = FlushFileHandler(date_log_filename, mode="w", encoding="utf8")
    date_file_handler.setLevel(NOTI)
    date_file_handler.setFormatter(file_formatter)
    handlers.append(date_file_handler)

# 콘솔 핸들러: 패키징 후에도 stdout을 사용하도록 명시적으로 sys.stdout 지정
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(NOTI)
console_formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
console_handler.setFormatter(console_formatter)
handlers.append(console_handler)

# 루트 로거에 핸들러 등록 (basicConfig 대신 직접 설정)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
for handler in handlers:
    logger.addHandler(handler)

class TradingStrategy:
    def __init__(self):
        # 거래 상태 변수 (초기 상태)
        self.position = 0         # 0: 없음, 1: 롱, -1: 숏
        self.long_entry_price = None
        self.long_add_count = 0
        self.long_next_add = None
        self.long_highest = None

        self.short_entry_price = None
        self.short_add_count = 0
        self.short_next_add = None
        self.short_lowest = None

        self.highest_price = None   # 실시간 롱 최고가
        self.lowest_price = None    # 실시간 숏 최저가

        self.real_time_price = None
        self.entry = None
        self.initial_balance = None
        self.last_candle_timestamp = None

        self.last_position_update = None
        self.last_update_time = 0
        self.min_notional_value = None
        
        self.step_size = None
        self.min_qty = None
        self.price_precision = None

        self.interval_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "4h": 14400,
            "1d": 86400
        }

        self.client = Client(config.API_KEY, config.API_SECRET)

    # ------------------ 실시간 가격 및 캔들 모니터링 ------------------ #
    async def async_read_real_time_price(self):
        """
        Binance WebSocket을 통해 실시간 가격 정보를 수신.
        """
        symbol = config.SYMBOL.lower()
        uri = f"wss://fstream.binance.com/ws/{symbol}@ticker"
        while True:
            try:
                async with websockets.connect(uri) as websocket:
                    logging.info("Binance WebSocket에 연결되었습니다.")
                    while True:
                        message = await websocket.recv()
                        data = json.loads(message)
                        if "c" in data:
                            try:
                                price = float(data["c"])
                                self.real_time_price = price
                                logging.debug("실시간 가격 업데이트: %s", self.real_time_price)
                            except Exception as e:
                                logging.error("가격 파싱 오류: %s", e)
            except Exception as e:
                logging.error("WebSocket 연결 오류: %s", e)
                await asyncio.sleep(1)

    async def notify_current_price(self):
        """
        매 시간 30분마다 현재 가격을 로그에 출력.
        """
        while True:
            now = datetime.now()
            if now.minute < 30:
                next_notify = now.replace(minute=30, second=0, microsecond=0)
            else:
                next_notify = (now + timedelta(hours=1)).replace(minute=30, second=0, microsecond=0)
            sleep_time = (next_notify - now).total_seconds()
            await asyncio.sleep(sleep_time)
            if self.real_time_price is not None:
                logging.log(NOTI, f"현재 가격: {self.real_time_price}")
            else:
                logging.log(NOTI, "실시간 가격 정보가 아직 업데이트되지 않았습니다.")

    # ------------------ API 호출 관련 함수 ------------------ #
    @decorator.call_binance_api
    def get_min_order_qty(self):
        try:
            logging.info('최소 주문수량 조회')
            exinfo = self.client.futures_exchange_info()
            exinfo_filter = list(filter(lambda a: a['symbol'] == config.SYMBOL, exinfo['symbols']))
            limit_exinfo = exinfo_filter[0]['filters'][1]
            min_qty = float(limit_exinfo['minQty'])
            logging.info("최소 주문수량: %s", min_qty)
            return min_qty
        except Exception as e:
            logging.error("최소 주문수량 조회 에러: %s", e)
            return None

    @decorator.call_binance_api
    def set_leverage(self):
        try:
            response = self.client.futures_change_leverage(symbol=config.SYMBOL, leverage=config.LEVERAGE)
            logging.log(NOTI, "레버리지 설정: %s, %s", response['symbol'], response['leverage'])
        except BinanceAPIException as e:
            logging.error("레버리지 설정 에러: %s", e)

    @decorator.call_binance_api
    def get_futures_balance_with_retry(self, max_retries=3, delay=2):
        for attempt in range(max_retries):
            try:
                balance_data = self.client.futures_account_balance()
                for asset in balance_data:
                    if asset['asset'] == 'USDT':
                        balance = float(asset['balance'])
                        logging.log(NOTI, "현재 futures 잔고: %s USDT", balance)
                        return balance
                logging.error("USDT 잔고를 찾지 못했습니다.")
                return None
            except Exception as e:
                logging.error("잔고 조회 에러 (시도 %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    time.sleep(delay)
        logging.error("모든 잔고 조회 시도가 실패했습니다.")
        return None

    @decorator.call_binance_api
    def get_recent_klines(self, symbol, interval, lookback=1000):
        try:
            klines = self.client.futures_klines(symbol=symbol, interval=interval, limit=lookback)
        except BinanceAPIException as e:
            logging.error("캔들 데이터 가져오기 에러: %s", e)
            return None

        data = []
        for k in klines:
            data.append({
                'timestamp': int(k[0]),
                'open': float(k[1]),
                'high': float(k[2]),
                'low': float(k[3]),
                'close': float(k[4]),
                'volume': float(k[5])
            })
        df = pd.DataFrame(data)
        return df

    def check_ini(self):
        """config.ini 파일 존재 여부 확인"""
        logging.info("설정 파일 확인...")
        required_keys = ['API_KEY', 'API_SECRET', 'SYMBOL', 'INTERVAL']
        for key in required_keys:
            if not hasattr(config, key) or getattr(config, key) is None or getattr(config, key) == '':
                logging.error(f"필수 설정 값 {key}가 없거나 비어 있습니다.")
                return False
        return True
    
    def add_ema_indicators(self, df):
        logging.info("EMA 지표를 계산합니다...")
        df['ema5'] = ta.ema(df['close'], length=config.EMA_PERIODS["ema5"])
        df['ema10'] = ta.ema(df['close'], length=config.EMA_PERIODS["ema10"])
        df['ema15'] = ta.ema(df['close'], length=config.EMA_PERIODS["ema15"])
        sd = self.count_decimal_places(df['close'].iloc[-2])
        logging.info("EMA 계산 완료: ema5: %s, ema10: %s, ema15: %s",
                     round(df['ema5'].iloc[-2], sd),
                     round(df['ema10'].iloc[-2], sd),
                     round(df['ema15'].iloc[-2], sd))
        return df

    def count_decimal_places(self, n):
        s = str(n)
        if '.' in s:
            return len(s.split('.')[1])
        return 0

    @decorator.call_binance_api
    def place_order(self, side, quantity):
        delay = 3
        attempt = 0
        while True:  # 주문이 성공하거나 치명적인 오류가 발생할 때까지 무한 루프
            attempt += 1
            try:
                logging.log(NOTI, "주문 실행 중: %s 주문, 수량: %s (시도 %d)", side, quantity, attempt)
                order = self.client.futures_create_order(
                    symbol=config.SYMBOL,
                    side=side,
                    type='MARKET',
                    quantity=quantity
                )
                logging.log(NOTI, "주문 결과: %s", order)
                return order  # 성공 시, 루프를 종료하고 주문 결과 반환
            except BinanceAPIException as e:
                if e.code == -1008:
                    # 서버 과부하 오류 시, 잠시 대기 후 재시도
                    logging.error("주문 실행 에러 (-1008: 서버 과부하). %d초 후 재시도...", delay)
                    time.sleep(delay)
                    continue  # while 루프의 다음 순회로 넘어가 재시도
                else:
                    # 다른 모든 바이낸스 API 오류 시, 로그를 남기고 시도 중단
                    logging.error("주문 실행 에러: %s", e)
                    return None  # 함수를 종료하고 None 반환
            except Exception as e:
                # 다른 모든 종류의 예외 발생 시, 로그를 남기고 시도 중단
                logging.error("주문 실행 중 알 수 없는 에러가 발생했습니다: %s", e)
                return None  # 함수를 종료하고 None 반환

    @decorator.call_binance_api
    def check_order_result(self, order_id, symbol):
        attempts = 0
        while attempts < 5:
            try:
                order_result = self.client.futures_get_order(symbol=symbol, orderId=order_id)
                
                if order_result is not None:
                    if not isinstance(order_result, dict):
                        logging.log(NOTI, "주문 결과의 형식이 올바르지 않습니다: %s", order_result)
                        return None

                    if 'orderId' not in order_result:
                        logging.log(NOTI, "주문 결과에 'orderId' 키가 없습니다: %s", order_result)
                        return None

                    logging.log(NOTI, "주문 결과 확인: %s", order_result)
                    return order_result

                else:
                    attempts += 1
                    logging.log(NOTI, "주문 결과가 None입니다. %d번째 재시도중...", attempts)
                    time.sleep(1)

            except BinanceAPIException as e:
                if e.code == -2013:
                    attempts += 1
                    logging.log(NOTI, "주문 결과 확인 에러(-2013): 주문이 존재하지 않음, %d번째 재시도중...", attempts)
                    time.sleep(1)
                    continue
                else:
                    logging.log(NOTI, "주문 결과 확인 에러: %s", e)
                    return None

            except Exception as e:
                logging.log(NOTI, "주문 결과 확인 중 알 수 없는 에러가 발생했습니다: %s", e)
                return None

        logging.log(NOTI, "5번 시도 후에도 주문 결과가 None입니다. API 응답을 확인하세요.")
        return None

    @decorator.call_binance_api
    def get_min_qty_from_error(self, symbol: str):
        
        symbol = symbol.strip().upper()
        base_url = "https://fapi.binance.com"
        order_endpoint = "/fapi/v1/order"
        timestamp = int(time.time() * 1000)

        exchange_info_url = f"{base_url}/fapi/v1/exchangeInfo"
        try:
            resp_info = requests.get(exchange_info_url)
            resp_info.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error("ExchangeInfo API 요청 에러: %s", e)
            return None

        data = resp_info.json()
        symbol_info = None
        lot_size_filter = None
        price_filter = None # price_filter 변수 추가
            
        for s in data.get("symbols", []):
            if s.get("symbol", "").strip().upper() == symbol:
                symbol_info = s
                for f in s.get("filters", []):
                    if f.get("filterType") == "LOT_SIZE":
                        lot_size_filter = f
                # ▼▼▼ 가격 필터 찾는 로직 추가 ▼▼▼
                    if f.get("filterType") == "PRICE_FILTER":
                        price_filter = f
                break
        if symbol_info is None or lot_size_filter is None:
            logging.error("심볼 혹은 LOT_SIZE/PRICE_FILTER 필터 정보를 찾지 못했습니다: %s", symbol)
            return None

        tick_size = price_filter.get('tickSize')
        if tick_size:
            self.price_precision = self.count_decimal_places(tick_size)
            logging.log(NOTI, f"가격 소수점 자리수 확인: {self.price_precision} (tickSize: {tick_size})")


        test_quantity = float(lot_size_filter.get("minQty"))
        min_qty = test_quantity
        step_size = float(lot_size_filter.get("stepSize"))

        params = {
            "symbol": symbol,
            "side": "BUY",
            "type": "MARKET",
            "quantity": test_quantity,
            "timestamp": timestamp
        }
        query_string = urlencode(params)
        signature = hmac.new(config.API_SECRET.encode('utf-8'),
                             query_string.encode('utf-8'),
                             hashlib.sha256).hexdigest()
        params["signature"] = signature

        headers = {
            "X-MBX-APIKEY": config.API_KEY
        }
        url = base_url + order_endpoint
        try:
            response = requests.post(url, params=params, headers=headers)
            response.raise_for_status()
            logging.log(NOTI, "예상치 못한 주문 성공:", response.json())
            return None
        except requests.exceptions.RequestException as e:
            try:
                error_response = response.json()
            except Exception:
                logging.error("응답을 JSON으로 파싱할 수 없습니다.")
                return None

            if error_response.get("code") == -4164:
                msg = error_response.get("msg", "")
                m = re.search(r"no smaller than ([\d\.]+)", msg)
                if m:
                    self.min_notional_value = float(m.group(1))
                    logging.log(NOTI, f"오류 메시지에서 추출한 최소 notional: {self.min_notional_value} USDT")
                else:
                    logging.error("오류 메시지에서 최소 notional 값을 추출하지 못했습니다.")
                    return None
            else:
                logging.error("오류 코드가 -4164가 아닙니다: %s", error_response)
                return None

        ticker_url = f"{base_url}/fapi/v1/ticker/price?symbol={symbol}"
        try:
            resp_price = requests.get(ticker_url)
            resp_price.raise_for_status()
        except requests.exceptions.RequestException as e:
            logging.error("Ticker API 요청 에러: %s", e)
            return None
        price_data = resp_price.json()
        current_price = float(price_data.get("price"))
        logging.log(NOTI, f"현재 가격: {current_price} USDT")

        required_qty = self.min_notional_value / current_price
        effective_qty = math.ceil(required_qty / step_size) * step_size
        effective_min_qty = max(min_qty, effective_qty)

        decimals = self.count_decimal_places(step_size)
        order_qty = round(effective_min_qty, decimals)

        logging.log(NOTI, f"계산된 최소 주문 수량: {order_qty} (LOT_SIZE minQty: {min_qty}, stepSize: {step_size})")
        return order_qty, step_size

    def check_order_notional(self, order_qty, current_price, min_notional=20):
        notional_value = order_qty * current_price
        if notional_value < min_notional:
            logging.error("Order's notional value is too low: %.4f USDT (minimum is %.4f USDT)", notional_value, min_notional)
            return False
        return True

    @decorator.call_binance_api
    def get_order_quantity_for_symbol_start(self, symbol, current_price):
        res = self.get_min_qty_from_error(symbol)
        if res is None:
            logging.error("심볼 %s의 최소 주문 정보가 없습니다.", symbol)
            return None
        self.min_qty, self.step_size = res

        decimals = self.count_decimal_places(self.step_size)
        available_margin = self.initial_balance * 0.9
        computed_qty = ((available_margin * config.LEVERAGE) / current_price) / 100
        order_qty = round(computed_qty, decimals)
        if order_qty < self.min_qty:
            order_qty = self.min_qty
        order_qty = round(math.floor(order_qty / self.step_size) * self.step_size, decimals)
        notional_value = order_qty * current_price
        if notional_value < self.min_notional_value:
            logging.error("계산된 주문금액이 최소 주문금액 미달입니다.: %.4f USDT / %.4f USDT", notional_value, self.min_notional_value)
            time.sleep(1)
            logging.log(NOTI, "계산된 주문금액이 최소 주문금액 미달입니다.: %.4f USDT / %.4f USDT", notional_value, self.min_notional_value)
            return None

        logging.log(NOTI, "심볼 %s 주문 수량 계산: %s (available_margin: %s, current_price: %s, min_qty: %s, step_size: %s)",
                    symbol, order_qty, available_margin, current_price, self.min_qty, self.step_size)
        return order_qty
    
    @decorator.call_binance_api
    def get_order_quantity_for_symbol(self, symbol, current_price):
        if self.min_qty is None and self.step_size is None:
            res = self.get_min_qty_from_error(symbol)
            if res is None:
                logging.error("심볼 %s의 최소 주문 정보가 없습니다.", symbol)
                return None
            self.min_qty, self.step_size = res

        decimals = self.count_decimal_places(self.step_size)
        available_margin = self.initial_balance * 0.95
        computed_qty = ((available_margin * config.LEVERAGE) / current_price) / 100
        order_qty = round(computed_qty, decimals)
        if order_qty < self.min_qty:
            order_qty = self.min_qty
        order_qty = round(math.floor(order_qty / self.step_size) * self.step_size, decimals)
        notional_value = order_qty * current_price
        if notional_value < self.min_notional_value:
            logging.error("계산된 주문금액이 최소 주문금액 미달입니다.: %.4f USDT / %.4f USDT", notional_value, self.min_notional_value)
            time.sleep(1)
            logging.log(NOTI, "계산된 주문금액이 최소 주문금액 미달입니다.: %.4f USDT / %.4f USDT", notional_value, self.min_notional_value)
            return None

        logging.log(NOTI, "심볼 %s 주문 수량 계산: %s (available_margin: %s, current_price: %s, min_qty: %s, step_size: %s)",
                    symbol, order_qty, available_margin, current_price, self.min_qty, self.step_size)
        return order_qty

    @decorator.call_binance_api
    def get_active_positions(self, symbol=None):
        try:
            client_local = Client(config.API_KEY, config.API_SECRET)
            positions = client_local.futures_position_information()
            active_positions = [pos for pos in positions if float(pos.get('positionAmt', 0)) != 0]
            if symbol:
                active_positions = [pos for pos in active_positions if pos.get('symbol') == symbol]
            return active_positions
        except Exception as e:
            logging.error("포지션 정보를 가져오는 중 오류 발생: %s", e)
            return None

    @decorator.call_binance_api
    async def clear_position_main(self):
        try:
            positions = self.client.futures_position_information()
            target = None
            for pos in positions:
                if pos.get('symbol') == config.SYMBOL and float(pos.get('positionAmt', 0)) != 0:
                    target = pos
                    break
            if target is None:
                logging.log(NOTI, "정리할 포지션이 없습니다.")
                return
            amt = float(target.get('positionAmt', 0))
            if amt > 0:
                side = "SELL"
                quantity = amt
            else:
                side = "BUY"
                quantity = abs(amt)
            
            order = self.client.futures_create_order(
                symbol=config.SYMBOL,
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=True
            )
            logging.log(NOTI, f"Clear Position 주문 실행: {side} {quantity}")
            
            self.position = 0
            self.long_entry_price = None
            self.long_add_count = 0
            self.long_next_add = None
            self.long_highest = None
            self.highest_price = None
            self.short_entry_price = None
            self.short_add_count = 0
            self.short_next_add = None
            self.short_lowest = None
            self.lowest_price = None
            self.min_qty = None
            self.step_size = None
            
            await self.update_position_via_api()
        except Exception as e:
            logging.log(NOTI, f"Clear Position 주문 오류: {e}")

    async def update_position_via_api(self, retries=3, delay=0.7):
        for i in range(retries):
            pos_list = self.get_active_positions(config.SYMBOL)
            
            if pos_list or self.position == 0:
                break
            
            logging.log(NOTI, f"API 포지션 정보 업데이트 대기... ({i+1}/{retries})")
            await asyncio.sleep(delay)

        if not pos_list:
            self.position = 0
            self.entry = "-"
            quantity = "-"
            unrealized_profit = "-"
            self.long_entry_price = None
            self.long_add_count = 0
            self.long_next_add = None
            self.long_highest = None
            self.highest_price = None
            self.short_entry_price = None
            self.short_add_count = 0
            self.short_next_add = None
            self.short_lowest = None
            self.lowest_price = None
            pos_type = "없음"
            stage = "-"
            next_price = "-"
        else:
            pos = pos_list[0]
            self.entry = pos.get('entryPrice', '-')
            quantity = pos.get('positionAmt', '-')
            unrealized_profit = pos.get('unRealizedProfit', '-')
            
            if self.position == 1:
                pos_type = "롱"
                stage = str(self.long_add_count)
                if self.long_next_add is not None:
                    next_price = f"{self.long_next_add:.{self.price_precision}f}" if self.price_precision is not None else str(self.long_next_add)
                else:
                    next_price = "-"
            elif self.position == -1:
                pos_type = "숏"
                stage = str(self.short_add_count)
                if self.short_next_add is not None:
                    next_price = f"{self.short_next_add:.{self.price_precision}f}" if self.price_precision is not None else str(self.short_next_add)
                else:
                    next_price = "-"
            else:
                pos_amt = float(quantity)
                if pos_amt > 0:
                    self.position = 1
                    pos_type = "롱"
                    self.long_add_count = 1
                    stage = "1"
                    self.long_entry_price = float(self.entry)
                    self.long_next_add = self.long_entry_price * (1 + config.SCALING_FACTOR)
                    next_price = f"{self.long_next_add:.{self.price_precision}f}" if self.price_precision is not None else str(self.long_next_add)
                elif pos_amt < 0:
                    self.position = -1
                    pos_type = "숏"
                    self.short_add_count = 1
                    stage = "1"
                    self.short_entry_price = float(self.entry)
                    self.short_next_add = self.short_entry_price * (1 - config.SCALING_FACTOR)
                    next_price = f"{self.short_next_add:.{self.price_precision}f}" if self.price_precision is not None else str(self.short_next_add)
                else:
                    pos_type = "없음"
                    stage = "-"
                    next_price = "-"

        current_update = f"{pos_type},{self.entry},{quantity},{unrealized_profit},{stage},{next_price}"
        now = time.time()
        if self.last_position_update == current_update and (now - self.last_update_time) < 1:
            return
        self.last_position_update = current_update
        self.last_update_time = now
        logging.log(NOTI, "POSITION_UPDATE:%s", current_update)
        
    # ------------------ 전략 로직 관련 함수 ------------------ #
    async def process_candle(self, df):
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        latest = df.iloc[-2]
        logging.info("최신 봉 정보: %s", latest.to_dict())

        if len(df) < 48:
            logging.warning("48봉 미만의 데이터입니다. 전략 실행 건너뜁니다.")
            return

        vol_lowest = df['volume'].iloc[-50:-2].min()
        vol_condition = latest['volume'] >= config.VOL_MULTIPLIER * vol_lowest
        logging.info("현재 거래량: %s, 48봉 최저 거래량*3: %s, 조건 충족: %s",
                     round(latest['volume'], self.count_decimal_places(latest['volume'])),
                     round(vol_lowest * 3, self.count_decimal_places(vol_lowest)),
                     vol_condition)

        if len(df) < 3:
            logging.warning("3봉 미만의 데이터입니다. 전략 실행 건너뜁니다.")
            return

        prev1 = df.iloc[-2]
        prev2 = df.iloc[-3]
        bullish_consecutive = (prev1['close'] > prev1['open']) and (prev2['close'] > prev2['open'])
        bearish_consecutive = (prev1['close'] < prev1['open']) and (prev2['close'] < prev2['open'])

        pre_long_condition = (latest['ema5'] > latest['ema10'])
        pre_short_condition = (latest['ema5'] < latest['ema10'])

        long_condition = (latest['ema5'] > latest['ema10'] > latest['ema15'])
        short_condition = (latest['ema5'] < latest['ema10'] < latest['ema15'])
        logging.log(NOTI, "MA5:%s, MA10:%s, MA15:%s", 
                    round(latest['ema5'], self.count_decimal_places(latest['close'])), 
                    round(latest['ema10'], self.count_decimal_places(latest['close'])),
                    round(latest['ema15'], self.count_decimal_places(latest['close']))
                    )
        current_price = latest['close']
        logging.info("정배열:%s, Bullish:%s, 거래량:%s", long_condition, bullish_consecutive, vol_condition)
        logging.info("역배열:%s, Bearish:%s, 거래량:%s", short_condition, bearish_consecutive, vol_condition)
        logging.log(NOTI, "마지막봉 종가: %s", current_price)
        logging.log(NOTI, "롱 조건:%s,%s,%s", long_condition, bullish_consecutive, vol_condition)
        logging.log(NOTI, "숏 조건:%s,%s,%s", short_condition, bearish_consecutive, vol_condition)

        # 롱 포지션 진입 및 관리
        if pre_long_condition:
            if self.position == -1:
                logging.log(NOTI, "역전발생: 현재 숏 포지션이므로 청산 진행")
                await self.clear_position_main()
                await asyncio.sleep(1)
                self.initial_balance = self.get_futures_balance_with_retry()
                logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                logging.log(NOTI, "숏 포지션 청산 완료")
                return

        if long_condition:
            while self.real_time_price is None:
                logging.debug("실시간 가격 대기중")
                await asyncio.sleep(1)
            if self.position <= 0 and vol_condition and bullish_consecutive:
                logging.log(NOTI, "롱 진입 조건 충족")
                logging.log(NOTI,"현재가격:%s", current_price)
                qty = self.get_order_quantity_for_symbol(config.SYMBOL, current_price)
                order = self.place_order("BUY", qty)
                order_id = order['orderId']
                order_result = self.check_order_result(order_id, config.SYMBOL)
                self.position = 1
                self.long_entry_price = float(order_result['avgPrice'])
                self.long_add_count = 1
                self.long_next_add = self.long_entry_price * (1 + config.SCALING_FACTOR)
                # ▼▼▼ 수정된 부분 ▼▼▼
                next_add_price_formatted = f"{self.long_next_add:.{self.price_precision}f}" if self.price_precision is not None else self.long_next_add
                logging.log(NOTI, "롱 포지션 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                            self.long_add_count, self.long_entry_price, next_add_price_formatted)
                # ▲▲▲ 수정된 부분 ▲▲▲
                await asyncio.sleep(1)
                await self.update_position_via_api()
            elif self.position == 1:
                if self.highest_price is not None and self.long_highest is not None:
                    self.long_highest = max(self.long_highest, self.highest_price)
                logging.log(NOTI, "롱 포지션 유지 중, 최고가 업데이트: %s", self.highest_price)
                
                if self.real_time_price is not None and self.long_next_add is not None and self.real_time_price >= self.long_next_add and self.long_add_count < config.MAX_ENTRIES:
                    logging.log(NOTI, "롱 추가 진입 조건 충족")
                    logging.log(NOTI,"현재가격:%s", current_price)
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("BUY", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL)
                    self.long_add_count += 1
                    self.long_next_add = self.long_entry_price * (1 + config.SCALING_FACTOR * self.long_add_count)
                    next_add_price = self.long_next_add
                    logging.log(NOTI, "롱 추가 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                                self.long_add_count, self.real_time_price, next_add_price)
                    await asyncio.sleep(1)
                    await self.update_position_via_api()

                exit_long_level1 = float(self.entry) + (self.highest_price - float(self.entry)) * config.SAFE_FACTOR if self.highest_price and self.entry != '-' else None
                exit_long_level2 = float(self.entry) + (self.highest_price - float(self.entry)) * config.EXIT_FACTOR if self.highest_price and self.entry != '-' else None
                
                if self.long_add_count >= config.TRAILING_SAFE:
                    logging.log(NOTI, "롱 안전 조건 가격: %s", exit_long_level1)
                if self.long_add_count >= config.TRAILING_SAFE and exit_long_level1 is not None and self.real_time_price <= exit_long_level1:
                    logging.log(NOTI, "롱 안전 조건 충족, 포지션 청산 진행")
                    await self.clear_position_main()
                    await asyncio.sleep(1)
                    self.initial_balance = self.get_futures_balance_with_retry()
                    logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                    logging.log(NOTI, "롱 포지션 안전 청산 완료")
                    return
                    
                if self.long_add_count >= config.TRAILING_START:
                    logging.log(NOTI, "롱 청산 조건 가격: %s", exit_long_level2)
                if self.long_add_count >= config.TRAILING_START and exit_long_level2 is not None and self.real_time_price <= exit_long_level2:
                    logging.log(NOTI, "롱 청산 조건 충족, 포지션 청산 진행")
                    await self.clear_position_main()
                    await asyncio.sleep(1)
                    self.initial_balance = self.get_futures_balance_with_retry()
                    logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                    logging.log(NOTI, "롱 포지션 청산 완료")
                    return

        # 숏 포지션 진입 및 관리
        if pre_short_condition:
            if self.position == 1:
                logging.log(NOTI, "역전발생: 현재 롱 포지션이므로 청산 진행")
                await self.clear_position_main()
                await asyncio.sleep(1)
                self.initial_balance = self.get_futures_balance_with_retry()
                logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                logging.log(NOTI, "롱 포지션 청산 완료")
                return
                
        if short_condition:
            while self.real_time_price is None:
                logging.debug("실시간 가격 대기중")
                await asyncio.sleep(1)
            if self.position >= 0 and vol_condition and bearish_consecutive:
                logging.log(NOTI, "숏 진입 조건 충족")
                logging.log(NOTI,"현재가격:%s", current_price)
                qty = self.get_order_quantity_for_symbol(config.SYMBOL, current_price)
                order = self.place_order("SELL", qty)
                order_id = order['orderId']
                order_result = self.check_order_result(order_id, config.SYMBOL)
                self.position = -1
                self.short_entry_price = float(order_result['avgPrice'])
                self.short_add_count = 1
                self.short_next_add = self.short_entry_price * (1 - config.SCALING_FACTOR)
                next_add_price_formatted = f"{self.short_next_add:.{self.price_precision}f}" if self.price_precision is not None else self.short_next_add
                self.short_lowest = latest['low']
                logging.log(NOTI, "숏 포지션 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                            self.short_add_count, self.short_entry_price, next_add_price_formatted)
                await asyncio.sleep(1)
                await self.update_position_via_api()
            elif self.position == -1:
                if self.lowest_price is not None and self.short_lowest is not None:
                    self.short_lowest = min(self.short_lowest, self.lowest_price)
                logging.log(NOTI, "숏 포지션 유지 중, 최저가 업데이트: %s", self.lowest_price)
                
                if self.real_time_price is not None and self.short_next_add is not None and self.real_time_price <= self.short_next_add and self.short_add_count < config.MAX_ENTRIES:
                    logging.log(NOTI, "숏 추가 진입 조건 충족")
                    logging.log(NOTI,"현재가격:%s", current_price)
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("SELL", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL)
                    self.short_add_count += 1
                    self.short_next_add = self.short_entry_price * (1 - config.SCALING_FACTOR * self.short_add_count)
                    next_add_price = self.short_next_add
                    logging.log(NOTI, "숏 추가 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                                self.short_add_count, self.short_entry_price, next_add_price)
                    await asyncio.sleep(1)
                    await self.update_position_via_api()

                exit_short_level1 = float(self.entry) - (float(self.entry) - self.lowest_price) * config.SAFE_FACTOR if self.lowest_price and self.entry != '-' else None
                exit_short_level2 = float(self.entry) - (float(self.entry) - self.lowest_price) * config.EXIT_FACTOR if self.lowest_price and self.entry != '-' else None

                if self.short_add_count >= config.TRAILING_SAFE:
                    logging.log(NOTI, "숏 안전 조건 가격: %s", exit_short_level1)
                if self.short_add_count >= config.TRAILING_SAFE and exit_short_level1 is not None and self.real_time_price >= exit_short_level1:
                    logging.log(NOTI, "숏 안전 조건 충족, 포지션 청산 진행")
                    await self.clear_position_main()
                    await asyncio.sleep(1)
                    self.initial_balance = self.get_futures_balance_with_retry()
                    logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                    logging.log(NOTI, "숏 포지션 안전 청산 완료")
                    return
                    
                if self.short_add_count >= config.TRAILING_START:
                    logging.log(NOTI, "숏 청산 조건 가격: %s", exit_short_level2)
                if self.short_add_count >= config.TRAILING_START and exit_short_level2 is not None and self.real_time_price >= exit_short_level2:
                    logging.log(NOTI, "숏 청산 조건 충족, 포지션 청산 진행")
                    await self.clear_position_main()
                    await asyncio.sleep(1)
                    self.initial_balance = self.get_futures_balance_with_retry()
                    logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                    logging.log(NOTI, "숏 포지션 청산 완료")
                    return

    async def monitor_candles(self):
        while True:
            interval_seconds = self.interval_map.get(config.INTERVAL, 60)
            current_time = time.time()
            next_candle_time = (self.last_candle_timestamp / 1000) + interval_seconds if self.last_candle_timestamp else current_time + interval_seconds
            sleep_duration = max(0, next_candle_time - current_time)
            if sleep_duration > 0.5:
                logging.log(NOTI, "다음 봉 종료까지 %.2f초 대기 (candle task)", sleep_duration)
                logging.log(NOTI, "============================================================")
            await asyncio.sleep(sleep_duration)
            new_df = self.get_recent_klines(config.SYMBOL, config.INTERVAL, lookback=100)
            if new_df is not None and not new_df.empty:
                new_latest = new_df.iloc[-1]
                if self.last_candle_timestamp is None or new_latest['timestamp'] > self.last_candle_timestamp:
                    logging.log(NOTI, "새로운 봉 감지: OLD %s, NEW %s", self.last_candle_timestamp, new_latest['timestamp'])
                    self.last_candle_timestamp = new_latest['timestamp']
                    await self.update_position_via_api()
                    await asyncio.sleep(0.5)
                    new_df = self.add_ema_indicators(new_df)
                    await self.process_candle(new_df)
            await asyncio.sleep(0.5)

    async def monitor_real_time_entry(self):
        while True:
            await asyncio.sleep(0.5)
            logging.debug("monitor_real_time_entry: position=%s, real_time_price=%s", self.position, self.real_time_price)
            
            if self.position == 1:
                if self.real_time_price is not None:
                    if self.highest_price is None:
                        self.highest_price = self.real_time_price
                    else:
                        self.highest_price = max(self.real_time_price, self.highest_price)
                
                if self.real_time_price is not None and self.long_next_add is not None and self.real_time_price >= self.long_next_add and self.long_add_count < config.MAX_ENTRIES:
                    logging.log(NOTI, "롱 추가 진입 조건 (실시간) 충족: 가격 %s, 목표 %s", self.real_time_price, self.long_next_add)
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("BUY", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL)
                    self.long_entry_price = float(order_result['avgPrice'])
                    self.long_add_count += 1
                    self.long_next_add = self.long_entry_price * (1 + config.SCALING_FACTOR * self.long_add_count)
                    next_add_price = self.long_next_add
                    logging.log(NOTI, "롱 추가 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                                self.long_add_count, self.long_entry_price, next_add_price)
                    await asyncio.sleep(1)
                    await self.update_position_via_api()
                    self.highest_price = max(self.highest_price or 0, self.real_time_price or 0)
                    continue

                if (self.real_time_price is not None and self.long_entry_price is not None and 
                    self.real_time_price >= self.long_entry_price * (1 + config.SCALING_FACTOR * (self.long_add_count - config.MAX_ENTRIES + 1)) and 
                    self.long_add_count >= config.MAX_ENTRIES and self.long_add_count < config.MAX_ENTRIES * 2):
                    logging.log(NOTI, "롱 부분 청산 조건 (실시간) 충족: 가격 %s, 목표 %s", 
                                self.real_time_price, self.long_entry_price * (1 + config.SCALING_FACTOR * (self.long_add_count - config.MAX_ENTRIES + 1)))
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("SELL", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL) 
                    self.long_entry_price = float(order_result['avgPrice'])
                    self.long_add_count += 1
                    next_partial_exit = self.long_entry_price * (1 + config.SCALING_FACTOR * (self.long_add_count - config.MAX_ENTRIES + 1))
                    logging.log(NOTI, "롱 부분 청산 완료 - 단계: %s, 청산가: %s, 다음 부분 청산 목표가: %s",
                                self.long_add_count, self.long_entry_price, next_partial_exit)
                    await asyncio.sleep(1)
                    await self.update_position_via_api()
                    if self.long_add_count >= config.MAX_ENTRIES * 2:
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "롱 포지션 완전 청산 완료 (부분 청산 결과)")
                    continue

                if self.long_add_count >= config.TRAILING_SAFE and self.real_time_price is not None and self.entry != '-':
                    exit_long_level1 = float(self.entry) + (self.highest_price - float(self.entry)) * config.SAFE_FACTOR if self.highest_price else None
                    if exit_long_level1 is not None and self.real_time_price <= exit_long_level1:
                        logging.log(NOTI, "롱 안전 조건 충족, 포지션 청산 진행")
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "롱 포지션 청산 완료")
                        continue
            
                if self.long_add_count >= config.TRAILING_START and self.real_time_price is not None and self.entry != '-':
                    exit_long_level2 = float(self.entry) + (self.highest_price - float(self.entry)) * config.EXIT_FACTOR if self.highest_price else None
                    if exit_long_level2 is not None and self.real_time_price <= exit_long_level2:
                        logging.log(NOTI, "롱 청산 조건 충족, 포지션 청산 진행")
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "롱 포지션 청산 완료")
                        continue
                        
            elif self.position == -1:
                if self.real_time_price is not None:
                    if self.lowest_price is None:
                        self.lowest_price = self.real_time_price
                    else:
                        self.lowest_price = min(self.real_time_price, self.lowest_price)

                if self.real_time_price is not None and self.short_next_add is not None and self.real_time_price <= self.short_next_add and self.short_add_count < config.MAX_ENTRIES:
                    logging.log(NOTI, "숏 추가 진입 조건 (실시간) 충족: 가격 %s, 목표 %s", self.real_time_price, self.short_next_add)
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("SELL", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL)
                    self.short_entry_price = float(order_result['avgPrice'])
                    self.short_add_count += 1
                    self.short_next_add = self.short_entry_price * (1 - config.SCALING_FACTOR * self.short_add_count)
                    # ▼▼▼ 수정된 부분 ▼▼▼
                    next_add_price_formatted = f"{self.short_next_add:.{self.price_precision}f}" if self.price_precision is not None else self.short_next_add
                    logging.log(NOTI, "숏 추가 진입 완료 - 단계: %s, 진입가: %s, 다음 추가 진입가: %s",
                                self.short_add_count, self.short_entry_price, next_add_price_formatted)
                    # ▲▲▲ 수정된 부분 ▲▲▲
                    await asyncio.sleep(1)
                    await self.update_position_via_api()
                    self.lowest_price = min(self.lowest_price or float('inf'), self.real_time_price or float('inf'))
                    continue
                    
                if (self.real_time_price is not None and self.short_entry_price is not None and 
                    self.real_time_price <= self.short_entry_price * (1 - config.SCALING_FACTOR * (self.short_add_count - config.MAX_ENTRIES + 1)) and 
                    self.short_add_count >= config.MAX_ENTRIES and self.short_add_count < config.MAX_ENTRIES * 2):
                    logging.log(NOTI, "숏 부분 청산 조건 (실시간) 충족: 가격 %s, 목표 %s",
                                self.real_time_price, self.short_entry_price * (1 - config.SCALING_FACTOR * (self.short_add_count - config.MAX_ENTRIES + 1)))
                    qty = self.get_order_quantity_for_symbol(config.SYMBOL, self.real_time_price)
                    order = self.place_order("BUY", qty)
                    order_id = order['orderId']
                    order_result = self.check_order_result(order_id, config.SYMBOL)
                    self.short_entry_price = float(order_result['avgPrice'])
                    self.short_add_count += 1
                    next_partial_exit = self.short_entry_price * (1 - config.SCALING_FACTOR * (self.short_add_count - config.MAX_ENTRIES + 1))
                    logging.log(NOTI, "숏 부분 청산 완료 - 단계: %s, 청산가: %s, 다음 부분 청산 목표가: %s",
                                self.short_add_count, self.short_entry_price, next_partial_exit)
                    await asyncio.sleep(1)
                    await self.update_position_via_api()
                    if self.short_add_count >= config.MAX_ENTRIES * 2:
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "숏 포지션 완전 청산 완료 (부분 청산 결과)")
                    continue

                if self.short_add_count >= config.TRAILING_SAFE and self.real_time_price is not None and self.entry != '-':
                    exit_short_level1 = float(self.entry) - (float(self.entry) - self.lowest_price) * config.SAFE_FACTOR if self.lowest_price else None
                    if exit_short_level1 is not None and self.real_time_price >= exit_short_level1:
                        logging.log(NOTI, "숏 안전 조건 충족, 포지션 청산 진행")
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "숏 포지션 청산 완료")
                        continue
                    
                if self.short_add_count >= config.TRAILING_START and self.real_time_price is not None and self.entry != '-':
                    exit_short_level2 = float(self.entry) - (float(self.entry) - self.lowest_price) * config.EXIT_FACTOR if self.lowest_price else None
                    if exit_short_level2 is not None and self.real_time_price >= exit_short_level2:
                        logging.log(NOTI, "숏 청산 조건 충족, 포지션 청산 진행")
                        await self.clear_position_main()
                        await asyncio.sleep(1)
                        self.initial_balance = self.get_futures_balance_with_retry()
                        logging.log(NOTI, "현재 잔고: %s", self.initial_balance)
                        logging.log(NOTI, "숏 포지션 청산 완료")
                        continue
                        
    async def run_strategy_async(self):
        asyncio.create_task(self.async_read_real_time_price())
        while self.real_time_price is None:
            await asyncio.sleep(1)
        self.initial_balance = self.get_futures_balance_with_retry()
        if self.initial_balance is None:
            logging.error("잔고 조회 실패로 인해 종료합니다.")
            return
        self.check_ini()
        self.set_leverage()
        self.get_min_order_qty()
        df = self.get_recent_klines(config.SYMBOL, config.INTERVAL, lookback=100)
        if df is None or df.empty:
            logging.error("초기 캔들 데이터를 가져오지 못했습니다.")
            return
        df = self.add_ema_indicators(df)
        latest = df.iloc[-1]
        self.last_candle_timestamp = latest['timestamp']
        current_price_for_initial = latest['close']
        logging.log(NOTI, "최소 주문금액 조건을 확인합니다...")
        self.get_order_quantity_for_symbol_start(config.SYMBOL, current_price_for_initial)
        await self.process_candle(df)
        await asyncio.sleep(1)
        await self.update_position_via_api()
        await asyncio.gather(
            self.notify_current_price(),
            self.monitor_candles(),
            self.monitor_real_time_entry()
        )

    def run_strategy(self):
        asyncio.run(self.run_strategy_async())


def run_gui():
    from PyQt5.QtWidgets import QApplication
    from gui import MainWindow
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    if "--strategy" in sys.argv:
        strategy = TradingStrategy()
        strategy.run_strategy()
    else:
        run_gui()