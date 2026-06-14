import asyncio
import websockets
import json
from PyQt5.QtCore import QThread, pyqtSignal

class WebSocketThread(QThread):
    """
    'websockets' (asyncio) 라이브러리를 사용하여
    바이낸스 *사용자 데이터 스트림*에 연결합니다.
    """
    account_update_received = pyqtSignal(dict)
    order_update_received = pyqtSignal(dict)

    def __init__(self, listen_key, market_type="fapi", parent=None):
        super().__init__(parent)
        self.listen_key = listen_key
        
        # 마켓 타입에 따라 웹소켓 주소 변경
        if market_type == "dapi":
            base_ws = "wss://dstream.binance.com" # COIN-M
            self.market_name = "dapi (COIN-M)"
        else:
            base_ws = "wss://fstream.binance.com" # USDⓈ-M (default)
            self.market_name = "fapi (USDⓈ-M)"
            
        self.ws_url = f"{base_ws}/ws/{self.listen_key}"
        self.running = True
        
        # ▼▼▼ [수정] asyncio 루프를 스레드가 소유 ▼▼▼
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = "WebSocketThread (User Data)"
        # ▲▲▲ [수정] ▲▲▲
        
        print(f"{self.log_prefix}: 사용자 데이터 스트림 연결 준비 ({self.ws_url})")

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
                        print(f"WebSocket Connected (User Data Stream: {self.market_name})")
                        
                        async for message in ws:
                            if not self.running:
                                break 
                            
                            try:
                                data = json.loads(message)
                                event_type = data.get('e')
                                
                                if event_type == 'ACCOUNT_UPDATE':
                                    self.account_update_received.emit(data)
                                elif event_type == 'ORDER_TRADE_UPDATE':
                                    self.order_update_received.emit(data)
                                    
                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류: {message}")

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print(f"사용자 데이터 웹소켓({self.market_name}) 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"사용자 데이터 웹소켓({self.market_name}) 오류: {e}. 3초 후 재연결 시도...")
                
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