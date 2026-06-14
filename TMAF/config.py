import configparser
import os
import sys
import shutil

import shutil  # 반드시 추가

def extract_resources():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS          # 패키징된 파일들이 위치한 기본 경로
        exe_dir = os.path.dirname(sys.executable)  # exe 파일이 있는 폴더
    else:
        base_path = os.path.dirname(__file__)
        exe_dir = base_path

    # consts.ini 파일 복사
    ini_src = os.path.join(base_path, "consts.ini")
    if not os.path.exists(ini_src):
        ini_src = os.path.join(base_path, "_internal", "consts.ini")
    ini_dest = os.path.join(exe_dir, "consts.ini")
    if not os.path.exists(ini_dest):
        try:
            shutil.copy(ini_src, ini_dest)
            print(f"consts.ini 파일을 {ini_dest} 로 복사했습니다.")
        except Exception as e:
            print(f"consts.ini 파일 복사 실패: {e}")

    # trading_strategy.log 파일 복사 (이 부분은 필요 시 구현)
    # ...

    return {"ini": ini_dest}

# INI 파일 추출 및 경로 확인
resources = extract_resources()
ini_file_path = resources["ini"]

# INI 파일 내용 출력
if os.path.exists(ini_file_path):
    with open(ini_file_path, "r", encoding="utf8") as f:
        ini_contents = f.read()
else:
    print("INI file does not exist at", ini_file_path)

# configparser를 통해 ini 파일을 읽고, 섹션과 옵션 출력
config = configparser.ConfigParser()
config.optionxform = str  # 대소문자 그대로 유지
config.read(ini_file_path)

# consts.ini 파일을 exe 디렉토리로 추출하고 그 경로를 가져옵니다.
ini_file_path = extract_resources()

API_KEY = config.get("DEFAULT", "API_KEY")
API_SECRET = config.get("DEFAULT", "API_SECRET")
SYMBOL = config.get("DEFAULT", "SYMBOL")
INTERVAL = config.get("DEFAULT", "INTERVAL")
VOL_MULTIPLIER = config.getint("DEFAULT", "VOL_MULTIPLIER")
SCALING_FACTOR = config.getfloat("DEFAULT", "SCALING_FACTOR")
TRAILING_START = config.getint("DEFAULT", "TRAILING_START")
TRAILING_SAFE = config.getint("DEFAULT", "TRAILING_SAFE")
MAX_ENTRIES = config.getint("DEFAULT", "MAX_ENTRIES")
EXIT_FACTOR = config.getfloat("DEFAULT", "EXIT_FACTOR")
SAFE_FACTOR = config.getfloat("DEFAULT", "SAFE_FACTOR")
LEVERAGE = config.getint("DEFAULT", "LEVERAGE")

EMA_PERIODS = {
    'ema5': config.getint("EMA_PERIODS", "ema5"),
    'ema10': config.getint("EMA_PERIODS", "ema10"),
    'ema15': config.getint("EMA_PERIODS", "ema15")
}
