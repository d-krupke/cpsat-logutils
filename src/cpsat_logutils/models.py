"""
Pydantic models for structured CP-SAT log data.

These models are designed to be clean, JSON-serializable, and easy to use
with frontend applications and data analysis tools.
"""

from typing import Optional, List, Dict, Any, Literal, Union
from pydantic import BaseModel, Field, ConfigDict


class LineReference(BaseModel):
    """Reference to lines in the original log that correspond to a semantic block."""

    model_config = ConfigDict(extra="forbid")

    start_line: int = Field(..., description="Starting line number (0-indexed)")
    end_line: int = Field(..., description="Ending line number (0-indexed, exclusive)")
    section_name: str = Field(..., description="Name of the semantic section")
    field_name: Optional[str] = Field(
        None, description="Field name in CPSATLog model"
    )


class LogMetadata(BaseModel):
    """Metadata about the parsed log, including completeness and line references."""

    model_config = ConfigDict(extra="forbid")

    is_complete: bool = Field(
        ...,
        description="Whether the log appears to be complete (has solver info and response)",
    )
    total_lines: int = Field(..., description="Total number of lines in the log")
    has_solver_info: bool = Field(
        ..., description="Whether solver information was found"
    )
    has_response: bool = Field(
        ..., description="Whether final response was found"
    )
    missing_sections: List[str] = Field(
        default_factory=list,
        description="List of expected sections that appear to be missing",
    )
    line_references: List[LineReference] = Field(
        default_factory=list,
        description="References to line ranges for each parsed section",
    )


class SolverInfo(BaseModel):
    """Information about the CP-SAT solver configuration."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(..., description="CP-SAT solver version (e.g., '9.8.3296')")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Solver parameters"
    )
    num_workers: Optional[int] = Field(
        None, description="Number of parallel workers"
    )


class VariableDomain(BaseModel):
    """Description of a variable domain."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(..., description="Number of variables")
    type: str = Field(
        ..., description="Type (e.g., 'Booleans', 'integer')"
    )
    min_value: Optional[int] = Field(None, description="Minimum value")
    max_value: Optional[int] = Field(None, description="Maximum value")


class ConstraintStats(BaseModel):
    """Statistics about a constraint type."""

    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., description="Constraint type (e.g., 'kLinear1')")
    count: int = Field(..., description="Number of constraints")
    additional_info: Dict[str, Any] = Field(
        default_factory=dict, description="Additional constraint metadata"
    )


class ModelStatistics(BaseModel):
    """Statistics about the model (before or after presolve)."""

    model_config = ConfigDict(extra="forbid")

    is_optimization: bool = Field(..., description="Whether this is an optimization model")
    model_name: str = Field("", description="Model name from the log")
    model_fingerprint: Optional[str] = Field(None, description="Model fingerprint")
    num_variables: Optional[int] = Field(None, description="Total number of variables")
    num_booleans_in_objective: Optional[int] = Field(
        None, description="Number of boolean variables in objective"
    )
    variable_domains: List[VariableDomain] = Field(
        default_factory=list, description="Variable domain information"
    )
    constraints: List[ConstraintStats] = Field(
        default_factory=list, description="Constraint statistics"
    )


class PresolveEntry(BaseModel):
    """A single presolve operation entry."""

    model_config = ConfigDict(extra="forbid")

    wall_time: Optional[float] = Field(None, description="Wall time in seconds")
    deterministic_time: Optional[float] = Field(
        None, description="Deterministic time"
    )
    operation: str = Field(..., description="Presolve operation name")
    details: Dict[str, Any] = Field(
        default_factory=dict, description="Additional operation details"
    )


class PresolveSummary(BaseModel):
    """Summary of presolve transformations."""

    model_config = ConfigDict(extra="forbid")

    affine_relations: int = Field(0, description="Number of affine relations detected")
    rules_applied: Dict[str, int] = Field(
        default_factory=dict, description="Rules applied with counts"
    )
    solved_during_presolve: bool = Field(
        False, description="Whether problem was solved during presolve"
    )


class PreloadingInfo(BaseModel):
    """Information from the preloading phase."""

    model_config = ConfigDict(extra="forbid")

    symmetry_info: Dict[str, Any] = Field(
        default_factory=dict, description="Symmetry detection information"
    )
    encoding_info: Dict[str, Any] = Field(
        default_factory=dict, description="Encoding information"
    )


class SubsolverInfo(BaseModel):
    """Information about subsolvers."""

    model_config = ConfigDict(extra="forbid")

    full_problem: List[str] = Field(
        default_factory=list, description="Full problem subsolvers"
    )
    first_solution: List[str] = Field(
        default_factory=list, description="First solution subsolvers"
    )
    incomplete: List[str] = Field(
        default_factory=list, description="Incomplete/LNS subsolvers"
    )
    helper: List[str] = Field(default_factory=list, description="Helper subsolvers")
    interleaved: List[str] = Field(
        default_factory=list, description="Interleaved subsolvers (older versions)"
    )


class SearchInfo(BaseModel):
    """Information about search configuration."""

    model_config = ConfigDict(extra="forbid")

    start_time: float = Field(..., description="Search start time in seconds")
    num_workers: int = Field(..., description="Number of workers")
    subsolvers: SubsolverInfo = Field(..., description="Subsolver configuration")
    search_type: Literal["parallel", "sequential"] = Field(
        "parallel", description="Type of search"
    )


class BoundEvent(BaseModel):
    """A bound improvement event."""

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["bound"] = "bound"
    time: float = Field(..., description="Time in seconds")
    best_objective: Optional[float] = Field(None, description="Best objective value")
    bound: float = Field(..., description="New bound value")
    lower_bound: Optional[float] = Field(None, description="Lower bound")
    upper_bound: Optional[float] = Field(None, description="Upper bound")
    subsolver: str = Field("", description="Subsolver that found the bound")
    additional_info: str = Field("", description="Additional information")


class ObjectiveEvent(BaseModel):
    """A new solution/objective found event."""

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["objective"] = "objective"
    solution_number: int = Field(..., description="Solution number")
    time: float = Field(..., description="Time in seconds")
    objective: float = Field(..., description="Objective value")
    bound: float = Field(..., description="Current bound")
    lower_bound: Optional[float] = Field(None, description="Lower bound")
    upper_bound: Optional[float] = Field(None, description="Upper bound")
    gap_percent: Optional[float] = Field(None, description="Gap percentage")
    subsolver: str = Field("", description="Subsolver that found the solution")
    additional_info: str = Field("", description="Additional information")


class ModelEvent(BaseModel):
    """A model update event (e.g., variable fixing)."""

    model_config = ConfigDict(extra="forbid")

    event_type: Literal["model"] = "model"
    time: float = Field(..., description="Time in seconds")
    vars_remaining: int = Field(..., description="Remaining variables")
    vars_total: int = Field(..., description="Total variables")
    constraints_remaining: int = Field(..., description="Remaining constraints")
    constraints_total: int = Field(..., description="Total constraints")
    additional_info: str = Field("", description="Additional information")


SearchEvent = Union[BoundEvent, ObjectiveEvent, ModelEvent]


class TaskTimingEntry(BaseModel):
    """Task timing statistics for a subsolver."""

    model_config = ConfigDict(extra="forbid")

    task_name: str = Field(..., description="Task/subsolver name")
    num_runs: Optional[int] = Field(None, description="Number of runs")
    time_spent: Optional[float] = Field(None, description="Time spent")
    deterministic_time: Optional[float] = Field(None, description="Deterministic time")
    additional_stats: Dict[str, Any] = Field(
        default_factory=dict, description="Additional statistics"
    )


class SearchStatEntry(BaseModel):
    """Search statistics for a subsolver."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="Subsolver name")
    booleans: Optional[int] = Field(None, description="Number of booleans")
    conflicts: Optional[int] = Field(None, description="Number of conflicts")
    branches: Optional[int] = Field(None, description="Number of branches")
    restarts: Optional[int] = Field(None, description="Number of restarts")
    bool_propagations: Optional[int] = Field(
        None, description="Boolean propagations"
    )
    integer_propagations: Optional[int] = Field(
        None, description="Integer propagations"
    )


class SATStatEntry(BaseModel):
    """SAT statistics for a subsolver."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="Subsolver name")
    stats: Dict[str, int] = Field(
        default_factory=dict, description="SAT-specific statistics"
    )


class LNSStatEntry(BaseModel):
    """LNS (Large Neighborhood Search) statistics."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="LNS subsolver name")
    num_solutions: Optional[int] = Field(None, description="Number of solutions found")
    improvement_range: Optional[List[int]] = Field(
        None, description="Range of solution improvements [min, max]"
    )


class LSStatEntry(BaseModel):
    """LS (Local Search) statistics."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="LS subsolver name")
    num_solutions: Optional[int] = Field(None, description="Number of solutions found")
    improvement_range: Optional[List[int]] = Field(
        None, description="Range of solution improvements [min, max]"
    )


class LPStatEntry(BaseModel):
    """LP (Linear Programming) statistics."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="LP subsolver name")
    stats: Dict[str, Any] = Field(
        default_factory=dict, description="LP-specific statistics"
    )


class SolutionRepositories(BaseModel):
    """Statistics about solution repositories."""

    model_config = ConfigDict(extra="forbid")

    repositories: Dict[str, Dict[str, int]] = Field(
        default_factory=dict,
        description="Repository statistics (added, queried, ignored, synchro)",
    )


class ObjectiveBoundEntry(BaseModel):
    """Objective bound statistics by subsolver."""

    model_config = ConfigDict(extra="forbid")

    subsolver: str = Field(..., description="Subsolver name")
    num_bounds: int = Field(..., description="Number of bounds found")


class ImprovingBoundsShared(BaseModel):
    """Statistics about improving bounds shared between workers."""

    model_config = ConfigDict(extra="forbid")

    bounds_by_subsolver: Dict[str, int] = Field(
        default_factory=dict, description="Number of bounds shared by each subsolver"
    )


class ClausesShared(BaseModel):
    """Statistics about clauses shared between workers."""

    model_config = ConfigDict(extra="forbid")

    clauses_by_subsolver: Dict[str, int] = Field(
        default_factory=dict, description="Number of clauses shared by each subsolver"
    )


class CPSolverResponse(BaseModel):
    """Final solver response summary."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(..., description="Solver status (e.g., OPTIMAL, FEASIBLE)")
    objective: Optional[float] = Field(None, description="Final objective value")
    best_bound: Optional[float] = Field(None, description="Best bound")
    num_integers: Optional[int] = Field(None, description="Number of integer variables")
    num_booleans: Optional[int] = Field(None, description="Number of boolean variables")
    conflicts: Optional[int] = Field(None, description="Total conflicts")
    branches: Optional[int] = Field(None, description="Total branches")
    propagations: Optional[int] = Field(None, description="Total propagations")
    integer_propagations: Optional[int] = Field(
        None, description="Total integer propagations"
    )
    restarts: Optional[int] = Field(None, description="Total restarts")
    lp_iterations: Optional[int] = Field(None, description="Total LP iterations")
    walltime: Optional[float] = Field(None, description="Wall time in seconds")
    usertime: Optional[float] = Field(None, description="User time in seconds")
    deterministic_time: Optional[float] = Field(
        None, description="Deterministic time"
    )
    gap_integral: Optional[float] = Field(None, description="Gap integral")
    solution_fingerprint: Optional[str] = Field(None, description="Solution fingerprint")
    additional_fields: Dict[str, str] = Field(
        default_factory=dict, description="Additional response fields"
    )


class CPSATLog(BaseModel):
    """Complete parsed CP-SAT log."""

    model_config = ConfigDict(extra="forbid")

    metadata: LogMetadata = Field(..., description="Log metadata including completeness and line references")
    solver_info: SolverInfo = Field(..., description="Solver configuration")
    initial_model: Optional[ModelStatistics] = Field(
        None, description="Initial model statistics"
    )
    presolve_log: List[PresolveEntry] = Field(
        default_factory=list, description="Presolve operations"
    )
    presolve_summary: Optional[PresolveSummary] = Field(
        None, description="Presolve summary"
    )
    presolved_model: Optional[ModelStatistics] = Field(
        None, description="Presolved model statistics"
    )
    preloading_info: Optional[PreloadingInfo] = Field(
        None, description="Preloading information"
    )
    search_info: Optional[SearchInfo] = Field(None, description="Search configuration")
    search_events: List[SearchEvent] = Field(
        default_factory=list, description="Search progress events"
    )
    task_timing: List[TaskTimingEntry] = Field(
        default_factory=list, description="Task timing statistics"
    )
    search_stats: List[SearchStatEntry] = Field(
        default_factory=list, description="Search statistics"
    )
    sat_stats: List[SATStatEntry] = Field(
        default_factory=list, description="SAT statistics"
    )
    lns_stats: List[LNSStatEntry] = Field(
        default_factory=list, description="LNS statistics"
    )
    ls_stats: List[LSStatEntry] = Field(
        default_factory=list, description="Local search statistics"
    )
    lp_stats: List[LPStatEntry] = Field(
        default_factory=list, description="LP statistics"
    )
    solution_repositories: Optional[SolutionRepositories] = Field(
        None, description="Solution repository statistics"
    )
    objective_bounds: List[ObjectiveBoundEntry] = Field(
        default_factory=list, description="Objective bounds by subsolver"
    )
    improving_bounds_shared: Optional[ImprovingBoundsShared] = Field(
        None, description="Improving bounds shared statistics"
    )
    clauses_shared: Optional[ClausesShared] = Field(
        None, description="Clauses shared statistics"
    )
    response: CPSolverResponse = Field(..., description="Final solver response")
    comments: List[str] = Field(
        default_factory=list, description="Comments from the log (// lines)"
    )
