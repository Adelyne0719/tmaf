import sys
import os
import requests
import time
import pandas as pd
import logging
from datetime import datetime
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QTableWidget, QHeaderView, QLabel,
                             QApplication, QTabWidget, QLineEdit, QFormLayout,
                             QTableWidgetItem, QScrollArea, QGroupBox, QMessageBox,
                             QComboBox, QSplitter, QButtonGroup, QStackedWidget, QCheckBox,
                             QTextEdit, QListWidget, QAbstractItemView, QFrame, QDialog,
                             QRadioButton)
from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, QTimer, QThread, QPropertyAnimation, pyqtProperty, QRect, QSize, QEvent
from PyQt5.QtGui import QPalette, QColor, QBrush, QPen, QPainter, QFont

import pyqtgraph as pg
from pyqtgraph import PlotDataItem, GraphicsObject

# 로깅 설정 (콘솔 출력만)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from v7_dual_api import BinanceAPI, BybitAPI
from v7_dual_ticker_ws import TickerSocketThread, BybitTickerSocketThread
import v7_dual_config_manager as config_manager
from v7_dual_ws_manager import WebSocketThread
from v7_dual_auto_trader import AutoTradeWorker
from v7_dual_resource_monitor import ResourceMonitor

# ========== 심볼 자동 변환 매핑 테이블 ==========

# Binance: USDT-M (fapi) → COIN-M (dapi)
BINANCE_SYMBOL_MAPPING = {
    'BTCUSDT': 'BTCUSD_PERP', 'ETHUSDT': 'ETHUSD_PERP', 'BNBUSDT': 'BNBUSD_PERP',
    'ADAUSDT': 'ADAUSD_PERP', 'DOGEUSDT': 'DOGEUSD_PERP', 'XRPUSDT': 'XRPUSD_PERP',
    'DOTUSDT': 'DOTUSD_PERP', 'SOLUSDT': 'SOLUSD_PERP', 'MATICUSDT': 'MATICUSD_PERP',
    'LTCUSDT': 'LTCUSD_PERP', 'AVAXUSDT': 'AVAXUSD_PERP', 'LINKUSDT': 'LINKUSD_PERP',
    'ATOMUSDT': 'ATOMUSD_PERP', 'ETCUSDT': 'ETCUSD_PERP', 'XLMUSDT': 'XLMUSD_PERP',
    'TRXUSDT': 'TRXUSD_PERP', 'FILUSDT': 'FILUSD_PERP', 'EOSUSDT': 'EOSUSD_PERP',
    'BCHUSDT': 'BCHUSD_PERP',
}

# Bybit: Linear → Inverse
BYBIT_SYMBOL_MAPPING = {
    'BTCUSDT': 'BTCUSD', 'ETHUSDT': 'ETHUSD', 'BNBUSDT': 'BNBUSD',
    'ADAUSDT': 'ADAUSD', 'DOGEUSDT': 'DOGEUSD', 'XRPUSDT': 'XRPUSD',
    'DOTUSDT': 'DOTUSD', 'SOLUSDT': 'SOLUSD', 'MATICUSDT': 'MATICUSD',
    'LTCUSDT': 'LTCUSD', 'AVAXUSDT': 'AVAXUSD', 'LINKUSDT': 'LINKUSD',
    'ATOMUSDT': 'ATOMUSD', 'ETCUSDT': 'ETCUSD', 'XLMUSDT': 'XLMUSD',
    'TRXUSDT': 'TRXUSD', 'FILUSDT': 'FILUSD', 'EOSUSDT': 'EOSUSD',
    'BCHUSDT': 'BCHUSD',
}

# 역방향 매핑 자동 생성
BINANCE_REVERSE_MAPPING = {v: k for k, v in BINANCE_SYMBOL_MAPPING.items()}
BYBIT_REVERSE_MAPPING = {v: k for k, v in BYBIT_SYMBOL_MAPPING.items()}


def convert_symbol_for_market(symbol, target_market, exchange):
    """
    심볼을 거래소와 마켓에 맞게 자동 변환 (범용 지원)
    
    변환 순서:
    1. _PERP, USD로 끝나는 심볼을 먼저 USDT 형태로 정규화
    2. target_market에 맞게 최종 변환
    """
    # Step 1: 심볼을 USDT 형태로 정규화
    normalized_symbol = symbol
    
    # Binance COIN-M 형식 (_PERP) → USDT 형태로 정규화
    if symbol.endswith('_PERP'):
        # BTCUSD_PERP → BTCUSDT
        base = symbol.replace('USD_PERP', '')
        normalized_symbol = base + 'USDT'
    
    # Bybit Inverse 형식 (USD) → USDT 형태로 정규화
    elif symbol.endswith('USD') and not symbol.endswith('USDT'):
        # BTCUSD → BTCUSDT
        normalized_symbol = symbol + 'T'
    
    # Step 2: target_market에 맞게 변환
    if exchange == "Binance":
        if target_market == 'dapi':
            # USDT → COIN-M (_PERP)
            if normalized_symbol in BINANCE_SYMBOL_MAPPING:
                return BINANCE_SYMBOL_MAPPING[normalized_symbol], True
        elif target_market == 'fapi':
            # 이미 USDT 형태면 그대로
            if normalized_symbol.endswith('USDT'):
                return normalized_symbol, (symbol != normalized_symbol)
    
    elif exchange == "Bybit":
        if target_market == 'dapi':
            # USDT → Inverse (USD)
            if normalized_symbol in BYBIT_SYMBOL_MAPPING:
                return BYBIT_SYMBOL_MAPPING[normalized_symbol], True
        elif target_market == 'fapi':
            # 이미 USDT 형태면 그대로
            if normalized_symbol.endswith('USDT'):
                return normalized_symbol, (symbol != normalized_symbol)
    
    return symbol, False


import v7_dual_trading_utils as trading_utils

class ConnectAPIThread(QThread):
    """오래 걸리는 API 연결 작업을 백그라운드에서 처리합니다."""
    connection_finished = pyqtSignal(str, dict)  # v7_dual: (side, result)

    def __init__(self, accounts, account_name, market_type, current_interval, old_ws_thread, old_ticker_thread, exchange, current_symbol="BTCUSDT", side='long', parent=None):
        super().__init__(parent)
        self.accounts = accounts
        self.account_name = account_name
        self.market_type = market_type
        self.current_interval = current_interval
        self.old_ws_thread = old_ws_thread
        self.old_ticker_thread = old_ticker_thread
        self.exchange = exchange
        self.current_symbol = current_symbol  # GUI에서 선택한 심볼
        self.side = side  # v7_dual: 'long' 또는 'short' 패널 구분자
        self.running = True

    def run(self):
        """스레드가 실행할 메인 로직 (모든 블로킹 작업)"""
        result = {'success': False, 'error': None, 'data': {}}
        
        # ▼▼▼ [API 모듈 선택] ▼▼▼
        self.api_module = None
        if self.exchange == "Bybit":
            self.api_module = BybitAPI()
        elif self.exchange == "Binance":
            self.api_module = BinanceAPI()
        else:
            result['error'] = f"Unsupported exchange: {self.exchange}"
            self.connection_finished.emit(self.side, result)  # v7_dual: side 추가
            return
        # ▲▲▲ [API 모듈 선택] ▲▲▲

        try:
            # 1. 이전 스레드 종료
            if self.old_ws_thread and self.old_ws_thread.isRunning():
                print("Worker: 이전 User Data 스레드 종료 대기 중...")
                self.old_ws_thread.stop()
                self.old_ws_thread.wait()
                print("Worker: 이전 User Data 스레드 종료 완료.")
            
            if self.old_ticker_thread and self.old_ticker_thread.isRunning():
                print("Worker: 이전 Ticker 스레드 종료 대기 중...")
                self.old_ticker_thread.stop()
                self.old_ticker_thread.wait()
                print("Worker: 이전 Ticker 스레드 종료 완료.")

            # 2. API 키 설정
            account_info = self.accounts.get(self.account_name)
            if not account_info:
                raise Exception(f"'{self.account_name}' 계정 정보를 찾을 수 없습니다.")

            # Binance의 경우 심볼에 따라 자동으로 market_type 결정
            # 계정 설정의 market 값을 우선 사용
            actual_market_type = account_info.get('market', self.market_type)
            print(f"Worker: 계정 설정 market 사용: {actual_market_type}")

            # 심볼을 market에 맞게 자동 변환 (Binance + Bybit)
            if self.current_symbol:
                converted_symbol, was_converted = convert_symbol_for_market(
                    self.current_symbol, actual_market_type, self.exchange
                )
                if was_converted:
                    market_name = "COIN-M" if actual_market_type == 'dapi' else "USDT-M"
                    if self.exchange == "Bybit":
                        market_name = "Inverse" if actual_market_type == 'dapi' else "Linear"
                    print(f"✅ 심볼 자동 변환: {self.current_symbol} → {converted_symbol}")
                    print(f"   ({self.exchange} {market_name}에 최적화됨)")
                    self.current_symbol = converted_symbol
                else:
                    if self.current_symbol.endswith('USDT') and actual_market_type == 'dapi':
                        print(f"⚠️ '{self.current_symbol}'는 지원되지 않을 수 있습니다.")
                    elif (self.current_symbol.endswith('_PERP') or 
                          (self.current_symbol.endswith('USD') and not self.current_symbol.endswith('USDT'))) and actual_market_type == 'fapi':
                        print(f"⚠️ '{self.current_symbol}'는 지원되지 않을 수 있습니다.")

            self.api_module.set_active_market(actual_market_type)
            self.api_module.set_active_api_keys(account_info['api_key'], account_info['api_secret'])
            
            if self.exchange == "Bybit":
                try:
                    print("Worker: Bybit 서버 시간과 로컬 시간 동기화 상태 확인 중...")
                    server_time_ms = self.api_module.get_server_time()
                    local_time_ms = int(time.time() * 1000)

                    if server_time_ms:
                        diff_ms = server_time_ms - local_time_ms
                        # pandas가 이미 import 되어 있으므로 to_datetime 사용
                        server_time_str = pd.to_datetime(server_time_ms, unit='ms')
                        local_time_str = pd.to_datetime(local_time_ms, unit='ms')

                        print("="*50)
                        print(f"  [시간 동기화 검사 결과]")
                        print(f"  Bybit 서버 시간: {server_time_str} ({server_time_ms} ms)")
                        print(f"  로컬 PC 시간:   {local_time_str} ({local_time_ms} ms)")
                        print(f"  시간 차이 (Server - Local): {diff_ms} ms")
                        print("="*50)

                        # 시간 차이가 1초 이상이면 자동 윈도우 시간 동기화 실행
                        if abs(diff_ms) > 1000:
                            print(f"  [경고] 시간 차이가 {abs(diff_ms)} ms로 감지되었습니다.")
                            print(f"  [자동 조치] 윈도우 시간 동기화를 실행합니다...")
                            print(f"  [참고] 관리자 권한으로 실행 시 자동 동기화가 성공합니다.")

                            try:
                                import subprocess

                                # w32tm /resync 명령 실행 (관리자 권한 필요)
                                sync_result = subprocess.run(
                                    ["w32tm", "/resync"],
                                    capture_output=True,
                                    text=True,
                                    timeout=5,
                                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                                )

                                if sync_result.returncode == 0:
                                    print(f"  [성공] 시간 동기화 완료")

                                    # 동기화 후 재확인
                                    time.sleep(1)
                                    new_server_time = self.api_module.get_server_time()
                                    if new_server_time and new_server_time > 0:
                                        new_local_time_ms = int(time.time() * 1000)
                                        new_diff_ms = new_server_time - new_local_time_ms
                                        print(f"  [재확인] 동기화 후 시간 차이: {new_diff_ms} ms")

                                        if abs(new_diff_ms) > 1000:
                                            print(f"  [경고] 동기화 후에도 {new_diff_ms}ms 차이가 있습니다 (recv_window={self.api_module._recv_window}ms 내에서 정상 작동)")
                                        else:
                                            print(f"  [완료] 시간 동기화가 성공적으로 완료되었습니다")
                                else:
                                    # 동기화 실패 (권한 부족)
                                    print(f"  [실패] 자동 시간 동기화 실패 (관리자 권한 필요)")
                                    print(f"  ")
                                    print(f"  ※ 해결 방법:")
                                    print(f"  1) 프로그램을 관리자 권한으로 실행 (우클릭 > 관리자 권한으로 실행)")
                                    print(f"  2) 또는 Windows 설정에서 수동 동기화:")
                                    print(f"     Win+I > 시간 및 언어 > 날짜 및 시간 > '지금 동기화' 클릭")
                                    print(f"  ")
                                    print(f"  [참고] recv_window가 {self.api_module._recv_window//1000}초로 설정되어 API는 정상 작동할 수 있습니다")

                            except subprocess.TimeoutExpired:
                                print(f"  [실패] 시간 동기화 명령 시간 초과")
                            except Exception as e:
                                print(f"  [실패] 시간 동기화 오류: {e}")

                        else:
                            print(f"  [정보] 시간 차이가 {diff_ms}ms로 정상 범위입니다.")

                    else:
                        print("Worker: Bybit 서버 시간을 가져오는 데 실패했습니다. (공개 API 문제)")

                except Exception as e:
                    print(f"Worker: 서버 시간 확인 중 오류 발생: {e}")
            
            if not self.running: return

            # 3. Listen Key 받기 (네트워크 I/O)
            listen_key = None
            
            if not self.running: return

            # 4. ▼▼▼ [수정] 초기 잔액 로드 (네트워크 I/O) ▼▼▼
            balance_info = self.api_module.get_initial_balance() # ◀◀◀ [API 모듈 사용]
            
            if not self.running: return
            
            # 5. 초기 포지션 로드 (네트워크 I/O)
            positions = self.api_module.get_initial_positions() # ◀◀◀ [API 모듈 사용]
            
            if not self.running: return

            # 6. 초기 주문 로드 (네트워크 I/O)
            orders = self.api_module.get_initial_open_orders() # ◀◀◀ [API 모듈 사용]
            
            # 7. 심볼 결정 (GUI에서 선택한 심볼 사용)
            api_symbol_to_use = self.current_symbol
            print(f"Worker: 선택된 심볼 사용: {api_symbol_to_use}")

            if not self.running: return

            # 8. OHLCV 데이터 로드 (네트워크 I/O)
            print(f"Worker: {api_symbol_to_use} ({self.current_interval}) 캔들 데이터 로드 중...")
            klines = self.api_module.get_ohlcv_data(api_symbol_to_use, self.current_interval, 500) # ◀◀◀ 500개로 제한 (성능 최적화)
            
            # ▼▼▼ [ 9. 웹소켓 스레드 생성 (거래소별 분리) ] ▼▼▼
            if self.exchange == "Binance":
                print("Worker: Binance Listen Key 요청 중...")
                listen_key = self.api_module.get_listen_key()
                if not listen_key:
                    raise Exception("Failed to get Binance Listen Key. Check API keys.")

                new_ws_thread = WebSocketThread(
                    exchange="Binance",
                    listen_key=listen_key,
                    market_type=actual_market_type,
                    side=self.side
                )
                new_ticker_thread = TickerSocketThread(actual_market_type, api_symbol_to_use)

            elif self.exchange == "Bybit":
                print("Worker: Bybit 웹소켓 스레드 생성 중 (Auth 방식)...")
                api_key = account_info['api_key']
                api_secret = account_info['api_secret']

                # Bybit는 Listen Key 대신 Key/Secret를 스레드에 직접 전달
                new_ws_thread = WebSocketThread(
                    exchange="Bybit",
                    api_key=api_key,
                    api_secret=api_secret,
                    market_type=actual_market_type,
                    side=self.side
                )
                new_ticker_thread = BybitTickerSocketThread(actual_market_type, api_symbol_to_use)

            else:
                raise Exception(f"Unsupported exchange for WebSockets: {self.exchange}")
            # ▲▲▲ [ 9. 웹소켓 스레드 생성 (거래소별 분리) ] ▲▲▲
            
            # 10. 성공 데이터 준비
            result['success'] = True
            result['data'] = {
                'listen_key': listen_key,
                'balance_info': balance_info,
                'positions': positions,
                'orders': orders,
                'current_symbol': api_symbol_to_use,
                'klines': klines,
                'new_ws_thread': new_ws_thread,
                'new_ticker_thread': new_ticker_thread,
                'api_module': self.api_module, # ◀◀◀ [API 모듈 전달]
                'exchange': self.exchange, # ◀◀◀ [거래소 정보 전달 - DCA 복구/Kline WebSocket 필요]
                'market_type': actual_market_type # ◀◀◀ [실제 사용된 마켓 타입 전달 - Kline WebSocket 필요]
            }
            
        except Exception as e:
            print(f"ConnectAPIThread 오류: {e}")
            result['error'] = str(e)
            if hasattr(self, 'api_module') and self.api_module: # ◀◀◀ [API 모듈 사용]
                self.api_module.set_active_api_keys(None, None) # 실패 시 키 비활성화

        # 11. 메인 스레드로 결과 전송
        self.connection_finished.emit(self.side, result)  # v7_dual: side 추가

    def stop(self):
        self.running = False

class SlideToggle(QWidget):
    """직사각형 슬라이드 토글 스위치"""
    toggled = pyqtSignal(bool)

    def __init__(self, text="", checked=False, parent=None):
        super().__init__(parent)
        self._checked = checked
        self._text = text
        self._knob_x = 0.0
        self._animation = QPropertyAnimation(self, b"knob_position")
        self._animation.setDuration(150)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(24)
        self._update_knob_target(animate=False)

    def get_knob_position(self):
        return self._knob_x

    def set_knob_position(self, val):
        self._knob_x = val
        self.update()

    knob_position = pyqtProperty(float, get_knob_position, set_knob_position)

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._update_knob_target(animate=True)
            self.toggled.emit(self._checked)

    def _update_knob_target(self, animate=True):
        target = 1.0 if self._checked else 0.0
        if animate:
            self._animation.setStartValue(self._knob_x)
            self._animation.setEndValue(target)
            self._animation.start()
        else:
            self._knob_x = target
            self.update()

    def mousePressEvent(self, event):
        self._checked = not self._checked
        self._update_knob_target(animate=True)
        self.toggled.emit(self._checked)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 토글 트랙 크기
        track_w, track_h = 36, 18
        knob_margin = 2
        knob_size = track_h - knob_margin * 2
        track_y = (self.height() - track_h) // 2

        # 트랙 색상
        off_color = QColor("#555555")
        on_color = QColor("#4CAF50")
        t = self._knob_x
        r = int(off_color.red() + (on_color.red() - off_color.red()) * t)
        g = int(off_color.green() + (on_color.green() - off_color.green()) * t)
        b = int(off_color.blue() + (on_color.blue() - off_color.blue()) * t)
        track_color = QColor(r, g, b)

        # 트랙 그리기 (둥근 직사각형)
        p.setBrush(track_color)
        p.setPen(Qt.NoPen)
        p.drawRoundedRect(0, track_y, track_w, track_h, track_h // 2, track_h // 2)

        # 노브 그리기
        knob_travel = track_w - knob_size - knob_margin * 2
        knob_x = knob_margin + self._knob_x * knob_travel
        p.setBrush(QColor("#FFFFFF"))
        p.drawRoundedRect(int(knob_x), track_y + knob_margin, knob_size, knob_size, knob_size // 2, knob_size // 2)

        # 텍스트
        if self._text:
            text_color = on_color if self._checked else QColor("#999999")
            p.setPen(text_color)
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            p.setFont(font)
            text_x = track_w + 6
            p.drawText(QRect(text_x, 0, self.width() - text_x, self.height()), Qt.AlignVCenter | Qt.AlignLeft, self._text)

    def sizeHint(self):
        return QSize(250, 24)


class AutoBalanceThread(QThread):
    """Auto Balance: 잔액 차이 5% 이상일 때 자동 이체하는 백그라운드 스레드"""
    transfer_finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, from_account_data, to_account_data, amount, parent=None):
        super().__init__(parent)
        self.from_account_data = from_account_data
        self.to_account_data = to_account_data
        self.amount = amount

    def run(self):
        try:
            from v7_dual_api import BybitAPI

            # 1. 송신자 API 생성
            from_api = BybitAPI()
            from_api.set_active_api_keys(
                self.from_account_data['api_key'],
                self.from_account_data['api_secret']
            )

            # 2. 수신자 API 생성 및 UID 조회
            to_api = BybitAPI()
            to_api.set_active_api_keys(
                self.to_account_data['api_key'],
                self.to_account_data['api_secret']
            )
            to_uid = to_api.get_uid()
            if not to_uid:
                self.transfer_finished.emit(False, "받는 계정 UID 조회 실패")
                return

            # 3. UNIFIED 지갑에서 내부 이체 실행
            amount_str = f"{self.amount:.4f}"
            success, message = from_api.withdraw_internal("USDT", amount_str, to_uid, "UNIFIED")

            if not success:
                self.transfer_finished.emit(False, f"이체 실패: {message}")
                return

            # 4. 수신측 FUND → UNIFIED 전환 대기 (최대 60초)
            import time as _time
            before_fund = to_api.get_usdt_balance("FUND")
            expected = before_fund + self.amount

            for attempt in range(60):
                _time.sleep(1)
                current_fund = to_api.get_usdt_balance("FUND")
                if current_fund >= expected - 0.001:
                    recv_ok, recv_result = to_api.transfer_between_accounts(
                        "USDT", amount_str, "FUND", "UNIFIED"
                    )
                    if recv_ok:
                        self.transfer_finished.emit(
                            True,
                            f"{amount_str} USDT 이체 완료 ({attempt + 1}초 대기)"
                        )
                    else:
                        self.transfer_finished.emit(
                            True,
                            f"{amount_str} USDT 이체 성공, FUND→UNIFIED 전환 실패: {recv_result}"
                        )
                    return

            # 타임아웃
            self.transfer_finished.emit(
                True,
                f"{amount_str} USDT 이체 성공, FUND→UNIFIED 전환 대기 타임아웃 (60초)"
            )

        except Exception as e:
            self.transfer_finished.emit(False, f"Auto Balance 오류: {e}")


class ReserveFundTransferThread(QThread):
    """비축금 적립 및 투입을 위한 백그라운드 스레드"""
    transfer_finished = pyqtSignal(bool, str)

    def __init__(self, mode, amount, primary_account_data, secondary_account_data=None, parent=None):
        super().__init__(parent)
        self.mode = mode
        self.amount = amount
        self.primary_account_data = primary_account_data
        self.secondary_account_data = secondary_account_data

    def run(self):
        try:
            from v7_dual_api import BybitAPI
            import time

            primary_api = BybitAPI()
            primary_api.set_active_api_keys(
                self.primary_account_data['api_key'],
                self.primary_account_data['api_secret']
            )

            if self.mode == 'SAVE':
                amount_str = f"{self.amount:.4f}"
                success, msg = primary_api.transfer_between_accounts("USDT", amount_str, "UNIFIED", "FUND")
                if success:
                    self.transfer_finished.emit(True, f"{amount_str} USDT 비축금 적립 완료")
                else:
                    self.transfer_finished.emit(False, f"비축금 적립 실패: {msg}")

            elif self.mode == 'RESTORE':
                messages = []
                
                # 1. 반대편 계정 비축금 가져오기
                if self.secondary_account_data:
                    secondary_api = BybitAPI()
                    secondary_api.set_active_api_keys(
                        self.secondary_account_data['api_key'],
                        self.secondary_account_data['api_secret']
                    )
                    secondary_fund = secondary_api.get_usdt_balance("FUND")
                    if secondary_fund > 0.0001:
                        primary_uid = primary_api.get_uid()
                        if primary_uid:
                            sec_amt_str = f"{secondary_fund:.4f}"
                            succ, msg = secondary_api.withdraw_internal("USDT", sec_amt_str, primary_uid, "FUND")
                            if succ:
                                time.sleep(3)  # 이체 도착 대기
                                messages.append(f"반대편 계정에서 {sec_amt_str} USDT 복구")
                            else:
                                messages.append(f"반대편 복구 실패: {msg}")
                
                # 2. 본인 계정 비축금 전체를 UNIFIED로 이동
                primary_fund = primary_api.get_usdt_balance("FUND")
                if primary_fund > 0.0001:
                    pri_amt_str = f"{primary_fund:.4f}"
                    succ, msg = primary_api.transfer_between_accounts("USDT", pri_amt_str, "FUND", "UNIFIED")
                    if succ:
                        messages.append(f"본인 계정에서 {pri_amt_str} USDT 투입 완료")
                    else:
                        messages.append(f"본인 계정 투입 실패: {msg}")
                
                if not messages:
                    messages.append("투입할 비축금이 없습니다.")
                    
                self.transfer_finished.emit(True, " | ".join(messages))

        except Exception as e:
            self.transfer_finished.emit(False, f"비축금 처리 오류: {e}")


class FetchReserveFundThread(QThread):
    """주기적으로 각 계정의 펀딩 계좌(비축금) 잔액을 가져오는 백그라운드 스레드"""
    result_ready = pyqtSignal(dict)

    def __init__(self, long_account_data, short_account_data, parent=None):
        super().__init__(parent)
        self.long_account_data = long_account_data
        self.short_account_data = short_account_data

    def run(self):
        try:
            from v7_dual_api import BybitAPI
            res = {}
            if self.long_account_data:
                api = BybitAPI()
                api.set_active_api_keys(self.long_account_data['api_key'], self.long_account_data['api_secret'])
                res['long'] = api.get_usdt_balance("FUND")
            if self.short_account_data:
                api = BybitAPI()
                api.set_active_api_keys(self.short_account_data['api_key'], self.short_account_data['api_secret'])
                res['short'] = api.get_usdt_balance("FUND")
            self.result_ready.emit(res)
        except Exception as e:
            print(f"FetchReserveFundThread 오류: {e}")


class SetupAutoTradeThread(QThread):
    """
    'Start' 버튼 클릭 시, GUI가 멈추지 않도록
    헷지 모드/레버리지 설정, 자금 계산 등 I/O 작업을 백그라운드에서 처리합니다.
    """
    # (성공여부, 에러메시지, 계산된 파라미터 딕셔너리)
    setup_finished = pyqtSignal(bool, str, dict)

    # GUI 상태 라벨에 로그를 보내기 위한 시그널
    log_message = pyqtSignal(str)

    def __init__(self, api_module, category, symbol, balance_asset, balance_total, strategy_settings, parent=None):
        super().__init__(parent)
        self.api_module = api_module
        self.category = category # "linear" or "inverse"
        self.symbol = symbol
        self.balance_asset = balance_asset # "USDT"
        self.balance_total = balance_total # 204.28
        self.strategy_settings = strategy_settings

        self.log_prefix = "SetupAutoTradeThread"

    def _get_min_order_value(self, symbol):
        """
        코인별 최소 주문 금액(USDT)을 반환합니다.

        Bybit 거래소의 일반적인 최소 주문 금액:
        - BTC, ETH: 20 USDT
        - 기타 대부분: 5 USDT

        Args:
            symbol: 거래 심볼 (예: "BTCUSDT", "XRPUSDT")

        Returns:
            float: 최소 주문 금액 (USDT)
        """
        # BTC, ETH는 20 USDT
        high_value_symbols = ['BTC', 'ETH']

        # 심볼에서 기본 자산 추출 (예: "BTCUSDT" -> "BTC")
        base_asset = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '')

        if base_asset in high_value_symbols:
            return 20.0
        else:
            return 5.0

    def run(self):
        print(f"{self.log_prefix}: 자동매매 설정 스레드 시작...")
        params = {}
        try:
            # 1. 포지션 모드를 헤지 모드(3)로 변경
            self.log_message.emit("Status: <b style='color: yellow;'>1/5: 헷지 모드 설정 중...</b>")
            if not self.api_module.set_position_mode(self.category, self.symbol, mode=3):
                raise Exception("헷지 모드 설정 실패. (API 권한 확인)")

            # 2. 격리 마진 모드 및 레버리지 설정
            leverage = self.strategy_settings.get("TARGET_LEVERAGE", 15)
            self.log_message.emit(f"Status: <b style='color: yellow;'>2/5: 마진 모드 및 레버리지({leverage}x) 설정 중...</b>")
            if not self.api_module.set_margin_and_leverage(self.category, self.symbol, margin_mode=1, leverage=leverage):
                raise Exception("격리 마진 모드 또는 레버리지 설정 실패. API 권한을 확인하세요.")

            # 3. 거래 규칙 조회
            self.log_message.emit("Status: <b style='color: yellow;'>3/5: 거래 규칙 조회 중...</b>")

            # 4. 거래 규칙 조회
            self.log_message.emit("Status: <b style='color: yellow;'>4/6: 거래 규칙 조회 중...</b>")
            rules = self.api_module.get_instrument_info(self.category, self.symbol)
            if not rules:
                raise Exception("거래 규칙 조회 실패.")

            qty_step = float(rules['lotSizeFilter']['qtyStep'])
            min_order_qty = float(rules['lotSizeFilter']['minOrderQty'])

            # 5. 현재 가격 조회
            self.log_message.emit("Status: <b style='color: yellow;'>5/6: 현재 가격 조회 중...</b>")
            mark_price = self.api_module.get_mark_price(self.category, self.symbol)
            if mark_price == 0.0:
                raise Exception("현재 가격 조회 실패.")

            # 6. 자금 계산 (test_entry_calculation.py 로직 사용)
            self.log_message.emit("Status: <b style='color: yellow;'>6/6: 10단계 진입 수량 계산 중...</b>")

            # test_entry_calculation.py의 TEST_SETTINGS와 동일한 설정 객체 생성
            config_params = self.strategy_settings.copy()
            # 동적 값 추가
            config_params["BALANCE_ASSET"] = self.balance_asset
            # % 값을 0.0-1.0 비율로 변환
            config_params["BALANCE_USAGE_PERCENTAGE"] = config_params.get("BALANCE_USAGE_PERCENTAGE", 70.0) / 100.0
            strat_config = trading_utils.ConfigHelper(config_params)
            
            # Bybit API의 `rules` 딕셔너리가 `test_entry_calculation.py`의 `USDT_M_SYMBOL_INFO` 역할을 함
            # Bybit는 `lotSizeFilter` 내부에 정보가 있음
            if 'lotSizeFilter' not in rules:
                raise Exception(f"거래 규칙에 'lotSizeFilter'가 없습니다: {rules}")
            
            # [수정] Bybit는 minOrderQty, Binance는 minQty. Bybit 기준으로 통일 (lotSizeFilter)
            min_order_qty = float(rules['lotSizeFilter']['minOrderQty'])

            # 새 유틸리티 함수 호출
            success, entry_qty_list, cumul_qty_list = trading_utils.calculate_entry_quantities(
                category=self.category,
                symbol_info=rules, # API에서 받은 전체 규칙 전달
                min_order_qty=min_order_qty,
                current_balance=self.balance_total,
                mark_price=mark_price,
                config=strat_config
            )
            
            if not success:
                raise Exception(f"진입 수량 계산 실패. (로그 확인): {entry_qty_list[0]}")

            # 테스트 모드 확인
            test_mode = self.strategy_settings.get("TEST_QUANTITY_MODE", False)

            if test_mode:
                # 테스트 모드: 코인별 최소 주문 금액을 만족하는 수량 계산
                print(f"[{self.log_prefix}] 원본 진입 수량 목록: {entry_qty_list}")

                # 수량 정밀도 계산
                qty_precision = trading_utils.count_decimal_places(qty_step)

                # 코인별 최소 주문 금액 조회
                min_order_value = self._get_min_order_value(self.symbol)
                print(f"[{self.log_prefix}] [테스트 모드] {self.symbol} 최소 주문 금액: ${min_order_value} USDT")

                # 최소 주문 금액을 만족하는 수량 계산
                required_qty = min_order_value / mark_price

                # qtyStep에 맞춰 올림 처리 (최소 주문 금액을 확실히 만족하도록)
                from decimal import Decimal, ROUND_UP
                required_qty_decimal = Decimal(str(required_qty))
                qty_step_decimal = Decimal(str(qty_step))

                # 올림 처리: (required_qty / qty_step).ceil() * qty_step
                test_qty = float((required_qty_decimal / qty_step_decimal).quantize(Decimal('1'), rounding=ROUND_UP) * qty_step_decimal)

                # minOrderQty보다 작으면 minOrderQty 사용
                if test_qty < min_order_qty:
                    test_qty = min_order_qty

                entry_qty_list = [test_qty] * strat_config.STEPS

                # 헷지 수량 목록 계산
                hedge_start = self.strategy_settings.get("HEDGE_START_PERCENT", 40)
                hedge_end = self.strategy_settings.get("HEDGE_END_PERCENT", 100)
                hedge_qty_list = []
                cumulative_entry = 0
                cumulative_hedge = 0
                for step in range(strat_config.STEPS):
                    cumulative_entry += test_qty
                    hedge_qty_raw = trading_utils.calculate_hedge_quantity(
                        test_qty, step, strat_config.STEPS,
                        cumulative_entry, cumulative_hedge,
                        hedge_start, hedge_end, test_mode,
                        frontload_final_step=self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False)
                    )
                    # 헷지 수량도 qtyStep에 맞춰 조정
                    hedge_qty_adjusted = trading_utils.adjust_quantity(
                        hedge_qty_raw, qty_step, qty_precision, min_order_qty
                    )
                    hedge_qty_list.append(hedge_qty_adjusted)
                    cumulative_hedge += hedge_qty_adjusted

                order_value = test_qty * mark_price
                print(f"[{self.log_prefix}] [테스트 모드] 최소 주문 금액({min_order_value} USDT)을 만족하는 수량: {test_qty} (주문 금액: ${order_value:.2f})")
                print(f"[{self.log_prefix}] [테스트 모드] 진입 수량 목록: {entry_qty_list}")
                print(f"[{self.log_prefix}] [테스트 모드] 헷지 수량 목록: {hedge_qty_list}")
                final_entry_qty = test_qty
            else:
                final_entry_qty = entry_qty_list[0]
                if final_entry_qty <= 0:
                    # 0번째가 0이면 1번째(최소수량)를 사용
                    final_entry_qty = entry_qty_list[1]

                # 수량 정밀도 계산
                qty_precision = trading_utils.count_decimal_places(qty_step)

                # 헷지 수량 목록 계산 (누적 기반)
                hedge_start = self.strategy_settings.get("HEDGE_START_PERCENT", 40)
                hedge_end = self.strategy_settings.get("HEDGE_END_PERCENT", 100)
                hedge_qty_list = []
                cumulative_entry = 0
                cumulative_hedge = 0
                for i, entry_qty in enumerate(entry_qty_list):
                    cumulative_entry += entry_qty
                    hedge_qty_raw = trading_utils.calculate_hedge_quantity(
                        entry_qty, i, strat_config.STEPS,
                        cumulative_entry, cumulative_hedge,
                        hedge_start, hedge_end, test_mode=False,
                        frontload_final_step=self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False)
                    )
                    # 헷지 수량도 qtyStep에 맞춰 조정
                    hedge_qty_adjusted = trading_utils.adjust_quantity(
                        hedge_qty_raw, qty_step, qty_precision, min_order_qty
                    )
                    hedge_qty_list.append(hedge_qty_adjusted)
                    cumulative_hedge += hedge_qty_adjusted

                print(f"[{self.log_prefix}] 계산 완료. 진입 수량 10단계 목록: {entry_qty_list}")
                print(f"[{self.log_prefix}] 계산 완료. 헷지 수량 10단계 목록: {hedge_qty_list}")
                print(f"[{self.log_prefix}] 자동매매 시작 수량 (Step 0 또는 1): {final_entry_qty}")

            # 헷지 수량 분할 검증 (Step 1의 헷지 수량을 4분할했을 때 최소 주문 금액 확인)
            # Step 1 헷지 수량 (인덱스 1)
            if len(hedge_qty_list) > 1:
                step1_hedge_qty = hedge_qty_list[1]

                # 헷지 분할 주문 계산 (4개로 분할, 비율 0.5)
                # calculate_hedge_split_orders는 (price, quantity) 튜플 리스트를 반환
                # 여기서는 수량만 확인하면 되므로 임시 가격 사용
                hedge_split_orders = trading_utils.calculate_hedge_split_orders(
                    step1_hedge_qty, mark_price, mark_price * 0.95, num_splits=4, ratio=0.5
                )

                # 코인별 최소 주문 금액 조회
                min_order_value = self._get_min_order_value(self.symbol)
                print(f"[{self.log_prefix}] {self.symbol} 최소 주문 금액: ${min_order_value} USDT")

                # 각 분할 수량의 주문 금액 확인
                below_min_count = 0
                for i, (price, qty) in enumerate(hedge_split_orders):
                    # qtyStep에 맞춰 조정
                    adj_qty = trading_utils.adjust_quantity(qty, qty_step, qty_precision, min_order_qty)
                    order_value = adj_qty * mark_price

                    if order_value < min_order_value:
                        below_min_count += 1
                        print(f"[{self.log_prefix}] [경고] Step 1 헷지 트리거 {i+1}/4: 주문 금액 ${order_value:.2f} < 최소 ${min_order_value} (수량: {adj_qty})")

                if below_min_count > 0:
                    # 최소 주문 금액 이하인 주문이 있음 - 사용자 확인 필요
                    params['needs_user_confirmation'] = True
                    params['warning_message'] = f"주문 최소 금액({min_order_value} USDT) 이하인 헷지 주문이 {below_min_count}개 있습니다.\n추가 금액을 입금하거나 배율을 높이세요.\n그래도 진행하시겠습니까?"
                else:
                    params['needs_user_confirmation'] = False

            params['symbol'] = self.symbol
            params['entry_quantity'] = str(final_entry_qty)
            params['entry_qty_list'] = entry_qty_list
            params['hedge_qty_list'] = hedge_qty_list
            params['symbol_info'] = rules
            params['category'] = self.category

            # 모든 설정 완료
            self.setup_finished.emit(True, "", params)

        except Exception as e:
            print(f"{self.log_prefix} 오류: {e}")
            self.setup_finished.emit(False, str(e), {})

# ... (CustomAxisItem, CustomViewBox, CandlestickItem 클래스는 변경 없음) ...
class CustomAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.precision = 2 # 기본 소수점 2자리 (FAPI)

    def setPrecision(self, precision):
        self.precision = precision
        self.picture = None 
        self.update()

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            strings.append(f"{v:.{self.precision}f}")
        return strings

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setMouseMode(self.PanMode) 

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == pg.QtCore.Qt.ControlModifier:
            self.setMouseEnabled(x=False, y=True)
        else:
            self.setMouseEnabled(x=True, y=False)
        super().wheelEvent(event)
        self.setMouseEnabled(x=True, y=True)
            
    def mouseDoubleClickEvent(self, ev, axis=None):
        if ev.button() == pg.QtCore.Qt.LeftButton:
            print("Auto-ranging chart...")
            self.autoRange()
            ev.accept()
        else:
            super().mouseDoubleClickEvent(ev, axis=axis)
            
    def mouseDragEvent(self, ev, axis=None):
        if ev.isStart():
            if ev.button() == pg.QtCore.Qt.RightButton:
                self.setMouseMode(self.RectMode)
                self.setMouseEnabled(x=False, y=True)
            elif ev.button() == pg.QtCore.Qt.LeftButton:
                self.setMouseMode(self.PanMode)
                self.setMouseEnabled(x=True, y=True)
        super().mouseDragEvent(ev, axis=None)
        if ev.isFinish():
            self.setMouseMode(self.PanMode)
            self.setMouseEnabled(x=True, y=True)        
            
class CandlestickItem(GraphicsObject):
    def __init__(self, data):
        GraphicsObject.__init__(self)
        self.data = data
        self.base_picture = None  # 확정된 캔들들 (0 ~ N-2)
        self.last_candle_picture = None  # 현재 진행 중인 마지막 캔들
        self.last_full_render_len = 0  # 마지막 전체 렌더링 시 캔들 개수
        self._candle_w = 0.4  # 캔들 폭
        self.generatePicture(data)

    def setData(self, data, update_only_last=False):
        self.prepareGeometryChange()
        self.data = data
        self.generatePicture(data, update_only_last=update_only_last)
        self.informViewBoundsChanged()
        self.update()

    def _draw_candle(self, p, t, o, h, l, c, w):
        """단일 캔들 그리기 헬퍼"""
        color = '#c00000' if o > c else '#00b050'
        p.setPen(pg.mkPen(color))
        p.drawLine(pg.QtCore.QPointF(t, l), pg.QtCore.QPointF(t, h))
        p.setBrush(pg.mkBrush(color))
        p.drawRect(pg.QtCore.QRectF(t - w, o, w * 2, c - o))

    def generatePicture(self, data, update_only_last=False):
        if data.empty:
            self.base_picture = None
            self.last_candle_picture = None
            return

        # 캔들 폭 계산
        if data.shape[0] > 1:
            self._candle_w = (data['time'].iloc[1] - data['time'].iloc[0]) * 0.4
        else:
            self._candle_w = 0.4
        w = self._candle_w

        # 진행 중인 봉만 업데이트하는 최적화 모드
        if update_only_last and len(data) > 0 and len(data) == self.last_full_render_len:
            # 마지막 캔들만 다시 그리기 (base_picture 유지)
            self.last_candle_picture = pg.QtGui.QPicture()
            p = pg.QtGui.QPainter(self.last_candle_picture)
            row = data.iloc[-1]
            self._draw_candle(p, row['time'], row['open'], row['high'], row['low'], row['close'], w)
            p.end()
        else:
            # 전체 캔들 그리기 (새 봉 추가 시 또는 초기 로드)
            self.last_full_render_len = len(data)

            # base_picture: 마지막 캔들을 제외한 모든 캔들
            if len(data) > 1:
                self.base_picture = pg.QtGui.QPicture()
                p_base = pg.QtGui.QPainter(self.base_picture)
                for i in range(len(data) - 1):
                    row = data.iloc[i]
                    self._draw_candle(p_base, row['time'], row['open'], row['high'], row['low'], row['close'], w)
                p_base.end()
            else:
                self.base_picture = None

            # 마지막 캔들
            self.last_candle_picture = pg.QtGui.QPicture()
            p_last = pg.QtGui.QPainter(self.last_candle_picture)
            row = data.iloc[-1]
            self._draw_candle(p_last, row['time'], row['open'], row['high'], row['low'], row['close'], w)
            p_last.end()

    def paint(self, p, *args):
        if self.base_picture is not None:
            p.drawPicture(0, 0, self.base_picture)
        if self.last_candle_picture is not None:
            p.drawPicture(0, 0, self.last_candle_picture)

    def boundingRect(self):
        if self.data.empty:
            return pg.QtCore.QRectF()
        t_min = self.data['time'].min()
        t_max = self.data['time'].max()
        p_min = self.data['low'].min()
        p_max = self.data['high'].max()
        w = self._candle_w
        return pg.QtCore.QRectF(t_min - w, p_min, (t_max - t_min) + w * 2, p_max - p_min)


# ========================================================================
# 설정 다이얼로그 클래스들
# ========================================================================

class AccountSettingsDialog(QDialog):
    """Account 설정 팝업 다이얼로그"""
    def __init__(self, accounts, current_long_account, current_short_account, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Account Settings")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)

        self.accounts = accounts
        self.selected_long_account = current_long_account
        self.selected_short_account = current_short_account

        layout = QVBoxLayout(self)

        # LONG Account 섹션
        long_group = QGroupBox("LONG Account")
        long_layout = QVBoxLayout(long_group)

        self.long_account_combo = QComboBox()
        self.long_account_combo.setMinimumHeight(35)
        for account_name in accounts.keys():
            self.long_account_combo.addItem(account_name)
        if current_long_account:
            self.long_account_combo.setCurrentText(current_long_account)
        long_layout.addWidget(self.long_account_combo)

        self.long_connect_btn = QPushButton("Connect LONG")
        self.long_connect_btn.setMinimumHeight(35)
        self.long_connect_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #0078d4; color: white;")
        self.long_connect_btn.clicked.connect(lambda: self.on_connect_clicked('long'))
        long_layout.addWidget(self.long_connect_btn)

        self.long_status_label = QLabel("Not connected")
        self.long_status_label.setStyleSheet("color: gray; font-size: 9pt;")
        self.long_status_label.setAlignment(Qt.AlignCenter)
        long_layout.addWidget(self.long_status_label)

        layout.addWidget(long_group)

        # SHORT Account 섹션
        short_group = QGroupBox("SHORT Account")
        short_layout = QVBoxLayout(short_group)

        self.short_account_combo = QComboBox()
        self.short_account_combo.setMinimumHeight(35)
        for account_name in accounts.keys():
            self.short_account_combo.addItem(account_name)
        if current_short_account:
            self.short_account_combo.setCurrentText(current_short_account)
        short_layout.addWidget(self.short_account_combo)

        self.short_connect_btn = QPushButton("Connect SHORT")
        self.short_connect_btn.setMinimumHeight(35)
        self.short_connect_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #0078d4; color: white;")
        self.short_connect_btn.clicked.connect(lambda: self.on_connect_clicked('short'))
        short_layout.addWidget(self.short_connect_btn)

        self.short_status_label = QLabel("Not connected")
        self.short_status_label.setStyleSheet("color: gray; font-size: 9pt;")
        self.short_status_label.setAlignment(Qt.AlignCenter)
        short_layout.addWidget(self.short_status_label)

        layout.addWidget(short_group)

        # Close 버튼
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(40)
        close_btn.setStyleSheet("font-size: 11pt; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def on_connect_clicked(self, side):
        """Connect 버튼 클릭 - 부모 윈도우의 연결 함수 호출"""
        # 선택한 계정 저장
        if side == 'long':
            self.selected_long_account = self.long_account_combo.currentText()
            account_name = self.selected_long_account
        else:
            self.selected_short_account = self.short_account_combo.currentText()
            account_name = self.selected_short_account

        # 부모 윈도우에 선택한 계정 업데이트
        parent = self.parent()
        if parent:
            parent.current_account_names[side] = account_name
            print(f"[{side.upper()}] Account 선택됨: {account_name}")

            # 부모 윈도우의 연결 함수 호출
            if hasattr(parent, 'on_connect_button_clicked'):
                parent.on_connect_button_clicked(side)


class SymbolMarketSettingsDialog(QDialog):
    """Symbol & Market 설정 팝업 다이얼로그"""
    def __init__(self, current_symbol, current_market, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Symbol & Market Settings")
        self.setMinimumWidth(400)
        self.setMinimumHeight(250)

        self.selected_symbol = current_symbol
        self.selected_market = current_market

        layout = QVBoxLayout(self)

        # Symbol 섹션
        symbol_group = QGroupBox("Symbol")
        symbol_layout = QVBoxLayout(symbol_group)

        self.symbol_combo = QComboBox()
        self.symbol_combo.setMinimumHeight(35)
        self.symbol_combo.addItems([
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT"
        ])
        self.symbol_combo.setCurrentText(current_symbol)
        symbol_layout.addWidget(self.symbol_combo)

        layout.addWidget(symbol_group)

        # Market Type 섹션
        market_group = QGroupBox("Market Type")
        market_layout = QVBoxLayout(market_group)

        self.market_combo = QComboBox()
        self.market_combo.setMinimumHeight(35)
        self.market_combo.addItems(["Linear (USDT)", "Inverse (COIN)"])
        if current_market in ['linear', 'fapi']:
            self.market_combo.setCurrentIndex(0)
        else:
            self.market_combo.setCurrentIndex(1)
        market_layout.addWidget(self.market_combo)

        layout.addWidget(market_group)

        # 버튼들
        button_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #00b050; color: white;")
        save_btn.clicked.connect(self.on_save_clicked)
        button_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.setStyleSheet("font-size: 11pt; font-weight: bold;")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def on_save_clicked(self):
        """Save 버튼 클릭"""
        self.selected_symbol = self.symbol_combo.currentText()
        market_text = self.market_combo.currentText()
        if "Linear" in market_text:
            self.selected_market = "linear"
        else:
            self.selected_market = "inverse"
        self.accept()


class EqualBalanceDialog(QDialog):
    """계정 간 잔액 균등화 다이얼로그"""
    def __init__(self, accounts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Equal Balance")
        self.setMinimumWidth(420)
        self.setMinimumHeight(350)
        self.accounts = accounts
        self.from_balance = 0.0
        self.to_balance = 0.0
        self.from_api = None
        self.to_api = None

        # Bybit 계정만 필터링
        self.bybit_accounts = {
            name: data for name, data in accounts.items()
            if data.get('exchange', '').lower() == 'bybit'
        }

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # === Auto Balance Checkbox ===
        import v7_dual_config_manager as config_manager
        config_data = config_manager.load_config_data()
        app_settings = config_data.get("app_settings", {})

        self.auto_balance_checkbox = QCheckBox("Auto Balance (5% 이상 차이시 자동 이체)")
        self.auto_balance_checkbox.setStyleSheet("font-size: 10pt; font-weight: bold; color: #FF8C00; padding: 5px;")
        self.auto_balance_checkbox.setChecked(app_settings.get("auto_balance_enabled", False))
        self.auto_balance_checkbox.stateChanged.connect(self._on_auto_balance_toggled)
        layout.addWidget(self.auto_balance_checkbox)

        # === From Account ===
        from_group = QGroupBox("From Account (보내는 계정)")
        from_layout = QVBoxLayout(from_group)
        self.from_combo = QComboBox()
        self.from_combo.setMinimumHeight(30)
        for name in self.bybit_accounts.keys():
            self.from_combo.addItem(name)
        self.from_combo.currentTextChanged.connect(lambda: self._on_account_changed('from'))
        from_layout.addWidget(self.from_combo)
        self.from_balance_label = QLabel("Balance: -")
        self.from_balance_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #00FF00;")
        self.from_balance_label.setAlignment(Qt.AlignCenter)
        from_layout.addWidget(self.from_balance_label)
        layout.addWidget(from_group)

        # === Swap Button ===
        swap_btn = QPushButton("\u21c5")
        swap_btn.setFixedSize(36, 24)
        swap_btn.setStyleSheet("font-size: 14pt; font-weight: bold; background-color: #444444; color: white; border-radius: 4px;")
        swap_btn.setToolTip("From / To 계정 스왑")
        swap_btn.clicked.connect(self._on_swap_clicked)
        swap_layout = QHBoxLayout()
        swap_layout.addStretch()
        swap_layout.addWidget(swap_btn)
        swap_layout.addStretch()
        layout.addLayout(swap_layout)

        # === To Account ===
        to_group = QGroupBox("To Account (받는 계정)")
        to_layout = QVBoxLayout(to_group)
        self.to_combo = QComboBox()
        self.to_combo.setMinimumHeight(30)
        for name in self.bybit_accounts.keys():
            self.to_combo.addItem(name)
        # 두 번째 계정 기본 선택
        if self.to_combo.count() > 1:
            self.to_combo.setCurrentIndex(1)
        self.to_combo.currentTextChanged.connect(lambda: self._on_account_changed('to'))
        to_layout.addWidget(self.to_combo)
        self.to_balance_label = QLabel("Balance: -")
        self.to_balance_label.setStyleSheet("font-size: 12pt; font-weight: bold; color: #00FF00;")
        self.to_balance_label.setAlignment(Qt.AlignCenter)
        to_layout.addWidget(self.to_balance_label)
        layout.addWidget(to_group)

        # === Transfer Info ===
        info_group = QGroupBox("Transfer Info")
        info_layout = QVBoxLayout(info_group)

        self.diff_label = QLabel("Difference: -")
        self.diff_label.setStyleSheet("font-size: 11pt; color: #AAAAAA;")
        self.diff_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.diff_label)

        amount_h = QHBoxLayout()
        amount_label = QLabel("Transfer Amount:")
        amount_label.setStyleSheet("font-size: 11pt;")
        self.amount_input = QLineEdit()
        self.amount_input.setMinimumHeight(30)
        self.amount_input.setStyleSheet("font-size: 12pt; font-weight: bold;")
        self.amount_input.setPlaceholderText("0.0000")
        amount_h.addWidget(amount_label)
        amount_h.addWidget(self.amount_input)
        info_layout.addLayout(amount_h)

        hint_label = QLabel("(잔액 차이의 절반이 자동 입력됩니다. 수동 수정 가능)")
        hint_label.setStyleSheet("font-size: 9pt; color: #888888;")
        hint_label.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(hint_label)

        # 출금 지갑 선택
        self.wallet_group = QButtonGroup(self)
        wallet_h = QHBoxLayout()
        wallet_label = QLabel("Wallet:")
        wallet_label.setStyleSheet("font-size: 11pt;")
        wallet_h.addWidget(wallet_label)
        self.radio_fund = QRadioButton("FUND")
        self.radio_unified = QRadioButton("UNIFIED")
        self.radio_unified.setChecked(True)
        self.radio_fund.setStyleSheet("font-size: 11pt;")
        self.radio_unified.setStyleSheet("font-size: 11pt;")
        self.wallet_group.addButton(self.radio_fund)
        self.wallet_group.addButton(self.radio_unified)
        self.radio_fund.toggled.connect(self._refresh_balances)
        wallet_h.addWidget(self.radio_fund)
        wallet_h.addWidget(self.radio_unified)
        wallet_h.addStretch()
        info_layout.addLayout(wallet_h)

        layout.addWidget(info_group)

        # === Buttons ===
        btn_layout = QHBoxLayout()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.setMinimumHeight(35)
        refresh_btn.setStyleSheet("font-size: 10pt; font-weight: bold; background-color: #555555; color: white;")
        refresh_btn.clicked.connect(self._refresh_balances)
        btn_layout.addWidget(refresh_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.setStyleSheet("font-size: 10pt; font-weight: bold;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.transfer_btn = QPushButton("Transfer")
        self.transfer_btn.setMinimumHeight(35)
        self.transfer_btn.setStyleSheet("font-size: 10pt; font-weight: bold; background-color: #FF8C00; color: white;")
        self.transfer_btn.clicked.connect(self._on_transfer_clicked)
        btn_layout.addWidget(self.transfer_btn)
        layout.addLayout(btn_layout)

        notice_label = QLabel("* UNIFIED 선택 시 이체 완료까지 최대 30초 소요될 수 있습니다.")
        notice_label.setStyleSheet("font-size: 8pt; color: #888888;")
        notice_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(notice_label)

        # 초기 잔액 로드
        QTimer.singleShot(100, self._refresh_balances)

    def _on_auto_balance_toggled(self, state):
        """Auto Balance 체크박스 상태 변경 시 config에 저장"""
        import v7_dual_config_manager as config_manager
        config_data = config_manager.load_config_data()
        if "app_settings" not in config_data:
            config_data["app_settings"] = {}
        config_data["app_settings"]["auto_balance_enabled"] = bool(state)
        config_manager.save_config_data(config_data)

    def _create_temp_api(self, account_name):
        """계정용 임시 BybitAPI 인스턴스 생성"""
        from v7_dual_api import BybitAPI
        account_data = self.bybit_accounts.get(account_name)
        if not account_data:
            return None
        api = BybitAPI()
        api.set_active_api_keys(account_data['api_key'], account_data['api_secret'])
        return api

    def _on_account_changed(self, which):
        """계정 선택 변경 시 잔액 새로고침"""
        self._refresh_balances()

    def _on_swap_clicked(self):
        """From / To 계정 스왑"""
        from_name = self.from_combo.currentText()
        to_name = self.to_combo.currentText()
        self.from_combo.blockSignals(True)
        self.to_combo.blockSignals(True)
        self.from_combo.setCurrentText(to_name)
        self.to_combo.setCurrentText(from_name)
        self.from_combo.blockSignals(False)
        self.to_combo.blockSignals(False)
        self._refresh_balances(auto_swap=False)


    def _refresh_balances(self, auto_swap=True):
        """양쪽 잔액 조회 및 UI 업데이트"""
        from_name = self.from_combo.currentText()
        to_name = self.to_combo.currentText()

        if not from_name or not to_name:
            return

        wallet_type = "FUND" if self.radio_fund.isChecked() else "UNIFIED"

        self.from_balance_label.setText("Balance: Loading...")
        self.to_balance_label.setText("Balance: Loading...")
        QApplication.processEvents()

        # From 잔액 조회
        self.from_api = self._create_temp_api(from_name)
        if self.from_api:
            self.from_balance = self.from_api.get_usdt_balance(wallet_type)
            self.from_balance_label.setText(f"Balance: {self.from_balance:.4f} USDT ({wallet_type})")
        else:
            self.from_balance = 0.0
            self.from_balance_label.setText("Balance: Error")

        QApplication.processEvents()

        # To 잔액 조회
        self.to_api = self._create_temp_api(to_name)
        if self.to_api:
            self.to_balance = self.to_api.get_usdt_balance(wallet_type)
            self.to_balance_label.setText(f"Balance: {self.to_balance:.4f} USDT ({wallet_type})")
        else:
            self.to_balance = 0.0
            self.to_balance_label.setText("Balance: Error")

        # 잔액이 높은 쪽이 From이 되도록 자동 스왑
        if auto_swap and self.from_balance < self.to_balance:
            self.from_combo.blockSignals(True)
            self.to_combo.blockSignals(True)
            self.from_combo.setCurrentText(to_name)
            self.to_combo.setCurrentText(from_name)
            self.from_combo.blockSignals(False)
            self.to_combo.blockSignals(False)
            self.from_balance, self.to_balance = self.to_balance, self.from_balance
            self.from_balance_label.setText(f"Balance: {self.from_balance:.4f} USDT ({wallet_type})")
            self.to_balance_label.setText(f"Balance: {self.to_balance:.4f} USDT ({wallet_type})")

        # 차이 계산 및 자동 입력
        diff = self.from_balance - self.to_balance
        self.diff_label.setText(f"Difference: {diff:+.4f} USDT")
        if diff > 0:
            self.diff_label.setStyleSheet("font-size: 11pt; color: #00FF00;")
        elif diff < 0:
            self.diff_label.setStyleSheet("font-size: 11pt; color: #FF4444;")
        else:
            self.diff_label.setStyleSheet("font-size: 11pt; color: #AAAAAA;")

        transfer_amount = abs(diff) / 2
        self.amount_input.setText(f"{transfer_amount:.4f}")

    def _on_transfer_clicked(self):
        """Transfer 버튼 클릭"""
        try:
            amount = float(self.amount_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "올바른 금액을 입력해주세요.")
            return

        if amount <= 0:
            QMessageBox.warning(self, "Error", "이체 금액은 0보다 커야 합니다.")
            return

        from_name = self.from_combo.currentText()
        to_name = self.to_combo.currentText()

        if from_name == to_name:
            QMessageBox.warning(self, "Error", "보내는 계정과 받는 계정이 같습니다.")
            return

        if amount > self.from_balance:
            QMessageBox.warning(self, "Error",
                f"이체 금액({amount:.4f})이 보내는 계정 잔액({self.from_balance:.4f})보다 큽니다.")
            return

        account_type = "FUND" if self.radio_fund.isChecked() else "UNIFIED"

        reply = QMessageBox.question(
            self, "Transfer Confirm",
            f"다음 이체를 진행하시겠습니까?\n\n"
            f"From: {from_name} ({account_type})\n"
            f"To: {to_name}\n"
            f"Amount: {amount:.4f} USDT\n\n"
            f"(Bybit UID 내부 이체 - 수수료 없음)",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        self.transfer_btn.setEnabled(False)
        self.transfer_btn.setText("Transferring...")
        QApplication.processEvents()

        try:
            # 받는 계정 UID 조회
            to_api = self._create_temp_api(to_name)
            if not to_api:
                QMessageBox.critical(self, "Error", f"받는 계정({to_name}) API 생성 실패")
                return
            to_uid = to_api.get_uid()
            if not to_uid:
                QMessageBox.critical(self, "Error", f"받는 계정({to_name}) UID 조회 실패")
                return

            # 송신자 API로 이체 실행
            from_api = self._create_temp_api(from_name)
            if not from_api:
                QMessageBox.critical(self, "Error", f"보내는 계정({from_name}) API 생성 실패")
                return

            success, message = from_api.withdraw_internal("USDT", f"{amount:.4f}", to_uid, account_type)

            if success:
                # 받는 계정: UNIFIED 선택 시 FUND → UNIFIED 자동 전환
                recv_msg = ""
                if account_type == "UNIFIED":
                    import time as _time
                    to_api = self._create_temp_api(to_name)
                    if to_api:
                        before_fund = to_api.get_usdt_balance("FUND")
                        expected = before_fund + amount
                        recv_ok = False
                        for attempt in range(60):
                            _time.sleep(1)
                            self.transfer_btn.setText(f"Waiting... ({attempt+1}s)")
                            QApplication.processEvents()
                            current_fund = to_api.get_usdt_balance("FUND")
                            if current_fund >= expected - 0.001:
                                recv_ok, recv_result = to_api.transfer_between_accounts("USDT", f"{amount:.4f}", "FUND", "UNIFIED")
                                if recv_ok:
                                    recv_msg = f"\n\n(받는 계정 FUND → UNIFIED 전환 완료, {attempt+1}초 대기)"
                                else:
                                    recv_msg = f"\n\n(받는 계정 FUND → UNIFIED 전환 실패: {recv_result})"
                                break
                        if not recv_ok and not recv_msg:
                            recv_msg = f"\n\n(받는 계정 입금 미확인 (60초 타임아웃)\n수동으로 FUND → UNIFIED 전환해주세요)"

                QMessageBox.information(self, "Success",
                    f"이체 완료!\n\n"
                    f"{from_name} ({account_type}) → {to_name}\n"
                    f"{amount:.4f} USDT\n\n"
                    f"{message}{recv_msg}")
                self._refresh_balances()
            else:
                QMessageBox.critical(self, "Transfer Failed",
                    f"이체 실패\n\n{message}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"이체 중 오류 발생:\n{e}")
        finally:
            self.transfer_btn.setEnabled(True)
            self.transfer_btn.setText("Transfer")


class AutoTraderGUI(QMainWindow):
    def __init__(self, auto_restore=False):
        super().__init__()
        self.auto_restore = auto_restore  # 와치독 재시작 시 DCA 자동 복구
        self.current_symbol = "BTCUSDT"
        self.current_interval = "5m"
        self.current_account_name = None  # 현재 연결된 계정 이름 (심볼 기억용)

        # === v7_dual: LONG/SHORT 이중 연결 지원 ===
        # WebSocket 스레드 (side별로 분리)
        self.ws_threads = {'long': None, 'short': None}
        self.ticker_threads = {'long': None, 'short': None}
        self.kline_threads = {'long': None, 'short': None}
        self.listen_keys = {'long': None, 'short': None}
        self.config_data = {}
        self.accounts = {}
        self.strategy_settings = {}
        self.current_market_type = "fapi"

        self.auto_trade_market_mode = "linear" # Bybit: linear (USDT-M) / inverse (COIN-M)
        self.auto_trade_side_mode = "LONG"   # LONG / SHORT

        # === v7_dual: Position & Balance 데이터 (side별로 분리) ===
        self.live_position_data_by_side = {'long': {}, 'short': {}}
        self.live_balances_by_side = {'long': {}, 'short': {}}
        self.live_orders_by_side = {'long': {}, 'short': {}}

        # === v7_dual: 연결 상태 관리 (side별) ===
        self.connect_threads = {'long': None, 'short': None}
        self.current_account_names = {'long': None, 'short': None}
        self.current_symbols = {'long': 'BTCUSDT', 'short': 'BTCUSDT'}
        self.current_market_types = {'long': 'fapi', 'short': 'fapi'}
        self.current_intervals = {'long': '1h', 'short': '1h'}
        self.current_prices_by_side = {'long': 0.0, 'short': 0.0}  # 현재가 캐시 (ticker에서 업데이트)

        # Auto Balance
        self.auto_balance_enabled = False
        self.auto_balance_thread = None

        # Watchdog
        self.watchdog_process = None

        # === v7_dual: UI 요소 (side별) ===
        self.symbol_combos = {'long': None, 'short': None}
        self.direction_combos = {'long': None, 'short': None}  # LONG/SHORT 방향 선택
        self.market_type_combos = {'long': None, 'short': None}  # Linear/Inverse 선택
        self.account_combos = {'long': None, 'short': None}
        self.connect_buttons = {'long': None, 'short': None}
        self.connection_status_labels = {'long': None, 'short': None}
        self.auto_trade_start_buttons = {'long': None, 'short': None}  # Start 버튼
        self.auto_trade_stop_buttons = {'long': None, 'short': None}   # Stop 버튼
        self.auto_trade_status_labels = {'long': None, 'short': None}  # Status 라벨
        self.auto_trade_step_labels = {'long': None, 'short': None}    # Step 라벨

        # === v7_dual: 거래 방향 및 마켓 타입 (side별) ===
        self.market_type_modes = {'long': 'linear', 'short': 'linear'}  # 'linear' or 'inverse'

        # === v7_dual: 거래 방향 (side별) ===
        # 각 패널이 독립적으로 LONG 또는 SHORT 포지션을 운용할 수 있음
        self.side_modes = {'long': 'LONG', 'short': 'SHORT'}  # 기본값: 왼쪽=LONG, 오른쪽=SHORT

        # 누적 통계
        self.total_cycles_completed = 0  # 완료된 사이클 수
        self.cumulative_pnl = 0.0  # 누적 손익
        self.cycle_start_balance = 0.0  # 사이클 시작 시점 잔액 (실시간 손익 계산용)

        self.is_dark_mode = True 
        self.original_palette = QApplication.instance().palette() 
        self.is_reduce_only = False
        
        # === v7_dual: 확정 PNL 추적 (side별) ===
        self.start_balances_by_side = {'long': 0.0, 'short': 0.0}  # 시작 잔액 (접속 시점)
        self.realized_pnl_labels = {'long': None, 'short': None, 'total': None}  # PNL 라벨
        self.cycles_by_side = {'long': 0, 'short': 0}  # side별 사이클 카운트
        self.cycle_count_labels = {'long': None, 'short': None}  # 사이클 카운트 라벨

        # === Statistics 탭 데이터 ===
        self.statistics_data = {'long': [], 'short': []}  # step별 통계
        self.statistics_widgets = {'long': {}, 'short': {}}

        # === v7_dual: UI Labels (side별로 분리) ===
        self.trade_price_labels = {'long': None, 'short': None}
        self.balance_labels = {'long': None, 'short': None}
        self.last_price_for_color = 0.0

        # === v7_dual: Chart Widgets (side별로 분리) ===
        self.chart_widgets = {'long': None, 'short': None}
        self.candlestick_items = {'long': None, 'short': None}
        self.price_line_items = {'long': None, 'short': None}
        self.position_lines_by_side = {'long': {}, 'short': {}}
        self.break_even_lines = {'long': None, 'short': None}
        self.order_lines_by_side = {'long': {}, 'short': {}}
        self.order_step_maps = {'long': {}, 'short': {}}
        self.hedge_trigger_markers_by_side = {'long': [], 'short': []}
        self.m4_order_marker = None  # M4 지정가 주문 마커
        self.profit_target_markers_by_side = {'long': None, 'short': None}
        self.fill_history_by_side = {'long': [], 'short': []}
        self.lines_visible_by_side = {'long': True, 'short': True}
        self.time_axes = {'long': None, 'short': None}
        self.ohlc_labels = {'long': None, 'short': None}  # 차트 내부 OHLC 오버레이 라벨
        self._ohlc_proxies = {'long': None, 'short': None}  # SignalProxy (GC 방지)
        self.crosshair_v = {'long': None, 'short': None}  # 크로스헤어 수직선
        self.crosshair_h = {'long': None, 'short': None}  # 크로스헤어 수평선
        self._crosshair_hide_timer = None  # 크로스헤어 숨김 타이머
        self.chart_refresh_timer_id = None  # SingleShot 타이머 ID 추적 (취소용)

        self.detected_precision = None
        self.price_precisions = {'long': 2, 'short': 2}  # side별 가격 소수점 자릿수

        self.pending_market_orders = set()

        self.loading_overlay = None
        self.loading_animation_timer = None
        self.loading_animation_state = 0
        self.base_loading_text = ""

        self.balance_refresh_timer = None  # 잔액 디바운스 타이머 (체결 후 5초 대기)
        self.reserve_fund_poll_timer = None  # 비축금 주기적 폴링 타이머
        self.fetch_reserve_fund_thread = None
        self.position_loaded = False  # 포지션 로드 완료 플래그

        # 익절 청산 완료 대기 플래그
        self.waiting_for_position_closure = False
        self.position_closure_check_start_time = 0
        self.dca_restore_check_pending = False  # DCA 복구 확인 대기 플래그
        self.position_closure_timer = None  # 포지션 청산 폴링 타이머 (QTimer)
        self.closure_long_pos_key = ""  # 청산 대기 중인 LONG 포지션 키
        self.closure_short_pos_key = ""  # 청산 대기 중인 SHORT 포지션 키

        self.chart_view_save_timer = None  # 차트 뷰 저장 디바운스 타이머 (1초 대기)

        # === v7_dual: Chart DataFrame (side별로 분리) ===
        self.chart_data_dfs = {'long': None, 'short': None}
        self.MAX_CANDLES = 1000  # 차트 데이터 최대 개수 (메모리 누수 방지)

        # Rate limiting for chart updates (성능 최적화)
        self.last_chart_update_time = 0
        self.chart_update_min_interval = 0.05  # 최소 0.05초 간격 (1초에 20번 업데이트)
        self.pending_chart_update = False  # 대기 중인 차트 업데이트
        self.chart_update_timer = None  # QTimer for batched chart updates
        self.current_kline_start_time = None  # 현재 진행 중인 캔들 시작 시간 (밀리초)

        # Rate limiting for Insight tab updates (성능 최적화)
        self.last_insight_update_time = 0
        self.insight_update_min_interval = 0.1  # 최소 0.1초 간격 (실시간 반응)
        self.last_insight_position_update_time = 0  # 포지션 업데이트용 별도 타이머
        self.insight_position_update_interval = 0.1  # 포지션은 0.1초 간격 (실시간 반응)

        # Rate limiting for position line updates (성능 최적화)
        self.last_position_line_update_time = 0
        self.position_line_update_interval = 0.1  # 포지션 라인은 0.1초 간격으로 업데이트

        # DCA 최초 진입 가격 저장 (Insight 탭용, side별)
        self.initial_main_entry_price_by_side = {'long': None, 'short': None}
        self.initial_hedge_entry_price_by_side = {'long': None, 'short': None}

        # Insight 히스토리 저장 (side별)
        self.insight_history_by_side = {'long': [], 'short': []}
        self.current_insight_snapshot_by_side = {'long': None, 'short': None}

        # === v7_dual: API Module (side별로 분리) ===
        self.connect_threads = {'long': None, 'short': None}
        self.api_modules = {'long': None, 'short': None}

        # === v7_dual: AutoTradeWorker (side별로 분리) ===
        self.setup_threads = {'long': None, 'short': None}
        self.auto_trade_threads = {'long': QThread(), 'short': QThread()}

        # LONG, SHORT worker 생성
        self.auto_trade_workers = {
            'long': AutoTradeWorker(side='long'),
            'short': AutoTradeWorker(side='short')
        }
        self.auto_trade_workers['long'].moveToThread(self.auto_trade_threads['long'])
        self.auto_trade_workers['short'].moveToThread(self.auto_trade_threads['short'])

        # 하위 호환성: self.auto_trade_worker = LONG worker
        self.auto_trade_worker = self.auto_trade_workers['long']
        self.auto_trade_thread = self.auto_trade_threads['long']

        # 워커 시그널 연결 (side별)
        for side in ['long', 'short']:
            worker = self.auto_trade_workers[side]
            # 로그 및 주문 실행 시그널
            worker.log_message.connect(lambda msg, s=side: self.on_auto_trade_log_for_side(s, msg))
            # side별로 분리된 주문 실행 (LONG/SHORT 계정 분리)
            worker.execute_trade_signal.connect(
                lambda symbol, order_side, qty, is_hedge, s=side:
                self.on_auto_trade_execute_for_side(s, symbol, order_side, qty, is_hedge)
            )
            worker.execute_limit_order_signal.connect(
                lambda symbol, order_side, quantity, price, is_hedge, s=side:
                self.on_auto_trade_limit_order_for_side(s, symbol, order_side, quantity, price, is_hedge)
            )

            # 차트 마커 업데이트 (양쪽 패널 모두)
            worker.hedge_triggers_updated.connect(
                lambda triggers, mode, step, s=side: self.draw_hedge_trigger_markers_for_side(s, triggers, mode, step)
            )
            worker.m_orders_updated.connect(
                lambda m_orders, s=side: self.draw_m4_order_marker_for_side(s, m_orders)
            )
            worker.profit_target_updated.connect(
                lambda price, step, s=side: self.draw_profit_target_marker_for_side(s, price)
            )
            worker.uptrend_threshold_updated.connect(
                lambda price, s=side: self.draw_uptrend_threshold_marker_for_side(s, price)
            )
            worker.uptrend_threshold_2_updated.connect(
                lambda price, s=side: self.draw_uptrend_threshold_2_marker_for_side(s, price)
            )

            # Insight 탭 업데이트 (side 전달)
            worker.hedge_triggers_updated.connect(
                lambda triggers, mode, step, s=side: self.update_insight_hedge_triggers(s, triggers, mode, step)
            )
            worker.hedge_slippage_updated.connect(
                lambda idx, slip, s=side: self.update_insight_hedge_slippage(s, idx, slip)
            )
            worker.m_orders_updated.connect(
                lambda m_orders, s=side: self.update_insight_m_orders(s, m_orders)
            )
            worker.profit_target_updated.connect(
                lambda price, step, s=side: self.update_insight_profit_target(s, price, step)
            )
            worker.uptrend_threshold_updated.connect(
                lambda price, s=side: self.update_insight_uptrend_threshold(s, price)
            )
            worker.uptrend_threshold_2_updated.connect(
                lambda price, s=side: self.update_insight_uptrend_threshold_2(s, price)
            )

            # Step 완료 및 경고 (양쪽 모두)
            worker.step_completed.connect(
                lambda step, s=side: self.save_insight_snapshot(s, step)
            )
            worker.hedge_liquidation_warning.connect(
                lambda liq, be, level, s=side: self.update_hedge_liquidation_warning(s, liq, be, level)
            )
            worker.emergency_exit_line_updated.connect(lambda price, s=side: self.draw_emergency_exit_line_marker(price, s))

            # 주문 조정 및 상태 저장
            worker.adjust_next_step_order_signal.connect(lambda order_id, slippage, s=side: self.on_adjust_next_step_order(order_id, slippage, s))
            worker.request_save_state.connect(lambda s=side: self.save_dca_state_for_side(s))
            worker.order_id_received.connect(worker.on_order_id_received)
            worker.hedge_order_id_received.connect(worker.on_hedge_order_id_received)

            # Statistics 탭: 헷지 프로토콜 발동 기록
            worker.hedge_protocol_fired.connect(
                lambda step, pnl, s=side: self.on_hedge_protocol_fired(s, step, pnl)
            )

            # 상승 진입 및 익절 요청
            worker.uptrend_entry_request.connect(lambda order_id, s=side: self.on_uptrend_entry_request(order_id, s))
            worker.profit_taking_request.connect(lambda s=side: self.on_profit_taking_request(s))
            worker.profit_taking_request.connect(lambda s=side: self.increment_cycle_count(s))

            # Stop Loss / Trailing Stop / 헤지 청산
            worker.request_stop_loss.connect(lambda sym, sd, qty, price, s=side: self.on_request_stop_loss(sym, sd, qty, price, s))
            worker.request_trailing_stop.connect(lambda sym, sd, qty, price, rate, s=side: self.on_request_trailing_stop(sym, sd, qty, price, rate, s))
            worker.reduce_hedge_signal.connect(lambda sym, sd, qty, s=side: self.on_reduce_hedge_request(sym, sd, qty, s))

        # 하위 호환성: LONG worker 참조
        self.auto_trade_worker.log_message.connect(self.on_auto_trade_log)

        # 양쪽 워커 스레드 모두 시작 (LONG + SHORT)
        for t in self.auto_trade_threads.values():
            t.start()

        # 로그 파일 초기화
        self.log_file = None
        self.log_file_path = None
        self.initialize_log_file()

        # 프로그램 정상 작동 표시 (하트비트)
        self.heartbeat_active = True  # 초록불 상태
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self.update_heartbeat)
        self.heartbeat_timer.start(1000)  # 1초마다 하트비트 갱신

        # 리소스 라벨 사전 초기화 (initUI 전에 ResourceMonitor가 참조할 수 있으므로)
        self.resource_memory_label = None
        self.resource_cpu_label = None
        self.resource_cleanup_label = None

        # 리소스 모니터링 시스템 초기화
        self.resource_monitor = ResourceMonitor(self)
        self.resource_monitor.memory_warning.connect(self.on_memory_warning)
        self.resource_monitor.cleanup_completed.connect(self.on_cleanup_completed)
        self.resource_monitor.resource_updated.connect(self.on_resource_updated)
        self.resource_monitor.start()

        self.initUI()

        # === v7_dual: 하위 호환성 참조 (기존 코드 호환용) ===
        # Phase 6 완료 전까지 LONG 패널을 기본으로 사용
        self.chart_widget = self.chart_widgets.get('long')
        self.candlestick_item = self.candlestick_items.get('long')
        self.price_line_item = self.price_line_items.get('long')
        self.position_table = self.position_tables.get('long')
        self.order_table = self.order_tables.get('long')
        self.trade_price_label = self.trade_price_labels.get('long')
        self.default_price_label_style = "font-size: 24pt; font-weight: bold; padding: 10px 0;"
        self.balance_label = self.balance_labels.get('long')
        self.time_axis = self.time_axes.get('long')
        self.buttons = self.timeframe_buttons_by_side.get('long', {})
        self.position_lines = self.position_lines_by_side.get('long', {})
        self.order_lines = self.order_lines_by_side.get('long', {})
        self.live_position_data = self.live_position_data_by_side.get('long', {})
        self.live_balances = self.live_balances_by_side.get('long', {})
        self.connect_thread = self.connect_threads.get('long')
        self.ws_thread = self.ws_threads.get('long')
        self.ticker_thread = self.ticker_threads.get('long')
        self.kline_thread = self.kline_threads.get('long')
        self.break_even_line = self.break_even_lines.get('long')
        self.order_step_map = self.order_step_maps.get('long', {})
        self.hedge_trigger_markers = self.hedge_trigger_markers_by_side.get('long', [])
        self.fill_history = self.fill_history_by_side.get('long', [])
        self.chart_visible_button = self.chart_visible_buttons.get('long')
        # y_axis는 chart_widget에서 가져오기
        if self.chart_widget:
            self.y_axis = self.chart_widget.getAxis('left')
            self.chart_viewbox = self.chart_widget.plotItem.vb

        # Chart data (전역 - 향후 side별로 분리 가능)
        self.chart_data_df = None

        self.apply_theme()
        self.load_config_data()

    # ========================================================================
    # v7_dual: 이중 패널 생성 헬퍼 메서드들
    # ========================================================================

    def _create_trading_panel(self, side):
        """
        LONG 또는 SHORT 패널 전체 생성

        Args:
            side: 'long' 또는 'short'

        Returns:
            QWidget: 완전한 trading 패널
            - LONG: 차트 + 테이블 + 컨트롤
            - SHORT: 테이블 + 컨트롤만 (차트 없음)
        """
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        if side == 'long':
            # LONG 패널: 수직 분할 [Chart Section] | [Tables + Controls]
            v_splitter = QSplitter(Qt.Vertical)

            # 상단: Chart Section (차트 + 툴바)
            chart_section = self._create_chart_section(side)
            v_splitter.addWidget(chart_section)

            # 하단: 수평 분할 [Tables] | [Controls]
            bottom_section = QSplitter(Qt.Horizontal)
            tables_widget = self._create_tables_widget(side)
            controls_widget = self._create_control_panel(side)
            bottom_section.addWidget(tables_widget)
            bottom_section.addWidget(controls_widget)
            bottom_section.setSizes([700, 400])  # Tables:Controls = 7:4

            v_splitter.addWidget(bottom_section)
            v_splitter.setSizes([600, 400])  # Chart:Bottom = 6:4

            panel_layout.addWidget(v_splitter)
        else:
            # SHORT 패널: 차트 없이 [Controls] | [Tables]만 표시
            bottom_section = QSplitter(Qt.Horizontal)
            tables_widget = self._create_tables_widget(side)
            controls_widget = self._create_control_panel(side)
            bottom_section.addWidget(controls_widget)
            bottom_section.addWidget(tables_widget)
            bottom_section.setSizes([400, 700])  # Controls:Tables = 4:7

            panel_layout.addWidget(bottom_section)

        return panel

    def _create_chart_section(self, side):
        """
        차트 섹션 생성 (툴바 + 차트 위젯)

        Args:
            side: 'long' 또는 'short'

        Returns:
            QWidget: 차트 섹션
        """
        section = QWidget()
        layout = QVBoxLayout(section)
        layout.setContentsMargins(5, 5, 5, 5)

        # 툴바
        toolbar_layout = QHBoxLayout()

        # Timeframe 버튼들
        buttons_dict = {}
        api_intervals = ["1m", "5m", "30m", "1h", "4h", "1d", "1w"]
        for tf in api_intervals:
            btn = QPushButton(tf)
            btn.clicked.connect(lambda checked, t=tf, s=side: self.change_timeframe_for_side(t, s))
            buttons_dict[tf] = btn
            toolbar_layout.addWidget(btn)

        # Side별로 저장
        if not hasattr(self, 'timeframe_buttons_by_side'):
            self.timeframe_buttons_by_side = {}
        self.timeframe_buttons_by_side[side] = buttons_dict

        toolbar_layout.addStretch(1)

        # Reset View 버튼
        reset_btn = QPushButton("Reset View")
        reset_btn.clicked.connect(lambda: self.reset_chart_view_for_side(side))
        toolbar_layout.addWidget(reset_btn)

        # Lock Mode 버튼
        lock_btn = QPushButton("🔓 Unlock")
        lock_btn.setCheckable(True)
        lock_btn.clicked.connect(lambda: self.toggle_lock_mode_for_side(side))
        toolbar_layout.addWidget(lock_btn)

        if not hasattr(self, 'lock_mode_buttons'):
            self.lock_mode_buttons = {}
        self.lock_mode_buttons[side] = lock_btn

        # Chart ON/OFF 버튼
        chart_visible_btn = QPushButton("📈 Chart ON")
        chart_visible_btn.setCheckable(True)
        chart_visible_btn.setChecked(True)
        chart_visible_btn.clicked.connect(lambda: self.toggle_chart_visibility_for_side(side))
        toolbar_layout.addWidget(chart_visible_btn)

        if not hasattr(self, 'chart_visible_buttons'):
            self.chart_visible_buttons = {}
        self.chart_visible_buttons[side] = chart_visible_btn

        toolbar_layout.addStretch(1)

        # 설정 버튼들 (공유) - 작은 크기
        if side == 'long':  # 첫 번째 패널에만 추가
            # Account 설정 버튼
            account_btn = QPushButton("⚙ Account")
            account_btn.setMaximumWidth(100)
            account_btn.setStyleSheet("font-size: 9pt; padding: 5px;")
            account_btn.clicked.connect(self.on_account_settings_clicked)
            toolbar_layout.addWidget(account_btn)

            # Symbol 설정 버튼
            symbol_btn = QPushButton("📊 Symbol")
            symbol_btn.setMaximumWidth(100)
            symbol_btn.setStyleSheet("font-size: 9pt; padding: 5px;")
            symbol_btn.clicked.connect(self.on_symbol_market_settings_clicked)
            toolbar_layout.addWidget(symbol_btn)

            # Market 설정 버튼
            market_btn = QPushButton("🏪 Market")
            market_btn.setMaximumWidth(100)
            market_btn.setStyleSheet("font-size: 9pt; padding: 5px;")
            market_btn.clicked.connect(self.on_symbol_market_settings_clicked)
            toolbar_layout.addWidget(market_btn)

            # Dark Mode 버튼
            dark_btn = QPushButton("🌙 Dark")
            dark_btn.setCheckable(True)
            dark_btn.setMaximumWidth(80)
            dark_btn.setStyleSheet("font-size: 9pt; padding: 5px;")
            dark_btn.clicked.connect(self.toggle_dark_mode)
            dark_btn.setChecked(self.is_dark_mode)
            toolbar_layout.addWidget(dark_btn)
            self.dark_mode_button = dark_btn

        layout.addLayout(toolbar_layout)

        # Chart Widget 생성
        time_axis = pg.DateAxisItem(orientation='bottom')
        y_axis = CustomAxisItem(orientation='left')
        viewbox = CustomViewBox()
        chart_widget = pg.PlotWidget(viewBox=viewbox, axisItems={'bottom': time_axis, 'left': y_axis})
        viewbox.setMouseEnabled(x=True, y=True)

        # Candlestick Item 생성
        candlestick_item = CandlestickItem(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
        chart_widget.addItem(candlestick_item)

        # Price Line 생성
        price_line = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen('cyan', style=Qt.DashLine, width=1), label='0.00',
            labelOpts={'position': 0.5, 'color': 'cyan', 'movable': True, 'fill': (0, 0, 0, 150), 'anchor': (0.5, 0.5)}
        )
        price_line.hide()
        chart_widget.addItem(price_line, ignoreBounds=True)

        chart_widget.setLabel('left', 'Price')
        chart_widget.setLabel('bottom', 'Time')
        chart_widget.showGrid(x=True, y=True, alpha=0.3)

        # Side별로 저장
        self.chart_widgets[side] = chart_widget
        self.candlestick_items[side] = candlestick_item
        self.price_line_items[side] = price_line
        self.time_axes[side] = time_axis

        # ViewBox 시그널 연결
        viewbox.sigRangeChanged.connect(lambda: self.on_chart_range_changed_for_side(side))

        layout.addWidget(chart_widget)

        # OHLC 오버레이 (차트 내부 좌상단 - pg.TextItem)
        ohlc_text = pg.TextItem(text='', anchor=(0, 0), color='#cccccc')
        ohlc_text.setFont(pg.QtGui.QFont('Consolas', 9))
        ohlc_text.setZValue(1000)  # 다른 아이템 위에 표시
        chart_widget.addItem(ohlc_text, ignoreBounds=True)
        self.ohlc_labels[side] = ohlc_text

        # 뷰 변경 시 OHLC 라벨 위치 고정 (좌상단)
        def _update_ohlc_pos(vb=viewbox, txt=ohlc_text):
            try:
                vr = vb.viewRange()
                txt.setPos(vr[0][0], vr[1][1])
            except:
                pass
        viewbox.sigRangeChanged.connect(_update_ohlc_pos)

        # 크로스헤어 (흰색 점선)
        crosshair_pen = pg.mkPen(color='#888888', style=Qt.DashLine, width=1)
        v_line = pg.InfiniteLine(angle=90, movable=False, pen=crosshair_pen)
        h_line = pg.InfiniteLine(angle=0, movable=False, pen=crosshair_pen)
        v_line.setZValue(999)
        h_line.setZValue(999)
        v_line.hide()
        h_line.hide()
        chart_widget.addItem(v_line, ignoreBounds=True)
        chart_widget.addItem(h_line, ignoreBounds=True)
        self.crosshair_v[side] = v_line
        self.crosshair_h[side] = h_line


        # 마우스 호버 → OHLC 라벨 업데이트 (scene 준비 후 지연 연결)
        def _connect_ohlc_proxy(s=side, cw=chart_widget):
            try:
                scene = cw.scene()
                if scene and hasattr(scene, 'sigMouseMoved'):
                    proxy = pg.SignalProxy(
                        scene.sigMouseMoved,
                        rateLimit=30,
                        slot=lambda evt, _s=s: self._on_chart_mouse_moved(_s, evt)
                    )
                    self._ohlc_proxies[s] = proxy
            except Exception as e:
                print(f"[OHLC Proxy] 연결 실패 ({s}): {e}")
        QTimer.singleShot(500, _connect_ohlc_proxy)

        # 차트 하단 바: LONG/SHORT 라인 토글 버튼
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)

        long_lines_btn = QPushButton("L Lines ON")
        long_lines_btn.setCheckable(True)
        long_lines_btn.setChecked(True)
        long_lines_btn.setMaximumWidth(100)
        long_lines_btn.setStyleSheet("font-size: 8pt; padding: 2px 8px; color: #00b050; font-weight: bold;")
        long_lines_btn.clicked.connect(lambda: self.toggle_lines_for_side('long'))
        bottom_bar.addWidget(long_lines_btn)

        bottom_bar.addStretch(1)

        short_lines_btn = QPushButton("S Lines ON")
        short_lines_btn.setCheckable(True)
        short_lines_btn.setChecked(True)
        short_lines_btn.setMaximumWidth(100)
        short_lines_btn.setStyleSheet("font-size: 8pt; padding: 2px 8px; color: #c00000; font-weight: bold;")
        short_lines_btn.clicked.connect(lambda: self.toggle_lines_for_side('short'))
        bottom_bar.addWidget(short_lines_btn)

        if not hasattr(self, 'toggle_lines_buttons'):
            self.toggle_lines_buttons = {}
        self.toggle_lines_buttons['long'] = long_lines_btn
        self.toggle_lines_buttons['short'] = short_lines_btn

        layout.addLayout(bottom_bar)

        return section

    def _create_tables_widget(self, side):
        """
        Position/Order 테이블 생성

        Args:
            side: 'long' 또는 'short'

        Returns:
            QWidget: 테이블 섹션
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)

        # Position Table
        position_table = QTableWidget()
        position_table.setColumnCount(7)
        position_table.setHorizontalHeaderLabels(["Symbol", "Amount", "Entry Price", "Liq. Price", "PNL", "ROI %", "Close"])
        position_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        position_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        position_table.setColumnWidth(6, 65)
        position_table.verticalHeader().setDefaultSectionSize(26)

        # Order Table
        order_table = QTableWidget()
        order_table.setColumnCount(8)
        order_table.setHorizontalHeaderLabels(["Symbol", "Type", "Side", "Price", "Amount", "Filled", "Cancel", "OrderId"])
        order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        order_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        order_table.setColumnWidth(6, 65)
        order_table.setColumnHidden(7, True)
        order_table.verticalHeader().setDefaultSectionSize(26)

        # Side별로 저장
        if not hasattr(self, 'position_tables'):
            self.position_tables = {}
        if not hasattr(self, 'order_tables'):
            self.order_tables = {}

        self.position_tables[side] = position_table
        self.order_tables[side] = order_table

        layout.addWidget(QLabel(f"포지션 (Positions) - {side.upper()}"))
        layout.addWidget(position_table)
        layout.addWidget(QLabel(f"미체결 주문 (Open Orders) - {side.upper()}"))
        layout.addWidget(order_table)

        # Start/Stop + Clear All 버튼 (가로 배치)
        direction = side.upper()
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)

        # Start/Stop 토글 버튼
        toggle_btn = QPushButton(f"Start {direction}")
        toggle_btn.setMinimumHeight(35)
        toggle_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #00b050; color: white;")
        toggle_btn.clicked.connect(lambda: self.on_auto_trade_toggle_for_side(side))
        self.auto_trade_start_buttons[side] = toggle_btn
        self.auto_trade_stop_buttons[side] = toggle_btn
        btn_layout.addWidget(toggle_btn)

        # Clear All 버튼
        clear_btn = QPushButton(f"Clear All")
        clear_btn.setMinimumHeight(35)
        clear_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #ff6600; color: white;")
        clear_btn.clicked.connect(lambda: self.on_clear_all_for_side(side))
        btn_layout.addWidget(clear_btn)

        layout.addLayout(btn_layout)

        return widget

    def _create_control_panel(self, side):
        """
        제어 패널 생성 (Account/Symbol/Price/Trade/Auto-Trade)

        Args:
            side: 'long' 또는 'short'

        Returns:
            QWidget: 제어 패널
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # === 1. Account 선택 ===
        account_box = QGroupBox(f"{side.upper()} - Account")
        account_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        account_layout = QVBoxLayout(account_box)
        account_layout.setContentsMargins(10, 15, 10, 10)

        account_combo = QComboBox()
        account_combo.setMinimumHeight(35)
        # 임시: 테스트용 아이템 추가
        account_combo.addItem(f"[Loading {side.upper()}...]")
        self.account_combos[side] = account_combo
        account_layout.addWidget(account_combo)

        # Connect 버튼
        connect_btn = QPushButton("Connect")
        connect_btn.setMinimumHeight(35)
        connect_btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #0078d4; color: white;")
        connect_btn.clicked.connect(lambda: self.on_connect_button_clicked(side))
        self.connect_buttons[side] = connect_btn
        account_layout.addWidget(connect_btn)

        # 연결 상태 라벨
        status_label = QLabel("Not connected")
        status_label.setStyleSheet("color: gray; font-size: 9pt;")
        status_label.setAlignment(Qt.AlignCenter)
        self.connection_status_labels[side] = status_label
        account_layout.addWidget(status_label)

        layout.addWidget(account_box)

        # === 2. Symbol & Direction 선택 ===
        symbol_box = QGroupBox("Symbol & Direction")
        symbol_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        symbol_layout = QVBoxLayout(symbol_box)
        symbol_layout.setContentsMargins(10, 15, 10, 10)

        # Symbol 콤보박스
        symbol_combo = QComboBox()
        symbol_combo.setMinimumHeight(35)
        symbol_combo.addItems([
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
            "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "DOTUSDT", "MATICUSDT"
        ])
        symbol_combo.setCurrentText(self.current_symbols.get(side, "BTCUSDT"))
        symbol_combo.currentTextChanged.connect(lambda text, s=side: self.on_symbol_changed_for_side(s, text))
        self.symbol_combos[side] = symbol_combo
        symbol_layout.addWidget(symbol_combo)

        # Direction 콤보박스
        direction_combo = QComboBox()
        direction_combo.setMinimumHeight(35)
        direction_combo.addItems(["LONG", "SHORT"])
        # 저장된 방향이 있으면 사용, 없으면 기본값 (왼쪽=LONG, 오른쪽=SHORT)
        saved_direction = self.side_modes.get(side, "LONG" if side == 'long' else "SHORT")
        direction_combo.setCurrentText(saved_direction)
        direction_combo.currentTextChanged.connect(lambda text, s=side: self.on_direction_changed_for_side(s, text))
        self.direction_combos[side] = direction_combo
        symbol_layout.addWidget(direction_combo)

        # Market Type 콤보박스 (Linear/Inverse)
        market_combo = QComboBox()
        market_combo.setMinimumHeight(35)
        market_combo.addItems(["Linear (USDT)", "Inverse (COIN)"])
        # 기본값: Linear
        saved_market = self.market_type_modes.get(side, 'linear')
        if saved_market in ['linear', 'fapi']:
            market_combo.setCurrentIndex(0)
        else:
            market_combo.setCurrentIndex(1)
        market_combo.currentTextChanged.connect(lambda text, s=side: self.on_market_type_changed_for_side(s, text))
        self.market_type_combos[side] = market_combo
        symbol_layout.addWidget(market_combo)

        layout.addWidget(symbol_box)

        # === 3. Price 표시 ===
        price_box = QGroupBox("Price")
        price_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        price_layout = QVBoxLayout(price_box)
        price_layout.setContentsMargins(10, 15, 10, 10)

        price_label = QLabel("0.00")
        price_label.setStyleSheet("font-size: 24pt; font-weight: bold; padding: 10px 0;")
        price_label.setAlignment(Qt.AlignCenter)
        self.trade_price_labels[side] = price_label
        price_layout.addWidget(price_label)

        layout.addWidget(price_box)

        # === 4. Balance 표시 ===
        balance_box = QGroupBox("Wallet Balance")
        balance_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        balance_layout = QVBoxLayout(balance_box)
        balance_layout.setContentsMargins(10, 15, 10, 10)

        balance_label = QLabel("N/A")
        balance_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        balance_label.setAlignment(Qt.AlignCenter)
        self.balance_labels[side] = balance_label
        balance_layout.addWidget(balance_label)

        layout.addWidget(balance_box)

        # === 5. Auto-Trade Controls (간소화 버전) ===
        auto_box = QGroupBox("Auto-Trade")
        auto_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        auto_layout = QVBoxLayout(auto_box)
        auto_layout.setContentsMargins(10, 15, 10, 10)

        # Status와 Step 레이블
        status_label = QLabel("Status: <b style='color: gray;'>Stopped</b>")
        status_label.setStyleSheet("font-size: 9pt;")
        step_label = QLabel("Step: <b>-</b>")
        step_label.setStyleSheet("font-size: 9pt;")
        self.auto_trade_status_labels[side] = status_label
        self.auto_trade_step_labels[side] = step_label
        auto_layout.addWidget(status_label)
        auto_layout.addWidget(step_label)

        # Start/Stop 버튼 (방향에 따라 동적으로 텍스트 설정)
        direction = self.side_modes.get(side, "LONG" if side == 'long' else "SHORT")

        start_btn = QPushButton(f"Start {direction}")
        start_btn.setMinimumHeight(40)
        start_btn.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #00b050; color: white;")
        start_btn.clicked.connect(lambda: self.on_auto_trade_start_for_side(side))
        self.auto_trade_start_buttons[side] = start_btn
        auto_layout.addWidget(start_btn)

        stop_btn = QPushButton(f"Stop {direction}")
        stop_btn.setMinimumHeight(40)
        stop_btn.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #c00000; color: white;")
        stop_btn.clicked.connect(lambda: self.on_auto_trade_stop_for_side(side))
        self.auto_trade_stop_buttons[side] = stop_btn
        auto_layout.addWidget(stop_btn)

        # Clear All 버튼 (포지션 청산 + 미체결 주문 취소)
        clear_btn = QPushButton(f"Clear All {direction}")
        clear_btn.setMinimumHeight(35)
        clear_btn.setStyleSheet("font-size: 10pt; font-weight: bold; background-color: #ff6600; color: white;")
        clear_btn.clicked.connect(lambda: self.on_clear_all_for_side(side))
        auto_layout.addWidget(clear_btn)

        layout.addWidget(auto_box)

        layout.addStretch()
        return widget

    def _create_unified_control_panel(self):
        """
        통합 제어 패널 생성 (Price/Balance LONG|SHORT/Trade LONG|SHORT)

        Returns:
            QWidget: 통합 제어 패널
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # 연결 상태 라벨 초기화 (다른 곳에서 참조되므로)
        long_status_label = QLabel("LONG: Not connected")
        long_status_label.setStyleSheet("color: gray; font-size: 0pt;")  # 숨김
        long_status_label.setVisible(False)
        self.connection_status_labels['long'] = long_status_label

        short_status_label = QLabel("SHORT: Not connected")
        short_status_label.setStyleSheet("color: gray; font-size: 0pt;")  # 숨김
        short_status_label.setVisible(False)
        self.connection_status_labels['short'] = short_status_label

        # === 1. Price 표시 (통합) ===
        price_box = QGroupBox("Price")
        price_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        price_layout = QVBoxLayout(price_box)
        price_layout.setContentsMargins(10, 15, 10, 10)

        price_label = QLabel("0.00")
        price_label.setStyleSheet("font-size: 24pt; font-weight: bold; padding: 10px 0;")
        price_label.setAlignment(Qt.AlignCenter)
        self.trade_price_labels['long'] = price_label
        self.trade_price_labels['short'] = price_label  # 동일한 라벨 공유
        price_layout.addWidget(price_label)

        layout.addWidget(price_box)

        # === 2. Auto-Trade Controls (LONG 왼쪽 / SHORT 오른쪽) ===
        auto_box = QGroupBox("Auto-Trade")
        auto_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        auto_h_layout = QHBoxLayout(auto_box)
        auto_h_layout.setContentsMargins(10, 15, 10, 10)

        # LONG (왼쪽)
        long_auto_layout = QVBoxLayout()
        long_status_label = QLabel("LONG: <b style='color: gray;'>Stopped</b>")
        long_status_label.setStyleSheet("font-size: 9pt;")
        long_step_label = QLabel("Step: <b>-</b>")
        long_step_label.setStyleSheet("font-size: 9pt;")
        self.auto_trade_status_labels['long'] = long_status_label
        self.auto_trade_step_labels['long'] = long_step_label
        long_auto_layout.addWidget(long_status_label)
        long_auto_layout.addWidget(long_step_label)
        auto_h_layout.addLayout(long_auto_layout)

        # SHORT (오른쪽)
        short_auto_layout = QVBoxLayout()
        short_status_label = QLabel("SHORT: <b style='color: gray;'>Stopped</b>")
        short_status_label.setStyleSheet("font-size: 9pt;")
        short_step_label = QLabel("Step: <b>-</b>")
        short_step_label.setStyleSheet("font-size: 9pt;")
        self.auto_trade_status_labels['short'] = short_status_label
        self.auto_trade_step_labels['short'] = short_step_label
        short_auto_layout.addWidget(short_status_label)
        short_auto_layout.addWidget(short_step_label)
        auto_h_layout.addLayout(short_auto_layout)

        layout.addWidget(auto_box)

        # === 3. Realized PNL 표시 (LONG | TOTAL | SHORT) ===
        pnl_box = QGroupBox("Realized PnL")
        pnl_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        pnl_layout = QVBoxLayout(pnl_box)
        pnl_layout.setContentsMargins(10, 15, 10, 10)
        pnl_layout.setSpacing(4)

        # TOTAL PNL (상단 중앙)
        total_pnl_label = QLabel("TOTAL: 0.00")
        total_pnl_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #888888;")
        total_pnl_label.setAlignment(Qt.AlignCenter)
        self.realized_pnl_labels['total'] = total_pnl_label
        pnl_layout.addWidget(total_pnl_label)

        # LONG | SHORT PNL (가로 배열)
        pnl_h_layout = QHBoxLayout()
        long_pnl_label = QLabel("L: 0.00")
        long_pnl_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #888888;")
        long_pnl_label.setAlignment(Qt.AlignCenter)
        self.realized_pnl_labels['long'] = long_pnl_label

        short_pnl_label = QLabel("S: 0.00")
        short_pnl_label.setStyleSheet("font-size: 10pt; font-weight: bold; color: #888888;")
        short_pnl_label.setAlignment(Qt.AlignCenter)
        self.realized_pnl_labels['short'] = short_pnl_label

        pnl_h_layout.addWidget(long_pnl_label)
        pnl_h_layout.addWidget(short_pnl_label)
        pnl_layout.addLayout(pnl_h_layout)

        # 사이클 카운트 (PNL 박스 내부 하단)
        cycle_h_layout = QHBoxLayout()
        long_cycle_label = QLabel("L: Cycle 0")
        long_cycle_label.setStyleSheet("font-size: 9pt; color: #AAAAAA;")
        long_cycle_label.setAlignment(Qt.AlignCenter)
        self.cycle_count_labels['long'] = long_cycle_label

        short_cycle_label = QLabel("S: Cycle 0")
        short_cycle_label.setStyleSheet("font-size: 9pt; color: #AAAAAA;")
        short_cycle_label.setAlignment(Qt.AlignCenter)
        self.cycle_count_labels['short'] = short_cycle_label

        cycle_h_layout.addWidget(long_cycle_label)
        cycle_h_layout.addWidget(short_cycle_label)
        pnl_layout.addLayout(cycle_h_layout)

        layout.addWidget(pnl_box)

        # === 4. Wallet Balance 표시 (LONG/SHORT 분리) ===
        balance_box = QGroupBox("Wallet Balance")
        balance_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        balance_layout = QVBoxLayout(balance_box)
        balance_layout.setContentsMargins(10, 15, 10, 10)

        long_balance_label = QLabel("LONG: N/A")
        long_balance_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        long_balance_label.setAlignment(Qt.AlignCenter)
        self.balance_labels['long'] = long_balance_label
        balance_layout.addWidget(long_balance_label)

        short_balance_label = QLabel("SHORT: N/A")
        short_balance_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        short_balance_label.setAlignment(Qt.AlignCenter)
        self.balance_labels['short'] = short_balance_label
        balance_layout.addWidget(short_balance_label)

        self.reserve_labels = {'long': None, 'short': None}
        
        long_reserve_label = QLabel("Long Reserve: N/A")
        long_reserve_label.setStyleSheet("font-size: 10pt; color: #BBBBBB;")
        long_reserve_label.setAlignment(Qt.AlignCenter)
        self.reserve_labels['long'] = long_reserve_label
        balance_layout.addWidget(long_reserve_label)

        short_reserve_label = QLabel("Short Reserve: N/A")
        short_reserve_label.setStyleSheet("font-size: 10pt; color: #BBBBBB;")
        short_reserve_label.setAlignment(Qt.AlignCenter)
        self.reserve_labels['short'] = short_reserve_label
        balance_layout.addWidget(short_reserve_label)

        equal_balance_btn = QPushButton("Equal Balance")
        equal_balance_btn.setMinimumHeight(28)
        equal_balance_btn.setStyleSheet("font-size: 9pt; font-weight: bold; background-color: #FF8C00; color: white;")
        equal_balance_btn.clicked.connect(self.on_equal_balance_clicked)
        balance_layout.addWidget(equal_balance_btn)

        layout.addWidget(balance_box)

        # === Watchdog & Reserve 슬라이드 토글 (Balance 섹션 밖) ===
        toggle_layout = QHBoxLayout()
        
        watchdog_enabled = self.config_data.get("app_settings", {}).get("watchdog_enabled", False)
        self.watchdog_toggle = SlideToggle("Watchdog (크래시 자동 재시작)", checked=watchdog_enabled)
        self.watchdog_toggle.toggled.connect(self._on_watchdog_toggled)
        toggle_layout.addWidget(self.watchdog_toggle)
        
        reserve_enabled = self.config_data.get("app_settings", {}).get("reserve_enabled", True)
        self.reserve_toggle = SlideToggle("Reserve (비축금)", checked=reserve_enabled)
        self.reserve_toggle.toggled.connect(self._on_reserve_toggled)
        toggle_layout.addWidget(self.reserve_toggle)
        
        toggle_layout.addStretch()
        layout.addLayout(toggle_layout)

        # === 5. Auto-Trade Control 속성 초기화 (UI 비표시, 코드 호환용) ===
        market_display = "USDT" if self.auto_trade_market_mode == "linear" else "COIN"
        self.auto_trade_market_toggle = QPushButton(f"Market: {market_display}")
        self.auto_trade_market_toggle.setVisible(False)
        self.auto_trade_side_toggle = QPushButton(f"Side: {self.auto_trade_side_mode.upper()}")
        self.auto_trade_side_toggle.setVisible(False)
        self.auto_trade_schedule_stop_button = QPushButton("Schedule Stop")
        self.auto_trade_schedule_stop_button.setVisible(False)

        layout.addStretch()
        return widget

    def _set_side_button_running(self, side=None):
        """side별 토글 버튼을 'Stop' 상태로 변경"""
        if side is None:
            side = self.auto_trade_side_mode.lower()
        btn = self.auto_trade_start_buttons.get(side)
        if btn:
            btn.setText(f"Stop {side.upper()}")
            btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #c00000; color: white;")

    def _set_side_button_stopped(self, side=None):
        """side별 토글 버튼을 'Start' 상태로 변경"""
        if side is None:
            side = self.auto_trade_side_mode.lower()
        btn = self.auto_trade_start_buttons.get(side)
        if btn:
            btn.setText(f"Start {side.upper()}")
            btn.setStyleSheet("font-size: 11pt; font-weight: bold; background-color: #00b050; color: white;")

    def on_unified_symbol_changed(self, text):
        """통합 심볼 변경 - LONG과 SHORT 모두에 적용"""
        self.on_symbol_changed_for_side('long', text)
        self.on_symbol_changed_for_side('short', text)

    def on_unified_market_type_changed(self, text):
        """통합 마켓 타입 변경 - LONG과 SHORT 모두에 적용"""
        self.on_market_type_changed_for_side('long', text)
        self.on_market_type_changed_for_side('short', text)

    def on_auto_trade_toggle_for_side(self, side):
        """Auto-Trade 토글 (Start ↔ Stop)"""
        worker = self.auto_trade_workers.get(side)
        if not worker:
            return

        # Worker가 실행 중이면 Stop, 아니면 Start
        if worker.is_running:
            self.on_auto_trade_stop_for_side(side)
        else:
            self.on_auto_trade_start_for_side(side)

    def _on_watchdog_toggled(self, state):
        """Watchdog 토글 변경"""
        enabled = bool(state)
        # config 저장
        if "app_settings" not in self.config_data:
            self.config_data["app_settings"] = {}
        self.config_data["app_settings"]["watchdog_enabled"] = enabled
        config_manager.save_config_data(self.config_data)

        if enabled:
            self._start_watchdog_daemon()
            print("[Watchdog] 활성화 - 크래시 발생 시 자동 재시작됩니다.")
        else:
            self._stop_watchdog_daemon()
            print("[Watchdog] 비활성화")

    def _on_reserve_toggled(self, state):
        """Reserve 토글 변경"""
        enabled = bool(state)
        if "app_settings" not in self.config_data:
            self.config_data["app_settings"] = {}
        self.config_data["app_settings"]["reserve_enabled"] = enabled
        config_manager.save_config_data(self.config_data)

        if enabled:
            print("[Reserve] 활성화 - 비축금 적립 및 투입 기능이 켜졌습니다.")
        else:
            print("[Reserve] 비활성화 - 비축금 관련 기능이 중지됩니다.")

    def _start_watchdog_daemon(self):
        """와치독 데몬 프로세스 시작"""
        if self.watchdog_process and self.watchdog_process.poll() is None:
            return  # 이미 실행 중

        import subprocess
        is_frozen = getattr(sys, 'frozen', False)
        my_pid = os.getpid()

        if is_frozen:
            cmd = [sys.executable, "--watchdog-daemon", str(my_pid)]
        else:
            script_path = os.path.abspath(sys.argv[0])
            cmd = [sys.executable, script_path, "--watchdog-daemon", str(my_pid)]

        try:
            self.watchdog_process = subprocess.Popen(
                cmd,
                cwd=os.path.dirname(os.path.abspath(sys.argv[0])),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
            print(f"[Watchdog] 데몬 시작 (PID: {self.watchdog_process.pid}, 감시 대상: {my_pid})")
        except Exception as e:
            print(f"[Watchdog] 데몬 시작 실패: {e}")

    def _stop_watchdog_daemon(self):
        """와치독 데몬 프로세스 종료"""
        if self.watchdog_process and self.watchdog_process.poll() is None:
            try:
                self.watchdog_process.terminate()
                self.watchdog_process.wait(timeout=5)
                print("[Watchdog] 데몬 종료 완료")
            except:
                try:
                    self.watchdog_process.kill()
                except:
                    pass
        self.watchdog_process = None

    def on_equal_balance_clicked(self):
        """Equal Balance 버튼 클릭 - 잔액 균등화 다이얼로그 표시"""
        if not self.accounts:
            QMessageBox.warning(self, "Error", "등록된 계정이 없습니다.")
            return
        dialog = EqualBalanceDialog(self.accounts, self)
        dialog.exec_()
        # 다이얼로그에서 Auto Balance 체크박스 변경했을 수 있으므로 config 재로드
        self.config_data = config_manager.load_config_data()
        self.auto_balance_enabled = self.config_data.get("app_settings", {}).get("auto_balance_enabled", False)

    def on_account_settings_clicked(self):
        """Account Settings 버튼 클릭 - 팝업 다이얼로그 표시"""
        current_long = self.current_account_names.get('long')
        current_short = self.current_account_names.get('short')

        self.account_settings_dialog = AccountSettingsDialog(self.accounts, current_long, current_short, self)

        # 다이얼로그 열릴 때 현재 연결 상태 반영
        self._update_account_dialog_status('long')
        self._update_account_dialog_status('short')

        # 다이얼로그에서 선택한 계정을 업데이트
        if self.account_settings_dialog.exec_() == QDialog.Accepted:
            # 선택된 계정 정보 저장
            if self.account_settings_dialog.selected_long_account:
                self.current_account_names['long'] = self.account_settings_dialog.selected_long_account
            if self.account_settings_dialog.selected_short_account:
                self.current_account_names['short'] = self.account_settings_dialog.selected_short_account

        # 다이얼로그 참조 해제
        self.account_settings_dialog = None

    def _update_account_dialog_status(self, side):
        """Account Settings 다이얼로그의 연결 상태 라벨 업데이트"""
        if not hasattr(self, 'account_settings_dialog') or not self.account_settings_dialog:
            return

        # API 연결 상태 확인
        api_module = self.api_modules.get(side)
        is_connected = api_module and api_module.is_api_key_active()

        # 다이얼로그의 상태 라벨 가져오기
        if side == 'long':
            status_label = self.account_settings_dialog.long_status_label
        else:
            status_label = self.account_settings_dialog.short_status_label

        if is_connected:
            account_name = self.current_account_names.get(side, 'Unknown')
            status_label.setText(f"✅ Connected to {account_name}")
            status_label.setStyleSheet("color: green; font-size: 9pt;")
        else:
            status_label.setText("Not connected")
            status_label.setStyleSheet("color: gray; font-size: 9pt;")

    def on_symbol_market_settings_clicked(self):
        """Symbol & Market Settings 버튼 클릭 - 팝업 다이얼로그 표시"""
        current_symbol = self.current_symbols.get('long', 'BTCUSDT')
        current_market = self.market_type_modes.get('long', 'linear')

        dialog = SymbolMarketSettingsDialog(current_symbol, current_market, self)

        if dialog.exec_() == QDialog.Accepted:
            # 선택된 설정 적용
            new_symbol = dialog.selected_symbol
            new_market = dialog.selected_market

            # Symbol 변경
            short_symbol = self.current_symbols.get('short', 'BTCUSDT')
            if new_symbol != current_symbol or new_symbol != short_symbol:
                self.on_unified_symbol_changed(new_symbol)
                self.current_symbols['long'] = new_symbol
                self.current_symbols['short'] = new_symbol
                print(f"Symbol 변경: {new_symbol}")

            # Market Type 변경
            if new_market != current_market:
                market_text = "Linear (USDT)" if new_market == "linear" else "Inverse (COIN)"
                self.on_unified_market_type_changed(market_text)
                self.market_type_modes['long'] = new_market
                self.market_type_modes['short'] = new_market
                print(f"Market 변경: {market_text}")

    # Placeholder 메서드들 (Phase 5-6에서 구현)
    def change_timeframe_for_side(self, interval, side):
        print(f"[TODO] change_timeframe_for_side: {interval}, {side}")

    def reset_chart_view_for_side(self, side):
        """차트 뷰를 자동 범위로 리셋 (side별 Reset View 버튼)"""
        # 현재는 공유 차트이므로 기존 로직 호출
        self.reset_chart_view()

    def toggle_lock_mode_for_side(self, side):
        """Lock Mode 토글 (side별 Lock 버튼)"""
        btn = self.lock_mode_buttons.get(side)
        if btn:
            checked = btn.isChecked()
            # 다른 side의 버튼도 동기화
            for s, b in self.lock_mode_buttons.items():
                if s != side:
                    b.blockSignals(True)
                    b.setChecked(checked)
                    b.blockSignals(False)
            self.toggle_lock_mode(checked)

    def toggle_chart_visibility_for_side(self, side):
        print(f"[TODO] toggle_chart_visibility_for_side: {side}")

    def on_chart_range_changed_for_side(self, side):
        """ViewBox 범위 변경 시 호출 - 기존 on_chart_range_changed 위임"""
        self.on_chart_range_changed()

    def _hide_crosshair_if_outside(self):
        """마우스가 차트 밖이면 크로스헤어 숨김"""
        from PyQt5.QtGui import QCursor
        cursor_pos = QCursor.pos()
        for side in ['long', 'short']:
            chart = self.chart_widgets.get(side)
            if chart is None:
                continue
            # 글로벌 커서 위치가 차트 위젯 영역 안에 있는지 확인
            local_pos = chart.mapFromGlobal(cursor_pos)
            if not chart.rect().contains(local_pos):
                v_line = self.crosshair_v.get(side)
                h_line = self.crosshair_h.get(side)
                if v_line:
                    v_line.hide()
                if h_line:
                    h_line.hide()

    def _on_chart_mouse_moved(self, side, evt):
        """차트 마우스 이동 → 크로스헤어 + OHLC 라벨 업데이트"""
        pos = evt[0]  # QPointF
        chart = self.chart_widgets.get(side)
        if chart is None:
            return
        vb = chart.plotItem.vb
        if chart.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            # 크로스헤어 표시 및 위치 업데이트
            v_line = self.crosshair_v.get(side)
            h_line = self.crosshair_h.get(side)
            if v_line:
                v_line.setPos(mouse_point.x())
                v_line.show()
            if h_line:
                h_line.setPos(mouse_point.y())
                h_line.show()
            self._update_ohlc_label(side, mouse_point.x())
        # 타이머로 마우스 이탈 체크 (sigMouseMoved가 멈추면 실행)
        if self._crosshair_hide_timer:
            self._crosshair_hide_timer.stop()
        self._crosshair_hide_timer = QTimer()
        self._crosshair_hide_timer.setSingleShot(True)
        self._crosshair_hide_timer.timeout.connect(self._hide_crosshair_if_outside)
        self._crosshair_hide_timer.start(150)

    def _update_ohlc_label(self, side, x_timestamp):
        """마우스 X좌표(timestamp)에 해당하는 캔들의 OHLC를 TextItem에 표시"""
        text_item = self.ohlc_labels.get(side)
        if not text_item:
            return
        candle_item = self.candlestick_items.get(side)
        if candle_item is None or candle_item.data is None or candle_item.data.empty:
            return
        df = candle_item.data
        idx = (df['time'] - x_timestamp).abs().idxmin()
        row = df.loc[idx]
        precision = self.price_precisions.get(side, 2)
        dt_str = datetime.fromtimestamp(row['time']).strftime("%Y-%m-%d %H:%M")
        o, h, l, c = row['open'], row['high'], row['low'], row['close']
        color = '#00b050' if c >= o else '#c00000'
        text_item.setColor(color)
        text_item.setText(
            f"O: {o:.{precision}f}  H: {h:.{precision}f}  "
            f"L: {l:.{precision}f}  C: {c:.{precision}f}  | {dt_str}"
        )
        # 위치 재조정 (좌상단 고정)
        chart = self.chart_widgets.get(side)
        if chart:
            vr = chart.plotItem.vb.viewRange()
            text_item.setPos(vr[0][0], vr[1][1])

    # ========================================================================
    # End of v7_dual helper methods
    # ========================================================================

    def _create_statistics_column(self, side):
        """Statistics 탭의 한쪽 칼럼(LONG 또는 SHORT) UI를 생성합니다."""
        side_label = "[L] LONG" if side == 'long' else "[S] SHORT"
        total_steps = self.strategy_settings.get("STEPS", 10)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)

        # 타이틀 + Reset 버튼
        header = QHBoxLayout()
        title = QLabel(f"<h2>{side_label}</h2>")
        header.addWidget(title)
        header.addStretch()
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(lambda: self.reset_statistics(side))
        header.addWidget(reset_btn)
        layout.addLayout(header)

        # 테이블
        from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        table = QTableWidget()
        table.setColumnCount(7)
        table.setHorizontalHeaderLabels(["Step", "사이클 종료", "헷지 프로토콜", "헷지 익절 누적손익%", "헷지 익절 평균손익%", "누적 손익%", "평균 손익%"])
        table.setRowCount(total_steps)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionMode(QTableWidget.NoSelection)
        table.setAlternatingRowColors(True)
        table.setStyleSheet("""
            QTableWidget { gridline-color: #555; font-size: 9pt; }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section { background-color: #333; color: white; padding: 4px; border: 1px solid #555; font-weight: bold; }
        """)

        # 컬럼 너비 설정
        h = table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.Fixed)
        table.setColumnWidth(0, 50)
        for col in range(1, 7):
            h.setSectionResizeMode(col, QHeaderView.Stretch)

        # 초기 행 세팅
        for row in range(total_steps):
            table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            for col in range(1, 7):
                table.setItem(row, col, QTableWidgetItem("0" if col <= 2 else "-"))

        layout.addWidget(table)

        self.statistics_widgets[side] = {'table': table, 'total_steps': total_steps}
        self._init_statistics_data(side, total_steps)
        return container

    def _init_statistics_data(self, side, total_steps):
        """Statistics 데이터 초기화 (기존 데이터가 없거나 step 수가 다를 때)"""
        current = self.statistics_data.get(side, [])
        # 기존 데이터에 hedge_tp_pcts 필드 없으면 추가 (하위 호환)
        for d in current:
            if 'hedge_tp_pcts' not in d:
                d['hedge_tp_pcts'] = []
        if len(current) == total_steps:
            return  # 이미 올바른 크기
        if len(current) < total_steps:
            for _ in range(total_steps - len(current)):
                current.append({'hedge_protocol_count': 0, 'cycle_end_count': 0, 'profit_pcts': [], 'hedge_tp_pcts': []})
        else:
            current = current[:total_steps]
        self.statistics_data[side] = current

    def _create_insight_column(self, side):
        """Insight 탭의 한쪽 칼럼(LONG 또는 SHORT) UI를 생성합니다."""
        w = self.insight_widgets[side]
        side_label = "[L] LONG" if side == 'long' else "[S] SHORT"
        total_steps = self.strategy_settings.get("STEPS", 10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # ===== 사이드 헤더 =====
        header = QLabel(f"<b>{side_label}</b>")
        header.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 4px 0;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        # ===== Step History 드롭다운 =====
        history_layout = QHBoxLayout()
        history_layout.setSpacing(8)
        history_label = QLabel("History:")
        history_label.setStyleSheet("font-size: 9pt; font-weight: bold;")
        combo = QComboBox()
        combo.setStyleSheet("font-size: 9pt; padding: 3px;")
        combo.addItem("📊 Current (Live)")
        combo.currentIndexChanged.connect(lambda idx, s=side: self.on_insight_history_changed(s, idx))
        w['history_combo'] = combo
        history_layout.addWidget(history_label)
        history_layout.addWidget(combo, 1)
        layout.addLayout(history_layout)

        # ===== Step + Price (가로) =====
        sp_layout = QHBoxLayout()
        sp_layout.setSpacing(6)

        step_box = QGroupBox("Step")
        step_box.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        sl = QVBoxLayout(step_box)
        sl.setContentsMargins(6, 12, 6, 6)
        step_lbl = QLabel(f"0/{total_steps}")
        step_lbl.setStyleSheet("font-size: 20pt; font-weight: bold; padding: 6px 0;")
        step_lbl.setAlignment(Qt.AlignCenter)
        sl.addWidget(step_lbl)
        w['current_step'] = step_lbl
        sp_layout.addWidget(step_box, 1)

        price_box = QGroupBox("Price")
        price_box.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        pl = QVBoxLayout(price_box)
        pl.setContentsMargins(6, 12, 6, 6)
        price_lbl = QLabel("0.00")
        price_lbl.setStyleSheet("font-size: 20pt; font-weight: bold; padding: 6px 0;")
        price_lbl.setAlignment(Qt.AlignCenter)
        pl.addWidget(price_lbl)
        w['current_price'] = price_lbl
        sp_layout.addWidget(price_box, 1)

        layout.addLayout(sp_layout)

        # ===== Uptrend Entry + Profit Target (가로) =====
        up_layout = QHBoxLayout()
        up_layout.setSpacing(6)

        # Uptrend Entry
        uptrend_group = QGroupBox("Uptrend Entry")
        uptrend_group.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        ut_layout = QVBoxLayout(uptrend_group)
        ut_layout.setContentsMargins(6, 12, 6, 6)
        ut_layout.setSpacing(4)
        ut_form = QFormLayout()
        ut_form.setSpacing(3)

        for key, label_text in [
            ('uptrend_threshold_price', 'Threshold:'),
            ('uptrend_distance', 'Distance:'),
            ('uptrend_status', 'Status:'),
            ('uptrend_threshold_price_2', 'Threshold 2:'),
            ('uptrend_distance_2', 'Distance 2:'),
            ('uptrend_status_2', 'Status 2:'),
        ]:
            lbl = QLabel("N/A")
            lbl.setStyleSheet("font-size: 9pt;")
            w[key] = lbl
            ut_form.addRow(label_text, lbl)

        ut_layout.addLayout(ut_form)
        up_layout.addWidget(uptrend_group)

        # Profit Target
        profit_group = QGroupBox("Profit Target")
        profit_group.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        pt_layout = QVBoxLayout(profit_group)
        pt_layout.setContentsMargins(6, 12, 6, 6)
        pt_layout.setSpacing(4)
        pt_form = QFormLayout()
        pt_form.setSpacing(3)

        for key, label_text in [
            ('profit_target_price', 'Target Price:'),
            ('profit_distance', 'Distance:'),
            ('profit_target_status', 'Status:'),
        ]:
            lbl = QLabel("N/A")
            lbl.setStyleSheet("font-size: 9pt;")
            w[key] = lbl
            pt_form.addRow(label_text, lbl)

        pt_layout.addLayout(pt_form)
        up_layout.addWidget(profit_group)

        layout.addLayout(up_layout)

        # ===== Hedge Liquidation Protection =====
        hliq_group = QGroupBox("Hedge Liq Protection")
        hliq_group.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        hliq_layout = QVBoxLayout(hliq_group)
        hliq_layout.setContentsMargins(6, 12, 6, 6)
        hliq_layout.setSpacing(4)
        hliq_form = QFormLayout()
        hliq_form.setSpacing(3)

        for key, label_text in [
            ('hedge_liq_price', 'Hedge Liq Price:'),
            ('hedge_liq_distance', 'Distance:'),
            ('hedge_liq_status', 'Status:'),
        ]:
            lbl = QLabel("N/A")
            lbl.setStyleSheet("font-size: 9pt;")
            w[key] = lbl
            hliq_form.addRow(label_text, lbl)

        hliq_layout.addLayout(hliq_form)
        layout.addWidget(hliq_group)

        # ===== Main Position =====
        main_group = QGroupBox("Main Position")
        main_group.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        main_layout = QVBoxLayout(main_group)
        main_layout.setContentsMargins(6, 12, 6, 6)
        main_layout.setSpacing(4)

        main_form = QFormLayout()
        main_form.setSpacing(3)
        for key, label_text in [
            ('main_entry_price', 'Entry Price:'),
            ('main_quantity', 'Quantity:'),
            ('main_avg_price', 'Avg Price:'),
            ('main_unrealized_pnl', 'Unrealized PnL:'),
        ]:
            lbl = QLabel("N/A")
            lbl.setStyleSheet("font-size: 9pt;")
            w[key] = lbl
            main_form.addRow(label_text, lbl)
        main_layout.addLayout(main_form)

        # 구분선
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(sep1)

        # Next Step Order (NSO)
        m_title = QLabel("<b>Next Step Order</b>")
        m_title.setStyleSheet("font-size: 9pt;")
        main_layout.addWidget(m_title)

        w['m_order_labels'] = []
        m_frame = QFrame()
        m_frame.setFrameStyle(QFrame.NoFrame)
        mfl = QVBoxLayout()
        mfl.setSpacing(2)
        mfl.setContentsMargins(4, 4, 4, 4)

        t_lbl = QLabel("<b>NSO (Limit)</b>")
        t_lbl.setStyleSheet("font-size: 8pt;")
        mfl.addWidget(t_lbl)

        row1 = QHBoxLayout()
        row1.setSpacing(6)
        m_price = QLabel("N/A")
        m_price.setStyleSheet("font-size: 8pt;")
        m_qty = QLabel("N/A")
        m_qty.setStyleSheet("font-size: 8pt;")
        row1.addWidget(QLabel("Price:"))
        row1.addWidget(m_price, 1)
        row1.addWidget(QLabel("Qty:"))
        row1.addWidget(m_qty, 1)
        mfl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(6)
        m_slip = QLabel("N/A")
        m_slip.setStyleSheet("font-size: 8pt;")
        m_status = QLabel("Waiting")
        m_status.setStyleSheet("font-size: 8pt;")
        row2.addWidget(QLabel("Slip:"))
        row2.addWidget(m_slip, 1)
        row2.addWidget(QLabel("Status:"))
        row2.addWidget(m_status, 1)
        mfl.addLayout(row2)

        m_frame.setLayout(mfl)
        main_layout.addWidget(m_frame)
        w['m_order_labels'].append({
            'price': m_price, 'qty': m_qty,
            'slippage': m_slip, 'status': m_status
        })

        main_layout.addStretch()
        layout.addWidget(main_group)

        # ===== Hedge Position =====
        hedge_group = QGroupBox("Hedge Position")
        hedge_group.setStyleSheet("QGroupBox { font-size: 10pt; font-weight: bold; }")
        hedge_layout = QVBoxLayout(hedge_group)
        hedge_layout.setContentsMargins(6, 12, 6, 6)
        hedge_layout.setSpacing(4)

        hedge_form = QFormLayout()
        hedge_form.setSpacing(3)
        for key, label_text in [
            ('hedge_entry_price', 'Entry Price:'),
            ('hedge_quantity', 'Quantity:'),
            ('hedge_avg_price', 'Avg Price:'),
            ('hedge_unrealized_pnl', 'Unrealized PnL:'),
        ]:
            lbl = QLabel("N/A")
            lbl.setStyleSheet("font-size: 9pt;")
            w[key] = lbl
            hedge_form.addRow(label_text, lbl)
        hedge_layout.addLayout(hedge_form)

        # 구분선
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setFrameShadow(QFrame.Sunken)
        hedge_layout.addWidget(sep2)

        # Hedge Triggers (4개)
        ht_title = QLabel("<b>Hedge Triggers</b>")
        ht_title.setStyleSheet("font-size: 9pt;")
        hedge_layout.addWidget(ht_title)

        w['hedge_labels'] = []
        for i in range(4):
            h_frame = QFrame()
            h_frame.setFrameStyle(QFrame.NoFrame)
            hfl = QVBoxLayout()
            hfl.setSpacing(2)
            hfl.setContentsMargins(4, 4, 4, 4)

            t_lbl = QLabel(f"<b>Trigger {i+1}</b>")
            t_lbl.setStyleSheet("font-size: 8pt;")
            hfl.addWidget(t_lbl)

            row1 = QHBoxLayout()
            row1.setSpacing(6)
            h_price = QLabel("N/A")
            h_price.setStyleSheet("font-size: 8pt;")
            h_qty = QLabel("N/A")
            h_qty.setStyleSheet("font-size: 8pt;")
            row1.addWidget(QLabel("Price:"))
            row1.addWidget(h_price, 1)
            row1.addWidget(QLabel("Qty:"))
            row1.addWidget(h_qty, 1)
            hfl.addLayout(row1)

            row2 = QHBoxLayout()
            row2.setSpacing(6)
            h_slip = QLabel("N/A")
            h_slip.setStyleSheet("font-size: 8pt;")
            h_status = QLabel("Waiting")
            h_status.setStyleSheet("font-size: 8pt;")
            row2.addWidget(QLabel("Slip:"))
            row2.addWidget(h_slip, 1)
            row2.addWidget(QLabel("Status:"))
            row2.addWidget(h_status, 1)
            hfl.addLayout(row2)

            h_frame.setLayout(hfl)
            hedge_layout.addWidget(h_frame)
            w['hedge_labels'].append({
                'price': h_price, 'qty': h_qty,
                'slippage': h_slip, 'status': h_status
            })

        hedge_layout.addStretch()
        layout.addWidget(hedge_group)

        layout.addStretch()
        scroll.setWidget(content)
        return scroll

    def initUI(self):
        self.setWindowTitle("v7_dual DCA Trader (LONG + SHORT)")
        self.setGeometry(100, 100, 1800, 1000)  # 더 넓은 기본 크기
        pg.setConfigOptions(antialias=True)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.chart_tab = QWidget()
        self.tabs.addTab(self.chart_tab, "📊 Chart (Dual)")
        self.insight_tab = QWidget()
        self.tabs.addTab(self.insight_tab, "📈 Insight")
        self.statistics_tab = QWidget()
        self.tabs.addTab(self.statistics_tab, "📊 Statistics")

        self.log_tab = QWidget()
        self.tabs.addTab(self.log_tab, "📋 Log")
        self.accounts_tab = QWidget()
        self.tabs.addTab(self.accounts_tab, "👤 Accounts")
        self.strategy_tab = QWidget()
        self.tabs.addTab(self.strategy_tab, "⚙️ Settings")

        # ========================================================================
        # v7_dual: Chart 탭 - 차트 상단 + 3개 섹션 하단 레이아웃 (통합 컨트롤)
        # ========================================================================
        tab_main_layout = QVBoxLayout(self.chart_tab)
        tab_main_layout.setContentsMargins(0, 0, 0, 0)

        # 수직 분할: [차트] | [LONG테이블|통합컨트롤|SHORT테이블]
        self.v_splitter_main = QSplitter(Qt.Vertical)

        # 상단: 차트 섹션 (LONG 패널 전용)
        chart_section = self._create_chart_section('long')
        self.v_splitter_main.addWidget(chart_section)

        # 하단: 3개 섹션 수평 배치
        bottom_h_splitter = QSplitter(Qt.Horizontal)

        # LONG 테이블
        long_tables = self._create_tables_widget('long')
        bottom_h_splitter.addWidget(long_tables)

        # 통합 컨트롤 (Account/Symbol/Price/Balance/Trade)
        unified_controls = self._create_unified_control_panel()
        bottom_h_splitter.addWidget(unified_controls)

        # SHORT 테이블
        short_tables = self._create_tables_widget('short')
        bottom_h_splitter.addWidget(short_tables)

        # 하단 3개 섹션 비율: 테이블:통합컨트롤:테이블 = 3:2:3
        bottom_h_splitter.setSizes([300, 200, 300])

        self.v_splitter_main.addWidget(bottom_h_splitter)
        # 상단(차트):하단(3섹션) = 6:4
        self.v_splitter_main.setSizes([600, 400])

        tab_main_layout.addWidget(self.v_splitter_main)

        # ========================================================================
        # 차트 관련 상태 변수들 (side별로 관리되지 않는 전역 상태)
        # ========================================================================
        self.chart_user_interacted = False
        self.chart_lock_mode = False
        self.last_candle_time = 0
        self.lock_mode_x_range = None
        self.lock_mode_last_x_max = None
        self.lock_mode_saved_x_min = None
        self.lock_mode_saved_x_max = None
        self.lock_mode_needs_first_restore = False
        self.saved_chart_x_min = None
        self.saved_chart_x_max = None
        self.last_chart_data_hash = None
        self.chart_retry_count = 0
        self.chart_refresh_pending = False
        
        self.loading_overlay = QLabel(self.tabs)
        self.loading_overlay.setText("API에 연결 중입니다...")
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.75); 
                color: white; 
                font-size: 24px; 
                font-weight: bold;
                border-radius: 10px;
            }
        """)
        self.loading_overlay.hide()
        self.loading_animation_timer = QTimer(self)
        self.loading_animation_timer.timeout.connect(self.animate_loading_text)

        # v7_dual: h_splitter removed (now h_splitter_dual)

        # --- Insight 탭 UI 설정 (Split View: LONG | SHORT) ---
        self.insight_widgets = {'long': {}, 'short': {}}
        insight_main_layout = QVBoxLayout(self.insight_tab)
        insight_main_layout.setContentsMargins(0, 0, 0, 0)

        # 좌우 Split: LONG(좌) | SHORT(우)
        insight_splitter = QSplitter(Qt.Horizontal)
        insight_splitter.setStyleSheet("QSplitter::handle { background-color: #555; width: 2px; }")

        for side in ['long', 'short']:
            column_widget = self._create_insight_column(side)
            insight_splitter.addWidget(column_widget)

        insight_splitter.setSizes([900, 900])
        insight_main_layout.addWidget(insight_splitter)

        # Insight 데이터 초기화 (side별)
        self.insight_data_by_side = {
            'long': {
                'main_position': {}, 'hedge_position': {},
                'next_order': {}, 'm_orders': [],
                'hedge_triggers': [{} for _ in range(4)],
                'profit_target': {}, 'uptrend_threshold': {},
                'current_price': 0
            },
            'short': {
                'main_position': {}, 'hedge_position': {},
                'next_order': {}, 'm_orders': [],
                'hedge_triggers': [{} for _ in range(4)],
                'profit_target': {}, 'uptrend_threshold': {},
                'current_price': 0
            }
        }

        # --- Statistics 탭 UI 설정 (Split View: LONG | SHORT) ---
        stats_main_layout = QVBoxLayout(self.statistics_tab)
        stats_main_layout.setContentsMargins(0, 0, 0, 0)
        stats_splitter = QSplitter(Qt.Horizontal)
        stats_splitter.setStyleSheet("QSplitter::handle { background-color: #555; width: 2px; }")
        for side in ['long', 'short']:
            col = self._create_statistics_column(side)
            stats_splitter.addWidget(col)
        stats_splitter.setSizes([900, 900])
        stats_main_layout.addWidget(stats_splitter)

        # --- Log 탭 UI 설정 ---
        log_main_layout = QVBoxLayout(self.log_tab)

        # 로그 리스트 위젯 (가상화 지원)
        self.log_list_widget = QListWidget()
        self.log_list_widget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.log_list_widget.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.log_list_widget.setUniformItemSizes(True)  # 가상화 성능 향상
        self.log_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 10pt;
                border: 1px solid #3e3e3e;
            }
            QListWidget::item {
                border: none;
                padding: 2px;
            }
            QListWidget::item:selected {
                background-color: #264f78;
            }
        """)
        log_main_layout.addWidget(self.log_list_widget)

        # 로그 컨트롤 버튼
        log_control_layout = QHBoxLayout()
        self.clear_log_button = QPushButton("🗑️ Clear Log")
        self.clear_log_button.clicked.connect(self.clear_log)
        self.auto_scroll_checkbox = QCheckBox("Auto Scroll")
        self.auto_scroll_checkbox.setChecked(True)

        # 최대 로그 라인 수 설정
        self.max_log_lines_label = QLabel("Max Lines:")
        self.max_log_lines_input = QLineEdit("5000")
        self.max_log_lines_input.setMaximumWidth(80)
        self.max_log_lines_input.setToolTip("최대 로그 라인 수 (메모리 관리)")

        log_control_layout.addWidget(self.clear_log_button)
        log_control_layout.addWidget(self.auto_scroll_checkbox)
        log_control_layout.addWidget(self.max_log_lines_label)
        log_control_layout.addWidget(self.max_log_lines_input)
        log_control_layout.addStretch()
        log_main_layout.addLayout(log_control_layout)

        # --- 1. Accounts 탭 UI 설정 ---
        accounts_main_layout = QVBoxLayout(self.accounts_tab)
        add_account_group = QGroupBox("Add / Update Account")
        
        # 'Add Account' 폼 레이아웃 생성
        form_layout = QFormLayout()
        self.new_exchange_combo = QComboBox()
        self.new_exchange_combo.addItems(["Binance", "Bybit"])
        form_layout.addRow(QLabel("Exchange:"), self.new_exchange_combo)
        self.new_account_name_input = QLineEdit()
        self.new_api_key_input = QLineEdit()
        self.new_api_secret_input = QLineEdit()
        self.new_api_secret_input.setEchoMode(QLineEdit.Password)
        self.new_email_input = QLineEdit()
        self.add_account_button = QPushButton("Save Account")
        form_layout.addRow(QLabel("Account Name:"), self.new_account_name_input)
        form_layout.addRow(QLabel("API Key:"), self.new_api_key_input)
        form_layout.addRow(QLabel("API Secret:"), self.new_api_secret_input)
        form_layout.addRow(QLabel("Email:"), self.new_email_input)
        form_layout.addRow(self.add_account_button)
        add_account_group.setLayout(form_layout)
        
        # 'Saved Accounts' 목록 생성
        account_list_group = QGroupBox("Saved Accounts")
        account_list_main_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.account_list_layout = QVBoxLayout(self.scroll_widget) 
        self.scroll_area.setWidget(self.scroll_widget)
        account_list_main_layout.addWidget(self.scroll_area)
        account_list_group.setLayout(account_list_main_layout)
        
        # 'Accounts' 탭 메인 레이아웃에 추가
        accounts_main_layout.addWidget(add_account_group)
        accounts_main_layout.addWidget(account_list_group)
        self.add_account_button.clicked.connect(self.add_new_account)

        # --- 2. Strategy Settings 탭 UI 설정 ---
        strategy_main_layout = QVBoxLayout(self.strategy_tab)

        # 위젯 생성
        self.settings_steps = QLineEdit()
        self.settings_timeframe = QLineEdit()
        self.settings_entry_start = QLineEdit()
        self.settings_entry_end = QLineEdit()
        self.settings_entry_exponent = QLineEdit()
        self.settings_balance_usage = QLineEdit()
        self.settings_target_leverage = QLineEdit()
        self.settings_hedge_start = QLineEdit()
        self.settings_hedge_end = QLineEdit()
        self.settings_hedge_exponent = QLineEdit()  # 헷지 곡선 지수
        self.settings_hedge_emergency_start_ratio = QLineEdit()  # 헷지 긴급 탈출 시작 비율
        self.settings_dca_interval_start = QLineEdit()
        self.settings_dca_interval_end = QLineEdit()
        self.settings_uptrend_entry_profit_threshold = QLineEdit()
        self.settings_uptrend_threshold_2_multiplier = QLineEdit()  # 2차 임계값 거리 배수
        self.settings_profit_start = QLineEdit()
        self.settings_profit_end = QLineEdit()
        self.settings_profit_ratio = QLineEdit()
        self.settings_stop_loss_ratio = QLineEdit()
        self.settings_trailing_callback_rate = QLineEdit()
        self.settings_hedge_reduction_steps = QLineEdit()  # 역방향진입 헷지 청산 단계 수
        # 헷지 프로토콜은 항상 활성화 (체크박스 제거됨)
        self.settings_hedge_protocol_retracement = QLineEdit()  # 헷지 프로토콜 되돌림 비율
        self.settings_hedge_protocol_tp_ratio = QLineEdit()  # 헷지 프로토콜 익절 비율
        self.settings_main_liquidation_safety_margin = QLineEdit()  # 메인 청산가 안전 마진
        self.settings_hedge_liquidation_safety_margin = QLineEdit()  # 헷지 청산가 안전 마진
        self.settings_test_quantity_mode = QCheckBox("활성화")
        self.settings_hedge_frontload = QCheckBox("활성화")
        
        # 비축금 설정
        self.settings_reserve_fund_ratio = QLineEdit()
        self.settings_reserve_fund_loss_threshold = QLineEdit()

        # === 1. 기본 전략 설정 ===
        basic_group = QGroupBox("📊 기본 전략 설정")
        basic_layout = QFormLayout()
        basic_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        basic_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        basic_layout.setHorizontalSpacing(10)

        # 라벨에 최소 너비 설정
        label_steps = QLabel("단계 수 (STEPS):")
        label_steps.setMinimumWidth(180)
        basic_layout.addRow(label_steps, self.settings_steps)

        label_timeframe = QLabel("시간봉 (Timeframe):")
        label_timeframe.setMinimumWidth(180)
        timeframe_help = QLabel("<small>1, 3, 5, 15, 30, 60, 120, 240, D</small>")
        timeframe_help.setStyleSheet("color: gray;")
        timeframe_layout = QHBoxLayout()
        timeframe_layout.addWidget(self.settings_timeframe)
        timeframe_layout.addWidget(timeframe_help)
        basic_layout.addRow(label_timeframe, timeframe_layout)

        label_balance = QLabel("자금 사용률 (%):")
        label_balance.setMinimumWidth(180)
        basic_layout.addRow(label_balance, self.settings_balance_usage)

        label_leverage = QLabel("목표 레버리지 (배):")
        label_leverage.setMinimumWidth(180)
        basic_layout.addRow(label_leverage, self.settings_target_leverage)

        label_test = QLabel("테스트 모드:")
        label_test.setMinimumWidth(180)
        basic_layout.addRow(label_test, self.settings_test_quantity_mode)

        basic_group.setLayout(basic_layout)

        # === 2. 진입 전략 ===
        entry_group = QGroupBox("📈 진입 전략 (Entry)")
        entry_layout = QFormLayout()
        entry_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        entry_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        entry_layout.setHorizontalSpacing(10)

        label_entry_start = QLabel("시작 비율 (ENTRY_START):")
        label_entry_start.setMinimumWidth(180)
        entry_layout.addRow(label_entry_start, self.settings_entry_start)

        label_entry_end = QLabel("종료 비율 (ENTRY_END):")
        label_entry_end.setMinimumWidth(180)
        entry_layout.addRow(label_entry_end, self.settings_entry_end)

        label_entry_exponent = QLabel("지수 (ENTRY_EXPONENT):")
        label_entry_exponent.setMinimumWidth(180)
        entry_layout.addRow(label_entry_exponent, self.settings_entry_exponent)

        label_uptrend = QLabel("역방향진입 수익률 (%):")
        label_uptrend.setMinimumWidth(180)
        entry_layout.addRow(label_uptrend, self.settings_uptrend_entry_profit_threshold)
        label_uptrend_2 = QLabel("2차 임계값 거리 배수:")
        label_uptrend_2.setMinimumWidth(180)
        entry_layout.addRow(label_uptrend_2, self.settings_uptrend_threshold_2_multiplier)

        label_main_liquidation_safety = QLabel("메인 청산가 안전 마진 (%):")
        label_main_liquidation_safety.setMinimumWidth(180)
        label_main_liquidation_safety.setToolTip("메인 포지션: 다음 단계 주문이 청산가로부터 떨어져야 하는 최소 거리\n예: 0.5% → 청산가 + 0.5% 이상")
        entry_layout.addRow(label_main_liquidation_safety, self.settings_main_liquidation_safety_margin)

        entry_group.setLayout(entry_layout)

        # === 3. 헷지 전략 (손실 구간) ===
        hedge_group = QGroupBox("🛡️ 헷지 전략 (손실 구간)")
        hedge_layout = QFormLayout()
        hedge_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hedge_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        hedge_layout.setHorizontalSpacing(10)

        label_hedge_start = QLabel("헷지 시작 (%):")
        label_hedge_start.setMinimumWidth(180)
        hedge_layout.addRow(label_hedge_start, self.settings_hedge_start)

        label_hedge_end = QLabel("헷지 종료 (%):")
        label_hedge_end.setMinimumWidth(180)
        hedge_layout.addRow(label_hedge_end, self.settings_hedge_end)

        label_hedge_exponent = QLabel("헷지 곡선 지수:")
        label_hedge_exponent.setMinimumWidth(180)
        label_hedge_exponent.setToolTip("헷지 증가 곡선의 가파름 정도\n1.0=선형, 2.0=완만, 3.0=균형(권장), 4.0=가파름")
        hedge_layout.addRow(label_hedge_exponent, self.settings_hedge_exponent)

        label_hedge_frontload = QLabel("최종단계-1에서 종료% 도달:")
        label_hedge_frontload.setMinimumWidth(180)
        label_hedge_frontload.setToolTip("활성화 시 헷지 종료%가 최종단계-1에서 도달합니다.\n최종단계에서는 헷지 프로토콜이 즉시 활성화되어 최저가를 추적합니다.")
        hedge_layout.addRow(label_hedge_frontload, self.settings_hedge_frontload)

        hedge_group.setLayout(hedge_layout)

        # === 3.5 DCA 진입 간격 ===
        dca_interval_group = QGroupBox("📏 DCA 진입 간격")
        dca_interval_layout = QFormLayout()
        dca_interval_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        dca_interval_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        dca_interval_layout.setHorizontalSpacing(10)

        label_dca_interval_start = QLabel("진입 간격 시작 (%):")
        label_dca_interval_start.setMinimumWidth(180)
        dca_interval_layout.addRow(label_dca_interval_start, self.settings_dca_interval_start)

        label_dca_interval_end = QLabel("진입 간격 종료 (%):")
        label_dca_interval_end.setMinimumWidth(180)
        dca_interval_layout.addRow(label_dca_interval_end, self.settings_dca_interval_end)

        dca_interval_group.setLayout(dca_interval_layout)

        # === 4. 익절 전략 (수익 구간) ===
        profit_group = QGroupBox("💰 익절 전략 (수익 구간)")
        profit_layout = QFormLayout()
        profit_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        profit_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        profit_layout.setHorizontalSpacing(10)

        label_profit_start = QLabel("익절 시작 (%):")
        label_profit_start.setMinimumWidth(180)
        profit_layout.addRow(label_profit_start, self.settings_profit_start)

        label_profit_end = QLabel("익절 종료 (%):")
        label_profit_end.setMinimumWidth(180)
        profit_layout.addRow(label_profit_end, self.settings_profit_end)

        label_profit_ratio = QLabel("익절 공비:")
        label_profit_ratio.setMinimumWidth(180)
        profit_layout.addRow(label_profit_ratio, self.settings_profit_ratio)

        profit_group.setLayout(profit_layout)

        # === 5. 최종 단계 손실 방지 ===
        final_protection_group = QGroupBox("🚨 최종 단계 손실 방지")
        final_protection_layout = QFormLayout()
        final_protection_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        final_protection_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        final_protection_layout.setHorizontalSpacing(10)

        label_stop_loss = QLabel("Stop Loss 비율:")
        label_stop_loss.setMinimumWidth(180)
        final_protection_layout.addRow(label_stop_loss, self.settings_stop_loss_ratio)

        label_trailing = QLabel("Trailing Stop 콜백 (%):")
        label_trailing.setMinimumWidth(180)
        final_protection_layout.addRow(label_trailing, self.settings_trailing_callback_rate)

        label_hedge_reduction = QLabel("역방향진입 헷지청산 단계:")
        label_hedge_reduction.setMinimumWidth(180)
        label_hedge_reduction.setToolTip("역방향진입 시 헷지 청산 단계 수\n예: 4 → 1/4, 1/3, 1/2, 전부\n예: 3 → 1/3, 1/2, 전부")
        final_protection_layout.addRow(label_hedge_reduction, self.settings_hedge_reduction_steps)

        final_protection_group.setLayout(final_protection_layout)

        # === 6. 헷지 프로토콜 ===
        hedge_protocol_group = QGroupBox("🎯 헷지 프로토콜")
        hedge_protocol_layout = QFormLayout()
        hedge_protocol_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        hedge_protocol_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        hedge_protocol_layout.setHorizontalSpacing(10)

        label_hedge_protocol_retracement = QLabel("되돌림 비율 (%):")
        label_hedge_protocol_retracement.setMinimumWidth(180)
        label_hedge_protocol_retracement.setToolTip("최저가 대비 헷지 진입평균가의 N% 되돌림 시 익절\n예: 50% → 헷지가 반등 50% 지점에서 익절")
        hedge_protocol_layout.addRow(label_hedge_protocol_retracement, self.settings_hedge_protocol_retracement)

        label_hedge_protocol_tp_ratio = QLabel("익절 수량 비율 (%):")
        label_hedge_protocol_tp_ratio.setMinimumWidth(180)
        label_hedge_protocol_tp_ratio.setToolTip("익절하는 헷지 수량 비율\n예: 50% → 헷지 수량의 50%만 익절")
        hedge_protocol_layout.addRow(label_hedge_protocol_tp_ratio, self.settings_hedge_protocol_tp_ratio)

        label_hedge_liquidation_safety_margin = QLabel("헷지 청산가 안전마진 (%):")
        label_hedge_liquidation_safety_margin.setMinimumWidth(180)
        label_hedge_liquidation_safety_margin.setToolTip("헷지 포지션: 안전망 주문을 청산가에서 N% 떨어진 위치에 설정\n예: 0.5% → 청산가 ± 0.5% 위치에 안전망 주문\n(기존 -1틱보다 훨씬 안전)")
        hedge_protocol_layout.addRow(label_hedge_liquidation_safety_margin, self.settings_hedge_liquidation_safety_margin)

        hedge_protocol_group.setLayout(hedge_protocol_layout)

        # === 8. 비축금 설정 ===
        reserve_fund_group = QGroupBox("🏦 비축금 설정 (Reserve Fund)")
        reserve_fund_layout = QFormLayout()
        reserve_fund_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        reserve_fund_layout.setFieldGrowthPolicy(QFormLayout.ExpandingFieldsGrow)
        reserve_fund_layout.setHorizontalSpacing(10)

        label_reserve_ratio = QLabel("수익 적립 비율 (%):")
        label_reserve_ratio.setMinimumWidth(180)
        label_reserve_ratio.setToolTip("사이클 완료 시 발생한 순수익금의 N%를 펀딩 계좌(비축금)로 자동 이체합니다.\n예: 50.0 → 수익금의 절반을 비축 (0 입력 시 비활성)")
        reserve_fund_layout.addRow(label_reserve_ratio, self.settings_reserve_fund_ratio)

        label_reserve_loss_threshold = QLabel("전액 투입 손실 기준 (%):")
        label_reserve_loss_threshold.setMinimumWidth(180)
        label_reserve_loss_threshold.setToolTip("해당 사이클 원금 대비 누적 손실이 N% 이상일 경우, 양쪽 계좌의 비축금을 모두 가져옵니다.\n예: 10.0 → -10% 손실 도달 시 비축금 전액 투입")
        reserve_fund_layout.addRow(label_reserve_loss_threshold, self.settings_reserve_fund_loss_threshold)

        reserve_fund_group.setLayout(reserve_fund_layout)

        # 저장 버튼
        self.save_settings_button = QPushButton("💾 Save Strategy Settings")
        self.save_settings_button.clicked.connect(self.on_save_strategy_settings)

        # 레이아웃에 추가
        strategy_main_layout.addWidget(basic_group)
        strategy_main_layout.addWidget(entry_group)
        strategy_main_layout.addWidget(hedge_group)
        strategy_main_layout.addWidget(dca_interval_group)
        strategy_main_layout.addWidget(profit_group)
        strategy_main_layout.addWidget(final_protection_group)
        strategy_main_layout.addWidget(hedge_protocol_group)
        strategy_main_layout.addWidget(reserve_fund_group)
        strategy_main_layout.addWidget(self.save_settings_button)
        strategy_main_layout.addStretch(1)

    def create_order_panel(self, parent_layout):
        # Symbol 선택 드롭다운
        symbol_box = QGroupBox("Symbol")
        symbol_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        symbol_layout = QVBoxLayout(symbol_box)
        symbol_layout.setContentsMargins(10, 15, 10, 10)

        self.symbol_combo = QComboBox()
        self.symbol_combo.setMinimumHeight(35)
        self.symbol_combo.addItems([
            "BTCUSDT",
            "ETHUSDT",
            "BNBUSDT",
            "SOLUSDT",
            "XRPUSDT",
            "ADAUSDT",
            "DOGEUSDT",
            "AVAXUSDT",
            "DOTUSDT",
            "MATICUSDT"
        ])
        self.symbol_combo.setCurrentText(self.current_symbol)
        self.symbol_combo.currentTextChanged.connect(self.on_symbol_changed)
        symbol_layout.addWidget(self.symbol_combo)

        parent_layout.addWidget(symbol_box)

        price_box = QGroupBox("Price")
        price_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        price_layout = QVBoxLayout(price_box)
        price_layout.setContentsMargins(10, 15, 10, 10)
        self.trade_price_label = QLabel("0.00")
        self.default_price_label_style = "font-size: 24pt; font-weight: bold; padding: 10px 0;"
        self.trade_price_label.setStyleSheet(self.default_price_label_style)
        self.trade_price_label.setAlignment(Qt.AlignCenter)
        price_layout.addWidget(self.trade_price_label)

        trade_box = QGroupBox("Trade")
        trade_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        trade_layout = QVBoxLayout(trade_box)
        trade_layout.setContentsMargins(10, 15, 10, 10)

        toggle_layout = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.close_button = QPushButton("Close")
        self.order_mode_group = QButtonGroup()
        self.open_button.setCheckable(True); self.close_button.setCheckable(True)
        self.order_mode_group.addButton(self.open_button); self.order_mode_group.addButton(self.close_button)
        self.open_button.setChecked(True)
        toggle_layout.addWidget(self.open_button); toggle_layout.addWidget(self.close_button)
        trade_layout.addLayout(toggle_layout)
        self.open_button.clicked.connect(self.update_order_panel_mode); self.close_button.clicked.connect(self.update_order_panel_mode)
        
        market_label = QLabel("Market Order"); market_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        trade_layout.addWidget(market_label)
        
        order_form_layout = QFormLayout()
        self.order_symbol_input = QLineEdit(self.current_symbol)
        order_form_layout.addRow(QLabel("Symbol:"), self.order_symbol_input)
        self.order_quantity_input = QLineEdit()
        self.order_quantity_input.setPlaceholderText("Size (e.g., 100 for COIN-M Cont, 0.1 for USD-M BTC)")
        order_form_layout.addRow(QLabel("Quantity:"), self.order_quantity_input)
        trade_layout.addLayout(order_form_layout)
        
        button_layout = QHBoxLayout()
        self.long_button = QPushButton("Open Long"); self.short_button = QPushButton("Open Short")
        self.long_button.setStyleSheet("background-color: #00b050; color: white; padding: 10px; font-weight: bold;")
        self.short_button.setStyleSheet("background-color: #c00000; color: white; padding: 10px; font-weight: bold;")
        button_layout.addWidget(self.long_button); button_layout.addWidget(self.short_button)
        trade_layout.addLayout(button_layout)
        
        # ▼▼▼ [레이아웃 수정] ▼▼▼
        # 'Clear All' 버튼 레이아웃
        clear_layout = QHBoxLayout()
        self.clear_all_button = QPushButton("🚨 Clear All (All Symbols)")
        self.update_clear_button_style()
        clear_layout.addWidget(self.clear_all_button)
        trade_layout.addLayout(clear_layout) # 1. Clear All 버튼 먼저 추가
        
        # 'Wallet Balance' 박스
        balance_box = QGroupBox("Wallet Balance")
        balance_layout = QVBoxLayout(balance_box)
        balance_layout.setContentsMargins(5, 5, 5, 5)

        self.balance_label = QLabel("N/A")
        self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.balance_label.setAlignment(Qt.AlignCenter)

        balance_layout.addWidget(self.balance_label)

        # 사이클 수 및 누적 손익 라벨 추가
        self.cycle_pnl_label = QLabel("Cycles: 0 | PnL: +0.0000")
        self.cycle_pnl_label.setStyleSheet("font-size: 10pt; color: #888888;")
        self.cycle_pnl_label.setAlignment(Qt.AlignCenter)

        balance_layout.addWidget(self.cycle_pnl_label)

        trade_layout.addWidget(balance_box) # 2. 그 *아래에* 잔액 박스 추가
        # ▲▲▲ [레이아웃 수정] ▲▲▲

        trade_layout.addStretch(1) # 3. 마지막에 Stretch 추가

        parent_layout.addWidget(price_box)
        parent_layout.addWidget(trade_box)

        # ▼▼▼ [Auto-Trade Controls 박스 - 제일 하단] ▼▼▼
        auto_trade_controls_box = QGroupBox("Auto-Trade Controls")
        auto_trade_controls_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        auto_trade_controls_layout = QVBoxLayout(auto_trade_controls_box)
        auto_trade_controls_layout.setContentsMargins(10, 15, 10, 10)
        auto_trade_controls_layout.setSpacing(8)

        # Status와 Step 레이블 (상단)
        status_step_layout = QVBoxLayout()
        status_step_layout.setSpacing(2)
        self.auto_trade_status_label = QLabel("Status: <b style='color: gray;'>Stopped</b>")
        self.auto_trade_step_label = QLabel("Step: <b>-</b>")
        status_step_layout.addWidget(self.auto_trade_status_label)
        status_step_layout.addWidget(self.auto_trade_step_label)
        auto_trade_controls_layout.addLayout(status_step_layout)

        # Market/Side 버튼 레이아웃
        market_side_layout = QHBoxLayout()
        market_side_layout.setSpacing(10)

        market_display = "USDT" if self.auto_trade_market_mode == "linear" else "COIN"
        self.auto_trade_market_toggle = QPushButton(f"Market: {market_display}")
        self.auto_trade_market_toggle.setToolTip("Click to toggle strategy market mode (USDT-M / COIN-M)")
        self.auto_trade_market_toggle.setFixedHeight(40)
        self.auto_trade_market_toggle.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.auto_trade_market_toggle.clicked.connect(self.on_auto_trade_market_toggle)
        market_side_layout.addWidget(self.auto_trade_market_toggle)

        self.auto_trade_side_toggle = QPushButton(f"Side: {self.auto_trade_side_mode.upper()}")
        self.auto_trade_side_toggle.setToolTip("Click to toggle strategy side (LONG / SHORT)")
        self.auto_trade_side_toggle.setFixedHeight(40)
        self.auto_trade_side_toggle.setStyleSheet("font-size: 11pt; font-weight: bold;")
        self.auto_trade_side_toggle.clicked.connect(self.on_auto_trade_side_toggle)
        market_side_layout.addWidget(self.auto_trade_side_toggle)

        auto_trade_controls_layout.addLayout(market_side_layout)

        # Start Auto-Trade 버튼
        self.auto_trade_start_button = QPushButton("Start Auto-Trade")
        self.auto_trade_start_button.setFixedHeight(45)
        self.auto_trade_start_button.setStyleSheet("font-size: 13pt; font-weight: bold;")
        self.auto_trade_start_button.clicked.connect(self.on_auto_trade_start_clicked)
        auto_trade_controls_layout.addWidget(self.auto_trade_start_button)

        # 예약 종료 버튼
        self.auto_trade_schedule_stop_button = QPushButton("⏱️ Schedule Stop")
        self.auto_trade_schedule_stop_button.setFixedHeight(35)
        self.auto_trade_schedule_stop_button.setStyleSheet("font-size: 11pt; background-color: #444444; color: #FFD700;")
        self.auto_trade_schedule_stop_button.setEnabled(False)  # 초기에는 비활성화
        self.auto_trade_schedule_stop_button.clicked.connect(self.on_auto_trade_schedule_stop_clicked)
        auto_trade_controls_layout.addWidget(self.auto_trade_schedule_stop_button)

        parent_layout.addWidget(auto_trade_controls_box)
        # ▲▲▲ [Auto-Trade Controls 박스] ▲▲▲

        # ▼▼▼ [리소스 모니터 박스 - 제일 하단] ▼▼▼
        resource_box = QGroupBox("System Resources")
        resource_box.setStyleSheet("QGroupBox { font-size: 11pt; font-weight: bold; }")
        resource_layout = QVBoxLayout(resource_box)
        resource_layout.setContentsMargins(10, 15, 10, 10)
        resource_layout.setSpacing(5)

        # 메모리 사용량
        self.resource_memory_label = QLabel("Memory: --")
        self.resource_memory_label.setStyleSheet("font-size: 10pt;")
        resource_layout.addWidget(self.resource_memory_label)

        # CPU 사용률
        self.resource_cpu_label = QLabel("CPU: --")
        self.resource_cpu_label.setStyleSheet("font-size: 10pt;")
        resource_layout.addWidget(self.resource_cpu_label)

        # 마지막 정리 시간
        self.resource_cleanup_label = QLabel("Last Cleanup: --")
        self.resource_cleanup_label.setStyleSheet("font-size: 9pt; color: #888888;")
        resource_layout.addWidget(self.resource_cleanup_label)

        parent_layout.addWidget(resource_box)
        # ▲▲▲ [리소스 모니터 박스] ▲▲▲

        parent_layout.addStretch(1)

        # 연결 상태 라벨 (오른쪽 패널 최하단)
        self.connection_status_label = QLabel("Not Connected")
        self.connection_status_label.setStyleSheet("color: gray; font-weight: bold; font-size: 10pt; padding: 5px;")
        self.connection_status_label.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        parent_layout.addWidget(self.connection_status_label)

        self.long_button.clicked.connect(lambda: self.on_place_order_clicked("BUY"))
        self.short_button.clicked.connect(lambda: self.on_place_order_clicked("SELL"))
        self.clear_all_button.clicked.connect(self.on_clear_all_clicked)
        self.update_order_panel_mode() 

    def update_clear_button_style(self):
        if not hasattr(self, 'clear_all_button'): return
        if self.is_dark_mode: style = "background-color: #8B0000; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        else: style = "background-color: #FF4500; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        self.clear_all_button.setStyleSheet(style)
    
    def update_order_panel_mode(self):
        base_style = "padding: 8px; font-weight: bold; border-radius: 4px;"
        if self.is_dark_mode: checked_style = "background-color: #555; color: white;"; unchecked_style = "background-color: #333; color: #888;"
        else: checked_style = "background-color: #BBB; color: black;"; unchecked_style = "background-color: #DDD; color: #777;"
        if self.open_button.isChecked():
            self.is_reduce_only = False
            self.open_button.setStyleSheet(base_style + checked_style); self.close_button.setStyleSheet(base_style + unchecked_style)
            self.long_button.setText("Open Long"); self.short_button.setText("Open Short")
        else:
            self.is_reduce_only = True
            self.open_button.setStyleSheet(base_style + unchecked_style); self.close_button.setStyleSheet(base_style + checked_style)
            self.long_button.setText("Close Short"); self.short_button.setText("Close Long")

    def _calculate_total_pnl(self):
        """
        현재 모든 포지션의 총 PNL을 계산합니다.
        GUI 테이블에 표시된 PNL 값을 직접 읽어서 합산합니다.

        Returns:
            float: 총 PNL (USDT)
        """
        total_pnl = 0.0

        # Position 테이블에서 직접 PNL 값을 읽어서 합산
        for row in range(self.position_table.rowCount()):
            try:
                # Column 3: PNL
                pnl_item = self.position_table.item(row, 3)
                if pnl_item:
                    pnl_text = pnl_item.text().strip()
                    pnl = float(pnl_text)
                    total_pnl += pnl
            except (ValueError, TypeError):
                continue

        return total_pnl

    def on_place_order_clicked(self, side):
        symbol = self.order_symbol_input.text().upper().strip()
        quantity = self.order_quantity_input.text().strip()
        if not symbol or not quantity: QMessageBox.warning(self, "Order Error", "Symbol and Quantity are required."); return
        if not self.api_module or not self.api_module.is_api_key_active(): QMessageBox.warning(self, "Order Error", "API is not connected. Please connect in Settings tab."); return
        reduce_only = self.is_reduce_only
        if side == "BUY": position_side = "LONG" if not reduce_only else "SHORT"
        else: position_side = "SHORT" if not reduce_only else "LONG"
        action_text = "Close" if reduce_only else "Open"; side_text = "Short" if position_side == "SHORT" else "Long"
        reply = QMessageBox.question(self, "Confirm Order", f"Place Market {action_text} {side_text} order?\n\nSymbol: {symbol}\nQuantity: {quantity}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        try:
            print(f"Placing order: {side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")
            result = self.api_module.place_market_order(symbol, side, quantity, reduce_only, position_side)
            if result and (result.get('orderId') or result.get('code') == 0):
                order_id = str(result.get('orderId'))
                print(f"주문 ID {order_id}가 접수되었습니다. WebSocket (FILLED) 응답 대기 중...")
                self.pending_market_orders.add(order_id)
                self.order_quantity_input.clear()
            elif result and result.get('code'):
                QMessageBox.warning(self, "Order Rejected", f"Order REJECTED by Binance (API).\n\nCode: {result.get('code')}\nMsg: {result.get('msg', 'Unknown error')}")
            else:
                QMessageBox.warning(self, "Order Failed", f"API request failed. Check console log for details.\nResult: {result}")
        except Exception as e:
            QMessageBox.critical(self, "Python Error", f"Failed to place order: {e}")

    def on_clear_all_clicked(self):
        if not self.api_module or not self.api_module.is_api_key_active(): QMessageBox.warning(self, "Error", "API is not connected."); return

        # 포지션이 있고 총 PNL이 음수인 경우 경고
        if len(self.live_position_data) > 0:
            total_pnl = self._calculate_total_pnl()
            if total_pnl < 0:
                loss_warning = QMessageBox.warning(
                    self,
                    "경고: 현재 손실 중",
                    f"현재 손실중입니다 (총 PNL: {total_pnl:.4f} USDT).\n거래를 종료 하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                if loss_warning == QMessageBox.No:
                    print("[Clear All] 사용자가 손실 경고로 인해 Clear All을 취소했습니다.")
                    return

        reply = QMessageBox.warning(
            self,
            "위험: 작업 확인",
            "다음 작업을 시도합니다:\n1. 모든 미체결 주문 취소 (모든 심볼)\n2. 모든 포지션 청산 (모든 심볼)\n\n이 작업은 되돌릴 수 없습니다. 계속하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No: return
        print("--- [Clear All] Starting ---")
        cancel_results = []; close_results = []; open_orders = []
        try:
            open_orders = self.api_module.get_initial_open_orders()
            if not open_orders: print("[Clear All] No open orders found to cancel.")
            else:
                for order in open_orders:
                    try: result = self.api_module.cancel_order(str(order['symbol']), str(order['orderId'])); cancel_results.append(result)
                    except Exception as e: cancel_results.append({"status": "PYTHON_ERROR", "msg": str(e)})
        except Exception as e: print(f"[Clear All] Failed to fetch open orders: {e}")
        # 실제 포지션 재조회
        actual_positions = []
        try:
            actual_positions = self.api_module.get_initial_positions()
            print(f"[Clear All] API에서 {len(actual_positions)}개 포지션 조회됨")
        except Exception as e:
            print(f"[Clear All] 포지션 조회 실패: {e}")
            actual_positions = []

        if not actual_positions:
            print("[Clear All] No open positions found to close.")
        else:
            for pos in actual_positions:
                try:
                    symbol = pos.get('symbol')
                    amount = abs(float(pos.get('positionAmt', 0)))

                    if amount == 0:
                        print(f"[Clear All] {symbol} 포지션 수량 0 - 스킵")
                        continue

                    position_side = pos.get('positionSide')
                    if not position_side or position_side == 'BOTH':
                        position_side = 'LONG' if float(pos.get('positionAmt', 0)) > 0 else 'SHORT'

                    side = "SELL" if float(pos.get('positionAmt', 0)) > 0 else "BUY"

                    print(f"[Clear All] {symbol} {position_side} 청산 중: {side} {amount}")
                    result = self.api_module.place_market_order(symbol, side, str(amount), reduce_only=True, position_side=position_side)
                    close_results.append(result)
                except Exception as e:
                    print(f"[Clear All] 포지션 청산 오류: {e}")
                    close_results.append({"status": "PYTHON_ERROR", "msg": str(e)})
        print("--- [Clear All] Finished ---")
        success_orders = sum(1 for r in cancel_results if r and (r.get('status') == 'CANCELED' or r.get('code') == -2011))
        success_positions = sum(1 for r in close_results if r and (r.get('status') == 'FILLED' or r.get('orderId') or r.get('retCode') == 0))

        # DCA 상태 삭제
        if "dca_state" in self.config_data:
            del self.config_data["dca_state"]
            config_manager.save_config_data(self.config_data)
            print("[Clear All] 저장된 DCA 상태 삭제 완료")

        QMessageBox.information(self, "Clear All Report", f"Orders Canceled: {success_orders} / {len(open_orders)}\nPositions Closed: {success_positions} / {len(actual_positions)}")

    def create_centered_cancel_button(self, callback):
        """Cancel 버튼을 중앙 정렬된 위젯으로 생성합니다."""
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(55, 22)
        cancel_btn.setStyleSheet("background-color: #555555; color: white; font-weight: bold;")
        cancel_btn.clicked.connect(callback)

        # 중앙 정렬을 위한 컨테이너 위젯
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.addWidget(cancel_btn)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)

        return container

    def close_single_position(self, position_key):
        """개별 포지션을 청산합니다."""
        if not self.api_module or not self.api_module.is_api_key_active():
            QMessageBox.warning(self, "Error", "API is not connected.")
            return

        pos_data = self.live_position_data.get(position_key)
        if not pos_data:
            QMessageBox.warning(self, "Error", f"Position {position_key} not found.")
            return

        # 확인 대화상자
        reply = QMessageBox.question(
            self,
            "포지션 청산 확인",
            f"포지션을 청산하시겠습니까?\n\nSymbol: {pos_data['symbol']}\nSide: {pos_data.get('side', pos_data.get('positionSide', ''))}\nAmount: {pos_data['amount']}\nEntry: ${self.fmt_price(pos_data.get('entry_price', pos_data.get('entry', 0)))}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            symbol = pos_data['symbol']
            position_side = pos_data.get('side', pos_data.get('positionSide', ''))

            # 실제 포지션 재조회하여 수량 확인
            print(f"[개별 청산] API에서 실제 포지션 조회 중... ({symbol} {position_side})")
            actual_positions = self.api_module.get_initial_positions()
            actual_amount = 0

            for p in actual_positions:
                if p.get('symbol') == symbol:
                    p_side = p.get('positionSide')
                    if not p_side or p_side == 'BOTH':
                        p_side = 'LONG' if float(p.get('positionAmt', 0)) > 0 else 'SHORT'

                    if p_side == position_side:
                        actual_amount = abs(float(p.get('positionAmt', 0)))
                        print(f"[개별 청산] 실제 포지션 수량: {actual_amount}")
                        break

            if actual_amount == 0:
                print(f"[개별 청산] 실제 포지션이 존재하지 않음 - 청산 스킵")
                QMessageBox.warning(self, "청산 실패", f"포지션이 이미 청산되었거나 존재하지 않습니다.\n\n{symbol} {position_side}")
                # GUI에서 제거
                if position_key in self.live_position_data:
                    row = self.live_position_data[position_key]['row']
                    self.position_table.removeRow(row)
                    del self.live_position_data[position_key]
                    self.reindex_position_rows()
                return

            amount = actual_amount
            side = "SELL" if pos_data['amount'] > 0 else "BUY"

            print(f"[개별 청산] {position_key} 포지션 청산 중: {side} {amount} {symbol}")
            result = self.api_module.place_market_order(symbol, side, str(amount), reduce_only=True, position_side=position_side)

            if result and (result.get('orderId') or result.get('retCode') == 0):
                print(f"[개별 청산] 성공: {result}")

                # 테이블에서 해당 포지션 즉시 제거
                if position_key in self.live_position_data:
                    row = self.live_position_data[position_key]['row']
                    self.position_table.removeRow(row)
                    print(f"[개별 청산] 테이블에서 포지션 제거 완료 (row={row})")

                    # 차트에서 포지션 라인 제거
                    self.remove_position_line_by_side(position_side)

                    # live_position_data에서 제거
                    del self.live_position_data[position_key]

                    # 나머지 포지션들의 row 번호 업데이트 (removeRow로 행이 밀렸으므로)
                    for key, data in self.live_position_data.items():
                        if data['row'] > row:
                            data['row'] -= 1

                QMessageBox.information(self, "Success", f"포지션 청산 주문이 실행되었습니다.\n\n{position_key}")
            else:
                print(f"[개별 청산] 실패: {result}")
                QMessageBox.warning(self, "Error", f"포지션 청산에 실패했습니다.\n\n{result}")
        except Exception as e:
            print(f"[개별 청산] 예외 발생: {e}")
            QMessageBox.critical(self, "Error", f"포지션 청산 중 오류가 발생했습니다.\n\n{str(e)}")

    def cancel_single_order(self, symbol, order_id, order_category='normal'):
        """개별 주문을 취소합니다."""
        if not self.api_module or not self.api_module.is_api_key_active():
            QMessageBox.warning(self, "Error", "API is not connected.")
            return

        # 확인 대화상자
        order_type_label = "Algo 조건부 주문" if order_category == 'algo' else "일반 주문"
        reply = QMessageBox.question(
            self,
            "주문 취소 확인",
            f"{order_type_label}을 취소하시겠습니까?\n\nSymbol: {symbol}\nOrder ID: {order_id}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            print(f"[개별 취소] 주문 취소 중: {symbol} (OrderID: {order_id}, Type: {order_category})")
            result = self.api_module.cancel_order(symbol, order_id, order_category)

            # 성공 여부 판단:
            # - Binance 일반 주문: result.get('orderId') 존재
            # - Binance Algo 주문: result.get('algoId') 존재 또는 result.get('code') == '200'
            # - Bybit: result.get('retCode') == 0
            is_success = False
            if result:
                if result.get('orderId'):  # Binance 일반 주문
                    is_success = True
                elif result.get('algoId') or result.get('code') == '200':  # Binance Algo 주문
                    is_success = True
                elif result.get('retCode') == 0:  # Bybit
                    is_success = True

            # 에러 코드 110001: 주문이 이미 존재하지 않음 (체결/취소됨)
            is_order_not_exists = False
            if isinstance(result, dict):
                error_code = result.get('code') or result.get('retCode')
                if error_code == 110001:
                    is_order_not_exists = True
                    print(f"[개별 취소] 주문이 이미 존재하지 않음 (코드: 110001) - 로컬에서 제거")

            if is_success or is_order_not_exists:
                if is_success:
                    print(f"[개별 취소] 성공: {result}")

                # 테이블에서 해당 주문 즉시 제거
                for row in range(self.order_table.rowCount()):
                    order_id_item = self.order_table.item(row, 7)  # OrderId는 7번 열
                    if order_id_item and order_id_item.text() == order_id:
                        self.order_table.removeRow(row)
                        print(f"[개별 취소] 테이블에서 주문 제거 완료 (row={row})")

                        # 차트에서 주문 라인 제거
                        self.remove_order_line_from_chart(order_id)
                        break

                if is_order_not_exists:
                    QMessageBox.information(self, "주문 제거", f"주문이 거래소에 존재하지 않아 로컬에서 제거했습니다.\n(이미 체결되었거나 취소되었을 수 있습니다)\n\nOrder ID: {order_id}")
                else:
                    QMessageBox.information(self, "Success", f"주문이 취소되었습니다.\n\nOrder ID: {order_id}")
            else:
                print(f"[개별 취소] 실패: {result}")
                QMessageBox.warning(self, "Error", f"주문 취소에 실패했습니다.\n\n{result}")
        except Exception as e:
            print(f"[개별 취소] 예외 발생: {e}")
            QMessageBox.critical(self, "Error", f"주문 취소 중 오류가 발생했습니다.\n\n{str(e)}")



    def cancel_single_order_for_side(self, side, symbol, order_id, order_category='normal'):
        """Side별 개별 주문을 취소합니다."""
        api_module = self.api_modules.get(side)
        if not api_module or not api_module.is_api_key_active():
            QMessageBox.warning(self, "Error", f"{side.upper()} API가 연결되지 않았습니다.")
            return

        order_type_label = "Algo 조건부 주문" if order_category == 'algo' else "일반 주문"
        reply = QMessageBox.question(
            self,
            f"[{side.upper()}] 주문 취소 확인",
            f"{order_type_label}을 취소하시겠습니까?\n\nSymbol: {symbol}\nOrder ID: {order_id}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            print(f"[{side.upper()}] 주문 취소 중: {symbol} (OrderID: {order_id}, Type: {order_category})")
            result = api_module.cancel_order(symbol, order_id, order_category)

            is_success = False
            if result:
                if result.get('orderId'):
                    is_success = True
                elif result.get('algoId') or result.get('code') == '200':
                    is_success = True

            is_order_not_exists = False
            if isinstance(result, dict):
                error_code = result.get('code') or result.get('retCode')
                if error_code == 110001:
                    is_order_not_exists = True
                    print(f"[{side.upper()}] 주문이 이미 존재하지 않음 (코드: 110001)")

            if is_success or is_order_not_exists:
                if is_success:
                    print(f"[{side.upper()}] 주문 취소 성공: {result}")

                order_table = self.order_tables.get(side)
                if order_table:
                    for row in range(order_table.rowCount()):
                        order_id_item = order_table.item(row, 7)
                        if order_id_item and order_id_item.text() == order_id:
                            order_table.removeRow(row)
                            print(f"[{side.upper()}] 테이블에서 주문 제거 (row={row})")
                            self.remove_order_line_from_chart(order_id)
                            break

                if is_order_not_exists:
                    QMessageBox.information(self, "주문 제거", f"주문이 거래소에 존재하지 않습니다.\n\nOrder ID: {order_id}")
                else:
                    QMessageBox.information(self, "Success", f"[{side.upper()}] 주문이 취소되었습니다.\n\nOrder ID: {order_id}")
            else:
                print(f"[{side.upper()}] 주문 취소 실패: {result}")
                QMessageBox.warning(self, "Error", f"주문 취소에 실패했습니다.\n\n{result}")
        except Exception as e:
            print(f"[{side.upper()}] 주문 취소 예외: {e}")
            QMessageBox.critical(self, "Error", f"주문 취소 중 오류가 발생했습니다.\n\n{str(e)}")

    def fmt_price(self, price):
        """가격을 심볼의 정밀도에 맞게 포맷"""
        if price is None:
            return "N/A"
        precision = self.detected_precision if self.detected_precision is not None else 4
        return f"{price:.{precision}f}"

    def populate_account_combos(self):
        """v7_dual: Account 정보 로드 (팝업 다이얼로그 사용으로 콤보박스 없음)"""
        account_names = list(self.accounts.keys())
        print(f"[populate_account_combos] Total accounts: {len(account_names)}")
        print(f"[populate_account_combos] Accounts: {account_names}")

        # 팝업 다이얼로그 방식에서는 콤보박스가 없으므로 로그만 출력
        if len(account_names) > 0:
            print(f"Account 설정은 '⚙ Account Settings' 버튼을 클릭하여 변경할 수 있습니다.")
        else:
            print(f"설정된 계정이 없습니다. Accounts 탭에서 계정을 추가하세요.")

    def load_config_data(self):
        self.config_data = config_manager.load_config_data()
        self.accounts = self.config_data.get("accounts", {})
        app_settings = self.config_data.get("app_settings", {})

        # Auto Balance 설정 로드
        self.auto_balance_enabled = app_settings.get("auto_balance_enabled", False)

        # Watchdog 설정 로드 및 데몬 자동 시작
        watchdog_enabled = app_settings.get("watchdog_enabled", False)
        if watchdog_enabled:
            # clean_shutdown 플래그 클리어 (새 세션 시작)
            if "app_settings" not in self.config_data:
                self.config_data["app_settings"] = {}
            self.config_data["app_settings"]["watchdog_clean_shutdown"] = False
            config_manager.save_config_data(self.config_data)
            self._start_watchdog_daemon()
            print("[Watchdog] 설정에서 활성화 감지 - 데몬 자동 시작")

        # v7_dual: 저장된 패널 방향 복원
        saved_directions = self.config_data.get("panel_directions", {})
        for side in ['long', 'short']:
            if side in saved_directions:
                self.side_modes[side] = saved_directions[side]
                print(f"[{side.upper()} 패널] 저장된 방향 복원: {saved_directions[side]}")

        self.strategy_settings = self.config_data.get("strategy_settings", {})
        self.settings_steps.setText(str(self.strategy_settings.get("STEPS", 10)))
        self.settings_timeframe.setText(str(self.strategy_settings.get("TIMEFRAME", "15")))
        self.settings_entry_start.setText(str(self.strategy_settings.get("ENTRY_START", 0.45)))
        self.settings_entry_end.setText(str(self.strategy_settings.get("ENTRY_END", 0.66)))
        self.settings_entry_exponent.setText(str(self.strategy_settings.get("ENTRY_EXPONENT", 3.0)))
        self.settings_balance_usage.setText(str(self.strategy_settings.get("BALANCE_USAGE_PERCENTAGE", 70.0)))
        self.settings_target_leverage.setText(str(self.strategy_settings.get("TARGET_LEVERAGE", 15)))
        self.settings_hedge_start.setText(str(self.strategy_settings.get("HEDGE_START_PERCENT", 0)))
        self.settings_hedge_end.setText(str(self.strategy_settings.get("HEDGE_END_PERCENT", 99)))
        self.settings_hedge_exponent.setText(str(self.strategy_settings.get("HEDGE_EXPONENT", 3.0)))
        # HEDGE_EMERGENCY_START_RATIO는 내부적으로만 사용 (GUI에 표시 안 함)
        # self.settings_hedge_emergency_start_ratio.setText(str(self.strategy_settings.get("HEDGE_EMERGENCY_START_RATIO", 50.0)))
        self.settings_uptrend_threshold_2_multiplier.setText(str(self.strategy_settings.get("UPTREND_THRESHOLD_2_MULTIPLIER", 2.0)))
        self.settings_dca_interval_start.setText(str(self.strategy_settings.get("DCA_INTERVAL_START_PERCENT", 40)))
        self.settings_dca_interval_end.setText(str(self.strategy_settings.get("DCA_INTERVAL_END_PERCENT", 100)))
        self.settings_uptrend_entry_profit_threshold.setText(str(self.strategy_settings.get("UPTREND_ENTRY_PROFIT_THRESHOLD", 1.0)))
        self.settings_profit_start.setText(str(self.strategy_settings.get("PROFIT_START_PERCENT", 60.0)))
        self.settings_profit_end.setText(str(self.strategy_settings.get("PROFIT_END_PERCENT", 30.0)))
        self.settings_profit_ratio.setText(str(self.strategy_settings.get("PROFIT_RATIO", 0.7)))
        self.settings_stop_loss_ratio.setText(str(self.strategy_settings.get("STOP_LOSS_RATIO", 0.99)))
        self.settings_trailing_callback_rate.setText(str(self.strategy_settings.get("TRAILING_CALLBACK_RATE", 0.5)))
        self.settings_hedge_reduction_steps.setText(str(self.strategy_settings.get("HEDGE_REDUCTION_STEPS", 3)))
        self.settings_test_quantity_mode.setChecked(self.strategy_settings.get("TEST_QUANTITY_MODE", False))
        # 헷지 프로토콜 항상 활성화 (체크박스 제거됨)
        self.settings_hedge_protocol_retracement.setText(str(self.strategy_settings.get("HEDGE_PROTOCOL_RETRACEMENT", 50.0)))
        self.settings_hedge_protocol_tp_ratio.setText(str(self.strategy_settings.get("HEDGE_PROTOCOL_TAKE_PROFIT_RATIO", 50.0)))
        self.settings_main_liquidation_safety_margin.setText(str(self.strategy_settings.get("MAIN_LIQUIDATION_SAFETY_MARGIN", 0.5)))
        self.settings_hedge_liquidation_safety_margin.setText(str(self.strategy_settings.get("HEDGE_LIQUIDATION_SAFETY_MARGIN", 0.5)))
        self.settings_hedge_frontload.setChecked(self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False))
        self.settings_reserve_fund_ratio.setText(str(self.strategy_settings.get("RESERVE_FUND_RATIO", 0.0)))
        self.settings_reserve_fund_loss_threshold.setText(str(self.strategy_settings.get("RESERVE_FUND_USAGE_LOSS_THRESHOLD", 10.0)))

        old_tf = self.current_interval
        self.current_interval = app_settings.get("last_timeframe", self.current_interval)

        # 저장된 심볼 로드
        saved_symbol = app_settings.get("last_symbol", self.current_symbol)
        if saved_symbol != self.current_symbol:
            self.current_symbol = saved_symbol
            if hasattr(self, 'symbol_combo'):
                self.symbol_combo.setCurrentText(self.current_symbol)

        print(f"{len(self.accounts)}개의 계정을 로드했습니다.")
        print(f"저장된 타임프레임 로드: {self.current_interval}")
        print(f"저장된 심볼 로드: {self.current_symbol}")
        self.rebuild_account_list_ui()
        self.update_timeframe_buttons(self.current_interval, old_tf)

        # v7_dual: 각 패널의 계정 콤보박스 채우기
        self.populate_account_combos()

        # Lock Mode 상태 복원
        lock_mode_enabled = app_settings.get("lock_mode_enabled", False)
        chart_x_range = app_settings.get("chart_x_range", None)
        chart_x_min = app_settings.get("chart_x_min", None)
        chart_x_max = app_settings.get("chart_x_max", None)
        lock_mode_x_min = app_settings.get("lock_mode_x_min", None)
        lock_mode_x_max = app_settings.get("lock_mode_x_max", None)

        # Chart Visible 상태 복원
        chart_visible = app_settings.get("chart_visible", True)  # 기본값: 표시
        if not chart_visible:
            self.chart_visible_button.setChecked(False)
            self.chart_widget.hide()
            self.chart_visible_button.setText("📉 Chart OFF")
            print("저장된 Chart Visible 상태 복원: 숨김")

        if lock_mode_enabled:
            for btn in self.lock_mode_buttons.values():
                btn.setChecked(True)

            # 저장된 차트 X축 범위 복원 (최소값 검증: 타임프레임 × 5개 캔들)
            min_range = self._get_min_chart_range_seconds()
            if chart_x_range is not None and chart_x_range >= min_range:
                self.lock_mode_x_range = chart_x_range
                print(f"저장된 차트 X축 범위 복원 (Lock Mode): {chart_x_range:.2f}초 (최소: {min_range:.0f}초)")
            elif chart_x_range is not None:
                print(f"[경고] 저장된 차트 X축 범위가 너무 작습니다 ({chart_x_range:.2f}초 < {min_range:.0f}초). 기본값 사용.")
                self.lock_mode_x_range = None

            # Lock Mode ON: 드래그 위치 복원
            if lock_mode_x_min is not None and lock_mode_x_max is not None:
                self.lock_mode_saved_x_min = lock_mode_x_min
                self.lock_mode_saved_x_max = lock_mode_x_max
                self.lock_mode_needs_first_restore = True  # 첫 차트 업데이트에서 위치 복원 필요
                print(f"저장된 차트 위치 복원 (Lock Mode ON): X축 범위 [{lock_mode_x_min:.2f} ~ {lock_mode_x_max:.2f}]")

            # config 복원으로 인한 호출임을 명시 (복원 플래그를 유지하기 위해)
            self.toggle_lock_mode(True, from_config_restore=True)
        else:
            # Lock Mode OFF: 차트 위치(X축 min/max) 복원
            if chart_x_min is not None and chart_x_max is not None:
                self.saved_chart_x_min = chart_x_min
                self.saved_chart_x_max = chart_x_max
                print(f"저장된 차트 위치 복원 (Lock Mode OFF): X축 범위 [{chart_x_min:.2f} ~ {chart_x_max:.2f}]")
            else:
                self.saved_chart_x_min = None
                self.saved_chart_x_max = None

        # v7_dual: 저장된 마지막 연결 계정 자동 연결 (side별)
        for side in ['long', 'short']:
            last_account_key = f"last_connected_account_{side}"
            last_market_key = f"last_connected_market_{side}"
            last_exchange_key = f"last_connected_exchange_{side}"

            last_account = app_settings.get(last_account_key)
            last_market = app_settings.get(last_market_key)
            last_exchange = app_settings.get(last_exchange_key)

            if last_account and last_market and last_exchange:
                # 계정이 아직 존재하는지 확인
                if last_account in self.accounts:
                    print(f"[{side.upper()}] 마지막 연결 계정 복원: {last_account} ({last_exchange} - {last_market})")
                    self.current_account_names[side] = last_account
                else:
                    print(f"[{side.upper()}] 마지막 연결 계정 '{last_account}'을(를) 찾을 수 없습니다.")

        # Statistics 데이터 복원
        self.load_statistics_data()

        # 자동 연결 시작 (UI 초기화 후 실행)
        QTimer.singleShot(500, self.auto_connect_last_accounts)

    def auto_connect_last_accounts(self):
        """마지막 연결 계정에 자동 연결"""
        print("[자동 연결] 마지막 연결 계정 연결 시작...")
        
        for side in ['long', 'short']:
            account_name = self.current_account_names.get(side)
            if account_name and account_name in self.accounts:
                print(f"[{side.upper()}] 자동 연결: {account_name}")
                self.on_connect_button_clicked(side)
            else:
                print(f"[{side.upper()}] 자동 연결 스킵: 계정이 설정되지 않음")

    def rebuild_account_list_ui(self):
        while self.account_list_layout.count():
            child = self.account_list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for account_name, account_data in self.accounts.items():
            account_widget = QWidget(); row_layout = QHBoxLayout(account_widget)
            label = QLabel(account_name); label.setMinimumWidth(150)
            
            saved_exchange = account_data.get('exchange', 'Binance')
            exchange_label = QLabel(f"<b>{saved_exchange}</b>")
            exchange_label.setFixedWidth(60)

            saved_email = account_data.get('email', '')
            email_label = QLabel(saved_email if saved_email else "-")
            email_label.setStyleSheet("color: #888888; font-size: 8pt;")
            email_label.setFixedWidth(150)

            market_combo = QComboBox(); market_combo.addItems(["USDⓈ-M (fapi)", "COIN-M (dapi)"])
            saved_market = account_data.get('market', 'fapi')
            market_combo.setCurrentIndex(1 if saved_market == 'dapi' else 0)
            market_combo.currentIndexChanged.connect(lambda index, name=account_name: self.on_market_changed(name, index))
            
            connect_btn = QPushButton("🔌 Connect")
            connect_btn.clicked.connect(lambda _, name=account_name, combo=market_combo, exch=saved_exchange: self.connect_to_api(name, "dapi" if combo.currentIndex() == 1 else "fapi", exch))
            
            edit_btn = QPushButton("✏️ Edit"); edit_btn.clicked.connect(lambda _, name=account_name: self.on_edit_account_clicked(name))
            delete_btn = QPushButton("❌ Delete"); delete_btn.clicked.connect(lambda _, name=account_name: self.delete_account(name))
            
            row_layout.addWidget(label)
            row_layout.addWidget(email_label)
            row_layout.addStretch(1)
            row_layout.addWidget(exchange_label)
            row_layout.addWidget(market_combo) 
            row_layout.addWidget(edit_btn); row_layout.addWidget(connect_btn); row_layout.addWidget(delete_btn)
            self.account_list_layout.addWidget(account_widget)
            
        self.account_list_layout.addStretch(1)

    def on_edit_account_clicked(self, account_name):
        if account_name in self.accounts:
            account_data = self.accounts[account_name]
            
            saved_exchange = account_data.get('exchange', 'Binance')
            index = self.new_exchange_combo.findText(saved_exchange)
            if index != -1:
                self.new_exchange_combo.setCurrentIndex(index)
            
            self.new_account_name_input.setText(account_name); self.new_api_key_input.setText(account_data.get('api_key', ''))
            self.new_api_secret_input.setText(account_data.get('api_secret', ''))
            self.new_email_input.setText(account_data.get('email', ''))
            
    def on_market_changed(self, account_name, index):
        market_type = "dapi" if index == 1 else "fapi"
        if account_name in self.accounts:
            self.accounts[account_name]['market'] = market_type
            config_manager.save_config_data(self.config_data)

    def add_new_account(self):
        exchange = self.new_exchange_combo.currentText()
        name = self.new_account_name_input.text().strip(); key = self.new_api_key_input.text().strip(); secret = self.new_api_secret_input.text().strip()
        email = self.new_email_input.text().strip()
        if not name or not key or not secret: QMessageBox.warning(self, "Input Error", "Account Name, API Key, and Secret are all required."); return
        existing_market = self.accounts.get(name, {}).get('market', 'fapi')
        self.accounts[name] = {
            "api_key": key,
            "api_secret": secret,
            "market": existing_market,
            "exchange": exchange,
            "email": email
        }
        config_manager.save_config_data(self.config_data); self.rebuild_account_list_ui()
        self.new_account_name_input.clear(); self.new_api_key_input.clear(); self.new_api_secret_input.clear(); self.new_email_input.clear()

    def delete_account(self, account_name):
        reply = QMessageBox.question(self, "Delete Account", f"Are you sure you want to delete '{account_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if account_name in self.accounts:
                del self.accounts[account_name]
                config_manager.save_config_data(self.config_data)
                self.rebuild_account_list_ui()


    def connect_to_api(self, account_name, market_type, exchange="Binance"):
        """'Connect' 버튼 클릭 시, 워커 스레드를 시작하고 오버레이를 표시합니다."""

        if self.connect_thread and self.connect_thread.isRunning():
            self.connect_thread.stop()
            self.connect_thread.wait()

        # 현재 계정 이름 저장 (심볼 기억용)
        self.current_account_name = account_name

        # 계정별 마지막 심볼 불러오기
        if "account_last_symbols" not in self.config_data:
            self.config_data["account_last_symbols"] = {}

        # 이 계정의 마지막 심볼이 있으면 복원
        if account_name in self.config_data["account_last_symbols"]:
            last_symbol = self.config_data["account_last_symbols"][account_name]
            self.current_symbol = last_symbol
            print(f"[계정 연결] {account_name}의 마지막 심볼 복원: {last_symbol}")

            # 심볼 콤보박스 업데이트
            if hasattr(self, 'symbol_combo'):
                self.symbol_combo.blockSignals(True)
                self.symbol_combo.setCurrentText(last_symbol)
                self.symbol_combo.blockSignals(False)

        try:
            self.base_loading_text = f"Connecting to {account_name} ({exchange} - {market_type})"
            self.loading_animation_state = 0

            self.loading_overlay.resize(self.tabs.size())
            self.loading_overlay.raise_()
            self.animate_loading_text()
            self.loading_overlay.show()

            self.loading_animation_timer.start(500)
            QApplication.processEvents()
        except Exception as e:
            print(f"오버레이 표시 오류: {e}")

        old_ws = self.ws_thread
        old_ticker = self.ticker_thread

        self.ws_thread = None
        self.ticker_thread = None

        self.remove_all_position_lines_from_chart()
        # 차트 타이머는 SingleShot으로 자동 관리되므로 별도 중지 불필요
        if self.balance_refresh_timer:
            self.balance_refresh_timer.stop()

        if self.api_module:
            self.api_module.set_active_api_keys(None, None)
        self.api_module = None # API 모듈 초기화

        self.position_table.setRowCount(0)
        self.order_table.setRowCount(0)
        self.live_position_data.clear()
        self.live_balances.clear() # [신규] 잔액 데이터 초기화

        # [신규] 잔액 라벨 초기화
        if hasattr(self, 'balance_label') and self.balance_label:
            self.balance_label.setText("Loading...")

        # 사이클/손익 라벨 초기화
        if hasattr(self, 'cycle_pnl_label') and self.cycle_pnl_label:
            self.update_cycle_pnl_display()

        self.current_market_type = market_type
        self.detected_precision = None
        self.y_axis.setPrecision(2)

        if self.candlestick_item:
            self.candlestick_item.setData(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
        if self.price_line_item:
            self.price_line_item.hide()

        self.connection_status_label.setText(f"Connecting...")
        self.connection_status_label.setStyleSheet("color: blue;")
        self.tabs.setCurrentWidget(self.chart_tab)

        self.connect_thread = ConnectAPIThread(
            accounts=self.accounts,
            account_name=account_name,
            market_type=market_type,
            current_interval=self.current_interval,
            old_ws_thread=old_ws,
            old_ticker_thread=old_ticker,
            exchange=exchange,
            current_symbol=self.current_symbol,  # GUI에서 선택한 심볼 전달 (복원된 심볼 포함)
            side='long'  # v7_dual: 기존 연결은 LONG 패널로 라우팅
        )
        # v7_dual: 기존 시그니처 유지하지만 내부적으로 long 패널 사용
        self.connect_thread.connection_finished.connect(
            lambda side, result: self.on_connection_finished(result) if side == 'long' else None
        )
        self.connect_thread.start()

    def connect_to_api_for_side(self, side, account_name, market_type, exchange="Binance"):
        """
        v7_dual: 특정 패널(LONG/SHORT)에 대한 API 연결을 시작합니다.

        Args:
            side: 'long' 또는 'short'
            account_name: 연결할 계정 이름
            market_type: 시장 타입 (예: 'fapi')
            exchange: 거래소 이름 (예: 'Binance', 'Bybit')
        """
        # 기존 연결 스레드가 있으면 중지
        if side in self.connect_threads and self.connect_threads[side] and self.connect_threads[side].isRunning():
            self.connect_threads[side].stop()
            self.connect_threads[side].wait()

        # 현재 계정 이름 저장 (심볼 기억용)
        self.current_account_names[side] = account_name

        # 계정별 마지막 심볼 불러오기
        if "account_last_symbols" not in self.config_data:
            self.config_data["account_last_symbols"] = {}

        # 이 계정의 마지막 심볼이 있으면 복원
        if side == 'short' and 'long' in self.current_symbols:
            last_symbol = self.current_symbols['long']
            self.current_symbols['short'] = last_symbol
            print(f"[{side.upper()} 패널] LONG 패널의 심볼로 강제 동기화: {last_symbol}")
        elif account_name in self.config_data.get("account_last_symbols", {}):
            last_symbol = self.config_data["account_last_symbols"][account_name]
            self.current_symbols[side] = last_symbol
            print(f"[{side.upper()} 패널] {account_name}의 마지막 심볼 복원: {last_symbol}")

            # 심볼 콤보박스 업데이트 (해당 side의 콤보박스)
            if side in self.symbol_combos and self.symbol_combos[side]:
                self.symbol_combos[side].blockSignals(True)
                self.symbol_combos[side].setCurrentText(last_symbol)
                self.symbol_combos[side].blockSignals(False)

        try:
            # 로딩 오버레이 표시 (필요시 side별 오버레이 구현 가능)
            self.base_loading_text = f"[{side.upper()}] Connecting to {account_name} ({exchange} - {market_type})"
            self.loading_animation_state = 0

            self.loading_overlay.resize(self.tabs.size())
            self.loading_overlay.raise_()
            self.animate_loading_text()
            self.loading_overlay.show()

            self.loading_animation_timer.start(500)
            QApplication.processEvents()
        except Exception as e:
            print(f"[{side.upper()}] 오버레이 표시 오류: {e}")

        # 기존 WebSocket/Ticker 스레드 저장
        old_ws = self.ws_threads.get(side)
        old_ticker = self.ticker_threads.get(side)

        # 초기화
        self.ws_threads[side] = None
        self.ticker_threads[side] = None

        # 차트 정리 (해당 side)
        # remove_all_position_lines_from_chart는 전역이므로 side별 구현 필요 시 수정
        # 일단 기본 동작 유지

        # API 모듈 초기화
        if self.api_modules.get(side):
            self.api_modules[side].set_active_api_keys(None, None)
        self.api_modules[side] = None

        # 테이블 초기화
        if side in self.position_tables and self.position_tables[side]:
            self.position_tables[side].setRowCount(0)
        if side in self.order_tables and self.order_tables[side]:
            self.order_tables[side].setRowCount(0)

        # 데이터 초기화
        self.live_position_data_by_side[side].clear()
        self.live_balances_by_side[side].clear()

        # 라벨 초기화
        if side in self.balance_labels and self.balance_labels[side]:
            self.balance_labels[side].setText(f"{side.upper()}: Loading...")

        # 사이클/손익 라벨 초기화 (side별 구현 필요시 수정)
        # 일단 기본 동작 유지

        self.current_market_types[side] = market_type

        # 차트 초기화
        if side in self.candlestick_items and self.candlestick_items[side]:
            self.candlestick_items[side].setData(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
        if side in self.price_line_items and self.price_line_items[side]:
            self.price_line_items[side].hide()

        # 연결 상태 라벨 업데이트 (side별 라벨 필요시 추가)
        if side in self.connection_status_labels and self.connection_status_labels[side]:
            self.connection_status_labels[side].setText(f"Connecting...")
            self.connection_status_labels[side].setStyleSheet("color: blue;")

        # Chart 탭으로 이동
        self.tabs.setCurrentWidget(self.chart_tab)

        # 연결 스레드 생성 및 시작
        self.connect_threads[side] = ConnectAPIThread(
            accounts=self.accounts,
            account_name=account_name,
            market_type=market_type,
            current_interval=self.current_interval,
            old_ws_thread=old_ws,
            old_ticker_thread=old_ticker,
            exchange=exchange,
            current_symbol=self.current_symbols.get(side, "BTCUSDT"),
            side=side  # v7_dual: side 파라미터 전달
        )
        self.connect_threads[side].connection_finished.connect(self.on_connection_finished_for_side)
        self.connect_threads[side].start()


    @pyqtSlot(dict)
    def on_connection_finished(self, result):
        """ConnectAPIThread가 완료되면 호출되어 GUI를 갱신합니다."""

        print(f"[연결] on_connection_finished 호출됨: success={result.get('success')}")

        self.loading_animation_timer.stop()
        self.loading_overlay.hide()
        QApplication.processEvents()

        try:
            if not result['success']:
                print(f"[연결] 연결 실패: {result.get('error')}")
                raise Exception(result.get('error', 'Unknown thread error'))

            print("[디버그] 1. 데이터 추출 시작")
            data = result['data']
            self.listen_key = data['listen_key']
            balance_info = data['balance_info'] # [수정]
            positions = data['positions']
            orders = data['orders']
            self.current_symbol = data['current_symbol']
            klines = data['klines']

            # 실제 사용된 market_type으로 업데이트 (Binance의 경우 심볼 기반 자동 감지됨)
            self.current_market_type = data['market_type']

            print("[디버그] 2. 스레드 객체 저장")
            self.ws_thread = data['new_ws_thread']
            self.ticker_thread = data['new_ticker_thread']

            print("[디버그] 3. 초기 데이터 채우기 시작")
            # ▼▼▼ [수정] 잔액 및 테이블 채우기 ▼▼▼
            self.populate_initial_balance(balance_info)
            self.populate_initial_positions(positions)
            self.populate_initial_orders(orders)
            print("[디버그] 4. 초기 데이터 채우기 완료")

            print("[디버그] 5. 차트 및 API 설정 시작")
            if self.current_market_type == 'dapi':
                precision = 2 if "USD" in self.current_symbol else 8
            else:
                precision = 2
            self.y_axis.setPrecision(precision)
            self.api_module = data['api_module']
            self.update_chart(self.current_symbol, self.current_interval, klines_data=klines, is_refresh=False)

            self.order_symbol_input.setText(self.current_symbol)
            print("[디버그] 6. 차트 업데이트 완료")

            print("[디버그] 7. WebSocket 스레드 시작")
            self.ws_thread.account_update_received.connect(self.handle_account_update)
            self.ws_thread.order_update_received.connect(self.handle_order_update)
            self.ws_thread.start()

            print("[디버그] 8. 티커 스레드 시작")
            self.ticker_thread.ticker_update.connect(self.handle_ticker_update)
            self.ticker_thread.start()
            print("[디버그] 9. 모든 스레드 시작 완료")

            print("[디버그] 10. Bybit 캔들 WebSocket 확인 중...")
            # Bybit 실시간 캔들 WebSocket 시작 (거래소와 완벽 동기화)
            if data['exchange'] == "Bybit":
                print("[디버그] 10-1. Bybit 캔들 WebSocket 시작")
                # 타임프레임을 Bybit 형식으로 변환 (5m -> 5)
                bybit_interval = self._convert_interval_to_bybit(self.current_interval)

                from v7_dual_ticker_ws import BybitKlineSocketThread
                self.kline_thread = BybitKlineSocketThread(
                    market_type=data['market_type'],
                    symbol=self.current_symbol,
                    interval=bybit_interval,
                    parent=self
                )
                self.kline_thread.kline_update.connect(self.handle_kline_update)
                self.kline_thread.start()
                print(f"[캔들 WebSocket] Bybit 실시간 캔들 스트림 시작: {self.current_symbol}/{bybit_interval}")

            print("[디버그] 11. 차트 타이머 시작")
            # 차트 갱신 타이머 시작 (SingleShot 재귀 방식, 타임프레임 00초 정렬)
            # Bybit은 WebSocket으로 실시간 업데이트되므로 타이머는 백업용
            self._start_chart_timer_aligned()
            print(f"차트 갱신 타이머 ({self.current_interval}) 시작 (타임프레임 00초 정렬).")

            print("[디버그] 12. 잔액 타이머 초기화")
            # 잔액 디바운스 타이머 초기화 (체결 메시지 후 5초 대기)
            self.balance_refresh_timer = QTimer(self)
            self.balance_refresh_timer.setSingleShot(True)  # 1회만 실행
            self.balance_refresh_timer.timeout.connect(self.refresh_balance)

            # 비축금 주기적 폴링 타이머 (60초 주기)
            self.reserve_fund_poll_timer = QTimer(self)
            self.reserve_fund_poll_timer.timeout.connect(self.fetch_reserve_fund_balances)
            self.reserve_fund_poll_timer.start(60000)
            # 첫 연결 시 즉시 폴링
            QTimer.singleShot(1000, self.fetch_reserve_fund_balances)

            print("[디버그] 13. 연결 상태 표시")
            self.connection_status_label.setText(f"✅ Connected to {self.connect_thread.account_name} ({self.current_market_type})")

            print("[디버그] 14. 설정 저장 시작")
            # 마지막 연결 정보 저장
            if "app_settings" not in self.config_data:
                self.config_data["app_settings"] = {}
            self.config_data["app_settings"]["last_connected_account"] = self.connect_thread.account_name
            self.config_data["app_settings"]["last_connected_market"] = self.current_market_type
            self.config_data["app_settings"]["last_connected_exchange"] = self.connect_thread.exchange
            config_manager.save_config_data(self.config_data)
            print(f"마지막 연결 정보 저장: {self.connect_thread.account_name} ({self.connect_thread.exchange} - {self.current_market_type})")

            print("[디버그] 15. DCA 복구 준비")
            # 저장된 DCA 상태 확인 (API로 이미 포지션 로드 완료)
            # WebSocket이 초기 스냅샷을 보내지 않을 수 있으므로 API 로드 직후 실행
            self.position_loaded = True  # API로 이미 로드됨
            self.dca_restore_check_pending = False
            print("[DCA 복구] API로 포지션 로드 완료. 복구 확인 시작...")
            QTimer.singleShot(500, self.check_and_restore_dca_state)  # 0.5초 후 실행 (UI 초기화 대기)
            print("[디버그] 16. DCA 복구 스케줄링 완료")

        except Exception as e:
            import traceback
            print(f"[오류] on_connection_finished 예외 발생: {e}")
            print(f"[오류] 트레이스백:\n{traceback.format_exc()}")
            self.api_module = None
            self.connection_status_label.setText(f"❌ Connection failed: {e}")
            self.connection_status_label.setStyleSheet("color: red;")

    @pyqtSlot(str, dict)
    def on_connection_finished_for_side(self, side, result):
        """
        v7_dual: ConnectAPIThread가 완료되면 호출되어 특정 패널(LONG/SHORT)의 GUI를 갱신합니다.

        Args:
            side: 'long' 또는 'short'
            result: 연결 결과 딕셔너리
        """
        print(f"[{side.upper()} 패널] on_connection_finished_for_side 호출됨: success={result.get('success')}")

        self.loading_animation_timer.stop()
        self.loading_overlay.hide()
        QApplication.processEvents()

        try:
            if not result['success']:
                print(f"[{side.upper()} 패널] 연결 실패: {result.get('error')}")
                raise Exception(result.get('error', 'Unknown thread error'))

            print(f"[{side.upper()} 패널] 1. 데이터 추출 시작")
            data = result['data']
            listen_key = data['listen_key']
            balance_info = data['balance_info']
            positions = data['positions']
            orders = data['orders']
            current_symbol = data['current_symbol']
            klines = data['klines']

            # 실제 사용된 market_type으로 업데이트
            self.current_market_types[side] = data['market_type']
            self.current_symbols[side] = current_symbol

            print(f"[{side.upper()} 패널] 2. 스레드 객체 저장")
            self.ws_threads[side] = data['new_ws_thread']
            self.ticker_threads[side] = data['new_ticker_thread']

            print(f"[{side.upper()} 패널] 3. 초기 데이터 채우기 시작")
            # Side별 데이터 채우기 (Phase 7에서 구현 예정)
            self.populate_initial_balance_for_side(side, balance_info)
            self.populate_initial_positions_for_side(side, positions)
            self.populate_initial_orders_for_side(side, orders)
            print(f"[{side.upper()} 패널] 4. 초기 데이터 채우기 완료")

            print(f"[{side.upper()} 패널] 5. 차트 및 API 설정 시작")
            self.api_modules[side] = data['api_module']

            # tickSize 기반 precision 설정
            api_module = data['api_module']
            category = 'linear' if self.current_market_types[side] in ['fapi', 'linear'] else 'inverse'
            try:
                symbol_info = api_module.get_instrument_info(category, current_symbol)
                if symbol_info:
                    tick_size = float(symbol_info.get('priceFilter', {}).get('tickSize', '0.01'))
                    import v7_dual_trading_utils as trading_utils
                    price_precision = trading_utils.count_decimal_places(tick_size)
                    self.price_precisions[side] = price_precision
                    print(f"[{side.upper()}] {current_symbol} precision 설정: {price_precision}자리 (tickSize: {tick_size})")

                    # Y축 precision 설정 (LONG 패널만, 차트 공유)
                    if side == 'long':
                        if self.y_axis:
                            self.y_axis.setPrecision(price_precision)
                        self.detected_precision = price_precision
                        print(f"[차트] Y축 precision을 {price_precision}자리로 설정")
            except Exception as e:
                print(f"[{side.upper()}] Symbol info 조회 실패: {e}")
                # 기본값 유지
                if side not in self.price_precisions:
                    self.price_precisions[side] = 2

            # Backward compatibility: LONG 패널 연결 시 레거시 참조 업데이트
            if side == 'long':
                self.api_module = data['api_module']
                self.connect_thread = self.connect_threads[side]
                self.current_symbol = current_symbol
                self.current_market_type = data['market_type']

            # Side별 차트 업데이트 (현재는 backward compatibility 사용)
            # TODO: update_chart를 side 파라미터를 받도록 수정 필요
            if side == 'long':  # 임시: LONG 패널만 차트 업데이트
                self.update_chart(current_symbol, self.current_interval, klines_data=klines, is_refresh=False)

            print(f"[{side.upper()} 패널] 6. 차트 업데이트 완료")

            print(f"[{side.upper()} 패널] 7. WebSocket 스레드 시작")
            self.ws_threads[side].account_update_received.connect(self.handle_account_update_for_side)
            self.ws_threads[side].order_update_received.connect(self.handle_order_update_for_side)
            self.ws_threads[side].start()

            print(f"[{side.upper()} 패널] 8. 티커 스레드 시작")
            self.ticker_threads[side].ticker_update.connect(lambda ticker_list, s=side: self.handle_ticker_update_for_side(s, ticker_list))
            # LONG 패널: 차트 업데이트도 연결 (price_line_item, 캔들 업데이트 등)
            if side == 'long':
                self.ticker_threads[side].ticker_update.connect(self.handle_ticker_update)
            self.ticker_threads[side].start()
            print(f"[{side.upper()} 패널] 9. 모든 스레드 시작 완료")

            print(f"[{side.upper()} 패널] 10. Bybit 캔들 WebSocket 확인 중...")
            # Bybit 실시간 캔들 WebSocket 시작
            if data['exchange'] == "Bybit":
                print(f"[{side.upper()} 패널] 10-1. Bybit 캔들 WebSocket 시작")
                bybit_interval = self._convert_interval_to_bybit(self.current_interval)

                from v7_dual_ticker_ws import BybitKlineSocketThread
                self.kline_threads[side] = BybitKlineSocketThread(
                    market_type=data['market_type'],
                    symbol=current_symbol,
                    interval=bybit_interval,
                    parent=self
                )
                self.kline_threads[side].kline_update.connect(lambda kline_data, s=side: self.handle_kline_update_for_side(s, kline_data))
                self.kline_threads[side].start()
                print(f"[{side.upper()} 패널] Bybit 실시간 캔들 스트림 시작: {current_symbol}/{bybit_interval}")

            # 차트 갱신 타이머 (side별 타이머 필요시 추가)
            # 일단 LONG 패널만 타이머 시작
            if side == 'long':
                print(f"[{side.upper()} 패널] 11. 차트 타이머 시작")
                self._start_chart_timer_aligned()
                print(f"차트 갱신 타이머 ({self.current_interval}) 시작")

            # 연결 상태 표시
            if side in self.connection_status_labels and self.connection_status_labels[side]:
                account_name = self.current_account_names.get(side, 'Unknown')
                market_type = self.current_market_types.get(side, 'Unknown')
                self.connection_status_labels[side].setText(f"✅ Connected to {account_name} ({market_type})")
                self.connection_status_labels[side].setStyleSheet("color: green;")

            # Account Settings 다이얼로그가 열려있으면 상태 업데이트
            self._update_account_dialog_status(side)

            # 마지막 연결 계정 저장 (side별)
            connect_thread = self.connect_threads.get(side)
            if connect_thread:
                if "app_settings" not in self.config_data:
                    self.config_data["app_settings"] = {}

                # Side별 마지막 연결 정보 저장
                last_connected_key = f"last_connected_account_{side}"
                last_market_key = f"last_connected_market_{side}"
                last_exchange_key = f"last_connected_exchange_{side}"

                self.config_data["app_settings"][last_connected_key] = connect_thread.account_name
                self.config_data["app_settings"][last_market_key] = self.current_market_types.get(side)
                self.config_data["app_settings"][last_exchange_key] = connect_thread.exchange

                config_manager.save_config_data(self.config_data)
                print(f"[{side.upper()}] 마지막 연결 정보 저장: {connect_thread.account_name} ({connect_thread.exchange} - {self.current_market_types.get(side)})")

            # DCA 상태 복구 확인 (API로 포지션 로드 완료 후)
            print(f"[{side.upper()} 패널] 15. DCA 복구 확인 시작")
            QTimer.singleShot(500, lambda s=side: self.check_and_restore_dca_state_for_side(s))

            print(f"[{side.upper()} 패널] 연결 완료")

        except Exception as e:
            import traceback
            print(f"[{side.upper()} 패널] on_connection_finished_for_side 예외 발생: {e}")
            print(f"[오류] 트레이스백:\n{traceback.format_exc()}")

            if self.api_modules.get(side):
                self.api_modules[side] = None

            if side in self.connection_status_labels and self.connection_status_labels[side]:
                self.connection_status_labels[side].setText(f"❌ Connection failed: {e}")
                self.connection_status_labels[side].setStyleSheet("color: red;")

    # === v7_dual: Side별 이벤트 핸들러 ===

    def on_connect_button_clicked(self, side):
        """Connect 버튼 클릭 핸들러 (side별) - 팝업 다이얼로그에서도 호출됨"""
        # 팝업 다이얼로그에서 호출된 경우, current_account_names에서 가져오기
        account_name = self.current_account_names.get(side)

        if not account_name:
            print(f"[{side.upper()}] No account selected")
            return

        # 계정 정보에서 exchange와 market_type 가져오기
        if account_name not in self.accounts:
            print(f"[{side.upper()}] Account '{account_name}' not found in config")
            return

        account_data = self.accounts[account_name]
        exchange = account_data.get('exchange', 'Binance')
        market_type = account_data.get('market_type', 'fapi')

        print(f"[{side.upper()}] Connecting to {account_name} ({exchange} - {market_type})")
        self.connect_to_api_for_side(side, account_name, market_type, exchange)

    def on_symbol_changed_for_side(self, side, new_symbol):
        """Symbol 변경 핸들러 (side별)"""
        old_symbol = self.current_symbols.get(side, "BTCUSDT")
        if old_symbol == new_symbol:
            return

        self.current_symbols[side] = new_symbol
        if side == 'long' and hasattr(self, 'order_symbol_input'):
            self.order_symbol_input.setText(new_symbol)
        print(f"[{side.upper()}] Symbol 변경: {old_symbol} → {new_symbol}")

        # 계정별 마지막 심볼 저장
        if "account_last_symbols" not in self.config_data:
            self.config_data["account_last_symbols"] = {}

        account_name = self.current_account_names.get(side)
        if account_name:
            self.config_data["account_last_symbols"][account_name] = new_symbol
            print(f"[{side.upper()}] {account_name} 계정의 심볼 저장: {new_symbol}")
            config_manager.save_config_data(self.config_data)

        # Phase 8: 심볼 동기화 - 다른 패널도 같은 심볼로 변경
        other_side = 'short' if side == 'long' else 'long'
        if other_side in self.current_symbols:
            old_other_symbol = self.current_symbols[other_side]
            if old_other_symbol != new_symbol:
                self.current_symbols[other_side] = new_symbol
                print(f"[심볼 동기화] {other_side.upper()} 패널도 {new_symbol}로 변경")

                # 다른 패널의 콤보박스도 업데이트
                if other_side in self.symbol_combos and self.symbol_combos[other_side]:
                    self.symbol_combos[other_side].blockSignals(True)
                    self.symbol_combos[other_side].setCurrentText(new_symbol)
                    self.symbol_combos[other_side].blockSignals(False)

                # 다른 패널의 계정도 저장
                other_account_name = self.current_account_names.get(other_side)
                if other_account_name:
                    self.config_data["account_last_symbols"][other_account_name] = new_symbol
                    config_manager.save_config_data(self.config_data)

                # 다른 패널의 WebSocket도 재시작 (중요!)
                self._restart_websockets_for_symbol(other_side, old_other_symbol, new_symbol)

        # Backward compatibility: LONG 패널 변경 시 self.current_symbol도 업데이트
        if side == 'long':
            self.current_symbol = new_symbol

        # 차트 및 WebSocket 재시작 (현재 패널)
        self._restart_websockets_for_symbol(side, old_symbol, new_symbol)

    def _restart_websockets_for_symbol(self, side, old_symbol, new_symbol):
        """
        심볼 변경 시 WebSocket 스레드 재시작

        Args:
            side: 'long' 또는 'short'
            old_symbol: 이전 심볼
            new_symbol: 새 심볼
        """
        # Symbol info 가져와서 precision 업데이트
        api_module = self.api_modules.get(side)
        if api_module and api_module.is_api_key_active():
            try:
                # Symbol info 조회
                category = self.current_market_types.get(side, 'linear')
                if category in ['fapi', 'linear']:
                    category = 'linear'
                elif category in ['dapi', 'inverse']:
                    category = 'inverse'

                symbol_info = api_module.get_instrument_info(category, new_symbol)
                if symbol_info:
                    tick_size = float(symbol_info.get('priceFilter', {}).get('tickSize', '0.01'))
                    import v7_dual_trading_utils as trading_utils
                    price_precision = trading_utils.count_decimal_places(tick_size)
                    self.price_precisions[side] = price_precision
                    print(f"[{side.upper()}] {new_symbol} precision 업데이트: {price_precision}자리")
            except Exception as e:
                print(f"[{side.upper()}] Symbol info 조회 실패: {e}")

        # 차트 업데이트 (현재는 LONG 패널만)
        if side == 'long':
            if api_module and api_module.is_api_key_active():
                interval = self.current_interval
                print(f"[{side.upper()}] 심볼 변경으로 차트 업데이트: {new_symbol} / {interval}")
                self.update_chart(new_symbol, interval)

        # 티커 스레드 재시작
        if side in self.ticker_threads and self.ticker_threads[side]:
            old_ticker = self.ticker_threads[side]
            print(f"[{side.upper()}] 티커 스레드 재시작: {old_symbol} → {new_symbol}")

            # 기존 티커 스레드 종료
            if old_ticker.isRunning():
                old_ticker.stop()
                old_ticker.wait()
                print(f"[{side.upper()}] 기존 티커 스레드 종료 완료")

            # 레거시 티커 스레드 정리 (중복 스트리밍 방지)
            if side == 'long' and hasattr(self, 'ticker_thread') and self.ticker_thread and self.ticker_thread != old_ticker:
                if self.ticker_thread.isRunning():
                    self.ticker_thread.stop()
                    self.ticker_thread.wait()
                    print(f"[{side.upper()}] 기존 레거시 티커 스레드 종료 완료")

            # 새로운 티커 스레드 생성
            market_type = self.current_market_types.get(side, 'linear')
            connect_thread = self.connect_threads.get(side)
            if connect_thread:
                exchange = connect_thread.exchange
                if exchange == "Binance":
                    from v7_dual_ticker_ws import TickerSocketThread
                    new_ticker = TickerSocketThread(market_type, new_symbol)
                elif exchange == "Bybit":
                    from v7_dual_ticker_ws import BybitTickerSocketThread
                    new_ticker = BybitTickerSocketThread(market_type, new_symbol)
                else:
                    print(f"[{side.upper()}] 지원되지 않는 거래소: {exchange}")
                    return

                # 시그널 연결 및 시작
                new_ticker.ticker_update.connect(lambda ticker_list, s=side: self.handle_ticker_update_for_side(s, ticker_list))
                # LONG 패널: 차트 업데이트도 연결 (price_line_item, 캔들 업데이트 등)
                if side == 'long':
                    new_ticker.ticker_update.connect(self.handle_ticker_update)
                new_ticker.start()
                self.ticker_threads[side] = new_ticker
                print(f"[{side.upper()}] 새 티커 스레드 시작 완료: {new_symbol}")

                # Backward compatibility
                if side == 'long':
                    self.ticker_thread = new_ticker

        # Kline 스레드 재시작 (Bybit만)
        if side in self.kline_threads and self.kline_threads[side]:
            old_kline = self.kline_threads[side]
            market_type = self.current_market_types.get(side, 'linear')
            connect_thread = self.connect_threads.get(side)

            if connect_thread and connect_thread.exchange == "Bybit":
                print(f"[{side.upper()}] Kline 스레드 재시작: {old_symbol} → {new_symbol}")

                # 기존 Kline 스레드 종료
                if old_kline.isRunning():
                    old_kline.stop()
                    old_kline.wait()
                    print(f"[{side.upper()}] 기존 Kline 스레드 종료 완료")

                # 새로운 Kline 스레드 생성
                interval = self.current_interval
                bybit_interval = self._convert_interval_to_bybit(interval)
                from v7_dual_ticker_ws import BybitKlineSocketThread
                new_kline = BybitKlineSocketThread(
                    market_type=market_type,
                    symbol=new_symbol,
                    interval=bybit_interval,
                    parent=self
                )
                new_kline.kline_update.connect(lambda kline_data, s=side: self.handle_kline_update_for_side(s, kline_data))
                new_kline.start()
                self.kline_threads[side] = new_kline
                print(f"[{side.upper()}] 새 Kline 스레드 시작 완료: {new_symbol}/{bybit_interval}")

                # Backward compatibility
                if side == 'long':
                    self.kline_thread = new_kline

    def on_direction_changed_for_side(self, side, direction):
        """Direction 변경 핸들러 (side별)"""
        old_direction = self.side_modes.get(side, "LONG")
        if old_direction == direction:
            return

        self.side_modes[side] = direction
        print(f"[{side.upper()} 패널] Direction 변경: {old_direction} → {direction}")

        # Start/Stop 버튼 텍스트 업데이트
        if side in self.auto_trade_start_buttons and self.auto_trade_start_buttons[side]:
            self.auto_trade_start_buttons[side].setText(f"Start {direction}")
        if side in self.auto_trade_stop_buttons and self.auto_trade_stop_buttons[side]:
            self.auto_trade_stop_buttons[side].setText(f"Stop {direction}")

        # Auto-Trade Worker가 있으면 방향 업데이트
        if side in self.auto_trade_workers and self.auto_trade_workers[side]:
            self.auto_trade_workers[side].side_mode = direction
            print(f"[{side.upper()} 패널] AutoTradeWorker 방향 업데이트: {direction}")

        # 설정 저장 (선택사항)
        if "panel_directions" not in self.config_data:
            self.config_data["panel_directions"] = {}
        self.config_data["panel_directions"][side] = direction
        config_manager.save_config_data(self.config_data)

    def on_market_type_changed_for_side(self, side, text):
        """Market Type 변경 핸들러 (side별)"""
        # "Linear (USDT)" -> 'linear', "Inverse (COIN)" -> 'inverse'
        if "Linear" in text:
            new_market = 'linear'
        else:
            new_market = 'inverse'

        old_market = self.market_type_modes.get(side, 'linear')
        if old_market == new_market:
            return

        self.market_type_modes[side] = new_market
        print(f"[{side.upper()} 패널] Market Type 변경: {old_market} → {new_market}")

        # 다른 패널도 동기화
        other_side = 'short' if side == 'long' else 'long'
        old_other_market = self.market_type_modes.get(other_side, 'linear')
        if old_other_market != new_market:
            self.market_type_modes[other_side] = new_market
            print(f"[Market Type 동기화] {other_side.upper()} 패널도 {new_market}로 변경")

            # 다른 패널의 콤보박스도 업데이트
            other_combo = self.market_type_combos.get(other_side)
            if other_combo:
                other_combo.blockSignals(True)
                if new_market == 'linear':
                    other_combo.setCurrentIndex(0)  # "Linear (USDT)"
                else:
                    other_combo.setCurrentIndex(1)  # "Inverse (COIN)"
                other_combo.blockSignals(False)

            # 다른 패널 설정도 저장
            if "panel_market_types" not in self.config_data:
                self.config_data["panel_market_types"] = {}
            self.config_data["panel_market_types"][other_side] = new_market

        # 설정 저장
        if "panel_market_types" not in self.config_data:
            self.config_data["panel_market_types"] = {}
        self.config_data["panel_market_types"][side] = new_market
        config_manager.save_config_data(self.config_data)

    def on_auto_trade_start_for_side(self, side):
        """Auto-Trade 시작 핸들러 (side별) - 사용자 클릭"""
        self._start_auto_trade_for_side(side, check_positions=True, skip_min_order_warning=False)

    def _start_auto_trade_for_side(self, side, check_positions=True, skip_min_order_warning=False):
        """
        자동매매 시작 (공통 로직, side별)

        Args:
            side: 'long' 또는 'short'
            check_positions: True면 포지션/주문 체크, False면 건너뛰기
            skip_min_order_warning: True면 최소 주문 금액 경고창 건너뛰기 (익절 후 재시작 시)
        """
        print(f"[{side.upper()}] Auto-Trade Start requested")

        # 0. API 연결 확인
        api_module = self.api_modules.get(side)
        if not api_module or not api_module.is_api_key_active():
            print(f"[{side.upper()}] Error: API not connected")
            return

        # 1. Bybit 확인 (Bybit만 지원)
        connect_thread = self.connect_threads.get(side)
        if not connect_thread or connect_thread.exchange != "Bybit":
            print(f"[{side.upper()}] Error: Only Bybit supported for Auto-Trade")
            return

        # 2. 현재 잔고 확인
        # 사용자가 선택한 market_type_modes를 우선 사용, 없으면 current_market_types 사용
        user_selected_market = self.market_type_modes.get(side)
        if user_selected_market:
            category = user_selected_market
        else:
            # 폴백: current_market_types에서 변환
            market_type = self.current_market_types.get(side, 'linear')
            if market_type in ['fapi', 'linear']:
                category = 'linear'
            elif market_type in ['dapi', 'inverse']:
                category = 'inverse'
            else:
                category = 'linear'

        # category에 따라 balance_asset 결정
        if category == 'linear':
            balance_asset = "USDT"
        else:  # inverse
            balance_asset = "BTC"

        live_balances = self.live_balances_by_side.get(side, {})
        balance_total_str = live_balances.get(balance_asset, "0.0")
        balance_total = float(balance_total_str)

        if balance_total <= 0.0:
            print(f"[{side.upper()}] Error: No {balance_asset} balance")
            return

        # 3. 포지션 및 미체결 주문 확인 (익절 후 재시작 시 건너뛰기)
        if check_positions:
            live_positions = self.live_position_data_by_side.get(side, {})
            if len(live_positions) > 0:
                QMessageBox.warning(
                    self,
                    "경고: 포지션 감지됨",
                    f"{side.upper()} panel: 포지션이 감지되었습니다. 포지션과 미체결 주문을 정리한 후 재시도하세요.",
                    QMessageBox.Ok
                )
                print(f"[{side.upper()}] Error: Existing positions detected")
                return

            try:
                open_orders = api_module.get_initial_open_orders()
                if open_orders and len(open_orders) > 0:
                    QMessageBox.warning(
                        self,
                        "경고: 미체결 주문 감지됨",
                        f"{side.upper()} panel: 미체결 주문이 감지되었습니다. 포지션과 미체결 주문을 정리한 후 다시 시도하세요.",
                        QMessageBox.Ok
                    )
                    print(f"[{side.upper()}] Error: Open orders detected")
                    return
            except Exception as e:
                print(f"[{side.upper()}] 미체결 주문 확인 오류: {e}")
                # 미체결 주문 확인 실패 시에도 포지션이 없으면 진행
        else:
            print(f"[{side.upper()}] 익절 후 재시작 - 포지션/주문 체크 건너뛰기")

        # 4. 설정 스레드 실행
        start_button = self.auto_trade_start_buttons.get(side)
        if start_button:
            start_button.setEnabled(False)
            start_button.setText("Setting up...")
        print(f"[{side.upper()}] Starting setup...")

        # 최소 주문 금액 경고창 건너뛰기 플래그 저장 (on_setup_finished_for_side에서 참조)
        if not hasattr(self, '_skip_min_order_warning_by_side'):
            self._skip_min_order_warning_by_side = {}
        self._skip_min_order_warning_by_side[side] = skip_min_order_warning

        # 현재 심볼
        current_symbol = self.current_symbols.get(side, "BTCUSDT")

        from v7_dual_setup_thread import SetupAutoTradeThread
        setup_thread = SetupAutoTradeThread(
            api_module=api_module,
            category=category,
            symbol=current_symbol,
            balance_asset=balance_asset,
            balance_total=balance_total,
            strategy_settings=self.strategy_settings,
            side=side
        )
        setup_thread.setup_finished.connect(lambda success, error_msg, params, s=side:
                                             self.on_setup_finished_for_side(s, success, error_msg, params))
        setup_thread.log_message.connect(lambda msg, s=side: self.on_auto_trade_log_for_side(s, msg))
        setup_thread.start()
        self.setup_threads[side] = setup_thread

    @pyqtSlot(str, bool, str, dict)
    def on_setup_finished_for_side(self, side, success, error_message, params):
        """설정 스레드 완료 시 (side별)"""
        start_button = self.auto_trade_start_buttons.get(side)

        if success:
            # 사용자 확인이 필요한 경우 (최소 주문 금액 이하인 헷지 주문이 있음)
            # 단, 익절 후 재시작 시에는 경고창 건너뛰기
            skip_warning = self._skip_min_order_warning_by_side.get(side, False)
            if params.get('needs_user_confirmation', False) and not skip_warning:
                warning_message = params.get('warning_message', '')
                reply = QMessageBox.warning(
                    self,
                    "경고: 최소 주문 금액 미달",
                    warning_message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.No:
                    # 사용자가 "아니오"를 선택 -> 자동매매 시작 취소
                    print(f"[{side.upper()}] 사용자가 최소 주문 금액 경고로 인해 자동매매를 취소했습니다.")
                    if start_button:
                        start_button.setEnabled(True)
                        direction = self.side_modes.get(side, 'LONG')
                        start_button.setText(f"Start {direction}")
                    return

                # 사용자가 "예"를 선택 -> 계속 진행
                print(f"[{side.upper()}] 사용자가 최소 주문 금액 경고에도 불구하고 진행을 선택했습니다.")
            elif skip_warning and params.get('needs_user_confirmation', False):
                print(f"[{side.upper()}] 익절 후 재시작 - 최소 주문 금액 경고창 건너뛰기")

            # 플래그 초기화 (다음 수동 시작 시에는 경고창 표시)
            self._skip_min_order_warning_by_side[side] = False

            print(f"[{side.upper()}] Setup Complete. Starting logic...")

            # Y축 및 Price precision 설정
            symbol_info = params.get('symbol_info', {})
            if symbol_info:
                tick_size = float(symbol_info.get('priceFilter', {}).get('tickSize', '0.01'))
                import v7_dual_trading_utils as trading_utils
                price_precision = trading_utils.count_decimal_places(tick_size)

                # side별 price precision 저장
                self.price_precisions[side] = price_precision
                print(f"[{side.upper()}] Price precision을 tickSize({tick_size})에 맞춰 {price_precision}자리로 설정")

                # Y축 precision 설정 (LONG 패널만, 차트 공유)
                if side == 'long':
                    if self.y_axis:
                        self.y_axis.setPrecision(price_precision)
                    self.detected_precision = price_precision
                    print(f"[차트] Y축 precision을 {price_precision}자리로 설정")

            # "Start" 버튼을 "Stop" 버튼으로 변경
            stop_button = self.auto_trade_stop_buttons.get(side)
            if start_button and stop_button:
                start_button.setEnabled(False)
                stop_button.setEnabled(True)

            # 시작 잔액 저장 (프로그램 최초 시작 시에만)
            # TODO: side별로 cycle_start_balance 관리 필요
            # if self.cycle_start_balance == 0.0:
            #     ...

            # '두뇌' 워커에게 계산된 파라미터를 전달하고 시작
            worker = self.auto_trade_workers.get(side)
            if worker:
                direction = self.side_modes.get(side, 'LONG')
                worker.start_trading(
                    params['symbol'],
                    params['entry_quantity'],
                    direction,
                    self.strategy_settings,  # 전략 설정 전달
                    0,  # 현재 스텝 (Step 0부터 시작)
                    self.strategy_settings.get("STEPS", 10),  # 전체 스텝 수
                    params.get('entry_qty_list', []),  # DCA 진입 수량 목록
                    params.get('hedge_qty_list', []),  # DCA 헷지 수량 목록
                    self.api_modules.get(side),  # API 모듈 (청산가 조회용)
                    params.get('symbol_info', {}),  # 심볼 정보 (tickSize, qtyStep 등)
                    params.get('category', 'linear'),  # 카테고리 (linear/inverse)
                    0  # 현재 가격 (TODO: 실시간 가격 전달)
                )
                print(f"[{side.upper()}] AutoTradeWorker started with DCA strategy")

                # 버튼을 Stop 상태로 변경
                if start_button:
                    start_button.setText(f"Stop {side.upper()}")
                    start_button.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #c00000; color: white;")
                    start_button.setEnabled(True)
        else:
            print(f"[{side.upper()}] Setup Failed: {error_message}")
            if start_button:
                start_button.setEnabled(True)
                start_button.setText(f"Start {side.upper()}")
                start_button.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #00b050; color: white;")

    def on_auto_trade_stop_for_side(self, side):
        """Auto-Trade 정지 핸들러 (side별)"""
        print(f"[{side.upper()}] Auto-Trade Stop requested")

        # Worker 정지
        worker = self.auto_trade_workers.get(side)
        if worker and worker.is_running:
            worker.stop_trading()
            print(f"[{side.upper()}] AutoTradeWorker stopped")

            # 버튼을 Start 상태로 변경
            if side in self.auto_trade_start_buttons:
                btn = self.auto_trade_start_buttons[side]
                btn.setText(f"Start {side.upper()}")
                btn.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #00b050; color: white;")
                btn.setEnabled(True)
        else:
            print(f"[{side.upper()}] Worker not running")

    def increment_cycle_count(self, side):
        """사이클 카운트 증가 및 라벨 업데이트"""
        self.cycles_by_side[side] = self.cycles_by_side.get(side, 0) + 1
        label = self.cycle_count_labels.get(side)
        if label:
            prefix = "L" if side == 'long' else "S"
            label.setText(f"{prefix}: Cycle {self.cycles_by_side[side]}")
        print(f"[{side.upper()}] 사이클 카운트: {self.cycles_by_side[side]}")

    def update_realized_pnl_display(self, side=None):
        """확정 PNL 라벨 업데이트 (side별 + TOTAL)"""
        try:
            sides_to_update = [side] if side else ['long', 'short']

            for s in sides_to_update:
                start_bal = self.start_balances_by_side.get(s, 0.0)
                if start_bal == 0.0:
                    continue

                market_type = self.current_market_types.get(s, 'fapi')
                if market_type == 'dapi':
                    asset_key = None
                    for a in ['BTC', 'ETH', 'USD']:
                        if a in self.live_balances_by_side[s]:
                            asset_key = a
                            break
                else:
                    asset_key = 'USDT'

                if not asset_key or asset_key not in self.live_balances_by_side[s]:
                    continue

                current_bal = float(self.live_balances_by_side[s][asset_key])
                pnl = current_bal - start_bal

                label = self.realized_pnl_labels.get(s)
                if label:
                    sign = "+" if pnl >= 0 else ""
                    color = "#00FF00" if pnl > 0 else "#FF4444" if pnl < 0 else "#888888"
                    prefix = "L" if s == 'long' else "S"
                    pnl_prec = 8 if market_type == 'dapi' else 4
                    label.setText(f"{prefix}: {sign}{pnl:.{pnl_prec}f}")
                    label.setStyleSheet(f"font-size: 10pt; font-weight: bold; color: {color};")

            # TOTAL 계산
            total_pnl = 0.0
            for s in ['long', 'short']:
                start_bal = self.start_balances_by_side.get(s, 0.0)
                if start_bal == 0.0:
                    continue
                market_type = self.current_market_types.get(s, 'fapi')
                asset_key = 'USDT' if market_type != 'dapi' else None
                if market_type == 'dapi':
                    for a in ['BTC', 'ETH', 'USD']:
                        if a in self.live_balances_by_side[s]:
                            asset_key = a
                            break
                if asset_key and asset_key in self.live_balances_by_side[s]:
                    current_bal = float(self.live_balances_by_side[s][asset_key])
                    total_pnl += current_bal - start_bal

            total_label = self.realized_pnl_labels.get('total')
            if total_label:
                sign = "+" if total_pnl >= 0 else ""
                color = "#00FF00" if total_pnl > 0 else "#FF4444" if total_pnl < 0 else "#888888"
                total_label.setText(f"TOTAL: {sign}{total_pnl:.4f}")
                total_label.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {color};")

        except Exception as e:
            print(f"[PNL] 확정 PNL 업데이트 오류: {e}")

    def on_clear_all_for_side(self, side):
        """Clear All 핸들러 - 포지션 청산 및 미체결 주문 취소 (side별)"""
        api_module = self.api_modules.get(side)
        if not api_module or not api_module.is_api_key_active():
            QMessageBox.warning(self, "Error", f"{side.upper()} 계정이 연결되지 않았습니다.")
            return

        symbol = self.current_symbols.get(side, "BTCUSDT")
        side_mode = self.side_modes.get(side, "LONG" if side == "long" else "SHORT")

        # 확인 다이얼로그
        reply = QMessageBox.question(
            self,
            f"Clear All {side.upper()}",
            f"{side.upper()} 계정의 {symbol} 모든 포지션을 청산하고\n미체결 주문을 취소하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        print(f"[{side.upper()}] Clear All 시작: {symbol}")

        # 1. 먼저 Worker 정지
        worker = self.auto_trade_workers.get(side)
        if worker and worker.is_running:
            worker.stop_trading()
            print(f"[{side.upper()}] AutoTradeWorker 정지됨")

        # 2. 미체결 주문 전체 취소
        try:
            print(f"[{side.upper()}] 미체결 주문 취소 중...")
            open_orders = api_module.get_initial_open_orders()
            if not open_orders:
                print(f"[{side.upper()}] 취소할 미체결 주문 없음")
            else:
                for order in open_orders:
                    order_symbol = str(order.get('symbol', ''))
                    if order_symbol != symbol:
                        continue
                    try:
                        order_id = str(order.get('orderId', ''))
                        order_category = order.get('orderCategory', 'normal')
                        api_module.cancel_order(order_symbol, order_id, order_category)
                        print(f"[{side.upper()}] 주문 취소: {order_symbol} #{order_id}")
                    except Exception as e:
                        print(f"[{side.upper()}] 주문 취소 실패 #{order.get('orderId')}: {e}")
                print(f"[{side.upper()}] 미체결 주문 취소 완료")
        except Exception as e:
            print(f"[{side.upper()}] 미체결 주문 취소 오류: {e}")

        # 3. 포지션 청산 (LONG과 SHORT 모두)
        try:
            print(f"[{side.upper()}] 포지션 청산 중...")
            positions = api_module.get_initial_positions()

            if positions:
                for pos in positions:
                    if pos.get('symbol') != symbol:
                        continue

                    pos_amt = float(pos.get('positionAmt', 0))
                    pos_side = pos.get('positionSide', 'BOTH')

                    if pos_amt == 0:
                        continue

                    # 포지션 청산 (반대 방향 주문)
                    if pos_amt > 0:  # LONG 포지션 -> SELL로 청산
                        order_side = "SELL"
                        qty = abs(pos_amt)
                    else:  # SHORT 포지션 -> BUY로 청산
                        order_side = "BUY"
                        qty = abs(pos_amt)

                    print(f"[{side.upper()}] {pos_side} 포지션 청산: {order_side} {qty} {symbol}")
                    result = api_module.place_market_order(
                        symbol, order_side, str(qty),
                        reduce_only=True,
                        position_side=pos_side
                    )

                    if result and result.get('orderId'):
                        print(f"[{side.upper()}] {pos_side} 포지션 청산 주문 완료: {result.get('orderId')}")
                    else:
                        print(f"[{side.upper()}] {pos_side} 포지션 청산 실패: {result}")

            print(f"[{side.upper()}] 포지션 청산 처리 완료")

        except Exception as e:
            print(f"[{side.upper()}] 포지션 청산 오류: {e}")
            import traceback
            traceback.print_exc()

        # 4. 버튼 상태 업데이트
        if side in self.auto_trade_start_buttons:
            btn = self.auto_trade_start_buttons[side]
            btn.setText(f"Start {side.upper()}")
            btn.setStyleSheet("font-size: 12pt; font-weight: bold; background-color: #00b050; color: white;")
            btn.setEnabled(True)

        # 5. 차트 마커 제거
        self.remove_uptrend_threshold_marker_for_side(side)
        self.remove_uptrend_threshold_2_marker_for_side(side)
        self.remove_hedge_trigger_markers_for_side(side)
        self.remove_m4_marker_for_side(side)
        self.remove_break_even_line(side)
        self.remove_profit_target_marker_for_side(side)
        self.remove_emergency_exit_line_marker(side)

        # 6. DCA 상태 삭제 (다음 실행 시 복구 알림 방지)
        config_key = f"dca_state_{side}"
        deleted_keys = []
        if config_key in self.config_data:
            del self.config_data[config_key]
            deleted_keys.append(config_key)
        # 레거시 dca_state 키도 삭제 (long side인 경우)
        if side == 'long' and "dca_state" in self.config_data:
            del self.config_data["dca_state"]
            deleted_keys.append("dca_state")
        if deleted_keys:
            config_manager.save_config_data(self.config_data)
            print(f"[{side.upper()}] DCA 상태 삭제 완료: {deleted_keys}")

        QMessageBox.information(self, "Clear All", f"{side.upper()} 계정 정리가 완료되었습니다.")
        print(f"[{side.upper()}] Clear All 완료")

    def handle_account_update_for_side(self, side, data):
        """
        계정 업데이트 핸들러 (side별)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            data: WebSocket에서 받은 계정 업데이트 데이터
        """
        try:
            # 잔액 업데이트
            balances = data.get('a', {}).get('B', [])
            for b in balances:
                asset = b.get('a')
                balance = b.get('wb')  # Wallet Balance
                if asset and balance is not None:
                    self.live_balances_by_side[side][asset] = balance

            # UI 업데이트 (잔액) - 통합 패널에서는 LONG:/SHORT: 접두사 추가
            if side in self.balance_labels and self.balance_labels[side]:
                market_type = self.current_market_types.get(side, 'fapi')
                asset_to_display = 'USDT' if market_type != 'dapi' else 'BTC'

                if asset_to_display in self.live_balances_by_side[side]:
                    balance_value = self.live_balances_by_side[side][asset_to_display]
                    bal_precision = 8 if market_type == 'dapi' else 4
                    self.balance_labels[side].setText(f"{side.upper()}: {float(balance_value):.{bal_precision}f} {asset_to_display}")

            # 확정 PNL 업데이트
            self.update_realized_pnl_display(side)

            # 포지션 업데이트
            positions = data.get('a', {}).get('P', [])
            for pos in positions:
                symbol = pos.get('s')
                position_side = pos.get('ps')
                amount_str = pos.get('pa', '0')
                entry_price_str = pos.get('ep', '0')
                mark_price_str = pos.get('mp', '0')  # Mark Price 추가
                liq_price_str = pos.get('lp', '0')   # Liq Price 추가

                try:
                    amount = float(amount_str)
                    entry_price = float(entry_price_str)
                    mark_price = float(mark_price_str)
                    liq_price = float(liq_price_str)
                except (ValueError, TypeError):
                    continue

                # PNL 직접 계산 (Bybit WebSocket의 unrealisedPnl이 0으로 오는 경우가 많음)
                # LONG: (mark_price - entry_price) * amount
                # SHORT: (entry_price - mark_price) * abs(amount)
                if entry_price > 0 and mark_price > 0:
                    if position_side == 'LONG':
                        unrealized_pnl = (mark_price - entry_price) * amount
                    else:  # SHORT
                        unrealized_pnl = (entry_price - mark_price) * abs(amount)
                else:
                    unrealized_pnl = 0.0

                # 현재 심볼과 일치하는 경우만 테이블 업데이트
                current_symbol = self.current_symbols.get(side, "")
                if symbol == current_symbol:
                    pos_key = f"{symbol}_{position_side}"

                    # 포지션이 청산되었으면 (amount == 0)
                    if amount == 0:
                        # 딕셔너리에서 제거
                        if pos_key in self.live_position_data_by_side[side]:
                            old_entry_price = self.live_position_data_by_side[side][pos_key].get('entry_price', 0)
                            del self.live_position_data_by_side[side][pos_key]

                            # 차트에서 라인 제거 (panel_side별 독립 추적)
                            if old_entry_price > 0:
                                self.remove_position_line_from_chart(old_entry_price, position_side, panel_side=side)
                    else:
                        # 기존 데이터에서 pnl_item, roi_item 참조 보존 (티커 업데이트용)
                        existing_data = self.live_position_data_by_side[side].get(pos_key, {})
                        pnl_item = existing_data.get('pnl_item')
                        roi_item = existing_data.get('roi_item')

                        # 포지션 데이터 저장/업데이트
                        self.live_position_data_by_side[side][pos_key] = {
                            'symbol': symbol,
                            'side': position_side,
                            'amount': amount,
                            'entry_price': entry_price,
                            'mark_price': mark_price,
                            'liq_price': liq_price,
                            'unrealized_pnl': unrealized_pnl,
                            'pnl_item': pnl_item,  # 기존 참조 보존
                            'roi_item': roi_item   # 기존 참조 보존
                        }

                        # 차트 라인 업데이트 (panel_side별 독립 추적)
                        # 진입가 변경 시 기존 라인 제거 후 새 라인 그리기
                        old_entry = existing_data.get('entry_price', 0)
                        if old_entry > 0 and old_entry != entry_price:
                            self.remove_position_line_from_chart(old_entry, position_side, panel_side=side)

                        if entry_price > 0:
                            self.draw_position_line_on_chart(entry_price, position_side, panel_side=side)

                    # 테이블 업데이트
                    self.update_position_table_for_side(side)

                # Insight 탭 포지션 업데이트
                worker = self.auto_trade_workers.get(side)
                if worker and worker.is_running and worker.symbol == symbol and abs(amount) > 0:
                    # Main Position
                    if worker.side_mode == position_side:
                        if self.initial_main_entry_price_by_side[side] is None:
                            self.initial_main_entry_price_by_side[side] = entry_price
                        initial_price = self.initial_main_entry_price_by_side[side] or entry_price
                        self.update_insight_main_position(side, initial_price, abs(amount), entry_price, unrealized_pnl)
                    # Hedge Position
                    else:
                        hedge_side = "SHORT" if worker.side_mode == "LONG" else "LONG"
                        if position_side == hedge_side:
                            if self.initial_hedge_entry_price_by_side[side] is None:
                                self.initial_hedge_entry_price_by_side[side] = entry_price
                            initial_price = self.initial_hedge_entry_price_by_side[side] or entry_price
                            self.update_insight_hedge_position(side, initial_price, abs(amount), entry_price, unrealized_pnl)

            # Break Even 라인 업데이트 (포지션 변경 시마다)
            self.draw_break_even_line(side)

            # Worker에 포지션 업데이트 전달 (process_tick 트리거)
            # Worker가 실행 중이고 현재 심볼의 포지션이 있으면 전달
            worker = self.auto_trade_workers.get(side)
            if worker and worker.is_running:
                current_symbol = self.current_symbols.get(side, "")
                if current_symbol:
                    # Worker에 전달할 포지션 데이터 준비
                    worker_position_data = self.live_position_data_by_side[side].copy()

                    # Worker의 process_tick에 전달
                    # 현재가 조회 우선순위:
                    # 1) current_prices_by_side (ticker WebSocket에서 실시간 업데이트)
                    # 2) WebSocket 포지션 데이터의 markPrice
                    # 3) trade_price_labels (UI에 표시된 가격)
                    # 4) worker.current_price (마지막 수단)
                    current_price = 0

                    # 1. current_prices_by_side에서 가져오기 (가장 최신 ticker 데이터)
                    if hasattr(self, 'current_prices_by_side') and side in self.current_prices_by_side:
                        current_price = self.current_prices_by_side.get(side, 0)

                    # 2. WebSocket 원본 데이터에서 markPrice 가져오기
                    if current_price == 0:
                        for pos in positions:
                            if pos.get('s') == current_symbol:
                                mark_price_str = pos.get('mp', '0')  # Binance 형식 markPrice
                                try:
                                    current_price = float(mark_price_str)
                                    if current_price > 0:
                                        break
                                except:
                                    pass

                    # 3. trade_price_labels에서 가져오기 (ticker WebSocket에서 업데이트됨)
                    if current_price == 0:
                        if hasattr(self, 'trade_price_labels') and side in self.trade_price_labels:
                            price_label = self.trade_price_labels[side]
                            if price_label:
                                price_text = price_label.text()
                                try:
                                    current_price = float(price_text.replace(',', ''))
                                except:
                                    pass

                    # 4. worker의 current_price 사용
                    if current_price == 0 and hasattr(worker, 'current_price'):
                        current_price = worker.current_price or 0

                    ticker_data = {'s': current_symbol, 'c': str(current_price)}

                    # 캐시된 캔들 데이터 사용
                    cache_key = f'_cached_candle_data_{side}'
                    candle_data = getattr(self, cache_key, None)

                    # process_tick 호출
                    worker.process_tick(ticker_data, worker_position_data, candle_data)

        except Exception as e:
            print(f"[{side.upper()}] Account update error: {e}")

    def update_position_table_for_side(self, side):
        """
        포지션 테이블 업데이트 (side별)

        Args:
            side: 'long' 또는 'short'
        """
        table = self.position_tables.get(side)
        if not table:
            return

        table.setRowCount(0)

        # live_position_data_by_side에서 포지션 가져오기
        positions = self.live_position_data_by_side.get(side, {})

        # 현재 가격 가져오기 (ticker WebSocket에서 실시간 업데이트)
        current_price = self.current_prices_by_side.get(side, 0) if hasattr(self, 'current_prices_by_side') else 0

        row = 0
        for pos_key, pos_data in positions.items():
            amount = pos_data.get('amount', 0)
            if amount == 0:
                continue  # 0인 포지션은 표시하지 않음

            symbol = pos_data.get('symbol', '')
            position_side = pos_data.get('side', '')
            entry_price = pos_data.get('entry_price', 0)

            # PNL 계산: 현재 가격이 있으면 실시간 계산, 없으면 저장된 값 사용
            if current_price > 0 and entry_price > 0:
                if position_side == 'LONG':
                    unrealized_pnl = (current_price - entry_price) * amount
                else:  # SHORT
                    unrealized_pnl = (entry_price - current_price) * abs(amount)
            else:
                unrealized_pnl = pos_data.get('unrealized_pnl', 0)

            # ROI 계산 (간단히 처리)
            roi_pct = 0.0
            if entry_price > 0 and amount != 0:
                # unrealized_pnl / (entry_price * abs(amount)) * 100
                position_value = entry_price * abs(amount)
                if position_value > 0:
                    roi_pct = (unrealized_pnl / position_value) * 100

            table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(symbol))
            table.setItem(row, 1, QTableWidgetItem(f"{amount:.4f}"))
            table.setItem(row, 2, QTableWidgetItem(f"{entry_price:.4f}"))

            # Liq. Price
            liq_price = pos_data.get('liq_price', 0)
            liq_item = QTableWidgetItem(f"{liq_price:.4f}" if liq_price > 0 else "-")
            if liq_price > 0:
                liq_item.setForeground(QColor('#ff6666'))
            table.setItem(row, 3, liq_item)

            # PNL과 ROI 아이템 생성 및 참조 저장 (티커 업데이트용)
            pnl_item = QTableWidgetItem(f"{unrealized_pnl:.4f}")
            roi_item = QTableWidgetItem(f"{roi_pct:.2f}%")
            table.setItem(row, 4, pnl_item)
            table.setItem(row, 5, roi_item)

            # PNL/ROI 아이템 참조를 position data에 저장
            pos_data['pnl_item'] = pnl_item
            pos_data['roi_item'] = roi_item
            pos_data['row'] = row

            # Close Position 버튼
            close_btn = QPushButton("Close")
            close_btn.setStyleSheet("background-color: #555555; color: white; font-weight: bold;")
            close_btn.clicked.connect(lambda checked, s=side, sym=symbol, ps=position_side, amt=amount:
                                     self.on_close_position_clicked(s, sym, ps, amt))
            table.setCellWidget(row, 6, close_btn)

            row += 1

    def handle_order_update_for_side(self, side, data):
        """
        주문 업데이트 핸들러 (side별)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            data: WebSocket에서 받은 주문 업데이트 데이터
        """
        try:
            # 자동매매 워커에게 주문 업데이트 전달
            worker = self.auto_trade_workers.get(side)
            if worker and worker.is_running:
                worker.on_order_update(data)

            order_data = data.get('o', {})
            symbol = order_data.get('s')
            order_id = order_data.get('i')
            status = order_data.get('X')
            order_type = order_data.get('o', '')
            side_str = order_data.get('S', '')
            price_str = order_data.get('p', '0')
            amount_str = order_data.get('q', '0')
            filled_str = order_data.get('z', '0')

            print(f"[{side.upper()}] Order update: {symbol} {order_id} {status}")

            # 주문이 체결되거나 취소되면 회색으로 표시 후 잠시 뒤 제거
            if status in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']:
                # 차트에서 주문 라인을 회색으로 변경 (체결 표시)
                self.gray_out_order_line_on_chart(order_id)
                # 500ms 후 차트 라인 제거
                QTimer.singleShot(500, lambda oid=order_id: self.remove_order_line_from_chart(oid))

                # 체결된 주문은 회색으로 표시 (잠시 후 제거)
                if order_id in self.live_orders_by_side.get(side, {}):
                    self.live_orders_by_side[side][order_id]['status'] = status
                    self.live_orders_by_side[side][order_id]['is_completed'] = True
                    # 테이블 즉시 업데이트 (회색으로 표시)
                    self.update_order_table_for_side(side)
                    # 500ms 후 주문 제거
                    QTimer.singleShot(500, lambda s=side, oid=order_id: self.remove_completed_order(s, oid))
                    return  # 아래 테이블 업데이트 스킵
            else:
                # 주문 추가/업데이트 (NEW, PARTIALLY_FILLED 등)
                try:
                    price = float(price_str)
                    amount = float(amount_str)
                    filled = float(filled_str)
                except (ValueError, TypeError):
                    price = 0.0
                    amount = 0.0
                    filled = 0.0

                # 현재 심볼과 일치하는 경우만 처리
                current_symbol = self.current_symbols.get(side, "")
                if symbol == current_symbol:
                    self.live_orders_by_side[side][order_id] = {
                        'symbol': symbol,
                        'order_id': order_id,
                        'type': order_type,
                        'side': side_str,
                        'price': price,
                        'amount': amount,
                        'filled': filled,
                        'status': status
                    }

                    # 차트에 주문 라인 그리기 (양쪽 패널 모두, LIMIT 주문만)
                    if order_type == 'LIMIT' and price > 0:
                        self.draw_order_line_on_chart(price, side_str, order_id, panel_side=side)

            # 테이블 업데이트
            self.update_order_table_for_side(side)

        except Exception as e:
            print(f"[{side.upper()}] Order update error: {e}")

    def update_order_table_for_side(self, side):
        """
        주문 테이블 업데이트 (side별)

        Args:
            side: 'long' 또는 'short'
        """
        table = self.order_tables.get(side)
        if not table:
            return

        table.setRowCount(0)

        # live_orders_by_side에서 주문 가져오기
        orders = self.live_orders_by_side.get(side, {})

        row = 0
        for order_id, order_data in orders.items():
            symbol = order_data.get('symbol', '')
            order_type = order_data.get('type', '')
            order_side = order_data.get('side', '')
            price = order_data.get('price', 0)
            amount = order_data.get('amount', 0)
            filled = order_data.get('filled', 0)

            table.insertRow(row)
            
            # 체결/취소된 주문인지 확인
            is_completed = order_data.get('is_completed', False)
            status = order_data.get('status', '')
            
            # 테이블 아이템 생성
            items = [
                QTableWidgetItem(symbol),
                QTableWidgetItem(order_type),
                QTableWidgetItem(order_side),
                QTableWidgetItem(f"{price:.4f}"),
                QTableWidgetItem(f"{amount:.4f}"),
                QTableWidgetItem(f"{filled:.4f}")
            ]
            
            # 체결/취소된 주문은 회색 배경 적용
            if is_completed:
                gray_color = QColor(128, 128, 128, 100)  # 반투명 회색
                for item in items:
                    item.setBackground(gray_color)
                    item.setForeground(QColor(180, 180, 180))  # 회색 텍스트
            
            for col, item in enumerate(items):
                table.setItem(row, col, item)

            # Cancel 버튼 (체결된 주문은 비활성화)
            cancel_btn = QPushButton("Cancel")
            if is_completed:
                cancel_btn.setStyleSheet("background-color: #555555; color: #888888; font-weight: bold;")
                cancel_btn.setEnabled(False)
            else:
                cancel_btn.setStyleSheet("background-color: #555555; color: white; font-weight: bold;")
                cancel_btn.clicked.connect(lambda checked, s=side, sym=symbol, oid=order_id:
                                          self.on_cancel_order_clicked(s, sym, oid))
            table.setCellWidget(row, 6, cancel_btn)

            row += 1

    def remove_completed_order(self, side, order_id):
        """체결/취소된 주문을 테이블에서 제거"""
        if order_id in self.live_orders_by_side.get(side, {}):
            del self.live_orders_by_side[side][order_id]
            self.update_order_table_for_side(side)
            print(f"[{side.upper()}] 완료된 주문 제거: {order_id}")

    def on_close_position_clicked(self, side, symbol, position_side, amount):
        """
        포지션 Close 버튼 클릭 핸들러 (side별)

        Args:
            side: 'long' 또는 'short'
            symbol: 심볼
            position_side: 포지션 방향 ('LONG' or 'SHORT')
            amount: 현재 포지션 수량
        """
        print(f"[{side.upper()}] Close position clicked: {symbol}_{position_side}, amount={amount}")

        # 확인 메시지
        reply = QMessageBox.question(
            self,
            "Close Position",
            f"Close {position_side} position for {symbol}?\nAmount: {amount}",
            QMessageBox.Yes | QMessageBox.No
        )

        print(f"[{side.upper()}] User reply: {'Yes' if reply == QMessageBox.Yes else 'No'}")

        if reply == QMessageBox.Yes:
            api_module = self.api_modules.get(side)
            if not api_module or not api_module.is_api_key_active():
                print(f"[{side.upper()}] API not connected")
                return

            # 포지션을 청산하려면 반대 방향으로 시장가 주문 (reduceOnly=True)
            close_side = "SELL" if position_side == "LONG" else "BUY"
            qty = abs(amount)

            print(f"[{side.upper()}] Closing position: {close_side} {qty} {symbol}")

            # Bybit 시장가 주문 (place_market_order 사용)
            result = api_module.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=qty,
                reduce_only=True,
                position_side=position_side
            )

            if result and result.get('orderId'):
                print(f"[{side.upper()}] Position close order placed: {result.get('orderId')}")
            else:
                error_msg = result.get('msg', 'Unknown error') if result else 'No response'
                print(f"[{side.upper()}] Failed to close position: {error_msg}")

    def on_cancel_order_clicked(self, side, symbol, order_id):
        """
        주문 Cancel 버튼 클릭 핸들러 (side별)

        Args:
            side: 'long' 또는 'short'
            symbol: 심볼
            order_id: 주문 ID
        """
        # 확인 메시지
        reply = QMessageBox.question(
            self,
            "Cancel Order",
            f"Cancel order {order_id}?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            api_module = self.api_modules.get(side)
            if not api_module or not api_module.is_api_key_active():
                print(f"[{side.upper()}] API not connected")
                return

            category = self.current_market_types.get(side, 'linear')
            if category in ['fapi', 'linear']:
                category = 'linear'
            elif category in ['dapi', 'inverse']:
                category = 'inverse'

            print(f"[{side.upper()}] Canceling order: {order_id}")

            # Bybit 주문 취소 (symbol, order_id 순서로 전달)
            result = api_module.cancel_order(symbol, order_id)

            if result:
                print(f"[{side.upper()}] Order canceled: {order_id}")
            else:
                print(f"[{side.upper()}] Failed to cancel order: {order_id}")

    def handle_ticker_update_for_side(self, side, ticker_list):
        """
        티커 업데이트 핸들러 (side별)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            ticker_list: 티커 데이터 리스트 (WebSocket에서 전달)
        """
        # ticker_list에서 첫 번째 항목 추출
        if not ticker_list:
            return

        ticker_data = ticker_list[0]

        # Bybit 형식: {'topic': 'tickers.BTCUSDT', 'data': {'symbol': 'BTCUSDT', 'lastPrice': '67036.5', ...}}
        # Binance 형식: {'s': 'BTCUSDT', 'c': '67036.5', ...}
        symbol = ticker_data.get('data', {}).get('symbol') or ticker_data.get('s', '')
        price_str = ticker_data.get('data', {}).get('lastPrice') or ticker_data.get('c', '0')

        try:
            price = float(price_str)
        except (ValueError, TypeError):
            return

        # 현재 패널의 심볼과 일치하는 경우만 업데이트
        current_symbol = self.current_symbols.get(side, "BTCUSDT")
        if symbol != current_symbol:
            return

        # 현재가 캐시에 저장 (account update에서 사용)
        self.current_prices_by_side[side] = price

        # Insight 탭 profit target 상태 재갱신 (Rate Limiting: 1초 간격)
        import time as time_module
        current_time = time_module.time()
        last_key = f'_last_insight_profit_update_{side}'
        if current_time - getattr(self, last_key, 0) >= 1.0:
            worker = self.auto_trade_workers.get(side)
            if worker and worker.is_running and getattr(worker, 'profit_target_price', None):
                self.update_insight_profit_target(side, worker.profit_target_price, worker.current_step)
            setattr(self, last_key, current_time)

        if side in self.trade_price_labels and self.trade_price_labels[side]:
            # side별 precision 사용 (기본값: 2)
            precision = self.price_precisions.get(side, 2)
            self.trade_price_labels[side].setText(f"{price:.{precision}f}")

        # Worker에 process_tick 전달 (헷지 트리거 모니터링 등)
        worker = self.auto_trade_workers.get(side)
        if worker and worker.is_running:
            import time as time_module
            current_time = time_module.time()

            # 캔들 데이터 추출 Rate Limiting (side별 1초에 1번만)
            candle_data = None
            last_extract_key = f'_last_candle_extract_time_{side}'
            cache_key = f'_cached_candle_data_{side}'
            should_extract_candle = current_time - getattr(self, last_extract_key, 0) >= 1.0

            if should_extract_candle:
                if self.candlestick_item and hasattr(self.candlestick_item, 'data'):
                    df = self.candlestick_item.data
                    if not df.empty and len(df) >= 2:
                        prev_candle = df.iloc[-2]
                        current_candle = df.iloc[-1]
                        candle_data = {
                            'prev': {
                                'timestamp': prev_candle['time'],
                                'open': prev_candle['open'],
                                'close': prev_candle['close'],
                                'high': prev_candle['high'],
                                'low': prev_candle['low']
                            },
                            'current': {
                                'timestamp': current_candle['time'],
                                'open': current_candle['open'],
                                'close': current_candle['close'],
                                'high': current_candle['high'],
                                'low': current_candle['low']
                            }
                        }
                        setattr(self, cache_key, candle_data)
                        setattr(self, last_extract_key, current_time)
            else:
                candle_data = getattr(self, cache_key, None)

            ticker_data = {'s': current_symbol, 'c': str(price)}
            worker_position_data = self.live_position_data_by_side[side].copy()
            worker.process_tick(ticker_data, worker_position_data, candle_data)

    def handle_kline_update_for_side(self, side, kline_data):
        """
        캔들 업데이트 핸들러 (side별)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            kline_data: WebSocket에서 받은 캔들 데이터
        """
        try:
            symbol = kline_data.get('symbol')

            # 현재 차트에 표시 중인 심볼과 일치하면 차트 업데이트
            if symbol == self.current_symbol:
                self.handle_kline_update(kline_data)

        except Exception as e:
            print(f"[{side.upper()}] Kline update error: {e}")

    def populate_initial_balance_for_side(self, side, balance_info):
        """
        초기 잔액 채우기 (side별)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            balance_info: API에서 받은 잔액 정보 리스트
        """
        self.live_balances_by_side[side].clear()

        if not balance_info:
            print(f"[{side.upper()}] 초기 잔액 정보가 없습니다.")
            return

        # 잔액 정보 저장
        for b in balance_info:
            asset = b.get('asset')
            balance = b.get('balance')  # 초기 로드 시 'balance' 키 사용
            if asset and balance is not None:
                self.live_balances_by_side[side][asset] = balance

        print(f"[{side.upper()}] {len(self.live_balances_by_side[side])}개 자산 잔액 로드 완료.")

        # 시작 잔액 기록 (확정 PNL 계산용)
        market_type = self.current_market_types.get(side, 'fapi')
        if market_type == 'dapi':
            for asset in ['BTC', 'ETH', 'USD']:
                if asset in self.live_balances_by_side[side]:
                    self.start_balances_by_side[side] = float(self.live_balances_by_side[side][asset])
                    break
        else:
            if 'USDT' in self.live_balances_by_side[side]:
                self.start_balances_by_side[side] = float(self.live_balances_by_side[side]['USDT'])
        print(f"[{side.upper()}] 시작 잔액 기록: {self.start_balances_by_side[side]}")

        # 확정 PNL 초기 표시 (시작 시 0.00)
        self.update_realized_pnl_display(side)

        # UI 라벨 업데이트
        if side in self.balance_labels and self.balance_labels[side]:
            market_type = self.current_market_types.get(side, 'fapi')

            # 표시할 자산 결정
            if market_type == 'dapi':
                # COIN-M: BTC, ETH, USD 등
                asset_to_display = None
                for asset in ['BTC', 'ETH', 'USD', 'USDT']:
                    if asset in self.live_balances_by_side[side]:
                        asset_to_display = asset
                        break
            else:
                # USD-M: USDT
                asset_to_display = 'USDT'

            if asset_to_display and asset_to_display in self.live_balances_by_side[side]:
                balance_value = self.live_balances_by_side[side][asset_to_display]
                self.balance_labels[side].setText(f"{side.upper()}: {balance_value} {asset_to_display}")
                print(f"[{side.upper()}] {asset_to_display} 잔액: {balance_value}")
            else:
                # 첫 번째 자산 표시
                if self.live_balances_by_side[side]:
                    first_asset = list(self.live_balances_by_side[side].keys())[0]
                    first_balance = self.live_balances_by_side[side][first_asset]
                    self.balance_labels[side].setText(f"{side.upper()}: {first_balance} {first_asset}")
                else:
                    self.balance_labels[side].setText(f"{side.upper()}: N/A")

    def populate_initial_positions_for_side(self, side, positions):
        """
        초기 포지션 채우기 (side별 필터링)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            positions: API에서 받은 전체 포지션 리스트
        """
        # 해당 side의 테이블 초기화
        position_table = self.position_tables.get(side)
        if not position_table:
            print(f"[{side.upper()}] Position table not found")
            return

        position_table.setRowCount(0)
        self.live_position_data_by_side[side].clear()

        if not positions:
            print(f"[{side.upper()}] 초기 포지션 정보가 없습니다.")
            return

        # 해당 계정의 모든 포지션 표시 (헤지 포지션 포함)
        panel_direction = self.side_modes.get(side, "LONG")
        filtered_positions = []
        for p in positions:
            amount = float(p['positionAmt'])
            if amount == 0:  # 포지션 없음
                continue

            position_side = p.get('positionSide')
            if not position_side or position_side == 'BOTH':
                # Hedge 모드가 아닌 경우: amount의 부호로 판단
                position_side = 'LONG' if amount > 0 else 'SHORT'

            filtered_positions.append(p)

        print(f"[{side.upper()} 패널] 전체 {len(positions)}개 중 {len(filtered_positions)}개 포지션 표시")

        # 자동매매 중이면 메인 포지션을 먼저 표시하도록 정렬
        worker = self.auto_trade_workers.get(side)
        if worker and worker.is_running:
            main_side = worker.side_mode
            filtered_positions_sorted = sorted(filtered_positions, key=lambda p: (
                0 if (p.get('positionSide') == main_side or
                      (not p.get('positionSide') or p.get('positionSide') == 'BOTH') and
                      ((main_side == 'LONG' and float(p['positionAmt']) > 0) or
                       (main_side == 'SHORT' and float(p['positionAmt']) < 0))) else 1
            ))
        else:
            filtered_positions_sorted = filtered_positions

        # 테이블에 표시
        market_type = self.current_market_types.get(side, 'fapi')
        for p in filtered_positions_sorted:
            row_count = position_table.rowCount()
            position_table.insertRow(row_count)

            symbol = p['symbol']
            amount = float(p['positionAmt'])
            entry_price = float(p['entryPrice'])
            api_pnl = float(p['unRealizedProfit'])
            mark_price = float(p.get('markPrice', 0))
            margin = float(p.get('initialMargin', p.get('isolatedWallet', 0)))

            # PNL 계산: API에서 0이면 mark price로 직접 계산
            position_side = p.get('positionSide')
            if not position_side or position_side == 'BOTH':
                position_side = 'LONG' if amount > 0 else 'SHORT'

            if api_pnl == 0 and mark_price > 0 and entry_price > 0:
                # PNL 직접 계산
                if position_side == 'LONG':
                    pnl = (mark_price - entry_price) * amount
                else:  # SHORT
                    pnl = (entry_price - mark_price) * abs(amount)
            else:
                pnl = api_pnl

            # ROI 계산
            position_value = abs(entry_price * amount) if entry_price != 0 else 0
            roi = (pnl / position_value) * 100 if position_value != 0 else 0

            pnl_precision = 8 if market_type == 'dapi' else 4

            unique_key = f"{symbol}_{position_side}"

            pnl_item = QTableWidgetItem(f"{pnl:.{pnl_precision}f}")
            roi_item = QTableWidgetItem(f"{roi:.2f}%")

            position_table.setItem(row_count, 0, QTableWidgetItem(symbol))
            position_table.setItem(row_count, 1, QTableWidgetItem(p['positionAmt']))
            position_table.setItem(row_count, 2, QTableWidgetItem(p['entryPrice']))
            position_table.setItem(row_count, 3, pnl_item)
            position_table.setItem(row_count, 4, roi_item)

            # Close 버튼 추가
            cancel_widget = self.create_centered_cancel_button(
                lambda checked, s=side, sym=symbol, ps=position_side, amt=amount:
                    self.on_close_position_clicked(s, sym, ps, amt)
            )
            position_table.setCellWidget(row_count, 5, cancel_widget)

            # 데이터 저장 (WebSocket 핸들러와 동일한 키 사용)
            self.live_position_data_by_side[side][unique_key] = {
                'row': row_count,
                'symbol': symbol,
                'amount': amount,
                'entry_price': entry_price,  # 키 통일
                'side': position_side,  # 키 통일
                'unrealized_pnl': pnl,  # 키 통일
                'mark_price': mark_price,
                'margin': margin,
                'pnl_item': pnl_item,
                'roi_item': roi_item
            }

    def populate_initial_orders_for_side(self, side, orders):
        """
        초기 주문 채우기 (side별 필터링)

        Args:
            side: 'long' 또는 'short' (패널 구분자)
            orders: API에서 받은 전체 주문 리스트
        """
        # 해당 side의 테이블 초기화
        order_table = self.order_tables.get(side)
        if not order_table:
            print(f"[{side.upper()}] Order table not found")
            return

        order_table.setRowCount(0)

        if not orders:
            print(f"[{side.upper()}] 초기 미체결 주문 정보가 없습니다.")
            return

        # 이 패널의 거래 방향 가져오기
        panel_direction = self.side_modes.get(side, "LONG")
        print(f"[{side.upper()} 패널] 주문 필터링: {panel_direction} 주문만 표시")

        # 주문 필터링: 패널 방향과 일치하는 주문만
        filtered_orders = []
        for o in orders:
            order_side = o.get('side', '').upper()  # 'BUY' 또는 'SELL'
            position_side = o.get('positionSide', '').upper()  # 'LONG' 또는 'SHORT' (Hedge 모드)

            # Hedge 모드인 경우 positionSide 사용
            if position_side and position_side in ['LONG', 'SHORT']:
                if position_side == panel_direction:
                    filtered_orders.append(o)
            # One-way 모드인 경우 side로 판단
            elif order_side:
                # BUY = LONG, SELL = SHORT로 매핑
                inferred_direction = 'LONG' if order_side == 'BUY' else 'SHORT'
                if inferred_direction == panel_direction:
                    filtered_orders.append(o)

        print(f"[{side.upper()} 패널] 전체 {len(orders)}개 중 {len(filtered_orders)}개 주문 표시")

        # 테이블에 표시
        for o in filtered_orders:
            row_count = order_table.rowCount()
            order_table.insertRow(row_count)

            order_table.setItem(row_count, 0, QTableWidgetItem(o['symbol']))
            order_table.setItem(row_count, 1, QTableWidgetItem(o['type']))
            order_table.setItem(row_count, 2, QTableWidgetItem(o['side']))
            order_table.setItem(row_count, 3, QTableWidgetItem(o['price']))
            order_table.setItem(row_count, 4, QTableWidgetItem(o['origQty']))
            order_table.setItem(row_count, 5, QTableWidgetItem(o['executedQty']))

            # Cancel 버튼 추가
            order_id = str(o['orderId'])
            symbol = o['symbol']
            order_category = o.get('orderCategory', 'normal')
            cancel_widget = self.create_centered_cancel_button(
                lambda checked, s=side, sym=symbol, oid=order_id, cat=order_category: self.cancel_single_order_for_side(s, sym, oid, cat)
            )
            order_table.setCellWidget(row_count, 6, cancel_widget)

            order_table.setItem(row_count, 7, QTableWidgetItem(order_id))

            # 차트에 주문 라인 추가 (현재 심볼만)
            current_symbol = self.current_symbols.get(side, self.current_symbol if hasattr(self, 'current_symbol') else '')
            if symbol == current_symbol:
                try:
                    price = float(o['price'])
                    order_side = o['side']
                    self.draw_order_line_on_chart(price, order_side, order_id, panel_side=side)
                except (ValueError, KeyError) as e:
                    print(f"[{side.upper()}] 주문 라인 추가 실패: {e}")

    # === 기존 핸들러 ===

    def on_auto_trade_start_clicked(self):
        """'Start Auto-Trade' 버튼 클릭 시."""
        self._start_auto_trade(check_positions=True)

    def _start_auto_trade_without_position_check(self, side=None):
        """익절 후 재시작 시 포지션 체크 및 경고창 건너뛰고 자동매매 시작"""
        if side:
            self._start_auto_trade_for_side(side, check_positions=False, skip_min_order_warning=True)
        else:
            self._start_auto_trade(check_positions=False, skip_min_order_warning=True)

    def _start_auto_trade(self, check_positions=True, skip_min_order_warning=False):
        """자동매매 시작 (공통 로직)

        Args:
            check_positions: True면 포지션/주문 체크, False면 건너뛰기
            skip_min_order_warning: True면 최소 주문 금액 경고창 건너뛰기 (익절 후 재시작 시)
        """
        # 0. API 연결 확인
        if not self.api_module or not self.api_module.is_api_key_active():
            self.on_auto_trade_log("Status: <b style='color: red;'>Error: API not connected.</b>")
            return

        # 1. Bybit/Binance 여부 확인 (Bybit만 지원)
        if self.connect_thread.exchange != "Bybit":
            self.on_auto_trade_log("Status: <b style='color: red;'>Error: Auto-Trade (Hedge Mode) only supports Bybit for now.</b>")
            return

        # 2. 현재 잔고 확인
        # (update_balance_display에서 asset_to_display 로직과 동일하게)
        category = self.auto_trade_market_mode # 'linear' or 'inverse'

        if category == 'linear':
            balance_asset = "USDT"
        else: # inverse
            balance_asset = "BTC"

        balance_total_str = self.live_balances.get(balance_asset, "0.0")
        balance_total = float(balance_total_str)

        if balance_total <= 0.0:
            self.on_auto_trade_log(f"Status: <b style='color: red;'>Error: No {balance_asset} balance.</b>")
            return

        # 3. 포지션 및 미체결 주문 확인 (익절 후 재시작 시 건너뛰기)
        if check_positions:
            if len(self.live_position_data) > 0:
                QMessageBox.warning(
                    self,
                    "경고: 포지션 감지됨",
                    "포지션이 감지되었습니다. 포지션과 미체결 주문을 정리한 후 재시도 하세요.",
                    QMessageBox.Ok
                )
                self.on_auto_trade_log("Status: <b style='color: orange;'>Error: Existing positions detected.</b>")
                return

            try:
                open_orders = self.api_module.get_initial_open_orders()
                if open_orders and len(open_orders) > 0:
                    QMessageBox.warning(
                        self,
                        "경고: 미체결 주문 감지됨",
                        "미체결 주문이 감지되었습니다. 포지션과 미체결 주문을 정리한 후 다시 시도하세요.",
                        QMessageBox.Ok
                    )
                    self.on_auto_trade_log("Status: <b style='color: orange;'>Error: Open orders detected.</b>")
                    return
            except Exception as e:
                print(f"[Auto-Trade Start] 미체결 주문 확인 오류: {e}")
                # 미체결 주문 확인 실패 시에도 포지션이 없으면 진행
        else:
            print("[Auto-Trade Start] 익절 후 재시작 - 포지션/주문 체크 건너뛰기")

        # 4. 설정 스레드 실행
        self._set_side_button_running()  # 버튼을 Stop 상태로 (설정 중)
        self.on_auto_trade_log("Status: <b style='color: yellow;'>Starting setup...</b>")

        # 최소 주문 금액 경고창 건너뛰기 플래그 저장 (on_setup_finished에서 참조)
        self._skip_min_order_warning = skip_min_order_warning

        self.setup_thread = SetupAutoTradeThread(
            api_module = self.api_module,
            category = category,
            symbol = self.current_symbol, # Chart 탭에서 선택한 심볼 사용
            balance_asset = balance_asset,
            balance_total = balance_total,
            strategy_settings = self.strategy_settings
        )
        self.setup_thread.setup_finished.connect(self.on_setup_finished)
        self.setup_thread.log_message.connect(self.on_auto_trade_log)
        self.setup_thread.start()

    @pyqtSlot(bool, str, dict)
    def on_setup_finished(self, success, error_message, params):
        """설정 스레드 완료 시."""
        if success:
            # 사용자 확인이 필요한 경우 (최소 주문 금액 이하인 헷지 주문이 있음)
            # 단, 익절 후 재시작 시에는 경고창 건너뛰기
            skip_warning = getattr(self, '_skip_min_order_warning', False)
            if params.get('needs_user_confirmation', False) and not skip_warning:
                warning_message = params.get('warning_message', '')
                reply = QMessageBox.warning(
                    self,
                    "경고: 최소 주문 금액 미달",
                    warning_message,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )

                if reply == QMessageBox.No:
                    # 사용자가 "아니오"를 선택 -> 자동매매 시작 취소
                    print("[Auto-Trade] 사용자가 최소 주문 금액 경고로 인해 자동매매를 취소했습니다.")
                    self.on_auto_trade_log("Status: <b style='color: orange;'>Canceled by User (Min Order Value Warning)</b>")
                    self._set_side_button_stopped()
                    return

                # 사용자가 "예"를 선택 -> 계속 진행
                print("[Auto-Trade] 사용자가 최소 주문 금액 경고에도 불구하고 진행을 선택했습니다.")
            elif skip_warning and params.get('needs_user_confirmation', False):
                print("[Auto-Trade] 익절 후 재시작 - 최소 주문 금액 경고창 건너뛰기")

            # 플래그 초기화 (다음 수동 시작 시에는 경고창 표시)
            self._skip_min_order_warning = False

            self.on_auto_trade_log("Status: <b style='color: green;'>Setup Complete. Starting logic...</b>")

            # Y축 precision을 symbol의 tickSize 기반으로 설정
            symbol_info = params.get('symbol_info', {})
            if symbol_info:
                tick_size = float(symbol_info.get('priceFilter', {}).get('tickSize', '0.01'))
                import v7_dual_trading_utils as trading_utils
                price_precision = trading_utils.count_decimal_places(tick_size)
                self.y_axis.setPrecision(price_precision)
                self.detected_precision = price_precision
                print(f"[차트] Y축 precision을 tickSize({tick_size})에 맞춰 {price_precision}자리로 설정")

            # "Start" 버튼을 "Stop" 버튼으로 변경
            self._set_side_button_running()

            # 시작 잔액 저장 (프로그램 최초 시작 시에만)
            # 익절 후 재시작 시에는 시작 잔액을 유지하여 누적 손익 계산
            if self.cycle_start_balance == 0.0:
                category = params.get('category', 'linear')
                if category == 'linear':
                    self.cycle_start_balance = float(self.live_balances.get("USDT", "0.0"))
                else:  # inverse
                    if "BTC" in self.current_symbol:
                        self.cycle_start_balance = float(self.live_balances.get("BTC", "0.0"))
                    elif "ETH" in self.current_symbol:
                        self.cycle_start_balance = float(self.live_balances.get("ETH", "0.0"))
                print(f"[프로그램 시작] 초기 잔액: {self.cycle_start_balance}")
            else:
                print(f"[사이클 재시작] 시작 잔액 유지: {self.cycle_start_balance}")

            # '두뇌' 워커에게 계산된 파라미터를 전달하고 시작
            self.auto_trade_worker.start_trading(
                params['symbol'],
                params['entry_quantity'],
                self.auto_trade_side_mode,
                self.strategy_settings,  # 전략 설정 전달
                0,  # 현재 스텝 (Step 0부터 시작)
                self.strategy_settings.get("STEPS", 10),  # 전체 스텝 수
                params.get('entry_qty_list', []),  # DCA 진입 수량 목록
                params.get('hedge_qty_list', []),  # DCA 헷지 수량 목록
                self.api_module,  # API 모듈 (청산가 조회용)
                params.get('symbol_info', {}),  # 심볼 정보 (tickSize, qtyStep 등)
                params.get('category', 'linear'),  # 카테고리 (linear/inverse)
                self.insight_data_by_side.get('long', {}).get('current_price', 0)  # 현재 가격
            )
        else:
            self.on_auto_trade_log(f"Status: <b style='color: red;'>Setup Failed: {error_message}</b>")
            self._set_side_button_stopped()
            
    def on_auto_trade_stop_clicked(self):
        """'Stop Auto-Trade' 버튼 클릭 시."""
        # 포지션이 있으면 총 PNL 확인 후 종료 여부 묻기
        if len(self.live_position_data) > 0:
            total_pnl = self._calculate_total_pnl()

            # PNL에 따라 메시지 구성
            if total_pnl > 0:
                status_text = "수익중"
                icon = QMessageBox.Information
                title = "수익 중 확인"
            elif total_pnl < 0:
                status_text = "손실중"
                icon = QMessageBox.Warning
                title = "손실 중 확인"
            else:
                status_text = "손익 없음"
                icon = QMessageBox.Question
                title = "종료 확인"

            # 확인 메시지 박스
            msg_box = QMessageBox(icon, title,
                f"현재 {status_text}상황입니다 (총 PNL: {total_pnl:.4f} USDT).\n\n자동매매를 종료하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No, self)
            msg_box.setDefaultButton(QMessageBox.No)

            if msg_box.exec_() == QMessageBox.No:
                print(f"[Stop Auto-Trade] 사용자가 자동매매 중지를 취소했습니다. (PNL: {total_pnl:.2f})")
                return

        self.auto_trade_worker.stop_trading()

        # DCA 상태 삭제 (stop 시 저장된 상태 제거)
        dca_keys_to_delete = [k for k in ["dca_state", "dca_state_long", "dca_state_short"] if k in self.config_data]
        if dca_keys_to_delete:
            for k in dca_keys_to_delete:
                del self.config_data[k]
            config_manager.save_config_data(self.config_data)
            print(f"[Stop Auto-Trade] 저장된 DCA 상태 삭제 완료: {dca_keys_to_delete}")

        # 헷지 트리거 마커 제거
        self.remove_all_hedge_trigger_markers()

        # 익절 트리거 마커 제거
        self.remove_profit_target_marker()

        # 역방향진입 임계값 마커 제거
        self.remove_uptrend_threshold_marker()
        self.remove_uptrend_threshold_2_marker()

        # 안전망 마커 제거
        self.remove_emergency_exit_line_marker()

        # Insight 탭 초기화
        self.reset_insight_tab()

        # 최초 진입 가격 초기화
        for s in ['long', 'short']:
            self.initial_main_entry_price_by_side[s] = None
            self.initial_hedge_entry_price_by_side[s] = None
        print("[Stop Auto-Trade] 최초 진입 가격 초기화 완료")

        # "Stop" 버튼을 "Start" 버튼으로 변경
        self._set_side_button_stopped()

    def on_auto_trade_schedule_stop_clicked(self):
        """'예약 종료' 버튼 클릭 시 - 사이클 종료 후 자동매매 중지 예약"""
        if not hasattr(self, 'auto_trade_worker') or not self.auto_trade_worker.is_running:
            return

        # 이미 예약된 경우 취소
        if self.auto_trade_worker.scheduled_stop:
            self.auto_trade_worker.scheduled_stop = False
            self.auto_trade_schedule_stop_button.setText("⏱️ Schedule Stop")
            self.auto_trade_schedule_stop_button.setStyleSheet("font-size: 11pt; background-color: #444444; color: #FFD700;")
            print("[예약 종료] 예약 취소됨")
            self.on_auto_trade_log("Status: <b style='color: yellow;'>예약 종료 취소됨</b>|||")
            return

        # 예약 확인
        reply = QMessageBox.question(
            self,
            "예약 종료 확인",
            "현재 DCA 사이클이 완료되고 모든 포지션이 청산된 후\n자동매매를 종료하시겠습니까?\n\n"
            "- 익절 목표 도달 시 청산 후 종료\n"
            "- 최종 단계 도달 시 청산 후 종료\n"
            "- 수동 청산 시 종료\n\n"
            "종료 예약을 취소하려면 버튼을 다시 클릭하세요.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.auto_trade_worker.scheduled_stop = True
            self.auto_trade_schedule_stop_button.setText("⏱️ Cancel Schedule")
            self.auto_trade_schedule_stop_button.setStyleSheet("font-size: 11pt; background-color: #ff6600; color: white;")
            print("[예약 종료] 사이클 완료 후 자동매매 종료 예약됨")
            self.on_auto_trade_log("Status: <b style='color: orange;'>사이클 완료 후 종료 예약됨</b>|||")

    @pyqtSlot(str)
    def on_auto_trade_log_for_side(self, side, message):
        """자동매매 워커가 보내는 로그를 GUI에 표시 (side별)"""
        # "|||" 구분자로 Status와 Step 분리
        if "|||" in message:
            parts = message.split("|||")
            if len(parts) >= 1 and side in self.auto_trade_status_labels:
                self.auto_trade_status_labels[side].setText(parts[0])
            if len(parts) >= 2 and side in self.auto_trade_step_labels:
                step_text = parts[1]
                self.auto_trade_step_labels[side].setText(step_text)

                # Insight 탭의 Step 박스도 업데이트 (나중에 side별로 구현 가능)
                # "Step: <b>1/10</b>" 형식에서 "1/10" 추출
                import re
                step_match = re.search(r'(\d+/\d+|-)', step_text)
                if step_match:
                    step_value = step_match.group(1)
                    if side in self.insight_widgets:
                        self.insight_widgets[side]['current_step'].setText(step_value)
        else:
            # 구분자가 없으면 기존 방식 (Status만)
            if side in self.auto_trade_status_labels:
                self.auto_trade_status_labels[side].setText(message)

    def on_auto_trade_log(self, message):
        """하위 호환성: LONG worker의 로그를 처리"""
        self.on_auto_trade_log_for_side('long', message)
    
    @pyqtSlot()
    def on_auto_trade_market_toggle(self):
        """자동매매 마켓 모드 (COIN-M / USDT-M) 토글"""
        if self.auto_trade_market_mode == "linear":
            self.auto_trade_market_mode = "inverse"
        else:
            self.auto_trade_market_mode = "linear"

        market_display = "USDT" if self.auto_trade_market_mode == "linear" else "COIN"
        self.auto_trade_market_toggle.setText(f"Market: {market_display}")
        print(f"Auto-Trade market mode set to: {self.auto_trade_market_mode}")

    @pyqtSlot()
    def on_auto_trade_side_toggle(self):
        """자동매매 전략 방향 (LONG / SHORT) 토글"""
        if self.auto_trade_side_mode == "LONG":
            self.auto_trade_side_mode = "SHORT"
        else:
            self.auto_trade_side_mode = "LONG"
        
        self.auto_trade_side_toggle.setText(f"Side: {self.auto_trade_side_mode.upper()}")
        print(f"Auto-Trade side set to: {self.auto_trade_side_mode}")
    
    @pyqtSlot(str, str, str, bool)
    def on_auto_trade_execute(self, symbol, side, quantity, is_hedge=False):
        """자동매매 워커(두뇌)로부터 받은 거래 신호를 실행합니다."""

        trade_type = "HEDGE" if is_hedge else "MAIN"
        print(f"AutoTraderGUI: 자동매매 신호 수신 -> [{trade_type}] {side} {quantity} {symbol}")

        if not self.api_module or not self.api_module.is_api_key_active():
            print("AutoTraderGUI: API가 연결되지 않아 자동매매 주문을 실행할 수 없습니다.")
            self.auto_trade_worker.log_message.emit("Status: <b style='color: red;'>Order FAILED (API not connected)</b>")
            return

        # 'reduce_only'와 'position_side' 결정 (v7_auto_trader.py의 전략 기준)
        reduce_only = False
        position_side = "BOTH"

        if is_hedge:
            # 헷지 포지션: 주거래의 반대 방향으로 새로운 포지션 진입
            if self.auto_trade_side_mode == "LONG":
                # 주거래가 LONG이면, 헷지는 SHORT 포지션 OPEN
                position_side = "SHORT"
                reduce_only = False
            elif self.auto_trade_side_mode == "SHORT":
                # 주거래가 SHORT이면, 헷지는 LONG 포지션 OPEN
                position_side = "LONG"
                reduce_only = False
        else:
            # 주거래 포지션 로직 (기존 코드)
            if self.auto_trade_side_mode == "LONG":
                if side.upper() == "BUY": # 롱 진입
                    position_side = "LONG"
                    reduce_only = False
                elif side.upper() == "SELL": # 롱 청산
                    position_side = "LONG"
                    reduce_only = True

            elif self.auto_trade_side_mode == "SHORT":
                if side.upper() == "SELL": # 숏 진입
                    position_side = "SHORT"
                    reduce_only = False
                elif side.upper() == "BUY": # 숏 청산
                    position_side = "SHORT"
                    reduce_only = True
        
        try:
            # [중요] 자동매매는 확인창(QMessageBox) 없이 바로 주문 실행
            print(f"Placing order: {side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")
            
            result = self.api_module.place_market_order(symbol, side, quantity, reduce_only, position_side)
            
            # Bybit와 Binance 응답 모두 orderId 포함 여부로 성공 판단
            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"자동매매 주문 ID {order_id}가 접수되었습니다.")
                self.auto_trade_worker.log_message.emit("Status: <b style='color: blue;'>Order Placed!</b>")

                # 주문 ID를 워커에게 전달
                if is_hedge:
                    # 헷지 주문인 경우, 슬리피지 추적을 위해 주문 ID와 트리거 정보를 워커로 전달
                    if hasattr(self.auto_trade_worker, 'last_hedge_trigger_info') and self.auto_trade_worker.last_hedge_trigger_info:
                        trigger_price, qty = self.auto_trade_worker.last_hedge_trigger_info
                        # 시그널 대신 직접 호출 (스레드 간 전달 확실성 보장)
                        self.auto_trade_worker.on_hedge_order_id_received(order_id, trigger_price, qty)
                        print(f"[슬리피지 추적] 헷지 주문 ID {order_id} 워커로 전달 (트리거가: ${trigger_price})")
                    # Step 0 초기 진입의 헷지는 트리거가 아니므로 추적 안 함 (정상)
                else:
                    # 메인 주문: 워커에게 order_id 전달 (체결 추적 및 다음 단계 진행용)
                    self.auto_trade_worker.order_id_received.emit(order_id)
                    print(f"[메인 주문] 주문 ID {order_id} 워커로 전달")
            
            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"AutoTraderGUI: 자동매매 주문이 API에서 거부됨: {msg}")
                self.auto_trade_worker.log_message.emit(f"Status: <b style='color: red;'>Order REJECTED: {msg}</b>")
            else:
                print(f"AutoTraderGUI: 자동매매 주문 API 요청 실패. {result}")
                self.auto_trade_worker.log_message.emit("Status: <b style='color: red;'>Order FAILED (API request)</b>")
                
        except Exception as e:
            print(f"AutoTraderGUI: 자동매매 주문 중 Python 오류: {e}")
            self.auto_trade_worker.log_message.emit(f"Status: <b style='color: red;'>Order FAILED (Python error)</b>")

    def on_auto_trade_execute_for_side(self, side, symbol, order_side, quantity, is_hedge=False):
        """Side별 자동매매 워커로부터 받은 거래 신호를 해당 계정으로 실행합니다.

        Args:
            side: 'long' 또는 'short' (어느 패널/계정에서 온 신호인지)
            symbol: 거래 심볼
            order_side: 'BUY' 또는 'SELL'
            quantity: 주문 수량
            is_hedge: 헷지 주문 여부
        """
        trade_type = "HEDGE" if is_hedge else "MAIN"
        print(f"AutoTraderGUI [{side.upper()}]: 자동매매 신호 수신 -> [{trade_type}] {order_side} {quantity} {symbol}")

        # side별 API 모듈과 워커 가져오기
        api_module = self.api_modules.get(side)
        worker = self.auto_trade_workers.get(side)
        side_mode = self.side_modes.get(side, 'LONG' if side == 'long' else 'SHORT')

        if not api_module or not api_module.is_api_key_active():
            print(f"AutoTraderGUI [{side.upper()}]: API가 연결되지 않아 자동매매 주문을 실행할 수 없습니다.")
            if worker:
                worker.log_message.emit("Status: <b style='color: red;'>Order FAILED (API not connected)</b>")
            return

        # 'reduce_only'와 'position_side' 결정
        reduce_only = False
        position_side = "BOTH"

        if is_hedge:
            # 헷지 포지션: 주거래의 반대 방향으로 새로운 포지션 진입
            if side_mode == "LONG":
                position_side = "SHORT"
                reduce_only = False
            elif side_mode == "SHORT":
                position_side = "LONG"
                reduce_only = False
        else:
            # 주거래 포지션 로직
            if side_mode == "LONG":
                if order_side.upper() == "BUY":  # 롱 진입
                    position_side = "LONG"
                    reduce_only = False
                elif order_side.upper() == "SELL":  # 롱 청산
                    position_side = "LONG"
                    reduce_only = True
            elif side_mode == "SHORT":
                if order_side.upper() == "SELL":  # 숏 진입
                    position_side = "SHORT"
                    reduce_only = False
                elif order_side.upper() == "BUY":  # 숏 청산
                    position_side = "SHORT"
                    reduce_only = True

        try:
            print(f"Placing order [{side.upper()}]: {order_side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")

            result = api_module.place_market_order(symbol, order_side, quantity, reduce_only, position_side)

            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"[{side.upper()}] 자동매매 주문 ID {order_id}가 접수되었습니다.")
                if worker:
                    worker.log_message.emit("Status: <b style='color: blue;'>Order Placed!</b>")

                # 주문 ID를 워커에게 전달
                if is_hedge:
                    if worker and hasattr(worker, 'last_hedge_trigger_info') and worker.last_hedge_trigger_info:
                        trigger_price, qty = worker.last_hedge_trigger_info
                        worker.on_hedge_order_id_received(order_id, trigger_price, qty)
                        print(f"[{side.upper()}][슬리피지 추적] 헷지 주문 ID {order_id} 워커로 전달 (트리거가: ${trigger_price})")
                else:
                    if worker:
                        worker.order_id_received.emit(order_id)
                        print(f"[{side.upper()}][메인 주문] 주문 ID {order_id} 워커로 전달")

            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"AutoTraderGUI [{side.upper()}]: 자동매매 주문이 API에서 거부됨: {msg}")
                if worker:
                    worker.log_message.emit(f"Status: <b style='color: red;'>Order REJECTED: {msg}</b>")
            else:
                print(f"AutoTraderGUI [{side.upper()}]: 자동매매 주문 API 요청 실패. {result}")
                if worker:
                    worker.log_message.emit("Status: <b style='color: red;'>Order FAILED (API request)</b>")

        except Exception as e:
            print(f"AutoTraderGUI [{side.upper()}]: 자동매매 주문 중 Python 오류: {e}")
            if worker:
                worker.log_message.emit(f"Status: <b style='color: red;'>Order FAILED (Python error)</b>")

    @pyqtSlot(str, str, str, str, bool)
    def on_auto_trade_limit_order(self, symbol, side, quantity, price, is_hedge=False):
        """자동매매 워커로부터 받은 지정가 주문 신호를 실행합니다."""

        trade_type = "HEDGE" if is_hedge else "MAIN"
        print(f"AutoTraderGUI: 지정가 주문 신호 수신 -> [{trade_type}] {side} {quantity} {symbol} @ ${price}")

        if not self.api_module or not self.api_module.is_api_key_active():
            print("AutoTraderGUI: API가 연결되지 않아 지정가 주문을 실행할 수 없습니다.")
            self.auto_trade_worker.log_message.emit("Status: <b style='color: red;'>Limit Order FAILED (API not connected)</b>")
            return

        # 'reduce_only'와 'position_side' 결정 (시장가 주문과 동일한 로직)
        reduce_only = False
        position_side = "BOTH"

        if is_hedge:
            # 헷지 포지션: 주거래의 반대 방향으로 새로운 포지션 진입
            if self.auto_trade_side_mode == "LONG":
                position_side = "SHORT"
                reduce_only = False
            elif self.auto_trade_side_mode == "SHORT":
                position_side = "LONG"
                reduce_only = False
        else:
            # 주거래 포지션 로직
            if self.auto_trade_side_mode == "LONG":
                if side.upper() == "BUY":  # 롱 진입
                    position_side = "LONG"
                    reduce_only = False
                elif side.upper() == "SELL":  # 롱 청산
                    position_side = "LONG"
                    reduce_only = True

            elif self.auto_trade_side_mode == "SHORT":
                if side.upper() == "SELL":  # 숏 진입
                    position_side = "SHORT"
                    reduce_only = False
                elif side.upper() == "BUY":  # 숏 청산
                    position_side = "SHORT"
                    reduce_only = True

        try:
            # 지정가 주문 실행
            print(f"Placing limit order: {side} {quantity} {symbol} @ ${price} (reduceOnly={reduce_only}, positionSide={position_side})")

            result = self.api_module.place_limit_order(symbol, side, quantity, price, reduce_only, position_side)

            # Bybit(retCode 0) 응답 처리
            if result and (result.get('orderId') or result.get('retCode') == 0):
                order_id = str(result.get('orderId', result.get('retCode', 'N/A')))
                print(f"지정가 주문 ID {order_id}가 접수되었습니다.")
                self.auto_trade_worker.log_message.emit("Status: <b style='color: blue;'>Limit Order Placed!</b>")

                # 주문 ID와 현재 Step 매핑 저장 (차트 라벨용)
                if hasattr(self.auto_trade_worker, 'current_step'):
                    # 다음 단계 주문이므로 current_step + 1
                    step_for_order = self.auto_trade_worker.current_step + 1
                    self.order_step_map[order_id] = step_for_order
                    print(f"[차트] 주문 ID {order_id}를 Step {step_for_order + 1}로 매핑")

                # 주문 ID를 워커로 전달 (다음 단계 진입 주문인 경우에만)
                if not is_hedge:
                    self.auto_trade_worker.order_id_received.emit(order_id)
                    print(f"[DCA] 다음 단계 주문 ID {order_id}를 워커에 전달")

                    # Insight 탭 업데이트: NSO 주문 정보는 m_orders_updated 시그널로 처리됨

            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"AutoTraderGUI: 지정가 주문이 API에서 거부됨: {msg}")
                self.auto_trade_worker.log_message.emit(f"Status: <b style='color: red;'>Limit Order REJECTED: {msg}</b>")
            else:
                print(f"AutoTraderGUI: 지정가 주문 API 요청 실패. {result}")
                self.auto_trade_worker.log_message.emit("Status: <b style='color: red;'>Limit Order FAILED (API request)</b>")

        except Exception as e:
            print(f"AutoTraderGUI: 지정가 주문 중 Python 오류: {e}")
            self.auto_trade_worker.log_message.emit(f"Status: <b style='color: red;'>Limit Order FAILED (Python error)</b>")

    def on_auto_trade_limit_order_for_side(self, side, symbol, order_side, quantity, price, is_hedge=False):
        """Side별 자동매매 워커로부터 받은 지정가 주문 신호를 해당 계정으로 실행합니다.

        Args:
            side: 'long' 또는 'short' (어느 패널/계정에서 온 신호인지)
            symbol: 거래 심볼
            order_side: 'BUY' 또는 'SELL'
            quantity: 주문 수량
            price: 지정가
            is_hedge: 헷지 주문 여부
        """
        trade_type = "HEDGE" if is_hedge else "MAIN"
        print(f"AutoTraderGUI [{side.upper()}]: 지정가 주문 신호 수신 -> [{trade_type}] {order_side} {quantity} {symbol} @ ${price}")

        # side별 API 모듈과 워커 가져오기
        api_module = self.api_modules.get(side)
        worker = self.auto_trade_workers.get(side)
        side_mode = self.side_modes.get(side, 'LONG' if side == 'long' else 'SHORT')

        if not api_module or not api_module.is_api_key_active():
            print(f"AutoTraderGUI [{side.upper()}]: API가 연결되지 않아 지정가 주문을 실행할 수 없습니다.")
            if worker:
                worker.log_message.emit("Status: <b style='color: red;'>Limit Order FAILED (API not connected)</b>")
            return

        # 'reduce_only'와 'position_side' 결정
        reduce_only = False
        position_side = "BOTH"

        if is_hedge:
            if side_mode == "LONG":
                position_side = "SHORT"
                reduce_only = False
            elif side_mode == "SHORT":
                position_side = "LONG"
                reduce_only = False
        else:
            if side_mode == "LONG":
                if order_side.upper() == "BUY":
                    position_side = "LONG"
                    reduce_only = False
                elif order_side.upper() == "SELL":
                    position_side = "LONG"
                    reduce_only = True
            elif side_mode == "SHORT":
                if order_side.upper() == "SELL":
                    position_side = "SHORT"
                    reduce_only = False
                elif order_side.upper() == "BUY":
                    position_side = "SHORT"
                    reduce_only = True

        try:
            print(f"Placing limit order [{side.upper()}]: {order_side} {quantity} {symbol} @ ${price} (reduceOnly={reduce_only}, positionSide={position_side})")

            result = api_module.place_limit_order(symbol, order_side, quantity, price, reduce_only, position_side)

            if result and (result.get('orderId') or result.get('retCode') == 0):
                order_id = str(result.get('orderId', result.get('retCode', 'N/A')))
                print(f"[{side.upper()}] 지정가 주문 ID {order_id}가 접수되었습니다.")
                if worker:
                    worker.log_message.emit("Status: <b style='color: blue;'>Limit Order Placed!</b>")

                # 주문 ID와 현재 Step 매핑 저장 (차트 라벨용)
                if worker and hasattr(worker, 'current_step'):
                    step_for_order = worker.current_step + 1
                    self.order_step_map[order_id] = step_for_order
                    print(f"[{side.upper()}][차트] 주문 ID {order_id}를 Step {step_for_order + 1}로 매핑")

                # 주문 ID를 워커로 전달 (다음 단계 진입 주문인 경우에만)
                if not is_hedge and worker:
                    worker.order_id_received.emit(order_id)
                    print(f"[{side.upper()}][DCA] 다음 단계 주문 ID {order_id}를 워커에 전달")

            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"AutoTraderGUI [{side.upper()}]: 지정가 주문이 API에서 거부됨: {msg}")
                if worker:
                    worker.log_message.emit(f"Status: <b style='color: red;'>Limit Order REJECTED: {msg}</b>")
            else:
                print(f"AutoTraderGUI [{side.upper()}]: 지정가 주문 API 요청 실패. {result}")
                if worker:
                    worker.log_message.emit("Status: <b style='color: red;'>Limit Order FAILED (API request)</b>")

        except Exception as e:
            print(f"AutoTraderGUI [{side.upper()}]: 지정가 주문 중 Python 오류: {e}")
            if worker:
                worker.log_message.emit(f"Status: <b style='color: red;'>Limit Order FAILED (Python error)</b>")

    @pyqtSlot(str, float)
    def on_adjust_next_step_order(self, order_id, slippage, panel_side=None):
        """슬리피지 발생 시 다음 단계 진입 주문 가격 조정"""
        print(f"[슬리피지 조정] 주문 ID '{order_id}' 가격 조정 요청 (슬리피지: ${self.fmt_price(slippage)}, side={panel_side})")

        # side-aware API 및 워커 선택
        api = self.api_modules.get(panel_side) if panel_side else self.api_module
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker

        if not api or not api.is_api_key_active():
            print("[슬리피지 조정] API가 연결되지 않아 주문을 조정할 수 없습니다.")
            return

        try:
            # 1. 기존 주문 정보 조회 (현재 주문 가격과 수량 확인)
            all_orders = api.get_initial_open_orders()

            # 현재 심볼의 주문만 필터링
            order_info = [o for o in all_orders if o.get('symbol') == self.current_symbol]

            target_order = None
            for order in order_info:
                if str(order.get('orderId')) == str(order_id):
                    target_order = order
                    break

            if not target_order:
                print(f"[슬리피지 조정] 주문 {order_id}를 찾을 수 없습니다. (이미 체결되었을 수 있음)")
                return

            old_price = float(target_order.get('price', 0))
            qty = target_order.get('origQty', 0)
            side = target_order.get('side')

            if old_price == 0:
                print(f"[슬리피지 조정] 주문 가격 정보를 가져올 수 없습니다.")
                return

            # 2. 새 가격 계산 (슬리피지만큼 조정)
            new_price = old_price + slippage

            # 가격 정밀도 조정
            tick_size = float(worker.symbol_info.get('priceFilter', {}).get('tickSize', '0.01'))
            import v7_dual_trading_utils as trading_utils
            price_precision = trading_utils.count_decimal_places(tick_size)
            new_price_adjusted = trading_utils.adjust_price(new_price, tick_size, price_precision)

            print(f"[슬리피지 조정] 주문 가격: ${self.fmt_price(old_price)} → ${self.fmt_price(new_price_adjusted)}")

            # 3. 기존 주문 취소
            print(f"[슬리피지 조정] 기존 주문 취소 중: {order_id}")
            cancel_result = api.cancel_order(self.current_symbol, order_id)

            if not (cancel_result and (cancel_result.get('orderId') or cancel_result.get('retCode') == 0)):
                print(f"[슬리피지 조정] 주문 취소 실패: {cancel_result}")
                return

            print(f"[슬리피지 조정] 주문 {order_id} 취소 성공")

            # 4. 새 가격으로 재주문
            position_side = worker.side_mode  # "LONG" 또는 "SHORT"
            print(f"[슬리피지 조정] 새 주문 생성: {side} {qty} @ ${self.fmt_price(new_price_adjusted)}")

            result = api.place_limit_order(
                self.current_symbol, side, str(qty), str(new_price_adjusted), False, position_side
            )

            if result and result.get('orderId'):
                new_order_id = str(result.get('orderId'))
                print(f"[슬리피지 조정] 새 주문 ID {new_order_id} 생성 성공")

                # 새 주문 ID를 워커에 전달
                worker.next_step_order_id = new_order_id
                worker.order_id_received.emit(new_order_id)

                # 차트에 주문 라인 업데이트
                self.remove_order_line_from_chart(order_id)
                next_step = worker.current_step + 1
                self.draw_order_line_on_chart(new_price_adjusted, side, new_order_id)
                # 주문 스텝 매핑 업데이트
                self.order_step_map[new_order_id] = next_step

                print(f"[슬리피지 조정] 주문 조정 완료")
            else:
                print(f"[슬리피지 조정] 새 주문 생성 실패: {result}")

        except Exception as e:
            print(f"[슬리피지 조정] 오류 발생: {e}")
            import traceback
            traceback.print_exc()

    def on_uptrend_entry_request(self, order_id, panel_side=None):
        """상승 중 추가진입: 메인 주문 취소 + 헷지 트리거(내부) 제거 + 시장가 진입"""
        _el = "하강진입" if panel_side == "short" else "상승진입"
        print(f"[{_el}] 주문 ID '{order_id}' 취소 요청 수신 (side={panel_side})")

        # side-aware API 및 워커 선택
        api = self.api_modules.get(panel_side) if panel_side else self.api_module
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker

        if not api or not api.is_api_key_active():
            return

        try:
            # 1. 메인 진입 지정가 주문 취소 (실제 주문이므로 API 취소 필요)
            if order_id and order_id.strip():
                print(f"[{_el}] 메인 진입 지정가 주문 취소 중: {order_id}")
                api.cancel_order(self.current_symbol, order_id)
            else:
                print(f"[{_el}] 취소할 메인 지정가 주문 없음 (익절 모니터링 모드 등)")

            # 1-1. M4 마커 제거 (역방향진입 후 익절 모니터링 모드에서는 새 M4가 안 나오므로 직접 제거)
            if panel_side:
                self.remove_m4_marker_for_side(panel_side)
            else:
                self.remove_m4_order_marker()

            # 2. 헷지 트리거 초기화 (소프트 트리거이므로 API 취소 불필요, 내부 상태만 초기화)
            if worker.hedge_trigger_prices:
                print(f"[{_el}] 헷지 트리거 {len(worker.hedge_trigger_prices)}개 비활성화")

                # 워커의 헷지 관련 상태 초기화
                worker.hedge_trigger_prices.clear()
                worker.remaining_hedge_qty = 0

                # 슬리피지 추적용 딕셔너리도 정리
                worker.pending_hedge_orders.clear()

                # 차트에서 해당 side의 헷지 트리거 마커만 제거
                if panel_side:
                    self.remove_hedge_trigger_markers_for_side(panel_side)
                else:
                    self.remove_all_hedge_trigger_markers()
                print(f"[{_el}] 헷지 트리거 마커 제거 완료")

            # 3. 메인 포지션 시장가 진입
            next_step = worker.current_step + 1
            if next_step < len(worker.entry_qty_list):
                next_entry_qty = worker.entry_qty_list[next_step]
                side = "BUY" if worker.side_mode == "LONG" else "SELL"
                position_side = worker.side_mode  # "LONG" 또는 "SHORT"

                print(f"[{_el}] 시장가 즉시 진입: {side} {next_entry_qty} {self.current_symbol} (positionSide={position_side})")

                result = api.place_market_order(
                    self.current_symbol, side, str(next_entry_qty), False, position_side
                )

                if result and result.get('orderId'):
                    worker.next_step_order_id = str(result.get('orderId'))
                    log_color = "green" if worker.side_mode == "LONG" else "red"
                    worker.log_message.emit(f"Status: <b style='color: {log_color};'>Uptrend Entry Executed!</b>")
                else:
                    print(f"[{_el}] 시장가 주문 실패: {result}")
                    worker.log_message.emit("Status: <b style='color: red;'>Uptrend Entry Failed</b>")

        except Exception as e:
            print(f"[{_el}] 오류 발생: {e}")
            import traceback
            traceback.print_exc()

    def on_profit_taking_request(self, side=None):
        """익절: 해당 side의 포지션 청산 및 자동매매 재시작"""
        print(f"[익절] GUI에서 전체 청산 및 재시작 요청 수신 (side={side})")

        # 워커의 current_step을 저장 (워커가 즉시 리셋하므로 여기서 캡처)
        worker = self.auto_trade_workers.get(side) if side else self.auto_trade_worker
        self._profit_taking_step = worker.current_step if worker else 0

        # side별 API 모듈 결정
        api = self.api_modules.get(side) if side else self.api_module
        if not api or not api.is_api_key_active():
            print(f"[익절] API가 연결되지 않아 청산을 실행할 수 없습니다. (side={side})")
            return

        try:
            # 1. 해당 side의 차트 마커만 제거
            if side:
                # side별 주문 라인 제거
                order_table = self.order_tables.get(side)
                if order_table:
                    for row in range(order_table.rowCount()):
                        try:
                            order_id = order_table.item(row, 7).text() if order_table.item(row, 7) else ""
                            if order_id:
                                self.remove_order_line_from_chart(order_id)
                        except:
                            pass
                self.remove_hedge_trigger_markers_for_side(side)
                self.remove_m4_marker_for_side(side)
                self.remove_profit_target_marker_for_side(side)
                self.remove_uptrend_threshold_marker_for_side(side)
                self.remove_uptrend_threshold_2_marker_for_side(side)
                self.remove_break_even_line(side)
            else:
                # side 미지정 시 레거시 동작 (전체 제거)
                self.remove_all_order_lines_from_chart()
                self.remove_all_hedge_trigger_markers()
                self.remove_profit_target_marker()
                self.remove_uptrend_threshold_marker()
                self.remove_uptrend_threshold_2_marker()
            self.remove_emergency_exit_line_marker(side)

            # 1-1. Insight 탭 초기화 (해당 side만)
            self.reset_insight_tab(side)
            print(f"[익절] Insight 탭 초기화 완료 (side={side})")

            # 2. 미체결 주문 취소 (해당 side의 API 사용)
            print(f"[익절] 미체결 주문 취소 중... (side={side})")
            try:
                open_orders = api.get_initial_open_orders()
                if open_orders:
                    for order in open_orders:
                        if order.get('symbol') == self.current_symbol:
                            order_id = order.get('orderId')
                            if order_id:
                                print(f"[익절] 주문 취소: {order_id}")
                                api.cancel_order(self.current_symbol, order_id)
                    print(f"[익절] {len([o for o in open_orders if o.get('symbol') == self.current_symbol])}개 주문 취소 완료")
                else:
                    print("[익절] 취소할 미체결 주문 없음")
            except Exception as e:
                print(f"[익절] 주문 취소 중 오류: {e}")

            # 3. 포지션 청산 (해당 side 계정의 모든 포지션)
            print(f"[익절] 포지션 청산 중... (side={side})")
            position_data = self.live_position_data_by_side.get(side, {}) if side else self.live_position_data
            print(f"[익절] 청산 전 포지션 데이터 확인: {position_data}")

            positions_closed = 0
            total_unrealized_pnl = 0.0

            # LONG 포지션 청산
            long_pos_key = f"{self.current_symbol}_LONG"
            if long_pos_key in position_data:
                long_qty = abs(float(position_data[long_pos_key].get('amount', 0)))
                long_pnl = float(position_data[long_pos_key].get('unrealisedPnl', position_data[long_pos_key].get('pnl', 0)))
                total_unrealized_pnl += long_pnl
                print(f"[익절] LONG 포지션 size: {long_qty}, 미실현 손익: {long_pnl}")
                if long_qty > 0:
                    print(f"[익절] LONG 포지션 청산 주문 실행: {long_qty}")
                    result = api.place_market_order(self.current_symbol, "SELL", str(long_qty), False, "LONG")
                    print(f"[익절] LONG 청산 주문 결과: {result}")
                    positions_closed += 1

            # SHORT 포지션 청산
            short_pos_key = f"{self.current_symbol}_SHORT"
            if short_pos_key in position_data:
                short_qty = abs(float(position_data[short_pos_key].get('amount', 0)))
                short_pnl = float(position_data[short_pos_key].get('unrealisedPnl', position_data[short_pos_key].get('pnl', 0)))
                total_unrealized_pnl += short_pnl
                print(f"[익절] SHORT 포지션 size: {short_qty}, 미실현 손익: {short_pnl}")
                if short_qty > 0:
                    print(f"[익절] SHORT 포지션 청산 주문 실행: {short_qty}")
                    result = api.place_market_order(self.current_symbol, "BUY", str(short_qty), True, "SHORT")
                    print(f"[익절] SHORT 청산 주문 결과: {result}")
                    positions_closed += 1

            if positions_closed == 0:
                print("[익절] 청산할 포지션이 없습니다.")

            # 청산 손익 계산 (사이클 시작 잔액 기준으로 실제 누적 손익 계산)
            # 현재 잔액 조회 (side별 잔액 사용)
            live_balances = self.live_balances_by_side.get(side, {}) if side else self.live_balances
            current_balance = 0.0
            market_type = self.current_market_types.get(side, 'fapi') if side else self.current_market_type
            if market_type == "fapi":
                current_balance = float(live_balances.get("USDT", "0.0"))
            elif market_type == "spot":
                if self.current_symbol.endswith("BTC"):
                    current_balance = float(live_balances.get("BTC", "0.0"))
                else:
                    current_balance = float(live_balances.get("ETH", "0.0"))

            # 실제 손익 = 현재 잔액 - 사이클 시작 잔액
            actual_cycle_pnl = current_balance - self.cycle_start_balance
            self.cycle_pnl_before_closure = actual_cycle_pnl

            print(f"[익절] 청산 전 총 미실현 손익: {total_unrealized_pnl}")
            print(f"[익절] 사이클 시작 잔액: {self.cycle_start_balance:.2f}")
            print(f"[익절] 현재 잔액: {current_balance:.2f}")
            print(f"[익절] 실제 사이클 손익: {actual_cycle_pnl:.2f}")

            print(f"[익절] 청산 완료 ({positions_closed}개 포지션)")

            # 4. DCA 상태 완전 초기화 (config 파일에서도 삭제)
            print(f"[익절] DCA 상태 초기화 중... (side={side})")
            config_key = f"dca_state_{side}" if side else "dca_state"
            if config_key in self.config_data:
                del self.config_data[config_key]
                config_manager.save_config_data(self.config_data)
                print(f"[익절] DCA 상태 파일 삭제 완료: {config_key}")

            # 5. 워커 상태가 이미 초기화되었는지 확인
            worker = self.auto_trade_workers.get(side) if side else self.auto_trade_worker
            print(f"[익절] 워커 상태 확인: is_running={worker.is_running}, current_step={worker.current_step}")

            # 6. 청산 완료 플래그 설정 및 QTimer 기반 비동기 모니터링
            self.waiting_for_position_closure = True
            self.position_closure_check_start_time = time.time()
            self.closure_long_pos_key = long_pos_key
            self.closure_short_pos_key = short_pos_key
            self.closure_side = side  # 익절 요청 side 저장
            self.position_closure_retry_count = 0

            print(f"[익절] 포지션 청산 완료 대기 중 (비동기 모니터링 시작, side={side})...")

            # QTimer를 사용한 비동기 폴링으로 GUI 블로킹 방지
            if self.position_closure_timer is None:
                self.position_closure_timer = QTimer(self)
                self.position_closure_timer.timeout.connect(self.check_position_closure)

            self.position_closure_timer.start(100)  # 0.1초마다 체크 (비동기)

        except Exception as e:
            print(f"[익절] 포지션 청산 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def check_position_closure(self):
        """포지션 청산 완료 여부를 비동기로 확인 (QTimer 콜백)"""
        try:
            if not self.waiting_for_position_closure:
                # 이미 청산 완료되었거나 타이머가 중지된 경우
                if self.position_closure_timer and self.position_closure_timer.isActive():
                    self.position_closure_timer.stop()
                return

            max_wait_time = 10  # 최대 10초 대기
            elapsed = time.time() - self.position_closure_check_start_time

            # 실시간으로 포지션 확인 (해당 side의 position_data 사용)
            closure_side = getattr(self, 'closure_side', None)
            pos_data = self.live_position_data_by_side.get(closure_side, {}) if closure_side else self.live_position_data
            current_long = abs(float(pos_data.get(self.closure_long_pos_key, {}).get('amount', 0)))
            current_short = abs(float(pos_data.get(self.closure_short_pos_key, {}).get('amount', 0)))

            if current_long < 0.0001 and current_short < 0.0001:
                # 청산 완료!
                print(f"[익절] 포지션 청산 완료 확인! (소요시간: {elapsed:.2f}초)")
                self.waiting_for_position_closure = False
                self.position_closure_timer.stop()
                self.on_position_closure_completed()  # 후속 처리 함수 호출
                return

            # 타임아웃 체크
            if elapsed >= max_wait_time:
                self.position_closure_timer.stop()
                self.on_position_closure_timeout()  # 타임아웃 처리 함수 호출
        except Exception as e:
            print(f"[익절] 포지션 청산 확인 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_position_closure_completed(self):
        """포지션 청산이 완료되었을 때 후속 처리"""
        try:
            closure_side = getattr(self, 'closure_side', None)
            worker = self.auto_trade_workers.get(closure_side) if closure_side else self.auto_trade_worker

            # 사이클 완료 통계 업데이트 (청산 완료 후 잔액으로 PnL 재계산)
            start_bal = self.start_balances_by_side.get(closure_side, 0.0) if closure_side else self.cycle_start_balance
            if start_bal > 0:
                # 청산 완료 후 실제 잔액으로 PnL 계산 (청산 전 값 대신)
                live_balances = self.live_balances_by_side.get(closure_side, {}) if closure_side else self.live_balances
                market_type = self.current_market_types.get(closure_side, 'fapi') if closure_side else self.current_market_type
                current_balance = 0.0
                if market_type == "fapi":
                    current_balance = float(live_balances.get("USDT", "0.0"))
                elif market_type == "dapi":
                    if "BTC" in self.current_symbol:
                        current_balance = float(live_balances.get("BTC", "0.0"))
                    elif "ETH" in self.current_symbol:
                        current_balance = float(live_balances.get("ETH", "0.0"))

                realized_pnl = current_balance - start_bal
                self.total_cycles_completed += 1
                self.cumulative_pnl += realized_pnl
                self.update_cycle_pnl_display()
                print(f"[통계] 사이클 완료: {self.total_cycles_completed}회, 이번 손익: {realized_pnl:.4f} (잔액: {current_balance:.4f} - 시작: {start_bal:.4f}), 누적: {self.cumulative_pnl:.4f}")

                # Statistics 탭: 사이클 종료 기록
                if worker and closure_side:
                    step = getattr(self, '_profit_taking_step', worker.current_step)
                    pnl_pct = (realized_pnl / start_bal * 100)
                    self.record_cycle_end_stat(closure_side, step, pnl_pct)

            # 예약 종료 확인 후 재시작 여부 결정
            if worker and hasattr(worker, 'scheduled_stop') and worker.scheduled_stop:
                print(f"[익절] 예약 종료가 설정되어 있어 자동매매를 중지합니다. (side={closure_side})")
                self.on_auto_trade_log("Status: <b style='color: orange;'>예약 종료 - 익절 완료 후 자동매매 중지</b>|||")

                # 자동매매 중지 (버튼 상태 변경)
                worker.stop_trading()
                self._set_side_button_stopped(closure_side)

                # Insight 탭 및 차트 마커 초기화
                self.reset_insight_tab()
                if closure_side:
                    self.remove_emergency_exit_line_marker(closure_side)
                    self.initial_main_entry_price_by_side[closure_side] = None
                    self.initial_hedge_entry_price_by_side[closure_side] = None
                else:
                    self.remove_emergency_exit_line_marker()
                    for s in ['long', 'short']:
                        self.initial_main_entry_price_by_side[s] = None
                        self.initial_hedge_entry_price_by_side[s] = None

                print("[익절] 예약 종료 완료")
                return

            # 자동매매 재시작 (API로 실제 포지션 재확인)
            self.restart_auto_trade_after_closure()

        except Exception as e:
            print(f"[익절] 청산 완료 후속 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_position_closure_timeout(self):
        """포지션 청산 타임아웃 발생 시 처리"""
        try:
            max_wait_time = 10
            closure_side = getattr(self, 'closure_side', None)
            pos_data = self.live_position_data_by_side.get(closure_side, {}) if closure_side else self.live_position_data
            api = self.api_modules.get(closure_side) if closure_side else self.api_module
            worker = self.auto_trade_workers.get(closure_side) if closure_side else self.auto_trade_worker

            final_check_long = abs(float(pos_data.get(self.closure_long_pos_key, {}).get('amount', 0)))
            final_check_short = abs(float(pos_data.get(self.closure_short_pos_key, {}).get('amount', 0)))
            print(f"[익절] 경고: {max_wait_time}초 타임아웃 - LONG: {final_check_long}, SHORT: {final_check_short} (side={closure_side})")

            if final_check_long > 0.0001 or final_check_short > 0.0001:
                # 재청산 시도 횟수 제한 (최대 2회)
                if not hasattr(self, 'position_closure_retry_count'):
                    self.position_closure_retry_count = 0

                if self.position_closure_retry_count >= 2:
                    print(f"[익절] 경고: 최대 재청산 시도 횟수({self.position_closure_retry_count})에 도달. 청산 실패로 처리.")
                    print("[익절] 자동매매를 중지합니다.")
                    self.on_auto_trade_log("Status: <b style='color: red;'>청산 실패 (최대 재시도 초과) - 자동매매 중지</b>|||")

                    # 자동매매 중지
                    worker.stop_trading()
                    self._set_side_button_stopped(closure_side)

                    # Insight 탭 초기화
                    self.reset_insight_tab()
                    if closure_side:
                        self.initial_main_entry_price_by_side[closure_side] = None
                        self.initial_hedge_entry_price_by_side[closure_side] = None
                    return

                self.position_closure_retry_count += 1
                print(f"[익절] WebSocket 데이터에 포지션이 남아있어 재청산 시도... (시도 {self.position_closure_retry_count}/2, side={closure_side})")

                long_already_closed = False
                short_already_closed = False

                # LONG 포지션 재청산 (해당 계정 내의 LONG 포지션)
                if final_check_long > 0.0001:
                    print(f"[익절] LONG 포지션 재청산: {final_check_long}")
                    try:
                        result = api.place_market_order(self.current_symbol, "SELL", str(final_check_long), False, "LONG")
                        print(f"[익절] LONG 재청산 주문 결과: {result}")
                        if isinstance(result, dict) and 'code' in result:
                            if result['code'] == 110017:
                                print(f"[익절] LONG 포지션 이미 청산됨 (에러 코드 110017)")
                                long_already_closed = True
                        elif isinstance(result, dict) and 'orderId' in result:
                            print(f"[익절] LONG 재청산 주문 접수됨 - 청산 완료 대기 재시작")
                            long_already_closed = False
                    except Exception as e:
                        print(f"[익절] LONG 재청산 실패: {e}")
                else:
                    long_already_closed = True

                # SHORT 포지션 재청산 (해당 계정 내의 SHORT 포지션)
                if final_check_short > 0.0001:
                    print(f"[익절] SHORT 포지션 재청산: {final_check_short}")
                    try:
                        result = api.place_market_order(self.current_symbol, "BUY", str(final_check_short), True, "SHORT")
                        print(f"[익절] SHORT 재청산 주문 결과: {result}")
                        if isinstance(result, dict) and 'code' in result:
                            if result['code'] == 110017:
                                print(f"[익절] SHORT 포지션 이미 청산됨 (에러 코드 110017)")
                                short_already_closed = True
                        elif isinstance(result, dict) and 'orderId' in result:
                            print(f"[익절] SHORT 재청산 주문 접수됨 - 청산 완료 대기 재시작")
                            short_already_closed = False
                    except Exception as e:
                        print(f"[익절] SHORT 재청산 실패: {e}")
                else:
                    short_already_closed = True

                # 청산 상태 확인
                if long_already_closed and short_already_closed:
                    print("[익절] 모든 포지션 청산 확인됨 (에러 코드 110017)")
                else:
                    # 재청산 주문이 실행된 경우 - 다시 폴링 시작
                    if (final_check_long > 0.0001 and not long_already_closed) or (final_check_short > 0.0001 and not short_already_closed):
                        print(f"[익절] 재청산 주문 발행 완료 - 청산 완료 대기 재시작 (추가 5초)")
                        self.waiting_for_position_closure = True
                        self.position_closure_check_start_time = time.time()
                        self.position_closure_timer.start(100)
                        return

                    # 재청산도 실패한 경우
                    print(f"[익절] 경고: 일부 포지션 재청산 실패 - LONG: {long_already_closed}, SHORT: {short_already_closed}")
                    print("[익절] 자동매매를 중지합니다.")
                    self.on_auto_trade_log("Status: <b style='color: red;'>청산 실패 - 자동매매 중지</b>|||")

                    # 자동매매 중지
                    worker.stop_trading()
                    self._set_side_button_stopped(closure_side)

                    # Insight 탭 및 차트 마커 초기화
                    self.reset_insight_tab()
                    self.remove_emergency_exit_line_marker(closure_side)
                    if closure_side:
                        self.initial_main_entry_price_by_side[closure_side] = None
                        self.initial_hedge_entry_price_by_side[closure_side] = None
                    return  # 재시작하지 않고 종료
            else:
                print("[익절] 청산 완료 확인 (타임아웃 후 재확인)")

            self.waiting_for_position_closure = False

            # 예약 종료 확인 후 재시작 여부 결정
            closure_side_for_restart = getattr(self, 'closure_side', None)
            worker_for_restart = self.auto_trade_workers.get(closure_side_for_restart) if closure_side_for_restart else self.auto_trade_worker
            if hasattr(worker_for_restart, 'scheduled_stop') and worker_for_restart.scheduled_stop:
                print(f"[익절] 예약 종료가 설정되어 있어 자동매매를 중지합니다. (side={closure_side_for_restart})")
                self.on_auto_trade_log("Status: <b style='color: orange;'>예약 종료 - 익절 완료 후 자동매매 중지</b>|||")

                # 자동매매 중지 (버튼 상태 변경)
                worker_for_restart.stop_trading()
                self._set_side_button_stopped(closure_side_for_restart)

                # Insight 탭 및 차트 마커 초기화
                self.reset_insight_tab()
                self.remove_emergency_exit_line_marker(closure_side_for_restart)
                if closure_side_for_restart:
                    self.initial_main_entry_price_by_side[closure_side_for_restart] = None
                    self.initial_hedge_entry_price_by_side[closure_side_for_restart] = None

                print("[익절] 예약 종료 완료")
            else:
                # 자동매매 재시작 (API로 실제 포지션 재확인)
                self.restart_auto_trade_after_closure()

        except Exception as e:
            print(f"[익절] 타임아웃 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def _check_and_execute_reserve_fund(self, closure_side, callback):
        """비축금(Reserve Fund) 적립 또는 손실 시 투입"""
        try:
            reserve_enabled = self.config_data.get("app_settings", {}).get("reserve_enabled", True)
            if not reserve_enabled:
                callback()
                return

            reserve_ratio = self.strategy_settings.get("RESERVE_FUND_RATIO", 0.0)
            loss_threshold = self.strategy_settings.get("RESERVE_FUND_USAGE_LOSS_THRESHOLD", 10.0)
            
            if reserve_ratio <= 0 and loss_threshold <= 0:
                callback()
                return

            start_bal = self.start_balances_by_side.get(closure_side, 0.0) if closure_side else self.cycle_start_balance
            
            # 현재 잔액 계산
            live_balances = self.live_balances_by_side.get(closure_side, {}) if closure_side else self.live_balances
            market_type = self.current_market_types.get(closure_side, 'fapi') if closure_side else self.current_market_type
            current_balance = 0.0
            if market_type == "fapi":
                current_balance = float(live_balances.get("USDT", "0.0"))
            elif market_type == "spot":
                if "BTC" in self.current_symbol:
                    current_balance = float(live_balances.get("BTC", "0.0"))
                elif "ETH" in self.current_symbol:
                    current_balance = float(live_balances.get("ETH", "0.0"))
            
            if start_bal <= 0 or current_balance <= 0:
                callback()
                return

            realized_pnl = current_balance - start_bal
            
            primary_account_name = self.current_account_names.get(closure_side)
            primary_account_data = self.accounts.get(primary_account_name) if primary_account_name else None
            
            if not primary_account_data:
                callback()
                return

            mode = None
            amount = 0.0
            secondary_account_data = None
            
            # 수익인 경우: 비축금 적립
            if realized_pnl > 0 and reserve_ratio > 0:
                mode = 'SAVE'
                amount = realized_pnl * (reserve_ratio / 100.0)
                print(f"[Reserve Fund] 수익 발생 ({realized_pnl:.4f}). {reserve_ratio}% 인 {amount:.4f} USDT를 비축금으로 적립합니다.")
                
            # 손실인 경우: 지정한 퍼센트 이상 손실 시 비축금 전액 투입
            elif realized_pnl < 0 and loss_threshold > 0:
                loss_percent = (abs(realized_pnl) / start_bal) * 100.0
                if loss_percent >= loss_threshold:
                    mode = 'RESTORE'
                    print(f"[Reserve Fund] 손실 기준 도달 ({loss_percent:.2f}% >= {loss_threshold}%). 비축금을 전액 투입합니다.")
                    
                    # 반대편 계정 찾기
                    other_side = 'short' if closure_side == 'long' else 'long'
                    secondary_account_name = self.current_account_names.get(other_side)
                    if secondary_account_name:
                        secondary_account_data = self.accounts.get(secondary_account_name)
                        
            if not mode:
                callback()
                return

            self.on_auto_trade_log_for_side(
                closure_side,
                f"Status: <b style='color: #00BFFF;'>Reserve Fund: {'적립' if mode == 'SAVE' else '복구'} 처리 중...</b>|||"
            )

            self.reserve_fund_thread = ReserveFundTransferThread(
                mode, amount, primary_account_data, secondary_account_data, self
            )
            self.reserve_fund_thread.transfer_finished.connect(
                lambda success, msg: self._on_reserve_fund_finished(success, msg, closure_side, callback)
            )
            self.reserve_fund_thread.start()

        except Exception as e:
            print(f"[Reserve Fund] 처리 중 오류: {e}")
            callback()

    def _on_reserve_fund_finished(self, success, message, closure_side, callback):
        if success:
            print(f"[Reserve Fund] 성공: {message}")
            self.on_auto_trade_log_for_side(
                closure_side,
                f"Status: <b style='color: #00FF00;'>Reserve Fund 완료: {message}</b>|||"
            )
        else:
            print(f"[Reserve Fund] 실패: {message}")
            self.on_auto_trade_log_for_side(
                closure_side,
                f"Status: <b style='color: red;'>Reserve Fund 실패: {message}</b>|||"
            )
        
        self.reserve_fund_thread = None
        self.fetch_reserve_fund_balances() # 잔액 표시 즉시 업데이트
        callback()

    def fetch_reserve_fund_balances(self):
        """비축금(FUND) 잔액을 백그라운드에서 조회"""
        try:
            long_account_name = self.current_account_names.get('long')
            short_account_name = self.current_account_names.get('short')
            long_data = self.accounts.get(long_account_name) if long_account_name else None
            short_data = self.accounts.get(short_account_name) if short_account_name else None
            
            self.fetch_reserve_fund_thread = FetchReserveFundThread(long_data, short_data, self)
            self.fetch_reserve_fund_thread.result_ready.connect(self._on_fetch_reserve_fund_finished)
            self.fetch_reserve_fund_thread.start()
        except Exception as e:
            print(f"fetch_reserve_fund_balances 오류: {e}")

    def _on_fetch_reserve_fund_finished(self, balances):
        """비축금 조회 완료 콜백"""
        try:
            if 'long' in balances and self.reserve_labels.get('long'):
                self.reserve_labels['long'].setText(f"Long Reserve: {balances['long']:.4f} USDT")
            if 'short' in balances and self.reserve_labels.get('short'):
                self.reserve_labels['short'].setText(f"Short Reserve: {balances['short']:.4f} USDT")
        except Exception as e:
            print(f"_on_fetch_reserve_fund_finished 오류: {e}")

    def _check_and_execute_auto_balance(self, closure_side, callback):
        """Auto Balance: 잔액 차이 확인 및 자동 이체 실행

        Args:
            closure_side: 익절 완료된 side ('long' or 'short')
            callback: 이체 완료 후 호출할 콜백 함수
        """
        if not self.auto_balance_enabled:
            callback()
            return

        # 양쪽 USDT 잔액 확인
        long_balance = float(self.live_balances_by_side.get('long', {}).get('USDT', '0.0'))
        short_balance = float(self.live_balances_by_side.get('short', {}).get('USDT', '0.0'))

        print(f"[Auto Balance] 잔액 확인 - LONG: {long_balance:.4f}, SHORT: {short_balance:.4f}")

        if long_balance <= 0 or short_balance <= 0:
            print(f"[Auto Balance] 잔액 조회 불가 - 건너뜀")
            callback()
            return

        # 잔액 많은쪽 / 적은쪽 판별
        if long_balance > short_balance:
            rich_side, poor_side = 'long', 'short'
            rich_balance, poor_balance = long_balance, short_balance
        else:
            rich_side, poor_side = 'short', 'long'
            rich_balance, poor_balance = short_balance, long_balance

        diff_ratio = (rich_balance - poor_balance) / poor_balance
        print(f"[Auto Balance] 차이 비율: {diff_ratio * 100:.2f}% ({rich_side.upper()} > {poor_side.upper()})")

        # 익절한 side가 잔액 많은 side가 아니면 건너뜀
        if closure_side != rich_side:
            print(f"[Auto Balance] 익절 side({closure_side}) != 잔액 많은 side({rich_side}) - 건너뜀")
            callback()
            return

        # 5% 미만이면 건너뜀
        if diff_ratio < 0.05:
            print(f"[Auto Balance] 차이 {diff_ratio * 100:.2f}% < 5% - 건너뜀")
            callback()
            return

        # 이체 금액 = 차이의 절반
        transfer_amount = (rich_balance - poor_balance) / 2
        print(f"[Auto Balance] ========================================")
        print(f"[Auto Balance] 이체 실행: {rich_side.upper()} → {poor_side.upper()}, {transfer_amount:.4f} USDT")
        print(f"[Auto Balance] ========================================")

        # 계정 데이터 조회
        rich_account_name = self.current_account_names.get(rich_side)
        poor_account_name = self.current_account_names.get(poor_side)

        if not rich_account_name or not poor_account_name:
            print(f"[Auto Balance] 계정 이름 확인 불가 - 건너뜀")
            callback()
            return

        rich_account_data = self.accounts.get(rich_account_name)
        poor_account_data = self.accounts.get(poor_account_name)

        if not rich_account_data or not poor_account_data:
            print(f"[Auto Balance] 계정 데이터 확인 불가 - 건너뜀")
            callback()
            return

        # 상태 표시
        self.on_auto_trade_log_for_side(
            closure_side,
            f"Status: <b style='color: #FF8C00;'>Auto Balance: {transfer_amount:.2f} USDT 이체 중...</b>|||"
        )

        # 백그라운드 스레드에서 이체 실행
        self.auto_balance_thread = AutoBalanceThread(
            rich_account_data, poor_account_data, transfer_amount, self
        )
        self.auto_balance_thread.transfer_finished.connect(
            lambda success, msg: self._on_auto_balance_finished(success, msg, closure_side, callback)
        )
        self.auto_balance_thread.start()

    def _on_auto_balance_finished(self, success, message, closure_side, callback):
        """Auto Balance 이체 완료 콜백"""
        if success:
            print(f"[Auto Balance] 성공: {message}")
            self.on_auto_trade_log_for_side(
                closure_side,
                f"Status: <b style='color: #00FF00;'>Auto Balance 완료: {message}</b>|||"
            )
        else:
            print(f"[Auto Balance] 실패: {message}")
            self.on_auto_trade_log_for_side(
                closure_side,
                f"Status: <b style='color: red;'>Auto Balance 실패: {message}</b>|||"
            )

        self.auto_balance_thread = None

        # 성공/실패 무관하게 재시작 진행
        callback()

    def restart_auto_trade_after_closure(self):
        """포지션 청산 완료 후 자동매매 재시작"""
        try:
            closure_side = getattr(self, 'closure_side', None)
            api = self.api_modules.get(closure_side) if closure_side else self.api_module
            print(f"[익절] 자동매매 재시작 중... (side={closure_side})")
            print("[익절] ========================================")

            # API로 실제 포지션 상태 확인 (해당 계정만 확인)
            print("[익절] API로 실제 포지션 상태 확인 중...")
            try:
                api_positions = api.get_initial_positions()
                remaining_position_found = False

                for pos in api_positions:
                    if pos.get('symbol') == self.current_symbol:
                        pos_amt = abs(float(pos.get('positionAmt', 0)))
                        if pos_amt > 0.0001:
                            pos_side = pos.get('positionSide', 'BOTH')
                            if not pos_side or pos_side == 'BOTH':
                                pos_side = 'LONG' if float(pos.get('positionAmt', 0)) > 0 else 'SHORT'
                            print(f"[익절] API 확인: {pos_side} 포지션 {pos_amt} 남아있음 (account={closure_side})")
                            remaining_position_found = True

                            # 남아있는 포지션 재청산 시도 (해당 계정의 API 사용)
                            print(f"[익절] {pos_side} 포지션 재청산 시도: {pos_amt}")
                            try:
                                if pos_side == "LONG":
                                    result = api.place_market_order(self.current_symbol, "SELL", str(pos_amt), False, "LONG")
                                else:
                                    result = api.place_market_order(self.current_symbol, "BUY", str(pos_amt), True, "SHORT")
                                print(f"[익절] {pos_side} 재청산 주문 결과: {result}")
                            except Exception as e:
                                print(f"[익절] {pos_side} 재청산 실패: {e}")

                if remaining_position_found:
                    print("[익절] 재청산 후 3초 대기...")
                    QTimer.singleShot(3000, self.finalize_restart_after_closure)
                    return

                print("[익절] API 확인: 모든 포지션 정리 완료")

            except Exception as e:
                print(f"[익절] API 포지션 확인 오류: {e}")

            # 포지션이 모두 정리되었으면 비축금 처리 후 Auto Balance 체크 후 재시작
            print(f"[익절] 포지션 정리 확인 완료. 비축금 및 Auto Balance 확인 후 재시작합니다. (side={closure_side})")
            self._check_and_execute_reserve_fund(
                closure_side,
                lambda s=closure_side: self._check_and_execute_auto_balance(
                    s, lambda s2=s: self._start_auto_trade_without_position_check(side=s2)
                )
            )

        except Exception as e:
            print(f"[익절] 청산 및 재시작 오류: {e}")
            import traceback
            traceback.print_exc()

    def finalize_restart_after_closure(self):
        """재청산 후 3초 대기 후 최종 확인 및 재시작"""
        try:
            closure_side = getattr(self, 'closure_side', None)
            api = self.api_modules.get(closure_side) if closure_side else self.api_module
            worker = self.auto_trade_workers.get(closure_side) if closure_side else self.auto_trade_worker

            print(f"[익절] 재청산 후 최종 포지션 확인 중... (side={closure_side})")
            # 재청산 후 최종 확인 (해당 계정만)
            api_positions_final = api.get_initial_positions()
            still_remaining = False
            for pos in api_positions_final:
                if pos.get('symbol') == self.current_symbol:
                    pos_amt = abs(float(pos.get('positionAmt', 0)))
                    if pos_amt > 0.0001:
                        still_remaining = True
                        print(f"[익절] 경고: 재청산 후에도 포지션 {pos_amt} 남아있음 (account={closure_side})")

            if still_remaining:
                print("[익절] 경고: 포지션 정리 실패. 자동매매를 중지합니다.")
                self.on_auto_trade_log("Status: <b style='color: red;'>청산 실패 - 자동매매 중지</b>|||")

                # 자동매매 중지
                worker.stop_trading()
                self._set_side_button_stopped(closure_side)

                # Insight 탭 초기화
                self.reset_insight_tab()
                if closure_side:
                    self.initial_main_entry_price_by_side[closure_side] = None
                    self.initial_hedge_entry_price_by_side[closure_side] = None
                return

            print("[익절] 재청산 성공!")
            print("[익절] API 확인: 모든 포지션 정리 완료")
            print(f"[익절] 포지션 정리 확인 완료. 비축금 및 Auto Balance 확인 후 재시작합니다. (side={closure_side})")
            self._check_and_execute_reserve_fund(
                closure_side,
                lambda s=closure_side: self._check_and_execute_auto_balance(
                    s, lambda s2=s: self._start_auto_trade_without_position_check(side=s2)
                )
            )

        except Exception as e:
            print(f"[익절] 최종 확인 오류: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(str, str, str, str)
    def on_request_stop_loss(self, symbol, side, quantity, stop_loss_price, panel_side=None):
        """최종 단계: Stop Loss 주문 요청 처리"""
        print(f"[최종단계] Stop Loss 주문 요청 수신: {side} {quantity} {symbol} @ ${stop_loss_price} (panel_side={panel_side})")

        # side-aware API 및 워커 선택
        api = self.api_modules.get(panel_side) if panel_side else self.api_module
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker

        if not api or not api.is_api_key_active():
            print("[최종단계] API가 연결되지 않아 Stop Loss 주문을 실행할 수 없습니다.")
            return

        try:
            # position_side 결정
            position_side = worker.side_mode if worker else "BOTH"

            # Stop Loss 주문 실행
            result = api.place_stop_loss_order(
                symbol, side, quantity, stop_loss_price, position_side
            )

            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"[최종단계] Stop Loss 주문 ID {order_id}가 접수되었습니다.")
            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"[최종단계] Stop Loss 주문이 API에서 거부됨: {msg}")
            else:
                print(f"[최종단계] Stop Loss 주문 API 요청 실패. {result}")

        except Exception as e:
            print(f"[최종단계] Stop Loss 주문 중 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_request_trailing_stop(self, symbol, side, quantity, activation_price, callback_rate, panel_side=None):
        """최종 단계: Trailing Stop 주문 요청 처리"""
        print(f"[최종단계] Trailing Stop 주문 요청 수신: {side} {quantity} {symbol} @ Activation=${activation_price}, Callback={callback_rate}% (panel_side={panel_side})")

        # side-aware API 및 워커 선택
        api = self.api_modules.get(panel_side) if panel_side else self.api_module
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker

        if not api or not api.is_api_key_active():
            print("[최종단계] API가 연결되지 않아 Trailing Stop 주문을 실행할 수 없습니다.")
            return

        try:
            # position_side 결정 (헷지 포지션은 주 포지션의 반대)
            if worker.side_mode == "LONG":
                position_side = "SHORT"  # 헷지 포지션
            elif worker.side_mode == "SHORT":
                position_side = "LONG"  # 헷지 포지션
            else:
                position_side = "BOTH"

            # Trailing Stop 주문 실행
            result = api.place_trailing_stop_order(
                symbol, side, quantity, activation_price, callback_rate, position_side
            )

            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"[최종단계] Trailing Stop 주문 ID {order_id}가 접수되었습니다.")
            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"[최종단계] Trailing Stop 주문이 API에서 거부됨: {msg}")
            else:
                print(f"[최종단계] Trailing Stop 주문 API 요청 실패. {result}")

        except Exception as e:
            print(f"[최종단계] Trailing Stop 주문 중 오류: {e}")
            import traceback
            traceback.print_exc()

    def on_reduce_hedge_request(self, symbol, side, quantity, panel_side=None):
        """역방향진입 시 헷지 포지션 부분 청산 요청 처리

        Args:
            symbol: 심볼
            side: 청산 방향 (BUY 또는 SELL)
            quantity: 청산 수량
            panel_side: 'long' 또는 'short' 패널
        """
        _el = "하강진입" if panel_side == "short" else "상승진입"
        print(f"[{_el} 헷지청산] 청산 요청 수신: {side} {quantity} {symbol} (panel_side={panel_side})")

        # side-aware API 및 워커 선택
        api = self.api_modules.get(panel_side) if panel_side else self.api_module
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker

        if not api or not api.is_api_key_active():
            print(f"[{_el} 헷지청산] API가 연결되지 않아 헷지 청산을 실행할 수 없습니다.")
            return

        try:
            # position_side 결정 (헷지 포지션은 주 포지션의 반대)
            if worker.side_mode == "LONG":
                position_side = "SHORT"  # 헷지 포지션
            elif worker.side_mode == "SHORT":
                position_side = "LONG"  # 헷지 포지션
            else:
                position_side = "BOTH"

            # reduce_only=True로 헷지 포지션 청산 (시장가)
            result = api.place_market_order(
                symbol, side, quantity,
                reduce_only=True,
                position_side=position_side
            )

            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"[{_el} 헷지청산] 청산 주문 ID {order_id}가 접수되었습니다.")
                worker.log_message.emit("Status: <b style='color: orange;'>Hedge Reduced!</b>")
            elif result and (result.get('code') or result.get('retCode')):
                msg = result.get('msg', result.get('retMsg', 'Unknown API error'))
                print(f"[{_el} 헷지청산] 청산 주문이 API에서 거부됨: {msg}")
            else:
                print(f"[{_el} 헷지청산] 청산 주문 API 요청 실패. {result}")

        except Exception as e:
            print(f"[{_el} 헷지청산] 청산 주문 중 오류: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot()
    def on_save_strategy_settings(self):
        """'Save Strategy Settings' 버튼 클릭 시."""
        try:
            # 1. UI에서 값 읽기 및 유효성 검사
            settings = {
                "STEPS": int(self.settings_steps.text()),
                "TIMEFRAME": str(self.settings_timeframe.text()),
                "ENTRY_START": float(self.settings_entry_start.text()),
                "ENTRY_END": float(self.settings_entry_end.text()),
                "ENTRY_EXPONENT": float(self.settings_entry_exponent.text()),
                "BALANCE_USAGE_PERCENTAGE": float(self.settings_balance_usage.text()),
                "TARGET_LEVERAGE": int(self.settings_target_leverage.text()),
                "HEDGE_START_PERCENT": int(self.settings_hedge_start.text()),
                "HEDGE_END_PERCENT": int(self.settings_hedge_end.text()),
                "HEDGE_EXPONENT": float(self.settings_hedge_exponent.text()),
                "HEDGE_EMERGENCY_START_RATIO": 50.0,  # 고정값 (내부 사용)
                "UPTREND_THRESHOLD_2_MULTIPLIER": float(self.settings_uptrend_threshold_2_multiplier.text()),
                "DCA_INTERVAL_START_PERCENT": int(self.settings_dca_interval_start.text()),
                "DCA_INTERVAL_END_PERCENT": int(self.settings_dca_interval_end.text()),
                "UPTREND_ENTRY_PROFIT_THRESHOLD": float(self.settings_uptrend_entry_profit_threshold.text()),
                "PROFIT_START_PERCENT": float(self.settings_profit_start.text()),
                "PROFIT_END_PERCENT": float(self.settings_profit_end.text()),
                "PROFIT_RATIO": float(self.settings_profit_ratio.text()),
                "STOP_LOSS_RATIO": float(self.settings_stop_loss_ratio.text()),
                "TRAILING_CALLBACK_RATE": float(self.settings_trailing_callback_rate.text()),
                "HEDGE_REDUCTION_STEPS": int(self.settings_hedge_reduction_steps.text()),
                "TEST_QUANTITY_MODE": self.settings_test_quantity_mode.isChecked(),
                "HEDGE_PROTOCOL_ENABLED": True,  # 항상 활성화
                "HEDGE_PROTOCOL_RETRACEMENT": float(self.settings_hedge_protocol_retracement.text()),
                "HEDGE_PROTOCOL_TAKE_PROFIT_RATIO": float(self.settings_hedge_protocol_tp_ratio.text()),
                "MAIN_LIQUIDATION_SAFETY_MARGIN": float(self.settings_main_liquidation_safety_margin.text()),
                "HEDGE_LIQUIDATION_SAFETY_MARGIN": float(self.settings_hedge_liquidation_safety_margin.text()),
                "HEDGE_FRONTLOAD_FINAL_STEP": self.settings_hedge_frontload.isChecked(),
                "RESERVE_FUND_RATIO": float(self.settings_reserve_fund_ratio.text()),
                "RESERVE_FUND_USAGE_LOSS_THRESHOLD": float(self.settings_reserve_fund_loss_threshold.text())
            }
            
            # 2. 전역 설정에 저장
            self.strategy_settings = settings
            self.config_data['strategy_settings'] = settings
            
            # 3. 파일에 저장
            config_manager.save_config_data(self.config_data)
            
            QMessageBox.information(self, "저장 완료", "전략 설정이 `api_config.json`에 저장되었습니다.")
            
        except ValueError as e:
            QMessageBox.warning(self, "입력 오류", f"설정 값에 오류가 있습니다 (숫자만 입력 가능): {e}")
        except Exception as e:
            QMessageBox.critical(self, "저장 실패", f"설정 저장 중 오류 발생: {e}")
    
    def populate_initial_balance(self, balance_info):
        """초기 API 로드 시 잔액 정보를 채웁니다."""
        self.live_balances.clear()
        if not balance_info:
            print(f"({self.current_market_type}) 초기 잔액 정보가 없습니다.")
            return

        for b in balance_info:
            asset = b.get('asset')
            balance = b.get('balance') # 초기 로드 시 'balance' 키 사용
            if asset and balance is not None:
                self.live_balances[asset] = balance

        print(f"{len(self.live_balances)}개 자산 잔액 로드 완료.")
        print(f"[디버그] 로드된 잔액: {list(self.live_balances.keys())}")
        if 'USDT' in self.live_balances:
            print(f"[디버그] USDT 잔액: {self.live_balances['USDT']}")

        # 프로그램 시작 시 cycle_start_balance 초기화 (실시간 PnL 계산용)
        if self.cycle_start_balance == 0.0:
            if self.current_market_type == 'fapi':
                self.cycle_start_balance = float(self.live_balances.get("USDT", "0.0"))
            elif self.current_market_type == 'dapi':
                # DAPI는 심볼에 따라 BTC 또는 ETH 사용
                # 심볼이 설정되지 않았으면 BTC 기본 사용
                if not self.current_symbol or "BTC" in self.current_symbol:
                    self.cycle_start_balance = float(self.live_balances.get("BTC", "0.0"))
                elif "ETH" in self.current_symbol:
                    self.cycle_start_balance = float(self.live_balances.get("ETH", "0.0"))
            print(f"[Cycle 시작] 초기 잔액: {self.cycle_start_balance} (market_type: {self.current_market_type}, symbol: {self.current_symbol})")

        self.update_balance_display() # UI 갱신

    def update_balance_display(self):
        """저장된 self.live_balances를 기반으로 잔액 라벨을 업데이트합니다."""
        if not hasattr(self, 'balance_label') or not self.balance_label:
            print("[디버그] balance_label이 없습니다.")
            return

        asset_to_display = None
        balance_str = "0.0"

        print(f"[디버그] update_balance_display 호출: market_type={self.current_market_type}, 잔액 수={len(self.live_balances)}")

        if self.current_market_type == 'fapi':
            # FAPI (USDⓈ-M)는 USDT를 우선으로 찾음
            if 'USDT' in self.live_balances:
                asset_to_display = 'USDT'
                print(f"[디버그] USDT 선택됨")
            elif 'BUSD' in self.live_balances: # 차선책
                asset_to_display = 'BUSD'
                print(f"[디버그] BUSD 선택됨")
            
        elif self.current_market_type == 'dapi':
            # DAPI (COIN-M)는 현재 심볼 기반으로 찾음
            # 로그에서 'BTCUSD_PERP' 확인
            if self.current_symbol.endswith("USD_PERP"): # 예: BTCUSD_PERP
                asset_name = self.current_symbol.replace("USD_PERP", "") # BTC
                if asset_name in self.live_balances:
                    asset_to_display = asset_name
            
            # 못찾았으면 BTC를 기본으로 시도
            if not asset_to_display and 'BTC' in self.live_balances:
                asset_to_display = 'BTC'

        # 그래도 못찾았으면 마켓 기본 자산(USDT/BTC)을 다시 시도
        if not asset_to_display:
            if self.current_market_type == 'fapi' and 'USDT' in self.live_balances:
                asset_to_display = 'USDT'
            elif self.current_market_type == 'dapi' and 'BTC' in self.live_balances:
                asset_to_display = 'BTC'
        
        if asset_to_display:
            balance_str = self.live_balances.get(asset_to_display, "0.0")
            print(f"[디버그] 표시할 자산: {asset_to_display}, 잔액: {balance_str}")
        else:
            # 표시할 자산이 없음
            print(f"[디버그] 표시할 자산이 없음. N/A 표시")
            self.balance_label.setText("N/A")
            return

        try:
            balance_float = float(balance_str)
            # dapi (BTC, ETH 등)는 8자리, fapi (USDT 등)는 4자리
            if self.current_market_type == 'dapi' and asset_to_display not in ['USDT', 'BUSD']:
                 precision = 8
            else: # fapi (USDT, BUSD)
                 precision = 4

            display_text = f"{balance_float:.{precision}f} {asset_to_display}"
            print(f"[디버그] 잔액 라벨 업데이트: {display_text}")
            self.balance_label.setText(display_text)

            # Cycle & PnL 업데이트 (프로그램 시작 이후 실시간 손익)
            if hasattr(self, 'cycle_start_balance'):
                current_pnl = balance_float - self.cycle_start_balance
                self._update_cycle_pnl_label(self.total_cycles_completed, current_pnl)
                print(f"[디버그] 실시간 PnL 업데이트: 시작={self.cycle_start_balance:.{precision}f}, 현재={balance_float:.{precision}f}, PnL={current_pnl:+.{precision}f}")
        except ValueError:
            print(f"[디버그] ValueError 발생, 원본 표시: {balance_str}")
            self.balance_label.setText(f"{balance_str} {asset_to_display}") # 숫자가 아닐 경우 원본 표시

    def update_realtime_pnl(self):
        """실시간 손익을 계산하여 표시를 업데이트합니다."""
        if not hasattr(self, 'cycle_pnl_label') or not self.cycle_pnl_label:
            return

        # 실시간 손익 계산 (현재 잔액 - 시작 잔액)
        if not hasattr(self, 'cycle_start_balance') or self.cycle_start_balance == 0:
            # 시작 잔액이 없으면 확정 손익만 표시
            self._update_cycle_pnl_label(self.total_cycles_completed, self.cumulative_pnl)
            return

        # 현재 잔액 가져오기
        current_balance = 0.0
        if self.current_market_type == 'fapi':
            current_balance = float(self.live_balances.get("USDT", "0.0"))
        elif self.current_market_type == 'dapi':
            if not self.current_symbol or "BTC" in self.current_symbol:
                current_balance = float(self.live_balances.get("BTC", "0.0"))
            elif "ETH" in self.current_symbol:
                current_balance = float(self.live_balances.get("ETH", "0.0"))

        # 실시간 손익 = 현재 잔액 - 시작 잔액
        current_pnl = current_balance - self.cycle_start_balance
        self._update_cycle_pnl_label(self.total_cycles_completed, current_pnl)

    def update_cycle_pnl_display(self):
        """사이클 수 및 누적 손익 라벨을 업데이트합니다 (사이클 완료 시)."""
        if not hasattr(self, 'cycle_pnl_label') or not self.cycle_pnl_label:
            return

        self._update_cycle_pnl_label(self.total_cycles_completed, self.cumulative_pnl)

    def _update_cycle_pnl_label(self, cycles, pnl):
        """사이클/손익 라벨을 실제로 업데이트하는 내부 함수"""
        try:
            # 손익에 따른 색상 결정
            if pnl > 0:
                color = "#00FF00"  # 초록색 (수익)
                sign = "+"
            elif pnl < 0:
                color = "#FF0000"  # 빨간색 (손실)
                sign = ""
            else:
                color = "#888888"  # 회색 (0)
                sign = "+"

            # 자산 단위 결정 (마켓 타입과 심볼에 따라)
            asset = ""
            precision = 2  # 기본 정밀도 (USDT 기준)

            if self.current_market_type == "dapi":  # Inverse (COIN-M)
                # dapi는 코인 단위로 손익 표시 (BTC, ETH 등)
                if self.current_symbol:
                    if "BTC" in self.current_symbol:
                        asset = "BTC"
                        precision = 8
                    elif "ETH" in self.current_symbol:
                        asset = "ETH"
                        precision = 8
                    else:
                        asset = "COIN"
                        precision = 8
                else:
                    asset = "COIN"
                    precision = 8
            else:  # fapi (Linear, USDT-M)
                # fapi는 USDT 단위로 손익 표시
                asset = "USDT"
                precision = 4  # USDT는 소수점 4자리

            # 라벨 업데이트
            label_text = f"Cycles: {cycles} | PnL: <span style='color: {color};'>{sign}{pnl:.{precision}f} {asset}</span>"
            self.cycle_pnl_label.setText(label_text)
            print(f"[디버그] PnL 라벨 업데이트: {label_text}")
        except Exception as e:
            print(f"[에러] PnL 라벨 업데이트 실패: {e}")
            import traceback
            traceback.print_exc()

    def refresh_balance(self):
        """
        API를 통해 잔액을 갱신합니다.
        체결 메시지 이후 디바운스 타이머에 의해 호출됩니다.
        Bybit WebSocket wallet 토픽은 거래로 인한 잔액 변화를 전송하지 않으므로,
        체결 후 API로 최신 잔액을 조회합니다.
        """
        if not self.api_module or not self.api_module.is_api_key_active():
            return

        try:
            balance_info = self.api_module.get_initial_balance()
            if balance_info:
                # 잔액 업데이트 (WebSocket과 동일한 방식)
                for b in balance_info:
                    asset = b.get('asset')
                    balance = b.get('balance')
                    if asset and balance is not None:
                        # 기존 잔액과 다른 경우에만 로그 출력
                        old_balance = self.live_balances.get(asset)
                        if old_balance != balance:
                            print(f"[잔액 갱신] {asset}: {old_balance} -> {balance}")
                        self.live_balances[asset] = balance

                self.update_balance_display()
                self.update_realtime_pnl()  # 잔액 변경 시 실시간 손익도 업데이트
        except Exception as e:
            # 잔액 갱신 실패 시 로그만 출력하고 계속 진행
            print(f"[경고] 잔액 갱신 중 오류 발생: {e}")

    def request_balance_refresh(self):
        """
        잔액 갱신을 요청합니다 (디바운싱 적용).
        여러 체결 메시지가 연속으로 올 경우, 마지막 메시지 이후 5초 뒤에 한 번만 실행됩니다.
        """
        if self.balance_refresh_timer:
            # 기존 타이머가 있으면 재시작 (디바운싱)
            self.balance_refresh_timer.stop()
            self.balance_refresh_timer.start(3000)  # 3초 후 실행

    def populate_initial_positions(self, positions):
        self.position_table.setRowCount(0); self.live_position_data.clear()
        self.remove_all_position_lines_from_chart()
        if not positions: print(f"({self.current_market_type}) 초기 포지션 정보가 없습니다."); return

        # 자동매매 중이면 메인 포지션을 먼저 표시하도록 정렬
        if self.auto_trade_worker and self.auto_trade_worker.is_running:
            main_side = self.auto_trade_worker.side_mode  # "LONG" or "SHORT"
            # 메인 포지션 먼저, 헷지 포지션 나중에
            positions_sorted = sorted(positions, key=lambda p: (
                0 if (p.get('positionSide') == main_side or
                      (not p.get('positionSide') or p.get('positionSide') == 'BOTH') and
                      ((main_side == 'LONG' and float(p['positionAmt']) > 0) or
                       (main_side == 'SHORT' and float(p['positionAmt']) < 0))) else 1
            ))
        else:
            positions_sorted = positions

        for p in positions_sorted:
            row_count = self.position_table.rowCount(); self.position_table.insertRow(row_count)
            symbol = p['symbol']; amount = float(p['positionAmt']); entry_price = float(p['entryPrice'])
            pnl = float(p['unRealizedProfit']); margin = float(p.get('initialMargin', p.get('isolatedWallet', 0)))

            # ROI 계산: Entry Price 기준 수익률
            # ROI = (PNL / (Entry Price × |Amount|)) × 100
            position_value = abs(entry_price * amount) if entry_price != 0 else 0
            roi = (pnl / position_value) * 100 if position_value != 0 else 0

            pnl_precision = 8 if self.current_market_type == 'dapi' else 4
            position_side = p.get('positionSide');
            if not position_side or position_side == 'BOTH': position_side = 'LONG' if amount > 0 else 'SHORT'
            unique_key = f"{symbol}_{position_side}"
            pnl_item = QTableWidgetItem(f"{pnl:.{pnl_precision}f}"); roi_item = QTableWidgetItem(f"{roi:.2f}%")
            self.position_table.setItem(row_count, 0, QTableWidgetItem(symbol))
            self.position_table.setItem(row_count, 1, QTableWidgetItem(p['positionAmt']))
            self.position_table.setItem(row_count, 2, QTableWidgetItem(p['entryPrice']))
            self.position_table.setItem(row_count, 3, pnl_item); self.position_table.setItem(row_count, 4, roi_item)

            # Cancel 버튼 추가 (중앙 정렬)
            cancel_widget = self.create_centered_cancel_button(lambda checked, key=unique_key: self.close_single_position(key))
            self.position_table.setCellWidget(row_count, 5, cancel_widget)

            self.live_position_data[unique_key] = {
                'row': row_count, 'symbol': symbol, 'amount': amount, 'entry': entry_price, 'margin': margin,
                'positionSide': position_side, 'pnl': pnl, 'pnl_item': pnl_item, 'roi_item': roi_item
            }
            self.draw_position_line_on_chart(entry_price, position_side)

    def populate_initial_orders(self, orders):
        self.order_table.setRowCount(0)
        self.remove_all_order_lines_from_chart()  # 기존 주문 라인 제거

        if not orders: print(f"({self.current_market_type}) 초기 미체결 주문 정보가 없습니다."); return

        for o in orders:
            row_count = self.order_table.rowCount(); self.order_table.insertRow(row_count)
            self.order_table.setItem(row_count, 0, QTableWidgetItem(o['symbol']))
            self.order_table.setItem(row_count, 1, QTableWidgetItem(o['type']))
            self.order_table.setItem(row_count, 2, QTableWidgetItem(o['side']))
            self.order_table.setItem(row_count, 3, QTableWidgetItem(o['price']))
            self.order_table.setItem(row_count, 4, QTableWidgetItem(o['origQty']))
            self.order_table.setItem(row_count, 5, QTableWidgetItem(o['executedQty']))

            # Cancel 버튼 추가 (중앙 정렬)
            order_id = str(o['orderId'])
            symbol = o['symbol']
            order_category = o.get('orderCategory', 'normal')  # algo 또는 normal
            cancel_widget = self.create_centered_cancel_button(lambda checked, oid=order_id, sym=symbol, cat=order_category: self.cancel_single_order(sym, oid, cat))
            self.order_table.setCellWidget(row_count, 6, cancel_widget)

            self.order_table.setItem(row_count, 7, QTableWidgetItem(order_id))

            # 차트에 주문 라인 추가 (현재 심볼만)
            if o['symbol'] == self.current_symbol:
                try:
                    price = float(o['price'])
                    side = o['side']
                    self.draw_order_line_on_chart(price, side, order_id)
                except (ValueError, KeyError) as e:
                    print(f"주문 라인 추가 실패: {e}")

    @pyqtSlot(dict)
    def handle_account_update(self, data):
        balance_updated = False # [추가]

        try:
            # [신규] 잔액 업데이트 처리 (B 키)
            balances = data.get('a', {}).get('B', [])
            for b in balances:
                asset = b.get('a')
                wallet_balance = b.get('wb') # 웹소켓은 'wb' (Wallet Balance)
                if asset and wallet_balance is not None:
                    # 라이브 데이터 갱신
                    self.live_balances[asset] = wallet_balance
                    balance_updated = True

            if balance_updated:
                # 잔액이 변경되었으면 UI 갱신
                self.update_balance_display()

            # [기존] 포지션 업데이트 처리 (P 키)
            positions = data.get('a', {}).get('P', [])

            # 포지션 라인 업데이트 Rate Limiting (0.5초 간격)
            position_changed = False
            position_closed = False  # 포지션 청산 감지 플래그
            position_entry_changed = False  # 포지션 평균가 변경 감지 플래그
            should_update_position_lines = False
            if positions:
                import time as time_module
                current_time = time_module.time()
                if current_time - self.last_position_line_update_time >= self.position_line_update_interval:
                    should_update_position_lines = True
                    self.last_position_line_update_time = current_time

            # Insight 탭 업데이트를 위한 Rate Limiting 체크 (루프 전에 한 번만 체크)
            import time as time_module
            current_time = time_module.time()
            should_update_insight = current_time - self.last_insight_position_update_time >= self.insight_position_update_interval

            for p_update in positions:
                symbol = p_update.get('s')
                position_side = p_update.get('ps', 'BOTH')

                # 빈 문자열 처리: 빈 문자열이면 0으로 변환
                pa_value = p_update.get('pa', '0')
                amount = float(pa_value) if pa_value and pa_value != '' else 0.0

                if position_side == 'BOTH': position_side = 'LONG' if amount > 0 else 'SHORT'
                unique_key = f"{symbol}_{position_side}"

                # 빈 문자열 처리
                ep_value = p_update.get('ep', '0')
                up_value = p_update.get('up', '0')
                im_value = p_update.get('im', p_update.get('iw', '0'))

                entry_price = float(ep_value) if ep_value and ep_value != '' else 0.0
                pnl = float(up_value) if up_value and up_value != '' else 0.0
                margin = float(im_value) if im_value and im_value != '' else 0.0
                pnl_precision = 8 if self.current_market_type == 'dapi' else 4
                found_row = -1
                if unique_key in self.live_position_data: found_row = self.live_position_data[unique_key]['row']
                if amount == 0:
                    if found_row != -1:
                        self.position_table.removeRow(found_row)
                        del self.live_position_data[unique_key]
                        self.reindex_position_rows()
                        position_closed = True  # 포지션 청산 플래그 설정

                        # 포지션 청산 시 헷지 트리거 마커 제거
                        if hasattr(self, 'auto_trade_worker') and self.auto_trade_worker.is_running:
                            if self.auto_trade_worker.symbol == symbol and self.auto_trade_worker.side_mode == position_side:
                                print(f"[헷지 트리거] 포지션 청산 감지. 마커 제거 (symbol={symbol}, side={position_side})")
                                self.remove_all_hedge_trigger_markers()
                else:
                    # ROI 계산: Entry Price 기준 수익률
                    position_value = abs(entry_price * amount) if entry_price != 0 else 0
                    roi = (pnl / position_value) * 100 if position_value != 0 else 0
                    roi_str = f"{roi:.2f}%"; pnl_str = f"{pnl:.{pnl_precision}f}"

                    if found_row != -1:
                        # 기존 포지션 업데이트 (값이 변경된 경우만 setText 호출 - 성능 최적화)
                        pos_data = self.live_position_data[unique_key]

                        # 진입가 변경 감지 (포지션 라인 즉시 업데이트를 위해)
                        old_entry = pos_data.get('entry', 0)
                        if abs(old_entry - entry_price) > 0.0001:  # 진입가가 변경됨
                            position_entry_changed = True

                        if found_row < self.position_table.rowCount():
                            # PnL과 ROI는 WebSocket에서 오는 값이 정확하므로 여기서만 업데이트
                            # (Ticker 업데이트의 계산된 값은 참고용)
                            # 값이 실제로 변경된 경우에만 setText 호출
                            try:
                                # QTableWidgetItem이 삭제되었을 수 있으므로 안전하게 접근
                                pnl_item = pos_data.get('pnl_item')
                                roi_item = pos_data.get('roi_item')

                                if pnl_item is not None:
                                    try:
                                        current_pnl = pnl_item.text()
                                        if current_pnl != pnl_str:
                                            pnl_item.setText(pnl_str)
                                    except RuntimeError:
                                        # C++ 객체가 삭제된 경우, 테이블에서 직접 가져오기
                                        pnl_item = self.position_table.item(found_row, 4)
                                        if pnl_item:
                                            pnl_item.setText(pnl_str)
                                            pos_data['pnl_item'] = pnl_item

                                if roi_item is not None:
                                    try:
                                        current_roi = roi_item.text()
                                        if current_roi != roi_str:
                                            roi_item.setText(roi_str)
                                    except RuntimeError:
                                        # C++ 객체가 삭제된 경우, 테이블에서 직접 가져오기
                                        roi_item = self.position_table.item(found_row, 5)
                                        if roi_item:
                                            roi_item.setText(roi_str)
                                            pos_data['roi_item'] = roi_item
                            except Exception as item_err:
                                print(f"[포지션 업데이트] PnL/ROI 업데이트 오류 (무시): {item_err}")

                            # Amount와 Entry Price - 값 변경 시에만 업데이트
                            pa_str = p_update.get('pa')
                            ep_str = p_update.get('ep')
                            current_pa = self.position_table.item(found_row, 1)
                            current_ep = self.position_table.item(found_row, 2)
                            if current_pa and current_pa.text() != pa_str:
                                current_pa.setText(pa_str)
                            if current_ep and current_ep.text() != ep_str:
                                current_ep.setText(ep_str)
                        pos_data.update({'amount': amount, 'entry': entry_price, 'margin': margin, 'pnl': pnl})
                    else:
                        # 새 포지션 추가 (자동매매 여부와 관계없이)
                        row_count = self.position_table.rowCount(); self.position_table.insertRow(row_count)
                        pnl_item = QTableWidgetItem(pnl_str); roi_item = QTableWidgetItem(roi_str)
                        self.position_table.setItem(row_count, 0, QTableWidgetItem(symbol)); self.position_table.setItem(row_count, 1, QTableWidgetItem(p_update.get('pa')))
                        self.position_table.setItem(row_count, 2, QTableWidgetItem(p_update.get('ep'))); self.position_table.setItem(row_count, 3, pnl_item); self.position_table.setItem(row_count, 4, roi_item)

                        # Cancel 버튼 추가 (중앙 정렬)
                        cancel_widget = self.create_centered_cancel_button(lambda checked, key=unique_key: self.close_single_position(key))
                        self.position_table.setCellWidget(row_count, 5, cancel_widget)

                        self.live_position_data[unique_key] = {
                            'row': row_count, 'symbol': symbol, 'amount': amount, 'entry': entry_price, 'margin': margin, 'positionSide': position_side,
                            'pnl': pnl, 'pnl_item': pnl_item, 'roi_item': roi_item
                        }

                    # Insight 탭 업데이트 (자동매매 실행 중이고 해당 포지션인 경우 추가로 업데이트)
                    for side_key, worker in self.auto_trade_workers.items():
                        if not worker or not worker.is_running:
                            continue
                        if worker.symbol != symbol:
                            continue
                        # Main Position
                        if worker.side_mode == position_side:
                            # 최초 진입 가격 저장 (포지션이 새로 생성되었을 때)
                            if self.initial_main_entry_price_by_side[side_key] is None and abs(amount) > 0:
                                self.initial_main_entry_price_by_side[side_key] = entry_price
                                print(f"[Insight][{side_key}] Main Position 최초 진입 가격 저장: ${self.fmt_price(entry_price)}")

                            # Insight 업데이트
                            if should_update_insight:
                                initial_price = self.initial_main_entry_price_by_side[side_key] if self.initial_main_entry_price_by_side[side_key] else entry_price
                                self.update_insight_main_position(side_key, initial_price, abs(amount), entry_price, pnl)
                        # Hedge Position
                        else:
                            hedge_position_side = "SHORT" if worker.side_mode == "LONG" else "LONG"
                            print(f"[디버그 헷지][{side_key}] position_side={position_side}, hedge_position_side={hedge_position_side}, side_mode={worker.side_mode}")
                            if position_side == hedge_position_side:
                                print(f"[디버그 헷지][{side_key}] 헷지 포지션 감지: amount={amount}, entry={entry_price}, pnl={pnl}")
                                # 최초 진입 가격 저장 (포지션이 새로 생성되었을 때)
                                if self.initial_hedge_entry_price_by_side[side_key] is None and abs(amount) > 0:
                                    self.initial_hedge_entry_price_by_side[side_key] = entry_price
                                    print(f"[Insight][{side_key}] Hedge Position 최초 진입 가격 저장: ${self.fmt_price(entry_price)}")

                                # Insight 업데이트
                                if should_update_insight:
                                    initial_price = self.initial_hedge_entry_price_by_side[side_key] if self.initial_hedge_entry_price_by_side[side_key] else entry_price
                                    print(f"[디버그 헷지][{side_key}] update_insight_hedge_position 호출: initial={initial_price}, qty={abs(amount)}, avg={entry_price}, pnl={pnl}")
                                    self.update_insight_hedge_position(side_key, initial_price, abs(amount), entry_price, pnl)
                            else:
                                print(f"[디버그 헷지][{side_key}] 헷지 포지션 매칭 실패: position_side({position_side}) != hedge_position_side({hedge_position_side})")

            # Rate Limiting 타임스탬프 갱신 (루프 후 한 번만 갱신)
            if should_update_insight and positions:
                self.last_insight_position_update_time = current_time

            # 포지션이 변경되었으면 실시간 손익 업데이트
            if position_changed:
                self.update_realtime_pnl()

        except Exception as e:
            print(f"계정 업데이트 처리 오류: {e}")
        finally:
            # 포지션 라인 다시 그리기 (Rate Limiting: 0.5초 간격, 단 포지션 청산/평균가 변경 시 즉시 업데이트)
            if should_update_position_lines or position_closed or position_entry_changed:
                self.remove_all_position_lines_from_chart()
                for panel_side in ['long', 'short']:
                    for key, pos_data in self.live_position_data_by_side.get(panel_side, {}).items():
                        if pos_data.get('symbol') == self.current_symbol:
                            entry = pos_data.get('entry_price', pos_data.get('entry', 0))
                            pos_side = pos_data.get('side', pos_data.get('positionSide', ''))
                            self.draw_position_line_on_chart(entry, pos_side, panel_side=panel_side)
                # Break Even 라인 그리기 (메인 + 헤지 포지션이 모두 있을 때)
                self.draw_break_even_line()
                if position_closed:
                    print(f"[포지션 청산] 차트 라인 즉시 업데이트 완료")
                elif position_entry_changed:
                    print(f"[포지션 평균가 변경] 차트 라인 즉시 업데이트 완료")

    def reindex_position_rows(self):
        live_data_copy = self.live_position_data.copy(); self.live_position_data.clear()

        # 자동매매 중이면 메인 포지션을 먼저 표시하도록 정렬
        if self.auto_trade_worker and self.auto_trade_worker.is_running:
            main_side = self.auto_trade_worker.side_mode
            # 포지션 데이터를 수집하여 정렬
            position_rows = []
            for row in range(self.position_table.rowCount()):
                symbol = self.position_table.item(row, 0).text()
                amount_str = self.position_table.item(row, 1).text()
                amount = float(amount_str)
                # 키 찾기
                found_key = None
                for key, data in live_data_copy.items():
                    if data['symbol'] == symbol and data['amount'] == amount:
                        found_key = key
                        break
                if found_key:
                    position_side = live_data_copy[found_key].get('side', live_data_copy[found_key].get('positionSide', ''))
                    is_main = (position_side == main_side)
                    position_rows.append((is_main, row, found_key, live_data_copy[found_key]))

            # 메인 포지션 먼저 (is_main=True -> 0, False -> 1)
            position_rows.sort(key=lambda x: (0 if x[0] else 1, x[1]))

            # 테이블 재구성 - 새 QTableWidgetItem 생성 (setRowCount(0) 시 기존 item들이 삭제되므로)
            self.position_table.setRowCount(0)
            for _, old_row, key, data in position_rows:
                new_row = self.position_table.rowCount()
                self.position_table.insertRow(new_row)

                # 새로운 QTableWidgetItem 생성 (기존 값 사용)
                pnl_precision = 8 if self.current_market_type == 'dapi' else 4
                pnl_str = f"{data.get('pnl', 0):.{pnl_precision}f}"
                position_value = abs(data.get('entry', 0) * data.get('amount', 0))
                roi = (data.get('pnl', 0) / position_value) * 100 if position_value != 0 else 0
                roi_str = f"{roi:.2f}%"

                pnl_item = QTableWidgetItem(pnl_str)
                roi_item = QTableWidgetItem(roi_str)

                self.position_table.setItem(new_row, 0, QTableWidgetItem(data['symbol']))
                self.position_table.setItem(new_row, 1, QTableWidgetItem(str(data['amount'])))
                self.position_table.setItem(new_row, 2, QTableWidgetItem(str(data.get('entry_price', data.get('entry', 0)))))
                self.position_table.setItem(new_row, 3, pnl_item)
                self.position_table.setItem(new_row, 4, roi_item)

                # Cancel 버튼 재생성 (중앙 정렬)
                cancel_widget = self.create_centered_cancel_button(lambda checked, k=key: self.close_single_position(k))
                self.position_table.setCellWidget(new_row, 5, cancel_widget)

                # 데이터 업데이트 - 새로 생성된 item 참조 저장
                data['row'] = new_row
                data['pnl_item'] = pnl_item
                data['roi_item'] = roi_item
                self.live_position_data[key] = data
        else:
            # 자동매매가 아닌 경우 기존 로직
            for row in range(self.position_table.rowCount()):
                symbol = self.position_table.item(row, 0).text()
                amount_str = self.position_table.item(row, 1).text()
                amount = float(amount_str)
                found_key = None
                for key, data in live_data_copy.items():
                    if data['symbol'] == symbol and data['amount'] == amount:
                        found_key = key
                        break
                if found_key:
                    data = live_data_copy[found_key]
                    data['row'] = row
                    data['pnl_item'] = self.position_table.item(row, 3)
                    data['roi_item'] = self.position_table.item(row, 4)
                    self.live_position_data[found_key] = data

        print(f"포지션 행 인덱스 재정렬 완료. (활성: {len(self.live_position_data)})")

    @pyqtSlot(list)
    def handle_ticker_update(self, ticker_list):
        try:
            import time as time_module
            current_time = time_module.time()

            for item in ticker_list:
                if self.auto_trade_worker and self.auto_trade_worker.is_running:
                    # 캔들 데이터 추출 Rate Limiting (1초에 1번만) - 성능 최적화
                    candle_data = None
                    should_extract_candle = current_time - getattr(self, '_last_candle_extract_time', 0) >= 1.0

                    if should_extract_candle:
                        if self.candlestick_item and hasattr(self.candlestick_item, 'data'):
                            df = self.candlestick_item.data
                            if not df.empty and len(df) >= 2:
                                # 마지막 2개 봉 추출
                                prev_candle = df.iloc[-2]
                                current_candle = df.iloc[-1]

                                candle_data = {
                                    'prev': {
                                        'timestamp': prev_candle['time'],
                                        'open': prev_candle['open'],
                                        'close': prev_candle['close'],
                                        'high': prev_candle['high'],
                                        'low': prev_candle['low']
                                    },
                                    'current': {
                                        'timestamp': current_candle['time'],
                                        'open': current_candle['open'],
                                        'close': current_candle['close'],
                                        'high': current_candle['high'],
                                        'low': current_candle['low']
                                    }
                                }
                                # 캔들 데이터 캐싱
                                self._cached_candle_data = candle_data
                                self._last_candle_extract_time = current_time
                    else:
                        # 캐시된 캔들 데이터 사용
                        candle_data = getattr(self, '_cached_candle_data', None)

                    # 워커의 process_tick 슬롯을 호출 (현재 포지션 정보 + 캔들 데이터)
                    self.auto_trade_worker.process_tick(item, self.live_position_data, candle_data)

                    # Insight 탭에 현재가 업데이트 (Rate Limiting: 1초 간격)
                    current_price = float(item.get('c', 0))
                    if current_price > 0:
                        if current_time - self.last_insight_update_time >= self.insight_update_min_interval:
                            for s in ['long', 'short']:
                                self.update_insight_current_price(s, current_price)
                            self.last_insight_update_time = current_time

                symbol = item.get('s') 
                if hasattr(self, 'order_symbol_input') and symbol == self.order_symbol_input.text():
                    last_price_str = item.get('c', '0.0'); last_price = float(last_price_str)
                    if self.trade_price_label:
                        self.trade_price_label.setText(last_price_str); base_style = self.default_price_label_style; color_style = ""
                        if last_price > self.last_price_for_color: color_style = "color: #00b050;"
                        elif last_price < self.last_price_for_color: color_style = "color: #c00000;"
                        else: color_style = "color: white;" if self.is_dark_mode else "color: black;"
                        self.trade_price_label.setStyleSheet(base_style + color_style)
                        if last_price != 0: self.last_price_for_color = last_price
                if symbol == self.current_symbol:
                    if self.price_line_item:
                        last_price_str = item.get('c', '0.0'); last_price = float(last_price_str)
                        if last_price > 0:
                            if self.detected_precision is None:
                                if '.' in last_price_str: new_precision = len(last_price_str.split('.')[-1])
                                else: new_precision = 0
                                print(f"[{symbol}] Precision 동적 감지: {new_precision} (Y축/포지션 라인 갱신)")
                                self.y_axis.setPrecision(new_precision); self.detected_precision = new_precision
                                self.remove_all_position_lines_from_chart()
                                for panel_side in ['long', 'short']:
                                    for key, pos_data in self.live_position_data_by_side.get(panel_side, {}).items():
                                        if pos_data.get('symbol') == self.current_symbol:
                                            entry = pos_data.get('entry_price', pos_data.get('entry', 0))
                                            pos_side = pos_data.get('side', pos_data.get('positionSide', ''))
                                            self.draw_position_line_on_chart(entry, pos_side, panel_side=panel_side)
                            self.price_line_item.setPos(last_price)
                            precision = self.detected_precision if self.detected_precision is not None else 2
                            self.price_line_item.label.setText(f"{last_price:.{precision}f}")
                            self.price_line_item.show()
                        # 실시간 캔들 업데이트: Ticker 데이터로 진행 중인 봉의 close/high/low 업데이트
                        # 차트 업데이트 간격(10ms)에 맞춰 실시간 반영
                        should_update_candle = current_time - getattr(self, '_last_ticker_candle_update_time', 0) >= self.chart_update_min_interval
                        if should_update_candle and self.chart_data_df is not None and not self.chart_data_df.empty:
                            try:
                                last_idx = len(self.chart_data_df) - 1
                                self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('close')] = last_price
                                if last_price > self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('high')]:
                                    self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('high')] = last_price
                                if last_price < self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('low')]:
                                    self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('low')] = last_price

                                # 차트 렌더링 트리거 (QTimer 배치 렌더링)
                                if self.chart_visible_button.isChecked():
                                    if not self.pending_chart_update:
                                        self.pending_chart_update = True
                                        if self.chart_update_timer is None:
                                            self.chart_update_timer = QTimer(self)
                                            self.chart_update_timer.setSingleShot(True)
                                            self.chart_update_timer.timeout.connect(self._batch_update_chart)
                                        self.chart_update_timer.start(50)  # 50ms 후 렌더링

                                self._last_ticker_candle_update_time = current_time
                            except Exception as e:
                                pass  # 성능 최적화: 로그 제거

                # Position Table PnL 업데이트 Rate Limiting (1초에 1번만) - 성능 최적화
                # 양쪽 패널 모두 업데이트 (LONG, SHORT)
                should_update_pnl = current_time - getattr(self, '_last_pnl_update_time', 0) >= 1.0
                if should_update_pnl:
                    last_price = float(item.get('c', 0))
                    if last_price > 0:
                        for side_key in ['long', 'short']:
                            side_positions = self.live_position_data_by_side.get(side_key, {})
                            for key, pos_data in side_positions.items():
                                if pos_data['symbol'] != symbol: continue
                                pnl_item = pos_data.get('pnl_item'); roi_item = pos_data.get('roi_item')
                                if not pnl_item or not roi_item: continue
                                pnl = 0.0; roi = 0.0; pnl_precision = 4
                                entry_val = pos_data.get('entry_price', pos_data.get('entry', 0))
                                amount_val = pos_data.get('amount', 0)
                                if entry_val == 0 or amount_val == 0: continue

                                market_type = self.current_market_types.get(side_key, 'fapi')
                                if market_type == 'dapi':
                                    pnl_precision = 8; contract_size = 0
                                    if symbol == "BTCUSD_PERP": contract_size = 100
                                    elif symbol == "ETHUSD_PERP": contract_size = 10
                                    if contract_size > 0 and entry_val > 0:
                                        if amount_val > 0: pnl = (1/entry_val - 1/last_price) * amount_val * contract_size
                                        else: pnl = (1/last_price - 1/entry_val) * abs(amount_val) * contract_size
                                    else: pnl = (last_price - entry_val) * amount_val
                                else:
                                    pnl = (last_price - entry_val) * amount_val; pnl_precision = 4

                                # ROI 계산: Entry Price 기준 수익률
                                position_value = abs(entry_val * amount_val)
                                roi = (pnl / position_value) * 100 if position_value != 0 else 0
                                try:
                                    pnl_item.setText(f"{pnl:.{pnl_precision}f}"); roi_item.setText(f"{roi:.2f}%")
                                    color = QColor("white") if self.is_dark_mode else QColor("black")
                                    if pnl > 0: color = QColor(0, 180, 0)
                                    elif pnl < 0: color = QColor(200, 0, 0)
                                    pnl_item.setForeground(color); roi_item.setForeground(color)
                                except RuntimeError:
                                    pass  # QTableWidgetItem 삭제됨
                    self._last_pnl_update_time = current_time
        except Exception as e: print(f"티커 업데이트 처리 오류: {e}")

    @pyqtSlot(dict)
    def handle_kline_update(self, kline_data):
        """Bybit WebSocket에서 실시간 캔들 데이터 수신 및 차트 업데이트"""
        try:
            # 심볼 확인
            if kline_data['symbol'] != self.current_symbol:
                logger.debug(f"캔들 WebSocket 심볼 불일치: {kline_data['symbol']} != {self.current_symbol}")
                return

            # 인터벌 확인 (다른 타임프레임 데이터 무시)
            kline_interval = kline_data.get('interval')
            expected_interval = self._convert_interval_to_bybit(self.current_interval)
            if kline_interval and str(kline_interval) != str(expected_interval):
                return

            # DataFrame이 없으면 초기화 (처음 연결 시)
            if self.chart_data_df is None or self.chart_data_df.empty:
                return  # 초기 API 로드를 기다림

            # 캔들 시작 시간 (초 단위로 변환)
            kline_start_time_sec = kline_data['start'] / 1000.0

            # 기존 캔들인지 확인 (마지막 인덱스로 최적화)
            if not self.chart_data_df.empty and self.chart_data_df['time'].iloc[-1] == kline_start_time_sec:
                # 기존 캔들 업데이트 (진행 중인 봉) - 마지막 봉만 업데이트
                last_idx = len(self.chart_data_df) - 1
                self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('high')] = kline_data['high']
                self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('low')] = kline_data['low']
                self.chart_data_df.iloc[last_idx, self.chart_data_df.columns.get_loc('close')] = kline_data['close']
                # open은 변경하지 않음

                # Rate limiting: 차트 업데이트 (QTimer 기반 배치 렌더링)
                # 차트가 숨겨져 있으면 렌더링 스킵 (성능 최적화)
                if self.chart_visible_button.isChecked():
                    if not self.pending_chart_update:
                        self.pending_chart_update = True
                        # QTimer를 사용한 지연 렌더링 (이벤트 루프에서 일괄 처리)
                        if self.chart_update_timer is None:
                            self.chart_update_timer = QTimer(self)
                            self.chart_update_timer.setSingleShot(True)
                            self.chart_update_timer.timeout.connect(self._batch_update_chart)
                        # 0.05초 후에 렌더링 (1초에 20번 업데이트)
                        self.chart_update_timer.start(50)

            else:
                # 새로운 캔들 (DataFrame에 없음)
                # confirm=False여도 진행 중인 새 봉으로 추가 (실시간 업데이트 위해)
                logger.info(f"캔들 WebSocket 새 봉 추가: {kline_data['symbol']} @ {kline_start_time_sec:.0f}")

                # DataFrame에 추가
                new_row_df = pd.DataFrame([{
                    'time': kline_start_time_sec,
                    'open': kline_data['open'],
                    'high': kline_data['high'],
                    'low': kline_data['low'],
                    'close': kline_data['close']
                }])

                self.chart_data_df = pd.concat([
                    self.chart_data_df,
                    new_row_df
                ], ignore_index=True)

                # 오래된 데이터 제거 (최근 500개만 유지 - 성능 최적화)
                if len(self.chart_data_df) > 500:
                    self.chart_data_df = self.chart_data_df.iloc[-500:]
                    self.chart_data_df.reset_index(drop=True, inplace=True)

                # 차트 업데이트 (차트가 표시 중일 때만 - 새 봉은 즉시 렌더링)
                if self.chart_visible_button.isChecked():
                    # 새 봉이 추가되면 기존 타이머 취소하고 즉시 렌더링
                    if self.chart_update_timer and self.chart_update_timer.isActive():
                        self.chart_update_timer.stop()
                    self.candlestick_item.setData(self.chart_data_df, update_only_last=False)  # 새 봉 추가 시 전체 렌더링

                    # Lock Mode: 최신 봉으로 스크롤
                    if self.chart_lock_mode:
                        self._lock_to_latest_candles()

                    self.pending_chart_update = False

        except Exception as e:
            logger.error(f"캔들 WebSocket 오류: {e}", exc_info=True)

    def _batch_update_chart(self, update_only_last=True):
        """배치 차트 업데이트 (QTimer 콜백) - 성능 최적화"""
        try:
            if self.chart_visible_button.isChecked() and self.chart_data_df is not None:
                # 진행 중인 봉만 업데이트 (성능 최적화)
                self.candlestick_item.setData(self.chart_data_df, update_only_last=update_only_last)

                # Lock Mode: 배치 업데이트는 현재 봉 갱신만 하므로 스크롤 불필요
                # (새 봉 추가 시에만 _lock_to_latest_candles() 호출)

            self.pending_chart_update = False
        except Exception as e:
            logger.error(f"배치 차트 업데이트 오류: {e}", exc_info=True)
            self.pending_chart_update = False

    @pyqtSlot(dict)
    def handle_order_update(self, data):
        try:
            # 자동매매 워커에게 주문 업데이트 전달
            if hasattr(self, 'auto_trade_worker') and self.auto_trade_worker:
                self.auto_trade_worker.on_order_update(data)

            o = data.get('o', {}); order_id = str(o.get('i')); status = o.get('X')
            if order_id in self.pending_market_orders:
                if status == 'FILLED':
                    QMessageBox.information(self, "Order Success (FILLED)", f"Order Filled (Status: {status}):\n{o.get('S')} {o.get('q')} {o.get('s')}\nAvg. Price: {o.get('ap', 'N/A')}")
                    self.pending_market_orders.remove(order_id)
                elif status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                    QMessageBox.warning(self, "Order Failed (WebSocket)", f"Order {order_id} failed or was canceled.\nStatus: {status}\nReason: {o.get('r', 'N/A')}")
                    self.pending_market_orders.remove(order_id)
            found_row = -1
            for row in range(self.order_table.rowCount()):
                if self.order_table.item(row, 7) and self.order_table.item(row, 7).text() == order_id: found_row = row; break

            # 주문 종료 시 테이블과 차트 라인 제거
            if status in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']:
                if found_row != -1: self.order_table.removeRow(found_row)
                self.remove_order_line_from_chart(order_id)  # 차트 라인 제거

                # 체결 시 잔액 갱신 요청 (디바운싱 적용)
                if status == 'FILLED':
                    self.request_balance_refresh()

            # 새 주문 시 테이블과 차트 라인 추가
            elif status == 'NEW':
                if found_row == -1:
                    row_count = self.order_table.rowCount(); self.order_table.insertRow(row_count)
                    self.order_table.setItem(row_count, 0, QTableWidgetItem(o['s'])); self.order_table.setItem(row_count, 1, QTableWidgetItem(o['o']))
                    self.order_table.setItem(row_count, 2, QTableWidgetItem(o['S'])); self.order_table.setItem(row_count, 3, QTableWidgetItem(o['p']))
                    self.order_table.setItem(row_count, 4, QTableWidgetItem(o['q'])); self.order_table.setItem(row_count, 5, QTableWidgetItem(o['z']))

                    # Cancel 버튼 추가 (중앙 정렬)
                    symbol = o['s']
                    cancel_widget = self.create_centered_cancel_button(lambda checked, oid=order_id, sym=symbol: self.cancel_single_order(sym, oid))
                    self.order_table.setCellWidget(row_count, 6, cancel_widget)

                    self.order_table.setItem(row_count, 7, QTableWidgetItem(order_id))

                    # 차트에 주문 라인 추가 (현재 심볼만)
                    if o['s'] == self.current_symbol:
                        try:
                            price = float(o['p'])
                            side = o['S']
                            self.draw_order_line_on_chart(price, side, order_id)
                        except (ValueError, KeyError) as e:
                            print(f"주문 라인 추가 실패: {e}")

            elif status == 'PARTIALLY_FILLED':
                if found_row != -1: self.order_table.item(found_row, 5).setText(o['z'])
                # 부분 체결도 잔액 변화가 발생하므로 갱신 요청
                self.request_balance_refresh()
        except Exception as e: print(f"주문 업데이트 처리 오류: {e}")

    def update_chart(self, symbol, interval, klines_data=None, is_refresh=False):
        if not is_refresh:
            print(f"pyqtgraph 차트 로드 시도: {symbol} {interval}")

        if not self.api_module or not self.api_module.is_api_key_active():
            print("API가 연결되지 않아 차트를 로드할 수 없습니다.")
            return

        klines = klines_data
        if klines is None:
            klines = self.api_module.get_ohlcv_data(symbol, interval, 500)  # 500개로 제한 (성능 최적화)
        
        if not klines:
            logger.error(f"{symbol} {interval} 캔들 데이터 가져오기 실패")
            self.candlestick_item.setData(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
            return

        df = pd.DataFrame(klines, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])

        # 성능 최적화: copy=False로 메모리 절약
        df = df[['time', 'open', 'high', 'low', 'close']].astype(float, copy=False)
        df['time'] = df['time'] / 1000

        # 디버깅: 최근 3개 봉의 시간 출력
        if len(df) >= 3 and not is_refresh:
            import datetime
            print(f"\n[차트 디버깅] {symbol} {interval} - GUI에서 받은 최근 3개 캔들:")
            for i in range(-3, 0):
                ts = df['time'].iloc[i]
                dt_utc = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
                dt_local = datetime.datetime.fromtimestamp(ts)
                print(f"  [{i}] Time: {ts:.0f} -> UTC: {dt_utc.strftime('%Y-%m-%d %H:%M:%S')} | Local: {dt_local.strftime('%Y-%m-%d %H:%M:%S')}")

        # 중복 데이터 감지 (is_refresh일 때만 체크)
        if is_refresh:
            import hashlib
            # 마지막 10개 봉의 데이터로 해시 생성 (전체 데이터는 너무 크므로)
            last_candles = df.tail(10).to_json()
            current_hash = hashlib.md5(last_candles.encode()).hexdigest()

            if current_hash == self.last_chart_data_hash:
                # 중복 데이터 감지 - 재시도 로직
                if self.chart_retry_count < 10:  # 최대 10회 재시도
                    self.chart_retry_count += 1
                    print(f"[차트 업데이트] 중복 데이터 감지 - 1초 후 재시도 ({self.chart_retry_count}/10)")
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(1000, self.refresh_chart_data)
                    return
                else:
                    # 최대 재시도 횟수 초과 - 재시도 카운터 리셋
                    print(f"[차트 업데이트] 최대 재시도 횟수 초과 - 다음 정규 업데이트 대기")
                    self.chart_retry_count = 0
                    return
            else:
                # 새로운 데이터 수신 - 해시 업데이트 및 재시도 카운터 리셋
                self.last_chart_data_hash = current_hash
                self.chart_retry_count = 0

        # 새로운 봉 추가 감지 (Lock Mode용) - 마지막 봉의 시간으로 판단
        current_last_candle_time = df['time'].iloc[-1] if len(df) > 0 else 0
        new_candle_added = (current_last_candle_time > self.last_candle_time)

        if is_refresh:
            # 새 봉 추가 여부 확인 (로그 출력 제거 - 5분마다 반복되는 정보)

            # 새 봉 추가 여부에 따라 재시도 카운터 관리
            if new_candle_added:
                # 새 봉이 추가되었으면 재시도 카운터 리셋
                self.chart_retry_count = 0
            else:
                # 새 봉이 없어도 현재 봉의 OHLC 업데이트를 위해 차트는 계속 갱신
                # 하지만 재시도 횟수는 증가시켜서 너무 많은 재시도 방지
                if self.chart_retry_count < 10:
                    self.chart_retry_count += 1
                    print(f"[차트 업데이트] 새 봉 미감지 - 현재 봉 업데이트 중 ({self.chart_retry_count}/10)")
                else:
                    # 최대 재시도 횟수 초과 - 재시도 카운터 리셋하고 계속 진행
                    print(f"[차트 업데이트] 최대 재시도 횟수 도달 - 재시도 카운터 리셋")
                    self.chart_retry_count = 0

        self.last_candle_time = current_last_candle_time

        # WebSocket 실시간 업데이트를 위해 DataFrame 저장 (성능 최적화: copy 제거)
        # 메모리 누수 방지: 최대 캔들 수 제한
        if len(df) > self.MAX_CANDLES:
            df = df.tail(self.MAX_CANDLES).reset_index(drop=True)
            print(f"[차트 데이터 정리] 최대 캔들 수 초과 - {len(df)}개로 제한")

        self.chart_data_df = df

        self.candlestick_item.setData(df, update_only_last=False)  # 초기 로드는 전체 렌더링

        # 차트 뷰 범위 조정
        if self.chart_lock_mode:
            # Lock Mode: 새로운 봉이 추가되었을 때만 최신 봉으로 스크롤
            # 또는 복원이 필요한 첫 업데이트인 경우 강제 실행
            if new_candle_added or self.lock_mode_needs_first_restore:
                self._lock_to_latest_candles()
                self.lock_mode_needs_first_restore = False  # 첫 복원 완료
        elif not self.chart_user_interacted:
            # 자동 범위 조정
            self.chart_viewbox.autoRange()

        if not is_refresh:
            print("심볼/타임프레임/계정 변경 감지. 라인을 새로고침합니다.")
            self.price_line_item.hide()

            # 포지션 라인 새로고침 (양쪽 패널 모두)
            self.remove_all_position_lines_from_chart()
            for panel_side in ['long', 'short']:
                for key, pos_data in self.live_position_data_by_side.get(panel_side, {}).items():
                    if pos_data.get('symbol') == symbol:
                        entry = pos_data.get('entry_price', pos_data.get('entry', 0))
                        pos_side = pos_data.get('side', pos_data.get('positionSide', ''))
                        self.draw_position_line_on_chart(entry, pos_side, panel_side=panel_side)

            # 미체결 주문 라인 새로고침 (양쪽 패널 모두)
            self.remove_all_order_lines_from_chart()
            for panel_side in ['long', 'short']:
                order_table = self.order_tables.get(panel_side)
                if not order_table:
                    continue
                for row in range(order_table.rowCount()):
                    try:
                        order_symbol = order_table.item(row, 0).text()
                        if order_symbol == symbol:
                            price = float(order_table.item(row, 3).text())
                            side = order_table.item(row, 2).text()
                            order_id = order_table.item(row, 7).text()  # 열 7 = OrderId
                            self.draw_order_line_on_chart(price, side, order_id, panel_side=panel_side)
                    except (ValueError, AttributeError) as e:
                        print(f"[{panel_side.upper()}] 주문 라인 새로고침 중 오류: {e}")

            # print(f"pyqtgraph 차트 업데이트 완료: {symbol} {interval}")  # 봉마감마다 출력 제거


    def on_symbol_changed(self, new_symbol):
        """Symbol 드롭다운 변경 시 호출"""
        if self.current_symbol == new_symbol:
            return

        old_symbol = self.current_symbol
        self.current_symbol = new_symbol

        print(f"Symbol 변경: {old_symbol} → {new_symbol}")

        # 계정별 마지막 심볼 저장
        if "account_last_symbols" not in self.config_data:
            self.config_data["account_last_symbols"] = {}

        # 현재 연결된 계정이 있으면 계정별로 저장
        if self.current_account_name:
            self.config_data["account_last_symbols"][self.current_account_name] = self.current_symbol
            print(f"[심볼 저장] {self.current_account_name} 계정의 심볼 저장: {self.current_symbol}")

        # 전역 마지막 심볼도 저장 (하위 호환성)
        if "app_settings" not in self.config_data:
            self.config_data["app_settings"] = {}
        self.config_data["app_settings"]["last_symbol"] = self.current_symbol
        config_manager.save_config_data(self.config_data)

        # Order Symbol 입력 필드도 업데이트
        if hasattr(self, 'order_symbol_input'):
            self.order_symbol_input.setText(self.current_symbol)

        # 심볼 변경 시 차트 뷰 리셋 (새로운 차트는 전체 범위를 보여줌)
        if not self.chart_lock_mode:  # Lock Mode가 아닐 때만 리셋
            self.chart_user_interacted = False
        self.last_candle_time = 0  # 새 심볼이므로 마지막 봉 시간 리셋

        # 차트 업데이트
        if self.api_module and self.api_module.is_api_key_active():
            self.update_chart(self.current_symbol, self.current_interval)
        else:
            print("API가 연결되지 않았습니다. 연결 후 차트가 업데이트됩니다.")

        # 티커 스레드 재시작 (가격 실시간 업데이트)
        if self.ticker_thread and hasattr(self, 'connect_thread'):
            print(f"티커 스레드 재시작 중: {old_symbol} → {new_symbol}")

            # 기존 티커 스레드 종료
            if self.ticker_thread.isRunning():
                self.ticker_thread.stop()
                self.ticker_thread.wait()
                print("기존 티커 스레드 종료 완료")

            # 새로운 티커 스레드 생성
            exchange = self.connect_thread.exchange
            if exchange == "Binance":
                new_ticker_thread = TickerSocketThread(self.current_market_type, new_symbol)
            elif exchange == "Bybit":
                new_ticker_thread = BybitTickerSocketThread(self.current_market_type, new_symbol)
            else:
                print(f"지원되지 않는 거래소: {exchange}")
                return

            # 시그널 연결 및 시작
            new_ticker_thread.ticker_update.connect(self.handle_ticker_update)
            new_ticker_thread.start()

            # 참조 업데이트
            self.ticker_thread = new_ticker_thread
            print(f"새 티커 스레드 시작 완료: {new_symbol}")

    def change_timeframe(self, timeframe_value):
        if self.current_interval == timeframe_value: return
        old_tf = self.current_interval; self.current_interval = timeframe_value
        self.update_timeframe_buttons(self.current_interval, old_tf)
        if "app_settings" not in self.config_data: self.config_data["app_settings"] = {}
        self.config_data["app_settings"]["last_timeframe"] = self.current_interval
        config_manager.save_config_data(self.config_data)

        # 타임프레임 변경 시 차트 갱신 타이머 재정렬 (SingleShot 방식으로 자동 재예약)
        self._start_chart_timer_aligned()
        print(f"차트 갱신 타이머 재정렬: {self.current_interval} (타임프레임 00초 맞춤)")

        # 타임프레임 변경 시 Kline WS 재연결 (새 타임프레임에 맞게)
        self._reconnect_kline_threads_for_new_interval()

        # 타임프레임 변경 시 차트 뷰 리셋 (새로운 차트는 전체 범위를 보여줌)
        if not self.chart_lock_mode:  # Lock Mode가 아닐 때만 리셋
            self.chart_user_interacted = False
        self.last_candle_time = 0  # 새 타임프레임이므로 마지막 봉 시간 리셋

        self.update_chart(self.current_symbol, self.current_interval)
        
    def _reconnect_kline_threads_for_new_interval(self):
        """타임프레임 변경 시 모든 Kline WS 스레드를 새 간격으로 재연결"""
        bybit_interval = self._convert_interval_to_bybit(self.current_interval)
        for side in ['long', 'short']:
            old_kline = self.kline_threads.get(side)
            if not old_kline:
                continue
            connect_thread = self.connect_threads.get(side)
            if not connect_thread or connect_thread.exchange != "Bybit":
                continue

            # 기존 Kline 스레드 종료
            if old_kline.isRunning():
                old_kline.stop()
                old_kline.wait()

            # 새로운 Kline 스레드 생성
            market_type = self.current_market_types.get(side, 'linear')
            symbol = self.current_symbols.get(side, self.current_symbol)
            from v7_dual_ticker_ws import BybitKlineSocketThread
            new_kline = BybitKlineSocketThread(
                market_type=market_type,
                symbol=symbol,
                interval=bybit_interval,
                parent=self
            )
            new_kline.kline_update.connect(lambda kline_data, s=side: self.handle_kline_update_for_side(s, kline_data))
            new_kline.start()
            self.kline_threads[side] = new_kline
            print(f"[{side.upper()}] Kline WS 재연결: {symbol}/{bybit_interval}")

            if side == 'long':
                self.kline_thread = new_kline

    def update_timeframe_buttons(self, new_tf, old_tf):
        if old_tf and old_tf in self.buttons: self.buttons[old_tf].setStyleSheet("")
        if new_tf and new_tf in self.buttons: self.buttons[new_tf].setStyleSheet("background-color: #007bff; color: white;")
        
    def toggle_dark_mode(self, checked):
        self.is_dark_mode = checked
        self.apply_theme()

    def apply_theme(self):
        app = QApplication.instance()
        if self.is_dark_mode:
            self.dark_mode_button.setText("☀️ Light Mode")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53)); dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(35, 35, 35)); dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white); dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white); dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white); dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218)); dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black); dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
            dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
            app.setPalette(dark_palette)
            if self.chart_widget:
                self.chart_widget.setBackground(QColor(35, 35, 35)); self.y_axis.setPen('w'); self.chart_widget.getAxis('bottom').setPen('w')
        else:
            self.dark_mode_button.setText("🌙 Dark Mode"); app.setPalette(self.original_palette) 
            if self.chart_widget:
                self.chart_widget.setBackground('w'); self.y_axis.setPen('k'); self.chart_widget.getAxis('bottom').setPen('k')
        if hasattr(self, 'open_button'): self.update_order_panel_mode()
        self.update_clear_button_style()

            
    def draw_position_line_on_chart(self, price, side, panel_side='long'):
        """포지션 라인을 차트에 추가 (panel_side별 독립 추적)"""
        if not hasattr(self, 'chart_widget') or price == 0: return

        # panel_side별 tracking dict 사용 (다른 패널의 라인과 충돌 방지)
        tracking_dict = self.position_lines_by_side.get(panel_side, self.position_lines)

        # 고유 키: price_side (LONG과 SHORT를 구분)
        line_key = f"{price}_{side}"
        if line_key in tracking_dict: return

        color = '#00b050' if side == "LONG" else '#c00000'
        pen = pg.mkPen(color, style=Qt.DotLine, width=2)
        precision = self.y_axis.precision

        label_text = f"{side} @ {price:.{precision}f}"

        # panel_side 기준으로 라벨 배치 (LONG패널=왼쪽, SHORT패널=오른쪽)
        is_left = (panel_side == 'long')
        label_position = 0.06 if is_left else 0.94
        label_anchor = (0, 0.5) if is_left else (1, 0.5)

        position_line = pg.InfiniteLine(
            pos=price, angle=0, movable=False, pen=pen, label=label_text,
            labelOpts={
                'position': label_position,
                'color': color,
                'movable': True,
                'fill': (0, 0, 0, 150),
                'anchor': label_anchor
            }
        )

        self.chart_widget.addItem(position_line, ignoreBounds=True)
        tracking_dict[line_key] = position_line
        print(f"차트 라인 추가: {side} @ {price} (key={line_key}, panel={panel_side})")

    def remove_position_line_from_chart(self, price, side, panel_side='long'):
        """포지션 라인을 차트에서 제거 (panel_side별 독립 추적)"""
        if not hasattr(self, 'chart_widget'):
            return

        tracking_dict = self.position_lines_by_side.get(panel_side, self.position_lines)

        line_key = f"{price}_{side}"
        if line_key in tracking_dict:
            line = tracking_dict[line_key]
            self.chart_widget.removeItem(line)
            del tracking_dict[line_key]
            print(f"차트 라인 제거: {side} @ {price} (key={line_key}, panel={panel_side})")

    def draw_order_line_on_chart(self, price, side, order_id, panel_side=None):
        """미체결 주문 라인을 차트에 추가"""
        if not hasattr(self, 'chart_widget') or price == 0: return
        if order_id in self.order_lines: return  # 이미 있으면 스킵

        # 주문 라인 색상 (점선, 더 연한 색)
        # BUY: 연한 녹색, SELL: 연한 분홍색
        color = '#90EE90' if side == "Buy" else '#FFB6C6'  # 연한 초록/연한 분홍
        pen = pg.mkPen(color, style=Qt.DashLine, width=1)
        precision = self.y_axis.precision

        # Step 정보가 있으면 라벨에 포함
        if order_id in self.order_step_map:
            step = self.order_step_map[order_id]
            label_text = f"Step {step + 1} ORDER {side} @ {price:.{precision}f}"
        else:
            label_text = f"ORDER {side} @ {price:.{precision}f}"

        # 메인/헷지 주문 위치 결정 (패널별 방향 반영)
        if panel_side:
            side_mode = self.side_modes.get(panel_side, 'LONG')
            is_main = (side_mode == 'LONG' and side == 'Buy') or (side_mode == 'SHORT' and side == 'Sell')
            if panel_side == 'long':
                # LONG 패널: 메인=왼쪽(0.2, [L] H트리거 옆), 헷지=오른쪽(0.8)
                label_pos = 0.2 if is_main else 0.8
                label_anchor = (0, 0.5) if is_main else (1, 0.5)
            else:
                # SHORT 패널: 메인=오른쪽(0.8, [S] H트리거 옆), 헷지=왼쪽(0.2)
                label_pos = 0.8 if is_main else 0.2
                label_anchor = (1, 0.5) if is_main else (0, 0.5)
        else:
            label_pos = 0.9
            label_anchor = (1, 0.5)

        order_line = pg.InfiniteLine(
            pos=price, angle=0, movable=False, pen=pen, label=label_text,
            labelOpts={'position': label_pos, 'color': color, 'movable': True, 'fill': (0, 0, 0, 100), 'anchor': label_anchor}
        )
        self.chart_widget.addItem(order_line, ignoreBounds=True)
        self.order_lines[order_id] = order_line

        if order_id in self.order_step_map:
            step = self.order_step_map[order_id]
            print(f"차트 주문 라인 추가: Step {step + 1} {side} @ {price} (OrderID: {order_id})")
        else:
            print(f"차트 주문 라인 추가: {side} @ {price} (OrderID: {order_id})")

    def remove_order_line_from_chart(self, order_id):
        """특정 주문 라인 제거"""
        if not hasattr(self, 'chart_widget'): return
        if order_id in self.order_lines:
            try:
                self.chart_widget.removeItem(self.order_lines[order_id])
                del self.order_lines[order_id]
                # Step 매핑도 제거
                if order_id in self.order_step_map:
                    del self.order_step_map[order_id]
                print(f"차트 주문 라인 제거: OrderID {order_id}")
            except Exception as e:
                print(f"주문 라인 제거 중 오류: {e}")

    def gray_out_order_line_on_chart(self, order_id):
        """차트 주문 라인을 회색으로 변경 (체결/취소 시)"""
        if not hasattr(self, 'chart_widget'): return
        if order_id not in self.order_lines: return

        try:
            old_line = self.order_lines[order_id]
            price = old_line.value()

            # 기존 라인 제거
            self.chart_widget.removeItem(old_line)

            # 회색 스타일로 새 라인 생성
            gray_color = '#808080'  # 회색
            pen = pg.mkPen(gray_color, style=Qt.DashLine, width=1)
            precision = self.y_axis.precision

            # Step 정보가 있으면 라벨에 포함 (FILLED 표시 추가)
            if order_id in self.order_step_map:
                step = self.order_step_map[order_id]
                label_text = f"Step {step + 1} FILLED @ {price:.{precision}f}"
            else:
                label_text = f"FILLED @ {price:.{precision}f}"

            gray_line = pg.InfiniteLine(
                pos=price, angle=0, movable=False, pen=pen, label=label_text,
                labelOpts={'position': 0.9, 'color': gray_color, 'movable': True, 'fill': (0, 0, 0, 100), 'anchor': (1, 0.5)}
            )
            self.chart_widget.addItem(gray_line, ignoreBounds=True)
            self.order_lines[order_id] = gray_line

            print(f"차트 주문 라인 회색 처리: OrderID {order_id} @ {price:.{precision}f}")

        except Exception as e:
            print(f"주문 라인 회색 처리 중 오류: {e}")

    def remove_all_order_lines_from_chart(self):
        """모든 주문 라인 제거"""
        if not hasattr(self, 'chart_widget'): return
        for order_id, line_item in list(self.order_lines.items()):
            try:
                self.chart_widget.removeItem(line_item)
            except Exception as e:
                print(f"주문 라인 제거 중 오류 (무시됨): {e}")
        self.order_lines.clear()
        self.order_step_map.clear()  # Step 매핑도 모두 제거

    def remove_position_line_by_side(self, position_side):
        """개별 포지션 라인을 차트에서 제거 (포지션 side 기준, 양쪽 패널 모두 검색)"""
        if not hasattr(self, 'chart_widget'): return

        for panel_side in ['long', 'short']:
            tracking_dict = self.position_lines_by_side.get(panel_side, {})
            keys_to_remove = [key for key in tracking_dict.keys() if key.endswith(f"_{position_side}")]

            for key in keys_to_remove:
                line_item = tracking_dict.get(key)
                if line_item:
                    try:
                        self.chart_widget.removeItem(line_item)
                        del tracking_dict[key]
                        print(f"차트 라인 제거: {key} (panel={panel_side})")
                    except Exception as e:
                        print(f"차트 라인 제거 중 오류 (무시됨): {e}")

    def remove_all_position_lines_from_chart(self):
        if not hasattr(self, 'chart_widget'): return
        # 양쪽 패널의 position_lines를 모두 정리
        for panel_side in ['long', 'short']:
            tracking_dict = self.position_lines_by_side.get(panel_side, {})
            for key, line_item in tracking_dict.items():
                try:
                    self.chart_widget.removeItem(line_item)
                except Exception as e:
                    print(f"차트 라인 제거 중 오류 (무시됨): {e}")
            tracking_dict.clear()
        self.remove_break_even_line()  # Break Even 라인도 함께 제거 (레거시)
        self.remove_break_even_line('long')
        self.remove_break_even_line('short')

    def calculate_break_even_price(self, side=None):
        """메인 포지션과 헤지 포지션의 손익분기점 계산 (side별)"""
        if side is not None:
            # dual-panel: side별 worker와 데이터 사용
            worker = self.auto_trade_workers.get(side)
            if not worker or not worker.is_running:
                return None
            symbol = worker.symbol
            side_mode = worker.side_mode
            pos_data = self.live_position_data_by_side.get(side, {})
        else:
            # 레거시
            if not (hasattr(self, 'auto_trade_worker') and self.auto_trade_worker.is_running):
                return None
            symbol = self.auto_trade_worker.symbol
            side_mode = self.auto_trade_worker.side_mode
            pos_data = self.live_position_data

        main_position_side = side_mode
        hedge_position_side = "SHORT" if side_mode == "LONG" else "LONG"

        main_position_key = f"{symbol}_{main_position_side}"
        hedge_position_key = f"{symbol}_{hedge_position_side}"

        if main_position_key not in pos_data or hedge_position_key not in pos_data:
            return None

        main_pos = pos_data[main_position_key]
        hedge_pos = pos_data[hedge_position_key]

        main_qty = abs(float(main_pos.get('amount', 0)))
        main_entry = float(main_pos.get('entry_price', main_pos.get('entry', 0)))
        hedge_qty = abs(float(hedge_pos.get('amount', 0)))
        hedge_entry = float(hedge_pos.get('entry_price', hedge_pos.get('entry', 0)))

        if main_qty == 0 or hedge_qty == 0:
            return None

        if side_mode == "LONG":
            numerator = main_qty * main_entry - hedge_qty * hedge_entry
            denominator = main_qty - hedge_qty
        else:
            numerator = hedge_qty * hedge_entry - main_qty * main_entry
            denominator = hedge_qty - main_qty

        if abs(denominator) < 0.0001:
            return None

        break_even_price = numerator / denominator

        if break_even_price <= 0:
            return None

        return break_even_price

    def draw_break_even_line(self, side=None):
        """손익분기점 라인을 차트에 표시 (side별)"""
        if not hasattr(self, 'chart_widget'):
            return

        # 기존 라인 제거
        self.remove_break_even_line(side)

        # 손익분기점 계산
        break_even_price = self.calculate_break_even_price(side)

        if break_even_price is None:
            return

        precision = self.y_axis.precision if hasattr(self, 'y_axis') and self.y_axis else 2

        if side is not None:
            # dual-panel: side별 색상 구분
            if side == 'long':
                color = '#FFA500'  # 주황색
                label_position = 0.35
            else:
                color = '#FF6347'  # 토마토색
                label_position = 0.65
            label_text = f"BE {side.upper()} @ {break_even_price:.{precision}f}"
        else:
            color = '#FFA500'
            label_position = 0.5
            label_text = f"Break Even @ {break_even_price:.{precision}f}"

        pen = pg.mkPen(color, style=Qt.DashLine, width=2)

        break_even_line = pg.InfiniteLine(
            pos=break_even_price, angle=0, movable=False, pen=pen, label=label_text,
            labelOpts={
                'position': label_position,
                'color': color,
                'movable': True,
                'fill': (0, 0, 0, 150),
                'anchor': (0.5, 0.5)
            }
        )

        self.chart_widget.addItem(break_even_line, ignoreBounds=True)

        if side is not None:
            self.break_even_lines[side] = break_even_line
        else:
            self.break_even_line = break_even_line
        print(f"차트에 Break Even 라인 추가: {side or 'legacy'} @ {break_even_price:.{precision}f}")

    def remove_break_even_line(self, side=None):
        """Break Even 라인 제거 (side별)"""
        if not hasattr(self, 'chart_widget'):
            return

        if side is not None:
            line = self.break_even_lines.get(side)
            if line is not None:
                try:
                    self.chart_widget.removeItem(line)
                    self.break_even_lines[side] = None
                except Exception as e:
                    print(f"Break Even 라인 제거 중 오류 (무시됨): {e}")
        else:
            if self.break_even_line is not None:
                try:
                    self.chart_widget.removeItem(self.break_even_line)
                    self.break_even_line = None
                except Exception as e:
                    print(f"Break Even 라인 제거 중 오류 (무시됨): {e}")


    @pyqtSlot(float, int)
    def draw_profit_target_marker(self, profit_target_price, current_step):
        """익절 트리거 가격을 차트에 수평선으로 표시"""
        if not hasattr(self, 'chart_widget') or profit_target_price is None or profit_target_price == 0:
            return

        # 포지션 존재 여부 확인
        symbol = self.auto_trade_worker.symbol if hasattr(self, 'auto_trade_worker') and self.auto_trade_worker else None
        side_mode = self.auto_trade_side_mode if hasattr(self, 'auto_trade_side_mode') else None

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            if position_key in self.live_position_data:
                pos_amount = abs(self.live_position_data[position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        # 포지션이 없으면 마커 제거
        if not has_position:
            self.remove_profit_target_marker()
            return

        # 기존 마커 제거
        self.remove_profit_target_marker()

        precision = self.y_axis.precision
        # 익절 라인은 초록색
        line_color = '#00b050'

        try:
            # InfiniteLine으로 수평선 생성
            pen = pg.mkPen(color=line_color, width=2, style=Qt.DashLine)

            # Step 번호 포함한 라벨 생성 (current_step은 0-based이므로 +1)
            label_text = f"Step {current_step+1} TP: ${profit_target_price:.{precision}f}"

            profit_line = pg.InfiniteLine(
                pos=profit_target_price,
                angle=0,
                movable=False,
                pen=pen,
                label=label_text,
                labelOpts={'position': 0.1, 'color': line_color, 'fill': (0, 176, 80, 100), 'movable': False}
            )

            self.chart_widget.addItem(profit_line, ignoreBounds=True)

            # 익절 라인 저장 (나중에 제거하기 위해)
            if not hasattr(self, 'profit_target_marker'):
                self.profit_target_marker = None
            self.profit_target_marker = profit_line

            logger.debug(f"[익절 트리거] 차트에 익절가 표시: Step {current_step+1} TP ${profit_target_price:.{precision}f}")

        except Exception as e:
            print(f"[익절 트리거] 마커 표시 오류: {e}")
            import traceback
            traceback.print_exc()

    def remove_profit_target_marker(self):
        """익절 트리거 마커 제거 (레거시 + side별 모두 제거)"""
        if hasattr(self, 'profit_target_marker') and self.profit_target_marker is not None:
            try:
                self.chart_widget.removeItem(self.profit_target_marker)
            except:
                pass
            self.profit_target_marker = None
        # side별 마커도 모두 제거
        for side in ['long', 'short']:
            self.remove_profit_target_marker_for_side(side)

    def draw_uptrend_threshold_marker(self, threshold_price):
        """상승 중 추가진입 임계값을 차트에 흰색 수평선으로 표시"""
        if not hasattr(self, 'chart_widget') or threshold_price is None or threshold_price == 0:
            return

        # 이미 같은 가격으로 표시되어 있으면 업데이트하지 않음 (불필요한 반복 방지)
        if hasattr(self, 'uptrend_threshold_price') and self.uptrend_threshold_price == threshold_price:
            return

        # 포지션 존재 여부 확인
        symbol = self.auto_trade_worker.symbol if hasattr(self, 'auto_trade_worker') and self.auto_trade_worker else None
        side_mode = self.auto_trade_side_mode if hasattr(self, 'auto_trade_side_mode') else None

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            if position_key in self.live_position_data:
                pos_amount = abs(self.live_position_data[position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        # 포지션이 없으면 마커 제거
        if not has_position:
            self.remove_uptrend_threshold_marker()
            return

        # 기존 마커 제거
        self.remove_uptrend_threshold_marker()

        precision = self.y_axis.precision
        # 임계값 라인은 흰색
        line_color = '#FFFFFF'

        try:
            # InfiniteLine으로 수평선 생성 (라인 두께를 1로 변경)
            pen = pg.mkPen(color=line_color, width=1, style=Qt.DashLine)

            label_text = f"Threshold: ${threshold_price:.{precision}f}"

            threshold_line = pg.InfiniteLine(
                pos=threshold_price,
                angle=0,
                movable=False,
                pen=pen,
                label=label_text,
                labelOpts={'position': 0.06, 'color': line_color, 'fill': (255, 255, 255, 100), 'movable': False}
            )

            self.chart_widget.addItem(threshold_line, ignoreBounds=True)

            # 임계값 라인 및 가격 저장 (나중에 제거하기 위해)
            if not hasattr(self, 'uptrend_threshold_marker'):
                self.uptrend_threshold_marker = None
            self.uptrend_threshold_marker = threshold_line
            self.uptrend_threshold_price = threshold_price

            print(f"[역방향진입 임계값] 차트에 임계값 표시: ${threshold_price:.{precision}f}")

        except Exception as e:
            print(f"[역방향진입 임계값] 마커 표시 오류: {e}")
            import traceback
            traceback.print_exc()

    def remove_uptrend_threshold_marker(self):
        """상승 중 추가진입 임계값 마커 제거"""
        if hasattr(self, 'uptrend_threshold_marker') and self.uptrend_threshold_marker is not None:
            try:
                self.chart_widget.removeItem(self.uptrend_threshold_marker)
                print("[역방향진입 임계값] 마커 제거됨")
            except:
                pass
            self.uptrend_threshold_marker = None
            self.uptrend_threshold_price = None

    def draw_uptrend_threshold_2_marker(self, threshold_price_2):
        """상승 중 추가진입 2차 임계값을 차트에 흰색 수평선으로 표시 (즉시 진입용)"""
        if not hasattr(self, 'chart_widget') or threshold_price_2 is None or threshold_price_2 == 0:
            return

        # 이미 같은 가격으로 표시되어 있으면 업데이트하지 않음 (불필요한 반복 방지)
        if hasattr(self, 'uptrend_threshold_price_2') and self.uptrend_threshold_price_2 == threshold_price_2:
            return

        # 포지션 존재 여부 확인
        symbol = self.auto_trade_worker.symbol if hasattr(self, 'auto_trade_worker') and self.auto_trade_worker else None
        side_mode = self.auto_trade_side_mode if hasattr(self, 'auto_trade_side_mode') else None

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            if position_key in self.live_position_data:
                pos_amount = abs(self.live_position_data[position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        # 포지션이 없으면 마커 제거
        if not has_position:
            self.remove_uptrend_threshold_2_marker()
            return

        # 기존 마커 제거
        self.remove_uptrend_threshold_2_marker()

        precision = self.y_axis.precision
        # 2차 임계값 라인도 흰색
        line_color = '#FFFFFF'

        try:
            # InfiniteLine으로 수평선 생성 (실선으로 구분)
            pen = pg.mkPen(color=line_color, width=1, style=Qt.SolidLine)

            label_text = f"Threshold 2: ${threshold_price_2:.{precision}f}"

            threshold_line = pg.InfiniteLine(
                pos=threshold_price_2,
                angle=0,
                movable=False,
                pen=pen,
                label=label_text,
                labelOpts={'position': 0.06, 'color': line_color, 'fill': (255, 255, 255, 100), 'movable': False}
            )

            self.chart_widget.addItem(threshold_line, ignoreBounds=True)

            # 임계값 라인 및 가격 저장 (나중에 제거하기 위해)
            if not hasattr(self, 'uptrend_threshold_marker_2'):
                self.uptrend_threshold_marker_2 = None
            self.uptrend_threshold_marker_2 = threshold_line
            self.uptrend_threshold_price_2 = threshold_price_2

            print(f"[역방향진입 2차 임계값] 차트에 임계값 표시: ${threshold_price_2:.{precision}f}")

        except RuntimeError as e:
            # Qt 객체가 이미 삭제된 경우
            print(f"[역방향진입 2차 임계값] 차트 렌더링 오류 (Qt 객체 삭제됨): {e}")
        except Exception as e:
            # 기타 예외
            print(f"[역방향진입 2차 임계값] 차트 렌더링 예외: {e}")
            import traceback
            traceback.print_exc()


    def remove_uptrend_threshold_2_marker(self):
        """상승 중 추가진입 2차 임계값 마커 제거"""
        if hasattr(self, 'uptrend_threshold_marker_2') and self.uptrend_threshold_marker_2 is not None:
            try:
                self.chart_widget.removeItem(self.uptrend_threshold_marker_2)
                print("[역방향진입 2차 임계값] 마커 제거됨")
            except:
                pass
            self.uptrend_threshold_marker_2 = None
            self.uptrend_threshold_price_2 = None

    # === Side별 마커 함수들 ===

    def draw_uptrend_threshold_marker_for_side(self, side, threshold_price):
        """Side별 상승 중 추가진입 임계값을 차트에 표시"""
        if not hasattr(self, 'chart_widget') or threshold_price is None or threshold_price == 0:
            return

        # side별 마커 저장소 초기화
        if not hasattr(self, 'uptrend_threshold_markers_by_side'):
            self.uptrend_threshold_markers_by_side = {'long': None, 'short': None}
            self.uptrend_threshold_prices_by_side = {'long': None, 'short': None}

        # 이미 같은 가격으로 표시되어 있으면 업데이트하지 않음
        if self.uptrend_threshold_prices_by_side.get(side) == threshold_price:
            return

        # 포지션 존재 여부 확인
        worker = self.auto_trade_workers.get(side)
        if not worker or not worker.is_running:
            self.remove_uptrend_threshold_marker_for_side(side)
            return

        symbol = worker.symbol if hasattr(worker, 'symbol') else None
        side_mode = worker.side_mode if hasattr(worker, 'side_mode') else ('LONG' if side == 'long' else 'SHORT')

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            if position_key in self.live_position_data_by_side.get(side, {}):
                pos_amount = abs(self.live_position_data_by_side[side][position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        if not has_position:
            self.remove_uptrend_threshold_marker_for_side(side)
            return

        # 기존 마커 제거
        self.remove_uptrend_threshold_marker_for_side(side)

        precision = self.y_axis.precision
        # LONG은 흰색, SHORT는 노란색
        line_color = '#FFFFFF' if side == 'long' else '#FFFF00'
        # LONG은 왼쪽, SHORT는 오른쪽 라벨
        label_pos = 0.06 if side == 'long' else 0.94
        label_anchor = (0, 0.5) if side == 'long' else (1, 0.5)
        side_label = "L" if side == 'long' else "S"

        try:
            pen = pg.mkPen(color=line_color, width=1, style=Qt.DashLine)
            label_text = f"[{side_label}] Threshold: ${threshold_price:.{precision}f}"

            threshold_line = pg.InfiniteLine(
                pos=threshold_price, angle=0, movable=False, pen=pen, label=label_text,
                labelOpts={'position': label_pos, 'color': line_color, 'fill': (255, 255, 255, 100), 'movable': False, 'anchor': label_anchor}
            )

            self.chart_widget.addItem(threshold_line, ignoreBounds=True)
            self.uptrend_threshold_markers_by_side[side] = threshold_line
            self.uptrend_threshold_prices_by_side[side] = threshold_price
            print(f"[{side.upper()} {'하강진입' if side == 'short' else '상승진입'} 임계값] 차트에 임계값 표시: ${threshold_price:.{precision}f}")

        except Exception as e:
            print(f"[{side.upper()} {'하강진입' if side == 'short' else '상승진입'} 임계값] 마커 표시 오류: {e}")

    def remove_uptrend_threshold_marker_for_side(self, side):
        """Side별 상승 중 추가진입 임계값 마커 제거"""
        if not hasattr(self, 'uptrend_threshold_markers_by_side'):
            return
        marker = self.uptrend_threshold_markers_by_side.get(side)
        if marker:
            try:
                self.chart_widget.removeItem(marker)
            except:
                pass
            self.uptrend_threshold_markers_by_side[side] = None
            self.uptrend_threshold_prices_by_side[side] = None

    def draw_uptrend_threshold_2_marker_for_side(self, side, threshold_price_2):
        """Side별 상승 중 추가진입 2차 임계값을 차트에 표시"""
        if not hasattr(self, 'chart_widget') or threshold_price_2 is None or threshold_price_2 == 0:
            return

        if not hasattr(self, 'uptrend_threshold_2_markers_by_side'):
            self.uptrend_threshold_2_markers_by_side = {'long': None, 'short': None}
            self.uptrend_threshold_2_prices_by_side = {'long': None, 'short': None}

        if self.uptrend_threshold_2_prices_by_side.get(side) == threshold_price_2:
            return

        worker = self.auto_trade_workers.get(side)
        if not worker or not worker.is_running:
            self.remove_uptrend_threshold_2_marker_for_side(side)
            return

        symbol = worker.symbol if hasattr(worker, 'symbol') else None
        side_mode = worker.side_mode if hasattr(worker, 'side_mode') else ('LONG' if side == 'long' else 'SHORT')

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            if position_key in self.live_position_data_by_side.get(side, {}):
                pos_amount = abs(self.live_position_data_by_side[side][position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        if not has_position:
            self.remove_uptrend_threshold_2_marker_for_side(side)
            return

        self.remove_uptrend_threshold_2_marker_for_side(side)

        precision = self.y_axis.precision
        line_color = '#FFFFFF' if side == 'long' else '#FFFF00'
        label_pos = 0.06 if side == 'long' else 0.94
        label_anchor = (0, 0.5) if side == 'long' else (1, 0.5)
        side_label = "L" if side == 'long' else "S"

        try:
            pen = pg.mkPen(color=line_color, width=1, style=Qt.DashDotLine)
            label_text = f"[{side_label}] Threshold 2: ${threshold_price_2:.{precision}f}"

            threshold_line = pg.InfiniteLine(
                pos=threshold_price_2, angle=0, movable=False, pen=pen, label=label_text,
                labelOpts={'position': label_pos, 'color': line_color, 'fill': (255, 255, 255, 100), 'movable': False, 'anchor': label_anchor}
            )

            self.chart_widget.addItem(threshold_line, ignoreBounds=True)
            self.uptrend_threshold_2_markers_by_side[side] = threshold_line
            self.uptrend_threshold_2_prices_by_side[side] = threshold_price_2
            print(f"[{side.upper()} {'하강진입' if side == 'short' else '상승진입'} 2차 임계값] 차트에 임계값 표시: ${threshold_price_2:.{precision}f}")

        except Exception as e:
            print(f"[{side.upper()} {'하강진입' if side == 'short' else '상승진입'} 2차 임계값] 마커 표시 오류: {e}")

    def remove_uptrend_threshold_2_marker_for_side(self, side):
        """Side별 상승 중 추가진입 2차 임계값 마커 제거"""
        if not hasattr(self, 'uptrend_threshold_2_markers_by_side'):
            return
        marker = self.uptrend_threshold_2_markers_by_side.get(side)
        if marker:
            try:
                self.chart_widget.removeItem(marker)
            except:
                pass
            self.uptrend_threshold_2_markers_by_side[side] = None
            self.uptrend_threshold_2_prices_by_side[side] = None

    def draw_profit_target_marker_for_side(self, side, profit_target_price):
        """Side별 익절 목표가를 차트에 표시"""
        if not hasattr(self, 'chart_widget') or profit_target_price is None or profit_target_price == 0:
            return

        # 기존 마커 제거
        self.remove_profit_target_marker_for_side(side)

        # 익절 모드에서는 H 트리거 마커 제거 (이미 제거된 경우 무시)
        if self.hedge_trigger_markers_by_side.get(side, []):
            self.remove_hedge_trigger_markers_for_side(side)

        worker = self.auto_trade_workers.get(side)
        current_step = getattr(worker, 'current_step', 0) if worker else 0
        precision = self.y_axis.precision

        line_color = '#00b050'
        pen = pg.mkPen(color=line_color, width=2, style=Qt.DashLine)

        side_prefix = "[L]" if side == 'long' else "[S]"
        label_text = f"{side_prefix} Step {current_step+1} TP: ${profit_target_price:.{precision}f}"

        # LONG=왼쪽(0.15), SHORT=오른쪽(0.85)
        label_position = 0.15 if side == 'long' else 0.85
        label_anchor = (0, 0.5) if side == 'long' else (1, 0.5)

        try:
            profit_line = pg.InfiniteLine(
                pos=profit_target_price, angle=0, movable=False, pen=pen,
                label=label_text,
                labelOpts={'position': label_position, 'color': line_color,
                           'fill': (0, 176, 80, 100), 'movable': False, 'anchor': label_anchor}
            )
            self.chart_widget.addItem(profit_line, ignoreBounds=True)
            self.profit_target_markers_by_side[side] = profit_line
            logger.debug(f"[{side.upper()} 익절 트리거] 차트에 익절가 표시: Step {current_step+1} TP ${profit_target_price:.{precision}f}")
        except Exception as e:
            print(f"[{side.upper()} 익절 트리거] 마커 표시 오류: {e}")

    def remove_profit_target_marker_for_side(self, side):
        """Side별 익절 트리거 마커 제거"""
        marker = self.profit_target_markers_by_side.get(side)
        if marker is not None:
            try:
                self.chart_widget.removeItem(marker)
                logger.debug(f"[{side.upper()} 익절 트리거] 마커 제거됨")
            except:
                pass
            self.profit_target_markers_by_side[side] = None

    def draw_hedge_trigger_markers_for_side(self, side, hedge_triggers, side_mode, current_step):
        """Side별 헷지 트리거를 차트에 표시"""
        if not hasattr(self, 'chart_widget'):
            return

        # side별 마커 저장소 초기화
        if not hasattr(self, 'hedge_trigger_markers_by_side'):
            self.hedge_trigger_markers_by_side = {'long': [], 'short': []}

        if not hedge_triggers:
            self.remove_hedge_trigger_markers_for_side(side)
            return

        self.remove_hedge_trigger_markers_for_side(side)

        precision = self.y_axis.precision
        # LONG 헷지(SHORT 포지션)는 빨간색, SHORT 헷지(LONG 포지션)는 파란색
        color = '#c00000' if side_mode == "LONG" else '#0070c0'
        # LONG은 왼쪽, SHORT는 오른쪽 라벨
        label_pos = 0.1 if side == 'long' else 0.9
        label_anchor = (0, 0.5) if side == 'long' else (1, 0.5)
        side_label = "L" if side == 'long' else "S"

        for i, trigger in enumerate(hedge_triggers):
            price, qty, executed = trigger
            line_color = '#808080' if executed else color

            try:
                pen = pg.mkPen(None)
                label_text = f"[{side_label}] Step {current_step+1} H{i+1}: ${price:.{precision}f}"

                hedge_line = pg.InfiniteLine(
                    pos=price, angle=0, movable=False, pen=pen, label=label_text,
                    labelOpts={'position': label_pos, 'color': line_color, 'movable': False, 'fill': (0, 0, 0, 150), 'anchor': label_anchor}
                )

                self.chart_widget.addItem(hedge_line, ignoreBounds=True)
                self.hedge_trigger_markers_by_side[side].append(hedge_line)

            except Exception as e:
                print(f"[{side.upper()}] 헷지 트리거 라벨 추가 오류: {e}")

    def remove_hedge_trigger_markers_for_side(self, side):
        """Side별 헷지 트리거 마커 제거"""
        if not hasattr(self, 'hedge_trigger_markers_by_side'):
            return
        markers = self.hedge_trigger_markers_by_side.get(side, [])
        for marker in markers:
            try:
                self.chart_widget.removeItem(marker)
            except:
                pass
        self.hedge_trigger_markers_by_side[side] = []

    def draw_m4_order_marker_for_side(self, side, m_orders_data):
        """Side별 NSO 지정가 주문을 차트에 표시"""
        if not hasattr(self, 'chart_widget'):
            return

        # side별 마커 저장소 초기화
        if not hasattr(self, 'm4_markers_by_side'):
            self.m4_markers_by_side = {'long': None, 'short': None}

        # 기존 마커 제거
        self.remove_m4_marker_for_side(side)

        if len(m_orders_data) < 1:
            return

        nso_data = m_orders_data[0]
        price = nso_data.get('price', 0)
        qty = nso_data.get('qty', 0)
        status = nso_data.get('status', 'Waiting')

        if price <= 0 or qty <= 0 or status == 'Skipped':
            return

        try:
            precision = self.y_axis.precision if hasattr(self, 'y_axis') and self.y_axis else 4

            worker = self.auto_trade_workers.get(side)
            side_mode = getattr(worker, 'side_mode', 'LONG' if side == 'long' else 'SHORT') if worker else ('LONG' if side == 'long' else 'SHORT')
            current_step = getattr(worker, 'current_step', 0) if worker else 0

            color = '#00aa00' if side_mode == "LONG" else '#aa0000'
            if status == 'Filled':
                color = '#808080'

            label_pos = 0.15 if side == 'long' else 0.85
            label_anchor = (0, 0.5) if side == 'long' else (1, 0.5)
            side_label = "L" if side == 'long' else "S"

            pen = pg.mkPen(None)
            label_text = f"[{side_label}] NSO (Step {current_step+2}): ${price:.{precision}f}"

            m4_line = pg.InfiniteLine(
                pos=price, angle=0, movable=False, pen=pen, label=label_text,
                labelOpts={'position': label_pos, 'color': color, 'fill': (0, 0, 0, 150), 'movable': False, 'anchor': label_anchor}
            )

            self.chart_widget.addItem(m4_line, ignoreBounds=True)
            self.m4_markers_by_side[side] = m4_line
            print(f"[{side.upper()}] NSO 주문 마커 추가: Step {current_step+2} @ ${price:.{precision}f} (상태: {status})")

        except Exception as e:
            print(f"[{side.upper()}] NSO 마커 표시 오류: {e}")

    def remove_m4_marker_for_side(self, side):
        """Side별 M4 마커 제거"""
        if not hasattr(self, 'm4_markers_by_side'):
            return
        marker = self.m4_markers_by_side.get(side)
        if marker:
            try:
                self.chart_widget.removeItem(marker)
            except:
                pass
            self.m4_markers_by_side[side] = None

    @pyqtSlot(float)
    def draw_emergency_exit_line_marker(self, exit_line_price, panel_side=None):
        """헷지 긴급 탈출 라인을 차트에 빨간색 수평선으로 표시"""
        sp = "[L]" if panel_side == 'long' else "[S]" if panel_side == 'short' else ""
        if not hasattr(self, 'chart_widget') or exit_line_price is None or exit_line_price == 0:
            return

        # side별 딕셔너리 초기화
        if not hasattr(self, 'emergency_exit_line_markers'):
            self.emergency_exit_line_markers = {}
        if not hasattr(self, 'emergency_exit_line_prices'):
            self.emergency_exit_line_prices = {}

        side_key = panel_side or '_legacy'

        # 이미 같은 가격으로 표시되어 있으면 업데이트하지 않음
        if self.emergency_exit_line_prices.get(side_key) == exit_line_price:
            return

        # 포지션 존재 여부 확인
        worker = self.auto_trade_workers.get(panel_side) if panel_side else self.auto_trade_worker
        symbol = worker.symbol if worker else None
        side_mode = worker.side_mode if worker else None

        has_position = False
        if symbol and side_mode:
            position_key = f"{symbol}_{side_mode}"
            pos_data = self.live_position_data_by_side.get(panel_side, {}) if panel_side else self.live_position_data
            if position_key in pos_data:
                pos_amount = abs(pos_data[position_key].get('amount', 0))
                if pos_amount > 0:
                    has_position = True

        # 포지션이 없으면 마커 제거
        if not has_position:
            self.remove_emergency_exit_line_marker(panel_side)
            return

        # 기존 마커 제거 (해당 side만)
        self.remove_emergency_exit_line_marker(panel_side)

        precision = self.y_axis.precision
        # 긴급 탈출 라인은 빨간색 (경고)
        line_color = '#FF0000'

        try:
            # InfiniteLine으로 수평선 생성 (점선으로 표시)
            pen = pg.mkPen(color=line_color, width=2, style=Qt.DashLine)

            label_text = f"{sp} 🚨 Emergency Exit: ${exit_line_price:.{precision}f}" if sp else f"🚨 Emergency Exit: ${exit_line_price:.{precision}f}"

            # panel_side 기준으로 라벨 배치 (LONG패널=왼쪽, SHORT패널=오른쪽)
            is_left = (panel_side == 'long')
            label_pos = 0.10 if is_left else 0.90
            label_anchor = (0, 0.5) if is_left else (1, 0.5)

            exit_line = pg.InfiniteLine(
                pos=exit_line_price,
                angle=0,
                movable=False,
                pen=pen,
                label=label_text,
                labelOpts={'position': label_pos, 'color': line_color, 'fill': (255, 0, 0, 100), 'movable': False, 'anchor': label_anchor}
            )

            self.chart_widget.addItem(exit_line, ignoreBounds=True)

            # 긴급 탈출 라인 및 가격 저장 (side별)
            self.emergency_exit_line_markers[side_key] = exit_line
            self.emergency_exit_line_prices[side_key] = exit_line_price

            print(f"{sp} [헷지 보호] 차트에 긴급 탈출 라인 표시: ${exit_line_price:.{precision}f}")

        except Exception as e:
            print(f"{sp} [헷지 보호] 긴급 탈출 라인 마커 표시 오류: {e}")
            import traceback
            traceback.print_exc()

    def remove_emergency_exit_line_marker(self, panel_side=None):
        """헷지 긴급 탈출 라인 마커 제거"""
        if not hasattr(self, 'emergency_exit_line_markers'):
            self.emergency_exit_line_markers = {}
        if not hasattr(self, 'emergency_exit_line_prices'):
            self.emergency_exit_line_prices = {}

        sp = "[L]" if panel_side == 'long' else "[S]" if panel_side == 'short' else ""

        if panel_side:
            # 특정 side만 제거
            side_key = panel_side
            marker = self.emergency_exit_line_markers.get(side_key)
            if marker is not None:
                try:
                    self.chart_widget.removeItem(marker)
                    print(f"{sp} [헷지 보호] 긴급 탈출 라인 마커 제거됨")
                except:
                    pass
                self.emergency_exit_line_markers.pop(side_key, None)
                self.emergency_exit_line_prices.pop(side_key, None)
        else:
            # side 미지정 시 모든 마커 제거
            for side_key, marker in list(self.emergency_exit_line_markers.items()):
                if marker is not None:
                    try:
                        self.chart_widget.removeItem(marker)
                        side_sp = "[L]" if side_key == 'long' else "[S]" if side_key == 'short' else ""
                        print(f"{side_sp} [헷지 보호] 긴급 탈출 라인 마커 제거됨")
                    except:
                        pass
            self.emergency_exit_line_markers.clear()
            self.emergency_exit_line_prices.clear()

    def draw_hedge_trigger_markers(self, hedge_triggers, side_mode, current_step):
        """헷지 트리거 가격을 차트에 수평선으로 표시"""
        if not hasattr(self, 'chart_widget'):
            return

        # 헷지 트리거가 없으면 기존 마커만 제거하고 종료
        if not hedge_triggers:
            self.remove_all_hedge_trigger_markers()
            print(f"[헷지 트리거] 트리거가 없어 모든 마커를 제거했습니다.")
            return

        # Worker가 이미 포지션 확인 후 시그널을 보냈으므로 추가 확인 불필요
        # 기존 마커 제거
        self.remove_all_hedge_trigger_markers()

        precision = self.y_axis.precision
        # LONG은 빨간색, SHORT는 파란색
        color = '#c00000' if side_mode == "LONG" else '#0070c0'

        for i, trigger in enumerate(hedge_triggers):
            price, qty, executed = trigger

            # 실행된 트리거는 회색으로 표시
            if executed:
                line_color = '#808080'
            else:
                line_color = color

            try:
                # InfiniteLine으로 수평선 생성 (투명)
                pen = pg.mkPen(None)  # 투명한 라인

                # Step 번호 포함한 라벨 생성 (current_step은 0-based이므로 +1)
                label_text = f"Step {current_step+1} H{i+1}: ${price:.{precision}f}"

                hedge_line = pg.InfiniteLine(
                    pos=price,
                    angle=0,
                    movable=False,
                    pen=pen,
                    label=label_text,
                    labelOpts={
                        'position': 0.1,
                        'color': line_color,
                        'movable': False,
                        'fill': (0, 0, 0, 150),
                        'anchor': (0, 0.5)
                    }
                )

                self.chart_widget.addItem(hedge_line, ignoreBounds=True)
                self.hedge_trigger_markers.append((hedge_line, None))
                print(f"헷지 트리거 라벨 추가: Step {current_step+1} H{i+1} {price:.{precision}f} (실행됨: {executed})")

            except Exception as e:
                print(f"헷지 트리거 라벨 추가 오류: {e}")

    def remove_all_hedge_trigger_markers(self):
        """모든 헷지 트리거 마커 제거"""
        if not hasattr(self, 'chart_widget'):
            return

        for line, _ in self.hedge_trigger_markers:
            try:
                if line:
                    self.chart_widget.removeItem(line)
            except Exception as e:
                print(f"헷지 트리거 라인 제거 중 오류 (무시됨): {e}")

        self.hedge_trigger_markers.clear()

    def draw_m4_order_marker(self, m_orders_data):
        """NSO 지정가 주문을 차트에 수평선으로 표시"""
        if not hasattr(self, 'chart_widget'):
            return

        # 기존 NSO 마커 제거
        self.remove_m4_order_marker()

        if len(m_orders_data) < 1:
            return

        nso_data = m_orders_data[0]
        price = nso_data.get('price', 0)
        qty = nso_data.get('qty', 0)
        status = nso_data.get('status', 'Waiting')

        if price <= 0 or qty <= 0 or status == 'Skipped':
            return

        try:
            precision = self.y_axis.precision if hasattr(self, 'y_axis') and self.y_axis else 4

            # Worker에서 side_mode 가져오기 (long 패널 우선)
            side_mode = "LONG"
            current_step = 0
            worker = self.auto_trade_workers.get('long')
            if worker and worker.is_running:
                side_mode = getattr(worker, 'side_mode', 'LONG')
                current_step = getattr(worker, 'current_step', 0)
            else:
                worker = self.auto_trade_workers.get('short')
                if worker and worker.is_running:
                    side_mode = getattr(worker, 'side_mode', 'SHORT')
                    current_step = getattr(worker, 'current_step', 0)

            color = '#00aa00' if side_mode == "LONG" else '#aa0000'
            if status == 'Filled':
                color = '#808080'

            pen = pg.mkPen(None)
            label_text = f"NSO (Step {current_step+2}): ${price:.{precision}f}"

            m4_line = pg.InfiniteLine(
                pos=price,
                angle=0,
                movable=False,
                pen=pen,
                label=label_text,
                labelOpts={
                    'position': 0.9,
                    'color': color,
                    'movable': False,
                    'fill': (0, 0, 0, 150),
                    'anchor': (1, 0.5)
                }
            )

            self.chart_widget.addItem(m4_line, ignoreBounds=True)
            self.m4_order_marker = m4_line
            print(f"NSO 주문 마커 추가: Step {current_step+2} @ ${price:.{precision}f} (상태: {status})")

        except Exception as e:
            print(f"NSO 주문 마커 추가 오류: {e}")

    def remove_m4_order_marker(self):
        """M4 주문 마커 제거"""
        if not hasattr(self, 'chart_widget'):
            return

        if self.m4_order_marker:
            try:
                self.chart_widget.removeItem(self.m4_order_marker)
            except Exception as e:
                print(f"M4 마커 제거 중 오류 (무시됨): {e}")
            self.m4_order_marker = None

    def toggle_chart_visibility(self):
        """차트 표시/숨김 토글 (성능 최적화)"""
        is_visible = self.chart_visible_button.isChecked()

        if is_visible:
            # 차트 표시
            self.chart_widget.show()
            self.chart_visible_button.setText("📈 Chart ON")
            print("[Chart] 차트 표시 활성화")
        else:
            # 차트 숨김
            self.chart_widget.hide()
            self.chart_visible_button.setText("📉 Chart OFF")
            print("[Chart] 차트 숨김 - 렌더링 부하 제거")

        # 상태 저장
        self._save_chart_view_state()

    def toggle_lines_for_side(self, side):
        """특정 사이드(LONG/SHORT)의 모든 차트 라인/마커 표시/숨김 토글"""
        btn = self.toggle_lines_buttons.get(side)
        if not btn:
            return

        visible = btn.isChecked()
        self.lines_visible_by_side[side] = visible

        side_label = "L" if side == 'long' else "S"
        if visible:
            btn.setText(f"{side_label} Lines ON")
        else:
            btn.setText(f"{side_label} Lines OFF")

        self._set_lines_visible_for_side(side, visible)
        print(f"[{side.upper()}] 차트 라인 {'표시' if visible else '숨김'}")

    def _set_lines_visible_for_side(self, side, visible):
        """특정 사이드의 모든 차트 라인/마커 가시성 설정"""
        # 포지션 라인
        for key, line in self.position_lines_by_side.get(side, {}).items():
            if line:
                line.setVisible(visible)

        # 주문 라인
        for key, line in self.order_lines_by_side.get(side, {}).items():
            if line:
                line.setVisible(visible)

        # Break Even 라인
        be_line = self.break_even_lines.get(side)
        if be_line:
            be_line.setVisible(visible)

        # 헷지 트리거 마커
        for marker in self.hedge_trigger_markers_by_side.get(side, []):
            if isinstance(marker, tuple):
                if marker[0]:
                    marker[0].setVisible(visible)
            elif marker:
                marker.setVisible(visible)

        # 역방향진입 임계값 마커
        if hasattr(self, 'uptrend_threshold_markers_by_side'):
            marker = self.uptrend_threshold_markers_by_side.get(side)
            if marker:
                marker.setVisible(visible)

        # 역방향진입 임계값 2 마커
        if hasattr(self, 'uptrend_threshold_2_markers_by_side'):
            marker = self.uptrend_threshold_2_markers_by_side.get(side)
            if marker:
                marker.setVisible(visible)

        # M4 주문 마커
        if hasattr(self, 'm4_markers_by_side'):
            marker = self.m4_markers_by_side.get(side)
            if marker:
                marker.setVisible(visible)

        # Side별 익절 트리거 마커
        profit_marker = self.profit_target_markers_by_side.get(side)
        if profit_marker is not None:
            profit_marker.setVisible(visible)

        # emergency_exit side별 분리
        if hasattr(self, 'emergency_exit_line_markers'):
            marker = self.emergency_exit_line_markers.get(side)
            if marker is not None:
                worker = self.auto_trade_workers.get(side)
                if worker and worker.is_running:
                    marker.setVisible(visible)

    def _get_refresh_interval_ms(self):
        """현재 타임프레임에 맞는 차트 갱신 간격(밀리초) 반환"""
        # 타임프레임을 밀리초로 변환
        interval_map = {
            "1m": 60 * 1000,      # 1분 = 60초
            "3m": 3 * 60 * 1000,  # 3분 = 180초
            "5m": 5 * 60 * 1000,  # 5분 = 300초
            "15m": 15 * 60 * 1000,  # 15분 = 900초
            "30m": 30 * 60 * 1000,  # 30분 = 1800초
            "1h": 60 * 60 * 1000,   # 1시간 = 3600초
            "2h": 2 * 60 * 60 * 1000,  # 2시간 = 7200초
            "4h": 4 * 60 * 60 * 1000,  # 4시간 = 14400초
            "6h": 6 * 60 * 60 * 1000,  # 6시간 = 21600초
            "12h": 12 * 60 * 60 * 1000,  # 12시간 = 43200초
            "1d": 24 * 60 * 60 * 1000,  # 1일 = 86400초
            "1w": 7 * 24 * 60 * 60 * 1000  # 1주 = 604800초
        }
        return interval_map.get(self.current_interval, 60 * 1000)  # 기본값: 60초

    def _get_min_chart_range_seconds(self):
        """차트 X축 최소 범위(초) 계산 - 최소 5개 캔들 표시"""
        min_candles = 5
        interval_seconds = self._get_refresh_interval_ms() / 1000.0
        return interval_seconds * min_candles

    def _convert_interval_to_bybit(self, interval):
        """타임프레임을 Bybit 형식으로 변환 (5m -> 5)"""
        mapping = {
            '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
            '1d': 'D', '1w': 'W', '1M': 'M'
        }
        return mapping.get(interval, '5')  # 기본값: 5분

    def _start_chart_timer_aligned(self):
        """타임프레임의 정확한 00초에 맞춰 타이머 시작"""
        import time

        refresh_interval_ms = self._get_refresh_interval_ms()
        refresh_interval_sec = refresh_interval_ms / 1000.0

        # 현재 시간 (Unix timestamp)
        current_time = time.time()

        # 다음 타임프레임 시작 시간 계산
        # 현재 시간을 타임프레임 간격으로 나눈 나머지를 빼면 다음 00초
        time_until_next = refresh_interval_sec - (current_time % refresh_interval_sec)

        # 1초 미만이면 다음 주기로 넘김 (즉시 실행 방지)
        if time_until_next < 1.0:
            time_until_next += refresh_interval_sec

        # Bybit은 WebSocket으로 실시간 업데이트되므로 타이머는 백업용
        # 다른 거래소의 경우 서버 지연 보정 필요 (필요 시 +3초 추가)

        print(f"[차트 타이머] 다음 타임프레임 시작까지: {time_until_next:.1f}초 대기")

        # SingleShot 타이머로 다음 00초에 실행 (정규 타이머 대신 재귀 방식 사용)
        QTimer.singleShot(int(time_until_next * 1000), self._on_aligned_timer_tick)

    def _on_aligned_timer_tick(self):
        """타임프레임 00초에 도달 시 실행 - 차트 업데이트 후 다음 타이머 예약"""
        # 차트 데이터 새로고침
        self.refresh_chart_data()

        # 다음 00초를 위한 타이머 재예약 (재귀 방식으로 시간 틀어짐 방지)
        self._schedule_next_aligned_timer()

    def _schedule_next_aligned_timer(self):
        """다음 타임프레임 00초를 위한 타이머 예약"""
        import time

        refresh_interval_ms = self._get_refresh_interval_ms()
        refresh_interval_sec = refresh_interval_ms / 1000.0

        # 현재 시간 (Unix timestamp)
        current_time = time.time()

        # 다음 타임프레임 시작 시간 계산
        time_until_next = refresh_interval_sec - (current_time % refresh_interval_sec)

        # 1초 미만이면 다음 주기로 넘김
        if time_until_next < 1.0:
            time_until_next += refresh_interval_sec

        # 다음 00초를 위한 SingleShot 타이머 예약
        QTimer.singleShot(int(time_until_next * 1000), self._on_aligned_timer_tick)

    def refresh_chart_data(self):
        # 중복 실행 방지
        if self.chart_refresh_pending:
            print(f"[차트 새로고침] 이미 진행 중 - 스킵")
            return

        if self.api_module and self.api_module.is_api_key_active() and self.current_symbol:
            self.chart_refresh_pending = True
            self.update_chart(self.current_symbol, self.current_interval, is_refresh=True)
            self.chart_refresh_pending = False

    def on_chart_range_changed(self):
        """차트 범위 변경 시 호출 - 사용자 조작 감지 및 범위 저장"""
        # Lock Mode가 활성화된 경우
        if self.chart_lock_mode:
            # 첫 복원이 필요한 경우 값을 저장하지 않음 (복원 전 ViewBox 초기화로 인한 덮어쓰기 방지)
            if self.lock_mode_needs_first_restore:
                return

            # X축 범위 및 위치 업데이트
            current_range = self.chart_viewbox.viewRange()
            new_x_range = current_range[0][1] - current_range[0][0]
            new_x_min = current_range[0][0]
            new_x_max = current_range[0][1]

            # 범위와 위치 모두 저장 (디바운스로 저장 빈도 조절)
            self.lock_mode_x_range = new_x_range
            self.lock_mode_saved_x_min = new_x_min
            self.lock_mode_saved_x_max = new_x_max
            self._save_chart_view_state()
        else:
            # Lock Mode OFF: 차트 위치(X축 min/max) 저장
            self.chart_user_interacted = True
            current_range = self.chart_viewbox.viewRange()
            new_x_min = current_range[0][0]
            new_x_max = current_range[0][1]

            # 위치 업데이트 (디바운스로 저장 빈도 조절)
            self.saved_chart_x_min = new_x_min
            self.saved_chart_x_max = new_x_max
            self._save_chart_view_state()

    def reset_chart_view(self):
        """차트 뷰를 자동 범위로 리셋 (버튼 클릭 시)"""
        self.chart_user_interacted = False
        self.chart_viewbox.autoRange()

    def toggle_lock_mode(self, checked, from_config_restore=False):
        """Lock Mode 토글 - 최신 봉을 오른쪽에 고정

        Args:
            checked: Lock Mode 활성화 여부
            from_config_restore: config 복원으로 인한 호출인지 여부 (기본값: False)
        """
        self.chart_lock_mode = checked

        if checked:
            for btn in self.lock_mode_buttons.values():
                btn.setText("🔒 Lock")
            self.chart_user_interacted = False  # 고정 모드 활성화 시 자동 범위 재개

            # Lock Mode 활성화 시: 저장된 범위가 없을 때만 현재 보고 있는 X축 범위를 저장
            # (config 복원 시 이미 설정된 값을 덮어쓰지 않기 위함)
            if self.lock_mode_x_range is None:
                current_range = self.chart_viewbox.viewRange()
                calculated_range = current_range[0][1] - current_range[0][0]
                self.lock_mode_x_range = calculated_range
                print(f"[Lock Mode] 현재 차트 범위로 초기화: {self.lock_mode_x_range:.2f}초")
            else:
                print(f"[Lock Mode] 저장된 범위 유지: {self.lock_mode_x_range:.2f}초")

            self.lock_mode_last_x_max = None  # 첫 실행에서 최신 봉 시간으로 초기화됨

            # config 복원이 아닌 경우(수동 활성화)만 복원 플래그를 리셋
            if not from_config_restore:
                self.lock_mode_needs_first_restore = False
        else:
            for btn in self.lock_mode_buttons.values():
                btn.setText("🔓 Unlock")
            self.lock_mode_x_range = None  # 범위 저장 초기화
            self.lock_mode_last_x_max = None  # 오른쪽 끝 시간 초기화
            self.lock_mode_needs_first_restore = False  # 플래그 초기화
            # 고정 모드 비활성화 시 현재 뷰 유지

        # Lock Mode 상태 및 차트 범위를 config에 저장
        self._save_chart_view_state()

    def _save_chart_view_state(self):
        """차트 뷰 상태 저장 (Lock Mode 상태 및 차트 범위) - 디바운스 적용"""
        # 기존 타이머가 있으면 중지
        if self.chart_view_save_timer is not None:
            self.chart_view_save_timer.stop()

        # 1초 후 실제 저장 실행
        self.chart_view_save_timer = QTimer()
        self.chart_view_save_timer.setSingleShot(True)
        self.chart_view_save_timer.timeout.connect(self._save_chart_view_state_immediate)
        self.chart_view_save_timer.start(1000)

    def _save_chart_view_state_immediate(self):
        """차트 뷰 상태 즉시 저장 (디바운스 후 실제 저장)"""
        if "app_settings" not in self.config_data:
            self.config_data["app_settings"] = {}

        self.config_data["app_settings"]["lock_mode_enabled"] = self.chart_lock_mode
        self.config_data["app_settings"]["chart_visible"] = self.chart_visible_button.isChecked()

        if self.chart_lock_mode:
            # Lock Mode ON: X축 범위와 위치 모두 저장
            if self.lock_mode_x_range is not None:
                min_range = self._get_min_chart_range_seconds()
                if self.lock_mode_x_range >= min_range:
                    self.config_data["app_settings"]["chart_x_range"] = self.lock_mode_x_range

            # Lock Mode ON에서 드래그한 위치 저장
            if self.lock_mode_saved_x_min is not None and self.lock_mode_saved_x_max is not None:
                self.config_data["app_settings"]["lock_mode_x_min"] = self.lock_mode_saved_x_min
                self.config_data["app_settings"]["lock_mode_x_max"] = self.lock_mode_saved_x_max
        else:
            # Lock Mode OFF: 차트 위치(X축 min/max) 저장
            if self.saved_chart_x_min is not None and self.saved_chart_x_max is not None:
                self.config_data["app_settings"]["chart_x_min"] = self.saved_chart_x_min
                self.config_data["app_settings"]["chart_x_max"] = self.saved_chart_x_max

        config_manager.save_config_data(self.config_data)

    def _restore_chart_position(self):
        """Lock Mode OFF: 저장된 차트 위치(X축 min/max) 복원"""
        try:
            if self.saved_chart_x_min is None or self.saved_chart_x_max is None:
                return

            # 캔들 데이터 가져오기
            data = self.candlestick_item.data
            if data is None or len(data) == 0:
                return

            # 저장된 X축 범위로 필터링
            visible_data = data[(data['time'] >= self.saved_chart_x_min) & (data['time'] <= self.saved_chart_x_max)]

            if len(visible_data) == 0:
                # 저장된 범위에 데이터가 없으면 자동 범위 사용
                print(f"[차트 복원] 저장된 범위에 데이터 없음. 자동 범위 사용.")
                self.chart_viewbox.autoRange()
                return

            # Y축 범위 계산
            y_min = visible_data['low'].min()
            y_max = visible_data['high'].max()
            y_range = y_max - y_min
            y_padding = y_range * 0.05

            # ViewBox 범위 설정
            self.chart_viewbox.setRange(
                xRange=(self.saved_chart_x_min, self.saved_chart_x_max),
                yRange=(y_min - y_padding, y_max + y_padding),
                padding=0
            )
            print(f"[차트 복원] 저장된 위치로 복원 완료: X축 [{self.saved_chart_x_min:.2f} ~ {self.saved_chart_x_max:.2f}]")

        except Exception as e:
            print(f"[차트 복원] 오류: {e}")
            import traceback
            traceback.print_exc()

    def _scroll_one_candle_left(self):
        """Unlock 상태에서 새 봉 추가 시 한 칸씩 왼쪽으로 스크롤 (자동 스크롤)"""
        try:
            # 캔들 데이터 가져오기
            data = self.candlestick_item.data
            if data is None or len(data) < 2:
                return

            # 현재 뷰 범위 가져오기
            current_range = self.chart_viewbox.viewRange()
            current_x_min = current_range[0][0]
            current_x_max = current_range[0][1]

            # 캔들 간격 계산 (마지막 두 봉의 시간 차이)
            candle_interval = data['time'].iloc[-1] - data['time'].iloc[-2]

            # 한 칸 왼쪽으로 이동 (X축 범위는 유지)
            new_x_min = current_x_min + candle_interval
            new_x_max = current_x_max + candle_interval

            # 표시될 데이터 범위 찾기 (Y축 계산용)
            visible_data = data[(data['time'] >= new_x_min) & (data['time'] <= new_x_max)]

            if len(visible_data) > 0:
                # Y축 범위 설정 (가격)
                y_min = visible_data['low'].min()
                y_max = visible_data['high'].max()
                y_range = y_max - y_min
                y_padding = y_range * 0.05

                # ViewBox 범위 설정
                self.chart_viewbox.setRange(
                    xRange=(new_x_min, new_x_max),
                    yRange=(y_min - y_padding, y_max + y_padding),
                    padding=0
                )
                # print(f"[차트 자동 스크롤] 한 칸 왼쪽으로 이동 ({candle_interval}초)")

        except Exception as e:
            logger.error(f"차트 자동 스크롤 오류: {e}", exc_info=True)

    def _lock_to_latest_candles(self):
        """차트를 최신 봉 기준으로 고정 (현재 뷰 범위 유지하며 스크롤)"""
        try:
            # 캔들 데이터 가져오기
            data = self.candlestick_item.data
            if data is None or len(data) == 0:
                return

            # 현재 뷰 범위 가져오기
            current_range = self.chart_viewbox.viewRange()

            # 최신 봉의 시간
            latest_candle_time = data['time'].iloc[-1]

            # 이전 오른쪽 끝 시간이 없으면 최신 봉 시간으로 초기화 (첫 실행)
            if self.lock_mode_last_x_max is None:
                self.lock_mode_last_x_max = latest_candle_time

                # [디버그] 복원 조건 확인
                print(f"[차트 디버그] 첫 실행 감지 - lock_mode_saved_x_min={self.lock_mode_saved_x_min}, lock_mode_saved_x_max={self.lock_mode_saved_x_max}")

                # 첫 실행 시: 저장된 위치가 있으면 복원 (드래그한 위치 복원)
                if self.lock_mode_saved_x_min is not None and self.lock_mode_saved_x_max is not None:
                    # 저장된 위치로 복원 (X축만)
                    new_x_min = self.lock_mode_saved_x_min
                    new_x_max = self.lock_mode_saved_x_max

                    self.chart_viewbox.setRange(
                        xRange=(new_x_min, new_x_max),
                        padding=0
                    )

                    # 현재 범위 저장 (향후 자동 스크롤을 위해)
                    self.lock_mode_x_range = new_x_max - new_x_min
                    print(f"[차트] 저장된 위치로 차트 뷰 복원 완료 (Lock Mode ON): X축 [{new_x_min:.2f} ~ {new_x_max:.2f}], 범위: {self.lock_mode_x_range:.2f}초")

                    return  # 저장된 위치로 복원했으므로 이후 로직 스킵

                # 저장된 위치가 없고 저장된 범위가 있으면 범위만 복원 (최신 봉 정렬)
                elif self.lock_mode_x_range is not None and self.lock_mode_x_range > 10:
                    # 저장된 범위가 유효한 경우 (10초 이상): 차트 범위 복원
                    new_x_max = latest_candle_time
                    new_x_min = latest_candle_time - self.lock_mode_x_range

                    self.chart_viewbox.setRange(
                        xRange=(new_x_min, new_x_max),
                        padding=0
                    )
                    print(f"[차트] 저장된 범위로 차트 뷰 복원 완료 (최신 봉 정렬, X축 범위: {self.lock_mode_x_range:.2f}초)")

                    return  # 저장된 범위로 복원했으므로 이후 로직 스킵

                else:
                    # 저장된 범위가 없는 경우: 현재 뷰 범위 사용
                    self.lock_mode_x_range = current_range[0][1] - current_range[0][0]
                    print(f"[차트] Lock Mode 첫 실행: 현재 차트 범위 저장 (X축 범위: {self.lock_mode_x_range:.2f}초)")
                    # 계속 진행하여 스크롤 로직 실행

            # 이전 뷰의 오른쪽 끝 시간과 최신 봉 시간의 차이 계산
            time_shift = latest_candle_time - self.lock_mode_last_x_max

            # 새 봉이 없으면 (time_shift == 0) 스크롤/Y축 재계산 불필요 → 사용자 조작 유지
            if time_shift == 0:
                return

            # 새로운 X축 범위 계산: 현재 뷰를 time_shift만큼 이동 (최신 봉이 이전 봉 위치에 나타나도록)
            new_x_max = current_range[0][1] + time_shift
            new_x_min = current_range[0][0] + time_shift

            # 이전 오른쪽 끝 시간 업데이트
            self.lock_mode_last_x_max = latest_candle_time

            # X축만 스크롤 (Y축은 사용자 조작 유지)
            self.chart_viewbox.setRange(
                xRange=(new_x_min, new_x_max),
                padding=0
            )
        except Exception as e:
            print(f"Lock Mode 적용 중 오류: {e}")
            import traceback
            traceback.print_exc()

    def resizeEvent(self, event):
        if self.loading_overlay: self.loading_overlay.resize(self.tabs.size())
        super(AutoTraderGUI, self).resizeEvent(event)

    def animate_loading_text(self):
        self.loading_animation_state = (self.loading_animation_state + 1) % 3
        if self.loading_animation_state == 0: dots = "."
        elif self.loading_animation_state == 1: dots = ".."
        else: dots = "..."
        self.loading_overlay.setText(f"{self.base_loading_text}\nPlease wait{dots}")

    # --- Log 탭 관련 메서드 ---
    def initialize_log_file(self):
        """프로그램 시작 시 로그 파일 생성"""
        try:
            # logs 폴더 생성 (PyInstaller 패키징 환경 대응)
            # PyInstaller로 패키징된 경우: EXE 파일이 있는 디렉토리
            # 일반 Python 실행인 경우: 스크립트가 있는 디렉토리
            if getattr(sys, 'frozen', False):
                # PyInstaller로 패키징된 경우
                base_dir = os.path.dirname(sys.executable)
            else:
                # 일반 Python 실행
                base_dir = os.path.dirname(__file__)

            log_dir = os.path.join(base_dir, "logs")
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 파일명 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"log_{timestamp}.md"
            self.log_file_path = os.path.join(log_dir, filename)

            # 파일 생성 및 헤더 작성
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Trading Bot Log - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("---\n\n")

            print(f"로그 파일 생성: {self.log_file_path}")

        except Exception as e:
            print(f"로그 파일 생성 중 오류 발생: {e}")
            self.log_file_path = None

    @pyqtSlot(str)
    def append_log(self, message):
        """로그 메시지를 파일과 GUI에 추가 (가상화 지원)"""
        # 1. 파일에 실시간 저장
        if self.log_file_path:
            try:
                with open(self.log_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{message}\n\n")
            except Exception as e:
                # 파일 저장 실패 시 터미널에만 출력 (무한 루프 방지)
                pass

        # 2. GUI에 표시
        if not hasattr(self, 'log_list_widget'):
            return

        # 최대 로그 라인 수 확인
        try:
            max_lines = int(self.max_log_lines_input.text())
        except (ValueError, AttributeError):
            max_lines = 5000

        # 최대 라인 수를 초과하면 가장 오래된 로그만 GUI에서 삭제
        if self.log_list_widget.count() >= max_lines:
            self.log_list_widget.takeItem(0)

        # 새 로그 추가
        self.log_list_widget.addItem(message)

        # Auto Scroll 설정이 활성화되어 있으면 자동 스크롤
        if hasattr(self, 'auto_scroll_checkbox') and self.auto_scroll_checkbox.isChecked():
            self.log_list_widget.scrollToBottom()

    def clear_log(self):
        """로그 리스트 위젯 내용 지우기 (파일은 유지)"""
        if hasattr(self, 'log_list_widget'):
            self.log_list_widget.clear()
            print(f"GUI 로그가 클리어되었습니다. (파일은 유지됨: {self.log_file_path})")

    def save_dca_state(self):
        """하위 호환성 래퍼: LONG side의 DCA 상태 저장"""
        self.save_dca_state_for_side('long')

    def save_dca_state_for_side(self, side):
        """현재 DCA 상태를 config에 저장 (side별)

        Args:
            side: 'long' 또는 'short'
        """
        try:
            worker = self.auto_trade_workers.get(side)
            if not worker:
                print(f"[DCA 상태] save_dca_state_for_side({side}) - 워커 없음")
                return

            config_key = f"dca_state_{side}"
            print(f"[DCA 상태] save_dca_state_for_side({side}) 호출됨 (is_running={worker.is_running})")

            if not worker.is_running:
                # DCA가 실행 중이 아니면 저장된 상태 삭제
                if config_key in self.config_data:
                    del self.config_data[config_key]
                    config_manager.save_config_data(self.config_data)
                    print(f"[DCA 상태] [{side.upper()}] 저장된 상태 삭제 (DCA 중지됨)")
                return

            fill_history = self.fill_history_by_side.get(side, [])

            dca_state = {
                "symbol": worker.symbol,
                "side_mode": worker.side_mode,
                "current_step": worker.current_step,
                "total_steps": worker.total_steps,
                "entry_qty_list": worker.entry_qty_list,
                "hedge_qty_list": worker.hedge_qty_list,
                "hedge_trigger_prices": worker.hedge_trigger_prices,  # 헷지 트리거 가격 저장
                "category": worker.category,
                "initial_entry_done": worker.initial_entry_done,
                "next_step_orders_placed": worker.next_step_orders_placed,
                "next_step_order_id": worker.next_step_order_id,  # 주문 ID 저장
                "last_step_entry_price": worker.last_step_entry_price,  # 마지막 진입 주문 가격 저장
                "strategy_settings": self.strategy_settings,
                # 익절 관련 상태 저장
                "profit_target_price": worker.profit_target_price,
                "entry_price_at_step": worker.entry_price_at_step,
                "high_price_since_entry": worker.high_price_since_entry,  # 익절 고가 저장
                "low_price_since_entry": worker.low_price_since_entry,    # 익절 저가 저장
                # 상승 중 추가진입 임계값 저장
                "uptrend_threshold_price": worker.uptrend_threshold_price,
                "uptrend_threshold_price_2": worker.uptrend_threshold_price_2,
                # 역방향진입 진행 중 플래그 저장 (시장가 주문 대기 중)
                "is_uptrend_entry": worker.is_uptrend_entry,
                # 역방향진입 횟수 저장 (헷지 청산 비율 결정용)
                "uptrend_entry_count": worker.uptrend_entry_count,
                # 최종 단계 손실 방지 상태 저장
                "final_step_protection_placed": worker.final_step_protection_placed,
                "monitoring_final_step_closure": worker.monitoring_final_step_closure,
                # Insight 탭용 최초 진입 가격 저장
                "initial_main_entry_price": self.initial_main_entry_price_by_side.get(side),
                "initial_hedge_entry_price": self.initial_hedge_entry_price_by_side.get(side),
                # 체결 이력 저장 (차트 마커 복원용)
                "fill_history": fill_history,
                # M 주문 데이터 저장 (Insight 탭 복원용)
                "m_orders_data": self.insight_data_by_side.get(side, {}).get('m_orders', []),
                # 헷지 프로토콜 상태 저장
                "hedge_protocol_active": worker.hedge_protocol_active,
                "hedge_protocol_executed": worker.hedge_protocol_executed,
                "hedge_protocol_lowest_price": worker.hedge_protocol_lowest_price,
                "hedge_protocol_hedge_avg_price": worker.hedge_protocol_hedge_avg_price,
                "hedge_protocol_exited_qty": worker.hedge_protocol_exited_qty,
                "hedge_protocol_waiting_for_be": worker.hedge_protocol_waiting_for_be,
                # 사이클 시작 잔액 저장 (누적 손익 계산용)
                "cycle_start_balance": self.cycle_start_balance,
                # Realized PnL 복구용: 접속 시점 잔액 저장
                "start_balance": self.start_balances_by_side.get(side, 0.0),
                # 사이클 카운트 저장
                "cycle_count": self.cycles_by_side.get(side, 0),
                # side 정보 저장
                "panel_side": side
            }

            # 단계 변경 시 모든 주문 라인 제거 (새 주문 생성 시 새로 그려짐)
            # 이전 저장 단계와 현재 단계 비교
            prev_step = self.config_data.get(config_key, {}).get("current_step", -1)
            current_step = dca_state['current_step']

            if prev_step != current_step and prev_step >= 0:
                print(f"[DCA 상태] [{side.upper()}] 단계 변경 감지 (Step {prev_step+1} → {current_step+1}), 차트 주문 라인 정리")
                # 모든 주문 라인 제거 (새 단계 주문 라인은 주문 생성 시 새로 그려짐)
                self.remove_all_order_lines_from_chart()

            self.config_data[config_key] = dca_state
            config_manager.save_config_data(self.config_data)

            # 표시용 단계 계산 (1-based 표시 - 현재 체결된 단계만 표시)
            display_step = dca_state['current_step'] + 1
            print(f"[DCA 상태] [{side.upper()}] 저장 완료: {dca_state['symbol']} {dca_state['side_mode']} Step {display_step}/{dca_state['total_steps']} (current_step={worker.current_step}, next_order_placed={dca_state['next_step_orders_placed']}, order_id={dca_state['next_step_order_id']}, profit_target={dca_state['profit_target_price']}, is_uptrend_entry={dca_state['is_uptrend_entry']}, final_protection={dca_state['final_step_protection_placed']})")

        except Exception as e:
            print(f"[DCA 상태] [{side.upper()}] 저장 오류: {e}")

    def check_and_restore_dca_state(self):
        """저장된 DCA 상태 확인 및 복구 제안 (양쪽 side 독립 처리)"""
        try:
            print(f"[DCA 상태] 복구 체크 시작...")
            print(f"[DCA 상태] config_data 키 목록: {list(self.config_data.keys())}")

            # 하위 호환성: 기존 단일 dca_state 키를 dca_state_long으로 마이그레이션
            if "dca_state" in self.config_data and "dca_state_long" not in self.config_data:
                print(f"[DCA 상태] 기존 dca_state → dca_state_long 마이그레이션")
                self.config_data["dca_state_long"] = self.config_data.pop("dca_state")
                config_manager.save_config_data(self.config_data)

            # 양쪽 side 확인
            for side in ['long', 'short']:
                config_key = f"dca_state_{side}"
                dca_state = self.config_data.get(config_key)
                if not dca_state:
                    print(f"[DCA 상태] [{side.upper()}] 저장된 DCA 상태가 없습니다.")
                    continue

                symbol = dca_state.get("symbol")
                side_mode = dca_state.get("side_mode")
                current_step = dca_state.get("current_step", 0)
                total_steps = dca_state.get("total_steps", 10)
                next_step_orders_placed = dca_state.get("next_step_orders_placed", False)
                next_step_order_id = dca_state.get("next_step_order_id")

                # 해당 심볼의 포지션이 있는지 확인 (side별 데이터 사용)
                has_position = False
                position_data = self.live_position_data_by_side.get(side, {})
                print(f"[DCA 상태] [{side.upper()}] 포지션 확인 중... (symbol={symbol}, side_mode={side_mode})")
                print(f"[DCA 상태] [{side.upper()}] 현재 로드된 포지션 데이터: {list(position_data.keys())}")

                for pos in position_data.values():
                    pos_side = pos.get('side', pos.get('positionSide', ''))
                    print(f"[DCA 상태] [{side.upper()}] 포지션 체크: symbol={pos['symbol']}, side={pos_side}, amount={pos['amount']}")
                    if pos['symbol'] == symbol and pos_side == side_mode and abs(pos['amount']) > 0:
                        has_position = True
                        print(f"[DCA 상태] [{side.upper()}] 일치하는 포지션 발견!")
                        break

                if not has_position:
                    print(f"[DCA 상태] [{side.upper()}] 경고: 저장된 상태가 있지만 일치하는 포지션을 찾을 수 없습니다.")
                    print(f"[DCA 상태] [{side.upper()}] 그래도 복구를 시도합니다. (포지션이 나중에 로드될 수 있음)")

                # 표시용 단계 계산 (1-based 표시 - 현재 체결된 단계만 표시)
                display_step = current_step + 1

                # 상태 메시지 생성
                status_message = f"Step {display_step} 체결됨" if not next_step_orders_placed else f"Step {display_step} 체결, Step {display_step+1} 주문 대기 중"
                if next_step_order_id:
                    status_message += f"\n주문 ID: {next_step_order_id}"

                # 와치독 재시작 시 팝업 없이 자동 복구
                if self.auto_restore:
                    print(f"[DCA 상태] [{side.upper()}] 와치독 재시작 감지 - 자동 복구 진행 ({symbol} {side_mode} Step {display_step}/{total_steps})")
                    self.restore_dca_state(dca_state, has_position, side)
                else:
                    # 사용자에게 복구 제안
                    reply = QMessageBox.question(
                        self,
                        f"DCA 상태 복구 [{side.upper()}]",
                        f"이전 DCA 전략이 감지되었습니다 [{side.upper()} 패널]:\n\n"
                        f"심볼: {symbol}\n"
                        f"방향: {side_mode}\n"
                        f"진행 상황: {status_message}\n"
                        f"전체 단계: Step {display_step}/{total_steps}\n\n"
                        f"계속 진행하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )

                    if reply == QMessageBox.Yes:
                        self.restore_dca_state(dca_state, has_position, side)
                    else:
                        # 복구 거부 시 상태 삭제
                        del self.config_data[config_key]
                        config_manager.save_config_data(self.config_data)
                        print(f"[DCA 상태] [{side.upper()}] 복구 거부. 상태 삭제.")

        except Exception as e:
            print(f"[DCA 상태] 확인 오류: {e}")

    def check_and_restore_dca_state_for_side(self, side):
        """특정 side의 저장된 DCA 상태 확인 및 복구 제안"""
        try:
            config_key = f"dca_state_{side}"

            # 하위 호환성: 기존 단일 dca_state 키를 dca_state_long으로 마이그레이션
            if side == 'long' and "dca_state" in self.config_data and "dca_state_long" not in self.config_data:
                print(f"[DCA 상태] 기존 dca_state → dca_state_long 마이그레이션")
                self.config_data["dca_state_long"] = self.config_data.pop("dca_state")
                config_manager.save_config_data(self.config_data)

            dca_state = self.config_data.get(config_key)
            if not dca_state:
                print(f"[DCA 상태] [{side.upper()}] 저장된 DCA 상태가 없습니다.")
                return

            symbol = dca_state.get("symbol")
            side_mode = dca_state.get("side_mode")
            current_step = dca_state.get("current_step", 0)
            total_steps = dca_state.get("total_steps", 10)
            next_step_orders_placed = dca_state.get("next_step_orders_placed", False)
            next_step_order_id = dca_state.get("next_step_order_id")

            # 해당 심볼의 포지션이 있는지 확인 (side별 데이터 사용)
            has_position = False
            position_data = self.live_position_data_by_side.get(side, {})
            print(f"[DCA 상태] [{side.upper()}] 포지션 확인 중... (symbol={symbol}, side_mode={side_mode})")
            print(f"[DCA 상태] [{side.upper()}] 현재 로드된 포지션 데이터: {list(position_data.keys())}")

            for pos in position_data.values():
                pos_side = pos.get('side', pos.get('positionSide', ''))
                print(f"[DCA 상태] [{side.upper()}] 포지션 체크: symbol={pos['symbol']}, side={pos_side}, amount={pos['amount']}")
                if pos['symbol'] == symbol and pos_side == side_mode and abs(pos['amount']) > 0:
                    has_position = True
                    print(f"[DCA 상태] [{side.upper()}] 일치하는 포지션 발견!")
                    break

            if not has_position:
                print(f"[DCA 상태] [{side.upper()}] 경고: 저장된 상태가 있지만 일치하는 포지션을 찾을 수 없습니다.")
                print(f"[DCA 상태] [{side.upper()}] 그래도 복구를 시도합니다. (포지션이 나중에 로드될 수 있음)")

            # 표시용 단계 계산
            display_step = current_step + 1
            status_message = f"Step {display_step} 체결됨" if not next_step_orders_placed else f"Step {display_step} 체결, Step {display_step+1} 주문 대기 중"
            if next_step_order_id:
                status_message += f"\n주문 ID: {next_step_order_id}"

            # 와치독 재시작 시 팝업 없이 자동 복구
            if self.auto_restore:
                print(f"[DCA 상태] [{side.upper()}] 와치독 재시작 감지 - 자동 복구 진행 ({symbol} {side_mode} Step {display_step}/{total_steps})")
                self.restore_dca_state(dca_state, has_position, side)
            else:
                # 사용자에게 복구 제안
                reply = QMessageBox.question(
                    self,
                    f"DCA 상태 복구 [{side.upper()}]",
                    f"이전 DCA 전략이 감지되었습니다 [{side.upper()} 패널]:\n\n"
                    f"심볼: {symbol}\n"
                    f"방향: {side_mode}\n"
                    f"진행 상황: {status_message}\n"
                    f"전체 단계: Step {display_step}/{total_steps}\n\n"
                    f"계속 진행하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )

                if reply == QMessageBox.Yes:
                    self.restore_dca_state(dca_state, has_position, side)
                else:
                    del self.config_data[config_key]
                    config_manager.save_config_data(self.config_data)
                    print(f"[DCA 상태] [{side.upper()}] 복구 거부. 상태 삭제.")

        except Exception as e:
            print(f"[DCA 상태] [{side.upper()}] 확인 오류: {e}")
            import traceback
            traceback.print_exc()

    def restore_dca_state(self, dca_state, has_position=False, side='long'):
        """DCA 상태 복구 (side별)

        Args:
            dca_state: 복구할 DCA 상태 딕셔너리
            has_position: 현재 포지션 존재 여부
            side: 'long' 또는 'short' 패널
        """
        try:
            worker = self.auto_trade_workers.get(side)
            if not worker:
                print(f"[DCA 상태] [{side.upper()}] 워커 없음, 복구 중단")
                return

            api_module = self.api_modules.get(side)
            order_table = self.order_tables.get(side)
            position_data = self.live_position_data_by_side.get(side, {})
            live_balances = self.live_balances_by_side.get(side, {})

            print(f"[DCA 상태] [{side.upper()}] 복구 시작...")

            # 심볼 변경 (시그널 차단하여 차트가 초기화되지 않도록)
            if dca_state.get("symbol") != self.current_symbol:
                self.current_symbol = dca_state.get("symbol")
                if hasattr(self, 'symbol_combo'):
                    # 시그널 차단 (on_symbol_changed 호출 방지)
                    self.symbol_combo.blockSignals(True)
                    self.symbol_combo.setCurrentText(self.current_symbol)
                    self.symbol_combo.blockSignals(False)
                    print(f"[DCA 상태] 심볼 변경: {self.current_symbol} (차트 초기화 방지)")

            # 전략 설정 복원
            strategy_settings = dca_state.get("strategy_settings", {})
            if strategy_settings:
                self.strategy_settings = strategy_settings

            # 워커에게 상태 복구 요청
            self.on_auto_trade_log_for_side(side, "Status: <b style='color: yellow;'>Restoring DCA state...</b>|||Step: -")

            # symbol_info 조회 (get_instrument_info 사용)
            symbol_info = {}
            if api_module and hasattr(api_module, 'get_instrument_info'):
                category = getattr(api_module, '_active_category', 'linear')
                symbol_info = api_module.get_instrument_info(category, dca_state.get("symbol")) or {}
                print(f"[DCA 상태] [{side.upper()}] 심볼 정보 조회 완료: priceFilter={symbol_info.get('priceFilter', {})}, lotSizeFilter keys={list(symbol_info.get('lotSizeFilter', {}).keys())}")

            # 복구된 상태 플래그를 먼저 설정 (start_trading 호출 전)
            # 포지션이 있으면 initial_entry_done은 항상 True여야 함
            initial_entry_done_flag = True if has_position else dca_state.get("initial_entry_done", False)

            # next_step_orders_placed는 저장된 상태 또는 next_step_order_id 존재 여부로 판단
            saved_next_step_placed = dca_state.get("next_step_orders_placed", False)
            saved_order_id = dca_state.get("next_step_order_id")

            # 추가: 주문 테이블에서 미체결 주문 확인 (API open_orders가 아닌 GUI 테이블 사용)
            has_pending_order = False
            saved_order_exists = False  # config에 저장된 주문 ID가 실제로 존재하는지 확인
            found_order_id = None  # 발견된 미체결 주문 ID 저장
            symbol = dca_state.get("symbol")
            side_mode = dca_state.get("side_mode", "LONG")

            if order_table:
                order_count = order_table.rowCount()
                print(f"[DCA 상태] [{side.upper()}] 미체결 주문 확인 중... (symbol={symbol}, side_mode={side_mode}, 총 주문 수={order_count})")
                if saved_order_id:
                    print(f"[DCA 상태] Config에 저장된 주문 ID: {saved_order_id}")

                for row in range(order_count):
                    try:
                        order_symbol = order_table.item(row, 0).text() if order_table.item(row, 0) else ""
                        order_side = order_table.item(row, 2).text() if order_table.item(row, 2) else ""
                        order_id = order_table.item(row, 7).text() if order_table.item(row, 7) else ""  # 열 7 = OrderId
                        order_price = order_table.item(row, 3).text() if order_table.item(row, 3) else ""

                        # [디버깅] 모든 미체결 주문 정보 출력
                        print(f"  - Order {order_id}: symbol={order_symbol}, side={order_side}, price={order_price}")

                        # Config에 저장된 주문 ID가 실제로 존재하는지 확인
                        if saved_order_id and order_id == saved_order_id:
                            saved_order_exists = True
                            found_order_id = order_id
                            print(f"[DCA 상태] ✅ Config에 저장된 주문 ID가 미체결 주문 테이블에 존재함: {order_id}")

                        # 다음 단계 진입 주문 확인 (심볼 일치 + 주문 방향만 확인)
                        if order_symbol == symbol:
                            # LONG 모드: Buy 주문 확인
                            if side_mode == "LONG" and order_side == "Buy":
                                has_pending_order = True
                                if not found_order_id:  # 아직 주문 ID를 찾지 못했으면 저장
                                    found_order_id = order_id
                                print(f"[DCA 상태] ✅ 기존 미체결 진입 주문 발견: {order_id} (BUY @ {order_price})")
                                # break 제거 - saved_order_exists도 확인해야 함
                            # SHORT 모드: Sell 주문 확인
                            elif side_mode == "SHORT" and order_side == "Sell":
                                has_pending_order = True
                                if not found_order_id:  # 아직 주문 ID를 찾지 못했으면 저장
                                    found_order_id = order_id
                                print(f"[DCA 상태] ✅ 기존 미체결 진입 주문 발견: {order_id} (SELL @ {order_price})")
                                # break 제거 - saved_order_exists도 확인해야 함
                    except Exception as e:
                        print(f"[DCA 상태] 주문 테이블 row {row} 읽기 오류: {e}")

            # Config에 주문 ID가 저장되어 있어도 실제로 존재하지 않으면 무효 처리
            if saved_order_id and not saved_order_exists:
                print(f"[DCA 상태] ⚠️ Config에 저장된 주문 ID({saved_order_id})가 미체결 주문 테이블에 없음 (체결/취소됨)")

            # 복구 조건: 실제 주문 존재 여부를 우선하여 판단
            # Config 플래그는 참고만 하고, 실제 미체결 주문이 있으면 복구 허용

            if has_pending_order:
                # 미체결 주문이 실제로 존재하면 무조건 복구 허용
                next_step_orders_placed_flag = True

                # Config 저장된 주문 ID가 있고 실제로 존재하면 사용
                if saved_order_exists:
                    print(f"[DCA 상태] ✅ Config 저장 주문 ID 존재 + 미체결 주문 존재 → 복구 허용 (주문 ID: {found_order_id})")
                elif saved_next_step_placed:
                    # Config 플래그는 True인데 주문 ID가 다름 → 새로 발견한 주문 ID 사용
                    print(f"[DCA 상태] ✅ Config 플래그 True + 미체결 주문 존재 → 복구 허용 (새 주문 ID: {found_order_id})")
                else:
                    # Config 플래그는 False이지만 실제 주문 존재 → 복구 허용 (상태 불일치 수정)
                    print(f"[DCA 상태] ⚠️ Config 플래그 False이지만 미체결 주문 발견 → 상태 불일치 수정하여 복구 허용 (주문 ID: {found_order_id})")
            else:
                # 미체결 주문이 없음
                next_step_orders_placed_flag = False

                if saved_next_step_placed:
                    # Config는 True인데 주문이 없음 → 주문이 체결/취소됨
                    print(f"[DCA 상태] ⚠️ Config 플래그 True이지만 주문 없음 → 이미 체결/취소됨 → 복구 불가")
                else:
                    # Config도 False이고 주문도 없음 → 정상적으로 주문 없는 상태
                    print(f"[DCA 상태] ℹ️ Config 플래그 False + 주문 없음 → 정상 상태")

            print(f"[DCA 상태] 플래그 복구 설정: has_position={has_position}, initial_entry_done={initial_entry_done_flag}, next_step_orders_placed={next_step_orders_placed_flag} (saved={saved_next_step_placed}, saved_order_exists={saved_order_exists}, has_pending={has_pending_order})")

            # 익절 모니터링 모드 확인 (역방향진입 후)
            profit_target_price = dca_state.get("profit_target_price")
            is_profit_monitoring_mode = profit_target_price is not None

            # 역방향진입 진행 중 플래그 확인 (시장가 주문 대기 중)
            is_uptrend_entry = dca_state.get("is_uptrend_entry", False)

            # 포지션은 있지만 주문이 없는 경우 체크
            if has_position and not next_step_orders_placed_flag:
                # 익절 모니터링 모드면 주문 없어도 정상 (역방향진입 후 익절 대기)
                if is_profit_monitoring_mode:
                    print(f"[DCA 복구] 익절 모니터링 모드 감지 (profit_target_price={profit_target_price}) - 주문 없이 복구 허용")
                # 역방향진입 진행 중이면 주문 없어도 정상 (시장가 주문 체결 대기)
                elif is_uptrend_entry:
                    _el = "하강진입" if side == "short" else "상승진입"
                    print(f"[DCA 복구] {_el} 진행 중 감지 (is_uptrend_entry=True) - 시장가 주문 체결 대기 중으로 복구 허용")
                else:
                    # 익절 모니터링도 아니고 역방향진입 중도 아닌데 주문이 없으면 복구 실패
                    from PyQt5.QtWidgets import QMessageBox
                    msg = QMessageBox(self)
                    msg.setIcon(QMessageBox.Warning)
                    msg.setWindowTitle("DCA 복구 실패")
                    msg.setText("DCA 상태를 복구할 수 없습니다.")
                    msg.setInformativeText(
                        f"포지션은 있지만 다음 단계 진입 주문이 없습니다.\n\n"
                        f"심볼: {symbol}\n"
                        f"모드: {side_mode}\n"
                        f"현재 단계: Step {dca_state.get('current_step', 0) + 1}/{dca_state.get('total_steps', 10)}\n\n"
                        f"수동으로 주문을 생성하거나, 자동매매를 중지하고 재시작해주세요."
                    )
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()

                    print(f"[DCA 상태] [{side.upper()}] ❌ 복구 실패: 포지션은 있지만 주문이 없어 복구를 중단합니다.")

                    self.on_auto_trade_log("Status: <b style='color: red;'>Restore Failed</b>")
                    return

            # 사이클 시작 잔액 복구
            saved_cycle_start_balance = dca_state.get("cycle_start_balance", 0.0)
            if saved_cycle_start_balance > 0:
                self.cycle_start_balance = saved_cycle_start_balance
                print(f"[DCA 복구] 시작 잔액 복구: {self.cycle_start_balance}")
            else:
                # 이전 버전 호환: 저장된 값이 없으면 현재 잔액으로 설정
                category = dca_state.get("category", "linear")
                symbol = dca_state.get("symbol", "")
                if category == 'linear':
                    self.cycle_start_balance = float(live_balances.get("USDT", "0.0"))
                else:  # inverse
                    if "BTC" in symbol:
                        self.cycle_start_balance = float(live_balances.get("BTC", "0.0"))
                    elif "ETH" in symbol:
                        self.cycle_start_balance = float(live_balances.get("ETH", "0.0"))
                print(f"[DCA 복구] 시작 잔액 (현재 값 사용): {self.cycle_start_balance}")

            # Realized PnL 복구: 접속 시점 잔액 복원
            saved_start_balance = dca_state.get("start_balance", 0.0)
            if saved_start_balance > 0:
                self.start_balances_by_side[side] = saved_start_balance
                print(f"[DCA 복구] [{side.upper()}] Realized PnL 시작 잔액 복구: {saved_start_balance}")
                self.update_realized_pnl_display(side)

            # 사이클 카운트 복구
            saved_cycle_count = dca_state.get("cycle_count", 0)
            if saved_cycle_count > 0:
                self.cycles_by_side[side] = saved_cycle_count
                label = self.cycle_count_labels.get(side)
                if label:
                    prefix = "L" if side == 'long' else "S"
                    label.setText(f"{prefix}: Cycle {saved_cycle_count}")
                print(f"[DCA 복구] [{side.upper()}] 사이클 카운트 복구: {saved_cycle_count}")

            # 워커 시작 (복구된 상태로)
            worker.start_trading(
                dca_state.get("symbol"),
                0,  # entry_quantity는 복구 시 사용하지 않음 (리스트에서 가져옴)
                dca_state.get("side_mode"),
                strategy_settings,
                dca_state.get("current_step", 0),
                dca_state.get("total_steps", 10),
                dca_state.get("entry_qty_list", []),
                dca_state.get("hedge_qty_list", []),
                api_module,
                symbol_info,
                dca_state.get("category", "linear"),
                self.insight_data_by_side.get(side, {}).get('current_price', 0)  # 현재 가격
            )

            # 복구된 상태 플래그 설정 (start_trading 후 다시 설정)
            worker.initial_entry_done = initial_entry_done_flag

            # [중요] 익절 모니터링 모드면 next_step_orders_placed를 강제로 True로 설정
            # 역방향진입 후에는 다음 단계 주문이 없는 것이 정상이므로 주문 생성 스킵
            if is_profit_monitoring_mode:
                worker.next_step_orders_placed = True
                print(f"[DCA 상태] 익절 모니터링 모드 - next_step_orders_placed 강제 True 설정 (주문 생성 방지)")
            # 역방향진입 진행 중이면 next_step_orders_placed를 True로 설정 (시장가 주문 체결 대기)
            elif is_uptrend_entry:
                worker.next_step_orders_placed = True
                _el = "하강진입" if side == "short" else "상승진입"
                print(f"[DCA 상태] {_el} 진행 중 - next_step_orders_placed 강제 True 설정 (시장가 주문 체결 대기)")
            else:
                worker.next_step_orders_placed = next_step_orders_placed_flag

            print(f"[DCA 상태] [{side.upper()}] 플래그 복구 완료: initial_entry_done={initial_entry_done_flag}, next_step_orders_placed={worker.next_step_orders_placed}")

            # 다음 단계 주문 ID 복원
            # 우선순위: 1) Config에 저장된 주문 ID (존재하는 경우), 2) GUI 테이블에서 발견한 주문 ID
            next_step_order_id = None

            if saved_order_exists and found_order_id:
                # Config에 저장된 주문 ID가 실제로 존재하면 사용
                next_step_order_id = found_order_id
                print(f"[DCA 상태] Config 저장 주문 ID 사용: {next_step_order_id}")
            elif has_pending_order and found_order_id:
                # Config에 저장된 주문 ID가 없지만 GUI 테이블에서 발견한 주문 ID 사용
                next_step_order_id = found_order_id
                print(f"[DCA 상태] GUI 테이블에서 발견한 주문 ID 사용: {next_step_order_id}")

            if next_step_order_id:
                worker.next_step_order_id = next_step_order_id
                print(f"[DCA 상태] 다음 단계 주문 ID 복원 완료: {next_step_order_id}")

            # 마지막 진입 주문 가격 복원
            last_step_entry_price = dca_state.get("last_step_entry_price")
            if last_step_entry_price is not None:
                worker.last_step_entry_price = last_step_entry_price
                print(f"[DCA 상태] 마지막 진입 주문 가격 복원: ${self.fmt_price(last_step_entry_price)}")

            # 헷지 트리거 가격 복원
            hedge_trigger_prices = dca_state.get("hedge_trigger_prices", [])
            if hedge_trigger_prices:
                worker.hedge_trigger_prices = hedge_trigger_prices
                print(f"[DCA 상태] 헷지 트리거 가격 복원: {len(hedge_trigger_prices)}개")
                # 차트에 마커 표시
                self.draw_hedge_trigger_markers_for_side(side, hedge_trigger_prices, dca_state.get("side_mode"), dca_state.get("current_step", 0))
                # Insight 탭 업데이트
                self.update_insight_hedge_triggers(side, hedge_trigger_prices, dca_state.get("side_mode"), dca_state.get("current_step", 0))

            # 익절 관련 상태 복원
            profit_target_price = dca_state.get("profit_target_price")
            if profit_target_price is not None:
                worker.profit_target_price = profit_target_price
                print(f"[DCA 상태] 익절 트리거 가격 복원: ${profit_target_price}")
                # 차트에 마커 표시
                self.draw_profit_target_marker_for_side(side, profit_target_price)
                # 익절 모드에서는 H 트리거 마커 제거
                self.remove_hedge_trigger_markers_for_side(side)
                # Insight 탭 업데이트
                self.update_insight_profit_target(side, profit_target_price, dca_state.get("current_step", 0))

            entry_price_at_step = dca_state.get("entry_price_at_step")
            if entry_price_at_step is not None:
                worker.entry_price_at_step = entry_price_at_step
                print(f"[DCA 상태] 추가진입 시점 가격 복원: ${entry_price_at_step}")

            # 익절 모니터링 모드면 고가/저가 복원 (저장된 값이 있으면 사용, 없으면 entry_price_at_step으로 초기화)
            if profit_target_price is not None:
                high_price_since_entry = dca_state.get("high_price_since_entry")
                low_price_since_entry = dca_state.get("low_price_since_entry")

                if high_price_since_entry is not None and low_price_since_entry is not None:
                    # 저장된 고가/저가 복원
                    worker.high_price_since_entry = high_price_since_entry
                    worker.low_price_since_entry = low_price_since_entry
                    print(f"[DCA 복구] 익절 고가/저가 복원: High={high_price_since_entry}, Low={low_price_since_entry}")
                elif entry_price_at_step is not None:
                    # 저장된 값이 없으면 진입가로 초기화 (하위 호환성)
                    worker.high_price_since_entry = entry_price_at_step
                    worker.low_price_since_entry = entry_price_at_step
                    print(f"[DCA 복구] 익절 고가/저가 초기화 (저장값 없음): High={entry_price_at_step}, Low={entry_price_at_step}")

            # 상승 중 추가진입 임계값 복원
            uptrend_threshold_price = dca_state.get("uptrend_threshold_price")
            if uptrend_threshold_price is not None:
                worker.uptrend_threshold_price = uptrend_threshold_price
                _el = "하강진입" if side == "short" else "상승진입"
                print(f"[DCA 상태] {_el} 임계값 복원: ${uptrend_threshold_price}")
                # 차트에 마커 표시
                self.draw_uptrend_threshold_marker_for_side(side, uptrend_threshold_price)
                # Insight 탭 업데이트
                self.update_insight_uptrend_threshold(side, uptrend_threshold_price)
            else:
                # 임계값이 null이면 재계산 트리거 (포지션이 있는 경우)
                if has_position or dca_state.get("initial_entry_done"):
                    worker.step_filled_need_threshold_recalc = True
                    print(f"[DCA 상태] [{side.upper()}] 임계값이 null → 재계산 플래그 설정")

            # 상승 중 추가진입 2차 임계값 복원
            uptrend_threshold_price_2 = dca_state.get("uptrend_threshold_price_2")
            if uptrend_threshold_price_2 is not None:
                worker.uptrend_threshold_price_2 = uptrend_threshold_price_2
                print(f"[DCA 상태] {_el} 2차 임계값 복원: ${uptrend_threshold_price_2}")
                # 차트에 마커 표시
                self.draw_uptrend_threshold_2_marker_for_side(side, uptrend_threshold_price_2)
                # Insight 탭 업데이트
                self.update_insight_uptrend_threshold_2(side, uptrend_threshold_price_2)

            # 역방향진입 진행 중 플래그 복원
            if is_uptrend_entry:
                worker.is_uptrend_entry = True
                print(f"[DCA 상태] {_el} 진행 중 플래그 복원: is_uptrend_entry=True (시장가 주문 체결 대기 중)")

            # 역방향진입 횟수 복원 (헷지 청산 비율 결정용)
            uptrend_entry_count = dca_state.get("uptrend_entry_count", 0)
            if uptrend_entry_count > 0:
                worker.uptrend_entry_count = uptrend_entry_count
                print(f"[DCA 상태] {_el} 횟수 복원: {uptrend_entry_count}회")

            # 최종 단계 손실 방지 상태 복원
            final_step_protection_placed = dca_state.get("final_step_protection_placed", False)
            monitoring_final_step_closure = dca_state.get("monitoring_final_step_closure", False)
            if final_step_protection_placed or monitoring_final_step_closure:
                worker.final_step_protection_placed = final_step_protection_placed
                worker.monitoring_final_step_closure = monitoring_final_step_closure
                print(f"[DCA 상태] 최종 단계 보호 상태 복원: placed={final_step_protection_placed}, monitoring={monitoring_final_step_closure}")

            # 헷지 프로토콜 상태 복원
            hedge_protocol_active = dca_state.get("hedge_protocol_active", False)
            hedge_protocol_executed = dca_state.get("hedge_protocol_executed", False)
            hedge_protocol_lowest_price = dca_state.get("hedge_protocol_lowest_price")
            hedge_protocol_hedge_avg_price = dca_state.get("hedge_protocol_hedge_avg_price")
            hedge_protocol_exited_qty = dca_state.get("hedge_protocol_exited_qty", 0)
            hedge_protocol_waiting_for_be = dca_state.get("hedge_protocol_waiting_for_be", False)

            if hedge_protocol_active or hedge_protocol_executed:
                worker.hedge_protocol_active = hedge_protocol_active
                worker.hedge_protocol_executed = hedge_protocol_executed
                worker.hedge_protocol_exited_qty = hedge_protocol_exited_qty
                worker.hedge_protocol_waiting_for_be = hedge_protocol_waiting_for_be
                print(f"[DCA 상태] 헷지 프로토콜 상태 복원: active={hedge_protocol_active}, executed={hedge_protocol_executed}, exited_qty={hedge_protocol_exited_qty}")

                if hedge_protocol_lowest_price is not None:
                    worker.hedge_protocol_lowest_price = hedge_protocol_lowest_price
                    print(f"[DCA 상태] 헷지 프로토콜 최저가 복원: ${hedge_protocol_lowest_price}")

                if hedge_protocol_hedge_avg_price is not None:
                    worker.hedge_protocol_hedge_avg_price = hedge_protocol_hedge_avg_price
                    print(f"[DCA 상태] 헷지 프로토콜 평균가 복원: ${hedge_protocol_hedge_avg_price}")

            # 표시용 단계 계산 (1-based 표시 - 현재 체결된 단계만 표시)
            display_step = dca_state.get('current_step') + 1
            print(f"[DCA 상태] 복구 완료: Step {display_step}/{dca_state.get('total_steps')}")

            # 상태 메시지 업데이트 (복구된 실제 단계로)
            log_color = "green" if dca_state.get("side_mode") == "LONG" else "red"
            if dca_state.get('next_step_orders_placed'):
                # 주문 대기 중
                worker.log_message.emit(f"Status: <b style='color: {log_color};'>Waiting for Step {display_step+1}</b>|||Step: <b>{display_step}/{dca_state.get('total_steps')}</b>")
            else:
                # 체결 완료
                worker.log_message.emit(f"Status: <b style='color: {log_color};'>DCA Running</b>|||Step: <b>{display_step}/{dca_state.get('total_steps')}</b>")

            # Start 버튼을 Stop 상태로 변경
            self._set_side_button_running(side)

            # Insight 탭의 포지션 정보 복원 (live_position_data 또는 API에서 가져오기)
            symbol = dca_state.get("symbol")
            side_mode = dca_state.get("side_mode")
            position_side = "LONG" if side_mode == "LONG" else "SHORT"
            hedge_position_side = "SHORT" if side_mode == "LONG" else "LONG"

            # Main Position 업데이트
            main_position_key = f"{symbol}_{position_side}"
            main_position_found = False

            if main_position_key in position_data:
                # position_data에 있으면 바로 사용
                main_pos = position_data[main_position_key]
                amount = abs(float(main_pos.get('amount', 0)))
                avg_entry = float(main_pos.get('entry', 0))
                pnl = float(main_pos.get('pnl', 0))

                if amount > 0:
                    self.initial_main_entry_price_by_side[side] = dca_state.get('initial_main_entry_price', avg_entry)
                    self.update_insight_main_position(side, self.initial_main_entry_price_by_side[side], amount, avg_entry, pnl)
                    print(f"[DCA 복구] Main Position Insight 업데이트 완료 (live_position_data) (최초: ${self.fmt_price(self.initial_main_entry_price_by_side[side])}, 수량: {amount}, 평균: ${self.fmt_price(avg_entry)}, PNL: ${pnl:.2f})")
                    main_position_found = True

            # live_position_data에 없으면 API로 직접 조회
            if not main_position_found and api_module and hasattr(api_module, 'get_initial_positions'):
                try:
                    print(f"[DCA 복구] [{side.upper()}] position_data에 Main Position 없음. API로 조회 중...")
                    positions = api_module.get_initial_positions()
                    for p in positions:
                        if p.get('symbol') == symbol:
                            p_side = p.get('positionSide')
                            if not p_side or p_side == 'BOTH':
                                p_side = 'LONG' if float(p.get('positionAmt', 0)) > 0 else 'SHORT'

                            if p_side == position_side:
                                amount = abs(float(p.get('positionAmt', 0)))
                                avg_entry = float(p.get('entryPrice', 0))
                                pnl = float(p.get('unRealizedProfit', 0))

                                if amount > 0:
                                    self.initial_main_entry_price_by_side[side] = dca_state.get('initial_main_entry_price', avg_entry)
                                    self.update_insight_main_position(side, self.initial_main_entry_price_by_side[side], amount, avg_entry, pnl)
                                    print(f"[DCA 복구] Main Position Insight 업데이트 완료 (API) (최초: ${self.fmt_price(self.initial_main_entry_price_by_side[side])}, 수량: {amount}, 평균: ${self.fmt_price(avg_entry)}, PNL: ${pnl:.2f})")
                                    main_position_found = True
                                break
                except Exception as e:
                    print(f"[DCA 복구] API로 Main Position 조회 오류: {e}")

            # Hedge Position 업데이트
            hedge_position_key = f"{symbol}_{hedge_position_side}"
            hedge_position_found = False

            if hedge_position_key in position_data:
                # position_data에 있으면 바로 사용
                hedge_pos = position_data[hedge_position_key]
                amount = abs(float(hedge_pos.get('amount', 0)))
                avg_entry = float(hedge_pos.get('entry', 0))
                pnl = float(hedge_pos.get('pnl', 0))

                if amount > 0:
                    self.initial_hedge_entry_price_by_side[side] = dca_state.get('initial_hedge_entry_price', avg_entry)
                    self.update_insight_hedge_position(side, self.initial_hedge_entry_price_by_side[side], amount, avg_entry, pnl)
                    print(f"[DCA 복구] Hedge Position Insight 업데이트 완료 (live_position_data) (최초: ${self.fmt_price(self.initial_hedge_entry_price_by_side[side])}, 수량: {amount}, 평균: ${self.fmt_price(avg_entry)}, PNL: ${pnl:.2f})")
                    hedge_position_found = True

            # live_position_data에 없으면 API로 직접 조회
            if not hedge_position_found and api_module and hasattr(api_module, 'get_initial_positions'):
                try:
                    print(f"[DCA 복구] [{side.upper()}] position_data에 Hedge Position 없음. API로 조회 중...")
                    positions = api_module.get_initial_positions()
                    for p in positions:
                        if p.get('symbol') == symbol:
                            p_side = p.get('positionSide')
                            if not p_side or p_side == 'BOTH':
                                p_side = 'LONG' if float(p.get('positionAmt', 0)) > 0 else 'SHORT'

                            if p_side == hedge_position_side:
                                amount = abs(float(p.get('positionAmt', 0)))
                                avg_entry = float(p.get('entryPrice', 0))
                                pnl = float(p.get('unRealizedProfit', 0))

                                if amount > 0:
                                    self.initial_hedge_entry_price_by_side[side] = dca_state.get('initial_hedge_entry_price', avg_entry)
                                    self.update_insight_hedge_position(side, self.initial_hedge_entry_price_by_side[side], amount, avg_entry, pnl)
                                    print(f"[DCA 복구] Hedge Position Insight 업데이트 완료 (API) (최초: ${self.fmt_price(self.initial_hedge_entry_price_by_side[side])}, 수량: {amount}, 평균: ${self.fmt_price(avg_entry)}, PNL: ${pnl:.2f})")
                                    hedge_position_found = True
                                break
                except Exception as e:
                    print(f"[DCA 복구] API로 Hedge Position 조회 오류: {e}")

            # M 주문 복원 (저장된 데이터 우선, 없으면 주문 테이블에서 M4만 재구성)
            saved_m_orders = dca_state.get("m_orders_data", [])
            if saved_m_orders:
                self.update_insight_m_orders(side, saved_m_orders)
                print(f"[DCA 복구] NSO Insight 복원 완료")
            elif next_step_order_id and order_table:
                for row in range(order_table.rowCount()):
                    try:
                        order_id = order_table.item(row, 7).text() if order_table.item(row, 7) else ""
                        if order_id == next_step_order_id:
                            nso_price = float(order_table.item(row, 3).text()) if order_table.item(row, 3) else 0
                            nso_qty = float(order_table.item(row, 4).text()) if order_table.item(row, 4) else 0
                            m_orders = [
                                {'price': nso_price, 'qty': nso_qty, 'status': 'Waiting', 'slippage': 0}
                            ]
                            self.update_insight_m_orders(side, m_orders)
                            print(f"[DCA 복구] NSO Insight (폴백): ${nso_price} x {nso_qty}")
                            break
                    except Exception as e:
                        print(f"[DCA 복구] NSO 업데이트 오류: {e}")

            # 체결 이력 복원 (차트 마커 복원용)
            fill_history = dca_state.get("fill_history", [])
            if fill_history:
                self.fill_history_by_side[side] = fill_history
                print(f"[DCA 복구] 체결 이력 복원: {len(fill_history)}개 체결 기록")
            else:
                print(f"[DCA 복구] 저장된 체결 이력 없음")

        except Exception as e:
            print(f"[DCA 상태] [{side.upper()}] 복구 오류: {e}")
            import traceback
            traceback.print_exc()
            self.on_auto_trade_log_for_side(side, f"Status: <b style='color: red;'>Restore Failed: {e}</b>|||Step: -")

    # ==================== Insight 탭 업데이트 함수 (Split View: side별) ====================

    def _iw(self, side):
        """Insight 위젯 딕셔너리 단축 접근"""
        return self.insight_widgets[side]

    def update_insight_main_position(self, side, entry_price, quantity, avg_price, unrealized_pnl):
        """주 포지션 정보 업데이트"""
        try:
            self.insight_data_by_side[side]['main_position'] = {
                'entry_price': entry_price, 'quantity': quantity,
                'avg_price': avg_price, 'unrealized_pnl': unrealized_pnl
            }
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            w['main_entry_price'].setText(f"${self.fmt_price(entry_price)}" if entry_price else "N/A")
            w['main_quantity'].setText(f"{quantity:.4f}" if quantity else "N/A")
            w['main_avg_price'].setText(f"${self.fmt_price(avg_price)}" if avg_price else "N/A")
            if unrealized_pnl is not None:
                color = "green" if unrealized_pnl >= 0 else "red"
                w['main_unrealized_pnl'].setText(f"<span style='color: {color};'>${unrealized_pnl:.4f}</span>")
            else:
                w['main_unrealized_pnl'].setText("N/A")
        except Exception as e:
            print(f"[Insight] 주 포지션 업데이트 오류 ({side}): {e}")

    def update_insight_hedge_position(self, side, entry_price, quantity, avg_price, unrealized_pnl):
        """헷지 포지션 정보 업데이트"""
        try:
            self.insight_data_by_side[side]['hedge_position'] = {
                'entry_price': entry_price, 'quantity': quantity,
                'avg_price': avg_price, 'unrealized_pnl': unrealized_pnl
            }
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            w['hedge_entry_price'].setText(f"${self.fmt_price(entry_price)}" if entry_price else "N/A")
            w['hedge_quantity'].setText(f"{quantity:.4f}" if quantity else "N/A")
            w['hedge_avg_price'].setText(f"${self.fmt_price(avg_price)}" if avg_price else "N/A")
            if unrealized_pnl is not None:
                color = "green" if unrealized_pnl >= 0 else "red"
                w['hedge_unrealized_pnl'].setText(f"<span style='color: {color};'>${unrealized_pnl:.4f}</span>")
            else:
                w['hedge_unrealized_pnl'].setText("N/A")
        except Exception as e:
            print(f"[Insight] 헷지 포지션 업데이트 오류 ({side}): {e}")

    def update_insight_m_orders(self, side, m_orders_data):
        """NSO(Next Step Order) 정보 업데이트"""
        try:
            self.insight_data_by_side[side]['m_orders'] = m_orders_data
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            m_labels = self._iw(side)['m_order_labels']
            if len(m_orders_data) >= 1 and len(m_labels) >= 1:
                order = m_orders_data[0]
                price = order.get('price', 0)
                qty = order.get('qty', 0)
                status = order.get('status', 'Waiting')
                slippage = order.get('slippage', 0)
                m_labels[0]['price'].setText(f"${self.fmt_price(price)}" if price else "N/A")
                m_labels[0]['qty'].setText(f"{qty:.4f}" if qty else "N/A")
                if slippage != 0:
                    sc = "red" if slippage < 0 else "green"
                    m_labels[0]['slippage'].setText(f"<span style='color: {sc};'>${slippage:+.2f}</span>")
                else:
                    m_labels[0]['slippage'].setText("N/A")
                sc2 = "orange" if status == "Waiting" else "green" if status == "Filled" else "gray"
                m_labels[0]['status'].setText(f"<span style='color: {sc2};'>{status}</span>")
            else:
                if len(m_labels) >= 1:
                    for k in ['price', 'qty', 'slippage', 'status']:
                        m_labels[0][k].setText("N/A")
        except Exception as e:
            print(f"[Insight] NSO 업데이트 오류 ({side}): {e}")

    def update_insight_hedge_triggers(self, side, hedge_triggers, side_mode, current_step):
        """헷지 트리거 정보 업데이트"""
        try:
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            h_labels = self._iw(side)['hedge_labels']
            data = self.insight_data_by_side[side]
            for i in range(4):
                if i < len(hedge_triggers):
                    trigger = hedge_triggers[i]
                    tp, tq = trigger[0], trigger[1]
                    executed = trigger[2] if len(trigger) > 2 else False
                    h_labels[i]['price'].setText(f"${self.fmt_price(tp)}" if tp else "N/A")
                    h_labels[i]['qty'].setText(f"{tq:.4f}" if tq else "N/A")
                    if executed:
                        h_labels[i]['status'].setText("<span style='color: green;'>✅ 체결됨</span>")
                        prev = data.get('hedge_triggers', [{}] * 4)
                        if isinstance(prev, list) and i < len(prev) and prev[i].get('slippage', 'N/A') != 'N/A':
                            continue
                    else:
                        h_labels[i]['status'].setText("<span style='color: orange;'>⏳ 대기 중</span>")
                    h_labels[i]['slippage'].setText("N/A")
                else:
                    for k in ['price', 'qty', 'status', 'slippage']:
                        h_labels[i][k].setText("N/A")
            if not isinstance(data.get('hedge_triggers'), list):
                data['hedge_triggers'] = [{} for _ in range(4)]
            for i in range(min(4, len(hedge_triggers))):
                t = hedge_triggers[i]
                executed = t[2] if len(t) > 2 else False
                if i < len(data['hedge_triggers']):
                    entry = {'price': t[0], 'qty': t[1], 'executed': executed}
                    if not executed:
                        data['hedge_triggers'][i].pop('slippage', None)
                    data['hedge_triggers'][i].update(entry)
        except Exception as e:
            print(f"[Insight] 헷지 트리거 업데이트 오류 ({side}): {e}")

    def update_insight_hedge_slippage(self, side, trigger_index, slippage):
        """헷지 트리거 슬리피지 업데이트"""
        try:
            if 0 <= trigger_index < 4:
                w = self._iw(side)
                data = self.insight_data_by_side[side]
                sc = "red" if slippage < 0 else "green"
                tp = data.get('hedge_triggers', [{}] * 4)[trigger_index].get('price', 0)
                sp = (slippage / tp * 100) if tp else 0
                w['hedge_labels'][trigger_index]['slippage'].setText(
                    f"<span style='color: {sc};'>${slippage:+.2f} ({sp:+.3f}%)</span>"
                )
                if isinstance(data.get('hedge_triggers'), list) and trigger_index < len(data['hedge_triggers']):
                    data['hedge_triggers'][trigger_index]['slippage'] = slippage
        except Exception as e:
            print(f"[Insight] 헷지 슬리피지 업데이트 오류 ({side}): {e}")

    def update_insight_profit_target(self, side, profit_target_price, current_step=0):
        """익절 트리거 정보 업데이트"""
        try:
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            data = self.insight_data_by_side[side]
            w['profit_target_price'].setText(f"${self.fmt_price(profit_target_price)}" if profit_target_price else "N/A")
            current_price = data.get('current_price', 0)
            if current_price > 0 and profit_target_price:
                distance = abs(current_price - profit_target_price)
                dp = (distance / profit_target_price) * 100
                w['profit_distance'].setText(f"${self.fmt_price(distance)} ({dp:.2f}%)")
                sm = self.auto_trade_workers[side].side_mode if side in self.auto_trade_workers else 'LONG'
                reached = (current_price >= profit_target_price) if sm == "LONG" else (current_price <= profit_target_price)
                if reached:
                    w['profit_target_status'].setText("<span style='color: green;'>🎯 익절가 도달!</span>")
                else:
                    w['profit_target_status'].setText("<span style='color: orange;'>⏳ 모니터링 중</span>")
            else:
                w['profit_target_status'].setText("N/A")
            data['profit_target'] = {'price': profit_target_price, 'current_step': current_step}
        except Exception as e:
            print(f"[Insight] 익절 트리거 업데이트 오류 ({side}): {e}")

    def update_insight_uptrend_threshold(self, side, threshold_price):
        """역방향진입 임계값 정보 업데이트"""
        try:
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            data = self.insight_data_by_side[side]
            w['uptrend_threshold_price'].setText(f"${self.fmt_price(threshold_price)}" if threshold_price else "N/A")
            current_price = data.get('current_price', 0)
            if current_price > 0 and threshold_price:
                distance = abs(current_price - threshold_price)
                dp = (distance / threshold_price) * 100
                w['uptrend_distance'].setText(f"${self.fmt_price(distance)} ({dp:.2f}%)")
                sm = self.auto_trade_workers[side].side_mode if side in self.auto_trade_workers else 'LONG'
                if sm == "LONG":
                    if current_price >= threshold_price:
                        w['uptrend_status'].setText("<span style='color: green;'>✅ 임계값 초과</span>")
                    else:
                        w['uptrend_status'].setText("<span style='color: orange;'>⏳ 임계값 미만</span>")
                else:
                    if current_price <= threshold_price:
                        w['uptrend_status'].setText("<span style='color: green;'>✅ 임계값 이하</span>")
                    else:
                        w['uptrend_status'].setText("<span style='color: orange;'>⏳ 임계값 초과</span>")
            else:
                w['uptrend_status'].setText("N/A")
            data['uptrend_threshold'] = {'price': threshold_price}
        except Exception as e:
            print(f"[Insight] 역방향진입 임계값 업데이트 오류 ({side}): {e}")

    def update_insight_uptrend_threshold_2(self, side, threshold_price_2):
        """역방향진입 2차 임계값 정보 업데이트"""
        try:
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            data = self.insight_data_by_side[side]
            w['uptrend_threshold_price_2'].setText(f"${self.fmt_price(threshold_price_2)}" if threshold_price_2 else "N/A")
            current_price = data.get('current_price', 0)
            if current_price > 0 and threshold_price_2:
                distance = abs(current_price - threshold_price_2)
                dp = (distance / threshold_price_2) * 100
                w['uptrend_distance_2'].setText(f"${self.fmt_price(distance)} ({dp:.2f}%)")
                sm = self.auto_trade_workers[side].side_mode if side in self.auto_trade_workers else 'LONG'
                if sm == "LONG":
                    triggered = current_price >= threshold_price_2
                else:
                    triggered = current_price <= threshold_price_2
                if triggered:
                    w['uptrend_status_2'].setText("<span style='color: red;'>🚀 즉시 진입 발동!</span>")
                else:
                    w['uptrend_status_2'].setText("<span style='color: gray;'>⏳ 대기 중</span>")
            else:
                w['uptrend_status_2'].setText("N/A")
            data['uptrend_threshold_2'] = {'price': threshold_price_2}
        except Exception as e:
            print(f"[Insight] 역방향진입 2차 임계값 업데이트 오류 ({side}): {e}")

    def update_hedge_liquidation_warning(self, side, hedge_liq_price, break_even_price, warning_level):
        """헷지 긴급 탈출 라인 업데이트"""
        try:
            if self.current_insight_snapshot_by_side[side] is not None:
                return
            w = self._iw(side)
            sp = side[0].upper()
            if warning_level == "EMERGENCY_LINE_SET":
                w['hedge_liq_price'].setText(f"${self.fmt_price(hedge_liq_price)}")
                distance = abs(hedge_liq_price - break_even_price)
                dp = (distance / break_even_price) * 100
                w['hedge_liq_distance'].setText(f"${self.fmt_price(distance)} ({dp:.2f}%)")
                w['hedge_liq_status'].setText("<span style='color: orange;'>⚠️ 긴급 탈출 라인 설정됨</span>")
                self.append_log(f"[{sp}][헷지 보호] 긴급 탈출 라인 생성 (BE: ${self.fmt_price(break_even_price)}, 청산가: ${self.fmt_price(hedge_liq_price)})")
            elif warning_level == "STAGE1_EXECUTED":
                w['hedge_liq_status'].setText("<span style='color: orange;'>⚠️ 1단계: 헷지 1/3 청산</span>")
                self.append_log(f"[{sp}][헷지 보호] 1단계 긴급 탈출 (${self.fmt_price(break_even_price)})")
            elif warning_level == "STAGE2_EXECUTED":
                w['hedge_liq_status'].setText("<span style='color: red;'>🔴 2단계: 헷지 2/3 청산</span>")
                self.append_log(f"[{sp}][헷지 보호] 2단계 긴급 탈출 (${self.fmt_price(break_even_price)})")
            elif warning_level == "STAGE3_EXECUTED":
                w['hedge_liq_price'].setText("N/A")
                w['hedge_liq_distance'].setText("N/A")
                w['hedge_liq_status'].setText("<span style='color: red;'>🚨 3단계: 전체 청산!</span>")
                self.append_log(f"[{sp}][헷지 보호] 3단계 최종 탈출 (${self.fmt_price(break_even_price)})")
        except Exception as e:
            print(f"[Insight] 헷지 긴급 탈출 업데이트 오류 ({side}): {e}")

    def update_insight_current_price(self, side, current_price):
        """현재가 업데이트"""
        try:
            self.insight_data_by_side[side]['current_price'] = current_price
            precision = self.detected_precision if self.detected_precision is not None else 4
            self._iw(side)['current_price'].setText(f"{current_price:.{precision}f}")
        except Exception as e:
            print(f"[Insight] 현재가 업데이트 오류 ({side}): {e}")

    def save_insight_snapshot(self, side, step_number):
        """현재 Insight 상태를 스냅샷으로 저장"""
        try:
            w = self._iw(side)
            snapshot = {
                'step': step_number,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'main_position': {k: w[f'main_{k}'].text() for k in ['entry_price', 'quantity', 'avg_price', 'unrealized_pnl']},
                'hedge_position': {k: w[f'hedge_{k}'].text() for k in ['entry_price', 'quantity', 'avg_price', 'unrealized_pnl']},
                'm_orders': [
                    {k: l[k].text() for k in ['price', 'qty', 'slippage', 'status']}
                    for l in w['m_order_labels']
                ],
                'hedge_triggers': [
                    {k: l[k].text() for k in ['price', 'qty', 'status', 'slippage']}
                    for l in w['hedge_labels']
                ],
                'profit_target': {
                    'price': w['profit_target_price'].text(),
                    'status': w['profit_target_status'].text(),
                    'distance': w['profit_distance'].text()
                },
                'uptrend_threshold': {
                    'price': w['uptrend_threshold_price'].text(),
                    'distance': w['uptrend_distance'].text(),
                    'status': w['uptrend_status'].text(),
                    'price_2': w['uptrend_threshold_price_2'].text(),
                    'distance_2': w['uptrend_distance_2'].text(),
                    'status_2': w['uptrend_status_2'].text()
                },
                'current_price': w['current_price'].text()
            }
            self.insight_history_by_side[side].append(snapshot)
            self.update_insight_history_dropdown(side)
            print(f"[Insight] [{side.upper()}] Step {step_number + 1} 스냅샷 저장")
        except Exception as e:
            print(f"[Insight] 스냅샷 저장 오류 ({side}): {e}")

    def update_insight_history_dropdown(self, side):
        """히스토리 드롭다운 업데이트"""
        try:
            combo = self._iw(side)['history_combo']
            combo.blockSignals(True)
            ci = combo.currentIndex()
            combo.clear()
            combo.addItem("📊 Current (Live)")
            for s in reversed(self.insight_history_by_side[side]):
                combo.addItem(f"📸 Step {s['step'] + 1} ({s['timestamp']})")
            if ci == 0 or ci >= combo.count():
                combo.setCurrentIndex(0)
            else:
                combo.setCurrentIndex(ci)
            combo.blockSignals(False)
        except Exception as e:
            print(f"[Insight] 드롭다운 업데이트 오류 ({side}): {e}")

    def on_insight_history_changed(self, side, index):
        """히스토리 드롭다운 선택 변경"""
        try:
            if index == 0:
                self.current_insight_snapshot_by_side[side] = None
                self.refresh_insight_to_current(side)
            else:
                history = self.insight_history_by_side[side]
                hi = len(history) - index
                if 0 <= hi < len(history):
                    self.load_insight_snapshot(side, history[hi])
        except Exception as e:
            print(f"[Insight] 선택 변경 오류 ({side}): {e}")

    def load_insight_snapshot(self, side, snapshot):
        """스냅샷을 Insight 탭에 로드"""
        try:
            self.current_insight_snapshot_by_side[side] = snapshot
            w = self._iw(side)
            total_steps = self.strategy_settings.get("STEPS", 10)
            w['current_step'].setText(f"{snapshot['step'] + 1}/{total_steps}")
            for k in ['entry_price', 'quantity', 'avg_price', 'unrealized_pnl']:
                w[f'main_{k}'].setText(snapshot['main_position'][k])
                w[f'hedge_{k}'].setText(snapshot['hedge_position'][k])
            if 'm_orders' in snapshot:
                for i, mo in enumerate(snapshot['m_orders']):
                    if i < len(w['m_order_labels']):
                        for k in ['price', 'qty', 'slippage', 'status']:
                            w['m_order_labels'][i][k].setText(mo[k])
            for i, ht in enumerate(snapshot['hedge_triggers']):
                if i < len(w['hedge_labels']):
                    for k in ['price', 'qty', 'status', 'slippage']:
                        w['hedge_labels'][i][k].setText(ht[k])
            w['profit_target_price'].setText(snapshot['profit_target']['price'])
            w['profit_target_status'].setText(snapshot['profit_target']['status'])
            w['profit_distance'].setText(snapshot['profit_target']['distance'])
            ut = snapshot['uptrend_threshold']
            for k in ['price', 'distance', 'status']:
                w[f'uptrend_threshold_{k}' if k == 'price' else f'uptrend_{k}'].setText(ut[k])
            w['uptrend_threshold_price_2'].setText(ut['price_2'])
            w['uptrend_distance_2'].setText(ut['distance_2'])
            w['uptrend_status_2'].setText(ut['status_2'])
            w['current_price'].setText(snapshot['current_price'])
        except Exception as e:
            print(f"[Insight] 스냅샷 로드 오류 ({side}): {e}")

    def reset_insight_tab(self, side=None):
        """Insight 탭 초기화 (side=None이면 양쪽)"""
        sides = [side] if side else ['long', 'short']
        for s in sides:
            try:
                w = self._iw(s)
                self.insight_history_by_side[s].clear()
                self.current_insight_snapshot_by_side[s] = None
                combo = w['history_combo']
                combo.blockSignals(True)
                combo.clear()
                combo.addItem("📊 Current (Live)")
                combo.blockSignals(False)
                total_steps = self.strategy_settings.get("STEPS", 10)
                w['current_step'].setText(f"0/{total_steps}")
                w['current_price'].setText("0.00")
                for k in ['profit_target_price', 'profit_target_status', 'profit_distance',
                           'uptrend_threshold_price', 'uptrend_distance', 'uptrend_status',
                           'uptrend_threshold_price_2', 'uptrend_distance_2', 'uptrend_status_2',
                           'hedge_liq_price', 'hedge_liq_distance', 'hedge_liq_status',
                           'main_entry_price', 'main_quantity', 'main_avg_price', 'main_unrealized_pnl',
                           'hedge_entry_price', 'hedge_quantity', 'hedge_avg_price', 'hedge_unrealized_pnl']:
                    w[k].setText("N/A")
                for labels in w['hedge_labels'] + w['m_order_labels']:
                    for k in ['price', 'qty', 'slippage']:
                        labels[k].setText("N/A")
                    labels['status'].setText("Waiting")
                self.insight_data_by_side[s] = {
                    'main_position': {}, 'hedge_position': {},
                    'next_order': {}, 'm_orders': [],
                    'hedge_triggers': [{} for _ in range(4)],
                    'profit_target': {}, 'uptrend_threshold': {},
                    'current_price': 0
                }
                print(f"[Insight] [{s.upper()}] 탭 초기화 완료")
            except Exception as e:
                print(f"[Insight] 탭 초기화 오류 ({s}): {e}")

    def refresh_insight_to_current(self, side):
        """현재 실시간 데이터로 Insight UI를 업데이트"""
        try:
            worker = self.auto_trade_workers.get(side)
            if not worker:
                return
            w = self._iw(side)
            w['current_step'].setText(f"{worker.current_step + 1}/{worker.total_steps}")
            if hasattr(self, 'current_price') and self.current_price > 0:
                precision = self.detected_precision if self.detected_precision is not None else 4
                w['current_price'].setText(f"{self.current_price:.{precision}f}")

            # 포지션 데이터 복원
            data = self.insight_data_by_side[side]
            mp = data.get('main_position', {})
            if mp:
                self.update_insight_main_position(
                    side, mp.get('entry_price', 0), mp.get('quantity', 0),
                    mp.get('avg_price', 0), mp.get('unrealized_pnl'))
            hp = data.get('hedge_position', {})
            if hp:
                self.update_insight_hedge_position(
                    side, hp.get('entry_price', 0), hp.get('quantity', 0),
                    hp.get('avg_price', 0), hp.get('unrealized_pnl'))

            # M 주문 데이터 복원
            m_orders = data.get('m_orders', [])
            if m_orders:
                self.update_insight_m_orders(side, m_orders)

            # 헷지 트리거 데이터 복원
            hedge_data = data.get('hedge_triggers', [])
            if hedge_data and any(ht.get('price', 0) for ht in hedge_data if isinstance(ht, dict)):
                trigger_list = []
                for ht in hedge_data:
                    if isinstance(ht, dict) and ht.get('price', 0):
                        trigger_list.append([ht['price'], ht.get('qty', 0), ht.get('executed', False)])
                if trigger_list:
                    self.update_insight_hedge_triggers(
                        side, trigger_list, worker.side_mode, worker.current_step)

            if worker.profit_target_price:
                self.update_insight_profit_target(side, worker.profit_target_price)
            else:
                w['profit_target_price'].setText("N/A")
                w['profit_target_status'].setText("N/A")
                w['profit_distance'].setText("N/A")
            if worker.uptrend_threshold_price:
                self.update_insight_uptrend_threshold(side, worker.uptrend_threshold_price)
            else:
                w['uptrend_threshold_price'].setText("N/A")
                w['uptrend_distance'].setText("N/A")
                w['uptrend_status'].setText("N/A")
            if worker.uptrend_threshold_price_2:
                self.update_insight_uptrend_threshold_2(side, worker.uptrend_threshold_price_2)
            else:
                w['uptrend_threshold_price_2'].setText("N/A")
                w['uptrend_distance_2'].setText("N/A")
                w['uptrend_status_2'].setText("N/A")
        except Exception as e:
            print(f"[Insight] 실시간 업데이트 오류 ({side}): {e}")

    # ============================================================
    # Statistics 탭 메서드
    # ============================================================

    def on_hedge_protocol_fired(self, side, step, estimated_pnl):
        """헷지 프로토콜 발동 시 해당 step 통계 업데이트"""
        try:
            data = self.statistics_data.get(side, [])
            if 0 <= step < len(data):
                data[step]['hedge_protocol_count'] += 1
                # 헷지 익절 손익% 기록 (잔액 대비)
                pnl_pct = (estimated_pnl / self.cycle_start_balance * 100) if self.cycle_start_balance > 0 else 0
                data[step].setdefault('hedge_tp_pcts', []).append(round(pnl_pct, 4))
                self.update_statistics_table(side)
                self.save_statistics_data()
        except Exception as e:
            print(f"[Statistics] 헷지 프로토콜 기록 오류 ({side}): {e}")

    def record_cycle_end_stat(self, side, step, pnl_pct):
        """사이클 종료 시 해당 step 통계 업데이트"""
        try:
            data = self.statistics_data.get(side, [])
            if 0 <= step < len(data):
                data[step]['cycle_end_count'] += 1
                data[step]['profit_pcts'].append(round(pnl_pct, 4))
                self.update_statistics_table(side)
                self.save_statistics_data()
        except Exception as e:
            print(f"[Statistics] 사이클 종료 기록 오류 ({side}): {e}")

    def update_statistics_table(self, side):
        """Statistics 테이블 전체 갱신
        컬럼: Step | 사이클 종료 | 헷지 프로토콜 | 헷지 익절 누적손익% | 헷지 익절 평균손익% | 누적 손익% | 평균 손익%
        """
        try:
            sw = self.statistics_widgets.get(side, {})
            table = sw.get('table')
            if not table:
                return
            data = self.statistics_data.get(side, [])
            total_steps = sw.get('total_steps', len(data))

            for row in range(min(total_steps, len(data))):
                d = data[row]
                ce = d.get('cycle_end_count', 0)
                hp = d.get('hedge_protocol_count', 0)
                pcts = d.get('profit_pcts', [])
                h_pcts = d.get('hedge_tp_pcts', [])

                # col 1: 사이클 종료
                table.item(row, 1).setText(str(ce))
                # col 2: 헷지 프로토콜
                table.item(row, 2).setText(str(hp))
                # col 3: 헷지 익절 누적손익%
                h_cumulative = sum(h_pcts)
                table.item(row, 3).setText(f"{h_cumulative:+.4f}%" if h_pcts else "-")
                # col 4: 헷지 익절 평균손익%
                h_avg = sum(h_pcts) / len(h_pcts) if h_pcts else 0
                table.item(row, 4).setText(f"{h_avg:+.4f}%" if h_pcts else "-")
                # col 5: 누적 손익%
                cumulative = sum(pcts)
                table.item(row, 5).setText(f"{cumulative:+.4f}%" if pcts else "-")
                # col 6: 평균 손익%
                avg = sum(pcts) / len(pcts) if pcts else 0
                table.item(row, 6).setText(f"{avg:+.4f}%" if pcts else "-")

        except Exception as e:
            print(f"[Statistics] 테이블 업데이트 오류 ({side}): {e}")

    def reset_statistics(self, side=None):
        """Statistics 데이터 초기화"""
        sides = [side] if side else ['long', 'short']
        for s in sides:
            total_steps = self.statistics_widgets.get(s, {}).get('total_steps', 10)
            self.statistics_data[s] = [
                {'hedge_protocol_count': 0, 'cycle_end_count': 0, 'profit_pcts': [], 'hedge_tp_pcts': []}
                for _ in range(total_steps)
            ]
            self.update_statistics_table(s)
        self.save_statistics_data()

    def save_statistics_data(self):
        """Statistics 데이터를 config에 저장"""
        try:
            save_data = {}
            for side in ['long', 'short']:
                save_data[side] = self.statistics_data.get(side, [])
            self.config_data['statistics'] = save_data
            config_manager.save_config_data(self.config_data)
        except Exception as e:
            print(f"[Statistics] 저장 오류: {e}")

    def load_statistics_data(self):
        """Statistics 데이터를 config에서 복원"""
        try:
            saved = self.config_data.get('statistics', {})
            for side in ['long', 'short']:
                if side in saved and isinstance(saved[side], list):
                    self.statistics_data[side] = saved[side]
                    total_steps = self.statistics_widgets.get(side, {}).get('total_steps', 10)
                    self._init_statistics_data(side, total_steps)
                    self.update_statistics_table(side)
        except Exception as e:
            print(f"[Statistics] 복원 오류: {e}")

    def closeEvent(self, event):
        """프로그램 종료 시 실행 (Qt 윈도우 close 이벤트)"""
        # 종료 확인 대화상자
        reply = QMessageBox.question(
            self,
            "프로그램 종료",
            "프로그램을 종료하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.No:
            event.ignore()  # 종료 취소
            return

        # 정상 종료: clean_shutdown 플래그를 세워 데몬이 재시작하지 않도록
        # (watchdog_enabled는 유지 → 다음 실행 시 자동 활성화)
        try:
            config_data = config_manager.load_config_data()
            if "app_settings" not in config_data:
                config_data["app_settings"] = {}
            config_data["app_settings"]["watchdog_clean_shutdown"] = True
            config_manager.save_config_data(config_data)
            self._stop_watchdog_daemon()
        except:
            pass

        print("프로그램 종료 중...")

        # DCA 실행 중이면 상태 저장 (로그 출력으로 확인)
        if self.auto_trade_worker.is_running:
            print(f"[종료] DCA 실행 중 감지. 현재 단계: Step {self.auto_trade_worker.current_step}")
            print(f"[종료] DCA 상태 저장 시작...")
            self.save_dca_state()
            print(f"[종료] DCA 상태 저장 완료!")
        else:
            print("[종료] DCA가 실행 중이 아니므로 상태 저장 안 함")

        # 리소스 모니터 정지
        if hasattr(self, 'resource_monitor'):
            self.resource_monitor.stop()
            print("[종료] 리소스 모니터 중지 완료")

        # 타이머 정리 (차트 타이머는 SingleShot으로 자동 관리되므로 별도 중지 불필요)
        # 차트 타이머는 프로그램 종료 시 자동으로 취소됨
        if self.balance_refresh_timer:
            self.balance_refresh_timer.stop()
        if self.loading_animation_timer:
            self.loading_animation_timer.stop()
        if self.chart_view_save_timer:
            self.chart_view_save_timer.stop()
            # 대기 중인 저장이 있으면 즉시 실행
            self._save_chart_view_state_immediate()

        # 차트 마커 정리
        self.remove_all_hedge_trigger_markers()

        # WebSocket 스레드 정리 (즉시 강제 종료)
        if self.ws_thread and self.ws_thread.isRunning():
            print("[종료] WebSocket 스레드 종료 중...")
            self.ws_thread.stop()
            self.ws_thread.terminate()  # 즉시 강제 종료

        if self.ticker_thread and self.ticker_thread.isRunning():
            print("[종료] Ticker 스레드 종료 중...")
            self.ticker_thread.stop()
            self.ticker_thread.terminate()  # 즉시 강제 종료

        if self.kline_thread and self.kline_thread.isRunning():
            print("[종료] Kline 스레드 종료 중...")
            self.kline_thread.stop()
            self.kline_thread.terminate()  # 즉시 강제 종료

        # API 키 정리
        if self.api_module:
            self.api_module.set_active_api_keys(None, None)

        print("[종료] 정리 완료. 프로그램 종료.")
        event.accept()

    def on_memory_warning(self, memory_mb, level):
        """메모리 경고 핸들러"""
        try:
            if level == "critical":
                print(f"[메모리 경고] ⚠️ 위험: {memory_mb:.1f}MB - 즉시 정리 필요")
                # 차트 데이터 강제 정리
                if self.chart_data_df is not None and len(self.chart_data_df) > self.MAX_CANDLES // 2:
                    old_len = len(self.chart_data_df)
                    self.chart_data_df = self.chart_data_df.tail(self.MAX_CANDLES // 2).reset_index(drop=True)
                    print(f"[메모리 정리] 차트 데이터 축소: {old_len} → {len(self.chart_data_df)}개")

                # 체결 이력 정리
                if len(self.fill_history) > 500:
                    old_len = len(self.fill_history)
                    self.fill_history = self.fill_history[-500:]
                    print(f"[메모리 정리] 체결 이력 축소: {old_len} → {len(self.fill_history)}개")
            else:
                print(f"[메모리 경고] 주의: {memory_mb:.1f}MB - 모니터링 중")
        except Exception as e:
            logger.error(f"[메모리 경고] 처리 오류: {e}")

    def on_resource_updated(self, memory_mb, cpu_percent, max_memory_mb):
        """리소스 모니터 업데이트 핸들러 (GUI 업데이트)"""
        try:
            if not self.resource_memory_label or not self.resource_cpu_label:
                return  # initUI 완료 전이면 스킵

            # 메모리 라벨 업데이트
            memory_color = "#00ff00"  # 초록색 (정상)
            if memory_mb > 800:
                memory_color = "#ff0000"  # 빨간색 (위험)
            elif memory_mb > 500:
                memory_color = "#ffaa00"  # 주황색 (경고)

            self.resource_memory_label.setText(
                f"<span style='color: {memory_color};'>Memory: {memory_mb:.1f}MB</span> / Max: {max_memory_mb:.1f}MB"
            )

            # CPU 라벨 업데이트
            cpu_color = "#00ff00"  # 초록색 (정상)
            if cpu_percent > 80:
                cpu_color = "#ff0000"  # 빨간색
            elif cpu_percent > 50:
                cpu_color = "#ffaa00"  # 주황색

            self.resource_cpu_label.setText(
                f"<span style='color: {cpu_color};'>CPU: {cpu_percent:.1f}%</span>"
            )

        except Exception as e:
            logger.error(f"[리소스 업데이트] GUI 업데이트 오류: {e}")

    def on_cleanup_completed(self, freed_mb):
        """메모리 정리 완료 핸들러"""
        try:
            # 마지막 정리 시간 업데이트
            if hasattr(self, 'resource_cleanup_label') and self.resource_cleanup_label:
                from datetime import datetime
                cleanup_time = datetime.now().strftime("%H:%M:%S")
                self.resource_cleanup_label.setText(f"Last Cleanup: {cleanup_time} (-{freed_mb:.1f}MB)")
        except Exception as e:
            logger.error(f"[정리 완료] GUI 업데이트 오류: {e}")

    def update_heartbeat(self):
        """프로그램 정상 작동 표시 (하트비트) - 윈도우 타이틀에 초록불 표시"""
        try:
            # 초록불 깜빡임 (토글)
            if self.heartbeat_active:
                indicator = "🟢"  # 초록불
                self.heartbeat_active = False
            else:
                indicator = "⚫"  # 검은불 (깜빡임 효과)
                self.heartbeat_active = True

            # 현재 심볼 가져오기 (LONG 패널 기준)
            current_symbol = self.current_symbols.get('long', 'BTCUSDT')

            # 현재 가격 가져오기 (trade_price_labels에서)
            current_price = "N/A"
            if 'long' in self.trade_price_labels and self.trade_price_labels['long']:
                price_text = self.trade_price_labels['long'].text()
                if price_text and price_text != "0.00":
                    current_price = price_text

            # 현재 마켓 타입 가져오기
            market_type = self.market_type_modes.get('long', 'linear')
            market_display = "Linear" if market_type in ['linear', 'fapi'] else "Inverse"

            # 타이틀 업데이트: [연결마켓] 현재가격 심볼 - v7 DCA Trader
            self.setWindowTitle(f"{indicator} [{market_display}] {current_price} {current_symbol} - v7 DCA Trader")
        except Exception as e:
            print(f"[하트비트] 업데이트 오류: {e}")