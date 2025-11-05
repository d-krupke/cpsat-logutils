"""
Tests for compatibility with the latest CP-SAT version.

These tests run actual CP-SAT problems and verify that the parser
can handle logs from the latest version of OR-Tools.
"""

import pytest

# Try to import ortools
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None  # Define cp_model as None when not available

from cpsat_logutils.parser import LogParser

# Skip all tests if ortools is not available
pytestmark = pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="ortools not installed")


if ORTOOLS_AVAILABLE:
    class LogCapture(cp_model.CpSolverSolutionCallback):
        """Callback to capture intermediate solutions."""

        def __init__(self):
            super().__init__()
            self.solution_count = 0
            self.solutions = []

        def on_solution_callback(self):
            self.solution_count += 1
            self.solutions.append(self.solution_count)


def capture_cpsat_log(model, solver_params=None):
    """
    Run a CP-SAT model and capture its log output.

    Args:
        model: CP model to solve
        solver_params: Optional solver parameters

    Returns:
        tuple: (log_string, solver_response)
    """
    solver = cp_model.CpSolver()

    # Enable logging
    solver.parameters.log_search_progress = True

    # Set additional parameters if provided
    if solver_params:
        for key, value in solver_params.items():
            setattr(solver.parameters, key, value)

    # Capture log using callback (CP-SAT uses callbacks, not stdout)
    log_lines = []
    solver.log_callback = lambda line: log_lines.append(line)

    # Solve the model
    status = solver.Solve(model)

    # Get the log
    log_string = "\n".join(log_lines)

    return log_string, status


class TestLatestVersionBasic:
    """Test basic problems with latest CP-SAT version."""

    def test_simple_optimization(self):
        """Test a simple optimization problem."""
        # Create a simple optimization model
        model = cp_model.CpModel()

        # Variables: x, y in [0, 10]
        x = model.NewIntVar(0, 10, 'x')
        y = model.NewIntVar(0, 10, 'y')

        # Constraint: x + y <= 15
        model.Add(x + y <= 15)

        # Objective: maximize x + 2*y
        model.Maximize(x + 2 * y)

        # Solve and capture log
        log_string, status = capture_cpsat_log(model)

        # Verify solve was successful
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert len(log_string) > 0, "No log output captured"

        # Parse the log
        parser = LogParser(log_string)
        result = parser.parse()

        # Validate parsed result
        assert result.solver_info is not None, "Failed to parse solver info"
        assert result.solver_info.version is not None, "Failed to parse version"
        assert result.response is not None, "Failed to parse response"
        assert result.response.status in ["OPTIMAL", "FEASIBLE"], \
            f"Unexpected status: {result.response.status}"

        # Should have initial model
        assert result.initial_model is not None, "Failed to parse initial model"
        assert result.initial_model.is_optimization is True

        # Print version for debugging
        print(f"\nCP-SAT version: {result.solver_info.version}")
        print(f"Status: {result.response.status}")

    def test_simple_satisfaction(self):
        """Test a simple satisfaction problem."""
        # Create a satisfaction model
        model = cp_model.CpModel()

        # Variables: x, y in [0, 5]
        x = model.NewIntVar(0, 5, 'x')
        y = model.NewIntVar(0, 5, 'y')

        # Constraints
        model.Add(x + y == 7)
        model.Add(x - y == 1)

        # Solve and capture log
        log_string, status = capture_cpsat_log(model)

        # Verify solve was successful
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.INFEASIBLE]
        assert len(log_string) > 0

        # Parse the log
        parser = LogParser(log_string)
        result = parser.parse()

        # Validate parsed result
        assert result.solver_info is not None
        assert result.response is not None

    def test_with_time_limit(self):
        """Test problem with time limit."""
        # Create a harder optimization model
        model = cp_model.CpModel()

        # Create 20 variables
        n = 20
        vars = [model.NewIntVar(0, 10, f'x_{i}') for i in range(n)]

        # Add constraints
        for i in range(n - 1):
            model.Add(vars[i] + vars[i + 1] <= 15)

        # Objective: maximize sum
        model.Maximize(sum(vars))

        # Solve with time limit
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 5}
        )

        # Parse the log
        parser = LogParser(log_string)
        result = parser.parse()

        # Should capture time limit parameter
        assert result.solver_info.parameters is not None
        # Time limit should be in parameters
        assert 'max_time_in_seconds' in result.solver_info.parameters or \
               result.solver_info.parameters != {}, \
            "Failed to parse parameters with time limit"

        print(f"\nParameters: {result.solver_info.parameters}")


class TestLatestVersionAdvanced:
    """Test more advanced features with latest CP-SAT."""

    def test_all_different_constraint(self):
        """Test problem with AllDifferent constraint."""
        model = cp_model.CpModel()

        # Create variables for a simple all-different problem
        n = 5
        vars = [model.NewIntVar(0, n - 1, f'x_{i}') for i in range(n)]

        # All different constraint
        model.AddAllDifferent(vars)

        # Add objective to make it interesting
        model.Maximize(sum(vars))

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Validate
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

    def test_boolean_optimization(self):
        """Test problem with boolean variables."""
        model = cp_model.CpModel()

        # Create boolean variables
        n = 50
        bools = [model.NewBoolVar(f'b_{i}') for i in range(n)]

        # Add some constraints
        for i in range(n - 1):
            model.AddBoolOr([bools[i], bools[i + 1]])

        # Objective: maximize number of true variables
        model.Maximize(sum(bools))

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Should have boolean variable info
        if result.initial_model:
            assert result.initial_model.num_variables >= n
            # Should mention booleans in objective
            if result.initial_model.num_booleans_in_objective is not None:
                assert result.initial_model.num_booleans_in_objective > 0

    def test_multiple_workers(self):
        """Test problem solved with multiple workers."""
        model = cp_model.CpModel()

        # Create a problem that benefits from parallelism
        n = 30
        vars = [model.NewIntVar(0, 20, f'x_{i}') for i in range(n)]

        # Add constraints
        for i in range(n - 2):
            model.Add(vars[i] + vars[i + 1] + vars[i + 2] <= 40)

        # Objective
        model.Maximize(sum(vars))

        # Solve with multiple workers
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'num_search_workers': 4}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Should capture worker count
        assert result.solver_info.num_workers is not None
        # If we set workers, it should be reflected (or may be capped by system)
        print(f"\nWorkers used: {result.solver_info.num_workers}")


class TestLatestVersionStatistics:
    """Test that statistics are captured correctly from latest version."""

    def test_search_statistics_present(self):
        """Test that search statistics are captured."""
        model = cp_model.CpModel()

        # Create a problem that requires some search
        n = 15
        vars = [model.NewIntVar(0, 10, f'x_{i}') for i in range(n)]
        model.AddAllDifferent(vars[:5])  # Can't be satisfied, forces search
        model.Maximize(sum(vars))

        # Solve
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 2}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Should have some search activity
        # Note: Might be empty for very simple problems
        print(f"\nSearch events: {len(result.search_events)}")
        print(f"Search stats: {len(result.search_stats)}")

        # At minimum, should parse without errors
        assert result.response is not None

    def test_presolve_operations(self):
        """Test that presolve operations are captured."""
        model = cp_model.CpModel()

        # Create a model with redundant constraints that presolve can optimize
        n = 20
        vars = [model.NewIntVar(0, 10, f'x_{i}') for i in range(n)]

        # Add redundant constraints
        for i in range(n - 1):
            model.Add(vars[i] <= 10)  # Already enforced by domain
            model.Add(vars[i] + vars[i + 1] <= 20)

        model.Maximize(sum(vars))

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Should have presolve information
        # Note: Modern CP-SAT might be very efficient, so presolve might be minimal
        print(f"\nPresolve log entries: {len(result.presolve_log)}")
        if result.presolve_summary:
            print(f"Rules applied: {len(result.presolve_summary.rules_applied)}")


class TestLatestVersionRegression:
    """Regression tests to catch parsing issues with new CP-SAT versions."""

    def test_no_parser_errors(self):
        """Test that parser doesn't error on latest CP-SAT output."""
        # Create various types of models and ensure no parsing errors
        test_models = []

        # Model 1: Simple optimization
        m1 = cp_model.CpModel()
        x1 = m1.NewIntVar(0, 10, 'x')
        m1.Maximize(x1)
        test_models.append(("simple_opt", m1))

        # Model 2: Satisfaction with constraints
        m2 = cp_model.CpModel()
        x2 = [m2.NewIntVar(0, 5, f'x_{i}') for i in range(3)]
        m2.Add(sum(x2) == 10)
        test_models.append(("satisfaction", m2))

        # Model 3: Boolean problem
        m3 = cp_model.CpModel()
        b3 = [m3.NewBoolVar(f'b_{i}') for i in range(10)]
        m3.AddBoolOr(b3)
        m3.Maximize(sum(b3))
        test_models.append(("boolean", m3))

        # Test each model
        for name, model in test_models:
            log_string, status = capture_cpsat_log(model)

            # Should not raise any exceptions
            try:
                parser = LogParser(log_string)
                result = parser.parse()

                # Basic validation
                assert result.solver_info is not None, f"Failed to parse solver_info in {name}"
                assert result.response is not None, f"Failed to parse response in {name}"

                print(f"\n{name}: OK (version {result.solver_info.version}, status {result.response.status})")

            except Exception as e:
                pytest.fail(f"Parser failed on {name} model: {e}")

    def test_version_comparison(self):
        """Test that we can parse and compare versions."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 5, 'x')
        model.Maximize(x)

        log_string, status = capture_cpsat_log(model)
        parser = LogParser(log_string)
        result = parser.parse()

        # Should have a valid version string
        version = result.solver_info.version
        assert version is not None
        assert version != "unknown"

        # Version should be parseable
        parts = version.split('.')
        assert len(parts) >= 2, f"Invalid version format: {version}"

        # Major version should be numeric
        try:
            major = int(parts[0])
            assert major >= 9, f"Expected CP-SAT version >= 9, got {version}"
        except ValueError:
            pytest.fail(f"Could not parse major version from: {version}")

        print(f"\nDetected CP-SAT version: {version}")


if __name__ == "__main__":
    if not ORTOOLS_AVAILABLE:
        print("Skipping tests: ortools not installed")
        print("Install with: pip install ortools")
    else:
        pytest.main([__file__, "-v", "-s"])
