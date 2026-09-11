"""Tests for orchestrator/__main__.py: the CLI entrypoint, run as a real subprocess."""

import subprocess
import sys

SAMPLE_DIR = "data/sample/olist"


def test_cli_runs_pipeline_and_exits_zero_on_success(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "orchestrator",
            SAMPLE_DIR,
            "e-commerce",
            "--no-postgres",
            "--analytical-path",
            str(tmp_path / "analytical.csv"),
            "--dashboard-layout-path",
            str(tmp_path / "layout.json"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "validation_status" in result.stdout
    assert "total_revenue" in result.stdout


def test_cli_prints_usage_and_exits_nonzero_with_missing_args():
    result = subprocess.run(
        [sys.executable, "-m", "orchestrator"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
