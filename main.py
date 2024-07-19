from modules.historical_price import WatchlistGenerator
from modules.money_management import CapitalManager
from modules.trade_management import TradeManager
from modules.risk_management import RiskManager

################################ INPUT ################################

currency = 'USDT'
saving_rate = 0.1
saving_threshold = 0.5

interval = '1h'
sma_window = 50
atr_window = 14
loockback = 1
filter = True

pct_risk_per_trade = 0.02
ATR_multiplier = 4
max_num_trades = 4

stablecoins = ['EURAEUR','ETHAEUR','AEURUSDT','EURUSDC','EURUSDT']

#######################################################################

# MONEY MANAGEMENT MODULE - get balances details and check savings
manager = CapitalManager(currency, saving_rate, saving_threshold)
capital, free_capital, saving_capital, target_saving_capital = manager.get_capital_amounts()
saving_adjustment = manager.check_saving_capital()
print(f'''
Currency: {currency}
Capital: {capital.round(2)}
Free Capital: {free_capital.round(2)}
Saving Capital: {saving_capital.round(2)}
Target Saving Capital: {target_saving_capital.round(2)}
''')

# HISTORICAL PRICE MODULE - Generate the Watchlist and calculate SMA and ATR
wl = WatchlistGenerator()
watchlist = wl.get_watchlist(currency, interval, sma_window, atr_window, loockback, filter)
watchlist = wl.get_symbol_info(watchlist)
watchlist = watchlist[~watchlist['Asset'].isin(stablecoins)]
print(watchlist)

# RISK MANAGEMENT MODULE - Generate the Trade sizing and SL according to defined risk
rm = RiskManager(watchlist,capital,saving_rate,pct_risk_per_trade,ATR_multiplier,max_num_trades)
orderbook = rm.get_order_book()
print(orderbook)

# TRADE MANAGEMENT MODULE - Execute the trades using data in the orderbook
tm = TradeManager()
results = tm.place_orders(orderbook)
print(results)
