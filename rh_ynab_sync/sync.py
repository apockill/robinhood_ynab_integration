import datetime
import logging
from typing import List

import ynab_client
from Robinhood import Robinhood

from .transfers import get_all_transfers, Transfer


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
    raise RuntimeError("What?")

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


def sync_robinhood_to_ynab(
        robinhood_assets_acc: str,
        robinhood_holding_acc: str,
        ynab_api_key: str,
        robinhood_username: str,
        robinhood_pass: str,
        robinhood_qr_code: str):
    last_rh_update_date = datetime.datetime.now() - datetime.timedelta(
        hours=1000)  # TODO: Do not commit.

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
        logging.info(f"Making adjustment {asset_adjustment}")
        make_transaction(
            amount=asset_adjustment,
            budget_id=budget_id,
            account_id=assets_acc.id,
            memo="Daily Account Adjustment",
            approved=True)
    else:
        logging.info("No Asset Adjustment Needed")

    all_transfers: List[Transfer] = get_all_transfers(trader=trader)
    for transfer in all_transfers:
        print(transfer)
