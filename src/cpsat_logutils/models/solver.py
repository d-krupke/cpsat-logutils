"""
Solver and model statistics models for CP-SAT logs.

This module contains models representing:
- Solver configuration and parameters
- Model structure (variables, constraints, domains)
- Statistics about the model before and after presolve
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SolverInfo(BaseModel):
    """
    Information about the CP-SAT solver configuration.

    Contains the solver version, parameters used, and parallelization settings.
    This information appears at the beginning of the log.

    The solver version helps determine which features are available and
    expected log format. Parameters show which solver settings were used.

    Example:
        >>> solver_info = result.solver_info
        >>> print(f"CP-SAT v{solver_info.version}")
        >>> if solver_info.num_workers:
        ...     print(f"Using {solver_info.num_workers} workers")
        >>> if 'max_time_in_seconds' in solver_info.parameters:
        ...     print(f"Time limit: {solver_info.parameters['max_time_in_seconds']}s")
    """

    model_config = ConfigDict(extra="forbid")

    version: str = Field(
        ...,
        description=(
            "CP-SAT solver version string (e.g., '9.8.3296', '9.10.4010'). "
            "Version numbers follow OR-Tools versioning: major.minor.patch. "
            "Set to 'unknown' if version cannot be determined from the log."
        ),
        min_length=1
    )

    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Solver parameters as key-value pairs. "
            "Common parameters: 'max_time_in_seconds', 'log_search_progress', "
            "'num_search_workers', 'relative_gap_limit', etc. "
            "Values can be integers, floats, booleans, or strings depending on the parameter."
        )
    )

    num_workers: Optional[int] = Field(
        None,
        description=(
            "Number of parallel search workers used by the solver. "
            "Typically determined by available CPU cores. "
            "More workers enable parallel search but use more memory. "
            "None if not specified in the log."
        ),
        ge=1
    )


class VariableDomain(BaseModel):
    """
    Description of a variable domain (range of possible values).

    CP-SAT groups variables by their domain types and ranges.
    This helps understand the model structure and complexity.

    Domain types include:
    - 'Booleans': Variables in {0, 1}
    - 'Integers': Variables with integer domains
    - 'Constants': Fixed variables

    Example:
        >>> for domain in result.initial_model.variable_domains:
        ...     print(f"{domain.count} {domain.type} in [{domain.min_value}, {domain.max_value}]")
        10 Booleans in [0, 1]
        5 integers in [0, 100]
    """

    model_config = ConfigDict(extra="forbid")

    count: int = Field(
        ...,
        description="Number of variables with this domain type",
        ge=0
    )

    type: str = Field(
        ...,
        description=(
            "Domain type description. "
            "Common types: 'Booleans', 'integers in [min..max]', 'constants'. "
            "The exact format depends on CP-SAT version."
        ),
        min_length=1
    )

    min_value: Optional[int] = Field(
        None,
        description="Minimum value in the domain (None if unbounded or not applicable)"
    )

    max_value: Optional[int] = Field(
        None,
        description="Maximum value in the domain (None if unbounded or not applicable)"
    )


class ConstraintStats(BaseModel):
    """
    Statistics about a specific constraint type in the model.

    CP-SAT uses many different constraint types internally.
    These statistics help understand model complexity and structure.

    Common constraint types:
    - kLinear1, kLinear2, kLinear3: Linear constraints
    - kBoolOr, kBoolAnd: Boolean logic constraints
    - kIntMax, kIntMin: Min/max constraints
    - kNoOverlap, kCumulative: Scheduling constraints
    - kAllDiff: All-different constraints

    Example:
        >>> for constraint in result.initial_model.constraints:
        ...     print(f"{constraint.count}x {constraint.type}")
        150x kLinear1
        20x kBoolOr
    """

    model_config = ConfigDict(extra="forbid")

    type: str = Field(
        ...,
        description=(
            "Internal constraint type name from CP-SAT. "
            "Types typically start with 'k' (e.g., 'kLinear1', 'kNoOverlap'). "
            "The exact types depend on how the model was built and CP-SAT's internal representation."
        ),
        min_length=1
    )

    count: int = Field(
        ...,
        description="Number of constraints of this type in the model",
        ge=0
    )

    additional_info: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional constraint-specific information. "
            "May include: 'expressions' (number of sub-expressions), "
            "'intervals' (for scheduling constraints), "
            "'literals' (for boolean constraints), etc."
        )
    )


class ModelStatistics(BaseModel):
    """
    Comprehensive statistics about the CP-SAT model structure.

    Describes the model either before presolve (initial model) or
    after presolve (presolved model). Presolve often significantly
    reduces model size by eliminating redundant variables and constraints.

    The model statistics include:
    - Whether it's an optimization or satisfaction problem
    - Number and types of variables
    - Number and types of constraints
    - Optional model metadata (name, fingerprint)

    Comparing initial vs presolved model shows presolve effectiveness:
        >>> initial = result.initial_model
        >>> presolved = result.presolved_model
        >>> if presolved:
        ...     reduction = (1 - presolved.num_variables / initial.num_variables) * 100
        ...     print(f"Presolve reduced variables by {reduction:.1f}%")

    Example:
        >>> model = result.initial_model
        >>> print(f"Model: {model.model_name}")
        >>> print(f"Type: {'Optimization' if model.is_optimization else 'Satisfaction'}")
        >>> print(f"Variables: {model.num_variables}")
        >>> print(f"Constraints: {sum(c.count for c in model.constraints)}")
    """

    model_config = ConfigDict(extra="forbid")

    is_optimization: bool = Field(
        ...,
        description=(
            "Whether this is an optimization model (has an objective function). "
            "True: Model has Minimize() or Maximize() objective. "
            "False: Satisfaction problem (just finding feasible solutions)."
        )
    )

    model_name: str = Field(
        "",
        description=(
            "Model name as it appears in the log. "
            "Often empty string if no name was specified. "
            "Can be useful for identifying which model produced a log in batch scenarios."
        )
    )

    model_fingerprint: Optional[str] = Field(
        None,
        description=(
            "Unique fingerprint/hash of the model structure. "
            "Format: hex string (e.g., '0x5d458082d52af80f'). "
            "Useful for detecting if models are identical or have changed."
        )
    )

    num_variables: Optional[int] = Field(
        None,
        description=(
            "Total number of variables in the model. "
            "Includes decision variables and auxiliary variables created during modeling. "
            "After presolve, this is often significantly reduced."
        ),
        ge=0
    )

    num_booleans_in_objective: Optional[int] = Field(
        None,
        description=(
            "Number of boolean variables that appear in the objective function. "
            "Only relevant for optimization models. "
            "High values may indicate the objective is complex or involves many choices."
        ),
        ge=0
    )

    variable_domains: List[VariableDomain] = Field(
        default_factory=list,
        description=(
            "List of variable domain groups. "
            "Each entry describes how many variables have a particular domain type. "
            "Helps understand the variable structure of the model."
        )
    )

    constraints: List[ConstraintStats] = Field(
        default_factory=list,
        description=(
            "List of constraint type statistics. "
            "Each entry shows how many constraints of a particular type exist. "
            "The total number of constraints is sum(c.count for c in constraints)."
        )
    )
