import requests
import time 
import pandas as pd
import os

class Data_parser:
    def __init__(self, base_url="https://api.binance.com", future_base_url="https://fapi.binance.com"):
        self.base_url = base_url
        self.future_base_url = future_base_url
        self.orderbook = {}
        self.open_interest = {}

    def make_request(self, endpoint, params={}):
        response = requests.get(self.base_url + endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def make_future_request(self, endpoint, params={}):
        response = requests.get(self.future_base_url + endpoint, params=params)
        response.raise_for_status()
        return response.json()

    def get_orderbook(self, symbol, limit=10):
        endpoint = "/api/v3/depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        return self.make_request(endpoint, params)
    
    def get_kline(self, symbol, interval="1m", limit=1):
        endpoint = "/api/v3/klines"
        params = {
            "symbol": symbol,
            "limit": limit,
            "interval":interval
        }
        return self.make_request(endpoint, params)
    
    def get_open_interest(self, symbol):
        endpoint = "/fapi/v1/openInterest"
        params = {"symbol": symbol}
        return self.make_future_request(endpoint, params)
    
if __name__ == "__main__":
    data_parser = Data_parser()

    symbol = 'BTCUSDT'

    starttime=time.time()
    while True:
        try:
            print("passthrough at ",time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
            
            orderbook_data = data_parser.get_orderbook(symbol)
            kline_data = data_parser.get_kline(symbol)
            open_interest = data_parser.get_open_interest(symbol)
            print(open_interest)

            bid_price = []
            bid_qty = []
            for bid in orderbook_data["bids"]:
                bid_price.append(float(bid[0]))
                bid_qty.append(float(bid[1]))

            ask_price = []
            ask_qty = []
            for ask in orderbook_data["asks"]:
                ask_price.append(float(ask[0]))
                ask_qty.append(float(ask[1]))

            data = {
                "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())),
                "bid": bid_price,
                "bid_qty": bid_qty,
                "ask": ask_price,
                "ask_qty": ask_qty,
                "open": float(kline_data[0][1]),
                "high": float(kline_data[0][2]),
                "low": float(kline_data[0][3]),
                "close": float(kline_data[0][4]),
                "volume": float(kline_data[0][5]),
                "open interest": open_interest["openInterest"]
            }

            df = pd.DataFrame([data])
            write_header = not os.path.exists("data.csv")
            df.to_csv("data.csv", mode='a', header=write_header, index=False)

            print("\n已存檔:", data)

            time.sleep(60 - ((time.time() - starttime) % 60.0))
        except KeyboardInterrupt:
            print('\n\nKeyboard exception received. Exiting.')
            break