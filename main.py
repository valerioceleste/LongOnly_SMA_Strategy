from modules.historical_price import WatchlistGenerator
from modules.money_management import CapitalManager

################################ INPUT ################################

# currency
currency = input("\nEnter the currency (e.g., 'EUR' or 'USDT'): ")


# money management
saving_margin = float(input("Enter the Saving Margin (e.g., 0.1): "))
saving_threshold = float(input("Enter the Saving Threshold you want to keep all the time (e.g., 0.5): "))

# historical market data
interval = '1h'
sma = 110
span = sma + 1
loockback = 10
filter = True

# trades management
max_trades = 8

#######################################################################

# MONEY MANAGEMENT MODULE - get balances details and check savings
manager = CapitalManager(currency, saving_margin, saving_threshold)
capital, free_capital, saving_capital, target_saving_capital = manager.get_capital_amounts()
saving_adjustment = manager.check_saving_capital()
print(f'\n\nCurrency: {currency}, \nCapital: {capital}, \nFree Capital: {free_capital}, \nSaving Capital: {saving_capital}, \nTarget Saving Capital:{target_saving_capital}\n\n')

# HISTORICAL PRICE MODULE - Genrate the Watchlist and calculate SMA
watchlist = WatchlistGenerator()
last_sma = watchlist.get_watchlist(currency, interval, span, sma, loockback, filter)
print(last_sma)

