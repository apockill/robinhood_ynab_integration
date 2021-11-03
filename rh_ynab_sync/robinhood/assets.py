from Robinhood import Robinhood, exceptions


def get_total_assets_value(rh: Robinhood) -> float:
    """
    :param rh: The logged-in robinhood object
    :return: $ in stocks, $ not allocated (Cash)
    """
    stocks_value = _get_stock_assets_value(rh)
    crypto_value = _get_crypto_assets_value(rh)
    return crypto_value + stocks_value


def _get_stock_assets_value(rh: Robinhood) -> float:
    """Returns the total value held in stocks"""
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
    return stock_assets


def _get_crypto_assets_value(rh: Robinhood) -> float:
    """Returns the total value held in crypto"""
    # print(rh.crypto_orders())
    crypto_assets = 0
    crypto_holdings_data = rh.crypto_holdings()["results"]

    for crypto_holding in crypto_holdings_data:
        quantity_available = float(crypto_holding["quantity_available"])
        if quantity_available == 0:
            continue

        code = crypto_holding["currency"]["code"]
        market_price_str = rh.crypto_quote(rh.CRYPTO_PAIRS[code])["mark_price"]

        crypto_assets += quantity_available * float(market_price_str)
    return crypto_assets
