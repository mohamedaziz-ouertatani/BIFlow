"""Data Engineering Agent entrypoint.

Owns profiling, quality/cleaning, and ETL. Called by the Orchestrator with a
RawDatasetRef and returns a CleanedDataset.
"""

from agents.data_engineering_agent.cleaner import clean_tables
from agents.data_engineering_agent.etl import run_etl
from agents.data_engineering_agent.profiler import load_all_tables, profile_dataset
from shared.schemas.data_contracts import CleanedDataset, RawDatasetRef

DEFAULT_OUTPUT_PATH = "data/processed/olist_orders_analytical.csv"


class DataEngineeringAgent:
    """Profiles, cleans, and transforms raw datasets for downstream agents.

    Postgres loading is opt-in: pass `database_url` to also load the
    analytical table into Postgres (in addition to the CSV, which remains
    the interchange format between agents). Leaving it as None (the
    default) keeps this CSV-only, so callers/tests that don't need Postgres
    aren't coupled to a live database.
    """

    # Stores the CSV output path and optional Postgres connection string.
    def __init__(self, output_path: str = DEFAULT_OUTPUT_PATH, database_url: str | None = None) -> None:
        self.output_path = output_path
        self.database_url = database_url

    # Runs profiling, cleaning, and ETL, returning the CleanedDataset for downstream agents.
    def run(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        """Runs profiling, cleaning, and ETL on the given raw dataset."""
        profiling_report = profile_dataset(raw_dataset)

        tables = load_all_tables(raw_dataset.dataset_path, raw_dataset.business_domain)
        cleaned_tables, clean_transformations = clean_tables(tables, raw_dataset.business_domain)
        output_path, etl_transformations = run_etl(
            cleaned_tables,
            self.output_path,
            raw_dataset.business_domain,
            database_url=self.database_url,
        )

        return CleanedDataset(
            dataset_path=output_path,
            data_quality_report=profiling_report,
            transformations_applied=clean_transformations + etl_transformations,
            business_domain=raw_dataset.business_domain,
        )
