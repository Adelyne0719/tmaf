# -*- coding: utf-8 -*-

import os
import time
import hmac
import hashlib
import requests
import json
from urllib.parse import urlencode

# --- API 키 설정 ---
# 환경 변수를 사용하거나 아래에 직접 키를 입력하세요.

api_key = "9Ni9kOuXna5x5t1dBWjLQkhbLebWr7iX8JreznhbTjX4izBYRUwHNS5s2Zafl8rL"
api_secret = "DipJWGoTpa4jqNEbZKbZLOuEG1B1Vtra2gxLyFBlPstSNbXyccplf860y66YczzF" #형꺼

# api_key = "uyAUXTyZ4RW9hOAkzbLJeCn7qlXnEOfjC8Pfw2673sJ4WlfYt2IoV8On12H27xb6"
# api_secret = "uHh2OQ00kuvy1uqVo2wNeTaxS5iae4VtIIyE82QqeFjZU1yM4yYZoBzFLzGxKe1C" #조형준대표님꺼

if not api_key or "YOUR_API_KEY_HERE" in api_key or not api_secret or "YOUR_SECRET_KEY_HERE" in api_secret:
    print("오류: 바이낸스 API 키와 시크릿 키를 설정해주세요.")
    exit()

def send_signed_request(base_url, http_method, api_path, payload={}):
    """바이낸스 API에 서명된 요청을 보내는 범용 함수"""
    timestamp = int(time.time() * 1000)
    params = payload.copy()
    params['timestamp'] = timestamp
    
    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()
    query_string += f'&signature={signature}'
    
    url = f"{base_url}{api_path}?{query_string}"
    headers = {'X-MBX-APIKEY': api_key}
    
    try:
        response = requests.request(http_method, url, headers=headers)
        response.raise_for_status() # 오류 발생 시 예외 처리
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 요청 중 오류가 발생했습니다: {e}")
        if e.response:
            try:
                print(f"오류 상세 정보: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"오류 응답 (JSON 아님): {e.response.text}")
        return None

def clear_market_activity(market_type):
    """지정된 선물 시장(USDT-M 또는 COIN-M)의 모든 활동을 정리합니다."""
    
    # --- 시장 타입에 따른 설정 ---
    if market_type == 'usdt':
        BASE_URL = "https://fapi.binance.com"
        market_name = "USDT-M"
        # <<< 🟢 핵심 수정: 잘못된 주소를 올바른 계정 정보 주소로 변경 🟢 >>>
        position_endpoint = '/fapi/v2/account' 
        order_endpoint = '/fapi/v1/order'
        open_orders_endpoint = '/fapi/v1/openOrders'
        cancel_all_endpoint = '/fapi/v1/allOpenOrders'
    elif market_type == 'coin':
        BASE_URL = "https://dapi.binance.com"
        market_name = "COIN-M"
        position_endpoint = '/dapi/v1/account' 
        order_endpoint = '/dapi/v1/order'
        open_orders_endpoint = '/dapi/v1/openOrders'
        cancel_all_endpoint = '/dapi/v1/allOpenOrders'
    else:
        print(f"알 수 없는 시장 타입입니다: {market_type}")
        return

    print("="*50)
    print(f"{market_name} 선물 시장의 모든 포지션과 주문 정리를 시작합니다.")

    # --- 1. 모든 포지션 종료 ---
    print(f"\n[1단계] 모든 {market_name} 포지션 종료를 시작합니다...")
    
    account_info = send_signed_request(BASE_URL, 'GET', position_endpoint)
    
    if not account_info:
        print(f" ! 계정/포지션 정보 조회에 실패하여 포지션 종료를 진행할 수 없습니다.")
        return

    # <<< 🟢 핵심 수정: USDT-M과 COIN-M 모두 동일한 구조의 응답을 처리하도록 통일 🟢 >>>
    positions_list = account_info.get('positions', [])
    
    open_positions = [p for p in positions_list if float(p.get('positionAmt', '0')) != 0]
    
    if not open_positions:
        print(f" ✔️ 현재 보유 중인 {market_name} 포지션이 없습니다.")
    else:
        print(f" - {len(open_positions)}개의 포지션을 발견했습니다. 시장가로 종료합니다...")
        for pos in open_positions:
            symbol = pos['symbol']
            quantity = abs(float(pos['positionAmt'])) 
            side = 'SELL' if float(pos['positionAmt']) > 0 else 'BUY'
            position_side = pos.get('positionSide', 'BOTH')
            
            if position_side == 'BOTH':
                params = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'MARKET',
                    'quantity': quantity,
                    'reduceOnly': 'true'
                }
                print(f"  - [{symbol}] 단방향 포지션 종료 시도 (수량: {quantity}, 방향: {side})...")
            else:
                params = {
                    'symbol': symbol,
                    'side': side,
                    'type': 'MARKET',
                    'positionSide': position_side,
                    'quantity': quantity
                }
                print(f"  - [{symbol}] {position_side} 포지션 종료 시도 (수량: {quantity}, 방향: {side})...")
            
            order_result = send_signed_request(BASE_URL, 'POST', order_endpoint, params)
            if order_result and 'orderId' in order_result:
                print(f"    - [{symbol}] 포지션 종료 주문 성공.")
            else:
                print(f"    - [{symbol}] 포지션 종료 주문 실패.")

    # --- 2. 모든 미체결 주문 취소 ---
    print(f"\n[2단계] 모든 {market_name} 미체결 주문 취소를 시작합니다...")
    open_orders = send_signed_request(BASE_URL, 'GET', open_orders_endpoint)

    if not open_orders:
        print(f" ✔️ 취소할 {market_name} 미체결 주문이 없습니다.")
    else:
        symbols_with_orders = {order['symbol'] for order in open_orders}
        print(f" - {len(symbols_with_orders)}개 심볼에서 미체결 주문을 발견했습니다. 취소를 진행합니다...")
        for symbol in symbols_with_orders:
            cancel_result = send_signed_request(BASE_URL, 'DELETE', cancel_all_endpoint, {'symbol': symbol})
            # USDT-M은 성공 시 리스트, COIN-M은 성공 객체를 반환하므로 더 유연하게 확인
            if isinstance(cancel_result, (list, dict)):
                 print(f"  - [{symbol}]의 모든 미체결 주문을 취소했습니다.")
            else:
                 print(f"  - [{symbol}] 주문 취소 중 오류가 발생했습니다.")
                 
    print("-" * 20 + " 완료 " + "-" * 22)


# --- 스크립트 실행 부분 ---
if __name__ == '__main__':
    while True:
        choice = input(
            "\n어떤 시장의 모든 활동을 정리하시겠습니까?\n"
            "1: USDT-M 선물\n"
            "2: COIN-M 선물\n"
            "3: 둘 다 (USDT-M -> COIN-M 순서)\n"
            "q: 종료\n"
            "선택: "
        ).strip()

        if choice in ['1', '2', '3']:
            confirmation = input(f"🚨 경고: 선택하신 시장의 모든 포지션과 주문을 정말로 취소하시겠습니까? (yes/no): ")
            if confirmation.lower() == 'yes':
                print("\n사용자 확인 완료. 작업을 시작합니다...")
                if choice == '1':
                    clear_market_activity('usdt')
                elif choice == '2':
                    clear_market_activity('coin')
                elif choice == '3':
                    clear_market_activity('usdt')
                    time.sleep(1) # API 호출 간 짧은 지연
                    clear_market_activity('coin')
                print("\n모든 작업이 완료되었습니다.")
                break
            else:
                print("작업이 취소되었습니다.")
        elif choice.lower() == 'q':
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 입력입니다. 1, 2, 3 또는 q 중에서 선택해주세요.")

