"""
Statistics models for CP-SAT logs.

This module contains models for various statistics collected during solving:
- Task timing: How much time each subsolver spent
- Search statistics: Conflicts, branches, propagations per subsolver
- SAT/LNS/LS/LP statistics: Specialized metrics for different solving approaches
- Information sharing: How subsolvers share bounds and clauses
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class TaskTimingEntry(BaseModel):
    """
    Timing statistics for a specific subsolver task.

    CP-SAT runs multiple subsolvers in parallel, each performing different
    tasks. Task timing shows how much time each subsolver spent and how
    many times it ran.

    Useful for:
    - Understanding which strategies are consuming the most time
    - Identifying inefficient subsolvers
    - Tuning parallel strategy allocation

    Example:
        >>> # Find the most time-consuming subsolver
        >>> task_timing = sorted(result.task_timing, key=lambda t: t.time_spent or 0, reverse=True)
        >>> top_task = task_timing[0]
        >>> print(f"{top_task.task_name}: {top_task.time_spent:.2f}s ({top_task.num_runs} runs)")
    """

    model_config = ConfigDict(extra="forbid")

    task_name: str = Field(
        ...,
        description=(
            "Name of the task/subsolver. "
            "Examples: 'default_lp', 'quick_restart_no_lp', 'rnd_var_lns_default'"
        ),
        min_length=1
    )

    num_runs: Optional[int] = Field(
        None,
        description=(
            "Number of times this subsolver ran. "
            "Multiple runs indicate the subsolver restarted or ran in batches."
        ),
        ge=0
    )

    time_spent: Optional[float] = Field(
        None,
        description=(
            "Total wall clock time spent on this task, in seconds. "
            "High values indicate time-consuming strategies."
        ),
        ge=0.0
    )

    deterministic_time: Optional[float] = Field(
        None,
        description=(
            "Deterministic time (reproducible across runs). "
            "Used for ensuring consistent behavior across different hardware."
        ),
        ge=0.0
    )

    additional_stats: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional task-specific statistics"
    )


class SearchStatEntry(BaseModel):
    """
    Search statistics for a specific subsolver.

    These are core SAT solver metrics: conflicts (failed attempts), branches
    (decision points), restarts (search tree resets), and propagations (constraint
    deductions).

    Higher conflicts/branches indicate harder problems. High propagation counts
    show active constraint propagation.

    Example:
        >>> # Compare search efficiency across subsolvers
        >>> for stat in result.search_stats:
        ...     if stat.conflicts and stat.branches:
        ...         ratio = stat.branches / stat.conflicts
        ...         print(f"{stat.subsolver}: {ratio:.2f} branches per conflict")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the subsolver these statistics belong to",
        min_length=1
    )

    booleans: Optional[int] = Field(
        None,
        description="Number of boolean variables handled by this subsolver",
        ge=0
    )

    conflicts: Optional[int] = Field(
        None,
        description=(
            "Number of conflicts encountered. "
            "A conflict occurs when the solver reaches an impossible state "
            "and must backtrack. More conflicts = harder problem."
        ),
        ge=0
    )

    branches: Optional[int] = Field(
        None,
        description=(
            "Number of branching decisions made. "
            "Each branch is a choice of variable assignment during search."
        ),
        ge=0
    )

    restarts: Optional[int] = Field(
        None,
        description=(
            "Number of search restarts. "
            "Restarts help escape bad search regions by restarting with learned clauses."
        ),
        ge=0
    )

    bool_propagations: Optional[int] = Field(
        None,
        description=(
            "Number of boolean constraint propagations. "
            "Propagations deduce variable values from constraints without branching."
        ),
        ge=0
    )

    integer_propagations: Optional[int] = Field(
        None,
        description=(
            "Number of integer constraint propagations. "
            "Similar to bool propagations but for integer variables."
        ),
        ge=0
    )


class SATStatEntry(BaseModel):
    """
    SAT-specific statistics for a subsolver.

    Contains detailed SAT solver metrics like clause learning, literal
    propagations, and other low-level SAT operations.

    Example:
        >>> # Examine SAT solver activity
        >>> for sat_stat in result.sat_stats:
        ...     print(f"{sat_stat.subsolver}:")
        ...     for metric, value in sat_stat.stats.items():
        ...         print(f"  {metric}: {value}")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the subsolver",
        min_length=1
    )

    stats: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "SAT-specific statistics. "
            "Common keys: 'literals', 'clauses', 'binary_clauses', etc."
        )
    )


class LNSStatEntry(BaseModel):
    """
    Large Neighborhood Search (LNS) statistics.

    LNS is an incomplete search strategy that fixes most variables and
    searches in a neighborhood of the current solution. It's effective for
    improving solutions but can't prove optimality.

    The improvement_range shows the quality of solutions found (measured
    in objective value improvements).

    Example:
        >>> # Evaluate LNS effectiveness
        >>> for lns_stat in result.lns_stats:
        ...     if lns_stat.num_solutions:
        ...         print(f"{lns_stat.subsolver}: {lns_stat.num_solutions} solutions")
        ...         if lns_stat.improvement_range:
        ...             print(f"  Improvements: {lns_stat.improvement_range}")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the LNS subsolver",
        min_length=1
    )

    num_solutions: Optional[int] = Field(
        None,
        description=(
            "Number of solutions found by this LNS subsolver. "
            "Higher values indicate productive LNS strategies."
        ),
        ge=0
    )

    improvement_range: Optional[List[int]] = Field(
        None,
        description=(
            "Range of solution improvements as [min, max]. "
            "Measures objective value improvements from LNS."
        )
    )


class LSStatEntry(BaseModel):
    """
    Local Search (LS) statistics.

    Local search explores neighboring solutions by making small changes.
    Similar to LNS but typically uses different neighborhood structures.

    Example:
        >>> # Compare LS performance
        >>> for ls_stat in result.ls_stats:
        ...     print(f"{ls_stat.subsolver}: {ls_stat.num_solutions} solutions")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the LS subsolver",
        min_length=1
    )

    num_solutions: Optional[int] = Field(
        None,
        description="Number of solutions found by this LS subsolver",
        ge=0
    )

    improvement_range: Optional[List[int]] = Field(
        None,
        description="Range of solution improvements as [min, max]"
    )


class LPStatEntry(BaseModel):
    """
    Linear Programming (LP) statistics.

    LP relaxations provide bounds by solving a continuous relaxation of the
    problem. LP statistics show how the LP subsolver performed.

    Example:
        >>> # Examine LP solver usage
        >>> for lp_stat in result.lp_stats:
        ...     print(f"{lp_stat.subsolver}:")
        ...     for key, value in lp_stat.stats.items():
        ...         print(f"  {key}: {value}")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the LP subsolver",
        min_length=1
    )

    stats: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "LP-specific statistics. "
            "May include iterations, simplex operations, etc."
        )
    )


class SolutionRepositories(BaseModel):
    """
    Statistics about solution repositories.

    CP-SAT maintains repositories of solutions found by different subsolvers.
    These statistics show how many solutions were added, queried, and
    synchronized between workers.

    Example:
        >>> repos = result.solution_repositories
        >>> if repos:
        ...     for repo_name, stats in repos.repositories.items():
        ...         print(f"{repo_name}: {stats.get('added', 0)} solutions added")
    """

    model_config = ConfigDict(extra="forbid")

    repositories: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description=(
            "Repository statistics by name. "
            "Common keys in each dict: 'added', 'queried', 'ignored', 'synchro'"
        )
    )


class ObjectiveBoundEntry(BaseModel):
    """
    Objective bound statistics by subsolver.

    Shows which subsolvers contributed bound improvements and how many.
    Useful for understanding which strategies are effective at proving bounds.

    Example:
        >>> # Find most productive bound-finding subsolvers
        >>> bounds_sorted = sorted(result.objective_bounds,
        ...                        key=lambda b: b.num_bounds, reverse=True)
        >>> for entry in bounds_sorted[:5]:
        ...     print(f"{entry.subsolver}: {entry.num_bounds} bounds")
    """

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(
        ...,
        description="Name of the subsolver",
        min_length=1
    )

    num_bounds: int = Field(
        ...,
        description="Number of bound improvements found by this subsolver",
        ge=0
    )


class ImprovingBoundsShared(BaseModel):
    """
    Statistics about improving bounds shared between workers.

    In parallel search, workers share bound improvements to help each other
    prune their search space. This shows how many bounds each subsolver
    contributed to the shared pool.

    Example:
        >>> if result.improving_bounds_shared:
        ...     for subsolver, count in result.improving_bounds_shared.bounds_by_subsolver.items():
        ...         print(f"{subsolver} shared {count} bounds")
    """

    model_config = ConfigDict(extra="forbid")

    bounds_by_subsolver: Dict[str, int] = Field(
        default_factory=dict,
        description="Number of bounds shared by each subsolver"
    )


class ClausesShared(BaseModel):
    """
    Statistics about clauses shared between workers.

    When one worker learns a conflict clause (a constraint implied by the
    problem), it can share it with other workers to help them avoid the
    same bad search paths.

    Clause sharing is a key component of parallel SAT solving performance.

    Example:
        >>> if result.clauses_shared:
        ...     for subsolver, count in result.clauses_shared.clauses_by_subsolver.items():
        ...         print(f"{subsolver} shared {count} clauses")
    """

    model_config = ConfigDict(extra="forbid")

    clauses_by_subsolver: Dict[str, int] = Field(
        default_factory=dict,
        description="Number of clauses shared by each subsolver"
    )
