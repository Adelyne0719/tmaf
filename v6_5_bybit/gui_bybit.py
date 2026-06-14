# gui_bybit.py
import tkinter as tk
import re
from tkinter import ttk, messagebox
import logging
# from binance.enums import * # Bybit 버전에서는 필요 없음
import configparser

# === iOS 스타일 토글 스위치 (부드러운 캡슐 + 애니메이션) ===
# (이 클래스는 순수 Tkinter이므로 변경 사항 없음)
class IOSToggleSwitch(tk.Frame):
    """
    iPhone 스타일 토글.
    checked=True  => ON (우측)
    checked=False => OFF (좌측)
    """
    def __init__(self, master=None, width=54, height=30,
                 checked=False, command=None,
                 on_color="#FF3B30", off_color="#34C759",
                 knob_outline="#E5E5EA", anim_ms=120, **kwargs):
        super().__init__(master, **kwargs)
        self.width  = int(width)
        self.height = int(height)
        self.pad = 2
        self.r = (self.height - 2*self.pad) // 2
        self.checked = bool(checked)
        self.command = command
        self.on_color = on_color
        self.off_color = off_color
        self.knob_outline = knob_outline
        self.anim_ms = int(anim_ms)
        self._anim_steps = 12

        try:
            bg_color = master.cget("bg")
        except tk.TclError:
            try:
                bg_color = self.winfo_toplevel().cget("bg")
            except Exception:
                bg_color = "#FFFFFF"

        self.canvas = tk.Canvas(
            self, width=self.width, height=self.height,
            bd=0, highlightthickness=0, relief="flat", bg=bg_color
        )
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._toggle)

        self._bg_ids = []
        self._knob_id = None
        self._draw_static()
        self._draw_dynamic()

    def _draw_static(self):
        for i in getattr(self, "_bg_ids", []):
            self.canvas.delete(i)
        self._bg_ids = []
        if getattr(self, "_knob_id", None) is not None:
            self.canvas.delete(self._knob_id)
            self._knob_id = None

        x1, y1 = int(self.pad), int(self.pad)
        x2, y2 = int(self.width - self.pad), int(self.height - self.pad)
        r = int((y2 - y1) // 2)

        fill = (self.on_color if self.checked else self.off_color)

        rect = self.canvas.create_rectangle(
            x1 + r, y1, x2 - r, y2, fill=fill, outline="", width=0
        )
        left_arc = self.canvas.create_arc(
            x1, y1, x1 + 2*r, y2, start=90, extent=180,
            style=tk.CHORD, fill=fill, outline="", width=0
        )
        right_arc = self.canvas.create_arc(
            x2 - 2*r, y1, x2, y2, start=270, extent=180,
            style=tk.CHORD, fill=fill, outline="", width=0
        )
        self._bg_ids = [rect, left_arc, right_arc]

        knob_d = (y2 - y1)
        start_x = self._knob_right_x() if self.checked else self._knob_left_x()
        self._knob_id = self.canvas.create_oval(
            start_x, y1, start_x + knob_d, y1 + knob_d,
            fill="white", outline=self.knob_outline
        )

    def _set_bg_fill(self, fill):
        for i in self._bg_ids:
            self.canvas.itemconfig(i, fill=fill)

    def _knob_left_x(self):
        return self.pad

    def _knob_right_x(self):
        return self.width - self.pad - (self.height - 2*self.pad)

    def _draw_dynamic(self):
        self._set_bg_fill(self.on_color if self.checked else self.off_color)
        target_x = self._knob_right_x() if self.checked else self._knob_left_x()
        self._move_knob_to(target_x)

    def _move_knob_to(self, target_x):
        x1, y1, x2, y2 = self.canvas.coords(self._knob_id)
        cur_x = x1
        dist = target_x - cur_x
        if dist == 0:
            return
        steps = self._anim_steps
        per  = dist / steps
        delay = max(1, self.anim_ms // max(1, steps))

        def step(i=0):
            if i >= steps:
                x1_now, y1_now, x2_now, y2_now = self.canvas.coords(self._knob_id)
                dx = target_x - x1_now
                self.canvas.move(self._knob_id, dx, 0)
                return
            self.canvas.move(self._knob_id, per, 0)
            self.canvas.after(delay, lambda: step(i+1))

        step(0)

    def _toggle(self, _event=None):
        self.checked = not self.checked
        self._set_bg_fill(self.on_color if self.checked else self.off_color)
        target_x = self._knob_right_x() if self.checked else self._knob_left_x()
        self._move_knob_to(target_x)
        if callable(self.command):
            try:
                self.command(self.checked)
            except Exception:
                pass

    def set(self, value: bool):
        value = bool(value)
        if value == self.checked:
            return
        self.checked = value
        self._draw_dynamic()

    def get(self) -> bool:
        return self.checked

class GuiManager:
    def __init__(self, root, symbol, steps, balance_asset, settings_file_path):
        self.root = root
        self.symbol = symbol
        self.steps = steps
        self.balance_asset = balance_asset
        self.settings_file_path = settings_file_path

        self.root.title("자동매매 봇 상태 (Bybit Ver.)") # 제목 수정
        self.root.geometry("1100x860")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 콜백 함수 및 상태 변수
        self._toggle_command = None
        self._on_closing_callback = None
        self._config_update_callback = None
        self._recalculate_callback = None
        self._is_running = False
        self.cumulative_pnl = 0.0
        self.current_config = {}
        self._stop_is_reserved = False
        
        # === [수정] Bybit에 맞는 설정 구조 ===
        self.settings_structure = {
            "API": [
                ('API_KEY', 'api_key', str),
                ('API_SECRET', 'api_secret', str)
            ],
            "Bybit 공통 설정": [ # Bybit 전용 설정
                ('TESTNET', 'testnet', bool)
            ],
            "USDT-M 설정 (Linear)": [ # URL 제거
                ('USDT_M_SYMBOL', 'symbol', str),
                ('USDT_M_BALANCE_ASSET', 'balance_asset', str)
            ],
            "COIN-M 설정 (Inverse)": [ # URL 제거
                ('COIN_M_SYMBOL', 'symbol', str),
                ('COIN_M_BALANCE_ASSET', 'balance_asset', str)
            ],
            "거래 기본 설정": [
                ('DEFAULT_TRADING_MODE', 'default_trading_mode', str),
                ('POSITION_BIAS', 'position_bias', str),
                ('MARGIN_MODE', 'margin_mode', str), # <--- 이 줄을 추가하세요
                ('AUTO_START_ON_RUN', 'auto_start_on_run', bool),
                ('KLINE_INTERVAL', 'kline_interval', str),
                ('TARGET_LEVERAGE', 'target_leverage', int),
                ('BALANCE_USAGE_PERCENTAGE', 'balance_usage_percentage', float),
                ('PRICE_RATIO_MIN', 'price_ratio_min', float),
                ('PRICE_RATIO_MAX', 'price_ratio_max', float)
            ],
            "전략 파라미터": [
                ('STEPS', 'steps', int),
                ('DIVIDE', 'divide', int),
                ('NO_SIGNAL_ZONE', 'no_signal_zone', float),
                ('MAGINOT', 'maginot', float),
                ('CALLBACK_RATE', 'callback_rate', float),
                ('CALLBACK_RATE_FOR_LAST', 'callback_rate_for_last', float),
                ('DIVIDE_RATE', 'divide_rate', float)
            ],
            "수량 파라미터 (Entry)": [
                ('ENTRY_START', 'entry_start', float),
                ('ENTRY_END', 'entry_end', float),
                ('ENTRY_EXPONENT', 'entry_exponent', float)
            ],
            "수량 파라미터 (Hedge)": [
                ('HEDGE_START', 'hedge_start', float),
                ('HEDGE_END', 'hedge_end', float),
                ('HEDGE_EXPONENT', 'hedge_exponent', float)
            ],
            "익절 파라미터 (Exit)": [
                ('EXIT_FIRST', 'exit_first', float),
                ('EXIT_LAST', 'exit_last', float),
                ('EXIT_EXPONENT', 'exit_exponent', float),
                ('EXIT_DISTANCE_MULTIPLIER', 'exit_distance_multiplier', float)
            ],
            "익절 파라미터 (TSM)": [
                ('TSM_EXIT_CALLBACK_RATE', 'tsm_exit_callback_rate', float),
                ('TSM_EXIT_ENABLED', 'tsm_exit_enabled', bool),
                ('TSM_EXIT_CALLBACK_RATE_MAX', 'tsm_exit_callback_rate_max', float),
                ('TSM_EXIT_CALLBACK_RATE_MIN', 'tsm_exit_callback_rate_min', float)
            ],
            "기타 설정": [
                ('RECONNECT_DELAY', 'reconnect_delay', int),
                ('POSITION_UPDATE_INTERVAL', 'position_update_interval', int),
                ('OPEN_ORDERS_CHECK_INTERVAL', 'open_orders_check_interval', int),
                ('PERIODIC_TIME_CHECK_INTERVAL_SECONDS', 'periodic_time_check_interval_seconds', int),
                ('TIME_DRIFT_THRESHOLD_MS', 'time_drift_threshold_ms', int),
                ('ORDER_RETRY_ATTEMPTS', 'order_retry_attempts', int),
                ('ORDER_RETRY_DELAY_SECONDS', 'order_retry_delay_seconds', int),
                ('EMERGENCY_HEDGE_RATIO', 'emergency_hedge_ratio', float)
            ]
        }
        # === [수정 끝] ===
        
        self.position_bias_var = tk.StringVar(value='LONG')
        self._position_switch = None
        self.trading_mode_var = tk.StringVar(value='COIN-M')
        self._trading_mode_switch = None

        # 스타일 설정 (변경 없음)
        style = ttk.Style()
        style.configure("TLabel", padding=3, font=('Helvetica', 9))
        style.configure("Value.TLabel", font=('Helvetica', 9), foreground="blue")
        style.configure("Status.TLabel", font=('Helvetica', 10, 'bold'))
        style.configure("WsStatus.TLabel", font=('Helvetica', 9, 'italic'))
        style.configure("WsData.TLabel", font=('Helvetica', 8), foreground="gray")
        style.configure("Qty.TLabel", font=('Helvetica', 9), foreground="green")
        style.configure("CumQty.TLabel", font=('Helvetica', 9), foreground="purple")
        style.configure("HedgeQty.TLabel", font=('Helvetica', 9), foreground="red")
        style.configure("CumHedgeQty.TLabel", font=('Helvetica', 9), foreground="darkred")
        style.configure("ExitRatio.TLabel", font=('Helvetica', 9), foreground="brown")
        style.configure("KeyStatus.TLabel", font=('Helvetica', 9), foreground="orange") # 이 스타일은 이제 사용되지 않음
        style.configure("PosLabel.TLabel", font=('Helvetica', 9, 'bold'))
        style.configure("PosValue.TLabel", font=('Helvetica', 9))
        style.configure("PosPnl.TLabel", font=('Helvetica', 9))
        style.configure("LargePrice.TLabel", font=('Helvetica', 16, 'bold'), foreground='black')
        style.configure("WsConn.TLabel", font=('Helvetica', 8), foreground='gray')
        style.configure("Step.TLabel", font=('Helvetica', 10, 'bold'), foreground='magenta')
        style.configure("Treeview.Heading", font=('Helvetica', 9, 'bold'))
        style.configure("Toggle.TButton", font=('Helvetica', 10, 'bold'))
        style.configure("Pnl.TLabel", font=('Helvetica', 9, 'bold'), foreground="darkgreen")
        style.configure("NszLabel.TLabel", font=('Helvetica', 9, 'bold'), foreground="orange")
        style.configure("NszValue.TLabel", font=('Helvetica', 9), foreground="orange")
        style.configure("ExitTargetTitle.TLabel", font=('Helvetica', 9, 'bold'), foreground='darkcyan')
        style.configure("ExitTargetValue.TLabel", font=('Helvetica',9), foreground='darkcyan')

        # GUI 변수 초기화
        self.symbol_var = tk.StringVar(value=self.symbol)
        self.leverage_var = tk.StringVar(value="로딩 중...")
        self.symbol_info_var = tk.StringVar(value="로딩 중...")
        self.min_qty_var = tk.StringVar(value="N/A")
        self.balance_var = tk.StringVar(value="로딩 중...")
        # === [수정] listen_key_status_var -> ws_connection_var ===
        self.ws_connection_var = tk.StringVar(value="대기 중...")
        # === [수정 끝] ===
        self.current_step_var = tk.StringVar(value="대기")
        self.status_var = tk.StringVar(value="초기화 중...")
        self.total_pnl_var = tk.StringVar(value="0.00")
        self.large_price_var = tk.StringVar(value="-")
        self.kline_data_var = tk.StringVar(value="-")
        self.kline_status_var = tk.StringVar(value="대기 중...")
        self.trade_status_var = tk.StringVar(value="대기 중...")
        self.user_status_var = tk.StringVar(value="대기 중...")
        self.long_size_var = tk.StringVar(value="-")
        self.long_entry_var = tk.StringVar(value="-")
        self.long_pnl_var = tk.StringVar(value="-")
        self.short_size_var = tk.StringVar(value="-")
        self.short_entry_var = tk.StringVar(value="-")
        self.short_pnl_var = tk.StringVar(value="-")
        self.nsz_range_var = tk.StringVar(value="-")
        self.exit_target_price_var = tk.StringVar(value="-")
        self.signal_status_var = tk.StringVar(value="대기 중...")

        # 메인 프레임 레이아웃 구성 (변경 없음)
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1); root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1); main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1); main_frame.columnconfigure(3, weight=1)
        main_frame.rowconfigure(0, weight=1); main_frame.rowconfigure(1, weight=0)

        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        left_frame.columnconfigure(0, weight=1); left_frame.rowconfigure(1, weight=1); left_frame.rowconfigure(2, weight=0)

        info_frame = ttk.LabelFrame(left_frame, text="기본 정보", padding="10")
        info_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)
        info_frame.columnconfigure(1, weight=1)
        self._create_info_widgets(info_frame)

        ws_frame = ttk.LabelFrame(left_frame, text="웹소켓 상태", padding="10")
        ws_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        ws_frame.columnconfigure(0, weight=1)
        self._create_ws_status_widgets(ws_frame)

        control_frame = ttk.Frame(left_frame, padding="5")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=(10,5))
        control_frame.columnconfigure(0, weight=1)
        self._create_control_buttons(control_frame)

        pos_frame = ttk.LabelFrame(main_frame, text="현재 포지션", padding="10")
        pos_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        pos_frame.columnconfigure(1, weight=1); pos_frame.columnconfigure(3, weight=1)
        self._create_position_widgets(pos_frame)

        orders_frame = ttk.LabelFrame(main_frame, text="미체결 주문", padding="10")
        orders_frame.grid(row=1, column=1, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        orders_frame.columnconfigure(0, weight=1); orders_frame.rowconfigure(0, weight=1)
        self._create_open_orders_widgets(orders_frame)

        self.entry_qty_frame = ttk.LabelFrame(main_frame, text="진입 수량 (스텝 / 누적)", padding="10")
        self.entry_qty_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_quantity_widgets(self.entry_qty_frame, "step_qty_vars", "cumulative_qty_vars", "Qty.TLabel", "CumQty.TLabel")

        self.hedge_qty_frame = ttk.LabelFrame(main_frame, text="헷지 수량 (스텝 / 누적)", padding="10")
        self.hedge_qty_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_quantity_widgets(self.hedge_qty_frame, "step_hedge_qty_vars", "cumulative_hedge_qty_vars", "HedgeQty.TLabel", "CumHedgeQty.TLabel")

        self.exit_ratio_frame = ttk.LabelFrame(main_frame, text="Exit 비율 (스텝별)", padding="10")
        self.exit_ratio_frame.grid(row=0, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_ratio_widgets(self.exit_ratio_frame)

        signal_status_frame = ttk.LabelFrame(main_frame, text="시그널 현황", padding="5")
        signal_status_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=5)
        signal_status_frame.columnconfigure(0, weight=1)
        ttk.Label(signal_status_frame, textvariable=self.signal_status_var, style="Status.TLabel").grid(row=0, column=0, sticky=tk.W)

    def _create_info_widgets(self, parent_frame):
        row_idx = 0
        ttk.Label(parent_frame, text="심볼:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.symbol_var, style="Value.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text="레버리지:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.leverage_var, style="Value.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text="심볼 정보:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.symbol_info_var, style="Value.TLabel", wraplength=300).grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text="최소수량:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.min_qty_var, style="Value.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text=f"{self.balance_asset} 잔고:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.balance_var, style="Value.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        # === [수정] Listen Key -> 웹소켓 연결 ===
        ttk.Label(parent_frame, text="웹소켓 연결:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.ws_connection_var, style="Value.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        # === [수정 끝] ===
        row_idx += 1
        ttk.Label(parent_frame, text="현재 단계:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.current_step_var, style="Step.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text="봇 상태:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.status_var, style="Status.TLabel").grid(column=1, row=row_idx, sticky=tk.W)
        row_idx += 1
        ttk.Label(parent_frame, text="총 실현 손익:").grid(column=0, row=row_idx, sticky=tk.W)
        ttk.Label(parent_frame, textvariable=self.total_pnl_var, style="Pnl.TLabel").grid(column=1, row=row_idx, sticky=tk.W)

    def _create_ws_status_widgets(self, parent_frame):
        # (변경 없음)
        ws_row_idx = 0
        parent_frame.rowconfigure(1, weight=1)
        ttk.Label(parent_frame, textvariable=self.large_price_var, style="LargePrice.TLabel").grid(column=0, row=ws_row_idx, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        ws_row_idx += 1
        kline_data_label = ttk.Label(parent_frame, textvariable=self.kline_data_var, style="WsData.TLabel", wraplength=300, anchor='nw')
        kline_data_label.grid(column=0, row=ws_row_idx, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=2)
        ws_row_idx += 1
        status_indicator_frame = ttk.Frame(parent_frame)
        status_indicator_frame.grid(column=0, row=ws_row_idx, columnspan=3, sticky=(tk.W, tk.E), pady=(5,0))
        status_indicator_frame.columnconfigure(0, weight=1); status_indicator_frame.columnconfigure(1, weight=1); status_indicator_frame.columnconfigure(2, weight=1)
        kline_status_frame = ttk.Frame(status_indicator_frame)
        kline_status_frame.grid(column=0, row=0, sticky=tk.W)
        ttk.Label(kline_status_frame, text="Kline:", style="WsConn.TLabel").pack(side=tk.LEFT, padx=(0,2))
        ttk.Label(kline_status_frame, textvariable=self.kline_status_var, style="WsStatus.TLabel").pack(side=tk.LEFT)
        trade_status_frame = ttk.Frame(status_indicator_frame)
        trade_status_frame.grid(column=1, row=0, sticky=tk.W, padx=(5,0))
        ttk.Label(trade_status_frame, text="Trade:", style="WsConn.TLabel").pack(side=tk.LEFT, padx=(0,2))
        ttk.Label(trade_status_frame, textvariable=self.trade_status_var, style="WsStatus.TLabel").pack(side=tk.LEFT)
        user_status_frame = ttk.Frame(status_indicator_frame)
        user_status_frame.grid(column=2, row=0, sticky=tk.W, padx=(5,0))
        ttk.Label(user_status_frame, text="User:", style="WsConn.TLabel").pack(side=tk.LEFT, padx=(0,2))
        ttk.Label(user_status_frame, textvariable=self.user_status_var, style="WsStatus.TLabel").pack(side=tk.LEFT)

    def _create_position_widgets(self, parent_frame):
        # (위젯 생성은 변경 없음, 데이터 업데이트 로직은 아래 update_position_display에서 변경)
        row_idx = 0
        parent_frame.columnconfigure(0, weight=0); parent_frame.columnconfigure(1, weight=1)
        parent_frame.columnconfigure(2, weight=0); parent_frame.columnconfigure(3, weight=1)
        ttk.Label(parent_frame, text="LONG:", style="PosLabel.TLabel").grid(column=0, row=row_idx, columnspan=4, sticky=tk.W, pady=(0,2)); row_idx += 1
        ttk.Label(parent_frame, text=" 수량:").grid(column=0, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.long_size_var, style="PosValue.TLabel").grid(column=1, row=row_idx, sticky=(tk.W, tk.E), padx=(0,5))
        ttk.Label(parent_frame, text=" 진입가:").grid(column=2, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.long_entry_var, style="PosValue.TLabel").grid(column=3, row=row_idx, sticky=(tk.W, tk.E), padx=(0,5)); row_idx += 1
        ttk.Label(parent_frame, text=" PNL:").grid(column=0, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.long_pnl_var, style="PosPnl.TLabel").grid(column=1, row=row_idx, columnspan=3, sticky=(tk.W, tk.E), padx=(0,5)); row_idx += 1
        ttk.Label(parent_frame, text="SHORT:", style="PosLabel.TLabel").grid(column=0, row=row_idx, columnspan=4, sticky=tk.W, pady=(5,2)); row_idx += 1
        ttk.Label(parent_frame, text=" 수량:").grid(column=0, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.short_size_var, style="PosValue.TLabel").grid(column=1, row=row_idx, sticky=(tk.W, tk.E), padx=(0,5))
        ttk.Label(parent_frame, text=" 진입가:").grid(column=2, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.short_entry_var, style="PosValue.TLabel").grid(column=3, row=row_idx, sticky=(tk.W, tk.E), padx=(0,5)); row_idx += 1
        ttk.Label(parent_frame, text=" PNL:").grid(column=0, row=row_idx, sticky=tk.W, padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.short_pnl_var, style="PosPnl.TLabel").grid(column=1, row=row_idx, columnspan=3, sticky=(tk.W, tk.E), padx=(0,5)); row_idx += 1
        ttk.Label(parent_frame, text="NSZ:", style="NszLabel.TLabel").grid(column=0, row=row_idx, sticky=tk.W, pady=(5,0), padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.nsz_range_var, style="NszValue.TLabel", anchor='w').grid(column=1, row=row_idx, sticky=(tk.W, tk.E), pady=(5,0), padx=(0,5))
        ttk.Label(parent_frame, text="Next Exit:", style="ExitTargetTitle.TLabel").grid(column=2, row=row_idx, sticky=tk.W, pady=(5,0), padx=(5,2))
        ttk.Label(parent_frame, textvariable=self.exit_target_price_var, style="ExitTargetValue.TLabel", anchor='e').grid(column=3, row=row_idx, sticky=(tk.W, tk.E), pady=(5,0), padx=(0,5))

    def _create_open_orders_widgets(self, parent_frame):
        # (위젯 생성은 변경 없음, 데이터 업데이트 로직은 아래 _update_treeview에서 변경)
        self.orders_tree = ttk.Treeview(parent_frame, columns=("CustomType", "ID", "Side", "Type", "Qty", "Price"), show="headings", height=5)
        self.orders_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=self.orders_tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.orders_tree.configure(yscrollcommand=scrollbar.set)
        self.orders_tree.heading("CustomType", text="구분"); self.orders_tree.heading("ID", text="ID")
        self.orders_tree.heading("Side", text="Side"); self.orders_tree.heading("Type", text="Type")
        self.orders_tree.heading("Qty", text="수량"); self.orders_tree.heading("Price", text="가격")
        self.orders_tree.column("CustomType", width=60, anchor=tk.W); self.orders_tree.column("ID", width=80, anchor=tk.W)
        self.orders_tree.column("Side", width=50, anchor=tk.CENTER); self.orders_tree.column("Type", width=80, anchor=tk.W)
        self.orders_tree.column("Qty", width=70, anchor=tk.E); self.orders_tree.column("Price", width=80, anchor=tk.E)

    def _create_quantity_widgets(self, parent_frame, step_var_name, cumul_var_name, step_style, cumul_style):
        # (변경 없음)
        step_vars = []; cumul_vars = []
        parent_frame.columnconfigure(1, weight=1); parent_frame.columnconfigure(2, weight=1)
        for i in range(self.steps):
            ttk.Label(parent_frame, text=f"STEP {i}:").grid(column=0, row=i, sticky=tk.W, padx=2, pady=1)
            step_var = tk.StringVar(value="계산 전"); step_vars.append(step_var)
            ttk.Label(parent_frame, textvariable=step_var, style=step_style).grid(column=1, row=i, sticky=tk.W, padx=2, pady=1)
            cum_var = tk.StringVar(value="계산 전"); cumul_vars.append(cum_var)
            ttk.Label(parent_frame, textvariable=cum_var, style=cumul_style).grid(column=2, row=i, sticky=tk.W, padx=2, pady=1)
        setattr(self, step_var_name, step_vars); setattr(self, cumul_var_name, cumul_vars)

    def _create_ratio_widgets(self, parent_frame):
        # (변경 없음)
        self.exit_ratio_vars = []
        parent_frame.columnconfigure(1, weight=1)
        for i in range(self.steps):
            ttk.Label(parent_frame, text=f"STEP {i}:").grid(column=0, row=i, sticky=tk.W, padx=2, pady=1)
            exit_var = tk.StringVar(value="계산 전"); self.exit_ratio_vars.append(exit_var)
            ttk.Label(parent_frame, textvariable=exit_var, style="ExitRatio.TLabel").grid(column=1, row=i, sticky=tk.W, padx=2, pady=1)

    def _create_control_buttons(self, parent_frame):
        # (변경 없음)
        self.toggle_button = ttk.Button(parent_frame, text="시작", command=self.toggle_bot_command, style="Toggle.TButton")
        self.toggle_button.grid(row=0, column=0, padx=5, sticky=(tk.W, tk.E))
        self.settings_button = ttk.Button(parent_frame, text="설정 변경", command=self.open_settings_window)
        self.settings_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        self.pending_config_var = tk.StringVar(value="설정 변경 적용 대기중")
        self.pending_config_label = ttk.Label(parent_frame, textvariable=self.pending_config_var, foreground="orange", font=('Helvetica', 9, 'italic'))
        self.pending_config_label.grid(row=1, column=0, columnspan=2, pady=(4,0), sticky=tk.N)
        self.pending_config_label.grid_remove()
        
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.columnconfigure(1, weight=1)

        control_switches_frame = ttk.Frame(parent_frame)
        control_switches_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(6,0))

        bias_wrap = ttk.Frame(control_switches_frame)
        bias_wrap.pack(side=tk.LEFT, padx=(0, 20))
        ttk.Label(bias_wrap, text="포지션 기준:", style="TLabel").pack(side=tk.LEFT, padx=(0,6))
        def _on_position_switch_change(checked: bool):
            bias = "SHORT" if checked else "LONG"
            self.position_bias_var.set(bias)
            if self._config_update_callback:
                try:
                    self._config_update_callback({'POSITION_BIAS': bias})
                except Exception as e:
                    logging.error(f"POSITION_BIAS 콜백 오류: {e}")
        self._position_switch = IOSToggleSwitch(
            bias_wrap, 
            checked=True if self.position_bias_var.get() == 'SHORT' else False,
            command=_on_position_switch_change
        )
        self._position_switch.pack(side=tk.LEFT)
        ttk.Label(bias_wrap, textvariable=self.position_bias_var, style="Value.TLabel").pack(side=tk.LEFT, padx=6)

        mode_wrap = ttk.Frame(control_switches_frame)
        mode_wrap.pack(side=tk.LEFT)
        ttk.Label(mode_wrap, text="거래 모드:", style="TLabel").pack(side=tk.LEFT, padx=(0, 6))
        def _on_mode_switch_change(checked: bool):
            mode = "COIN-M" if checked else "USDT-M"
            self.trading_mode_var.set(mode)
            if self._config_update_callback:
                try:
                    self._config_update_callback({'DEFAULT_TRADING_MODE': mode})
                except Exception as e:
                    logging.error(f"거래 모드 콜백 오류: {e}")
        self._trading_mode_switch = IOSToggleSwitch(
            mode_wrap,
            checked=True if self.trading_mode_var.get() == 'COIN-M' else False,
            command=_on_mode_switch_change,
            on_color="#007AFF",
            off_color="#FF9500"
        )
        self._trading_mode_switch.pack(side=tk.LEFT)
        ttk.Label(mode_wrap, textvariable=self.trading_mode_var, style="Value.TLabel").pack(side=tk.LEFT, padx=6)

    def set_controls_for_run_state(self, is_running: bool):
        # (변경 없음)
        state = tk.DISABLED if is_running else tk.NORMAL
        if self._position_switch:
            if is_running:
                self._position_switch.canvas.unbind("<Button-1>")
            else:
                self._position_switch.canvas.bind("<Button-1>", self._position_switch._toggle)
        if self._trading_mode_switch:
             if is_running:
                self._trading_mode_switch.canvas.unbind("<Button-1>")
             else:
                self._trading_mode_switch.canvas.bind("<Button-1>", self._trading_mode_switch._toggle)

    def _rebuild_step_dependent_widgets(self):
        # (변경 없음)
        logging.info(f"GUI: steps가 변경되어 관련 프레임을 재구성합니다. (New steps: {self.steps})")
        
        if hasattr(self, 'entry_qty_frame'):
            self.entry_qty_frame.destroy()
        if hasattr(self, 'hedge_qty_frame'):
            self.hedge_qty_frame.destroy()
        if hasattr(self, 'exit_ratio_frame'):
            self.exit_ratio_frame.destroy()

        main_frame = self.root.winfo_children()[0]

        self.entry_qty_frame = ttk.LabelFrame(main_frame, text="진입 수량 (스텝 / 누적)", padding="10")
        self.entry_qty_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_quantity_widgets(self.entry_qty_frame, "step_qty_vars", "cumulative_qty_vars", "Qty.TLabel", "CumQty.TLabel")

        self.hedge_qty_frame = ttk.LabelFrame(main_frame, text="헷지 수량 (스텝 / 누적)", padding="10")
        self.hedge_qty_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_quantity_widgets(self.hedge_qty_frame, "step_hedge_qty_vars", "cumulative_hedge_qty_vars", "HedgeQty.TLabel", "CumHedgeQty.TLabel")

        self.exit_ratio_frame = ttk.LabelFrame(main_frame, text="Exit 비율 (스텝별)", padding="10")
        self.exit_ratio_frame.grid(row=0, column=3, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        self._create_ratio_widgets(self.exit_ratio_frame)

    def set_button_to_stop_mode(self):
        # (변경 없음)
        self.root.after(0, lambda: self.toggle_button.config(text="정지"))
        self.set_controls_for_run_state(True)
        style = ttk.Style(); style.configure("Toggle.TButton", foreground='red', font=('Helvetica', 10, 'bold'))
        if hasattr(self, 'settings_button'):
            pass
        
    def set_button_to_stop_reserved_mode(self):
        # (변경 없음)
        self._stop_is_reserved = True
        self.root.after(0, lambda: self.toggle_button.config(text="정지 예약 취소", state=tk.NORMAL))
        style = ttk.Style()
        style.configure("Toggle.TButton", foreground='orange', font=('Helvetica', 10, 'bold'))

    def update_signal_status(self, status_text):
        # (변경 없음)
        self._safe_update(self.signal_status_var, status_text)

    def _safe_update(self, var, value):
        # (변경 없음)
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.after(0, lambda: var.set(str(value)))

    def set_config_update_callback(self, command):
        # (변경 없음)
        self._config_update_callback = command

    def set_recalculate_callback(self, command):
        # (변경 없음)
        self._recalculate_callback = command

    def load_current_configs(self, config_dict: dict):
        # (변경 없음)
        self.current_config = config_dict
        logging.info("GUI가 현재 설정 값을 로드했습니다.")
        try:
            bias = (self.current_config or {}).get('POSITION_BIAS', 'LONG')
            self.position_bias_var.set(str(bias).upper())
            if self._position_switch:
                self._position_switch.set(True if str(bias).upper()=='SHORT' else False)
        except Exception as e:
            logging.error(f'POSITION_BIAS 초기화 오류: {e}')

    def _read_config_from_file(self, settings_structure):
        # (이 함수는 현재 메인 로직에서 사용되지 않음, 변경 없음)
        config_values = {}
        all_keys = {param[0] for params in settings_structure.values() for param in params}
        
        try:
            with open('settings.ini', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#') or line.startswith('['):
                        continue
                    
                    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.*)', line)
                    if match:
                        key = match.group(1).strip().upper()
                        value_str = match.group(2).strip().split('#')[0].strip()
                        
                        if key in all_keys:
                            try:
                                config_values[key] = eval(value_str)
                            except:
                                config_values[key] = value_str.strip("'\"")
        except Exception as e:
            logging.error(f"settings.ini 파일 읽기 오류: {e}")
            messagebox.showerror("오류", f"settings.ini 파일을 읽는 중 오류가 발생했습니다:\n{e}")
        return config_values

    def _write_config_to_file(self, new_configs, settings_structure):
        # (이 함수는 현재 메인 로직에서 사용되지 않음, 변경 없음)
        try:
            lines = []
            with open('settings.ini', 'r', encoding='utf-8') as f:
                lines = f.readlines()

            with open('settings.ini', 'w', encoding='utf-8') as f:
                for line in lines:
                    stripped_line = line.strip()
                    if not stripped_line or stripped_line.startswith('#') or stripped_line.startswith('['):
                        f.write(line)
                        continue
                    
                    match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=', stripped_line)
                    if match:
                        key = match.group(1).strip().upper()
                        if key in new_configs:
                            new_value = new_configs[key]
                            
                            param_info = next((p for params in settings_structure.values() for p in params if p[0] == key), None)
                            original_key = param_info[1] if param_info else key.lower()

                            if isinstance(new_value, str):
                                new_line = f"{original_key} = \"{new_value}\"\n"
                            else:
                                new_line = f"{original_key} = {new_value}\n"
                            f.write(new_line)
                        else:
                            f.write(line)
                    else:
                        f.write(line)
            return True
        except Exception as e:
            logging.error(f"settings.ini 파일 쓰기 오류: {e}")
            messagebox.showerror("오류", f"settings.ini 파일에 쓰는 중 오류가 발생했습니다:\n{e}")
            return False

    def open_settings_window(self):
        # (settings_structure가 변경되었으므로, 이 함수는 자동으로 새 구조를 반영함. 코드 변경 없음)
        settings_win = tk.Toplevel(self.root)
        settings_win.title("설정 변경")
        settings_win.geometry("950x650")

        settings_structure = self.settings_structure
        
        notebook = ttk.Notebook(settings_win)
        notebook.pack(expand=True, fill='both', padx=10, pady=10)
        entries = {}

        for tab_name, params in settings_structure.items():
            tab_frame = ttk.Frame(notebook, padding="10")
            notebook.add(tab_frame, text=tab_name)

            for i, (key, original_key, _type) in enumerate(params):
                ttk.Label(tab_frame, text=f"{original_key}:").grid(row=i, column=0, padx=5, pady=3, sticky=tk.W)
                
                entry_width = 40 if any(x in original_key.lower() for x in ['key', 'secret', 'url']) else 20
                entry = ttk.Entry(tab_frame, width=entry_width)
                entry.grid(row=i, column=1, padx=5, pady=3, sticky=tk.W)
                
                current_val = self.current_config.get(key, "")
                
                entry.insert(0, str(current_val))
                entries[key] = entry

        button_frame = ttk.Frame(settings_win)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))

        def apply_changes():
            new_configs = {}
            original_configs = self.current_config.copy()
            try:
                for key, entry_widget in entries.items():
                    value_str = entry_widget.get()
                    param_info = next((p for cat in settings_structure.values() for p in cat if p[0] == key), None)
                    
                    if param_info:
                        _type = param_info[2]
                        
                        new_val = None
                        if _type == bool:
                            new_val = value_str.lower() in ['true', '1', 't', 'y', 'yes']
                        elif _type in [int, float]:
                            try:
                                new_val = _type(value_str)
                            except ValueError:
                                messagebox.showerror("입력 오류", f"'{param_info[1]}' 필드에 유효한 숫자를 입력해야 합니다.")
                                return
                        else:
                            new_val = str(value_str)
                        
                        new_configs[key] = new_val
                
                new_steps = new_configs.get('STEPS')
                if new_steps is not None and new_steps != self.steps:
                    self.steps = new_steps
                    self._rebuild_step_dependent_widgets()
                
                if self._config_update_callback:
                    self._config_update_callback(new_configs)

                is_changed = any(original_configs.get(key) != value for key, value in new_configs.items())
                
                if is_changed and self._is_running:
                    self.pending_config_label.grid()
                    logging.info("설정 변경 감지. 다음 사이클부터 적용됩니다.")
                
                messagebox.showinfo("성공", "설정이 적용되었습니다")
                settings_win.destroy()

            except Exception as e:
                messagebox.showerror("오류", f"설정 적용 중 오류 발생:\n{e}")

        apply_button = ttk.Button(button_frame, text="적용 및 저장", command=apply_changes)
        apply_button.pack(side=tk.LEFT, expand=True, padx=5)
        
        close_button = ttk.Button(button_frame, text="닫기", command=settings_win.destroy)
        close_button.pack(side=tk.LEFT, expand=True, padx=5)

    def set_toggle_command(self, command): self._toggle_command = command
    def set_on_closing(self, command): self._on_closing_callback = command
    def toggle_bot_command(self):
        # (변경 없음)
        if self._toggle_command:
            if not self._is_running:
                self._is_running = True
                self.set_button_to_stop_mode()
                self._toggle_command("start")
            elif self._stop_is_reserved:
                self._toggle_command("cancel_stop")
            else:
                self._toggle_command("stop")

    def set_button_to_start_mode(self):
        # (변경 없음)
        self._is_running = False
        self._stop_is_reserved = False
        self.set_controls_for_run_state(False)
        
        self.root.after(0, lambda: self.toggle_button.config(text="시작", state=tk.NORMAL))
        style = ttk.Style(); style.configure("Toggle.TButton", foreground='green', font=('Helvetica', 10, 'bold'))
        
        if hasattr(self, 'settings_button'):
            self.settings_button.config(state=tk.NORMAL)

    def _safe_update(self, var, value):
        # (변경 없음)
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.after(0, lambda: var.set(str(value)))

    def reset_to_initial_state(self):
        if hasattr(self, 'pending_config_label'): self.pending_config_label.grid_remove()
        self._safe_update(self.leverage_var, "로딩 중...")
        self._safe_update(self.symbol_info_var, "로딩 중...")
        self._safe_update(self.min_qty_var, "N/A")
        self._safe_update(self.balance_var, "로딩 중...")
        # === [수정] ws_connection_var로 변경 ===
        self._safe_update(self.ws_connection_var, "대기 중...")
        # === [수정 끝] ===
        self._safe_update(self.current_step_var, "대기")
        self._safe_update(self.kline_status_var, "대기 중...")
        self._safe_update(self.trade_status_var, "대기 중...")
        self._safe_update(self.user_status_var, "대기 중...")
        self._safe_update(self.long_size_var, "-"); self._safe_update(self.long_entry_var, "-"); self._safe_update(self.long_pnl_var, "-")
        self._safe_update(self.short_size_var, "-"); self._safe_update(self.short_entry_var, "-"); self._safe_update(self.short_pnl_var, "-")
        self._safe_update(self.nsz_range_var, "-")
        for i in range(self.steps):
            if hasattr(self, 'step_qty_vars') and i < len(self.step_qty_vars): self._safe_update(self.step_qty_vars[i], "계산 전")
            if hasattr(self, 'cumulative_qty_vars') and i < len(self.cumulative_qty_vars): self._safe_update(self.cumulative_qty_vars[i], "계산 전")
            if hasattr(self, 'step_hedge_qty_vars') and i < len(self.step_hedge_qty_vars): self._safe_update(self.step_hedge_qty_vars[i], "계산 전")
            if hasattr(self, 'cumulative_hedge_qty_vars') and i < len(self.cumulative_hedge_qty_vars): self._safe_update(self.cumulative_hedge_qty_vars[i], "계산 전")
            if hasattr(self, 'exit_ratio_vars') and i < len(self.exit_ratio_vars): self._safe_update(self.exit_ratio_vars[i], "계산 전")
        if hasattr(self, 'orders_tree'):
            for item in self.orders_tree.get_children():
                try: self.orders_tree.delete(item)
                except tk.TclError: pass

    # (단순 업데이트 함수들, 변경 없음)
    def update_leverage(self, leverage_text): self._safe_update(self.leverage_var, leverage_text)
    def update_symbol_info(self, info_text): self._safe_update(self.symbol_info_var, info_text)
    def update_min_qty(self, qty_text): self._safe_update(self.min_qty_var, qty_text)
    def update_balance(self, balance_text): self._safe_update(self.balance_var, balance_text)
    def update_status(self, status_text): self._safe_update(self.status_var, status_text)
    
    # === [수정] 함수 이름 변경 ===
    def update_ws_connection_status(self, status_text): self._safe_update(self.ws_connection_var, status_text)
    # === [수정 끝] ===
    
    def update_current_step(self, step_index): self._safe_update(self.current_step_var, str(step_index))
    def update_kline_status(self, status): self._safe_update(self.kline_status_var, status)
    def update_kline_data(self, data): self._safe_update(self.kline_data_var, data)
    def update_trade_status(self, status): self._safe_update(self.trade_status_var, status)
    def update_trade_data(self, price_data): self._safe_update(self.large_price_var, price_data)
    def update_user_status(self, status): self._safe_update(self.user_status_var, status)
    
    # (수량/비율 리스트 업데이트 함수, 변경 없음)
    def update_entry_lists(self, step_list, cumulative_list, precision):
        for i in range(self.steps):
            step_val = f"{step_list[i]:.{precision}f}" if i < len(step_list) and isinstance(step_list[i], (int, float)) else "-"
            cum_val = f"{cumulative_list[i]:.{precision}f}" if i < len(cumulative_list) and isinstance(cumulative_list[i], (int, float)) else "-"
            if hasattr(self, 'step_qty_vars') and i < len(self.step_qty_vars): self._safe_update(self.step_qty_vars[i], step_val)
            if hasattr(self, 'cumulative_qty_vars') and i < len(self.cumulative_qty_vars): self._safe_update(self.cumulative_qty_vars[i], cum_val)
    def update_hedge_lists(self, step_list, cumulative_list, precision):
        for i in range(self.steps):
            step_val = f"{step_list[i]:.{precision}f}" if i < len(step_list) and isinstance(step_list[i], (int, float)) else "-"
            cum_val = f"{cumulative_list[i]:.{precision}f}" if i < len(cumulative_list) and isinstance(cumulative_list[i], (int, float)) else "-"
            if hasattr(self, 'step_hedge_qty_vars') and i < len(self.step_hedge_qty_vars): self._safe_update(self.step_hedge_qty_vars[i], step_val)
            if hasattr(self, 'cumulative_hedge_qty_vars') and i < len(self.cumulative_hedge_qty_vars): self._safe_update(self.cumulative_hedge_qty_vars[i], cum_val)
    def update_exit_ratio_list(self, ratio_list):
        for i in range(self.steps):
            val = f"{ratio_list[i]:.5f}" if i < len(ratio_list) and isinstance(ratio_list[i], (int, float)) else "-"
            if hasattr(self, 'exit_ratio_vars') and i < len(self.exit_ratio_vars): self._safe_update(self.exit_ratio_vars[i], val)
    def update_total_pnl(self, realized_pnl):
        # (변경 없음)
        try:
            pnl_value = float(realized_pnl)
            self.cumulative_pnl += pnl_value
            self._safe_update(self.total_pnl_var, f"{self.cumulative_pnl:.4f}")
            logging.info(f"실현 손익 업데이트: {pnl_value:.4f}, 누적: {self.cumulative_pnl:.4f}")
        except Exception as e:
            logging.error(f"PNL 업데이트 중 오류: {e}")

    # === [수정] Bybit V5 API 응답에 맞게 파싱 ===
    def update_position_display(self, positions, target_symbol):
        """Bybit V5 API의 포지션 목록(REST 또는 WS)을 파싱하여 GUI를 업데이트합니다."""
        long_pos_data = None
        short_pos_data = None
        
        # Bybit V5: positions는 포지션 객체의 리스트
        for pos in positions:
            symbol = pos.get('symbol')
            if symbol == target_symbol:
                side = pos.get('side') # 'Buy', 'Sell', 또는 'None'
                if side == 'Buy':
                    long_pos_data = pos
                elif side == 'Sell':
                    short_pos_data = pos
        
        # --- LONG 포지션 업데이트 ---
        if long_pos_data:
            size_str = long_pos_data.get('size', '0')
            try: size = float(size_str)
            except (ValueError, TypeError): size = 0.0
            
            if size != 0:
                self._safe_update(self.long_size_var, size_str)
                self._safe_update(self.long_entry_var, long_pos_data.get('avgPrice', '-'))
                self._safe_update(self.long_pnl_var, f"{float(long_pos_data.get('unrealisedPnl', '0.0')):.4f}")
            else:
                self._safe_update(self.long_size_var, "0")
                self._safe_update(self.long_entry_var, "-")
                self._safe_update(self.long_pnl_var, "0.00")
        else: # LONG 포지션 데이터가 없는 경우
            self._safe_update(self.long_size_var, "0")
            self._safe_update(self.long_entry_var, "-")
            self._safe_update(self.long_pnl_var, "0.00")

        # --- SHORT 포지션 업데이트 ---
        if short_pos_data:
            size_str = short_pos_data.get('size', '0')
            try: size = float(size_str)
            except (ValueError, TypeError): size = 0.0

            if size != 0:
                # Bybit는 SHORT 수량을 양수로 반환하므로, 표시를 위해 음수 기호 추가
                self._safe_update(self.short_size_var, f"-{size_str}") 
                self._safe_update(self.short_entry_var, short_pos_data.get('avgPrice', '-'))
                self._safe_update(self.short_pnl_var, f"{float(short_pos_data.get('unrealisedPnl', '0.0')):.4f}")
            else:
                self._safe_update(self.short_size_var, "0")
                self._safe_update(self.short_entry_var, "-")
                self._safe_update(self.short_pnl_var, "0.00")
        else: # SHORT 포지션 데이터가 없는 경우
            self._safe_update(self.short_size_var, "0")
            self._safe_update(self.short_entry_var, "-")
            self._safe_update(self.short_pnl_var, "0.00")
    # === [수정 끝] ===

    def update_nsz_range(self, nsz_text): self._safe_update(self.nsz_range_var, nsz_text)
    def update_exit_target_price(self, price_text: str): self._safe_update(self.exit_target_price_var, price_text)
    
    def update_open_orders_display(self, open_orders_list, order_type_map):
        if hasattr(self, 'orders_tree'):
            try: self.root.after(0, self._update_treeview, open_orders_list, order_type_map)
            except Exception as e: logging.error(f"Treeview 업데이트 예약 중 오류: {e}")

    # === [수정] Bybit V5 API 응답에 맞게 파싱 ===
    def _update_treeview(self, open_orders_list, order_type_map):
        if not hasattr(self, 'orders_tree'): return
        try:
            for item in self.orders_tree.get_children(): self.orders_tree.delete(item)
            # open_orders_list가 [None] 같은 비정상적인 빈 값을 가질 경우 처리
            if not open_orders_list or not isinstance(open_orders_list, list) or (len(open_orders_list) > 0 and not open_orders_list[0]):
                return

            # 정렬을 위한 가격 추출 함수 (Bybit-compatible)
            def get_price_for_sort(order):
                try:
                    # Bybit V5: 조건부 주문은 'triggerPrice', 지정가 주문은 'price'
                    price_str = order.get('triggerPrice', '0')
                    # triggerPrice가 0이거나 없으면(지정가), price 필드를 사용
                    if not price_str or float(price_str) == 0:
                        price_str = order.get('price', '0')
                    
                    return float(price_str)
                except (ValueError, TypeError):
                    return 0.0

            sorted_orders = sorted(open_orders_list, key=get_price_for_sort, reverse=True)
            
            for order in sorted_orders:
                # Bybit V5 키: 'orderId'
                order_id = str(order.get('orderId', ''))
                custom_type = order_type_map.get(order_id, '?')
                
                # Bybit V5 키: 'side' (Buy/Sell), 'orderType' (Limit/Market/etc)
                side = order.get('side', '?')
                o_type = order.get('orderType', '?')
                
                # Bybit V5 키: 'qty'
                qty = order.get('qty', '')
                
                # 표시 가격 결정 로직 (get_price_for_sort와 동일)
                display_price = get_price_for_sort(order)
                
                # Bybit TSM 주문의 경우 'trailingStop' (거리) 표시
                if o_type == 'Market' and order.get('trailingStop'):
                    o_type = "TSM"
                    display_price = order.get('trailingStop') # 가격 대신 거리 표시
                # Bybit 조건부 주문(Stop Market 등)
                elif o_type == 'Market' and order.get('triggerPrice'):
                     o_type = "StopMarket"
                     
                self.orders_tree.insert('', tk.END, values=(custom_type, order_id, side, o_type, qty, f"{display_price:.4f}"))
                
        except Exception as e: 
            logging.error(f"_update_treeview 실행 중 오류: {e}", exc_info=True)
    # === [수정 끝] ===
            
    def on_closing(self):
        # (변경 없음)
        logging.info("GUI 창 닫기 요청됨.")
        if self._on_closing_callback: self._on_closing_callback()
        if hasattr(self, 'root') and self.root: self.root.after(100, self.root.destroy)
        
    def show_error_popup(self, title, message):
        # (변경 없음)
        if hasattr(self, 'root') and self.root and self.root.winfo_exists():
            self.root.after(0, lambda: messagebox.showerror(title, message))
            
    def set_position_bias(self, bias: str):
        # (변경 없음)
        bias = (bias or "LONG").upper()
        self.position_bias_var.set(bias)
        if getattr(self, "_position_switch", None):
            self._position_switch.set(True if bias == "SHORT" else False)