# 설정 파일 로드
import os
import configparser

# 현재 스크립트가 위치한 디렉토리를 기준으로 config.ini 경로 지정
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, 'config.ini')
config = configparser.ConfigParser()
files_read = config.read(config_path)
if not files_read:
    raise FileNotFoundError(f"Config file not found at {config_path}")

# BINANCE 설정
API_KEY    = config.get('BINANCE', 'api_key')
API_SECRET = config.get('BINANCE', 'api_secret')
SYMBOL     = config.get('BINANCE', 'symbol')
INTERVAL   = config.get('BINANCE', 'interval')

# TRADING 설정
LEVERAGE = config.getint('TRADING', 'leverage')
NO_SIGNAL_ZONE = config.getfloat('TRADING', 'no_signal_zone')

# ENTRY 비율표 설정
ENTRY_START    = config.getfloat('ENTRY', 'start')
ENTRY_END      = config.getfloat('ENTRY', 'end')
ENTRY_STEPS    = config.getint('ENTRY', 'steps')
ENTRY_EXPONENT = config.getfloat('ENTRY', 'exponent')
ENTRY_MAGINOT  = config.getfloat('ENTRY', 'maginot')

# EXIT 비율표 설정
EXIT_FIRST     = config.getfloat('EXIT', 'first')
EXIT_LAST      = config.getfloat('EXIT', 'last')
EXIT_STEPS     = config.getint('EXIT', 'steps')
EXIT_EXPONENT  = config.getfloat('EXIT', 'exponent')
EXIT_MAGINOT   = config.getfloat('EXIT', 'boom')