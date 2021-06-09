import config, EMA
import binance_futures_api
from datetime import datetime
from termcolor import colored

def lets_make_some_money(i):
    print(binance_futures_api.pair[i])
    klines   = binance_futures_api.KLINE_INTERVAL_1HOUR(i)
    response = binance_futures_api.position_information(i)
    dataset  = binance_futures_api.closing_price_list(klines)
    EMA_low  = EMA.compute(5, dataset)
    EMA_mid  = EMA.compute(8, dataset)
    EMA_high = EMA.compute(13, dataset)

    leverage = config.leverage
    if int(response.get("leverage")) != leverage: binance_futures_api.change_leverage(i, leverage)
    if response.get('marginType') != "isolated": binance_futures_api.change_margin_to_ISOLATED(i)

    if binance_futures_api.get_position_amount(i) > 0: # LONGING
        if EXIT_LONG_CONDITION(klines, EMA_low, EMA_high):
            binance_futures_api.close_long(i, response)
            print("💰 CLOSE_LONG 💰")
        else: print(colored("HOLDING_LONG", "green"))

    elif binance_futures_api.get_position_amount(i) < 0: # SHORTING
        if EXIT_SHORT_CONDITION(klines, EMA_low, EMA_high):
            binance_futures_api.close_short(i, response)
            print("💰 CLOSE_SHORT 💰")
        else: print(colored("HOLDING_SHORT", "red"))

    else:
        if GO_LONG_CONDITION(klines, EMA_low, EMA_mid, EMA_high):
            binance_futures_api.open_long_position(i)
            print(colored("🚀 GO_LONG 🚀", "green"))

        elif GO_SHORT_CONDITION(klines, EMA_low, EMA_mid, EMA_high):
            binance_futures_api.open_short_position(i)
            print(colored("💥 GO_SHORT 💥", "red"))

        else: print("🐺 WAIT 🐺")

    print("Last action executed @ " + datetime.now().strftime("%H:%M:%S") + "\n")

# ==========================================================================================================================================================================
#                                                    ENTRY CONDITIONS
# ==========================================================================================================================================================================

def GO_LONG_CONDITION(klines, EMA_low, EMA_mid, EMA_high):
    if (EMA.DELTA_UP(EMA_low, EMA_mid, EMA_high) or binance_futures_api.current_close(klines) > EMA.current(EMA_mid)) and \
        binance_futures_api.current_close(klines) > EMA.current(EMA_low) and \
        binance_futures_api.candle_color(klines) == "GREEN": return True

def GO_SHORT_CONDITION(klines, EMA_low, EMA_mid, EMA_high):
    if (EMA.DELTA_DOWN(EMA_low, EMA_mid, EMA_high) or binance_futures_api.current_close(klines) < EMA.current(EMA_mid)) and \
        binance_futures_api.current_close(klines) < EMA.current(EMA_low) and \
        binance_futures_api.candle_color(klines) == "RED": return True

def EXIT_LONG_CONDITION(klines, EMA_low, EMA_high):
    if  binance_futures_api.current_close(klines) < EMA.current(EMA_high) and \
        binance_futures_api.current_close(klines) < EMA.current(EMA_low) and \
        binance_futures_api.candle_color(klines) == "RED": return True

def EXIT_SHORT_CONDITION(klines, EMA_low, EMA_high):
    if  binance_futures_api.current_close(klines) > EMA.current(EMA_high) and \
        binance_futures_api.current_close(klines) > EMA.current(EMA_low) and \
        binance_futures_api.candle_color(klines) == "GREEN": return True

# ==========================================================================================================================================================================
#                                                    DEPLOY THE BOT
# ==========================================================================================================================================================================

import requests, socket, urllib3
from binance.exceptions import BinanceAPIException
from apscheduler.schedulers.blocking import BlockingScheduler

if config.live_trade:
    print(colored("LIVE TRADE IS ENABLED\n", "green"))
else: print(colored("THIS IS BACKTESTING\n", "red"))

def add_this_to_cron_job():
    for i in range(len(config.coin)): lets_make_some_money(i)

try:
    if config.enable_scheduler:
        scheduler = BlockingScheduler()
        scheduler.add_job(add_this_to_cron_job, 'cron', second='0')
        scheduler.start()
    else: add_this_to_cron_job()

except (socket.timeout,
        BinanceAPIException,
        urllib3.exceptions.ProtocolError,
        urllib3.exceptions.ReadTimeoutError,
        requests.exceptions.ConnectionError,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        ConnectionResetError, KeyError, OSError) as e: print(e)

except KeyboardInterrupt: print("\n\nAborted.\n")