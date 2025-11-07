"""
Tests for DataFrame export functionality.

These tests require pandas to be installed:
    pip install cpsat-logutils[dataframes]
"""

import pytest
from pathlib import Path
from cpsat_logutils import LogParser

# Try importing pandas
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Get example logs
EXAMPLE_DIR = Path(__file__).parent.parent / "example_logs"


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestSearchEventsDataFrames:
    """Test DataFrame export for search events."""

    def test_bounds_and_solutions_df(self):
        """Test bounds_and_solutions_df() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.search_events.bounds_and_solutions_df()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have expected columns
        expected_columns = {
            'time_seconds', 'event_type', 'value',
            'solution_number', 'gap_percent', 'subsolver', 'additional_info'
        }
        assert set(df.columns) == expected_columns

        # Should have data (98_01.txt has many events)
        assert len(df) > 0

        # All event_type values should be 'bound' or 'objective'
        assert set(df['event_type'].unique()).issubset({'bound', 'objective'})

        # time_seconds should be numeric
        assert pd.api.types.is_numeric_dtype(df['time_seconds'])

        # value should be numeric
        assert pd.api.types.is_numeric_dtype(df['value'])

        # Should have solution events (objective)
        objective_events = df[df['event_type'] == 'objective']
        assert len(objective_events) > 0

        # Solution numbers should be sequential for objectives
        sol_nums = objective_events['solution_number'].dropna()
        if len(sol_nums) > 0:
            assert sol_nums.iloc[0] == 1  # First solution is #1

    def test_model_events_df(self):
        """Test model_events_df() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.search_events.model_events_df()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have expected columns
        expected_columns = {
            'time_seconds', 'vars_remaining', 'vars_total',
            'constraints_remaining', 'constraints_total', 'additional_info'
        }
        assert set(df.columns) == expected_columns

        # Model events may be empty for some logs (CP-SAT doesn't always log these)

    def test_empty_search_events(self):
        """Test DataFrame export with no search events."""
        log_content = """Starting CP-SAT solver v9.8.0
Parameters: {}

CpSolverResponse summary:
status: OPTIMAL
objective: 0
best_bound: 0
booleans: 1
conflicts: 0
branches: 0
propagations: 0
integer_propagations: 0
restarts: 0
lp_iterations: 0
walltime: 0.01
usertime: 0.01
deterministic_time: 0
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Should return empty DataFrames with proper columns
        df_bounds = result.search_events.bounds_and_solutions_df()
        assert isinstance(df_bounds, pd.DataFrame)
        assert len(df_bounds) == 0
        assert 'time_seconds' in df_bounds.columns

        df_model = result.search_events.model_events_df()
        assert isinstance(df_model, pd.DataFrame)
        assert len(df_model) == 0
        assert 'time_seconds' in df_model.columns


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestPresolveDataFrame:
    """Test DataFrame export for presolve log."""

    def test_presolve_log_df(self):
        """Test presolve_log.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.presolve_log.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have data
        assert len(df) > 0

        # Should have expected columns
        expected_columns = {'operation', 'wall_time_seconds'}
        assert expected_columns.issubset(set(df.columns))

        # wall_time_seconds should be numeric
        assert pd.api.types.is_numeric_dtype(df['wall_time_seconds'])

        # Operations should be strings
        assert all(isinstance(op, str) for op in df['operation'])


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestStatisticsDataFrames:
    """Test DataFrame export for various statistics tables."""

    def test_task_timing_df(self):
        """Test task_timing.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.task_timing.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have data
        assert len(df) > 0

        # Should have expected columns
        expected_columns = {'task_name', 'time_spent_seconds'}
        assert expected_columns.issubset(set(df.columns))

        # time_spent_seconds should be numeric if not all None
        if df['time_spent_seconds'].notna().any():
            # Check that non-null values are numeric
            assert all(isinstance(v, (int, float)) for v in df['time_spent_seconds'].dropna())

    def test_search_stats_df(self):
        """Test search_stats.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.search_stats.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have data
        assert len(df) > 0

        # Should have expected columns (at least subsolver and booleans)
        assert 'subsolver' in df.columns

        # Numeric columns should be numeric
        numeric_cols = ['booleans', 'conflicts', 'branches', 'restarts']
        for col in numeric_cols:
            if col in df.columns:
                assert pd.api.types.is_numeric_dtype(df[col])

    def test_sat_stats_df(self):
        """Test sat_stats.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.sat_stats.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # If data exists, check structure
        if len(df) > 0:
            assert 'subsolver' in df.columns

    def test_lns_stats_df(self):
        """Test lns_stats.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.lns_stats.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # LNS stats may be empty for some logs
        if len(df) > 0:
            assert 'subsolver' in df.columns

    def test_ls_stats_df(self):
        """Test ls_stats.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.ls_stats.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # LS stats may be empty for some logs
        if len(df) > 0:
            assert 'subsolver' in df.columns

    def test_lp_stats_df(self):
        """Test lp_stats.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.lp_stats.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # LP stats may be empty for some logs
        if len(df) > 0:
            assert 'subsolver' in df.columns

    def test_objective_bounds_df(self):
        """Test objective_bounds.to_dataframe() export."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get DataFrame
        df = result.objective_bounds.to_dataframe()

        # Should be a DataFrame
        assert isinstance(df, pd.DataFrame)

        # Should have data
        assert len(df) > 0

        # Should have expected columns
        expected_columns = {'subsolver', 'num_bounds'}
        assert expected_columns.issubset(set(df.columns))

        # num_bounds should be numeric
        assert pd.api.types.is_numeric_dtype(df['num_bounds'])


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestSnakeCaseColumns:
    """Test that all DataFrame exports use snake_case column naming."""

    def test_all_columns_snake_case(self):
        """Verify all DataFrame columns use snake_case."""
        log_path = EXAMPLE_DIR / "98_01.txt"
        with open(log_path) as f:
            log_text = f.read()

        parser = LogParser(log_text)
        result = parser.parse()

        # Get all DataFrames
        dfs = {
            'bounds_and_solutions': result.search_events.bounds_and_solutions_df(),
            'model_events': result.search_events.model_events_df(),
            'presolve_log': result.presolve_log.to_dataframe(),
            'task_timing': result.task_timing.to_dataframe(),
            'search_stats': result.search_stats.to_dataframe(),
            'sat_stats': result.sat_stats.to_dataframe(),
            'lns_stats': result.lns_stats.to_dataframe(),
            'ls_stats': result.ls_stats.to_dataframe(),
            'lp_stats': result.lp_stats.to_dataframe(),
            'objective_bounds': result.objective_bounds.to_dataframe(),
        }

        # Check all columns are snake_case
        for name, df in dfs.items():
            for col in df.columns:
                # snake_case: lowercase with underscores
                assert col.islower() or '_' in col, (
                    f"Column '{col}' in {name} DataFrame is not snake_case"
                )
                # No spaces
                assert ' ' not in col, (
                    f"Column '{col}' in {name} DataFrame contains spaces"
                )
                # No camelCase (check for lowercase followed by uppercase)
                assert not any(
                    col[i].islower() and col[i+1].isupper()
                    for i in range(len(col)-1)
                ), f"Column '{col}' in {name} DataFrame appears to be camelCase"


@pytest.mark.skipif(not PANDAS_AVAILABLE, reason="pandas not installed")
class TestDataFrameWithoutPandas:
    """Test error handling when pandas is not available."""

    def test_requires_pandas_error(self, monkeypatch):
        """Test that helpful error is raised when pandas is not available."""
        # This test temporarily makes pandas unavailable
        import sys
        import cpsat_logutils.models.wrappers as wrappers

        # Save original state
        original_pandas = wrappers.PANDAS_AVAILABLE
        original_pd = wrappers.pd

        # Make pandas unavailable
        wrappers.PANDAS_AVAILABLE = False
        wrappers.pd = None

        try:
            log_path = EXAMPLE_DIR / "98_01.txt"
            with open(log_path) as f:
                log_text = f.read()

            parser = LogParser(log_text)
            result = parser.parse()

            # Should raise ImportError with helpful message
            with pytest.raises(ImportError) as exc_info:
                result.search_events.bounds_and_solutions_df()

            assert "pandas is required" in str(exc_info.value).lower()
            assert "dataframes" in str(exc_info.value).lower()

        finally:
            # Restore original state
            wrappers.PANDAS_AVAILABLE = original_pandas
            wrappers.pd = original_pd


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
