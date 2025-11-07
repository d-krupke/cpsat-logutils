"""
Main log model for CP-SAT.

This module contains the CPSATLog model, which is the top-level container
for all parsed CP-SAT log data. It brings together all the individual
components (solver info, presolve, search, statistics, response) into
a single structured representation.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from .metadata import LogMetadata
from .solver import SolverInfo, ModelStatistics
from .presolve import PresolveSummary, PreloadingInfo
from .search import SearchInfo
from .statistics import (
    SolutionRepositories,
    SolutionEntry,
    ImprovingBoundsShared,
    ClausesShared,
)
from .response import CPSolverResponse
from .wrappers import (
    SearchEvents,
    PresolveEntries,
    TaskTiming,
    SearchStatistics,
    SATStatistics,
    LNSStatistics,
    LSStatistics,
    LPStatistics,
    ObjectiveBoundsTable,
)


class CPSATLog(BaseModel):
    """
    Complete parsed CP-SAT log.

    This is the top-level model that contains all information extracted
    from a CP-SAT log. It provides a structured, type-safe representation
    that can be easily serialized to JSON for web frontends or analyzed
    programmatically.

    **Log structure:**
    1. **metadata**: Completeness info and line references
    2. **solver_info**: Version and configuration
    3. **initial_model**: Model before presolve
    4. **presolve_log/presolve_summary**: Presolve transformations
    5. **presolved_model**: Model after presolve
    6. **search_info**: Search configuration
    7. **search_events**: Real-time search progress
    8. **Statistics**: Various solver metrics
    9. **response**: Final result summary

    Example:
        >>> from cpsat_logutils import LogParser
        >>>
        >>> # Parse a log
        >>> parser = LogParser(log_text)
        >>> log = parser.parse()
        >>>
        >>> # Access structured data
        >>> print(f"Solver: {log.solver_info.version}")
        >>> print(f"Status: {log.response.status}")
        >>> print(f"Complete: {log.metadata.is_complete}")
        >>>
        >>> # Analyze optimization progress
        >>> solutions = [e for e in log.search_events if e.event_type == "objective"]
        >>> for sol in solutions:
        ...     print(f"Solution {sol.solution_number}: {sol.objective}")
        >>>
        >>> # Export to JSON
        >>> json_data = log.model_dump_json(indent=2)
        >>> with open("log.json", "w") as f:
        ...     f.write(json_data)

    Example:
        >>> # Check log quality
        >>> if not log.metadata.is_complete:
        ...     print("Warning: Incomplete log!")
        ...     print(f"Missing: {log.metadata.missing_sections}")
        >>>
        >>> # Compare model sizes
        >>> if log.initial_model and log.presolved_model:
        ...     initial_vars = log.initial_model.num_variables
        ...     presolved_vars = log.presolved_model.num_variables
        ...     reduction = (1 - presolved_vars / initial_vars) * 100
        ...     print(f"Presolve reduced variables by {reduction:.1f}%")

    Example:
        >>> # Analyze solver performance
        >>> print(f"Wall time: {log.response.walltime}s")
        >>> print(f"Conflicts: {log.response.conflicts}")
        >>> print(f"Branches: {log.response.branches}")
        >>>
        >>> # Find most time-consuming subsolver
        >>> if log.task_timing:
        ...     top = max(log.task_timing, key=lambda t: t.time_spent or 0)
        ...     print(f"Most time: {top.task_name} ({top.time_spent:.2f}s)")
    """

    model_config = ConfigDict(extra="forbid")

    metadata: LogMetadata = Field(
        ...,
        description=(
            "Metadata about the log, including completeness status and "
            "line references mapping parsed sections to original log lines"
        )
    )

    solver_info: SolverInfo = Field(
        ...,
        description=(
            "Solver configuration: version, parameters, and worker count"
        )
    )

    initial_model: Optional[ModelStatistics] = Field(
        None,
        description=(
            "Statistics about the initial model before presolve. "
            "Shows original problem size and structure."
        )
    )

    presolve_log: PresolveEntries = Field(
        default_factory=lambda: PresolveEntries(entries=[]),
        description=(
            "Detailed log of presolve operations. "
            "Each entry represents a presolve transformation step. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    presolve_summary: Optional[PresolveSummary] = Field(
        None,
        description=(
            "Summary of presolve transformations, including affine relations "
            "and rules applied"
        )
    )

    presolved_model: Optional[ModelStatistics] = Field(
        None,
        description=(
            "Statistics about the model after presolve. "
            "Compare with initial_model to see presolve effectiveness."
        )
    )

    preloading_info: Optional[PreloadingInfo] = Field(
        None,
        description=(
            "Information from the preloading phase, including symmetry "
            "detection and encoding details"
        )
    )

    search_info: Optional[SearchInfo] = Field(
        None,
        description=(
            "Search configuration: start time, workers, subsolvers. "
            "Describes how the parallel search is organized."
        )
    )

    search_events: SearchEvents = Field(
        default_factory=lambda: SearchEvents(events=[]),
        description=(
            "Real-time search progress events. "
            "Includes solution improvements, bound updates, and model changes. "
            "Use .bounds_and_solutions_df() for convergence analysis, "
            "or .model_events_df() for model changes."
        )
    )

    task_timing: TaskTiming = Field(
        default_factory=lambda: TaskTiming(entries=[]),
        description=(
            "Time spent by each subsolver task. "
            "Useful for understanding which strategies consume the most time. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    search_stats: SearchStatistics = Field(
        default_factory=lambda: SearchStatistics(entries=[]),
        description=(
            "Core search statistics (conflicts, branches, propagations) "
            "broken down by subsolver. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    sat_stats: SATStatistics = Field(
        default_factory=lambda: SATStatistics(entries=[]),
        description=(
            "Detailed SAT solver statistics by subsolver. "
            "Contains low-level metrics like clause learning. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    lns_stats: LNSStatistics = Field(
        default_factory=lambda: LNSStatistics(entries=[]),
        description=(
            "Large Neighborhood Search statistics. "
            "Shows LNS subsolver effectiveness at finding solutions. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    ls_stats: LSStatistics = Field(
        default_factory=lambda: LSStatistics(entries=[]),
        description=(
            "Local Search statistics. "
            "Shows LS subsolver solution improvements. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    lp_stats: LPStatistics = Field(
        default_factory=lambda: LPStatistics(entries=[]),
        description=(
            "Linear Programming statistics. "
            "Shows LP relaxation usage and effectiveness. "
            "Use .to_dataframe() to export as pandas DataFrame."
        )
    )

    solution_repositories: Optional[SolutionRepositories] = Field(
        None,
        description=(
            "Statistics about solution repositories: how many solutions "
            "were added, queried, and synchronized between workers"
        )
    )

    solutions: List[SolutionEntry] = Field(
        default_factory=list,
        description=(
            "Solutions found by each subsolver with quality rankings"
        )
    )

    objective_bounds: ObjectiveBoundsTable = Field(
        default_factory=lambda: ObjectiveBoundsTable(entries=[]),
        description=(
            "Objective bound improvements by subsolver. "
            "Shows which subsolvers are effective at finding bounds. "
            "Use .to_dataframe() to export as pandas DataFrame for convergence plotting."
        )
    )

    improving_bounds_shared: Optional[ImprovingBoundsShared] = Field(
        None,
        description=(
            "Statistics about bound improvements shared between workers. "
            "Shows parallel cooperation effectiveness."
        )
    )

    clauses_shared: Optional[ClausesShared] = Field(
        None,
        description=(
            "Statistics about learned clauses shared between workers. "
            "Key metric for parallel SAT solving performance."
        )
    )

    response: CPSolverResponse = Field(
        ...,
        description=(
            "Final solver response with status, objective, bounds, and "
            "overall performance metrics"
        )
    )

    comments: List[str] = Field(
        default_factory=list,
        description=(
            "Comment lines from the log (lines starting with //). "
            "May contain additional context or debugging information."
        )
    )
