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

        # Create solver and capture log
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
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

        # Verify domains are parsed
        assert result.initial_model is not None
        domains = result.initial_model.variable_domains

        # Should have at least the two integer domains we created
        # (may have more due to internal variables)
        int_domains = [d for d in domains if d.type == 'in']
        assert len(int_domains) >= 2

        # Check that we can find our discrete domains
        # Note: CP-SAT may reorder or consolidate domains
        found_discrete = False
        for domain in int_domains:
            if domain.domain_ranges and len(domain.domain_ranges) > 1:
                # Found a domain with multiple discrete values
                found_discrete = True
                # Verify it's represented as discrete ranges
                for range_item in domain.domain_ranges:
                    assert len(range_item) == 2

        # We should have found at least one discrete domain
        assert found_discrete, "No discrete domain found in parsed log"

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

        # Create solver and capture log
        solver = cp_model.CpSolver()
        solver.parameters.log_search_progress = True
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

        # Verify parsing worked
        assert result.initial_model is not None
        domains = result.initial_model.variable_domains

        # Should have Boolean and integer domains
        bool_domains = [d for d in domains if d.type == 'Booleans']
        int_domains = [d for d in domains if d.type == 'in']

        assert len(bool_domains) >= 1
        assert len(int_domains) >= 1

        # Check for mixed domains (continuous + discrete)
        found_mixed = False
        for domain in int_domains:
            if domain.domain_ranges and len(domain.domain_ranges) > 1:
                # Check if it has both continuous ranges and discrete values
                has_continuous = any(r[1] - r[0] > 0 for r in domain.domain_ranges)
                has_discrete = any(r[1] == r[0] for r in domain.domain_ranges)
                if has_continuous and has_discrete:
                    found_mixed = True
                    break

        # We should find a mixed domain
        assert found_mixed, "No mixed domain found in parsed log"
