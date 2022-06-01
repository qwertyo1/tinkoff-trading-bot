### 🥇 The winner in [Tinkoff invest robot contest](https://github.com/Tinkoff/invest-robot-contest) 01.06.2022

# Tinkoff Trading Bot

This is a bot for trading on Tinkoff broker.
It uses [Tinkoff investments API](https://github.com/Tinkoff/investAPI)

App name is `qwertyo1`

## How to run
To run the bot, you need to have a Tinkoff account.
- Generate token for your account at [the settings](https://www.tinkoff.ru/invest/settings/)
- Create a file `.env` with required env variables. You can find an example in `.env.example`
- Create a file `instuments_config.json` with configurations. You can find an example in `instruments_config.json.example`
- [Optional] Create virtual environment and activate it:
  ```bash
  pip install virtualenv
  virtualenv --python=python3.9 venv
  source venv/bin/activate
  ```
- Install dependencies with
  ```bash
  pip install -r requirements.txt
  ```
- Run the bot with 
  ```bash 
  make start
  ```

## .env file content
- `TOKEN`: Your Tinkoff token. You can generate it in [the settings](https://www.tinkoff.ru/invest/settings/)
Can be a token for sandbox or for real account.
- `ACCOUNT_ID`: Your Tinkoff account id. You can get it using [get accounts tool](#get-accounts-tool). If not specified, the first account  used.
- `SANDBOX`: Set to `false` if you want to use real account. Default is `true`.

## instruments_config.json file content
#### instruments
List of instruments you want to trade along with their settings.
Each list element is a dictionary with the following keys:
- `figi`: Tinkoff instrument id
- `strategy`: The strategy configuration
  - `name`: The name of the strategy to use
  - `parameters`: Parameters of the strategy. More details can be found in the documentation of the strategy

#### Interval strategy parameters
- `interval_size`: The percent of the prices to include into interval
- `days_back_to_consider`: The number of days back to consider in interval calculation
- `check_interval`: The interval in seconds to check for a new prices and for interval recalculation
- `stop_loss_percent`: The percent from the price to trigger a stop loss
- `quantity_limit`: The maximum quantity of the instrument to have in the portfolio

## Strategies
### Interval strategy
Main strategy logic is to buy at the lowest price and sell at the highest price of the
calculated interval.

Interval is calculated by taking `interval_size` percents of the last prices
for the last `days_back_to_consider` days. By default, it's set to 80 percents which means
that the interval is from 10th to 90th percentile.

## Get accounts tool
This is the tool to get your Tinkoff accounts. Useful when you don't know your account id.
To run use this command:
```bash
make get_accounts
```

## Backtest
In `test/strategies/interval/backtest/conftest.py` you can find the test configuration.
Set up `figi`, `comission`, strategy config object, and `from_date` offset.
To run backtest use this command:
```bash
make backtest
```
The result is saved in `test/strategies/interval/backtest/test_on_historical_data.txt`

## Stats displaying
Use this command to display stats:
```bash
make display_stats
```
It will display the list of executed trades
