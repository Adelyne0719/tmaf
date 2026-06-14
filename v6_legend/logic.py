# logic.py
import logging
import asyncio
import time
import aiohttp
import hashlib
import hmac
import urllib.parse
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext
from binance import AsyncClient
from binance.enums import *
from binance.error import ClientError
import gui

import math # ceil 대신 // 사용 예정이지만 혹시 몰라 유지

price_precision = None

getcontext().prec = 28

# --- 🟢 2. 아래 코드를 추가하세요. ---
# main.py에서 설정을 받아 저장할 전역 변수
config = None
# Algo 주문 생성 시 보호 리스트에 등록하는 콜백 함수
algo_order_protection_callback = None

def set_config_source(config_obj):
    """main.py로부터 설정 객체를 받아 이 모듈의 전역 변수로 설정합니다."""
    global config
    config = config_obj
    logging.info("logic.py: Configuration source has been set.")

def set_algo_order_protection_callback(callback_func):
    """main.py로부터 Algo 주문 보호 콜백을 받아 설정합니다."""
    global algo_order_protection_callback
    algo_order_protection_callback = callback_func
    logging.info("logic.py: Algo order protection callback has been set.")
# --- 추가 코드 끝 ---

# --- 유틸리티 함수 ---
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
    except Exception as e: logging.error(f"소수점 자릿수 계산 오류: {number_str}, 오류: {e}"); return 0

def adjust_quantity(quantity, step_size_str, precision, min_qty_str):
    """수량을 stepSize에 맞춰 내림 처리하고, 최소 수량 확인 후 포맷팅된 float 반환"""
    try:
        # 모든 입력을 Decimal로 변환하여 정밀도 유지
        step_size = Decimal(str(step_size_str))
        min_qty = Decimal(str(min_qty_str))
        qty = Decimal(str(quantity))

        if qty <= 0: return 0.0 # 0 또는 음수 수량은 0.0 반환

        # step_size 단위로 내림 처리
        adjusted_qty = (qty // step_size) * step_size

        # 최소 주문 수량 확인 (조정된 수량이 최소값보다 작으면 최소값 사용)
        if adjusted_qty < min_qty:
            # 최소 수량이 step_size의 배수가 아닐 수 있으므로, 최소 수량 자체를 사용
            adjusted_qty = min_qty
            logging.warning(f"조정된 수량({adjusted_qty})이 최소 주문 수량({min_qty})보다 작아 최소 주문 수량으로 설정합니다.")

        # 최종 수량을 정밀도에 맞춰 양자화 (소수점 이하 버림 효과)
        quantized_qty = adjusted_qty.quantize(Decimal('1e-' + str(precision)), rounding=ROUND_DOWN)

        # 최종적으로 float 형태로 반환
        return float(quantized_qty)

    except Exception as e:
        logging.error(f"수량 조정 오류: qty={quantity}, step={step_size_str}, prec={precision}, min={min_qty_str}, error={e}", exc_info=True)
        return None # 오류 발생 시 None 반환
    
def format_price(price, tick_size_str):
    """가격을 tickSize에 맞춰 포맷팅"""
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
    """주어진 스텝 인덱스에 대한 분할 횟수 계산 (나머지를 뒤쪽 그룹에 배분)"""
    if num_groups <= 0: return 1 # DIVIDE 값이 0 이하인 경우 오류 방지

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
    # 결과가 num_groups를 초과하지 않도록 보장 (이론상 발생 안 함)
    return min(num_divisions, num_groups)


# --- 바이낸스 API 호출 함수 ---
async def check_futures_connection(client: AsyncClient):
    try: await client.futures_ping(); await client.futures_time(); logging.info("선물 서버 연결 성공."); return True
    except Exception as e: logging.error(f"선물 서버 연결 실패: {e}"); return False

async def get_futures_balance(client: AsyncClient, asset, gui):
    """선물 잔고 조회 및 GUI 업데이트"""
    current_balance = 0.0
    current_balance_str = "조회 실패"
    try:
        balances = await client.futures_account_balance()
        balance_found = False
        for balance in balances:
            if balance['asset'] == asset:
                balance_val = balance['balance']; logging.info(f"{asset} 선물 잔고: {balance_val}"); current_balance = float(balance_val); current_balance_str = str(balance_val); balance_found = True; break
        if not balance_found: logging.warning(f"{asset} 자산을 찾을 수 없습니다."); current_balance = 0.0; current_balance_str = "찾을 수 없음"
    except Exception as e:
        logging.error(f"선물 잔고 확인 실패: {e}"); current_balance = 0.0
    finally:
        if gui: gui.update_balance(current_balance_str)
        return current_balance, current_balance_str

async def check_position_mode(client: AsyncClient, gui): # gui 파라미터 추가
    """포지션 모드를 확인하고, 단방향(One-way) 모드일 경우 헤지(Hedge) 모드로 자동 변경을 시도합니다."""
    try:
        position_mode = await client.futures_get_position_mode()
        is_hedge_mode = position_mode.get('dualSidePosition', False)
        
        if is_hedge_mode:
            logging.info("현재 포지션 모드: 헤지 모드")
            return True
        else:
            logging.warning("현재 포지션 모드: 단방향 모드. 헤지 모드로 변경을 시도합니다...")
            if gui: gui.update_status("헤지 모드로 변경 중...")
            
            try:
                # dualSidePosition=True 가 헤지 모드를 의미합니다.
                await client.futures_change_position_mode(dualSidePosition=True)
                logging.info("포지션 모드를 성공적으로 헤지 모드로 변경했습니다.")
                if gui: gui.update_status("헤지 모드 변경 완료.")
                return True
            except Exception as change_e:
                # 이미 헤지 모드인 경우의 오류는 무시할 필요가 없으므로 모든 오류를 로깅합니다.
                logging.error(f"헤지 모드 변경 실패: {change_e}")
                if gui: gui.update_status(f"헤지 모드 변경 실패!")
                return False
                
    except Exception as e:
        logging.error(f"포지션 모드 확인/변경 중 오류: {e}")
        if gui: gui.update_status("포지션 모드 확인 실패!")
        return False

async def check_all_open_positions(client: AsyncClient):
    try:
        all_positions = await client.futures_position_information(); open_positions = [p for p in all_positions if float(p.get('positionAmt', 0)) != 0]
        if open_positions:
            logging.warning(f"경고: {len(open_positions)}개 오픈 포지션 발견."); [logging.warning(f"  - {p['symbol']}, {p['positionSide']}, {p['positionAmt']}") for p in open_positions]; return True
        else: logging.info("현재 오픈된 선물 포지션 없음."); return False
    except Exception as e: logging.error(f"전체 포지션 정보 확인 실패: {e}"); return True

async def check_and_cancel_pending_orders(client: AsyncClient):
    try:
        open_orders = await client.futures_get_open_orders()
        if not open_orders: logging.info("현재 미체결 주문 없음."); return True
        logging.warning(f"경고: {len(open_orders)}개 미체결 주문 발견. 취소 시도..."); cancelled_count = 0; failed_count = 0
        cancel_tasks = [client.futures_cancel_order(symbol=order['symbol'], orderId=order['orderId']) for order in open_orders]
        results = await asyncio.gather(*cancel_tasks, return_exceptions=True)
        for i, result in enumerate(results):
            order = open_orders[i]
            if isinstance(result, Exception): logging.error(f"  - 주문 취소 실패: {order.get('symbol', 'N/A')}, ID={order.get('orderId', 'N/A')}, 오류: {result}"); failed_count += 1
            else: logging.info(f"  - 주문 취소 성공: {order['symbol']}, ID={order['orderId']}"); cancelled_count += 1
        if failed_count > 0: logging.error(f"{failed_count}개 주문 취소 실패."); return False
        else: logging.info(f"{cancelled_count}개 주문 성공적으로 취소."); return True
    except Exception as e: logging.error(f"미체결 주문 처리 중 오류: {e}"); return False

async def set_leverage(client: AsyncClient, symbol, leverage, gui):
    """마진 타입을 '격리'로 설정한 후, 레버리지를 설정하고 GUI를 업데이트합니다."""
    leverage_set = False
    leverage_str = "설정 실패"
    
    try:
        # <<< 1. 현재 마진 타입 확인 후 필요시에만 변경 >>>
        logging.info(f"{symbol} 현재 마진 타입 확인 중...")
        positions = await client.futures_position_information(symbol=symbol)
        
        # 현재 마진 타입 확인 (LONG 또는 SHORT 포지션 정보에서)
        current_margin_type = None
        for pos in positions:
            if pos.get('symbol') == symbol:
                current_margin_type = pos.get('marginType', '').upper()
                break
        
        if current_margin_type == 'ISOLATED':
            logging.info(f"{symbol} 이미 격리(ISOLATED) 마진 모드입니다. 변경 불필요.")
        elif current_margin_type == 'CROSS':
            logging.info(f"{symbol} 현재 교차(CROSS) 마진 모드. 격리(ISOLATED)로 변경 시도...")
            try:
                await client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
                logging.info(f"{symbol} 마진 타입 '격리(ISOLATED)'로 변경 완료.")
            except Exception as margin_e:
                error_code = getattr(margin_e, 'code', None)
                if error_code == -4046:
                    logging.info("이미 격리 마진 모드입니다.")
                elif error_code == -4047:
                    # 오픈 주문이 있어서 변경 불가 - 에러로 처리
                    logging.error(f"{symbol} 오픈 주문이 있어 마진 타입을 변경할 수 없습니다. 기존 주문을 먼저 정리해주세요.")
                    if gui: gui.update_leverage("마진타입 변경 불가 (오픈주문)")
                    return False, "마진타입 변경 불가"
                else:
                    logging.error(f"{symbol} 마진 타입 변경 실패: {margin_e}")
                    if gui: gui.update_leverage("마진타입 설정 실패")
                    return False, "마진타입 실패"
        else:
            logging.warning(f"{symbol} 마진 타입 확인 불가 (응답: {current_margin_type}). 변경 시도...")
            try:
                await client.futures_change_margin_type(symbol=symbol, marginType='ISOLATED')
                logging.info(f"{symbol} 마진 타입 '격리(ISOLATED)'로 설정 완료.")
            except Exception as margin_e:
                error_code = getattr(margin_e, 'code', None)
                if error_code in [-4046]:
                    logging.info("이미 격리 마진 모드입니다.")
                elif error_code == -4047:
                    logging.error(f"{symbol} 오픈 주문이 있어 마진 타입을 변경할 수 없습니다.")
                    if gui: gui.update_leverage("마진타입 변경 불가 (오픈주문)")
                    return False, "마진타입 변경 불가"
                else:
                    logging.warning(f"{symbol} 마진 타입 설정 중 오류 (무시): {margin_e}")
            
    except Exception as e:
        logging.warning(f"{symbol} 마진 타입 확인/설정 중 예외 발생: {e}")
        
    try:
        # <<< 2. 레버리지 설정 >>>
        logging.info(f"{symbol} 레버리지 {leverage}배 설정 시도...");
        response = await client.futures_change_leverage(symbol=symbol, leverage=leverage)
        leverage_val = response.get('leverage', 'N/A')
        logging.info(f"{symbol} 레버리지 설정(확인) 완료: {leverage_val}x")
        leverage_set = True
        leverage_str = f"{leverage_val}x"
    except Exception as e:
        logging.error(f"{symbol} 레버리지 설정 실패: {e}")
    finally:
        if gui: gui.update_leverage(leverage_str)
        return leverage_set, leverage_str

async def get_symbol_info(client: AsyncClient, symbol, gui):
    """심볼 정보 조회 및 GUI 업데이트, 상태 반환"""
    global price_precision
    
    symbol_info = {}
    symbol_info_loaded = False
    symbol_info_str = "조회 실패"
    try:
        logging.info(f"{symbol} 거래 규칙 정보 조회 시도..."); exchange_info = await client.futures_exchange_info()
        info_found = False
        for item in exchange_info['symbols']:
            if item['symbol'] == symbol:
                logging.info(f"{symbol} 정보 찾음.")
                info_found = True
                symbol_info['quantityPrecision'] = item.get('quantityPrecision')
                symbol_info['pricePrecision'] = item.get('pricePrecision')
                price_precision = symbol_info['pricePrecision']
                for f in item['filters']:
                    if f.get('filterType') == 'LOT_SIZE':
                        symbol_info['minQty'] = f.get('minQty')
                        symbol_info['stepSize'] = f.get('stepSize')
                    elif f.get('filterType') == 'MIN_NOTIONAL':
                        symbol_info['minNotional'] = f.get('notional')
                    elif f.get('filterType') == 'PRICE_FILTER':
                        symbol_info['tickSize'] = f.get('tickSize')
                required_keys = ['quantityPrecision', 'minQty', 'stepSize', 'minNotional', 'tickSize', 'pricePrecision']
                if all(key in symbol_info and symbol_info[key] is not None for key in required_keys):
                    info_text = (f"수량(정밀도:{symbol_info['quantityPrecision']}, 최소:{symbol_info['minQty']}, 스텝:{symbol_info['stepSize']}), "
                                 f"가격(정밀도:{symbol_info['pricePrecision']}, 스텝:{symbol_info['tickSize']}), 최소금액:{symbol_info['minNotional']}USDT")
                    logging.info(f" - {info_text}")
                    symbol_info_loaded = True
                    symbol_info_str = info_text
                else: err_msg = f"{symbol} 필수 필터 정보 누락."; logging.error(err_msg); symbol_info_str = err_msg
                break
        if not info_found: err_msg = f"{symbol} 정보 없음."; logging.error(err_msg); symbol_info_str = err_msg
    except Exception as e: logging.error(f"{symbol} 정보 조회 실패: {e}")
    finally:
        if gui: gui.update_symbol_info(symbol_info_str)
        return symbol_info_loaded, symbol_info

async def calculate_effective_min_qty(client: AsyncClient, symbol, symbol_info, gui):
    """실제 최소 주문 가능 수량 계산 및 GUI 업데이트"""
    calculated_min_qty = None
    calculated_min_qty_str = "N/A"
    if not symbol_info: logging.error("최소 주문 수량 계산 불가: 심볼 정보 부족.")
    else:
        try:
            min_lot_size_qty = symbol_info.get('minQty')
            step_size = symbol_info.get('stepSize')
            min_notional_value = symbol_info.get('minNotional')
            logging.debug(f"{symbol} Mark Price 조회 시도...")
            mark_price_data = await client.futures_mark_price(symbol=symbol)
            mark_price = float(mark_price_data.get('markPrice'))
            logging.info(f"{symbol} 현재 Mark Price: {mark_price}")
            if mark_price <= 0: raise ValueError("Mark Price가 0 또는 음수")
            notional_qty = float(min_notional_value) / mark_price
            notional_qty_d = Decimal(str(notional_qty)); step_size_d = Decimal(str(step_size))
            adjusted_notional_qty_d = (notional_qty_d / step_size_d).to_integral_value(rounding=ROUND_UP) * step_size_d
            adjusted_notional_qty = float(adjusted_notional_qty_d)
            min_lot_f = float(min_lot_size_qty)
            effective_min_qty = max(min_lot_f, adjusted_notional_qty)
            decimals = count_decimal_places(step_size)
            final_min_qty_d = Decimal(str(effective_min_qty)).quantize(Decimal('1e-' + str(decimals)), rounding=ROUND_DOWN)
            if final_min_qty_d < Decimal(str(min_lot_size_qty)): final_min_qty_d = Decimal(str(min_lot_size_qty))
            calculated_min_qty = float(final_min_qty_d)
            calculated_min_qty_str = f"{final_min_qty_d:.{decimals}f}"
            logging.info(f"계산된 최종 최소 주문 수량: {calculated_min_qty}")
        except Exception as e: logging.error(f"최소 주문 수량 계산 중 오류: {e}", exc_info=True); calculated_min_qty_str = "계산오류"
        finally:
            if gui: gui.update_min_qty(calculated_min_qty_str)
            return calculated_min_qty, calculated_min_qty_str

# === 계산 함수들: config 모듈 직접 사용 ===
async def calculate_entry_quantities(client: AsyncClient, symbol, symbol_info, min_order_qty, current_balance, gui):
    entry_qty_list = []; cumul_entry_qty_list = []; success = False
    if min_order_qty is None or not symbol_info:
        logging.error("진입 수량 계산 불가: 입력 데이터 부족.")
        if gui: gui.update_entry_lists(["계산 불가"] * config.STEPS, ["계산 불가"] * config.STEPS, 1)
    else:
        try:
            step_size = symbol_info['stepSize']; qty_precision = symbol_info['quantityPrecision']
            base_quantities_adj = [0.0] * config.STEPS; q_raw = [0.0] * config.STEPS; cumulative_sum_raw = Decimal('0')
            q1_d = Decimal(str(min_order_qty)); q_raw[1] = float(q1_d)
            q1_adj = adjust_quantity(q_raw[1], step_size, qty_precision, symbol_info['minQty']); base_quantities_adj[1] = q1_adj
            if q1_adj is None: raise ValueError("Q(1) 조정 실패")
            if config.ENTRY_START <= 0: raise ValueError("ENTRY_START는 0보다 커야 합니다.")
            q0_d = q1_d / Decimal(str(config.ENTRY_START)); q_raw[0] = float(q0_d)
            q0_adj = adjust_quantity(q_raw[0], step_size, qty_precision, symbol_info['minQty']); base_quantities_adj[0] = q0_adj
            if q0_adj is None: raise ValueError("Q(0) 조정 실패")
            cumulative_sum_raw = Decimal(str(q0_adj)) + Decimal(str(q1_adj))
            if config.STEPS > 2:
                ratio_steps = config.STEPS - 2
                for i in range(2, config.STEPS):
                    k = i - 2; x = Decimal('1.0') if ratio_steps <= 1 else Decimal(str(k)) / Decimal(str(ratio_steps - 1))
                    ratio_multiplier_d = Decimal(str(config.ENTRY_START)) + (Decimal(str(config.ENTRY_END)) - Decimal(str(config.ENTRY_START))) * (x ** Decimal(str(config.ENTRY_EXPONENT)))
                    qi_d = cumulative_sum_raw * ratio_multiplier_d; q_raw[i] = float(qi_d)
                    qi_adj = adjust_quantity(q_raw[i], step_size, qty_precision, symbol_info['minQty'])
                    if qi_adj is None: raise ValueError(f"Q({i}) 조정 실패")
                    base_quantities_adj[i] = qi_adj; cumulative_sum_raw += Decimal(str(qi_adj))
            sum_q_adj = sum(base_quantities_adj)
            if sum_q_adj <= 0: raise ValueError("기본 수량 합계가 0 이하")
            total_margin = (current_balance * config.BALANCE_USAGE_PERCENTAGE) * config.TARGET_LEVERAGE
            logging.info(f"자금 사용률({config.BALANCE_USAGE_PERCENTAGE * 100}%) 적용. 실제 사용될 잔고: {current_balance * config.BALANCE_USAGE_PERCENTAGE:.4f} {config.BALANCE_ASSET}")
            mark_price_data = await client.futures_mark_price(symbol=symbol); mark_price = float(mark_price_data.get('markPrice'))
            if mark_price <= 0: raise ValueError("Mark Price 오류")
            target_total_quantity = total_margin / mark_price; scaling_factor = target_total_quantity / sum_q_adj
            final_quantities = []; cumulative_sum_final = 0.0; cumulative_quantities_final = []
            for i in range(config.STEPS):
                q_final_unadjusted = base_quantities_adj[i] * scaling_factor
                q_final_adjusted = adjust_quantity(q_final_unadjusted, step_size, qty_precision, symbol_info['minQty'])
                if q_final_adjusted is None: raise ValueError(f"최종 Q({i}) 조정 실패")
                final_quantities.append(q_final_adjusted); cumulative_sum_final += q_final_adjusted
                cumulative_quantities_final.append(round(cumulative_sum_final, qty_precision))
            entry_qty_list = final_quantities; cumul_entry_qty_list = cumulative_quantities_final
            logging.info(f"최종 스케일링된 진입 수량 목록: {entry_qty_list}")
            logging.info(f"최종 누적 진입 수량 목록: {cumul_entry_qty_list}")
            success = True
        except Exception as e: logging.error(f"진입 수량 계산 중 오류 발생: {e}", exc_info=True); entry_qty_list = []; cumul_entry_qty_list = []
        finally:
            if gui:
                precision = symbol_info.get('quantityPrecision', 1) if symbol_info else 1
                err_msg = ["계산 오류"] * config.STEPS
                gui.update_entry_lists(entry_qty_list if success else err_msg, cumul_entry_qty_list if success else err_msg, precision)
            return success, entry_qty_list, cumul_entry_qty_list

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
            # per_step_list = [0,4,5,6,7,8,9,10,11,12,13,14] # 테스트용 코드 제거 또는 주석 처리
            # logging.info(f"헷지수량 테스트수량으로 교체: {per_step_list}")
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

# --- Algo Order API 호출 함수 (2025-12-09 이후 TRAILING_STOP_MARKET 지원) ---
async def place_algo_order(client: AsyncClient, symbol: str, side: str, position_side: str, 
                          quantity: str, order_type: str, activation_price: str = None, 
                          callback_rate: str = None, stop_price: str = None,
                          working_type: str = "MARK_PRICE", reduce_only: bool = False):
    """
    Binance Futures Algo Order API를 직접 호출합니다.
    (POST 요청 시 data 파라미터 사용, activatePrice 파라미터명 수정)
    """
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v1/algo/order"  # 🔴 엔드포인트 수정 (algoOrder -> algo/order)
    
    api_key = client.API_KEY
    api_secret = client.API_SECRET
    
    timestamp = int(time.time() * 1000)
    
    # 기본 파라미터
    params = {
        "algoType": "CONDITIONAL",
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "quantity": quantity,
        "type": order_type,
        "workingType": working_type,
        "timestamp": str(timestamp),
    }

    # reduceOnly 설정 (TSM은 API 에러(-1106) 방지를 위해 제외)
    if reduce_only and order_type != 'TRAILING_STOP_MARKET':
        params["reduceOnly"] = "true"
    
    # 주문 유형별 추가 파라미터
    if order_type == "TRAILING_STOP_MARKET":
        if callback_rate:
            params["callbackRate"] = str(callback_rate)
        if activation_price:
            # [🔴 핵심 수정] activationPrice -> activatePrice 로 변경
            # Algo Order API는 'activatePrice'를 사용합니다.
            params["activatePrice"] = str(activation_price)
            
    elif order_type in ["STOP_MARKET", "TAKE_PROFIT_MARKET", "STOP", "TAKE_PROFIT"]:
        if stop_price:
            params["triggerPrice"] = str(stop_price)
    
    # [디버그 로그] 실제 전송되는 파라미터 확인
    logging.info(f"======== [Algo Order Params Check (Fixed Key)] ========")
    logging.info(f"Type: {order_type}, Symbol: {symbol}, Qty: {quantity}")
    logging.info(f"ActivatePrice Sent (Key: activatePrice): {params.get('activatePrice')}") # 키 이름 확인
    logging.info(f"CallbackRate Sent: {params.get('callbackRate')}")
    logging.info(f"Full Params: {params}")
    logging.info(f"==========================================")

    # 서명 생성
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    
    headers = {
        "X-MBX-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{base_url}{endpoint}",
                data=params, 
                headers=headers
            ) as response:
                response_text = await response.text()
                if response.status == 200:
                    import json
                    order_data = json.loads(response_text)
                    
                    # API 응답에서 실제로 설정된 activatePrice 확인
                    returned_activate_price = order_data.get('activatePrice', 'N/A')
                    logging.info(f"Algo Order API 성공. 설정된 ActivatePrice: {returned_activate_price}")
                    
                    return order_data, True, None
                else:
                    import json
                    try:
                        error_json = json.loads(response_text)
                        error_code = error_json.get('code')
                        error_msg = error_json.get('msg')
                        logging.error(f"Algo Order API 실패: code={error_code}, msg={error_msg}")
                        return None, False, error_code
                    except:
                        logging.error(f"Algo Order API 실패: status={response.status}, response={response_text}")
                        return None, False, response.status
    except Exception as e:
        logging.error(f"Algo Order API 예외 발생: {e}")
        return None, False, str(e)

async def cancel_algo_order(client: AsyncClient, symbol: str, algo_id: str):
    """
    Binance Futures Algo Order 취소 API 호출
    DELETE /fapi/v1/algo/order
    """
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v1/algo/order"  # 🔴 엔드포인트 수정 (algoOrder -> algo/order)
    
    api_key = client.API_KEY
    api_secret = client.API_SECRET
    
    timestamp = int(time.time() * 1000)
    params = {
        "symbol": symbol,
        "algoId": algo_id,
        "timestamp": str(timestamp),
    }
    
    # 서명 생성
    query_string = urllib.parse.urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    params["signature"] = signature
    
    headers = {
        "X-MBX-APIKEY": api_key,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{base_url}{endpoint}",
                params=params,
                headers=headers
            ) as response:
                response_text = await response.text()
                if response.status == 200:
                    import json
                    result = json.loads(response_text)
                    logging.info(f"Algo Order 취소 성공: algoId={algo_id}, 응답={result}")
                    return result, True, None
                else:
                    import json
                    try:
                        error_json = json.loads(response_text)
                        error_code = error_json.get('code')
                        error_msg = error_json.get('msg')
                        logging.error(f"Algo Order 취소 실패: algoId={algo_id}, code={error_code}, msg={error_msg}")
                        return None, False, error_code
                    except:
                        logging.error(f"Algo Order 취소 실패: algoId={algo_id}, status={response.status}, response={response_text}")
                        return None, False, response.status
    except Exception as e:
        logging.error(f"Algo Order 취소 예외 발생: algoId={algo_id}, error={e}")
        return None, False, str(e)

async def place_futures_order(client: AsyncClient, symbol_info, symbol, side, position_side, quantity,
                              order_type=FUTURE_ORDER_TYPE_MARKET, price=None, stop_price=None,
                              activation_price=None, callback_rate=None,
                              reduce_only=False,
                              open_orders_state_ref: dict = None,
                              order_type_mapping_ref: dict = None,
                              mapping_key: str = None, # 주문의 목적/유형을 나타내는 키 (예: "EntryAttempt-0-timestamp")
                              client_order_id: str = None): # 사용자가 지정하는 고유 ID
    if not symbol_info:
        logging.error("주문 불가: 심볼 정보 없음")
        return None, False, None # 데이터, 성공여부, API오류코드

    min_order_qty_str = symbol_info.get('minQty')
    step_size = symbol_info.get('stepSize')
    qty_precision = symbol_info.get('quantityPrecision')
    tick_size = symbol_info.get('tickSize')

    if None in [min_order_qty_str, step_size, qty_precision, tick_size]:
        logging.error("주문 불가: 심볼 정보 필터 부족 (minQty, stepSize, quantityPrecision, or tickSize is None)")
        return None, False, None

    order_success = False
    error_code_from_api = None
    order_data_from_api = None

    max_retries = config.ORDER_RETRY_ATTEMPTS
    base_retry_delay_seconds = config.ORDER_RETRY_DELAY_SECONDS

    # 수량 조정
    final_adjusted_qty = adjust_quantity(float(quantity), step_size, qty_precision, min_order_qty_str)
    if final_adjusted_qty is None or final_adjusted_qty <= 0:
        logging.warning(f"조정된 주문 수량이 0 이하({final_adjusted_qty}) 또는 오류. 주문 안함.")
        return None, False, None
    formatted_qty_str = f"{final_adjusted_qty:.{qty_precision}f}"

    # API 요청 파라미터 설정
    params = {
        "symbol": symbol,
        "side": side,
        "positionSide": position_side,
        "type": order_type,
        "quantity": formatted_qty_str
    }

    # Client Order ID 설정 (제공된 경우)
    if client_order_id:
        params["newClientOrderId"] = client_order_id
        logging.info(f"주문 생성 시 ClientOrderId 사용: {client_order_id}")

    # 주문 유형별 추가 파라미터 설정
    if order_type == FUTURE_ORDER_TYPE_LIMIT:
        if price is None: logging.error(f"{order_type} 주문에 price 필요"); return None, False, None
        formatted_price = format_price(price, tick_size)
        if formatted_price is None: logging.error(f"가격 포맷팅 실패 ({price})"); return None, False, None
        params["price"] = formatted_price
        params["timeInForce"] = TIME_IN_FORCE_GTC
    elif order_type == FUTURE_ORDER_TYPE_STOP_MARKET:
        if stop_price is None: logging.error(f"{order_type} 주문에 stopPrice 필요"); return None, False, None
        formatted_stop_price = format_price(stop_price, tick_size)
        if formatted_stop_price is None: logging.error(f"Stop Price 포맷팅 실패 ({stop_price})"); return None, False, None
        params["stopPrice"] = formatted_stop_price
        params["workingType"] = "MARK_PRICE"
    elif order_type == FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET:
        if stop_price is None: logging.error(f"{order_type} 주문에 stopPrice 필요"); return None, False, None
        formatted_stop_price = format_price(stop_price, tick_size)
        if formatted_stop_price is None: logging.error(f"Stop Price 포맷팅 실패 ({stop_price})"); return None, False, None
        params["stopPrice"] = formatted_stop_price
        params["workingType"] = "MARK_PRICE"
    elif order_type == FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET:
        if activation_price is not None:
            params["activationPrice"] = format_price(activation_price, tick_size)
        if callback_rate is None: logging.error(f"{order_type} 주문에 callbackRate 필요"); return None, False, None
        params["callbackRate"] = str(callback_rate)
        params["workingType"] = "MARK_PRICE"
        logging.info(f"TRAILING_STOP_MARKET 파라미터 설정 완료: activationPrice={params.get('activationPrice')}, callbackRate={params.get('callbackRate')}")

    # reduceOnly 파라미터는 TRAILING_STOP_MARKET이 아닌 경우에만 조건부로 추가
    if reduce_only:
        # 일반적으로 이들은 reduceOnly가 기본 동작이거나 파라미터가 불필요할 수 있습니다.
        if order_type not in [FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET, 
                              FUTURE_ORDER_TYPE_STOP_MARKET, 
                              FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET]:
            params["reduceOnly"] = "true"
        else:
            logging.info(f"{order_type} 주문 유형에는 reduceOnly 파라미터를 명시적으로 보내지 않습니다 (오류 -1106 방지).")

    # 주문 실행 (재시도 로직 포함)
    original_order_type = order_type  # 원본 주문 유형 저장
    
    # 조건부 주문 유형 목록 (2025-12-09부터 Algo Order API 필요)
    conditional_order_types = [
        FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET,
        FUTURE_ORDER_TYPE_STOP_MARKET,
        FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
        'STOP',
        'TAKE_PROFIT'
    ]
    use_algo_api = order_type in conditional_order_types
    
    for attempt in range(max_retries):
        try:
            logging.info(f"주문 시도 (시도 {attempt + 1}/{max_retries}): {params}")
            
            if use_algo_api:
                # Algo Order API 사용 (조건부 주문)
                logging.info(f"Algo Order API로 {order_type} 주문 시도...")
                
                # Algo Order API용 파라미터 준비
                algo_activation_price = params.get("activationPrice")
                algo_callback_rate = params.get("callbackRate")
                algo_stop_price = params.get("stopPrice")
                
                # [수정] reduce_only 파라미터 전달 추가
                should_reduce_only = False
                if reduce_only: # place_futures_order의 인자로 받은 reduce_only 값
                    should_reduce_only = True
                elif params.get("reduceOnly") == "true":
                    should_reduce_only = True
                
                order_data_from_api, order_success, error_code_from_api = await place_algo_order(
                    client=client,
                    symbol=params["symbol"],
                    side=params["side"],
                    position_side=params["positionSide"],
                    quantity=params["quantity"],
                    order_type=order_type,
                    activation_price=algo_activation_price,
                    callback_rate=algo_callback_rate,
                    stop_price=algo_stop_price,
                    working_type=params.get("workingType", "MARK_PRICE"),
                    reduce_only=should_reduce_only # <--- 여기 추가됨
                )
                
                if order_success:
                    logging.info(f"Algo Order API 주문 성공: {order_data_from_api}")
                    
                    # === API 응답 성공 후 즉시 로컬 상태 업데이트 ===
                    if order_data_from_api and open_orders_state_ref is not None and \
                       order_type_mapping_ref is not None and mapping_key:
                        
                        # Algo Order API는 'algoId' 또는 'orderId'를 반환
                        order_id_from_api = str(order_data_from_api.get('algoId', order_data_from_api.get('orderId', '')))
                        client_oid_from_api = order_data_from_api.get('clientAlgoId', order_data_from_api.get('clientOrderId', ''))

                        order_state_to_store = order_data_from_api.copy()
                        order_state_to_store['creationTime'] = order_data_from_api.get('updateTime', time.time() * 1000) / 1000.0
                        order_state_to_store['isAlgoOrder'] = True  # Algo 주문 표시
                        
                        if order_id_from_api:
                            open_orders_state_ref[order_id_from_api] = order_state_to_store
                            order_type_mapping_ref[order_id_from_api] = mapping_key
                            
                            # clientAlgoId도 매핑에 저장 (TSM 트리거 시 새 orderId로 이벤트가 오지만 clientOrderId는 동일)
                            if client_oid_from_api:
                                order_type_mapping_ref[client_oid_from_api] = mapping_key
                                logging.info(f"Algo 주문 로컬 상태 업데이트 완료: AlgoID={order_id_from_api}, ClientAlgoID={client_oid_from_api}, 구분={mapping_key}")
                            else:
                                logging.info(f"Algo 주문 로컬 상태 업데이트 완료: AlgoID={order_id_from_api}, 구분={mapping_key}")
                            
                            # 🟢 Algo 주문 보호 콜백 호출
                            if algo_order_protection_callback:
                                try:
                                    algo_order_protection_callback(order_id_from_api)
                                except Exception as cb_e:
                                    logging.warning(f"Algo 주문 보호 콜백 호출 중 오류: {cb_e}")
                    break  # 성공 시 루프 탈출
                else:
                    logging.error(f"Algo Order API 실패: error_code={error_code_from_api}")
                    if attempt >= max_retries - 1:
                        break
                    await asyncio.sleep(base_retry_delay_seconds)
                    continue
            else:
                # 일반 주문 API 사용 (MARKET, LIMIT 등)
                order = await client.futures_create_order(**params)
                
                logging.info(f"주문 성공 (API 응답): {order}")
                order_data_from_api = order
                order_success = True
                error_code_from_api = None

                # === API 응답 성공 후 즉시 로컬 상태 업데이트 ===
                if order_data_from_api and open_orders_state_ref is not None and \
                   order_type_mapping_ref is not None and mapping_key:
                    
                    order_id_from_api = str(order_data_from_api.get('orderId', ''))
                    client_oid_from_api = order_data_from_api.get('clientOrderId', '')

                    order_state_to_store = order_data_from_api.copy()
                    order_state_to_store['creationTime'] = order_data_from_api.get('updateTime', time.time() * 1000) / 1000.0
                    
                    if order_id_from_api:
                        open_orders_state_ref[order_id_from_api] = order_state_to_store
                        order_type_mapping_ref[order_id_from_api] = mapping_key
                        
                        logging.info(f"주문 즉시 로컬 상태 업데이트 완료: OrderID={order_id_from_api}, ClientOID={client_oid_from_api}, 구분={mapping_key}")
                break  # 성공 시 루프 탈출
            
        except Exception as e:
            logging.error(f"주문 시도 {attempt + 1}/{max_retries} 실패: {e}")
            error_code_from_api = getattr(e, 'code', None)
            
            if error_code_from_api == -1008 and attempt < max_retries - 1:  # 서버 과부하 시 재시도
                current_retry_delay = base_retry_delay_seconds * (2 ** attempt)
                logging.info(f"서버 과부하 (코드: -1008). {current_retry_delay}초 후 재시도합니다...")
                await asyncio.sleep(current_retry_delay)
            else:  # 재시도 불가능한 오류 또는 마지막 시도
                order_success = False
                break

    return order_data_from_api, order_success, error_code_from_api


async def place_divided_orders(client: AsyncClient, gui, symbol_info, state,
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
            if order_type == FUTURE_ORDER_TYPE_MARKET:
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
                    order_data_market_sub, success_market_sub, error_code_market_sub = await place_futures_order(client, symbol_info, symbol, side, position_side, qty_to_place_float, FUTURE_ORDER_TYPE_MARKET, False, open_orders, order_mapping, sub_order_mapping_key)
                    if success_market_sub and order_data_market_sub:
                        placed_orders_list.append(order_data_market_sub)
                        try: accumulated_qty_placed_dec += Decimal(str(order_data_market_sub.get('origQty', '0')))
                        except: pass 
                        if i < num_total_divisions_for_step - 1: await asyncio.sleep(0.2) 
                    else: all_market_subs_successful = False; logging.error(f"  - [{order_purpose} 스텝 {target_step_index} 분할 {i+1}] MARKET 주문 실패. ErrorCode: {error_code_market_sub}")
                final_success_market_divided = all_market_subs_successful and bool(placed_orders_list)
                return final_success_market_divided, placed_orders_list, None 
            elif order_type == FUTURE_ORDER_TYPE_LIMIT: # 조건부 시장가 설정 시 이 함수는 직접 호출되지 않음. place_triggered_market_order가 호출됨.
                logging.error(f"[{order_purpose} 스텝 {target_step_index}] LIMIT 주문은 place_divided_orders에서 직접 처리하지 않습니다. 조건부 시장가 설정을 확인하세요.")
                return False, [], None
            else: logging.error(f"[{order_purpose} 스텝 {target_step_index}] 지원되지 않는 주문 유형: {order_type} (General/SignalEntry 목적)"); return False, [], None
        elif order_purpose == "SysClosePos" and order_type == FUTURE_ORDER_TYPE_MARKET:
            order_mapping_key_sys_close = f'{base_mapping_key}-0'
            order_data_sys_close, success_sys_close, _ = await place_futures_order(client, symbol_info, symbol, side, position_side, total_quantity, FUTURE_ORDER_TYPE_MARKET, True, open_orders, order_mapping, order_mapping_key_sys_close)
            if success_sys_close and order_data_sys_close: placed_orders_list.append(order_data_sys_close)
            return success_sys_close, placed_orders_list 
        elif order_purpose in ['Maginot', 'Maginot Hedge']: # Maginot Hedge는 시장가로 변경
            order_mapping_key_maginot = f'{base_mapping_key}-0'
            actual_order_type_maginot = FUTURE_ORDER_TYPE_LIMIT if order_purpose == 'Maginot' else FUTURE_ORDER_TYPE_MARKET
            reduce_only_maginot = False # Maginot, Maginot Hedge 모두 False
            order_data_maginot, success_maginot, _ = await place_futures_order(client, symbol_info, symbol, side, position_side, total_quantity, actual_order_type_maginot, price, None, reduce_only_maginot, open_orders, order_mapping, order_mapping_key_maginot) # stop_price=None 추가
            if success_maginot and order_data_maginot: placed_orders_list.append(order_data_maginot)
            return success_maginot, placed_orders_list 
        elif order_purpose == 'Exit': # Exit 주문은 TRAILING_STOP_MARKET 또는 LIMIT (분할 시)
             logging.error("place_divided_orders: Exit 주문은 이 함수에서 직접 분할 처리하지 않습니다. place_single_exit_sub_order 또는 place_exit_hedge_order를 사용하세요.")
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

async def place_maginot_step_hedge_order(client: AsyncClient, gui, symbol_info: dict, state: dict, step_to_hedge: int, total_hedge_qty_for_step: float, main_position_side: str):
    """ Maginot 주문 체결로 진입한 스텝에 대해, 해당 스텝의 전체 헤지 수량을 단일 시장가 주문으로 실행합니다. """
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state'); order_type_mapping_ref = state.get('order_type_mapping')
    if not symbol_info or total_hedge_qty_for_step <= 0: logging.error(f"[MaginotStepHedge] 스텝 {step_to_hedge}: 헤지 불가 - 심볼 정보 없거나 수량 ({total_hedge_qty_for_step}) <= 0."); return False, None
    hedge_side = None; hedge_position_side = None
    if main_position_side == 'LONG': hedge_side = SIDE_SELL; hedge_position_side = 'SHORT'
    elif main_position_side == 'SHORT': hedge_side = SIDE_BUY; hedge_position_side = 'LONG'
    else: logging.error(f"[MaginotStepHedge] 스텝 {step_to_hedge}: 알 수 없는 주 포지션 사이드 '{main_position_side}'. 헤지 주문 불가."); return False, None
    mapping_key = f"MaginotHedge-{step_to_hedge}-{int(time.time())}" # Maginot Hedge 구분자 변경
    logging.info(f"[MaginotStepHedge] 스텝 {step_to_hedge} 전체 헤지 주문: Side: {hedge_side}, PosSide: {hedge_position_side}, Qty: {total_hedge_qty_for_step}, Key: {mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, total_hedge_qty_for_step, FUTURE_ORDER_TYPE_MARKET, None, None, False, open_orders_state_ref, order_type_mapping_ref, mapping_key)
    if success and order_data: logging.info(f"  -> [MaginotStepHedge] 스텝 {step_to_hedge} 헤지 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [MaginotStepHedge] 스텝 {step_to_hedge} 헤지 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_single_exit_hedge_sub_order(client: AsyncClient, gui, symbol_info: dict, state: dict, filled_exit_step_index: int, filled_exit_sub_order_index: int, hedge_quantity: float, original_main_position_side: str ):
    """ 체결된 Exit 분할 주문에 대해 단일 시장가 헤지 주문을 실행합니다. (STOP_MARKET -> MARKET) """
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state'); order_type_mapping_ref = state.get('order_type_mapping')
    if not symbol_info or hedge_quantity <= 0: logging.error(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index}: 심볼 정보 없거나 헤지 수량 ({hedge_quantity}) <= 0. 주문 안함."); return False, None
    hedge_side = None; hedge_position_side = None
    if original_main_position_side == 'LONG': hedge_side = SIDE_BUY; hedge_position_side = 'SHORT' # Exit(SELL) -> Hedge(BUY) for SHORT
    elif original_main_position_side == 'SHORT': hedge_side = SIDE_SELL; hedge_position_side = 'LONG' # Exit(BUY) -> Hedge(SELL) for LONG
    else: logging.error(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index}: 알 수 없는 원본 포지션 사이드 '{original_main_position_side}'. 헤지 주문 불가."); return False, None
    mapping_key = f"ExitHedgeSub-{filled_exit_step_index}-{filled_exit_sub_order_index}-{int(time.time())}"
    logging.info(f"[ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 대응: 시장가 헤지 주문. Side: {hedge_side}, PosSide: {hedge_position_side}, Qty: {hedge_quantity}, Key: {mapping_key}")
    # Exit Hedge 주문은 항상 새로운 포지션을 열거나 기존 반대 포지션을 늘리는 것이므로 reduceOnly=False
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, hedge_quantity, FUTURE_ORDER_TYPE_MARKET, None, None, False, open_orders_state_ref, order_type_mapping_ref, mapping_key)
    if success and order_data: logging.info(f"  -> [ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 헤지 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [ExitHedgeSub] 스텝 {filled_exit_step_index} 분할 {filled_exit_sub_order_index} 헤지 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_market_hedge_for_general_sub_order(client: AsyncClient, gui, symbol_info: dict, state: dict, filled_general_step_index: int, filled_general_sub_order_index: int, num_total_divisions_for_general_step: int, total_hedge_qty_for_completed_step: float, general_order_main_side: str ): # general_order_position_side -> general_order_main_side
    """ 체결된 General 분할 주문에 대응하여 단일 MARKET 헤지 주문을 실행합니다. """
    if total_hedge_qty_for_completed_step <= 0 or num_total_divisions_for_general_step <= 0: logging.warning(f"[SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index}: 헤지 수량({total_hedge_qty_for_completed_step}) 또는 분할 수({num_total_divisions_for_general_step})가 0 이하. 헤지 주문 건너뜁니다."); return False, None
    hedge_qty_for_this_sub = Decimal(str(total_hedge_qty_for_completed_step)) / Decimal(str(num_total_divisions_for_general_step))
    hedge_qty_for_this_sub_float = float(hedge_qty_for_this_sub); qty_precision_hedge = symbol_info.get('quantityPrecision', 2)
    
    # General 주문이 LONG(BUY)이면 Hedge는 SHORT(SELL), General 주문이 SHORT(SELL)이면 Hedge는 LONG(BUY)
    hedge_side = SIDE_SELL if general_order_main_side == 'LONG' else SIDE_BUY
    hedge_position_side = 'SHORT' if general_order_main_side == 'LONG' else 'LONG'

    logging.info(f"[SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 대응: MARKET {hedge_side} 헤지 주문 시작. 목표 수량: {hedge_qty_for_this_sub_float:.{qty_precision_hedge}f}, PositionSide: {hedge_position_side}, reduceOnly=False")
    symbol = state.get('symbol'); open_orders_state_ref = state.get('open_orders_state', {}); order_type_mapping_ref = state.get('order_type_mapping', {})
    reduce_only_flag = False; hedge_mapping_key = f"SubHedge-{filled_general_step_index}-{filled_general_sub_order_index}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(client, symbol_info, symbol, hedge_side, hedge_position_side, hedge_qty_for_this_sub_float, FUTURE_ORDER_TYPE_MARKET, None, None, reduce_only_flag, open_orders_state_ref, order_type_mapping_ref, hedge_mapping_key)
    if success and order_data: logging.info(f"  -> [SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 헤지 주문 요청 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [SubHedge] 스텝 {filled_general_step_index} 분할 {filled_general_sub_order_index} 헤지 주문 요청 실패. ErrorCode: {error_code}")
    return success, order_data

def calculate_general_entry_triggers(base_entry_price: float, total_quantity: float, num_divisions: int, side: str, symbol_info: dict): # for_sell_trigger_calc_identically 제거
    """ 조건부 시장가 주문을 위한 트리거 가격 및 분할 수량 목록을 계산합니다. """
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
        
        # BUY 주문: 현재가 <= 기준가 - 오프셋 일 때 트리거
        # SELL 주문: 현재가 >= 기준가 + 오프셋 일 때 트리거 (프롬프트의 "해당가격 이하"와는 다름, 일반적인 조건부 주문 방식)
        # 사용자의 "해당가격 이하가 되었을때 주문" 조건은 BUY에만 해당되는 것으로 해석, SELL은 반대로.
        if side == SIDE_BUY: trigger_price_dec = base_price_d - price_offset
        elif side == SIDE_SELL: trigger_price_dec = base_price_d + price_offset # SELL 주문은 가격 상승 시 트리거
        else: trigger_price_dec = base_price_d # 기본값 (오류 방지)

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

async def handle_signal(client: AsyncClient, gui, symbol_info_local: dict, state: dict): # symbol_info -> symbol_info_local
    """ 시그널 처리: 조건부 시장가 주문을 위한 트리거 정보를 계산하여 반환합니다. """
    signal_type_local = state['signal_type']; current_step_for_signal = 0 
    entry_qty_list_from_state = state['entry_quantity_list']
    attempt_key_prefix_for_entry = f"EntryAttempt-{current_step_for_signal}-{int(time.time())}" 
    logging.info(f"=== {signal_type_local} 시그널 처리 시작 (스텝 {current_step_for_signal}, 조건부 시장가 설정) ===")
    if not entry_qty_list_from_state or current_step_for_signal >= len(entry_qty_list_from_state): logging.error(f"handle_signal: 스텝 {current_step_for_signal} 진입 수량 정보 없음."); return False, 0, [], 0, None
    total_entry_qty_for_step0 = entry_qty_list_from_state[current_step_for_signal]
    if total_entry_qty_for_step0 <= 0: logging.error(f"handle_signal: 스텝 {current_step_for_signal} 진입 수량이 0 이하입니다."); return False, 0, [], 0, None
    base_entry_price = 0.0
    try:
        mark_price_data = await client.futures_mark_price(symbol=config.SYMBOL)
        base_entry_price = float(mark_price_data.get('markPrice'))
        if base_entry_price <= 0: raise ValueError("유효하지 않은 Mark Price")
    except Exception as e: logging.error(f"handle_signal: 기준 가격(Mark Price) 조회 실패: {e}"); return False, 0, [], 0, None
    num_divisions = calculate_num_divisions(current_step_for_signal, config.STEPS, config.DIVIDE)
    if num_divisions <= 0: num_divisions = 1
    entry_side = SIDE_BUY if signal_type_local == 'LONG' else SIDE_SELL
    triggers = calculate_general_entry_triggers(base_entry_price, total_entry_qty_for_step0, num_divisions, entry_side, symbol_info_local) # symbol_info_local 사용
    if not triggers: logging.error(f"handle_signal: 스텝 {current_step_for_signal}에 대한 유효한 트리거를 생성할 수 없습니다."); return False, 0, [], 0, None
    actual_total_quantity_from_triggers = sum(t['quantity'] for t in triggers)
    logging.info(f"handle_signal: 스텝 {current_step_for_signal} 조건부 시장가 주문 트리거 {len(triggers)}개 생성 완료. 총 수량: {actual_total_quantity_from_triggers}")
    return True, len(triggers), triggers, actual_total_quantity_from_triggers, attempt_key_prefix_for_entry

# logic.py

async def handle_step_entry_signal(client: AsyncClient, gui, symbol_info_local: dict, state: dict, target_step: int):
    signal_type_local_step = state['signal_type']
    entry_qty_list_step = state['entry_quantity_list']
    open_orders_state_ref = state.get('open_orders_state', {}) # main.py의 전역변수 참조
    order_type_mapping_ref = state.get('order_type_mapping', {}) # main.py의 전역변수 참조

    attempt_key_prefix_step = f"EntryAttempt-{target_step}-{int(time.time())}" 
    logging.info(f"=== 시그널 기반 스텝 {target_step} 즉시 시장가 주문 실행 시작 ===")

    # 1. 이전 스텝의 Maginot 주문 등 정리 (기존 로직과 유사하게)
    # <<< 이 코드가 올바르고 안전한 버전입니다 >>>
    logging.info(f"스텝 {target_step} 진입 전, 이전 스텝의 모든 관련 주문을 취소합니다.")
    prefixes_to_clear = [
        'MainPartialExitTSM-',  # 모든 스텝의 TSM 주문을 대상으로 함
        'HedgePartialExitSM-', # 모든 스텝의 SM 주문을 대상으로 함
        f'Maginot-{target_step}-'  # 진입하려는 스텝의 Maginot 주문만 대상으로 함
    ]

    for prefix in prefixes_to_clear:
        await cancel_orders_by_prefix(client, config.SYMBOL, open_orders_state_ref, order_type_mapping_ref, prefix)
    
    if gui: gui.update_open_orders_display(list(open_orders_state_ref.values()), order_type_mapping_ref)
    # <<< 여기까지 >>>


    if not entry_qty_list_step or target_step >= len(entry_qty_list_step):
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 진입 수량 정보 없음.")
        return False, 0, [], 0, None # 실패 시 반환 형식 유지

    total_entry_qty_for_target_step = entry_qty_list_step[target_step]
    if total_entry_qty_for_target_step <= 0:
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 진입 수량이 0 이하입니다.")
        return False, 0, [], 0, None

    entry_side_step = SIDE_BUY if signal_type_local_step == 'LONG' else SIDE_SELL
    position_side_step = signal_type_local_step # 'LONG' 또는 'SHORT'

    # logic.place_general_order_market 과 유사하게 직접 시장가 주문 실행
    # place_general_order_market 함수를 재활용하거나, 여기서 직접 place_futures_order 호출
    
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
        # 이 경우, triggers 목록은 반환할 필요가 없거나, 빈 리스트 또는 단일 실행 정보로 반환할 수 있음
        # process_kline에서 pending_entry_info를 어떻게 사용하는지에 따라 조정
        # 여기서는 성공적으로 주문 "요청"이 되었음을 알리고, 실제 체결은 USER_DATA 스트림에서 처리
        return True, 1, [{'status':'placed', 'orderId':order_data.get('orderId')}], total_entry_qty_for_target_step, attempt_key_prefix_step
    else:
        logging.error(f"handle_step_entry_signal: 스텝 {target_step} 시장가 주문 실패. ErrorCode: {error_code}")
        return False, 0, [], 0, None

async def cancel_orders_by_prefix(client: AsyncClient, symbol: str, open_orders_state: dict, order_type_mapping: dict, prefix: str):
    """특정 prefix로 시작하는 미체결 주문들을 취소 (Algo Order 지원)"""
    cancelled_ids = []
    normal_orders_to_cancel = []  # 일반 주문
    algo_orders_to_cancel = []    # Algo 주문

    for order_id_key, order_data_value in list(open_orders_state.items()):
        custom_type = order_type_mapping.get(order_id_key)
        if custom_type and custom_type.startswith(prefix):
            is_algo_order = order_data_value.get('isAlgoOrder', False)
            
            if is_algo_order:
                # Algo Order는 algoId 사용
                algo_id = order_data_value.get('algoId')
                if algo_id:
                    algo_orders_to_cancel.append({
                        'algo_id': str(algo_id),
                        'local_key': order_id_key,
                        'custom_type': custom_type
                    })
                else:
                    logging.warning(f"Algo 주문 취소 건너뜀: 로컬 키 {order_id_key} (구분: {custom_type})에 algoId 없음. 데이터: {order_data_value}")
            else:
                # 일반 주문은 orderId 사용
                api_call_order_id = order_data_value.get('orderId', order_data_value.get('i'))
                if api_call_order_id is not None:
                    normal_orders_to_cancel.append({
                        'id_for_api': str(api_call_order_id),
                        'local_key': order_id_key,
                        'custom_type': custom_type
                    })
                else:
                    logging.warning(f"일반 주문 취소 건너뜀: 로컬 키 {order_id_key} (구분: {custom_type})에 orderId 없음. 데이터: {order_data_value}")

    total_to_cancel = len(normal_orders_to_cancel) + len(algo_orders_to_cancel)
    if total_to_cancel == 0:
        logging.debug(f"'{prefix}' prefix를 가진 취소할 주문 없음.")
        return cancelled_ids

    logging.info(f"'{prefix}' prefix를 가진 {total_to_cancel}개 주문 취소 시도... (일반: {len(normal_orders_to_cancel)}, Algo: {len(algo_orders_to_cancel)})")
    
    # 1. 일반 주문 취소
    if normal_orders_to_cancel:
        cancel_tasks = [
            client.futures_cancel_order(symbol=symbol, orderId=int(order_info['id_for_api']))
            for order_info in normal_orders_to_cancel
        ]
        results = await asyncio.gather(*cancel_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            order_info = normal_orders_to_cancel[i]
            local_order_key = order_info['local_key']
            api_id_used = order_info['id_for_api']

            if isinstance(result, Exception):
                if hasattr(result, 'code') and result.code == -2011:
                    logging.warning(f"일반 주문 취소 - 서버에 없음: ID={api_id_used} (로컬키:{local_order_key}). 로컬 정리.")
                elif "Order does not exist" in str(result):
                    logging.warning(f"일반 주문 취소 - 이미 처리됨: ID={api_id_used} (로컬키:{local_order_key}).")
                else:
                    logging.error(f"일반 주문 취소 실패: ID={api_id_used} (로컬키:{local_order_key}), 오류: {result}")
                    continue  # 실패한 경우 로컬 상태 유지
            else:
                logging.info(f"일반 주문 취소 성공: ID={api_id_used} (로컬키:{local_order_key}), 구분:{order_info['custom_type']}")
            
            # 성공 또는 서버에 없는 경우 로컬 상태 정리
            if local_order_key in open_orders_state: del open_orders_state[local_order_key]
            if local_order_key in order_type_mapping: del order_type_mapping[local_order_key]
            cancelled_ids.append(local_order_key)

    # 2. Algo 주문 취소
    if algo_orders_to_cancel:
        cancel_tasks = [
            cancel_algo_order(client, symbol, order_info['algo_id'])
            for order_info in algo_orders_to_cancel
        ]
        results = await asyncio.gather(*cancel_tasks, return_exceptions=True)

        for i, result in enumerate(results):
            order_info = algo_orders_to_cancel[i]
            local_order_key = order_info['local_key']
            algo_id_used = order_info['algo_id']

            if isinstance(result, Exception):
                logging.error(f"Algo 주문 취소 예외: algoId={algo_id_used} (로컬키:{local_order_key}), 오류: {result}")
                continue
            
            # cancel_algo_order는 (data, success, error_code) 튜플 반환
            cancel_data, success, error_code = result
            
            if success:
                logging.info(f"Algo 주문 취소 성공: algoId={algo_id_used} (로컬키:{local_order_key}), 구분:{order_info['custom_type']}")
                if local_order_key in open_orders_state: del open_orders_state[local_order_key]
                if local_order_key in order_type_mapping: del order_type_mapping[local_order_key]
                cancelled_ids.append(local_order_key)
            else:
                # 이미 체결/취소된 경우 (-20012 또는 유사 오류)
                if error_code in [-20012, -2011]:
                    logging.warning(f"Algo 주문 취소 - 서버에 없음/이미처리: algoId={algo_id_used}. 로컬 정리.")
                    if local_order_key in open_orders_state: del open_orders_state[local_order_key]
                    if local_order_key in order_type_mapping: del order_type_mapping[local_order_key]
                    cancelled_ids.append(local_order_key)
                else:
                    logging.error(f"Algo 주문 취소 실패: algoId={algo_id_used}, error_code={error_code}")
            
    return cancelled_ids

async def place_triggered_market_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, step_index: int, sub_index: int, quantity: float, side: str, position_side: str, base_attempt_key_prefix: str): # symbol_info -> symbol_info_local
    """ 가격 조건이 충족되었을 때 실제 시장가 주문을 실행하는 함수. """
    logging.info(f"[TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index}: 시장가 {side} 주문 실행. 수량: {quantity}")
    order_mapping_key = f"{base_attempt_key_prefix}-{sub_index}"
    order_data, success, error_code = await place_futures_order(
        client, symbol_info_local, state.get('symbol'), 
        side, position_side, quantity, 
        FUTURE_ORDER_TYPE_MARKET, 
        price=None, # 시장가 주문이므로 price 불필요
        stop_price=None, # 시장가 주문이므로 stop_price 불필요
        reduce_only=False, # <<< 이 부분을 False로 명시하거나, place_futures_order 함수가 기본값을 False로 처리한다면 생략 가능
        open_orders_state_ref=state.get('open_orders_state'), 
        order_type_mapping_ref=state.get('order_type_mapping'), 
        mapping_key=order_mapping_key
    )
    if success and order_data: logging.info(f"  -> [TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index} 주문 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"  -> [TriggeredMarketOrder] 스텝 {step_index} 분할 {sub_index} 주문 실패. ErrorCode: {error_code}")
    return success, order_data

async def place_single_maginot_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, step_index_to_place: int): # symbol_info -> symbol_info_local
    """주어진 스텝 인덱스에 해당하는 Maginot 주문을 생성합니다."""
    logging.info(f"[스텝 {step_index_to_place}] Maginot 주문 생성 시도...")
    symbol = state.get('symbol'); entry_qty_list_local = state.get('entry_quantity_list'); maginot_ratio_local = state.get('maginot_ratio') # entry_qty_list, maginot_ratio 이름 변경
    tick_size = symbol_info_local.get('tickSize'); step_size = symbol_info_local.get('stepSize') # symbol_info_local 사용
    qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty') # symbol_info_local 사용
    signal_type_local = state.get('signal_type') 
    if not all([symbol, entry_qty_list_local, maginot_ratio_local is not None, signal_type_local, symbol_info_local]): logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 필수 정보 누락."); return False, None
    if not (0 <= step_index_to_place < config.STEPS and step_index_to_place < len(entry_qty_list_local)): logging.warning(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 유효하지 않은 스텝 또는 수량 정보 없음."); return False, None
    entry_side = SIDE_BUY if signal_type_local == 'LONG' else SIDE_SELL
    position_side = 'LONG' if signal_type_local == 'LONG' else 'SHORT'
    maginot_qty = entry_qty_list_local[step_index_to_place]
    adjusted_maginot_qty = adjust_quantity(maginot_qty, step_size, qty_precision, min_qty_str)
    if adjusted_maginot_qty is None or adjusted_maginot_qty <= 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 수량 조정 실패/0 이하: 원본={maginot_qty}, 조정={adjusted_maginot_qty}."); return False, None
    logging.info(f"[Maginot 스텝 {step_index_to_place}] 사전 조정된 수량: {adjusted_maginot_qty} (원본: {maginot_qty})")
    try:
        positions = await client.futures_position_information(symbol=symbol)
        current_pos = next((p for p in positions if p.get('positionSide') == position_side), None)
        if not current_pos or float(current_pos.get('positionAmt', '0')) == 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: {position_side} 포지션 없음."); return False, None
        avg_entry_price = float(current_pos.get('entryPrice', '0')); liq_price = float(current_pos.get('liquidationPrice', '0'))
        if avg_entry_price <= 0 or liq_price <= 0: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 불가: 유효하지 않은 진입가({avg_entry_price}) 또는 청산가({liq_price})."); return False, None
        maginot_price_d = Decimal(str(avg_entry_price)) + (Decimal(str(liq_price)) - Decimal(str(avg_entry_price))) * Decimal(str(maginot_ratio_local)) # maginot_ratio_local 사용
        maginot_price_str = format_price(maginot_price_d, tick_size)
        if not maginot_price_str: logging.error(f"[Maginot 스텝 {step_index_to_place}] 가격 포맷팅 실패: {maginot_price_d}"); return False, None
        logging.info(f"[Maginot 스텝 {step_index_to_place}] 주문 실행: Side={entry_side}, PosSide={position_side}, Qty={adjusted_maginot_qty}, Price={maginot_price_str}")
        success, placed_orders = await place_divided_orders(client, gui, symbol_info_local, state, 'Maginot', step_index_to_place, adjusted_maginot_qty, entry_side, position_side, FUTURE_ORDER_TYPE_LIMIT, maginot_price_str) # symbol_info_local 사용
        return success, placed_orders[0] if placed_orders else None 
    except Exception as e: logging.error(f"[Maginot 스텝 {step_index_to_place}] 생성 중 오류: {e}", exc_info=True); return False, None

async def place_general_hedge_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, filled_step_index: int, hedge_quantity: float, general_order_main_side: str): # general_order_position_side -> general_order_main_side, symbol_info -> symbol_info_local
    """ General 주문 체결 후 해당 스텝의 Hedge 주문 (시장가)을 실행합니다. """
    logging.info(f"=== General Hedge 주문 생성 시도: 스텝 {filled_step_index}, 수량 {hedge_quantity}, 원 주문 주사이드: {general_order_main_side} ===") # general_order_position_side -> general_order_main_side
    symbol = state.get('symbol'); open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {}) # open_orders_state, order_type_mapping 이름 변경
    hedge_side = SIDE_SELL if general_order_main_side == 'LONG' else SIDE_BUY # 헤지 주문 방향 결정
    hedge_position_side = 'SHORT' if general_order_main_side == 'LONG' else 'LONG' # 헤지 주문 포지션 사이드 결정
    if not hedge_position_side: logging.error(f"[GeneralHedge 스텝 {filled_step_index}] 주문 생성 불가: 원 주문의 주사이드 정보 없음."); return False, [] # general_order_position_side -> general_order_main_side
    attempt_key_prefix = f"GeneralHedge-{filled_step_index}"
    logging.info(f"[GeneralHedge 스텝 {filled_step_index}] 주문 정보: Symbol={symbol}, Side={hedge_side}, PositionSide={hedge_position_side}, Qty={hedge_quantity}, Type=MARKET, KeyPrefix={attempt_key_prefix}")
    success, placed_orders = await place_divided_orders(client, gui, symbol_info_local, state, 'GeneralHedge', filled_step_index, hedge_quantity, hedge_side, hedge_position_side, FUTURE_ORDER_TYPE_MARKET, None, None, None, attempt_key_prefix) # symbol_info_local, price 등 None 처리
    if success and placed_orders: logging.info(f"[GeneralHedge 스텝 {filled_step_index}] 시장가 주문 생성 요청 성공: {len(placed_orders)}개 주문, ID(s)={[o.get('orderId') for o in placed_orders]}")
    else: logging.error(f"[GeneralHedge 스텝 {filled_step_index}] 시장가 주문 생성 요청 실패.")
    return success, placed_orders

async def place_single_general_sub_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, order_purpose: str, target_step_index: int, sub_order_index: int, num_total_divisions: int, quantity_for_this_sub: float, base_entry_price_for_spread: float, side: str, position_side: str, attempt_key_prefix: str ): # symbol_info -> symbol_info_local
    """단일 General 또는 SignalEntry 분할 주문(LIMIT)을 생성합니다.""" # 이 함수는 현재 조건부 시장가 로직에서는 직접 사용되지 않음.
    logging.info(f"[{order_purpose} 스텝 {target_step_index}] 단일 분할 주문 생성 시도 (분할 {sub_order_index + 1}/{num_total_divisions})")
    symbol = state.get('symbol'); tick_size = symbol_info_local.get('tickSize') # symbol_info_local 사용
    open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {}) # open_orders_state, order_type_mapping 이름 변경
    base_price_d = Decimal(str(base_entry_price_for_spread)); tick_size_d = Decimal(str(tick_size)); raw_price_increment = base_price_d * Decimal(str(config.DIVIDE_RATE)); price_increment_abs = Decimal('0')
    if raw_price_increment > Decimal('0'):
        price_increment_abs = (raw_price_increment / tick_size_d).quantize(Decimal('1'), rounding=ROUND_UP) * tick_size_d
        if price_increment_abs < tick_size_d: price_increment_abs = tick_size_d
    elif config.DIVIDE_RATE == 0: price_increment_abs = Decimal('0')
    else: price_increment_abs = Decimal('0') 
    price_offset = price_increment_abs * Decimal(str(sub_order_index))
    if side == SIDE_BUY: calculated_price_dec = base_price_d - price_offset
    elif side == SIDE_SELL: calculated_price_dec = base_price_d + price_offset
    else: calculated_price_dec = base_price_d
    formatted_calc_price = format_price(calculated_price_dec, tick_size)
    if not formatted_calc_price: logging.error(f"[{order_purpose} 스텝 {target_step_index} 분할 {sub_order_index}] 가격 포맷팅 실패: {calculated_price_dec}"); return None, False, None 
    calculated_price_float = float(formatted_calc_price); order_mapping_key = f'{attempt_key_prefix}-{sub_order_index}' 
    logging.info(f"  - {order_purpose} 단일 분할 주문 (스텝 {target_step_index}, 분할 {sub_order_index + 1}/{num_total_divisions}): 수량 {quantity_for_this_sub}, 가격 {calculated_price_float}, Key={order_mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, side, position_side, quantity_for_this_sub, FUTURE_ORDER_TYPE_LIMIT, calculated_price_float, None, False, open_orders_state_local, order_type_mapping_local, order_mapping_key) # symbol_info_local 사용, stop_price=None 추가
    return order_data, success, error_code

async def place_single_exit_sub_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, target_step_index: int, sub_order_index: int, avg_entry_price: float, exit_ratio: float, entry_quantity_for_this_sub_order: float, signal_type_local: str ): # symbol_info -> symbol_info_local, signal_type -> signal_type_local
    """단일 Exit 분할 주문(LIMIT)을 생성합니다."""
    logging.info(f"[스텝 {target_step_index}] 단일 Exit 분할 주문 생성 시도 (분할 인덱스: {sub_order_index})")
    symbol = state.get('symbol'); tick_size = symbol_info_local.get('tickSize'); step_size = symbol_info_local.get('stepSize') # symbol_info_local 사용
    qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty') # symbol_info_local 사용
    open_orders_state_local = state.get('open_orders_state', {}); order_type_mapping_local = state.get('order_type_mapping', {}) # open_orders_state, order_type_mapping 이름 변경
    exit_side = SIDE_SELL if signal_type_local == 'LONG' else SIDE_BUY
    position_side = 'LONG' if signal_type_local == 'LONG' else 'SHORT'
    base_exit_price_d = Decimal(str(avg_entry_price)) * (Decimal('1.0') + Decimal(str(exit_ratio)) if signal_type_local == 'LONG' else Decimal('1.0') - Decimal(str(exit_ratio)))
    price_increment_abs = base_exit_price_d * Decimal(str(config.DIVIDE_RATE)) 
    price_offset = price_increment_abs * Decimal(str(sub_order_index))
    if exit_side == SIDE_SELL: calculated_price_dec = base_exit_price_d + price_offset
    elif exit_side == SIDE_BUY: calculated_price_dec = base_exit_price_d - price_offset
    else: calculated_price_dec = base_exit_price_d 
    formatted_calc_price = format_price(calculated_price_dec, tick_size)
    if not formatted_calc_price: logging.error(f"[Exit 분할 {sub_order_index}] 가격 포맷팅 실패: {calculated_price_dec}"); return None, False, None 
    calculated_price_float = float(formatted_calc_price)
    adjusted_sub_qty = adjust_quantity(entry_quantity_for_this_sub_order, step_size, qty_precision, min_qty_str)
    if adjusted_sub_qty is None or adjusted_sub_qty <= 0: logging.error(f"[Exit 분할 {sub_order_index}] 수량 조정 실패/0 이하: 원본={entry_quantity_for_this_sub_order}, 조정={adjusted_sub_qty}"); return None, False, None
    quantity_step_index_for_key = target_step_index - sub_order_index
    order_mapping_key = f'Exit-{target_step_index}-{sub_order_index}_qty{quantity_step_index_for_key}'
    logging.info(f"  - Exit 단일 분할 주문 (스텝 {target_step_index}, 분할 {sub_order_index}): 수량 {adjusted_sub_qty}, 가격 {calculated_price_float}, Key={order_mapping_key}")
    order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, exit_side, position_side, adjusted_sub_qty, FUTURE_ORDER_TYPE_LIMIT, calculated_price_float, None, True, open_orders_state_local, order_type_mapping_local, order_mapping_key) # symbol_info_local 사용, stop_price=None 추가
    return order_data, success, error_code

async def get_current_position_quantity(client: AsyncClient, symbol: str, position_side_to_check: str) -> Decimal:
    """특정 심볼과 포지션 사이드의 현재 수량을 Decimal로 반환합니다. 포지션 없으면 0 반환."""
    try:
        positions = await client.futures_position_information(symbol=symbol)
        for p in positions:
            if p.get('positionSide') == position_side_to_check:
                return Decimal(p.get('positionAmt', '0')) # SHORT는 음수일 수 있으므로 필요시 abs()
        return Decimal('0') # 해당 사이드 포지션 없음
    except Exception as e:
        logging.error(f"get_current_position_quantity({symbol}, {position_side_to_check}) 오류: {e}")
        return Decimal('0') # 오류 시 0 반환

def place_trailing_stop_exit_order(client, symbol, position_side, quantity, activation_price, callback_rate):
    """
    TRAILING_STOP_MARKET을 사용하여 포지션을 익절합니다.
    - 'callbackRate'는 0.1 ~ 5.0 사이의 값이어야 합니다.
    - 'reduceOnly'는 True로 설정하여 포지션 감소만 되도록 보장합니다.
    """
    try:
        # 포지션 종료를 위한 주문 방향 설정
        # 예: SHORT 포지션 익절 -> BUY 주문
        side = 'BUY' if position_side == 'SHORT' else 'SELL'

        params = {
            'symbol': symbol,
            'side': side,
            'positionSide': position_side,
            'type': 'TRAILING_STOP_MARKET',
            'quantity': quantity,
            'callbackRate': callback_rate,        # 콜백 비율 (예: 0.5% -> 0.5)
            'reduceOnly': True                    # 포지션을 줄이는 용도로만 사용
        }

        print(f"TRAILING_STOP_MARKET 주문 시도: {params}")
        
        # 선물 주문 생성 API 호출
        order = client.new_order(**params)
        
        print("주문 성공:")
        print(order)
        return order

    except ClientError as error:
        print(
            f"API 오류 발생: {error.error_code} - {error.error_message}"
        )
        return None

async def place_partial_hedge_exit_market_order(
    client: AsyncClient,
    symbol_info_local: dict,
    state: dict, # main.py의 open_orders_state, order_type_mapping 포함
    step_index_info: int, # 로깅 및 매핑키용
    quantity: Decimal,
    main_pos_side: str # 주 포지션 방향 (LONG 또는 SHORT)
) -> tuple[dict | None, bool, str | None]:
    """ 특정 수량만큼의 헤지 포지션을 시장가로 청산하는 주문 """
    
    symbol = state.get('symbol')
    open_orders_state_ref = state.get('open_orders_state')
    order_type_mapping_ref = state.get('order_type_mapping')

    hedge_exit_side = None
    hedge_pos_side_to_exit = None

    if main_pos_side == 'LONG': # 주 포지션이 LONG이면, 헤지는 SHORT
        hedge_exit_side = SIDE_BUY    # SHORT 헤지를 청산하기 위해 BUY
        hedge_pos_side_to_exit = 'SHORT'
    elif main_pos_side == 'SHORT': # 주 포지션이 SHORT이면, 헤지는 LONG
        hedge_exit_side = SIDE_SELL   # LONG 헤지를 청산하기 위해 SELL
        hedge_pos_side_to_exit = 'LONG'
    else:
        logging.error(f"[PartialHedgeExitMarket] 알 수 없는 주 포지션({main_pos_side}). 헤지 청산 불가.")
        return None, False, "INVALID_MAIN_POS_SIDE"

    mapping_key = f"PartialHedgeExitMarket-{step_index_info}-{int(time.time())}"
    
    logging.info(f"[PartialHedgeExitMarket 스텝 {step_index_info}] 실행: Side={hedge_exit_side}, PosSide={hedge_pos_side_to_exit}, Qty={quantity}, Key={mapping_key}")

    # reduceOnly=True로 포지션 감소만 허용
    order_data, success, error_code = await place_futures_order(
        client, symbol_info_local, symbol,
        hedge_exit_side, hedge_pos_side_to_exit, float(quantity), # 수량은 float으로
        order_type=FUTURE_ORDER_TYPE_MARKET,
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
    client: AsyncClient,
    gui,
    symbol_info_local: dict,
    state: dict,
    current_step_index_local: int,
    trigger_event: str
):
    """
    현재 스텝에 맞는 익절/다음 스텝 주문을 설정합니다. (TSM 주문 유지 로직 수정)
    """
    function_name = "logic.place_orders_for_step (v_final_tsm_keep)"
    logging.info(f"=== 스텝 {current_step_index_local} 주문 설정 시작 ({function_name}, Trigger: {trigger_event}) ===")

    try:
        # --- 1. 정보 추출 ---
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

        # --- 2. 기존 주문 정리 (조건부로 TSM 제외) ---
        logging.info(f"[{function_name}] 기존 익절/마지노 주문 정리 시작")

        # --- 🟢 핵심 수정: STEP_DOWN 이벤트가 아닐 때만 MainPartialExitTSM- 주문을 취소 ---
        if trigger_event != 'STEP_DOWN':
            logging.info(f"[{function_name}] Trigger가 '{trigger_event}'이므로, 기존 MainPartialExitTSM 주문을 정리합니다.")
            await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'MainPartialExitTSM-')
        else:
            logging.info(f"[{function_name}] Trigger가 'STEP_DOWN'이므로, 기존 MainPartialExitTSM 주문을 유지합니다.")
        # --- 수정 끝 ---
            
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'HedgePartialExitSM-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'Maginot-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'MainStopLoss-')
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'HedgeTakeProfitTSM-')

        # --- 3. 현재 포지션 정보 조회 및 변수 설정 (진단 로그 추가) ---
        positions = []
        main_pos_qty, main_pos_avg_price, main_pos_liq_price = Decimal('0'), Decimal('0'), Decimal('0')
        hedge_pos_qty = Decimal('0')
        
        max_retries = 10
        retry_delay = 1

        for attempt in range(max_retries):
            positions = await client.futures_position_information(symbol=symbol)
            
            for p_info in positions:
                pos_side = p_info.get('positionSide')
                amt = Decimal(p_info.get('positionAmt', '0'))
                if pos_side == signal_type_local:
                    main_pos_qty = abs(amt)
                    main_pos_avg_price = Decimal(p_info.get('entryPrice', '0'))
                    main_pos_liq_price = Decimal(p_info.get('liquidationPrice', '0'))
                elif (signal_type_local == 'LONG' and pos_side == 'SHORT') or (signal_type_local == 'SHORT' and pos_side == 'LONG'):
                    hedge_pos_qty = abs(amt)
            
            if main_pos_liq_price > 0:
                logging.info(f"[{function_name}] 시도 {attempt + 1}: 유효한 청산가({main_pos_liq_price}) 확인 완료.")
                break
            
            logging.warning(f"[{function_name}] 시도 {attempt + 1}: 청산가({main_pos_liq_price})가 아직 유효하지 않습니다. {retry_delay}초 후 재시도합니다.")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                logging.error(f"[{function_name}] 최대 재시도 횟수({max_retries}) 초과. 유효한 청산가를 얻지 못했습니다.")

        price_precision = int(symbol_info_local.get('pricePrecision', 4))
        logging.info(f"[{function_name}] 주 포지션({signal_type_local}): Qty={main_pos_qty} @ {main_pos_avg_price:.{price_precision}f}")
        logging.info(f"[{function_name}] 헤지 포지션: Qty={hedge_pos_qty}")

        # --- 4. 익절 주문 설정 ---
        current_step_hedge_qty = Decimal(str(per_step_hedge_quantity_list_local[current_step_index_local]))
        min_qty = Decimal(str(symbol_info_local.get('minQty', '0.1')))

        # 공통 로직: 익절 발동가 계산
        trigger_price = Decimal('0')
        
        # [수정] previous_exit_price가 있어도, TSM은 비율 기반이므로 정확한 비율 계산을 위해 아래 로직 강화
        if previous_exit_price and previous_exit_price > 0:
            logging.info(f"[{function_name}] 이전 익절가({previous_exit_price})를 기준으로 다음 익절가 설정.")
            base_price = Decimal(str(previous_exit_price))
            divide_rate = Decimal(str(config.DIVIDE_RATE))
            if signal_type_local == 'LONG':
                trigger_price = base_price * (Decimal('1') + divide_rate)
            else: # SHORT
                trigger_price = base_price * (Decimal('1') - divide_rate)
        
        elif main_pos_qty > 0:
            logging.info(f"[{function_name}] 포지션 평단가({main_pos_avg_price})를 기준으로 익절가 설정.")
            
            # 1. 리스트에서 비율 가져오기
            raw_ratio = exit_ratio_list_local[current_step_index_local]
            exit_ratio = Decimal(str(raw_ratio))
            
            # [🟢 추가된 안전장치] 비율이 0.1%(0.001) 미만이면 비정상으로 간주하고 EXIT_FIRST 설정값 사용
            if exit_ratio < Decimal('0.001'):
                logging.warning(f"⚠️ 경고: 스텝 {current_step_index_local}의 계산된 익절 비율({exit_ratio})이 너무 낮습니다. 설정값(EXIT_FIRST: {config.EXIT_FIRST})을 대신 사용합니다.")
                exit_ratio = Decimal(str(config.EXIT_FIRST))
            
            logging.info(f"[{function_name}] 최종 적용 Exit 비율: {exit_ratio} (설정값 기반)")

            # 2. 가격 계산
            if signal_type_local == 'LONG':
                trigger_price = main_pos_avg_price * (Decimal('1') + exit_ratio)
            else: # SHORT
                trigger_price = main_pos_avg_price * (Decimal('1') - exit_ratio)

        # 익절 주문 실행
        if trigger_price > 0:
            formatted_trigger_price = format_price(trigger_price, symbol_info_local.get('tickSize'))
            main_exit_qty = float(entry_quantity_list_local[current_step_index_local])
            
            # 시나리오 1: 주 포지션 + 헤지 포지션 동시 익절
            if main_pos_qty > 0 and hedge_pos_qty > 0 and current_step_hedge_qty >= min_qty:
                logging.info(f"[{function_name}] 시나리오 1 활성화 (주+헤지 동시 익절). 발동가: {formatted_trigger_price}")
                hedge_exit_qty = float(current_step_hedge_qty)
                main_exit_side, main_exit_pos_side = (SIDE_SELL, 'LONG') if signal_type_local == 'LONG' else (SIDE_BUY, 'SHORT')
                hedge_exit_side, hedge_exit_pos_side = (SIDE_BUY, 'SHORT') if signal_type_local == 'LONG' else (SIDE_SELL, 'LONG')
                
                await place_futures_order(client, symbol_info_local, symbol, side=main_exit_side, position_side=main_exit_pos_side, quantity=main_exit_qty,
                                          order_type=FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET, activation_price=float(formatted_trigger_price), callback_rate=config.CALLBACK_RATE, reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"MainPartialExitTSM-{current_step_index_local}")

                if gui:
                    gui.update_exit_target_price(f"TSM @ {formatted_trigger_price}")
                    
                await place_futures_order(client, symbol_info_local, symbol, side=hedge_exit_side, position_side=hedge_exit_pos_side, quantity=hedge_exit_qty,
                                          order_type=FUTURE_ORDER_TYPE_STOP_MARKET, stop_price=float(formatted_trigger_price), reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"HedgePartialExitSM-{current_step_index_local}")

            # 시나리오 2: 주 포지션만 익절
            elif main_pos_qty > 0:
                logging.info(f"[{function_name}] 시나리오 2 활성화 (주 포지션만 익절). 발동가: {formatted_trigger_price}")
                main_exit_side, main_exit_pos_side = (SIDE_SELL, 'LONG') if signal_type_local == 'LONG' else (SIDE_BUY, 'SHORT')

                await place_futures_order(client, symbol_info_local, symbol, side=main_exit_side, position_side=main_exit_pos_side, quantity=main_exit_qty,
                                          order_type=FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET, activation_price=float(formatted_trigger_price), callback_rate=config.CALLBACK_RATE, reduce_only=True,
                                          open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"MainPartialExitTSM-{current_step_index_local}")

                if gui:
                    gui.update_exit_target_price(f"TSM @ {formatted_trigger_price}")

        else:
            logging.warning(f"[{function_name}] 익절 주문 설정 조건 불충족 (주 포지션 수량 0 또는 가격 계산 실패).")


        # --- 5. 최종 단계 또는 다음 스텝 Maginot 주문 설정 ---
        if current_step_index_local == config.STEPS - 1:
            logging.info(f"[{function_name}] 최종 스텝({current_step_index_local}) 손절매/헤지익절 주문 설정.")
            if main_pos_avg_price > 0 and main_pos_liq_price > 0:
                if signal_type_local == 'LONG':
                    stop_price_dec = main_pos_avg_price - (main_pos_avg_price - main_pos_liq_price) * (Decimal('1') - Decimal(str(config.MAGINOT)))
                    main_stop_side, main_stop_pos_side, hedge_profit_side, hedge_profit_pos_side = SIDE_SELL, 'LONG', SIDE_BUY, 'SHORT'
                else: # SHORT
                    stop_price_dec = main_pos_avg_price + (main_pos_liq_price - main_pos_avg_price) * (Decimal('1') - Decimal(str(config.MAGINOT)))
                    main_stop_side, main_stop_pos_side, hedge_profit_side, hedge_profit_pos_side = SIDE_BUY, 'SHORT', SIDE_SELL, 'LONG'

                formatted_stop_price = format_price(stop_price_dec, symbol_info_local.get('tickSize'))
                if main_pos_qty > 0:
                    await place_futures_order(client, symbol_info_local, symbol, side=main_stop_side, position_side=main_stop_pos_side, quantity=float(main_pos_qty),
                                              order_type=FUTURE_ORDER_TYPE_STOP_MARKET, stop_price=float(formatted_stop_price), reduce_only=True,
                                              open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"MainStopLoss-{current_step_index_local}")
                if hedge_pos_qty > 0:
                     await place_futures_order(client, symbol_info_local, symbol, side=hedge_profit_side, position_side=hedge_profit_pos_side, quantity=float(hedge_pos_qty),
                                              order_type=FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET, activation_price=float(formatted_stop_price), callback_rate=config.CALLBACK_RATE_FOR_LAST, reduce_only=True,
                                              open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"HedgeTakeProfitTSM-{current_step_index_local}")
        else:
            next_maginot_step_index = current_step_index_local + 1
            if main_pos_avg_price > 0 and main_pos_liq_price > 0:
                maginot_qty_for_next_step = Decimal(str(entry_quantity_list_local[next_maginot_step_index]))
                if maginot_qty_for_next_step >= min_qty:
                    if signal_type_local == 'LONG':
                        maginot_price_dec = main_pos_avg_price - (main_pos_avg_price - main_pos_liq_price) * (Decimal('1') - Decimal(str(config.MAGINOT)))
                        maginot_side, maginot_pos_side = SIDE_BUY, 'LONG'
                    else: # SHORT
                        maginot_price_dec = main_pos_avg_price + (main_pos_liq_price - main_pos_avg_price) * (Decimal('1') - Decimal(str(config.MAGINOT)))
                        maginot_side, maginot_pos_side = SIDE_SELL, 'SHORT'

                    formatted_maginot_price = format_price(maginot_price_dec, symbol_info_local.get('tickSize'))
                    logging.info(f"[{function_name}] 다음 스텝({next_maginot_step_index}) Maginot({maginot_pos_side}) 주문 설정: Qty={maginot_qty_for_next_step}, Price={formatted_maginot_price}")
                    await place_futures_order(client, symbol_info_local, symbol, side=maginot_side, position_side=maginot_pos_side, quantity=float(maginot_qty_for_next_step),
                                              order_type=FUTURE_ORDER_TYPE_LIMIT, price=float(formatted_maginot_price), reduce_only=False,
                                              open_orders_state_ref=open_orders_state_local, order_type_mapping_ref=order_type_mapping_local, mapping_key=f"Maginot-{next_maginot_step_index}")
            else:
                logging.warning(f"[{function_name}] 다음 스텝 Maginot 주문 설정 불가: 평단가/청산가 정보 부족.")
        
        if gui:
            gui.update_open_orders_display(list(open_orders_state_local.values()), order_type_mapping_local)

    except Exception as e:
        logging.error(f"[{function_name}] 스텝 {current_step_index_local} 주문 설정 중 예외 발생: {e}", exc_info=True)
    
    logging.info(f"=== 스텝 {current_step_index_local} 주문 설정 로직 완료 ({function_name}) ===")

async def close_all_open_positions_for_symbol(client: AsyncClient, symbol: str, symbol_info_local: dict, open_orders_state_ref: dict, order_type_mapping_ref: dict): # symbol_info -> symbol_info_local
    """지정된 심볼의 모든 오픈 포지션을 시장가로 종료합니다."""
    logging.info(f"[{symbol}] 모든 오픈 포지션 종료 시도...")
    closed_count = 0; failed_count = 0; all_positions_closed_successfully = True 
    try:
        positions = await client.futures_position_information(symbol=symbol)
        if not positions: logging.info(f"[{symbol}] 조회된 포지션 정보 없음. 종료할 포지션 없음."); return True
        qty_precision = symbol_info_local.get('quantityPrecision'); step_size = symbol_info_local.get('stepSize'); min_qty_str = symbol_info_local.get('minQty') # symbol_info_local 사용
        if qty_precision is None or step_size is None or min_qty_str is None: logging.error(f"[{symbol}] 포지션 종료 위한 심볼 정보 부족 (정밀도/스텝사이즈/최소수량)."); return False
        active_positions_to_close = []
        for position in positions:
            pos_amt_str = position.get('positionAmt', '0'); pos_side = position.get('positionSide') 
            try:
                pos_amt_decimal = Decimal(pos_amt_str)
                if pos_amt_decimal != Decimal('0'): active_positions_to_close.append({'amount_decimal': pos_amt_decimal, 'side_ws': pos_side, 'symbol': position.get('symbol')})
            except Exception as e: logging.warning(f"[{symbol}] 포지션 수량 '{pos_amt_str}' 처리 중 오류: {e}. 건너뜀."); continue
        if not active_positions_to_close: logging.info(f"[{symbol}] 현재 활성 포지션 없음. 종료 작업 불필요."); return True
        for pos_data in active_positions_to_close:
            pos_amt_dec = pos_data['amount_decimal']; ws_pos_side = pos_data['side_ws'] 
            order_side_to_close = None; order_position_side = ws_pos_side 
            if ws_pos_side == 'BOTH': 
                if pos_amt_dec > Decimal('0'): order_side_to_close = SIDE_SELL
                elif pos_amt_dec < Decimal('0'): order_side_to_close = SIDE_BUY
            elif ws_pos_side == 'LONG' and pos_amt_dec > Decimal('0'): order_side_to_close = SIDE_SELL
            elif ws_pos_side == 'SHORT' and pos_amt_dec < Decimal('0'): order_side_to_close = SIDE_BUY
            else: logging.warning(f"[{symbol}] 포지션({ws_pos_side}, 수량:{pos_amt_dec})에 대한 종료 방향 결정 불가. 건너뜀."); failed_count += 1; all_positions_closed_successfully = False; continue
            if order_side_to_close is None: logging.warning(f"[{symbol}] 포지션({ws_pos_side}, 수량:{pos_amt_dec})에 대한 실제 주문 방향(order_side_to_close) 결정 불가. 건너뜀."); failed_count += 1; all_positions_closed_successfully = False; continue
            quantity_to_close_abs_dec = abs(pos_amt_dec)
            adjusted_qty_float = adjust_quantity(float(quantity_to_close_abs_dec), step_size, qty_precision, min_qty_str)
            if adjusted_qty_float is None or adjusted_qty_float <= 0: logging.error(f"[{symbol}] 포지션({ws_pos_side}) 종료 수량 조정 실패 또는 0 이하 (원본: {quantity_to_close_abs_dec}, 조정: {adjusted_qty_float})."); failed_count += 1; all_positions_closed_successfully = False; continue
            logging.info(f"  - [{symbol}] 포지션({ws_pos_side}, 현재수량:{pos_amt_dec}) 종료 주문 요청: Side={order_side_to_close}, Qty={adjusted_qty_float}, PosSide(주문용)={order_position_side}, ReduceOnly=True")
            mapping_key_close_pos = f"SysClosePos-{symbol}-{ws_pos_side}-{int(time.time())}"
            order_data, success, error_code = await place_futures_order(client, symbol_info_local, symbol, order_side_to_close, order_position_side, adjusted_qty_float, FUTURE_ORDER_TYPE_MARKET, None, None, True, open_orders_state_ref, order_type_mapping_ref, mapping_key_close_pos) # symbol_info_local 사용, stop_price=None 추가
            if success and order_data: logging.info(f"    -> [{symbol}] 포지션({ws_pos_side}) 종료 주문 요청 성공. OrderID: {order_data.get('orderId')}"); closed_count += 1
            else: logging.error(f"    -> [{symbol}] 포지션({ws_pos_side}) 종료 주문 요청 실패. ErrorCode: {error_code}"); failed_count += 1; all_positions_closed_successfully = False
            await asyncio.sleep(0.25) 
        if failed_count == 0 and closed_count > 0: logging.info(f"[{symbol}] 총 {closed_count}개 포지션에 대한 종료 주문 성공적으로 '요청'됨 (체결 확인은 웹소켓).")
        elif closed_count > 0 and failed_count > 0: logging.warning(f"[{symbol}] {closed_count}개 포지션 종료 주문 요청, {failed_count}개 실패.")
        elif closed_count == 0 and failed_count > 0: logging.error(f"[{symbol}] 모든 포지션 종료 주문 요청 실패 ({failed_count}개).")
        return all_positions_closed_successfully
    except Exception as e: logging.error(f"[{symbol}] 모든 포지션 종료 처리 중 예기치 않은 오류: {e}", exc_info=True); return False

async def place_exit_hedge_order(client: AsyncClient, gui, symbol_info_local: dict, state: dict, filled_step_index: int, position_side_local: str): # symbol_info -> symbol_info_local, position_side -> position_side_local
    """EXIT 주문 체결 후 필요한 EXIT HEDGE 주문 생성 (TRAILING_STOP_MARKET, 스텝 0 제외, reduceOnly 제거)"""
    # 이 함수는 프롬프트의 "마지막 Exit 주문 체결시 ... Last Hedge 주문" 과 유사한 역할을 할 수 있음 (전체 포지션 청산용)
    # 또는, 모든 분할 Exit 주문 완료 후 남은 포지션에 대해 실행될 수 있음.
    if filled_step_index == 0 and config.STEPS > 1 : # 스텝이 여러 개일 때만 스텝0 헤지 방지
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 스텝 0에서는 Trailing Exit Hedge 주문을 생성하지 않습니다 (분할 Exit Hedge가 처리).")
        return False, None
    try:
        symbol = state['symbol']; open_orders_state_local = state['open_orders_state']; order_type_mapping_local = state['order_type_mapping'] # open_orders_state, order_type_mapping 이름 변경
        step_size = symbol_info_local.get('stepSize'); qty_precision = symbol_info_local.get('quantityPrecision'); min_qty_str = symbol_info_local.get('minQty'); tick_size = symbol_info_local.get('tickSize') # symbol_info_local 사용
        if not all([step_size, qty_precision is not None, min_qty_str, tick_size]): logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: 필수 심볼 정보 누락."); return False, None
        positions = await client.futures_position_information(symbol=symbol)
        current_pos = next((p for p in positions if p.get('positionSide') == position_side_local), None) # position_side_local 사용
        if not current_pos or float(current_pos.get('positionAmt', '0')) == 0: logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 포지션 없음, Hedge 생성 안함"); return False, None
        avg_entry_price = float(current_pos.get('entryPrice', '0'))
        if avg_entry_price <= 0: logging.warning(f"[EXIT HEDGE] 스텝 {filled_step_index}: 유효 진입가 없음 ({avg_entry_price})"); return False, None
        position_amt = abs(float(current_pos.get('positionAmt', '0')))
        adjusted_hedge_qty = adjust_quantity(position_amt, step_size, qty_precision, min_qty_str)
        if adjusted_hedge_qty is None or adjusted_hedge_qty <= 0: logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: 헷지 수량 조정 실패: 원본={position_amt}, 조정={adjusted_hedge_qty}"); return False, None
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index}: 사전 조정된 헷지 수량: {adjusted_hedge_qty} (원본: {position_amt})")
        activation_price = avg_entry_price; callback_rate = config.CALLBACK_RATE
        side = SIDE_SELL if position_side_local == 'LONG' else SIDE_BUY # position_side_local 사용
        formatted_activation_price = format_price(activation_price, tick_size)
        if formatted_activation_price is None: logging.error(f"[EXIT HEDGE] 스텝 {filled_step_index}: Activation Price 포맷팅 실패: {activation_price}"); return False, None
        params = {"symbol": symbol, "side": side, "positionSide": position_side_local, "type": FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET, "quantity": f"{adjusted_hedge_qty:.{qty_precision}f}", "activationPrice": formatted_activation_price, "callbackRate": callback_rate, "reduceOnly": "true"} # reduceOnly=true 추가 (포지션 종료 목적)
        logging.info(f"[EXIT HEDGE] 스텝 {filled_step_index} TRAILING_STOP 주문 시도: {params}")
        
        # 기존 ExitHedge- 접두사 주문 취소 (중복 방지)
        await cancel_orders_by_prefix(client, symbol, open_orders_state_local, order_type_mapping_local, 'ExitHedge-')
        if gui: gui.update_open_orders_display(list(open_orders_state_local.values()), order_type_mapping_local)

        order = await client.futures_create_order(**params) # place_futures_order 대신 직접 호출 (매핑키 자동생성 회피)
        if order:
            order_id_str = str(order.get('orderId'))
            order_data_with_creation_time = order.copy()
            order_data_with_creation_time['creationTime'] = time.time()
            open_orders_state_local[order_id_str] = order_data_with_creation_time # open_orders_state_local 사용
            order_type_mapping_local[order_id_str] = f'ExitHedge-{filled_step_index}' # order_type_mapping_local 사용
            logging.info(f"[EXIT HEDGE] 주문 성공: ID={order_id_str}, 구분=ExitHedge-{filled_step_index}")
            return True, order
        else: logging.error(f"[EXIT HEDGE] 주문 실패"); return False, None
    except Exception as e: logging.error(f"[EXIT HEDGE] 주문 생성 중 오류: {e}", exc_info=True); return False, None
    
async def place_general_order(client: AsyncClient, gui, symbol_info, state, step_index: int, quantity: float, attempt_key_prefix_base: str):
    logging.info(f"[General주문 스텝{step_index}] 생성 시도. 수량: {quantity}")
    order_mapping_key = f"{attempt_key_prefix_base}-0"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=SIDE_BUY, position_side='LONG', quantity=quantity,
        order_type=FUTURE_ORDER_TYPE_MARKET,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[General주문 스텝{step_index}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[General주문 스텝{step_index}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_general_order_market(client: AsyncClient, gui, symbol_info, state, step_index: int, quantity: float, base_attempt_key_prefix: str, signal_type: str):
    """ General 주문 (MARKET) 생성 - signal_type에 따라 동적으로 주문 """
    logging.info(f"[General주문 스텝{step_index}] Market 생성 시도. 수량: {quantity}, 기준: {signal_type}")
    
    order_mapping_key = f"{base_attempt_key_prefix}-0" 
    client_oid_suffix = str(int(time.time() * 1000))[-4:]
    generated_client_order_id = f"{order_mapping_key.replace('-', '_')}_{client_oid_suffix}"[:36]
    
    # --- 🟢 핵심 수정: signal_type에 따라 주문 방향 결정 ---
    if signal_type == 'SHORT':
        order_side = SIDE_SELL
        order_position_side = 'SHORT'
    else: # 기본값 또는 'LONG'
        order_side = SIDE_BUY
        order_position_side = 'LONG'
    # --- 수정 끝 ---

    logging.info(f"Generated ClientOrderId for General Order: {generated_client_order_id}")

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=order_side, position_side=order_position_side, quantity=quantity, # 🟢 변수로 교체
        order_type=FUTURE_ORDER_TYPE_MARKET,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key, 
        client_order_id=generated_client_order_id 
    )
    if success: logging.info(f"[General주문 스텝{step_index}] Market 성공. OrderID: {order_data.get('orderId')}, ClientOID: {order_data.get('clientOrderId')}")
    else: logging.error(f"[General주문 스텝{step_index}] Market 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_hedge_order_for_general(
    client: AsyncClient, 
    gui, 
    symbol_info_local: dict, # 일관성을 위해 symbol_info -> symbol_info_local로 변경 (선택적)
    state: dict, 
    general_step_index: int, 
    hedge_quantity: float,
    general_order_main_side: str # <<< 누락되었던 7번째 인자 추가
):
    """
    General 주문 또는 Maginot 주문 체결 후 해당 스텝의 Hedge 주문 (시장가)을 실행합니다.
    general_order_main_side 인자를 받아 헤지 방향을 결정합니다.
    """
    function_name = "logic.place_hedge_order_for_general" # 로깅용 함수 이름
    logging.info(f"[{function_name}] 스텝 {general_step_index} General/Maginot 주문 체결 후 헤지 주문 생성. 주포지션 방향: {general_order_main_side}, 헤지수량: {hedge_quantity}")
    
    symbol = state.get('symbol', config.SYMBOL) 
    open_orders_state_ref = state.get('open_orders_state')
    order_type_mapping_ref = state.get('order_type_mapping')

    if not symbol_info_local: # symbol_info_local 파라미터 사용
        logging.error(f"[{function_name}] 헤지 주문 불가: symbol_info_local 없음.")
        return None, False, None # API 응답, 성공여부, API 오류코드

    # 주 주문 방향(general_order_main_side)에 따라 헤지 주문의 side 및 positionSide 결정
    hedge_side = None
    hedge_position_side = None
    if general_order_main_side == 'LONG':
        hedge_side = SIDE_SELL  # 주 포지션이 LONG이면 헤지는 SHORT (매도)
        hedge_position_side = 'SHORT'
    elif general_order_main_side == 'SHORT':
        hedge_side = SIDE_BUY   # 주 포지션이 SHORT이면 헤지는 LONG (매수)
        hedge_position_side = 'LONG'
    else:
        logging.error(f"[{function_name}] 알 수 없는 주 주문 방향('{general_order_main_side}')으로 헤지 주문 방향을 결정할 수 없습니다.")
        return None, False, "UNKNOWN_MAIN_SIDE"

    # 고유한 mapping_key 생성
    # 사용자의 기존 mapping_key 형식 유지 또는 필요시 base_attempt_key_prefix 등을 활용하여 더 구체적으로 생성 가능
    # 여기서는 general_step_index와 타임스탬프 사용
    order_mapping_key = f"HedgeForGeneral-{general_step_index}-{int(time.time())}" 
    
    logging.info(f"  -> [{function_name}] 헤지 주문 요청: Side={hedge_side}, PosSide={hedge_position_side}, Qty={hedge_quantity}, MappingKey={order_mapping_key}")

    order_data, success, error_code = await place_futures_order(
        client=client, 
        symbol_info=symbol_info_local, # 수정된 파라미터명 사용
        symbol=symbol,
        side=hedge_side, 
        position_side=hedge_position_side, 
        quantity=hedge_quantity,
        order_type=FUTURE_ORDER_TYPE_MARKET, # 헤지 주문은 시장가로 가정
        price=None,         # 시장가이므로 불필요
        stop_price=None,    # 시장가이므로 불필요
        activation_price=None, # 시장가이므로 불필요 (TSM 아님)
        callback_rate=None,    # 시장가이므로 불필요 (TSM 아님)
        reduce_only=False,  # 헤지는 새로운 포지션을 잡는 것이므로 False
        open_orders_state_ref=open_orders_state_ref,
        order_type_mapping_ref=order_type_mapping_ref,
        mapping_key=order_mapping_key
    )

    if success:
        logging.info(f"[{function_name}] 스텝 {general_step_index} 헤지 주문 성공. ID: {order_data.get('orderId') if order_data else 'N/A'}")
    else:
        logging.error(f"[{function_name}] 스텝 {general_step_index} 헤지 주문 실패. ErrorCode: {error_code}")
    
    return order_data, success, error_code

async def place_maginot_order(client: AsyncClient, gui, symbol_info, state, step_to_place_maginot: int, quantity: float, price: float):
    logging.info(f"[Maginot주문 스텝{step_to_place_maginot}] 생성 시도. 수량: {quantity}, 가격: {price}")
    order_mapping_key = f"Maginot-{step_to_place_maginot}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=SIDE_BUY, position_side='LONG', quantity=quantity,
        order_type=FUTURE_ORDER_TYPE_LIMIT, price=price,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[Maginot주문 스텝{step_to_place_maginot}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[Maginot주문 스텝{step_to_place_maginot}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_maginot_hedge_order(client: AsyncClient, gui, symbol_info, state, maginot_step_index: int, hedge_quantity: float):
    logging.info(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 생성 시도. 수량: {hedge_quantity}")
    order_mapping_key = f"MaginotHedge-{maginot_step_index}-{int(time.time())}"
    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=SIDE_SELL, position_side='SHORT', quantity=hedge_quantity,
        order_type=FUTURE_ORDER_TYPE_MARKET,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[MaginotHedge주문 for Maginot스텝{maginot_step_index}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code


# --- 탈출 주문 상세 (수정됨) ---

async def place_main_exit_order_trailing_stop(client: AsyncClient, gui, symbol_info, state, quantity: float, callback_rate: float, order_key_suffix: str = ""):
    """ 주 포지션(LONG) 청산을 위한 Exit 주문 (TRAILING_STOP_MARKET) 생성 """
    logging.info(f"[MainExit-TSM 스텝{order_key_suffix}] 생성 시도. 수량: {quantity}, 콜백: {callback_rate}")
    order_mapping_key = f"MainExitTSM-{order_key_suffix}-{int(time.time())}"

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=SIDE_SELL, position_side='LONG', quantity=quantity, # LONG 포지션 청산
        order_type=FUTURE_ORDER_TYPE_TRAILING_STOP_MARKET,
        callback_rate=callback_rate,
        reduce_only=True,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[MainExit-TSM 스텝{order_key_suffix}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[MainExit-TSM 스텝{order_key_suffix}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code

async def place_hedge_exit_order_stop_market(client: AsyncClient, gui, symbol_info, state, quantity: float, stop_price: float, order_key_suffix: str = ""):
    """ 헤지 포지션(SHORT) 청산을 위한 Exit Hedge 주문 (STOP_MARKET) 생성 """
    logging.info(f"[HedgeExit-SM 스텝{order_key_suffix}] 생성 시도. 수량: {quantity}, 발동가: {stop_price}")
    order_mapping_key = f"HedgeExitSM-{order_key_suffix}-{int(time.time())}"

    order_data, success, error_code = await place_futures_order(
        client=client, symbol_info=symbol_info, symbol=state.get('symbol'),
        side=SIDE_BUY, position_side='SHORT', quantity=quantity, # SHORT 포지션 청산
        order_type=FUTURE_ORDER_TYPE_STOP_MARKET, stop_price=stop_price,
        reduce_only=True,
        open_orders_state_ref=state.get('open_orders_state'),
        order_type_mapping_ref=state.get('order_type_mapping'),
        mapping_key=order_mapping_key
    )
    if success: logging.info(f"[HedgeExit-SM 스텝{order_key_suffix}] 성공. ID: {order_data.get('orderId')}")
    else: logging.error(f"[HedgeExit-SM 스텝{order_key_suffix}] 실패. ErrorCode: {error_code}")
    return order_data, success, error_code