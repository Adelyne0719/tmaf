import asyncio
import logging
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext
from unittest.mock import MagicMock, AsyncMock # Using unittest.mock for mocking

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
getcontext().prec = 28 # Set precision for Decimal operations

# --- Configuration Mock ---
class MockConfig:
    def __init__(self, settings):
        self._settings = settings

    def __getattr__(self, name):
        return self._settings.get(name)

# --- GUI Mock ---
class MockGui:
    def update_entry_lists(self, step_list, cumulative_list, precision):
        logging.info(f"[Mock GUI] Updating entry lists (Precision: {precision}):")
        logging.info(f"  Step Qty: {step_list}")
        logging.info(f"  Cumul Qty: {cumulative_list}")

# --- Binance Client Mock ---
class MockBinanceFuturesClient:
    def __init__(self, mode='USDT-M', mark_price_value=Decimal('50000.0')):
        self.mode = mode.upper()
        self._mark_price_value = mark_price_value
        logging.info(f"MockBinanceFuturesClient initialized for {self.mode} mode.")

    async def mark_price(self, symbol):
        logging.info(f"[Mock Client] Returning mark_price for {symbol}: {self._mark_price_value}")
        if self.mode == 'COIN-M':
            return [{'symbol': symbol, 'markPrice': str(self._mark_price_value)}]
        else:
            return {'symbol': symbol, 'markPrice': str(self._mark_price_value)}

# --- Functions copied/adapted from logic.py ---
config = None # Global config reference

def set_config_source(config_obj):
    global config
    config = config_obj
    logging.info("logic.py mock: Configuration source has been set.")

def count_decimal_places(number_str):
    try:
        if isinstance(number_str, (int, float)): number_str = str(number_str)
        if 'e' in number_str.lower():
            d = Decimal(number_str)
            return abs(d.as_tuple().exponent) if d.as_tuple().exponent < 0 else 0
        else:
            d = Decimal(number_str)
            if d == d.to_integral_value(): return 0
            parts = number_str.split('.')
            return len(parts[1].rstrip('0')) if len(parts) == 2 else 0
    except Exception as e:
        logging.error(f"Error counting decimal places for {number_str}: {e}")
        return 0

def adjust_quantity(quantity, step_size_str, precision, min_qty_str):
    """Adjusts quantity based on step size, precision, and min quantity."""
    try:
        step_size = Decimal(str(step_size_str))
        min_qty = Decimal(str(min_qty_str))
        # Ensure quantity is treated as Decimal for precision
        qty = Decimal(str(quantity))

        if qty <= 0: return 0.0
        if step_size <= 0:
             logging.warning("Step size is zero or negative, returning original quantity.")
             # Return as float matching expected output type
             return float(qty.quantize(Decimal('1e-' + str(precision)), rounding=ROUND_DOWN))


        # Adjust down to the nearest step size
        # Ensure step_size is used correctly in division
        adjusted_qty = (qty // step_size) * step_size

        # Check against minimum quantity *after* step size adjustment
        if adjusted_qty < min_qty:
             # If adjusted is less than min, the final quantity must be at least min_qty
             # The actual order quantity might need further checks depending on exact exchange rules
             # but for calculation purposes, we enforce the minimum threshold here.
             adjusted_qty = min_qty
             # Log only if the original qty wasn't already below min_qty
             if qty >= min_qty:
                 logging.warning(f"Adjusted quantity ({adjusted_qty}) below min ({min_qty}) after step size floor. Using min quantity.")


        # Quantize to the required precision using ROUND_DOWN (floor)
        quantized_qty = adjusted_qty.quantize(Decimal('1e-' + str(precision)), rounding=ROUND_DOWN)

        # Final check: Ensure the quantized result isn't less than min_qty
        # This can happen if min_qty itself isn't a multiple of step_size
        if quantized_qty < min_qty:
             # Reset to min_qty if quantization dropped it below minimum
             quantized_qty = min_qty
             # logging.warning(f"Quantization resulted in value ({quantized_qty}) < min_qty ({min_qty}). Resetting to min_qty.")


        return float(quantized_qty) # Return as float

    except Exception as e:
        logging.error(f"Error adjusting quantity: qty={quantity}, step={step_size_str}, prec={precision}, min={min_qty_str}, error={e}", exc_info=True)
        return None


# --- The function to test (MODIFIED VERSION) ---
# --- The function to test (MODIFIED VERSION - CORRECTED) ---
async def calculate_entry_quantities(client: MockBinanceFuturesClient, symbol: str, symbol_info: dict, min_order_qty: float, current_balance: float, gui: MockGui):
    """
    진입 수량을 모드(USDT-M/COIN-M)에 따라 다르게 계산합니다. (COIN-M 계산 로직 최종 수정)
    --- ✨ 수정: 스케일링 후 최종 단계에서 adjust_quantity 적용 ---
    --- ✨ 수정2: 누락된 cumulative_quantities_final 초기화 및 할당 추가 ---
    """
    current_mode = client.mode
    logging.info(f"'{current_mode}' 모드에 대한 진입 수량 계산 시작... (Modified Logic: Scale First)")

    entry_qty_list = []
    cumul_entry_qty_list = []
    success = False

    # --- 모드 분기 시작 ---
    if current_mode == 'USDT-M':
        # --- 1. USDT-M 모드 계산 로직 ---
        if min_order_qty is None or not symbol_info:
            logging.error("USDT-M 진입 수량 계산 불가: 입력 데이터 부족.")
            if gui: gui.update_entry_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 1)
            return False, [], []

        try:
            step_size = symbol_info['stepSize']
            qty_precision = symbol_info['quantityPrecision']
            min_qty_str = symbol_info['minQty']

            # --- ✨ 수정: Raw 값 계산 ---
            q_raw = [Decimal('0')] * config.STEPS # Use Decimal for raw calculations
            cumulative_sum_raw = Decimal('0')

            q1_d_raw = Decimal(str(min_order_qty))
            q_raw[1] = q1_d_raw

            if config.ENTRY_START <= 0: raise ValueError("ENTRY_START는 0보다 커야 합니다.")
            q0_d_raw = q1_d_raw / Decimal(str(config.ENTRY_START))
            q_raw[0] = q0_d_raw

            cumulative_sum_raw = q0_d_raw + q1_d_raw # Start with raw sum

            if config.STEPS > 2:
                ratio_steps = config.STEPS - 2
                for i in range(2, config.STEPS):
                    k = i - 2
                    x = Decimal('1.0') if ratio_steps <= 1 else Decimal(str(k)) / Decimal(str(ratio_steps - 1))
                    ratio_multiplier_d = Decimal(str(config.ENTRY_START)) + (Decimal(str(config.ENTRY_END)) - Decimal(str(config.ENTRY_START))) * (x ** Decimal(str(config.ENTRY_EXPONENT)))
                    qi_d_raw = cumulative_sum_raw * ratio_multiplier_d
                    q_raw[i] = qi_d_raw
                    cumulative_sum_raw += qi_d_raw # Update raw cumulative sum

            logging.debug(f"Raw base quantities (unadjusted): {[float(q) for q in q_raw]}")

            sum_q_raw = sum(q_raw) # Sum of unadjusted raw values
            if sum_q_raw <= 0: raise ValueError("원시 기본 수량 합계가 0 이하")

            # --- 목표 총 수량 계산 (기존과 동일) ---
            total_margin = (current_balance * config.BALANCE_USAGE_PERCENTAGE) * config.TARGET_LEVERAGE
            logging.info(f"자금 사용률({config.BALANCE_USAGE_PERCENTAGE * 100}%) 적용. 실제 사용될 잔고: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}")

            mark_price_data = await client.mark_price(symbol=symbol)
            mark_price = float(mark_price_data.get('markPrice')) if isinstance(mark_price_data, dict) else 0.0
            if mark_price <= 0: raise ValueError("Mark Price 오류")
            target_total_quantity = total_margin / mark_price

            # --- ✨ 수정: 스케일링 후 최종 조정 ---
            scaling_factor = Decimal(str(target_total_quantity)) / sum_q_raw
            logging.info(f"Target Quantity: {target_total_quantity}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            cumulative_sum_final = 0.0 # Use float for final accumulation
            # --- ✨✨✨ 누락된 초기화 추가 ✨✨✨ ---
            cumulative_quantities_final = []

            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)

                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)
                cumulative_sum_final += q_final_adjusted
                # Round cumulative sum based on precision
                cumulative_quantities_final.append(round(cumulative_sum_final, qty_precision)) # 이제 에러 없음

            entry_qty_list = final_quantities
            # --- ✨✨✨ 누락된 할당 추가 ✨✨✨ ---
            cumul_entry_qty_list = cumulative_quantities_final

            logging.info(f"최종 스케일링 및 조정된 진입 수량 목록: {entry_qty_list}")
            logging.info(f"최종 누적 진입 수량 목록: {cumul_entry_qty_list}")
            success = True

        except Exception as e:
            logging.error(f"USDT-M 진입 수량 계산 중 오류 발생: {e}", exc_info=True)
            entry_qty_list, cumul_entry_qty_list = [], []

        finally:
            if gui:
                precision = symbol_info.get('quantityPrecision', 1) if symbol_info else 1
                err_msg = ["계산 오류"] * config.STEPS
                gui.update_entry_lists(entry_qty_list if success else err_msg, cumul_entry_qty_list if success else err_msg, precision)
            return success, entry_qty_list, cumul_entry_qty_list

    elif current_mode == 'COIN-M':
        # --- 2. COIN-M 모드 계산 로직 (계약 기반) ---
        # ... (COIN-M 로직은 이전과 동일, 변경 없음) ...
        contract_size_str = symbol_info.get('contractSize')

        if min_order_qty is None or not symbol_info or not contract_size_str:
            logging.error("COIN-M 진입 수량 계산 불가: 입력 데이터 또는 contractSize 정보 부족.")
            if gui: gui.update_entry_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 0)
            return False, [], []

        try:
            step_size = symbol_info.get('stepSize', '1')
            qty_precision = 0 # 계약은 정수
            min_qty_str = symbol_info.get('minQty', '1')

            # --- ✨ 수정: Raw 값 계산 ---
            q_raw = [Decimal('0')] * config.STEPS
            cumulative_sum_raw = Decimal('0')

            q1_d_raw = Decimal(str(min_order_qty)) # min contracts
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

            logging.debug(f"Raw base contracts (unadjusted): {[float(q) for q in q_raw]}")

            sum_q_raw = sum(q_raw)
            if sum_q_raw <= 0: raise ValueError("원시 기본 계약 수 합계가 0 이하")

            # --- 목표 총 계약 수 계산 (기존과 동일) ---
            mark_price_data = await client.mark_price(symbol=symbol)
            mark_price = 0.0
            if isinstance(mark_price_data, list) and len(mark_price_data) > 0:
                mark_price = float(mark_price_data[0].get('markPrice'))
            elif isinstance(mark_price_data, dict):
                mark_price = float(mark_price_data.get('markPrice'))

            if mark_price <= 0: raise ValueError(f"Mark Price 조회 실패 또는 0 이하: {mark_price}")
            total_balance_in_usd = current_balance * mark_price
            total_position_in_usd = total_balance_in_usd * config.BALANCE_USAGE_PERCENTAGE * config.TARGET_LEVERAGE
            contract_value_in_usd = float(contract_size_str)
            if contract_value_in_usd <= 0: raise ValueError("Contract value must be positive")
            target_total_contracts = total_position_in_usd / contract_value_in_usd

            logging.info(f"목표 총 계약 수: {target_total_contracts:.4f} (사용 자산: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}, "
                         f"총 포지션 가치: ${total_position_in_usd:,.2f}, 레버리지: {config.TARGET_LEVERAGE}x, 계약가치: ${contract_value_in_usd})")

            # --- ✨ 수정: 스케일링 후 최종 조정 ---
            scaling_factor = Decimal(str(target_total_contracts)) / sum_q_raw
            logging.info(f"Target Contracts: {target_total_contracts}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            # cumulative_sum_final = 0.0 # Use float for final accumulation # This line is correctly placed here in the original code.

            # Manual sum for cumulative list needs initialization
            current_cumul_sum = 0.0
            cumul_entry_qty_list_calc = []


            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)

                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 계약 수 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)

                # Update manual sum for cumulative list
                current_cumul_sum += q_final_adjusted
                cumul_entry_qty_list_calc.append(round(current_cumul_sum)) # Round cumulative contracts


            entry_qty_list = final_quantities
            cumul_entry_qty_list = cumul_entry_qty_list_calc # Assign calculated list


            logging.info(f"최종 스케일링 및 조정된 진입 계약 수 목록: {entry_qty_list}")
            logging.info(f"최종 누적 진입 계약 수 목록: {cumul_entry_qty_list}")
            success = True

        except Exception as e:
            logging.error(f"COIN-M 진입 수량 계산 중 오류 발생: {e}", exc_info=True)
            entry_qty_list, cumul_entry_qty_list = [], []

        finally:
            if gui:
                err_msg = ["계산 오류"] * config.STEPS
                gui.update_entry_lists(entry_qty_list if success else err_msg, cumul_entry_qty_list if success else err_msg, 0)
            return success, entry_qty_list, cumul_entry_qty_list


    else:
        # --- 3. 지원되지 않는 모드일 경우 에러 처리 ---
        logging.error(f"지원되지 않는 거래 모드입니다: {current_mode}")
        if gui: gui.update_entry_lists(["모드 오류"] * config.STEPS, ["모드 오류"] * config.STEPS, 0)
        return False, [], []

# --- Test Execution ---
# ...(run_test 함수 및 if __name__ == "__main__": 부분은 변경 없음)...
async def run_test():
    """Sets up mocks and runs the test cases."""
    mock_gui = MockGui()

    # --- Test Case 1: USDT-M ---
    print("\n--- Testing USDT-M (Scale First Logic - Corrected) ---")
    usdt_m_settings = {
        'STEPS': 12,
        'ENTRY_START': 0.4,
        'ENTRY_END': 0.66,
        'ENTRY_EXPONENT': 4, # Using float exponent
        'BALANCE_USAGE_PERCENTAGE': 0.7,
        'TARGET_LEVERAGE': 15,
        'BALANCE_ASSET': 'USDT' # Make sure this matches
    }
    mock_config_usdt = MockConfig(usdt_m_settings)
    set_config_source(mock_config_usdt) # Set global config for logic functions

    mock_client_usdt = MockBinanceFuturesClient(mode='USDT-M', mark_price_value=Decimal('100000.0')) # Test with 100k price

    symbol_info_usdt = {
        'stepSize': '0.001',
        'quantityPrecision': 3,
        'minQty': '0.001',
        'tickSize': '0.01',
        'pricePrecision': 2
    }
    min_order_qty_usdt = 0.001
    current_balance_usdt = 10000.0 # Example balance in USDT

    success_usdt, entry_list_usdt, cumul_list_usdt = await calculate_entry_quantities(
        mock_client_usdt,
        'BTCUSDT',
        symbol_info_usdt,
        min_order_qty_usdt,
        current_balance_usdt,
        mock_gui
    )
    print(f"USDT-M Success: {success_usdt}")
    if success_usdt:
        print(f"USDT-M Entry List: {entry_list_usdt}")
        print(f"USDT-M Cumul List: {cumul_list_usdt}")

    # --- Test Case 2: COIN-M ---
    print("\n--- Testing COIN-M (Scale First Logic - Corrected) ---")
    coin_m_settings = {
        'STEPS': 12,
        'ENTRY_START': 0.4,
        'ENTRY_END': 0.66,
        'ENTRY_EXPONENT': 4,
        'BALANCE_USAGE_PERCENTAGE': 0.7,
        'TARGET_LEVERAGE': 15,
        'BALANCE_ASSET': 'BTC' # Make sure this matches
    }
    mock_config_coin = MockConfig(coin_m_settings)
    set_config_source(mock_config_coin) # Set global config for logic functions

    mock_client_coin = MockBinanceFuturesClient(mode='COIN-M', mark_price_value=Decimal('100000.0')) # Same price

    symbol_info_coin = {
        'stepSize': '1',        # Contracts are usually whole numbers
        'quantityPrecision': 0, # Precision is 0 for contracts
        'minQty': '1',          # Minimum 1 contract
        'contractSize': '100',  # Example: 1 contract = $100 USD value
        'tickSize': '0.1',      # Example tick size
        'pricePrecision': 1     # Example price precision
    }
    min_order_qty_coin = 1.0 # Minimum order quantity in contracts
    current_balance_coin = 0.1 # Example balance in BTC

    success_coin, entry_list_coin, cumul_list_coin = await calculate_entry_quantities(
        mock_client_coin,
        'BTCUSD_PERP',
        symbol_info_coin,
        min_order_qty_coin,
        current_balance_coin,
        mock_gui
    )
    print(f"COIN-M Success: {success_coin}")
    if success_coin:
        # Keep as float from calculation, display logic might round
        print(f"COIN-M Entry List (Contracts): {entry_list_coin}")
        # Cumulative list is already rounded in the function
        print(f"COIN-M Cumul List (Contracts): {cumul_list_coin}")


if __name__ == "__main__":
    asyncio.run(run_test())