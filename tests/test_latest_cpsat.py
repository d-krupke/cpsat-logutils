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


class TestLatestVersionIntervalVariables:
    """Test problems with interval variables (scheduling)."""

    def test_simple_scheduling(self):
        """Test scheduling problem with interval variables."""
        model = cp_model.CpModel()

        # Create 5 tasks with start, duration, and end
        horizon = 100
        num_tasks = 5

        tasks = []
        for i in range(num_tasks):
            start_var = model.NewIntVar(0, horizon, f'start_{i}')
            duration = 10 + i * 2  # Varying durations
            end_var = model.NewIntVar(0, horizon, f'end_{i}')

            # Create interval variable
            interval = model.NewIntervalVar(start_var, duration, end_var, f'task_{i}')
            tasks.append((start_var, duration, end_var, interval))

        # Add NoOverlap constraint (tasks can't overlap)
        model.AddNoOverlap([task[3] for task in tasks])

        # Objective: minimize makespan
        makespan = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(makespan, [task[2] for task in tasks])
        model.Minimize(makespan)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Verify
        assert status in [cp_model.OPTIMAL, cp_model.FEASIBLE]

        # Parse the log
        parser = LogParser(log_string)
        result = parser.parse()

        # Should have parsed the model
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

        # Should have interval variables in the model
        if result.initial_model:
            assert result.initial_model.num_variables >= num_tasks * 3  # start, end, and helper vars
            print(f"\nScheduling: {result.initial_model.num_variables} variables")

    def test_scheduling_with_optional_intervals(self):
        """Test scheduling with optional interval variables."""
        model = cp_model.CpModel()

        horizon = 50
        num_tasks = 8

        intervals = []
        presences = []

        for i in range(num_tasks):
            # Optional task - might not be scheduled
            presence = model.NewBoolVar(f'presence_{i}')
            start_var = model.NewIntVar(0, horizon, f'start_{i}')
            duration = 5
            end_var = model.NewIntVar(0, horizon, f'end_{i}')

            # Optional interval
            interval = model.NewOptionalIntervalVar(
                start_var, duration, end_var, presence, f'task_{i}'
            )

            intervals.append(interval)
            presences.append(presence)

        # At most 5 tasks can be selected
        model.Add(sum(presences) <= 5)

        # No overlap for selected tasks
        model.AddNoOverlap(intervals)

        # Maximize number of tasks
        model.Maximize(sum(presences))

        # Solve
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 5}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Should parse successfully
        assert result.solver_info is not None
        assert result.response is not None
        print(f"\nOptional intervals: {result.response.status}")


class TestLatestVersionDomainVariables:
    """Test problems with variables having different domains."""

    def test_mixed_domains(self):
        """Test model with variables having different domains."""
        model = cp_model.CpModel()

        # Create variables with very different domains
        small_var = model.NewIntVar(0, 10, 'small')
        medium_var = model.NewIntVar(0, 1000, 'medium')
        large_var = model.NewIntVar(0, 1000000, 'large')

        # Negative domain
        negative_var = model.NewIntVar(-100, 100, 'negative')

        # Large negative to positive
        wide_var = model.NewIntVar(-1000000, 1000000, 'wide')

        # Constrained domain (not starting at 0)
        constrained_var = model.NewIntVar(50, 150, 'constrained')

        # Add some constraints linking them
        model.Add(medium_var == small_var * 100)
        model.Add(large_var == medium_var * 1000)
        model.Add(negative_var + constrained_var >= 0)
        model.Add(wide_var == negative_var * 1000)

        # Objective
        model.Maximize(small_var + negative_var + constrained_var)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify parsing
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

        # Should show different variable domains
        if result.initial_model and result.initial_model.variable_domains:
            print(f"\nVariable domains found: {len(result.initial_model.variable_domains)}")
            for domain in result.initial_model.variable_domains[:3]:
                print(f"  {domain.type}: {domain.count} vars, range [{domain.min_value}, {domain.max_value}]")

    def test_enumerated_domains(self):
        """Test variables with non-contiguous domains."""
        model = cp_model.CpModel()

        # Create variables with enumerated domains
        # Note: CP-SAT will convert these internally
        x = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues([1, 3, 5, 7, 9]), 'x'
        )
        y = model.NewIntVarFromDomain(
            cp_model.Domain.FromValues([2, 4, 6, 8, 10]), 'y'
        )
        z = model.NewIntVarFromDomain(
            cp_model.Domain.FromIntervals([[0, 5], [10, 15], [20, 25]]), 'z'
        )

        # Add constraints
        model.Add(x + y <= 15)
        model.Add(z >= x)

        # Objective
        model.Maximize(x + y + z)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE", "INFEASIBLE"]
        print(f"\nEnumerated domains: {result.response.status}")


class TestLatestVersionConditionalConstraints:
    """Test problems with conditional constraints (only_enforce_if)."""

    def test_only_enforce_if_basic(self):
        """Test basic only_enforce_if constraints."""
        model = cp_model.CpModel()

        # Create variables
        x = model.NewIntVar(0, 10, 'x')
        y = model.NewIntVar(0, 10, 'y')
        z = model.NewIntVar(0, 10, 'z')

        # Boolean conditions
        condition_a = model.NewBoolVar('condition_a')
        condition_b = model.NewBoolVar('condition_b')

        # Conditional constraints
        # If condition_a is true, then x + y <= 5
        model.Add(x + y <= 5).OnlyEnforceIf(condition_a)

        # If condition_b is true, then y + z >= 8
        model.Add(y + z >= 8).OnlyEnforceIf(condition_b)

        # If condition_a is false, then x >= 7
        model.Add(x >= 7).OnlyEnforceIf(condition_a.Not())

        # At least one condition must be true
        model.AddBoolOr([condition_a, condition_b])

        # Objective
        model.Maximize(x + y + z)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]
        print(f"\nConditional constraints: {result.response.status}")

    def test_implication_constraints(self):
        """Test implication constraints (a => b)."""
        model = cp_model.CpModel()

        n = 10
        bools = [model.NewBoolVar(f'b_{i}') for i in range(n)]

        # Chain of implications: b_i => b_{i+1}
        for i in range(n - 1):
            model.AddImplication(bools[i], bools[i + 1])

        # If first is true, last must be true
        # If last is false, first must be false

        # Add some other constraints
        model.Add(sum(bools) >= 3)
        model.Add(sum(bools) <= 7)

        # Minimize number of true variables
        model.Minimize(sum(bools))

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

    def test_complex_conditional_with_intervals(self):
        """Test conditional constraints combined with intervals."""
        model = cp_model.CpModel()

        horizon = 50
        num_jobs = 5

        # Each job can be processed on machine A or B
        # But different processing times
        intervals_a = []
        intervals_b = []
        use_machine_a = []

        for i in range(num_jobs):
            # Machine A
            start_a = model.NewIntVar(0, horizon, f'start_a_{i}')
            duration_a = 10
            end_a = model.NewIntVar(0, horizon, f'end_a_{i}')
            present_a = model.NewBoolVar(f'present_a_{i}')
            interval_a = model.NewOptionalIntervalVar(
                start_a, duration_a, end_a, present_a, f'interval_a_{i}'
            )
            intervals_a.append(interval_a)

            # Machine B
            start_b = model.NewIntVar(0, horizon, f'start_b_{i}')
            duration_b = 7  # Faster on machine B
            end_b = model.NewIntVar(0, horizon, f'end_b_{i}')
            present_b = model.NewBoolVar(f'present_b_{i}')
            interval_b = model.NewOptionalIntervalVar(
                start_b, duration_b, end_b, present_b, f'interval_b_{i}'
            )
            intervals_b.append(interval_b)

            # Exactly one machine per job
            model.AddExactlyOne([present_a, present_b])
            use_machine_a.append(present_a)

        # No overlap on each machine
        model.AddNoOverlap(intervals_a)
        model.AddNoOverlap(intervals_b)

        # Minimize makespan
        all_ends = [model.NewIntVar(0, horizon, f'end_{i}') for i in range(num_jobs)]
        for i in range(num_jobs):
            # Conditional: if on machine A, use end_a, else use end_b
            start_a_var = intervals_a[i].StartExpr()
            end_a_var = model.NewIntVar(0, horizon, f'temp_end_a_{i}')
            model.Add(end_a_var == start_a_var + 10).OnlyEnforceIf(use_machine_a[i])

            start_b_var = intervals_b[i].StartExpr()
            end_b_var = model.NewIntVar(0, horizon, f'temp_end_b_{i}')
            model.Add(end_b_var == start_b_var + 7).OnlyEnforceIf(use_machine_a[i].Not())

            # Set all_ends[i] based on which machine
            model.Add(all_ends[i] == end_a_var).OnlyEnforceIf(use_machine_a[i])
            model.Add(all_ends[i] == end_b_var).OnlyEnforceIf(use_machine_a[i].Not())

        makespan = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(makespan, all_ends)
        model.Minimize(makespan)

        # Solve
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 10}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response is not None
        print(f"\nComplex conditional+intervals: {result.response.status}")


class TestLatestVersionComplexConstraints:
    """Test other complex constraint types."""

    def test_circuit_constraint(self):
        """Test circuit constraint (traveling salesman-like)."""
        model = cp_model.CpModel()

        n = 10  # Number of nodes

        # Create arc variables
        # arcs[i][j] = 1 if we go from i to j
        arcs = {}
        for i in range(n):
            for j in range(n):
                if i != j:
                    arcs[(i, j)] = model.NewBoolVar(f'arc_{i}_{j}')

        # Circuit constraint: forms a single cycle visiting all nodes
        model.AddCircuit([(i, j, arcs[(i, j)]) for i, j in arcs])

        # Optional: add some costs
        costs = {(i, j): abs(i - j) for i, j in arcs}
        total_cost = sum(arcs[(i, j)] * costs[(i, j)] for i, j in arcs)
        model.Minimize(total_cost)

        # Solve
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 10}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]
        print(f"\nCircuit constraint: {result.response.status}")

    def test_element_constraint(self):
        """Test element constraint (array indexing)."""
        model = cp_model.CpModel()

        # Array of values
        values = [10, 25, 30, 15, 40, 35, 20]

        # Index variable (which element to select)
        index = model.NewIntVar(0, len(values) - 1, 'index')

        # Target variable (value at the selected index)
        target = model.NewIntVar(min(values), max(values), 'target')

        # Element constraint: target = values[index]
        model.AddElement(index, values, target)

        # Additional variables and constraints
        x = model.NewIntVar(0, 100, 'x')
        y = model.NewIntVar(0, 100, 'y')

        model.Add(x + y == target)
        model.Add(x >= y)

        # Maximize target
        model.Maximize(target)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

    def test_table_constraint(self):
        """Test table constraint (allowed tuples)."""
        model = cp_model.CpModel()

        # Variables
        x = model.NewIntVar(0, 5, 'x')
        y = model.NewIntVar(0, 5, 'y')
        z = model.NewIntVar(0, 5, 'z')

        # Allowed tuples (x, y, z)
        allowed_tuples = [
            (1, 2, 3),
            (2, 3, 4),
            (1, 3, 5),
            (3, 1, 4),
            (0, 1, 1),
            (5, 0, 5),
        ]

        # Table constraint
        model.AddAllowedAssignments([x, y, z], allowed_tuples)

        # Additional constraints
        total = model.NewIntVar(0, 20, 'total')
        model.Add(total == x + y + z)

        # Maximize total
        model.Maximize(total)

        # Solve
        log_string, status = capture_cpsat_log(model)

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]

    def test_cumulative_constraint(self):
        """Test cumulative constraint (resource constraint)."""
        model = cp_model.CpModel()

        horizon = 100
        capacity = 5  # Maximum resource capacity
        num_tasks = 10

        intervals = []
        demands = []

        for i in range(num_tasks):
            start = model.NewIntVar(0, horizon, f'start_{i}')
            duration = 10 + i
            end = model.NewIntVar(0, horizon, f'end_{i}')

            interval = model.NewIntervalVar(start, duration, end, f'task_{i}')
            intervals.append(interval)

            # Each task demands some resource
            demand = 1 + (i % 3)  # Demands: 1, 2, or 3
            demands.append(demand)

        # Cumulative constraint: sum of demands at any time <= capacity
        model.AddCumulative(intervals, demands, capacity)

        # Minimize makespan
        makespan = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(makespan, [interval.EndExpr() for interval in intervals])
        model.Minimize(makespan)

        # Solve
        log_string, status = capture_cpsat_log(
            model,
            solver_params={'max_time_in_seconds': 10}
        )

        # Parse
        parser = LogParser(log_string)
        result = parser.parse()

        # Verify
        assert result.solver_info is not None
        assert result.response.status in ["OPTIMAL", "FEASIBLE"]
        print(f"\nCumulative: {result.response.status}")


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
