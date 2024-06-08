import ccxt
import time
import schedule
import time


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
bybit.options["dafaultType"] = 'future'


def get_balance():
    try:
        params ={'type':'swap', 'code':'USDT'}
        account = bybit.fetch_balance(params)['USDT']['total']
        print(account)
    except ccxt.RequestTimeout as e:
        print(f"A request timeout occurred: {e}")
    except ccxt.AuthenticationError as e:
        print(f"An authentication error occurred: {e}")
    except ccxt.ExchangeError as e:
        print(f"An exchange error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

get_balance()

def kill_switch():
    try:
        positions = bybit.fetch_positions()
        print(f"{positions}information")
        

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
                #10 x leverage= tp =1.02 and sl=0.71
        

                if pnl <= -14 or pnl >= 20:
                    print(f"Closing position for {symbol} with PnL: {pnl}%")
                
                    if position['side'] == 'short':
                        side = 'buy'
                        order = bybit.create_market_order(
                            
                            symbol=symbol,
                            side=side,
                            
                            amount=amount,
                        )
                        if order:
                            print(f"Position closed: {order}")
                            time.sleep(20)
                            break
                    else:
                        side = 'sell'
                        order = bybit.create_market_order(
                            
                            symbol=symbol,
                            side=side,
                            
                            amount=amount,
                        )
                        if order:
                            print(f"Position closed: {order}")
                            time.sleep(20)
                            break
                else:
                    pass
            else:
                print("There is no open position.")
                

    except ccxt.RequestTimeout as e:
        print(f"A request timeout occurred: {e}")
    except ccxt.AuthenticationError as e:
        print(f"An authentication error occurred: {e}")
    except ccxt.ExchangeError as e:
        print(f"An exchange error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Run the kill switch function
kill_switch()

#schedule.every(20).seconds.do(kill_switch)
schedule.every(1).minutes.do(kill_switch)
# Call the trading_bot function every 1 minutes
while True:
    schedule.run_pending()

    time.sleep(10)
    



