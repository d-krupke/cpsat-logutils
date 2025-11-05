"""
Parser components for CP-SAT log parsing.

This module provides a registration-based architecture for extending
the log parser with new components.
"""

from .base import ParserComponent, ParserRegistry
from .solver_info import SolverInfoParser
from .model_statistics import ModelStatisticsParser, InitialModelParser, PresolvedModelParser
from .presolve_log import PresolveLogParser
from .presolve_summary import PresolveSummaryParser
from .preloading_info import PreloadingInfoParser
from .search_info import SearchInfoParser
from .search_events import SearchEventsParser
from .task_timing import TaskTimingParser
from .search_stats import SearchStatsParser
from .sat_stats import SATStatsParser
from .lns_stats import LNSStatsParser
from .ls_stats import LSStatsParser
from .lp_stats import LPStatsParser
from .solution_repositories import SolutionRepositoriesParser
from .objective_bounds import ObjectiveBoundsParser
from .improving_bounds_shared import ImprovingBoundsSharedParser
from .clauses_shared import ClausesSharedParser
from .response import ResponseParser
from .comments import CommentsParser

__all__ = [
    "ParserComponent",
    "ParserRegistry",
    "SolverInfoParser",
    "ModelStatisticsParser",
    "InitialModelParser",
    "PresolvedModelParser",
    "PresolveLogParser",
    "PresolveSummaryParser",
    "PreloadingInfoParser",
    "SearchInfoParser",
    "SearchEventsParser",
    "TaskTimingParser",
    "SearchStatsParser",
    "SATStatsParser",
    "LNSStatsParser",
    "LSStatsParser",
    "LPStatsParser",
    "SolutionRepositoriesParser",
    "ObjectiveBoundsParser",
    "ImprovingBoundsSharedParser",
    "ClausesSharedParser",
    "ResponseParser",
    "CommentsParser",
]
