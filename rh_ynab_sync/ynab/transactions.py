import datetime

import ynab_client


def make_ynab_transaction(amount, budget_id, account_id,
                          payee=None,
                          memo=None,
                          date=None,
                          approved=False):
    print("Would have made transaction", account_id, memo, date, amount)
    return
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