import asyncio
import websockets
import json

async def main():
    url = "wss://stream.binance.com:9443/ws/btcusdt@depth5@100ms"
    async with websockets.connect(url) as ws:
        print("✅ Connected to Binance depth5 stream")
        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            bids = [(float(price), float(qty)) for price, qty in data["bids"]]
            asks = [(float(price), float(qty)) for price, qty in data["asks"]]

            best_bid = bids[0][0]
            best_ask = asks[0][0]
            spread = best_ask - best_bid
            mid_price = (best_bid + best_ask) / 2

            print("\n==== Order Book Top 5 ====")
            print("Bids:", bids)
            print("Asks:", asks)
            print(f"Best Bid: {best_bid}, Best Ask: {best_ask}")
            print(f"Spread: {spread}, Mid Price: {mid_price}")
            print("=" * 40)

asyncio.run(main())
# ==== Order Book Top 5 ====
# Bids: [(110538.98, 1.26628), (110538.97, 0.0007), (110538.83, 0.0001), (110538.4, 5e-05), (110537.89, 0.0001)]
# Asks: [(110538.99, 11.15438), (110539.0, 5e-05), (110539.14, 0.0001), (110539.17, 5e-05), (110539.24, 0.00044)]
# Best Bid: 110538.98, Best Ask: 110538.99
# Spread: 0.010000000009313226, Mid Price: 110538.985