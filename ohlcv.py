import pandas as pd
from binance.client import Client
from datetime import datetime

# --- 설정 ---
# API 키는 공개 데이터 조회 시 필수는 아니지만, 요청 제한을 늘리려면 입력하는 것이 좋습니다.
api_key = "qlTZPJYCc6ADJF9AeWD78Gs0XKpXMb9zOBF2lYkL5D78nKu35oGHCcDlQ2VwRByn"
api_secret = "AlXog0s8gKE88LtlFtr54pscTF0tRNILYE9TwjU9gFQuJ2UdgK7GP3aPpB1KzrxI"

# 조회할 Ticker 및 기간 설정
symbol = "XRPUSDT"
interval = Client.KLINE_INTERVAL_5MINUTE
start_date = "2025-09-01 00:00:00"

# --- 데이터 요청 및 처리 ---
try:
    # 바이낸스 클라이언트 생성
    client = Client(api_key, api_secret)

    # get_historical_klines_generator를 사용하면 1000개 제한 없이 모든 데이터를 편리하게 가져올 수 있습니다.
    klines_generator = client.futures_historical_klines_generator(
        symbol=symbol,
        interval=interval,
        start_str=start_date
    )

    # 제너레이터에서 모든 데이터를 리스트로 변환
    klines = list(klines_generator)

    # 데이터가 없는 경우 처리
    if not klines:
        print(f"{start_date}부터 현재까지 {symbol}의 {interval} 데이터가 없습니다.")
    else:
        # DataFrame으로 변환
        df = pd.DataFrame(klines, columns=[
            'Open Time', 'Open', 'High', 'Low', 'Close', 'Volume', 
            'Close Time', 'Quote Asset Volume', 'Number of Trades', 
            'Taker Buy Base Asset Volume', 'Taker Buy Quote Asset Volume', 'Ignore'
        ])

        # 필요한 컬럼만 선택
        df = df[['Open Time', 'Open', 'High', 'Low', 'Close', 'Volume']]

        # 데이터 타입 변환 (숫자형으로)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # 시간 컬럼을 한국 시간(KST)으로 변환
        # 바이낸스 타임스탬프는 밀리초(ms) 단위이므로 unit='ms'를 사용합니다.
        df['Open Time'] = pd.to_datetime(df['Open Time'], unit='ms') + pd.Timedelta(hours=9)
        df.rename(columns={'Open Time': 'Open Time (KST)'}, inplace=True)

        # 'Open Time (KST)'를 인덱스로 설정
        df.set_index('Open Time (KST)', inplace=True)

        # 결과 출력
        print(f"--- {symbol} | {interval} | {start_date} ~ 현재 ---")
        print("최신 데이터 5개:")
        print(df.tail(5))
        
        print("\n과거 데이터 5개:")
        print(df.head(5))

        # (선택) CSV 파일로 저장
        file_name = f"{symbol}_{interval}_data.csv"
        df.to_csv(file_name)
        print(f"\n데이터를 '{file_name}' 파일로 저장했습니다.")

except Exception as e:
    print(f"오류가 발생했습니다: {e}")