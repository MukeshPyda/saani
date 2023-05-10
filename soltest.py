
# https://fapi.binance.com/fapi/v1/ticker/price?symbol=FILUSDT
import requests
import time

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

from binance.client import Client
from binance.enums import *


class light_bot():
    price = 0.0
    request_client = None
    client_binance = None

    api_key = "api key"
    secret_key = "secret key"

    def __init__(self):
        self.request_client = RequestClient(
            api_key=self.api_key, secret_key=self.secret_key)
        self.client_binance = Client(
            api_key=self.api_key, api_secret=self.secret_key)
        print('Connected')

    def get_current_price(self):
        self.price = round(float(requests.get(
            'https://fapi.binance.com/fapi/v1/ticker/price?symbol=FILUSDT').json()['price']), 3)

    def __buy_limit(self, price_=0.0, quantity_=0.0, side_=""):
        self.client_binance.futures_create_order(symbol="FILUSDT", quantity=quantity_, price= round(float(price_), 3), type="LIMIT", side=side_, timeInForce="GTC", recvWindow=100000000)
        # PrintBasic.print_obj(result_buy)

    def __sell_limit(self, price_=0.0, quantity_=0.0, side_=""):
        self.client_binance.futures_create_order(symbol="FILUSDT", quantity=quantity_, price= round(float(price_), 3), type="LIMIT", side=side_, timeInForce="GTC", recvWindow=100000000)
        # PrintBasic.print_obj(result_buy)

    def __sell_market(self,quantity_=0.0):
        self.client_binance.futures_create_order(symbol="FILUSDT", quantity=quantity_, type="MARKET", side="SELL", recvWindow=100000000)

    def __buy_market(self,quantity_=0.0):
        self.client_binance.futures_create_order(symbol="FILUSDT", quantity=quantity_, type="MARKET", side="BUY", recvWindow=100000000)

    def __cancel_buy_lower(self, limit_ = 0.0, symbol_="FILUSDT"):
        list_orders = self.client_binance.futures_get_open_orders()
        for i in list_orders:
            if i['symbol'] == symbol_ and i['side'] == "BUY" and float(i['price']) < limit_:
                self.client_binance.futures_cancel_order(symbol=symbol_, orderId=i['orderId'])



    def __cancel_sell_higher(self, limit_, symbol_="FILUSDT"):
        list_orders = self.client_binance.futures_get_open_orders()
        for i in list_orders:
            if i['symbol'] == symbol_ and i['side'] == "SELL" and float(i['price']) > limit_:
                self.client_binance.futures_cancel_order(symbol=symbol_, orderId=i['orderId'])

    def __cancel_all(self):
        self.client_binance.futures_cancel_all_open_orders(symbol="FILUSDT", timestamp=time.time(), recvWindow=100000000)


    def __get_position(self, symbol="FILUSDT"):
        list = self.client_binance.futures_position_information(recvWindow=100000000)
        for i in list:
            if i['symbol'] == symbol:
                return round(float(i['unRealizedProfit']), 3)

    def __has_buy_orders(self, symbol="FILUSDT"):
        list_orders = self.client_binance.futures_get_open_orders()
        count = 0
        for i in list_orders:
            if i['symbol'] == symbol and i['side'] == "BUY":
                count += 1
        return count

    def __has_sell_orders(self, symbol="FILUSDT"):
        list_orders = self.client_binance.futures_get_open_orders()
        count = 0
        for i in list_orders:
            if i['symbol'] == symbol and i['side'] == "SELL":
                count += 1
        return count


    def __get_position(self, symbol="FILUSDT", parameter='unRealizedProfit'):
        # "notional" and "unRealizedProfit"
        list = self.client_binance.futures_position_information(recvWindow=100000000)
        for i in list:
            if i['symbol'] == symbol:
                return round(float(i[parameter]), 3)

    def preset(self, var=0, qty=0, limit_notional=4):
        stp = round(var/400, 3)
        grid = 3
        self.__cancel_all()
        newNotional = round(self.__get_position(parameter='notional')/self.price , 3)
        if newNotional < limit_notional:
            self.__buy_market(quantity_=qty*2)
        for gridNumber in range(1, grid+1):
            self.__buy_limit(price_=var-(gridNumber*stp), quantity_=qty, side_="BUY")
            self.__sell_limit(price_=var+(gridNumber*stp), quantity_=qty, side_="SELL")

    def bot(self, limit_notional=4):
        self.client_binance.futures_change_leverage(
            symbol="FILUSDT", leverage=20)

        self.get_current_price()
        var = self.price
        self.preset(var, qty=1)
        while True:
            try:
                stp = round(var/400, 3)
                shrinkstp= round(0.5*stp,3)
                qty = 1
                grid = 3
                self.get_current_price()
                pnl = self.__get_position(symbol="FILUSDT")
                newNotional = round(self.__get_position(parameter='notional')/self.price , 3)
                if newNotional < limit_notional:
                    self.__buy_market(quantity_=qty*2)

                time.sleep(0.4)
                if self.price-var > shrinkstp:
                    if self.__has_sell_orders() < grid:
                        var = round(var+stp, 3)
                        self.__buy_limit(price_=var-stp, quantity_=qty, side_="BUY")
                        self.__sell_limit(price_=var+grid*stp, quantity_=qty, side_="SELL")
                        self.__cancel_buy_lower(limit_=round(var-(grid+0.3)*stp, 3))
                        print("FIL Up")
                elif self.price-var < -shrinkstp:
                    if self.__has_buy_orders() < grid:
                        var = round(var-stp, 3) 
                        self.__sell_limit(price_=var+stp, quantity_=qty, side_="SELL")
                        self.__buy_limit(price_=var-grid*stp, quantity_=qty, side_="BUY")
                        self.__cancel_sell_higher(limit_=round(var+(grid+0.3)*stp, 3))
                        print("FIL down")
            except:
                time.sleep(2)
                continue


    def test(self):
        self.__sell_limit(price_=70.00, quantity_=0.2)
        print(self.client_binance.futures_get_open_orders()
              )



while True:
    try:
        obj = light_bot()
        obj.bot()
    
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
        except BaseException as error:
            print('An exception occurred: {}'.format(error))
