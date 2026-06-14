import asyncio
import websockets
import json
import time
import hmac
import hashlib
from PyQt5.QtCore import QThread, pyqtSignal

class WebSocketThread(QThread):
    """
    통합 WebSocket 매니저 (Binance & Bybit)

    거래소별 사용자 데이터 스트림에 연결하고,
    모든 데이터를 Binance 형식으로 변환하여 GUI로 전송합니다.

    v7_dual: side 파라미터 추가 (LONG/SHORT 구분)
    """
    account_update_received = pyqtSignal(str, dict)  # (side, data)
    order_update_received = pyqtSignal(str, dict)    # (side, data)

    def __init__(self, exchange="Binance", listen_key=None, api_key=None, api_secret=None, market_type="fapi", side='long', parent=None):
        """
        Args:
            exchange: "Binance" 또는 "Bybit"
            listen_key: Binance용 Listen Key
            api_key: Bybit용 API Key
            api_secret: Bybit용 API Secret
            market_type: "fapi" (USDⓈ-M/Linear) 또는 "dapi" (COIN-M/Inverse)
            side: 'long' 또는 'short' (v7_dual용 패널 구분자)
        """
        super().__init__(parent)
        self.exchange = exchange
        self.listen_key = listen_key
        self.api_key = api_key
        self.api_secret = api_secret
        self.market_type = market_type
        self.side = side  # v7_dual: 패널 구분자 저장

        # WebSocket URL 설정
        if exchange == "Binance":
            if market_type == "dapi":
                base_ws = "wss://dstream.binance.com"
                self.market_name = "Binance COIN-M"
            else:
                base_ws = "wss://fstream.binance.com"
                self.market_name = "Binance USDⓈ-M"
            self.ws_url = f"{base_ws}/ws/{listen_key}"

        elif exchange == "Bybit":
            self.ws_url = "wss://stream.bybit.com/v5/private"
            self.market_name = "Bybit V5 Private"

        else:
            raise ValueError(f"지원되지 않는 거래소: {exchange}")

        self.running = True
        self.loop = asyncio.new_event_loop()
        self.main_task = None
        self.log_prefix = f"WebSocketThread ({exchange})"

        print(f"{self.log_prefix}: {self.market_name} 사용자 데이터 스트림 연결 준비...")

    def run(self):
        """스레드 메인 루프"""
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
                # 취소된 태스크들이 완료될 때까지 대기
                if pending:
                    self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception as e:
                print(f"{self.log_prefix}: 태스크 취소 중 오류 (무시): {e}")

            # Async generators 종료
            try:
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception as e:
                print(f"{self.log_prefix}: Asyncgens 종료 중 오류 (무시): {e}")

            # 이벤트 루프 완전 종료
            try:
                self.loop.close()
            except Exception as e:
                print(f"{self.log_prefix}: 루프 종료 중 오류 (무시): {e}")

            print(f"{self.log_prefix}: 스레드 및 루프 종료 완료.")

    async def listen(self):
        """WebSocket 연결 및 메시지 수신"""
        heartbeat_task = None  # 초기화
        try:
            while self.running:
                try:
                    async with websockets.connect(self.ws_url, ping_interval=20, ping_timeout=30) as ws:

                        # Bybit의 경우 인증 및 구독 필요
                        if self.exchange == "Bybit":
                            if not await self._bybit_authenticate(ws):
                                break
                            await self._bybit_subscribe(ws)

                            # Bybit V5 Heartbeat 태스크 시작
                            heartbeat_task = asyncio.create_task(self._bybit_heartbeat(ws))

                        print(f"WebSocket Connected (User Data Stream: {self.market_name})")

                        async for message in ws:
                            if not self.running:
                                break

                            try:
                                data = json.loads(message)

                                # Bybit pong 응답 무시
                                if self.exchange == "Bybit" and data.get('op') == 'pong':
                                    continue

                                # 거래소별 메시지 처리
                                if self.exchange == "Binance":
                                    self._process_binance_message(data)
                                elif self.exchange == "Bybit":
                                    self._process_bybit_message(data)

                            except json.JSONDecodeError:
                                print(f"JSON 디코딩 오류: {message}")

                        # Heartbeat 태스크 정리
                        if self.exchange == "Bybit" and heartbeat_task:
                            heartbeat_task.cancel()
                            try:
                                await heartbeat_task
                            except asyncio.CancelledError:
                                pass
                            heartbeat_task = None

                except websockets.exceptions.ConnectionClosed:
                    if self.running:
                        print(f"{self.market_name} 웹소켓 연결 끊김. 3초 후 재연결 시도...")
                except Exception as e:
                    if self.running:
                        print(f"{self.market_name} 웹소켓 오류: {e}. 3초 후 재연결 시도...")

                if self.running:
                    await asyncio.sleep(3)

        except asyncio.CancelledError:
            print(f"{self.log_prefix}: listen() 코루틴 취소됨.")
        finally:
            # Heartbeat 태스크가 남아있으면 정리
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
            print(f"{self.log_prefix}: listen() 코루틴 종료.")

    # ==================== Binance 메시지 처리 ====================

    def _process_binance_message(self, data):
        """Binance 메시지 처리 (이미 표준 형식)"""
        event_type = data.get('e')

        if event_type == 'ACCOUNT_UPDATE':
            self.account_update_received.emit(self.side, data)  # v7_dual: side 추가
        elif event_type == 'ORDER_TRADE_UPDATE':
            self.order_update_received.emit(self.side, data)  # v7_dual: side 추가

    # ==================== Bybit 인증 및 구독 ====================

    async def _bybit_authenticate(self, ws):
        """Bybit V5 인증"""
        expires = int((time.time() + 10) * 1000)
        payload = f"GET/realtime{expires}"

        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        auth_msg = {
            "op": "auth",
            "args": [self.api_key, expires, signature]
        }
        await ws.send(json.dumps(auth_msg))
        print(f"{self.log_prefix}: 인증 요청 전송...")

        auth_response = await ws.recv()
        auth_data = json.loads(auth_response)

        if auth_data.get('success') == True:
            print(f"{self.log_prefix}: Bybit 웹소켓 인증 성공.")
            return True
        else:
            print(f"{self.log_prefix}: Bybit 웹소켓 인증 실패: {auth_data.get('ret_msg')}")
            return False

    async def _bybit_subscribe(self, ws):
        """Bybit Private 토픽 구독"""
        subscribe_msg = {
            "op": "subscribe",
            "args": [
                "position",  # 포지션
                "order",     # 주문
                "wallet"     # 잔액
            ]
        }
        await ws.send(json.dumps(subscribe_msg))
        print(f"{self.log_prefix}: 'position', 'order', 'wallet' 토픽 구독 요청.")

    async def _bybit_heartbeat(self, ws):
        """Bybit V5 Heartbeat - 20초마다 ping 전송"""
        try:
            while True:
                await asyncio.sleep(20)
                ping_msg = {"op": "ping"}
                await ws.send(json.dumps(ping_msg))
                # ping 로그는 생략 (너무 빈번함)
        except asyncio.CancelledError:
            pass  # 정상 종료 시 로그 생략
        except Exception as e:
            print(f"{self.log_prefix}: Heartbeat 오류: {e}")

    # ==================== Bybit 메시지 변환 ====================

    def _process_bybit_message(self, data):
        """Bybit V5 메시지를 Binance 형식으로 변환"""
        topic = data.get('topic')
        payload = data.get('data')

        if not payload:
            return

        try:
            # 1. 잔액 (Wallet)
            if topic == 'wallet':
                binance_balances = []
                for account in payload:
                    # Bybit V5: payload=[{accountType, coin: [{coin, walletBalance, ...}]}]
                    coins = account.get('coin', [])
                    for c in coins:
                        binance_balances.append({
                            'a': c.get('coin'),
                            'wb': c.get('walletBalance')
                        })
                formatted_msg = {'e': 'ACCOUNT_UPDATE', 'a': {'B': binance_balances, 'P': []}}
                self.account_update_received.emit(self.side, formatted_msg)  # v7_dual: side 추가

            # 2. 포지션 (Position)
            elif topic == 'position':
                binance_positions = []
                for p in payload:
                    # [디버깅] 원본 Bybit 포지션 데이터 출력
                    print(f"[Bybit Position Update] Raw data: {p}")

                    # positionIdx로 헤지 모드 구분
                    # 0 = One-Way, 1 = Hedge Long, 2 = Hedge Short
                    position_idx = p.get('positionIdx', 0)
                    side = p.get('side', 'None')

                    # positionSide 결정
                    if position_idx == 1:
                        position_side = 'LONG'
                    elif position_idx == 2:
                        position_side = 'SHORT'
                    else:
                        position_side = 'LONG' if side == 'Buy' else 'SHORT' if side == 'Sell' else 'BOTH'

                    # 수량 변환
                    amt = float(p.get('size', '0'))
                    if position_side == 'SHORT' and amt > 0:
                        amt = -amt

                    # Entry Price: avgPrice 또는 entryPrice 사용
                    entry_price = p.get('avgPrice') or p.get('entryPrice', '0')

                    binance_positions.append({
                        's': p.get('symbol'),
                        'ps': position_side,
                        'pa': str(amt),
                        'ep': entry_price,
                        'up': p.get('unrealisedPnl', '0'),
                        'im': p.get('positionIM', '0'),
                        'mp': p.get('markPrice', '0'),  # 현재가 (markPrice)
                        'lp': p.get('liqPrice', '0')    # 청산가 (liqPrice)
                    })
                formatted_msg = {'e': 'ACCOUNT_UPDATE', 'a': {'B': [], 'P': binance_positions}}
                self.account_update_received.emit(self.side, formatted_msg)  # v7_dual: side 추가

            # 3. 주문 (Order)
            elif topic == 'order':
                for o in payload:
                    formatted_msg = {
                        'e': 'ORDER_TRADE_UPDATE',
                        'o': {
                            'i': o.get('orderId'),
                            'X': self._map_bybit_order_status(o.get('orderStatus')),
                            's': o.get('symbol'),
                            'o': o.get('orderType'),
                            'S': o.get('side'),
                            'p': o.get('price'),
                            'q': o.get('qty'),
                            'z': o.get('cumExecQty', '0'),
                            'ap': o.get('avgPrice', '0')  # 평균 체결가 추가
                        }
                    }
                    self.order_update_received.emit(self.side, formatted_msg)  # v7_dual: side 추가

        except Exception as e:
            print(f"Bybit 메시지 변환 오류: {e} (데이터: {data})")

    def _map_bybit_order_status(self, bybit_status):
        """Bybit 주문 상태를 Binance 형식으로 변환"""
        mapping = {
            'Created': 'NEW',
            'New': 'NEW',
            'PartiallyFilled': 'PARTIALLY_FILLED',
            'Filled': 'FILLED',
            'Cancelled': 'CANCELED',
            'Deactivated': 'CANCELED',
            'Rejected': 'REJECTED'
        }
        return mapping.get(bybit_status, bybit_status.upper())

    # ==================== 종료 처리 ====================

    def stop(self):
        """스레드를 안전하게 종료"""
        print(f"{self.log_prefix}: 종료 요청 수신")
        self.running = False

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        if self.main_task:
            self.loop.call_soon_threadsafe(self.main_task.cancel)
