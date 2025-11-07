"""
Wrapper models that provide DataFrame export capabilities.

These wrappers encapsulate collections from the log and provide methods
to export them as pandas DataFrames for analysis and visualization.
"""

from __future__ import annotations
from typing import List, Optional, Any
from pydantic import BaseModel, Field


# Check if pandas is available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


def _require_pandas():
    """Raise helpful error if pandas is not available."""
    if not PANDAS_AVAILABLE or pd is None:
        raise ImportError(
            "pandas is required for DataFrame export. "
            "Install with: pip install cpsat-logutils[dataframes] "
            "or: pip install pandas"
        )


class SearchEvents(BaseModel):
    """
    Wrapper for search events with DataFrame export capabilities.

    Search events include bound updates, objective improvements, and model changes
    during the solving process.
    """

    events: List[Any] = Field(
        default_factory=list,
        description="List of search events (BoundEvent, ObjectiveEvent, ModelEvent)"
    )

    def bounds_and_solutions_df(self) -> Any:
        """
        Get DataFrame of bound and objective events for convergence analysis.

        Combines BoundEvent and ObjectiveEvent into a unified table suitable
        for plotting convergence (lower bound, upper bound, objective values).

        Returns:
            pandas.DataFrame with columns:
                - time_seconds: Time in seconds
                - event_type: 'bound' or 'objective'
                - value: The bound or objective value
                - solution_number: Solution number (if applicable)
                - num_new_solutions: Number of new solutions (for bounds)
                - description: Event description

        Raises:
            ImportError: If pandas is not installed

        Example:
            >>> df = result.search_events.bounds_and_solutions_df()
            >>> df.plot(x='time_seconds', y='value', kind='line')
        """
        _require_pandas()

        from ..models.search import BoundEvent, ObjectiveEvent

        rows = []
        for event in self.events:
            if isinstance(event, BoundEvent):
                rows.append({
                    'time_seconds': event.time,
                    'event_type': 'bound',
                    'value': event.bound_value,
                    'solution_number': event.solution_number,
                    'num_new_solutions': event.num_new_solutions,
                    'description': event.description or ''
                })
            elif isinstance(event, ObjectiveEvent):
                rows.append({
                    'time_seconds': event.time,
                    'event_type': 'objective',
                    'value': event.objective_value,
                    'solution_number': event.solution_number,
                    'num_new_solutions': None,
                    'description': event.description or ''
                })

        if not rows:
            # Return empty DataFrame with proper columns
            return pd.DataFrame(columns=[
                'time_seconds', 'event_type', 'value', 'solution_number',
                'num_new_solutions', 'description'
            ])

        return pd.DataFrame(rows)

    def model_events_df(self) -> Any:
        """
        Get DataFrame of model events.

        Model events track changes to the model structure during solving
        (e.g., reductions, transformations).

        Returns:
            pandas.DataFrame with columns:
                - time_seconds: Time in seconds
                - description: Event description

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        from ..models.search import ModelEvent

        rows = []
        for event in self.events:
            if isinstance(event, ModelEvent):
                rows.append({
                    'time_seconds': event.time,
                    'description': event.description or ''
                })

        if not rows:
            return pd.DataFrame(columns=['time_seconds', 'description'])

        return pd.DataFrame(rows)


class PresolveEntries(BaseModel):
    """Wrapper for presolve entries with DataFrame export."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of presolve operations"
    )

    def to_dataframe(self) -> Any:
        """
        Get DataFrame of presolve operations.

        Returns:
            pandas.DataFrame with columns:
                - operation: Name of the presolve operation
                - duration_ms: Duration in milliseconds
                - num_removed: Number of items removed (if applicable)

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        rows = []
        for entry in self.entries:
            rows.append({
                'operation': entry.operation,
                'duration_ms': entry.duration_ms if entry.duration_ms is not None else None,
                'num_removed': entry.num_removed if entry.num_removed is not None else None,
            })

        if not rows:
            return pd.DataFrame(columns=['operation', 'duration_ms', 'num_removed'])

        return pd.DataFrame(rows)


class TaskTiming(BaseModel):
    """Wrapper for task timing entries with DataFrame export."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of task timing entries"
    )

    def to_dataframe(self) -> Any:
        """
        Get DataFrame of task timing information.

        Returns:
            pandas.DataFrame with columns:
                - task: Task name
                - duration_seconds: Duration in seconds
                - num_calls: Number of times called

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        rows = []
        for entry in self.entries:
            rows.append({
                'task': entry.task,
                'duration_seconds': entry.duration,
                'num_calls': entry.num_calls if entry.num_calls is not None else None,
            })

        if not rows:
            return pd.DataFrame(columns=['task', 'duration_seconds', 'num_calls'])

        return pd.DataFrame(rows)


class SearchStatistics(BaseModel):
    """Wrapper for search statistics with DataFrame export."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of search statistics entries"
    )

    def to_dataframe(self) -> Any:
        """
        Get DataFrame of search statistics.

        Returns:
            pandas.DataFrame with columns varying based on stat type.
            Common columns: worker_id, num_conflicts, num_branches, etc.

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        rows = []
        for entry in self.entries:
            row = entry.model_dump()
            rows.append(row)

        if not rows:
            # Return empty with common columns
            return pd.DataFrame(columns=['worker_id', 'num_conflicts', 'num_branches'])

        return pd.DataFrame(rows)


class SATStatistics(BaseModel):
    """Wrapper for SAT statistics with DataFrame export."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of SAT statistics entries"
    )

    def to_dataframe(self) -> Any:
        """Get DataFrame of SAT statistics."""
        _require_pandas()

        rows = []
        for entry in self.entries:
            row = entry.model_dump()
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=['worker_id', 'num_clauses', 'num_variables'])

        return pd.DataFrame(rows)


class LNSStatistics(BaseModel):
    """Wrapper for LNS (Large Neighborhood Search) statistics."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of LNS statistics entries"
    )

    def to_dataframe(self) -> Any:
        """Get DataFrame of LNS statistics."""
        _require_pandas()

        rows = []
        for entry in self.entries:
            row = entry.model_dump()
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=['worker_id', 'num_improvements'])

        return pd.DataFrame(rows)


class LSStatistics(BaseModel):
    """Wrapper for LS (Local Search) statistics."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of LS statistics entries"
    )

    def to_dataframe(self) -> Any:
        """Get DataFrame of LS statistics."""
        _require_pandas()

        rows = []
        for entry in self.entries:
            row = entry.model_dump()
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=['worker_id', 'num_moves'])

        return pd.DataFrame(rows)


class LPStatistics(BaseModel):
    """Wrapper for LP (Linear Programming) statistics."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of LP statistics entries"
    )

    def to_dataframe(self) -> Any:
        """Get DataFrame of LP statistics."""
        _require_pandas()

        rows = []
        for entry in self.entries:
            row = entry.model_dump()
            rows.append(row)

        if not rows:
            return pd.DataFrame(columns=['worker_id', 'num_iterations'])

        return pd.DataFrame(rows)


class ObjectiveBoundsTable(BaseModel):
    """Wrapper for objective bounds table with DataFrame export."""

    entries: List[Any] = Field(
        default_factory=list,
        description="List of objective bound entries"
    )

    def to_dataframe(self) -> Any:
        """
        Get DataFrame of objective bounds over time.

        Returns:
            pandas.DataFrame with columns:
                - time_seconds: Time in seconds
                - objective_lb: Lower bound on objective
                - objective_ub: Upper bound on objective
                - gap: Optimality gap (if available)

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        rows = []
        for entry in self.entries:
            rows.append({
                'time_seconds': entry.time,
                'objective_lb': entry.objective_lb,
                'objective_ub': entry.objective_ub,
            })

        if not rows:
            return pd.DataFrame(columns=['time_seconds', 'objective_lb', 'objective_ub'])

        return pd.DataFrame(rows)


class VariableDomains(BaseModel):
    """Wrapper for variable domains with DataFrame export."""

    domains: List[Any] = Field(
        default_factory=list,
        description="List of variable domain descriptions"
    )

    def to_dataframe(self) -> Any:
        """
        Get DataFrame of variable domains.

        Returns:
            pandas.DataFrame with columns:
                - count: Number of variables
                - type: Domain type (Booleans, in, constants, etc.)
                - min_value: Minimum value in domain
                - max_value: Maximum value in domain
                - num_ranges: Number of ranges in domain

        Raises:
            ImportError: If pandas is not installed
        """
        _require_pandas()

        rows = []
        for domain in self.domains:
            num_ranges = len(domain.domain_ranges) if domain.domain_ranges else None
            rows.append({
                'count': domain.count,
                'type': domain.type,
                'min_value': domain.min_value,
                'max_value': domain.max_value,
                'num_ranges': num_ranges,
            })

        if not rows:
            return pd.DataFrame(columns=['count', 'type', 'min_value', 'max_value', 'num_ranges'])

        return pd.DataFrame(rows)
