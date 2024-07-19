from binance.exceptions import BinanceAPIException
from binance.client import Client
from dotenv import load_dotenv
import pandas as pd
import os

load_dotenv()
testnet_api_key = os.getenv('testnet_api_key')
testnet_api_secret_key = os.getenv('testnet_api_secret_key')

class TradeManager:
    
    def __init__(self):
        self.client = Client(api_key=testnet_api_key, api_secret=testnet_api_secret_key, testnet=True)

    def place_orders(self, orderbook):
        
        orderbook = orderbook.to_dict('records')

        results = {}

        for order in orderbook:
            symbol = order['Asset']
            entry_price = round(order['Entry'], int(order['TickSize']))
            stop_loss = round(order['SL'], int(order['TickSize']))
            quantity = round(order['Budget_Size'], int(order['StepSize']))
            
            try:
                
                # Place limit order
                limit_order = self.client.create_order(symbol = symbol,
                                                       side = Client.SIDE_BUY,
                                                       type = Client.ORDER_TYPE_LIMIT,
                                                       timeInForce = Client.TIME_IN_FORCE_GTC,
                                                       quantity = quantity,
                                                       price = entry_price)
                
                # Place stop loss order
                stop_loss_order = self.client.create_order(symbol = symbol,
                                                           side = Client.SIDE_SELL,
                                                           type = Client.ORDER_TYPE_STOP_LOSS_LIMIT,
                                                           timeInForce = Client.TIME_IN_FORCE_GTC,
                                                           quantity = quantity,
                                                           stopPrice = stop_loss,
                                                           price = stop_loss)
                
                results[symbol] = {'limit_order': limit_order,
                                   'stop_loss_order': stop_loss_order,
                                   'status': 'Success'}
                
            except BinanceAPIException as e:
                results[symbol] = {'status': 'Failed', 'error': str(e)}
            
            except Exception as e:
                results[symbol] = {'status': 'Failed', 'error': f'Unexpected error: {str(e)}'}
        return pd.DataFrame(results)
