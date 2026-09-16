"""One-off script: builds data/sample/banking/ from data/raw/berka/.

Mirrors the role of data/sample/olist/: a small, git-friendly subset used
by tests and local dev. Selects a fixed random sample of accounts (seed=42)
plus every row in related tables that those accounts reference -- same
approach as the Olist sample's order-based selection.

Run once: `python scripts/build_banking_sample.py`
"""

import os

import pandas as pd

RAW_DIR = "data/raw/berka"
SAMPLE_DIR = "data/sample/banking"
SEED = 42
N_ACCOUNTS = 25


def main() -> None:
    account = pd.read_csv(os.path.join(RAW_DIR, "account.csv"), sep=";")
    disp = pd.read_csv(os.path.join(RAW_DIR, "disp.csv"), sep=";")
    client = pd.read_csv(os.path.join(RAW_DIR, "client.csv"), sep=";")
    district = pd.read_csv(os.path.join(RAW_DIR, "district.csv"), sep=";")
    loan = pd.read_csv(os.path.join(RAW_DIR, "loan.csv"), sep=";")
    card = pd.read_csv(os.path.join(RAW_DIR, "card.csv"), sep=";")
    order = pd.read_csv(os.path.join(RAW_DIR, "order.csv"), sep=";")
    trans = pd.read_csv(os.path.join(RAW_DIR, "trans.csv"), sep=";")

    sampled_accounts = account.sample(n=N_ACCOUNTS, random_state=SEED)
    account_ids = set(sampled_accounts["account_id"])

    sampled_trans = trans[trans["account_id"].isin(account_ids)]
    sampled_disp = disp[disp["account_id"].isin(account_ids)]
    sampled_loan = loan[loan["account_id"].isin(account_ids)]
    sampled_card = card[card["disp_id"].isin(sampled_disp["disp_id"])]
    sampled_order = order[order["account_id"].isin(account_ids)]

    client_ids = set(sampled_disp["client_id"])
    sampled_client = client[client["client_id"].isin(client_ids)]

    district_ids = set(sampled_accounts["district_id"]) | set(sampled_client["district_id"])
    sampled_district = district[district["A1"].isin(district_ids)]

    os.makedirs(SAMPLE_DIR, exist_ok=True)
    tables = {
        "account": sampled_accounts,
        "client": sampled_client,
        "disp": sampled_disp,
        "district": sampled_district,
        "loan": sampled_loan,
        "card": sampled_card,
        "order": sampled_order,
        "trans": sampled_trans,
    }
    for name, df in tables.items():
        df.to_csv(os.path.join(SAMPLE_DIR, f"{name}.csv"), sep=";", index=False)
        print(f"{name}: {len(df)} rows")

    months = pd.to_datetime(sampled_trans["date"].astype(str), format="%y%m%d").dt.to_period("M")
    print(f"trans spans {months.nunique()} distinct months: {sorted(months.unique().astype(str))}")


if __name__ == "__main__":
    main()
