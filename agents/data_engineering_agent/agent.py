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
    """Profiles, cleans, and transforms raw datasets for downstream agents."""

    def __init__(self, output_path: str = DEFAULT_OUTPUT_PATH) -> None:
        self.output_path = output_path

    def run(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        """Runs profiling, cleaning, and ETL on the given raw dataset."""
        profiling_report = profile_dataset(raw_dataset)

        tables = load_all_tables(raw_dataset.dataset_path)
        cleaned_tables, clean_transformations = clean_tables(tables)
        output_path, etl_transformations = run_etl(cleaned_tables, self.output_path)

        return CleanedDataset(
            dataset_path=output_path,
            data_quality_report=profiling_report,
            transformations_applied=clean_transformations + etl_transformations,
        )
