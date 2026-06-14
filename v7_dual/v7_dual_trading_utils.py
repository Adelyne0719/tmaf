# v7_trading_utils.py
import math
import logging
import threading
from decimal import Decimal, getcontext, ROUND_DOWN, ROUND_UP

# --- 로깅 설정 ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
getcontext().prec = 28 # Decimal 정밀도 설정

# --- 스레드별 로그 프리픽스 ---
_thread_local = threading.local()

def set_log_prefix(prefix):
    """현재 스레드의 로그 프리픽스 설정 ([L] 또는 [S])"""
    _thread_local.log_prefix = prefix

def _lp():
    """현재 스레드의 로그 프리픽스 반환"""
    return getattr(_thread_local, 'log_prefix', '')

# --- MockConfig (test_entry_calculation.py에서 복사) ---
class ConfigHelper:
    """
    test_entry_calculation.py의 MockConfig를 기반으로,
    전략 파라미터 딕셔너리를 객체처럼 사용할 수 있게 해주는 헬퍼 클래스입니다.
    """
    def __init__(self, settings_dict):
        self._settings = settings_dict

    def __getattr__(self, name):
        return self._settings.get(name)

# --- 유틸리티 함수 (test_entry_calculation.py에서 복사) ---

def count_decimal_places(number_str):
    """문자열 형태의 숫자의 소수점 이하 자릿수를 반환"""
    try:
        if isinstance(number_str, (int, float)): number_str = str(number_str)
        if 'e' in number_str.lower():
            d = Decimal(number_str)
            if d.as_tuple().exponent < 0: return abs(d.as_tuple().exponent)
            else: return 0
        else:
            d = Decimal(number_str)
            if d == d.to_integral_value(): return 0
            parts = number_str.split('.')
            if len(parts) == 2: return len(parts[1].rstrip('0'))
            else: return 0
    except Exception as e: logging.error(f"{_lp()}소수점 자릿수 계산 오류: {number_str}, 오류: {e}"); return 0

def adjust_quantity(quantity, step_size_str, precision, min_qty_str):
    """수량을 stepSize에 맞춰 내림 처리하고, 최소 수량 확인 후 포맷팅된 float 반환"""
    try:
        step_size = Decimal(str(step_size_str))
        min_qty = Decimal(str(min_qty_str))
        qty = Decimal(str(quantity))

        if qty <= 0: return 0.0
        if step_size <= 0: return 0.0

        adjusted_qty = (qty // step_size) * step_size

        if adjusted_qty < min_qty:
            # [참고] test_entry_calculation.py와 달리, 최소 수량보다 작으면 0을 반환하여
            # 첫 스텝(q0, q1)이 0이 되는 것을 방지하고, q1이 min_qty가 되도록 유도합니다.
            # (만약 min_qty로 설정하면, 모든 스텝이 min_qty가 될 수 있음)
            logging.warning(f"{_lp()}조정된 수량({adjusted_qty})이 최소 주문 수량({min_qty})보다 작아 0.0으로 처리합니다.")
            return 0.0

        # qtyStep의 소수점 자릿수로 포맷팅 (내림 처리는 이미 위에서 완료)
        # precision이 제대로 전달되지 않을 경우를 대비해 step_size에서 직접 계산
        step_decimal_places = abs(step_size.as_tuple().exponent)
        quantized_qty = adjusted_qty.quantize(Decimal('1e-' + str(step_decimal_places)), rounding=ROUND_DOWN)
        quantized_qty = float(quantized_qty)

        return quantized_qty

    except Exception as e:
        logging.error(f"{_lp()}수량 조정 오류: qty={quantity}, step={step_size_str}, prec={precision}, min={min_qty_str}, error={e}", exc_info=True)
        return None

# --- 핵심 함수 (test_entry_calculation.py에서 복사 및 수정) ---

def calculate_entry_quantities(
    category: str, 
    symbol_info: dict, 
    min_order_qty: float, 
    current_balance: float, 
    mark_price: float,
    config: ConfigHelper
    ):
    """
    진입 수량을 모드(USDT-M/COIN-M)에 따라 다르게 계산합니다.
    (async를 제거하고 동기식으로 변경)
    """
    logging.info(f"{_lp()}'{category}' 모드에 대한 진입 수량 계산 시작...")

    entry_qty_list = []
    cumul_entry_qty_list = []
    success = False

    if category == 'linear': # USDT-M
        if min_order_qty is None or not symbol_info:
            logging.error(f"{_lp()}USDT-M 진입 수량 계산 불가: 입력 데이터 부족.")
            return False, ["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS

        try:
            step_size = symbol_info['lotSizeFilter']['qtyStep']
            qty_precision = count_decimal_places(step_size)
            min_qty_str = symbol_info['lotSizeFilter']['minOrderQty']

            q_raw = [Decimal('0')] * config.STEPS
            cumulative_sum_raw = Decimal('0')

            q1_d_raw = Decimal(str(min_order_qty))
            q_raw[1] = q1_d_raw

            if config.ENTRY_START <= 0: raise ValueError("ENTRY_START는 0보다 커야 합니다.")
            q0_d_raw = q1_d_raw / Decimal(str(config.ENTRY_START))
            q_raw[0] = q0_d_raw

            cumulative_sum_raw = q0_d_raw + q1_d_raw

            if config.STEPS > 2:
                ratio_steps = config.STEPS - 2
                for i in range(2, config.STEPS):
                    k = i - 2
                    x = Decimal('1.0') if ratio_steps <= 1 else Decimal(str(k)) / Decimal(str(ratio_steps - 1))
                    ratio_multiplier_d = Decimal(str(config.ENTRY_START)) + (Decimal(str(config.ENTRY_END)) - Decimal(str(config.ENTRY_START))) * (x ** Decimal(str(config.ENTRY_EXPONENT)))
                    qi_d_raw = cumulative_sum_raw * ratio_multiplier_d
                    q_raw[i] = qi_d_raw
                    cumulative_sum_raw += qi_d_raw

            sum_q_raw = sum(q_raw)
            if sum_q_raw <= 0: raise ValueError("원시 기본 수량 합계가 0 이하")

            total_margin = (current_balance * config.BALANCE_USAGE_PERCENTAGE) * config.TARGET_LEVERAGE
            logging.info(f"{_lp()}자금 사용률({config.BALANCE_USAGE_PERCENTAGE * 100}%) 적용. 실제 사용될 잔고: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}")

            if mark_price <= 0: raise ValueError("Mark Price 오류")
            target_total_quantity = total_margin / mark_price

            scaling_factor = Decimal(str(target_total_quantity)) / sum_q_raw
            logging.info(f"{_lp()}Target Quantity: {target_total_quantity}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            cumulative_sum_final = 0.0
            cumulative_quantities_final = []

            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)
                
                # [수정] adjust_quantity는 최소 수량보다 작으면 0을 반환할 수 있음
                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)

                # 첫 번째 스텝(q0)이 0이면, 두 번째 스텝(q1)을 최소 수량으로 강제 설정
                if i == 1 and final_quantities[0] == 0.0 and q_final_adjusted == 0.0:
                    logging.warning(f"{_lp()}q0, q1이 모두 0입니다. q1을 min_qty({min_qty_str})로 강제 설정합니다.")
                    q_final_adjusted = float(min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)
                cumulative_sum_final += q_final_adjusted
                cumulative_quantities_final.append(round(cumulative_sum_final, qty_precision))

            entry_qty_list = final_quantities
            cumul_entry_qty_list = cumulative_quantities_final
            success = True

        except Exception as e:
            logging.error(f"{_lp()}USDT-M 진입 수량 계산 중 오류 발생: {e}", exc_info=True)
            entry_qty_list, cumul_entry_qty_list = ["계산 오류"] * config.STEPS, ["계산 오류"] * config.STEPS

        finally:
            return success, entry_qty_list, cumul_entry_qty_list

    elif category == 'inverse': # COIN-M
        contract_size_str = symbol_info['lotSizeFilter'].get('contractSize') # Bybit는 lotSizeFilter 내부에 있음

        if min_order_qty is None or not symbol_info or not contract_size_str:
            logging.error(f"{_lp()}COIN-M 진입 수량 계산 불가: 입력 데이터 또는 contractSize 정보 부족.")
            return False, ["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS

        try:
            step_size = symbol_info['lotSizeFilter'].get('qtyStep', '1')
            qty_precision = 0 # 계약은 정수
            min_qty_str = symbol_info['lotSizeFilter'].get('minOrderQty', '1')

            q_raw = [Decimal('0')] * config.STEPS
            cumulative_sum_raw = Decimal('0')

            q1_d_raw = Decimal(str(min_order_qty))
            q_raw[1] = q1_d_raw

            if config.ENTRY_START <= 0: raise ValueError("ENTRY_START는 0보다 커야 합니다.")
            q0_d_raw = q1_d_raw / Decimal(str(config.ENTRY_START))
            q_raw[0] = q0_d_raw

            cumulative_sum_raw = q0_d_raw + q1_d_raw

            if config.STEPS > 2:
                ratio_steps = config.STEPS - 2
                for i in range(2, config.STEPS):
                    k = i - 2
                    x = Decimal('1.0') if ratio_steps <= 1 else Decimal(str(k)) / Decimal(str(ratio_steps - 1))
                    ratio_multiplier_d = Decimal(str(config.ENTRY_START)) + (Decimal(str(config.ENTRY_END)) - Decimal(str(config.ENTRY_START))) * (x ** Decimal(str(config.ENTRY_EXPONENT)))
                    qi_d_raw = cumulative_sum_raw * ratio_multiplier_d
                    q_raw[i] = qi_d_raw
                    cumulative_sum_raw += qi_d_raw

            sum_q_raw = sum(q_raw)
            if sum_q_raw <= 0: raise ValueError("원시 기본 계약 수 합계가 0 이하")

            if mark_price <= 0: raise ValueError(f"Mark Price 조회 실패 또는 0 이하: {mark_price}")
            
            total_balance_in_usd = current_balance * mark_price
            total_position_in_usd = total_balance_in_usd * config.BALANCE_USAGE_PERCENTAGE * config.TARGET_LEVERAGE
            contract_value_in_usd = float(contract_size_str)
            if contract_value_in_usd <= 0: raise ValueError("Contract value must be positive")
            target_total_contracts = total_position_in_usd / contract_value_in_usd

            logging.info(f"{_lp()}목표 총 계약 수: {target_total_contracts:.4f} (사용 자산: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}, "
                         f"총 포지션 가치: ${total_position_in_usd:,.2f}, 레버리지: {config.TARGET_LEVERAGE}x, 계약가치: ${contract_value_in_usd})")

            scaling_factor = Decimal(str(target_total_contracts)) / sum_q_raw
            logging.info(f"{_lp()}Target Contracts: {target_total_contracts}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            current_cumul_sum = 0.0
            cumul_entry_qty_list_calc = []

            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)

                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)
                
                if i == 1 and final_quantities[0] == 0.0 and q_final_adjusted == 0.0:
                    logging.warning(f"{_lp()}q0, q1이 모두 0입니다. q1을 min_qty({min_qty_str})로 강제 설정합니다.")
                    q_final_adjusted = float(min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 계약 수 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)

                current_cumul_sum += q_final_adjusted
                cumul_entry_qty_list_calc.append(round(current_cumul_sum)) # 계약은 정수 누적

            entry_qty_list = final_quantities
            cumul_entry_qty_list = cumul_entry_qty_list_calc
            success = True

        except Exception as e:
            logging.error(f"{_lp()}COIN-M 진입 수량 계산 중 오류 발생: {e}", exc_info=True)
            entry_qty_list, cumul_entry_qty_list = ["계산 오류"] * config.STEPS, ["계산 오류"] * config.STEPS

        finally:
            return success, entry_qty_list, cumul_entry_qty_list
    
    else:
        logging.error(f"{_lp()}지원되지 않는 거래 모드입니다: {category}")
        return False, ["모드 오류"] * config.STEPS, ["모드 오류"] * config.STEPS


def adjust_price(price, tick_size_str, price_precision):
    """가격을 tickSize에 맞춰 내림 처리하고 포맷팅된 float 반환"""
    try:
        tick_size = Decimal(str(tick_size_str))
        price_dec = Decimal(str(price))

        if tick_size <= 0:
            return float(price_dec)

        # tickSize로 내림 처리
        adjusted_price = (price_dec // tick_size) * tick_size

        # 정밀도에 맞춰 quantize
        quantized_price = adjusted_price.quantize(Decimal('1e-' + str(price_precision)), rounding=ROUND_DOWN)

        return float(quantized_price)

    except Exception as e:
        logging.error(f"{_lp()}가격 조정 오류: price={price}, tick={tick_size_str}, prec={price_precision}, error={e}", exc_info=True)
        return float(price)


def calculate_next_step_entry_price(avg_entry_price, liq_price, hedge_percent):
    """
    다음 단계 진입가 계산

    Args:
        avg_entry_price: 현재 평균 진입가
        liq_price: 청산가
        hedge_percent: 헷지 퍼센트 (0-100)

    Returns:
        float: 다음 단계 진입가

    공식:
        진입가 = 평균진입가 - (평균진입가 - 청산가) × (헷지% / 100)
    """
    price_range = avg_entry_price - liq_price
    entry_price = avg_entry_price - (price_range * (hedge_percent / 100.0))
    return entry_price


def calculate_hedge_split_orders(total_hedge_qty, current_price, next_entry_price, num_splits=4, ratio=0.5):
    """
    헷지 수량을 지수 감소로 분할하여 가격별 주문 목록 생성

    Args:
        total_hedge_qty: 총 헷지 수량
        current_price: 현재 가격 (평균 진입가)
        next_entry_price: 다음 단계 진입가
        num_splits: 분할 개수 (기본값: 4)
        ratio: 공비 (기본값: 0.5)

    Returns:
        list: [(price, quantity), ...] 형태의 리스트 (가격 내림차순)
    """
    try:
        # 가격 구간 계산
        price_range = current_price - next_entry_price
        price_step = price_range / num_splits

        # 지수 감소 비율 계산 (공비 ratio)
        weights = []
        for i in range(num_splits):
            weight = ratio ** i  # 1.0, 0.5, 0.25, 0.125
            weights.append(weight)

        total_weight = sum(weights)

        # 가격 및 수량 목록 생성
        orders = []
        for i in range(num_splits):
            # 가격: 현재가에서 점점 아래로
            price = current_price - (price_step * (i + 1))

            # 수량: 지수 감소
            quantity = total_hedge_qty * (weights[i] / total_weight)

            orders.append((price, quantity))

        return orders

    except Exception as e:
        logging.error(f"{_lp()}헷지 분할 주문 계산 오류: {e}", exc_info=True)
        # 오류 시 균등 분할
        return [(current_price - (price_range / num_splits * (i + 1)), total_hedge_qty / num_splits) for i in range(num_splits)]


def calculate_profit_target_ratios(start_percent, end_percent, total_steps, ratio=0.7):
    """
    단계별 익절 비율 리스트 생성 (지수 감소)

    Args:
        start_percent: 시작 익절 비율 (%, Step 0)
        end_percent: 종료 익절 비율 (%, 마지막 Step)
        total_steps: 전체 단계 수
        ratio: 공비 (기본값: 0.7, 사용되지 않음 - 자동 계산됨)

    Returns:
        list: [60.0, 48.66, 39.43, ...] 형태의 익절 비율 리스트 (%)

    예시:
        calculate_profit_target_ratios(60, 30, 10, 0.7)
        → Step 0: 60%, Step 9: 30%로 지수 감소
    """
    try:
        if total_steps <= 1:
            return [start_percent]

        # 공비를 역산하여 정확히 마지막 단계에서 end_percent가 되도록 함
        # 공식: r^(n-1) = end_percent / start_percent
        # r = (end_percent / start_percent)^(1/(n-1))

        calculated_ratio = (end_percent / start_percent) ** (1.0 / (total_steps - 1))

        ratios = []
        current_value = start_percent

        for step in range(total_steps):
            ratios.append(round(current_value, 4))
            current_value *= calculated_ratio

        logging.info(f"{_lp()}익절 비율 리스트 생성: 시작={start_percent}%, 종료={end_percent}%, 계산된 공비={calculated_ratio:.6f}, Steps={total_steps}")
        logging.info(f"{_lp()}익절 비율: {ratios}")

        return ratios

    except Exception as e:
        logging.error(f"{_lp()}익절 비율 리스트 생성 오류: {e}", exc_info=True)
        # 오류 시 균등 분할 반환
        step_size = (start_percent - end_percent) / (total_steps - 1) if total_steps > 1 else 0
        return [start_percent - (step_size * i) for i in range(total_steps)]


def calculate_hedge_quantity(entry_quantity, current_step, total_steps, cumulative_entry_qty, previous_cumulative_hedge_qty=0, hedge_start_percent=0, hedge_end_percent=100, hedge_exponent=3.0, test_mode=False, frontload_final_step=False):
    """
    헷지 수량을 계산합니다 (선형 방식).

    Args:
        entry_quantity: 현재 단계의 진입 수량
        current_step: 현재 단계 (0부터 시작)
        total_steps: 전체 단계 수
        cumulative_entry_qty: 현재 단계까지의 누적 진입 수량
        previous_cumulative_hedge_qty: 이전 단계까지의 누적 헷지 수량 (기본값: 0)
        hedge_start_percent: 시작 헷지 퍼센트 (기본값: 0)
        hedge_end_percent: 종료 헷지 퍼센트 (기본값: 100)
        hedge_exponent: 헷지 곡선 지수 (사용 안 함, 하위 호환성 유지)
        test_mode: 테스트 모드 활성화 여부 (기본값: False) - 로깅용으로만 사용
        frontload_final_step: 최종단계-1에서 종료%에 도달 (기본값: False)

    Returns:
        float: 현재 단계의 헷지 수량 (증분)

    예시 (0% → 85%, 선형 방식):
        - Step 0: 0.00% → 헷지수량 = 0
        - Step 1: 9.44% → 선형 증가
        - Step 5: 47.22% → 중간 단계
        - Step 7: 66.11% → 후반부
        - Step 9: 85.00% → 최종 단계
        - 선형 방식: 각 단계별 헷지 증분이 메인 진입보다 작아 역전 방지
        - 테스트 모드: 헷지 비율은 동일하게 적용, 수량만 최소값 사용
    """
    try:
        if total_steps <= 1:
            # 단계가 1개 이하면 종료 퍼센트 사용
            hedge_percent = hedge_end_percent
        elif frontload_final_step and total_steps >= 3:
            # 프론트로드: 최종단계-1에서 종료%에 도달
            if current_step < total_steps - 1:
                # step 0 ~ step (N-2): (N-2)단계에 걸쳐 start→end 보간
                hedge_percent = hedge_start_percent + ((hedge_end_percent - hedge_start_percent) / (total_steps - 2)) * current_step
            else:
                # step (N-1): end%로 고정 (추가 진입분에 대해서만 헷지)
                hedge_percent = hedge_end_percent
        else:
            # 기존: step 0 ~ step (N-1) 전체에 걸쳐 보간
            hedge_percent = hedge_start_percent + ((hedge_end_percent - hedge_start_percent) / (total_steps - 1)) * current_step

        # 현재 단계까지의 누적 헷지 목표 수량 계산
        cumulative_target_hedge_qty = cumulative_entry_qty * (hedge_percent / 100.0)

        # 현재 단계의 증분 헷지 수량 = 누적 목표 - 이전 누적 헷지
        hedge_quantity = cumulative_target_hedge_qty - previous_cumulative_hedge_qty

        mode_label = "[테스트 모드] " if test_mode else ""
        logging.info(f"{_lp()}{mode_label}헷지 수량 계산 (선형): Step {current_step}/{total_steps-1}, 누적진입: {cumulative_entry_qty}, 헷지%: {hedge_percent:.2f}%, 누적목표: {cumulative_target_hedge_qty:.4f}, 증분헷지: {hedge_quantity:.4f}")

        return hedge_quantity

    except Exception as e:
        logging.error(f"{_lp()}헷지 수량 계산 오류: {e}", exc_info=True)
        return entry_quantity * (hedge_start_percent / 100.0)  # 기본값으로 시작 퍼센트 반환