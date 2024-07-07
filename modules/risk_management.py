import pandas as pd

class RiskManager:
    
    def __init__(self, watchlist, capital, saving_rate, pct_risk_per_trade, ATR_multiplier, max_num_trades):
        
        self.watchlist = watchlist 
        self.capital = capital 
        self.saving_rate = saving_rate
        self.pct_risk_per_trade = pct_risk_per_trade 
        self.ATR_multiplier = ATR_multiplier
        self.max_num_trades = max_num_trades
        self.free_capital = capital * (1 - saving_rate)
        self.trade_budget = self.free_capital / max_num_trades
        self.loss_per_trade = self.free_capital * pct_risk_per_trade
        
    def get_order_book(self):
        
        orderbook = pd.DataFrame()
        watchlist = pd.DataFrame(self.watchlist)
        watchlist.rename(columns={watchlist.columns[2]: 'SMA', watchlist.columns[3]: 'ATR'}, inplace=True)
        
        orderbook['Asset'] = watchlist['Asset']
        orderbook['Entry'] = watchlist['SMA']
        orderbook['SL'] = watchlist['SMA'] - watchlist['ATR'] * self.ATR_multiplier
        orderbook['Pct_Loss'] = (orderbook['SL'] / orderbook['Entry'] - 1).round(4)
        orderbook['Size'] = self.loss_per_trade / (orderbook['Entry'] - orderbook['SL'])
        orderbook['Amount'] = orderbook['Entry'] * orderbook['Size']
        orderbook['Loss'] = orderbook['Amount'] * orderbook['Pct_Loss']
        orderbook['Budget'] = self.trade_budget
        orderbook['Budget_Size'] = orderbook['Budget'] / orderbook['Entry']
        orderbook['Budget_Loss'] = orderbook['Budget'] * orderbook['Pct_Loss']
        
        print(f'\n\nTrade Sizing based on a Free capital of {self.free_capital} and a total of max {self.max_num_trades} trades ({self.trade_budget}) with a max loss of {self.pct_risk_per_trade*100}% ({self.loss_per_trade})\n')
        return orderbook

# verificare che il rischio sia prezzato sul budget del singolo trade non di ptf. questo dovrebbe funzionare su margine/futures, non spot