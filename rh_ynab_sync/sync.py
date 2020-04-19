import logging
import datetime
from typing import List
from datetime import datetime as Datetime

from Robinhood import Robinhood
from ynab_client import Account

from .robinhood.assets import get_total_assets_value
from .robinhood.transfers import get_all_transfers, Transfer
from .ynab.accounts import get_ynab_accounts
from .ynab.transactions import make_ynab_transaction, TransactionsLookup


def sync_assets_account(assets_acc: Account, trader: Robinhood, budget_id: int):
    """
    :param assets_acc: The ynab_client Account API object
    :param trader: The Robinhood trader API object
    :param budget_id: The ID of the budget being worked with
    :return:
    """

    real_asset_dollars, _ = get_total_assets_value(trader)
    asset_dollars = assets_acc.balance / 1000
    asset_adjustment = round(real_asset_dollars - asset_dollars, 3)
    if abs(asset_adjustment) >= 0.01:
        logging.info(f"Making adjustment {asset_adjustment}")
        make_ynab_transaction(
            amount=asset_adjustment,
            budget_id=budget_id,
            account_id=assets_acc.id,
            memo="Daily Account Adjustment",
            approved=True)
    else:
        logging.info("No Asset Adjustment Needed")


def sync_holdings_account(since_date: Datetime, trader: Robinhood,
                          budget_id: int, account_id: int):
    """
    :param since_date: The number of hours
    :param trader: The Robinhood trader API object
    :param account_id: The ynab_client Account ID "Holding" account. This is
    the account that represents Robinhood Cash transactions.
    :param budget_id: The ID of the budget being worked with
    :return:
    """
    rh_transfers_since_date: List[Transfer] = [
        t for t in get_all_transfers(trader=trader)
        if not t.is_older_than(since_date)]

    if len(rh_transfers_since_date) == 0:
        # Exit early if there are no transactions between these dates
        return

    ynab_transactions = TransactionsLookup(
        budget_id=budget_id,
        account_id=account_id,
        since_date=since_date)

    for transfer in rh_transfers_since_date:
        logging.info(f"Adding new transfer {transfer}")
        ynab_transaction = ynab_transactions.pop_matching(transfer.amount)
        if ynab_transaction is not None:
            # This transaction has already been added to YNAB
            continue
        make_ynab_transaction(
            amount=transfer.amount,
            budget_id=budget_id,
            account_id=account_id,
            memo=transfer.memo,
            date=transfer.date,
            approved=False)



def sync_robinhood_to_ynab(
        robinhood_assets_acc: str,
        robinhood_holding_acc: str,
        ynab_api_key: str,
        robinhood_username: str,
        robinhood_pass: str,
        robinhood_qr_code: str):
    # Log in to Robinhood
    trader = Robinhood()
    login_successful = trader.login(
        username=robinhood_username,
        password=robinhood_pass,
        qr_code=robinhood_qr_code)

    if not login_successful:
        raise RuntimeError("Unable to log into Robinhood with the given "
                           "credentials!")

    # Get the 'holding' and 'assets' budget categories from YNAB
    budget_id, holding_acc, assets_acc = get_ynab_accounts(
        ynab_api_key=ynab_api_key,
        holding_acc_name=robinhood_holding_acc,
        assets_acc_name=robinhood_assets_acc)

    sync_assets_account(
        assets_acc=assets_acc,
        trader=trader,
        budget_id=budget_id)

    since_date = Datetime.now() - datetime.timedelta(days=14)
    sync_holdings_account(
        since_date=since_date,
        trader=trader,
        budget_id=budget_id,
        account_id=holding_acc.id)
