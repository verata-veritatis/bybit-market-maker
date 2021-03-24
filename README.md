# bybit-market-maker-v2
A very primitive Python-based market maker bot for Bybit, meant to be used a sample. Users can fork this repository and customize their own algorithms. Uses the [`pybit`](https://github.com/verata-veritatis/pybit) module.

[![Python 3.6](https://img.shields.io/badge/python-3.6%20|%203.7%20|%203.8-blue.svg)](https://www.python.org/downloads/)

![Market Maker](https://i.imgur.com/XZc8tUg.png)

## Usage
Be sure you have [`pybit`](https://github.com/verata-veritatis/pybit) installed:
```
pip install pybit
```
Next, clone or download this repository and extract. Modify `config.py` to your liking, navigate to the project via CLI, and `python run.py`.

## How It Works
- A given number of long and short orders are spaced evenly from the current last price up to a user-defined range. The last price at the time of placement is considered the *median*. 
- If a single side of orders begins to fill, the bot cancels the other side of orders and places a take-profit at a user-defined distance away from the entry price.
- A stop-loss can be set at a distance that is also user-defined.
- If the position is closed, whether by close orders or stop loss, new long and short orders are placed and the cycle continues.
- This strategy has little-to-no risk management and is meant to be used by the user as a "starting point". By default, a pretty distant stop-loss is used. It hurts.

## Disclaimer
*This project is still in the early stages of development. Please refrain from using the bot on livenet until it is stable!*
