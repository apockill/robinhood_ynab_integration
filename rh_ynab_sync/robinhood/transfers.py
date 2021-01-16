import dateutil.parser as date_parser
import datetime
import logging
from typing import List, Optional
from enum import Enum

from Robinhood import Robinhood


class Transfer:
    class TransferType(Enum):
        internal_transfers = "Internal Transfers"
        received_transfers = "External Transfers"
        settled_transactions = "Settled Transactions"
        dividend = "Dividends"
        interest = "Interest"
        stock_purchase = "Stock Purchase"

    def __init__(self, amount, date, transfer_type: TransferType, memo=None):
        self.date: datetime.datetime = self.parse_iso_date(date)
        self.amount: float = float(amount)
        self.transfer_type: Transfer.TransferType = transfer_type
        self.memo: str = memo
        if self.memo is None:
            self.memo = f"Transfer Type: {self.transfer_type.value}"

    def __repr__(self):
        return f"Transfer(amount={self.amount}, " \
               f"date={self.date}," \
               f"transfer_type={self.transfer_type}," \
               f"memo={self.memo})"

    @staticmethod
    def parse_iso_date(date_str) -> datetime.datetime:
        return date_parser.parse(date_str).replace(tzinfo=None)

    def is_older_than(self, comparison_date: datetime.datetime):
        return (self.date - comparison_date).total_seconds() < 0


def get_signed_amount(amount, key, pos, neg):
    if key == pos:
        return float(amount)
    elif key == neg:
        return float(amount) * -1
    else:
        raise RuntimeError(f"The key {key} didn't match either {pos} or {neg}")


def get_all_transfers(trader: Robinhood) -> List[Transfer]:
    all_transfers: List[Transfer] = []

    # These are transfers that were initiated from within RH to an outside acc
    transfers = trader.get_transfers()["results"]
    for transfer in transfers:
        sign = 1 if transfer["direction"] == "deposit" else -1
        all_transfers.append(
            Transfer(
                amount=float(transfer["amount"]) * sign,
                date=transfer["created_at"],
                transfer_type=Transfer.TransferType.internal_transfers))

    # This is money from interest
    sweeps = trader.get_sweeps()["results"]
    for sweep in sweeps:
        assert sweep["amount"]["currency_code"] == "USD"
        amount = get_signed_amount(
            sweep["amount"]["amount"],
            key=sweep["direction"],
            pos="credit", neg="debit")
        all_transfers.append(
            Transfer(
                amount=amount,
                date=sweep["pay_date"],
                transfer_type=Transfer.TransferType.interest))

    # These are transfers that were initiated from an outside account to RH
    received_transfers = trader.get_received_transfers()["results"]
    for transfer in received_transfers:
        assert transfer["amount"]["currency_code"] == "USD"
        amount = get_signed_amount(
            transfer["amount"]["amount"],
            key=transfer["direction"],
            pos="credit", neg="debit")

        all_transfers.append(
            Transfer(
                amount=amount,
                date=transfer["created_at"],
                transfer_type=Transfer.TransferType.received_transfers))

    # These are transfers initiated by the RH Cash debit card
    settled_transactions = trader.get_settled_transactions()["results"]
    for transaction in settled_transactions:
        if transaction["source_type"] != "settled_card_transaction":
            continue
        assert transaction["amount"]["currency_code"] == "USD"
        amount = get_signed_amount(amount=transaction["amount"]["amount"],
                                   key=transaction["direction"],
                                   pos="credit", neg="debit")
        all_transfers.append(
            Transfer(
                amount=amount,
                date=transaction["initiated_at"],
                transfer_type=Transfer.TransferType.settled_transactions))

    # Update internal stock purchases and sales
    order_history = trader.order_history()["results"]
    for order in order_history:
        if not order["state"] == "filled" or len(order["executions"]) == 0:
            logging.info("Ignoring order because it is not marked 'filled'."
                         f" Order {order}")
            continue

        symbol = trader.get_url(order["instrument"])["symbol"]

        outflow = 0
        for execution in order["executions"]:
            price = float(execution["price"])
            quantity = float(execution["quantity"])
            outflow += price * quantity

        amount = get_signed_amount(
            outflow,
            key=order["side"],
            pos="sell", neg="buy")
        memo = f"Robinhood {symbol} {'Purchased' if amount < 0 else 'Sold'}"

        all_transfers.append(
            Transfer(
                amount=amount,
                date=order["last_transaction_at"],
                transfer_type=Transfer.TransferType.stock_purchase,
                memo=memo))

    # Update dividend payouts
    dividends = trader.dividends()["results"]
    for dividend in dividends:
        # Make sure the divident actually went through (could be voided/pending)
        if dividend["state"] != "paid":
            continue

        symbol = trader.get_url(dividend["instrument"])["symbol"]
        all_transfers.append(
            Transfer(
                amount=dividend["amount"],
                memo=f"Dividend from {symbol}",
                date=dividend["paid_at"],
                transfer_type=Transfer.TransferType.dividend))

    all_transfers.sort(key=lambda t: t.date)
    return all_transfers
