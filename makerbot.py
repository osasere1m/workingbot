
import ccxt
import pandas as pd
import pandas_ta as ta 
import time
import schedule
from pybit.unified_trading import HTTP

bybit = ccxt.bybit({
    'apiKey': 'LQLW7aAhcalaYMAiUe',
    'secret': 'X02KF8x2VVXuXDQmoWAd8TCXx3dS7M7fAaKD',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    }
})

session = HTTP(
    testnet=False,
    api_key="LQLW7aAhcalaYMAiUe",
    api_secret="X02KF8x2VVXuXDQmoWAd8TCXx3dS7M7fAaKD",
)

#bybit.set_sandbox_mode(True) # activates testnet mode
#bybit future contract enable
bybit.options["dafaultType"] = 'future'
bybit.load_markets()
def get_balance():
    params ={'type':'swap', 'code':'USDT'}
    account = bybit.fetch_balance(params)['USDT']['total']
    print(account)
get_balance()

#Step 4: Fetch historical data

# Step 5: Calculate technical indicators




def trading_bot():
    symbol = 'LINK/USDT'

    timeframe = '4h'
    #limit = 500
    ohlcv = bybit.fetch_ohlcv(symbol, timeframe)


    # Convert the data into a pandas DataFrame for easy manipulation
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    # Calculate Higher Highs (HH) and Higher Lows (HL)
    df['HH'] = df['high'] > df['high'].shift(4)
    df['HL'] = df['low'] > df['low'].shift(4)

    # Calculate Lower Highs (LH) and Lower Lows (LL)
    #The shift function is used to compare the current high/low with the high/low 8 periods ago for HH/HL and 4 periods ago for LH/LL.
    df['LH'] = df['high'] < df['high'].shift(4)
    df['LL'] = df['low'] < df['low'].shift(4)
    df['SMA_10']= ta.sma(df['close'], length=10)


    # Determine the trend
    df['trend'] = 0 #consolidating
    df.loc[(df['HH'] & df['HL']), 'trend'] = 1 #uptrend'
    df.loc[(df['LH'] & df['LL']), 'trend'] = 2 #downtrend'

    # Print the last few rows to see the trend
    print(df.tail(50))
    df["signal"] = 0
    df.loc[(df['close'] > df['SMA_10']) , "signal"] = 1 # buy
    df.loc[(df['close'] < df['SMA_10']) , "signal"] = 2 # sell
    
        
        
    try:
        
        positions = bybit.fetch_positions()

        check_positions = [position for position in positions if 'LINK' in position['symbol']]
        print(f"open position {positions}")
        
        #check open order
        if not check_positions:

            for i, row in df.iterrows():

                #check open order
                

                # Step 6: Implement the trading strategy
                
                
                
                if df['signal'].iloc[-1] ==1 :
                    print(f"PRICE CLOSE ABOVE SMA 10--BULLISH")
                    if df['trend'].iloc[-1] == 1:
                    
                        order = (session.place_order(
                            category="linear",
                            symbol=symbol,
                            side="Buy",
                            orderType="Market",
                            qty=0.2,
                            
                        ))
                        print(f"three long order placed:{order}")
                        time.sleep(43200)
                        break
                    else:
                        print(f"ENTRY CONDITION NOT MEET FOR BUY")
                else :
                    print(f"PRICE CLOSE BELOW SMA 10--BEARISH")
                    if df['trend'].iloc[-1] == 2:
                    
                        order = (session.place_order(
                            category="linear",
                            symbol=symbol,
                            side="Sell",
                            orderType="Market",
                            qty=0.2,
                        ))
                        
                        print(f"short order placed: {order}")
                        time.sleep(43200)
                        break
                    else:
                        print(f"ENTRY CONDITION NOT MEET FOR SEll")
            
            
        else:
            print("There is already an open position")
            
            time.sleep(60)
            pass

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Handle all other unexpected errors
trading_bot()
schedule.every(1).minutes.do(trading_bot)
# Call the trading_bot function every 2 minutes
while True:
    schedule.run_pending()
    time.sleep(20)                       
                    
                