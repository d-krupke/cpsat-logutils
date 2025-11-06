import random
import os
import sys
import pytest

# Try to import ortools - skip tests if not available
try:
    from ortools.sat.python import cp_model  # pip install -U ortools
    ORTOOLS_AVAILABLE = True
except ImportError:
    ORTOOLS_AVAILABLE = False
    cp_model = None

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from cpsat_logutils.parser import LogParser
from cpsat_logutils.capture import solve_and_capture

# Skip all tests if ortools is not available
pytestmark = pytest.mark.skipif(not ORTOOLS_AVAILABLE, reason="ortools not installed")


def test_latest_cpsat():
    # Specifying the input
    n = 5_000
    weights = [random.randint(1, 1000) for _ in range(n)]
    values = [random.randint(1, 100) for _ in range(n)]
    capacity = 20 * n

    # Now we solve the problem
    model = cp_model.CpModel()
    xs = [model.new_bool_var(f"x_{i}") for i in range(len(weights))]

    model.add(sum(x * w for x, w in zip(xs, weights)) <= capacity)
    model.maximize(sum(x * v for x, v in zip(xs, values)))

    # Solve and capture log using the utility
    solve_result = solve_and_capture(model, parse=True)

    # Get the parsed result
    result = solve_result.parsed_log

    # Verify we parsed the key components
    assert result.solver_info is not None, "Failed to parse solver info"
    assert result.solver_info.version is not None, "Failed to parse version"
    assert result.response is not None, "Failed to parse response"
    assert result.response.status in ["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN"], \
        f"Unexpected status: {result.response.status}"

    print(f"\nCP-SAT version: {result.solver_info.version}")
    print(f"Status: {result.response.status}")
    print(f"Search events: {len(result.search_events)}")
