from dateutil import parser as dateparse
from datetime import datetime, timedelta
import socket
import argparse

from bunq.sdk.client import Pagination
from bunq.sdk.context import ApiEnvironmentType, ApiContext, BunqContext
from bunq.sdk.exception import BunqException
from bunq.sdk.model.generated import endpoint

from secret import API_KEY, ACCOUNT_ID


# Get current date and
epoch = datetime.utcfromtimestamp(0)

# Provide helper function for time diffs
def unix_time(dt):
    return (dt - epoch).total_seconds()


def iterate_transactions(account):

    # Loop until end of account
    last_result = None
    while last_result == None or last_result.value != []:
        if last_result == None:
            # Initialize pagination object
            pagination = Pagination()
            pagination.count = 100
            params = pagination.url_params_count_only
        else:
            # When there is already a paged request, you can get the next page from it, no need to create it ourselfs:
            try:
                params = last_result.pagination.url_params_previous_page
            except BunqException:
                break

        # Fetch last result
        last_result = endpoint.Payment.list(params=params, monetary_account_id=account)

        # Exit at last result
        if len(last_result.value) == 0:
            break

        # The data is in the '.value' field.
        for payment in last_result.value:
            yield payment


def fetch_transactions(days):

    # Ensure the whole account is included
    print("\nLoading Bunq API environment...")
    env = ApiEnvironmentType.PRODUCTION

    # Authenticate session & load context
    print("Authenticating and loading context...")
    api_context = ApiContext(
        ApiEnvironmentType.PRODUCTION, API_KEY, socket.gethostname()
    )
    api_context.ensure_session_active()
    BunqContext.load_api_context(api_context)

    # Get user info
    print("Loading user info...")
    user = endpoint.User.get().value.get_referenced_object()

    # Fetch account detials
    account = endpoint.MonetaryAccountJoint.get(ACCOUNT_ID).value
    description = account.description
    balance = account.balance.value

    print(
        f"\nLoaded account '{description}' with current balance of \N{euro sign}{balance}"
    )

    start_date = datetime.now() - timedelta(days)
    transactions = []
    for transaction in iterate_transactions(ACCOUNT_ID):

        transaction_dict = {
            "timestamp": transaction.created,
            "amount": transaction.amount.value,
            "description": transaction.description.replace("\r", "").replace("\n", " "),
            "counterparty": transaction.counterparty_alias.label_monetary_account.display_name,
        }

        # Still in range
        if dateparse.parse(transaction.created) >= start_date:
            transactions.append(transaction_dict)
        else:
            break

    print(transactions)


if __name__ == "__main__":

    # Fetch day offset argument
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--days", action="store", help="Days of transactions to fetch"
    )
    args = parser.parse_args()
    days = args.days if args.days else 7

    fetch_transactions(days)
