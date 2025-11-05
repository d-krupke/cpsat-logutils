"""
Search-related models for CP-SAT logs.

This module contains models representing the search phase, including:
- Search configuration and subsolvers
- Search progress events (solutions, bounds, model updates)
"""

from typing import Optional, List, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class SubsolverInfo(BaseModel):
    """
    Information about the parallel subsolvers used by CP-SAT.

    CP-SAT uses portfolio parallelism, running multiple different solving
    strategies (subsolvers) in parallel. Different subsolvers excel at
    different problem types.

    Subsolver types:
    - **full_problem**: Complete search strategies
    - **first_solution**: Heuristics focused on finding first feasible solution
    - **incomplete**: Large Neighborhood Search (LNS) strategies
    - **helper**: Auxiliary strategies (e.g., probing, clause learning)
    - **interleaved**: Older versions used interleaved search

    Example:
        >>> subsolvers = result.search_info.subsolvers
        >>> print(f"Full problem solvers: {len(subsolvers.full_problem)}")
        >>> print(f"LNS solvers: {len(subsolvers.incomplete)}")
    """

    model_config = ConfigDict(extra="forbid")

    full_problem: List[str] = Field(
        default_factory=list,
        description=(
            "List of full problem subsolvers. "
            "These perform complete search on the entire problem. "
            "Examples: 'no_lp', 'default_lp', 'max_lp', 'quick_restart'"
        )
    )

    first_solution: List[str] = Field(
        default_factory=list,
        description=(
            "List of first solution subsolvers. "
            "These use heuristics to quickly find an initial feasible solution. "
            "Useful for optimization: any feasible solution provides a bound."
        )
    )

    incomplete: List[str] = Field(
        default_factory=list,
        description=(
            "List of incomplete/LNS subsolvers. "
            "These use Large Neighborhood Search: fix most variables, "
            "search in a neighborhood of current solution. "
            "Effective for improving solutions but can't prove optimality alone."
        )
    )

    helper: List[str] = Field(
        default_factory=list,
        description=(
            "List of helper subsolvers. "
            "These don't search for solutions directly but aid other solvers. "
            "Examples: 'probing_worker' (learns implications), 'synchronization_agent'"
        )
    )

    interleaved: List[str] = Field(
        default_factory=list,
        description=(
            "List of interleaved subsolvers (used in older CP-SAT versions). "
            "Modern versions use 'full_problem' and 'incomplete' instead."
        )
    )


class SearchInfo(BaseModel):
    """
    Configuration information about the search phase.

    Describes when search started, how many workers are being used,
    which subsolvers are active, and the search strategy.

    Search typically starts after presolve completes. The start_time
    indicates presolve duration.

    Example:
        >>> info = result.search_info
        >>> print(f"Search started at {info.start_time:.2f}s")
        >>> print(f"Using {info.num_workers} workers")
        >>> print(f"Search type: {info.search_type}")
    """

    model_config = ConfigDict(extra="forbid")

    start_time: float = Field(
        ...,
        description=(
            "Wall clock time when search started, in seconds from solver start. "
            "This also indicates how long presolve took. "
            "Example: 0.5 means presolve completed in 0.5 seconds."
        ),
        ge=0.0
    )

    num_workers: int = Field(
        ...,
        description=(
            "Number of parallel search workers. "
            "Each worker runs a different subsolver strategy. "
            "Typically equals CPU core count. More workers = faster but more memory."
        ),
        ge=1
    )

    subsolvers: SubsolverInfo = Field(
        ...,
        description=(
            "Information about which subsolvers are being used. "
            "CP-SAT dynamically allocates workers to different strategies."
        )
    )

    search_type: Literal["parallel", "sequential"] = Field(
        "parallel",
        description=(
            "'parallel': Multiple workers search simultaneously (modern CP-SAT). "
            "'sequential': Single-threaded search (older versions or when num_workers=1)."
        )
    )


class BoundEvent(BaseModel):
    """
    Event representing an improvement to the objective bound.

    For optimization problems, CP-SAT maintains bounds on the optimal objective:
    - **Lower bound**: Best proven bound (no better solution can exist)
    - **Upper bound**: Best solution found so far

    For minimization: lower_bound ≤ optimal ≤ upper_bound
    For maximization: upper_bound ≥ optimal ≥ lower_bound

    Bound improvements don't find new solutions but prove no better solution
    exists above/below the bound.

    Example:
        >>> # Filter bound events
        >>> bound_events = [e for e in result.search_events if e.event_type == "bound"]
        >>> for event in bound_events[:5]:
        ...     print(f"{event.time:.2f}s: bound improved to {event.bound}")
    """

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["bound"] = "bound"

    time: float = Field(
        ...,
        description="Wall clock time in seconds when this bound was found",
        ge=0.0
    )

    best_objective: Optional[float] = Field(
        None,
        description=(
            "Current best objective value (from best solution found). "
            "None if no solution found yet."
        )
    )

    bound: float = Field(
        ...,
        description=(
            "The new bound value. "
            "For minimization, this is a lower bound. "
            "For maximization, this is an upper bound."
        )
    )

    lower_bound: Optional[float] = Field(
        None,
        description="Lower bound (minimization) or None"
    )

    upper_bound: Optional[float] = Field(
        None,
        description="Upper bound (maximization) or None"
    )

    subsolver: str = Field(
        "",
        description=(
            "Name of the subsolver that found this bound. "
            "Example: 'default_lp' (linear programming relaxation)"
        )
    )

    additional_info: str = Field(
        "",
        description="Additional information about the bound (if any)"
    )


class ObjectiveEvent(BaseModel):
    """
    Event representing a new solution with its objective value.

    Each time CP-SAT finds a solution (feasible or improving), it logs
    an objective event. These show the optimization progress over time.

    The gap percentage shows how close we are to optimal:
    - gap = 0%: Solution is proven optimal
    - gap < 1%: Very close to optimal
    - gap > 10%: Significant room for improvement

    Example:
        >>> # Track solution quality over time
        >>> solutions = [e for e in result.search_events if e.event_type == "objective"]
        >>> for sol in solutions:
        ...     print(f"#{sol.solution_number} at {sol.time:.2f}s: "
        ...           f"obj={sol.objective}, gap={sol.gap_percent:.2f}%")
    """

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["objective"] = "objective"

    solution_number: int = Field(
        ...,
        description=(
            "Sequential solution number (starting from 1). "
            "Useful for tracking solution progress."
        ),
        ge=1
    )

    time: float = Field(
        ...,
        description="Wall clock time in seconds when this solution was found",
        ge=0.0
    )

    objective: float = Field(
        ...,
        description=(
            "Objective value of this solution. "
            "For minimization, lower is better. "
            "For maximization, higher is better."
        )
    )

    bound: float = Field(
        ...,
        description=(
            "Best bound at the time this solution was found. "
            "Gap between objective and bound shows remaining optimization potential."
        )
    )

    lower_bound: Optional[float] = Field(
        None,
        description="Lower bound if minimization, None otherwise"
    )

    upper_bound: Optional[float] = Field(
        None,
        description="Upper bound if maximization, None otherwise"
    )

    gap_percent: Optional[float] = Field(
        None,
        description=(
            "Optimality gap as percentage: 100 * |objective - bound| / |objective|. "
            "0% means proven optimal. "
            "None if objective is zero (undefined gap)."
        ),
        ge=0.0
    )

    subsolver: str = Field(
        "",
        description=(
            "Name of the subsolver that found this solution. "
            "Examples: 'no_lp', 'quick_restart_no_lp', 'rnd_var_lns_default'"
        )
    )

    additional_info: str = Field(
        "",
        description="Additional information (e.g., 'left', 'right' indicating search direction)"
    )


class ModelEvent(BaseModel):
    """
    Event representing a change to the model structure during search.

    As search progresses, CP-SAT may fix variables or add constraints,
    effectively reducing the model size. Model events show this reduction.

    Large reductions indicate effective pruning and learning.

    Example:
        >>> # Track model reduction
        >>> model_events = [e for e in result.search_events if e.event_type == "model"]
        >>> for event in model_events:
        ...     var_reduction = (1 - event.vars_remaining / event.vars_total) * 100
        ...     print(f"{event.time:.2f}s: {var_reduction:.0f}% variables fixed")
    """

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["model"] = "model"

    time: float = Field(
        ...,
        description="Wall clock time in seconds when this model update occurred",
        ge=0.0
    )

    vars_remaining: int = Field(
        ...,
        description=(
            "Number of unfixed variables remaining. "
            "Decreases as search fixes variables."
        ),
        ge=0
    )

    vars_total: int = Field(
        ...,
        description="Total number of variables in the model",
        ge=0
    )

    constraints_remaining: int = Field(
        ...,
        description=(
            "Number of constraints still active. "
            "May decrease as constraints become trivially satisfied."
        ),
        ge=0
    )

    constraints_total: int = Field(
        ...,
        description="Total number of constraints in the model",
        ge=0
    )

    additional_info: str = Field(
        "",
        description="Additional information about the model update"
    )


# Union type for all search events
SearchEvent = Union[BoundEvent, ObjectiveEvent, ModelEvent]
