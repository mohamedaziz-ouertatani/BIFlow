"""CLI entrypoint for running the BIFlow pipeline for real.

Usage:
    python -m orchestrator <dataset_path> <business_domain> [options]

Example:
    python -m orchestrator data/sample/olist e-commerce
"""

import argparse
import sys

from orchestrator.orchestrator import BIFlowOrchestrator, PipelineStageError
from shared.config import get_settings
from shared.schemas.data_contracts import AuditReport, RawDatasetRef


# Parses CLI arguments for running the pipeline (dataset path, domain, output overrides).
def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m orchestrator", description="Run the BIFlow pipeline end-to-end."
    )
    parser.add_argument("dataset_path", help="Directory containing the raw dataset CSVs")
    parser.add_argument("business_domain", help='e.g. "e-commerce"')
    parser.add_argument(
        "--dataset-name", default=None, help="Defaults to the dataset_path's directory name"
    )
    parser.add_argument("--analytical-path", default=None)
    parser.add_argument("--dashboard-layout-path", default=None)
    parser.add_argument(
        "--no-postgres",
        action="store_true",
        help="Skip loading the analytical table into Postgres (loads by default)",
    )
    return parser.parse_args(argv)


# Prints the final AuditReport's validation status, traceability log, and explanations.
def print_report(report: AuditReport) -> None:
    print(f"validation_status: {report.validation_status}")
    print()
    print("traceability_log:")
    for line in report.traceability_log:
        print(f"  - {line}")
    print()
    print("explanations:")
    for subject, explanation in report.explanations.items():
        print(f"  {subject}: {explanation}")


# CLI entrypoint: parses args, runs the pipeline, prints the report, and returns an exit code.
def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    orchestrator_kwargs = {}
    if args.analytical_path:
        orchestrator_kwargs["analytical_path"] = args.analytical_path
    if args.dashboard_layout_path:
        orchestrator_kwargs["dashboard_layout_path"] = args.dashboard_layout_path
    if not args.no_postgres:
        orchestrator_kwargs["database_url"] = get_settings().database_url

    orchestrator = BIFlowOrchestrator(**orchestrator_kwargs)
    raw_dataset = RawDatasetRef(
        dataset_path=args.dataset_path,
        dataset_name=args.dataset_name or args.dataset_path.rstrip("/\\").rsplit("/", 1)[-1],
        business_domain=args.business_domain,
    )

    try:
        report = orchestrator.run_pipeline(raw_dataset)
    except PipelineStageError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print_report(report)

    return 1 if report.validation_status == "failed" else 0


if __name__ == "__main__":
    sys.exit(main())
