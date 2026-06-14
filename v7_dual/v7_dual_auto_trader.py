import time
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal
import v7_dual_trading_utils as trading_utils

class AutoTradeWorker(QObject):
    """
    DCA (Dollar Cost Averaging) + 헷지 전략을 처리하는 워커입니다.
    Step 0 체결 후 → Step 1 지정가 주문 생성 → Step 1 체결 후 → Step 2 ...
    """

    # GUI의 상태 라벨을 업데이트하기 위한 시그널
    log_message = pyqtSignal(str)

    # GUI에 시장가 주문을 요청하기 위한 시그널 (symbol, side, quantity, is_hedge)
    execute_trade_signal = pyqtSignal(str, str, str, bool)

    # GUI에 지정가 주문을 요청하기 위한 새 시그널 (symbol, side, quantity, price, is_hedge)
    execute_limit_order_signal = pyqtSignal(str, str, str, str, bool)

    # 헷지 트리거 업데이트 시그널 (hedge_triggers, side_mode, current_step)
    hedge_triggers_updated = pyqtSignal(list, str, int)

    # DCA 상태 저장 요청 시그널
    request_save_state = pyqtSignal()

    # 주문 ID 응답 수신 시그널 (order_id)
    order_id_received = pyqtSignal(str)

    # 헷지 주문 ID 응답 수신 시그널 (order_id, trigger_price, quantity)
    hedge_order_id_received = pyqtSignal(str, float, float)

    # 주문 가격 조정 요청 시그널 (order_id, new_price)
    adjust_order_price = pyqtSignal(str, str)

    # 상승 중 추가진입: 지정가 주문 취소 후 시장가 진입 요청 시그널 (order_id)
    uptrend_entry_request = pyqtSignal(str)

    # 익절: 전체 청산 및 자동매매 재시작 요청 시그널
    profit_taking_request = pyqtSignal()

    # 익절 트리거 업데이트 시그널 (profit_target_price, current_step)
    profit_target_updated = pyqtSignal(float, int)

    # 상승 중 추가진입 임계값 업데이트 시그널 (uptrend_threshold_price)
    uptrend_threshold_updated = pyqtSignal(float)

    # 상승 중 추가진입 2차 임계값 업데이트 시그널 (uptrend_threshold_price_2)
    uptrend_threshold_2_updated = pyqtSignal(float)

    # 최종 단계 손실 방지: Stop Loss 주문 요청 시그널 (symbol, side, quantity, price)
    request_stop_loss = pyqtSignal(str, str, str, str)

    # 최종 단계 손실 방지: Trailing Stop 주문 요청 시그널 (symbol, side, quantity, activation_price, callback_rate)
    request_trailing_stop = pyqtSignal(str, str, str, str, str)

    # 헷지 슬리피지 업데이트 시그널 (trigger_index, slippage)
    hedge_slippage_updated = pyqtSignal(int, float)

    # 다음 단계 진입 주문 가격 조정 시그널 (order_id, slippage)
    adjust_next_step_order_signal = pyqtSignal(str, float)

    # 역방향진입 시 헷지 포지션 부분 청산 시그널 (symbol, side, quantity)
    reduce_hedge_signal = pyqtSignal(str, str, str)

    # Step 변경 시그널 (이전 step 번호) - Insight 히스토리 저장용
    step_completed = pyqtSignal(int)

    # 헷지 청산가 경고 시그널 (hedge_liq_price, emergency_exit_line, warning_level)
    hedge_liquidation_warning = pyqtSignal(float, float, str)

    # 헷지 긴급 탈출 라인 업데이트 시그널 (emergency_exit_line)
    emergency_exit_line_updated = pyqtSignal(float)

    # 사이클 완료 시그널 (realized_pnl)
    cycle_completed = pyqtSignal(float)

    # 헷지 프로토콜 발동 시그널 (step 번호, 추정 손익) - Statistics 탭용
    hedge_protocol_fired = pyqtSignal(int, float)

    # M 주문 업데이트 시그널 (m_orders_data: list of dict)
    m_orders_updated = pyqtSignal(list)

    def __init__(self, side='long', parent=None):
        """
        v7_dual: side 파라미터 추가
        Args:
            side: 'long' 또는 'short' (패널 구분자)
        """
        super().__init__(parent)
        self.is_running = False
        self.symbol = "BTCUSDT"
        self.assigned_side = side  # v7_dual: 패널 구분자 저장
        self.side_mode = "LONG" if side == 'long' else "SHORT"  # v7_dual: side에 따라 자동 설정
        self._lp = "[L]" if side == 'long' else "[S]"  # log prefix
        self._el = "상승진입" if side == 'long' else "하강진입"  # entry label (LONG=상승진입, SHORT=하강진입)

        # DCA 전략 상태
        self.current_step = 0
        self.total_steps = 10
        self.initial_entry_done = False
        self.next_step_orders_placed = False

        # 다음 단계 진입 주문 ID 및 가격 저장
        self.next_step_order_id = None
        self.last_step_entry_price = None  # 마지막 단계 진입 주문 가격 (다음 단계 가격 계산 기준)
        self.m_orders_data = []  # NSO 주문 데이터 (슬리피지 조정 시 마커 업데이트용)


        # 가격 정밀도 (기본값, start_trading에서 심볼별로 설정됨)
        self.price_precision = 4

        # 헷지 가격 조건부 주문 상태 (가격별로 실행 여부 추적)
        self.hedge_trigger_prices = []  # [(price, quantity, executed), ...]
        self.remaining_hedge_qty = 0
        self.previous_cumulative_hedge_qty = 0  # 이전 Step까지의 누적 헷지 수량

        # 헷지 주문 추적 (슬리피지 계산용)
        self.pending_hedge_orders = {}  # {order_id: (trigger_price, quantity)}

        # 헷지 주문 체결 후 임계값 재계산 플래그
        self.hedge_filled_need_threshold_recalc = False
        
        # 다음 단계 주문 체결 후 임계값 재계산 플래그
        self.step_filled_need_threshold_recalc = False

        # Break Even 없이 임계값 계산된 경우 재계산 필요 플래그
        self.threshold_needs_break_even_update = False

        # 상승 중 추가진입을 위한 캔들 데이터 저장 (최근 3개)
        self.prev_prev_candle = None  # 전전봉 (완성된 이전의 이전 봉)
        self.prev_candle = None  # 전봉 (완성된 이전 봉)
        self.current_candle = None  # 현재봉 (진행 중인 봉)
        self.last_candle_check_time = 0  # 마지막 봉 체크 시간 (봉 마감 시에만 조건 체크)

        # 익절 관련 상태
        self.profit_target_ratios = []  # 단계별 익절 비율 리스트 [60.0, 42.0, 29.4, ...]
        self.profit_target_price = None  # 현재 익절 트리거 가격
        self.profit_base_price = None
        self.entry_price_at_step = None  # 역방향진입 시점의 실시간 가격 (익절가 계산용)
        self.is_uptrend_entry = False  # 역방향진입 플래그 (정상 DCA와 구분)
        self.uptrend_threshold_price = None  # 상승 중 추가진입 임계값 (1차)
        self.uptrend_threshold_price_2 = None  # 상승 중 추가진입 임계값 (2차 - 즉시 진입)
        self.uptrend_entry_in_progress = False  # 역방향진입 처리 중 플래그 (중복 emit 방지)
        self.uptrend_entry_count = 0  # 역방향진입 횟수 (헷지 청산 비율 결정용: 1차=1/3, 2차=1/2, 3차=전부)

        # 익절 가격 갱신용 고가/저가 추적
        self.high_price_since_entry = None  # 추가진입 이후 최고가
        self.low_price_since_entry = None   # 추가진입 이후 최저가
        self.last_profit_target_update_time = 0  # 마지막 익절가 갱신 시간 (0.5초마다 갱신)
        self.is_profit_taking_in_progress = False  # 익절 실행 중 플래그 (중복 실행 방지)
        self.profit_base_price = None  # 익절가 계산 기준 가격 (Break Even 또는 메인 평균가 중 안전한 값)
        self._profit_base_needs_recalc = False  # 포지션 데이터 부족으로 기준가 재계산 필요 플래그

        # 포지션 데이터 저장 (익절가 계산용 Break Even 계산에 필요)
        self.current_position_data = {}  # WebSocket으로부터 받은 최신 포지션 데이터
        
        # 현재가 저장 (헷지 청산 시 최소 금액 계산용)
        self.current_price = 0

        # 최종 단계 손실 방지 상태
        self.final_step_protection_placed = False  # Stop Loss 및 Trailing Stop 주문 완료 여부
        self.monitoring_final_step_closure = False  # 최종 단계 포지션 청산 모니터링 여부
        self.main_liquidation_handled = False  # 메인 포지션 강제 청산 감지 후 헷지 보호 완료 여부
        self.hedge_liquidation_handled = False  # 헷지 포지션 청산 감지 후 메인 보호 완료 여부
        self._last_final_step_protection_attempt = 0  # 최종 단계 보호 주문 마지막 시도 시각

        # 예약 종료 상태
        self.scheduled_stop = False  # 사이클 종료 후 자동매매 중지 예약

        # 헷지 청산가 보호 상태 (3단계 긴급 탈출 라인 시스템)
        self.hedge_liq_protection_enabled = False  # 헷지 청산가 보호 활성화 여부
        self.hedge_emergency_exit_lines = []  # 3단계 긴급 탈출 라인 [(line1, executed), (line2, executed), (line3, executed)]
        self.emergency_exit_triggered = False  # 최종 긴급 탈출 실행 여부

        # 헷지 청산가 안전망 주문 (긴급탈출라인이 없을 때 청산가 직전 주문)
        self.hedge_safety_order_id = None  # 헷지 청산가 안전망 주문 ID
        self.hedge_safety_order_price = None  # 헷지 청산가 안전망 주문 가격

        # 헷지 프로토콜 상태
        self.hedge_protocol_enabled = True  # 헷지 프로토콜 활성화 여부
        self.hedge_protocol_active = False  # 현재 단계에서 헷지 프로토콜 활성 상태 (H1 체결 후 활성, H4 체결 또는 익절 후 비활성)
        self.hedge_protocol_executed = False  # 현재 단계에서 헷지 프로토콜 실행 완료 여부 (단계당 1회만)
        self.hedge_protocol_lowest_price = None  # 헷지 프로토콜 활성 후 최저가
        self.hedge_protocol_hedge_avg_price = None  # 헷지 진입 평균가 (익절 트리거 계산용)
        self.hedge_protocol_retracement_percent = 50.0  # 되돌림 비율 (%)
        self.hedge_protocol_tp_ratio = 50.0  # 익절하는 헷지 수량 비율 (%)
        self.hedge_protocol_exited_qty = 0  # 익절로 탈출한 헷지 수량 (재진입 시 사용)
        self.hedge_protocol_waiting_for_be = False  # BE 안전 조건 대기 중 (로그 스팸 방지)
        self.hedge_protocol_pending_check = None  # WebSocket 포지션 업데이트 후 체크할 헷지 트리거 정보 (trigger_index, fill_price)
        self.main_liquidation_safety_margin = 0.5  # 메인 포지션 청산가 안전마진 (%)
        self.hedge_liquidation_safety_margin = 0.5  # 헷지 포지션 청산가 안전마진 (%)
        self.hedge_frontload_final_step = False  # 헷지 프론트로드 설정
        self.hedge_frontload_reentry_pending = False  # 프론트로드 최종단계 재진입 대기
        self.hedge_frontload_reentry_price = None  # 재진입 가격 (H4 가격)
        self.hedge_frontload_reentry_qty = 0  # 재진입 수량 (익절된 수량)

        self._log("AutoTradeWorker: DCA 전략 워커 생성됨.")

    def _log(self, *args, **kwargs):
        """[L]/[S] 프리픽스 로그 출력"""
        if args:
            print(f"{self._lp} {args[0]}", *args[1:], **kwargs)
        else:
            print(self._lp, **kwargs)

    @pyqtSlot()
    def start_trading(self, symbol, entry_quantity, side_mode, strategy_settings=None, current_step=0, total_steps=10,
                     entry_qty_list=None, hedge_qty_list=None, api_module=None, symbol_info=None, category="linear",
                     current_price=0):
        """자동매매 시작"""
        if self.is_running:
            return

        trading_utils.set_log_prefix(self._lp)
        self.is_running = True
        self.symbol = symbol
        self.side_mode = side_mode
        self.current_step = current_step
        self.total_steps = total_steps
        self.category = category
        self.current_price = current_price  # 현재 가격 저장

        # DCA 전략을 위한 데이터
        self.entry_qty_list = entry_qty_list if entry_qty_list else []
        self.hedge_qty_list = hedge_qty_list if hedge_qty_list else []
        self.api_module = api_module
        self.symbol_info = symbol_info if symbol_info else {}

        # 가격 정밀도 계산 (tickSize 기반)
        tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
        self.price_precision = trading_utils.count_decimal_places(tick_size)
        self._log(f"[DCA] 가격 정밀도: {self.price_precision}자리 (tickSize={tick_size})")

        # 전략 설정
        self.strategy_settings = strategy_settings if strategy_settings else {}
        self.test_mode = self.strategy_settings.get("TEST_QUANTITY_MODE", False)
        self.uptrend_entry_profit_threshold = self.strategy_settings.get("UPTREND_ENTRY_PROFIT_THRESHOLD", 1.0)

        self.uptrend_threshold_2_multiplier = self.strategy_settings.get("UPTREND_THRESHOLD_2_MULTIPLIER", 2.0)
        self.hedge_exponent = self.strategy_settings.get("HEDGE_EXPONENT", 3.0)  # 헷지 곡선 지수

        # 헷지 청산가 보호 설정 (3단계 긴급 탈출 라인)
        self.hedge_liq_protection_enabled = self.strategy_settings.get("HEDGE_LIQ_PROTECTION_ENABLED", True)
        self.hedge_emergency_start_ratio = self.strategy_settings.get("HEDGE_EMERGENCY_START_RATIO", 50.0) / 100.0  # % → 비율
        self._log(f"[헷지 보호] 3단계 긴급 탈출 라인 {'활성화' if self.hedge_liq_protection_enabled else '비활성화'}")
        self._log(f"[헷지 보호] 시작 지점: BE와 청산가 사이 {self.strategy_settings.get('HEDGE_EMERGENCY_START_RATIO', 50.0)}%")

        # 헷지 프로토콜 설정 (항상 활성화)
        self.hedge_protocol_enabled = True
        self.hedge_protocol_retracement_percent = self.strategy_settings.get("HEDGE_PROTOCOL_RETRACEMENT", 50.0)
        self.hedge_protocol_tp_ratio = self.strategy_settings.get("HEDGE_PROTOCOL_TAKE_PROFIT_RATIO", 50.0)
        self.main_liquidation_safety_margin = self.strategy_settings.get("MAIN_LIQUIDATION_SAFETY_MARGIN", 0.5)
        self.hedge_liquidation_safety_margin = self.strategy_settings.get("HEDGE_LIQUIDATION_SAFETY_MARGIN", 0.5)
        self.hedge_frontload_final_step = self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False)
        self._log(f"[헷지 프로토콜 설정] 되돌림: {self.hedge_protocol_retracement_percent}%, 익절: {self.hedge_protocol_tp_ratio}%")
        self._log(f"[청산가 안전마진] 메인: {self.main_liquidation_safety_margin}%, 헷지: {self.hedge_liquidation_safety_margin}%")
        if self.hedge_frontload_final_step:
            self._log(f"[헷지 프론트로드] 최종단계-1에서 헷지 종료% 도달 모드 활성화")

        # 익절 비율 리스트 생성 (설정값 사용)
        profit_start = self.strategy_settings.get("PROFIT_START_PERCENT", 60.0)  # 시작 익절 비율 (%)
        profit_end = self.strategy_settings.get("PROFIT_END_PERCENT", 30.0)      # 종료 익절 비율 (%)
        profit_ratio = self.strategy_settings.get("PROFIT_RATIO", 0.7)           # 공비
        self.profit_target_ratios = trading_utils.calculate_profit_target_ratios(
            profit_start, profit_end, total_steps, profit_ratio
        )
        self._log(f"[익절] 단계별 익절 비율: {self.profit_target_ratios}")

        # 복구 모드 확인: entry_quantity가 0이고 리스트가 있으면 복구 모드
        is_restore_mode = (entry_quantity == 0 and len(self.entry_qty_list) > current_step)

        # 상태 플래그 (복구 모드가 아닐 때만 초기화)
        if not is_restore_mode:
            self.initial_entry_done = False
            self.next_step_orders_placed = False
            self.uptrend_entry_in_progress = False  # 역방향진입 중복 방지 플래그 리셋
            self.uptrend_entry_count = 0  # 역방향진입 횟수 리셋 (헷지 청산 비율용)

            # 이전 사이클 잔여 상태 초기화 (워커 객체 재사용으로 인한 상태 잔존 방지)
            self.entry_price_at_step = None
            self.is_uptrend_entry = False
            self.profit_target_price = None
            self.profit_base_price = None
            self._profit_base_needs_recalc = False
            self.high_price_since_entry = None
            self.low_price_since_entry = None
            self.last_profit_target_update_time = 0
            self.uptrend_threshold_price = None
            self.uptrend_threshold_price_2 = None
            self.hedge_trigger_prices = []
            self.remaining_hedge_qty = 0
            self.next_step_order_id = None
            self.last_step_entry_price = None
            self.step_filled_need_threshold_recalc = False
            self.threshold_needs_break_even_update = False
            self.hedge_filled_need_threshold_recalc = False
            # 헷지 프로토콜 상태 초기화
            self.hedge_protocol_active = False
            self.hedge_protocol_executed = False
            self.hedge_protocol_lowest_price = None
            self.hedge_protocol_hedge_avg_price = None
            self.hedge_protocol_exited_qty = 0
            self.hedge_protocol_waiting_for_be = False
            self.hedge_protocol_pending_check = None
            # 최종 단계 보호 상태 초기화
            self.final_step_protection_placed = False
            self.monitoring_final_step_closure = False
            self.main_liquidation_handled = False
            self.hedge_liquidation_handled = False
            self._last_final_step_protection_attempt = 0
            # 헷지 청산가 보호 상태 초기화
            self.hedge_emergency_exit_lines = []
            self.emergency_exit_triggered = False
            self.hedge_safety_order_id = None
            self.hedge_safety_order_price = None
            # 헷지 프론트로드 상태 초기화
            self.hedge_frontload_reentry_pending = False
            self.hedge_frontload_reentry_price = None
            self.hedge_frontload_reentry_qty = 0
            # 기타 (캔들 데이터는 시장 데이터이므로 유지)
            self.pending_hedge_orders = {}
            self.m_orders_data = []
            self.scheduled_stop = False
        # 복구 모드일 때는 GUI에서 설정한 플래그 값을 유지

        if is_restore_mode:
            # 복구 모드: 현재 단계의 진입 수량을 리스트에서 가져옴
            self.entry_quantity = float(self.entry_qty_list[current_step]) if current_step < len(self.entry_qty_list) else 0
            self._log(f"[DCA 복구] Step {current_step+1} 진입 수량: {self.entry_quantity}")
        else:
            # 일반 모드
            self.entry_quantity = float(entry_quantity)

        # 헷지 설정
        hedge_start = self.strategy_settings.get("HEDGE_START_PERCENT", 40)
        hedge_end = self.strategy_settings.get("HEDGE_END_PERCENT", 100)

        # 현재 단계까지의 누적 진입 수량 계산
        if is_restore_mode and len(self.entry_qty_list) > current_step:
            cumulative_entry_qty = sum(float(q) for q in self.entry_qty_list[:current_step + 1])
            self._log(f"[DCA 복구] 누적 진입 수량: {cumulative_entry_qty} (Step 1~{current_step+1})")
        else:
            cumulative_entry_qty = self.entry_quantity

        # 이전 단계까지의 누적 헷지 수량 계산
        if is_restore_mode and len(self.hedge_qty_list) > 0 and current_step > 0:
            previous_cumulative_hedge_qty = sum(float(q) for q in self.hedge_qty_list[:current_step])
            self._log(f"[DCA 복구] 이전 누적 헷지 수량: {previous_cumulative_hedge_qty} (Step 1~{current_step})")
        else:
            previous_cumulative_hedge_qty = 0

        # 누적 헷지 수량 저장 (M 주문 계산에 사용)
        self.previous_cumulative_hedge_qty = previous_cumulative_hedge_qty

        # 현재 단계의 헷지 수량 계산
        # hedge_qty_list가 있으면 그것을 사용, 없으면 계산
        if len(self.hedge_qty_list) > current_step:
            # SetupAutoTradeThread에서 이미 계산된 헷지 수량 사용
            self.hedge_quantity = float(self.hedge_qty_list[current_step])
            self._log(f"[DCA] Step {current_step} 헷지 수량 (리스트): {self.hedge_quantity}")
        else:
            # 헷지 수량 계산 (폴백)
            hedge_quantity_raw = trading_utils.calculate_hedge_quantity(
                self.entry_quantity,
                current_step,
                total_steps,
                cumulative_entry_qty,
                previous_cumulative_hedge_qty,
                hedge_start,
                hedge_end,
                self.hedge_exponent,
                self.test_mode,
                frontload_final_step=self.hedge_frontload_final_step
            )

            # 헷지 수량을 qtyStep에 맞춰 조정
            if symbol_info and 'lotSizeFilter' in symbol_info:
                qty_step = float(symbol_info.get('lotSizeFilter', {}).get('qtyStep', '0.01'))
                min_order_qty = float(symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.01'))
                qty_precision = trading_utils.count_decimal_places(qty_step)

                self.hedge_quantity = trading_utils.adjust_quantity(
                    hedge_quantity_raw, qty_step, qty_precision, min_order_qty
                )
                self._log(f"[DCA] 헷지 수량 조정: {hedge_quantity_raw:.4f} → {self.hedge_quantity} (qtyStep={qty_step})")
            else:
                self.hedge_quantity = hedge_quantity_raw

        self.last_trade_time = time.time()

        # 익절 실행 중 플래그 해제 (자동매매 재시작 시)
        self.is_profit_taking_in_progress = False

        log_color = "green" if self.side_mode == "LONG" else "red"
        self.log_message.emit(f"Status: <b style='color: {log_color};'>DCA Running</b>|||Step: <b>{self.current_step+1}/{self.total_steps}</b>")
        self._log(f"AutoTradeWorker: DCA 시작. Mode: {self.side_mode}, Symbol: {self.symbol}, Entry: {self.entry_quantity}, Hedge: {self.hedge_quantity:.4f}")

        # 복구 모드가 아니고 초기 진입이 안 되었으면 즉시 초기 진입 실행
        if not is_restore_mode and not self.initial_entry_done:
            self._log("[DCA] Step 0 초기 진입 실행 (자동)")
            self._execute_initial_entry()
            self.initial_entry_done = True

            # 실시간 상태 저장 (초기 진입 후에만)
            self._log("[DCA 상태] 초기 진입 후 상태 저장 요청")
            self.request_save_state.emit()
        elif is_restore_mode:
            self._log(f"[DCA 복구] 복구 모드: 초기 진입 건너뜀 (initial_entry_done={self.initial_entry_done})")
            # 복구 모드에서는 상태 저장하지 않음 (GUI에서 복원한 값 유지)

    @pyqtSlot()
    def stop_trading(self):
        """자동매매 중지"""
        if not self.is_running:
            return
        self.is_running = False
        self.next_step_order_id = None  # 주문 ID 초기화
        self.last_step_entry_price = None  # 마지막 진입 주문 가격 초기화

        # 헷지 안전망 주문 취소
        self._cancel_hedge_safety_order()

        self.log_message.emit("Status: <b style='color: gray;'>Stopped</b>|||Step: <b>-</b>")
        self._log("AutoTradeWorker: DCA 중지.")

    def fmt_price(self, price):
        """가격을 심볼의 정밀도에 맞게 포맷"""
        return f"{price:.{self.price_precision}f}"

    @pyqtSlot(str)
    def on_order_id_received(self, order_id):
        """GUI로부터 다음 단계 진입 주문 ID를 받음"""
        # 초기 진입(Step 0) 시장가 주문 ID는 무시
        # next_step_orders_placed가 True일 때만 저장 (NSO 지정가 주문이 생성된 후)
        if not self.next_step_orders_placed:
            self._log(f"[DCA] 주문 ID {order_id} 무시 (초기 진입 주문 - next_step_orders_placed=False)")
            return
        self.next_step_order_id = order_id
        self._log(f"[DCA] 다음 단계 주문 ID 저장: {order_id}")

    @pyqtSlot(str, float, float)
    def on_hedge_order_id_received(self, order_id, trigger_price, quantity):
        """GUI로부터 헷지 주문 ID를 받음 (슬리피지 추적용)"""
        # 트리거 인덱스 찾기 (hedge_trigger_prices에서 해당 트리거의 인덱스)
        trigger_index = -1
        for i, trigger in enumerate(self.hedge_trigger_prices):
            if abs(trigger[0] - trigger_price) < 0.0001:  # 부동소수점 비교
                trigger_index = i
                break

        self.pending_hedge_orders[order_id] = (trigger_price, quantity, trigger_index)
        self._log(f"[DCA 슬리피지] 헷지 주문 추적 시작: ID={order_id}, 트리거가=${trigger_price}, 수량={quantity}, 인덱스={trigger_index}")

    @pyqtSlot(dict)
    def on_order_update(self, order_data):
        """WebSocket으로부터 주문 업데이트 수신"""
        if not self.is_running:
            return

        try:
            o = order_data.get('o', {})
            order_id = str(o.get('i'))
            status = o.get('X')

            # 0. 헷지 안전망 주문 체결 확인
            if self.hedge_safety_order_id and order_id == self.hedge_safety_order_id and status == 'FILLED':
                self._log(f"[헷지 안전망] 안전망 주문 체결 감지! (주문 ID: {order_id})")
                self._handle_hedge_safety_order_filled()
                return  # 다른 로직 실행하지 않음

            # 1. 헷지 주문 체결 확인 (슬리피지 계산)
            if order_id in self.pending_hedge_orders and status == 'FILLED':
                trigger_price, quantity, trigger_index = self.pending_hedge_orders[order_id]
                avg_price = float(o.get('ap', 0))  # 평균 체결가

                if avg_price > 0:
                    # 가격 정밀도 가져오기 (tickSize 기반)
                    tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
                    price_precision = trading_utils.count_decimal_places(tick_size)

                    # 슬리피지 계산
                    slippage = avg_price - trigger_price
                    slippage_percent = (slippage / trigger_price) * 100

                    self._log(f"[DCA 헷지] 주문 체결 완료! (ID: {order_id})")
                    self._log(f"[DCA 헷지] 트리거가: ${trigger_price:.{price_precision}f}, 체결가: ${avg_price:.{price_precision}f}")
                    self._log(f"[DCA 헷지] 슬리피지: ${slippage:.{price_precision}f} ({slippage_percent:.2f}%)")

                    # GUI로 슬리피지 전송 (trigger_index가 유효한 경우)
                    if trigger_index >= 0:
                        self.hedge_slippage_updated.emit(trigger_index, slippage)
                        self._log(f"[DCA 헷지] GUI로 슬리피지 전송: 인덱스={trigger_index}, 슬리피지=${slippage:.{price_precision}f}")

                    # 불리한 슬리피지만 적용 (유의미한 경우: 0.01% 이상)
                    # LONG: 헷지 SHORT → 체결가 < 트리거가 (하방 슬리피지) 시 불리 → 수정
                    # SHORT: 헷지 LONG → 체결가 > 트리거가 (상방 슬리피지) 시 불리 → 수정
                    should_adjust = False
                    if self.side_mode == "LONG":
                        # LONG 모드: 하방 슬리피지만 적용
                        if slippage < 0 and abs(slippage_percent) >= 0.01:
                            should_adjust = True
                            self._log(f"[DCA 헷지] LONG 모드: 불리한 하방 슬리피지 감지 → 주문 조정")
                        elif slippage > 0:
                            self._log(f"[DCA 헷지] LONG 모드: 유리한 상방 슬리피지 → 조정 안 함")
                    elif self.side_mode == "SHORT":
                        # SHORT 모드: 상방 슬리피지만 적용
                        if slippage > 0 and abs(slippage_percent) >= 0.01:
                            should_adjust = True
                            self._log(f"[DCA 헷지] SHORT 모드: 불리한 상방 슬리피지 감지 → 주문 조정")
                        elif slippage < 0:
                            self._log(f"[DCA 헷지] SHORT 모드: 유리한 하방 슬리피지 → 조정 안 함")

                    if should_adjust:
                        self._adjust_orders_for_slippage(slippage)

                # 헷지 체결 시 임계값 재계산 플래그 설정
                self.hedge_filled_need_threshold_recalc = True
                self._log("[DCA 헷지] 임계값 재계산 플래그 설정 - 다음 ticker에서 재계산됨")

                # 헷지 체결 시 긴급 탈출 라인 설정 (API 호출 1회만)
                if self.hedge_liq_protection_enabled and not self.is_uptrend_entry:
                    self._setup_emergency_exit_line()

                # 헷지 프로토콜: WebSocket 포지션 업데이트 후 체크하도록 플래그 설정
                if self.hedge_protocol_enabled and not self.is_uptrend_entry:
                    self.hedge_protocol_pending_check = (trigger_index, avg_price)
                    self._log(f"[헷지 프로토콜] H{trigger_index+1} 체결 - WebSocket 포지션 업데이트 대기 중...")

                # 추적 목록에서 제거
                del self.pending_hedge_orders[order_id]

            # 2. 다음 단계 진입 주문이 체결되었는지 확인
            if self.next_step_order_id and order_id == self.next_step_order_id and status == 'FILLED':
                self._log(f"[DCA] Step {self.current_step+2} 주문 체결 감지! (주문 ID: {order_id})")

                # 역방향진입 처리 완료: 중복 방지 플래그 리셋
                if self.uptrend_entry_in_progress:
                    self.uptrend_entry_in_progress = False
                    self._log(f"[{self._el}] 체결 완료 - 중복 방지 플래그 리셋")

                # 체결가 조회 (평균 진입가 업데이트를 위해 필요)
                avg_fill_price = float(o.get('ap', 0))

                # 역방향진입인 경우만 익절 트리거 설정
                if self.is_uptrend_entry:
                    # 추가진입 시점의 실시간 가격 저장 (익절가 계산용)
                    self.entry_price_at_step = avg_fill_price
                    self._log(f"[{self._el}] 추가진입가 저장: ${self.fmt_price(self.entry_price_at_step)}")

                    # 고가/저가 추적 초기화 (추가진입 시점부터 새로 시작)
                    self.high_price_since_entry = avg_fill_price
                    self.low_price_since_entry = avg_fill_price
                    self._log(f"[{self._el}] 고가/저가 추적 초기화: High=${self.fmt_price(self.high_price_since_entry)}, Low=${self.fmt_price(self.low_price_since_entry)}")

                    # 헷지 트리거 초기화 (역방향진입 완료 후에는 헷지 불필요)
                    if self.hedge_trigger_prices:
                        self._log(f"[{self._el}] 헷지 트리거 초기화: {len(self.hedge_trigger_prices)}개 트리거 제거")
                        self.hedge_trigger_prices = []
                        self.remaining_hedge_qty = 0
                        # GUI에 헷지 트리거 초기화 알림
                        self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

                    # 헷지 청산은 역방향진입 요청 시점에 이미 처리됨 (진입 전에 먼저 청산)

                    # 익절가 즉시 계산 및 GUI 업데이트
                    self._calculate_and_emit_profit_target()
                    
                    # 역방향진입 완료 후 임계값 재계산 (새로운 entry_price_at_step 기준)
                    self.step_filled_need_threshold_recalc = True

                    # 플래그 리셋
                    self.is_uptrend_entry = False
                else:
                    self._log(f"[DCA] 정상 하향진입 체결 (익절 트리거 설정 안 함)")
                    
                    # 정상 진입 시 임계값 재계산 플래그 설정
                    self.step_filled_need_threshold_recalc = True

                # 단계 증가 전 NSO 상태를 "Filled"로 업데이트 (스냅샷에 반영)
                if self.m_orders_data and len(self.m_orders_data) >= 1:
                    self.m_orders_data[0]['status'] = 'Filled'
                    if avg_fill_price and self.m_orders_data[0].get('price', 0):
                        nso_slippage = avg_fill_price - self.m_orders_data[0]['price']
                        self.m_orders_data[0]['slippage'] = nso_slippage
                    self.m_orders_updated.emit(self.m_orders_data)

                # 헷지 트리거 최종 상태 동기화 (NSO 체결 시 H1-H4도 모두 체결된 상태)
                for trigger in self.hedge_trigger_prices:
                    if len(trigger) > 2 and not trigger[2]:
                        trigger[2] = True
                self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

                # 단계 증가 전 이전 Step 스냅샷 저장 시그널 발송
                previous_step = self.current_step
                self._log(f"[DCA 스냅샷] Step {previous_step} 완료 시그널 발송 (GUI 스냅샷 저장 요청)")
                self.step_completed.emit(previous_step)

                # 단계 증가 전 누적 헷지 수량 업데이트
                if previous_step < len(self.hedge_qty_list):
                    self.previous_cumulative_hedge_qty += self.hedge_qty_list[previous_step]
                    self._log(f"[DCA] 누적 헷지 수량 업데이트: {self.previous_cumulative_hedge_qty:.2f}")

                # 헷지 프로토콜: 다음 단계로 이동 시 플래그 리셋
                if self.hedge_protocol_enabled:
                    self.hedge_protocol_active = False
                    self.hedge_protocol_executed = False
                    self.hedge_protocol_exited_qty = 0
                    self.hedge_protocol_lowest_price = None
                    self.hedge_protocol_hedge_avg_price = None
                    self.hedge_protocol_waiting_for_be = False
                    self._log(f"[헷지 프로토콜] 단계 증가 → 플래그 리셋")

                # 단계 증가
                self.current_step += 1
                self.next_step_order_id = None  # 주문 ID 초기화

                # 헷지 프론트로드: 최종 단계 진입 시 프로토콜 즉시 활성화
                if (self.hedge_frontload_final_step and self.hedge_protocol_enabled
                        and self.current_step + 1 >= self.total_steps
                        and not self.is_uptrend_entry):
                    self._log(f"[헷지 프론트로드] 최종 단계 진입 - 프로토콜 즉시 활성화 시도")
                    self._update_hedge_protocol_avg_price()
                    if self.hedge_protocol_hedge_avg_price and self.hedge_protocol_hedge_avg_price > 0:
                        self.hedge_protocol_active = True
                        self.hedge_protocol_exited_qty = 0
                        self.hedge_protocol_waiting_for_be = False
                        self.hedge_protocol_lowest_price = self.hedge_protocol_hedge_avg_price
                        self._log(f"[헷지 프론트로드] 프로토콜 활성화! 최저가: ${self.fmt_price(self.hedge_protocol_lowest_price)}")

                # 역방향진입 완료 시에는 새 주문을 생성하지 않도록 플래그 유지
                # 정상 하향진입 시에만 다음 단계 주문 생성 허용
                if self.entry_price_at_step is not None:
                    # 역방향진입 완료 → 익절 트리거만 모니터링, 새 주문 생성 안 함
                    self.next_step_orders_placed = True
                    self._log(f"[{self._el}] 익절 모니터링 모드 진입 (다음 단계 주문 생성 안 함)")
                else:
                    # 정상 하향진입 → 다음 단계 주문 생성 허용
                    self.next_step_orders_placed = False

                # 상태 저장 (GUI에 저장 요청)
                self._log(f"[DCA] 현재 단계 업데이트: Step {self.current_step+1}/{self.total_steps}")
                self.request_save_state.emit()

                # 마지막 단계가 아니면 계속 진행
                if self.current_step + 1 < self.total_steps:
                    self._log(f"[DCA] Step {self.current_step+1} 완료. 다음 단계 준비 중...")
                    log_color = "green" if self.side_mode == "LONG" else "red"
                    self.log_message.emit(f"Status: <b style='color: {log_color};'>DCA Running</b>|||Step: <b>{self.current_step+1}/{self.total_steps}</b>")
                else:
                    # 마지막 단계 (Step 10) 완료 - 손실 방지 로직 발동
                    self._log(f"[DCA] 마지막 단계 완료!")
                    log_color = "green" if self.side_mode == "LONG" else "red"
                    self.log_message.emit(f"Status: <b style='color: {log_color};'>Final Step Completed</b>|||Step: <b>{self.current_step+1}/{self.total_steps}</b>")

                    # 최종 단계 손실 방지 주문 (Stop Loss + Trailing Stop)
                    if not self.final_step_protection_placed:
                        self._place_final_step_protection()

        except Exception as e:
            self._log(f"[DCA] 주문 업데이트 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    @pyqtSlot(dict, dict, dict)
    def process_tick(self, ticker_data, position_data, candle_data=None):
        """실시간 가격 및 포지션 데이터 처리

        Args:
            ticker_data: 티커 데이터 (현재가 등)
            position_data: 포지션 데이터
            candle_data: 최근 캔들 데이터 {'prev': {...}, 'current': {...}}
        """
        if not self.is_running:
            return

        try:
            # 포지션 데이터 저장 (익절가 계산 시 Break Even 계산에 사용)
            if position_data:
                self.current_position_data = position_data
            # 캔들 데이터 업데이트 및 봉 마감 감지
            candle_updated = False
            if candle_data:
                prev_candle = candle_data.get('prev')
                current_candle = candle_data.get('current')

                # 현재 봉의 timestamp를 사용하여 봉이 변경되었는지 확인
                if current_candle and current_candle.get('timestamp'):
                    current_candle_time = float(current_candle.get('timestamp', 0))

                    # 초기화 체크: last_candle_check_time이 0이면 첫 실행이므로 초기화만 하고 봉 마감으로 간주하지 않음
                    if self.last_candle_check_time == 0:
                        self.last_candle_check_time = current_candle_time
                        # 초기화: 전전봉 없음, 전봉=prev, 현재봉=current
                        self.prev_prev_candle = None
                        self.prev_candle = prev_candle
                        self.current_candle = current_candle
                        self._log(f"[봉 체크] 초기화: 현재 봉 timestamp={current_candle_time} (봉 마감으로 간주 안 함)")
                    # 이전에 체크한 봉과 다른 봉인지 확인 (봉 마감 감지)
                    elif current_candle_time != self.last_candle_check_time:
                        candle_updated = True
                        self.last_candle_check_time = current_candle_time
                        # [수정] GUI에서 전달받은 데이터 사용
                        # GUI의 prev = df.iloc[-2] = 전전봉 (마감됨)
                        # GUI의 current = df.iloc[-1] = 전봉 (방금 마감됨, 새 봉 시작 시점)
                        # 봉 마감 시점에서 조건 체크는 전전봉(prev)과 전봉(이전 current의 최종 데이터)을 사용해야 함
                        # 하지만 GUI의 prev가 이미 전전봉이므로, 기존 prev_candle을 전전봉으로 사용
                        self.prev_prev_candle = self.prev_candle  # 기존 전봉 → 전전봉
                        self.prev_candle = prev_candle  # GUI의 prev (마감된 전봉의 최종 데이터)
                        self.current_candle = current_candle
                        self._log(f"[봉 마감] prev_prev: {self.prev_prev_candle.get('open') if self.prev_prev_candle else 'None'}->{self.prev_prev_candle.get('close') if self.prev_prev_candle else 'None'}, prev: {prev_candle.get('open')}->{prev_candle.get('close')}")
                    else:
                        # 같은 봉이 진행 중 - 현재봉만 업데이트 (전전봉, 전봉은 유지)
                        self.current_candle = current_candle
                else:
                    # timestamp가 없으면 그냥 업데이트 (이전 방식 호환)
                    if self.prev_candle is None:
                        self.prev_prev_candle = None
                        self.prev_candle = prev_candle
                    self.current_candle = current_candle

            # 1. 심볼 확인
            if ticker_data.get('s') != self.symbol:
                return

            # 2. 포지션 확인
            long_pos_key = f"{self.symbol}_LONG"
            short_pos_key = f"{self.symbol}_SHORT"

            long_pos_amt = float(position_data.get(long_pos_key, {}).get('amount', 0))
            short_pos_amt = float(position_data.get(short_pos_key, {}).get('amount', 0))

            has_main_position = (long_pos_amt > 0 if self.side_mode == "LONG" else short_pos_amt < 0)

            # 3. Step 0 초기 진입 로직
            if not self.initial_entry_done:
                # 10초 타임아웃
                if time.time() - self.last_trade_time > 10:
                    self._log("AutoTradeWorker: Step 0 초기 진입 타임아웃. 중지.")
                    self.stop_trading()
                    return

                # 포지션 없으면 즉시 진입
                if not has_main_position:
                    self._execute_initial_entry()
                    self.initial_entry_done = True

                    # 실시간 상태 저장 (Step 0 초기 진입 후)
                    self._log("[DCA 상태] Step 0 진입 후 상태 저장 요청")
                    self.request_save_state.emit()
                    return

            # 4. Step 0 체결 후 → Step 1 지정가 주문 생성
            # [중요] 익절 모니터링 모드(역방향진입 후)에서는 주문 생성 안 함
            if self.initial_entry_done and not self.next_step_orders_placed:
                # 익절 모니터링 모드 확인: entry_price_at_step이 있으면 역방향진입 완료 상태
                if self.entry_price_at_step is not None:
                    # 역방향진입 완료 → 익절만 모니터링, 새 주문 생성 안 함
                    self._log(f"[DCA] 익절 모니터링 모드 감지 ({self._el} 완료) - 다음 단계 주문 생성 스킵")
                    # 플래그를 True로 설정하여 반복 실행 방지
                    self.next_step_orders_placed = True
                elif has_main_position:
                    self._log(f"[DCA] Step {self.current_step+1} 체결 확인. 다음 단계 주문 생성 시작...")
                    self._place_next_step_orders(position_data)
                    self.next_step_orders_placed = True

                    # 초기 임계값 계산 플래그 설정 (다음 단계 주문 생성 후)
                    self.step_filled_need_threshold_recalc = True

                    # 마지막 단계가 아닌 경우에만 "다음 주문 대기" 로그 출력
                    if self.current_step + 1 < self.total_steps:
                        self._log(f"[DCA] Step {self.current_step+2} 지정가 주문 완료. 체결 대기 중...")

                        # 실시간 상태 저장 (다음 단계 주문 생성 후)
                        self._log(f"[DCA 상태] Step {self.current_step+2} 주문 생성 후 상태 저장 요청")
                        self.request_save_state.emit()

                        # Step 업데이트 (다음 단계 대기 중)
                        log_color = "green" if self.side_mode == "LONG" else "red"
                        self.log_message.emit(f"Status: <b style='color: {log_color};'>Waiting for Step {self.current_step+2}</b>|||Step: <b>{self.current_step+1}/{self.total_steps}</b>")

            # 4-1. 다음 단계 지정가 주문 체결 확인
            # (이제 주문 ID 기반으로 WebSocket 주문 업데이트에서 처리됨 - on_order_update 참조)

            # 현재가 조회 (헷지 모니터링 및 익절 모니터링에 공통 사용)
            current_price = float(ticker_data.get('c', 0))
            if current_price == 0:
                return
            
            # 현재가 저장 (헷지 청산 시 최소 금액 계산용)
            self.current_price = current_price

            # 고가/저가 추적 업데이트 (익절가 계산용 - 역방향진입 후에만 활성화)
            if self.high_price_since_entry is not None and self.low_price_since_entry is not None:
                if current_price > self.high_price_since_entry:
                    self.high_price_since_entry = current_price
                if current_price < self.low_price_since_entry:
                    self.low_price_since_entry = current_price

            # 4-2. 헷지 프로토콜: 되돌림 감지 및 익절 체크
            if self.hedge_protocol_active and not self.is_uptrend_entry:
                self._check_hedge_protocol_retracement(current_price)

            # 4-3. 헷지 프로토콜: 대기 중인 활성화 조건 체크 (WebSocket 포지션 업데이트 후)
            if self.hedge_protocol_pending_check is not None and not self.is_uptrend_entry:
                pending_trigger_index, pending_fill_price = self.hedge_protocol_pending_check
                self.hedge_protocol_pending_check = None  # 플래그 초기화
                self._log(f"[헷지 프로토콜] H{pending_trigger_index+1} 포지션 업데이트 완료 - 활성화 조건 체크 시작")
                self._handle_hedge_protocol_trigger(pending_trigger_index, pending_fill_price)

            # 4-4. 헷지 프론트로드: 최종 단계에서 프로토콜 미활성이면 즉시 활성화
            if (self.hedge_protocol_enabled and self.hedge_frontload_final_step
                    and self.current_step + 1 >= self.total_steps
                    and not self.hedge_protocol_active
                    and not self.hedge_protocol_executed
                    and not self.is_uptrend_entry):
                self._update_hedge_protocol_avg_price()
                if self.hedge_protocol_hedge_avg_price and self.hedge_protocol_hedge_avg_price > 0:
                    self.hedge_protocol_active = True
                    self.hedge_protocol_exited_qty = 0
                    self.hedge_protocol_waiting_for_be = False
                    self.hedge_protocol_lowest_price = self.hedge_protocol_hedge_avg_price
                    self._log(f"[헷지 프론트로드] 최종 단계 프로토콜 활성화 (복구) - 최저가 추적 시작")

            # 4-5. 헷지 프론트로드: 최종단계 재진입 모니터링 (익절 후 H4 가격에서 재진입)
            if self.hedge_frontload_reentry_pending and self.hedge_frontload_reentry_price:
                reentry_triggered = False
                if self.side_mode == "LONG" and current_price <= self.hedge_frontload_reentry_price:
                    reentry_triggered = True
                    hedge_side = "SELL"
                elif self.side_mode == "SHORT" and current_price >= self.hedge_frontload_reentry_price:
                    reentry_triggered = True
                    hedge_side = "BUY"

                if reentry_triggered:
                    reentry_qty = self.hedge_frontload_reentry_qty
                    self._log(f"[헷지 프론트로드] 재진입 가격 도달! 현재가: ${self.fmt_price(current_price)}, H4: ${self.fmt_price(self.hedge_frontload_reentry_price)}")
                    self._log(f"[헷지 프론트로드] 재진입 시장가 주문: {hedge_side} {reentry_qty}")
                    self.execute_trade_signal.emit(self.symbol, hedge_side, str(reentry_qty), True)
                    self.hedge_frontload_reentry_pending = False
                    self.hedge_frontload_reentry_price = None
                    self.hedge_frontload_reentry_qty = 0
                    self.hedge_protocol_exited_qty = 0

            # 5. 헷지 가격 조건 모니터링 (가격 돌파 시 시장가 주문)
            if self.next_step_orders_placed and self.hedge_trigger_prices:

                for trigger in self.hedge_trigger_prices:
                    trigger_price, qty, executed = trigger

                    if executed:
                        continue  # 이미 실행된 트리거는 스킵

                    # LONG 포지션: 가격 하방 돌파 확인 (현재가 <= 트리거 가격)
                    # SHORT 포지션: 가격 상방 돌파 확인 (현재가 >= 트리거 가격)
                    triggered = False

                    if self.side_mode == "LONG" and current_price <= trigger_price:
                        triggered = True
                        hedge_side = "SELL"
                    elif self.side_mode == "SHORT" and current_price >= trigger_price:
                        triggered = True
                        hedge_side = "BUY"

                    if triggered:
                        self._log(f"[DCA 헷지] 가격 돌파 감지! 현재가: ${current_price}, 트리거: ${trigger_price}")

                        # 최소 주문 금액 체크 (주문 전에 확인)
                        min_order_value = float(self.symbol_info.get('lotSizeFilter', {}).get('minNotionalValue', '5'))
                        order_value = qty * current_price
                        if order_value < min_order_value:
                            self._log(f"[DCA 헷지] 주문 금액(${order_value:.2f})이 최소 주문 금액(${min_order_value}) 미만으로 스킵")
                            # 실행 완료 표시 (재시도 방지)
                            trigger[2] = True
                            self.remaining_hedge_qty -= qty
                            # GUI에 헷지 트리거 업데이트 알림
                            self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)
                            continue

                        self._log(f"[DCA 헷지] {hedge_side} {qty} 시장가 주문 실행")

                        # 헷지 주문 추적 정보 저장 (시그널 emit 전에 먼저 저장)
                        # GUI는 이 정보를 사용하여 주문 ID를 다시 워커로 전달
                        self.last_hedge_trigger_info = (trigger_price, qty)

                        # 시장가 헷지 주문 실행 (트리거 가격과 수량 포함)
                        self.execute_trade_signal.emit(self.symbol, hedge_side, str(qty), True)

                        # 실행 완료 표시
                        trigger[2] = True
                        self.remaining_hedge_qty -= qty

                        # GUI에 헷지 트리거 업데이트 알림 (마커 색상 변경을 위해)
                        self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

                        # 실시간 상태 저장 (헷지 트리거 발동 시)
                        self._log(f"[DCA 상태] 헷지 트리거 ${trigger_price} 발동 후 상태 저장 요청")
                        self.request_save_state.emit()

            # 6. 상승 중 추가진입 임계값 가격 계산 및 차트 표시
            # 임계값 재계산이 필요한 경우만 계산 (매 ticker마다 계산하지 않음)
            should_recalculate_threshold = False
            
            # 조건 1: 헷지 주문 체결 시 (플래그로 트리거됨)
            if self.hedge_filled_need_threshold_recalc:
                should_recalculate_threshold = True
                self._log("[임계값] 헷지 체결 감지 - 임계값 재계산")
            
            # 조건 2: 다음 단계 주문 체결 시 또는 초기 주문 생성 시 (플래그로 트리거됨)
            if self.step_filled_need_threshold_recalc:
                should_recalculate_threshold = True
                self._log("[임계값] 주문 생성/체결 감지 - 임계값 재계산")

            # 조건 3: Break Even 없이 임계값 계산되었던 경우, Break Even이 가능해지면 재계산
            if self.threshold_needs_break_even_update and not should_recalculate_threshold:
                pos_key_main = f"{self.symbol}_{self.side_mode}"
                pos_key_hedge = f"{self.symbol}_{'SHORT' if self.side_mode == 'LONG' else 'LONG'}"
                main_pos = position_data.get(pos_key_main, {})
                hedge_pos = position_data.get(pos_key_hedge, {})
                if abs(float(hedge_pos.get('amount', 0))) > 0 and float(hedge_pos.get('entry_price', hedge_pos.get('entry', 0))) > 0:
                    if abs(float(main_pos.get('amount', 0))) > 0 and float(main_pos.get('entry_price', main_pos.get('entry', 0))) > 0:
                        should_recalculate_threshold = True
                        self._log("[임계값] Break Even 데이터 확보 - 임계값 재계산")
            
            if should_recalculate_threshold:
                # 기준 가격 결정: Break Even 가격 우선, 계산 불가 시 평균 진입가 사용
                base_price = 0.0
                is_break_even_base = False

                if self.entry_price_at_step is not None:
                    # 역방향진입 완료: 역방향진입 체결가 기준
                    base_price = self.entry_price_at_step
                    self.threshold_needs_break_even_update = False
                    self._log(f"[임계값] 기준가: {self._el} 체결가 ${self.fmt_price(base_price)}")
                else:
                    # 정상 DCA: Break Even 가격 계산 시도
                    pos_key_main = f"{self.symbol}_{self.side_mode}"
                    pos_key_hedge = f"{self.symbol}_{'SHORT' if self.side_mode == 'LONG' else 'LONG'}"

                    main_position = position_data.get(pos_key_main, {})
                    hedge_position = position_data.get(pos_key_hedge, {})

                    main_qty = abs(float(main_position.get('amount', 0)))
                    main_entry = float(main_position.get('entry_price', main_position.get('entry', 0)))
                    hedge_qty = abs(float(hedge_position.get('amount', 0)))
                    hedge_entry = float(hedge_position.get('entry_price', hedge_position.get('entry', 0)))

                    # Break Even 계산 가능 여부 확인
                    if main_qty > 0 and hedge_qty > 0 and main_entry > 0 and hedge_entry > 0:
                        # Break Even 계산
                        if self.side_mode == "LONG":
                            numerator = main_qty * main_entry - hedge_qty * hedge_entry
                            denominator = main_qty - hedge_qty
                        else:
                            numerator = hedge_qty * hedge_entry - main_qty * main_entry
                            denominator = hedge_qty - main_qty

                        if abs(denominator) >= 0.0001:
                            break_even_price = numerator / denominator
                            if break_even_price > 0:
                                # LONG: max(Break Even, 평균 진입가), SHORT: min(Break Even, 평균 진입가)
                                if self.side_mode == "LONG":
                                    base_price = max(break_even_price, main_entry)
                                    comparison = "높은 값"
                                else:  # SHORT
                                    base_price = min(break_even_price, main_entry)
                                    comparison = "낮은 값"

                                is_break_even_base = True
                                self.threshold_needs_break_even_update = False
                                self._log(f"[임계값] Break Even: ${self.fmt_price(break_even_price)}, 메인 평균가: ${self.fmt_price(main_entry)}")
                                self._log(f"[임계값] 기준가: ${self.fmt_price(base_price)} ({comparison} 선택) (메인: {main_qty}@${self.fmt_price(main_entry)}, 헷지: {hedge_qty}@${self.fmt_price(hedge_entry)})")

                    # Break Even 계산 실패 시 메인 평균가 사용
                    if base_price == 0:
                        base_price = main_entry if main_entry > 0 else 0
                        self.threshold_needs_break_even_update = True
                        self._log(f"[임계값] 기준가: 메인 평균가 ${self.fmt_price(base_price)} (Break Even 계산 불가)")

                if base_price > 0:
                    # 임계값 조정: Break Even 기준일 때는 조정 없음, 역방향진입 후에도 조정 없음
                    threshold_adjustment = 0.0

                    if is_break_even_base:
                        # Break Even 기준: 조정값 없이 설정값만 사용
                        self._log(f"[임계값] Break Even 기준 - 추가 조정 없음")
                    elif self.entry_price_at_step is not None:
                        # 역방향진입 완료: 조정값 없이 설정값만 사용
                        self._log(f"[임계값] {self._el} 완료 후 - 추가 조정 없음")

                    # 임계값 가격 계산
                    adjusted_threshold = self.uptrend_entry_profit_threshold + threshold_adjustment

                    if self.side_mode == "LONG":
                        # LONG: 기준가 × (1 + 조정된 임계값%)
                        threshold_price = base_price * (1 + adjusted_threshold / 100.0)
                        # 2차 임계값: 1차 임계값의 2배 거리
                        threshold_price_2 = base_price * (1 + adjusted_threshold * self.uptrend_threshold_2_multiplier / 100.0)
                    else:
                        # SHORT: 기준가 × (1 - 조정된 임계값%)
                        threshold_price = base_price * (1 - adjusted_threshold / 100.0)
                        # 2차 임계값: 1차 임계값의 2배 거리
                        threshold_price_2 = base_price * (1 - adjusted_threshold * self.uptrend_threshold_2_multiplier / 100.0)

                    self._log(f"[DEBUG 임계값] 기준가: ${self.fmt_price(base_price)}, 조정 임계값: {adjusted_threshold:.4f}%, 1차: ${self.fmt_price(threshold_price)}, 2차: ${self.fmt_price(threshold_price_2)}")

                    # 임계값 저장 및 GUI 업데이트 (변경된 경우에만)
                    if self.uptrend_threshold_price is None or abs(self.uptrend_threshold_price - threshold_price) > 0.0001:
                        self.uptrend_threshold_price = threshold_price
                        self.uptrend_threshold_price_2 = threshold_price_2
                        self._log(f"[임계값 갱신] 1차: ${self.fmt_price(threshold_price)}, 2차: ${self.fmt_price(threshold_price_2)}")
                        # GUI에 임계값 가격 업데이트 알림 (차트에 표시)
                        self.uptrend_threshold_updated.emit(threshold_price)
                        self.uptrend_threshold_2_updated.emit(threshold_price_2)
                    
                    # 임계값 계산 완료 - 플래그 리셋
                    self.hedge_filled_need_threshold_recalc = False
                    self.step_filled_need_threshold_recalc = False
                else:
                    # base_price가 0이면 임계값 계산 불가 - 플래그 유지하여 다음 틱에서 재시도
                    self._log("[임계값] 기준가 없음 (0) - 플래그 유지, 다음 틱에서 재시도")

            # 2차 임계값 즉시 진입 확인 (실시간 가격 체크)
            if self.uptrend_threshold_price_2 is not None and not self.uptrend_entry_in_progress:
                threshold_2_breached = False

                if self.side_mode == "LONG":
                    # LONG: 현재가가 2차 임계값 이상이면 즉시 진입
                    if current_price >= self.uptrend_threshold_price_2:
                        threshold_2_breached = True
                else:
                    # SHORT: 현재가가 2차 임계값 이하면 즉시 진입
                    if current_price <= self.uptrend_threshold_price_2:
                        threshold_2_breached = True

                if threshold_2_breached:
                    self._log(f"[{self._el} 2차 임계값] 돌파 감지! 현재가 ${self.fmt_price(current_price)}, 2차 임계값 ${self.fmt_price(self.uptrend_threshold_price_2)}")
                    self._log(f"[{self._el} 2차 임계값] 캔들 패턴 무시하고 즉시 진입")

                    # 중복 진입 방지 플래그 설정
                    self.uptrend_entry_in_progress = True

                    # ========== 헷지 청산을 역방향진입보다 먼저 실행 ==========
                    self._reduce_hedge_on_uptrend_entry()

                    # 지정가 주문이 있으면 취소 요청과 함께 전송
                    order_id_to_cancel = self.next_step_order_id if self.next_step_order_id else ""

                    # next_step_order_id 초기화 (시장가 주문은 취소 불가하므로 즉시 제거)
                    self.next_step_order_id = None

                    # 역방향진입 플래그 설정 (체결 시 익절 트리거 설정용)
                    self.is_uptrend_entry = True

                    # GUI에 주문 취소 및 시장가 진입 요청
                    self.uptrend_entry_request.emit(order_id_to_cancel)

                    # 임계값 체크 방지를 위해 임계값을 None으로 설정 (중복 진입 방지)
                    self.uptrend_threshold_price = None
                    self.uptrend_threshold_price_2 = None

                    # 즉시 진입 요청 후 나머지 로직 스킵 (1차 임계값 체크 불필요)
                    return

            # 상승 중 추가진입 조건 확인 (봉 마감 시에만 체크 - 1차 임계값)
            # [수정] 익절 모니터링 중에도 추가 역방향진입 허용 (entry_price_at_step 체크 제거)
            if candle_updated and not self.uptrend_entry_in_progress:
                condition_result = self._check_uptrend_entry_condition(position_data)
                self._log(f"[DEBUG {self._el}] 봉마감 체크 - 결과: {condition_result}, entry_price_at_step: {self.entry_price_at_step}")

                if condition_result:
                    self._log(f"[{self._el}] 조건 만족! 시장가 즉시 진입")

                    # 중복 진입 방지 플래그 설정
                    self.uptrend_entry_in_progress = True

                    # ========== 헷지 청산을 역방향진입보다 먼저 실행 ==========
                    self._reduce_hedge_on_uptrend_entry()

                    # 지정가 주문이 있으면 취소 요청과 함께 전송 (order_id 포함)
                    # 지정가 주문이 없으면 빈 문자열로 전송 (GUI에서 취소 스킵하고 바로 시장가 진입)
                    order_id_to_cancel = self.next_step_order_id if self.next_step_order_id else ""

                    # next_step_order_id 초기화 (시장가 주문은 취소 불가하므로 즉시 제거)
                    self.next_step_order_id = None

                    # 역방향진입 플래그 설정 (체결 시 익절 트리거 설정용)
                    self.is_uptrend_entry = True

                    # GUI에 주문 취소 및 시장가 진입 요청
                    self.uptrend_entry_request.emit(order_id_to_cancel)

            # 7. 익절 트리거 모니터링 (상향 돌파 후 하향 돌파 감지)
            # entry_price_at_step이 설정되어 있으면 익절 모니터링 시작 (첫 계산 포함)
            if self.entry_price_at_step is not None and has_main_position:
                self._monitor_profit_target(current_price, position_data)

            # 7.5. 헷지 긴급 탈출 라인 제거됨 (항상 안전망 주문 사용)

            # 8. 최종 단계: 보호 주문 미완료 시 재시도 (2초 간격)
            if self.current_step + 1 >= self.total_steps and not self.final_step_protection_placed:
                if time.time() - self._last_final_step_protection_attempt >= 2:
                    self._last_final_step_protection_attempt = time.time()
                    self._place_final_step_protection()

            # 9. 최종 단계: 메인 포지션 강제 청산 감지 → 헷지 트레일링 스탑
            if self.current_step + 1 >= self.total_steps and not self.main_liquidation_handled:
                self._check_main_liquidation_and_protect_hedge(position_data, current_price)

            # 9.5. 최종 단계: 헷지 포지션 청산 감지 → 메인 트레일링 스탑
            if self.current_step + 1 >= self.total_steps and not self.hedge_liquidation_handled:
                self._check_hedge_liquidation_and_protect_main(position_data, current_price)

            # 10. 최종 단계 포지션 청산 모니터링
            if self.monitoring_final_step_closure:
                self._monitor_final_step_position_closure(position_data)

        except Exception as e:
            self._log(f"AutoTradeWorker: process_tick 오류: {e}")
            import traceback
            traceback.print_exc()

    def calculate_break_even(self, position_data):
        """
        Break Even (손익분기점) 계산
        
        Args:
            position_data: 포지션 데이터 딕셔너리
            
        Returns:
            float: Break Even 가격, 계산 불가능하면 None
        """
        try:
            long_pos_key = f"{self.symbol}_LONG"
            short_pos_key = f"{self.symbol}_SHORT"
            
            long_pos = position_data.get(long_pos_key, {})
            short_pos = position_data.get(short_pos_key, {})
            
            # Safe conversion: None, '', 빈 문자열 처리
            long_amt = abs(float(long_pos.get('amount') or 0))
            short_amt = abs(float(short_pos.get('amount') or 0))

            # 평균가 조회: 'entry_price' 키 우선, 'entry' 폴백
            long_avg_price = float(long_pos.get('entry_price', long_pos.get('entry', 0)) or 0)
            short_avg_price = float(short_pos.get('entry_price', short_pos.get('entry', 0)) or 0)
            
            # LONG 포지션 전략
            if self.side_mode == "LONG":
                main_qty = long_amt
                main_avg_price = long_avg_price
                hedge_qty = short_amt
                hedge_avg_price = short_avg_price
            # SHORT 포지션 전략
            else:
                main_qty = short_amt
                main_avg_price = short_avg_price
                hedge_qty = long_amt
                hedge_avg_price = long_avg_price
            
            # 유효성 검사
            if main_qty == 0 or main_avg_price == 0:
                return None
            
            # 헷지가 없으면 평균 진입가 + 시장가 수수료가 손익분기점
            if hedge_qty == 0 or hedge_avg_price == 0:
                # Bybit 시장가 수수료 (Taker fee: 0.055%)
                market_fee_percent = 0.055
                if self.side_mode == "LONG":
                    # LONG 포지션: 매도 시 수수료 고려 (더 높은 가격에 청산해야 손익분기)
                    return main_avg_price * (1 + market_fee_percent / 100.0)
                else:  # SHORT
                    # SHORT 포지션: 매수 시 수수료 고려 (더 낮은 가격에 청산해야 손익분기)
                    return main_avg_price * (1 - market_fee_percent / 100.0)
            
            # Net Position 계산
            net_qty = main_qty - hedge_qty
            
            # Net Position이 0이면 계산 불가 (완전 헷지 상태)
            if abs(net_qty) < 0.0001:
                return None
            
            # Break Even 계산
            # break_even = (main_qty × main_avg_price - hedge_qty × hedge_avg_price) / net_qty
            break_even = (main_qty * main_avg_price - hedge_qty * hedge_avg_price) / net_qty
            
            return break_even
            
        except Exception as e:
            import traceback
            self._log(f"[Break Even] 계산 오류: {e}")
            self._log(f"[Break Even] 상세 오류:")
            traceback.print_exc()
            self._log(f"[Break Even] position_data 내용: {position_data}")
            return None

    def _check_uptrend_entry_condition(self, position_data):
        """상승 중 추가진입 조건 확인

        조건 1: 전봉 마감 가격이 임계값 가격 이상/이하
                - LONG: 전봉 종가 >= (평균진입가 × (1 + 임계값%))
                - SHORT: 전봉 종가 <= (평균진입가 × (1 - 임계값%))
                (기본값: 1%, UPTREND_ENTRY_PROFIT_THRESHOLD 설정으로 변경 가능)
        조건 2: 음봉 후 음봉의 open가를 초과하는 양봉 (LONG) / 양봉 후 양봉의 open가 미만인 음봉 (SHORT)
                - 전전봉과 전봉을 비교 (둘 다 완성된 캔들)

        Returns:
            bool: 조건 만족 시 True
        """
        try:
            # 캔들 데이터가 없으면 False (전전봉과 전봉이 모두 필요)
            if not self.prev_prev_candle or not self.prev_candle:
                # print(f"[DEBUG {self._el} 체크] 완성된 캔들 2개 필요 - prev_prev_candle={self.prev_prev_candle is not None}, prev_candle={self.prev_candle is not None}")  # 봉마감마다 출력 제거
                return False

            # 평균 진입가 조회
            pos_key = f"{self.symbol}_{self.side_mode}"
            position = position_data.get(pos_key, {})
            avg_entry_price = float(position.get('entry_price', position.get('entry', 0)))

            if avg_entry_price == 0:
                # print(f"[DEBUG {self._el} 체크] 평균 진입가 없음 - avg_entry_price=0")  # 봉마감마다 출력 제거
                return False

            # 캔들 데이터 파싱: 전전봉과 전봉 (둘 다 완성된 캔들)
            prev_prev_open = float(self.prev_prev_candle.get('open', 0))
            prev_prev_close = float(self.prev_prev_candle.get('close', 0))
            prev_open = float(self.prev_candle.get('open', 0))
            prev_close = float(self.prev_candle.get('close', 0))

            if prev_prev_open == 0 or prev_prev_close == 0 or prev_open == 0 or prev_close == 0:
                # print(f"[DEBUG {self._el} 체크] 캔들 데이터 값 오류 (0 포함)")  # 봉마감마다 출력 제거
                return False

            # LONG 포지션 조건
            if self.side_mode == "LONG":
                # Break Even 계산
                break_even = self.calculate_break_even(position_data)
                
                # 안전한 기준가 선택
                if self.entry_price_at_step is not None:
                    # 역방향진입 이후면 진입가 사용
                    base_price = self.entry_price_at_step
                else:
                    # Break Even이 있으면 avg_entry_price와 비교하여 더 높은 값 사용 (안전한 값)
                    if break_even is not None:
                        base_price = max(break_even, avg_entry_price)
                        if break_even != avg_entry_price:
                            self._log(f"[{self._el} 체크] Break Even: ${self.fmt_price(break_even)}, 평균진입가: ${self.fmt_price(avg_entry_price)} → 기준가: ${self.fmt_price(base_price)}")
                    else:
                        base_price = avg_entry_price

                # 임계값 가격 계산 (기준가 × (1 + 임계값%))
                threshold_price = base_price * (1 + self.uptrend_entry_profit_threshold / 100.0)

                # 먼저 전봉 종가가 임계값 이상인지 확인 (임계값을 넘어섰을 때만 체크)
                if prev_close < threshold_price:
                    self._log(f"[DEBUG {self._el} 체크] LONG: 전봉 종가({prev_close:.4f}) < 임계값({threshold_price:.4f}) → 체크 스킵")
                    return False

                self._log(f"[DEBUG {self._el} 체크] 캔들 데이터 (완성된 캔들 2개):")
                self._log(f"  전전봉: open={prev_prev_open:.4f}, close={prev_prev_close:.4f}")
                self._log(f"  전봉: open={prev_open:.4f}, close={prev_close:.4f}")
                self._log(f"  기준가: ${base_price:.4f}, 임계값: ${threshold_price:.4f}")

                # 조건 1: 전봉 마감가가 임계값 가격 이상
                condition1 = prev_close >= threshold_price

                # 조건 2: 전봉이 양봉 & 전봉이 전전봉 open 초과 (상승추세, 전전봉 음/양봉 모두 허용)
                # prev_prev_is_bearish = prev_prev_close < prev_prev_open  # 전전봉 음봉 조건 제거
                prev_is_bullish = prev_close > prev_open  # 전봉이 양봉
                prev_exceeds_prev_prev_open = prev_close > prev_prev_open  # 전봉이 전전봉 open 초과
                condition2 = prev_is_bullish and prev_exceeds_prev_prev_open  # 전전봉 음봉 조건 제거

                self._log(f"[DEBUG {self._el} 체크] LONG 조건 확인:")
                self._log(f"  조건1 (가격 임계값): prev_close={prev_close:.4f} >= threshold_price={threshold_price:.4f} = {condition1}")
                self._log(f"  조건2 (캔들패턴): 전봉양봉={prev_is_bullish}, 전봉>전전봉open={prev_exceeds_prev_prev_open} = {condition2}")

                if condition1 and condition2:
                    self._log(f"[{self._el}] LONG 조건 만족!")
                    self._log(f"  평균진입가: ${self.fmt_price(avg_entry_price)}, 전봉 종가: ${self.fmt_price(prev_close)}")
                    self._log(f"  임계값 가격: ${self.fmt_price(threshold_price)} (평균진입가 + {self.uptrend_entry_profit_threshold}%)")
                    self._log(f"  전전봉: open=${self.fmt_price(prev_prev_open)}, close=${self.fmt_price(prev_prev_close)}")
                    self._log(f"  전봉: open=${self.fmt_price(prev_open)}, close=${self.fmt_price(prev_close)} (양봉, 전전봉 open 돌파)")
                    return True
                # else:
                    # print(f"[DEBUG {self._el} 체크] LONG 조건 미충족 - condition1={condition1}, condition2={condition2}")  # 봉마감마다 출력 제거

            # SHORT 포지션 조건 (반대)
            elif self.side_mode == "SHORT":
                # Break Even 계산
                break_even = self.calculate_break_even(position_data)
                
                # 안전한 기준가 선택
                if self.entry_price_at_step is not None:
                    # 역방향진입 이후면 진입가 사용
                    base_price = self.entry_price_at_step
                else:
                    # Break Even이 있으면 avg_entry_price와 비교하여 더 낮은 값 사용 (안전한 값)
                    if break_even is not None:
                        base_price = min(break_even, avg_entry_price)
                        if break_even != avg_entry_price:
                            self._log(f"[{self._el} 체크] Break Even: ${self.fmt_price(break_even)}, 평균진입가: ${self.fmt_price(avg_entry_price)} → 기준가: ${self.fmt_price(base_price)}")
                    else:
                        base_price = avg_entry_price

                # 임계값 가격 계산 (기준가 × (1 - 임계값%))
                threshold_price = base_price * (1 - self.uptrend_entry_profit_threshold / 100.0)

                # 먼저 전봉 종가가 임계값 이하인지 확인 (임계값 아래로 떨어졌을 때만 체크)
                if prev_close > threshold_price:
                    # print(f"[DEBUG {self._el} 체크] SHORT: 전봉 종가({prev_close:.4f}) > 임계값({threshold_price:.4f}) → 체크 스킵")  # 봉마감마다 출력 제거
                    return False

                # print(f"[DEBUG {self._el} 체크] 캔들 데이터 (완성된 캔들 2개):")  # 봉마감마다 출력 제거
                # print(f"  전전봉: open={prev_prev_open}, close={prev_prev_close}")
                # print(f"  전봉: open={prev_open}, close={prev_close}")
                # print(f"  평균진입가: {avg_entry_price}")
                # print(f"[DEBUG {self._el} 체크] 기준가: ${base_price:.4f}, 임계값: ${threshold_price:.4f}")

                # 조건 1: 전봉 마감가가 임계값 가격 이하
                condition1 = prev_close <= threshold_price

                # 조건 2: 전봉이 음봉 & 전봉이 전전봉 open 미만 (하락추세, 전전봉 음/양봉 모두 허용)
                # prev_prev_is_bullish = prev_prev_close > prev_prev_open  # 전전봉 양봉 조건 제거
                prev_is_bearish = prev_close < prev_open  # 전봉이 음봉
                prev_below_prev_prev_open = prev_close < prev_prev_open  # 전봉이 전전봉 open 미만
                condition2 = prev_is_bearish and prev_below_prev_prev_open  # 전전봉 양봉 조건 제거

                # print(f"[DEBUG {self._el} 체크] SHORT 조건 확인:")  # 봉마감마다 출력 제거
                # print(f"  조건1 (가격 임계값): prev_close={prev_close:.4f} <= threshold_price={threshold_price:.4f} = {condition1}")
                self._log(f"  조건2 (캔들패턴): 전봉음봉={prev_is_bearish}, 전봉<전전봉open={prev_below_prev_prev_open} = {condition2}")

                if condition1 and condition2:
                    self._log(f"[{self._el}] SHORT 조건 만족!")
                    self._log(f"  평균진입가: ${self.fmt_price(avg_entry_price)}, 전봉 종가: ${self.fmt_price(prev_close)}")
                    self._log(f"  임계값 가격: ${self.fmt_price(threshold_price)} (평균진입가 - {self.uptrend_entry_profit_threshold}%)")
                    self._log(f"  전전봉: open=${self.fmt_price(prev_prev_open)}, close=${self.fmt_price(prev_prev_close)}")
                    self._log(f"  전봉: open=${self.fmt_price(prev_open)}, close=${self.fmt_price(prev_close)} (음봉, 전전봉 open 하회)")
                    return True
                # else:
                    # print(f"[DEBUG {self._el} 체크] SHORT 조건 미충족 - condition1={condition1}, condition2={condition2}")  # 봉마감마다 출력 제거

            return False

        except Exception as e:
            self._log(f"[{self._el}] 조건 확인 오류: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _execute_initial_entry(self):
        """Step 0 초기 진입 (시장가)"""
        # 최소 주문 수량 및 최소 주문 금액 확인
        min_order_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.01'))
        min_order_value = float(self.symbol_info.get('lotSizeFilter', {}).get('minNotionalValue', '5'))

        if self.side_mode == "LONG":
            self._log(f"[DCA Step {self.current_step+1}] LONG 진입 (주거래 Qty: {self.entry_quantity})")
            self.execute_trade_signal.emit(self.symbol, "BUY", str(self.entry_quantity), False)

            # 헷지 주문: 최소 수량 AND 최소 금액 체크
            hedge_value = self.hedge_quantity * self.current_price if self.current_price else 0
            if self.hedge_quantity >= min_order_qty and (hedge_value >= min_order_value or self.current_price == 0):
                self._log(f"[DCA Step {self.current_step+1}] 헷지 SHORT 진입 (헷지 Qty: {self.hedge_quantity:.4f}, 금액: ${hedge_value:.2f})")
                self.execute_trade_signal.emit(self.symbol, "SELL", str(self.hedge_quantity), True)
            else:
                if self.hedge_quantity > 0:
                    if self.hedge_quantity < min_order_qty:
                        self._log(f"[DCA Step {self.current_step+1}] 헷지 수량({self.hedge_quantity:.4f})이 최소 주문 수량({min_order_qty}) 미만이므로 헷지 주문 건너뜀")
                    elif hedge_value < min_order_value:
                        self._log(f"[DCA Step {self.current_step+1}] 헷지 금액(${hedge_value:.2f})이 최소 주문 금액(${min_order_value}) 미만이므로 헷지 주문 건너뜀")

        elif self.side_mode == "SHORT":
            self._log(f"[DCA Step {self.current_step+1}] SHORT 진입 (주거래 Qty: {self.entry_quantity})")
            self.execute_trade_signal.emit(self.symbol, "SELL", str(self.entry_quantity), False)

            # 헷지 주문: 최소 수량 AND 최소 금액 체크
            hedge_value = self.hedge_quantity * self.current_price if self.current_price else 0
            if self.hedge_quantity >= min_order_qty and (hedge_value >= min_order_value or self.current_price == 0):
                self._log(f"[DCA Step {self.current_step+1}] 헷지 LONG 진입 (헷지 Qty: {self.hedge_quantity:.4f}, 금액: ${hedge_value:.2f})")
                self.execute_trade_signal.emit(self.symbol, "BUY", str(self.hedge_quantity), True)
            else:
                if self.hedge_quantity > 0:
                    if self.hedge_quantity < min_order_qty:
                        self._log(f"[DCA Step {self.current_step+1}] 헷지 수량({self.hedge_quantity:.4f})이 최소 주문 수량({min_order_qty}) 미만이므로 헷지 주문 건너뜀")
                    elif hedge_value < min_order_value:
                        self._log(f"[DCA Step {self.current_step+1}] 헷지 금액(${hedge_value:.2f})이 최소 주문 금액(${min_order_value}) 미만이므로 헷지 주문 건너뜀")

        self.last_trade_time = time.time() - 20  # 중복 실행 방지

    def _place_next_step_orders(self, position_data):
        """다음 단계 지정가 주문 생성 (Step 1)"""
        try:
            # 다음 단계가 없으면 종료
            if self.current_step + 1 >= self.total_steps:
                self._log("[DCA] 마지막 단계입니다. 더 이상 주문하지 않습니다.")
                return

            # 1. 현재 포지션 정보 조회
            pos_key = f"{self.symbol}_LONG" if self.side_mode == "LONG" else f"{self.symbol}_SHORT"
            pos_data = position_data.get(pos_key, {})

            avg_entry_price = float(pos_data.get('entry_price', pos_data.get('entry', 0)))

            if avg_entry_price == 0:
                self._log(f"[DCA] 평균 진입가를 가져올 수 없습니다. pos_data={pos_data}. 재시도 대기 중...")
                self.next_step_orders_placed = False  # 다음 틱에 재시도
                return

            # 2. 청산가 조회 (API 사용)
            liq_price = self._get_liquidation_price()

            if liq_price == 0:
                self._log("[DCA] 청산가를 가져올 수 없습니다. 재시도 대기 중...")
                self.next_step_orders_placed = False
                return

            self._log(f"[DCA] 평균진입가: ${avg_entry_price}, 청산가: ${liq_price}")

            # 3. 다음 단계 진입 간격 퍼센트 계산 (DCA 진입 간격 설정 사용)
            next_step = self.current_step + 1
            dca_interval_start = self.strategy_settings.get("DCA_INTERVAL_START_PERCENT", 40)
            dca_interval_end = self.strategy_settings.get("DCA_INTERVAL_END_PERCENT", 100)

            if self.total_steps > 1:
                interval_percent = dca_interval_start + ((dca_interval_end - dca_interval_start) / (self.total_steps - 1)) * next_step
            else:
                interval_percent = dca_interval_end

            # 4. 다음 단계 진입가 계산 기준 가격 결정
            # Step 0 이후(Step 1 주문 생성 시): 평균 진입가 사용 (시장가 체결이므로)
            # Step 1 이후: 마지막 진입 주문 가격 사용 (지정가 주문 가격)
            if self.current_step == 0 or self.last_step_entry_price is None:
                # Step 0 체결 후 Step 1 주문 생성 시: 평균 진입가 사용
                base_price_for_calculation = avg_entry_price
                self._log(f"[DCA] 기준 가격: 평균 진입가 ${self.fmt_price(avg_entry_price)} (Step {self.current_step} 체결 후)")
            else:
                # Step 1 이상 체결 후: 마지막 진입 주문 가격 사용
                base_price_for_calculation = self.last_step_entry_price
                self._log(f"[DCA] 기준 가격: 마지막 진입 주문 가격 ${self.fmt_price(self.last_step_entry_price)} (Step {self.current_step} 지정가)")

            # 다음 단계 진입가 계산
            next_entry_price = trading_utils.calculate_next_step_entry_price(base_price_for_calculation, liq_price, interval_percent)

            # 5. 가격 정밀도 조정
            tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
            price_precision = trading_utils.count_decimal_places(tick_size)
            next_entry_price_adjusted = trading_utils.adjust_price(next_entry_price, tick_size, price_precision)

            # 6. 청산가 안전장치 (다음 진입가가 청산가에 너무 가깝지 않도록)
            # 안전 마진: 청산가로부터 최소 N% 이상 떨어져야 함 (Settings에서 설정 가능)
            safety_margin_percent = self.main_liquidation_safety_margin

            if self.side_mode == "LONG":
                # LONG: 진입가가 청산가보다 낮으면 안됨 (청산가 + 0.5% 이상)
                safe_price_min = liq_price * (1 + safety_margin_percent / 100)
                safe_price = trading_utils.adjust_price(safe_price_min, tick_size, price_precision)

                if next_entry_price_adjusted < safe_price:
                    self._log(f"[DCA 안전장치] 진입가 ${self.fmt_price(next_entry_price_adjusted)}가 청산가 ${self.fmt_price(liq_price)}에 너무 가까움!")
                    self._log(f"[DCA 안전장치] 청산가와의 거리: {((next_entry_price_adjusted - liq_price) / liq_price * 100):.3f}% < {safety_margin_percent}%")
                    next_entry_price_adjusted = safe_price
                    self._log(f"[DCA 안전장치] 진입가를 청산가 + {safety_margin_percent}%로 조정: ${self.fmt_price(next_entry_price_adjusted)}")
            else:  # SHORT
                # SHORT: 진입가가 청산가보다 높으면 안됨 (청산가 - 0.5% 이하)
                safe_price_max = liq_price * (1 - safety_margin_percent / 100)
                safe_price = trading_utils.adjust_price(safe_price_max, tick_size, price_precision)

                if next_entry_price_adjusted > safe_price:
                    self._log(f"[DCA 안전장치] 진입가 ${self.fmt_price(next_entry_price_adjusted)}가 청산가 ${self.fmt_price(liq_price)}에 너무 가까움!")
                    self._log(f"[DCA 안전장치] 청산가와의 거리: {((liq_price - next_entry_price_adjusted) / liq_price * 100):.3f}% < {safety_margin_percent}%")
                    next_entry_price_adjusted = safe_price
                    self._log(f"[DCA 안전장치] 진입가를 청산가 - {safety_margin_percent}%로 조정: ${self.fmt_price(next_entry_price_adjusted)}")

            self._log(f"[DCA] Step {next_step} 진입가: ${self.fmt_price(next_entry_price_adjusted)} (진입간격%: {interval_percent:.2f}%, 청산가: ${self.fmt_price(liq_price)})")

            # 7. Step 수량
            if next_step < len(self.entry_qty_list):
                next_entry_qty = self.entry_qty_list[next_step]
            else:
                self._log(f"[DCA] Step {next_step} 수량 정보 없음. 중단.")
                return

            # 마지막 진입 주문 가격 저장 (다음 단계 계산에 사용)
            self.last_step_entry_price = next_entry_price_adjusted
            self._log(f"[DCA] 마지막 진입 주문 가격 저장: ${self.fmt_price(self.last_step_entry_price)}")

            # 8. 헷지 조건부 주문 설정 (가격 돌파 시 시장가 실행)
            if next_step < len(self.hedge_qty_list):
                total_hedge_qty = self.hedge_qty_list[next_step]

                # 헷지 분할 주문 계산 (기준 가격은 위에서 결정한 base_price_for_calculation 사용)
                hedge_orders = trading_utils.calculate_hedge_split_orders(
                    total_hedge_qty, base_price_for_calculation, next_entry_price_adjusted, num_splits=4, ratio=0.5
                )

                # 헷지 프로토콜: H4에 재진입 수량 추가
                if self.hedge_protocol_enabled and self.hedge_protocol_exited_qty > 0 and len(hedge_orders) == 4:
                    h4_price, h4_qty = hedge_orders[3]
                    h4_qty_with_reentry = self._handle_hedge_protocol_reentry_on_h4(h4_qty)
                    hedge_orders[3] = (h4_price, h4_qty_with_reentry)
                    self._log(f"[헷지 프로토콜] H4 수량 조정: {h4_qty:.4f} → {h4_qty_with_reentry:.4f} (재진입 +{self.hedge_protocol_exited_qty:.4f})")

                qty_step = float(self.symbol_info.get('lotSizeFilter', {}).get('qtyStep', '0.01'))
                qty_precision = trading_utils.count_decimal_places(qty_step)
                min_order_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.01'))

                # 헷지 트리거 가격 목록 초기화
                self.hedge_trigger_prices = []

                side = "BUY" if self.side_mode == "LONG" else "SELL"
                m_orders_data = []

                # 헷지 트리거 생성
                for i, (price, qty) in enumerate(hedge_orders):
                    # 가격 및 수량 조정
                    # 참고: 헷지 트리거는 base_price_for_calculation과 next_entry_price_adjusted 사이를 4등분
                    # next_entry_price_adjusted가 이미 청산가 안전장치를 통과했으므로 헷지 트리거도 자동으로 안전함
                    adj_price = trading_utils.adjust_price(price, tick_size, price_precision)

                    # 마지막 헷지는 다음 스텝 진입가보다 1틱 아래로 설정
                    # (다음 스텝 메인 주문이 체결된 후에만 마지막 헷지가 실행되도록)
                    is_last_hedge = (i == len(hedge_orders) - 1)
                    if is_last_hedge:
                        if self.side_mode == "LONG":
                            # LONG: 진입가보다 1틱 아래
                            adj_price = next_entry_price_adjusted - tick_size
                        else:
                            # SHORT: 진입가보다 1틱 위
                            adj_price = next_entry_price_adjusted + tick_size
                        adj_price = trading_utils.adjust_price(adj_price, tick_size, price_precision)
                        self._log(f"[DCA] 마지막 헷지 트리거 가격 조정: 다음 스텝 진입가 ± 1틱 = ${self.fmt_price(adj_price)}")

                    adj_qty = trading_utils.adjust_quantity(qty, qty_step, qty_precision, min_order_qty)

                    # 최소 주문 수량 체크 (수량 미달은 트리거 생성 자체를 스킵)
                    if adj_qty < min_order_qty:
                        self._log(f"[DCA] 헷지 트리거 {i+1} 수량({adj_qty})이 최소 주문 수량({min_order_qty}) 미만으로 스킵.")
                        continue

                    # (가격, 수량, 실행여부) 튜플로 저장
                    # 주문 금액 체크는 실행 시점에서 수행 (가격 변동 고려)
                    self.hedge_trigger_prices.append([adj_price, adj_qty, False])
                    self._log(f"[DCA] 헷지 트리거 {i+1}/4 설정: ${self.fmt_price(adj_price)} (수량: {adj_qty})")

                # NSO(Next Step Order): 다음 단계 메인 진입 지정가 주문
                nso_qty = trading_utils.adjust_quantity(next_entry_qty, qty_step, qty_precision, min_order_qty)

                if nso_qty >= min_order_qty:
                    self._log(f"[DCA] NSO 메인 진입 주문 (다음 Step 주문): {nso_qty} @ ${next_entry_price_adjusted}")
                    # 시그널 emit 전에 플래그 설정 (on_order_id_received 콜백이 ID를 수락하도록)
                    self.next_step_orders_placed = True
                    self.execute_limit_order_signal.emit(
                        self.symbol, side, str(nso_qty), str(next_entry_price_adjusted), False
                    )
                    # NSO 주문 ID는 on_order_id_received() 콜백에서 self.next_step_order_id에 저장됨
                    m_orders_data.append({
                        'price': next_entry_price_adjusted,
                        'qty': nso_qty,
                        'status': 'Waiting',
                        'slippage': 0
                    })
                else:
                    self._log(f"[DCA] NSO 수량({nso_qty})이 최소 주문 수량 미만으로 스킵.")
                    m_orders_data.append({
                        'price': next_entry_price_adjusted,
                        'qty': 0,
                        'status': 'Skipped',
                        'slippage': 0
                    })

                self.remaining_hedge_qty = total_hedge_qty
                self._log(f"[DCA] 총 {len(self.hedge_trigger_prices)}개 헷지 트리거 설정 완료. 가격 모니터링 시작.")

                # GUI에 헷지 트리거 업데이트 알림
                self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

                # NSO 주문 데이터 저장 (슬리피지 조정 시 마커 업데이트용)
                self.m_orders_data = m_orders_data

                # GUI에 NSO 주문 업데이트 알림
                self.m_orders_updated.emit(m_orders_data)
                self._log(f"[DCA] NSO 주문 업데이트 완료")

        except Exception as e:
            self._log(f"[DCA] 다음 단계 주문 생성 오류: {e}")
            import traceback
            traceback.print_exc()

    def _adjust_orders_for_slippage(self, slippage):
        """슬리피지에 따라 다음 단계 주문과 남은 헷지 트리거 조정

        [핵심] H 트리거와 NSO에 동일한 adjusted_slippage를 적용하여 가격 동기화 유지.
        NSO 안전 마진으로 슬리피지가 제한되면 H 트리거도 동일하게 제한됨.
        """
        try:
            self._log(f"[DCA 슬리피지] 주문 조정 시작: 슬리피지=${self.fmt_price(slippage)}")

            tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))

            # 1. NSO 안전 마진을 고려한 조정 슬리피지 계산 (H 트리거에도 동일 적용)
            adjusted_slippage = slippage

            if self.next_step_order_id and self.last_step_entry_price:
                self._log(f"[DCA 슬리피지] NSO 주문 조정 (주문 ID: {self.next_step_order_id})")
                main_liq_price = self._get_liquidation_price()

                if main_liq_price > 0:
                    current_order_price = self.last_step_entry_price
                    new_order_price = current_order_price + slippage

                    if self.side_mode == "LONG":
                        safe_price = main_liq_price + tick_size
                        if new_order_price < safe_price:
                            self._log(f"[DCA 슬리피지] ⚠️ 청산가 충돌 감지!")
                            self._log(f"[DCA 슬리피지]   슬리피지 적용 가격: ${self.fmt_price(new_order_price)}")
                            self._log(f"[DCA 슬리피지]   메인 청산가: ${self.fmt_price(main_liq_price)}")
                            self._log(f"[DCA 슬리피지]   안전 가격 (청산가+1틱): ${self.fmt_price(safe_price)}")

                            if abs(current_order_price - safe_price) < tick_size * 0.1:
                                self._log(f"[DCA 슬리피지]   현재 주문이 이미 안전 가격 위치 → 조정 안 함")
                                adjusted_slippage = 0
                            else:
                                adjusted_slippage = safe_price - current_order_price
                                self._log(f"[DCA 슬리피지]   안전 가격으로 조정: 슬리피지 ${self.fmt_price(slippage)} → ${self.fmt_price(adjusted_slippage)}")
                    else:  # SHORT
                        safe_price = main_liq_price - tick_size
                        if new_order_price > safe_price:
                            self._log(f"[DCA 슬리피지] ⚠️ 청산가 충돌 감지!")
                            self._log(f"[DCA 슬리피지]   슬리피지 적용 가격: ${self.fmt_price(new_order_price)}")
                            self._log(f"[DCA 슬리피지]   메인 청산가: ${self.fmt_price(main_liq_price)}")
                            self._log(f"[DCA 슬리피지]   안전 가격 (안전마진 적용): ${self.fmt_price(safe_price)}")

                            if abs(current_order_price - safe_price) < tick_size * 0.1:
                                self._log(f"[DCA 슬리피지]   현재 주문이 이미 안전 가격 위치 → 조정 안 함")
                                adjusted_slippage = 0
                            else:
                                adjusted_slippage = safe_price - current_order_price
                                self._log(f"[DCA 슬리피지]   안전 가격으로 조정: 슬리피지 ${self.fmt_price(slippage)} → ${self.fmt_price(adjusted_slippage)}")
                else:
                    self._log(f"[DCA 슬리피지] 청산가 조회 실패 - 원래 슬리피지 적용")

            # 조정할 슬리피지가 없으면 종료
            if abs(adjusted_slippage) < tick_size * 0.1:
                self._log(f"[DCA 슬리피지] 조정할 슬리피지 없음 (조정 스킵)")
                return

            # 2. 남은 헷지 트리거 가격 조정 (adjusted_slippage 적용 - NSO와 동기화)
            adjusted_count = 0
            for trigger in self.hedge_trigger_prices:
                trigger_price, qty, executed = trigger
                if not executed:
                    new_price = trigger_price + adjusted_slippage
                    trigger[0] = new_price
                    adjusted_count += 1
                    self._log(f"[DCA 슬리피지] 헷지 트리거 조정: ${self.fmt_price(trigger_price)} → ${self.fmt_price(new_price)}")

            if adjusted_count > 0:
                self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

            # 3. NSO 주문 가격 조정 (거래소 주문 수정)
            if self.next_step_order_id:
                self.adjust_next_step_order_signal.emit(self.next_step_order_id, adjusted_slippage)

                # last_step_entry_price 업데이트 (다음 슬리피지 계산 시 누적 적용 방지)
                self.last_step_entry_price += adjusted_slippage
                self._log(f"[DCA 슬리피지] 마지막 진입 주문 가격 업데이트: ${self.fmt_price(self.last_step_entry_price)}")

                # NSO 차트 마커 업데이트
                if self.m_orders_data and len(self.m_orders_data) >= 1:
                    self.m_orders_data[0]['price'] = self.last_step_entry_price
                    self.m_orders_updated.emit(self.m_orders_data)
                    self._log(f"[DCA 슬리피지] NSO 마커 업데이트: ${self.fmt_price(self.last_step_entry_price)}")

            # 실시간 상태 저장
            self._log(f"[DCA 상태] 슬리피지 조정 후 상태 저장 요청")
            self.request_save_state.emit()

            self._log(f"[DCA 슬리피지] 주문 조정 완료: {adjusted_count}개 헷지 트리거 + NSO 동기화 조정됨")

        except Exception as e:
            self._log(f"[DCA 슬리피지] 주문 조정 오류: {e}")
            import traceback
            traceback.print_exc()

    def _get_liquidation_price(self):
        """API를 통해 청산가 조회"""
        try:
            if not self.api_module:
                self._log("[DCA] API 모듈이 없습니다.")
                return 0

            # Bybit API로 포지션 정보 조회
            positions = self.api_module.get_initial_positions()

            self._log(f"[DCA] 포지션 정보 조회 결과: {positions}")

            if not positions:
                self._log("[DCA] 포지션 정보가 비어있습니다.")
                return 0

            for pos in positions:
                symbol = pos.get('symbol')
                pos_side = pos.get('positionSide', 'BOTH')

                self._log(f"[DCA] 포지션 확인 중: symbol={symbol}, side={pos_side}, 찾는 심볼={self.symbol}, 찾는 사이드={self.side_mode}")

                # 현재 심볼 및 사이드 매칭
                if symbol == self.symbol:
                    if (self.side_mode == "LONG" and pos_side == "LONG") or \
                       (self.side_mode == "SHORT" and pos_side == "SHORT"):
                        liq_price_str = pos.get('liqPrice', '0')
                        liq_price = float(liq_price_str) if liq_price_str else 0

                        # Bybit API에서 청산가를 못 가져온 경우 (빈 문자열 또는 0)
                        if liq_price == 0:
                            self._log(f"[DCA 오류] API에서 청산가를 조회할 수 없습니다.")
                            self._log(f"[DCA 오류] 격리 마진(Isolated Margin) 모드로 설정되어 있는지 확인하세요.")
                            self._log(f"[DCA 오류] Bybit 웹 거래소 → 설정 → Margin Mode → Isolated Margin 선택")
                            self._log(f"[DCA 오류] 또는 자동매매를 중지하고 재시작하여 마진 모드를 다시 설정하세요.")
                            return 0

                        self._log(f"[DCA] 청산가 반환: {liq_price}")
                        return liq_price

            self._log(f"[DCA] 일치하는 포지션을 찾지 못했습니다. (symbol={self.symbol}, side_mode={self.side_mode})")
            return 0

        except Exception as e:
            self._log(f"[DCA] 청산가 조회 오류: {e}")
            import traceback
            traceback.print_exc()
            return 0

    def _get_hedge_liquidation_price(self):
        """헷지 포지션의 청산가 조회"""
        try:
            if not self.api_module:
                self._log("[헷지 보호] API 모듈이 없습니다.")
                return 0

            # Bybit API로 포지션 정보 조회
            positions = self.api_module.get_initial_positions()

            if not positions:
                return 0

            # 헷지 포지션의 사이드 결정 (메인 포지션의 반대)
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"

            for pos in positions:
                symbol = pos.get('symbol')
                pos_side = pos.get('positionSide', 'BOTH')

                # 헷지 심볼 및 사이드 매칭
                if symbol == self.symbol and pos_side == hedge_side:
                    liq_price_str = pos.get('liqPrice', '0')
                    liq_price = float(liq_price_str) if liq_price_str else 0

                    if liq_price == 0:
                        return 0

                    return liq_price

            return 0

        except Exception as e:
            self._log(f"[헷지 보호] 헷지 청산가 조회 오류: {e}")
            return 0

    def _setup_emergency_exit_line(self):
        """헷지 체결 시 3단계 긴급 탈출 라인 설정 (헷지 체결마다 재계산)

        Break Even과 헷지 청산가 사이의 설정된 시작 지점(기본 50%)부터 3등분:
        - 시작 지점 = BE + (BE~청산가 거리 × 시작비율)
        - 1단계: 시작 지점 + 1/3
        - 2단계: 시작 지점 + 2/3
        - 3단계 (청산가): 헷지 전체 청산 + 메인 시장가 청산

        헷지가 추가로 체결되면 청산가와 BE가 변경되므로 라인을 재계산합니다.
        """
        try:
            # 긴급 탈출이 실행되었으면 스킵
            if self.emergency_exit_triggered:
                return

            # 역방향진입 임계값이 없으면 스킵
            if self.uptrend_threshold_price is None:
                return

            # 청산가 안전망 주문 설정
            self._log("[헷지 보호] 청산가 안전망 주문 설정 시도...")

            # 헷지 청산가 조회 (API 호출)
            hedge_liq_price = self._get_hedge_liquidation_price()

            if hedge_liq_price == 0:
                self._log("[헷지 보호] 헷지 청산가 조회 실패 - 안전망 설정 안 함")
                return

            # Break Even 가격 계산 (GUI 표시용)
            break_even_price = self.calculate_break_even(self.current_position_data)

            if break_even_price is None:
                self._log("[헷지 보호] 완전 헷지 상태 (Net Position ≈ 0)")
                break_even_price = 0

            if break_even_price == 0:
                self._log("[헷지 보호] Break Even 가격 계산 실패")

            # GUI에 헷지 청산가 및 Break Even 전송 (Insight 탭 표시용)
            if break_even_price > 0:
                self.hedge_liquidation_warning.emit(hedge_liq_price, break_even_price, "SAFETY_NET_SET")
                self._log(f"[헷지 보호] Break Even: ${self.fmt_price(break_even_price)}")
                self._log(f"[헷지 보호] 헷지 청산가: ${self.fmt_price(hedge_liq_price)}")

            # 청산가 안전마진을 적용한 안전망 주문 설정
            self._place_hedge_safety_order(hedge_liq_price)

        except Exception as e:
            self._log(f"[헷지 보호] 긴급 탈출 라인 설정 오류: {e}")
            import traceback
            traceback.print_exc()

    def _check_emergency_exit_line_breach(self, current_price, position_data):
        """3단계 긴급 탈출 라인 돌파 감지 (매 틱마다 호출, API 호출 없음)

        Args:
            current_price: 현재가
            position_data: 포지션 데이터
        """
        try:
            # 긴급 탈출 라인이 없으면 스킵
            if len(self.hedge_emergency_exit_lines) == 0:
                return

            # 헷지 포지션 수량 확인
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"
            pos_key_hedge = f"{self.symbol}_{hedge_side}"
            hedge_position = self.current_position_data.get(pos_key_hedge, {})
            hedge_qty = abs(float(hedge_position.get('amount', 0)))

            if hedge_qty <= 0:
                return  # 헷지 포지션 없으면 체크 안 함

            # 각 단계 라인 체크 (순서대로)
            for stage_idx, line_data in enumerate(self.hedge_emergency_exit_lines):
                line_price = line_data[0]
                executed = line_data[1]

                # 이미 실행된 단계는 스킵
                if executed:
                    continue

                # 돌파 감지
                line_crossed = False

                if self.side_mode == "LONG":
                    # LONG: 가격이 라인 위로 돌파
                    if current_price >= line_price:
                        line_crossed = True
                else:
                    # SHORT: 가격이 라인 아래로 돌파
                    if current_price <= line_price:
                        line_crossed = True

                if line_crossed:
                    stage_num = stage_idx + 1
                    self._log(f"[헷지 보호] 🚨 {stage_num}단계 긴급 탈출 라인 돌파!")
                    self._log(f"[헷지 보호] 현재가: ${self.fmt_price(current_price)}")
                    self._log(f"[헷지 보호] {stage_num}단계 라인: ${self.fmt_price(line_price)}")

                    # 단계별 액션 실행
                    if stage_num == 1:
                        # 1단계: 헷지 1/3 청산
                        self._execute_stage1_exit(hedge_qty, current_price)
                    elif stage_num == 2:
                        # 2단계: 헷지 추가 1/3 청산 (누적 2/3)
                        self._execute_stage2_exit(hedge_qty, current_price)
                    elif stage_num == 3:
                        # 3단계: 헷지 전체 청산 + 메인 트레일링
                        self._execute_stage3_exit(hedge_qty, current_price, position_data)

                    # 실행 완료 표시
                    self.hedge_emergency_exit_lines[stage_idx][1] = True

                    # 한 번에 하나의 단계만 실행
                    break

        except Exception as e:
            self._log(f"[헷지 보호] 라인 돌파 감지 오류: {e}")
            import traceback
            traceback.print_exc()

    def _execute_emergency_exit(self, hedge_qty, current_price, position_data):
        """긴급 탈출 시스템 실행

        1. 헷지 포지션 전체 청산
        2. 메인 포지션에 트레일링 스탑 설정
        3. DCA 중단

        Args:
            hedge_qty: 현재 헷지 수량
            current_price: 현재가
            position_data: 포지션 데이터
        """
        try:
            # 중복 실행 방지
            if self.emergency_exit_triggered:
                return

            self.emergency_exit_triggered = True

            self._log(f"[헷지 보호] ========================================")
            self._log(f"[헷지 보호] 긴급 탈출 시스템 실행 중...")
            self._log(f"[헷지 보호] ========================================")

            # 1. 헷지 포지션 전체 청산
            hedge_close_side = "BUY" if self.side_mode == "LONG" else "SELL"
            self._log(f"[헷지 보호] [1/3] 헷지 전체 청산: {hedge_close_side} {hedge_qty}")
            self.execute_trade_signal.emit(self.symbol, hedge_close_side, str(hedge_qty), True)

            # 2. 메인 포지션 수량 확인
            pos_key_main = f"{self.symbol}_{self.side_mode}"
            main_position = self.current_position_data.get(pos_key_main, {})
            main_qty = abs(float(main_position.get('amount', 0)))

            if main_qty > 0:
                # 메인 포지션에 트레일링 스탑 설정
                self._log(f"[헷지 보호] [2/3] 메인 포지션 트레일링 스탑 설정")

                # 활성화 가격 계산 (현재가의 99.5%)
                activation_price = current_price * 0.995 if self.side_mode == "LONG" else current_price * 1.005

                # 콜백 비율 (0.5%)
                callback_rate = self.strategy_settings.get("TRAILING_CALLBACK_RATE", 0.5)

                # 트레일링 스탑 방향 (메인 포지션 청산)
                trailing_side = "SELL" if self.side_mode == "LONG" else "BUY"

                self._log(f"[헷지 보호] 트레일링 스탑: {trailing_side} {main_qty}, 활성화가: ${self.fmt_price(activation_price)}, 콜백: {callback_rate}%")

                # GUI에 트레일링 스탑 요청
                self.request_trailing_stop.emit(
                    self.symbol,
                    trailing_side,
                    str(main_qty),
                    str(activation_price),
                    str(callback_rate)
                )
            else:
                self._log(f"[헷지 보호] [2/3] 메인 포지션 없음 - 트레일링 스탑 생략")

            # 3. DCA 중단
            self._log(f"[헷지 보호] [3/3] DCA 자동매매 중단")
            self.is_running = False

            # GUI에 긴급 탈출 완료 알림
            self.hedge_liquidation_warning.emit(0, current_price, "EMERGENCY_EXIT_DONE")

            self._log(f"[헷지 보호] ========================================")
            self._log(f"[헷지 보호] 긴급 탈출 시스템 실행 완료!")
            self._log(f"[헷지 보호] - 헷지: 전체 청산")
            self._log(f"[헷지 보호] - 메인: 트레일링 스탑 설정")
            self._log(f"[헷지 보호] - DCA: 중단됨")
            self._log(f"[헷지 보호] ========================================")

        except Exception as e:
            self._log(f"[헷지 보호] 긴급 탈출 오류: {e}")
            import traceback
            traceback.print_exc()

    def _execute_stage1_exit(self, hedge_qty, current_price):
        """1단계 긴급 탈출: 헷지 1/3 청산 + 메인 1/3 시장가 청산

        Args:
            hedge_qty: 현재 헷지 수량
            current_price: 현재가
        """
        try:
            self._log(f"[헷지 보호 1단계] ========================================")
            self._log(f"[헷지 보호 1단계] 1단계 긴급 탈출 발동!")
            self._log(f"[헷지 보호 1단계] ========================================")

            # 1. 헷지 1/3 청산
            hedge_reduce_qty = hedge_qty / 3

            # 최소 주문 수량/금액 확인
            min_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.001'))
            min_notional = float(self.symbol_info.get('lotSizeFilter', {}).get('minNotionalValue', '5'))
            effective_min_qty = max(min_qty, min_notional / current_price)

            # 최소 수량 미달 시 조정
            if hedge_reduce_qty < effective_min_qty:
                hedge_reduce_qty = effective_min_qty
                self._log(f"[헷지 보호 1단계] 헷지 청산 수량을 최소값으로 조정: {hedge_reduce_qty}")

            # 청산 방향 결정 (헷지 포지션의 반대)
            hedge_close_side = "BUY" if self.side_mode == "LONG" else "SELL"

            self._log(f"[헷지 보호 1단계] [1/2] 헷지 1/3 청산: {hedge_close_side} {hedge_reduce_qty} (원본: {hedge_qty})")
            self.execute_trade_signal.emit(self.symbol, hedge_close_side, str(hedge_reduce_qty), True)

            # 2. 메인 포지션 1/3 시장가 청산
            pos_key_main = f"{self.symbol}_{self.side_mode}"
            main_position = self.current_position_data.get(pos_key_main, {})
            main_qty = abs(float(main_position.get('amount', 0)))

            if main_qty > 0:
                main_reduce_qty = main_qty / 3

                # 최소 수량 확인
                if main_reduce_qty < effective_min_qty:
                    main_reduce_qty = effective_min_qty
                    self._log(f"[헷지 보호 1단계] 메인 청산 수량을 최소값으로 조정: {main_reduce_qty}")

                # 메인 청산 방향 (메인 포지션의 반대)
                main_close_side = "SELL" if self.side_mode == "LONG" else "BUY"

                self._log(f"[헷지 보호 1단계] [2/2] 메인 1/3 시장가 청산: {main_close_side} {main_reduce_qty} (원본: {main_qty})")

                # 시장가 청산 실행
                self.execute_trade_signal.emit(self.symbol, main_close_side, str(main_reduce_qty), True)
            else:
                self._log(f"[헷지 보호 1단계] [2/2] 메인 포지션 없음 - 청산 생략")

            # GUI 알림
            self.hedge_liquidation_warning.emit(0, current_price, "STAGE1_EXECUTED")

            self._log(f"[헷지 보호 1단계] ========================================")
            self._log(f"[헷지 보호 1단계] 1단계 긴급 탈출 완료!")
            self._log(f"[헷지 보호 1단계] ========================================")

        except Exception as e:
            self._log(f"[헷지 보호 1단계] 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    def _execute_stage2_exit(self, hedge_qty, current_price):
        """2단계 긴급 탈출: 헷지 추가 1/3 청산 + 메인 추가 1/3 시장가 청산 (누적 2/3)

        Args:
            hedge_qty: 현재 헷지 수량
            current_price: 현재가
        """
        try:
            self._log(f"[헷지 보호 2단계] ========================================")
            self._log(f"[헷지 보호 2단계] 2단계 긴급 탈출 발동!")
            self._log(f"[헷지 보호 2단계] ========================================")

            # 1. 헷지 추가 1/3 청산 (현재 수량의 1/2 = 원래의 1/3)
            # 1단계에서 1/3 청산했으므로 남은 2/3 중에서 1/2 청산
            hedge_reduce_qty = hedge_qty / 2

            # 최소 주문 수량/금액 확인
            min_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.001'))
            min_notional = float(self.symbol_info.get('lotSizeFilter', {}).get('minNotionalValue', '5'))
            effective_min_qty = max(min_qty, min_notional / current_price)

            # 최소 수량 미달 시 조정
            if hedge_reduce_qty < effective_min_qty:
                hedge_reduce_qty = effective_min_qty
                self._log(f"[헷지 보호 2단계] 헷지 청산 수량을 최소값으로 조정: {hedge_reduce_qty}")

            # 청산 방향 결정 (헷지 포지션의 반대)
            hedge_close_side = "BUY" if self.side_mode == "LONG" else "SELL"

            self._log(f"[헷지 보호 2단계] [1/2] 헷지 추가 1/3 청산 (누적 2/3): {hedge_close_side} {hedge_reduce_qty} (현재: {hedge_qty})")
            self.execute_trade_signal.emit(self.symbol, hedge_close_side, str(hedge_reduce_qty), True)

            # 2. 메인 포지션 추가 1/3 시장가 청산
            pos_key_main = f"{self.symbol}_{self.side_mode}"
            main_position = self.current_position_data.get(pos_key_main, {})
            main_qty = abs(float(main_position.get('amount', 0)))

            if main_qty > 0:
                # 메인도 현재 수량의 1/2 청산 (1단계에서 1/3 이미 청산됨)
                main_reduce_qty = main_qty / 2

                # 최소 수량 확인
                if main_reduce_qty < effective_min_qty:
                    main_reduce_qty = effective_min_qty
                    self._log(f"[헷지 보호 2단계] 메인 청산 수량을 최소값으로 조정: {main_reduce_qty}")

                # 메인 청산 방향
                main_close_side = "SELL" if self.side_mode == "LONG" else "BUY"

                self._log(f"[헷지 보호 2단계] [2/2] 메인 추가 1/3 시장가 청산 (누적 2/3): {main_close_side} {main_reduce_qty} (현재: {main_qty})")

                # 시장가 청산 실행
                self.execute_trade_signal.emit(self.symbol, main_close_side, str(main_reduce_qty), True)
            else:
                self._log(f"[헷지 보호 2단계] [2/2] 메인 포지션 없음 - 청산 생략")

            # GUI 알림
            self.hedge_liquidation_warning.emit(0, current_price, "STAGE2_EXECUTED")

            self._log(f"[헷지 보호 2단계] ========================================")
            self._log(f"[헷지 보호 2단계] 2단계 긴급 탈출 완료!")
            self._log(f"[헷지 보호 2단계] ========================================")

        except Exception as e:
            self._log(f"[헷지 보호 2단계] 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    def _execute_stage3_exit(self, hedge_qty, current_price, position_data):
        """3단계 긴급 탈출: 헷지 나머지 전체 청산 + 메인 나머지 전체 시장가 청산 + DCA 중단

        Args:
            hedge_qty: 현재 헷지 수량
            current_price: 현재가
            position_data: 포지션 데이터
        """
        try:
            # 최종 긴급 탈출 플래그 설정
            self.emergency_exit_triggered = True

            self._log(f"[헷지 보호 3단계] ========================================")
            self._log(f"[헷지 보호 3단계] 최종 긴급 탈출 시스템 발동!")
            self._log(f"[헷지 보호 3단계] ========================================")

            # 1. 남은 헷지 전체 청산
            hedge_close_side = "BUY" if self.side_mode == "LONG" else "SELL"
            self._log(f"[헷지 보호 3단계] [1/3] 남은 헷지 전체 청산: {hedge_close_side} {hedge_qty}")
            self.execute_trade_signal.emit(self.symbol, hedge_close_side, str(hedge_qty), True)

            # 2. 메인 포지션 나머지 전체 시장가 청산
            pos_key_main = f"{self.symbol}_{self.side_mode}"
            main_position = self.current_position_data.get(pos_key_main, {})
            main_qty = abs(float(main_position.get('amount', 0)))

            if main_qty > 0:
                # 메인 청산 방향
                main_close_side = "SELL" if self.side_mode == "LONG" else "BUY"

                self._log(f"[헷지 보호 3단계] [2/3] 메인 나머지 전체 시장가 청산: {main_close_side} {main_qty}")

                # 시장가 청산 실행
                self.execute_trade_signal.emit(self.symbol, main_close_side, str(main_qty), True)
            else:
                self._log(f"[헷지 보호 3단계] [2/3] 메인 포지션 없음 - 청산 생략")

            # 3. DCA 중단
            self._log(f"[헷지 보호 3단계] [3/3] DCA 자동매매 중단")
            self.is_running = False

            # GUI 알림
            self.hedge_liquidation_warning.emit(0, current_price, "STAGE3_EXECUTED")

            self._log(f"[헷지 보호 3단계] ========================================")
            self._log(f"[헷지 보호 3단계] 최종 긴급 탈출 완료!")
            self._log(f"[헷지 보호 3단계] - 헷지: 전체 청산")
            self._log(f"[헷지 보호 3단계] - 메인: 전체 시장가 청산")
            self._log(f"[헷지 보호 3단계] - DCA: 중단됨")
            self._log(f"[헷지 보호 3단계] ========================================")

        except Exception as e:
            self._log(f"[헷지 보호 3단계] 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    def _set_profit_target_trigger(self):
        """상승 중 추가진입 직후 익절 트리거 설정"""
        try:
            # 현재 Step의 익절 비율 가져오기
            if self.current_step >= len(self.profit_target_ratios):
                self._log(f"[익절] Step {self.current_step+1}의 익절 비율 정보 없음.")
                return

            profit_ratio = self.profit_target_ratios[self.current_step]

            # 포지션 정보에서 평균 진입가 조회 필요 (다음 틱에서 업데이트될 예정)
            # 일단 여기서는 설정만 하고, 다음 틱에서 평균 진입가를 받아 익절가 계산
            self._log(f"[익절] Step {self.current_step+1} 익절 비율 설정: {profit_ratio}%")

            # 익절가 계산은 다음 틱에서 평균 진입가를 받은 후 수행
            # 여기서는 플래그만 초기화
            self.profit_target_crossed = False

        except Exception as e:
            self._log(f"[익절] 트리거 설정 오류: {e}")
            import traceback
            traceback.print_exc()

    def _monitor_profit_target(self, current_price, position_data):
        """익절 트리거 모니터링 (Trailing Stop 방식)"""
        try:
            if self.entry_price_at_step is None: return
            if self.profit_base_price is None: return
            if self.high_price_since_entry is None or self.low_price_since_entry is None: return

            # profit_base_price 재계산 (체결 시점에 포지션 데이터 미갱신 대응)
            if self._profit_base_needs_recalc and position_data:
                pos_key_main = f"{self.symbol}_{self.side_mode}"
                main_position = position_data.get(pos_key_main, {})
                new_main_entry = float(main_position.get('entry_price', main_position.get('entry', 0)))
                new_main_qty = abs(float(main_position.get('amount', 0)))

                if new_main_entry > 0 and new_main_qty > 0 and abs(new_main_entry - self.profit_base_price) > 0.0001:
                    old_base = self.profit_base_price

                    # 헷지 포지션 확인 후 BE 계산
                    pos_key_hedge = f"{self.symbol}_{'SHORT' if self.side_mode == 'LONG' else 'LONG'}"
                    hedge_position = position_data.get(pos_key_hedge, {})
                    hedge_qty = abs(float(hedge_position.get('amount', 0)))
                    hedge_entry = float(hedge_position.get('entry_price', hedge_position.get('entry', 0)))

                    if hedge_qty > 0 and hedge_entry > 0:
                        if self.side_mode == "LONG":
                            num = new_main_qty * new_main_entry - hedge_qty * hedge_entry
                            den = new_main_qty - hedge_qty
                        else:
                            num = hedge_qty * hedge_entry - new_main_qty * new_main_entry
                            den = hedge_qty - new_main_qty
                        if abs(den) >= 0.0001:
                            be = num / den
                            if be > 0:
                                self.profit_base_price = max(be, new_main_entry) if self.side_mode == "LONG" else min(be, new_main_entry)
                            else:
                                self.profit_base_price = new_main_entry
                        else:
                            self.profit_base_price = new_main_entry
                    else:
                        self.profit_base_price = new_main_entry

                    self._log(f"[익절] 기준가 재계산: ${self.fmt_price(old_base)} → ${self.fmt_price(self.profit_base_price)} (포지션 데이터 갱신 반영)")
                    self._profit_base_needs_recalc = False

            # [수정] 인덱스 오류 방지
            if not self.profit_target_ratios: return
            # 현재 단계가 리스트 길이보다 크면 마지막 비율 사용
            ratio_index = min(self.current_step, len(self.profit_target_ratios) - 1)
            profit_ratio = self.profit_target_ratios[ratio_index]

            if self.is_profit_taking_in_progress: return

            # 2. 최고가/최저가 갱신
            if current_price > self.high_price_since_entry:
                self.high_price_since_entry = current_price
            if current_price < self.low_price_since_entry:
                self.low_price_since_entry = current_price

            # 3. 트레일링 스탑 가격 계산
            ratio_decimal = profit_ratio / 100.0
            dynamic_stop_price = 0.0

            if self.side_mode == "LONG":
                spread = self.high_price_since_entry - self.profit_base_price
                if spread > 0:
                    retracement = spread * ratio_decimal
                    dynamic_stop_price = self.high_price_since_entry - retracement
                else:
                    dynamic_stop_price = self.profit_base_price # 수익 구간 아니면 본전 방어

            elif self.side_mode == "SHORT":
                spread = self.profit_base_price - self.low_price_since_entry
                if spread > 0:
                    retracement = spread * ratio_decimal
                    dynamic_stop_price = self.low_price_since_entry + retracement
                else:
                    dynamic_stop_price = self.profit_base_price

            # 4. GUI 업데이트 (0.5초 간격)
            current_time = time.time()
            if self.profit_target_price is None or (current_time - self.last_profit_target_update_time >= 0.5):
                if self.profit_target_price is None or abs(dynamic_stop_price - self.profit_target_price) > 0.0001:
                    self.profit_target_price = dynamic_stop_price
                    self.last_profit_target_update_time = current_time
                    self.profit_target_updated.emit(self.profit_target_price, self.current_step)

            # 5. 청산 조건 확인
            triggered = False
            if self.side_mode == "LONG":
                if current_price <= dynamic_stop_price:
                    # [안전장치] 최소한 기준가(본전) 이상일 때만 익절 (손실 마감 방지)
                    # 단, 헷지 수익으로 커버되는 경우는 Break Even이 기준가이므로 안전함
                    if current_price >= self.profit_base_price:
                        triggered = True
                        self._log(f"[익절] Trailing Stop 발동! (High ${self.high_price_since_entry} -> Now ${current_price} <= Stop ${dynamic_stop_price})")

            elif self.side_mode == "SHORT":
                if current_price >= dynamic_stop_price:
                    if current_price <= self.profit_base_price:
                        triggered = True
                        self._log(f"[익절] Trailing Stop 발동! (Low ${self.low_price_since_entry} -> Now ${current_price} >= Stop ${dynamic_stop_price})")

            if triggered:
                self._execute_profit_taking()

        except Exception as e:
            self._log(f"[익절] 모니터링 오류: {e}")
            import traceback
            traceback.print_exc()

    def _calculate_and_emit_profit_target(self):
        """역방향진입 직후 익절가를 계산 (트레일링 스탑 기준가 설정)"""
        try:
            # 역방향진입 체결가 확인
            if self.entry_price_at_step is None or self.entry_price_at_step == 0:
                self._log(f"[{self._el}] 진입가 없음 - 익절가 계산 불가")
                return

            # Break Even 가격 계산 (기존 로직 유지)
            break_even_price = None
            pos_key_main = f"{self.symbol}_{self.side_mode}"
            pos_key_hedge = f"{self.symbol}_{'SHORT' if self.side_mode == 'LONG' else 'LONG'}"

            main_position = self.current_position_data.get(pos_key_main, {})
            hedge_position = self.current_position_data.get(pos_key_hedge, {})

            main_qty = abs(float(main_position.get('amount', 0)))
            main_entry = float(main_position.get('entry_price', main_position.get('entry', 0)))
            hedge_qty = abs(float(hedge_position.get('amount', 0)))
            hedge_entry = float(hedge_position.get('entry_price', hedge_position.get('entry', 0)))

            # Break Even 계산 가능 여부 확인
            if main_qty > 0 and hedge_qty > 0 and main_entry > 0 and hedge_entry > 0:
                # Break Even 계산
                if self.side_mode == "LONG":
                    numerator = main_qty * main_entry - hedge_qty * hedge_entry
                    denominator = main_qty - hedge_qty
                else:
                    numerator = hedge_qty * hedge_entry - main_qty * main_entry
                    denominator = hedge_qty - main_qty

                if abs(denominator) >= 0.0001:
                    break_even_price = numerator / denominator
                    if break_even_price > 0:
                        self._log(f"[{self._el}] Break Even 계산: ${self.fmt_price(break_even_price)} (메인: {main_qty}@${self.fmt_price(main_entry)}, 헷지: {hedge_qty}@${self.fmt_price(hedge_entry)})")
                    else:
                        self._log(f"[{self._el}] Break Even 계산 실패: 음수 값")
                        break_even_price = None
                else:
                    self._log(f"[{self._el}] Break Even 계산 불가: 수량 상쇄됨")
            else:
                self._log(f"[{self._el}] Break Even 계산 불가: 포지션 데이터 부족")
                self._profit_base_needs_recalc = True

            # 익절가 기준 가격(Base Price) 결정
            # [수정] 헷지 포지션이 없으면 메인 포지션 평균 진입가를 기준으로 사용
            if break_even_price is not None and break_even_price > 0:
                if self.side_mode == "LONG":
                    base_price = max(break_even_price, main_entry)
                else:  # SHORT
                    base_price = min(break_even_price, main_entry)
                self._log(f"[{self._el}] 트레일링 스탑 기준가: ${self.fmt_price(base_price)} (Break Even 고려)")
            elif main_entry > 0:
                # 헷지 포지션이 없으면 메인 평균 진입가 사용
                base_price = main_entry
                self._log(f"[{self._el}] 트레일링 스탑 기준가: ${self.fmt_price(base_price)} (메인 평균 진입가, 헷지 없음)")
            else:
                # 메인 포지션 정보도 없으면 역방향진입 체결가 사용 (fallback)
                base_price = self.entry_price_at_step
                self._log(f"[{self._el}] 트레일링 스탑 기준가: {self._el} 체결가 ${self.fmt_price(base_price)} (포지션 데이터 없음)")

            # [수정됨] 기준가 저장 및 초기화
            self.profit_base_price = base_price
            
            # 트레일링 스탑은 _monitor_profit_target에서 실시간으로 계산되므로
            # 초기값은 None으로 설정하여 첫 틱에 계산을 유도합니다.
            self.profit_target_price = None 
            self.last_profit_target_update_time = 0 

            # [버그 수정] None인 값을 포맷팅하려다 발생하는 에러 방지
            self._log(f"[{self._el}] 익절 시스템 가동 준비 완료 (기준가: ${self.fmt_price(self.profit_base_price) if self.profit_base_price else 'N/A'})")
            self._log(f"[{self._el}] - 메인 포지션: {main_qty} @ ${self.fmt_price(main_entry) if main_entry else 'N/A'}")
            self._log(f"[{self._el}] - 헷지 포지션: {hedge_qty} @ ${self.fmt_price(hedge_entry) if hedge_entry else 'N/A'}")

        except Exception as e:
            self._log(f"[{self._el}] 익절가 계산 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _execute_profit_taking(self):
        """익절 발동: 전체 포지션 청산 및 자동매매 재시작"""
        try:
            # 이미 익절 실행 중이면 중복 실행 방지
            if self.is_profit_taking_in_progress:
                self._log("[익절] 이미 익절 실행 중입니다. 중복 실행 방지.")
                return

            self._log("[익절] ========================================")
            self._log("[익절] 익절 트리거 발동! 전체 청산 시작...")
            self._log("[익절] ========================================")

            # 익절 실행 중 플래그 설정 (중복 실행 방지)
            self.is_profit_taking_in_progress = True

            # 1. GUI에 전체 청산 및 재시작 요청
            self.profit_taking_request.emit()

            # 2. DCA 상태 초기화
            self.current_step = 0
            self.initial_entry_done = False
            self.next_step_orders_placed = False
            self.entry_price_at_step = None
            self.is_uptrend_entry = False
            self.uptrend_entry_in_progress = False  # 역방향진입 중복 방지 플래그 리셋
            self.uptrend_entry_count = 0  # 역방향진입 횟수 리셋
            self.profit_target_price = None
            self.profit_base_price = None
            self._profit_base_needs_recalc = False
            self.high_price_since_entry = None
            self.low_price_since_entry = None
            self.last_profit_target_update_time = 0
            self.next_step_order_id = None
            self.last_step_entry_price = None
            self.m_orders_data = []
            self.hedge_trigger_prices = []
            self.remaining_hedge_qty = 0
            self.pending_hedge_orders = {}
            self.hedge_filled_need_threshold_recalc = False
            self.step_filled_need_threshold_recalc = False
            self.uptrend_threshold_price = None  # 임계값 초기화
            self.uptrend_threshold_price_2 = None

            self._log("[익절] DCA 상태 초기화 완료")
            self._log("[익절] GUI에 전체 청산 및 자동매매 재시작 요청 전송")

            # 3. 상태 저장 (초기화된 상태로 저장 → 삭제 목적)
            self.request_save_state.emit()

        except Exception as e:
            self._log(f"[익절] 청산 및 재시작 오류: {e}")
            import traceback
            traceback.print_exc()

    def _place_final_step_protection(self):
        """최종 단계 (Step 9) 손실 방지: Stop Loss + Trailing Stop 주문"""
        try:
            self._log("[최종단계] ========================================")
            self._log("[최종단계] 손실 방지 로직 시작...")
            self._log("[최종단계] ========================================")

            # 1. 청산가 조회
            liq_price = self._get_liquidation_price()
            if liq_price == 0:
                self._log("[최종단계] 청산가를 가져올 수 없습니다. 재시도 필요.")
                return

            # 2. 평균 진입가 조회 (API 사용)
            positions = self.api_module.get_initial_positions()
            avg_entry_price = 0

            for pos in positions:
                symbol = pos.get('symbol')
                pos_side = pos.get('positionSide', 'BOTH')

                if symbol == self.symbol:
                    if (self.side_mode == "LONG" and pos_side == "LONG") or \
                       (self.side_mode == "SHORT" and pos_side == "SHORT"):
                        avg_entry_price = float(pos.get('entryPrice', '0'))
                        break

            if avg_entry_price == 0:
                self._log("[최종단계] 평균 진입가를 가져올 수 없습니다. 재시도 필요.")
                return

            # 3. Stop Loss 가격 계산
            # 공식: stop_loss_price = avg_entry_price - (avg_entry_price - liq_price) * stop_loss_ratio
            stop_loss_ratio = self.strategy_settings.get("STOP_LOSS_RATIO", 0.99)
            stop_loss_price = avg_entry_price - (avg_entry_price - liq_price) * stop_loss_ratio

            # 가격 정밀도 조정
            tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
            price_precision = trading_utils.count_decimal_places(tick_size)
            stop_loss_price_adjusted = trading_utils.adjust_price(stop_loss_price, tick_size, price_precision)

            self._log(f"[최종단계] 평균진입가: ${self.fmt_price(avg_entry_price)}")
            self._log(f"[최종단계] 청산가: ${self.fmt_price(liq_price)}")
            self._log(f"[최종단계] Stop Loss 가격: ${stop_loss_price_adjusted}")

            # 4. 주 포지션 수량 조회
            main_position_qty = sum(float(q) for q in self.entry_qty_list[:self.current_step + 1])

            # 5. 헷지 포지션 수량 조회
            hedge_position_qty = sum(float(q) for q in self.hedge_qty_list[:self.current_step + 1])

            self._log(f"[최종단계] 주 포지션 수량: {main_position_qty}")
            self._log(f"[최종단계] 헷지 포지션 수량: {hedge_position_qty}")

            # 6. Stop Loss 주문 (주 포지션)
            stop_loss_side = "SELL" if self.side_mode == "LONG" else "BUY"
            self._log(f"[최종단계] Stop Loss 주문: {stop_loss_side} {main_position_qty} @ ${stop_loss_price_adjusted}")
            self.request_stop_loss.emit(
                self.symbol,
                stop_loss_side,
                str(main_position_qty),
                str(stop_loss_price_adjusted)
            )

            # 7. Trailing Stop 주문 (헷지 포지션)
            trailing_stop_side = "BUY" if self.side_mode == "LONG" else "SELL"  # 헷지 포지션은 반대 방향
            trailing_callback_rate = str(self.strategy_settings.get("TRAILING_CALLBACK_RATE", 0.5))  # 설정값 사용
            self._log(f"[최종단계] Trailing Stop 주문: {trailing_stop_side} {hedge_position_qty} @ Activation=${stop_loss_price_adjusted}, Callback={trailing_callback_rate}%")
            self.request_trailing_stop.emit(
                self.symbol,
                trailing_stop_side,
                str(hedge_position_qty),
                str(stop_loss_price_adjusted),
                trailing_callback_rate
            )

            # 8. 주문 완료 플래그 설정
            self.final_step_protection_placed = True
            self.monitoring_final_step_closure = True

            self._log("[최종단계] Stop Loss 및 Trailing Stop 주문 완료")
            self._log("[최종단계] 포지션 청산 모니터링 시작")

            # 9. 상태 저장
            self.request_save_state.emit()

        except Exception as e:
            self._log(f"[최종단계] 손실 방지 주문 오류: {e}")
            import traceback
            traceback.print_exc()

    def _check_main_liquidation_and_protect_hedge(self, position_data, current_price):
        """최종 단계에서 메인 포지션 강제 청산 감지 시 헷지에 트레일링 스탑 설정"""
        try:
            main_pos_key = f"{self.symbol}_{self.side_mode}"
            hedge_side = "LONG" if self.side_mode == "SHORT" else "SHORT"
            hedge_pos_key = f"{self.symbol}_{hedge_side}"

            main_amt = abs(float(position_data.get(main_pos_key, {}).get('amount', 0)))
            hedge_amt = abs(float(position_data.get(hedge_pos_key, {}).get('amount', 0)))

            # 메인 포지션이 없고 헷지가 남아있는 경우 = 메인 강제 청산
            if main_amt < 0.0001 and hedge_amt > 0.0001:
                self.main_liquidation_handled = True

                self._log("[최종단계] ========================================")
                self._log("[최종단계] 메인 포지션 강제 청산 감지!")
                self._log(f"[최종단계] 헷지 포지션 잔존: {hedge_amt} {self.symbol}")
                self._log("[최종단계] 헷지 트레일링 스탑 긴급 설정")
                self._log("[최종단계] ========================================")

                # 트레일링 스탑 방향: 헷지 포지션을 닫는 방향
                # SHORT 모드 → 헷지는 LONG → SELL로 닫음
                # LONG 모드 → 헷지는 SHORT → BUY로 닫음
                trailing_stop_side = "SELL" if self.side_mode == "SHORT" else "BUY"
                trailing_callback_rate = str(self.strategy_settings.get("TRAILING_CALLBACK_RATE", 0.5))

                # 활성화 가격 = 현재가
                tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
                price_precision = trading_utils.count_decimal_places(tick_size)
                activation_price = trading_utils.adjust_price(current_price, tick_size, price_precision)

                self._log(f"[최종단계] 트레일링 스탑: {trailing_stop_side} {hedge_amt} @ Activation=${activation_price}, Callback={trailing_callback_rate}%")

                self.request_trailing_stop.emit(
                    self.symbol,
                    trailing_stop_side,
                    str(hedge_amt),
                    str(activation_price),
                    trailing_callback_rate
                )

                # 포지션 청산 모니터링 시작 (헷지가 닫히면 DCA 재시작)
                self.monitoring_final_step_closure = True
                self._log("[최종단계] 헷지 포지션 청산 모니터링 시작")

        except Exception as e:
            self._log(f"[최종단계] 메인 청산 감지 오류: {e}")
            import traceback
            traceback.print_exc()

    def _check_hedge_liquidation_and_protect_main(self, position_data, current_price):
        """최종 단계에서 헷지 포지션 청산 감지 시 메인에 트레일링 스탑 설정"""
        try:
            main_pos_key = f"{self.symbol}_{self.side_mode}"
            hedge_side = "LONG" if self.side_mode == "SHORT" else "SHORT"
            hedge_pos_key = f"{self.symbol}_{hedge_side}"

            main_amt = abs(float(position_data.get(main_pos_key, {}).get('amount', 0)))
            hedge_amt = abs(float(position_data.get(hedge_pos_key, {}).get('amount', 0)))

            # 헷지 포지션이 없고 메인이 남아있는 경우 = 헷지 청산됨
            if hedge_amt < 0.0001 and main_amt > 0.0001:
                self.hedge_liquidation_handled = True

                self._log("[최종단계] ========================================")
                self._log("[최종단계] 헷지 포지션 청산 감지!")
                self._log(f"[최종단계] 메인 포지션 잔존: {main_amt} {self.symbol}")
                self._log("[최종단계] 메인 트레일링 스탑 긴급 설정")
                self._log("[최종단계] ========================================")

                # 트레일링 스탑 방향: 메인 포지션을 닫는 방향
                # LONG 모드 → 메인은 LONG → SELL로 닫음
                # SHORT 모드 → 메인은 SHORT → BUY로 닫음
                trailing_stop_side = "SELL" if self.side_mode == "LONG" else "BUY"
                trailing_callback_rate = str(self.strategy_settings.get("TRAILING_CALLBACK_RATE", 0.5))

                # 활성화 가격 = 현재가
                tick_size = float(self.symbol_info.get('priceFilter', {}).get('tickSize', '0.0001'))
                price_precision = trading_utils.count_decimal_places(tick_size)
                activation_price = trading_utils.adjust_price(current_price, tick_size, price_precision)

                self._log(f"[최종단계] 트레일링 스탑: {trailing_stop_side} {main_amt} @ Activation=${activation_price}, Callback={trailing_callback_rate}%")

                self.request_trailing_stop.emit(
                    self.symbol,
                    trailing_stop_side,
                    str(main_amt),
                    str(activation_price),
                    trailing_callback_rate
                )

                # 포지션 청산 모니터링 시작 (메인이 닫히면 DCA 재시작)
                self.monitoring_final_step_closure = True
                self._log("[최종단계] 메인 포지션 청산 모니터링 시작")

        except Exception as e:
            self._log(f"[최종단계] 헷지 청산 감지 오류: {e}")
            import traceback
            traceback.print_exc()

    def _monitor_final_step_position_closure(self, position_data):
        """최종 단계: 주 포지션과 헷지 포지션이 모두 청산되었는지 확인"""
        try:
            if not self.monitoring_final_step_closure:
                return

            # 포지션 수량 확인
            long_pos_key = f"{self.symbol}_LONG"
            short_pos_key = f"{self.symbol}_SHORT"

            long_pos_amt = float(position_data.get(long_pos_key, {}).get('amount', 0))
            short_pos_amt = float(position_data.get(short_pos_key, {}).get('amount', 0))

            # 주 포지션과 헷지 포지션이 모두 없는지 확인
            both_positions_closed = (abs(long_pos_amt) < 0.0001 and abs(short_pos_amt) < 0.0001)

            if both_positions_closed:
                self._log("[최종단계] ========================================")
                self._log("[최종단계] 양쪽 포지션 모두 청산 감지!")
                self._log("[최종단계] DCA 초기화 및 자동매매 재시작...")
                self._log("[최종단계] ========================================")

                # DCA 상태 초기화 (익절과 동일)
                self.current_step = 0
                self.initial_entry_done = False
                self.next_step_orders_placed = False
                self.next_step_order_id = None
                self.last_step_entry_price = None
                self.m_orders_data = []
                self.hedge_trigger_prices = []
                self.remaining_hedge_qty = 0
                self.pending_hedge_orders = {}
                self.hedge_filled_need_threshold_recalc = False
                self.step_filled_need_threshold_recalc = False
                self.uptrend_threshold_price = None  # 임계값 초기화
                self.uptrend_threshold_price_2 = None
                self.profit_target_price = None
                self.profit_base_price = None
                self._profit_base_needs_recalc = False
                self.entry_price_at_step = None
                self.is_uptrend_entry = False
                self.uptrend_entry_in_progress = False  # 역방향진입 중복 방지 플래그 리셋
                self.uptrend_entry_count = 0  # 역방향진입 횟수 리셋
                self.high_price_since_entry = None
                self.low_price_since_entry = None
                self.last_profit_target_update_time = 0
                self.final_step_protection_placed = False
                self.monitoring_final_step_closure = False
                self.main_liquidation_handled = False
                self.hedge_liquidation_handled = False

                self._log("[최종단계] DCA 상태 초기화 완료")

                # 상태 저장 (초기화된 상태로 저장 → 삭제 목적)
                self.request_save_state.emit()

                # 자동매매 재시작 요청 (GUI에 전달)
                self.profit_taking_request.emit()

        except Exception as e:
            self._log(f"[최종단계] 포지션 청산 모니터링 오류: {e}")
            import traceback
            traceback.print_exc()

    def _reduce_hedge_on_uptrend_entry(self):
        """역방향진입 시 헷지 포지션 부분 청산
        
        청산 비율:
        - 1차 역방향진입 (count=0): 현재 헷지의 1/3 청산
        - 2차 역방향진입 (count=1): 남은 헷지의 1/2 청산
        - 3차 역방향진입 이상 (count>=2): 남은 헷지 전부 청산
        
        최소 주문 수량/금액 처리:
        - 청산 수량 < 최소 수량 → 최소 수량으로 청산
        - 청산 금액 < 최소 금액 → 최소 금액에 해당하는 수량으로 청산
        - 청산 후 남은 수량 < 최소 수량 → 전부 청산
        - 청산 후 남은 금액 < 최소 금액 → 전부 청산
        """
        try:
            # 현재 헷지 포지션 수량 조회
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"
            pos_key_hedge = f"{self.symbol}_{hedge_side}"
            
            hedge_position = self.current_position_data.get(pos_key_hedge, {})
            hedge_qty = abs(float(hedge_position.get('amount', 0)))
            
            if hedge_qty <= 0:
                self._log(f"[{self._el} 헷지청산] 헷지 포지션 없음 - 청산 스킵")
                return
            
            # 수량 정밀도 및 최소 주문 수량/금액 조회
            step_size = float(self.symbol_info.get('lotSizeFilter', {}).get('qtyStep', '1'))
            min_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minQty', '1'))
            min_notional = float(self.symbol_info.get('lotSizeFilter', {}).get('minNotionalValue', '5'))
            qty_precision = trading_utils.count_decimal_places(step_size)
            
            # 현재가 확인
            current_price = self.current_price if self.current_price and self.current_price > 0 else 0
            
            # 최소 금액에 해당하는 최소 수량 계산
            min_qty_by_notional = 0
            if current_price > 0:
                min_qty_by_notional = min_notional / current_price
                # step_size에 맞게 올림 처리
                min_qty_by_notional = float(int(min_qty_by_notional / step_size + 0.9999) * step_size)
                min_qty_by_notional = round(min_qty_by_notional, qty_precision)
            
            # 실제 적용할 최소 수량 (수량 기준과 금액 기준 중 큰 값)
            effective_min_qty = max(min_qty, min_qty_by_notional)
            
            # 청산 단계 수 설정값 가져오기 (기본값 3: 1/3 → 1/2 → 전부)
            hedge_reduction_steps = self.strategy_settings.get("HEDGE_REDUCTION_STEPS", 3)
            
            # 남은 청산 단계 계산
            remaining_steps = hedge_reduction_steps - self.uptrend_entry_count
            
            # 청산 비율 및 수량 결정
            if remaining_steps <= 1:
                # 마지막 단계 또는 초과: 전부 청산
                reduce_ratio = 1.0
                reduce_qty = hedge_qty
                ratio_desc = "전부 (1/1)"
            else:
                # 남은 단계에 따라 비율 결정 (1/remaining_steps)
                reduce_ratio = 1.0 / remaining_steps
                reduce_qty = hedge_qty * reduce_ratio
                ratio_desc = f"1/{remaining_steps}"
            
            # 내림 처리 (안전하게)
            reduce_qty = float(int(reduce_qty / step_size) * step_size)
            reduce_qty = round(reduce_qty, qty_precision)
            
            # ========== 최소 주문 수량/금액 처리 ==========
            adjustment_reason = ""
            
            # 1. 청산 수량이 최소 수량 미만이면 → 최소 수량으로 조정
            if reduce_qty < effective_min_qty:
                reduce_qty = effective_min_qty
                if min_qty_by_notional > min_qty:
                    adjustment_reason = f"청산금액 < 최소금액(${min_notional}) → 최소금액 수량({effective_min_qty})으로 조정"
                else:
                    adjustment_reason = f"청산수량 < 최소수량({min_qty}) → 최소수량으로 조정"
            
            # 2. 청산 후 남은 수량 계산
            remaining_after_reduce = hedge_qty - reduce_qty
            
            # 3. 청산 후 남은 수량이 최소 수량 미만이면 → 전부 청산
            if 0 < remaining_after_reduce < effective_min_qty:
                reduce_qty = hedge_qty
                ratio_desc = "전부 (잔여부족)"
                remaining_value = remaining_after_reduce * current_price if current_price > 0 else 0
                adjustment_reason = f"청산 후 잔여({remaining_after_reduce:.4f}, ${remaining_value:.2f}) < 최소기준 → 전부 청산"
            
            # 청산 수량이 보유 수량 초과 방지
            if reduce_qty > hedge_qty:
                reduce_qty = hedge_qty
                ratio_desc = "전부 (초과보정)"
            
            if reduce_qty <= 0:
                self._log(f"[{self._el} 헷지청산] 청산 수량이 0 이하 - 청산 스킵 (원본: {hedge_qty}, 비율: {ratio_desc})")
                return
            
            # 청산 금액 계산
            reduce_value = reduce_qty * current_price if current_price > 0 else 0
            remaining_value = (hedge_qty - reduce_qty) * current_price if current_price > 0 else 0
            
            self._log(f"[{self._el} 헷지청산] ========================================")
            self._log(f"[{self._el} 헷지청산] 청산 단계 설정: {hedge_reduction_steps}단계")
            self._log(f"[{self._el} 헷지청산] {self._el} 횟수: {self.uptrend_entry_count + 1}회차 (남은 단계: {remaining_steps})")
            self._log(f"[{self._el} 헷지청산] 현재가: ${current_price}")
            self._log(f"[{self._el} 헷지청산] 현재 헷지 수량: {hedge_qty} (${hedge_qty * current_price:.2f})")
            self._log(f"[{self._el} 헷지청산] 최소 주문 수량: {min_qty}, 최소 주문 금액: ${min_notional}")
            self._log(f"[{self._el} 헷지청산] 적용 최소 수량: {effective_min_qty} (${effective_min_qty * current_price:.2f})")
            self._log(f"[{self._el} 헷지청산] 청산 비율: {ratio_desc} ({reduce_qty/hedge_qty*100:.1f}%)")
            self._log(f"[{self._el} 헷지청산] 청산 수량: {reduce_qty} (${reduce_value:.2f})")
            if adjustment_reason:
                self._log(f"[{self._el} 헷지청산] ⚠ 수량 조정: {adjustment_reason}")
            self._log(f"[{self._el} 헷지청산] 청산 후 잔여: {hedge_qty - reduce_qty} (${remaining_value:.2f})")
            self._log(f"[{self._el} 헷지청산] ========================================")
            
            # 헷지 청산 방향 결정 (헷지 포지션 청산이므로 반대 방향)
            # LONG 모드: 헷지는 SHORT → BUY로 청산
            # SHORT 모드: 헷지는 LONG → SELL로 청산
            close_side = "BUY" if self.side_mode == "LONG" else "SELL"
            
            # GUI에 헷지 청산 요청 (reduce_only로 처리)
            self.reduce_hedge_signal.emit(self.symbol, close_side, str(reduce_qty))

            # 헷지 전부 청산 시 안전망 주문 취소 및 Emergency Exit 라인 제거
            if reduce_qty >= hedge_qty:
                self._cancel_hedge_safety_order()

            # 역방향진입 횟수 증가
            self.uptrend_entry_count += 1
            self._log(f"[{self._el} 헷지청산] {self._el} 카운트 업데이트: {self.uptrend_entry_count}")
            
            # 상태 저장 요청
            self.request_save_state.emit()
            
        except Exception as e:
            self._log(f"[{self._el} 헷지청산] 오류: {e}")
            import traceback
            traceback.print_exc()

    def _place_hedge_safety_order(self, hedge_liq_price):
        """헷지 청산가 안전망 주문을 설정합니다 (청산가 안전마진% 적용).

        긴급탈출라인이 설정되지 않는 상황에서도 헷지 청산을 방지하기 위해
        청산가 직전에 헷지 전체를 정리하는 주문을 걸어둡니다.
        안전마진은 LIQUIDATION_SAFETY_MARGIN 설정으로 조절 가능합니다.
        """
        try:
            # 기존 안전망 주문이 있으면 먼저 취소
            self._cancel_hedge_safety_order()

            # API를 통해 헷지 포지션 직접 조회 (WebSocket보다 빠름)
            hedge_qty = 0
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"

            try:
                positions = self.api_module.get_initial_positions()
                for pos in positions:
                    if pos.get('symbol') == self.symbol and pos.get('positionSide') == hedge_side:
                        hedge_qty = abs(float(pos.get('positionAmt', 0)))
                        self._log(f"[헷지 안전망] API로부터 헷지 포지션 조회: {hedge_qty}")
                        break
            except Exception as e:
                self._log(f"[헷지 안전망] API 포지션 조회 실패: {e}")
                # API 실패 시 self.current_position_data 사용 (fallback)
                for _, pos_data in self.current_position_data.items():
                    if pos_data.get('side', pos_data.get('positionSide')) == hedge_side:
                        hedge_qty = abs(float(pos_data.get('amount', 0)))
                        self._log(f"[헷지 안전망] WebSocket 데이터로부터 헷지 포지션 사용: {hedge_qty}")
                        break

            if hedge_qty == 0:
                self._log(f"[헷지 안전망] 헷지 포지션 없음 - 주문 설정 안 함")
                return

            # 청산가 안전마진% 적용하여 가격 계산
            safety_margin = self.hedge_liquidation_safety_margin  # 헷지 포지션 청산가 안전마진

            if self.side_mode == "LONG":
                # LONG: 헷지는 SHORT, 가격 상승 시 청산 위험 → 청산가보다 낮은 가격에 BUY 주문
                # 청산가에서 안전마진%만큼 낮춘 가격
                safety_price = hedge_liq_price * (1 - safety_margin / 100.0)
                close_side = "BUY"
            else:
                # SHORT: 헷지는 LONG, 가격 하락 시 청산 위험 → 청산가보다 높은 가격에 SELL 주문
                # 청산가에서 안전마진%만큼 높인 가격
                safety_price = hedge_liq_price * (1 + safety_margin / 100.0)
                close_side = "SELL"

            # 가격 반올림
            safety_price = round(safety_price, self.price_precision)

            self._log(f"[헷지 안전망] ==================== 안전망 주문 설정 ====================")
            self._log(f"[헷지 안전망] 헷지 청산가: ${self.fmt_price(hedge_liq_price)}")
            self._log(f"[헷지 안전망] 안전마진: {safety_margin}%")
            self._log(f"[헷지 안전망] 안전망 주문 가격: ${self.fmt_price(safety_price)}")
            self._log(f"[헷지 안전망] 주문 수량: {hedge_qty} (헷지 전체)")
            self._log(f"[헷지 안전망] 주문 방향: {close_side}")
            self._log(f"[헷지 안전망] ===========================================================")

            # STOP MARKET 주문 발행 (청산가 도달 시 시장가로 청산)
            # 헷지 포지션 방향 결정
            hedge_position_side = "SHORT" if self.side_mode == "LONG" else "LONG"

            result = self.api_module.place_stop_market_order(
                symbol=self.symbol,
                side=close_side,
                quantity=hedge_qty,
                stop_price=safety_price,
                reduce_only=True,  # 포지션 청산 전용
                position_side=hedge_position_side
            )

            if result and result.get('orderId'):
                self.hedge_safety_order_id = result['orderId']
                self.hedge_safety_order_price = safety_price
                self._log(f"[헷지 안전망] 안전망 주문 설정 완료: ID={self.hedge_safety_order_id}")

                # GUI에 안전망 주문 가격 전송 (차트 마커 표시용)
                self.emergency_exit_line_updated.emit(safety_price)
            else:
                self._log(f"[헷지 안전망] 안전망 주문 설정 실패: {result}")

        except Exception as e:
            self._log(f"[헷지 안전망] 안전망 주문 설정 오류: {e}")
            import traceback
            traceback.print_exc()

    def _cancel_hedge_safety_order(self):
        """헷지 청산가 안전망 주문을 취소합니다."""
        try:
            if self.hedge_safety_order_id is None:
                return

            self._log(f"[헷지 안전망] 기존 안전망 주문 취소 시도: ID={self.hedge_safety_order_id}")

            result = self.api_module.cancel_order(
                symbol=self.symbol,
                order_id=self.hedge_safety_order_id,
                order_category='normal'
            )

            if result:
                self._log(f"[헷지 안전망] 안전망 주문 취소 완료")
            else:
                self._log(f"[헷지 안전망] 안전망 주문 취소 실패 (이미 체결되었거나 존재하지 않음)")

            # 변수 초기화
            self.hedge_safety_order_id = None
            self.hedge_safety_order_price = None

            # GUI에 안전망 제거 알림 (차트 마커 제거용)
            self.emergency_exit_line_updated.emit(0)

        except Exception as e:
            self._log(f"[헷지 안전망] 안전망 주문 취소 오류: {e}")
            # 오류 발생 시에도 변수는 초기화
            self.hedge_safety_order_id = None
            self.hedge_safety_order_price = None

    def _handle_hedge_safety_order_filled(self):
        """헷지 안전망 주문이 체결되었을 때 메인 포지션 청산 후 다음 사이클 시작"""
        try:
            self._log(f"[헷지 안전망] ==================== 안전망 주문 체결 감지 ====================")
            self._log(f"[헷지 안전망] 헷지가 청산가에 도달하여 안전망 주문 체결됨")
            self._log(f"[헷지 안전망] 메인 포지션 전체 시장가 청산 시작...")
            self._log(f"[헷지 안전망] ================================================================")

            # 메인 포지션 수량 확인
            main_qty = 0
            for _, pos_data in self.current_position_data.items():
                if pos_data.get('side', pos_data.get('positionSide')) == self.side_mode:
                    main_qty = abs(float(pos_data.get('amount', 0)))
                    break

            if main_qty == 0:
                self._log(f"[헷지 안전망] 메인 포지션 없음 - 사이클 완료 처리")
            else:
                # 메인 포지션 시장가 청산
                main_close_side = "SELL" if self.side_mode == "LONG" else "BUY"

                self._log(f"[헷지 안전망] 메인 포지션 청산: {main_qty} {self.symbol} ({main_close_side})")

                # positionIdx 결정
                position_side = "LONG" if self.side_mode == "LONG" else "SHORT"

                result = self.api_module.place_market_order(
                    symbol=self.symbol,
                    side=main_close_side,
                    quantity=main_qty,
                    reduce_only=True,
                    position_side=position_side
                )

                if result and result.get('orderId'):
                    self._log(f"[헷지 안전망] 메인 포지션 청산 주문 완료: ID={result['orderId']}")
                else:
                    self._log(f"[헷지 안전망] 메인 포지션 청산 주문 실패: {result}")

            # DCA 상태 초기화 (다음 사이클 준비)
            self._log(f"[헷지 안전망] ========================================")
            self._log(f"[헷지 안전망] 사이클 완료 - DCA 상태 초기화")
            self._log(f"[헷지 안전망] ========================================")

            self.current_step = 0
            self.initial_entry_done = False
            self.next_step_orders_placed = False
            self.entry_price_at_step = None
            self.is_uptrend_entry = False
            self.uptrend_entry_in_progress = False
            self.uptrend_entry_count = 0
            self.profit_target_price = None
            self.profit_base_price = None
            self._profit_base_needs_recalc = False
            self.high_price_since_entry = None
            self.low_price_since_entry = None
            self.last_profit_target_update_time = 0
            self.next_step_order_id = None
            self.last_step_entry_price = None
            self.m_orders_data = []
            self.hedge_trigger_prices = []
            self.remaining_hedge_qty = 0
            self.pending_hedge_orders = {}
            self.hedge_filled_need_threshold_recalc = False
            self.step_filled_need_threshold_recalc = False
            self.uptrend_threshold_price = None
            self.uptrend_threshold_price_2 = None
            self.final_step_protection_placed = False
            self.monitoring_final_step_closure = False
            self.main_liquidation_handled = False
            self.hedge_liquidation_handled = False

            # 헷지 청산가 보호 상태 초기화
            self.hedge_emergency_exit_lines = []
            self.emergency_exit_triggered = False
            self.hedge_safety_order_id = None
            self.hedge_safety_order_price = None

            # 헷지 프로토콜 상태 초기화
            self.hedge_protocol_active = False
            self.hedge_protocol_lowest_price = None
            self.hedge_protocol_avg_entry = None
            self.hedge_protocol_retracement_price = None

            self._log(f"[헷지 안전망] DCA 상태 초기화 완료 - 다음 사이클 준비됨")

            # GUI에 전체 청산 및 재시작 요청 (익절과 동일)
            self.profit_taking_request.emit()
            self._log(f"[헷지 안전망] GUI에 전체 청산 및 자동매매 재시작 요청 전송")

        except Exception as e:
            self._log(f"[헷지 안전망] 안전망 체결 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def _trigger_emergency_exit(self):
        """긴급 탈출 상태로 전환 (DCA 중단)

        NOTE: 이 함수는 더 이상 안전망 체결에서 사용되지 않습니다.
        안전망 체결 시에는 _handle_hedge_safety_order_filled()에서 초기화 후 재시작합니다.
        이 함수는 향후 다른 긴급 상황을 위해 남겨둡니다.
        """
        if not self.emergency_exit_triggered:
            self.emergency_exit_triggered = True
            self._log(f"[긴급 탈출] DCA 자동매매 긴급 중단")

            # 다음 단계 주문 취소
            if self.next_step_order_id:
                try:
                    self.api_module.cancel_order(
                        symbol=self.symbol,
                        order_id=self.next_step_order_id,
                        category=self.category
                    )
                    self._log(f"[헷지 안전망] 다음 단계 주문 취소: ID={self.next_step_order_id}")
                except:
                    pass

            # GUI 업데이트 (상태 저장 요청)
            self.request_save_state.emit()

    def _calculate_current_break_even(self):
        """현재 Break Even 계산 (헷지 프로토콜용 헬퍼)

        Returns:
            float: 현재 BE 가격, 계산 불가능하면 None
        """
        be = self.calculate_break_even(self.current_position_data)
        if be is None:
            self._log(f"[헷지 프로토콜 디버그] BE 계산 실패")
            self._log(f"[헷지 프로토콜 디버그] position_data keys: {list(self.current_position_data.keys())}")
            for key, data in self.current_position_data.items():
                self._log(f"[헷지 프로토콜 디버그] {key}: {data}")
        return be

    def _get_main_position_avg_price(self):
        """메인 포지션 평균가 조회 (헷지 프로토콜용 헬퍼)

        Returns:
            float: 메인 포지션 평균가, 조회 실패 시 None
        """
        try:
            pos_key_main = f"{self.symbol}_LONG" if self.side_mode == "LONG" else f"{self.symbol}_SHORT"
            main_position = self.current_position_data.get(pos_key_main, {})
            main_avg_price = float(main_position.get('entry_price', main_position.get('entry', 0)) or 0)

            if main_avg_price <= 0:
                return None

            return main_avg_price

        except Exception as e:
            self._log(f"[헷지 프로토콜] 메인 평균가 조회 오류: {e}")
            return None

    def _handle_hedge_protocol_trigger(self, trigger_index, hedge_fill_price):
        """헷지 프로토콜: 헷지 체결 시 처리 (H1 활성화, H4 비활성화)

        Args:
            trigger_index: 헷지 트리거 인덱스 (0=H1, 1=H2, 2=H3, 3=H4)
            hedge_fill_price: 헷지 체결가
        """
        try:
            if trigger_index == 0:  # H1 체결
                if not self.hedge_protocol_active and not self.hedge_protocol_executed:
                    # H1 체결 시 BE 안전성 체크 → 조건 충족 시에만 프로토콜 활성화
                    self._log(f"[헷지 프로토콜] H1 체결 감지 - 활성화 조건 체크")

                    # 헷지 평균가 업데이트 (API에서 실제 헷지 포지션 평균가 조회)
                    self._update_hedge_protocol_avg_price()

                    # BE 계산
                    current_be = self._calculate_current_break_even()
                    if current_be is None:
                        self._log(f"[헷지 프로토콜] BE 계산 불가 - 활성화 중단")
                        return

                    # 안전망 가격 조회
                    safety_price = getattr(self, 'hedge_safety_order_price', None)
                    if safety_price is None:
                        self._log(f"[헷지 프로토콜] 안전망 가격 없음 - 활성화 중단")
                        return

                    # 메인 평균가 조회
                    main_avg_price = self._get_main_position_avg_price()
                    if main_avg_price is None:
                        self._log(f"[헷지 프로토콜] 메인 평균가 조회 불가 - 활성화 중단")
                        return

                    # 메인 평균가와 안전망 가격의 익절비율% 기준점 계산
                    tp_ratio = self.hedge_protocol_tp_ratio / 100.0
                    if self.side_mode == "LONG":
                        threshold = main_avg_price + (safety_price - main_avg_price) * tp_ratio
                    else:
                        threshold = main_avg_price - (main_avg_price - safety_price) * tp_ratio

                    self._log(f"[헷지 프로토콜] 메인 평균가: ${self.fmt_price(main_avg_price)}")
                    self._log(f"[헷지 프로토콜] 안전망 가격: ${self.fmt_price(safety_price)}")
                    self._log(f"[헷지 프로토콜] {self.hedge_protocol_tp_ratio}% 기준가: ${self.fmt_price(threshold)}")
                    self._log(f"[헷지 프로토콜] 현재 BE: ${self.fmt_price(current_be)}")

                    # BE 안전성 체크: BE가 메인 평균가와 안전망의 익절비율% 기준을 넘었을 때 프로토콜 발동
                    # LONG: BE > 기준가 → BE가 너무 높아 헷지 축소 필요
                    # SHORT: BE < 기준가 → BE가 너무 낮아 헷지 축소 필요
                    be_needs_fix = current_be > threshold if self.side_mode == "LONG" else current_be < threshold
                    if be_needs_fix:
                        # 헷지 프로토콜 활성화
                        self.hedge_protocol_active = True
                        self.hedge_protocol_exited_qty = 0  # 탈출 수량 초기화
                        self.hedge_protocol_waiting_for_be = False  # BE 대기 플래그 리셋

                        # 최저가를 헷지 평균가로 초기화 (위에서 이미 업데이트됨)
                        self.hedge_protocol_lowest_price = self.hedge_protocol_hedge_avg_price

                        self._log(f"[헷지 프로토콜] ✓ BE 안전 조건 충족 - 활성화!")
                        self._log(f"[헷지 프로토콜] 헷지 평균가: ${self.fmt_price(self.hedge_protocol_hedge_avg_price)}")
                        self._log(f"[헷지 프로토콜] 최저가 초기화: ${self.fmt_price(self.hedge_protocol_lowest_price)}")
                        self._log(f"[헷지 프로토콜] 되돌림 비율: {self.hedge_protocol_retracement_percent}%")
                        self._log(f"[헷지 프로토콜] 최저가 추적 시작")
                    else:
                        self._log(f"[헷지 프로토콜] ✗ BE 안전 조건 미충족 - 활성화 안함")
                        self._log(f"[헷지 프로토콜] H2/H3 체결 시 재확인")

            elif trigger_index in [1, 2]:  # H2, H3 체결
                # 헷지 평균가 업데이트 (API에서 실제 헷지 포지션 평균가 조회)
                self._update_hedge_protocol_avg_price()

                if self.hedge_protocol_active:
                    # 프로토콜이 이미 활성화된 경우: 아무것도 안함
                    # 되돌림 체크는 매 틱마다 수행됨
                    pass

                elif not self.hedge_protocol_executed:
                    # 프로토콜이 아직 활성화되지 않은 경우: 활성화 조건 체크
                    self._log(f"[헷지 프로토콜] H{trigger_index + 1} 체결 감지 - 활성화 조건 체크")

                    # BE 계산
                    current_be = self._calculate_current_break_even()
                    if current_be is None:
                        self._log(f"[헷지 프로토콜] BE 계산 불가 - 활성화 중단")
                        return

                    # 안전망 가격 조회
                    safety_price = getattr(self, 'hedge_safety_order_price', None)
                    if safety_price is None:
                        self._log(f"[헷지 프로토콜] 안전망 가격 없음 - 활성화 중단")
                        return

                    # 메인 평균가 조회
                    main_avg_price = self._get_main_position_avg_price()
                    if main_avg_price is None:
                        self._log(f"[헷지 프로토콜] 메인 평균가 조회 불가 - 활성화 중단")
                        return

                    # 메인 평균가와 안전망 가격의 익절비율% 기준점 계산
                    tp_ratio = self.hedge_protocol_tp_ratio / 100.0
                    if self.side_mode == "LONG":
                        threshold = main_avg_price + (safety_price - main_avg_price) * tp_ratio
                    else:
                        threshold = main_avg_price - (main_avg_price - safety_price) * tp_ratio

                    self._log(f"[헷지 프로토콜] 현재 BE: ${self.fmt_price(current_be)}")
                    self._log(f"[헷지 프로토콜] 안전망 가격: ${self.fmt_price(safety_price)}")
                    self._log(f"[헷지 프로토콜] {self.hedge_protocol_tp_ratio}% 기준가: ${self.fmt_price(threshold)}")

                    # BE 안전성 체크: BE가 메인 평균가와 안전망의 익절비율% 기준을 넘었을 때 프로토콜 발동
                    # LONG: BE > 기준가 → BE가 너무 높아 헷지 축소 필요
                    # SHORT: BE < 기준가 → BE가 너무 낮아 헷지 축소 필요
                    be_needs_fix = current_be > threshold if self.side_mode == "LONG" else current_be < threshold
                    if be_needs_fix:
                        # 헷지 프로토콜 활성화
                        self.hedge_protocol_active = True
                        # 최저가를 헷지 평균가로 초기화 (라인 2893에서 이미 업데이트됨)
                        self.hedge_protocol_lowest_price = self.hedge_protocol_hedge_avg_price
                        self.hedge_protocol_exited_qty = 0
                        self.hedge_protocol_waiting_for_be = False

                        self._log(f"[헷지 프로토콜] ✓ BE 안전 조건 충족 - 활성화!")
                        self._log(f"[헷지 프로토콜] 헷지 평균가: ${self.fmt_price(self.hedge_protocol_hedge_avg_price)}")
                        self._log(f"[헷지 프로토콜] 최저가 초기화: ${self.fmt_price(self.hedge_protocol_lowest_price)}")
                        self._log(f"[헷지 프로토콜] 최저가 추적 시작")
                    else:
                        self._log(f"[헷지 프로토콜] ✗ BE 안전 조건 미충족 - 활성화 안함")

            elif trigger_index == 3:  # H4 체결
                if self.hedge_protocol_active:
                    # 프론트로드 최종단계: H4에서 비활성화하지 않음 (계속 추적)
                    if self.hedge_frontload_final_step and self.current_step + 1 >= self.total_steps:
                        self._log(f"[헷지 프론트로드] H4 체결 - 최종 단계이므로 프로토콜 유지")
                    else:
                        self.hedge_protocol_active = False
                        self._log(f"[헷지 프로토콜] H4 체결 → 비활성화")

        except Exception as e:
            self._log(f"[헷지 프로토콜] 트리거 처리 오류: {e}")
            import traceback
            traceback.print_exc()

    def _check_retracement_condition(self, current_price):
        """헷지 프로토콜: 되돌림 조건 체크

        Args:
            current_price: 현재가

        Returns:
            bool: 되돌림 조건 충족 여부
        """
        if self.hedge_protocol_hedge_avg_price is None:
            return False

        # 되돌림 비율 계산
        if self.side_mode == "LONG":
            # LONG: 하락 후 반등
            if current_price >= self.hedge_protocol_hedge_avg_price:
                return False

            total_distance = self.hedge_protocol_hedge_avg_price - self.hedge_protocol_lowest_price

            if total_distance < 0:
                self._log(f"[헷지 프로토콜] 경고: 비정상 상태 감지 (hedge_avg < lowest)")
                return False

            if total_distance == 0:
                return False

            current_retracement_distance = current_price - self.hedge_protocol_lowest_price
            retracement_percent = (current_retracement_distance / total_distance) * 100

        else:  # SHORT
            # SHORT: 상승 후 하락
            if current_price <= self.hedge_protocol_hedge_avg_price:
                return False

            total_distance = self.hedge_protocol_lowest_price - self.hedge_protocol_hedge_avg_price

            if total_distance < 0:
                self._log(f"[헷지 프로토콜] 경고: 비정상 상태 감지 (hedge_avg > highest)")
                return False

            if total_distance == 0:
                return False

            current_retracement_distance = self.hedge_protocol_lowest_price - current_price
            retracement_percent = (current_retracement_distance / total_distance) * 100

        # 되돌림 임계값 도달 여부
        if retracement_percent >= self.hedge_protocol_retracement_percent:
            self._log(f"[헷지 프로토콜] ========================================")
            self._log(f"[헷지 프로토콜] 되돌림 임계값 도달!")
            self._log(f"[헷지 프로토콜] 최저가: ${self.fmt_price(self.hedge_protocol_lowest_price)}")
            self._log(f"[헷지 프로토콜] 헷지 평균가: ${self.fmt_price(self.hedge_protocol_hedge_avg_price)}")
            self._log(f"[헷지 프로토콜] 현재가: ${self.fmt_price(current_price)}")
            self._log(f"[헷지 프로토콜] 되돌림: {retracement_percent:.2f}% / {self.hedge_protocol_retracement_percent}%")
            return True

        return False

    def _check_hedge_protocol_retracement(self, current_price):
        """헷지 프로토콜: 가격 추적 및 되돌림 체크 (매 틱마다 실행)

        Args:
            current_price: 현재가

        Note:
            1. 최저가/최고가 업데이트
            2. 되돌림 50% 체크 → 익절 실행
        """
        if not self.hedge_protocol_active or self.hedge_protocol_executed:
            return

        try:
            # 1. 최저가/최고가 업데이트
            if self.hedge_protocol_lowest_price is None:
                self.hedge_protocol_lowest_price = current_price
            else:
                if self.side_mode == "LONG":
                    # LONG: 하락 추적 (최저가)
                    if current_price < self.hedge_protocol_lowest_price:
                        self.hedge_protocol_lowest_price = current_price
                else:
                    # SHORT: 상승 추적 (최고가)
                    if current_price > self.hedge_protocol_lowest_price:
                        self.hedge_protocol_lowest_price = current_price

            # 2. 되돌림 조건 체크
            if not self._check_retracement_condition(current_price):
                return

            # 3. 되돌림 50% 도달 → BE 안전성 체크 후 익절
            current_be = self._calculate_current_break_even()
            safety_price = getattr(self, 'hedge_safety_order_price', None)

            if current_be is None:
                self._log(f"[헷지 프로토콜] BE 계산 불가 - 프로토콜 비활성화")
                self._log(f"[헷지 프로토콜] ========================================")
                self.hedge_protocol_executed = True
                self.hedge_protocol_active = False
                return

            if safety_price is None:
                self._log(f"[헷지 프로토콜] 경고: 안전망 가격 없음 - BE 체크 스킵하고 익절")
                self._log(f"[헷지 프로토콜] ========================================")
                self._execute_hedge_protocol_take_profit(current_price)
                return

            # 메인 평균가 조회
            main_avg_price = self._get_main_position_avg_price()
            if main_avg_price is None:
                self._log(f"[헷지 프로토콜] 메인 평균가 조회 불가 - 프로토콜 비활성화")
                self._log(f"[헷지 프로토콜] ========================================")
                self.hedge_protocol_executed = True
                self.hedge_protocol_active = False
                return

            # 메인 평균가와 안전망 가격의 익절비율% 기준점 계산
            tp_ratio = self.hedge_protocol_tp_ratio / 100.0
            if self.side_mode == "LONG":
                threshold = main_avg_price + (safety_price - main_avg_price) * tp_ratio
            else:
                threshold = main_avg_price - (main_avg_price - safety_price) * tp_ratio

            self._log(f"[헷지 프로토콜] --- BE 안전성 체크 ---")
            self._log(f"[헷지 프로토콜] 메인 평균가: ${self.fmt_price(main_avg_price)}")
            self._log(f"[헷지 프로토콜] 안전망 가격: ${self.fmt_price(safety_price)}")
            self._log(f"[헷지 프로토콜] {self.hedge_protocol_tp_ratio}% 기준가: ${self.fmt_price(threshold)}")
            self._log(f"[헷지 프로토콜] 현재 BE: ${self.fmt_price(current_be)}")

            # BE 안전성 체크: BE가 메인 평균가와 안전망의 익절비율% 기준을 넘었을 때 익절 실행
            # LONG: BE > 기준가 → BE가 너무 높아 헷지 축소 필요
            # SHORT: BE < 기준가 → BE가 너무 낮아 헷지 축소 필요
            be_needs_fix = current_be > threshold if self.side_mode == "LONG" else current_be < threshold
            if be_needs_fix:
                self._log(f"[헷지 프로토콜] ✓ BE 안전 조건 충족!")
                self._log(f"[헷지 프로토콜] 헷지 익절 실행")
                self._log(f"[헷지 프로토콜] ========================================")
                self._execute_hedge_protocol_take_profit(current_price)
            else:
                # BE 안전 조건 미충족 - 프로토콜 비활성화 (다음 H 체결 시 재검증)
                self._log(f"[헷지 프로토콜] ✗ BE 안전 조건 미충족")
                self._log(f"[헷지 프로토콜] 비활성화 - 다음 H 체결 시 재검증")
                self._log(f"[헷지 프로토콜] ========================================")
                self.hedge_protocol_active = False  # 비활성화 (executed는 False 유지 → 다음 H 체결 시 재활성화 가능)
                self.hedge_protocol_lowest_price = None  # 최저가 리셋
                return

        except Exception as e:
            self._log(f"[헷지 프로토콜] 되돌림 체크 오류: {e}")
            import traceback
            traceback.print_exc()

    def _execute_hedge_protocol_take_profit(self, current_price=0):
        """헷지 프로토콜: Break Even이 목표 위치가 되도록 헷지 수량 일부 익절

        목표: Break Even이 메인 진입 평균가와 안전망 가격의 중간(익절 비율%)에 위치하도록
        """
        try:
            # 헷지 포지션 조회
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"
            hedge_qty = 0
            hedge_avg_price = 0

            self._log(f"[헷지 프로토콜 디버그] 찾는 헷지 Side: {hedge_side}")
            self._log(f"[헷지 프로토콜 디버그] 현재 포지션 데이터: {self.current_position_data}")

            for pos_key, pos_data in self.current_position_data.items():
                pos_side = pos_data.get('side', pos_data.get('positionSide'))
                self._log(f"[헷지 프로토콜 디버그] 포지션 키: {pos_key}, Side: {pos_side}, Amount: {pos_data.get('amount')}")
                if pos_side == hedge_side:
                    hedge_qty = abs(float(pos_data.get('amount', 0)))
                    hedge_avg_price = float(pos_data.get('entry_price', pos_data.get('entry', 0)))
                    self._log(f"[헷지 프로토콜 디버그] 헷지 포지션 발견! 수량: {hedge_qty}, 평균가: ${self.fmt_price(hedge_avg_price)}")
                    break

            if hedge_qty == 0 or hedge_avg_price == 0:
                self._log(f"[헷지 프로토콜] 헷지 포지션 없음 - 익절 스킵")
                self.hedge_protocol_executed = True
                self.hedge_protocol_active = False
                return

            # 메인 포지션 정보 조회
            main_qty = 0
            main_avg_price = 0
            for pos_key, pos_data in self.current_position_data.items():
                pos_side = pos_data.get('side', pos_data.get('positionSide'))
                if pos_side == self.side_mode:
                    main_qty = abs(float(pos_data.get('amount', 0)))
                    main_avg_price = float(pos_data.get('entry_price', pos_data.get('entry', 0)))
                    break

            if main_qty == 0 or main_avg_price == 0:
                self._log(f"[헷지 프로토콜] 메인 포지션 정보 없음 - 익절 스킵")
                self.hedge_protocol_executed = True
                self.hedge_protocol_active = False
                return

            # 안전망 가격 조회 (hedge_safety_order_price)
            safety_net_price = getattr(self, 'hedge_safety_order_price', None)

            if safety_net_price is None or safety_net_price == 0:
                self._log(f"[헷지 프로토콜] 안전망 가격 없음 - 단순 비율 방식 사용")
                # Fallback: 단순 비율 방식
                tp_qty = hedge_qty * (self.hedge_protocol_tp_ratio / 100.0)
            else:
                # 현재 Break Even 계산
                current_be = (main_qty * main_avg_price - hedge_qty * hedge_avg_price) / (main_qty - hedge_qty)

                # 목표 Break Even 계산: 메인 진입가와 안전망의 N% 위치
                if self.side_mode == "LONG":
                    target_be = main_avg_price + (safety_net_price - main_avg_price) * (self.hedge_protocol_tp_ratio / 100.0)
                else:  # SHORT
                    target_be = main_avg_price - (main_avg_price - safety_net_price) * (self.hedge_protocol_tp_ratio / 100.0)

                self._log(f"[헷지 프로토콜] 메인 진입가: ${self.fmt_price(main_avg_price)}")
                self._log(f"[헷지 프로토콜] 헷지 진입가: ${self.fmt_price(hedge_avg_price)}")
                self._log(f"[헷지 프로토콜] 현재 Break Even: ${self.fmt_price(current_be)}")
                self._log(f"[헷지 프로토콜] 안전망 가격: ${self.fmt_price(safety_net_price)}")
                self._log(f"[헷지 프로토콜] 목표 Break Even ({self.hedge_protocol_tp_ratio}%): ${self.fmt_price(target_be)}")

                # 현재 BE가 이미 목표보다 안전한지 확인
                # LONG 모드: 현재 BE가 목표 BE보다 낮으면 이미 안전 (헷지 익절 시 BE는 더 내려감)
                # SHORT 모드: 현재 BE가 목표 BE보다 높으면 이미 안전 (헷지 익절 시 BE는 더 올라감)
                already_safe = False
                if self.side_mode == "LONG":
                    if current_be <= target_be:
                        self._log(f"[헷지 프로토콜] 현재 BE({self.fmt_price(current_be)})가 목표 BE({self.fmt_price(target_be)}) 이하")
                        self._log(f"[헷지 프로토콜] 이미 안전한 상태 → 헷지 프로토콜 스킵")
                        already_safe = True
                else:  # SHORT
                    if current_be >= target_be:
                        self._log(f"[헷지 프로토콜] 현재 BE({self.fmt_price(current_be)})가 목표 BE({self.fmt_price(target_be)}) 이상")
                        self._log(f"[헷지 프로토콜] 이미 안전한 상태 → 헷지 프로토콜 스킵")
                        already_safe = True

                if already_safe:
                    # 이미 안전 → 프로토콜 실행하지 않음
                    self.hedge_protocol_executed = True
                    self.hedge_protocol_active = False
                    return

                # 목표 BE가 실현 가능한지 확인
                # 헷지 익절 시 BE는 메인 평균가 방향으로 이동
                # LONG 모드: BE는 내려가므로 목표 BE > 헷지 평균가여야 도달 가능
                # SHORT 모드: BE는 올라가므로 목표 BE < 헷지 평균가여야 도달 가능
                target_achievable = True
                if self.side_mode == "LONG":
                    if target_be < hedge_avg_price:
                        self._log(f"[헷지 프로토콜] 목표 BE({self.fmt_price(target_be)})가 헷지 평균가({self.fmt_price(hedge_avg_price)})보다 낮음")
                        self._log(f"[헷지 프로토콜] 익절로는 도달 불가 → 단순 비율 방식({self.hedge_protocol_tp_ratio}%) 사용")
                        target_achievable = False
                else:  # SHORT
                    if target_be > hedge_avg_price:
                        self._log(f"[헷지 프로토콜] 목표 BE({self.fmt_price(target_be)})가 헷지 평균가({self.fmt_price(hedge_avg_price)})보다 높음")
                        self._log(f"[헷지 프로토콜] 익절로는 도달 불가 → 단순 비율 방식({self.hedge_protocol_tp_ratio}%) 사용")
                        target_achievable = False

                if not target_achievable:
                    # 목표 도달 불가 → 단순 비율 방식 사용
                    tp_qty = hedge_qty * (self.hedge_protocol_tp_ratio / 100.0)
                    self._log(f"[헷지 프로토콜] 단순 비율 익절 수량: {tp_qty:.4f} (헷지 {hedge_qty}의 {self.hedge_protocol_tp_ratio}%)")
                else:
                    # 익절 수량 역산
                    # Break Even = (main_qty × main_avg - (hedge_qty - tp_qty) × hedge_avg) / (main_qty - (hedge_qty - tp_qty))
                    # target_be = (main_qty × main_avg - hedge_qty × hedge_avg + tp_qty × hedge_avg) / (main_qty - hedge_qty + tp_qty)
                    # tp_qty × (target_be - hedge_avg) = main_qty × (main_avg - target_be) - hedge_qty × (hedge_avg - target_be)

                    numerator = main_qty * (main_avg_price - target_be) - hedge_qty * (hedge_avg_price - target_be)
                    denominator = target_be - hedge_avg_price

                    if abs(denominator) < 0.0001:
                        self._log(f"[헷지 프로토콜] 계산 불가 (분모가 0에 가까움) - 단순 비율 방식 사용")
                        tp_qty = hedge_qty * (self.hedge_protocol_tp_ratio / 100.0)
                    else:
                        tp_qty = numerator / denominator

                        # 음수이거나 헷지 수량보다 크면 제한
                        if tp_qty < 0:
                            self._log(f"[헷지 프로토콜] 계산된 수량이 음수 ({tp_qty:.4f}) → 헷지 전체 청산")
                            tp_qty = hedge_qty
                        elif tp_qty > hedge_qty:
                            self._log(f"[헷지 프로토콜] 계산된 수량({tp_qty:.4f})이 헷지({hedge_qty})보다 큼 → 헷지 전체 청산")
                            tp_qty = hedge_qty
                        else:
                            self._log(f"[헷지 프로토콜] 계산된 익절 수량: {tp_qty:.4f} (헷지 {hedge_qty}의 {(tp_qty/hedge_qty*100):.1f}%)")

            # 수량 조정
            qty_step = float(self.symbol_info.get('lotSizeFilter', {}).get('qtyStep', '0.001'))
            qty_precision = trading_utils.count_decimal_places(qty_step)
            min_order_qty = float(self.symbol_info.get('lotSizeFilter', {}).get('minOrderQty', '0.001'))

            tp_qty = trading_utils.adjust_quantity(tp_qty, qty_step, qty_precision, min_order_qty)

            if tp_qty < min_order_qty:
                self._log(f"[헷지 프로토콜] 익절 수량({tp_qty})이 최소 주문 수량 미만 - 스킵")
                self.hedge_protocol_executed = True
                self.hedge_protocol_active = False
                return

            # 시장가로 헷지 익절 (포지션 일부 청산)
            close_side = "BUY" if self.side_mode == "LONG" else "SELL"

            self._log(f"[헷지 프로토콜] 헷지 익절 실행: {close_side} {tp_qty} (현재 헷지: {hedge_qty})")

            # 헷지 포지션 일부 청산
            self.execute_trade_signal.emit(self.symbol, close_side, str(tp_qty), True)

            # 탈출 수량 저장 (H4에서 재진입 시 사용)
            self.hedge_protocol_exited_qty = tp_qty

            # 헷지 프로토콜 실행 완료 표시 (단계당 1회만)
            self.hedge_protocol_executed = True
            self.hedge_protocol_active = False

            self._log(f"[헷지 프로토콜] 익절 완료 - 탈출 수량: {tp_qty}")
            self._log(f"[헷지 프로토콜] 비활성화 (단계당 1회 실행 완료)")

            # Statistics 탭: 헷지 프로토콜 발동 기록 (추정 손익 포함)
            hedge_avg = getattr(self, 'hedge_protocol_hedge_avg_price', 0)
            if current_price > 0 and hedge_avg > 0:
                if self.side_mode == "LONG":
                    estimated_pnl = tp_qty * (hedge_avg - current_price)
                else:
                    estimated_pnl = tp_qty * (current_price - hedge_avg)
            else:
                estimated_pnl = 0.0
            self.hedge_protocol_fired.emit(self.current_step, estimated_pnl)

            # 미발동 H 트리거 수량을 H4에 합산
            self._consolidate_unfired_hedge_to_last()

            # 프론트로드 최종단계: 재진입 모니터링 설정 (H4 가격에서 재진입)
            if self.hedge_frontload_final_step and self.current_step + 1 >= self.total_steps:
                if self.hedge_trigger_prices and len(self.hedge_trigger_prices) >= 4:
                    h4_price = self.hedge_trigger_prices[3][0]
                    self.hedge_frontload_reentry_pending = True
                    self.hedge_frontload_reentry_price = h4_price
                    self.hedge_frontload_reentry_qty = tp_qty
                    self._log(f"[헷지 프론트로드] 재진입 모니터링 설정: 가격 ${self.fmt_price(h4_price)}, 수량 {tp_qty}")

            # 헷지 안전망 주문 업데이트 (남은 헷지 수량으로 재설정)
            if self.hedge_liq_protection_enabled:
                self._log(f"[헷지 프로토콜] 헷지 안전망 주문 업데이트 시작 (익절 후)")
                self._setup_emergency_exit_line()

        except Exception as e:
            self._log(f"[헷지 프로토콜] 익절 실행 오류: {e}")
            import traceback
            traceback.print_exc()

    def _consolidate_unfired_hedge_to_last(self):
        """헷지 프로토콜 익절 후: 미발동 H 트리거 수량을 마지막 H(H4)에 합산

        H4를 제외한 미발동 트리거의 수량을 H4에 합산하고 executed로 마킹하여
        개별 발동을 방지한다. H4 발동 시 합산 수량으로 한번에 처리된다.
        """
        if not self.hedge_trigger_prices or len(self.hedge_trigger_prices) < 2:
            return

        # 마지막 트리거 (H4) 찾기
        last_idx = len(self.hedge_trigger_prices) - 1
        last_trigger = self.hedge_trigger_prices[last_idx]

        # H4도 이미 발동됐으면 합산 불필요
        if last_trigger[2]:
            return

        # 미발동 H 트리거 (H4 제외) 수량 합산
        consolidated_qty = 0
        consolidated_names = []
        for i, trigger in enumerate(self.hedge_trigger_prices):
            if i == last_idx:
                continue  # H4는 스킵
            if not trigger[2]:  # 미발동인 것만
                consolidated_qty += trigger[1]
                consolidated_names.append(f"H{i+1}({trigger[1]:.4f})")
                trigger[2] = True  # executed 마킹 (개별 발동 방지)

        if consolidated_qty <= 0:
            return

        # H4에 수량 합산
        original_h4_qty = last_trigger[1]
        last_trigger[1] = original_h4_qty + consolidated_qty

        self._log(f"[헷지 프로토콜] 미발동 헷지 합산: {', '.join(consolidated_names)} → H{last_idx+1}")
        self._log(f"[헷지 프로토콜] H{last_idx+1} 수량: {original_h4_qty:.4f} → {last_trigger[1]:.4f} (+{consolidated_qty:.4f})")

        # GUI 마커/Insight 탭 업데이트
        self.hedge_triggers_updated.emit(self.hedge_trigger_prices, self.side_mode, self.current_step)

    def _update_hedge_protocol_avg_price(self):
        """헷지 프로토콜: 헷지 포지션 평균가 업데이트 (WebSocket 포지션 데이터 사용)"""
        try:
            hedge_side = "SHORT" if self.side_mode == "LONG" else "LONG"
            pos_key = f"{self.symbol}_{hedge_side}"

            # WebSocket으로 실시간 업데이트된 포지션 데이터 사용
            hedge_position = self.current_position_data.get(pos_key, {})
            avg_price = float(hedge_position.get('entry_price', hedge_position.get('entry', 0)))

            if avg_price > 0:
                self.hedge_protocol_hedge_avg_price = avg_price
                self._log(f"[헷지 프로토콜] 헷지 평균가 업데이트: ${self.fmt_price(avg_price)}")
            else:
                self._log(f"[헷지 프로토콜] 경고: 헷지 포지션 평균가 조회 실패 (entry: {avg_price})")

        except Exception as e:
            self._log(f"[헷지 프로토콜] 평균가 업데이트 오류: {e}")

    def _handle_hedge_protocol_reentry_on_h4(self, h4_qty):
        """헷지 프로토콜: H4 체결 시 탈출했던 수량 재진입

        Args:
            h4_qty: H4 원래 수량

        Returns:
            float: H4 + 재진입 수량
        """
        if self.hedge_protocol_exited_qty > 0:
            total_qty = h4_qty + self.hedge_protocol_exited_qty
            self._log(f"[헷지 프로토콜] H4 재진입: 원래 수량 {h4_qty} + 탈출 수량 {self.hedge_protocol_exited_qty} = {total_qty}")
            return total_qty
        return h4_qty