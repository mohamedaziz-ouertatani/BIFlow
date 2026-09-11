"""ETL logic for the Data Engineering Agent."""


def run_etl(cleaned_dataset_path: str) -> list[str]:
    """Runs any final transform/load steps and returns the list of transformations applied.

    TODO (owner): implement — e.g. loading into PostgreSQL data model,
    derived-column computation, schema normalization. Return a list of
    human-readable transformation descriptions for CleanedDataset.transformations_applied.
    """
    raise NotImplementedError("TODO: implement ETL step")
