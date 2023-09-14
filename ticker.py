#!/bin/env python3

import json
from time import sleep
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

from os import system, name, environ
from datetime import datetime

# Used by the sleep timer to determine API call frequency
refresh_cycle = 60

def clear():
    # For Windows NT based systems
    if name == "nt":
        _ = system("cls")
    # For POSIX systems (Linux, macOS, FreeBSD, OpenBSD, NetBSD, and more)
    else:
        _ = system("clear")

def get_stock_quotes(tickers):
    stock_dict = {}
    base_url = "https://api.finnhub.io/api/v1"
    endpoint = "/quote?symbol="
    # Fetch API token from user environment variable
    api_token = environ.get("X-Finnhub-Token")
    for ticker in tickers:
        req = Request(base_url + endpoint + ticker)
        req.add_header("X-Finnhub-Token", api_token)
        try:
            content = urlopen(req).read()
            # API response reference
            # c     - Current price
            # d     - Change
            # dp    - Percent change
            # h     - High price of the day
            # l     - Low price of the day
            # o     - Open price of the day
            # pc    - Previous close price
            # t     - Published time in UNIX timestamp
            current_price = json.loads(content)["c"]
            percent_change = round(json.loads(content)["dp"], 2)
            time = datetime.fromtimestamp(json.loads(content)["t"])
            stock_dict[ticker] = {"current_price": current_price, "percent_change": percent_change, "time": time}
        except HTTPError as err:
            if err.code == 429:
                print("Too many requests were made and you reached the API rate limit.")
                exit(1)
            else:
                raise

    return stock_dict

def build_ticker_layout(stocks, ticker):
    ticker_info = stocks[ticker]
    cp = ticker_info["current_price"]
    pc = ticker_info["percent_change"]
    t = ticker_info["time"]
    if pc < 0:
        return f"[b]{ticker}[/b]\n[grey69]${cp}\n[red]{pc}%\n[bright_white][i]{t}[/i]"

    return f"[b]{ticker}[/b]\n[grey69]${cp}\n[green]+{pc}%\n[bright_white][i]{t}[/i]"
    
def setup():
    console = Console()
    clear()
    
    # Limit to a maximum of 30 tickers due to rate limiting.
    # If your limit is exceeded, you will receive a response with status code 429.
    # On top of all plan's limit, there is a 30 API calls/ second limit.
    # See https://finnhub.io/docs/api/rate-limit

    tickers = []

    with open('tickers.txt') as file:
        [tickers.append(line.strip()) for line in file.readlines()]

    if len(tickers) > 30:
        print("You have more than 30 tickers in your list. Please reduce this number in order to avoid the API rate limit.")
        exit(0)
    
    stocks = get_stock_quotes(tickers)
    # Uncomment to view raw data
    # console.print(stocks, overflow="ignore", crop=False)
    stock_renderables = [Panel(build_ticker_layout(stocks, stock), expand=True) for stock in stocks]
    console.print(Columns(stock_renderables))

def main():
    # Allows for graceful program exit when using Ctrl-C
    try:
        setup()
        while True:
            sleep(refresh_cycle)
            setup()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
