"""
Extensible, registration-based parser for CP-SAT logs that produces Pydantic models.

This parser uses a component-based architecture where each parser component
is responsible for parsing a specific section of the log. Components can be
registered, replaced, or extended to customize the parser behavior.

Example:
    Basic usage:
        parser = LogParser(log_content)
        parsed_log = parser.parse()

    Using custom registry:
        from cpsat_logutils.parsers import ParserRegistry, ParserComponent

        # Create custom registry
        registry = ParserRegistry()

        # Register custom components
        registry.register(MyCustomParser)

        # Use custom registry
        parser = LogParser(log_content, registry=registry)
        parsed_log = parser.parse()

    Replacing a component:
        from cpsat_logutils.parsers import default_registry, SolverInfoParser

        class MySolverInfoParser(SolverInfoParser):
            def parse(self):
                # Custom parsing logic
                pass

        default_registry.register(MySolverInfoParser)
"""

from typing import List, Union, Optional
from .models import CPSATLog
from .parsers.base import ParserRegistry, default_registry
from .parsers import (
    CommentsParser,
    SolverInfoParser,
    InitialModelParser,
    PresolvedModelParser,
    PresolveLogParser,
    PresolveSummaryParser,
    PreloadingInfoParser,
    SearchInfoParser,
    SearchEventsParser,
    TaskTimingParser,
    SearchStatsParser,
    SATStatsParser,
    LNSStatsParser,
    LSStatsParser,
    LPStatsParser,
    SolutionRepositoriesParser,
    ObjectiveBoundsParser,
    ImprovingBoundsSharedParser,
    ClausesSharedParser,
    ResponseParser,
)

# Register all default components
default_registry.register(CommentsParser)
default_registry.register(SolverInfoParser)
default_registry.register(InitialModelParser)
default_registry.register(PresolvedModelParser)
default_registry.register(PresolveLogParser)
default_registry.register(PresolveSummaryParser)
default_registry.register(PreloadingInfoParser)
default_registry.register(SearchInfoParser)
default_registry.register(SearchEventsParser)
default_registry.register(TaskTimingParser)
default_registry.register(SearchStatsParser)
default_registry.register(SATStatsParser)
default_registry.register(LNSStatsParser)
default_registry.register(LSStatsParser)
default_registry.register(LPStatsParser)
default_registry.register(SolutionRepositoriesParser)
default_registry.register(ObjectiveBoundsParser)
default_registry.register(ImprovingBoundsSharedParser)
default_registry.register(ClausesSharedParser)
default_registry.register(ResponseParser)


class LogParser:
    """
    Extensible parser for CP-SAT logs that produces structured Pydantic models.

    This parser uses a component-based architecture where each section of the log
    is parsed by a dedicated parser component. Components can be customized or
    replaced to extend the parser functionality.
    """

    def __init__(
        self,
        log: Union[str, List[str]],
        registry: Optional[ParserRegistry] = None
    ):
        """
        Initialize the parser with a log string or list of lines.

        Args:
            log: CP-SAT log as a string or list of lines
            registry: Optional custom parser registry. If None, uses default registry.
        """
        if isinstance(log, list):
            self.lines = log
        else:
            self.lines = log.split("\n")

        # Normalize lines
        self.lines = [line.rstrip() for line in self.lines]

        # Use provided registry or default
        self.registry = registry or default_registry

    def parse(self) -> CPSATLog:
        """
        Parse the complete log and return a structured CPSATLog model.

        This method iterates through all registered parser components in priority
        order and collects their parsed results into a CPSATLog model.

        Returns:
            CPSATLog: Structured log data

        Example:
            >>> parser = LogParser(log_content)
            >>> result = parser.parse()
            >>> print(result.solver_info.version)
            '9.8.3296'
        """
        # Dictionary to store parsed results
        parsed_data = {}

        # Get all components sorted by priority
        components = self.registry.get_sorted_components()

        # Parse each component
        for field_name, component_class in components:
            try:
                # Instantiate the component
                component = component_class(self.lines)

                # Parse and store result
                result = component.parse()
                parsed_data[field_name] = result
            except Exception as e:
                # Log error but continue parsing other components
                print(f"Warning: Failed to parse {field_name}: {e}")
                parsed_data[field_name] = None

        # Create and return CPSATLog model
        return CPSATLog(**parsed_data)
