"""Data Engineering Agent entrypoint.

Owns profiling, quality/cleaning, and ETL. Called by the Orchestrator with a
RawDatasetRef and returns a CleanedDataset.
"""

from agents.data_engineering_agent.cleaner import clean_dataset
from agents.data_engineering_agent.etl import run_etl
from agents.data_engineering_agent.profiler import profile_dataset
from shared.schemas.data_contracts import CleanedDataset, RawDatasetRef


class DataEngineeringAgent:
    """
    Profiles, cleans, and transforms raw datasets for downstream agents.

    TODO (owner): implement the full profile -> clean -> ETL flow, deciding
    what counts as a blocking data-quality issue vs. a warning.
    """

    def run(self, raw_dataset: RawDatasetRef) -> CleanedDataset:
        """Runs profiling, cleaning, and ETL on the given raw dataset.

        TODO (owner): implement — call profile_dataset, then clean_dataset,
        then run_etl, and assemble the CleanedDataset result.
        """
        raise NotImplementedError("TODO: implement Data Engineering Agent pipeline")
