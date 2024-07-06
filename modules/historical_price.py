from datetime import datetime, timedelta
from binance.client import Client
from dotenv import load_dotenv
import pandas_ta as ta
import pandas as pd

load_dotenv()
testnet_api_key = os.getenv('testnet_api_key')
testnet_api_secret_key = os.getenv('testnet_api_secret_key')

class WatchlistGenerator:

	def __init__(self): #initialize the client
		self.client = Client(api_key=testnet_api_key, api_secret=testnet_api_secret_key, tld='com', testnet=True)

	def get_history(self, symbol, interval, start, end=None):
		bars = self.client.get_historical_klines(symbol=symbol, interval=interval,
										   start_str=start, end_str=end, limit=1000)
		df = pd.DataFrame(bars)
		df["Date"] = pd.to_datetime(df.iloc[:, 0], unit="ms")
		df.columns = ["Open Time", "Open", "High", "Low", "Close", "Volume",
                      "Clos Time", "Quote Asset Volume", "Number of Trades",
                      "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore", "Date"]
		df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
		df.set_index("Date", inplace=True)
		for column in df.columns:
			df[column] = pd.to_numeric(df[column], errors="coerce")
		return df
    
	def get_watchlist(self, currency, interval, span, sma, loockback, filter=True):
		coins = pd.DataFrame(self.client.get_all_tickers()) # get all the available assets
		coins['price'] = pd.to_numeric(coins['price'], errors='coerce') # Convert 'price' string to numeric 
		coins = coins[(coins['symbol'].str.contains(currency)) & (coins['price'] > 0)].reset_index(drop=True) # filter for selected currency and asset price greater than zero

		symbols = coins['symbol'].values

		interval_mapping = {
			'd': timedelta(days=span),
			'1h': timedelta(hours=span),
			'4h': timedelta(hours=span*4)
		}

		now = datetime.now(datetime.UTC)
		before_now = now - interval_mapping[interval]

		historical_close = {}
		for symbol in symbols:
			try:
				historical_close[symbol] = self.get_history(symbol=symbol, interval=interval, start=str(before_now))['Close']
			except Exception as e:
				print(f"Error fetching data for {symbol}: {e}")

		historical_data = pd.DataFrame(historical_close)
		historical_data.index = pd.to_datetime(historical_data.index)

		market_sma = pd.DataFrame(historical_data.rolling(sma).mean().iloc[-2])
		market_sma = market_sma.rename(columns={market_sma.columns[0]: f'SMA({sma})'})
	

		if loockback == 1:
			market_sma['last_price'] = historical_data.iloc[-1]
			market_sma['delta'] = round(market_sma['last_price'] / market_sma[f'SMA({sma})'] - 1,4)
			if filter is True:
				watchlist = market_sma[market_sma[f'last_price'] < market_sma[f'SMA({sma})']]
			else:
				watchlist = market_sma
		elif loockback > 1:
			market_sma[f'max_last_{loockback}_prices'] = historical_data.tail(loockback).max()
			market_sma['delta'] = round(market_sma[f'max_last_{loockback}_prices'] / market_sma[f'SMA({sma})'] - 1,4)
			if filter is True:
				watchlist = market_sma[market_sma[f'max_last_{loockback}_prices'] < market_sma[f'SMA({sma})']]
			else:
				watchlist = market_sma
				
		return watchlist.sort_values(by='delta')
	
