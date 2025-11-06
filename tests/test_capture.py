"""Tests for the capture utility module."""

import pytest

# Try to import ortools
try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None

from cpsat_logutils.capture import solve_and_capture, capture_log

# Skip all tests if ortools is not available
pytestmark = pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="ortools not installed")


class TestSolveAndCapture:
    """Test the solve_and_capture function."""

    def test_basic_usage(self):
        """Test basic usage with default parameters."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        result = solve_and_capture(model, parse=True)

        assert result.status == cp_model.OPTIMAL
        assert len(result.log_string) > 0
        assert result.parsed_log is not None
        assert result.solver is not None
        assert result.parsed_log.solver_info is not None

    def test_with_solver_params(self):
        """Test using solver_params dict."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        result = solve_and_capture(
            model,
            parse=True,
            solver_params={'max_time_in_seconds': 10}
        )

        assert result.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert len(result.log_string) > 0
        assert result.parsed_log is not None

    def test_with_preconfigured_solver(self):
        """Test using a pre-configured solver object."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        # Create and configure solver
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.parameters.log_search_progress = True
        solver.parameters.num_search_workers = 1

        result = solve_and_capture(model, parse=True, solver=solver)

        assert result.status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert len(result.log_string) > 0
        assert result.parsed_log is not None
        # Verify we got the same solver back
        assert result.solver is solver

    def test_without_parsing(self):
        """Test capturing log without parsing."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        result = solve_and_capture(model, parse=False)

        assert result.status == cp_model.OPTIMAL
        assert len(result.log_string) > 0
        assert result.parsed_log is None
        assert result.solver is not None

    def test_solution_access(self):
        """Test that we can access the solution from the solver."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        y = model.NewIntVar(0, 5, 'y')
        model.Maximize(x + y)

        result = solve_and_capture(model, parse=True)

        assert result.status == cp_model.OPTIMAL
        # Can access solution through the solver
        assert result.solver.Value(x) == 10
        assert result.solver.Value(y) == 5


class TestCaptureLog:
    """Test the capture_log function."""

    def test_basic_usage(self):
        """Test basic usage of capture_log."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        log_string, status = capture_log(model)

        assert status == cp_model.OPTIMAL
        assert len(log_string) > 0
        assert "CP-SAT" in log_string or "Starting" in log_string

    def test_with_solver_params(self):
        """Test capture_log with solver params."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        log_string, status = capture_log(
            model,
            solver_params={'max_time_in_seconds': 10}
        )

        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert len(log_string) > 0

    def test_with_preconfigured_solver(self):
        """Test capture_log with pre-configured solver."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10
        solver.parameters.log_search_progress = True

        log_string, status = capture_log(model, solver=solver)

        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]
        assert len(log_string) > 0


class TestSolverResult:
    """Test the SolveResult object."""

    def test_result_repr(self):
        """Test that SolveResult has a useful repr."""
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, 'x')
        model.Maximize(x)

        result = solve_and_capture(model, parse=True)

        repr_str = repr(result)
        assert "OPTIMAL" in repr_str or "Status" in repr_str
        assert "parsed" in repr_str
        assert "log_length" in repr_str
