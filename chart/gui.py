import sys
import requests
import pandas as pd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QTableWidget, QHeaderView, QLabel, 
                             QApplication, QTabWidget, QLineEdit, QFormLayout,
                             QTableWidgetItem, QScrollArea, QGroupBox, QMessageBox,
                             QComboBox, QSplitter, QButtonGroup, QStackedWidget)
from PyQt5.QtCore import pyqtSlot, QUrl, Qt, pyqtSignal, QTimer, QThread
from PyQt5.QtGui import QPalette, QColor, QBrush, QPen

import pyqtgraph as pg
from pyqtgraph import PlotDataItem, GraphicsObject

import binance_api 
from ws_manager import WebSocketThread
from ticker_ws import TickerSocketThread

class ConnectAPIThread(QThread):
    """오래 걸리는 API 연결 작업을 백그라운드에서 처리합니다."""
    connection_finished = pyqtSignal(dict)

    def __init__(self, accounts, account_name, market_type, current_interval, old_ws_thread, old_ticker_thread, parent=None):
        super().__init__(parent)
        self.accounts = accounts
        self.account_name = account_name
        self.market_type = market_type
        self.current_interval = current_interval 
        self.old_ws_thread = old_ws_thread       
        self.old_ticker_thread = old_ticker_thread 
        self.running = True

    def run(self):
        """스레드가 실행할 메인 로직 (모든 블로킹 작업)"""
        result = {'success': False, 'error': None, 'data': {}}
        try:
            # 1. 이전 스레드 종료
            if self.old_ws_thread and self.old_ws_thread.isRunning():
                print("Worker: 이전 User Data 스레드 종료 대기 중...")
                self.old_ws_thread.stop()
                self.old_ws_thread.wait()
                print("Worker: 이전 User Data 스레드 종료 완료.")
            
            if self.old_ticker_thread and self.old_ticker_thread.isRunning():
                print("Worker: 이전 Ticker 스레드 종료 대기 중...")
                self.old_ticker_thread.stop()
                self.old_ticker_thread.wait()
                print("Worker: 이전 Ticker 스레드 종료 완료.")

            # 2. API 키 설정
            account_info = self.accounts.get(self.account_name)
            if not account_info:
                raise Exception(f"'{self.account_name}' 계정 정보를 찾을 수 없습니다.")
            
            binance_api.set_active_market(self.market_type)
            binance_api.set_active_api_keys(account_info['api_key'], account_info['api_secret'])
            
            if not self.running: return

            # 3. Listen Key 받기 (네트워크 I/O)
            listen_key = binance_api.get_listen_key()
            if not listen_key:
                raise Exception("Failed to get Listen Key. Check API keys.")
            
            if not self.running: return

            # 4. ▼▼▼ [수정] 초기 잔액 로드 (네트워크 I/O) ▼▼▼
            balance_info = binance_api.get_initial_balance()
            
            if not self.running: return
            
            # 5. 초기 포지션 로드 (네트워크 I/O)
            positions = binance_api.get_initial_positions()
            
            if not self.running: return

            # 6. 초기 주문 로드 (네트워크 I/O)
            orders = binance_api.get_initial_open_orders()
            
            # 7. 심볼 결정
            api_symbol_to_use = "BTCUSDT" 
            if positions:
                api_symbol = positions[0]['symbol']
                api_symbol_to_use = api_symbol
            else:
                if self.market_type == 'dapi':
                    api_symbol_to_use = "BTCUSD_PERP"
                else:
                    api_symbol_to_use = "BTCUSDT"

            if not self.running: return

            # 8. OHLCV 데이터 로드 (네트워크 I/O)
            print(f"Worker: {api_symbol_to_use} ({self.current_interval}) 캔들 데이터 로드 중...")
            klines = binance_api.get_ohlcv_data(api_symbol_to_use, self.current_interval, 1000)
            
            # 9. 새 웹소켓 객체 생성
            new_ws_thread = WebSocketThread(listen_key, self.market_type)
            new_ticker_thread = TickerSocketThread(self.market_type)
            
            # 10. 성공 데이터 준비
            result['success'] = True
            result['data'] = {
                'listen_key': listen_key,
                'balance_info': balance_info, # [추가]
                'positions': positions,
                'orders': orders,
                'current_symbol': api_symbol_to_use,
                'klines': klines,
                'new_ws_thread': new_ws_thread,
                'new_ticker_thread': new_ticker_thread
            }
            
        except Exception as e:
            print(f"ConnectAPIThread 오류: {e}")
            result['error'] = str(e)
            binance_api.set_active_api_keys(None, None) # 실패 시 키 비활성화
        
        # 11. 메인 스레드로 결과 전송
        self.connection_finished.emit(result)

    def stop(self):
        self.running = False


# ... (CustomAxisItem, CustomViewBox, CandlestickItem 클래스는 변경 없음) ...
class CustomAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.precision = 2 # 기본 소수점 2자리 (FAPI)

    def setPrecision(self, precision):
        self.precision = precision
        self.picture = None 
        self.update()

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            strings.append(f"{v:.{self.precision}f}")
        return strings

class CustomViewBox(pg.ViewBox):
    def __init__(self, *args, **kargs):
        super().__init__(*args, **kargs)
        self.setMouseMode(self.PanMode) 

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == pg.QtCore.Qt.ControlModifier:
            self.setMouseEnabled(x=False, y=True)
        else:
            self.setMouseEnabled(x=True, y=False)
        super().wheelEvent(event)
        self.setMouseEnabled(x=True, y=True)
            
    def mouseDoubleClickEvent(self, ev, axis=None):
        if ev.button() == pg.QtCore.Qt.LeftButton:
            print("Auto-ranging chart...")
            self.autoRange()
            ev.accept()
        else:
            super().mouseDoubleClickEvent(ev, axis=axis)
            
    def mouseDragEvent(self, ev, axis=None):
        if ev.isStart():
            if ev.button() == pg.QtCore.Qt.RightButton:
                self.setMouseMode(self.RectMode)
                self.setMouseEnabled(x=False, y=True)
            elif ev.button() == pg.QtCore.Qt.LeftButton:
                self.setMouseMode(self.PanMode)
                self.setMouseEnabled(x=True, y=True)
        super().mouseDragEvent(ev, axis=None)
        if ev.isFinish():
            self.setMouseMode(self.PanMode)
            self.setMouseEnabled(x=True, y=True)        
            
class CandlestickItem(GraphicsObject):
    def __init__(self, data):
        GraphicsObject.__init__(self)
        self.data = data
        self.picture = pg.QtGui.QPicture()
        self.generatePicture(data)
    def setData(self, data):
        self.data = data
        self.generatePicture(data)
        self.update()
    def generatePicture(self, data):
        self.picture = pg.QtGui.QPicture()
        p = pg.QtGui.QPainter(self.picture)
        if data.shape[0] > 1:
            w = (data['time'].iloc[1] - data['time'].iloc[0]) * 0.4
        else:
            w = 0.4
        color_red = '#c00000'
        color_green = '#00b050'
        for (i, row) in data.iterrows():
            time, open, high, low, close = row['time'], row['open'], row['high'], row['low'], row['close']
            p.setPen(pg.mkPen(color_red if open > close else color_green))
            p.drawLine(pg.QtCore.QPointF(time, low), pg.QtCore.QPointF(time, high))
            if open > close:
                p.setPen(pg.mkPen(color_red))
                p.setBrush(pg.mkBrush(color_red))
            else:
                p.setPen(pg.mkPen(color_green))
                p.setBrush(pg.mkBrush(color_green))
            p.drawRect(pg.QtCore.QRectF(time - w, open, w * 2, close - open))
        p.end()
    def paint(self, p, *args):
        p.drawPicture(0, 0, self.picture)
    def boundingRect(self):
        if self.data.empty:
            return pg.QtCore.QRectF()
        t_min = self.data['time'].min()
        t_max = self.data['time'].max()
        p_min = self.data['low'].min()
        p_max = self.data['high'].max()
        return pg.QtCore.QRectF(t_min, p_min, t_max - t_min, p_max - p_min)

class BinanceTrader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.current_symbol = "BTCUSDT"
        self.current_interval = "5m" 
        
        self.ws_thread = None 
        self.ticker_thread = None 
        self.listen_key = None 
        self.config_data = {}
        self.accounts = {}
        self.current_market_type = "fapi"
        
        self.live_position_data = {} 
        self.live_balances = {} # [신규] 잔액 정보 저장
        
        self.is_dark_mode = True 
        self.original_palette = QApplication.instance().palette() 
        self.is_reduce_only = False
        
        self.trade_price_label = None
        self.balance_label = None # [신규] 잔액 표시 라벨
        self.last_price_for_color = 0.0
        
        self.chart_widget = None
        self.candlestick_item = None
        self.price_line_item = None
        self.position_lines = {}
        self.time_axis = None
        self.chart_refresh_timer = None
        
        self.detected_precision = None
        
        self.pending_market_orders = set()
        
        self.loading_overlay = None
        self.loading_animation_timer = None
        self.loading_animation_state = 0
        self.base_loading_text = ""
        
        self.connect_thread = None 
        
        self.initUI()
        self.apply_theme() 
        self.load_config_data() 
        
    def initUI(self):
        self.setWindowTitle("Binance Trader (Multi-Account & Market)")
        self.setGeometry(100, 100, 1400, 900) 
        pg.setConfigOptions(antialias=True)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.chart_tab = QWidget()
        self.tabs.addTab(self.chart_tab, "📊 Chart")
        self.settings_tab = QWidget()
        self.tabs.addTab(self.settings_tab, "⚙️ Settings")
        tab_main_layout = QHBoxLayout(self.chart_tab)
        self.h_splitter = QSplitter(Qt.Horizontal)
        tab_main_layout.addWidget(self.h_splitter)
        left_widget = QWidget()
        chart_layout = QVBoxLayout(left_widget)
        top_toolbar_layout = QHBoxLayout()
        self.buttons = {}
        api_intervals = ["1m", "5m", "30m", "1h", "4h", "1d", "1w"]
        for tf in api_intervals:
            btn = QPushButton(tf)
            btn.clicked.connect(lambda _, t=tf: self.change_timeframe(t))
            self.buttons[tf] = btn
            top_toolbar_layout.addWidget(btn)
        self.update_timeframe_buttons(self.current_interval, None)
        top_toolbar_layout.addStretch(1) 
        self.connection_status_label = QLabel("Not Connected")
        self.connection_status_label.setStyleSheet("color: gray; font-weight: bold;")
        top_toolbar_layout.addWidget(self.connection_status_label)
        top_toolbar_layout.addStretch(1)
        self.dark_mode_button = QPushButton("🌙 Dark Mode")
        self.dark_mode_button.setCheckable(True) 
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.dark_mode_button.setChecked(self.is_dark_mode) 
        top_toolbar_layout.addWidget(self.dark_mode_button)
        chart_layout.addLayout(top_toolbar_layout)
        self.time_axis = pg.DateAxisItem(orientation='bottom')
        self.y_axis = CustomAxisItem(orientation='left')
        self.chart_viewbox = CustomViewBox()
        self.chart_widget = pg.PlotWidget(viewBox=self.chart_viewbox, axisItems={'bottom': self.time_axis, 'left': self.y_axis})
        self.chart_viewbox.setMouseEnabled(x=True, y=True)
        self.candlestick_item = CandlestickItem(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
        self.chart_widget.addItem(self.candlestick_item)
        self.price_line_item = pg.InfiniteLine(
            angle=0, movable=False, pen=pg.mkPen('cyan', style=Qt.DashLine, width=1), label='0.00',
            labelOpts={'position': 0.05, 'color': 'cyan', 'movable': True, 'fill': (0, 0, 0, 150), 'anchor': (0, 0.5)}
        )
        self.price_line_item.hide()
        self.chart_widget.addItem(self.price_line_item)
        self.chart_widget.setLabel('left', 'Price')
        self.chart_widget.setLabel('bottom', 'Time')
        self.chart_widget.showGrid(x=True, y=True, alpha=0.3)
        chart_layout.addWidget(self.chart_widget, stretch=5)
        chart_layout.addWidget(QLabel("포지션 (Positions)"))
        self.position_table = QTableWidget()
        self.position_table.setColumnCount(5)
        self.position_table.setHorizontalHeaderLabels(["Symbol", "Amount", "Entry Price", "PNL", "ROI %"])
        self.position_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        chart_layout.addWidget(self.position_table, stretch=2)
        chart_layout.addWidget(QLabel("미체결 주문 (Open Orders)"))
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels(["Symbol", "Type", "Side", "Price", "Amount", "Filled", "OrderId"])
        self.order_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.order_table.setColumnHidden(6, True)
        chart_layout.addWidget(self.order_table, stretch=2)
        
        right_panel_container = QWidget()
        right_panel_layout = QVBoxLayout(right_panel_container)
        self.create_order_panel(right_panel_layout)
        self.h_splitter.addWidget(left_widget)
        self.h_splitter.addWidget(right_panel_container)
        
        self.loading_overlay = QLabel(self.tabs)
        self.loading_overlay.setText("API에 연결 중입니다...")
        self.loading_overlay.setAlignment(Qt.AlignCenter)
        self.loading_overlay.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 0.75); 
                color: white; 
                font-size: 24px; 
                font-weight: bold;
                border-radius: 10px;
            }
        """)
        self.loading_overlay.hide()
        self.loading_animation_timer = QTimer(self)
        self.loading_animation_timer.timeout.connect(self.animate_loading_text)
        self.h_splitter.setSizes([1000, 400])

        settings_main_layout = QVBoxLayout(self.settings_tab)
        add_account_group = QGroupBox("Add / Update Account")
        form_layout = QFormLayout()
        self.new_account_name_input = QLineEdit()
        self.new_api_key_input = QLineEdit()
        self.new_api_secret_input = QLineEdit()
        self.new_api_secret_input.setEchoMode(QLineEdit.Password)
        self.add_account_button = QPushButton("Save Account")
        form_layout.addRow(QLabel("Account Name:"), self.new_account_name_input)
        form_layout.addRow(QLabel("API Key:"), self.new_api_key_input)
        form_layout.addRow(QLabel("API Secret:"), self.new_api_secret_input)
        form_layout.addRow(self.add_account_button)
        add_account_group.setLayout(form_layout)
        settings_main_layout.addWidget(add_account_group)
        account_list_group = QGroupBox("Saved Accounts")
        account_list_main_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.account_list_layout = QVBoxLayout(self.scroll_widget) 
        self.scroll_area.setWidget(self.scroll_widget)
        account_list_main_layout.addWidget(self.scroll_area)
        account_list_group.setLayout(account_list_main_layout)
        settings_main_layout.addWidget(account_list_group)
        self.add_account_button.clicked.connect(self.add_new_account)

    def create_order_panel(self, parent_layout):
        price_box = QGroupBox("Price")
        price_layout = QVBoxLayout(price_box)
        self.trade_price_label = QLabel("0.00")
        self.default_price_label_style = "font-size: 24pt; font-weight: bold; padding: 10px 0;"
        self.trade_price_label.setStyleSheet(self.default_price_label_style)
        self.trade_price_label.setAlignment(Qt.AlignCenter)
        price_layout.addWidget(self.trade_price_label)
        
        trade_box = QGroupBox("Trade")
        trade_layout = QVBoxLayout(trade_box)
        
        toggle_layout = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.close_button = QPushButton("Close")
        self.order_mode_group = QButtonGroup()
        self.open_button.setCheckable(True); self.close_button.setCheckable(True)
        self.order_mode_group.addButton(self.open_button); self.order_mode_group.addButton(self.close_button)
        self.open_button.setChecked(True)
        toggle_layout.addWidget(self.open_button); toggle_layout.addWidget(self.close_button)
        trade_layout.addLayout(toggle_layout)
        self.open_button.clicked.connect(self.update_order_panel_mode); self.close_button.clicked.connect(self.update_order_panel_mode)
        
        market_label = QLabel("Market Order"); market_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        trade_layout.addWidget(market_label)
        
        order_form_layout = QFormLayout()
        self.order_symbol_input = QLineEdit(self.current_symbol)
        order_form_layout.addRow(QLabel("Symbol:"), self.order_symbol_input)
        self.order_quantity_input = QLineEdit()
        self.order_quantity_input.setPlaceholderText("Size (e.g., 100 for COIN-M Cont, 0.1 for USD-M BTC)")
        order_form_layout.addRow(QLabel("Quantity:"), self.order_quantity_input)
        trade_layout.addLayout(order_form_layout)
        
        button_layout = QHBoxLayout()
        self.long_button = QPushButton("Open Long"); self.short_button = QPushButton("Open Short")
        self.long_button.setStyleSheet("background-color: #00b050; color: white; padding: 10px; font-weight: bold;")
        self.short_button.setStyleSheet("background-color: #c00000; color: white; padding: 10px; font-weight: bold;")
        button_layout.addWidget(self.long_button); button_layout.addWidget(self.short_button)
        trade_layout.addLayout(button_layout)
        
        # ▼▼▼ [레이아웃 수정] ▼▼▼
        # 'Clear All' 버튼 레이아웃
        clear_layout = QHBoxLayout()
        self.clear_all_button = QPushButton("🚨 Clear All (All Symbols)")
        self.update_clear_button_style()
        clear_layout.addWidget(self.clear_all_button)
        trade_layout.addLayout(clear_layout) # 1. Clear All 버튼 먼저 추가
        
        # 'Wallet Balance' 박스
        balance_box = QGroupBox("Wallet Balance")
        balance_layout = QVBoxLayout(balance_box)
        balance_layout.setContentsMargins(5, 5, 5, 5) 
        
        self.balance_label = QLabel("N/A")
        self.balance_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.balance_label.setAlignment(Qt.AlignCenter)
        
        balance_layout.addWidget(self.balance_label)
        trade_layout.addWidget(balance_box) # 2. 그 *아래에* 잔액 박스 추가
        # ▲▲▲ [레이아웃 수정] ▲▲▲
        
        trade_layout.addStretch(1) # 3. 마지막에 Stretch 추가
        
        parent_layout.addWidget(price_box); parent_layout.addWidget(trade_box)
        parent_layout.addStretch(1)
        
        self.long_button.clicked.connect(lambda: self.on_place_order_clicked("BUY"))
        self.short_button.clicked.connect(lambda: self.on_place_order_clicked("SELL"))
        self.clear_all_button.clicked.connect(self.on_clear_all_clicked)
        self.update_order_panel_mode() 

    def update_clear_button_style(self):
        if not hasattr(self, 'clear_all_button'): return
        if self.is_dark_mode: style = "background-color: #8B0000; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        else: style = "background-color: #FF4500; color: white; padding: 10px; font-weight: bold; border-radius: 4px;"
        self.clear_all_button.setStyleSheet(style)
    
    def update_order_panel_mode(self):
        base_style = "padding: 8px; font-weight: bold; border-radius: 4px;"
        if self.is_dark_mode: checked_style = "background-color: #555; color: white;"; unchecked_style = "background-color: #333; color: #888;"
        else: checked_style = "background-color: #BBB; color: black;"; unchecked_style = "background-color: #DDD; color: #777;"
        if self.open_button.isChecked():
            self.is_reduce_only = False
            self.open_button.setStyleSheet(base_style + checked_style); self.close_button.setStyleSheet(base_style + unchecked_style)
            self.long_button.setText("Open Long"); self.short_button.setText("Open Short")
        else:
            self.is_reduce_only = True
            self.open_button.setStyleSheet(base_style + unchecked_style); self.close_button.setStyleSheet(base_style + checked_style)
            self.long_button.setText("Close Short"); self.short_button.setText("Close Long")

    def on_place_order_clicked(self, side):
        symbol = self.order_symbol_input.text().upper().strip()
        quantity = self.order_quantity_input.text().strip()
        if not symbol or not quantity: QMessageBox.warning(self, "Order Error", "Symbol and Quantity are required."); return
        if not binance_api.is_api_key_active(): QMessageBox.warning(self, "Order Error", "API is not connected. Please connect in Settings tab."); return
        reduce_only = self.is_reduce_only
        if side == "BUY": position_side = "LONG" if not reduce_only else "SHORT"
        else: position_side = "SHORT" if not reduce_only else "LONG"
        action_text = "Close" if reduce_only else "Open"; side_text = "Short" if position_side == "SHORT" else "Long"
        reply = QMessageBox.question(self, "Confirm Order", f"Place Market {action_text} {side_text} order?\n\nSymbol: {symbol}\nQuantity: {quantity}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        try:
            print(f"Placing order: {side} {quantity} {symbol} (reduceOnly={reduce_only}, positionSide={position_side})")
            result = binance_api.place_market_order(symbol, side, quantity, reduce_only, position_side)
            if result and result.get('orderId'):
                order_id = str(result.get('orderId'))
                print(f"주문 ID {order_id}가 접수되었습니다. WebSocket (FILLED) 응답 대기 중...")
                self.pending_market_orders.add(order_id)
                self.order_quantity_input.clear()
            elif result and result.get('code'):
                QMessageBox.warning(self, "Order Rejected", f"Order REJECTED by Binance (API).\n\nCode: {result.get('code')}\nMsg: {result.get('msg', 'Unknown error')}")
            else:
                QMessageBox.warning(self, "Order Failed", f"API request failed. Check console log for details.\nResult: {result}")
        except Exception as e:
            QMessageBox.critical(self, "Python Error", f"Failed to place order: {e}")

    def on_clear_all_clicked(self):
        if not binance_api.is_api_key_active(): QMessageBox.warning(self, "Error", "API is not connected."); return
        reply = QMessageBox.warning(self, "DANGER: Confirm Action", "This will attempt to:\n1. Cancel ALL open orders (all symbols)\n2. Close ALL open positions (all symbols)\n\nThis action is IRREVERSIBLE. Are you sure?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No: return
        print("--- [Clear All] Starting ---")
        cancel_results = []; close_results = []; open_orders = []
        try:
            open_orders = binance_api.get_initial_open_orders()
            if not open_orders: print("[Clear All] No open orders found to cancel.")
            else:
                for order in open_orders:
                    try: result = binance_api.cancel_order(str(order['symbol']), str(order['orderId'])); cancel_results.append(result)
                    except Exception as e: cancel_results.append({"status": "PYTHON_ERROR", "msg": str(e)})
        except Exception as e: print(f"[Clear All] Failed to fetch open orders: {e}")
        positions_to_close = list(self.live_position_data.values())
        if not positions_to_close: print("[Clear All] No open positions found to close.")
        else:
            for pos_data in positions_to_close:
                try:
                    side = "SELL" if pos_data['amount'] > 0 else "BUY" 
                    result = binance_api.place_market_order(pos_data['symbol'], side, str(abs(pos_data['amount'])), reduce_only=True, position_side=pos_data['positionSide'])
                    close_results.append(result)
                except Exception as e: close_results.append({"status": "PYTHON_ERROR", "msg": str(e)})
        print("--- [Clear All] Finished ---")
        success_orders = sum(1 for r in cancel_results if r and (r.get('status') == 'CANCELED' or r.get('code') == -2011))
        success_positions = sum(1 for r in close_results if r and r.get('status') == 'FILLED')
        QMessageBox.information(self, "Clear All Report", f"Orders Canceled: {success_orders} / {len(open_orders)}\nPositions Closed: {success_positions} / {len(positions_to_close)}")

    def load_config_data(self):
        self.config_data = binance_api.load_config_data()
        self.accounts = self.config_data.get("accounts", {})
        app_settings = self.config_data.get("app_settings", {})
        old_tf = self.current_interval
        self.current_interval = app_settings.get("last_timeframe", self.current_interval)
        print(f"{len(self.accounts)}개의 계정을 로드했습니다."); print(f"저장된 타임프레임 로드: {self.current_interval}")
        self.rebuild_account_list_ui()
        self.update_timeframe_buttons(self.current_interval, old_tf)

    def rebuild_account_list_ui(self):
        while self.account_list_layout.count():
            child = self.account_list_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        for account_name, account_data in self.accounts.items():
            account_widget = QWidget(); row_layout = QHBoxLayout(account_widget)
            label = QLabel(account_name); label.setMinimumWidth(150)
            market_combo = QComboBox(); market_combo.addItems(["USDⓈ-M (fapi)", "COIN-M (dapi)"])
            saved_market = account_data.get('market', 'fapi')
            market_combo.setCurrentIndex(1 if saved_market == 'dapi' else 0)
            market_combo.currentIndexChanged.connect(lambda index, name=account_name: self.on_market_changed(name, index))
            connect_btn = QPushButton("🔌 Connect")
            connect_btn.clicked.connect(lambda _, name=account_name, combo=market_combo: self.connect_to_api(name, "dapi" if combo.currentIndex() == 1 else "fapi"))
            edit_btn = QPushButton("✏️ Edit"); edit_btn.clicked.connect(lambda _, name=account_name: self.on_edit_account_clicked(name))
            delete_btn = QPushButton("❌ Delete"); delete_btn.clicked.connect(lambda _, name=account_name: self.delete_account(name))
            row_layout.addWidget(label); row_layout.addStretch(1); row_layout.addWidget(market_combo) 
            row_layout.addWidget(edit_btn); row_layout.addWidget(connect_btn); row_layout.addWidget(delete_btn)
            self.account_list_layout.addWidget(account_widget)
        self.account_list_layout.addStretch(1)

    def on_edit_account_clicked(self, account_name):
        if account_name in self.accounts:
            account_data = self.accounts[account_name]
            self.new_account_name_input.setText(account_name); self.new_api_key_input.setText(account_data.get('api_key', ''))
            self.new_api_secret_input.setText(account_data.get('api_secret', ''))
            
    def on_market_changed(self, account_name, index):
        market_type = "dapi" if index == 1 else "fapi"
        if account_name in self.accounts:
            self.accounts[account_name]['market'] = market_type
            binance_api.save_config_data(self.config_data)

    def add_new_account(self):
        name = self.new_account_name_input.text().strip(); key = self.new_api_key_input.text().strip(); secret = self.new_api_secret_input.text().strip()
        if not name or not key or not secret: QMessageBox.warning(self, "Input Error", "Account Name, API Key, and Secret are all required."); return
        existing_market = self.accounts.get(name, {}).get('market', 'fapi')
        self.accounts[name] = {"api_key": key, "api_secret": secret, "market": existing_market}
        binance_api.save_config_data(self.config_data); self.rebuild_account_list_ui() 
        self.new_account_name_input.clear(); self.new_api_key_input.clear(); self.new_api_secret_input.clear()

    def delete_account(self, account_name):
        reply = QMessageBox.question(self, "Delete Account", f"Are you sure you want to delete '{account_name}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            if account_name in self.accounts:
                del self.accounts[account_name]
                binance_api.save_config_data(self.config_data)
                self.rebuild_account_list_ui()


    def connect_to_api(self, account_name, market_type):
        """'Connect' 버튼 클릭 시, 워커 스레드를 시작하고 오버레이를 표시합니다."""
        
        if self.connect_thread and self.connect_thread.isRunning():
            self.connect_thread.stop()
            self.connect_thread.wait()

        try:
            self.base_loading_text = f"Connecting to {account_name} ({market_type})"
            self.loading_animation_state = 0
            
            self.loading_overlay.resize(self.tabs.size())
            self.loading_overlay.raise_()
            self.animate_loading_text()
            self.loading_overlay.show()
            
            self.loading_animation_timer.start(500)
            QApplication.processEvents()
        except Exception as e:
            print(f"오버레이 표시 오류: {e}")
        
        old_ws = self.ws_thread
        old_ticker = self.ticker_thread
        
        self.ws_thread = None
        self.ticker_thread = None
        
        self.remove_all_position_lines_from_chart()
        if self.chart_refresh_timer:
            self.chart_refresh_timer.stop()
            
        binance_api.set_active_api_keys(None, None)
        self.position_table.setRowCount(0) 
        self.order_table.setRowCount(0)
        self.live_position_data.clear() 
        self.live_balances.clear() # [신규] 잔액 데이터 초기화
        
        # [신규] 잔액 라벨 초기화
        if hasattr(self, 'balance_label') and self.balance_label:
            self.balance_label.setText("Loading...") 
            
        self.current_market_type = market_type
        self.detected_precision = None
        self.y_axis.setPrecision(2) 
        
        if self.candlestick_item:
            self.candlestick_item.setData(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
        if self.price_line_item:
            self.price_line_item.hide()
            
        self.connection_status_label.setText(f"Connecting...")
        self.connection_status_label.setStyleSheet("color: blue;")
        self.tabs.setCurrentWidget(self.chart_tab) 
        
        self.connect_thread = ConnectAPIThread(
            accounts=self.accounts,
            account_name=account_name,
            market_type=market_type,
            current_interval=self.current_interval, 
            old_ws_thread=old_ws,                 
            old_ticker_thread=old_ticker            
        )
        self.connect_thread.connection_finished.connect(self.on_connection_finished)
        self.connect_thread.start()

    @pyqtSlot(dict)
    def on_connection_finished(self, result):
        """ConnectAPIThread가 완료되면 호출되어 GUI를 갱신합니다."""
        
        self.loading_animation_timer.stop()
        self.loading_overlay.hide()
        QApplication.processEvents()
        
        try:
            if not result['success']:
                raise Exception(result.get('error', 'Unknown thread error'))

            data = result['data']
            self.listen_key = data['listen_key']
            balance_info = data['balance_info'] # [수정]
            positions = data['positions']
            orders = data['orders']
            self.current_symbol = data['current_symbol']
            klines = data['klines']
            
            self.ws_thread = data['new_ws_thread']
            self.ticker_thread = data['new_ticker_thread']
            
            # ▼▼▼ [수정] 잔액 및 테이블 채우기 ▼▼▼
            self.populate_initial_balance(balance_info) 
            self.populate_initial_positions(positions)
            self.populate_initial_orders(orders)
            
            if self.current_market_type == 'dapi':
                precision = 2 if "USD" in self.current_symbol else 8
            else:
                precision = 2 
            self.y_axis.setPrecision(precision)
            
            self.update_chart(self.current_symbol, self.current_interval, klines_data=klines, is_refresh=False)
            
            self.order_symbol_input.setText(self.current_symbol)

            self.ws_thread.account_update_received.connect(self.handle_account_update)
            self.ws_thread.order_update_received.connect(self.handle_order_update)
            self.ws_thread.start()
            
            self.ticker_thread.ticker_update.connect(self.handle_ticker_update)
            self.ticker_thread.start()
            
            self.chart_refresh_timer = QTimer(self)
            self.chart_refresh_timer.timeout.connect(self.refresh_chart_data)
            self.chart_refresh_timer.start(60000) 
            print("차트 갱신 타이머 (60초) 시작.")
            
            self.connection_status_label.setText(f"✅ Connected to {self.connect_thread.account_name} ({self.current_market_type})")
            
        except Exception as e:
            self.connection_status_label.setText(f"❌ Connection failed: {e}")
            self.connection_status_label.setStyleSheet("color: red;")
            binance_api.set_active_api_keys(None, None)
    
    # ▼▼▼ [신규 함수] ▼▼▼
    def populate_initial_balance(self, balance_info):
        """초기 API 로드 시 잔액 정보를 채웁니다."""
        self.live_balances.clear()
        if not balance_info:
            print(f"({self.current_market_type}) 초기 잔액 정보가 없습니다.")
            return
            
        for b in balance_info:
            asset = b.get('asset')
            balance = b.get('balance') # 초기 로드 시 'balance' 키 사용
            if asset and balance is not None:
                self.live_balances[asset] = balance
                
        print(f"{len(self.live_balances)}개 자산 잔액 로드 완료.")
        self.update_balance_display() # UI 갱신

    # ▼▼▼ [신규 함수] ▼▼▼
    def update_balance_display(self):
        """저장된 self.live_balances를 기반으로 잔액 라벨을 업데이트합니다."""
        if not hasattr(self, 'balance_label') or not self.balance_label:
            return
        
        asset_to_display = None
        balance_str = "0.0"
        
        if self.current_market_type == 'fapi':
            # FAPI (USDⓈ-M)는 USDT를 우선으로 찾음
            if 'USDT' in self.live_balances:
                asset_to_display = 'USDT'
            elif 'BUSD' in self.live_balances: # 차선책
                asset_to_display = 'BUSD'
            
        elif self.current_market_type == 'dapi':
            # DAPI (COIN-M)는 현재 심볼 기반으로 찾음
            # 로그에서 'BTCUSD_PERP' 확인
            if self.current_symbol.endswith("USD_PERP"): # 예: BTCUSD_PERP
                asset_name = self.current_symbol.replace("USD_PERP", "") # BTC
                if asset_name in self.live_balances:
                    asset_to_display = asset_name
            
            # 못찾았으면 BTC를 기본으로 시도
            if not asset_to_display and 'BTC' in self.live_balances:
                asset_to_display = 'BTC'

        # 그래도 못찾았으면 마켓 기본 자산(USDT/BTC)을 다시 시도
        if not asset_to_display:
            if self.current_market_type == 'fapi' and 'USDT' in self.live_balances:
                asset_to_display = 'USDT'
            elif self.current_market_type == 'dapi' and 'BTC' in self.live_balances:
                asset_to_display = 'BTC'
        
        if asset_to_display:
            balance_str = self.live_balances.get(asset_to_display, "0.0")
        else:
            # 표시할 자산이 없음
            self.balance_label.setText("N/A")
            return

        try:
            balance_float = float(balance_str)
            # dapi (BTC, ETH 등)는 8자리, fapi (USDT 등)는 2자리
            precision = 8 if asset_to_display not in ['USDT', 'BUSD'] else 2
            # dapi이고 USDT가 아닌 경우 (BTC, ETH...) 8자리
            if self.current_market_type == 'dapi' and asset_to_display not in ['USDT', 'BUSD']:
                 precision = 8
            else: # fapi (USDT, BUSD)
                 precision = 2
            
            self.balance_label.setText(f"{balance_float:.{precision}f} {asset_to_display}")
        except ValueError:
            self.balance_label.setText(f"{balance_str} {asset_to_display}") # 숫자가 아닐 경우 원본 표시


    def populate_initial_positions(self, positions):
        self.position_table.setRowCount(0); self.live_position_data.clear()
        self.remove_all_position_lines_from_chart()
        if not positions: print(f"({self.current_market_type}) 초기 포지션 정보가 없습니다."); return
        for p in positions:
            row_count = self.position_table.rowCount(); self.position_table.insertRow(row_count)
            symbol = p['symbol']; amount = float(p['positionAmt']); entry_price = float(p['entryPrice'])
            pnl = float(p['unRealizedProfit']); margin = float(p.get('initialMargin', p.get('isolatedWallet', 0)))
            roe = (pnl / margin) * 100 if margin != 0 else 0
            pnl_precision = 8 if self.current_market_type == 'dapi' else 2
            position_side = p.get('positionSide'); 
            if not position_side or position_side == 'BOTH': position_side = 'LONG' if amount > 0 else 'SHORT'
            unique_key = f"{symbol}_{position_side}"
            pnl_item = QTableWidgetItem(f"{pnl:.{pnl_precision}f}"); roe_item = QTableWidgetItem(f"{roe:.2f}%")
            self.position_table.setItem(row_count, 0, QTableWidgetItem(symbol))
            self.position_table.setItem(row_count, 1, QTableWidgetItem(p['positionAmt']))
            self.position_table.setItem(row_count, 2, QTableWidgetItem(p['entryPrice']))
            self.position_table.setItem(row_count, 3, pnl_item); self.position_table.setItem(row_count, 4, roe_item)
            self.live_position_data[unique_key] = {
                'row': row_count, 'symbol': symbol, 'amount': amount, 'entry': entry_price, 'margin': margin,
                'positionSide': position_side, 'pnl_item': pnl_item, 'roe_item': roe_item  
            }
            self.draw_position_line_on_chart(entry_price, position_side)

    def populate_initial_orders(self, orders):
        self.order_table.setRowCount(0)
        if not orders: print(f"({self.current_market_type}) 초기 미체결 주문 정보가 없습니다."); return
        for o in orders:
            row_count = self.order_table.rowCount(); self.order_table.insertRow(row_count)
            self.order_table.setItem(row_count, 0, QTableWidgetItem(o['symbol']))
            self.order_table.setItem(row_count, 1, QTableWidgetItem(o['type']))
            self.order_table.setItem(row_count, 2, QTableWidgetItem(o['side']))
            self.order_table.setItem(row_count, 3, QTableWidgetItem(o['price']))
            self.order_table.setItem(row_count, 4, QTableWidgetItem(o['origQty']))
            self.order_table.setItem(row_count, 5, QTableWidgetItem(o['executedQty']))
            self.order_table.setItem(row_count, 6, QTableWidgetItem(str(o['orderId'])))

    # ▼▼▼ [수정] 잔액 업데이트 로직 추가 ▼▼▼
    @pyqtSlot(dict)
    def handle_account_update(self, data):

        self.remove_all_position_lines_from_chart()
        balance_updated = False # [추가]
        
        try:
            # [신규] 잔액 업데이트 처리 (B 키)
            balances = data.get('a', {}).get('B', [])
            for b in balances:
                asset = b.get('a')
                wallet_balance = b.get('wb') # 웹소켓은 'wb' (Wallet Balance)
                if asset and wallet_balance is not None:
                    # 라이브 데이터 갱신
                    self.live_balances[asset] = wallet_balance
                    balance_updated = True
            
            if balance_updated:
                # 잔액이 변경되었으면 UI 갱신
                self.update_balance_display()

            # [기존] 포지션 업데이트 처리 (P 키)
            positions = data.get('a', {}).get('P', [])
            for p_update in positions:
                symbol = p_update.get('s'); position_side = p_update.get('ps', 'BOTH'); amount = float(p_update.get('pa', 0))
                if position_side == 'BOTH': position_side = 'LONG' if amount > 0 else 'SHORT'
                unique_key = f"{symbol}_{position_side}"
                entry_price = float(p_update.get('ep', 0)); pnl = float(p_update.get('up', 0)); margin = float(p_update.get('im', p_update.get('iw', 0))) 
                pnl_precision = 8 if self.current_market_type == 'dapi' else 2
                found_row = -1
                if unique_key in self.live_position_data: found_row = self.live_position_data[unique_key]['row']
                if amount == 0:
                    if found_row != -1: self.position_table.removeRow(found_row); del self.live_position_data[unique_key]; self.reindex_position_rows() 
                else:
                    roe = (pnl / margin) * 100 if margin != 0 else 0; roe_str = f"{roe:.2f}%"; pnl_str = f"{pnl:.{pnl_precision}f}"
                    if found_row != -1:
                        pos_data = self.live_position_data[unique_key]
                        if found_row < self.position_table.rowCount():
                            pos_data['pnl_item'].setText(pnl_str); pos_data['roe_item'].setText(roe_str)
                            self.position_table.item(found_row, 1).setText(p_update.get('pa')); self.position_table.item(found_row, 2).setText(p_update.get('ep'))
                        pos_data.update({'amount': amount, 'entry': entry_price, 'margin': margin})
                    else:
                        row_count = self.position_table.rowCount(); self.position_table.insertRow(row_count)
                        pnl_item = QTableWidgetItem(pnl_str); roe_item = QTableWidgetItem(roe_str)
                        self.position_table.setItem(row_count, 0, QTableWidgetItem(symbol)); self.position_table.setItem(row_count, 1, QTableWidgetItem(p_update.get('pa')))
                        self.position_table.setItem(row_count, 2, QTableWidgetItem(p_update.get('ep'))); self.position_table.setItem(row_count, 3, pnl_item); self.position_table.setItem(row_count, 4, roe_item)
                        self.live_position_data[unique_key] = {
                            'row': row_count, 'symbol': symbol, 'amount': amount, 'entry': entry_price, 'margin': margin, 'positionSide': position_side,
                            'pnl_item': pnl_item, 'roe_item': roe_item
                        }
        except Exception as e: print(f"계정 업데이트 처리 오류: {e}")
        
        # 포지션 라인 다시 그리기
        for key, pos_data in self.live_position_data.items():
            if pos_data['symbol'] == self.current_symbol:
                self.draw_position_line_on_chart(pos_data['entry'], pos_data['positionSide'])

    def reindex_position_rows(self):
        live_data_copy = self.live_position_data.copy(); self.live_position_data.clear()
        for row in range(self.position_table.rowCount()):
            symbol = self.position_table.item(row, 0).text(); amount_str = self.position_table.item(row, 1).text(); amount = float(amount_str)
            found_key = None
            for key, data in live_data_copy.items():
                if data['symbol'] == symbol and data['amount'] == amount: found_key = key; break
            if found_key:
                data = live_data_copy[found_key]; data['row'] = row
                data['pnl_item'] = self.position_table.item(row, 3); data['roe_item'] = self.position_table.item(row, 4)
                self.live_position_data[found_key] = data
        print(f"포지션 행 인덱스 재정렬 완료. (활성: {len(self.live_position_data)})")

    @pyqtSlot(list)
    def handle_ticker_update(self, ticker_list):
        try:
            for item in ticker_list:
                symbol = item.get('s') 
                if hasattr(self, 'order_symbol_input') and symbol == self.order_symbol_input.text():
                    last_price_str = item.get('c', '0.0'); last_price = float(last_price_str)
                    if self.trade_price_label:
                        self.trade_price_label.setText(last_price_str); base_style = self.default_price_label_style; color_style = ""
                        if last_price > self.last_price_for_color: color_style = "color: #00b050;"
                        elif last_price < self.last_price_for_color: color_style = "color: #c00000;"
                        else: color_style = "color: white;" if self.is_dark_mode else "color: black;"
                        self.trade_price_label.setStyleSheet(base_style + color_style)
                        if last_price != 0: self.last_price_for_color = last_price
                if symbol == self.current_symbol:
                    if self.price_line_item:
                        last_price_str = item.get('c', '0.0'); last_price = float(last_price_str)
                        if last_price > 0:
                            if self.detected_precision is None:
                                if '.' in last_price_str: new_precision = len(last_price_str.split('.')[-1])
                                else: new_precision = 0
                                print(f"[{symbol}] Precision 동적 감지: {new_precision} (Y축/포지션 라인 갱신)")
                                self.y_axis.setPrecision(new_precision); self.detected_precision = new_precision
                                self.remove_all_position_lines_from_chart()
                                for key, pos_data in self.live_position_data.items():
                                    if pos_data['symbol'] == self.current_symbol:
                                        self.draw_position_line_on_chart(pos_data['entry'], pos_data['positionSide'])
                            self.price_line_item.setPos(last_price)
                            precision = self.detected_precision if self.detected_precision is not None else 2
                            self.price_line_item.label.setText(f"{last_price:.{precision}f}")
                            self.price_line_item.show()
                        df = self.candlestick_item.data
                        if not df.empty:
                            try:
                                last_row_index = df.index[-1]; df.loc[last_row_index, 'close'] = last_price
                                if last_price > df.loc[last_row_index, 'high']: df.loc[last_row_index, 'high'] = last_price
                                if last_price < df.loc[last_row_index, 'low']: df.loc[last_row_index, 'low'] = last_price
                                self.candlestick_item.setData(df)
                            except Exception as e: print(f"실시간 캔들 업데이트 중 오류 (무시됨): {e}")
                for key, pos_data in self.live_position_data.items():
                    if pos_data['symbol'] != symbol: continue 
                    row = pos_data['row']; margin = pos_data.get('margin', 0)
                    pnl_item = pos_data.get('pnl_item'); roe_item = pos_data.get('roe_item')
                    if not pnl_item or not roe_item or margin == 0: continue
                    pnl = 0.0; roe = 0.0; pnl_precision = 2; last_price = float(item.get('c', 0)); 
                    if last_price == 0: continue
                    if self.current_market_type == 'dapi':
                        pnl_precision = 8; contract_size = 0
                        if symbol == "BTCUSD_PERP": contract_size = 100
                        elif symbol == "ETHUSD_PERP": contract_size = 10
                        if contract_size > 0 and pos_data['entry'] > 0:
                            amount_val = pos_data['amount']
                            if amount_val > 0: pnl = (1/pos_data['entry'] - 1/last_price) * amount_val * contract_size
                            else: pnl = (1/last_price - 1/pos_data['entry']) * abs(amount_val) * contract_size
                        else: pnl = (last_price - pos_data['entry']) * pos_data['amount']
                    else:
                        pnl = (last_price - pos_data['entry']) * pos_data['amount']; pnl_precision = 2
                    if margin != 0: roe = (pnl / margin) * 100
                    pnl_item.setText(f"{pnl:.{pnl_precision}f}"); roe_item.setText(f"{roe:.2f}%")
                    color = QColor("white") if self.is_dark_mode else QColor("black")
                    if pnl > 0: color = QColor(0, 180, 0)
                    elif pnl < 0: color = QColor(200, 0, 0)
                    pnl_item.setForeground(color); roe_item.setForeground(color)
        except Exception as e: print(f"티커 업데이트 처리 오류: {e}")

    @pyqtSlot(dict)
    def handle_order_update(self, data):
        try:
            o = data.get('o', {}); order_id = str(o.get('i')); status = o.get('X')
            if order_id in self.pending_market_orders:
                if status == 'FILLED':
                    QMessageBox.information(self, "Order Success (FILLED)", f"Order Filled (Status: {status}):\n{o.get('S')} {o.get('q')} {o.get('s')}\nAvg. Price: {o.get('ap', 'N/A')}")
                    self.pending_market_orders.remove(order_id)
                elif status in ['CANCELED', 'REJECTED', 'EXPIRED']:
                    QMessageBox.warning(self, "Order Failed (WebSocket)", f"Order {order_id} failed or was canceled.\nStatus: {status}\nReason: {o.get('r', 'N/A')}")
                    self.pending_market_orders.remove(order_id)
            found_row = -1
            for row in range(self.order_table.rowCount()):
                if self.order_table.item(row, 6) and self.order_table.item(row, 6).text() == order_id: found_row = row; break
            if status in ['FILLED', 'CANCELED', 'EXPIRED', 'REJECTED']:
                if found_row != -1: self.order_table.removeRow(found_row)
            elif status == 'NEW':
                if found_row == -1:
                    row_count = self.order_table.rowCount(); self.order_table.insertRow(row_count)
                    self.order_table.setItem(row_count, 0, QTableWidgetItem(o['s'])); self.order_table.setItem(row_count, 1, QTableWidgetItem(o['o']))
                    self.order_table.setItem(row_count, 2, QTableWidgetItem(o['S'])); self.order_table.setItem(row_count, 3, QTableWidgetItem(o['p']))
                    self.order_table.setItem(row_count, 4, QTableWidgetItem(o['q'])); self.order_table.setItem(row_count, 5, QTableWidgetItem(o['z'])) 
                    self.order_table.setItem(row_count, 6, QTableWidgetItem(order_id))
            elif status == 'PARTIALLY_FILLED':
                if found_row != -1: self.order_table.item(found_row, 5).setText(o['z']) 
        except Exception as e: print(f"주문 업데이트 처리 오류: {e}")

    def update_chart(self, symbol, interval, klines_data=None, is_refresh=False):
        if not is_refresh:
            print(f"pyqtgraph 차트 로드 시도: {symbol} {interval}")

        if not binance_api.is_api_key_active():
            print("API가 연결되지 않아 차트를 로드할 수 없습니다.")
            return

        klines = klines_data
        if klines is None:
            klines = binance_api.get_ohlcv_data(symbol, interval, 1000)
        
        if not klines:
            print(f"{symbol} {interval} 캔들 데이터를 가져오는 데 실패했습니다.")
            self.candlestick_item.setData(pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close']))
            return

        df = pd.DataFrame(klines, columns=[
            'time', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        
        df = df[['time', 'open', 'high', 'low', 'close']].astype(float)
        df['time'] = df['time'] / 1000
        self.candlestick_item.setData(df)
        
        if not is_refresh:
            print("심볼/타임프레임/계정 변경 감지. 라인을 새로고침합니다.")
            self.price_line_item.hide()
            self.remove_all_position_lines_from_chart()
            for key, pos_data in self.live_position_data.items():
                if pos_data['symbol'] == symbol:
                    self.draw_position_line_on_chart(pos_data['entry'], pos_data['positionSide'])
            print(f"pyqtgraph 차트 업데이트 완료: {symbol} {interval}")


    def change_timeframe(self, timeframe_value):
        if self.current_interval == timeframe_value: return 
        old_tf = self.current_interval; self.current_interval = timeframe_value
        self.update_timeframe_buttons(self.current_interval, old_tf)
        if "app_settings" not in self.config_data: self.config_data["app_settings"] = {}
        self.config_data["app_settings"]["last_timeframe"] = self.current_interval
        binance_api.save_config_data(self.config_data)
        self.update_chart(self.current_symbol, self.current_interval)
        
    def update_timeframe_buttons(self, new_tf, old_tf):
        if old_tf and old_tf in self.buttons: self.buttons[old_tf].setStyleSheet("")
        if new_tf and new_tf in self.buttons: self.buttons[new_tf].setStyleSheet("background-color: #007bff; color: white;")
        
    def toggle_dark_mode(self, checked):
        self.is_dark_mode = checked
        self.apply_theme()

    def apply_theme(self):
        app = QApplication.instance()
        if self.is_dark_mode:
            self.dark_mode_button.setText("☀️ Light Mode")
            dark_palette = QPalette()
            dark_palette.setColor(QPalette.Window, QColor(53, 53, 53)); dark_palette.setColor(QPalette.WindowText, Qt.white)
            dark_palette.setColor(QPalette.Base, QColor(35, 35, 35)); dark_palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ToolTipBase, Qt.white); dark_palette.setColor(QPalette.ToolTipText, Qt.white)
            dark_palette.setColor(QPalette.Text, Qt.white); dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
            dark_palette.setColor(QPalette.ButtonText, Qt.white); dark_palette.setColor(QPalette.BrightText, Qt.red)
            dark_palette.setColor(QPalette.Link, QColor(42, 130, 218)); dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
            dark_palette.setColor(QPalette.HighlightedText, Qt.black); dark_palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
            dark_palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
            app.setPalette(dark_palette)
            if self.chart_widget:
                self.chart_widget.setBackground(QColor(35, 35, 35)); self.y_axis.setPen('w'); self.chart_widget.getAxis('bottom').setPen('w')
        else:
            self.dark_mode_button.setText("🌙 Dark Mode"); app.setPalette(self.original_palette) 
            if self.chart_widget:
                self.chart_widget.setBackground('w'); self.y_axis.setPen('k'); self.chart_widget.getAxis('bottom').setPen('k')
        if hasattr(self, 'open_button'): self.update_order_panel_mode()
        self.update_clear_button_style()

            
    def draw_position_line_on_chart(self, price, side):
        if not hasattr(self, 'chart_widget') or price == 0: return
        if price in self.position_lines: return
        color = '#00b050' if side == "LONG" else '#c00000'; pen = pg.mkPen(color, style=Qt.DotLine, width=2)
        precision = self.y_axis.precision; label_text = f"{side} @ {price:.{precision}f}"
        position_line = pg.InfiniteLine(
            pos=price, angle=0, movable=False, pen=pen, label=label_text,
            labelOpts={'position': 0.9, 'color': color, 'movable': True, 'fill': (0, 0, 0, 150), 'anchor': (1, 0.5)}
        )
        self.chart_widget.addItem(position_line); self.position_lines[price] = position_line
        print(f"차트 라인 추가: {side} @ {price}")

    def remove_all_position_lines_from_chart(self):
        if not hasattr(self, 'chart_widget'): return
        for price, line_item in self.position_lines.items():
            try: self.chart_widget.removeItem(line_item)
            except Exception as e: print(f"차트 라인 제거 중 오류 (무시됨): {e}")
        self.position_lines.clear()

    def refresh_chart_data(self):
        if binance_api.is_api_key_active() and self.current_symbol:
            # print(f"[{self.current_symbol}] 60초 타이머: 캔들 데이터 새로고침")
            self.update_chart(self.current_symbol, self.current_interval, is_refresh=True)

    def resizeEvent(self, event):
        if self.loading_overlay: self.loading_overlay.resize(self.tabs.size())
        super(BinanceTrader, self).resizeEvent(event)

    def animate_loading_text(self):
        self.loading_animation_state = (self.loading_animation_state + 1) % 3
        if self.loading_animation_state == 0: dots = "."
        elif self.loading_animation_state == 1: dots = ".."
        else: dots = "..."
        self.loading_overlay.setText(f"{self.base_loading_text}\nPlease wait{dots}")

    def closeEvent(self, event):
        print("프로그램 종료 중...")
        if self.chart_refresh_timer: self.chart_refresh_timer.stop()
        if self.loading_animation_timer: self.loading_animation_timer.stop()
        
        if self.ws_thread and self.ws_thread.isRunning():
            self.ws_thread.stop(); self.ws_thread.wait()
        if self.ticker_thread and self.ticker_thread.isRunning():
            self.ticker_thread.stop(); self.ticker_thread.wait()
            
        binance_api.set_active_api_keys(None, None)
        event.accept()