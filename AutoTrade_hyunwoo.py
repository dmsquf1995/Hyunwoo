
import builtins
from re import T
import time
import pyupbit
import datetime
import numpy as np

access = "xtmFHwV0ZRUDR4OozvK19hVcG56S0V4wkTj6UZcZ"
secret = "421eW4p4aG8cSAn4Mk2e1Syf7BSTxwsr8p1ktNQh"

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker) :
    """ 잔고 조회 """
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0

def get_current_price(ticker) :
    """ 현재가 조회 """
    return pyupbit.get_orderbook(tickers=ticker)[0]["orderbook_units"][0]["ask_price"]

def get_open_price(ticker) :
    """ 시가 조회 """
    df = pyupbit.get_ohlcv(ticker, count=1)
    return df.iloc[0]['open']

def get_high_price(ticker) :
    """ 고가 조회 """
    df = pyupbit.get_ohlcv(ticker, count=1)
    return df.iloc[0]['high']

def get_target_price(ticker, k) :
    """ 매수 목표가 조회 """
    df = pyupbit.get_ohlcv(ticker, count=1)
    return df.iloc[0]['open'] * k # 시가의 k %


'''
p % 수익, 하루에 한 번 매수, 9시 30분 부터 시작, k % +- 0.5 %의 코인 매수, 매수가 -5 %가 되면 매도
'''

# 로그인
upbit = pyupbit.Upbit(access, secret)

coin_name = pyupbit.get_tickers(fiat="KRW")

ch = 0 # 판매 상태 확인 0 : 코인 찾는 중 1 : 코인 매수 함 2 : 코인 매도 함
buy_coin = None # 매수한 코인
p = 1.02 # 수익률
k = 0.95 # 시가의 95 %

while True : # 9시까지 거래 금지
    now = datetime.datetime.now()
    start_time = get_start_time("KRW-BTC")
    end_time = start_time + datetime.timedelta(days=1)

    if now >= end_time - datetime.timedelta(minutes=2) :
        if ch == 1 :
            coin_count = get_balance(buy_coin[4:])

            if coin_count * get_current_price(buy_coin) > 5000 :
                upbit.sell_market_order(buy_coin, coin_count)
                buy_coin = None
                ch = 0
        break
    print("아직 9시가 아닙니다")

    time.sleep(60)
    
print("AUTOTRADE START",get_balance("KRW") - 411651)

money = get_balance("KRW") - 411651

# 자동매매 시작
while True :
    try :

        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC") + datetime.timedelta(minutes = 30)
        end_time = start_time + datetime.timedelta(days = 1)

        if buy_coin == None : # 코인을 사지 않았을 때

            if start_time < now < end_time - datetime.timedelta(minutes = 2) :
                #print(datetime.datetime.now())
                for coin in coin_name : # 현재 사기 가장 좋은 코인 고르기

                    target_price = get_target_price(coin, k - 0.005) # 목표 가격 - 0.05%
                    target_price2 = get_target_price(coin, k + 0.005) # 목표 가격 + 0.05%
                    current_price = get_current_price(coin) # 현재 가격
                    open_price = get_open_price(coin) # 시가
                    high_price = get_high_price(coin) # 고가

                    print(format(coin, " >10s"), "   현재가 : %11.2f"%current_price, "   목표가 : %11.2f, %11.2f"%(target_price,target_price2), "   시가 : %11.2f"%open_price,"   고가 : %11.2f"%high_price)
                    
                    if target_price <= current_price and target_price2 >= current_price and ch == 0 and open_price * 1.05 > high_price :

                        money = get_balance("KRW") - 411651

                        if money > 5000 :

                            upbit.buy_market_order(coin, money - (money * 0.0005))
                            buy_coin = coin # 매수 코인의 이름
                            buy_coin_price = get_current_price(coin) # 매수 코인의 가격
                            ch = 1
                            break

        else : # 코인을 샀을 때
            
            print(buy_coin, "   현재가 :", get_current_price(buy_coin), "   매수가 : ",buy_coin_price, "    목표 수익가 : ",buy_coin_price*p)

            if start_time < now < end_time - datetime.timedelta(minutes = 2) :

                if ch == 1 :

                    if buy_coin_price * p <= get_current_price(buy_coin) or buy_coin_price * 0.95 >= get_current_price(buy_coin) : # p % 이상 오르면 매도 or 매수가 -5 %가 되면 매도

                        coin_count = get_balance(buy_coin[4:])

                        if coin_count * get_current_price(buy_coin) > 5000 :
                            upbit.sell_market_order(buy_coin, coin_count)
                            buy_coin = None
                            ch = 2

            else :

                if ch == 1 :

                    coin_count = get_balance(buy_coin[4:])

                    if coin_count * get_current_price(buy_coin) > 5000 :
                        upbit.sell_market_order(buy_coin, coin_count)

                buy_coin = None
                ch = 0

        #time.sleep(0.01)

    except Exception as e :
        print(e)
        #time.sleep(0.01)
