import ccxt
import pandas as pd
import pandas_ta as ta
import time
import schedule
import numpy as np
from scipy.signal import argrelextrema
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
    side= 'Buy'
    limit = 200
    ohlcv = bybit.fetch_ohlcv(symbol, timeframe)

    # Convert the data into a pandas DataFrame for easy manipulation
    df = pd.DataFrame(ohlcv, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
    df.set_index('Timestamp', inplace=True)
    print(df)
    # Step 5: Calculate technical indicators

    #df.ta.ema(length=20, append=True)
  
    

    WINDOW = 10 

    df['min'] = df.iloc[argrelextrema(df['Close'].values, np.less_equal, order=WINDOW)[0]]['Close']
    df['max'] = df.iloc[argrelextrema(df['Close'].values, np.greater_equal, order=WINDOW)[0]]['Close']
    print(df)

    #entry signal
    df["support"] = 0

    df.loc[(df['min'] < 0), "support" ]= 1 #not at support
    df.loc[(df['min'] > 1), "support" ]= 2 #at support'
    print(df)
    df["resistance"] = 0

    df.loc[(df['max'] < 0), "resistance" ]= 1 #not at resistance
    df.loc[(df['max'] > 1), "resistance" ]= 2 #at resistance
    print(df)
   
    # Define the conditions for long trades
    df["long_condition"] = 1
    df.loc[(df["support"] == 2 ), "long_condition"] = 2

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
                if df['long_condition'].iloc[-1] > 1:
                    order =bybit.create_market_order(symbol, side, amount)
                    
                    
                    print(f"long order placed: {order}")
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

