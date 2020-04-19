import ynab_client


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