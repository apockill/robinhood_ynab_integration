from Robinhood import Robinhood, exceptions


def get_total_assets_value(rh: Robinhood):
    """
    :param rh: The logged-in robinhood object
    :return: $ in stocks, $ not allocated (Cash)
    """
    equity = rh.equity()
    positions = rh.positions()["results"]
    stock_assets = 0
    for position in positions:
        num_stocks = float(position["quantity"])

        if num_stocks == 0:
            # Sometimes RH returns stocks that have never been bought by
            # the account
            continue

        instrument = rh.get_url(position["instrument"])
        if instrument["state"] == "inactive":
            # This symbol may have been discontinued and changed into a
            # different symbol. Calling get_quote() will result in an
            # InvalidTickerSymbol exception
            continue

        symbol = instrument["symbol"]
        quote = rh.get_quote(symbol)
        price_str = quote["last_extended_hours_trade_price"]
        if price_str is None:
            price_str = quote["last_trade_price"]

        stock_assets += float(price_str) * num_stocks
    return stock_assets, equity - stock_assets