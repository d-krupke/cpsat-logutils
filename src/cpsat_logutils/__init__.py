from .parser import LogParser
from .models import (
    LineReference,
    LogMetadata,
    CPSATLog,
    SolverInfo,
    ModelStatistics,
    VariableDomain,
    ConstraintStats,
    PresolveEntry,
    PresolveSummary,
    PreloadingInfo,
    SearchInfo,
    SubsolverInfo,
    BoundEvent,
    ObjectiveEvent,
    ModelEvent,
    SearchEvent,
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
    CPSolverResponse,
)

# Import capture utilities (only available if ortools is installed)
try:
    from .capture import solve_and_capture, capture_log, SolveResult
    _CAPTURE_AVAILABLE = True
except ImportError:
    _CAPTURE_AVAILABLE = False

__all__ = [
    "LogParser",
    "LineReference",
    "LogMetadata",
    "CPSATLog",
    "SolverInfo",
    "ModelStatistics",
    "VariableDomain",
    "ConstraintStats",
    "PresolveEntry",
    "PresolveSummary",
    "PreloadingInfo",
    "SearchInfo",
    "SubsolverInfo",
    "BoundEvent",
    "ObjectiveEvent",
    "ModelEvent",
    "SearchEvent",
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
    "CPSolverResponse",
]

# Add capture utilities to __all__ if available
if _CAPTURE_AVAILABLE:
    __all__.extend(["solve_and_capture", "capture_log", "SolveResult"])
