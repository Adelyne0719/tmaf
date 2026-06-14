import time
import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode

# 마켓별 API 엔드포인트
MARKET_URLS = {
    "fapi": "fapi.binance.com", # USDⓈ-M
    "dapi": "dapi.binance.com"  # COIN-M
}
CONFIG_FILE = "api_config.json"

# 프로그램 실행 시간 동안 활성화된 API 키 및 마켓
_active_key = None
_active_secret = None
_active_market = "fapi" # 기본값
_symbol_info_cache = {}

def load_config_data():
    """'api_config.json'에서 계정 정보 및 앱 설정을 읽어옵니다."""
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
            # 이전 버전 호환: accounts 키가 없으면 변환
            if "accounts" not in data and "app_settings" not in data:
                print("이전 버전 config 감지. 'accounts' 키 하위로 마이그레이션합니다.")
                return {"accounts": data, "app_settings": {}}
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # 기본 구조 반환
        return {"accounts": {}, "app_settings": {}}

def save_config_data(config_data):
    """계정 정보 및 앱 설정을 'api_config.json'에 저장합니다."""
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config_data, f, indent=4)
        print("Config 정보가 JSON에 저장되었습니다.")
    except Exception as e:
        print(f"Config 정보 저장 오류: {e}")

def set_active_api_keys(api_key, api_secret):
    """요청에 사용할 API 키를 활성화합니다."""
    global _active_key, _active_secret
    _active_key = api_key
    _active_secret = api_secret
    if api_key:
        print(f"API Key가 활성화되었습니다: ...{api_key[-4:]}")
    else:
        print("API Key가 비활성화되었습니다.")

def is_api_key_active():
    """API 키가 현재 활성화(연결)되어 있는지 확인합니다."""
    global _active_key
    return _active_key is not None

def set_active_market(market_type="fapi"):
    """'fapi' 또는 'dapi' 중 활성 마켓을 설정합니다."""
    global _active_market
    if market_type in MARKET_URLS:
        _active_market = market_type
        print(f"활성 마켓이 {market_type} (COIN-M)" if market_type == "dapi" else f"활성 마켓이 {market_type} (USDⓈ-M)" )
    else:
        raise ValueError(f"지원되지 않는 마켓 타입: {market_type}")

def _get_url(endpoint_path):
    """활성 마켓에 맞는 전체 URL을 반환합니다."""
    base_url = MARKET_URLS[_active_market]
    
    # COIN-M (dapi)는 엔드포인트 버전이 다릅니다.
    if _active_market == 'dapi':
        endpoint_path = endpoint_path.replace("/fapi/v2/", "/dapi/v1/").replace("/fapi/v1/", "/dapi/v1/")
        
    return f"https://{base_url}{endpoint_path}"


def _send_signed_request(method, endpoint_path, params={}):
    """활성화된 API 키와 마켓으로 바이낸스에 서명된 요청을 보냅니다."""
    global _active_key, _active_secret
    
    if not _active_key or not _active_secret:
        raise Exception("API 키가 활성화되지 않았습니다. 'Connect'를 눌러주세요.")
        
    session = requests.Session()
    session.headers.update({'X-MBX-APIKEY': _active_key})
    
    params_copy = params.copy()
    params_copy['timestamp'] = int(time.time() * 1000)
    
    query_string = urlencode(params_copy)
    signature = hmac.new(
        _active_secret.encode('utf-8'), 
        query_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()
    
    params_copy['signature'] = signature
    
    url = _get_url(endpoint_path)
    
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
                return e.response.json() # {"code": -1111, "msg": "..."}
            except json.JSONDecodeError:
                print(f"API 요청 오류 (JSON 디코딩 불가): {e.response.text}")
                return {"code": e.response.status_code, "msg": e.response.text}
        
        print(f"API 요청 오류 ({url}): {e}")
        return None 

# --- 공개 함수 ---

def get_listen_key():
    """웹소켓 연결을 위한 Listen Key를 발급받습니다."""
    print("Listen Key 발급 시도...")
    data = _send_signed_request('POST', '/fapi/v1/listenKey') 
    if data and data.get('listenKey'):
        return data.get('listenKey')
    else:
        print(f"Listen Key 발급 실패: {data}")
        return None

# ▼▼▼ [신규 함수 추가] ▼▼▼
def get_initial_balance():
    """현재 계정 잔액 정보를 가져옵니다."""
    print("초기 잔액 정보 로드 중...") # ◀◀◀ 이 로그가 보여야 합니다.
    # fapi v2 balance 엔드포인트 사용, dapi는 _get_url에서 v1으로 자동 변환됨
    data = _send_signed_request('GET', '/fapi/v2/balance') 
    if data and isinstance(data, list): 
        return data
    elif data and data.get('code'):
         print(f"잔액 정보 로드 실패 (API): {data.get('msg')}")
    return []
# ▲▲▲ [신규 함수 추가] ▲▲▲

def get_initial_positions():
    """현재 모든 포지션 정보를 가져옵니다."""
    print("초기 포지션 정보 로드 중...")
    data = _send_signed_request('GET', '/fapi/v2/positionRisk') 
    if data and isinstance(data, list): 
        positions = [p for p in data if float(p.get('positionAmt', 0)) != 0]
        return positions
    return []

def get_initial_open_orders():
    """현재 모든 미체결 주문을 가져옵니다."""
    print("초기 미체결 주문 로드 중...")
    data = _send_signed_request('GET', '/fapi/v1/openOrders')
    if data and isinstance(data, list): 
        return data
    return []

def place_market_order(symbol, side, quantity, reduce_only=False, position_side="BOTH"):
    """시장가 주문을 전송합니다. (헷지 모드 호환)"""
    print(f"시장가 주문 요청: {side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")
    
    params = {
        'symbol': symbol,
        'side': side,
        'type': 'MARKET',
        'quantity': quantity,
        'positionSide': position_side 
    }
        
    data = _send_signed_request('POST', '/fapi/v1/order', params)
    return data

def cancel_order(symbol, order_id):
    """특정 주문을 취소합니다."""
    print(f"주문 취소 요청: {symbol} (OrderID: {order_id})")
    
    params = {
        'symbol': symbol,
        'orderId': order_id,
    }
    
    data = _send_signed_request('DELETE', '/fapi/v1/order', params)
    return data

def get_ohlcv_data(symbol, interval='1h', limit=500):
    """
    (공개 API) 특정 심볼의 OHLCV (Klines) 데이터를 가져옵니다.
    pyqtgraph 차트를 그리는 데 사용됩니다.
    """
    global _active_market
    
    # 1. 활성 마켓에 따라 기본 URL 결정
    if _active_market == "dapi":
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
        print(f"OHLCV 데이터 요청 오류 ({url}): {e}")
        if e.response is not None:
            print(f"오류 응답: {e.response.json()}")
        return None