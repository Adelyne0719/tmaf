import tkinter as tk
from tkinter import ttk
import queue
import threading
import datetime
import logging
from config import *

# 전역 큐들 (gui.py 내부에서 사용)
message_queue = queue.Queue()    # Candle close 메시지
price_queue = queue.Queue()      # Real-time Price 메시지
position_queue = queue.Queue()   # 포지션 정보 메시지
exit_order_queue = queue.Queue() # Exit 주문 정보 메시지

class DarkModeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-time Monitor")
        self.root.configure(bg="#2e2e2e")
        
        # 다크 테마 적용: Treeview 스타일 설정
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Treeview",
                        background="#3e3e3e",
                        foreground="white",
                        fieldbackground="#3e3e3e",
                        font=("Helvetica", 10))
        style.configure("Treeview.Heading",
                        background="#2e2e2e",
                        foreground="white",
                        font=("Helvetica", 12, "bold"))
        style.map("Treeview", background=[('selected', '#6A6A6A')])
        
        # 섹션 0: 계좌 정보 (Balance와 Profit Rate) - 포지션 정보 위에 표시
        account_frame = tk.Frame(root, bg="#2e2e2e")
        account_frame.pack(padx=10, pady=5, fill="x")
        self.balance_var = tk.StringVar(value="Balance: -")
        self.profit_var = tk.StringVar(value="Profit Rate: -")
        tk.Label(account_frame, textvariable=self.balance_var, font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(side="left", padx=10)
        tk.Label(account_frame, textvariable=self.profit_var, font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(side="left", padx=10)
        
        # 섹션 1: Candle 정보
        candle_frame = tk.Frame(root, bg="#2e2e2e")
        candle_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(candle_frame, text="Bot Infomation:", font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(side="left")
        self.candle_var = tk.StringVar(value="-")
        self.candle_label = tk.Label(candle_frame, textvariable=self.candle_var, font=("Helvetica", 16), bg="#2e2e2e", fg="#00ffff")
        self.candle_label.pack(side="left", padx=10)
        
        # 섹션 2: 실시간 가격
        price_frame = tk.Frame(root, bg="#2e2e2e")
        price_frame.pack(padx=10, pady=5, fill="x")
        tk.Label(price_frame, text="Real-time Price:", font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(side="left")
        self.price_var = tk.StringVar(value="-")
        self.price_label = tk.Label(price_frame, textvariable=self.price_var, font=("Helvetica", 16), bg="#2e2e2e", fg="#00ff00")
        self.price_label.pack(side="left", padx=10)
        
        # 추가: 현재 stage / 최대 stage를 표시할 섹션
        stage_frame = tk.Frame(root, bg="#2e2e2e")
        stage_frame.pack(padx=10, pady=5, fill="x")
        self.stage_var = tk.StringVar(value="Stage: - / -")
        tk.Label(stage_frame, textvariable=self.stage_var, font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(side="left", padx=10)
        
        # 섹션 3: 포지션 정보 테이블
        pos_frame = tk.Frame(root, bg="#2e2e2e")
        pos_frame.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(pos_frame, text="Position Info:", font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(anchor="w")
        pos_columns = ("Symbol", "Size", "Entry Price", "Liq.Price", "Margin", "PNL(ROI%)")
        self.tree = ttk.Treeview(pos_frame, columns=pos_columns, show="headings", height=8)
        for col in pos_columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.tree.tag_configure("oddrow", background="#3e3e3e", foreground="white")
        self.tree.tag_configure("evenrow", background="#4e4e4e", foreground="white")
        
        # 섹션 4: Exit 주문 테이블
        exit_frame = tk.Frame(root, bg="#2e2e2e")
        exit_frame.pack(padx=10, pady=5, fill="both", expand=True)
        tk.Label(exit_frame, text="Exit Orders:", font=("Helvetica", 14), bg="#2e2e2e", fg="white").pack(anchor="w")
        exit_columns = ("Symbol" , "Size", "Exit Price", "Status", "OrderID", "UpdateTime")
        self.exit_tree = ttk.Treeview(exit_frame, columns=exit_columns, show="headings", height=5)
        for col in exit_columns:
            self.exit_tree.heading(col, text=col)
            self.exit_tree.column(col, anchor="center")
        self.exit_tree.pack(fill="both", expand=True)
        
        # 섹션 5: Start/Stop 토글 버튼
        self.trading_running = False
        self.start_stop_button = tk.Button(root, text="Start", font=("Helvetica", 12), command=self.toggle_trading)
        self.start_stop_button.pack(pady=10)
        
        # 최신 exit 주문 정보를 저장할 변수 (누적하지 않고 최신 정보만)
        self.latest_exit_order = None
        
        self.poll_queues()
    
    def poll_queues(self):
        # Candle 메시지 업데이트
        try:
            while True:
                latest_candle = message_queue.get_nowait()
                self.candle_var.set(latest_candle.strip())
        except queue.Empty:
            pass
        
        # 실시간 가격 업데이트
        try:
            while True:
                latest_price = price_queue.get_nowait()
                self.price_var.set(latest_price.strip())
        except queue.Empty:
            pass
        
        # 추가: 현재 stage/최대 stage 업데이트
        try:
            from main import trading_bot_instance
            if trading_bot_instance:
                current_stage = len(trading_bot_instance.position)
                max_stage = ENTRY_STEPS
                self.stage_var.set(f"Stage: {current_stage} / {max_stage}")
        except Exception as e:
            logging.error("Error updating stage info: %s", e)
            
        # 포지션 정보 업데이트
        try:
            while True:
                latest_pos = position_queue.get_nowait()
                self.update_position_table(latest_pos)
        except queue.Empty:
            pass
        
        # Balance와 Profit Rate 업데이트: TradingBot 인스턴스에서 정보 갱신
        try:
            from main import trading_bot_instance
            if trading_bot_instance and hasattr(trading_bot_instance, "balance") and hasattr(trading_bot_instance, "initial_balance"):
                current_balance = trading_bot_instance.balance
                initial_balance = trading_bot_instance.initial_balance
                profit_rate = ((current_balance - initial_balance) / initial_balance * 100) if initial_balance else 0
                self.balance_var.set(f"Balance: {current_balance:.2f} USDT")
                self.profit_var.set(f"Profit Rate: {profit_rate:.2f}%")
        except Exception as e:
            logging.error("Error updating balance/profit info: %s", e)
        
        # Exit 주문 정보 업데이트: exit_order_queue에서 새 데이터가 있으면 최신 데이터만 저장
        new_exit_order = None
        try:
            while True:
                order_info = exit_order_queue.get_nowait()
                new_exit_order = order_info  # 새 데이터가 들어오면 최신 데이터로 갱신
        except queue.Empty:
            pass
        
        if new_exit_order is not None:
            self.latest_exit_order = new_exit_order
        
        # Treeview 업데이트: 최신 exit 주문 정보 표시
        for row in self.exit_tree.get_children():
            self.exit_tree.delete(row)
        if self.latest_exit_order is not None:
            update_time = self.latest_exit_order.get("UpdateTime", "")
            update_time_formatted = ""
            if update_time:
                try:
                    timestamp = float(update_time) / 1000.0
                    update_time_formatted = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    logging.error("Error formatting update time: %s", e)
                    update_time_formatted = str(update_time)
            self.exit_tree.insert("", "end", values=(
                self.latest_exit_order.get("Symbol", ""),
                self.latest_exit_order.get("Size", ""),
                self.latest_exit_order.get("Price", ""),
                self.latest_exit_order.get("Status", ""),
                self.latest_exit_order.get("OrderID", ""),
                update_time_formatted
            ))
        
        self.root.after(1000, self.poll_queues)
    
    def update_position_table(self, data_str):
        lines = data_str.strip().split("\n")
        if not lines:
            return
        for row in self.tree.get_children():
            self.tree.delete(row)
        for i, line in enumerate(lines[1:]):
            if not line.strip():
                continue
            cells = [cell.strip() for cell in line.split("|")]
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=cells, tags=(tag,))
    
    def toggle_trading(self):
        if not self.trading_running:
            self.trading_running = True
            self.start_stop_button.config(text="Stop")
            from main import start_trading_bot
            trading_thread = threading.Thread(target=start_trading_bot, daemon=True)
            trading_thread.start()
            message_queue.put("Trading Bot Started.")
        else:
            self.trading_running = False
            self.start_stop_button.config(text="Start")
            from main import stop_trading_bot
            stop_trading_bot()
            message_queue.put("Trading Bot Stopped.")

def start_gui():
    root = tk.Tk()
    app = DarkModeGUI(root)
    root.mainloop()

def run_gui(dev_mode):
    if dev_mode:
        start_gui()
    else:
        print("Development mode is False, GUI not running.")
