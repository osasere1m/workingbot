#fixed support and resistance level
#entry price close below a support and price above resistance level


import schedule
import ccxt
import time
import pandas as pd
import pandas_ta as ta
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
#load market
bybit.load_markets()
  

def trading_bot():
    
    #Step 4: Fetch historical data
    symbol = 'LTC/USDT'
    limit= 200 
    timeframe='15m'
    ohlcv = bybit.fetch_ohlcv(symbol, timeframe, limit=limit)
    
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    #df.set_index('Timestamp', inplace=True)

    print(df)
    # support and resistance detection
    
    df['support'] = df['close'].min()
    df['support_2'] = df['close'].quantile(0.15)  # Optional: Add additional support levels
    df['resistance']  = df['close'].max()
    df['resistance_2'] = df['close'].quantile(0.85)  # Optional: Add additional resistance levels

    
    print(df.tail(50))
    df.ta.rsi(length=14, append=True)
   
    #SMA crossover for HFT directional bias
    
    print(df)

    #Define the conditions for long and short trades
    df["long_condition"] = 1
    df.loc[(df['close'] < df['support']), "long_condition"] = 2  # at support
    
    df["short_condition"] = 1
    df.loc[(df['close'] > df['resistance']), "short_condition"] = 2  # at support

    print(df)

    
    


    
    
    try:

        positions = bybit.fetch_positions()
        #print(positions)
        check_positions = [position for position in positions if 'LTC' in position['symbol']]
        
        
        if not check_positions:
            # Step 6: Implement the trading strategy
            for i, row in df.iterrows():
                
                
                if df['long_condition'].iloc[-1] == 2:
                    if df['RS1_14'].iloc[-1] < 30:
                        order = (session.place_order(
                            category="linear",
                            symbol="LTCUSDT",
                            side="Buy",
                            orderType="Market",
                            qty=0.1,
                        ))
                        
                        
                        print(f"long order placed: {order}")
                        #print(f"long order placed:")
                        time.sleep(60)
                        break
                    else:
                        print(f"Long condition not met RSI:{df['RS1_14']}")

                elif df['short_condition'].iloc[-1] == 2:
                    if df['RS1_14'].iloc[-1] < 27.9:
                        order = (session.place_order(
                            category="linear",
                            symbol="LTCUSDT",
                            side="Sell",
                            orderType="Market",
                            qty=0.1,
                        ))
                        
                        
                        print(f"long order placed: {order}")
                        #print(f"long order placed:")
                        time.sleep(60)
                        break
                    else:
                        print(f"Short condition not met RSI:{df['RS1_14']}")   
                   
                else:
                    print(f"checking for signals")
                    
                    time.sleep(60)
                    break
                    
                    
                    
        else:
            print("There is already an open position.")
            
            
                
            time.sleep(30)

    except ccxt.RequestTimeout as e:
        print(f"A request timeout occurred: {e}")
        # Handle request timeout error

    except ccxt.AuthenticationError as e:
        print(f"An authentication error occurred: {e}")
        # Handle authentication error

    except ccxt.ExchangeError as e:
        print(f"An exchange error occurred: {e}")
        # Handle exchange error

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Handle all other unexpected errors
# Run the trading_bot function
trading_bot()

schedule.every(1).minutes.do(trading_bot)
# Call the trading_bot function every 2 minutes
while True:
    schedule.run_pending()
    time.sleep(20)
    



