"""
Utilities for capturing and parsing CP-SAT solver logs.

This module provides convenient utilities to capture logs from the
CP-SAT solver and optionally parse them directly.
"""

from typing import Any, Dict, Optional, Tuple

try:
    from ortools.sat.python import cp_model
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None

from cpsat_logutils.parser import LogParser
from cpsat_logutils.models.log import CPSATLog


class SolveResult:
    """
    Result from solving a CP-SAT model with log capture.

    Attributes:
        status: The solver status (from cp_model.CpSolver.Solve)
        log_string: The captured log as a string
        parsed_log: The parsed log (if parse=True was used), otherwise None
        solver: The solver instance (contains solution, statistics, etc.)
    """

    def __init__(
        self,
        status: int,
        log_string: str,
        parsed_log: Optional[CPSATLog],
        solver: Any
    ):
        self.status = status
        self.log_string = log_string
        self.parsed_log = parsed_log
        self.solver = solver

    def __repr__(self) -> str:
        status_name = None
        if ORTOOLS_AVAILABLE and cp_model:
            # Try to get status name
            status_names = {
                cp_model.UNKNOWN: "UNKNOWN",
                cp_model.MODEL_INVALID: "MODEL_INVALID",
                cp_model.FEASIBLE: "FEASIBLE",
                cp_model.INFEASIBLE: "INFEASIBLE",
                cp_model.OPTIMAL: "OPTIMAL",
            }
            status_name = status_names.get(self.status, f"Status({self.status})")
        else:
            status_name = f"Status({self.status})"

        parsed_info = "parsed" if self.parsed_log else "not parsed"
        return f"SolveResult(status={status_name}, {parsed_info}, log_length={len(self.log_string)})"


def solve_and_capture(
    model,
    parse: bool = True,
    solver: Optional[Any] = None,
    solver_params: Optional[Dict[str, Any]] = None,
    log_search_progress: bool = True,
) -> SolveResult:
    """
    Solve a CP-SAT model and capture its log output.

    This function uses the proper CP-SAT log callback mechanism to capture
    logs without redirecting stdout.

    Args:
        model: CP-SAT model to solve (ortools.sat.python.cp_model.CpModel)
        parse: If True, automatically parse the log and return parsed result
        solver: Optional pre-configured solver instance. If provided, this solver
                will be used instead of creating a new one. In this case,
                solver_params and log_search_progress are ignored.
        solver_params: Optional dict of solver parameters to set. Only used if
                      solver is not provided.
                      (e.g., {'max_time_in_seconds': 10, 'num_search_workers': 4})
        log_search_progress: If True, enable search progress logging (default: True).
                           Only used if solver is not provided.

    Returns:
        SolveResult containing:
            - status: Solver status
            - log_string: Captured log
            - parsed_log: Parsed log (CPSATLog) if parse=True, else None
            - solver: The solver instance

    Example with auto-created solver:
        >>> from ortools.sat.python import cp_model
        >>> from cpsat_logutils.capture import solve_and_capture
        >>>
        >>> model = cp_model.CpModel()
        >>> x = model.NewIntVar(0, 10, 'x')
        >>> model.Maximize(x)
        >>>
        >>> # Let the function create and configure the solver
        >>> result = solve_and_capture(model, solver_params={'max_time_in_seconds': 10})
        >>> print(result.parsed_log.solver_info.version)

    Example with pre-configured solver:
        >>> # Configure your own solver
        >>> solver = cp_model.CpSolver()
        >>> solver.parameters.max_time_in_seconds = 10
        >>> solver.parameters.num_search_workers = 4
        >>> solver.parameters.log_search_progress = True
        >>>
        >>> # Pass it to solve_and_capture
        >>> result = solve_and_capture(model, solver=solver)
        >>> print(result.status)

    Raises:
        ImportError: If ortools is not installed
    """
    if not ORTOOLS_AVAILABLE or cp_model is None:
        raise ImportError(
            "ortools is required to use solve_and_capture. "
            "Install it with: pip install ortools"
        )

    # Use provided solver or create a new one
    if solver is None:
        solver = cp_model.CpSolver()

        # Enable logging
        solver.parameters.log_search_progress = log_search_progress

        # Set additional parameters if provided
        if solver_params:
            for key, value in solver_params.items():
                setattr(solver.parameters, key, value)

    # Capture log using callback
    # CP-SAT calls this callback for each log line
    log_lines = []
    solver.log_callback = lambda line: log_lines.append(line)

    # Solve the model
    status = solver.Solve(model)

    # Reconstruct the log string
    log_string = "\n".join(log_lines)

    # Parse if requested
    parsed_log = None
    if parse:
        parser = LogParser(log_string)
        parsed_log = parser.parse()

    return SolveResult(
        status=status,
        log_string=log_string,
        parsed_log=parsed_log,
        solver=solver
    )


def capture_log(
    model,
    solver: Optional[Any] = None,
    solver_params: Optional[Dict[str, Any]] = None,
    log_search_progress: bool = True,
) -> Tuple[str, int]:
    """
    Solve a CP-SAT model and return the log string and status.

    This is a simpler version of solve_and_capture that only returns
    the log string and status, without parsing.

    Args:
        model: CP-SAT model to solve
        solver: Optional pre-configured solver instance
        solver_params: Optional dict of solver parameters (ignored if solver provided)
        log_search_progress: If True, enable search progress logging (ignored if solver provided)

    Returns:
        tuple: (log_string, status)

    Example:
        >>> log, status = capture_log(model, solver_params={'max_time_in_seconds': 10})
        >>> parser = LogParser(log)
        >>> result = parser.parse()
    """
    result = solve_and_capture(
        model,
        parse=False,
        solver=solver,
        solver_params=solver_params,
        log_search_progress=log_search_progress
    )
    return result.log_string, result.status
