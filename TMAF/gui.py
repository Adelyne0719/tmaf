import sys
import os
import re
import json
import logging
import time
import tempfile
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QPlainTextEdit, QTabWidget, QFormLayout, QLineEdit, QComboBox, 
    QSpinBox, QDoubleSpinBox, QGridLayout, QGroupBox, QHBoxLayout
)
from PyQt5.QtCore import QTimer, QUrl, QProcess, QProcessEnvironment, Qt
from PyQt5.QtWebSockets import QWebSocket
from binance.client import Client
import config  # 기존 consts 대신 config 사용
from binance_user_data_stream import BinanceUserDataStream
import configparser

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("실시간 트레이딩 모니터링 및 설정")
        self.resize(900, 1000)

        self.setStyleSheet("""
            QWidget {
                background-color: #2e2e2e;
                color: #ffffff;
                font-size: 16px;
            }
            QLabel, QPushButton {
                padding: 5px;
            }
            QPlainTextEdit, QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background: #2e2e2e;
            }
            QTabBar::tab {
                background: #2e2e2e;
                border: 1px solid #555555;
                padding: 8px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
            }
            QTabBar::tab:hover {
                background: #3e3e3e;
            }
        """)

        # 탭 위젯 생성
        self.tabs = QTabWidget()
        self.trading_tab = QWidget()
        # self.settings_tab = QWidget() #셋팅탭 삭제해둠
        self.tabs.addTab(self.trading_tab, "Trading")
        # self.tabs.addTab(self.settings_tab, "Settings") #셋팅탭 삭제해둠

        # ----- Trading 탭 구성 -----
        self.positionLabel = QLabel("없음")
        self.entryPriceLabel = QLabel("-")
        self.qtyLabel = QLabel("-")
        self.stageLabel = QLabel("-")
        self.unrealizedProfitLabel = QLabel("-")
        self.nextPriceLabel = QLabel("-")
        self.priceLabel = QLabel("-")
        self.ma5Label = QLabel("-")
        self.ma10Label = QLabel("-")
        self.ma15Label = QLabel("-")
        self.vol3Label = QLabel("-")
        self.prevVolLabel = QLabel("-")
        self.balanceLabel = QLabel("-")
        self.profitLabel = QLabel("-")
        self.uidLabel = QLabel("-")
        self.startStopButton = QPushButton("Start")
        self.startStopButton.clicked.connect(self.toggle_trading)
        self.clearPositionButton = QPushButton("Clear Position")
        self.clearPositionButton.setStyleSheet("background-color: red; color: white;")
        self.clearPositionButton.clicked.connect(self.clear_position)
        self.logViewer = QPlainTextEdit()
        self.logViewer.setReadOnly(True)

        self.accountGroup = QGroupBox("계좌 정보")
        accountLayout = QGridLayout()
        accountLayout.addWidget(QLabel("UID:"), 0, 0)
        accountLayout.addWidget(self.uidLabel, 0, 1)
        accountLayout.addWidget(QLabel("잔고:"), 1, 0)
        accountLayout.addWidget(self.balanceLabel, 1, 1)
        accountLayout.addWidget(QLabel("수익률:"), 2, 0)
        accountLayout.addWidget(self.profitLabel, 2, 1)
        self.accountGroup.setLayout(accountLayout)

        self.positionGroup = QGroupBox("포지션 정보")
        posLayout = QGridLayout()
        posLayout.addWidget(QLabel("포지션:"), 0, 0)
        posLayout.addWidget(self.positionLabel, 0, 1)
        posLayout.addWidget(QLabel("진입가:"), 1, 0)
        posLayout.addWidget(self.entryPriceLabel, 1, 1)
        posLayout.addWidget(QLabel("수량:"), 2, 0)
        posLayout.addWidget(self.qtyLabel, 2, 1)
        posLayout.addWidget(QLabel("미실현수익:"), 3, 0)
        posLayout.addWidget(self.unrealizedProfitLabel, 3, 1)
        posLayout.addWidget(QLabel("단계:"), 4, 0)
        posLayout.addWidget(self.stageLabel, 4, 1)
        posLayout.addWidget(QLabel("다음가격:"), 5, 0)
        posLayout.addWidget(self.nextPriceLabel, 5, 1)
        self.positionGroup.setLayout(posLayout)

        self.priceGroup = QGroupBox("가격 및 지표")
        priceLayout = QGridLayout()
        priceLayout.addWidget(QLabel("실시간 가격:"), 0, 0)
        priceLayout.addWidget(self.priceLabel, 0, 1)
        priceLayout.addWidget(QLabel("ema5:"), 1, 0)
        priceLayout.addWidget(self.ma5Label, 1, 1)
        priceLayout.addWidget(QLabel("ema10:"), 2, 0)
        priceLayout.addWidget(self.ma10Label, 2, 1)
        priceLayout.addWidget(QLabel("ema15:"), 3, 0)
        priceLayout.addWidget(self.ma15Label, 3, 1)
        priceLayout.addWidget(QLabel("2x Min Vol (48):"), 4, 0)
        priceLayout.addWidget(self.vol3Label, 4, 1)
        priceLayout.addWidget(QLabel("Prev Candle Vol:"), 5, 0)
        priceLayout.addWidget(self.prevVolLabel, 5, 1)
        self.priceGroup.setLayout(priceLayout)

        tradingMainLayout = QVBoxLayout()
        tradingMainLayout.addWidget(self.accountGroup)
        middleLayout = QHBoxLayout()
        middleLayout.addWidget(self.positionGroup)
        middleLayout.addWidget(self.priceGroup)
        tradingMainLayout.addLayout(middleLayout)
        btnLayout = QHBoxLayout()
        btnLayout.addStretch(1)
        btnLayout.addWidget(self.startStopButton)
        btnLayout.addWidget(self.clearPositionButton)
        btnLayout.addStretch(1)
        tradingMainLayout.addLayout(btnLayout)
        tradingMainLayout.addWidget(self.logViewer)
        self.trading_tab.setLayout(tradingMainLayout)

        # ----- Settings 탭 구성 -----
        # self.constsForm = QFormLayout()
        # self.apiKeyEdit = QLineEdit(config.API_KEY)
        # self.apiSecretEdit = QLineEdit(config.API_SECRET)
        # self.symbolEdit = QLineEdit(config.SYMBOL)
        # self.constsForm.addRow("API_KEY:", self.apiKeyEdit)
        # self.constsForm.addRow("API_SECRET:", self.apiSecretEdit)
        # self.symbolCombo = QComboBox()
        # self.symbolCombo.addItems(["BTCUSDT", "ETHUSDT", "XRPUSDT"])
        # index = self.symbolCombo.findText(config.SYMBOL)
        # if index != -1:
        #     self.symbolCombo.setCurrentIndex(index)
        # self.constsForm.addRow("SYMBOL:", self.symbolCombo)
        # self.intervalCombo = QComboBox()
        # intervals = ["1m", "5m", "15m", "30m", "1h", "4h", "1d"]
        # self.intervalCombo.addItems(intervals)
        # index = intervals.index(config.INTERVAL) if config.INTERVAL in intervals else 0
        # self.intervalCombo.setCurrentIndex(index)
        # self.constsForm.addRow("INTERVAL:", self.intervalCombo)
        # self.volMultiplierSpin = QSpinBox()
        # self.volMultiplierSpin.setMinimum(1)
        # self.volMultiplierSpin.setMaximum(5)
        # self.volMultiplierSpin.setValue(config.VOL_MULTIPLIER)
        # self.constsForm.addRow("VOL_MULTIPLIER:", self.volMultiplierSpin)
        # self.ema5Spin = QSpinBox()
        # self.ema5Spin.setMinimum(5)
        # self.ema5Spin.setMaximum(5)
        # self.ema5Spin.setValue(config.EMA_PERIODS.get("ema5", 5))
        # self.ema10Spin = QSpinBox()
        # self.ema10Spin.setMinimum(10)
        # self.ema10Spin.setMaximum(10)
        # self.ema10Spin.setValue(config.EMA_PERIODS.get("ema10", 10))
        # self.ema15Spin = QSpinBox()
        # self.ema15Spin.setMinimum(15)
        # self.ema15Spin.setMaximum(15)
        # self.ema15Spin.setValue(config.EMA_PERIODS.get("ema15", 15))
        # self.constsForm.addRow("ema5:", self.ema5Spin)
        # self.constsForm.addRow("ema10:", self.ema10Spin)
        # self.constsForm.addRow("ema15:", self.ema15Spin)
        # self.scalingFactorSpin = QDoubleSpinBox()
        # self.scalingFactorSpin.setDecimals(3)
        # self.scalingFactorSpin.setSingleStep(0.001)
        # self.scalingFactorSpin.setValue(config.SCALING_FACTOR)
        # self.constsForm.addRow("SCALING_FACTOR:", self.scalingFactorSpin)
        # self.maxEntriesSpin = QSpinBox()
        # self.maxEntriesSpin.setMinimum(1)
        # self.maxEntriesSpin.setMaximum(20)
        # self.maxEntriesSpin.setValue(config.MAX_ENTRIES)
        # self.constsForm.addRow("MAX_ENTRIES:", self.maxEntriesSpin)
        # self.exitFactorSpin = QDoubleSpinBox()
        # self.exitFactorSpin.setDecimals(2)
        # self.exitFactorSpin.setSingleStep(0.01)
        # self.exitFactorSpin.setValue(config.EXIT_FACTOR)
        # self.constsForm.addRow("EXIT_FACTOR:", self.exitFactorSpin)
        # self.leverageSpin = QSpinBox()
        # self.leverageSpin.setMinimum(1)
        # self.leverageSpin.setMaximum(50)
        # self.leverageSpin.setValue(config.LEVERAGE)
        # self.constsForm.addRow("LEVERAGE:", self.leverageSpin)
        # self.saveSettingsButton = QPushButton("Save Settings")
        # self.saveSettingsButton.clicked.connect(self.save_consts)
        # settingsLayout = QVBoxLayout()
        # settingsLayout.addLayout(self.constsForm)
        # settingsLayout.addWidget(self.saveSettingsButton)
        # self.settings_tab.setLayout(settingsLayout) #셋팅탭 삭제해둠

        self.setCentralWidget(self.tabs)

        self.client = Client(config.API_KEY, config.API_SECRET)
        self.initial_balance = self.get_futures_balance() or 0

        self.ws = None
        self.ws_kline = None
        self.balance_timer = None
        self.process = None
        self.running = False
        self.candles = []
        self.setup_logging()

        self.userDataStream = BinanceUserDataStream(config.API_KEY)
        self.userDataStream.on_account_update = self.update_position_from_ws
        
        self.unrealizedProfitTimer = QTimer(self)
        self.unrealizedProfitTimer.timeout.connect(self.update_unrealized_profit)
        self.unrealizedProfitTimer.start(5000)
        
        self.logFilePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trading_strategy.log")
        if os.path.exists(self.logFilePath):
            self.lastLogSize = os.path.getsize(self.logFilePath)
        else:
            self.lastLogSize = 0
        self.logFileTimer = QTimer(self)
        self.logFileTimer.timeout.connect(self.read_log_file)
        self.logFileTimer.start(500)  # 0.5초마다 체크

    def setup_logging(self):
        class NotiFilter(logging.Filter):
            def filter(self, record):
                return record.levelno == 25
        class QTextEditLogger(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget
            def emit(self, record):
                msg = self.format(record).rstrip()
                self.widget.appendPlainText(msg)
        self.log_handler = QTextEditLogger(self.logViewer)
        self.log_handler.addFilter(NotiFilter())
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        self.log_handler.setFormatter(formatter)
        logging.getLogger().addHandler(self.log_handler)

    def update_position_from_ws(self, pos_data):
            logging.info("WebSocket에서 포지션 업데이트: %s", pos_data)
            self.positionLabel.setText(pos_data.get("position", ""))
            self.entryPriceLabel.setText(pos_data.get("entry", ""))
            self.qtyLabel.setText(pos_data.get("quantity", ""))
            self.unrealizedProfitLabel.setText(pos_data.get("unrealized_profit", ""))
            self.stageLabel.setText(pos_data.get("stage", ""))
            
            # 포지션이 없음으로 변경된 경우 nextPriceLabel도 초기화
            if pos_data.get("position", "") == "없음":
                self.nextPriceLabel.setText("-")

    def clear_position(self):
        try:
            positions = self.client.futures_position_information()
            target = None
            for pos in positions:
                if pos.get('symbol') == config.SYMBOL and float(pos.get('positionAmt', 0)) != 0:
                    target = pos
                    break
            if target is None:
                self.logViewer.appendPlainText("정리할 포지션이 없습니다.")
                return
            amt = float(target.get('positionAmt', 0))
            if amt > 0:
                side = "SELL"
                quantity = amt
            else:
                side = "BUY"
                quantity = abs(amt)
            order = self.client.futures_create_order(
                symbol=config.SYMBOL,
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=True
            )
            self.logViewer.appendPlainText(f"Clear Position 주문 실행: {side} {quantity}")
            
            # 청산 주문 후 GUI 정보 초기화
            # 이 부분도 추가했습니다
            self.reset_position_info()
        except Exception as e:
            self.logViewer.appendPlainText(f"Clear Position 주문 오류: {e}")

    def reset_position_info(self):
        self.positionLabel.setText("없음")
        self.entryPriceLabel.setText("-")
        self.qtyLabel.setText("-")
        self.unrealizedProfitLabel.setText("-")
        self.stageLabel.setText("-")
        self.nextPriceLabel.setText("-")

    def toggle_trading(self):
        if not self.running:
            self.start_trading()
            self.startStopButton.setText("Stop")
            self.running = True
        else:
            self.stop_trading()
            self.startStopButton.setText("Start")
            self.running = False

    def load_initial_candles(self):
        try:
            klines = self.client.futures_klines(symbol=config.SYMBOL, interval=config.INTERVAL, limit=100)
            self.candles = []
            for k in klines:
                candle = {
                    "timestamp": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5])
                }
                self.candles.append(candle)
            self.update_indicators()
            logging.info("Initial candles loaded successfully.")
        except Exception as e:
            logging.error("Initial candle load error: %s", e)

    def start_trading(self):
        self.initial_balance = self.get_futures_balance() or 0
        self.uid = self.get_account_uid()
        self.uidLabel.setText(str(self.uid))
        self.logViewer.appendPlainText("Trading bot 시작 중...")

        # QWebSocket 생성 및 에러 시그널 연결 (PyQt5 최신 방식 지원)
        self.ws = QWebSocket()
        if hasattr(self.ws, "errorOccurred"):
            self.ws.errorOccurred.connect(self.on_error)
        else:
            self.ws.error.connect(self.on_error)
        self.ws.textMessageReceived.connect(self.on_message)
        self.ws.connected.connect(self.on_connected)
        stream_symbol = config.SYMBOL.lower()
        ws_url = f"wss://fstream.binance.com/ws/{stream_symbol}@ticker"
        logging.info("웹소켓 연결: %s", ws_url)
        self.ws.open(QUrl(ws_url))

        self.ws_kline = QWebSocket()
        if hasattr(self.ws_kline, "errorOccurred"):
            self.ws_kline.errorOccurred.connect(self.on_error)
        else:
            self.ws_kline.error.connect(self.on_error)
        self.ws_kline.textMessageReceived.connect(self.on_kline_message)
        kline_url = f"wss://fstream.binance.com/ws/{stream_symbol}@kline_{config.INTERVAL}"
        logging.info("Kline 웹소켓 연결: %s", kline_url)
        self.ws_kline.open(QUrl(kline_url))

        self.load_initial_candles()

        self.balance_timer = QTimer(self)
        self.balance_timer.timeout.connect(self.update_balance_profit)
        self.balance_timer.start(5000)

        self.process = QProcess(self)
        current_dir = os.path.abspath(os.path.dirname(__file__))
        self.process.setWorkingDirectory(current_dir)
        
        if getattr(sys, 'frozen', False):
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)

        # 부모 프로세스의 환경 변수를 복사하고 STRATEGY_MODE를 "live"로 설정
        env = QProcessEnvironment.systemEnvironment()
        env.insert("STRATEGY_MODE", "live")
        self.process.setProcessEnvironment(env)

        if getattr(sys, "frozen", False):
            # 패키징된 경우: 현재 실행 파일 자체를 호출하고, "--strategy" 인자를 추가합니다.
            executable = sys.executable
            args = ["--strategy"]
        else:
            # 개발 환경: main.py를 직접 호출
            executable = sys.executable
            main_py_path = os.path.join(current_dir, "main.py")
            args = [main_py_path, "--strategy"]

        # Windows에서 콘솔창이 뜨지 않도록 python.exe 대신 pythonw.exe 사용 (필요 시)
        if os.name == 'nt' and executable.lower().endswith("python.exe"):
            executable = executable.replace("python.exe", "pythonw.exe")

        
        self.process.start(executable, args)
        self.userDataStream.start()

    def read_log_file(self):
        # 로그 파일이 존재하지 않으면 종료
        if not os.path.exists(self.logFilePath):
            return
        try:
            current_size = os.path.getsize(self.logFilePath)
            # 파일 크기가 self.lastLogSize보다 작으면(새 실행에 의해 파일이 재작성된 경우) 오프셋을 0으로 재설정
            if current_size < self.lastLogSize:
                self.lastLogSize = 0
            with open(self.logFilePath, "r", encoding="utf8") as f:
                f.seek(self.lastLogSize)
                new_data = f.read()
                self.lastLogSize = f.tell()
                if new_data:
                    # 데이터를 줄 단위로 분리
                    lines = new_data.splitlines()
                    for line in lines:
                        # 로그 뷰어에 각 줄을 추가
                        self.logViewer.appendPlainText(line)
                        # 각 줄에 대해 단계와 다음가격 정보를 업데이트
                        self.update_stage_and_next_price_from_log(line)
                        self.update_position_basic_info_from_log(line)
        except Exception as e:
            logging.error("로그 파일 읽기 오류: %s", e)


    def stop_trading(self):
        self.logViewer.appendPlainText("Trading bot 중지 중...")
        if self.process is not None:
            self.process.kill()
            self.process = None
        if self.ws is not None:
            self.ws.close()
            self.ws = None
        if self.ws_kline is not None:
            self.ws_kline.close()
            self.ws_kline = None
        if self.balance_timer is not None:
            self.balance_timer.stop()
            self.balance_timer = None
        if self.userDataStream and self.userDataStream.ws:
            self.userDataStream.ws.close()
        self.reset_labels()
        self.logViewer.appendPlainText("Trading bot 중지 완료.")

    def reset_labels(self):
        self.positionLabel.setText("없음")
        self.entryPriceLabel.setText("-")
        self.qtyLabel.setText("-")
        self.unrealizedProfitLabel.setText("-")
        self.stageLabel.setText("-")
        self.priceLabel.setText("-")
        self.ma5Label.setText("-")
        self.ma10Label.setText("-")
        self.ma15Label.setText("-")
        self.vol3Label.setText("-")
        self.prevVolLabel.setText("-")
        self.balanceLabel.setText("-")
        self.profitLabel.setText("-")
        self.nextPriceLabel.setText("-")
    
    def stop_trading(self):
        self.logViewer.appendPlainText("Trading bot 중지 중...")
        if self.process is not None:
            self.process.kill()
            self.process = None
        if self.ws is not None:
            self.ws.close()
            self.ws = None
        if self.ws_kline is not None:
            self.ws_kline.close()
            self.ws_kline = None
        if self.balance_timer is not None:
            self.balance_timer.stop()
            self.balance_timer = None
        # BinanceUserDataStream의 웹소켓도 종료합니다.
        if self.userDataStream and self.userDataStream.ws:
            self.userDataStream.ws.close()
        self.reset_labels()
        self.logViewer.appendPlainText("Trading bot 중지 완료.")

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        text = bytes(data).decode("utf8", errors="replace")
        text = text.strip()
        self.logViewer.appendPlainText(text)
        self.update_position_basic_info_from_log(text)
        self.update_stage_and_next_price_from_log(text)

    def handle_stderr(self):
        if self.process is None:
            return
        data = self.process.readAllStandardError()
        text = bytes(data).decode("utf8")
        text = text.strip()
        if "STOP_TRADING_TRIGGER" in text:
            self.logViewer.appendPlainText("최소거래금액이 부족합니다. LEVERAGE를 증가시키거나 MAX_ENTRIES를 줄이세요. 거래를 중단합니다.")
            self.toggle_trading()
            return
        self.logViewer.appendPlainText(text)
        self.update_position_basic_info_from_log(text)
        self.update_stage_and_next_price_from_log(text)

    def on_connected(self):
        logging.info("웹소켓에 연결되었습니다.")

    def on_error(self, error):
        logging.error("웹소켓 에러: %s", error)

    def on_message(self, message):
        try:
            data = json.loads(message)
            price = float(data.get("c", 0))
            self.priceLabel.setText(f"{price:.4f}")
            if self.process is not None and self.process.state() == QProcess.Running:
                self.process.write(f"{price}\n".encode("utf-8"))
        except Exception as e:
            logging.error("메시지 파싱 에러: %s", e)

    def on_kline_message(self, message):
        try:
            data = json.loads(message)
            if data.get("e") == "kline":
                kline = data.get("k", {})
                is_closed = kline.get("x", False)
                if is_closed:
                    candle = {
                        "timestamp": kline.get("t"),
                        "open": float(kline.get("o")),
                        "high": float(kline.get("h")),
                        "low": float(kline.get("l")),
                        "close": float(kline.get("c")),
                        "volume": float(kline.get("v"))
                    }
                    self.candles.append(candle)
                    if len(self.candles) > 100:
                        self.candles.pop(0)
            self.update_indicators()
        except Exception as e:
            logging.error("Kline 메시지 처리 에러: %s", e)

    def update_indicators(self):
        closed = self.candles
        if len(closed) >= 5:
            ema5 = sum(c["close"] for c in closed[-5:]) / 5
            self.ma5Label.setText(f"{ema5:.4f}")
        else:
            self.ma5Label.setText("-")
        if len(closed) >= 10:
            ema10 = sum(c["close"] for c in closed[-10:]) / 10
            self.ma10Label.setText(f"{ema10:.4f}")
        else:
            self.ma10Label.setText("-")
        if len(closed) >= 15:
            ema15 = sum(c["close"] for c in closed[-15:]) / 15
            self.ma15Label.setText(f"{ema15:.4f}")
        else:
            self.ma15Label.setText("-")
        if len(closed) >= 48:
            min_vol = min(c["volume"] for c in closed[-48:])
            self.vol3Label.setText(f"{min_vol * 3:.2f}")
        else:
            self.vol3Label.setText("-")
        if len(closed) >= 1:
            prev_vol = closed[-1]["volume"]
            self.prevVolLabel.setText(f"{prev_vol:.2f}")
        else:
            self.prevVolLabel.setText("-")

    def update_position_basic_info_from_log(self, text):
        pos_update = re.search(
            r".*POSITION_UPDATE:(롱|숏|없음),\s*(-?(?:[\d\.]+)|-),\s*(-?(?:[\d\.]+)|-),\s*(-?(?:[\d\.]+)|-)",
            text
        )
        if pos_update:
            position_type = pos_update.group(1)
            entry_price = pos_update.group(2)
            quantity = pos_update.group(3)
            unrealized_profit = pos_update.group(4)
            self.positionLabel.setText(position_type)
            self.entryPriceLabel.setText(entry_price)
            self.qtyLabel.setText(quantity)
            self.unrealizedProfitLabel.setText(unrealized_profit)

    def update_stage_and_next_price_from_log(self, text):
        entry_update = re.search(
            r".*?롱 포지션 진입 완료(?: \(실시간\))?\s*-\s*단계\s*:\s*(\d+),\s*진입가\s*:\s*([\d\.]+),\s*다음 추가 진입가\s*:\s*([\d\.]+)",
            text
        )
        if entry_update:
            self.stageLabel.setText(entry_update.group(1))
            self.nextPriceLabel.setText(entry_update.group(3))
            return
        entry_update = re.search(
            r".*?숏 포지션 진입 완료(?: \(실시간\))?\s*-\s*단계\s*:\s*(\d+),\s*진입가\s*:\s*([\d\.]+),\s*다음 추가 진입가\s*:\s*([\d\.]+)",
            text
        )
        if entry_update:
            self.stageLabel.setText(entry_update.group(1))
            self.nextPriceLabel.setText(entry_update.group(3))
            return
        long_add_update = re.search(
            r".*?롱 추가 진입 완료(?: \(실시간\))?\s*-\s*단계\s*:\s*(\d+),\s*진입가\s*:\s*([\d\.]+),\s*다음 추가 진입가\s*:\s*([\d\.]+)",
            text
        )
        if long_add_update:
            self.stageLabel.setText(long_add_update.group(1))
            self.nextPriceLabel.setText(long_add_update.group(3))
            return
        short_add_update = re.search(
            r".*?숏 추가 진입 완료(?: \(실시간\))?\s*-\s*단계\s*:\s*(\d+),\s*진입가\s*:\s*([\d\.]+),\s*다음 추가 진입가\s*:\s*([\d\.]+)",
            text
        )
        if short_add_update:
            self.stageLabel.setText(short_add_update.group(1))
            self.nextPriceLabel.setText(short_add_update.group(3))
            return
        if re.search(r".*?(포지션 청산 완료)", text):
            self.stageLabel.setText("-")
            self.nextPriceLabel.setText("-")

    def get_account_uid(self):
        try:
            logging.info("계정연결")
            account_info = self.client.get_account()
            account_uid = account_info['uid']
            if account_info is not None:
                logging.info("연결된 UID: %s", account_uid)
                return account_uid
            else:
                logging.error("입력된 API KEY의 UID를 찾을 수 없습니다.")
                return None
        except Exception as e:
            logging.error("UID 조회 실패: %s", e)
            return None
                    
    def get_futures_balance(self):
        try:
            balance_data = self.client.futures_account_balance()
            for asset in balance_data:
                if asset['asset'] == 'USDT':
                    balance = float(asset['balance'])
                    logging.info("현재 futures 잔고: %s USDT", balance)
                    return balance
            logging.error("USDT 잔고를 찾을 수 없습니다.")
            return None
        except Exception as e:
            logging.error("잔고 조회 에러: %s", e)
            return None

    def update_balance_profit(self):
        balance = self.get_futures_balance()
        if balance is not None:
            self.balanceLabel.setText(f"{balance:.2f} USDT")
            if self.initial_balance > 0:
                profit_rate = (balance - self.initial_balance) / self.initial_balance * 100
                self.profitLabel.setText(f"{profit_rate:.4f}%")
            else:
                self.profitLabel.setText("수익률: -")
        else:
            self.balanceLabel.setText("잔고: 조회 실패")
            self.profitLabel.setText("수익률: -")
            
    def update_unrealized_profit(self):
        try:
            positions = self.client.futures_position_information()
            for pos in positions:
                if pos.get("symbol") == config.SYMBOL:
                    unrealized_profit = pos.get("unRealizedProfit", "-")
                    try:
                        value = float(unrealized_profit)
                        rounded_value = round(value, 8)  # 소수점 8자리로 반올림
                        self.unrealizedProfitLabel.setText(format(rounded_value, 'g'))
                    except ValueError:
                        self.unrealizedProfitLabel.setText(str(unrealized_profit))
                    break
        except Exception as e:
            logging.error("미실현수익 업데이트 에러: %s", e)

    def save_consts(self):
        debug_messages = []
        
        # config.py에서 추출한 ini 파일 경로 사용
        ini_path = config.ini_file_path
        debug_messages.append(f"DEBUG: ini_path = {ini_path}")
        
        # ini 파일 존재 여부 체크
        if os.path.exists(ini_path):
            debug_messages.append("DEBUG: ini_file exists.")
        else:
            debug_messages.append("DEBUG: ini_file does NOT exist.")
                
        # ini 파일이 위치한 디렉토리와 쓰기 권한 확인
        ini_dir = os.path.dirname(ini_path)
        debug_messages.append(f"DEBUG: ini_dir = {ini_dir}")
        if os.access(ini_dir, os.W_OK):
            debug_messages.append("DEBUG: Directory is writable.")
        else:
            debug_messages.append("DEBUG: Directory is NOT writable.")
        
        # 설정 값을 config_parser에 채움
        config_parser = configparser.ConfigParser()
        config_parser['DEFAULT'] = {
            'API_KEY': self.apiKeyEdit.text(),
            'API_SECRET': self.apiSecretEdit.text(),
            'SYMBOL': self.symbolCombo.currentText(),
            'INTERVAL': self.intervalCombo.currentText(),
            'VOL_MULTIPLIER': str(self.volMultiplierSpin.value()),
            'SCALING_FACTOR': str(self.scalingFactorSpin.value()),
            'MAX_ENTRIES': str(self.maxEntriesSpin.value()),
            'EXIT_FACTOR': str(self.exitFactorSpin.value()),
            'LEVERAGE': str(self.leverageSpin.value())
        }
        config_parser['EMA_PERIODS'] = {
            'ema5': str(self.ema5Spin.value()),
            'ema10': str(self.ema10Spin.value()),
            'ema15': str(self.ema15Spin.value())
        }
        try:
            with open(ini_path, "w", encoding="utf8") as configfile:
                config_parser.write(configfile)
            logging.log(25, "Settings saved successfully.")
            debug_messages.append("DEBUG: Settings saved successfully.")
        except Exception as e:
            logging.log(25, f"Error saving settings: {e}")
            debug_messages.append(f"DEBUG: Error saving settings: {e}")
        
        # debug 메시지를 NOTI 레벨로 출력
        for msg in debug_messages:
            logging.log(25, msg)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
