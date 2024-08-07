from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv
from functools import partial
import concurrent.futures
import pandas_ta as ta
import pandas as pd
import os

load_dotenv()
testnet_api_key = os.getenv('testnet_api_key')
testnet_api_secret_key = os.getenv('testnet_api_secret_key')

class WatchlistGenerator:

    def __init__(self):  # initialize the client
        self.client = Client(api_key=testnet_api_key, api_secret=testnet_api_secret_key, tld='com', testnet=True)


    def get_history(self, symbol, interval, start, end=None):
        bars = self.client.get_historical_klines(symbol=symbol, interval=interval,
                                                 start_str=start, end_str=end, limit=1000)
        df = pd.DataFrame(bars)
        df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
        df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                      "Close Time", "Quote Asset Volume", "Number of Trades",
                      "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        df.set_index("Date", inplace=True)
        for column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
        return df


    def fetch_history(self, symbol, interval, start, sma_window, atr_window):
        try:
            data = self.get_history(symbol=symbol, interval=interval, start=str(start))
            if data is not None and not data.empty:
                data['SMA'] = ta.sma(data['Close'], length=sma_window)
                data['ATR'] = ta.atr(data['High'], data['Low'], data['Close'], length=atr_window)
            return symbol, data
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return symbol, None


    def get_historical_close(self, symbols, interval, before_now, sma_window, atr_window):
        fetch_func = partial(self.fetch_history, interval=interval, start=before_now,
                             sma_window=sma_window, atr_window=atr_window)

        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(fetch_func, symbols)

        return {symbol: data for symbol, data in results if data is not None}


    def get_watchlist(self, currency, interval, sma_window, atr_window, lookback, filter):
        span = sma_window + 1
        coins = pd.DataFrame(self.client.get_all_tickers())  # get all the available assets
        coins['price'] = pd.to_numeric(coins['price'], errors='coerce')  # Convert 'price' string to numeric
        coins = coins[(coins['symbol'].str.contains(currency)) & (coins['price'] > 0)].reset_index(drop=True)  # filter for selected currency and asset price greater than zero

        symbols = coins['symbol'].values

        interval_mapping = {
            '5m': timedelta(minutes=span * 5),
            '15m': timedelta(minutes=span * 15),
            '30m': timedelta(minutes=span * 30),
            '1h': timedelta(hours=span),
            '2h': timedelta(hours=span * 2),
            '4h': timedelta(hours=span * 4),
            '1d': timedelta(days=span)
        }


        #now = datetime.now(datetime.UTC)
        now = datetime.utcnow()
        before_now = now - interval_mapping[interval]

        historical_data = self.get_historical_close(symbols, interval, before_now, sma_window, atr_window)

        if lookback == 1:
            
            data = [{'Asset': key,
                 'Close': historical_data[key]['Close'].iloc[-1],
                 'SMA': historical_data[key]['SMA'].iloc[-2],
                 'ATR': historical_data[key]['ATR'].iloc[-1]}
                for key in historical_data.keys()]
            
            df = pd.DataFrame(data, columns=['Asset', 'Close', 'SMA', 'ATR'])
            df['delta'] = (df['Close'] / df['SMA'] - 1).round(4)
            
            df.rename(columns={'SMA': f'SMA({sma_window})', 'ATR': f'ATR({atr_window})'}, inplace=True)
            
            if filter:
                watchlist = df.loc[df['Close'] < df[f'SMA({sma_window})']]
                print(f'Watchlist filtered using a Lookback value of {lookback}\n')
            else:
                watchlist = df
                
        elif lookback > 1:
            
            data = [{'Asset': key,
                 'Close': historical_data[key]['Close'].iloc[-1],
                 'SMA': historical_data[key]['SMA'].iloc[-2],
                 'ATR': historical_data[key]['ATR'].iloc[-1],
                 'Lookback_Close': historical_data[key]['Close'][-lookback:].max()}
                for key in historical_data.keys()]
            
            df = pd.DataFrame(data, columns=['Asset', 'Close', 'SMA', 'ATR','Lookback_Close'])
            df['delta'] = (df['Close'] / df['SMA'] - 1).round(4)
            df.rename(columns={'SMA': f'SMA({sma_window})', 'ATR': f'ATR({atr_window})'}, inplace=True)
            
            if filter:
                watchlist = df.loc[df[f'Lookback_Close'] < df[f'SMA({sma_window})']]
                watchlist = watchlist.drop(columns='Lookback_Close')
                print(f'\nWatchlist filtered using a Lookback value of {lookback}\n')
            else:
                watchlist = df

        return watchlist.sort_values(by='delta').reset_index(drop=True)


    def get_symbol_info(self, watchlist):

        # Initialize an empty list to store the result dictionaries
        data = []

        for symbol in watchlist['Asset']:
            info = self.client.get_symbol_info(symbol)

            tick_size = next(f['tickSize'] for f in info['filters'] if f['filterType'] == 'PRICE_FILTER')
            lot_size = next(f['stepSize'] for f in info['filters'] if f['filterType'] == 'LOT_SIZE')

            info_dict = {
                'symbol': info['symbol'],
                'status': info['status'],
                'ocoAllowed': info['ocoAllowed'],
                'otoAllowed': info['otoAllowed'],
                'allowTrailingStop': info['allowTrailingStop'],
                'tickSize': len(tick_size.split('.')[1].rstrip('0')) if '.' in tick_size else 0,
                'stepSize': len(lot_size.split('.')[1].rstrip('0')) if '.' in lot_size else 0,
            }
            data.append(info_dict)

        info_df = pd.DataFrame(data, columns=['symbol', 'status', 'ocoAllowed', 'otoAllowed', 'allowTrailingStop', 'tickSize', 'stepSize'])
        final_df = watchlist.merge(info_df, left_on='Asset', right_on='symbol')
        final_df.drop(columns='symbol',inplace=True)
    
        return final_df #milgiorare per numero decimale corretto