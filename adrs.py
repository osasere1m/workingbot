#fixed support and resistance level
#entry price close below a support and price above resistance level


import schedule
import ccxt
import time
import pandas as pd
import pandas_ta as ta
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

#bybit future contract enable
bybit.options["dafaultType"] = 'future'
#load market
bybit.load_markets()
  

def trading_bot():
     
    
    try:

        positions = bybit.fetch_positions()
        print(positions)
        check_positions = [position for position in positions if 'LTC' in position['symbol']]
        
        
        if not check_positions:
            # Step 6: Implement the trading strategy
            symbol = 'LTC/USDT'
            amount = 0.1 
            type = 'market'
            hft_timeframe = '4h'
            hft_limit = 100

            hft_ohlcv = bybit.fetch_ohlcv(symbol, timeframe=hft_timeframe, limit=hft_limit)
            

            # Convert the data into a pandas DataFrame for easy manipulation
            hft_df = pd.DataFrame(hft_ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            hft_df['Timestamp'] = pd.to_datetime(hft_df['Timestamp'], unit='ms')
            hft_df.set_index('Timestamp', inplace=True)
            print(hft_df.tail)
            # Calculate technical indicators

            # Calculate SMAs with periods of 20 and 50

            hft_df['cross'] = hft_df['Close'] > hft_df.ta.sma(length=20, append=True) 
            print(hft_df)

            for i, row in hft_df.iterrows():

                if hft_df['cross'].iloc[-1] == True:
                    print(f"Price over SMA 20 4hr--- UPTREND")
                    timeframe='5m'
                    limit= 50
                    ohlcv_1h = bybit.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

                    df_1 = pd.DataFrame(ohlcv_1h, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df_1['Timestamp'] = pd.to_datetime(df_1['Timestamp'], unit='ms')
                    #df.set_index('Timestamp', inplace=True)

                    print(df_1)
                    df_1['support'] = df_1['close'].min()
                    df_1['resistance']  = df_1['close'].max()
                    print(df_1)
                    df_1["long_condition"] = 1
                    df_1.loc[(df_1['close'] <= df_1['support']), "long_condition"] = 2  # at support
                            
                    
                    if df_1['long_condition'].iloc[-1] == 2:
                        order = (session.place_order(
                            category="linear",
                            symbol="LTCUSDT",
                            side="Buy",
                            orderType="Market",
                            qty=0.2,
                        ))
                        
                        
                        print(f"long order placed: {order}")
                        #print(f"long order placed:")
                        time.sleep(21600)
                        break
                        
                    
                    else:
                        print(f"price is not at support")
                        
                        time.sleep(60)
                        break
                else:
                    print(f"Price under SMA 20 4hr- DOWNTREND")
                    timeframe='5m'
                    limit= 100
                    ohlcv_1h = bybit.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

                    df_1 = pd.DataFrame(ohlcv_1h, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
                    df_1['Timestamp'] = pd.to_datetime(df_1['Timestamp'], unit='ms')
                    #df.set_index('Timestamp', inplace=True)

                    print(df_1)
                    df_1['support'] = df_1['close'].min()
                    df_1['resistance']  = df_1['close'].max()
                    print(df_1)
                    df_1["short_condition"] = 1
                    df_1.loc[(df_1['close'] >= df_1['resistance']), "short_condition"] = 2  # at support
                            
                    
                    if df_1['short_condition'].iloc[-1] == 2:
                        order = (session.place_order(
                            category="linear",
                            symbol="LTCUSDT",
                            side="Sell",
                            orderType="Market",
                            qty=0.1,

                        ))
                        
                        
                        print(f"short order placed: {order}")
                        #print(f"long order placed:")
                        time.sleep(21600)
                        break
                        
                    
                    else:
                        print(f"price is not at resistance")
                        
                        time.sleep(10)
                        break
                    
                    
                    
        else:
            print("There is already an open position.")
            
            
                
            time.sleep(20)

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
    



