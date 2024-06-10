import ccxt
import schedule


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
        #print(f"{positions}information")
        if positions:
            positions = bybit.fetch_positions()
    
            position_balances = [item['info']['positionBalance'] for item in positions]

            # Print the filtered position balances
            for balance in position_balances:
                balance= balance
            #print(positionBalance)
            for position in positions:
                if abs(position['contracts']) > 0:

                    ds = position['id']
                    symbol = position['symbol']
                    entryPrice = position['entryPrice']
                    amount = position['contracts']
                    markPrice= position['markPrice']
                    positionBalance = float(balance)
                    print(f"{symbol} and entryPrice:{entryPrice}, amount:{amount}")

                    if position['unrealizedPnl'] is None or position['initialMargin'] is None:
                        print("Skipping position pnl due to value being zero")
                        continue

                    
            
                    if position['side'] == 'long':
                        pnl_cal = float((markPrice - entryPrice)* amount)
                        pnl_usd= round(pnl_cal, 3)
                        pnl_divide= float((pnl_usd/positionBalance)*100)
                        pnl_round = round(pnl_divide, 3)
                        ROI = pnl_round
                        print(f"Long position: pnlUSD: {pnl_usd} and ROI:{pnl_round} percent")
                        
                        
                    else:
                        pnl_cal = float((entryPrice - markPrice)* amount)
                        pnl_usd= round(pnl_cal,3)
                        pnl_divide= float((pnl_usd/positionBalance)*100)
                        pnl_round = round(pnl_divide, 3)
                        ROI = pnl_round
                        print(f"Short Postion: pnlUSD: {pnl_usd} and ROI:{pnl_round} percent")
                        


                    if ROI <= -13 or ROI >= 20:
                        print(f"Closing position for {symbol} with PnL: {ROI}%")
                    
                        if position['side'] == 'short':
                            side = 'buy'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=side,
                                
                                amount=amount,
                            )
                            
                            break
                        else:
                            side = 'sell'
                            order = bybit.create_market_order(
                                
                                symbol=symbol,
                                side=side,
                                
                                amount=amount,
                            )
                            
                            break
                    else:
                        pass
        else:
            print("There is no open position.")
            pass
                

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
schedule.every(20).seconds.do(kill_switch)
# Call the trading_bot function every 2 minutes
while True:
    schedule.run_pending()

    #time.sleep(10)
    



