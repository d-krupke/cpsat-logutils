"""
Comprehensive validation tests for bound parsing and convergence.

This test suite validates that:
1. Bounds are parsed correctly from next:[lower,upper] format
2. Lower bounds increase (converge from below) over time
3. Upper bounds decrease (converge from above) over time
4. Event times are consistent with final walltime
5. Final bounds match the response summary
"""

import pytest
from pathlib import Path
from cpsat_logutils import LogParser


# Get all example log files
EXAMPLE_DIR = Path(__file__).parent.parent.parent / "example_logs"
EXAMPLE_LOGS = sorted(EXAMPLE_DIR.glob("*.txt"))


class TestBoundParsing:
    """Test that bounds are parsed correctly from the next:[lower,upper] format."""

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_bounds_are_numbers_not_strings(self, log_file):
        """Verify bounds are parsed as numbers, not strings with commas."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Check all objective events have proper numeric bounds
        for event in result.search_events:
            if event.event_type == "objective":
                if event.lower_bound is not None:
                    assert isinstance(event.lower_bound, (int, float)), (
                        f"Lower bound should be numeric, got {type(event.lower_bound)}: {event.lower_bound}"
                    )
                    # Bounds should be reasonable numbers (not parsed as comma-decimal)
                    assert event.lower_bound > 0, f"Lower bound should be positive: {event.lower_bound}"

                if event.upper_bound is not None:
                    assert isinstance(event.upper_bound, (int, float)), (
                        f"Upper bound should be numeric, got {type(event.upper_bound)}: {event.upper_bound}"
                    )
                    assert event.upper_bound > 0, f"Upper bound should be positive: {event.upper_bound}"

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_bounds_have_correct_format(self, log_file):
        """
        Verify bounds are parsed correctly and have sensible relationships.

        The next:[lower,upper] field shows search bounds. Key properties:
        - Lower bound is typically close to or just above previous objective
        - Upper bound starts high and decreases as better solutions are found
        - For optimal solutions, next:[] is used (both bounds None)
        """
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        for event in result.search_events:
            if event.event_type == "objective":
                # Verify bound field is set (required field)
                assert event.bound is not None, (
                    f"Solution #{event.solution_number}: bound is None"
                )

                # If both bounds are None, we should be at optimality
                if event.lower_bound is None and event.upper_bound is None:
                    # bound should equal objective for optimal solutions
                    assert event.bound == event.objective, (
                        f"Solution #{event.solution_number}: "
                        f"bound {event.bound} != objective {event.objective} when next:[]"
                    )


class TestBoundsConvergence:
    """Test that bounds converge over time (lower increases, upper decreases)."""

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_lower_bounds_increase(self, log_file):
        """Verify lower bounds increase (or stay same) over time for minimization."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Extract lower bounds from objective and bound events
        lower_bounds = []
        for event in result.search_events:
            if event.event_type == "objective" and event.lower_bound is not None:
                lower_bounds.append((event.time, event.lower_bound, f"solution #{event.solution_number}"))
            elif event.event_type == "bound" and event.lower_bound is not None:
                lower_bounds.append((event.time, event.lower_bound, "bound event"))

        # Check that lower bounds are non-decreasing (allowing small tolerances)
        # We allow some lenience for rare out-of-order events
        violations = []
        for i in range(1, len(lower_bounds)):
            prev_time, prev_bound, prev_desc = lower_bounds[i - 1]
            curr_time, curr_bound, curr_desc = lower_bounds[i]

            # Allow small decreases (tolerance for floating point and rare reordering)
            tolerance_ratio = 0.001  # 0.1% tolerance
            if curr_bound < prev_bound * (1 - tolerance_ratio):
                violations.append(
                    f"Lower bound decreased from {prev_bound} ({prev_desc} at {prev_time}s) "
                    f"to {curr_bound} ({curr_desc} at {curr_time}s)"
                )

        # Allow up to 5% of events to violate (for rare reordering issues)
        max_violations = max(1, len(lower_bounds) * 0.05)
        if len(violations) > max_violations:
            pytest.fail(
                f"Too many lower bound violations in {log_file.name} "
                f"({len(violations)}/{len(lower_bounds)} events):\n" + "\n".join(violations[:5])
            )

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_upper_bounds_decrease(self, log_file):
        """Verify upper bounds decrease (or stay same) over time for minimization."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Extract upper bounds from objective and bound events
        upper_bounds = []
        for event in result.search_events:
            if event.event_type == "objective" and event.upper_bound is not None:
                upper_bounds.append((event.time, event.upper_bound, f"solution #{event.solution_number}"))
            elif event.event_type == "bound" and event.upper_bound is not None:
                upper_bounds.append((event.time, event.upper_bound, "bound event"))

        # Check that upper bounds are non-increasing (allowing small tolerances)
        violations = []
        for i in range(1, len(upper_bounds)):
            prev_time, prev_bound, prev_desc = upper_bounds[i - 1]
            curr_time, curr_bound, curr_desc = upper_bounds[i]

            # Allow small increases (tolerance for floating point and rare reordering)
            tolerance_ratio = 0.001  # 0.1% tolerance
            if curr_bound > prev_bound * (1 + tolerance_ratio):
                violations.append(
                    f"Upper bound increased from {prev_bound} ({prev_desc} at {prev_time}s) "
                    f"to {curr_bound} ({curr_desc} at {curr_time}s)"
                )

        # Allow up to 5% of events to violate (for rare reordering issues)
        max_violations = max(1, len(upper_bounds) * 0.05)
        if len(violations) > max_violations:
            pytest.fail(
                f"Too many upper bound violations in {log_file.name} "
                f"({len(violations)}/{len(upper_bounds)} events):\n" + "\n".join(violations[:5])
            )

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_gap_decreases(self, log_file):
        """Verify that the gap between bounds decreases over time."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Calculate gap at different times
        gaps = []
        for event in result.search_events:
            lower = None
            upper = None

            if event.event_type == "objective":
                lower = event.lower_bound
                upper = event.upper_bound
            elif event.event_type == "bound":
                lower = event.lower_bound
                upper = event.upper_bound

            if lower is not None and upper is not None and lower > 0:
                gap = (upper - lower) / lower
                gaps.append((event.time, gap))

        if len(gaps) < 2:
            pytest.skip(f"Not enough gap data in {log_file.name}")

        # Check that gap generally decreases (with tolerance)
        # Compare first and last quarters
        quarter = len(gaps) // 4
        if quarter < 1:
            pytest.skip(f"Not enough gap data in {log_file.name}")

        first_quarter_avg = sum(g for _, g in gaps[:quarter]) / quarter
        last_quarter_avg = sum(g for _, g in gaps[-quarter:]) / quarter

        # Gap should decrease or stay similar (allow 10% increase for noise)
        assert last_quarter_avg <= first_quarter_avg * 1.1, (
            f"Gap increased significantly in {log_file.name}: "
            f"from {first_quarter_avg:.2%} to {last_quarter_avg:.2%}"
        )


class TestTimeConsistency:
    """Test that event times are consistent with solver execution."""

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_event_times_within_walltime(self, log_file):
        """Verify all event times are <= final walltime."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        if result.response.walltime is None:
            pytest.skip(f"No walltime in {log_file.name}")

        final_walltime = result.response.walltime
        violations = []

        for event in result.search_events:
            # Allow 1% tolerance for timing measurement variations
            max_allowed = final_walltime * 1.01
            if event.time > max_allowed:
                violations.append(
                    f"{event.event_type} event at {event.time}s exceeds walltime {final_walltime}s"
                )

        if violations:
            pytest.fail(f"Time violations in {log_file.name}:\n" + "\n".join(violations))

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_event_times_monotonic(self, log_file):
        """Verify event times are generally increasing (monotonic)."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        if len(result.search_events) < 2:
            pytest.skip(f"Not enough events in {log_file.name}")

        # Check times are mostly increasing
        violations = []
        for i in range(1, len(result.search_events)):
            prev_time = result.search_events[i - 1].time
            curr_time = result.search_events[i].time

            # Allow small decreases (0.01s) for timing precision
            if curr_time < prev_time - 0.01:
                violations.append(
                    f"Event {i} time {curr_time}s < previous time {prev_time}s"
                )

        # Allow up to 5% violations for rare out-of-order logging
        max_violations = max(1, len(result.search_events) * 0.05)
        if len(violations) > max_violations:
            pytest.fail(
                f"Too many time violations in {log_file.name} "
                f"({len(violations)}/{len(result.search_events)} events):\n" + "\n".join(violations[:5])
            )


class TestResponseConsistency:
    """Test that parsed events are consistent with final response."""

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_final_objective_matches_last_solution(self, log_file):
        """Verify final objective matches the last solution found."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        if result.response.objective is None:
            pytest.skip(f"No objective in response for {log_file.name}")

        # Find last objective event
        objective_events = [e for e in result.search_events if e.event_type == "objective"]
        if not objective_events:
            pytest.skip(f"No objective events in {log_file.name}")

        last_objective = objective_events[-1].objective
        final_objective = result.response.objective

        # Allow small floating point differences
        tolerance = max(abs(final_objective) * 1e-6, 1e-6)
        assert abs(last_objective - final_objective) <= tolerance, (
            f"Last solution objective {last_objective} doesn't match "
            f"final response objective {final_objective} in {log_file.name}"
        )

    @pytest.mark.parametrize("log_file", EXAMPLE_LOGS, ids=lambda p: p.name)
    def test_final_bound_consistent(self, log_file):
        """Verify final bound is consistent with last reported bounds."""
        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        if result.response.best_bound is None:
            pytest.skip(f"No best_bound in response for {log_file.name}")

        # Find last lower bound (for minimization)
        last_lower = None
        for event in reversed(result.search_events):
            if event.event_type in ["objective", "bound"] and event.lower_bound is not None:
                last_lower = event.lower_bound
                break

        if last_lower is None:
            pytest.skip(f"No lower bounds in {log_file.name}")

        final_bound = result.response.best_bound

        # Final bound should be >= last lower bound (within tolerance)
        # Allow 1% tolerance for different bound reporting methods
        tolerance = max(abs(final_bound) * 0.01, 1)
        assert final_bound >= last_lower - tolerance, (
            f"Final bound {final_bound} is less than last lower bound {last_lower} in {log_file.name}"
        )


class TestSpecificLogValues:
    """Test specific values in key example logs to catch regressions."""

    def test_98_01_first_solution_bounds(self):
        """Test that first solution in 98_01.txt has correct bounds."""
        log_file = EXAMPLE_DIR / "98_01.txt"
        if not log_file.exists():
            pytest.skip("98_01.txt not found")

        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Find first solution
        first_sol = None
        for event in result.search_events:
            if event.event_type == "objective" and event.solution_number == 1:
                first_sol = event
                break

        assert first_sol is not None, "First solution not found"

        # From the log: #1  1.52s best:3.15168966e+09 next:[65445416,3.15168966e+09]
        assert first_sol.lower_bound == 65445416, f"Expected lower_bound=65445416, got {first_sol.lower_bound}"
        assert abs(first_sol.upper_bound - 3.15168966e+09) < 1e3, (
            f"Expected upper_bound≈3.15168966e+09, got {first_sol.upper_bound}"
        )
        assert abs(first_sol.objective - 3.15168966e+09) < 1e3, (
            f"Expected objective≈3.15168966e+09, got {first_sol.objective}"
        )

    def test_98_01_solution_15_bounds(self):
        """Test solution #15 in 98_01.txt has correct bounds."""
        log_file = EXAMPLE_DIR / "98_01.txt"
        if not log_file.exists():
            pytest.skip("98_01.txt not found")

        with open(log_file) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Find solution #15
        sol_15 = None
        for event in result.search_events:
            if event.event_type == "objective" and event.solution_number == 15:
                sol_15 = event
                break

        assert sol_15 is not None, "Solution #15 not found"

        # From the log: #15  2.50s best:920856694 next:[66366584,920856693]
        assert sol_15.lower_bound == 66366584, f"Expected lower_bound=66366584, got {sol_15.lower_bound}"
        assert sol_15.upper_bound == 920856693, f"Expected upper_bound=920856693, got {sol_15.upper_bound}"
        assert sol_15.objective == 920856694, f"Expected objective=920856694, got {sol_15.objective}"
