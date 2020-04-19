import os

from rh_ynab_sync import sync_robinhood_to_ynab


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
        robinhood_holding_acc=os.environ["RH_CHECKING_ACC"],

        # Params
        oldest_transaction_day_age=os.environ.get("SINCE_DAYS_OLD", 13)
    )


if __name__ == "__main__":
    main("")
