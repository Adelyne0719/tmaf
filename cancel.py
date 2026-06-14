from binance.client import Client
from binance.exceptions import BinanceAPIException

# 1. 본인의 API 키와 시크릿 키를 입력하세요
API_KEY = "9Ni9kOuXna5x5t1dBWjLQkhbLebWr7iX8JreznhbTjX4izBYRUwHNS5s2Zafl8rL"
API_SECRET = "DipJWGoTpa4jqNEbZKbZLOuEG1B1Vtra2gxLyFBlPstSNbXyccplf860y66YczzF"

# 2. 바이낸스 클라이언트 생성
# 실제 매매용 (메인넷)
client = Client(API_KEY, API_SECRET)

# 테스트넷을 사용 중이라면 아래 주석을 해제하세요
# client = Client(API_KEY, API_SECRET, testnet=True)

# 3. 취소할 주문 정보
# 이전 대화에서 확인된 중복 주문 ID 중 하나를 예시로 사용합니다.
target_symbol = "BTCUSDT"
target_order_id = 798657399245  # 여기에 취소할 실제 주문 ID를 입력하세요

# 4. 주문 취소 시도
try:
    print(f"심볼: {target_symbol}")
    print(f"주문 ID: {target_order_id}의 취소를 시도합니다...")
    
    # 선물(Futures) 주문 취소 API 호출
    cancel_response = client.futures_cancel_order(
        symbol=target_symbol,
        orderId=target_order_id
    )
    
    print("\n--- 주문 취소 성공 ---")
    print(f"상태: {cancel_response.get('status')}")
    print(f"주문 ID: {cancel_response.get('orderId')}")
    print(f"심볼: {cancel_response.get('symbol')}")
    print(f"클라이언트 ID: {cancel_response.get('clientOrderId')}")

except BinanceAPIException as e:
    # API 오류 처리
    print(f"\n--- 주문 취소 실패 (API 오류) ---")
    print(f"오류 코드: {e.code}")
    print(f"오류 메시지: {e.message}")
    
    if e.code == -2011:
        print("-> (참고) 'Unknown order sent.' 오류는 주문이 이미 체결되었거나,\n   존재하지 않거나, 이전에 이미 취소된 경우 발생할 수 있습니다.")

except Exception as e:
    # 기타 오류 처리
    print(f"\n--- 알 수 없는 오류 발생 ---")
    print(e)