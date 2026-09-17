"""One-off script: builds data/sample/telco/ from data/raw/telco/.

Mirrors the role of data/sample/olist/ and data/sample/banking/: a small,
git-friendly subset used by tests and local dev. Unlike those two domains,
telco is a single flat table (one row per customer, no related tables to
join), so the sample is a plain random row sample.

Run once: `python scripts/build_telco_sample.py`
"""

import os

import pandas as pd

RAW_DIR = "data/raw/telco"
RAW_FILENAME = "WA_Fn-UseC_-Telco-Customer-Churn.csv"
SAMPLE_DIR = "data/sample/telco"
SEED = 42
N_CUSTOMERS = 500


# Samples N_CUSTOMERS customer rows and writes them as the telco sample dataset.
def main() -> None:
    customers = pd.read_csv(os.path.join(RAW_DIR, RAW_FILENAME))

    # Force-include every tenure=0/blank-TotalCharges row so the sample
    # actually exercises the cleaner's TotalCharges-coercion rule -- a
    # plain random sample of 500/7043 rows would include none of the 11.
    blank_total_charges = customers[customers["TotalCharges"] == " "]
    rest = customers.drop(blank_total_charges.index)
    sampled_rest = rest.sample(n=N_CUSTOMERS - len(blank_total_charges), random_state=SEED)
    sampled = pd.concat([blank_total_charges, sampled_rest]).sample(frac=1, random_state=SEED)

    os.makedirs(SAMPLE_DIR, exist_ok=True)
    out_path = os.path.join(SAMPLE_DIR, "customers.csv")
    sampled.to_csv(out_path, index=False)
    print(f"customers: {len(sampled)} rows")

    n_blank_total_charges = int((sampled["TotalCharges"] == " ").sum())
    print(f"rows with blank TotalCharges (tenure=0): {n_blank_total_charges}")


if __name__ == "__main__":
    main()
