# logic.py (Bybit-compatible)
import logging
import asyncio
import time
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext
import gui_bybit
import math
from pybit.unified_trading import HTTP
from pybit.exceptions import InvalidRequestError, FailedRequestError

price_precision = None

getcontext().prec = 28

config = None

def set_config_source(config_obj):
    global config
    config = config_obj
    logging.info("logic.py: Configuration source has been set.")

# --- 유틸리티 함수 ---
def count_decimal_places(number_str):
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
    except Exception as e: logging.error(f"소수점 자릿수 계산 오류: {number_str}, 오류: {e}"); return 0

def adjust_quantity(quantity, step_size_str, precision, min_qty_str):
    try:
        step_size = Decimal(str(step_size_str))
        min_qty = Decimal(str(min_qty_str))
        qty = Decimal(str(quantity))

        if qty <= 0: return 0.0

        adjusted_qty = (qty // step_size) * step_size

        if adjusted_qty < min_qty:
            adjusted_qty = min_qty
            logging.warning(f"조정된 수량({adjusted_qty})이 최소 주문 수량({min_qty})보다 작아 최소 주문 수량으로 설정합니다.")

        quantized_qty = adjusted_qty.quantize(Decimal('1e-' + str(precision)), rounding=ROUND_DOWN)

        return float(quantized_qty)

    except Exception as e:
        logging.error(f"수량 조정 오류: qty={quantity}, step={step_size_str}, prec={precision}, min={min_qty_str}, error={e}", exc_info=True)
        return None
    
def format_price(price, tick_size_str):
    if tick_size_str is None:
        logging.warning("format_price 호출 시 tick_size가 None입니다.")
        try: return str(float(price))
        except: return str(price)
    try:
        price_d = Decimal(str(price)); tick_size_d = Decimal(str(tick_size_str))
        formatted_price_d = (price_d / tick_size_d).quantize(Decimal('1'), rounding=ROUND_DOWN) * tick_size_d
        decimals = count_decimal_places(tick_size_str)
        return f"{formatted_price_d:.{decimals}f}"
    except Exception as e: logging.error(f"가격 포맷팅 오류: price={price}, tick_size={tick_size_str}, error={e}"); return None

# --- 분할 횟수 계산 함수 ---
def calculate_num_divisions(step_index, total_steps, num_groups):
    if num_groups <= 0: return 1

    base_group_size = total_steps // num_groups
    remainder = total_steps % num_groups
    num_smaller_groups = num_groups - remainder

    cumulative_counts = []
    count = 0
    for i in range(num_groups):
        current_group_size = base_group_size + (1 if i >= num_smaller_groups else 0)
        count += current_group_size
        cumulative_counts.append(count)

    num_divisions = 1
    for group_index, end_index in enumerate(cumulative_counts):
        if step_index < end_index:
            num_divisions = group_index + 1
            break
    return min(num_divisions, num_groups)


# --- Bybit API 호출 함수 ---
async def check_futures_connection(client: HTTP):
    try:
        await asyncio.to_thread(client.get_server_time)
        logging.info("Bybit 서버 연결 성공.")
        return True
    except Exception as e:
        logging.error(f"Bybit 서버 연결 실패: {e}")
        return False

async def get_futures_balance(client: HTTP, asset, gui):
    current_balance = 0.0
    current_balance_str = "조회 실패"
    
    account_type = "UNIFIED" if config.CATEGORY in ['linear', 'inverse'] else "CONTRACT"
    if config.CATEGORY == 'inverse':
        account_type = "CONTRACT"

    try:
        response = await asyncio.to_thread(
            client.get_wallet_balance,
            accountType=account_type,
            coin=asset
        )
        logging.debug(f"get_wallet_balance 응답: {response}")

        balance_found = False
        if response.get('retCode') == 0:
            result_list = response.get('result', {}).get('list', [])
            if result_list:
                account_data = result_list[0]
                coin_data_list = account_data.get('coin', [])
                for coin_data in coin_data_list:
                    if coin_data.get('coin') == asset:
                        balance_val = coin_data.get('walletBalance')
                        logging.info(f"{asset} 선물 잔고 ({account_type}): {balance_val}")
                        current_balance = float(balance_val)
                        current_balance_str = str(balance_val)
                        balance_found = True
                        break
        
        if not balance_found: 
            logging.warning(f"{asset} 자산을 찾을 수 없습니다 (Account: {account_type}).")
            current_balance = 0.0
            current_balance_str = "찾을 수 없음"
            
    except Exception as e:
        logging.error(f"선물 잔고 확인 실패: {e}")
        current_balance = 0.0
    finally:
        if gui: gui.update_balance(current_balance_str)
        return current_balance, current_balance_str

async def check_position_mode(client: HTTP, gui):
    try:
        # 1. 'get_account_info' 메서드를 호출합니다. (category, symbol 불필요)
        response = await asyncio.to_thread(
            client.get_account_info
        )
        logging.debug(f"get_account_info 응답: {response}")

        if response.get('retCode') != 0:
            raise InvalidRequestError(status_code=response.get('retCode'), message=response.get('retMsg'), response=response)

        # 2. 'result' 객체에서 'positionMode' 필드를 확인합니다.
        mode_str = response.get('result', {}).get('positionMode', '0')
        is_hedge_mode = (mode_str == '3') # Bybit는 문자열 '3'을 반환

        if is_hedge_mode:
            logging.info("현재 포지션 모드: 헤지 모드 (Mode 3)")
            return True
        else:
            logging.warning(f"현재 포지션 모드: 단방향 모드 (Mode {mode_str}). 헤지 모드로 변경을 시도합니다...")
            if gui: gui.update_status("헤지 모드로 변경 중...")
            
            try:
                category = config.CATEGORY
                settle_coin = config.BALANCE_ASSET 
                
                logging.info(f"통합계정(UTA)의 [{category} / {settle_coin}] 포지션 모드를 'mode=3' (헷지 모드)로 변경 시도합니다...")
                await asyncio.to_thread(
                    client.switch_position_mode,
                    category=category,
                    coin=settle_coin,  # <--- FIX: 'settleCoin'을 'coin'으로 변경
                    mode=3 
                )
                logging.info("포지션 모드를 성공적으로 헤지 모드로 변경했습니다.")
                if gui: gui.update_status("헤지 모드 변경 완료.")
                return True
            except Exception as change_e:
                logging.error(f"헤지 모드 변경 실패: {change_e}")
                if gui: gui.update_status("헤지 모드 변경 실패!")
                return False
                
    except Exception as e:
        logging.error(f"포지션 모드 확인/변경 중 오류: {e}")
        if gui: gui.update_status("포지션 모드 확인 실패!")
        return False
    
async def check_all_open_positions(client: HTTP):
    try:
        # config 객체에서 현재 활성화된 카테고리와 정산 코인을 가져옴
        category = config.CATEGORY 
        settle_coin = config.BALANCE_ASSET
        
        logging.info(f"check_all_open_positions: [Category: {category}, SettleCoin: {settle_coin}] 포지션 확인 중...")

        response = await asyncio.to_thread(
            client.get_positions,
            category=category,
            settleCoin=settle_coin, # <--- FIX: settleCoin 파라미터 추가
            limit=200 
        )
        
        if response.get('retCode') != 0:
            # API가 0이 아닌 코드를 반환하면 예외 발생
            raise InvalidRequestError(status_code=response.get('retCode'), message=response.get('retMsg'), response=response)

        positions = response.get('result', {}).get('list', [])
        open_positions = [p for p in positions if float(p.get('size', 0)) != 0]
        
        if open_positions:
            logging.warning(f"경고: {len(open_positions)}개 오픈 포지션 발견 (Category: {category}, SettleCoin: {settle_coin}).")
            for p in open_positions:
                logging.warning(f"  - {p['symbol']} ({p['side']}), 수량: {p['size']}")
            return True # 오픈된 포지션이 있음을 반환
        else:
            logging.info(f"현재 오픈된 선물 포지션 없음 (Category: {category}, SettleCoin: {settle_coin}).")
            return False # 오픈된 포지션이 없음을 반환
            
    except Exception as e:
        logging.error(f"전체 포지션 정보 확인 실패: {e}")
        return True # 오류 발생 시 안전을 위해 포지션이 있는 것으로 간주

async def check_and_cancel_pending_orders(client: HTTP):
    try:
        # config 객체에서 현재 활성화된 카테고리와 정산 코인을 가져옴
        category = config.CATEGORY 
        settle_coin = config.BALANCE_ASSET
        
        logging.info(f"check_and_cancel_pending_orders: [Category: {category}, SettleCoin: {settle_coin}] 미체결 주문 확인 중...")

        response = await asyncio.to_thread(
            client.get_open_orders,
            category=category,
            settleCoin=settle_coin # <--- FIX: settleCoin 파라미터 추가
        )
        
        if response.get('retCode') != 0:
            # API가 0이 아닌 코드를 반환하면 예외 발생
            raise InvalidRequestError(status_code=response.get('retCode'), message=response.get('retMsg'), response=response)
            
        open_orders = response.get('result', {}).get('list', [])
        
        if not open_orders:
            logging.info(f"현재 미체결 주문 없음 (Category: {category}, SettleCoin: {settle_coin}).")
            return True

        logging.warning(f"경고: {len(open_orders)}개 미체결 주문 발견. 취소 시도...")
        
        cancelled_count = 0
        failed_count = 0
        
        cancel_tasks = []
        for order in open_orders:
            # API 응답에 category가 없을 수 있으므로, 현재 config의 category를 사용
            cancel_tasks.append(
                asyncio.to_thread(
                    client.cancel_order,
                    category=category, # <--- FIX: category 명시
                    symbol=order['symbol'], 
                    orderId=order['orderId']
                )
            )
            
        results = await asyncio.gather(*cancel_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            order = open_orders[i]
            if isinstance(result, Exception):
                logging.error(f"  - 주문 취소 실패: {order.get('symbol', 'N/A')}, ID={order.get('orderId', 'N/A')}, 오류: {result}")
                failed_count += 1
            else:
                logging.info(f"  - 주문 취소 성공: {order['symbol']}, ID={order['orderId']}")
                cancelled_count += 1
        
        if failed_count > 0:
            logging.error(f"{failed_count}개 주문 취소 실패.")
            return False
        else:
            logging.info(f"{cancelled_count}개 주문 성공적으로 취소.")
            return True
            
    except Exception as e:
        logging.error(f"미체결 주문 처리 중 오류: {e}")
        return False
    
async def set_leverage(client: HTTP, symbol, leverage, gui):
    leverage_set = False
    leverage_str = "설정 실패"
    category = config.CATEGORY
 
    # --- 추가: 마진 모드 설정값 읽기 ---
    margin_mode_setting = str(config.MARGIN_MODE).upper()
    trade_mode_api = "1" if margin_mode_setting == "ISOLATED" else "0"
    margin_mode_str = "격리(Isolated)" if trade_mode_api == "1" else "교차(Cross)"
    # --- 추가 끝 ---

    try:
        # --- 수정: tradeMode 파라미터 추가 및 로그 메시지 변경 ---
        logging.info(f"[{category}] {symbol} 레버리지 {leverage}배 및 {margin_mode_str} 모드 설정 시도...");
        leverage_str_api = str(int(leverage))
        await asyncio.to_thread(
            client.set_leverage,
            category=category,
            symbol=symbol,
            buyLeverage=leverage_str_api,
            sellLeverage=leverage_str_api,
            tradeMode=trade_mode_api # <--- 격리/교차 모드 설정
        )
        logging.info(f"{symbol} 레버리지({leverage}x) 및 {margin_mode_str} 모드 설정 완료.")
        leverage_set = True
        leverage_str = f"{leverage}x ({margin_mode_str})" # --- 수정: GUI 표시
    
    except (InvalidRequestError, FailedRequestError) as e:
        # --- FIX: 110043 오류를 성공으로 처리 ---
        if e.status_code == 110043:
            # --- 수정: 로그 메시지 변경 ---
            logging.info(f"{symbol} 레버리지({leverage}x) 및 {margin_mode_str} 모드가 이미 설정되어 있습니다 (110043).")
            leverage_set = True # 성공으로 간주
            leverage_str = f"{leverage}x ({margin_mode_str}) (기존)" # --- 수정: GUI 표시
        # --- FIX 끝 ---
        else:
            # 그 외 다른 오류는 실패로 간주
            logging.error(f"{symbol} 레버리지/마진 모드 설정 실패: {e}")
            leverage_str = "설정 실패"
            leverage_set = False
            
    except Exception as e: # 기타 알 수 없는 오류
        logging.error(f"{symbol} 레버리지/마진 모드 설정 중 알 수 없는 오류: {e}", exc_info=True)
        leverage_str = "오류"
        leverage_set = False

    finally:
        if gui: gui.update_leverage(leverage_str)
        return leverage_set, leverage_str

async def get_symbol_info(client: HTTP, symbol, gui):
    global price_precision
    
    symbol_info = {}
    symbol_info_loaded = False
    symbol_info_str = "조회 실패"
    category = config.CATEGORY

    try:
        logging.info(f"'{category}' 모드 {symbol} 거래 규칙 정보 조회 시도...");
        response = await asyncio.to_thread(
            client.get_instruments_info,
            category=category,
            symbol=symbol
        )
        
        if response.get('retCode') != 0:
            raise Exception(f"API Error: {response.get('retMsg')}")

        item_list = response.get('result', {}).get('list', [])
        if not item_list:
            info_found = False
        else:
            item = item_list[0]
            info_found = True
            
            lot_size_filter = item.get('lotSizeFilter', {})
            price_filter = item.get('priceFilter', {})
            
            symbol_info['minQty'] = lot_size_filter.get('minOrderQty')
            symbol_info['stepSize'] = lot_size_filter.get('qtyStep')
            symbol_info['tickSize'] = price_filter.get('tickSize')
            
            symbol_info['quantityPrecision'] = count_decimal_places(symbol_info['stepSize'])
            symbol_info['pricePrecision'] = count_decimal_places(symbol_info['tickSize'])
            price_precision = symbol_info['pricePrecision']

            if category == 'linear': # USDT-M
                # 'minNotional'이 아니라 'minNotionalValue'가 올바른 키 이름입니다.
                symbol_info['minNotional'] = lot_size_filter.get('minNotionalValue') # <--- FIX: 'minNotionalValue'로 수정
            else: # inverse (COIN-M)
                symbol_info['contractSize'] = item.get('contractVal')

            required_keys = ['quantityPrecision', 'minQty', 'stepSize', 'tickSize', 'pricePrecision']
            info_text_parts = [
                f"수량(정밀도:{symbol_info.get('quantityPrecision')}, 최소:{symbol_info.get('minQty')}, 스텝:{symbol_info.get('stepSize')})",
                f"가격(정밀도:{symbol_info.get('pricePrecision')}, 스텝:{symbol_info.get('tickSize')})"
            ]

            if category == 'linear':
                required_keys.append('minNotional')
                info_text_parts.append(f"최소금액:{symbol_info.get('minNotional')}USDT")
            else:
                required_keys.append('contractSize')
                info_text_parts.append(f"계약크기:{symbol_info.get('contractSize')}")

            if all(key in symbol_info and symbol_info[key] is not None for key in required_keys):
                symbol_info_loaded = True
                symbol_info_str = ", ".join(info_text_parts)
                logging.info(f" - {symbol_info_str}")
            else:
                err_msg = f"{symbol} 필수 필터 정보 누락. 필요: {required_keys}"; 
                logging.error(err_msg); symbol_info_str = err_msg
                
        if not info_found: err_msg = f"{symbol} 정보 없음."; logging.error(err_msg); symbol_info_str = err_msg
    except Exception as e: logging.error(f"{symbol} 정보 조회 실패: {e}")
    finally:
        if gui: gui.update_symbol_info(symbol_info_str)
        return symbol_info_loaded, symbol_info

async def calculate_effective_min_qty(client: HTTP, symbol, symbol_info, gui):
    calculated_min_qty = None
    calculated_min_qty_str = "N/A"
    category = config.CATEGORY

    if not symbol_info:
        logging.error("최소 주문 수량 계산 불가: 심볼 정보 부족.")
        if gui:
            gui.update_min_qty("심볼정보없음")
        return None, "심볼정보없음"
    
    try:
        if category == 'linear':
            min_lot_size_qty = symbol_info.get('minQty')
            step_size = symbol_info.get('stepSize')
            min_notional_value = symbol_info.get('minNotional')
            
            if not all([min_lot_size_qty, step_size, min_notional_value]):
                raise ValueError("USDT-M 모드 필수 정보(minQty, stepSize, minNotional) 누락.")

            logging.debug(f"{symbol} Mark Price 조회 시도 (for min_qty_calc)...")
            response = await asyncio.to_thread(
                client.get_tickers,
                category=category,
                symbol=symbol
            )
            mark_price = float(response.get('result', {}).get('list', [{}])[0].get('markPrice', 0))
            logging.info(f"{symbol} 현재 Mark Price: {mark_price}")

            if mark_price <= 0:
                raise ValueError(f"Mark Price가 0 또는 음수: {mark_price}")

            notional_qty = float(min_notional_value) / mark_price
            notional_qty_d = Decimal(str(notional_qty))
            step_size_d = Decimal(str(step_size))

            adjusted_notional_qty_d = (notional_qty_d / step_size_d).to_integral_value(rounding=ROUND_UP) * step_size_d
            adjusted_notional_qty = float(adjusted_notional_qty_d)
            
            min_lot_f = float(min_lot_size_qty)
            
            effective_min_qty = max(min_lot_f, adjusted_notional_qty)
            
            decimals = count_decimal_places(step_size)
            final_min_qty_d = Decimal(str(effective_min_qty)).quantize(Decimal(f'1e-{decimals}'), rounding=ROUND_DOWN)

            if final_min_qty_d < Decimal(str(min_lot_size_qty)):
                final_min_qty_d = Decimal(str(min_lot_size_qty))

            calculated_min_qty = float(final_min_qty_d)
            calculated_min_qty_str = f"{final_min_qty_d:.{decimals}f}"
            logging.info(f"계산된 최종 최소 주문 수량 (USDT-M): {calculated_min_qty}")

        elif category == 'inverse':
            min_lot_size_qty = symbol_info.get('minQty')
            if min_lot_size_qty is None:
                raise ValueError("COIN-M 모드에서 minQty 정보를 찾을 수 없습니다.")
            
            calculated_min_qty = float(min_lot_size_qty)
            calculated_min_qty_str = str(int(calculated_min_qty))
            logging.info(f"최소 주문 수량 (COIN-M): {calculated_min_qty_str} 계약")

    except Exception as e:
        logging.error(f"최소 주문 수량 계산 중 오류: {e}", exc_info=True)
        calculated_min_qty_str = "계산오류"
    
    finally:
        if gui:
            gui.update_min_qty(calculated_min_qty_str)
        return calculated_min_qty, calculated_min_qty_str


async def calculate_entry_quantities(client: HTTP, symbol: str, symbol_info: dict, min_order_qty: float, current_balance: float, gui):
    current_mode = config.CATEGORY
    logging.info(f"'{current_mode}' 모드에 대한 진입 수량 계산 시작...")

    entry_qty_list = []
    cumul_entry_qty_list = []
    success = False

    if current_mode == 'linear':
        if min_order_qty is None or not symbol_info:
            logging.error("USDT-M 진입 수량 계산 불가: 입력 데이터 부족.")
            if gui: gui.update_entry_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 1)
            return False, [], []

        try:
            step_size = symbol_info['stepSize']
            qty_precision = symbol_info['quantityPrecision']
            min_qty_str = symbol_info['minQty']

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

            logging.debug(f"Raw base quantities (unadjusted): {[float(q) for q in q_raw]}")

            sum_q_raw = sum(q_raw)
            if sum_q_raw <= 0: raise ValueError("원시 기본 수량 합계가 0 이하")

            total_margin = (current_balance * config.BALANCE_USAGE_PERCENTAGE) * config.TARGET_LEVERAGE
            logging.info(f"자금 사용률({config.BALANCE_USAGE_PERCENTAGE * 100}%) 적용. 실제 사용될 잔고: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}")

            response = await asyncio.to_thread(
                client.get_tickers,
                category=current_mode,
                symbol=symbol
            )
            mark_price = float(response.get('result', {}).get('list', [{}])[0].get('markPrice', 0))
            if mark_price <= 0: raise ValueError("Mark Price 오류")
            target_total_quantity = total_margin / mark_price

            scaling_factor = Decimal(str(target_total_quantity)) / sum_q_raw
            logging.info(f"Target Quantity: {target_total_quantity}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            cumulative_sum_final = 0.0
            cumulative_quantities_final = []

            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)

                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)
                cumulative_sum_final += q_final_adjusted
                cumulative_quantities_final.append(round(cumulative_sum_final, qty_precision))

            entry_qty_list = final_quantities
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

    elif current_mode == 'inverse':
        contract_size_str = symbol_info.get('contractSize')

        if min_order_qty is None or not symbol_info or not contract_size_str:
            logging.error("COIN-M 진입 수량 계산 불가: 입력 데이터 또는 contractSize 정보 부족.")
            if gui: gui.update_entry_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 0)
            return False, [], []

        try:
            step_size = symbol_info.get('stepSize', '1')
            qty_precision = 0
            min_qty_str = symbol_info.get('minQty', '1')

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

            logging.debug(f"Raw base contracts (unadjusted): {[float(q) for q in q_raw]}")

            sum_q_raw = sum(q_raw)
            if sum_q_raw <= 0: raise ValueError("원시 기본 계약 수 합계가 0 이하")

            response = await asyncio.to_thread(
                client.get_tickers,
                category=current_mode,
                symbol=symbol
            )
            mark_price = float(response.get('result', {}).get('list', [{}])[0].get('markPrice', 0))

            if mark_price <= 0: raise ValueError(f"Mark Price 조회 실패 또는 0 이하: {mark_price}")
            total_balance_in_usd = current_balance * mark_price
            total_position_in_usd = total_balance_in_usd * config.BALANCE_USAGE_PERCENTAGE * config.TARGET_LEVERAGE
            contract_value_in_usd = float(contract_size_str)
            if contract_value_in_usd <= 0: raise ValueError("Contract value must be positive")
            target_total_contracts = total_position_in_usd / contract_value_in_usd

            logging.info(f"목표 총 계약 수: {target_total_contracts:.4f} (사용 자산: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}, "
                         f"총 포지션 가치: ${total_position_in_usd:,.2f}, 레버리지: {config.TARGET_LEVERAGE}x, 계약가치: ${contract_value_in_usd})")

            scaling_factor = Decimal(str(target_total_contracts)) / sum_q_raw
            logging.info(f"Target Contracts: {target_total_contracts}, Sum Raw Q: {float(sum_q_raw)}, Scaling Factor: {float(scaling_factor)}")

            final_quantities = []
            current_cumul_sum = 0.0
            cumul_entry_qty_list_calc = []


            for i in range(config.STEPS):
                q_final_unadjusted_dec = q_raw[i] * scaling_factor
                q_final_unadjusted_float = float(q_final_unadjusted_dec)

                q_final_adjusted = adjust_quantity(q_final_unadjusted_float, step_size, qty_precision, min_qty_str)

                if q_final_adjusted is None: raise ValueError(f"최종 계약 수 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted)

                current_cumul_sum += q_final_adjusted
                cumul_entry_qty_list_calc.append(round(current_cumul_sum))


            entry_qty_list = final_quantities
            cumul_entry_qty_list = cumul_entry_qty_list_calc


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
        logging.error(f"지원되지 않는 거래 모드입니다: {current_mode}")
        if gui: gui.update_entry_lists(["모드 오류"] * config.STEPS, ["모드 오류"] * config.STEPS, 0)
        return False, [], []
    
async def calculate_hedge_quantities(symbol_info, entry_qty_list, cumul_entry_qty_list, min_order_qty, gui):
    per_step_list = []; cumul_list = []; success = False
    if not entry_qty_list or not cumul_entry_qty_list or not symbol_info or min_order_qty is None:
        logging.error("헷지 수량 계산 불가: 입력 데이터 부족.")
        if gui: gui.update_hedge_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 1)
    else:
        try:
            step_size = symbol_info['stepSize']; qty_precision = symbol_info['quantityPrecision']; min_qty_str = symbol_info['minQty']
            final_step_hedge_quantities = [0.0] * config.STEPS; final_cumulative_hedge_quantities = [0.0] * config.STEPS
            for i in range(config.STEPS):
                if config.STEPS == 1: x = Decimal('1.0')
                else: denominator = Decimal(str(config.STEPS - 1)); x = Decimal(str(i)) / denominator if denominator != 0 else Decimal('1.0')
                hedge_ratio_d = Decimal(str(config.HEDGE_START)) + (Decimal(str(config.HEDGE_END)) - Decimal(str(config.HEDGE_START))) * (x ** Decimal(str(config.HEDGE_EXPONENT)))
                hedge_ratio = float(hedge_ratio_d)
                if i < len(cumul_entry_qty_list): cumul_hedge_qty_raw = cumul_entry_qty_list[i] * hedge_ratio
                else: cumul_hedge_qty_raw = 0.0
                cumul_hedge_qty_adjusted = adjust_quantity(cumul_hedge_qty_raw, step_size, qty_precision, min_qty_str)
                if cumul_hedge_qty_adjusted is None: raise ValueError(f"누적 헷지 Q({i}) 조정 실패")
                final_cumulative_hedge_quantities[i] = cumul_hedge_qty_adjusted
            for i in range(config.STEPS):
                if i == 0: step_hedge_adjusted = final_cumulative_hedge_quantities[i]
                else:
                    step_hedge = Decimal(str(final_cumulative_hedge_quantities[i])) - Decimal(str(final_cumulative_hedge_quantities[i-1]))
                    if step_hedge < 0: step_hedge = Decimal('0')
                    if step_hedge == 0: step_hedge_adjusted = 0.0
                    else:
                        step_hedge_adjusted_temp = adjust_quantity(float(step_hedge), step_size, qty_precision, min_qty_str)
                        if step_hedge_adjusted_temp is None: raise ValueError(f"스텝별 헷지 Q({i}) 조정 실패")
                        step_hedge_adjusted = step_hedge_adjusted_temp
                final_step_hedge_quantities[i] = step_hedge_adjusted
            per_step_list = final_step_hedge_quantities; cumul_list = final_cumulative_hedge_quantities
            logging.info(f"최종 스텝별 헷지 수량 목록: {per_step_list}")
            logging.info(f"최종 누적 헷지 수량 목록: {cumul_list}")
            success = True
        except Exception as e: logging.error(f"헷지 수량 계산 중 오류 발생: {e}", exc_info=True)
        finally:
            if gui:
                precision = symbol_info.get('quantityPrecision', 1) if symbol_info else 1
                err_msg = ["계산 오류"] * config.STEPS
                gui.update_hedge_lists(per_step_list if success else err_msg, cumul_list if success else err_msg, precision)
            return success, per_step_list, cumul_list

async def calculate_exit_ratios(gui):
    exit_ratios = []; success = False
    try:
        ratios = [0.0] * config.STEPS
        for i in range(config.STEPS):
            if config.STEPS == 1: x = Decimal('1.0')
            else: denominator = Decimal(str(config.STEPS - 1)); x = Decimal(str(i)) / denominator if denominator != 0 else Decimal('1.0')
            exit_ratio_d = Decimal(str(config.EXIT_LAST)) + (Decimal(str(config.EXIT_FIRST)) - Decimal(str(config.EXIT_LAST))) * ((Decimal('1.0') - x) ** Decimal(str(config.EXIT_EXPONENT)))
            ratios[i] = float(exit_ratio_d)
        exit_ratios = ratios
        logging.info(f"Exit 비율 목록: {exit_ratios}")
        success = True
    except Exception as e: logging.error(f"Exit 비율 계산 중 오류 발생: {e}", exc_info=True)
    finally:
        if gui: gui.update_exit_ratio_list(exit_ratios if success else ["계산 오류"] * config.STEPS)
        return success, exit_ratios

async def calculate_max_placeable_hedge_qty(client: HTTP, symbol: str, symbol_info: dict, position_side: str) -> float | None:
    try:
        logging.info(f"[{symbol}-{position_side}] 증거금 부족 감지. 최대 주문 가능 헤지 수량 계산 시작...")
        category = config.CATEGORY
        
        response = await asyncio.to_thread(
            client.get_wallet_balance,
            accountType="UNIFIED", # Assuming UTA
            coin=config.BALANCE_ASSET
        )
        available_balance = 0.0
        if response.get('retCode') == 0:
            result_list = response.get('result', {}).get('list', [])
            if result_list:
                coin_data = result_list[0].get('coin', [])
                if coin_data:
                    available_balance = float(coin_data[0].get('availableBalance', '0'))

        if available_balance <= 0:
            logging.error("  -> 계산 불가: 가용 잔고가 0 이하입니다.")
            return None

        logging.info(f"  -> 현재 가용 잔고 ({config.BALANCE_ASSET}): {available_balance}")

        response_ticker = await asyncio.to_thread(
            client.get_tickers,
            category=category,
            symbol=symbol
        )
        mark_price = float(response_ticker.get('result', {}).get('list', [{}])[0].get('markPrice', 0))

        if mark_price <= 0:
            logging.error(f"  -> 계산 불가: Mark Price가 유효하지 않습니다 ({mark_price}).")
            return None
        
        logging.info(f"  -> 현재 Mark Price: {mark_price}")

        max_notional_value = (available_balance * config.EMERGENCY_HEDGE_RATIO) * config.TARGET_LEVERAGE
        
        max_quantity = 0.0
        if category == 'linear':
            max_quantity = max_notional_value / mark_price
        elif category == 'inverse':
            contract_size = float(symbol_info.get('contractSize', '1'))
            if contract_size <= 0: 
                logging.error("  -> 계산 불가: COIN-M 모드에서 계약 사이즈를 알 수 없습니다.")
                return None
            max_quantity = max_notional_value / contract_size

        logging.info(f"  -> 계산된 최대 주문 가능 수량 (조정 전): {max_quantity}")
        
        step_size = symbol_info['stepSize']
        qty_precision = symbol_info['quantityPrecision']
        min_qty_str = symbol_info['minQty']

        adjusted_max_qty = adjust_quantity(max_quantity, step_size, qty_precision, min_qty_str)

        if adjusted_max_qty is None or adjusted_max_qty <= 0:
            logging.error(f"  -> 계산 실패: 조정된 최종 수량이 0 이하입니다 ({adjusted_max_qty}).")
            return None
            
        logging.warning(f"  -> 최종 조정된 최대 주문 가능 수량: {adjusted_max_qty}")
        return adjusted_max_qty

    except Exception as e:
        logging.error(f"최대 주문 가능 헤지 수량 계산 중 예외 발생: {e}", exc_info=True)
        return None

# logic_bybit.py

async def place_futures_order(client: HTTP, *, symbol_info, symbol, side, position_side, quantity,
                              order_type=None, price=None, stop_price=None,
                              activation_price=None, callback_rate=None,
                              reduce_only=False,
                              open_orders_state_ref: dict = None,
                              order_type_mapping_ref: dict = None,
                              mapping_key: str = None,
                              client_order_id: str = None):
    
    if not symbol_info:
        logging.error("주문 불가: 심볼 정보 없음")
        return None, False, None

    min_order_qty_str = symbol_info.get('minQty')
    step_size = symbol_info.get('stepSize')
    qty_precision = symbol_info.get('quantityPrecision')
    tick_size = symbol_info.get('tickSize')
    category = config.CATEGORY

    if None in [min_order_qty_str, step_size, qty_precision, tick_size]:
        logging.error("주문 불가: 심볼 정보 필터 부족")
        return None, False, None

    order_success = False
    error_code_from_api = None
    order_data_from_api = None

    max_retries = config.ORDER_RETRY_ATTEMPTS
    base_retry_delay_seconds = config.ORDER_RETRY_DELAY_SECONDS

    final_adjusted_qty = adjust_quantity(float(quantity), step_size, qty_precision, min_order_qty_str)
    if final_adjusted_qty is None or final_adjusted_qty <= 0:
        logging.warning(f"조정된 주문 수량이 0 이하({final_adjusted_qty}) 또는 오류. 주문 안함.")
        return None, False, None
    formatted_qty_str = f"{final_adjusted_qty:.{qty_precision}f}"

    # Bybit 파라미터 매핑
    bybit_side = "Buy" if side == "BUY" else "Sell"
    position_idx = 1 if position_side == "LONG" else 2
    
    bybit_order_type = "Market"
    if order_type == "LIMIT":
        bybit_order_type = "Limit"
    
    params = {
        "category": category,
        "symbol": symbol,
        "side": bybit_side,
        "positionIdx": position_idx,
        "orderType": bybit_order_type,
        "qty": formatted_qty_str
    }

    if client_order_id:
        params["orderLinkId"] = client_order_id

    if bybit_order_type == "Limit":
        if price is None: logging.error(f"{order_type} 주문에 price 필요"); return None, False, None
        params["price"] = format_price(price, tick_size)
    
    # Bybit는 STOP_MARKET, TAKE_PROFIT_MARKET, TRAILING_STOP_MARKET을
    # 'triggerPrice', 'trailingStop', 'activePrice' 등을 통해 설정
    
    trigger_direction = None
    
    # 1. Stop/Take Profit Market (Conditional Market Order)
    if order_type in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]:
        if stop_price is None: logging.error(f"{order_type} 주문에 stopPrice 필요"); return None, False, None
        params["triggerPrice"] = format_price(stop_price, tick_size)
        
        # 트리거 방향 결정
        if order_type == "TAKE_PROFIT_MARKET":
            trigger_direction = 1 if bybit_side == "Sell" else 2
        else: # STOP_MARKET
            trigger_direction = 2 if bybit_side == "Sell" else 1
            
        params["triggerDirection"] = trigger_direction

    # 2. Trailing Stop Market
    elif order_type == "TRAILING_STOP_MARKET":
        if callback_rate is None: logging.error(f"{order_type} 주문에 callbackRate(distance) 필요"); return None, False, None
        params["trailingStop"] = str(callback_rate) # e.g., "100" (for $100 distance)
        
        if activation_price is not None:
             params["activePrice"] = format_price(activation_price, tick_size)

    if reduce_only:
        params["reduceOnly"] = True

    price_buffer_multiplier = 1

    for attempt in range(max_retries):
        try:
            
            # --- (버그 수정 2) TSM 주문 로직 수정 ---
            is_tsm_order = order_type == "TRAILING_STOP_MARKET"
            
            if is_tsm_order and "activePrice" in params:
                try:
                    # activePrice가 설정되었는지 확인
                    activation_price_float = float(params["activePrice"])
                    current_price_response = await asyncio.to_thread(
                        client.get_tickers, category=category, symbol=symbol
                    )
                    current_price = float(current_price_response.get('result', {}).get('list', [{}])[0].get('markPrice', 0))

                    if current_price > 0:
                        # (익절 주문) Sell TSM인데 발동가가 현재가보다 높거나, Buy TSM인데 발동가가 현재가보다 낮으면
                        if (bybit_side == 'Sell' and activation_price_float > current_price) or \
                           (bybit_side == 'Buy' and activation_price_float < current_price):
                            # 이것은 Take Profit TSM입니다. activePrice를 제거해야 즉시 활성화됩니다.
                            logging.warning(f"Take Profit TSM (Side: {bybit_side}) 감지. 즉시 활성화를 위해 activePrice({activation_price_float})를 제거합니다.")
                            del params["activePrice"]
                        else:
                            # 이것은 Stop Loss TSM입니다. activePrice를 유지합니다.
                            logging.info(f"Stop Loss TSM (Side: {bybit_side}) 감지. activePrice({activation_price_float})를 유지합니다.")
                    else:
                        logging.warning("TSM activePrice 로직: 현재 가격을 가져올 수 없어 activePrice를 유지합니다.")
                except Exception as ap_err:
                    logging.error(f"TSM activePrice 처리 중 오류 (무시하고 진행): {ap_err}")
            # --- (수정 끝) ---

            logging.info(f"Bybit 주문 시도 (시도 {attempt + 1}/{max_retries}): {params}")
            order_response = await asyncio.to_thread(client.place_order, **params)
            logging.info(f"Bybit 주문 성공 (API 응답): {order_response}")

            if order_response.get('retCode') != 0:
                raise InvalidRequestError(
                    status_code=order_response.get('retCode'), 
                    message=order_response.get('retMsg'), 
                    response=order_response
                )
            
            order_data_from_api = order_response.get('result', {})
            order_success = True
            error_code_from_api = None

            if order_data_from_api and open_orders_state_ref is not None and \
               order_type_mapping_ref is not None and mapping_key:
                
                order_id_from_api = str(order_data_from_api.get('orderId'))
                client_oid_from_api = order_data_from_api.get('orderLinkId')
                
                order_state_to_store = order_data_from_api.copy()
                order_state_to_store['creationTime'] = time.time()
                
                order_state_to_store.update({
                    'symbol': symbol,
                    'side': bybit_side,
                    'orderType': bybit_order_type,
                    'qty': formatted_qty_str,
                    'price': params.get('price', '0'),
                    'triggerPrice': params.get('triggerPrice', '0'),
                    'positionIdx': position_idx
                })

                open_orders_state_ref[order_id_from_api] = order_state_to_store
                order_type_mapping_ref[order_id_from_api] = mapping_key
                logging.info(f"주문 즉시 로컬 상태 업데이트 완료: OrderID={order_id_from_api}, ClientOID={client_oid_from_api}, 구분={mapping_key}")
            break

        except (InvalidRequestError, FailedRequestError) as e:
            logging.error(f"주문 시도 {attempt + 1}/{max_retries} 실패: {e}")
            error_code_from_api = e.status_code
            
            if error_code_from_api == 110043 and attempt < max_retries - 1:
                logging.warning(f"주문 즉시 체결 오류 (코드: 110043). 버퍼를 늘려 가격 재조정 후 재시도합니다...")
                try:
                    current_price_dec = Decimal('0')
                    last_price_from_config = getattr(config, 'last_price', None)

                    if last_price_from_config and isinstance(last_price_from_config, Decimal) and last_price_from_config > 0:
                        current_price_dec = last_price_from_config
                        logging.info(f"  -> 웹소켓 last_price({current_price_dec})를 사용하여 가격을 재조정합니다.")
                    else:
                        logging.warning("  -> 웹소켓 last_price를 사용할 수 없어 Mark Price를 조회합니다.")
                        response_ticker = await asyncio.to_thread(
                            client.get_tickers, category=category, symbol=symbol
                        )
                        current_price_dec = Decimal(str(response_ticker.get('result', {}).get('list', [{}])[0].get('markPrice', 0)))

                    if current_price_dec <= 0:
                        logging.error("  -> 가격 재조정 실패: 유효한 현재 가격을 얻을 수 없습니다.")
                        break

                    tick_size_dec = Decimal(str(tick_size))
                    price_buffer = tick_size_dec * 10 * price_buffer_multiplier
                    logging.info(f"  -> 현재 버퍼 승수: {price_buffer_multiplier}, 적용 버퍼: {price_buffer}")

                    new_trigger_price_dec = Decimal('0')
                    price_key_to_update = None

                    if order_type == "TRAILING_STOP_MARKET":
                        price_key_to_update = 'activePrice'
                    elif order_type in ["STOP_MARKET", "TAKE_PROFIT_MARKET"]:
                        price_key_to_update = 'triggerPrice'
                    else:
                        logging.error(f"  -> 가격 재조정 실패: 110043 오류는 {order_type} 유형에서 처리할 수 없습니다.")
                        break

                    if bybit_side == "Buy": 
                        logging.info("  -> (TP -110043 Fix) BUY 주문: 현재가에서 버퍼를 '차감'합니다.")
                        new_trigger_price_dec = current_price_dec - price_buffer
                    elif bybit_side == "Sell": 
                        logging.info("  -> (TP -110043 Fix) SELL 주문: 현재가에 버퍼를 '더합니다'.")
                        new_trigger_price_dec = current_price_dec + price_buffer

                    formatted_new_price = format_price(new_trigger_price_dec, tick_size)
                    if not formatted_new_price:
                        logging.error(f"  -> 가격 재조정 실패: 새로운 트리거 가격 포맷팅 오류 ({new_trigger_price_dec})")
                        break

                    if price_key_to_update:
                        original_price = params.get(price_key_to_update, 'N/A')
                        params[price_key_to_update] = formatted_new_price
                        logging.info(f"  -> 새로운 발동가({price_key_to_update}): {original_price} -> {formatted_new_price}")
                        price_buffer_multiplier += 1
                        await asyncio.sleep(base_retry_delay_seconds)
                        continue
                    else:
                        logging.error("  -> 가격 재조정 로직 오류: 업데이트할 가격 키를 결정하지 못했습니다.")
                        break

                except Exception as retry_err:
                    logging.error(f"-110043 오류 처리 중 추가 오류 발생: {retry_err}")
                    break
            
            elif error_code_from_api == 110007:
                logging.error(f"증거금 부족 (코드: 110007). 재시도 안함.")
                break
                
            elif error_code_from_api == 10006 and attempt < max_retries - 1: # Rate limit
                current_retry_delay = base_retry_delay_seconds * 2
                logging.info(f"서버 과부하 (코드: 10006). {current_retry_delay}초 후 재시도합니다...")
                await asyncio.sleep(current_retry_delay)
            else:
                order_success = False
                logging.error(f"주문 최종 실패 (시도 {attempt + 1}/{max_retries}). ErrorCode: {error_code_from_api}")
                break

    return order_data_from_api, order_success, error_code_from_api

async def place_divided_orders(client: HTTP, gui, symbol_info, state,
                               order_purpose, target_step_index, total_quantity,
                               side, position_side, order_type,
                               price=None, stop_price=None, base_entry_price=None,
                               attempt_key_prefix: str = None,
                               current_sub_division_status: dict = None
                              ):
    open_orders = state['open_orders_state']; order_mapping = state['order_type_mapping']
    symbol = state['symbol']; placed_orders_list = [] 
    min_qty_str = symbol_info.get('minQty'); step_size = symbol_info.get('stepSize'); qty_precision = symbol_info.get('quantityPrecision')
    base_mapping_key = attempt_key_prefix if attempt_key_prefix else f'{order_purpose}-{target_step_index}'
    try:
        if order_purpose in ['General', 'SignalEntry']:
            num_total_divisions_for_step = calculate_num_divisions(target_step_index, config.STEPS, config.DIVIDE)
            if num_total_divisions_for_step <= 0: num_total_divisions_for_step = 1 
            if order_type == "MARKET":
                logging.info(f"[{order_purpose} 스텝 {target_step_index}] MARKET 주문 {num_total_divisions_for_step}회 분할 실행 시작. 총 수량: {total_quantity}")
                if total_quantity <= 0: logging.warning(f"[{order_purpose} 스텝 {target_step_index}] 총 주문 수량이 0 이하이므로 MARKET 분할 주문을 실행하지 않습니다."); return False, [], None 
                qty_per_division_raw = Decimal(str(total_quantity)) / Decimal(str(num_total_divisions_for_step))
                accumulated_qty_placed_dec = Decimal('0'); all_market_subs_successful = True
                for i in range(num_total_divisions_for_step):
                    current_sub_qty_dec = qty_per_division_raw
                    if i == num_total_divisions_for_step - 1: current_sub_qty_dec = Decimal(str(total_quantity)) - accumulated_qty_placed_dec
                    qty_to_place_float = float(current_sub_qty_dec)
                    if qty_to_place_float <= float(min_qty_str) / 2 and num_total_divisions_for_step > 1: logging.warning(f"  - [{order_purpose} 스텝 {target_step_index} 분할 {i+1}] 목표 수량({qty_to_place_float})이 매우 작습니다.")
                    if qty_to_place_float <= 0:
                        if num_total_divisions_for_step == 1: logging.error(f"  - [{order_purpose} 스텝 {target_step_index}] 단일 MARKET 주문 수량이 0 이하입니다. 주문 실패."); all_market_subs_successful = False; break 
                        logging.info(f"  - [{order_purpose} 스텝 {target_step_index} 분할 {i+1}] 계산된 수량 0 이하 ({qty_to_place_float}). 건너뜁니다."); continue
                    sub_order_mapping_key = f'{base_mapping_key}-{i}'
                    logging.info(f"  - [{order_purpose} 스텝 {target_step_index} 분할 {i+1}/{num_total_divisions_for_step}] MARKET 주문 시도. 수량: {qty_to_place_float}")
                    order_data_market_sub, success_market_sub, error_code_market_sub = await place_futures_order(client, symbol_info, symbol, side, position_side, qty_to_place_float, "MARKET", False, open_orders, order_mapping, sub_order_mapping_key)
                    if success_market_sub and order_data_market_sub:
                        placed_orders_list.append(order_data_market_sub)
                        try: accumulated_qty_placed_dec += Decimal(str(order_data_market_sub.get('qty', '0')))
                        except: pass 
                        if i < num_total_divisions_for_step - 1: await asyncio.sleep(0.2) 
                    else: all_market_subs_successful = False; logging.error(f"  - [{order_purpose} 스텝 {target_step_index} 분할 {i+1}] MARKET 주문 실패. ErrorCode: {error_code_market_sub}")
                final_success_market_divided = all_market_subs_successful and bool(placed_orders_list)
                return final_success_market_divided, placed_orders_list, None 
            elif order_type == "LIMIT":
                logging.error(f"[{order_purpose} 스텝 {target_step_index}] LIMIT 주문은 place_divided_orders에서 직접 처리하지 않습니다. 조건부 시장가 설정을 확인하세요.")
                return False, [], None
            else: logging.error(f"[{order_purpose} 스텝 {target_step_index}] 지원되지 않는 주문 유형: {order_type} (General/SignalEntry 목적)"); return False, [], None
        elif order_purpose == "SysClosePos" and order_type == "MARKET":
            order_mapping_key_sys_close = f'{base_mapping_key}-0'
            order_data_sys_close, success_sys_close, _ = await place_futures_order(client, symbol_info, symbol, side, position_side, total_quantity, "MARKET", True, open_orders, order_mapping, order_mapping_key_sys_close)
            if success_sys_close and order_data_sys_close: placed_orders_list.append(order_data_sys_close)
            return success_sys_close, placed_orders_list 
        elif order_purpose in ['Maginot', 'Maginot Hedge']:
            order_mapping_key_maginot = f'{base_mapping_key}-0'
            actual_order_type_maginot = "LIMIT" if order_purpose == 'Maginot' else "MARKET"
            reduce_only_maginot = False
            order_data_maginot, success_maginot, _ = await place_futures_order(client, symbol_info, symbol, side, position_side, total_quantity, actual_order_type_maginot, price, None, reduce_only_maginot, open_orders, order_mapping, order_mapping_key_maginot)
            if success_maginot and order_data_maginot: placed_orders_list.append(order_data_maginot)
            return success_maginot, placed_orders_list 
        elif order_purpose == 'Exit':
             logging.error("place_divided_orders: Exit 주문은 이 함수에서 직접 분할 처리하지 않습니다.")
             return False, [], 0 
        else:
            logging.error(f"place_divided_orders: 알 수 없거나 처리할 수 없는 주문 목적 '{order_purpose}' 또는 주문 유형 '{order_type}' 조합")
            if order_purpose == 'Exit': return False, [], 0
            elif order_purpose in ['General', 'SignalEntry']: return False, [], None
            else: return False, []
    except Exception as e:
        logging.error(f"[{order_purpose} 스텝 {target_step_index}] 분할 주문 생성 중 최상위 오류: {e}", exc_info=True)
        if order_purpose == 'Exit': return False, placed_orders_list, 1 
        elif order_purpose in ['General', 'SignalEntry']: return False, placed_orders_list, None
        else: return False, placed_orders_list

async def place_maginot_step_hedge_order(client: HTTP, gui, symbol_info: dict, state: dict, step_to_hedge: int, total_hedge_qty_for_step: float, main_position_side: str):
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state'); order_type_mapping_ref = state.get('order_type_mapping')
    if not symbol_info or total_hedge_qty_for_step <= 0: logging.error(f"[MaginotStepHedge] 스텝 {step_to_hedge}: 헤지 불가 - 심볼 정보 없거나 수량 ({total_hedge_qty_for_step}) <= 0."); return False, None
    hedge_side = None; hedge_position_side = None
    if main_position_side == 'LONG': hedge_side = "SELL"; hedge_position_side = 'SHORT'
    elif main_position_side == 'SHORT': hedge_side = "BUY"; hedge_position_side = 'LONG'
    else: logging.error(f"[MaginotStepHedge] 스텝 {step_to_hedge}: 알 수 없는 주 포지션 사이드 '{main_position_side}'. 헤지 주문 불가."); return False, None
    mapping_key = f"MaginotHedge-{step_to_hedge}-{int(time.time())}"
    logging.info(f"[MaginotStepHedge] 스텝 {step_to_hedge} 전체 헤지 주문: Side: {hedge_side}, PosSide: {hedge_position_side}, Qty: {total_hedge_qty_for_step}, Key: {mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, total_hedge_qty_for_step, "MARKET", None, None, False, open_orders_state_ref, order_type_mapping_ref, mapping_key)
    if success and order_data: logging.info(f"  -> [MaginotStepHedge] 스텝 {step_to_hedge} 헤지 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [MaginotStepHedge] 스텝 {step_to_hedge} 헤지 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_single_exit_hedge_sub_order(client: HTTP, gui, symbol_info: dict, state: dict, filled_exit_step_index: int, filled_exit_sub_order_index: int, hedge_quantity: float, original_main_position_side: str ):
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state'); order_type_mapping_ref = state.get('order_type_mapping')
    if not symbol_info or hedge_quantity <= 0: logging.error(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index}: 심볼 정보 없거나 헤지 수량 ({hedge_quantity}) <= 0. 주문 안함."); return False, None
    hedge_side = None; hedge_position_side = None
    if original_main_position_side == 'LONG': hedge_side = "BUY"; hedge_position_side = 'SHORT'
    elif original_main_position_side == 'SHORT': hedge_side = "SELL"; hedge_position_side = 'LONG'
    else: logging.error(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index}: 알 수 없는 원본 포지션 사이드 '{original_main_position_side}'. 헤지 주문 불가."); return False, None
    mapping_key = f"ExitHedgeSub-{filled_exit_step_index}-{filled_exit_sub_order_index}-{int(time.time())}"
    logging.info(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 대응: 시장가 헤지 주문. Side: {hedge_side}, PosSide: {hedge_position_side}, Qty: {hedge_quantity}, Key: {mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, hedge_quantity, "MARKET", None, None, False, open_orders_state_ref, order_type_mapping_ref, mapping_key)
    if success and order_data: logging.info(f"  -> [ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 헤지 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 헤지 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_market_hedge_for_general_sub_order(client: HTTP, gui, symbol_info: dict, state: dict, filled_general_step_index: int, filled_general_sub_order_index: int, num_total_divisions_for_general_step: int, total_hedge_qty_for_completed_step: float, general_order_main_side: str ):
    if total_hedge_qty_for_completed_step <= 0 or num_total_divisions_for_general_step <= 0: logging.warning(f"[SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index}: 헤지 수량({total_hedge_qty_for_completed_step}) 또는 분할 수({num_total_divisions_for_general_step})가 0 이하. 헤지 주문 건너뜁니다."); return False, None
    hedge_qty_for_this_sub = Decimal(str(total_hedge_qty_for_completed_step)) / Decimal(str(num_total_divisions_for_general_step))
    hedge_qty_for_this_sub_float = float(hedge_qty_for_this_sub); qty_precision_hedge = symbol_info.get('quantityPrecision', 2)
    
    hedge_side = "SELL" if general_order_main_side == 'LONG' else "BUY"
    hedge_position_side = 'SHORT' if general_order_main_side == 'LONG' else 'LONG'

    logging.info(f"[SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 대응: MARKET {hedge_side} 헤지 주문 시작. 목표 수량: {hedge_qty_for_this_sub_float:.{qty_precision_hedge}f}, PositionSide: {hedge_position_side}, reduceOnly=False")
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state', {}); order_type_mapping_ref = state.get('order_type_mapping', {})
    reduce_only_flag = False; hedge_mapping_key = f"SubHedge-{filled_general_step_index}-{filled_general_sub_order_index}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, hedge_qty_for_this_sub_float, "MARKET", None, None, reduce_only_flag, open_orders_state_ref, order_type_mapping_ref, hedge_mapping_key)
    if success and order_data: logging.info(f"  -> [SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 헤지 주문 요청 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 헤지 주문 요청 실패. ErrorCode: {error_code}")
    return success, order_data

def calculate_general_entry_triggers(base_entry_price: float, total_quantity: float, num_divisions: int, side: str, symbol_info: dict):
    triggers = []
    if num_divisions <= 0 or total_quantity <= 0 or base_entry_price <= 0: logging.warning(f"calculate_general_entry_triggers: 유효하지 않은 입력값으로 트리거 계산 불가. base:{base_entry_price}, qty:{total_quantity}, divs:{num_divisions}"); return triggers
    base_price_d = Decimal(str(base_entry_price)); tick_size_d = Decimal(str(symbol_info.get('tickSize', '0.0001'))) 
    qty_per_division_raw = Decimal(str(total_quantity)) / Decimal(str(num_divisions)); accumulated_qty_dec = Decimal('0')
    logging.info(f"트리거 계산 시작: 기준가={base_entry_price}, 총수량={total_quantity}, 분할={num_divisions}, 방향={side}")
    for i in range(num_divisions):
        raw_price_increment = base_price_d * Decimal(str(config.DIVIDE_RATE)); price_increment_abs = Decimal('0')
        if raw_price_increment > Decimal('0'):
            price_increment_abs = (raw_price_increment / tick_size_d).quantize(Decimal('1'), rounding=ROUND_UP) * tick_size_d
            if price_increment_abs < tick_size_d: price_increment_abs = tick_size_d
        price_offset = price_increment_abs * Decimal(str(i))
        
        if side == "BUY": trigger_price_dec = base_price_d - price_offset
        elif side == "SELL": trigger_price_dec = base_price_d + price_offset
        else: trigger_price_dec = base_price_d

        formatted_trigger_price = format_price(trigger_price_dec, symbol_info.get('tickSize'))
        if not formatted_trigger_price: logging.error(f"트리거 가격 포맷팅 실패 (분할 {i}): {trigger_price_dec}"); continue
        current_sub_qty_dec = qty_per_division_raw
        if i == num_divisions - 1: current_sub_qty_dec = Decimal(str(total_quantity)) - accumulated_qty_dec
        adjusted_sub_qty = adjust_quantity(float(current_sub_qty_dec), symbol_info.get('stepSize'), symbol_info.get('quantityPrecision'), symbol_info.get('minQty'))
        if adjusted_sub_qty is not None and adjusted_sub_qty > 0:
            triggers.append({'trigger_price': float(formatted_trigger_price), 'quantity': adjusted_sub_qty, 'side': side, 'status': 'pending'})
            accumulated_qty_dec += Decimal(str(adjusted_sub_qty))
            logging.debug(f"  분할 {i}: 트리거가={formatted_trigger_price}, 수량={adjusted_sub_qty}, 누적수량={accumulated_qty_dec}")
        else: logging.warning(f"  분할 {i}: 조정된 수량 0 이하 ({adjusted_sub_qty}). 해당 트리거 건너뜀.")
    if accumulated_qty_dec != Decimal(str(total_quantity)) and triggers: logging.warning(f"트리거 수량 총합({accumulated_qty_dec})과 원래 총수량({total_quantity}) 불일치.")
    return triggers

async def handle_signal(client: HTTP, gui, symbol_info_local: dict, state: dict):
    signal_type_local = state['signal_type']; current_step_for_signal = 0 
    entry_qty_list_from_state = state['entry_quantity_list']
    attempt_key_prefix_for_entry = f"EntryAttempt-{current_step_for_signal}-{int(time.time())}" 
    logging.info(f"=== {signal_type_local} 시그널 처리 시작 (스텝 {current_step_for_signal}, 조건부 시장가 설정) ===")
    if not entry_qty_list_from_state or current_step_for_signal >= len(entry_qty_list_from_state): logging.error(f"handle_signal: 스텝 {current_step_for_signal} 진입 수량 정보 없음."); return False, 0, [], 0, None
    total_entry_qty_for_step0 = entry_qty_list_from_state[current_step_for_signal]
    if total_entry_qty_for_step0 <= 0: logging.error(f"handle_signal: 스텝 {current_step_for_signal} 진입 수량이 0 이하입니다."); return False, 0, [], 0, None
    base_entry_price = 0.0
    try:
        response_ticker = await asyncio.to_thread(
            client.get_tickers,
            category=config.CATEGORY,
            symbol=config.SYMBOL
        )
        base_entry_price = float(response_ticker.get('result', {}).get('list', [{}])[0].get('markPrice', 0))
        if base_entry_price <= 0: raise ValueError("유효하지 않은 Mark Price")
    except Exception as e: logging.error(f"handle_signal: 기준 가격(Mark Price) 조회 실패: {e}"); return False, 0, [], 0, None
    num_divisions = calculate_num_divisions(current_step_for_signal, config.STEPS, config.DIVIDE)
    if num_divisions <= 0: num_divisions = 1
    entry_side = "BUY" if signal_type_local == 'LONG' else "SELL"
    triggers = calculate_general_entry_triggers(base_entry_price, total_entry_qty_for_step0, num_divisions, entry_side, symbol_info_local)
    if not triggers: logging.error(f"handle_signal: 스텝 {current_step_for_signal}에 대한 유효한 트리거를 생성할 수 없습니다."); return False, 0, [], 0, None
    actual_total_quantity_from_triggers = sum(t['quantity'] for t in triggers)
    logging.info(f"handle_signal: 스텝 {current_step_for_signal} 조건부 시장가 주문 트리거 {len(triggers)}개 생성 완료. 총 수량: {actual_total_quantity_from_triggers}")
    return True, len(triggers), triggers, actual_total_quantity_from_triggers, attempt_key_prefix_for_entry

async def handle_step_entry_signal(client: HTTP, gui, symbol_info_local: dict, state: dict, target_step: int):
    signal_type_local_step = state['signal_type']
    entry_qty_list_step = state['entry_quantity_list']
    open_orders_state_ref = state.get('open_orders_state', {})
    order_type_mapping_ref = state.get('order_type_mapping', {})

    attempt_key_prefix_step = f"EntryAttempt-{target_step}-{int(time.time())}" 
    logging.info(f"=== 시그널 기반 스텝 {target_step} 즉시 시장가 주문 실행 시작 ===")

    logging.info(f"스텝 {target_step} 진입 전, 이전 스텝의 모든 관련 주문을 취소합니다.")
    prefixes_to_clear = [
        'MainPartialExitTSM-',
        'HedgePartialExitSM-',
        f'Maginot-{target_step}-'
    ]

    for prefix in prefixes_to_clear:
        await cancel_orders_by_prefix(client, config.SYMBOL, open_orders_state_ref, order_type_mapping_ref, prefix)
    
    if gui: gui.update_open_orders_display(list(open_orders_state_ref.values()), order_type_mapping_ref)


    if not entry_qty_list_step or target_step >= len(entry_qty_list_step):
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 진입 수량 정보 없음.")
        return False, 0, [], 0, None

    total_entry_qty_for_target_step = entry_qty_list_step[target_step]
    if total_entry_qty_for_target_step <= 0:
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 진입 수량이 0 이하입니다.")
        return False, 0, [], 0, None

    entry_side_step = "BUY" if signal_type_local_step == 'LONG' else "SELL"
    position_side_step = signal_type_local_step

    state_for_order = {'symbol': config.SYMBOL, 'open_orders_state': open_orders_state_ref, 'order_type_mapping': order_type_mapping_ref}

    order_data, success, error_code = await place_general_order_market(
        client, gui, symbol_info_local, state_for_order,
        target_step, 
        total_entry_qty_for_target_step,
        attempt_key_prefix_step,
        signal_type_local_step 
    )

    if success and order_data:
        logging.info(f"handle_step_entry_signal: 스텝 {target_step} 시장가 주문 성공. OrderID: {order_data.get('orderId')}")
        return True, 1, [{'status':'placed', 'orderId':order_data.get('orderId')}], total_entry_qty_for_target_step, attempt_key_prefix_step
    else:
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 시장가 주문 실패. ErrorCode: {error_code}")
        return False, 0, [], 0, None

async def cancel_orders_by_prefix(client: HTTP, symbol: str, open_orders_state: dict, order_type_mapping: dict, prefix: str):
    cancelled_ids = []
    orders_to_cancel_info = []
    category = config.CATEGORY

    for order_id_key, order_data_value in list(open_orders_state.items()):
        custom_type = order_type_mapping.get(order_id_key)
        if custom_type and custom_type.startswith(prefix):
            api_call_order_id = order_data_value.get('orderId', order_data_value.get('i'))
            
            if api_call_order_id is not None:
                orders_to_cancel_info.append({'id_for_api': str(api_call_order_id), 'local_key': order_id_key, 'custom_type': custom_type})
            else:
                logging.warning(f"주문 취소 건너뜀: 로컬 키 {order_id_key} (구분: {custom_type})에 대한 API 호출용 주문 ID를 찾을 수 없음. 데이터: {order_data_value}")

    if not orders_to_cancel_info:
        logging.debug(f"'{prefix}' prefix를 가진 취소할 주문 없음 (또는 주문 ID 누락).")
        return cancelled_ids

    logging.info(f"'{prefix}' prefix를 가진 {len(orders_to_cancel_info)}개 주문 취소 시도...")
    
    cancel_tasks = [
        asyncio.to_thread(
            client.cancel_order,
            category=category, 
            symbol=symbol, 
            orderId=order_info['id_for_api']
        )
        for order_info in orders_to_cancel_info
    ]
    
    results = await asyncio.gather(*cancel_tasks, return_exceptions=True)

    for i, result in enumerate(results):
        order_info_cancelled = orders_to_cancel_info[i]
        local_order_key = order_info_cancelled['local_key']
        api_id_used = order_info_cancelled['id_for_api']

        if isinstance(result, (InvalidRequestError, FailedRequestError)):
            # Bybit 'order not found' (110001)
            if result.status_code == 110001:
                logging.warning(f"주문 취소 시도 중 API 오류(코드 110001): ID={api_id_used} (로컬키:{local_order_key})는 서버에 존재하지 않음. 로컬 상태 정리.")
                if local_order_key in open_orders_state: del open_orders_state[local_order_key]
                if local_order_key in order_type_mapping: del order_type_mapping[local_order_key]
                cancelled_ids.append(local_order_key)
            else:
                 logging.error(f"주문 취소 실패: ID={api_id_used} (로컬키:{local_order_key}), 구분:{order_info_cancelled['custom_type']}, 오류: {result}")
        elif isinstance(result, Exception):
            logging.error(f"주문 취소 중 알 수 없는 오류: ID={api_id_used}, 오류: {result}")
        else:
            logging.info(f"주문 취소 성공: ID={api_id_used} (로컬키:{local_order_key}), 구분:{order_info_cancelled['custom_type']}")
            if local_order_key in open_orders_state: del open_orders_state[local_order_key]
            if local_order_key in order_type_mapping: del order_type_mapping[local_order_key]
            cancelled_ids.append(local_order_key)
            
    return cancelled_ids

async def place_triggered_market_order(client: HTTP, gui, symbol_info_local: dict, state: dict, step_index: int, sub_index: int, quantity: float, side: str, position_side: str, base_attempt_key_prefix: str):
    logging.info(f"[TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index}: 시장가 {side} 주문 실행. 수량: {quantity}")
    order_mapping_key = f"{base_attempt_key_prefix}-{sub_index}"
    order_data, success, error_code = await place_futures_order(
        client, symbol_info_local, state.get('symbol'), 
        side, position_side, quantity, 
        "MARKET", 
        price=None,
        stop_price=None,
        reduce_only=False,
        open_orders_state_ref=state.get('open_orders_state'), 
        order_type_mapping_ref=state.get('order_type_mapping'), 
        mapping_key=order_mapping_key
    )
    if success and order_data: logging.info(f"  -> [TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index} 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index} 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_single_maginot_order(client: HTTP, gui, symbol_info_local: dict, state: dict, step_index_to_place: int):
    logging.info(f"[스텝 {step_index_to_place}] Maginot 주문 생성 시도...")
    symbol = state.get('symbol'); entry_qty_list_local = state.get('entry_quantity_list'); maginot_ratio_local = state.get('maginot_ratio')
    tick_size = symbol_info_local.get('tickSize'); step_size = symbol_info_local.get('stepSize')
    qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty')
    signal_type_local = state.get('signal_type') 
    category = config.CATEGORY

    if not all([symbol, entry_qty_list_local, maginot_ratio_local is not None, signal_type_local, symbol_info_local]): logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 필수 정보 누락."); return False, None
    if not (0 <= step_index_to_place < config.STEPS and step_index_to_place < len(entry_qty_list_local)): logging.warning(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 유효하지 않은 스텝 또는 수량 정보 없음."); return False, None
    entry_side = "BUY" if signal_type_local == 'LONG' else "SELL"
    position_side = 'LONG' if signal_type_local == 'LONG' else 'SHORT'
    maginot_qty = entry_qty_list_local[step_index_to_place]
    adjusted_maginot_qty = adjust_quantity(maginot_qty, step_size, qty_precision, min_qty_str)
    if adjusted_maginot_qty is None or adjusted_maginot_qty <= 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 수량 조정 실패/0 이하: 원본={maginot_qty}, 조정={adjusted_maginot_qty}."); return False, None
    logging.info(f"[Maginot 스텝 {step_index_to_place}] 사전 조정된 수량: {adjusted_maginot_qty} (원본: {maginot_qty})")
    try:
        response = await asyncio.to_thread(
            client.get_positions,
            category=category,
            symbol=symbol
        )
        positions = response.get('result', {}).get('list', [])
        
        current_pos = None
        for p in positions:
            if position_side == 'LONG' and p.get('side') == 'Buy': current_pos = p; break
            if position_side == 'SHORT' and p.get('side') == 'Sell': current_pos = p; break

        if not current_pos or float(current_pos.get('size', '0')) == 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: {position_side} 포지션 없음."); return False, None
        avg_entry_price = float(current_pos.get('avgPrice', '0')); liq_price = float(current_pos.get('liqPrice', '0'))
        if avg_entry_price <= 0 or liq_price <= 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 유효하지 않은 진입가({avg_entry_price}) 또는 청산가({liq_price})."); return False, None
        maginot_price_d = Decimal(str(avg_entry_price)) + (Decimal(str(liq_price)) - Decimal(str(avg_entry_price))) * Decimal(str(maginot_ratio_local))
        maginot_price_str = format_price(maginot_price_d, tick_size)
        if not maginot_price_str: logging.error(f"[Maginot 스텝 {step_index_to_place}] 가격 포맷팅 실패: {maginot_price_d}"); return False, None
        logging.info(f"[Maginot 스텝 {step_index_to_place}] 주문 실행: Side={entry_side}, PosSide={position_side}, Qty={adjusted_maginot_qty}, Price={maginot_price_str}")
        success, placed_orders = await place_divided_orders(client, gui, symbol_info_local, state, 'Maginot', step_index_to_place, adjusted_maginot_qty, entry_side, position_side, "LIMIT", maginot_price_str)
        return success, placed_orders[0] if placed_orders else None 
    except Exception as e: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 중 오류: {e}", exc_info=True); return False, None

async def place_general_hedge_order(client: HTTP, gui, symbol_info_local: dict, state: dict, filled_step_index: int, hedge_quantity: float, general_order_main_side: str):
    logging.info(f"=== General Hedge 주문 생성 시도: 스텝 {filled_step_index}, 수량 {hedge_quantity}, 원 주문 주사이드: {general_order_main_side} ===")
    symbol = state.get('symbol'); open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {})
    hedge_side = "SELL" if general_order_main_side == 'LONG' else "BUY"
    hedge_position_side = 'SHORT' if general_order_main_side == 'LONG' else 'LONG'
    if not hedge_position_side: logging.error(f"[GeneralHedge 스텝 {filled_step_index}] 주문 생성 불가: 원 주문의 주사이드 정보 없음."); return False, []
    attempt_key_prefix = f"GeneralHedge-{filled_step_index}"
    logging.info(f"[GeneralHedge 스텝 {filled_step_index}] 주문 정보: Symbol={symbol}, Side={hedge_side}, PositionSide={hedge_position_side}, Qty={hedge_quantity}, Type=MARKET, KeyPrefix={attempt_key_prefix}")
    success, placed_orders = await place_divided_orders(client, gui, symbol_info_local, state, 'GeneralHedge', filled_step_index, hedge_quantity, hedge_side, hedge_position_side, "MARKET", None, None, None, attempt_key_prefix)
    if success and placed_orders: logging.info(f"[GeneralHedge 스텝 {filled_step_index}] 시장가 주문 생성 요청 성공: {len(placed_orders)}개 주문, ID(s)={[o.get('orderId') for o in placed_orders]}")
    else: logging.error(f"[GeneralHedge 스텝 {filled_step_index}] 시장가 주문 생성 요청 실패.")
    return success, placed_orders

async def place_single_general_sub_order(client: HTTP, gui, symbol_info_local: dict, state: dict, order_purpose: str, target_step_index: int, sub_order_index: int, num_total_divisions: int, quantity_for_this_sub: float, base_entry_price_for_spread: float, side: str, position_side: str, attempt_key_prefix: str ):
    logging.info(f"[{order_purpose} 스텝 {target_step_index}] 단일 분할 주문 생성 시도 (분할 {sub_order_index + 1}/{num_total_divisions})")
    symbol = state.get('symbol'); tick_size = symbol_info_local.get('tickSize')
    open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {})
    base_price_d = Decimal(str(base_entry_price_for_spread)); tick_size_d = Decimal(str(tick_size)); raw_price_increment = base_price_d * Decimal(str(config.DIVIDE_RATE)); price_increment_abs = Decimal('0')
    if raw_price_increment > Decimal('0'):
        price_increment_abs = (raw_price_increment / tick_size_d).quantize(Decimal('1'), rounding=ROUND_UP) * tick_size_d
        if price_increment_abs < tick_size_d: price_increment_abs = tick_size_d
    elif config.DIVIDE_RATE == 0: price_increment_abs = Decimal('0')
    else: price_increment_abs = Decimal('0') 
    price_offset = price_increment_abs * Decimal(str(sub_order_index))
    if side == "BUY": calculated_price_dec = base_price_d - price_offset
    elif side == "SELL": calculated_price_dec = base_price_d + price_offset
    else: calculated_price_dec = base_price_d
    formatted_calc_price = format_price(calculated_price_dec, tick_size)
    if not formatted_calc_price: logging.error(f"[{order_purpose} 스텝 {target_step_index} 분할 {sub_order_index}] 가격 포맷팅 실패: {calculated_price_dec}"); return None, False, None 
    calculated_price_float = float(formatted_calc_price); order_mapping_key = f'{attempt_key_prefix}-{sub_order_index}' 
    logging.info(f"  - {order_purpose} 단일 분할 주문 (스텝 {target_step_index}, 분할 {sub_order_index + 1}/{num_total_divisions}): 수량 {quantity_for_this_sub}, 가격 {calculated_price_float}, Key={order_mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, side, position_side, quantity_for_this_sub, "LIMIT", calculated_price_float, None, False, open_orders_state_local, order_type_mapping_local, order_mapping_key)
    return order_data, success, error_code

async def place_single_exit_sub_order(client: HTTP, gui, symbol_info_local: dict, state: dict, target_step_index: int, sub_order_index: int, avg_entry_price: float, exit_ratio: float, entry_quantity_for_this_sub_order: float, signal_type_local: str ):
    logging.info(f"[스텝 {target_step_index}] 단일 Exit 분할 주문 생성 시도 (분할 인덱스: {sub_order_index})")
    symbol = state.get('symbol'); tick_size = symbol_info_local.get('tickSize'); step_size = symbol_info_local.get('stepSize')
    qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty')
    open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {})
    exit_side = "SELL" if signal_type_local == 'LONG' else "BUY"
    position_side = 'LONG' if signal_type_local == 'LONG' else 'SHORT'
    base_exit_price_d = Decimal(str(avg_entry_price)) * (Decimal('1.0') + Decimal(str(exit_ratio)) if signal_type_local == 'LONG' else Decimal('1.0') - Decimal(str(exit_ratio)))
    price_increment_abs = base_exit_price_d * Decimal(str(config.DIVIDE_RATE)) 
    price_offset = price_increment_abs * Decimal(str(sub_order_index))
    if exit_side == "SELL": calculated_price_dec = base_exit_price_d + price_offset
    elif exit_side == "BUY": calculated_price_dec = base_exit_price_d - price_offset
    else: calculated_price_dec = base_exit_price_d 
    formatted_calc_price = format_price(calculated_price_dec, tick_size)
    if not formatted_calc_price: logging.error(f"[Exit 분할 {sub_order_index}] 가격 포맷팅 실패: {calculated_price_dec}"); return None, False, None 
    calculated_price_float = float(formatted_calc_price)
    adjusted_sub_qty = adjust_quantity(entry_quantity_for_this_sub_order, step_size, qty_precision, min_qty_str)
    if adjusted_sub_qty is None or adjusted_sub_qty <= 0: logging.error(f"[Exit 분할 {sub_order_index}] 수량 조정 실패/0 이하: 원본={entry_quantity_for_this_sub_order}, 조정={adjusted_sub_qty}"); return None, False, None
    quantity_step_index_for_key = target_step_index - sub_order_index
    order_mapping_key = f'Exit-{target_step_index}-{sub_order_index}_qty{quantity_step_index_for_key}'
    logging.info(f"  - Exit 단일 분할 주문 (스텝 {target_step_index}, 분할 {sub_order_index}): 수량 {adjusted_sub_qty}, 가격 {calculated_price_float}, Key={order_mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, exit_side, position_side, adjusted_sub_qty, "LIMIT", calculated_price_float, None, True, open_orders_state_local, order_type_mapping_local, order_mapping_key)
    return order_data, success, error_code

async def get_current_position_quantity(client: HTTP, symbol: str, position_side_to_check: str) -> Decimal:
    try:
        category = config.CATEGORY
        response = await asyncio.to_thread(
            client.get_positions,
            category=category,
            symbol=symbol
        )
        positions = response.get('result', {}).get('list', [])
        
        for p in positions:
            side_str = p.get('side') # 'Buy' or 'Sell'
            if (position_side_to_check == 'LONG' and side_str == 'Buy') or (position_side_to_check == 'SHORT' and side_str == 'Sell'):
                return Decimal(p.get('size', '0'))
        return Decimal('0')
    except Exception as e:
        logging.error(f"get_current_position_quantity({symbol}, {position_side_to_check}) 오류: {e}")
        return Decimal('0')

async def place_trailing_stop_exit_order(client: HTTP, symbol_info_local: dict, state: dict, current_step: int, quantity: float, main_pos_side: str, callback_rate: float):
    # (주의: Bybit는 %가 아닌 가격 '거리'를 사용. callback_rate를 가격 거리로 해석)
    logging.warning(f"[place_trailing_stop_exit_order] Bybit TSM 주문: callback_rate({callback_rate})를 가격 '거리'로 사용합니다.")
    
    symbol = state.get('symbol')
    open_orders_state_ref = state.get('open_orders_state')
    order_type_mapping_ref = state.get('order_type_mapping')

    side = 'SELL' if main_pos_side == 'LONG' else 'BUY'
    position_side = main_pos_side # 'LONG' or 'SHORT'
    order_key_suffix = f"{current_step}-HedgeTSM"
    order_mapping_key = f"HedgePartialExitSM-{current_step}-{int(time.time())}" # (이름은 SM이지만 TSM을 사용)

    order_data, success, error_code = await place_futures_order(
        client=client, 
        symbol_info=symbol_info_local, 
        symbol=symbol,
        side=side, 
        position_side=position_side, 
        quantity=quantity,
        order_type="TRAILING_STOP_MARKET",
        callback_rate=callback_rate, # 가격 거리
        activation_price=None, # 즉시 발동
        reduce_only=True,
        open_orders_state_ref=open_orders_state_ref,
        order_type_mapping_ref=order_type_mapping_ref,
        mapping_key=order_mapping_key
    )
    
    return order_data, success, error_code


async def place_partial_hedge_exit_market_order(
    client: HTTP,
    symbol_info_local: dict,
    state: dict,
    step_index_info: int,
    quantity: Decimal,
    main_pos_side: str
) -> tuple[dict | None, bool, str | None]:
    
    symbol = state.get('symbol')
    open_orders_state_ref = state.get('open_orders_state')
    order_type_mapping_ref = state.get('order_type_mapping')

    hedge_exit_side = None
    hedge_pos_side_to_exit = None

    if main_pos_side == 'LONG':
        hedge_exit_side = "BUY"
        hedge_pos_side_to_exit = 'SHORT'
    elif main_pos_side == 'SHORT':
        hedge_exit_side = "SELL"
        hedge_pos_side_to_exit = 'LONG'
    else:
        logging.error(f"[PartialHedgeExitMarket] 알 수 없는 주 포지션({main_pos_side}). 헤지 청산 불가.")
        return None, False, "INVALID_MAIN_POS_SIDE"

    mapping_key = f"PartialHedgeExitMarket-{step_index_info}-{int(time.time())}"
    
    logging.info(f"[PartialHedgeExitMarket 스텝 {step_index_info}] 실행: Side={hedge_exit_side}, PosSide={hedge_pos_side_to_exit}, Qty={quantity}, Key={mapping_key}")

    order_data, success, error_code = await place_futures_order(
        client, symbol_info_local, symbol,
        hedge_exit_side, hedge_pos_side_to_exit, float(quantity),
        order_type="MARKET",
        reduce_only=True, # reduceOnly=True로 수정
        open_orders_state_ref=open_orders_state_ref,
        order_type_mapping_ref=order_type_mapping_ref,
        mapping_key=mapping_key
    )

    if success and order_data:
        logging.info(f"  -> [PartialHedgeExitMarket] 주문 성공. ID: {order_data.get('orderId')}")
    else:
        logging.error(f"  -> [PartialHedgeExitMarket] 주문 실패. ErrorCode: {error_code}")
        
    return order_data, success, error_code

async def place_orders_for_step(
    client: HTTP,
    gui,
    symbol_info_local: dict,
    state: dict,
    current_step_index_local: int,
    trigger_event: str
):
    function_name = "logic.place_orders_for_step (Bybit)"
    logging.info(f"=== 스텝 {current_step_index_local} 주문 설정 시작 ({function_name}, Trigger: {trigger_event}) ===")
    category = config.CATEGORY

    try:
        symbol = state.get('symbol')
        open_orders_state_local = state.get('open_orders_state', {})
        order_type_mapping_local = state.get('order_type_mapping', {})
        signal_type_local = state.get('signal_type')
        entry_quantity_list_local = state.get('entry_quantity_list')
        per_step_hedge_quantity_list_local = state.get('per_step_hedge_quantity_list')
        exit_ratio_list_local = state.get('exit_ratio_list')
        previous_exit_price = state.get('previous_exit_price')
        
        if not all([symbol, entry_quantity_list_local, exit_ratio_list_local, signal_type_local, per_step_hedge_quantity_list_local, symbol_info_local]):
            logging.error(f"[{function_name}] 주문 설정 불가: 필수 정보 부족.")
            return

        logging.info(f"[{function_name}] 기존 익절/마지노 주문 정리 시작")
        
        if trigger_event != 'STEP_DOWN':
            await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'MainPartialExitTSM-')
        else:
            logging.info(f"[{function_name}] Trigger가 'STEP_DOWN'이므로, 기존 MainPartialExitTSM 주문을 유지합니다.")
            
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'HedgePartialExitSM-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'Maginot-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'MainStopLoss-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'HedgeTakeProfitTSM-')

        try:
            margin_to_add = 0.0
            
            if category == 'inverse':
                margin_to_add = 0.00001 
            else: # linear
                margin_to_add = 0.01

            logging.info(f"[{category} 모드] API 정보 업데이트를 위해 {margin_to_add} 증거금을 포지션에 추가합니다.")
            
            
            await add_margin_to_position(
                client=client,
                symbol=symbol,
                position_side=signal_type_local, # 'LONG' 또는 'SHORT'
                amount=margin_to_add,
                gui=gui
            )
            # --- 수정 끝 ---
            logging.info("증거금 추가 요청 완료. 잠시 후 포지션 정보 조회를 시작합니다.")
            await asyncio.sleep(1)

        except Exception as margin_err:
            logging.warning(f"증거금 추가 '트릭' 실행 중 오류 발생 (무시하고 진행): {margin_err}")
            
        positions = []
        main_pos_qty, main_pos_avg_price, main_pos_liq_price = Decimal('0'), Decimal('0'), Decimal('0')
        hedge_pos_qty = Decimal('0')
        
        max_retries_pos = 15
        for attempt in range(max_retries_pos):
            response = await asyncio.to_thread(
                client.get_positions,
                category=category,
                symbol=symbol
            )
            positions = response.get('result', {}).get('list', [])

            for p_info in positions:
                side_str = p_info.get('side') # 'Buy' or 'Sell'
                amt = Decimal(p_info.get('size', '0'))
                
                if (signal_type_local == 'LONG' and side_str == 'Buy') or (signal_type_local == 'SHORT' and side_str == 'Sell'):
                    main_pos_qty = amt
                    main_pos_avg_price = Decimal(p_info.get('avgPrice', '0'))
                    main_pos_liq_price = Decimal(p_info.get('liqPrice', '0'))
                elif (signal_type_local == 'LONG' and side_str == 'Sell') or (signal_type_local == 'SHORT' and side_str == 'Buy'):
                    hedge_pos_qty = amt

            if main_pos_liq_price > 0:
                logging.info(f"[{function_name}] 시도 {attempt + 1}: 유효한 청산가({main_pos_liq_price}) 확인 완료.")
                break
            logging.warning(f"[{function_name}] 시도 {attempt + 1}: 유효한 청산가({main_pos_liq_price})가 아직 유효하지 않습니다. 1초 후 재시도합니다.")
            if attempt < max_retries_pos - 1:
                await asyncio.sleep(1)
            else:
                logging.error(f"[{function_name}] 최대 재시도 횟수({max_retries_pos}) 초과. 유효한 청산가를 얻지 못했습니다.")

        price_precision = int(symbol_info_local.get('pricePrecision', 4))
        logging.info(f"[{function_name}] 주 포지션({signal_type_local}): Qty={main_pos_qty} @ {main_pos_avg_price:.{price_precision}f}")
        logging.info(f"[{function_name}] 헤지 포지션: Qty={hedge_pos_qty}")

        current_step_hedge_qty = Decimal(str(per_step_hedge_quantity_list_local[current_step_index_local]))
        min_qty = Decimal(str(symbol_info_local.get('minQty', '0.1')))

        trigger_price = Decimal('0')
        if previous_exit_price and previous_exit_price > 0:
            base_price = Decimal(str(previous_exit_price))
            divide_rate = Decimal(str(config.DIVIDE_RATE))
            trigger_price = base_price * (Decimal('1') + divide_rate) if signal_type_local == 'LONG' else base_price * (Decimal('1') - divide_rate)
        elif main_pos_qty > 0:
            exit_ratio = Decimal(str(exit_ratio_list_local[current_step_index_local]))
            trigger_price = main_pos_avg_price * (Decimal('1') + exit_ratio) if signal_type_local == 'LONG' else main_pos_avg_price * (Decimal('1') - exit_ratio)

        if trigger_price > 0:
            formatted_trigger_price = format_price(trigger_price, symbol_info_local.get('tickSize'))
            main_exit_qty = float(entry_quantity_list_local[current_step_index_local])
            
            # (주의: Bybit는 TSM % 대신 가격 '거리'를 사용. CALLBACK_RATE를 거리로 해석)
            callback_distance = float(formatted_trigger_price) * (config.CALLBACK_RATE / 100.0)
            logging.warning(f"Bybit TSM 주문: CALLBACK_RATE({config.CALLBACK_RATE}%)를 가격 거리({callback_distance})로 변환하여 사용합니다.")

            if main_pos_qty > 0 and hedge_pos_qty > 0 and current_step_hedge_qty >= min_qty:
                logging.info(f"[{function_name}] 시나리오 1 활성화 (주+헤지 동시 익절). 발동가: {formatted_trigger_price}")
                hedge_exit_qty = float(current_step_hedge_qty)
                main_exit_side, main_exit_pos_side = ("SELL", 'LONG') if signal_type_local == 'LONG' else ("BUY", 'SHORT')
                hedge_exit_side, hedge_exit_pos_side = ("BUY", 'SHORT') if signal_type_local == 'LONG' else ("SELL", 'LONG')
                
                await place_futures_order(client, 
                                          symbol_info=symbol_info_local, symbol=symbol, side=main_exit_side, 
                                          position_side=main_exit_pos_side, quantity=main_exit_qty,
                                          order_type="TRAILING_STOP_MARKET", 
                                          activation_price=float(formatted_trigger_price), 
                                          callback_rate=callback_distance, # 거리
                                          reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, 
                                          order_type_mapping_ref=order_type_mapping_local, 
                                          mapping_key=f"MainPartialExitTSM-{current_step_index_local}")

                if gui: gui.update_exit_target_price(f"TSM @ {formatted_trigger_price}")
                    
                await place_futures_order(client, 
                                          symbol_info=symbol_info_local, symbol=symbol, side=hedge_exit_side, 
                                          position_side=hedge_exit_pos_side, quantity=hedge_exit_qty,
                                          order_type="STOP_MARKET", 
                                          stop_price=float(formatted_trigger_price), reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, 
                                          order_type_mapping_ref=order_type_mapping_local, 
                                          mapping_key=f"HedgePartialExitSM-{current_step_index_local}")

            elif main_pos_qty > 0:
                logging.info(f"[{function_name}] 시나리오 2 활성화 (주 포지션만 익절). 발동가: {formatted_trigger_price}")
                main_exit_side, main_exit_pos_side = ("SELL", 'LONG') if signal_type_local == 'LONG' else ("BUY", 'SHORT')

                await place_futures_order(client, 
                                          symbol_info=symbol_info_local, symbol=symbol, side=main_exit_side, 
                                          position_side=main_exit_pos_side, quantity=main_exit_qty,
                                          order_type="TRAILING_STOP_MARKET", 
                                          activation_price=float(formatted_trigger_price), 
                                          callback_rate=callback_distance, # 거리
                                          reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, 
                                          order_type_mapping_ref=order_type_mapping_local, 
                                          mapping_key=f"MainPartialExitTSM-{current_step_index_local}")
                if gui: gui.update_exit_target_price(f"TSM @ {formatted_trigger_price}")
        else:
            logging.warning(f"[{function_name}] 익절 주문 설정 조건 불충족.")

        if current_step_index_local == config.STEPS - 1:
            logging.info(f"[{function_name}] 최종 스텝({current_step_index_local}) 손절매/헤지익절 주문 설정.")
            if main_pos_avg_price > 0 and main_pos_liq_price > 0:
                maginot_factor = Decimal('1') - Decimal(str(config.MAGINOT))
                if signal_type_local == 'LONG':
                    stop_price_dec = main_pos_avg_price - (main_pos_avg_price - main_pos_liq_price) * maginot_factor
                    main_stop_side, main_stop_pos_side, hedge_profit_side, hedge_profit_pos_side = "SELL", 'LONG', "BUY", 'SHORT'
                else:
                    stop_price_dec = main_pos_avg_price + (main_pos_liq_price - main_pos_avg_price) * maginot_factor
                    main_stop_side, main_stop_pos_side, hedge_profit_side, hedge_profit_pos_side = "BUY", 'SHORT', "SELL", 'LONG'

                formatted_stop_price = format_price(stop_price_dec, symbol_info_local.get('tickSize'))
                
                callback_distance_last = float(formatted_stop_price) * (config.CALLBACK_RATE_FOR_LAST / 100.0)

                if main_pos_qty > 0:
                    await place_futures_order(client, 
                                              symbol_info=symbol_info_local, symbol=symbol, side=main_stop_side, 
                                              position_side=main_stop_pos_side, quantity=float(main_pos_qty),
                                              order_type="STOP_MARKET", 
                                              stop_price=float(formatted_stop_price), reduce_only=True,
                                              open_orders_state_ref=open_orders_state_local, 
                                              order_type_mapping_ref=order_type_mapping_local, 
                                              mapping_key=f"MainStopLoss-{current_step_index_local}")
                if hedge_pos_qty > 0:
                     await place_futures_order(client, 
                                              symbol_info=symbol_info_local, symbol=symbol, side=hedge_profit_side, 
                                              position_side=hedge_profit_pos_side, quantity=float(hedge_pos_qty),
                                              order_type="TRAILING_STOP_MARKET", 
                                              activation_price=float(formatted_stop_price), 
                                              callback_rate=callback_distance_last, # 거리
                                              reduce_only=True,
                                              open_orders_state_ref=open_orders_state_local, 
                                              order_type_mapping_ref=order_type_mapping_local, 
                                              mapping_key=f"HedgeTakeProfitTSM-{current_step_index_local}")
        else:
            next_maginot_step_index = current_step_index_local + 1
            if main_pos_avg_price > 0 and main_pos_liq_price > 0:
                maginot_qty_for_next_step = Decimal(str(entry_quantity_list_local[next_maginot_step_index]))
                if maginot_qty_for_next_step >= min_qty:
                    maginot_factor = Decimal('1') - Decimal(str(config.MAGINOT))
                    maginot_price_dec = main_pos_avg_price - (main_pos_avg_price - main_pos_liq_price) * maginot_factor if signal_type_local == 'LONG' else main_pos_avg_price + (main_pos_liq_price - main_pos_avg_price) * maginot_factor
                    maginot_side, maginot_pos_side = ("BUY", 'LONG') if signal_type_local == 'LONG' else ("SELL", 'SHORT')
                    formatted_maginot_price = format_price(maginot_price_dec, symbol_info_local.get('tickSize'))
                    logging.info(f"[{function_name}] 다음 스텝({next_maginot_step_index}) Maginot({maginot_pos_side}) 주문 설정: Qty={maginot_qty_for_next_step}, Price={formatted_maginot_price}")
                    
                    _ , success, error_code = await place_futures_order(
                        client, 
                        symbol_info=symbol_info_local, symbol=symbol, side=maginot_side, 
                        position_side=maginot_pos_side, quantity=float(maginot_qty_for_next_step),
                        order_type="LIMIT", price=float(formatted_maginot_price), 
                        reduce_only=False,
                        open_orders_state_ref=open_orders_state_local, 
                        order_type_mapping_ref=order_type_mapping_local, 
                        mapping_key=f"Maginot-{next_maginot_step_index}"
                    )

                    # Bybit 'Insufficient balance' (110007)
                    if not success and error_code == 110007:
                        logging.warning(f"Maginot 주문 증거금 부족(110007). 증거금 1회 추가 후 재시도 로직을 시작합니다.")
                        margin_added_successfully_once = False
                        
                        max_retries_margin = config.ORDER_RETRY_ATTEMPTS
                        for attempt in range(max_retries_margin):
                            logging.info(f"Maginot 주문 재시도 {attempt + 1}/{max_retries_margin}...")

                            if not margin_added_successfully_once:
                                logging.info("증거금 추가를 시도합니다 (이번 재시도 루프에서 첫 시도).")
                                current_position_value = main_pos_qty * main_pos_avg_price
                                current_initial_margin = current_position_value / Decimal(str(config.TARGET_LEVERAGE))
                                margin_to_add = current_initial_margin * Decimal('0.1')
                                
                                margin_added, _ = await add_margin_to_position(client, symbol, maginot_pos_side, float(margin_to_add), gui)
                                
                                if margin_added:
                                    margin_added_successfully_once = True
                                    logging.info("증거금 추가 성공. 이제부터는 주문만 재시도합니다.")
                                else:
                                    logging.error("재시도 중 증거금 추가에 실패했습니다. 재시도를 중단합니다.")
                                    break
                            
                            logging.info(f"Maginot 지정가 주문 재시도 {attempt + 1}...")
                            _, success, error_code = await place_futures_order(
                                client,
                                symbol_info=symbol_info_local, symbol=symbol, side=maginot_side, 
                                position_side=maginot_pos_side, quantity=float(maginot_qty_for_next_step),
                                order_type="LIMIT", price=float(formatted_maginot_price),
                                reduce_only=False,
                                open_orders_state_ref=open_orders_state_local, 
                                order_type_mapping_ref=order_type_mapping_local, 
                                mapping_key=f"Maginot-{next_maginot_step_index}"
                            )
                            
                            if success:
                                logging.info(f"Maginot 주문 재시도 {attempt + 1} 성공!")
                                break
                            else:
                                logging.warning(f"Maginot 주문 재시도 {attempt + 1} 실패. ErrorCode: {error_code}.")
                            
                            await asyncio.sleep(config.ORDER_RETRY_DELAY_SECONDS)

                        if not success:
                            final_fail_msg = f"Maginot 주문 최종 실패: {max_retries_margin}번의 재시도 후에도 주문을 생성할 수 없었습니다. 수동 개입이 필요합니다."
                            logging.critical(final_fail_msg)
                            if gui: gui.show_error_popup("치명적 오류", final_fail_msg)
            else:
                logging.warning(f"[{function_name}] 다음 스텝 Maginot 주문 설정 불가: 평단가/청산가 정보 부족.")
        
        if gui:
            gui.update_open_orders_display(list(open_orders_state_local.values()), order_type_mapping_local)

    except Exception as e:
        logging.error(f"[{function_name}] 스텝 {current_step_index_local} 주문 설정 중 예외 발생: {e}", exc_info=True)
    
    logging.info(f"=== 스텝 {current_step_index_local} 주문 설정 로직 완료 ({function_name}) ===")

async def close_all_open_positions_for_symbol(client: HTTP, symbol: str, symbol_info_local: dict, open_orders_state_ref: dict, order_type_mapping_ref: dict):
    logging.info(f"[{symbol}] 모든 오픈 포지션 종료 시도...")
    closed_count = 0; failed_count = 0; all_positions_closed_successfully = True 
    category = config.CATEGORY
    try:
        response = await asyncio.to_thread(
            client.get_positions,
            category=category,
            symbol=symbol
        )
        positions = response.get('result', {}).get('list', [])
        
        if not positions: logging.info(f"[{symbol}] 조회된 포지션 정보 없음. 종료할 포지션 없음."); return True
        qty_precision = symbol_info_local.get('quantityPrecision'); step_size = symbol_info_local.get('stepSize'); min_qty_str = symbol_info_local.get('minQty')
        if qty_precision is None or step_size is None or min_qty_str is None: logging.error(f"[{symbol}] 포지션 종료 위한 심볼 정보 부족."); return False
        
        active_positions_to_close = []
        for position in positions:
            pos_amt_str = position.get('size', '0'); pos_side = position.get('side') # 'Buy' or 'Sell'
            try:
                pos_amt_decimal = Decimal(pos_amt_str)
                if pos_amt_decimal > Decimal('0'):
                    active_positions_to_close.append({'amount_decimal': pos_amt_decimal, 'side_str': pos_side, 'symbol': position.get('symbol')})
            except Exception as e: logging.warning(f"[{symbol}] 포지션 수량 '{pos_amt_str}' 처리 중 오류: {e}. 건너뜀."); continue
        
        if not active_positions_to_close: logging.info(f"[{symbol}] 현재 활성 포지션 없음. 종료 작업 불필요."); return True
        
        for pos_data in active_positions_to_close:
            pos_amt_dec = pos_data['amount_decimal']; bybit_pos_side = pos_data['side_str'] 
            
            order_side_to_close = "Sell" if bybit_pos_side == "Buy" else "Buy"
            internal_position_side = "LONG" if bybit_pos_side == "Buy" else "SHORT"
            
            quantity_to_close_abs_dec = abs(pos_amt_dec)
            adjusted_qty_float = adjust_quantity(float(quantity_to_close_abs_dec), step_size, qty_precision, min_qty_str)
            if adjusted_qty_float is None or adjusted_qty_float <= 0: logging.error(f"[{symbol}] 포지션({bybit_pos_side}) 종료 수량 조정 실패."); failed_count += 1; all_positions_closed_successfully = False; continue
            
            logging.info(f"  - [{symbol}] 포지션({bybit_pos_side}, 현재수량:{pos_amt_dec}) 종료 주문 요청: Side={order_side_to_close}, Qty={adjusted_qty_float}, PosSide(내부)={internal_position_side}, ReduceOnly=True")
            mapping_key_close_pos = f"SysClosePos-{symbol}-{bybit_pos_side}-{int(time.time())}"
            
            order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, order_side_to_close, internal_position_side, adjusted_qty_float, "MARKET", None, None, True, open_orders_state_ref, order_type_mapping_ref, mapping_key_close_pos)
            
            if success and order_data: logging.info(f"    -> [{symbol}] 포지션({bybit_pos_side}) 종료 주문 요청 성공. OrderID: {order_data.get('orderId')}"); closed_count += 1
            else: logging.error(f"    -> [{symbol}] 포지션({bybit_pos_side}) 종료 주문 요청 실패. ErrorCode: {error_code}"); failed_count += 1; all_positions_closed_successfully = False
            await asyncio.sleep(0.25) 

        if failed_count == 0 and closed_count > 0: logging.info(f"[{symbol}] 총 {closed_count}개 포지션에 대한 종료 주문 성공적으로 '요청'됨.")
        elif closed_count > 0 and failed_count > 0: logging.warning(f"[{symbol}] {closed_count}개 포지션 종료 주문 요청, {failed_count}개 실패.")
        elif closed_count == 0 and failed_count > 0: logging.error(f"[{symbol}] 모든 포지션 종료 주문 요청 실패 ({failed_count}개).")
        return all_positions_closed_successfully
    except Exception as e: logging.error(f"[{symbol}] 모든 포지션 종료 처리 중 예기치 않은 오류: {e}", exc_info=True); return False

async def place_exit_hedge_order(client: HTTP, gui, symbol_info_local: dict, state: dict, filled_step_index: int, position_side_local: str):
    if filled_step_index == 0 and config.STEPS > 1 :
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 스텝 0에서는 Trailing Exit Hedge 주문을 생성하지 않습니다.")
        return False, None
    try:
        symbol = state['symbol']; open_orders_state_local = state['open_orders_state']; order_type_mapping_local = state['order_type_mapping']
        step_size = symbol_info_local.get('stepSize'); qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty'); tick_size = symbol_info_local.get('tickSize')
        category = config.CATEGORY

        if not all([step_size, qty_precision is not None, min_qty_str, tick_size]): logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: 필수 심볼 정보 누락."); return False, None
        
        response = await asyncio.to_thread(
            client.get_positions,
            category=category,
            symbol=symbol
        )
        positions = response.get('result', {}).get('list', [])
        current_pos = None
        for p in positions:
            if position_side_local == 'LONG' and p.get('side') == 'Buy': current_pos = p; break
            if position_side_local == 'SHORT' and p.get('side') == 'Sell': current_pos = p; break

        if not current_pos or float(current_pos.get('size', '0')) == 0: 
            logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 포지션 없음, Hedge 생성 안함")
            return False, None
        
        avg_entry_price = float(current_pos.get('avgPrice', '0'))
        if avg_entry_price <= 0: 
            logging.warning(f"[EXIT HEDGE] 스텝 {filled_step_index}: 유효 진입가 없음 ({avg_entry_price})")
            return False, None
        
        position_amt = abs(float(current_pos.get('size', '0'))) # Bybit는 'size'
        adjusted_hedge_qty = adjust_quantity(position_amt, step_size, qty_precision, min_qty_str)
        
        if adjusted_hedge_qty is None or adjusted_hedge_qty <= 0: 
            logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: 헷지 수량 조정 실패: 원본={position_amt}, 조정={adjusted_hedge_qty}")
            return False, None
        
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 사전 조정된 헷지 수량: {adjusted_hedge_qty} (원본: {position_amt})")
        
        activation_price = avg_entry_price
        
        # (중요) Bybit는 %가 아닌 가격 '거리'를 사용합니다.
        # config.CALLBACK_RATE가 %라면 가격 거리로 변환해야 합니다.
        callback_distance = float(activation_price) * (config.CALLBACK_RATE / 100.0)
        logging.warning(f"Bybit TSM 주문: CALLBACK_RATE({config.CALLBACK_RATE}%)를 가격 거리({callback_distance})로 변환하여 사용합니다.")

        side = "Sell" if position_side_local == 'LONG' else "Buy" # Bybit side
        formatted_activation_price = format_price(activation_price, tick_size)
        
        if formatted_activation_price is None: 
            logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: Activation Price 포맷팅 실패: {activation_price}")
            return False, None
        
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index} TRAILING_STOP 주문 시도: Act.Price={formatted_activation_price}, Distance={callback_distance}")

        # 기존 ExitHedge- 접두사 주문 취소 (중복 방지)
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'ExitHedge-')
        if gui: gui.update_open_orders_display(list(open_orders_state_local.values()), order_type_mapping_local)

        # 중앙 주문 함수 사용
        order_mapping_key = f'ExitHedge-{filled_step_index}'
        order_data, success, error_code = await place_futures_order(
            client=client, 
            symbol_info=symbol_info_local, 
            symbol=symbol,
            side=side, 
            position_side=position_side_local, 
            quantity=float(adjusted_hedge_qty),
            order_type="TRAILING_STOP_MARKET",
            activation_price=float(formatted_activation_price),
            callback_rate=callback_distance, # 가격 거리 전달
            reduce_only=True,
            open_orders_state_ref=open_orders_state_local,
            order_type_mapping_ref=order_type_mapping_local,
            mapping_key=order_mapping_key
        )

        if success:
            logging.info(f"[EXIT HEDGE] 주문 성공: ID={order_data.get('orderId')}, 구분={order_mapping_key}")
            return True, order_data
        else:
            logging.error(f"[EXIT HEDGE] 주문 실패. ErrorCode: {error_code}")
            return False, None

    except Exception as e: 
        logging.error(f"[EXIT HEDGE] 주문 생성 중 오류: {e}", exc_info=True)
        return False, None

async def place_general_order(client: HTTP, gui, symbol_info, state, step_index: int, quantity: float, attempt_key_prefix_base: str):
    """ (참고: 이 함수는 place_general_order_market으로 대체되어 거의 사용되지 않을 수 있음) """
    logging.info(f"[General주문 스텝{step_index}] 생성 시도. 수량: {quantity} (Hardcoded LONG)")
    order_mapping_key = f"{attempt_key_prefix_base}-0"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side="Buy", position_side='LONG', quantity=quantity, # Bybit: "Buy"
        order_type="Market", # Bybit: "Market"
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[General주문 스텝{step_index}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[General주문 스텝{step_index}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_general_order_market(client: HTTP, gui, symbol_info, state, step_index: int, quantity: float, base_attempt_key_prefix: str, signal_type: str):
    """ General 주문 (MARKET) 생성 - signal_type에 따라 동적으로 주문 (Bybit용) """
    logging.info(f"[General주문 스텝{step_index}] Market 생성 시도. 수량: {quantity}, 기준: {signal_type}")
    
    order_mapping_key = f"{base_attempt_key_prefix}-0" 
    client_oid_suffix = str(int(time.time() * 1000))[-4:]
    # Bybit orderLinkId는 최대 36자
    generated_client_order_id = f"{order_mapping_key.replace('-', '_')}_{client_oid_suffix}"[:36]
    
    if signal_type == 'SHORT':
        order_side = "SELL"
        order_position_side = 'SHORT'
    else: # 기본값 또는 'LONG'
        order_side = "BUY"
        order_position_side = 'LONG'

    logging.info(f"Generated ClientOrderId (orderLinkId) for General Order: {generated_client_order_id}")

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=order_side, position_side=order_position_side, quantity=quantity,
        order_type="Market", # Bybit: "Market"
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key, 
        client_order_id=generated_client_order_id 
    )
    if success: logging.info(f"[General주문 스텝{step_index}] Market 성공. OrderID: {order_data.get('orderId')}, ClientOID: {order_data.get('orderLinkId')}")
    else: logging.error(f"[General주문 스텝{step_index}] Market 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_hedge_order_for_general(
    client: HTTP, 
    gui, 
    symbol_info_local: dict,
    state: dict, 
    general_step_index: int, 
    hedge_quantity: float,
    general_order_main_side: str
):
    """
    General/Maginot 주문 체결 후 헤지 주문(시장가)을 실행하고, 결과(성공, 실패, 에러코드)를 반환합니다. (Bybit용)
    """
    function_name = "logic.place_hedge_order_for_general (Bybit)"
    logging.info(f"[{function_name}] 스텝 {general_step_index} 헤지 주문 생성. 주포지션: {general_order_main_side}, 목표수량: {hedge_quantity}")
    
    symbol = state.get('symbol', config.SYMBOL) 
    open_orders_state_ref = state.get('open_orders_state')
    order_type_mapping_ref = state.get('order_type_mapping')

    if not symbol_info_local:
        logging.error(f"[{function_name}] 헤지 주문 불가: symbol_info 없음.")
        return None, False, "NO_SYMBOL_INFO"

    hedge_side = "Sell" if general_order_main_side == 'LONG' else "Buy"
    hedge_position_side = 'SHORT' if general_order_main_side == 'LONG' else 'LONG'

    order_mapping_key = f"HedgeForGeneral-{general_step_index}-{int(time.time())}" 
    logging.info(f"  -> [{function_name}] 주문 요청: Side={hedge_side}, PosSide={hedge_position_side}, Qty={hedge_quantity}")

    order_data, success, error_code = await place_futures_order(
        client=client,
        symbol_info=symbol_info_local,
        symbol=symbol,
        side=hedge_side,
        position_side=hedge_position_side,
        quantity=hedge_quantity,
        order_type="Market", # Bybit: "Market"
        open_orders_state_ref=open_orders_state_ref,
        order_type_mapping_ref=order_type_mapping_ref,
        mapping_key=order_mapping_key
    )

    if success:
        logging.info(f"[{function_name}] 스텝 {general_step_index} 헤지 주문 요청 성공. ID: {order_data.get('orderId') if order_data else 'N/A'}")
    else:
        logging.error(f"[{function_name}] 스텝 {general_step_index} 헤지 주문 요청 실패. ErrorCode: {error_code}")
    
    return order_data, success, error_code

async def place_maginot_order(client: HTTP, gui, symbol_info, state, step_to_place_maginot: int, quantity: float, price: float):
    """ (참고: 이 함수는 place_orders_for_step으로 통합되어 거의 사용되지 않을 수 있음) """
    logging.info(f"[Maginot주문 스텝{step_to_place_maginot}] 생성 시도. 수량: {quantity}, 가격: {price} (Hardcoded LONG)")
    order_mapping_key = f"Maginot-{step_to_place_maginot}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side="Buy", position_side='LONG', quantity=quantity, # Bybit: "Buy"
        order_type="Limit", price=price, # Bybit: "Limit"
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[Maginot주문 스텝{step_to_place_maginot}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[Maginot주문 스텝{step_to_place_maginot}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_maginot_hedge_order(client: HTTP, gui, symbol_info, state, maginot_step_index: int, hedge_quantity: float):
    """ (참고: 이 함수는 place_hedge_order_for_general로 대체되어 거의 사용되지 않을 수 있음) """
    logging.info(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 생성 시도. 수량: {hedge_quantity} (Hardcoded SHORT)")
    order_mapping_key = f"MaginotHedge-{maginot_step_index}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side="Sell", position_side='SHORT', quantity=hedge_quantity, # Bybit: "Sell"
        order_type="Market", # Bybit: "Market"
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_main_exit_order_trailing_stop(client: HTTP, gui, symbol_info, state, quantity: float, callback_rate: float, order_key_suffix: str = ""):
    """ 주 포지션(LONG) 청산을 위한 Exit 주문 (TRAILING_STOP_MARKET) 생성 (Bybit용) """
    logging.info(f"[MainExit-TSM 스텝{order_key_suffix}] 생성 시도. 수량: {quantity}, 콜백(거리): {callback_rate} (Hardcoded LONG)")
    order_mapping_key = f"MainExitTSM-{order_key_suffix}-{int(time.time())}"

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side="Sell", position_side='LONG', quantity=quantity, # LONG 포지션 청산
        order_type="TRAILING_STOP_MARKET",
        callback_rate=callback_rate, # 가격 거리
        reduce_only=True,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[MainExit-TSM 스텝{order_key_suffix}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[MainExit-TSM 스텝{order_key_suffix}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_hedge_exit_order_stop_market(client: HTTP, gui, symbol_info, state, quantity: float, stop_price: float, order_key_suffix: str = ""):
    """ 헤지 포지션(SHORT) 청산을 위한 Exit Hedge 주문 (STOP_MARKET) 생성 (Bybit용) """
    logging.info(f"[HedgeExit-SM 스텝{order_key_suffix}] 생성 시도. 수량: {quantity}, 발동가: {stop_price} (Hardcoded SHORT)")
    order_mapping_key = f"HedgeExitSM-{order_key_suffix}-{int(time.time())}"

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side="Buy", position_side='SHORT', quantity=quantity, # SHORT 포지션 청산
        order_type="STOP_MARKET", stop_price=stop_price,
        reduce_only=True,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[HedgeExit-SM 스텝{order_key_suffix}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[HedgeExit-SM 스텝{order_key_suffix}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def add_margin_to_position(
    client: HTTP, 
    symbol: str, 
    position_side: str, 
    amount: float, 
    gui
) -> tuple[bool, int | None]:
    """
    지정된 격리 포지션에 증거금을 추가합니다. (Bybit용)
    :return: (성공 여부, API 에러 코드)
    """
    
    # 1. Bybit용 파라미터 준비
    position_idx = 1 if position_side == "LONG" else (2 if position_side == "SHORT" else 0)
    if position_idx == 0:
        logging.error(f"[{symbol}-{position_side}] 증거금 추가 불가: 유효하지 않은 position_side.")
        return False, -1 # 내부 로직 오류
        
    # Bybit는 증거금을 문자열로 받으며, 코인에 따라 정밀도가 중요할 수 있음
    # USDT의 경우
    if config.CATEGORY == 'linear':
        formatted_amount = f"{amount:.4f}" 
    else: # COIN-M
        formatted_amount = f"{amount:.8f}" # 예: BTC

    logging.info(f"[{symbol}-{position_side}(Idx:{position_idx})] 포지션에 증거금 {formatted_amount} {config.BALANCE_ASSET} 추가 시도...")

    max_retries = config.ORDER_RETRY_ATTEMPTS
    base_retry_delay_seconds = config.ORDER_RETRY_DELAY_SECONDS
    category = config.CATEGORY

    for attempt in range(max_retries):
        try:
            response = await asyncio.to_thread(
                client.add_margin,
                category=category,
                symbol=symbol,
                margin=formatted_amount,
                positionIdx=position_idx
            )
            
            if response.get('retCode') != 0:
                # 이미 추가 중이거나(110034), 모드 불일치 등
                raise InvalidRequestError(status_code=response.get('retCode'), message=response.get('retMsg'), response=response)

            success_msg = f"✅ 증거금 추가 성공: {formatted_amount}이 {symbol}-{position_side} 포지션에 추가되었습니다."
            logging.info(success_msg)
            if gui:
                original_status = gui.status_var.get()
                gui.update_status(f"증거금 {formatted_amount} 추가 완료!")
                gui.root.after(3000, lambda: gui.update_status(original_status)) # 3초 후 원래 상태로
            return True, None # 성공

        except (InvalidRequestError, FailedRequestError) as e:
            error_code = e.status_code
            logging.error(f"증거금 추가 시도 {attempt + 1}/{max_retries} 실패: {e}")
            
            if error_code == 10006 and attempt < max_retries - 1: # Rate limit
                current_retry_delay = base_retry_delay_seconds
                logging.info(f"서버 과부하 (코드: 10006). {current_retry_delay}초 후 재시도합니다...")
                await asyncio.sleep(current_retry_delay)
            else: 
                fail_msg = f"🚨 증거금 추가 최종 실패 (코드: {error_code}): {e.message}"
                # GUI 팝업은 main.py의 place_orders_for_step에서 처리하도록 제거
                return False, error_code # 실패
    
    return False, -1 # 루프 모두 실패