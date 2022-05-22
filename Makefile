start:
	PYTHONPATH=./ python app/main.py

run_backtest:
	PYTHONPATH=./ pytest .

display_stats:
	PYTHONPATH=./ python tools/display_stats.py BBG000QDVR53

get_accounts:
	PYTHONPATH=./ python tools/get_accounts.py