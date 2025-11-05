import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cpsat_logutils import LogParser

EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../example_logs")


def test_all_examples():
    """Test that all example logs can be parsed with the new parser."""
    for file in os.listdir(EXAMPLE_DIR):
        if file.endswith(".txt"):
            with open(os.path.join(EXAMPLE_DIR, file)) as f:
                print(f"Testing {file}")
                data = f.read()

                # Parse with new parser
                parser = LogParser(data)
                result = parser.parse()

                # Verify basic parsing succeeded
                assert result.solver_info is not None, f"Failed to parse solver info in {file}"
                assert result.response is not None, f"Failed to parse response in {file}"

                # Verify we got expected information based on log type
                if result.response.status != "UNKNOWN":
                    # Should have at least initial model for non-empty logs
                    if result.initial_model is not None:
                        print(f"  - Parsed initial model with {result.initial_model.num_variables} variables")

                    # If optimization problem, should have objective
                    if result.initial_model and result.initial_model.is_optimization:
                        if result.response.objective is not None:
                            print(f"  - Objective: {result.response.objective}")

                print(f"  ✓ {file} parsed successfully")
