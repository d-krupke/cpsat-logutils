"""
Presolve-related models for CP-SAT logs.

This module contains models representing the presolve phase,
where CP-SAT simplifies and transforms the model before search.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class PresolveEntry(BaseModel):
    """
    A single presolve operation entry from the log.

    During presolve, CP-SAT applies many transformation rules to
    simplify the model. Each entry represents one presolve operation
    with timing information.

    Presolve operations include:
    - DetectDominanceRelations: Finding dominated variables
    - ExpandObjective: Expanding objective function
    - RemoveUnusedVariables: Eliminating unused variables
    - ProbeAndFindEquivalentClauses: Boolean simplification
    - And many more...

    Example:
        >>> for entry in result.presolve_log[:5]:
        ...     print(f"{entry.wall_time:.3f}s: {entry.operation}")
        0.001s: DetectDominanceRelations
        0.002s: ExpandObjective
        0.003s: RemoveUnusedVariables
    """

    model_config = ConfigDict(extra="forbid")

    wall_time: Optional[float] = Field(
        None,
        description=(
            "Wall clock time in seconds when this operation started/completed. "
            "Measured from solver start. Useful for profiling presolve performance."
        ),
        ge=0.0
    )

    deterministic_time: Optional[float] = Field(
        None,
        description=(
            "Deterministic time measure (platform-independent). "
            "Unlike wall time, deterministic time should be reproducible across runs. "
            "Unit is arbitrary but consistent within a solve."
        ),
        ge=0.0
    )

    operation: str = Field(
        ...,
        description=(
            "Name of the presolve operation/rule applied. "
            "Examples: 'DetectDominanceRelations', 'ExpandObjective', "
            "'RemoveUnusedVariables', 'ProbeAndFindEquivalentClauses', etc. "
            "The exact names depend on CP-SAT version."
        ),
        min_length=1
    )

    details: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Additional operation-specific details. "
            "May include transformation statistics, rule parameters, etc. "
            "Content varies by operation type."
        )
    )


class PresolveSummary(BaseModel):
    """
    Summary of all presolve transformations applied.

    After presolve completes, CP-SAT outputs a summary showing:
    - How many affine relations were detected
    - Which rules were applied and how many times
    - Whether the problem was solved during presolve

    Affine relations (e.g., y = 2x + 3) allow CP-SAT to eliminate
    variables and simplify the model structure.

    Example:
        >>> summary = result.presolve_summary
        >>> print(f"Affine relations: {summary.affine_relations}")
        >>> print(f"Solved during presolve: {summary.solved_during_presolve}")
        >>> for rule, count in summary.rules_applied.items():
        ...     print(f"  {rule}: {count}")
    """

    model_config = ConfigDict(extra="forbid")

    affine_relations: int = Field(
        0,
        description=(
            "Number of affine relations detected during presolve. "
            "Affine relations are linear equalities like y = ax + b. "
            "Each relation allows eliminating a variable, simplifying the model. "
            "Higher numbers indicate more model simplification."
        ),
        ge=0
    )

    rules_applied: Dict[str, int] = Field(
        default_factory=dict,
        description=(
            "Dictionary mapping presolve rule names to application counts. "
            "Shows which transformations were most frequently applied. "
            "Example keys: 'presolve: 123 rules applied', 'linear: 45 reductions', etc. "
            "Useful for understanding which presolve techniques were effective."
        )
    )

    solved_during_presolve: bool = Field(
        False,
        description=(
            "Whether the problem was completely solved during presolve. "
            "True: Presolve proved optimality or infeasibility without search. "
            "False: Search phase is needed. "
            "Problems solved during presolve are typically very fast."
        )
    )


class PreloadingInfo(BaseModel):
    """
    Information from the preloading/preprocessing phase.

    Before presolve, CP-SAT may perform initial analysis including:
    - Symmetry detection (finding symmetrical structure)
    - Encoding transformations (converting to internal representation)

    Symmetry breaking can significantly speed up solving by eliminating
    equivalent solutions. The more symmetry detected, the more pruning
    is possible.

    Example:
        >>> info = result.preloading_info
        >>> if info and info.symmetry_info:
        ...     print("Symmetry detected:", info.symmetry_info)
        >>> if info and info.encoding_info:
        ...     print("Encoding info:", info.encoding_info)
    """

    model_config = ConfigDict(extra="forbid")

    symmetry_info: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Information about detected symmetries in the model. "
            "May include: number of symmetry classes, generators, orbits, etc. "
            "Symmetry breaking constraints are automatically added by CP-SAT. "
            "More symmetry usually means faster solving."
        )
    )

    encoding_info: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Information about model encoding transformations. "
            "May include details about how high-level constraints were "
            "converted to CP-SAT's internal representation. "
            "Content varies by CP-SAT version."
        )
    )
