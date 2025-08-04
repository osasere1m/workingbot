
#market maker

import ccxt

import time
import pandas as pd
import pandas_ta as ta
import time
import schedule
from pybit.unified_trading import HTTP

bybit = ccxt.bybit({
    'apiKey': '',
    'secret': '',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    }
})
session = HTTP(
    testnet=False,
    api_key="",
    api_secret="",
)
#bybit.set_sandbox_mode(True) # activates testnet mode
bybit.options["dafaultType"] = 'future'
def trading_bot():
    # Fetch historical OHLCV data for BTC/USD
    symbol = 'LINK/USDT'
    timeframe = '1h' # 1-hour candles
    limit = 200 # Number of candles to fetch

    ohlcv = bybit.fetch_ohlcv(symbol, timeframe, limit=limit)

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Calculate Higher Highs (HH) and Higher Lows (HL)
    df['HH'] = df['high'] > df['high'].shift(4)
    df['HL'] = df['low'] > df['low'].shift(4)

    # Calculate Lower Highs (LH) and Lower Lows (LL)
    #The shift function is used to compare the current high/low with the high/low 8 periods ago for HH/HL and 4 periods ago for LH/LL.
    df['LH'] = df['high'] < df['high'].shift(4)
    df['LL'] = df['low'] < df['low'].shift(4)

    # Determine the trend
    df['trend'] = 0 #'consolidating'
    df.loc[(df['HH'] & df['HL']), 'trend'] = 1 #uptrend'
    df.loc[(df['LH'] & df['LL']), 'trend'] = 2 #downtrend'

    #direction of trend with ma
     
    df['sma_50'] = ta.sma(df['close'], length=9)
    
    df['direction'] = df['sma_50'].tail(10).is_monotonic_increasing
    #Define the conditions for long and short trades
    
    df["long_condition"] = 1
    df.loc[(df['direction'] == True) & (df['trend'] == 1), "long_condition"] = 2  
    
    df["short_condition"] = 1
    df.loc[(df['direction'] == False) & (df['trend'] == 2), "short_condition"] = 2 
    print(df.tail(50))  


    # Print the last few rows to see the trend
    print(df.tail(50))
    for i, row in df.iterrows():
        positions = bybit.fetch_positions()
        print(positions)
        check_positions = [position for position in positions if 'LINK' in position['symbol']]
        symbol="LINKUSDT" 
        buyside = "Buy" 
        sellside="Sell"
        ob = session.get_orderbook(
            category="linear",
            symbol=symbol,
            ) 
        #print(ob)
        ask1 = ob['result']['a'][0][0]
        bid1 = ob['result']['b'][0][0]
        size = 0.3
        #first tp and bid price for buy trade
        point =0.25
        long_price1 = float(bid1)
        #print(long_price1)
        tp_point = point
        long_tp_cal= long_price1 + tp_point
        long_tp1 = round(long_tp_cal, 2)
        print(f"buy price --{long_price1} takeprofit price--{long_tp1}")

        #first tp and ask price for sell trade
        short_price = float(ask1)
        #print(short_price)
        point =0.22
        tp_point = point
        short_tp_cal= short_price - tp_point
        short_tp = round(short_tp_cal, 2)
        print(f"sell price --{short_price} takeprofit price--{short_tp}")



        #uptrend signal
        if df['long_condition'].iloc[-1] == 2:
            #check for open postions
            if not check_positions:
                print(f"NO open position for {symbol}")
                #fetch open order
                open_limit_order= len(session.get_open_orders(
                    category="linear",
                    symbol=symbol,
                    openOnly=0,
                    limit=1,
                ))==0
                #print(open_limit_order)

                #check for open limit order

                if not open_limit_order:
                    print(f"NO limit order for {symbol}")
                    print(f"create limit order for {symbol}") 
                    limit_order = (session.place_order(
                        category="linear",
                        symbol=symbol,
                        side=buyside,
                        orderType="Limit",
                        takeProfit=long_tp1,                        
                        price=bid1,
                        qty=size,
                        ))
                    print(f"long order placed: {limit_order}")
                    time.sleep(40)
                    break
                    
                else:
                    print("There is already an open limit order.")
                    open_limit_order= session.get_open_orders(
                        category="linear",
                        symbol=symbol,
                        openOnly=0,
                        limit=1,
                    )
                    #print(open_limit_order)
                    for item in open_limit_order['result']['list']:
                        side = item['side']
                        print(side)

                        # Check if the side is 'Buy' and if so, cancel the order
                        if side == 'Sell':
                            order_id = item['orderId']
                            cancel_order=session.cancel_order(
                                category="linear",
                                symbol=symbol,
                                orderId=order_id,
                            )
                            print(cancel_order)
                            time.sleep(10)
                            #create new  buy limit order
                            print(f"create limit buy order for {symbol}") 
                            limit_order = (session.place_order(
                                category="linear",
                                symbol=symbol,
                                side=buyside,
                                orderType="Limit",
                                takeProfit=long_tp1,                        
                                price=bid1,
                                qty=size,
                                ))
                            print(f"Long order placed: {limit_order}")
                            break
                        else:
                            print(f"same size as trend direction")

                            break
                
                    time.sleep(10)
                    break

            else:
                print(f"in position already") 
                for position in positions:
                    if abs(position['contracts']) > 0:

                        ds = position['id']
                        symbol = position['symbol']
                        
                        entryPrice = position['entryPrice']
                        amount = position['contracts']

                        

                        print(f"{symbol} and {entryPrice}, {amount}")

                        if position['unrealizedPnl'] is None or position['initialMargin'] is None:
                            print("Skipping position pnl due to value being zero")
                            continue

                        pnl = position['unrealizedPnl'] * 100

                        print(f"pnl {pnl} percent") 
                        print(f"Closing position for {symbol} with PnL: {pnl}%")
                    
                        if position['side'] == 'short':
                            pnl_side_buy = 'buy'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=pnl_side_buy,
                                
                                amount=amount,
                            )
                            if order:
                                print(f"Position closed: {order}")
                                time.sleep(10)
                                break
                        else:
                            print(f"same side as trend direction") 
                            break

                print(f"create limit order for {symbol}") 
                limit_order = session.place_order(
                    category="linear",
                    symbol=symbol,
                    side=buyside,
                    orderType="Limit",
                    takeProfit=long_tp1,                        
                    price=bid1,
                    qty=size,
                    )
                print(f"Long order placed: {limit_order}")
                #print(f"long order placed:")
                time.sleep(40)
                break
            
                
        #downtrend signal
        elif df['short_condition'].iloc[-1] == 2:
            print(f"In a downtrend ")
            #check for open postions
            if not check_positions:
                print(f"NO open position for {symbol}")
                #fetch open order
                open_limit_order= len(session.get_open_orders(
                    category="linear",
                    symbol=symbol,
                    openOnly=0,
                    limit=1,
                ))
                #print(open_limit_order)
                if not open_limit_order:
                    print(f"NO open order for {symbol}")
                    print(f"create limit order for {symbol}") 
                    limit_order = session.place_order(
                        category="linear",
                        symbol=symbol,
                        side=sellside,
                        orderType="Limit",
                        takeProfit=short_tp,                        
                        price=ask1,
                        qty=size,
                        )
                    print(f"Short order placed: {limit_order}")
                    
                    time.sleep(40)
                    break
                    
                else:
                    print("There is already an open limit order.")
                    open_limit_order= session.get_open_orders(
                        category="linear",
                        symbol=symbol,
                        openOnly=0,
                        limit=1,
                    )
                    for item in open_limit_order['result']['list']:
                        side = item['side']
                        print(side)

                        # Check if the side is 'Buy' and if so, cancel the order
                        if side == 'Buy':
                            order_id = item['orderId']
                            cancel_order=session.cancel_order(
                                category="linear",
                                symbol=symbol,
                                orderId=order_id,
                            )
                            print(cancel_order)
                            time.sleep(10)
                            print(f"create limit sell order for {symbol}") 
                            limit_order = session.place_order(
                                category="linear",
                                symbol=symbol,
                                side=sellside,
                                orderType="Limit",
                                takeProfit=short_tp,                        
                                price=ask1,
                                qty=size,
                                
                                )
                            print(f"Short order placed: {limit_order}")
                            time.sleep(20)
                            break
                        else:
                            print(f"open limit order--same side as trend direction")

                            break
                
                    time.sleep(10)
                    break

            else:
                print(f"in position already") 
                for position in positions:
                    if abs(position['contracts']) > 0:

                        ds = position['id']
                        symbol = position['symbol']
                        
                        entryPrice = position['entryPrice']
                        amount = position['contracts']

                        

                        print(f"{symbol} and {entryPrice}, {amount}")

                        if position['unrealizedPnl'] is None or position['initialMargin'] is None:
                            print("Skipping position pnl due to value being zero")
                            continue

                        pnl = position['unrealizedPnl'] * 100

                        print(f"pnl {pnl} percent") 
                        print(f"Closing position for {symbol} with PnL: {pnl}%")
                    
                        if position['side'] == 'long':
                            pnl_side_sell = 'sell'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=pnl_side_sell,
                                
                                amount=amount,
                            )
                            if order:
                                print(f"Position closed: {order}")
                                time.sleep(10)
                                print(f"create limit sell order for {symbol}") 
                                limit_order = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side=sellside,
                                    orderType="Limit",
                                    takeProfit=short_tp,                        
                                    price=ask1,
                                    qty=size,
                                    )
                                print(f"Short order placed: {limit_order}")
                                time.sleep(40)
                                break
                                
                        else:
                            print(f"same side as trend direction") 
                            break
                break
                
        
        else:
            print(f"trend is consolidating")
            if not check_positions:
                print(f"NO open position for {symbol}")
                #fetch open order
                open_limit_order= len(session.get_open_orders(
                    category="linear",
                    symbol=symbol,
                    openOnly=0,
                    limit=1,
                ))==0
                if not open_limit_order:
                    print(f"NO limit order for {symbol}")
                    
                    time.sleep(10)
                    break
                    
                else:
                    print("There is already an open limit order.")
                    open_limit_order= session.get_open_orders(
                        category="linear",
                        symbol=symbol,
                        openOnly=0,
                        limit=1,
                    )
                    #print(open_limit_order)
                    for item in open_limit_order['result']['list']:
                        side = item['side']
                        print(side)

                        # Check if the side is 'Buy' and if so, cancel the order
                        if side == 'Sell':
                            order_id = item['orderId']
                            cancel_order=session.cancel_order(
                                category="linear",
                                symbol=symbol,
                                orderId=order_id,
                            )
                            print(cancel_order)
                            
                            #create new  buy limit order
                            print(f"cancel order limit sell order for {symbol}") 
                            time.sleep(10)
                            break
                           
                        else:
                            print(f"same size as trend direction")
                            order_id = item['orderId']
                            cancel_order=session.cancel_order(
                                category="linear",
                                symbol=symbol,
                                orderId=order_id,
                            )
                            print(cancel_order)
                            time.sleep(10)
                            print(f"cancel order limit buy order for {symbol}") 
                            break
                    break

            else:
                print(f"in position already") 
                for position in positions:
                    if abs(position['contracts']) > 0:

                        ds = position['id']
                        symbol = position['symbol']
                        
                        entryPrice = position['entryPrice']
                        amount = position['contracts']

                        

                        print(f"{symbol} and {entryPrice}, {amount}")

                        if position['unrealizedPnl'] is None or position['initialMargin'] is None:
                            print("Skipping position pnl due to value being zero")
                            continue

                        pnl = position['unrealizedPnl'] * 100

                        print(f"pnl {pnl} percent") 
                        print(f"Closing position for {symbol} with PnL: {pnl}%")
                    
                        if position['side'] == 'long':
                            pnl_side_sell = 'sell'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=pnl_side_sell,
                                
                                amount=amount,
                            )
                            if order:
                                print(f"close open long position for {symbol}") 
                                time.sleep(10)
                                
                                break
                        else:
                            pnl_side_buy = 'buy'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=pnl_side_buy,
                                
                                amount=amount,
                            )
                            if order:
                                print(f"close open short position for {symbol}") 
                                time.sleep(10)
                                
                                break

                break

trading_bot()           

schedule.every(1).minutes.do(trading_bot)
# Call the trading_bot function every 2 minutes
while True:
    schedule.run_pending()
    time.sleep(20)          
