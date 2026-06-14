"""
통합 거래소 API 모듈 (Binance & Bybit)
각 거래소의 API를 동일한 인터페이스로 제공합니다.
"""

import time
import hmac
import hashlib
import requests
import json
import sys
import os
from urllib.parse import urlencode

# PyInstaller 환경에서 certifi 인증서 경로 설정
if getattr(sys, 'frozen', False):
    # PyInstaller 임시폴더(_MEIPASS)는 Windows Temp 정리로 삭제될 수 있으므로
    # exe 실행 디렉토리에 인증서를 복사하여 안정적으로 유지
    import shutil
    bundle_cert = os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem')
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    stable_cert = os.path.join(exe_dir, 'cacert.pem')

    # 안정적 경로에 인증서가 없거나 번들 버전이 더 새로우면 복사
    if os.path.exists(bundle_cert):
        if not os.path.exists(stable_cert) or os.path.getsize(stable_cert) != os.path.getsize(bundle_cert):
            try:
                shutil.copy2(bundle_cert, stable_cert)
            except Exception:
                pass

    # 안정적 경로 우선, 없으면 번들 경로 사용
    cert_path = stable_cert if os.path.exists(stable_cert) else bundle_cert
    os.environ['SSL_CERT_FILE'] = cert_path
    os.environ['REQUESTS_CA_BUNDLE'] = cert_path

# =============================================================================
# Binance API Implementation
# =============================================================================

class BinanceAPI:
    """바이낸스 선물 API (USDⓈ-M / COIN-M)"""
    
    MARKET_URLS = {
        "fapi": "fapi.binance.com",  # USDⓈ-M
        "dapi": "dapi.binance.com"   # COIN-M
    }
    
    def __init__(self):
        self._active_key = None
        self._active_secret = None
        self._active_market = "fapi"
    
    def set_active_api_keys(self, api_key, api_secret):
        """API 키를 활성화합니다."""
        self._active_key = api_key
        self._active_secret = api_secret
        if api_key:
            print(f"Binance API Key가 활성화되었습니다: ...{api_key[-4:]}")
        else:
            print("Binance API Key가 비활성화되었습니다.")
    
    def is_api_key_active(self):
        """API 키가 활성화되어 있는지 확인합니다."""
        return self._active_key is not None
    
    def set_active_market(self, market_type="fapi"):
        """마켓 타입을 설정합니다 (fapi/dapi)."""
        if market_type in self.MARKET_URLS:
            self._active_market = market_type
            market_name = "USDⓈ-M" if market_type == "fapi" else "COIN-M"
            print(f"활성 마켓이 {market_type} ({market_name})로 설정되었습니다.")
        else:
            raise ValueError(f"지원되지 않는 마켓 타입: {market_type}")
    
    def _get_url(self, endpoint_path):
        """활성 마켓에 맞는 전체 URL을 반환합니다."""
        base_url = self.MARKET_URLS[self._active_market]
        
        # COIN-M (dapi)는 엔드포인트 버전이 다름
        if self._active_market == 'dapi':
            endpoint_path = endpoint_path.replace("/fapi/v2/", "/dapi/v1/").replace("/fapi/v1/", "/dapi/v1/")
        
        return f"https://{base_url}{endpoint_path}"
    
    def _send_signed_request(self, method, endpoint_path, params={}):
        """서명된 요청을 바이낸스에 전송합니다."""
        if not self._active_key or not self._active_secret:
            raise Exception("Binance API 키가 활성화되지 않았습니다.")
        
        session = requests.Session()
        session.headers.update({'X-MBX-APIKEY': self._active_key})
        
        params_copy = params.copy()
        params_copy['timestamp'] = int(time.time() * 1000)
        
        query_string = urlencode(params_copy)
        signature = hmac.new(
            self._active_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params_copy['signature'] = signature
        url = self._get_url(endpoint_path)
        
        try:
            if method == 'GET':
                response = session.get(url, params=params_copy)
            elif method == 'POST':
                response = session.post(url, params=params_copy)
            elif method == 'DELETE':
                response = session.delete(url, params=params_copy)
            
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            if e.response is not None:
                try:
                    return e.response.json()
                except json.JSONDecodeError:
                    print(f"Binance API 요청 오류 (JSON 디코딩 불가): {e.response.text}")
                    return {"code": e.response.status_code, "msg": e.response.text}
            
            print(f"Binance API 요청 오류 ({url}): {e}")
            return None

    def _send_algo_signed_request(self, method, endpoint_path, params={}):
        """Algo 주문 API용 서명된 요청 (api.binance.com 사용)."""
        if not self._active_key or not self._active_secret:
            raise Exception("Binance API 키가 활성화되지 않았습니다.")

        session = requests.Session()
        session.headers.update({'X-MBX-APIKEY': self._active_key})

        params_copy = params.copy()
        params_copy['timestamp'] = int(time.time() * 1000)

        query_string = urlencode(params_copy)
        signature = hmac.new(
            self._active_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        params_copy['signature'] = signature
        # Algo 주문은 api.binance.com 사용 (fapi/dapi가 아님)
        url = f"https://api.binance.com{endpoint_path}"

        try:
            if method == 'GET':
                response = session.get(url, params=params_copy)
            elif method == 'POST':
                response = session.post(url, params=params_copy)
            elif method == 'DELETE':
                response = session.delete(url, params=params_copy)

            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            if e.response is not None:
                try:
                    return e.response.json()
                except json.JSONDecodeError:
                    print(f"Binance Algo API 요청 오류 (JSON 디코딩 불가): {e.response.text}")
                    return {"code": e.response.status_code, "msg": e.response.text}
            raise

    def get_listen_key(self):
        """웹소켓 연결용 Listen Key를 발급받습니다."""
        print("Binance Listen Key 발급 시도...")
        data = self._send_signed_request('POST', '/fapi/v1/listenKey')
        if data and data.get('listenKey'):
            return data.get('listenKey')
        else:
            print(f"Listen Key 발급 실패: {data}")
            return None
    
    def get_initial_balance(self):
        """현재 계정 잔액 정보를 가져옵니다."""
        print("Binance 초기 잔액 정보 로드 중...")
        data = self._send_signed_request('GET', '/fapi/v2/balance')
        if data and isinstance(data, list):
            return data
        elif data and data.get('code'):
            print(f"Binance 잔액 정보 로드 실패 (API): {data.get('msg')}")
        return []
    
    def get_initial_positions(self):
        """현재 모든 포지션 정보를 가져옵니다."""
        print("Binance 초기 포지션 정보 로드 중...")
        data = self._send_signed_request('GET', '/fapi/v2/positionRisk')
        if data and isinstance(data, list):
            positions = [p for p in data if float(p.get('positionAmt', 0)) != 0]
            return positions
        return []
    
    def get_initial_open_orders(self):
        """현재 모든 미체결 주문을 가져옵니다 (일반 주문 + Algo 조건부 주문)."""
        print("Binance 초기 미체결 주문 로드 중 (일반 + Algo)...")

        orders = []
        normal_count = 0
        algo_count = 0

        # 1. 일반 주문 조회 (/fapi/v1/openOrders)
        normal_data = self._send_signed_request('GET', '/fapi/v1/openOrders')

        print(f"[디버그] 일반 주문 API 응답 타입: {type(normal_data)}, 길이: {len(normal_data) if isinstance(normal_data, list) else 'N/A'}")
        if normal_data and isinstance(normal_data, list):
            for o in normal_data:
                o['orderCategory'] = 'normal'
                orders.append(o)
                normal_count += 1
            print(f"✅ 일반 주문 조회 완료: {normal_count}개")
        else:
            print(f"⚠️ 일반 주문 조회 실패 - 응답: {normal_data}")

        # 2. Algo 조건부 주문 조회 (/sapi/v1/algo/futures/openOrders)
        # 2025년 12월 9일부터 Binance는 STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET 등을
        # Algo Order API로 분리했습니다.
        # 주의: algo 주문은 fapi가 아닌 api.binance.com의 /sapi/ 경로를 사용합니다.
        try:
            print(f"[디버그] Algo 주문 조회 요청 중... (endpoint: /sapi/v1/algo/futures/openOrders)")
            algo_data = self._send_algo_signed_request('GET', '/sapi/v1/algo/futures/openOrders')

            print(f"[디버그] Algo 주문 API 응답 타입: {type(algo_data)}")

            # 응답 형식: {total: N, orders: [...]}
            if algo_data and isinstance(algo_data, dict) and 'orders' in algo_data:
                algo_orders = algo_data.get('orders', [])
                total_count = algo_data.get('total', 0)
                print(f"[디버그] Algo 주문 총 개수: {total_count}개")

                if len(algo_orders) > 0:
                    print(f"[디버그] 첫 번째 Algo 주문 샘플: {algo_orders[0]}")

                for algo_order in algo_orders:
                    # Algo 주문을 일반 주문 형식으로 변환
                    normalized_order = {
                        'orderId': str(algo_order.get('algoId', '')),  # algoId를 orderId로 매핑
                        'symbol': algo_order.get('symbol', ''),
                        'type': algo_order.get('algoType', 'ALGO'),  # algoType 사용
                        'side': algo_order.get('side', ''),
                        'price': str(algo_order.get('avgPrice', '0')),  # avgPrice 사용
                        'origQty': str(algo_order.get('totalQty', '0')),
                        'executedQty': str(algo_order.get('executedQty', '0')),
                        'orderCategory': 'algo',
                        'algoStatus': algo_order.get('algoStatus', 'NEW'),
                        # 원본 데이터 보존
                        '_raw_algo_order': algo_order
                    }
                    orders.append(normalized_order)
                    algo_count += 1
                print(f"✅ Algo 조건부 주문 조회 완료: {algo_count}개")
            else:
                print(f"⚠️ Algo 주문 조회 실패 - 응답: {algo_data}")
        except Exception as e:
            print(f"⚠️ Algo 주문 조회 중 오류: {e}")

        if len(orders) == 0:
            print("✅ 미체결 주문 없음")
            return []

        print(f"✅ 총 미체결 주문: {len(orders)}개 (일반: {normal_count}개, Algo: {algo_count}개)")
        return orders
    
    def place_market_order(self, symbol, side, quantity, reduce_only=False, position_side="BOTH"):
        """시장가 주문을 전송합니다."""
        print(f"Binance 시장가 주문 요청: {side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET',
            'quantity': quantity,
            'positionSide': position_side
        }
        
        data = self._send_signed_request('POST', '/fapi/v1/order', params)
        return data
    
    def cancel_order(self, symbol, order_id, order_category='normal'):
        """특정 주문을 취소합니다."""
        print(f"Binance 주문 취소 요청: {symbol} (OrderID: {order_id}, Type: {order_category})")

        if order_category == 'algo':
            # Algo 주문 취소 (/sapi/v1/algo/futures/order)
            params = {
                'algoId': order_id,  # algo 주문은 algoId만 필요 (symbol 불필요)
            }
            data = self._send_algo_signed_request('DELETE', '/sapi/v1/algo/futures/order', params)
            print(f"✅ Algo 주문 취소 응답: {data}")
            return data
        else:
            # 일반 주문 취소
            params = {
                'symbol': symbol,
                'orderId': order_id,
            }
            data = self._send_signed_request('DELETE', '/fapi/v1/order', params)
            return data
    
    def get_ohlcv_data(self, symbol, interval='1h', limit=500):
        """(공개 API) OHLCV 캔들 데이터를 가져옵니다."""
        if self._active_market == "dapi":
            base_url = "https://dapi.binance.com"
            endpoint = "/dapi/v1/klines"
        else:
            base_url = "https://fapi.binance.com"
            endpoint = "/fapi/v1/klines"
        
        url = f"{base_url}{endpoint}"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as e:
            print(f"Binance OHLCV 데이터 요청 오류 ({url}): {e}")
            if e.response is not None:
                print(f"오류 응답: {e.response.json()}")
            return None


# =============================================================================
# Bybit API Implementation
# =============================================================================

class BybitAPI:
    """Bybit V5 선물 API (Linear / Inverse)"""

    BASE_URL = "https://api.bybit.com"

    def __init__(self):
        self._active_key = None
        self._active_secret = None
        self._active_category = "linear"  # linear or inverse
        self._recv_window = 60000  # 60초 (시간 동기화 여유 확보)
        self._symbol_info_cache = {}  # 심볼별 거래 규칙 캐시
    
    def set_active_api_keys(self, api_key, api_secret):
        """API 키를 활성화합니다."""
        self._active_key = api_key
        self._active_secret = api_secret
        if api_key:
            print(f"Bybit API Key가 활성화되었습니다: ...{api_key[-4:]}")
        else:
            print("Bybit API Key가 비활성화되었습니다.")
    
    def is_api_key_active(self):
        """API 키가 활성화되어 있는지 확인합니다."""
        return self._active_key is not None
    
    def set_active_market(self, market_type="fapi"):
        """
        마켓 타입을 설정합니다.
        'fapi' (USDⓈ-M) -> 'linear' (USDT Perpetual)
        'dapi' (COIN-M) -> 'inverse' (Inverse Perpetual)
        """
        if market_type == "dapi":
            self._active_category = "inverse"
            print(f"활성 마켓이 {market_type} (Bybit: inverse)로 설정되었습니다.")
        else:
            self._active_category = "linear"
            print(f"활성 마켓이 {market_type} (Bybit: linear)로 설정되었습니다.")
    
    def _send_signed_request(self, method, endpoint_path, params={}):
        """서명된 요청을 Bybit V5에 전송합니다."""
        if not self._active_key or not self._active_secret:
            print("Bybit API 키가 활성화되지 않았습니다.")
            return {"retCode": -999, "retMsg": "API Key not set"}

        session = requests.Session()
        timestamp = str(int(time.time() * 1000))
        recv_window = str(self._recv_window)
        
        headers = {
            'X-BAPI-API-KEY': self._active_key,
            'X-BAPI-TIMESTAMP': timestamp,
            'X-BAPI-RECV-WINDOW': recv_window,
        }
        
        try:
            if method == 'GET':
                if params:
                    sorted_params = sorted(params.items())
                    query_string = urlencode(sorted_params)
                else:
                    query_string = ""
                
                sign_payload = timestamp + self._active_key + recv_window + query_string
                signature = hmac.new(
                    self._active_secret.encode('utf-8'),
                    sign_payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                headers['X-BAPI-SIGN'] = signature
                # 서명에 사용된 query_string과 동일한 순서로 URL 구성 (params 대신 직접 URL에 붙임)
                if query_string:
                    url = f"{self.BASE_URL}{endpoint_path}?{query_string}"
                else:
                    url = f"{self.BASE_URL}{endpoint_path}"
                response = session.get(url, headers=headers)
            
            elif method == 'POST':
                if params:
                    body_string = json.dumps(params, separators=(',', ':'))
                else:
                    body_string = ""
                
                sign_payload = timestamp + self._active_key + recv_window + body_string
                signature = hmac.new(
                    self._active_secret.encode('utf-8'),
                    sign_payload.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                
                headers['X-BAPI-SIGN'] = signature
                headers['Content-Type'] = 'application/json'
                response = session.post(f"{self.BASE_URL}{endpoint_path}", data=body_string, headers=headers)
            
            response.raise_for_status()
            return response.json()
        
        except requests.RequestException as e:
            if e.response is not None:
                print(f"[ERROR] Bybit API 오류 (HTTP {e.response.status_code}): {e.response.text}")
                try:
                    return e.response.json()
                except json.JSONDecodeError:
                    return {"retCode": e.response.status_code, "retMsg": e.response.text}
            
            print(f"[ERROR] Bybit 네트워크 오류 ({endpoint_path}): {e}")
            return {"retCode": -1000, "retMsg": str(e)}
    
    def get_listen_key(self):
        """Bybit는 Listen Key를 사용하지 않습니다. (WebSocket Auth 방식 사용)"""
        raise NotImplementedError(
            "Bybit API는 Listen Key 모델을 사용하지 않습니다. "
            "WebSocket 인증 로직을 수정해야 합니다."
        )
    
    def get_initial_balance(self):
        """현재 계정 잔액 정보를 가져옵니다."""
        print("Bybit 초기 잔액 정보 로드 중...")
        params = {"accountType": "UNIFIED"}
        data = self._send_signed_request('GET', '/v5/account/wallet-balance', params)
        
        if data and data.get('retCode') == 0:
            balance_list = []
            if data['result'].get('list'):
                for coin_balance in data['result']['list'][0]['coin']:
                    balance_list.append({
                        'asset': coin_balance['coin'],
                        'balance': coin_balance['walletBalance']
                    })
            return balance_list
        
        print(f"Bybit 잔액 정보 로드 실패 (retCode: {data.get('retCode')}): {data.get('retMsg', 'Unknown error')}")
        return []
    
    def get_usdt_balance(self, account_type="UNIFIED"):
        """USDT 잔액만 float로 반환합니다.

        Args:
            account_type: "UNIFIED" 또는 "FUND"
        """
        if account_type == "FUND":
            params = {"accountType": "FUND", "coin": "USDT"}
            data = self._send_signed_request('GET', '/v5/asset/transfer/query-account-coins-balance', params)
            if data and data.get('retCode') == 0:
                for coin_info in data['result'].get('balance', []):
                    if coin_info['coin'] == 'USDT':
                        return float(coin_info['walletBalance'])
        else:
            params = {"accountType": "UNIFIED"}
            data = self._send_signed_request('GET', '/v5/account/wallet-balance', params)
            if data and data.get('retCode') == 0:
                if data['result'].get('list'):
                    for coin_balance in data['result']['list'][0]['coin']:
                        if coin_balance['coin'] == 'USDT':
                            return float(coin_balance['walletBalance'])
        return 0.0

    def get_uid(self):
        """계정 UID를 조회합니다."""
        data = self._send_signed_request('GET', '/v5/user/query-api')
        if data and data.get('retCode') == 0:
            uid = data['result'].get('userID')
            print(f"Bybit UID 조회 성공: {uid}")
            return str(uid)
        print(f"Bybit UID 조회 실패: {data.get('retMsg', 'Unknown error')}")
        return None

    def transfer_between_accounts(self, coin, amount, from_type, to_type):
        """내부 계좌 간 전환 (UNIFIED ↔ FUND)

        Returns:
            (success: bool, message: str)
        """
        import uuid
        params = {
            "transferId": str(uuid.uuid4()),
            "coin": coin,
            "amount": str(amount),
            "fromAccountType": from_type,
            "toAccountType": to_type
        }
        print(f"Bybit {from_type} → {to_type} 전환: {coin} {amount}")
        data = self._send_signed_request('POST', '/v5/asset/transfer/inter-transfer', params)
        print(f"Bybit 계좌 전환 응답: {data}")
        if data and data.get('retCode') == 0:
            print(f"Bybit {from_type} → {to_type} 전환 성공")
            return True, f"{from_type} → {to_type} successful"
        error_msg = data.get('retMsg', 'Unknown error') if data else 'No response'
        print(f"Bybit {from_type} → {to_type} 전환 실패: {error_msg}")
        return False, error_msg

    def withdraw_internal(self, coin, amount, to_uid, account_type="FUND"):
        """UID 기반 Bybit 내부 이체 (수수료 없음)

        Args:
            coin: 코인 종류 (예: "USDT")
            amount: 이체 수량 (문자열)
            to_uid: 수신자 UID
            account_type: 출금 지갑 ("FUND" 또는 "UNIFIED")

        Returns:
            (success: bool, message: str)
        """
        # UNIFIED 선택 시: 먼저 FUND로 전환 후 FUND에서 출금
        if account_type == "UNIFIED":
            success, msg = self.transfer_between_accounts(coin, amount, "UNIFIED", "FUND")
            if not success:
                return False, f"UNIFIED→FUND 전환 실패: {msg}"

        params = {
            "coin": coin,
            "address": str(to_uid),
            "amount": str(amount),
            "accountType": "FUND",
            "forceChain": 2,
            "timestamp": int(time.time() * 1000)
        }
        print(f"Bybit 내부 이체 요청: {coin} {amount} → UID {to_uid}")
        data = self._send_signed_request('POST', '/v5/asset/withdraw/create', params)
        if data and data.get('retCode') == 0:
            withdraw_id = data['result'].get('id', '')
            print(f"Bybit 내부 이체 성공: ID={withdraw_id}")
            return True, f"Transfer successful (ID: {withdraw_id})"
        error_msg = data.get('retMsg', 'Unknown error') if data else 'No response'
        print(f"Bybit 내부 이체 실패: {error_msg}")
        return False, error_msg

    def get_initial_positions(self):
        """현재 모든 포지션 정보를 가져옵니다."""
        print("Bybit 초기 포지션 정보 로드 중...")
        settle_coin = "USDT" if self._active_category == "linear" else "BTC"
        
        params = {
            "category": self._active_category,
            "settleCoin": settle_coin
        }
        data = self._send_signed_request('GET', '/v5/position/list', params)
        
        if data and data.get('retCode') == 0:
            positions = []
            for p in data['result']['list']:
                size = float(p.get('size', 0))
                if size == 0:
                    continue

                # Bybit positionIdx로 헤지 모드 구분
                # 0 = One-Way Mode, 1 = Hedge Mode Buy(Long), 2 = Hedge Mode Sell(Short)
                position_idx = int(p.get('positionIdx', 0))
                side = p.get('side', 'None')

                # 헤지 모드일 때 positionSide 결정
                if position_idx == 1:
                    position_side = 'LONG'
                elif position_idx == 2:
                    position_side = 'SHORT'
                else:
                    # One-Way Mode: side 기반으로 결정
                    position_side = 'LONG' if side == 'Buy' else 'SHORT' if side == 'Sell' else 'BOTH'

                # Binance 형식: LONG은 양수, SHORT는 음수
                position_amt = size if position_side == 'LONG' else -size

                positions.append({
                    'symbol': p['symbol'],
                    'positionAmt': str(position_amt),
                    'entryPrice': p['avgPrice'],
                    'unRealizedProfit': p['unrealisedPnl'],
                    'initialMargin': p.get('positionIM', '0'),  # positionMargin -> positionIM
                    'positionSide': position_side,
                    'liqPrice': p.get('liqPrice', '0'),  # 청산가 추가
                    'markPrice': p.get('markPrice', '0')  # 마크 가격 추가 (PNL 계산용)
                })
            return positions
        
        print(f"Bybit 포지션 정보 로드 실패 (retCode: {data.get('retCode')}): {data.get('retMsg', 'Unknown error')}")
        return []
    
    def get_initial_open_orders(self):
        """현재 모든 미체결 주문을 가져옵니다 (일반 주문 + Conditional 주문)."""
        print("Bybit 초기 미체결 주문 로드 중 (일반 + Conditional)...")
        settle_coin = "USDT" if self._active_category == "linear" else "BTC"

        orders = []
        normal_count = 0
        conditional_count = 0

        # 1. 일반 주문 조회 (/v5/order/realtime - orderFilter="Order")
        params = {
            "category": self._active_category,
            "settleCoin": settle_coin,
            "orderFilter": "Order"  # 일반 주문만
        }
        data = self._send_signed_request('GET', '/v5/order/realtime', params)

        if data and data.get('retCode') == 0:
            for o in data['result']['list']:
                orders.append({
                    'symbol': o['symbol'],
                    'type': o['orderType'],
                    'side': o['side'],
                    'price': o['price'],
                    'origQty': o['qty'],
                    'executedQty': o.get('cumExecQty', '0'),
                    'orderId': o['orderId'],
                    'orderCategory': 'normal'
                })
                normal_count += 1
            print(f"✅ 일반 주문 (Basic): {normal_count}개")
        else:
            print(f"⚠️ 일반 주문 로드 실패 (retCode: {data.get('retCode')}): {data.get('retMsg', 'Unknown error')}")

        # 2. 조건부 주문 조회 (Conditional: Stop, Trailing Stop 등)
        try:
            conditional_params = {
                "category": self._active_category,
                "settleCoin": settle_coin,
                "orderFilter": "StopOrder"  # Conditional orders만
            }
            conditional_data = self._send_signed_request('GET', '/v5/order/realtime', conditional_params)

            if conditional_data and conditional_data.get('retCode') == 0:
                for o in conditional_data['result']['list']:
                    orders.append({
                        'symbol': o['symbol'],
                        'type': o.get('stopOrderType', o.get('orderType', 'Unknown')),
                        'side': o['side'],
                        'price': o.get('triggerPrice', o.get('price', '0')),
                        'origQty': o['qty'],
                        'executedQty': o.get('cumExecQty', '0'),
                        'orderId': o['orderId'],
                        'orderCategory': 'conditional'
                    })
                    conditional_count += 1
                print(f"✅ 조건부 주문 (Conditional): {conditional_count}개")
            else:
                print(f"⚠️ 조건부 주문 없음 또는 조회 실패")
        except Exception as e:
            print(f"⚠️ 조건부 주문 조회 오류: {e}")

        print(f"📊 총 미체결 주문: {len(orders)}개 (일반: {normal_count}, 조건부: {conditional_count})")
        return orders
    
    def place_market_order(self, symbol, side, quantity, reduce_only=False, position_side="BOTH"):
        """시장가 주문을 전송합니다."""
        # 수량 포맷 적용 (심볼별 정밀도 규칙에 맞게)
        formatted_qty = self.format_quantity(symbol, quantity)

        print(f"Bybit 시장가 주문 요청: {side} {formatted_qty} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")

        # Bybit API는 "Buy" 또는 "Sell" 형식 요구 (첫 글자만 대문자)
        # Binance 형식 "BUY", "SELL"을 Bybit 형식으로 변환
        bybit_side = side.capitalize()  # "BUY" -> "Buy", "SELL" -> "Sell"

        # positionIdx: 0=One-Way, 1=Hedge Long, 2=Hedge Short
        position_idx = 0
        if position_side == "LONG":
            position_idx = 1
        elif position_side == "SHORT":
            position_idx = 2

        params = {
            'category': self._active_category,
            'symbol': symbol,
            'side': bybit_side,
            'orderType': 'Market',
            'qty': formatted_qty,
            'reduceOnly': reduce_only,
            'positionIdx': position_idx
        }

        data = self._send_signed_request('POST', '/v5/order/create', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to place order')}

    def place_limit_order(self, symbol, side, quantity, price, reduce_only=False, position_side="BOTH"):
        """지정가 주문을 전송합니다."""
        # 수량 포맷 적용 (심볼별 정밀도 규칙에 맞게)
        formatted_qty = self.format_quantity(symbol, quantity)

        print(f"Bybit 지정가 주문 요청: {side} {formatted_qty} {symbol} @ ${price} (reduceOnly={reduce_only}, positionSide={position_side})")

        # Bybit API는 "Buy" 또는 "Sell" 형식 요구 (첫 글자만 대문자)
        bybit_side = side.capitalize()  # "BUY" -> "Buy", "SELL" -> "Sell"

        # positionIdx: 0=One-Way, 1=Hedge Long, 2=Hedge Short
        position_idx = 0
        if position_side == "LONG":
            position_idx = 1
        elif position_side == "SHORT":
            position_idx = 2

        params = {
            'category': self._active_category,
            'symbol': symbol,
            'side': bybit_side,
            'orderType': 'Limit',
            'qty': formatted_qty,
            'price': str(price),
            'reduceOnly': reduce_only,
            'positionIdx': position_idx
        }

        data = self._send_signed_request('POST', '/v5/order/create', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to place limit order')}

    def place_stop_loss_order(self, symbol, side, quantity, stop_loss_price, position_side="BOTH"):
        """Stop Loss 주문을 전송합니다."""
        # 수량 포맷 적용 (심볼별 정밀도 규칙에 맞게)
        formatted_qty = self.format_quantity(symbol, quantity)

        print(f"Bybit Stop Loss 주문 요청: {side} {formatted_qty} {symbol} @ Stop=${stop_loss_price} (positionSide={position_side})")

        # Bybit API는 "Buy" 또는 "Sell" 형식 요구 (첫 글자만 대문자)
        bybit_side = side.capitalize()  # "BUY" -> "Buy", "SELL" -> "Sell"

        # positionIdx: 0=One-Way, 1=Hedge Long, 2=Hedge Short
        position_idx = 0
        if position_side == "LONG":
            position_idx = 1
        elif position_side == "SHORT":
            position_idx = 2

        params = {
            'category': self._active_category,
            'symbol': symbol,
            'side': bybit_side,
            'orderType': 'Market',  # Stop Loss는 Market 타입으로 발동
            'qty': formatted_qty,
            'stopLoss': str(stop_loss_price),
            'reduceOnly': True,  # Stop Loss는 항상 포지션 청산용
            'positionIdx': position_idx
        }

        data = self._send_signed_request('POST', '/v5/order/create', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to place stop loss order')}

    def place_trailing_stop_order(self, symbol, side, quantity, activation_price, callback_rate, position_side="BOTH"):
        """Trailing Stop 주문을 전송합니다.

        Args:
            symbol: 거래 심볼
            side: 주문 방향 (BUY/SELL)
            quantity: 수량
            activation_price: 트레일링 스탑 활성화 가격
            callback_rate: 콜백 비율 (%, 예: "0.5")
            position_side: 포지션 방향 (LONG/SHORT/BOTH)
        """
        # 수량 포맷 적용 (심볼별 정밀도 규칙에 맞게)
        formatted_qty = self.format_quantity(symbol, quantity)

        print(f"Bybit Trailing Stop 주문 요청: {side} {formatted_qty} {symbol} @ Activation=${activation_price}, Callback={callback_rate}% (positionSide={position_side})")

        # Bybit API는 "Buy" 또는 "Sell" 형식 요구 (첫 글자만 대문자)
        bybit_side = side.capitalize()  # "BUY" -> "Buy", "SELL" -> "Sell"

        # positionIdx: 0=One-Way, 1=Hedge Long, 2=Hedge Short
        position_idx = 0
        if position_side == "LONG":
            position_idx = 1
        elif position_side == "SHORT":
            position_idx = 2

        params = {
            'category': self._active_category,
            'symbol': symbol,
            'side': bybit_side,
            'orderType': 'Market',  # Trailing Stop은 시장가로 체결
            'qty': formatted_qty,
            'triggerPrice': str(activation_price),  # 활성화 가격
            'triggerBy': 'LastPrice',  # 마지막 거래 가격 기준
            'trailingStop': str(callback_rate),  # 콜백 비율 (%)
            'reduceOnly': True,  # Trailing Stop은 항상 포지션 청산용
            'positionIdx': position_idx
        }

        data = self._send_signed_request('POST', '/v5/order/create', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to place trailing stop order')}

    def place_stop_market_order(self, symbol, side, quantity, stop_price, reduce_only=False, position_side="BOTH"):
        """STOP MARKET 주문을 전송합니다 (조건부 주문).

        Args:
            symbol: 거래 심볼
            side: 주문 방향 (BUY/SELL)
            quantity: 수량
            stop_price: 트리거 가격 (이 가격 도달 시 시장가 주문 발동)
            reduce_only: 포지션 청산 전용 여부
            position_side: 포지션 방향 (LONG/SHORT/BOTH)
        """
        # 수량 포맷 적용
        formatted_qty = self.format_quantity(symbol, quantity)

        print(f"Bybit STOP MARKET 주문 요청: {side} {formatted_qty} {symbol} @ Stop=${stop_price} (reduceOnly={reduce_only}, positionSide={position_side})")

        # Bybit API는 "Buy" 또는 "Sell" 형식 요구
        bybit_side = side.capitalize()

        # positionIdx: 0=One-Way, 1=Hedge Long, 2=Hedge Short
        position_idx = 0
        if position_side == "LONG":
            position_idx = 1
        elif position_side == "SHORT":
            position_idx = 2

        # triggerDirection: 1=Rising (상승), 2=Falling (하락)
        # SHORT 청산용 BUY STOP: 가격이 상승하면 트리거 (1)
        # LONG 청산용 SELL STOP: 가격이 하락하면 트리거 (2)
        trigger_direction = 1 if side.upper() == "BUY" else 2

        params = {
            'category': self._active_category,
            'symbol': symbol,
            'side': bybit_side,
            'orderType': 'Market',  # 시장가로 체결
            'qty': formatted_qty,
            'triggerPrice': str(stop_price),  # 트리거 가격
            'triggerDirection': trigger_direction,  # 트리거 방향 (필수)
            'triggerBy': 'LastPrice',  # 마지막 거래 가격 기준
            'reduceOnly': reduce_only,
            'positionIdx': position_idx
        }

        data = self._send_signed_request('POST', '/v5/order/create', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to place stop market order')}

    def cancel_order(self, symbol, order_id, order_category='normal'):
        """특정 주문을 취소합니다."""
        print(f"Bybit 주문 취소 요청: {symbol} (OrderID: {order_id}, Type: {order_category})")

        # Bybit V5 API는 일반 주문과 조건부 주문 모두 동일한 엔드포인트 사용
        params = {
            'category': self._active_category,
            'symbol': symbol,
            'orderId': order_id,
        }

        data = self._send_signed_request('POST', '/v5/order/cancel', params)

        if data and data.get('retCode') == 0:
            return {"orderId": data['result'].get('orderId')}
        else:
            return {"code": data.get('retCode'), "msg": data.get('retMsg', 'Failed to cancel order')}
    
    def get_ohlcv_data(self, symbol, interval='1h', limit=500):
        """(공개 API) OHLCV 캔들 데이터를 가져옵니다."""
        mapped_interval = self._map_interval(interval)
        
        params = {
            'category': self._active_category,
            'symbol': symbol,
            'interval': mapped_interval,
            'limit': limit
        }
        
        url = f"{self.BASE_URL}/v5/market/kline"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('retCode') == 0 and data['result'].get('list'):
                klines = []
                for k in data['result']['list']:
                    klines.append([
                        k[0], k[1], k[2], k[3], k[4], k[5],
                        "0", k[6], "0", "0", "0", "0"
                    ])

                klines.reverse()

                return klines
            else:
                print(f"Bybit OHLCV 데이터 오류: {data.get('retMsg')}")
                return None
        
        except requests.RequestException as e:
            print(f"Bybit OHLCV 데이터 요청 오류 ({url}): {e}")
            return None
    
    def get_server_time(self):
        """(공개 API) Bybit 서버의 현재 시간을 가져옵니다."""
        url = f"{self.BASE_URL}/v5/market/time"
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            if data.get('retCode') == 0 and data['result'].get('timeNano'):
                return int(data['result']['timeNano']) // 1000000
            else:
                print(f"Bybit 서버 시간 로드 실패: {data.get('retMsg')}")
                return None
        except Exception as e:
            print(f"Bybit 서버 시간 요청 오류: {e}")
            return None
    
    def _map_interval(self, interval):
        """Binance 인터벌을 Bybit V5 인터벌로 변환합니다."""
        mapping = {
            '1m': '1', '3m': '3', '5m': '5', '15m': '15', '30m': '30',
            '1h': '60', '2h': '120', '4h': '240', '6h': '360', '12h': '720',
            '1d': 'D', '1w': 'W', '1M': 'M'
        }
        return mapping.get(interval, '60')

    def set_position_mode(self, category, symbol, mode=3):
        """
        포지션 모드를 설정합니다.
        mode: 0 = Merged Single (One-Way Mode), 3 = Both Sides (Hedge Mode)
        """
        params = {
            'category': category,
            'symbol': symbol,
            'mode': mode
        }

        result = self._send_signed_request('POST', '/v5/position/switch-mode', params)

        if result.get('retCode') == 0:
            mode_str = "Hedge Mode" if mode == 3 else "One-Way Mode"
            print(f"Bybit 포지션 모드 설정 성공: {mode_str}")
            return True
        elif result.get('retCode') == 110025:
            # 이미 해당 모드로 설정되어 있음
            print(f"Bybit 포지션 모드 이미 설정됨")
            return True
        else:
            print(f"Bybit 포지션 모드 설정 실패: {result.get('retMsg')}")
            return False

    def set_leverage(self, category, symbol, leverage=15):
        """
        레버리지만 설정합니다 (마진 모드는 별도 함수에서 설정).
        """
        params = {
            'category': category,
            'symbol': symbol,
            'buyLeverage': str(leverage),
            'sellLeverage': str(leverage)
        }

        print(f"[API] 레버리지 설정 요청: {leverage}x (symbol={symbol})")
        result = self._send_signed_request('POST', '/v5/position/set-leverage', params)

        print(f"[API] 레버리지 설정 응답: retCode={result.get('retCode')}, retMsg={result.get('retMsg')}")

        if result.get('retCode') == 0:
            print(f"Bybit 레버리지 설정 성공: {leverage}x")
            return True

        # "leverage not modified" - 이미 설정됨
        ret_msg = result.get('retMsg', '')
        if 'leverage not modified' in ret_msg.lower():
            print(f"Bybit 레버리지 이미 설정됨: {leverage}x")
            return True

        # 실제 오류
        print(f"[오류] Bybit 레버리지 설정 실패: {ret_msg}")
        return False

    def set_margin_and_leverage(self, category, symbol, margin_mode=1, leverage=15):
        """
        (통합 계정용) 마진 모드와 레버리지를 설정합니다.
        margin_mode: 0 = Cross Margin, 1 = Isolated Margin

        Bybit UTA 계정은 /v5/position/set-leverage API 하나로
        tradeMode와 leverage를 동시에 설정해야 합니다.

        [버그 우회]
        이미 해당 레버리지로 설정된 경우 "leverage not modified"가 반환되며
        tradeMode 변경이 무시될 수 있습니다.
        이를 우회하기 위해, 다른 레버리지(예: 20)로 1단계 설정 후,
        목표 레버리지로 2단계 설정을 수행합니다.
        """
        margin_str = "Isolated Margin" if margin_mode == 1 else "Cross Margin"

        # 1단계: 임시 레버리지 (예: 20x)로 마진 모드 강제 변경
        temp_leverage = 20
        if leverage == 20:  # 사용자가 20을 타겟으로 할 경우
            temp_leverage = 21

        params_temp = {
            'category': category,
            'symbol': symbol,
            'tradeMode': margin_mode,
            'buyLeverage': str(temp_leverage),
            'sellLeverage': str(temp_leverage)
        }

        print(f"[API] 마진/레버리지 설정 1단계: {margin_str} + 임시 레버리지 {temp_leverage}x")
        result_temp = self._send_signed_request('POST', '/v5/position/set-leverage', params_temp)
        print(f"[API] 1단계 응답: retCode={result_temp.get('retCode')}, retMsg={result_temp.get('retMsg')}")

        ret_msg_temp = result_temp.get('retMsg', '')
        if result_temp.get('retCode') != 0 and 'leverage not modified' not in ret_msg_temp:
            # "leverage not modified"가 아닌 실제 오류 (예: 포지션 보유 중)
            print(f"[오류] Bybit 마진 모드 설정 1단계 실패: {ret_msg_temp}")
            if 'position' in ret_msg_temp.lower():
                print(f"[오류] 포지션이 존재하면 마진 모드를 변경할 수 없습니다.")
            return False
        
        # 2단계: 원래 레버리지로 복원 (마진 모드 재전송)
        params_final = {
            'category': category,
            'symbol': symbol,
            'tradeMode': margin_mode,
            'buyLeverage': str(leverage),
            'sellLeverage': str(leverage)
        }

        print(f"[API] 마진/레버리지 설정 2단계: 원래 레버리지 {leverage}x로 복원")
        result_final = self._send_signed_request('POST', '/v5/position/set-leverage', params_final)
        print(f"[API] 2단계 응답: retCode={result_final.get('retCode')}, retMsg={result_final.get('retMsg')}")

        ret_msg_final = result_final.get('retMsg', '')
        if result_final.get('retCode') == 0 or 'leverage not modified' in ret_msg_final.lower():
            # 2단계가 성공하거나, "not modified" (이미 1단계에서 성공적으로 15x로 변경됨)
            print(f"Bybit 마진 모드 및 레버리지 설정 완료: {margin_str} (레버리지 {leverage}x)")
            return True
        else:
            print(f"[오류] Bybit 마진 모드 및 레버리지 설정 2단계 실패: {ret_msg_final}")
            return False
        
    def get_instrument_info(self, category, symbol):
        """
        거래 규칙(Instrument Info)을 조회합니다.
        """
        # 캐시에서 확인
        cache_key = f"{category}:{symbol}"
        if cache_key in self._symbol_info_cache:
            return self._symbol_info_cache[cache_key]

        params = {
            'category': category,
            'symbol': symbol
        }

        url = f"{self.BASE_URL}/v5/market/instruments-info"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('retCode') == 0 and data['result'].get('list'):
                info = data['result']['list'][0]
                # 캐시 저장
                self._symbol_info_cache[cache_key] = info
                return info
            else:
                print(f"Bybit Instrument Info 조회 실패: {data.get('retMsg')}")
                return None

        except requests.RequestException as e:
            print(f"Bybit Instrument Info 요청 오류: {e}")
            return None

    def format_quantity(self, symbol, quantity):
        """
        심볼별 수량 정밀도 규칙에 맞게 수량을 포맷합니다.

        Args:
            symbol: 거래 심볼 (예: XRPUSDT)
            quantity: 원본 수량 (float 또는 str)

        Returns:
            str: 포맷된 수량 문자열
        """
        try:
            qty_float = float(quantity)

            # Instrument Info 조회
            info = self.get_instrument_info(self._active_category, symbol)
            if not info:
                print(f"[WARNING] {symbol} 심볼 정보를 가져올 수 없어 수량을 그대로 사용합니다: {quantity}")
                return str(quantity)

            # lotSizeFilter에서 qtyStep 확인
            lot_size_filter = info.get('lotSizeFilter', {})
            qty_step = lot_size_filter.get('qtyStep')

            if not qty_step:
                print(f"[WARNING] {symbol}의 qtyStep을 찾을 수 없어 수량을 그대로 사용합니다: {quantity}")
                return str(quantity)

            # qtyStep 단위로 내림 처리 (모든 경우에 decimal 사용)
            import decimal
            decimal.getcontext().rounding = decimal.ROUND_DOWN

            qty_decimal = decimal.Decimal(str(qty_float))
            step_decimal = decimal.Decimal(str(qty_step))

            # 내림 처리 (qtyStep의 배수로)
            formatted_qty = (qty_decimal // step_decimal) * step_decimal

            # 소수점 자릿수 계산
            step_float = float(qty_step)
            if step_float >= 1:
                # qtyStep이 1 이상이면 소수점 1자리 (예: qtyStep="1" -> 4.74 -> 4.7)
                formatted_str = f"{float(formatted_qty):.1f}"
            else:
                # qtyStep이 1 미만이면 qtyStep의 소수점 자릿수만큼 (예: qtyStep="0.01" -> 4.747 -> 4.74)
                decimal_places = abs(decimal.Decimal(str(step_float)).as_tuple().exponent)
                formatted_str = f"{formatted_qty:.{decimal_places}f}"

            print(f"[Qty Format] {symbol}: {quantity} -> {formatted_str} (qtyStep={qty_step})")
            return formatted_str

        except Exception as e:
            print(f"[ERROR] 수량 포맷 중 오류 발생 ({symbol}, {quantity}): {e}")
            return str(quantity)

    def get_mark_price(self, category, symbol):
        """
        마크 프라이스를 조회합니다.
        """
        params = {
            'category': category,
            'symbol': symbol
        }

        url = f"{self.BASE_URL}/v5/market/tickers"

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get('retCode') == 0 and data['result'].get('list'):
                mark_price = data['result']['list'][0].get('markPrice')
                if mark_price:
                    return float(mark_price)

            print(f"Bybit Mark Price 조회 실패: {data.get('retMsg')}")
            return None

        except requests.RequestException as e:
            print(f"Bybit Mark Price 요청 오류: {e}")
            return None


# =============================================================================
# NOTE: v7_dual에서는 글로벌 싱글톤 패턴을 제거했습니다.
# 각 패널(LONG/SHORT)이 독립적인 API 인스턴스를 생성하여 사용합니다.
# BinanceAPI()와 BybitAPI() 클래스를 직접 인스턴스화하여 사용하세요.
# =============================================================================