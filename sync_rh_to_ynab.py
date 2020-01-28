import datetime
import logging
import os

import dateutil.parser as date_parser
import ynab_client
from Robinhood import Robinhood


def get_robinhood_info(rh: Robinhood):
    """
    :param rh: The logged-in robinhood object
    :return: $ in stocks, $ not allocated
    """
    equity = rh.equity()
    positions = rh.positions()["results"]
    stock_assets = 0
    for position in positions:
        num_stocks = float(position["quantity"])
        symbol = rh.get_url(position["instrument"])["symbol"]

        quote = rh.get_quote(symbol)
        price_str = quote["last_extended_hours_trade_price"]
        if price_str is None:
            price_str = quote["last_trade_price"]

        stock_assets += float(price_str) * num_stocks
    return stock_assets, equity - stock_assets


def make_transaction(amount, budget_id, account_id,
                     payee=None,
                     memo=None,
                     date=None,
                     approved=False):
    amount = int(amount * 1000)
    date = date or datetime.datetime.now().isoformat()
    transaction = ynab_client.SaveTransaction(
        account_id=account_id,
        amount=amount,
        date=str(date),
        cleared="cleared",
        approved=approved
    ).to_dict()

    transaction["memo"] = memo if memo else None
    transaction["payee_name"] = payee if payee else "RobinhoodAPIScript"
    transactions_api = ynab_client.TransactionsApi()

    transactions_api.create_transaction(
        budget_id=budget_id,
        transaction=ynab_client.SaveTransactionWrapper(transaction))


def get_ynab_accounts(ynab_api_key, holding_acc_name, assets_acc_name):
    # Log in to YNAB
    config = ynab_client.Configuration()
    config.api_key_prefix["Authorization"] = "Bearer"
    config.api_key["Authorization"] = ynab_api_key
    client = ynab_client.ApiClient(configuration=config)

    # Get Budgets
    budgets_api = ynab_client.BudgetsApi()
    budget_id = budgets_api.get_budgets().data.budgets[0].id

    # Get accounts
    accounts_api = ynab_client.AccountsApi()
    accounts = accounts_api.get_accounts(budget_id=budget_id).data.accounts

    holding_acc = next(a for a in accounts if a.name == holding_acc_name)
    assets_acc = next(a for a in accounts if a.name == assets_acc_name)

    return budget_id, holding_acc, assets_acc


def parse_iso_date(date_str) -> datetime.datetime:
    return date_parser.parse(date_str).replace(tzinfo=None)


def is_old_date(date, last_update_date):
    if not isinstance(date, datetime.datetime):
        date = parse_iso_date(date)
    return (date - last_update_date).total_seconds() < 0


def sync_robinhood_to_ynab(
        robinhood_assets_acc: str,
        robinhood_holding_acc: str,
        ynab_api_key: str,
        robinhood_username: str,
        robinhood_pass: str,
        robinhood_qr_code: str):
    last_rh_update_date = datetime.datetime.now() - datetime.timedelta(hours=8)

    # Log in to Robinhood
    trader = Robinhood()
    login_successful = trader.login(
        username=robinhood_username,
        password=robinhood_pass,
        qr_code=robinhood_qr_code)

    if not login_successful:
        raise RuntimeError("Unable to log into Robinhood with the given "
                           "credentials!")

    #### Update Assets Account ####
    real_asset_dollars, real_holding_dollars = get_robinhood_info(trader)

    budget_id, holding_acc, assets_acc = get_ynab_accounts(
        ynab_api_key=ynab_api_key,
        holding_acc_name=robinhood_holding_acc,
        assets_acc_name=robinhood_assets_acc)

    # Make adjustments to the assets account
    asset_dollars = assets_acc.balance / 1000
    asset_adjustment = round(real_asset_dollars - asset_dollars, 3)
    if asset_adjustment != 0:
        logging.info("Making adjustment", asset_adjustment)
        make_transaction(
            amount=asset_adjustment,
            budget_id=budget_id,
            account_id=assets_acc.id,
            memo="Daily Account Adjustment",
            approved=True)
    else:
        logging.info("No Asset Adjustment Needed", asset_dollars,
                     asset_adjustment)

    #### Update Holdings Account ####
    # Update incoming and outgoing transfers made from within Robinhood
    transfers = trader.get_transfers()["results"]
    for transfer in transfers:
        # Only process transactions since the last time the script ran
        if is_old_date(transfer["created_at"], last_rh_update_date):
            continue

        # Add transaction to robinhood
        sign = 1 if transfer["direction"] == "deposit" else -1

        logging.info(f"Processing transaction {transfer}")
        make_transaction(
            amount=float(transfer["amount"]) * sign,
            budget_id=budget_id,
            date=transfer["created_at"],
            account_id=holding_acc.id,
            memo="Robinhood Transfer")

    # Update incoming and outgoing transfers made from external sources (debit)
    received_transfers = trader.get_received_transfers()["results"]
    for transfer in received_transfers:
        if is_old_date(transfer["created_at"], last_rh_update_date):
            continue

        if transfer["amount"]["currency_code"] != "USD":
            raise RuntimeError("'Cash Management' Transactions that are not "
                               "USD are not currently supported by this script!")

        direction = transfer['direction']
        if direction == 'debit':
            sign = -1
        elif direction == 'credit':
            sign = 1
        else:
            raise RuntimeError(f"Unsupported transaction direction {direction}")

        logging.info(f"Processing transaction {transfer}")
        make_transaction(
            amount=float(transfer['amount']['amount']) * sign,
            budget_id=budget_id,
            payee=transfer["originator_name"],
            date=transfer["created_at"],
            account_id=holding_acc.id)

    # Update internal stock purchases and sales
    order_history = trader.order_history()["results"]
    for order in order_history:
        filled = order["state"] == "filled"
        if not filled or len(order["executions"]) == 0:
            logging.info("Ignoring order because it is not marked 'filled'."
                         f" Order {order}")
            continue

        last_transaction_time = parse_iso_date(order["last_transaction_at"])
        if is_old_date(last_transaction_time, last_rh_update_date):
            continue

        symbol = trader.get_url(order["instrument"])["symbol"]

        outflow = 0
        for execution in order["executions"]:
            price = float(execution["price"])
            quantity = float(execution["quantity"])
            outflow += price * quantity

        sign = -1 if order["side"] == "buy" else 1
        logging.info("Adding transaction for stock order",
                     symbol, outflow * sign, last_transaction_time)
        make_transaction(
            amount=outflow * sign,
            budget_id=budget_id,
            account_id=holding_acc.id,
            date=last_transaction_time,
            memo=f"Robinhood {symbol} {'Purchased' if sign < 0 else 'Sold'}"
        )

    # Update dividend payouts
    dividends = trader.dividends()["results"]
    for dividend in dividends:
        # Make sure the divident actually went through
        if dividend["state"] == "voided":
            continue

        # Make sure this is a new transaction
        payment_date = parse_iso_date(dividend["paid_at"])
        if is_old_date(dividend["paid_at"], last_rh_update_date):
            continue

        symbol = trader.get_url(dividend["instrument"])["symbol"]
        logging.info(f"Adding Dividend Adjustment: {dividend}")
        make_transaction(
            amount=float(dividend["amount"]),
            budget_id=budget_id,
            account_id=holding_acc.id,
            memo=f"Dividend from {symbol}",
            date=payment_date)


def main(*args):
    """
    The only reason '*args' is accepted is so that Google Cloud Functions can
    run this script.
    """
    sync_robinhood_to_ynab(
        # Lot's of secrets

        robinhood_username=os.environ["RH_USERNAME"],
        robinhood_pass=os.environ["RH_PASS"],
        robinhood_qr_code=os.environ["RH_QR_CODE"],
        ynab_api_key=os.environ["YNAB_API_KEY"],

        # General Arguments
        robinhood_assets_acc=os.environ["RH_ASSETS_ACC"],
        robinhood_holding_acc=os.environ["RH_CHECKING_ACC"]
    )


if __name__ == "__main__":
    main("")
