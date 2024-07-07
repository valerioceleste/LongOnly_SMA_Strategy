from binance.client import Client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
testnet_api_key = os.getenv('testnet_api_key')
testnet_api_secret_key = os.getenv('testnet_api_secret_key')


class CapitalManager:
    def __init__(self, currency, saving_rate, saving_threshold):
        self.currency = currency
        self.saving_threshold = saving_threshold
        self.saving_rate = saving_rate
        self.client = Client(api_key=testnet_api_key, api_secret=testnet_api_secret_key, tld='com', testnet=True)

    def get_capital_amounts(self):
        account = pd.DataFrame(self.client.get_account()['balances'])[['asset', 'free']] # details of the free amount available in the given currency
        account['free'] = pd.to_numeric(account['free'], errors='coerce') # converts the free amount from string to number
        capital = account[account['asset'] == self.currency]['free'].values[0] # gives the balance of the selected currency
        free_capital = capital * (1 - self.saving_rate) # defines the free capital as the capital available fro training once reduced by saving
        saving_capital = target_saving_capital = capital * self.saving_rate # capital to be put aside
        return capital, free_capital, saving_capital, target_saving_capital

    def check_saving_capital(self):
        _, _, saving_capital, target_saving_capital = self.get_capital_amounts()
        if saving_capital < target_saving_capital * self.saving_threshold: # check if saving capital needs to be replenished
            return target_saving_capital - saving_capital
        return 0