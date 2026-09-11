"""Dataset profiling logic for the Data Engineering Agent."""

from shared.schemas.data_contracts import ProfilingReport, RawDatasetRef


def profile_dataset(raw_dataset: RawDatasetRef) -> ProfilingReport:
    """Profiles a raw dataset: row/column counts, types, missing values, anomalies.

    TODO (owner): implement using Pandas/Polars — load dataset from
    raw_dataset.dataset_path, compute schema, missing-value ratios per
    column, duplicate row count, and flag anomalies (e.g. outliers,
    inconsistent types).
    """
    raise NotImplementedError("TODO: implement dataset profiling")
