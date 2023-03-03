import time
import asyncio
import logging
import traceback
import pandas as pd
import ccxt
import ccxt.pro as ccxtpro
from ta import volatility
from datetime import datetime
from binance import client
from binance.error import ClientError
from binance.um_futures import UMFutures
from binance import AsyncClient, BinanceSocketManager
from binance.lib.utils import config_logging
from consts import *
import decorator


config_logging(logging, logging.INFO)

class Trader():

    def __init__(self):
        #관리자 전역변수
        self.binance = UMFutures(key=API_KEY, secret=API_SECRET)
        self.status = NEUTRAL
        self.now = None
        self.check_time = None
        self.price = 0
        self.redundancy = None
        self.position = None
        self.is_init_success = False
        self.min_qty = 0
        self.cycle = None
        self.init_data()

        #시그날 전역변수
        self.signal = None
        self.df = None
        self.close_price = None
        self.atr = None
        self.order_minimum_space = None
        
        #진입관리 매니지먼트 전역변수
        self.general = False
        self.general_stage = None
        self.general_orderlist = {}
        self.general_pricelist = {}

        # alrgo4 전역변수
        self.g_order_id = None
        self.g_order_status = False
        self.p_order_active = False
        self.p_order_price = None
        self.p_order_status = False
        self.standard_price = None
        self.avgprice = None
        self.stage_max = None
        self.stage = None

    def init_data(self):
        """
        트레이딩에 필요한 기능 초기화
        :return:
        """
        try:
            logging.info('init_data starts')
            # 초기화할 기능
            self.set_leverage()  # 레버리지 설정
            self.set_margin_type()  # 마진타입 설정
            self.get_position()  # 포지션 조회
            self.get_balance()  # 잔고 조회
            self.get_min_order_qty()  # 최소주문수량 조회
            self.is_init_success = True  # 초기화함수 완료
        except Exception as e:
            logging.error(traceback.format_exc())


    @decorator.call_binance_api
    def set_leverage(self):
        """
        레버리지 설정
        :return:
        """
        try:
            logging.info('set_leverage starts')
            self.position = self.binance.get_position_risk(symbol=SYMBOL)
            cur_long_leverage = self.position[0]['leverage']
            cur_short_leverage = self.position[1]['leverage']
            cur_long_positionAmt = self.position[0]['positionAmt']
            cur_short_positionAmt = self.position[1]['positionAmt']
            if abs(float(cur_long_positionAmt)) + abs(float(cur_short_positionAmt)) == 0:
                if cur_long_leverage or cur_short_leverage != LEVERAGE:
                    res = self.binance.change_leverage(symbol=SYMBOL, leverage=LEVERAGE, recvWindow=6000)
                    logging.info(res)
                else:
                    logging.info('leverage :', LEVERAGE)
            else:
                logging.info('Need to close position')
        
        except Exception as e:
            logging.error(traceback.format_exc())


    @decorator.call_binance_api
    def set_margin_type(self):
        """
        마진타입 설정
        :return:
        """
        try:
            logging.info('set_margin_type starts')
            cur_margintype = self.position[0]['marginType']
            upr = cur_margintype.upper()
            if upr != MARGIN_TYPE:
                res = self.binance.change_margin_type(symbol=SYMBOL, marginType=MARGIN_TYPE, recvWindow=6000)
                logging.info(res)
            else:
                logging.info('margin_type is checked')
        except Exception as e:
            logging.error(traceback.format_exc())


    @decorator.call_binance_api
    def get_balance(self):
        """
        잔고 조회
        :return:
        """
        try:
            logging.info('get_balance')
            res = self.binance.account(recvWindow=6000)
            res_ = list(filter(lambda a: a['asset'] == 'USDT', res['assets']))
            self.balance = res_[0]['availableBalance']
            logging.info(self.balance)
        except Exception as e:
            logging.error(traceback.format_exc())


    @decorator.call_binance_api
    def get_position(self):
        """
        포지션 조회
        :return:
        """
        try:
            logging.info('get_position')
            res = self.binance.account(recvWindow=6000)
            res = list(filter(lambda a: a['symbol'] == SYMBOL, res['positions']))
            self.position = res if len(res) > 0 and float(res[1]['positionAmt']) != 0 else None
            logging.info(self.position)
        except Exception as e:
            logging.error(traceback.format_exc())

    @decorator.call_binance_api
    def get_min_order_qty(self):
        """
        최소주문수량 조회
        """
        try:
            logging.info('get_minimum_order_qty')
            exinfo = self.binance.exchange_info() # 심볼코인 정보 요청 API
            exinfo_filter = list(filter(lambda a: a['symbol'] == SYMBOL, exinfo['symbols']))
            limit_exinfo = exinfo_filter[0]['filters'][1]
            self.min_qty = float(limit_exinfo['minQty']) #리미트 주문시 최소주문 수량
            logging.info(self.min_qty)
        except Exception as e:
            logging.error(traceback.format_exc())

    @decorator.call_binance_api
    def candle_data(self, time_frame, req_limit):
        """
        캔들정보
        """

        retry_count = 0
        while True: #리턴값이 없으면 0.25초 후 재요청
            candles = self.binance.klines("BTCUSDT", time_frame, limit=req_limit)
            if candles == None:
                time.sleep(0.25)
                retry_count += 1
            else:
                break
        df = pd.DataFrame(columns=['Open_time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close_time'])
        opentime, lopen, lhigh, llow, lclose, lvol, closetime = [], [], [], [], [], [], []

        for candle in candles:

            opentime.append(datetime.fromtimestamp(int(candle[0]) / 1000))
            lopen.append(float(candle[1]))
            lhigh.append(float(candle[2]))
            llow.append(float(candle[3]))
            lclose.append(float(candle[4]))
            lvol.append(float(candle[5]))
            closetime.append(datetime.fromtimestamp(int(candle[6]) / 1000))

        df['Open_time'] = opentime
        df['Open'] = lopen
        df['High'] = lhigh
        df['Low'] = llow
        df['Close'] = lclose
        df['Volume'] = lvol
        df['Close_time'] = closetime
        df['Atr'] = volatility.average_true_range(high=df['High'],low=df['Low'],close=df['Close'])
        print('재시도 횟수:', retry_count)

        return df

    def signal_generator(self):
        """
        시그널발생기
        """

        frame_num = int(TIME_FRAME[:-1])
        frame_text = TIME_FRAME[-1]
        result = {}
        try:
            if self.general == False:
                if TIME_FRAME: # 시그널 확인 조건 체크
                    if frame_text == 'm':
                        h_condition = True
                        m_condition = True if int(str(self.now)[-5:-3]) % frame_num == 0 else False
                    elif frame_text == 'h':
                        h_condition = True if int(str(self.now)[-8:-6]) % frame_num == 0 else False
                        m_condition = True if int(str(self.now)[-5:-3]) == 0 else False

                    if h_condition and m_condition:
                        self.df = trader.candle_data(TIME_FRAME, REQ_LIMIT)
                        candle_condition = self.df['Close'].iloc[-2] - self.df['Open'].iloc[-2]
                        if self.status == NEUTRAL:
                            if candle_condition < 0:
                                if self.df['Close'].iloc[-2] + (abs(candle_condition) * CONDITION_RATE) <= self.df['Close'].iloc[-1] <= self.df['Open'].iloc[-2]:
                                    result['signal'] = LONG
                            elif candle_condition > 0:
                                if self.df['Close'].iloc[-2] - (abs(candle_condition) * CONDITION_RATE) >= self.df['Close'].iloc[-1] >= self.df['Open'].iloc[-2]:
                                    result['signal'] = SHORT

                        elif self.status == LONG: # 진입평균가 1% ATR 추가해야됨
                            if candle_condition < 0:
                                if self.df['Close'].iloc[-2] + (abs(candle_condition) * CONDITION_RATE) <= self.df['Close'].iloc[-1] <= self.df['Open'].iloc[-2]:
                                    result['signal'] = LONG
                        elif self.status == SHORT:
                            if candle_condition > 0:
                                if self.df['Close'].iloc[-2] - (abs(candle_condition) * CONDITION_RATE) >= self.df['Close'].iloc[-1] >= self.df['Open'].iloc[-2]:
                                    result['signal'] = SHORT
                        
                        result['close_price'] = self.df['Close'].iloc[-1]
                        result['atr'] = self.df['Atr'].iloc[-1]
                        result['mingap'] = (result['close_price']*GAP_PERCENT if result['close_price'] >= result['atr'] else result['atr'])/GENERAL_DIV
                        
                    return result
            
        except Exception as e:
            logging.error(traceback.format_exc())

    def general_management(self):

        if self.general == False and self.signal:
            self.general = True
        
        if self.general == True:#매니지먼트가 실행중인지 확인
            #실행중이라면
                if self.general_orderlist == {}: #주문이 있는지 확인
                    """"""
                    test=3
                    #주문이 없다면
                        # self.general_order(self.signal[0], 24700, 0.001,"test11") #G주문
                    #주문이 있다면 (겟뉴오더 클라이언트 오더아이디가 제너럴이 있는지 확인)
                        #패스(체결 기다림)

            #실행중이 아니라면
                #패스
            
    
    @decorator.call_binance_api
    def general_order(self, signal, order_price, qty, coid):

        order = self.binance.new_order(
            symbol=SYMBOL,
            type=LIMIT,
            side=SIGNAL_TO_OPEN_SIDE[signal],
            PositionSide=[signal],
            price=order_price,
            quantity=qty,
            timeInForce="GTC",
            newClientOrderId=coid
        )
        self.general_orderlist['{coid}'] = order['orderId'] #주문 후 오더리스트에 오더 저장





    async def administrator(self):
        """
        메인관리자
        """

        exchange = ccxtpro.binance(config={
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })

        while True:
            res_price = await exchange.watch_ticker(SYMBOL)
            res_orderbook = await exchange.watch_order_book(TICKER)
            top_bid = float(res_orderbook['bids'][0][1])
            top_ask = float(res_orderbook['asks'][0][1])
            time_stamp = datetime.fromtimestamp(int(res_price['timestamp']) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            self.now = time_stamp
            self.price = res_price['close']


            
            if str(self.now)[-2:] == '00':
                if self.redundancy == None: # 2번 요청하지 않기 위한 리던던시
                    self.signal = self.signal_generator()
                    self.redundancy = str(self.now)[:-2]
                else:
                    if self.redundancy != str(self.now)[:-2]:
                        self.redundancy = None
            self.general_management()

            print(time_stamp, 'price:',self.price,'signal:', self.signal)






# alrgo4 전용 함수 ----------------------------------------------------------------------------------------------------------------------


    async def realtime_infomation(self):
        """
        실시간 포지션 수신
        """
        
        client = await AsyncClient.create(API_KEY, API_SECRET)
        bm = BinanceSocketManager(client)
        ts = bm.futures_user_socket()

        async with ts as tscm:
            while True:
                try:
                    event = await tscm.recv()
                    if event['e'] == 'ORDER_TRADE_UPDATE' and event['o']['X'] == 'NEW':
                        if event['o']['o'] == LIMIT and event['o']['ps'] == SHORT: #gw_order 주문
                            self.g_order_id = event['o']['i']
                    elif event['e'] == 'ORDER_TRADE_UPDATE' and event['o']['X'] == 'FILLED':
                        if event['o']['o'] == LIMIT and event['o']['ps'] == SHORT: #gw_order 체결
                            self.g_order_status = True
                        elif event['o']['o'] == MARKET and event['o']['ps'] == LONG: #p_order 체결
                            self.p_order_status = True
                        elif event['o']['o'] == MARKET and event['o']['ps'] == SHORT: 
                            if event['o']['c'] == "entry": # entry_order 체결
                                self.standard_price = float(event['o']['ap'])
                            else: # gf_order 체결
                                self.last_order_price = float(event['o']['ap'] )
                    elif event['e'] == 'ORDER_TRADE_UPDATE' and event['o']['X'] == 'CANCELED':
                        if event['o']['o'] == LIMIT and event['o']['ps'] == SHORT: #gw_order 취소
                            self.g_order_id = None
                        elif event['o']['o'] == LIMIT and event['o']['ps'] == LONG: #p_order 취소
                            self.p_order_id = None

                except Exception as e:
                    logging.error(traceback.format_exc())


    def get_price(self):
        coin_info = self.binance.ticker_price(SYMBOL)
        coin_price = coin_info['price'] # coin_info['close'] == coin_info['last'] 

        return coin_price


    def create_entry_list(self, percent):
        
        try:
            logging.info('create_entry_list')
            per = percent
            entry_list = []
            able_balance = float(self.balance)*0.95
            price = self.get_price()
            able_coin = able_balance / float(price) * LEVERAGE
            decimal = self.min_qty%1
            decimal = len(str(decimal))-2

            while True:
                if entry_list == []:
                    add = self.min_qty
                    entry_list.append(add)
                else:
                    summ = sum(entry_list)
                    if summ <= self.min_qty:
                        add = self.min_qty
                        entry_list.append(add)
                    else:
                        if summ <= able_coin:
                            add = round(summ * per, decimal)
                            entry_list.append(add)
                        else:
                            entry_list.pop()
                            break
            
            self.stage_max = len(entry_list)
            logging.info(entry_list)
            logging.info('len')
            logging.info(self.stage_max)
            return entry_list
        
        except Exception as e:
            logging.error(traceback.format_exc())


    @decorator.call_binance_api
    def entry_order(self, signal, qty):
        
        try:
            logging.info("entry order")
            order = self.binance.new_order(
                symbol=SYMBOL,
                type=MARKET,
                side=SIGNAL_TO_OPEN_SIDE[signal],
                PositionSide=[signal],
                quantity=qty,
                newClientOrderId="entry"
            )
            return order['orderId']
        except Exception as e:
            logging.error(traceback.format_exc())
    
    @decorator.call_binance_api
    def gw_order(self, signal, order_price, qty):
        
        try:
            logging.info("gw_order")
            order = self.binance.new_order(
                symbol=SYMBOL,
                type=LIMIT,
                side=SIGNAL_TO_OPEN_SIDE[signal],
                PositionSide=[signal],
                price=round(order_price,1),
                quantity=qty,
                timeInForce="GTC",
            )
            print(signal,'order_price:',round(order_price,1),'qty:',qty)
        except Exception as e:
            logging.error(traceback.format_exc())

    @decorator.call_binance_api
    def gf_order(self, signal, qty):
        
        try:
            logging.info("gf_order")
            order = self.binance.new_order(
                symbol=SYMBOL,
                type=MARKET,
                side=SIGNAL_TO_OPEN_SIDE[signal],
                PositionSide=[signal],
                quantity=qty,
            )
            print(signal,'order_price:',self.price,'qty:',qty)
        except Exception as e:
            logging.error(traceback.format_exc())

    @decorator.call_binance_api
    def p_order(self, signal, qty):
        
        try:
            logging.info("p_order")
            order = self.binance.new_order(
                symbol=SYMBOL,
                type=MARKET,
                side=SIGNAL_TO_OPEN_SIDE[signal],
                PositionSide=[signal],
                quantity=qty
            )
            print(signal,'order_price:',self.price,'qty:',qty)
        except Exception as e:
            logging.error(traceback.format_exc())

    def cancel_order(self, order_id):
        
        try:
            logging.info("cancel_order")
            cancel = self.binance.cancel_order(
                symbol=SYMBOL,
                orderId=order_id
            )
        except Exception as e:
            logging.error(traceback.format_exc())

    # async def get_order_info(self, order_id):

    #     while True:
    #         info = self.binance.get_all_orders(
    #             symbol=SYMBOL,
    #             orderId=order_id
    #         )
    #         if info != []:
    #             if info[0]['status'] == 'FILLED':
    #                 break
    #             else:
    #                 now = datetime.now()
    #                 print(now)
    #                 print("retry status")
    #                 await asyncio.sleep(0.2)
    #         else:
    #             now = datetime.now()
    #             print(now)
    #             print("retry status")
    #             time.sleep(2)

    #     return info[0]['avgPrice']

    def alrgo4_reset(self):
        self.g_order_id = None
        self.g_order_status = False
        self.p_order_active = False
        self.p_order_price = None
        self.p_order_status = False
        self.standard_price = None
        self.avgprice = None
        self.stage_max = None
        self.stage = None

    async def alrgo4_admin(self):

        exchange = ccxtpro.binance(config={
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future'
            }
        })

        qty_percent = 0.75
        scale_percent = 0.04


        if not self.is_init_success:
            logging.error('init_data got an error')
            return  # 초기화 비정상이면 프로그램 에러
        logging.info('price_websocket connect')

        while True:
            await asyncio.sleep(0.1)
            res_price = await exchange.watch_ticker(SYMBOL)
            res_orderbook = await exchange.watch_order_book(TICKER)
            top_bid = float(res_orderbook['bids'][0][1])
            top_ask = float(res_orderbook['asks'][0][1])
            time_stamp = datetime.fromtimestamp(int(res_price['timestamp']) / 1000).strftime('%Y-%m-%d %H:%M:%S')
            self.now = time_stamp
            self.price = res_price['close']

            if str(self.now)[-5:-3] != self.check_time:
                if self.redundancy == None: # 2번 요청하지 않기 위한 리던던시
                    print('Program in operating', self.now, 
                          'stage:', self.stage,'/',self.stage_max-1, 
                          'position_info:[entryPrice:',self.position[1]['entryPrice'],'Amount:',self.position[1]['positionAmt'],'] P-Active:',self.p_order_active)
                    self.redundancy = str(self.now)[:-2]
                else:
                    if self.redundancy != str(self.now)[:-2]:
                        self.redundancy = None
            self.check_time = self.now

            if self.p_order_active == False: # p 오더가 비활성중이고
                if self.position == None: #포지션이 없으면
                    entry_list = self.create_entry_list(percent=qty_percent)
                    self.entry_order(signal=SHORT,qty=entry_list[0]) #엔트리 진입
                    while True: #체결정보 리턴까지 대기
                        if self.standard_price == None:
                            await asyncio.sleep(0.25)
                        else:
                            break
                    self.get_position()
                    del entry_list[0]
                    if self.cycle == None:
                        self.cycle = 0
                    self.stage = 0 # 스테이지 0 입력
                else: #포지션이 있으면
                    if self.g_order_id == None: #g오더를 안했을 경우
                        self.avgprice = float(self.position[1]['entryPrice']) #현재진입평균가를 확인하고
                        op = self.avgprice + self.standard_price*scale_percent # 위쪽에 가격을 설정후
                        self.gw_order(signal=SHORT, order_price=op, qty=entry_list[0]) # gw 주문을 함
                    else:
                        if self.g_order_status == True: #gw주문이 체결되었을 경우에는
                            self.get_position() #포지션을 조회해서
                            self.avgprice = float(self.position[1]['entryPrice']) #현재진입평균가를 확인하고
                            del entry_list[0] #주문리스트 목록을 삭제해줌
                            self.stage += 1 #스테이지 단계 상승
                            self.g_order_id = None # 체결된 주문아이디 지워주고
                            self.g_order_status = False # 할일 끝냈으니 다시 false로 만듦

                    if self.price <= (float(self.position[1]['entryPrice']) - (float(self.position[1]['entryPrice'])*scale_percent)): #가격이 불타기 가격조건 달성하면
                        """
                        주문전 스테이지 확인하고 이미 마지막 스테이지인 경우트레일링 스탑 주문함
                        """
                        self.gf_order(signal=SHORT,qty=entry_list[0]) #불타기 주문함
                        while True: # 체결정보 리턴까지 대기
                            if self.last_order_price == None: 
                                await asyncio.sleep(0.25)
                            else:
                                break
                        del entry_list[0] #주문하고 바로 체결되니 리스트 지워주고
                        self.cancel_order(self.g_order_id) #gw오더 지워주고
                        self.get_position() #포지션을 조회해서
                        self.avgprice = float(self.position[1]['entryPrice']) #현재진입평균가를 확인하고
                        self.p_order_price = float(self.position[1]['entryPrice']) - (float(self.position[1]['entryPrice']) - self.last_order_price)/2
                        self.last_order_price = None
                        self.stage += 1
                        self.p_order_active = True

            elif self.p_order_active == True: # p 오더가 활성화 되고
                if self.p_order_price <= self.price: #가격이 조건을 달성하면
                    self.p_order(signal=LONG,qty=self.position['positionAmt']) #p 주문
                    while True: #체결정보 업데이트까지 대기
                        if self.p_order_status == False:
                            await asyncio.sleep(0.25)
                        else:
                            break
                    self.alrgo4_reset() # 모두 초기화
                    print('cycle done')
                    self.cycle += 1
                


    async def test(self):

        await asyncio.sleep(10)

        while True:
            self.gf_order(signal=SHORT,qty=0.001)
            await asyncio.sleep(0.1)




    async def run(self):
        tasks = [trader.alrgo4_admin(), trader.realtime_infomation()]
        result = await asyncio.gather(*tasks)
        print(result)

    async def test_run(self):
        tasks = [trader.test(), trader.realtime_infomation()]
        result = await asyncio.gather(*tasks)
        print(result)


if __name__ == "__main__":
    try:
        if not API_KEY or not API_SECRET:
            logging.error('Set API_KEY and API_SECRET')
        else:
            trader = Trader()
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            asyncio.run(trader.run())
    except Exception as e:
        logging.error(traceback.format_exc())