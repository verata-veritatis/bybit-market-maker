from pybit import HTTP
from pybit.exceptions import InvalidRequestError
from datetime import datetime as dt

import numpy as np
import time

import config


def _print(message, level='info'):
    """
    Just a custom print function. Better than logging.
    """
    if level == 'position':
        print(f'{dt.utcnow()} - {message}.', end='\r')
    else:
        print(f'{dt.utcnow()} - {level.upper()} - {message.capitalize()}.')


def scale_qtys(x, n):
    """
    Will create a list of qtys on both long and short
    side that scale additively i.e.
    [5, 4, 3, 2, 1, -1, -2, -3, -4, -5].

    x: How much of your balance to use.
    n: Number of orders.
    """
    n_ = x / ((n + n ** 2) / 2)
    long_qtys = [int(n_ * i) for i in reversed(range(1, n + 1))]
    short_qtys = [-i for i in long_qtys]
    return long_qtys + short_qtys[::-1]


if __name__ == '__main__':
    print('\n--- SAMPLE MARKET MAKER V2 ---')
    print('For pybit, created by verata_veritatis.')

    if not config.API_KEY or not config.PRIVATE_KEY:
        raise PermissionError('An API key is required to run this program.')

    print('\nUSE AT YOUR OWN RISK!!!\n')
    time.sleep(1)

    _print('opening session')
    s = HTTP(
        api_key=config.API_KEY,
        api_secret=config.PRIVATE_KEY,
        logging_level=50,
        retry_codes={10002, 10006},
        ignore_codes={20001, 30034},
        force_retry=True,
        retry_delay=3
    )

    # Auth sanity test.
    try:
        s.get_wallet_balance()
    except InvalidRequestError as e:
        raise PermissionError('API key is invalid.')
    else:
        _print('authenticated sanity check passed')

    # Set leverage to cross.
    try:
        s.set_leverage(
            symbol=config.SYMBOL,
            leverage=0
        )
    except InvalidRequestError as e:
        if e.status_code == 34015:
            _print('margin is already set to cross')
    else:
        _print('forced cross margin')

    print('\n------------------------------\n')

    # Main loop.
    while True:

        # Cancel orders.
        s.cancel_all_active_orders(
            symbol=config.SYMBOL
        )

        # Close position if open.
        s.close_position(
            symbol=config.SYMBOL
        )

        # Grab the last price.
        _print('checking last price')
        last = float(s.latest_information_for_symbol(
            symbol=config.SYMBOL
        )['result'][0]['last_price'])
        price_range = config.RANGE * last

        # Create order price span.
        _print('generating order prices')
        prices = np.linspace(
            last - price_range/2, last + price_range/2, config.NUM_ORDERS * 2
        )
        tp_dp = config.TP_DIST * last

        # Scale quantity additively (1x, 2x, 3x, 4x).
        _print('generating order quantities')
        balance_in_usd = float(s.get_wallet_balance(
            coin=config.COIN
        )['result'][config.COIN]['available_balance']) * last
        available_equity = balance_in_usd * config.EQUITY
        qtys = scale_qtys(available_equity, config.NUM_ORDERS)

        # Prepare orders.
        orders = [
            {
                'symbol': config.SYMBOL,
                'side': 'Buy' if qtys[k] > 0 else 'Sell',
                'order_type': 'Limit',
                'qty': abs(qtys[k]),
                'price': int(prices[k]),
                'time_in_force': 'GoodTillCancel',
            } for k in range(len(qtys))
        ]
        _print('submitting orders')
        responses = s.place_active_order_bulk(orders=orders)

        # Let's create an ID list of buys and sells as a dict.
        _print('orders submitted successfully')
        order_ids = {
            'Buy': [i['result']['order_id']
                    for i in responses if i['result']['side'] == 'Buy'],
            'Sell': [i['result']['order_id']
                     for i in responses if i['result']['side'] == 'Sell'],
        }

        # In-position loop.
        while True:

            # Await position.
            _print('awaiting position')
            while not abs(s.my_position(
                    symbol=config.SYMBOL
            )['result']['size']):
                time.sleep(1 / config.POLLING_RATE)

            # When we have a position, get the size and cancel all the
            # opposing orders.
            if s.my_position(
                    symbol=config.SYMBOL
            )['result']['side'] == 'Buy':
                to_cancel = [{
                    'symbol': config.SYMBOL,
                    'order_id': i
                } for i in order_ids['Sell']]
            elif s.my_position(
                    symbol=config.SYMBOL
            )['result']['side'] == 'Sell':
                to_cancel = [{
                    'symbol': config.SYMBOL,
                    'order_id': i
                } for i in order_ids['Buy']]
            else:
                # Position was closed immediately for some reason. Restart.
                _print('position closed unexpectedly—resetting')
                break
            s.cancel_active_order_bulk(
                orders=to_cancel
            )

            # Set a TP.
            p = s.my_position(symbol=config.SYMBOL)['result']
            e = float(p['entry_price'])
            tp_response = s.place_active_order(
                symbol=config.SYMBOL,
                side='Sell' if p['side'] == 'Buy' else 'Buy',
                order_type='Limit',
                qty=p['size'],
                price=int(e + tp_dp if p['side'] == 'Buy' else e - tp_dp),
                time_in_force='GoodTillCancel',
                reduce_only=True
            )
            curr_size = p['size']

            # Set a position stop.
            if config.STOP_DIST:
                e = float(p['entry_price'])
                if p['side'] == 'Buy':
                    stop_price = e - (e * config.STOP_DIST)
                else:
                    stop_price = e + (e * config.STOP_DIST)
                s.set_trading_stop(
                    symbol=config.SYMBOL,
                    stop_loss=int(stop_price)
                )

            # Monitor position.
            print('\n------------------------------\n')
            while p['size']:

                # Get the size with sign based on side.
                signed_size = p['size'] if p['side'] == 'Buy' else -p['size']
                pnl_sign = '+' if float(p['unrealised_pnl']) > 0 else '-'

                # Show status.
                _print(
                    f'Size: {signed_size} ({p["effective_leverage"]}x), '
                    f'Entry: {float(p["entry_price"]):.2f}, '
                    f'Balance: {float(p["wallet_balance"]):.8f}, '
                    f'PNL: {pnl_sign}{abs(float(p["unrealised_pnl"])):.8f}',
                    level='position'
                )

                # Sleep and re-fetch.
                time.sleep(1 / config.POLLING_RATE)
                p = s.my_position(symbol=config.SYMBOL)['result']

                # If size has changed, update TP based on entry and size.
                if p['size'] > curr_size:
                    e = float(p['entry_price'])
                    tp_price = e + tp_dp if p['side'] == 'Buy' else e - tp_dp
                    s.replace_active_order(
                        symbol=config.SYMBOL,
                        order_id=tp_response['result']['order_id'],
                        p_r_price=int(tp_price),
                        p_r_qty=p['size']
                    )
                    curr_size = p['size']

            # Position has closed—get PNL information.
            print(' ' * 101, end='\r')
            pnl_r = s.closed_profit_and_loss(
                symbol=config.SYMBOL
            )['result']['data'][0]

            # Store PNL data as string.
            pos = f'{pnl_r["side"]} {pnl_r["qty"]}'
            prc = f'{pnl_r["avg_entry_price"]} -> {pnl_r["avg_exit_price"]}'

            # Display PNL info.
            _print(f'position closed successfully—{pos} ({prc})')
            print('\n------------------------------\n')
            break
