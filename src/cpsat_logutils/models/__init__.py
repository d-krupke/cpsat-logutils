"""
Pydantic models for structured CP-SAT log data.

This package provides type-safe, well-documented models for all components
of CP-SAT logs. All models support JSON serialization via Pydantic.

Main imports:
    - CPSATLog: The top-level log container
    - LogParser: Use this to parse logs (from cpsat_logutils.parser)

Example:
    >>> from cpsat_logutils import LogParser
    >>> parser = LogParser(log_text)
    >>> log = parser.parse()  # Returns CPSATLog
    >>> print(log.response.status)
"""

# Metadata models
from .metadata import (
    LineReference,
    LogMetadata,
)

# Solver and model statistics
from .solver import (
    SolverInfo,
    VariableDomain,
    ConstraintStats,
    ModelStatistics,
)

# Presolve models
from .presolve import (
    PresolveEntry,
    PresolveSummary,
    PreloadingInfo,
)

# Search models
from .search import (
    SubsolverInfo,
    SearchInfo,
    BoundEvent,
    ObjectiveEvent,
    ModelEvent,
    SearchEvent,
)

# Statistics models
from .statistics import (
    TaskTimingEntry,
    SearchStatEntry,
    SATStatEntry,
    LNSStatEntry,
    LSStatEntry,
    LPStatEntry,
    SolutionRepositories,
    ObjectiveBoundEntry,
    ImprovingBoundsShared,
    ClausesShared,
)

# Response model
from .response import (
    CPSolverResponse,
)

# Main log model
from .log import (
    CPSATLog,
)

__all__ = [
    # Metadata
    "LineReference",
    "LogMetadata",
    # Solver
    "SolverInfo",
    "VariableDomain",
    "ConstraintStats",
    "ModelStatistics",
    # Presolve
    "PresolveEntry",
    "PresolveSummary",
    "PreloadingInfo",
    # Search
    "SubsolverInfo",
    "SearchInfo",
    "BoundEvent",
    "ObjectiveEvent",
    "ModelEvent",
    "SearchEvent",
    # Statistics
    "TaskTimingEntry",
    "SearchStatEntry",
    "SATStatEntry",
    "LNSStatEntry",
    "LSStatEntry",
    "LPStatEntry",
    "SolutionRepositories",
    "ObjectiveBoundEntry",
    "ImprovingBoundsShared",
    "ClausesShared",
    # Response
    "CPSolverResponse",
    # Main log
    "CPSATLog",
]
