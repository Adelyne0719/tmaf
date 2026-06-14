import asyncio
import websockets
import json
from PyQt5.QtCore import QThread, pyqtSignal

class TickerSocketThread(QThread):
    """
    'websockets' (asyncio) 라이브러리를 사용하여
    모든 심볼의 실시간 *티커* (Last Price) 데이터를 수신합니다.
    """
    ticker_update = pyqtSignal(list)

    def __init__(self, market_type, parent=None):
        super().__init__(parent)
        self.market_type = market_type
        
        if self.market_type == 'dapi':
            self.ws_url = "wss://dstream.binance.com/ws/!ticker@arr"
        else: # 'fapi' (default)
            self.ws_url = "wss://fstream.binance.com/ws/!ticker@arr"
            
        self.running = True
        
        # ▼▼▼ [수정] asyncio 루프를 스레드가 소유 ▼▼▼
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = "TickerSocketThread"
        # ▲▲▲ [수정] ▲▲▲
        
        print(f"{self.log_prefix}: {self.ws_url} 연결 준비...")

    def run(self):
        # ▼▼▼ [수정] 스레드에서 asyncio 루프를 직접 실행 ▼▼▼
        asyncio.set_event_loop(self.loop)
        try:
            self.main_task = self.loop.create_task(self.listen())
            self.loop.run_forever() # loop.stop()이 호출될 때까지 실행
        except Exception as e:
            if self.running:
                print(f"Asyncio 루프 실행 중 오류 ({self.log_prefix}): {e}")
        finally:
            # run_forever()가 종료되면(stop() 호출 시) 루프 정리
            if self.main_task:
                self.loop.run_until_complete(self.main_task)
            self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            self.loop.close()
            print(f"{self.log_prefix}: 스레드 및 루프 종료 완료.")
        # ▲▲▲ [수정] ▲▲▲

    async def listen(self):
        # ▼▼▼ [수정] 취소 예외 처리 추가 ▼▼▼
        try:
            while self.running:
                try:
                    async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=30) as ws:
                        print(f"WebSocket Connected (Ticker Stream: {self.market_type})")
                        
                        async for message in ws:
                            if not self.running:
                                break 
                            
                            try:
                                data = json.loads(message)
                                if isinstance(data, list):
                                    self.ticker_update.emit(data)
                                    
                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류 (Ticker): {message}")

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print("Ticker 웹소켓 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"Ticker 웹소켓 오류: {e}. 3초 후 재연결 시도...")
                
                if self.running:
                    await asyncio.sleep(3) 

        except asyncio.CancelledError:
            print(f"{self.log_prefix}: listen() 코루틴 취소됨.")
        finally:
            print(f"{self.log_prefix}: listen() 코루틴 종료.")
        # ▲▲▲ [수정] ▲▲▲

    def stop(self):
        """스레드를 안전하게 종료합니다. (메인 스레드에서 호출됨)"""
        print(f"{self.log_prefix}: 종료 요청 수신")
        self.running = False
        
        # ▼▼▼ [수정] 다른 스레드에서 asyncio 루프를 중지시키는 방법 ▼▼▼
        if self.loop and self.loop.is_running():
            # loop.stop()을 루프의 스레드에서 실행하도록 예약
            self.loop.call_soon_threadsafe(self.loop.stop)
            
        if self.main_task:
            # 메인 태스크를 취소하여 'await'에서 즉시 빠져나오도록 함
            self.loop.call_soon_threadsafe(self.main_task.cancel)
        # ▲▲▲ [수정] ▲▲▲