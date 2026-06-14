"""
SetupAutoTradeThread: 자동매매 설정을 백그라운드에서 처리하는 스레드
"""
from PyQt5.QtCore import QThread, pyqtSignal
from decimal import Decimal, ROUND_UP
import v7_dual_trading_utils as trading_utils


class SetupAutoTradeThread(QThread):
    """
    'Start' 버튼 클릭 시, GUI가 멈추지 않도록
    헷지 모드/레버리지 설정, 자금 계산 등 I/O 작업을 백그라운드에서 처리합니다.
    """
    # (성공여부, 에러메시지, 계산된 파라미터 딕셔너리)
    setup_finished = pyqtSignal(bool, str, dict)

    # GUI 상태 라벨에 로그를 보내기 위한 시그널
    log_message = pyqtSignal(str)

    def __init__(self, api_module, category, symbol, balance_asset, balance_total, strategy_settings, side='long', parent=None):
        super().__init__(parent)
        self.api_module = api_module
        self.category = category # "linear" or "inverse"
        self.symbol = symbol
        self.balance_asset = balance_asset # "USDT"
        self.balance_total = balance_total # 204.28
        self.strategy_settings = strategy_settings
        self._lp = "[L]" if side == 'long' else "[S]"

        self.log_prefix = f"{self._lp} SetupAutoTradeThread"

    def _get_min_order_value(self, symbol):
        """
        코인별 최소 주문 금액(USDT)을 반환합니다.

        Bybit 거래소의 일반적인 최소 주문 금액:
        - BTC, ETH: 20 USDT
        - 기타 대부분: 5 USDT

        Args:
            symbol: 거래 심볼 (예: "BTCUSDT", "XRPUSDT")

        Returns:
            float: 최소 주문 금액 (USDT)
        """
        # BTC, ETH는 20 USDT
        high_value_symbols = ['BTC', 'ETH']

        # 심볼에서 기본 자산 추출 (예: "BTCUSDT" -> "BTC")
        base_asset = symbol.replace('USDT', '').replace('USDC', '').replace('BUSD', '')

        if base_asset in high_value_symbols:
            return 20.0
        else:
            return 5.0

    def run(self):
        trading_utils.set_log_prefix(self._lp)
        print(f"{self.log_prefix}: 자동매매 설정 스레드 시작...")
        params = {}
        try:
            # 0. 기존 포지션 확인 (포지션이 있으면 레버리지 설정 건너뛰기)
            has_existing_position = False
            try:
                positions = self.api_module.get_initial_positions()
                if positions:
                    for pos in positions:
                        if pos.get('symbol') == self.symbol:
                            pos_amt = abs(float(pos.get('positionAmt', 0)))
                            if pos_amt > 0:
                                has_existing_position = True
                                print(f"{self.log_prefix}: 기존 포지션 발견 ({self.symbol}): {pos_amt}")
                                break
            except Exception as e:
                print(f"{self.log_prefix}: 포지션 확인 오류 (무시하고 계속): {e}")

            # 1. 포지션 모드를 헤지 모드(3)로 변경
            self.log_message.emit("Status: <b style='color: yellow;'>1/5: 헷지 모드 설정 중...</b>")
            if not self.api_module.set_position_mode(self.category, self.symbol, mode=3):
                raise Exception("헷지 모드 설정 실패. (API 권한 확인)")

            # 2. 격리 마진 모드 및 레버리지 설정 (기존 포지션이 없을 때만)
            leverage = self.strategy_settings.get("TARGET_LEVERAGE", 15)
            if has_existing_position:
                # 포지션이 있으면 레버리지 변경 건너뛰기 (마진 부족으로 포지션 청산 방지)
                self.log_message.emit(f"Status: <b style='color: yellow;'>2/5: 레버리지 설정 건너뛰기 (기존 포지션 있음)</b>")
                print(f"{self.log_prefix}: 기존 포지션이 있어 레버리지 설정 건너뜀 (마진 부족 방지)")
            else:
                self.log_message.emit(f"Status: <b style='color: yellow;'>2/5: 마진 모드 및 레버리지({leverage}x) 설정 중...</b>")
                if not self.api_module.set_margin_and_leverage(self.category, self.symbol, margin_mode=1, leverage=leverage):
                    raise Exception("격리 마진 모드 또는 레버리지 설정 실패. API 권한을 확인하세요.")

            # 3. 거래 규칙 조회
            self.log_message.emit("Status: <b style='color: yellow;'>3/5: 거래 규칙 조회 중...</b>")

            # 4. 거래 규칙 조회
            self.log_message.emit("Status: <b style='color: yellow;'>4/6: 거래 규칙 조회 중...</b>")
            rules = self.api_module.get_instrument_info(self.category, self.symbol)
            if not rules:
                raise Exception("거래 규칙 조회 실패.")

            qty_step = float(rules['lotSizeFilter']['qtyStep'])
            min_order_qty = float(rules['lotSizeFilter']['minOrderQty'])

            # 5. 현재 가격 조회
            self.log_message.emit("Status: <b style='color: yellow;'>5/6: 현재 가격 조회 중...</b>")
            mark_price = self.api_module.get_mark_price(self.category, self.symbol)
            if mark_price == 0.0:
                raise Exception("현재 가격 조회 실패.")

            # 6. 자금 계산 (test_entry_calculation.py 로직 사용)
            self.log_message.emit("Status: <b style='color: yellow;'>6/6: 10단계 진입 수량 계산 중...</b>")

            # test_entry_calculation.py의 TEST_SETTINGS와 동일한 설정 객체 생성
            config_params = self.strategy_settings.copy()
            # 동적 값 추가
            config_params["BALANCE_ASSET"] = self.balance_asset
            # % 값을 0.0-1.0 비율로 변환
            config_params["BALANCE_USAGE_PERCENTAGE"] = config_params.get("BALANCE_USAGE_PERCENTAGE", 70.0) / 100.0
            strat_config = trading_utils.ConfigHelper(config_params)

            # Bybit API의 `rules` 딕셔너리가 `test_entry_calculation.py`의 `USDT_M_SYMBOL_INFO` 역할을 함
            # Bybit는 `lotSizeFilter` 내부에 정보가 있음
            if 'lotSizeFilter' not in rules:
                raise Exception(f"거래 규칙에 'lotSizeFilter'가 없습니다: {rules}")

            # [수정] Bybit는 minOrderQty, Binance는 minQty. Bybit 기준으로 통일 (lotSizeFilter)
            min_order_qty = float(rules['lotSizeFilter']['minOrderQty'])

            # 새 유틸리티 함수 호출
            success, entry_qty_list, cumul_qty_list = trading_utils.calculate_entry_quantities(
                category=self.category,
                symbol_info=rules, # API에서 받은 전체 규칙 전달
                min_order_qty=min_order_qty,
                current_balance=self.balance_total,
                mark_price=mark_price,
                config=strat_config
            )

            if not success:
                raise Exception(f"진입 수량 계산 실패. (로그 확인): {entry_qty_list[0]}")

            # 테스트 모드 확인
            test_mode = self.strategy_settings.get("TEST_QUANTITY_MODE", False)

            if test_mode:
                # 테스트 모드: 코인별 최소 주문 금액을 만족하는 수량 계산
                print(f"[{self.log_prefix}] 원본 진입 수량 목록: {entry_qty_list}")

                # 수량 정밀도 계산
                qty_precision = trading_utils.count_decimal_places(qty_step)

                # 코인별 최소 주문 금액 조회
                min_order_value = self._get_min_order_value(self.symbol)
                print(f"[{self.log_prefix}] [테스트 모드] {self.symbol} 최소 주문 금액: ${min_order_value} USDT")

                # 최소 주문 금액을 만족하는 수량 계산
                required_qty = min_order_value / mark_price

                # qtyStep에 맞춰 올림 처리 (최소 주문 금액을 확실히 만족하도록)
                required_qty_decimal = Decimal(str(required_qty))
                qty_step_decimal = Decimal(str(qty_step))

                # 올림 처리: (required_qty / qty_step).ceil() * qty_step
                test_qty = float((required_qty_decimal / qty_step_decimal).quantize(Decimal('1'), rounding=ROUND_UP) * qty_step_decimal)

                # minOrderQty보다 작으면 minOrderQty 사용
                if test_qty < min_order_qty:
                    test_qty = min_order_qty

                entry_qty_list = [test_qty] * strat_config.STEPS

                # 헷지 수량 목록 계산
                hedge_start = self.strategy_settings.get("HEDGE_START_PERCENT", 40)
                hedge_end = self.strategy_settings.get("HEDGE_END_PERCENT", 100)
                hedge_qty_list = []
                cumulative_entry = 0
                cumulative_hedge = 0
                for step in range(strat_config.STEPS):
                    cumulative_entry += test_qty
                    hedge_qty_raw = trading_utils.calculate_hedge_quantity(
                        test_qty, step, strat_config.STEPS,
                        cumulative_entry, cumulative_hedge,
                        hedge_start, hedge_end, test_mode,
                        frontload_final_step=self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False)
                    )
                    # 헷지 수량도 qtyStep에 맞춰 조정
                    hedge_qty_adjusted = trading_utils.adjust_quantity(
                        hedge_qty_raw, qty_step, qty_precision, min_order_qty
                    )
                    hedge_qty_list.append(hedge_qty_adjusted)
                    cumulative_hedge += hedge_qty_adjusted

                order_value = test_qty * mark_price
                print(f"[{self.log_prefix}] [테스트 모드] 최소 주문 금액({min_order_value} USDT)을 만족하는 수량: {test_qty} (주문 금액: ${order_value:.2f})")
                print(f"[{self.log_prefix}] [테스트 모드] 진입 수량 목록: {entry_qty_list}")
                print(f"[{self.log_prefix}] [테스트 모드] 헷지 수량 목록: {hedge_qty_list}")
                final_entry_qty = test_qty
            else:
                final_entry_qty = entry_qty_list[0]
                if final_entry_qty <= 0:
                    # 0번째가 0이면 1번째(최소수량)를 사용
                    final_entry_qty = entry_qty_list[1]

                # 수량 정밀도 계산
                qty_precision = trading_utils.count_decimal_places(qty_step)

                # 헷지 수량 목록 계산 (누적 기반)
                hedge_start = self.strategy_settings.get("HEDGE_START_PERCENT", 40)
                hedge_end = self.strategy_settings.get("HEDGE_END_PERCENT", 100)
                hedge_qty_list = []
                cumulative_entry = 0
                cumulative_hedge = 0
                for i, entry_qty in enumerate(entry_qty_list):
                    cumulative_entry += entry_qty
                    hedge_qty_raw = trading_utils.calculate_hedge_quantity(
                        entry_qty, i, strat_config.STEPS,
                        cumulative_entry, cumulative_hedge,
                        hedge_start, hedge_end, test_mode=False,
                        frontload_final_step=self.strategy_settings.get("HEDGE_FRONTLOAD_FINAL_STEP", False)
                    )
                    # 헷지 수량도 qtyStep에 맞춰 조정
                    hedge_qty_adjusted = trading_utils.adjust_quantity(
                        hedge_qty_raw, qty_step, qty_precision, min_order_qty
                    )
                    hedge_qty_list.append(hedge_qty_adjusted)
                    cumulative_hedge += hedge_qty_adjusted

                print(f"[{self.log_prefix}] 계산 완료. 진입 수량 10단계 목록: {entry_qty_list}")
                print(f"[{self.log_prefix}] 계산 완료. 헷지 수량 10단계 목록: {hedge_qty_list}")
                print(f"[{self.log_prefix}] 자동매매 시작 수량 (Step 0 또는 1): {final_entry_qty}")

            # 헷지 수량 분할 검증 (Step 1의 헷지 수량을 4분할했을 때 최소 주문 금액 확인)
            # Step 1 헷지 수량 (인덱스 1)
            if len(hedge_qty_list) > 1:
                step1_hedge_qty = hedge_qty_list[1]

                # 헷지 분할 주문 계산 (4개로 분할, 비율 0.5)
                # calculate_hedge_split_orders는 (price, quantity) 튜플 리스트를 반환
                # 여기서는 수량만 확인하면 되므로 임시 가격 사용
                hedge_split_orders = trading_utils.calculate_hedge_split_orders(
                    step1_hedge_qty, mark_price, mark_price * 0.95, num_splits=4, ratio=0.5
                )

                # 코인별 최소 주문 금액 조회
                min_order_value = self._get_min_order_value(self.symbol)
                print(f"[{self.log_prefix}] {self.symbol} 최소 주문 금액: ${min_order_value} USDT")

                # 각 분할 수량의 주문 금액 확인
                below_min_count = 0
                for i, (price, qty) in enumerate(hedge_split_orders):
                    # qtyStep에 맞춰 조정
                    adj_qty = trading_utils.adjust_quantity(qty, qty_step, qty_precision, min_order_qty)
                    order_value = adj_qty * mark_price

                    if order_value < min_order_value:
                        below_min_count += 1
                        print(f"[{self.log_prefix}] [경고] Step 1 헷지 트리거 {i+1}/4: 주문 금액 ${order_value:.2f} < 최소 ${min_order_value} (수량: {adj_qty})")

                if below_min_count > 0:
                    # 최소 주문 금액 이하인 주문이 있음 - 사용자 확인 필요
                    params['needs_user_confirmation'] = True
                    params['warning_message'] = f"주문 최소 금액({min_order_value} USDT) 이하인 헷지 주문이 {below_min_count}개 있습니다.\n추가 금액을 입금하거나 배율을 높이세요.\n그래도 진행하시겠습니까?"
                else:
                    params['needs_user_confirmation'] = False

            params['symbol'] = self.symbol
            params['entry_quantity'] = str(final_entry_qty)
            params['entry_qty_list'] = entry_qty_list
            params['hedge_qty_list'] = hedge_qty_list
            params['symbol_info'] = rules
            params['category'] = self.category

            # 모든 설정 완료
            self.setup_finished.emit(True, "", params)

        except Exception as e:
            print(f"{self.log_prefix} 오류: {e}")
            self.setup_finished.emit(False, str(e), {})
