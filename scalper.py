import ccxt
import pandas as pd
#import pandas_ta as ta
import numpy as np
from scipy.signal import argrelextrema
import time
from datetime import datetime
from pybit.unified_trading import HTTP
import schedule
# Configuration


#PARAMETERS
SYMBOL = 'LINKUSDT'  # Using linear contract symbol
TIMEFRAME = '15m'
EMA_PERIOD = 100
SL_PIPS = 0.50
TP1_PIPS, TP2_PIPS, TP3_PIPS = 0.100, 0.150, 0.160
TP1_PERCENT, TP2_PERCENT, TP3_PERCENT = 50, 25, 25
LOT_SIZE = 0.4  
PIP_VALUE = 0.5 

session = HTTP(
    testnet=False,
    api_key="",
    api_secret="",
)
# Initialize Bybit exchange
bybit = ccxt.bybit({
    'apiKey': '',
    'secret': '',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    }
})
bybit.options["dafaultType"] = 'future'
#load market
bybit.load_markets()


def calculate_support_resistance(df, lookback=15):
    """Calculate support and resistance levels"""
    # Initialize columns
    for level in ['resistance_1', 'resistance_2', 'resistance_3', 'support_1', 'support_2', 'support_3']:
        if level not in df.columns:
            df[level] = np.nan
    
    # Find local maxima and minima
    highs = df['high'].values
    lows = df['low'].values
    
    # Resistance levels (peaks)
    resistance_idx = argrelextrema(highs, np.greater, order=lookback)[0]
    if len(resistance_idx) >= 3:
        df['resistance_1'] = highs[resistance_idx[-1]]
        df['resistance_2'] = highs[resistance_idx[-2]]
        df['resistance_3'] = highs[resistance_idx[-3]]
    
    
    # Support levels (troughs)
    support_idx = argrelextrema(lows, np.less, order=lookback)[0]
    if len(support_idx) >= 3:
        df['support_1'] = lows[support_idx[-1]]
        df['support_2'] = lows[support_idx[-2]]
        df['support_3'] = lows[support_idx[-3]]
    
    
    return df

def check_trading_conditions(df):
    """Check for trading signals"""
    current_close = df['close'].iloc[-1]
    prev_close = df['close'].iloc[-2]
    ema_value = df['ema'].iloc[-1]
    ema_slope = df['ema_slope'].iloc[-1]
    resistance_zone = [df['resistance_3'].iloc[-1]]
    support_zone = df['support_3'].iloc[-1]
                       
    print(df)
    # Get current market price
    ticker = session.get_tickers(category="linear", symbol=SYMBOL)['result']['list'][0]
    ask = float(ticker['ask1Price'])
    bid = float(ticker['bid1Price'])
    
     # CORRECTED CONDITION ASSIGNMENT - Now works for entire DataFrame
    df['Long_entry'] = (df['close'] > df['resistance_1']) & \
                        (df['open'] < df['resistance_1']) & \
                        (df['low'] < df['resistance_1']) & \
                       (df['close'] > df['ema']) & \
                        (df['ema'] > df['ema_200']) & \
                       (df['ema_slope'] > 15)
    
    df['Sell_entry'] = (df['close'] < df['support_1']) & \
                        (df['open'] > df['support_1']) & \
                        (df['high'] > df['support_1']) & \
                       (df['close'] < df['ema']) & \
                       (df['ema'] < df['ema_200']) & \
                       (df['ema_slope'] < -15)
    
    # Initialize condition columns
    df["Long_condition"] = 1
    df.loc[df['Long_entry'], "Long_condition"] = 2
    
    df["Sell_condition"] = 1
    df.loc[df['Sell_entry'], "Sell_condition"] = 2
    print(df)
    open_limit_order= len(session.get_open_orders(
        category="linear",
        symbol=SYMBOL,
        openOnly=0,
        limit=1,
    ))==0
    #print(open_limit_order)
    print(df)
    signals = []
    
    # Extract support/resistance levels
    resistance_levels = [x for x in [df['resistance_3'].iloc[-1], df['resistance_2'].iloc[-1]] if not np.isnan(x)]
    support_levels = [x for x in [df['support_3'].iloc[-1], df['support_2'].iloc[-1]] if not np.isnan(x)]
    

    if df['Long_condition'].iloc[-1] == 2:
        if not open_limit_order:
            print(f"NO limit order for {SYMBOL}")
            print(f"create Buy limit order for {SYMBOL}")
            try:
                stoploss_cal = (bid - SL_PIPS ) 
                stop_loss = stoploss_cal
                tp1 = round(bid + (TP1_PIPS ),3)
                tp2 = round(bid + (TP2_PIPS ),3)
                tp3 = round(bid + (TP3_PIPS ),3)
                # Uncomment for live trading
                session.place_order(
                    category="linear",
                    symbol=SYMBOL,
                    side="Buy",
                    orderType="Limit",
                    tpslMode="Partial",
                    takeProfit=tp1,        
                    qty=LOT_SIZE,
                    price=bid,
                    stopLoss=stop_loss,
                    
                )
                time.sleep(10)
                """
                session.place_order(
                    category="linear",
                    symbol=SYMBOL,
                    side="Buy",
                    orderType="Limit",
                    tpslMode="Partial",
                    takeProfit=tp2,        
                    qty=LOT_SIZE,
                    price=bid,
                    stopLoss=stop_loss,
                    
                )

                time.sleep(10)
                session.place_order(
                category="linear",
                symbol=SYMBOL,
                side="Buy",
                orderType="Limit",
                tpslMode="Partial",
                takeProfit=tp3,        
                qty=LOT_SIZE,
                price=bid,
                stopLoss=stop_loss,
                
                )
                """
            except Exception as e:
                print(f"Order placement failed: {e}")
        else:
            print("There is already an open limit order.")
            open_limit_order= session.get_open_orders(
                category="linear",
                symbol=SYMBOL,
                openOnly=0,
                limit=3,
            )
            print(open_limit_order)
            
            
    else:
        print("No valid Bullish breakout found")
        time.sleep(10)

    if df['Sell_condition'].iloc[-1] == 2:
        if not open_limit_order:
            print(f"NO limit order for {SYMBOL}")
            print(f"create Sell limit order for {SYMBOL}")
            try:
                stoploss_cal = round((ask + SL_PIPS ),3) 
                stop_loss = stoploss_cal
                tp1 = round(ask - (TP1_PIPS ),3)
                tp2 = round(ask - (TP2_PIPS ),3)
                tp3 = round(ask - (TP3_PIPS ),3)
                
                # Uncomment for live trading
                limitorder = session.place_order(
                    category="linear",
                    symbol=SYMBOL,
                    side="Sell",
                    orderType="Limit",
                    tpslMode="Partial",
                    takeProfit=tp1,        
                    qty=LOT_SIZE,
                    price=ask,
                    stopLoss=stop_loss,
                    
                )
                print(limitorder)
                time.sleep(10)
                """
                session.place_order(
                    category="linear",
                    symbol=SYMBOL,
                    side="Sell",
                    orderType="Limit",
                    tpslMode="Partial",
                    takeProfit=tp2,        
                    qty=LOT_SIZE,
                    price=ask,
                    stopLoss=stop_loss,
                    
                )

                time.sleep(10)
                session.place_order(
                    category="linear",
                    symbol=SYMBOL,
                    side="Sell",
                    orderType="Limit",
                    tpslMode="Partial",
                    takeProfit=tp3,        
                    qty=LOT_SIZE,
                    price=ask,
                    stopLoss=stop_loss,
                    
                )
                """
            except Exception as e:
                print(f"Order placement failed: {e}")
        else:
            print("There is already an open limit order.")
            open_limit_order= session.get_open_orders(
                category="linear",
                symbol=SYMBOL,
                openOnly=0,
                limit=3,
            )
            #print(open_limit_order)
    else:
        print("No valid Bearish breakout found")
        time.sleep(10)
   

def print_status(df):
    """Print current market status"""
    print(f"\n{datetime.now()} - Market Status:")
    print(f"Price: {df['close'].iloc[-1]} | EMA: {df['ema'].iloc[-1]}")
    print(f"Support: {df['support_1'].iloc[-1]},{df['support_2'].iloc[-1]} | Resistance: {df['resistance_1'].iloc[-1]}, {df['resistance_2'].iloc[-2]}")
    print(f"EMA Slope: {df['ema_slope'].iloc[-1]:.2f} degree")

def trading_system():
    """Complete trading system with pybit API"""
    while True:
        try:
            # 1. Check existing positions with proper error handling
            try:
                positions_response = session.get_positions(category="linear", symbol=SYMBOL)
                if positions_response and 'result' in positions_response and 'list' in positions_response['result']:
                    positions = positions_response['result']['list']
                    if positions and float(positions[0].get('size', 0)) > 0:
                        pos = positions[0]
                        print(f"\nExisting position found:")
                        print(f"Side: {pos.get('side')}, Size: {pos.get('size')}, Entry: {pos.get('avgPrice')}")
                    else:
                        print(f"\nNo open positions for {SYMBOL}")
                else:
                    print("\nFailed to get positions data")
                    positions = []
            except Exception as e:
                print(f"Error checking positions: {e}")
                positions = []

            # 2. Fetch and prepare data
            try:
                ohlcv = bybit.fetch_ohlcv(symbol=SYMBOL, timeframe=TIMEFRAME, limit=400)
                df = pd.DataFrame(ohlcv, columns=['Timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
                df.set_index('Timestamp', inplace=True)
            except Exception as e:
                print(f"Error fetching OHLCV data: {e}")
                time.sleep(60)
                continue

            # 3. Calculate indicators
            try:
                #df['ema'] = ta.ema(df['close'], length=EMA_PERIOD)
                df['ema'] = df['close'].ewm(span=EMA_PERIOD, adjust=False).mean()
                df['ema_200'] = df['close'].ewm(span=200, adjust=False).mean()
                df['ema_slope'] = df['ema'].diff() * 10000
            except Exception as e:
                print(f"Error calculating indicators: {e}")
                time.sleep(60)
                continue

            # 4. Calculate support/resistance
            try:
                df = calculate_support_resistance(df)
            except Exception as e:
                print(f"Error calculating support/resistance: {e}")
                time.sleep(60)
                continue

            # 5. Check trading conditions (only if no existing position)
            if not positions or float(positions[0].get('size', 0)) == 0:
                try:
                    df = check_trading_conditions(df)
                except Exception as e:
                    print(f"Error checking trading conditions: {e}")

            # 7. Check for breakeven opportunities
            try:
                move_to_breakeven()
            except Exception as e:
                print(f"Error in breakeven check: {e}")

            # 8. Display status
            try:
                print_status(df)
            except Exception as e:
                print(f"Error printing status: {e}")

            time.sleep(60)
            break
            
        except Exception as e:
            print(f"System error: {e}")
            time.sleep(60)
            
def execute_trades(signals, df):
    """Execute trades using pybit API"""
    


    for signal in signals:
        try:
            print(f"\nExecuting {signal['type']} signal:")
            print(f"Price: {signal['price']}, SL: {signal['stop_loss']}")
            
            for i, (TP1_PIPS,TP2_PIPS,TP3_PIPS, lot) in enumerate(zip(signal['take_profits'], signal['lots']), 1):
                print(f"  Part {i}: {lot} contracts | TP: {TP1_PIPS,TP2_PIPS,TP3_PIPS}")
                # Check for buy signal on most recent candle only
                

            print(signal['message'])
            
        except Exception as e:
            print(f"Trade execution failed: {e}")

def move_to_breakeven():
    """Move stop loss to breakeven when conditions are met"""
    try:
        # Get positions from both APIs for redundancy
        positions = bybit.fetch_positions()
        
        
        # Check positions from both sources
        check_positions = [position for position in positions if 'LINK' in position['symbol']]

        #check_positions = [p for p in bybit_positions if SYMBOL.split('/')[0] in p['symbol']]
        
        if check_positions:
            print(" positions found ") 
            session_positions = session.get_positions(category="linear", symbol=SYMBOL)
            #print(session_positions)
            # Get detailed position info from session API
            if 'result' in session_positions and 'list' in session_positions['result']:
                positions = session_positions['result']['list']
                
                for position in positions:  # Directly iterate through the list
                    if position['symbol'] == SYMBOL and float(position['size']) > 0:
                        side = position['side']
                        current_size = float(position['size'])
                        entry_price = float(position['avgPrice'])
                        pos_stoploss = float(position.get('stopLoss', 0))
                        
                        print(f"Position found: {side}, Size: {current_size}, Entry: {entry_price}, SL: {pos_stoploss}")

                        # Calculate total original size (3 orders)
                        #totalsize = LOT_SIZE * 3 
                        totalsize = LOT_SIZE 

                        # Check if position is <= 50% of original size
                        if current_size < totalsize:
                            # Calculate breakeven with 1 pip buffer
                            if side == 'Buy':
                                if entry_price > pos_stoploss:  
                                    new_sl = round(entry_price + (0.02 * PIP_VALUE), 3)  # 1 pip buffer
                                    print(f"\nMoving to breakeven: {SYMBOL} {side}")
                                    print(f"Original Entry: {entry_price} | New SL: {new_sl}")
                                    
                                    # Uncomment to execute live
                                    session.set_trading_stop(
                                         category="linear",
                                         symbol=SYMBOL,
                                         stopLoss=new_sl,
                                         positionIdx=0
                                     )
                                else:
                                    print("SL already at or above breakeven")
                            
                            elif side == 'Sell':
                                if entry_price < pos_stoploss: 
                                    new_sl = round(entry_price - (0.01 * PIP_VALUE), 3)
                                    print(f"\nMoving to breakeven: {SYMBOL} {side}")
                                    print(f"Original Entry: {entry_price} | New SL: {new_sl}")
                                    
                                    # Uncomment to execute live
                                    session.set_trading_stop(
                                        category="linear",
                                        symbol=SYMBOL,
                                        stopLoss=new_sl,
                                        positionIdx=0
                                    )
                                else:
                                    print("SL already at or below breakeven")
                        
                                    time.sleep(1)  # Small delay between position checks
                    else:
                        print("Position size does meet requirement")
                        return    
            pass
        else: 
            print("No positions found for breakeven adjustment")
            
    except Exception as e:
        print(f"Breakeven move failed: {str(e)}")


def run_scheduled_job():
    """Wrapper function for scheduled execution"""
    print(f"\n{datetime.now()} - Running scheduled trading system check")
    trading_system()

if __name__ == "__main__":
    print("Starting trading system with pybit API...")
    # Schedule the job to run every 15 minutes
    schedule.every(15).minutes.do(run_scheduled_job)
    
    # Run immediately on startup
    run_scheduled_job()
    
    # Keep the program running and execute scheduled jobs
    while True:
        schedule.run_pending()
        time.sleep(1)  # Sleep to reduce CPU usage



