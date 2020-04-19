import datetime
from typing import List
from datetime import datetime as Datetime

import ynab_client
from ynab_client import TransactionDetail


def make_ynab_transaction(amount, budget_id, account_id,
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


class TransactionsLookup:
    def __init__(self, budget_id, account_id, since_date: Datetime):
        """
        Minimize API calls. This class will search YNAB for transactions
        since a certain date. Then, with helper functions, it is easy to try
        to find matching transactions based on date and dollar value.
        """
        transactions_api = ynab_client.TransactionsApi()

        # Get all valid transactions
        self._transactions: List[TransactionDetail] = []
        transactions = transactions_api.get_transactions_by_account(
            budget_id=budget_id,
            account_id=account_id,
            since_date=str(since_date.isoformat())).data.transactions

        for transaction in transactions:
            if transaction.deleted:
                # Don't try to match with deleted transactions
                continue
            self._transactions.append(transaction)

    def pop_matching(self, amount):
        """Finds transactions that match the amount specified to within
        +-1 cent, and return said transaction."""

        def abs_difference(transaction):
            t1 = round(transaction.amount / 1000, 3)
            t2 = round(amount, 3)
            return round(abs(t1 - t2), 3)

        closest_transaction = min(self._transactions, key=abs_difference)

        # Allow a +-1 cent threshold (happens once in a blue moon)
        if abs_difference(closest_transaction) <= 0.01:
            return self._transactions.pop(
                self._transactions.index(closest_transaction))
