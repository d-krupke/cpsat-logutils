"""
Regression tests to ensure parsing remains consistent.

These tests compare current parsing output against saved JSON baselines.
If parsing changes, the test will show differences and provide instructions
for updating baselines if the changes are intentional.
"""

import json
import pytest
from pathlib import Path
from cpsat_logutils import LogParser


EXAMPLE_DIR = Path(__file__).parent.parent / "example_logs"
JSON_DIR = EXAMPLE_DIR / "parsed_json"
EXAMPLE_LOGS = sorted(EXAMPLE_DIR.glob("*.txt"))


def normalize_for_comparison(data):
    """
    Normalize data for comparison.

    Removes fields that may change between runs or are not critical
    for regression testing.
    """
    if isinstance(data, dict):
        # Create a copy to avoid modifying original
        result = {}
        for key, value in data.items():
            # Skip line_references as we're improving those
            if key == "line_references":
                continue
            result[key] = normalize_for_comparison(value)
        return result
    elif isinstance(data, list):
        return [normalize_for_comparison(item) for item in data]
    else:
        return data


class TestParsingRegression:
    """Test that parsing output remains consistent across changes."""

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_parsing_matches_baseline(self, log_file):
        """Verify current parsing matches saved JSON baseline."""
        json_file = JSON_DIR / f"{log_file.stem}.json"

        if not json_file.exists():
            pytest.skip(f"No baseline JSON for {log_file.name}")

        # Parse current
        with open(log_file) as f:
            current_result = LogParser(f.read()).parse()
        current_data = json.loads(current_result.model_dump_json())

        # Load baseline
        with open(json_file) as f:
            baseline_data = json.load(f)

        # Normalize both for comparison (excluding line_references)
        current_normalized = normalize_for_comparison(current_data)
        baseline_normalized = normalize_for_comparison(baseline_data)

        # Compare
        if current_normalized != baseline_normalized:
            # Find differences
            differences = find_differences(baseline_normalized, current_normalized, "")

            error_msg = (
                f"\n{'='*70}\n"
                f"PARSING REGRESSION DETECTED in {log_file.name}\n"
                f"{'='*70}\n\n"
                f"Differences found:\n"
            )

            for diff in differences[:10]:  # Show first 10 differences
                error_msg += f"  • {diff}\n"

            if len(differences) > 10:
                error_msg += f"  ... and {len(differences) - 10} more differences\n"

            error_msg += (
                f"\n{'='*70}\n"
                f"If these changes are INTENTIONAL:\n"
                f"{'='*70}\n"
                f"1. Review the differences above carefully\n"
                f"2. Update the baseline by running:\n"
                f"   python3 -c \"from pathlib import Path; from cpsat_logutils import LogParser; "
                f"Path('example_logs/parsed_json/{log_file.stem}.json').write_text("
                f"LogParser(Path('{log_file}').read_text()).parse().model_dump_json(indent=2))\"\n"
                f"\n"
                f"Or update ALL baselines:\n"
                f"   python3 scripts/update_parsing_baselines.py\n"
                f"{'='*70}\n"
            )

            pytest.fail(error_msg)


def find_differences(baseline, current, path):
    """Find differences between two data structures."""
    differences = []

    if type(baseline) != type(current):
        differences.append(f"{path}: Type changed from {type(baseline).__name__} to {type(current).__name__}")
        return differences

    if isinstance(baseline, dict):
        all_keys = set(baseline.keys()) | set(current.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key

            if key not in baseline:
                differences.append(f"{new_path}: NEW field added")
            elif key not in current:
                differences.append(f"{new_path}: Field REMOVED")
            else:
                differences.extend(find_differences(baseline[key], current[key], new_path))

    elif isinstance(baseline, list):
        if len(baseline) != len(current):
            differences.append(f"{path}: List length changed from {len(baseline)} to {len(current)}")

        for i in range(min(len(baseline), len(current))):
            differences.extend(find_differences(baseline[i], current[i], f"{path}[{i}]"))

    else:
        if baseline != current:
            # For numbers, check if they're close (floating point tolerance)
            if isinstance(baseline, (int, float)) and isinstance(current, (int, float)):
                if abs(baseline - current) > 1e-6:
                    differences.append(f"{path}: Value changed from {baseline} to {current}")
            else:
                differences.append(f"{path}: Value changed from {baseline} to {current}")

    return differences


def test_all_example_logs_have_baselines():
    """Ensure all example logs have corresponding JSON baselines."""
    missing = []
    for log_file in EXAMPLE_LOGS:
        json_file = JSON_DIR / f"{log_file.stem}.json"
        if not json_file.exists():
            missing.append(log_file.name)

    if missing:
        pytest.fail(
            f"Missing JSON baselines for: {', '.join(missing)}\n"
            f"Run: python3 scripts/generate_parsing_baselines.py"
        )
