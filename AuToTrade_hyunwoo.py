import time
import pyupbit
import datetime
import numpy as np

access = "Yaw14TZSxUIeOtXHdRw7cyQO79yiCXkbNq0xlfSy"
secret = "Gzp8VOxnDwWtSLtvKA3FW50EpNTfhLUoH9QKELs2"

def get_target_price(ticker, k) :
    """변동성 돌파 전략으로 매수 목표가 조회"""
    df = pyupbit.get_ohlcv(ticker,  interval="minute60", count=2)
    target_price = df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    return target_price

def get_start_time(ticker) :
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker,  interval="minute60", count=1)
    start_time = df.index[0]
    return start_time

def get_ma6(ticker) :
    """6시간 이동 평균선 조회"""
    df = pyupbit.get_ohlcv(ticker,  interval="minute60", count=6)
    ma6 = df['close'].rolling(6).mean().iloc[-1]
    return ma6

def get_balance(ticker) :
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker) :
    """현재가 조회"""
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_ror(ticker, k) :
    """수익률 계산"""

    # OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
    df = pyupbit.get_ohlcv(coin, interval="minute60", count=2)

    # 변동폭 * k 계산, (고가 - 저가) * k값
    df['range'] = (df['high'] - df['low']) * k

    # target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
    df['target'] = df['open'] + df['range'].shift(1)

    # ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값)
    df['ror'] = np.where(df['high'] > df['target'],
                        df['close'] / df['target'],
                        1)
    return df.iloc[1]['ror']

def get_check_coin(ticker, k) :
    """거래가 활발한 코인인지 조회"""

    # OHLCV(open, high, low, close, volume)로 당일 시가, 고가, 저가, 종가, 거래량에 대한 데이터
    df = pyupbit.get_ohlcv(ticker, count=2)
    
    # 변동폭 * k 계산, (고가 - 저가) * k값
    df['range'] = (df['high'] - df['low']) * k
    
    # target(매수가), range 컬럼을 한칸씩 밑으로 내림(.shift(1))
    df['target'] = df['open'] + df['range'].shift(1)
    
    # ror(수익률), np.where(조건문, 참일때 값, 거짓일때 값)
    df['ror'] = np.where(df['high'] > df['target'],
                        df['close'] / df['target'],
                        1)

    if df.iloc[1]['ror'] >= 1.05 :
        return 1
    else :
        return 0
    
# 로그인
upbit = pyupbit.Upbit(access, secret)
print("AUTOTRADE START",get_balance("KRW"))

coin_name=pyupbit.get_tickers(fiat="KRW")

ch = 0 # 판매 상태 확인 0 : 코인 찾는중 1 : 코인 매수 함 2 : 코인 매도 함
k = 0.5 # 변동성을 구하기 위한 K
p = 1.01 # 이득봐야할 % 18-00시 까지 1% 00-17시 까지 0.6%
p_ch = 0

# 자동매매 시작
while True :
    try :

        now = datetime.datetime.now()
        start_time = now - datetime.timedelta(minutes=now.minute) - datetime.timedelta(seconds=now.second) - datetime.timedelta(microseconds=now.microsecond) + datetime.timedelta(minutes=3)
        end_time = now + datetime.timedelta(hours=1) - datetime.timedelta(minutes=now.minute) - datetime.timedelta(seconds=now.second) - datetime.timedelta(microseconds=now.microsecond)

        max_ror = 0 # 최대 수익률
        max_coin = None # 최대 수익률의 코인

        if now.hour > 0 and now.hour <= 17 :
            p = 1.006

        elif now.hour >= 18 and now.hour <= 24 :
            p = 1.01
        
        for coin in coin_name : # 현재 사기 가장 좋은 코인 고르기
            
            if coin == "KRW-SNT" :
                continue

            ror=get_ror(coin, k) # 코인 수익률 구하기

            time.sleep(0.006)

            if ror <= 1 or get_check_coin(coin, k) == 0 : # 수익률이 101% 이하 이거나 전날대비 5% 이하인 코인은 패스
                continue
            
            if max_ror < ror :
                max_ror = ror
                max_coin = coin

        if max_coin != None : # 조건에 맞는 코인 있을 때

            #print(max_coin,get_current_price(max_coin),get_target_price(max_coin, k),get_ma6(max_coin),max_ror,ch)

            if start_time < now < end_time - datetime.timedelta(minutes=3) :

                target_price = get_target_price(max_coin, k) # 목표 가격
                ma6 = get_ma6(max_coin) # 6시간 이동평균가격
                current_price = get_current_price(max_coin) # 현재 가격

                if target_price <= current_price and ma6 < current_price and ch == 0 :

                    money = get_balance("KRW")

                    if money > 5000 :

                        upbit.buy_market_order(max_coin, money - (money * 0.0005))
                        buy_coin = max_coin # 매수 코인의 이름
                        buy_coin_price = get_current_price(buy_coin) # 매수 코인의 가격
                        ch = 1 

                if ch == 1 :
                    
                    if p_ch == 0 :
                        if buy_coin_price * 0.97 > get_current_price(buy_coin) : # 3% 하락시 0.2% 수익
                            p = 1.002
                            p_ch = 1
                    else :
                        p = 1.002

                    if buy_coin_price * p <= get_current_price(buy_coin) : # 1% 이상 오르면 매도

                        coin_count = get_balance(buy_coin[4:])

                        if coin_count * get_current_price(buy_coin) > 5000 :

                            upbit.sell_market_order(buy_coin, coin_count)
                            ch = 2
                            p_ch = 0
                
            else :
                if ch == 1 :

                    coin_count = get_balance(buy_coin[4:])

                    if coin_count * get_current_price(buy_coin) > 5000 :
                        upbit.sell_market_order(buy_coin, coin_count)
                ch = 0
                p_ch = 0
        
        else : # 조건에 맞는 코인 없을 때
            #print("살 코인 없음")

            if start_time < now < end_time - datetime.timedelta(minutes=3) :
                if ch == 1 :

                    if p_ch == 0 :
                        if buy_coin_price * 0.97 > get_current_price(buy_coin) : # 3% 하락시 0.2% 수익
                            p = 1.002
                            p_ch = 1
                    else :
                        p = 1.002
                        
                    if buy_coin_price * p <= get_current_price(buy_coin) : # 1% 이상 오르면 매도

                        coin_count = get_balance(buy_coin[4:])

                        if coin_count * get_current_price(buy_coin) > 5000 :

                            upbit.sell_market_order(buy_coin, coin_count)
                            ch = 2
                            p_ch = 0
                    
            else :
                if ch == 1 :

                    coin_count = get_balance(buy_coin[4:])

                    if coin_count * get_current_price(buy_coin) > 5000 :
                        upbit.sell_market_order(buy_coin, coin_count)

                ch = 0
                p_ch = 0

        time.sleep(1)

    except Exception as e :
        print(e)
        time.sleep(1)