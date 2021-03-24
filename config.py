"""
Configuration.
Use at your own risk.
"""

# Auth stuff.
API_KEY = ''
PRIVATE_KEY = ''

# Set the market symbol and the coin associated with the market.
SYMBOL = 'BTCUSD'
COIN = 'BTC'

# How much of your balance to use in decimal
# i.e. 1 = 100% (1x), 0.1 = 10% (0.1x), 100 = 10000% = (100x)
EQUITY = 20

# Number of orders and the range.
RANGE = 0.04  # in decimal of last price i.e. 0.1 = 10% of last price
NUM_ORDERS = 20  # number of orders ON EACH SIDE i.e. 20 = 20 buys, 20 sells

# How many times should we check for updates.
POLLING_RATE = 2  # in per seconds i.e. time.sleep(1/polling_rate)

# Take profit distance in percentage of price.
TP_DIST = 0.003

# Stop distance...SET IT LARGER THAN THE ORDER RANGE/2 FOR OBVIOUS REASONS.
# If STOP_DIST = None or 0, no stop will be set.
STOP_DIST = 0.025
