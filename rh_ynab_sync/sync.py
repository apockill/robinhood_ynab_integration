import datetime
import logging
from typing import List

from Robinhood import Robinhood

from .robinhood.assets import get_total_assets_value
from .robinhood.transfers import get_all_transfers, Transfer
from .ynab.accounts import get_ynab_accounts
from .ynab.transactions import make_ynab_transaction


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

    # Get the 'holding' and 'assets' budget categories from YNAB
    budget_id, holding_acc, assets_acc = get_ynab_accounts(
        ynab_api_key=ynab_api_key,
        holding_acc_name=robinhood_holding_acc,
        assets_acc_name=robinhood_assets_acc)

    #### Update Assets Account ####
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

    all_transfers: List[Transfer] = get_all_transfers(trader=trader)
    for transfer in all_transfers:
        print(transfer)
        if transfer.is_older_than(last_rh_update_date):
            logging.info(f"Ignoring old transfer {transfer}")
            continue
        logging.info(f"Adding new transfer {transfer}")
        make_ynab_transaction(
            amount=transfer.amount,
            budget_id=budget_id,
            account_id=holding_acc.id,
            memo=transfer.memo,
            date=transfer.date,
            approved=False)
