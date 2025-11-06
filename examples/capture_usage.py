"""
Example demonstrating the two ways to use solve_and_capture:
1. With solver_params dict
2. With a pre-configured solver object
"""

try:
    from ortools.sat.python import cp_model
except ImportError:
    print("This example requires ortools. Install with: pip install ortools")
    exit(1)

from cpsat_logutils.capture import solve_and_capture


def create_simple_model():
    """Create a simple optimization model for demonstration."""
    model = cp_model.CpModel()

    # Variables
    x = model.NewIntVar(0, 10, 'x')
    y = model.NewIntVar(0, 10, 'y')
    z = model.NewIntVar(0, 10, 'z')

    # Constraints
    model.Add(x + y + z <= 20)
    model.Add(x >= 2)

    # Objective: maximize x + 2*y + 3*z
    model.Maximize(x + 2 * y + 3 * z)

    return model, (x, y, z)


def example_with_solver_params():
    """Example using solver_params dict."""
    print("=" * 60)
    print("Example 1: Using solver_params dict")
    print("=" * 60)

    model, (x, y, z) = create_simple_model()

    # Let solve_and_capture create and configure the solver
    result = solve_and_capture(
        model,
        parse=True,
        solver_params={
            'max_time_in_seconds': 10,
            'num_search_workers': 2,
        }
    )

    print(f"\nStatus: {result.status}")
    print(f"CP-SAT Version: {result.parsed_log.solver_info.version}")
    print(f"Solution found: x={result.solver.Value(x)}, y={result.solver.Value(y)}, z={result.solver.Value(z)}")
    print(f"Objective value: {result.solver.ObjectiveValue()}")
    print(f"Log length: {len(result.log_string)} characters")
    print(f"Number of search events: {len(result.parsed_log.search_events)}")


def example_with_preconfigured_solver():
    """Example using a pre-configured solver."""
    print("\n" + "=" * 60)
    print("Example 2: Using pre-configured solver")
    print("=" * 60)

    model, (x, y, z) = create_simple_model()

    # Create and fully configure your own solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.num_search_workers = 2
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = False  # We're capturing via callback

    # You can set any advanced parameters you want
    solver.parameters.cp_model_presolve = True
    solver.parameters.symmetry_level = 2

    # Pass your configured solver to solve_and_capture
    result = solve_and_capture(
        model,
        parse=True,
        solver=solver
    )

    print(f"\nStatus: {result.status}")
    print(f"CP-SAT Version: {result.parsed_log.solver_info.version}")
    print(f"Solution found: x={result.solver.Value(x)}, y={result.solver.Value(y)}, z={result.solver.Value(z)}")
    print(f"Objective value: {result.solver.ObjectiveValue()}")
    print(f"Log length: {len(result.log_string)} characters")
    print(f"Number of search events: {len(result.parsed_log.search_events)}")

    # Verify we got the same solver back
    print(f"\nSame solver instance: {result.solver is solver}")


def example_accessing_parsed_data():
    """Example showing how to access parsed log data."""
    print("\n" + "=" * 60)
    print("Example 3: Accessing parsed log data")
    print("=" * 60)

    model, _ = create_simple_model()

    result = solve_and_capture(model, parse=True)

    log = result.parsed_log

    print(f"\nSolver info:")
    print(f"  Version: {log.solver_info.version}")
    print(f"  Parameters: {list(log.solver_info.parameters.keys())[:5]}...")

    if log.initial_model:
        print(f"\nInitial model:")
        print(f"  Variables: {log.initial_model.num_variables}")
        print(f"  Constraints: {log.initial_model.num_constraints}")
        print(f"  Variable domains: {len(log.initial_model.variable_domains)}")

    print(f"\nSearch events: {len(log.search_events)}")
    if log.search_events:
        first_event = log.search_events[0]
        print(f"  First event type: {type(first_event).__name__}")

    print(f"\nResponse:")
    print(f"  Status: {log.response.status}")
    print(f"  Wall time: {log.response.wall_time}s")
    print(f"  User time: {log.response.user_time}s")


if __name__ == "__main__":
    example_with_solver_params()
    example_with_preconfigured_solver()
    example_accessing_parsed_data()

    print("\n" + "=" * 60)
    print("All examples completed!")
    print("=" * 60)
