import socket

from bunq.sdk.client import Pagination
from bunq.sdk.context import ApiEnvironmentType, ApiContext, BunqContext
from bunq.sdk.exception import BunqException
from bunq.sdk.model.generated import endpoint

from secret import API_KEY


def list_accounts():
    """
    List all shared accounts (id, name, balance)
    """

    # Load API
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
    print("Loading user info...\n")
    user = endpoint.User.get().value.get_referenced_object()

    # Fetch account detials
    accounts = endpoint.MonetaryAccountJoint.list().value
    for account in accounts:
        print(
            f"[{account.id_}] {account.description} (\N{euro sign}{account.balance.value})"
        )


if __name__ == "__main__":
    list_accounts()
