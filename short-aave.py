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
#load market
bybit.load_markets()

#get future account balance
def get_balance():
    params ={'type':'swap', 'code':'USDT'}
    account = bybit.fetch_balance(params)['USDT']['total']
    print(account)
get_balance()


# Step 3: Define the trading bot function

def trading_bot():
    
    #Fetch historical data
    symbol = 'AAVE/USDT'
    amount = 0.1 
    type = 'market'
    timeframe = '1h'
    limit = 300
    side = 'Sell'
    ohlcv = bybit.fetch_ohlcv(symbol, timeframe)

    # Convert the data into a pandas DataFrame for easy manipulation
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    print(df)
    # Step 5: Calculate technical indicators

    SMA_20 = df.ta.sma()
  
    df['support'] = df['close'].min()
    df['resistance']  = df['close'].max()

    #entry signal
   
   

    # Define the conditions for short trades
    df["short_condition"] = 1
    df.loc[(df["resistance"] == 2 ), "short_condition"] = 2


    print(df)
    


    
    try:
        # Check if there is an open trade position
        positions = bybit.fetch_positions()
        print(positions)
        check_positions = [position for position in positions if 'AAVE' in position['symbol']]
        #print(f"open position {positions}")
        

        
        if not check_positions:
            # Step 6: Implement the trading strategy
            for i, row in df.iterrows():

                 # Step 7: Check for signals and execute trades
                if df['short_condition'].iloc[-1] > 1:
                    order = (session.place_order(
                        category="linear",
                        symbol="AAVEUSDT",
                        side="Sell",
                        orderType="Market",
                        qty=0.1,
                    ))
                    
                    print(f"short order placed: {order}")
                    #print(f"long order placed:")
                    time.sleep(21600)
                    break

                   
                
                else:
                    print(f"checking for long signals")
                
                    time.sleep(120)
                    break
                        
                   
                    
        else:
            print("There is already an open position.")
            
            time.sleep(120)
            pass

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

