import json
import logging
import requests
from PyQt5.QtCore import QUrl
from PyQt5.QtWebSockets import QWebSocket
import config  # 기존 consts 대신 config 사용

class BinanceUserDataStream:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws = QWebSocket()
        self.ws.textMessageReceived.connect(self.on_message)
        self.listen_key = None
        # 콜백 함수를 통해 GUI 등에서 수신한 데이터를 처리할 수 있도록 합니다.
        self.on_account_update = None
        self.last_position_amt = None

    def on_connected(self):
        logging.info("User Data WebSocket에 연결되었습니다.")

    def on_error(self, error):
        logging.error("User Data WebSocket 에러: %s", error)
        # 연결 오류 시 재연결 시도
        self.reconnect()

    def reconnect(self):
        if self.ws.state() == self.ws.Open:
            self.ws.close()
        self.start()

    def start(self):
        self.listen_key = self.get_listen_key()
        if self.listen_key:
            ws_url = f"wss://fstream.binance.com/ws/{self.listen_key}"
            logging.info("User Data WebSocket URL: %s", ws_url)
            self.ws.open(QUrl(ws_url))
        else:
            logging.error("ListenKey 발급 실패")

    def get_listen_key(self):
        base_url = "https://fapi.binance.com"
        endpoint = "/fapi/v1/listenKey"
        headers = {"X-MBX-APIKEY": self.api_key}
        try:
            response = requests.post(base_url + endpoint, headers=headers)
            if response.status_code == 200:
                data = response.json()
                logging.info("발급된 listenKey: %s", data.get("listenKey"))
                return data.get("listenKey")
            else:
                logging.error("listenKey 발급 실패: %s", response.text)
        except Exception as e:
            logging.error("listenKey 발급 중 예외 발생: %s", e)
        return None

    def on_message(self, message):
        try:
            data = json.loads(message)
            event_type = data.get("e", "")
            logging.debug("User Data Stream 이벤트: %s", event_type)
            
            if event_type == "ACCOUNT_UPDATE":
                account_data = data.get("a", {})
                positions = account_data.get("P", [])
                
                # 우선 대상 심볼 포지션을 찾음
                target_position = None
                for pos in positions:
                    if pos.get("s") == config.SYMBOL:
                        target_position = pos
                        break
                
                # 포지션 정보 처리
                if target_position:
                    position_amt = float(target_position.get("pa", "0"))
                    entry_price = target_position.get("ep", "-")
                    unrealized_profit = target_position.get("up", "-")
                    
                    # 포지션이 없는 경우 (청산된 경우)
                    if position_amt == 0:
                        if self.on_account_update:
                            self.on_account_update({
                                "position": "없음",
                                "entry": "-",
                                "quantity": "0",
                                "unrealized_profit": "0",
                                "stage": "-"
                            })
                            self.last_position_amt = 0
                            logging.info("포지션 청산 감지: GUI 업데이트 완료")
                    else:
                        if self.on_account_update:
                            position_type = "롱" if position_amt > 0 else "숏"
                            self.on_account_update({
                                "position": position_type,
                                "entry": entry_price,
                                "quantity": str(position_amt),
                                "unrealized_profit": unrealized_profit,
                                "stage": "-"  # stage 정보는 제공되지 않으므로 '-'로 처리
                            })
                            self.last_position_amt = position_amt
                elif self.last_position_amt is not None:  # 이전에 포지션이 있었는데 이제 없는 경우
                    if self.on_account_update:
                        self.on_account_update({
                            "position": "없음",
                            "entry": "-",
                            "quantity": "0",
                            "unrealized_profit": "0",
                            "stage": "-"
                        })
                        self.last_position_amt = 0
                        logging.info("포지션 청산 감지: GUI 업데이트 완료")
                
            elif event_type == "ORDER_TRADE_UPDATE":
                order_data = data.get("o", {})
                symbol = order_data.get("s")
                status = order_data.get("X")
                side = order_data.get("S")
                order_type = order_data.get("o")
                
                # 청산 주문이 체결된 경우 (FILLED)
                if symbol == config.SYMBOL and status == "FILLED" and order_type == "MARKET":
                    logging.info(f"{side} 주문 체결 감지: 포지션 상태 확인 중")
        except Exception as e:
            logging.error("User data 메시지 처리 에러: %s", e)
