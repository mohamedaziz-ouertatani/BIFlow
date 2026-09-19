# Data Quality Report Template

**Owner:** Person A (Data Engineering Agent)

Used to render `shared.schemas.data_contracts.ProfilingReport` into a
human-readable report. The sections below match `ProfilingReport`'s fields
(`n_rows`, `n_columns`, `duplicate_rows`, `column_types`, `missing_values`,
`anomalies`) plus `CleanedDataset.transformations_applied`. Nothing renders
it automatically yet: the dashboard's audit bay and the PDF report show the
same facts, and this file is the reference layout if a standalone report is
ever needed.

## Dataset: <dataset_name>

- **Rows:** <n_rows>
- **Columns:** <n_columns>
- **Duplicate rows:** <duplicate_rows>

### Column types

| Column | Type |
|---|---|
| ... | ... |

### Missing values

| Column | % missing |
|---|---|
| ... | ... |

### Anomalies

- <anomaly 1>
- <anomaly 2>

### Transformations applied

- <transformation 1>
- <transformation 2>
