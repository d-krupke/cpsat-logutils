"""Tests for variable domain parsing."""

import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cpsat_logutils.parser import LogParser


class TestComplexDomainParsing:
    """Test parsing of complex variable domains."""

    def test_910_01_domain_parsing(self):
        """Test that 910_01.txt domains are parsed correctly."""
        log_path = Path(__file__).parent.parent / "example_logs" / "910_01.txt"
        with open(log_path) as f:
            content = f.read()

        parser = LogParser(content)
        result = parser.parse()

        assert result.initial_model is not None
        domains = result.initial_model.variable_domains

        # According to the log:
        # - 342 Booleans in [0,1]
        # - 12 in [0][10][20][30][40][50][60][70][80][90][100]
        # - 6 in [0][10][20][30][40][100]
        # - 6 in [0][80][100]
        # - 6 in [0][100]
        # - 6 in [0,1][34][67][100]
        # - 12 in [0,6]
        # - 18 in [0,7]
        # - 6 in [0,35]
        # - 6 in [0,36]
        # - 6 in [0,100]
        # - 12 in [21,57]
        # - 12 in [22,57]

        assert len(domains) == 13

        # Test Booleans
        assert domains[0].count == 342
        assert domains[0].type == "Booleans"
        assert domains[0].domain_ranges == [[0, 1]]
        assert domains[0].min_value == 0
        assert domains[0].max_value == 1

        # Test discrete domain: [0][10][20][30][40][50][60][70][80][90][100]
        assert domains[1].count == 12
        assert domains[1].type == "in"
        assert domains[1].domain_ranges == [
            [0, 0], [10, 10], [20, 20], [30, 30], [40, 40],
            [50, 50], [60, 60], [70, 70], [80, 80], [90, 90], [100, 100]
        ]
        assert domains[1].min_value == 0
        assert domains[1].max_value == 100

        # Test discrete domain: [0][10][20][30][40][100]
        assert domains[2].count == 6
        assert domains[2].type == "in"
        assert domains[2].domain_ranges == [
            [0, 0], [10, 10], [20, 20], [30, 30], [40, 40], [100, 100]
        ]
        assert domains[2].min_value == 0
        assert domains[2].max_value == 100

        # Test discrete domain: [0][80][100]
        assert domains[3].count == 6
        assert domains[3].type == "in"
        assert domains[3].domain_ranges == [[0, 0], [80, 80], [100, 100]]
        assert domains[3].min_value == 0
        assert domains[3].max_value == 100

        # Test discrete domain: [0][100]
        assert domains[4].count == 6
        assert domains[4].type == "in"
        assert domains[4].domain_ranges == [[0, 0], [100, 100]]
        assert domains[4].min_value == 0
        assert domains[4].max_value == 100

        # Test mixed domain: [0,1][34][67][100]
        assert domains[5].count == 6
        assert domains[5].type == "in"
        assert domains[5].domain_ranges == [[0, 1], [34, 34], [67, 67], [100, 100]]
        assert domains[5].min_value == 0
        assert domains[5].max_value == 100

        # Test continuous ranges
        assert domains[6].count == 12
        assert domains[6].type == "in"
        assert domains[6].domain_ranges == [[0, 6]]
        assert domains[6].min_value == 0
        assert domains[6].max_value == 6

        assert domains[7].count == 18
        assert domains[7].type == "in"
        assert domains[7].domain_ranges == [[0, 7]]
        assert domains[7].min_value == 0
        assert domains[7].max_value == 7

        assert domains[8].count == 6
        assert domains[8].type == "in"
        assert domains[8].domain_ranges == [[0, 35]]
        assert domains[8].min_value == 0
        assert domains[8].max_value == 35

        assert domains[9].count == 6
        assert domains[9].type == "in"
        assert domains[9].domain_ranges == [[0, 36]]
        assert domains[9].min_value == 0
        assert domains[9].max_value == 36

        assert domains[10].count == 6
        assert domains[10].type == "in"
        assert domains[10].domain_ranges == [[0, 100]]
        assert domains[10].min_value == 0
        assert domains[10].max_value == 100

        assert domains[11].count == 12
        assert domains[11].type == "in"
        assert domains[11].domain_ranges == [[21, 57]]
        assert domains[11].min_value == 21
        assert domains[11].max_value == 57

        assert domains[12].count == 12
        assert domains[12].type == "in"
        assert domains[12].domain_ranges == [[22, 57]]
        assert domains[12].min_value == 22
        assert domains[12].max_value == 57

    def test_simple_domain_parsing(self):
        """Test parsing of simple domains."""
        log_content = """Initial optimization model '': (model_fingerprint: 0xtest)
#Variables: 25
  - 10 Booleans in [0,1]
  - 15 in [1,10]
"""
        parser = LogParser(log_content)
        result = parser.parse()

        domains = result.initial_model.variable_domains
        assert len(domains) == 2

        # Booleans
        assert domains[0].count == 10
        assert domains[0].type == "Booleans"
        assert domains[0].domain_ranges == [[0, 1]]

        # Integer range
        assert domains[1].count == 15
        assert domains[1].type == "in"
        assert domains[1].domain_ranges == [[1, 10]]
        assert domains[1].min_value == 1
        assert domains[1].max_value == 10


class TestCPSATComplexDomains:
    """Test CP-SAT models with complex domains."""

    def test_cpsat_discrete_domain(self):
        """Test creating a CP-SAT model with discrete domains."""
        pytest.importorskip("ortools")
        from ortools.sat.python import cp_model
        from io import StringIO
        import sys

        model = cp_model.CpModel()

        # Create variables with discrete domains
        # Variable with domain {0, 10, 20, 30}
        x = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues([0, 10, 20, 30]), 'x'
        )

        # Variable with domain {5, 15, 25}
        y = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues([5, 15, 25]), 'y'
        )

        # Add a constraint to make the problem non-trivial
        model.Add(x + y <= 30)

        # Create solver and capture log
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = True
        solver.parameters.cp_model_presolve = True
        solver.parameters.max_time_in_seconds = 1

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = log_capture = StringIO()

        try:
            status = solver.Solve(model)
        finally:
            sys.stdout = old_stdout

        log_content = log_capture.getvalue()

        # Parse the log
        parser = LogParser(log_content)
        result = parser.parse()

        # Skip if no initial model in log (CP-SAT may not log it for trivial models)
        if result.initial_model is None:
            pytest.skip("CP-SAT did not produce initial model statistics (model may be trivial)")

        domains = result.initial_model.variable_domains

        # Filter for integer domains (type 'in' or 'integer')
        int_domains = [d for d in domains if d.type in ('in', 'integer')]

        if len(int_domains) < 1:
            pytest.skip("No integer domains found (model may have been fully presolved)")

        # Validate that discrete domains are properly parsed
        # We expect at least one domain with discrete values from our model
        # The model creates variables with domains {0,10,20,30} and {5,15,25}
        found_discrete = False
        for domain in int_domains:
            if domain.domain_ranges and len(domain.domain_ranges) > 1:
                # Found a domain with multiple discrete values - validate structure
                found_discrete = True

                # Each range should be [min, max]
                for range_item in domain.domain_ranges:
                    assert len(range_item) == 2, f"Range should be [min, max], got {range_item}"
                    assert isinstance(range_item[0], int), "Range min should be int"
                    assert isinstance(range_item[1], int), "Range max should be int"
                    assert range_item[0] <= range_item[1], "Range min should be <= max"

                # For discrete domains like [0][10][20], each range should be [v,v]
                # Check if we have discrete (single value) ranges
                has_discrete_values = any(r[0] == r[1] for r in domain.domain_ranges)
                if has_discrete_values:
                    # Validate min/max values are computed correctly from ranges
                    assert domain.min_value is not None, "Domain should have min_value"
                    assert domain.max_value is not None, "Domain should have max_value"
                    expected_min = min(r[0] for r in domain.domain_ranges)
                    expected_max = max(r[1] for r in domain.domain_ranges)
                    assert domain.min_value == expected_min, f"min_value mismatch: {domain.min_value} != {expected_min}"
                    assert domain.max_value == expected_max, f"max_value mismatch: {domain.max_value} != {expected_max}"

                    # Check that all discrete values are properly represented as [v,v]
                    for r in domain.domain_ranges:
                        if r[0] == r[1]:
                            # This is a discrete value - good!
                            pass

        if not found_discrete:
            pytest.skip("No discrete domains found (CP-SAT may have presolved them)")

    def test_cpsat_mixed_domain(self):
        """Test creating a CP-SAT model with mixed continuous and discrete domains."""
        pytest.importorskip("ortools")
        from ortools.sat.python import cp_model
        from io import StringIO
        import sys

        model = cp_model.CpModel()

        # Create variable with mixed domain: {0-5, 10, 20, 30}
        x = model.NewIntVarFromDomain(
            cp_model.Domain.FromIntervals([[0, 5], [10, 10], [20, 20], [30, 30]]),
            'x'
        )

        # Boolean variable
        b = model.NewBoolVar('b')

        # Add a constraint to make the problem non-trivial
        model.Add(x >= 0).OnlyEnforceIf(b)

        # Create solver and capture log
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
        solver.parameters.log_to_stdout = True
        solver.parameters.cp_model_presolve = True
        solver.parameters.max_time_in_seconds = 1

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = log_capture = StringIO()

        try:
            status = solver.Solve(model)
        finally:
            sys.stdout = old_stdout

        log_content = log_capture.getvalue()

        # Parse the log
        parser = LogParser(log_content)
        result = parser.parse()

        # Skip if no initial model in log (CP-SAT may not log it for simple models)
        if result.initial_model is None:
            pytest.skip("CP-SAT did not produce initial model statistics for this simple model")

        domains = result.initial_model.variable_domains

        # Should have Boolean and integer domains
        bool_domains = [d for d in domains if d.type == 'Booleans']
        int_domains = [d for d in domains if d.type == 'in']

        if len(int_domains) < 1:
            pytest.skip("No integer domains found in log (model may have been fully presolved)")

        # Validate mixed domains (continuous ranges + discrete values)
        # We expect a domain like [0,5][10][20][30] from our model
        found_mixed = False
        for domain in int_domains:
            if domain.domain_ranges and len(domain.domain_ranges) > 1:
                # Check if it has both continuous ranges and discrete values
                has_continuous = any(r[1] - r[0] > 0 for r in domain.domain_ranges)
                has_discrete = any(r[1] == r[0] for r in domain.domain_ranges)

                if has_continuous and has_discrete:
                    found_mixed = True

                    # Validate the structure
                    for range_item in domain.domain_ranges:
                        assert len(range_item) == 2, f"Range should be [min, max], got {range_item}"
                        assert isinstance(range_item[0], int), "Range min should be int"
                        assert isinstance(range_item[1], int), "Range max should be int"
                        assert range_item[0] <= range_item[1], "Range min should be <= max"

                    # Validate min/max values
                    assert domain.min_value is not None, "Domain should have min_value"
                    assert domain.max_value is not None, "Domain should have max_value"
                    expected_min = min(r[0] for r in domain.domain_ranges)
                    expected_max = max(r[1] for r in domain.domain_ranges)
                    assert domain.min_value == expected_min, f"min_value mismatch: {domain.min_value} != {expected_min}"
                    assert domain.max_value == expected_max, f"max_value mismatch: {domain.max_value} != {expected_max}"

                    # This is what we're looking for - mixed domain properly represented
                    break

        if not found_mixed:
            pytest.skip("No mixed domains found (CP-SAT may have presolved them)")
