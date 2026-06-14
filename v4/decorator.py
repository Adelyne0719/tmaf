import time
import requests
import json
import platform
import logging
import subprocess


def call_binance_api(original_func):
    def wrapper(*args, **kwargs):
        url = "https://fapi.binance.com/fapi/v1/time"
        t = time.time() * 1000
        try:
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            result = response.json()
            if "serverTime" not in result:
                raise KeyError("serverTime 키가 응답에 없습니다.")
            server_time = int(result["serverTime"])
            time_diff = abs(int(t) - server_time)
            if time_diff > 1000:
                logging.info(f"서버시간과 로컬 시간 차이: {time_diff} 밀리초")
                logging.info("Windows 시간 동기화 시작")
                if platform.system() == "Windows":
                    commands = [
                        'chcp 65001',
                        'net stop w32time',
                        'w32tm /unregister',
                        'w32tm /register',
                        'net start w32time',
                        'w32tm /resync'
                    ]
                    for cmd in commands:
                        try:
                            result_cmd = subprocess.run(
                                cmd,
                                shell=True,
                                capture_output=True,
                                text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            if result_cmd.returncode != 0:
                                logging.warning(
                                    f"명령어 '{cmd}' 실행 실패, exit code: {result_cmd.returncode}, stderr: {result_cmd.stderr.strip()}"
                                )
                        except Exception as e:
                            logging.error(f"명령어 '{cmd}' 실행 중 예외 발생: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Binance API 연결 에러: {e}")
        except (KeyError, json.JSONDecodeError) as e:
            logging.error(f"API 응답 처리 에러: {e}")
        return original_func(*args, **kwargs)
    return wrapper
