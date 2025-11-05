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
    Event representing an improvement to the objective bound (without finding a new solution).

    CP-SAT can improve bounds through techniques like LP relaxation, cutting planes,
    or domain propagation without finding a complete solution. These prove that
    no solution better than the bound exists.

    The `next:[a,b]` field from the log represents the search interval:
    - For minimization: [proven_lower_bound, ~current_objective]
    - For maximization: [~current_objective, proven_upper_bound]

    Example:
        >>> # Filter bound events
        >>> bound_events = [e for e in result.search_events if e.event_type == "bound"]
        >>> for event in bound_events[:5]:
        ...     print(f"{event.time:.2f}s: proven bound {event.proven_bound}")
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
            "Current best objective value (from best solution found so far). "
            "None/inf if no solution found yet."
        )
    )

    proven_bound: float = Field(
        ...,
        description=(
            "The proven bound on the optimal objective. "
            "For minimization: no solution < proven_bound exists. "
            "For maximization: no solution > proven_bound exists."
        )
    )

    next_min: Optional[float] = Field(
        None,
        description=(
            "Lower limit of the search interval from next:[min,max]. "
            "For minimization: this is the proven lower bound. "
            "For maximization: this is near the current objective."
        )
    )

    next_max: Optional[float] = Field(
        None,
        description=(
            "Upper limit of the search interval from next:[min,max]. "
            "For minimization: this is near the current objective. "
            "For maximization: this is the proven upper bound."
        )
    )

    subsolver: str = Field(
        "",
        description=(
            "Name of the subsolver that found this bound. "
            "Example: 'default_lp', 'objective_shaving_search_no_lp'"
        )
    )

    additional_info: str = Field(
        "",
        description="Additional information about the bound event"
    )


class ObjectiveEvent(BaseModel):
    """
    Event representing a new solution with its objective value.

    Each time CP-SAT finds a solution (feasible or improving), it logs
    an objective event showing the solution's objective and the search interval
    for finding better solutions.

    The `next:[a,b]` field represents where CP-SAT will search next:
    - **Minimization** (objectives decrease over time):
      - next:[proven_lower, ~objective] where `a` is the proven bound
      - Gap = (objective - a) / |objective|

    - **Maximization** (objectives increase over time):
      - next:[~objective, proven_upper] where `b` is the proven bound
      - Gap = (b - objective) / |objective|

    When next:[], the solution is proven optimal (gap = 0%).

    Example:
        >>> # Track solution quality over time
        >>> solutions = [e for e in result.search_events if e.event_type == "objective"]
        >>> for sol in solutions:
        ...     gap_str = f"{sol.gap_percent:.2f}%" if sol.gap_percent else "optimal"
        ...     print(f"#{sol.solution_number} at {sol.time:.2f}s: "
        ...           f"obj={sol.objective}, gap={gap_str}")
    """

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["objective"] = "objective"

    solution_number: int = Field(
        ...,
        description="Sequential solution number (starting from 1)",
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
            "For minimization, this decreases over time. "
            "For maximization, this increases over time."
        )
    )

    proven_bound: float = Field(
        ...,
        description=(
            "Proven bound on the optimal objective at this point in the search. "
            "For minimization: no solution better than this lower bound exists. "
            "For maximization: no solution better than this upper bound exists. "
            "Equal to objective when next:[] (proven optimal)."
        )
    )

    next_min: Optional[float] = Field(
        None,
        description=(
            "Lower limit of search interval from next:[min,max]. "
            "For minimization: the proven lower bound. "
            "For maximization: approximately current_objective + ε. "
            "None when next:[] (optimal)."
        )
    )

    next_max: Optional[float] = Field(
        None,
        description=(
            "Upper limit of search interval from next:[min,max]. "
            "For minimization: approximately current_objective - ε. "
            "For maximization: the proven upper bound. "
            "None when next:[] (optimal)."
        )
    )

    gap_percent: Optional[float] = Field(
        None,
        description=(
            "Optimality gap as percentage. "
            "0% or None means proven optimal. "
            "Calculated as: 100 * |objective - proven_bound| / |objective|"
        ),
        ge=0.0
    )

    subsolver: str = Field(
        "",
        description=(
            "Name of the subsolver that found this solution. "
            "Examples: 'default_lp', 'quick_restart_no_lp', 'rnd_var_lns'"
        )
    )

    additional_info: str = Field(
        "",
        description="Additional information from the log line"
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
