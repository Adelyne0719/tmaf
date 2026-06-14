"""
통합 티커 웹소켓 모듈 (Binance & Bybit)
실시간 가격(Last Price) 데이터를 수신합니다.
"""

import asyncio
import websockets
import json
from PyQt5.QtCore import QThread, pyqtSignal


class BinanceTickerSocketThread(QThread):
    """
    Binance 특정 심볼의 실시간 티커(Last Price) 데이터를 수신합니다.
    """
    ticker_update = pyqtSignal(list)

    def __init__(self, market_type, symbol="BTCUSDT", parent=None):
        super().__init__(parent)
        self.market_type = market_type
        self.symbol = symbol.lower()  # Binance는 소문자 심볼 사용

        # 특정 심볼의 티커 스트림 구독
        if self.market_type == 'dapi':
            self.ws_url = f"wss://dstream.binance.com/ws/{self.symbol}@ticker"
        else:  # 'fapi' (default)
            self.ws_url = f"wss://fstream.binance.com/ws/{self.symbol}@ticker"

        self.running = True
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = f"BinanceTickerThread({symbol})"

        print(f"{self.log_prefix}: {self.ws_url} 연결 준비...")

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.main_task = self.loop.create_task(self.listen())
            self.loop.run_forever()
        except Exception as e:
            if self.running:
                print(f"Asyncio 루프 실행 중 오류 ({self.log_prefix}): {e}")
        finally:
            # 모든 pending tasks 취소 및 정리
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                print(f"{self.log_prefix}: 태스크 취소 중 오류 (무시): {e}")

            try:
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception as e:
                print(f"{self.log_prefix}: Asyncgens 종료 중 오류 (무시): {e}")

            try:
                self.loop.close()
            except Exception as e:
                print(f"{self.log_prefix}: 루프 종료 중 오류 (무시): {e}")

            print(f"{self.log_prefix}: 스레드 및 루프 종료 완료.")

    async def listen(self):
        try:
            while self.running:
                try:
                    async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=30) as ws:
                        print(f"WebSocket Connected (Ticker Stream: Binance {self.market_type})")
                        
                        async for message in ws:
                            if not self.running:
                                break 
                            
                            try:
                                data = json.loads(message)
                                # 단일 심볼 티커 데이터를 리스트로 감싸서 emit
                                if isinstance(data, dict):
                                    self.ticker_update.emit([data])

                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류 (Ticker): {message}")

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print("Binance Ticker 웹소켓 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"Binance Ticker 웹소켓 오류: {e}. 3초 후 재연결 시도...")
                
                if self.running:
                    await asyncio.sleep(3) 

        except asyncio.CancelledError:
            print(f"{self.log_prefix}: listen() 코루틴 취소됨.")
        finally:
            print(f"{self.log_prefix}: listen() 코루틴 종료.")

    def stop(self):
        """스레드를 안전하게 종료합니다."""
        print(f"{self.log_prefix}: 종료 요청 수신")
        self.running = False
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        if self.main_task:
            self.loop.call_soon_threadsafe(self.main_task.cancel)


class BybitTickerSocketThread(QThread):
    """
    Bybit V5 특정 심볼의 실시간 티커(Last Price) 데이터를 수신합니다.
    
    [중요] Bybit 티커를 Binance 티커 형식으로 변환하여 GUI로 전송합니다.
    """
    ticker_update = pyqtSignal(list)

    def __init__(self, market_type, symbol, parent=None):
        super().__init__(parent)
        self.market_type = market_type
        
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"  # fapi (linear)
        self.category = "linear"
        if self.market_type == 'dapi':
            self.ws_url = "wss://stream.bybit.com/v5/public/inverse"
            self.category = "inverse"
            
        self.topic = f"tickers.{symbol}"
            
        self.running = True
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = "BybitTickerThread"
        
        print(f"{self.log_prefix}: {self.ws_url} ({self.topic}) 연결 준비...")

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.main_task = self.loop.create_task(self.listen())
            self.loop.run_forever()
        except Exception as e:
            if self.running:
                print(f"Asyncio 루프 실행 중 오류 ({self.log_prefix}): {e}")
        finally:
            # 모든 pending tasks 취소 및 정리
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                print(f"{self.log_prefix}: 태스크 취소 중 오류 (무시): {e}")

            try:
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception as e:
                print(f"{self.log_prefix}: Asyncgens 종료 중 오류 (무시): {e}")

            try:
                self.loop.close()
            except Exception as e:
                print(f"{self.log_prefix}: 루프 종료 중 오류 (무시): {e}")

            print(f"{self.log_prefix}: 스레드 및 루프 종료 완료.")

    async def listen(self):
        try:
            while self.running:
                try:
                    async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=30) as ws:
                        # 구독 메시지 전송
                        subscribe_msg = {
                            "op": "subscribe",
                            "args": [self.topic]
                        }
                        await ws.send(json.dumps(subscribe_msg))
                        
                        print(f"WebSocket Connected (Ticker Stream: Bybit {self.category})")
                        
                        async for message in ws:
                            if not self.running:
                                break 
                            
                            try:
                                data = json.loads(message)
                                
                                # Bybit 티커 데이터를 Binance 형식으로 변환
                                if data.get('topic') == self.topic and data.get('data'):
                                    bybit_ticker = data['data']
                                    
                                    # Binance 형식: [{'s': 'BTCUSDT', 'c': '25000.5'}]
                                    binance_formatted = [{
                                        's': bybit_ticker.get('symbol'),
                                        'c': bybit_ticker.get('lastPrice')
                                    }]
                                    
                                    if binance_formatted[0]['s'] and binance_formatted[0]['c']:
                                        self.ticker_update.emit(binance_formatted)
                                    
                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류 (Ticker): {message}")

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print("Bybit Ticker 웹소켓 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"Bybit Ticker 웹소켓 오류: {e}. 3초 후 재연결 시도...")
                
                if self.running:
                    await asyncio.sleep(3) 

        except asyncio.CancelledError:
            print(f"{self.log_prefix}: listen() 코루틴 취소됨.")
        finally:
            print(f"{self.log_prefix}: listen() 코루틴 종료.")

    def stop(self):
        """스레드를 안전하게 종료합니다."""
        print(f"{self.log_prefix}: 종료 요청 수신")
        self.running = False
        
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        if self.main_task:
            self.loop.call_soon_threadsafe(self.main_task.cancel)


# =============================================================================
# Factory Function (편의 함수)
# =============================================================================

def create_ticker_thread(exchange, market_type, symbol=None, parent=None):
    """
    거래소에 맞는 티커 웹소켓 스레드를 생성합니다.
    
    Args:
        exchange (str): "Binance" 또는 "Bybit"
        market_type (str): "fapi" 또는 "dapi"
        symbol (str, optional): Bybit의 경우 필수 (예: "BTCUSDT")
        parent (QObject, optional): 부모 객체
    
    Returns:
        QThread: 거래소별 티커 웹소켓 스레드
    
    Examples:
        >>> ticker_thread = create_ticker_thread("Binance", "fapi")
        >>> ticker_thread = create_ticker_thread("Bybit", "fapi", "BTCUSDT")
    """
    if exchange == "Binance":
        return BinanceTickerSocketThread(market_type, parent)
    elif exchange == "Bybit":
        if not symbol:
            raise ValueError("Bybit 티커 스레드는 symbol 파라미터가 필요합니다.")
        return BybitTickerSocketThread(market_type, symbol, parent)
    else:
        raise ValueError(f"지원되지 않는 거래소: {exchange}")


class BybitKlineSocketThread(QThread):
    """
    Bybit V5 실시간 캔들(Kline) 데이터를 수신합니다.

    실시간으로 캔들이 업데이트되므로 차트를 거래소와 정확히 동기화할 수 있습니다.
    """
    kline_update = pyqtSignal(dict)  # {'symbol': str, 'interval': str, 'kline': {...}}

    def __init__(self, market_type, symbol, interval="5", parent=None):
        """
        Args:
            market_type (str): "fapi" (linear) 또는 "dapi" (inverse)
            symbol (str): 심볼 (예: "XRPUSDT")
            interval (str): 캔들 간격 (1, 3, 5, 15, 30, 60, 120, 240, 360, 720, D, W, M)
        """
        super().__init__(parent)
        self.market_type = market_type
        self.symbol = symbol
        self.interval = interval

        # WebSocket URL 설정
        if market_type == 'dapi':
            self.ws_url = "wss://stream.bybit.com/v5/public/inverse"
            self.category = "inverse"
        else:
            self.ws_url = "wss://stream.bybit.com/v5/public/linear"
            self.category = "linear"

        self.topic = f"kline.{interval}.{symbol}"

        self.running = True
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = f"BybitKlineThread({symbol}/{interval})"

        print(f"{self.log_prefix}: {self.ws_url} ({self.topic}) 연결 준비...")

    def run(self):
        asyncio.set_event_loop(self.loop)
        try:
            self.main_task = self.loop.create_task(self.listen())
            self.loop.run_forever()
        except Exception as e:
            if self.running:
                print(f"Asyncio 루프 실행 중 오류 ({self.log_prefix}): {e}")
        finally:
            # 모든 pending tasks 취소 및 정리
            try:
                pending = asyncio.all_tasks(self.loop)
                for task in pending:
                    task.cancel()
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                print(f"{self.log_prefix}: 태스크 취소 중 오류 (무시): {e}")

            try:
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception as e:
                print(f"{self.log_prefix}: Asyncgens 종료 중 오류 (무시): {e}")

            try:
                self.loop.close()
            except Exception as e:
                print(f"{self.log_prefix}: 루프 종료 중 오류 (무시): {e}")

            print(f"{self.log_prefix}: 스레드 및 루프 종료 완료.")

    async def listen(self):
        try:
            while self.running:
                try:
                    async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=30) as ws:
                        # 구독 메시지 전송
                        subscribe_msg = {
                            "op": "subscribe",
                            "args": [self.topic]
                        }
                        await ws.send(json.dumps(subscribe_msg))

                        print(f"WebSocket Connected (Kline Stream: Bybit {self.category} {self.symbol}/{self.interval})")

                        async for message in ws:
                            if not self.running:
                                break

                            try:
                                data = json.loads(message)

                                # Bybit 캔들 데이터 처리
                                if data.get('topic') == self.topic and data.get('data'):
                                    kline_data = data['data'][0] if isinstance(data['data'], list) else data['data']

                                    # 캔들 데이터 변환 및 emit
                                    # Bybit V5 kline 응답은 symbol 필드가 없으므로 구독한 심볼 사용
                                    parsed_kline = {
                                        'symbol': self.symbol,  # topic에서 추출한 심볼 사용
                                        'interval': kline_data.get('interval'),
                                        'start': int(kline_data.get('start')),  # 시작 시간 (밀리초)
                                        'end': int(kline_data.get('end')),      # 종료 시간 (밀리초)
                                        'open': float(kline_data.get('open')),
                                        'high': float(kline_data.get('high')),
                                        'low': float(kline_data.get('low')),
                                        'close': float(kline_data.get('close')),
                                        'volume': float(kline_data.get('volume')),
                                        'confirm': kline_data.get('confirm'),  # True: 캔들 확정, False: 진행 중
                                        'timestamp': int(kline_data.get('timestamp'))  # 업데이트 시간
                                    }

                                    self.kline_update.emit(parsed_kline)

                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류 (Kline): {message}")
                            except Exception as e:
                                print(f"캔들 데이터 처리 오류: {e}")

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print("Bybit Kline 웹소켓 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"Bybit Kline 웹소켓 오류: {e}. 3초 후 재연결 시도...")

                if self.running:
                    await asyncio.sleep(3)

        except asyncio.CancelledError:
            print(f"{self.log_prefix}: listen() 코루틴 취소됨.")
        finally:
            print(f"{self.log_prefix}: listen() 코루틴 종료.")

    def stop(self):
        """스레드를 안전하게 종료합니다."""
        print(f"{self.log_prefix}: 종료 요청 수신")
        self.running = False

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.main_task:
            self.loop.call_soon_threadsafe(self.main_task.cancel)

    def update_subscription(self, symbol, interval):
        """구독 중인 심볼/간격 변경 (재연결 필요)"""
        self.symbol = symbol
        self.interval = interval
        self.topic = f"kline.{interval}.{symbol}"
        print(f"{self.log_prefix}: 구독 변경 -> {self.topic}")


# Backward Compatibility (기존 코드 호환성)
# v7_gui.py에서 직접 클래스를 import하는 경우를 위해 별칭 제공
TickerSocketThread = BinanceTickerSocketThread