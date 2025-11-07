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
from .models import CPSATLog, LogMetadata, LineReference
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
    SolutionsParser,
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
default_registry.register(SolutionsParser)
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
            CPSATLog: Structured log data with metadata including line references

        Example:
            >>> parser = LogParser(log_content)
            >>> result = parser.parse()
            >>> print(result.solver_info.version)
            '9.8.3296'
            >>> print(f"Log is complete: {result.metadata.is_complete}")
            >>> for ref in result.metadata.line_references:
            >>>     print(f"{ref.section_name}: lines {ref.start_line}-{ref.end_line}")
        """
        # Dictionary to store parsed results
        parsed_data = {}

        # List to collect line references from all components
        all_line_references: List[LineReference] = []

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

                # Collect line references from this component
                for start, end in component.get_line_ranges():
                    line_ref = LineReference(
                        start_line=start,
                        end_line=end,
                        section_name=component_class.__name__.replace("Parser", ""),
                        field_name=field_name
                    )
                    all_line_references.append(line_ref)

            except Exception as e:
                # Log error but continue parsing other components
                print(f"Warning: Failed to parse {field_name}: {e}")
                parsed_data[field_name] = None

        # Build metadata
        metadata = self._build_metadata(parsed_data, all_line_references)
        parsed_data["metadata"] = metadata

        # Wrap lists in wrapper models for DataFrame export capability
        from .models.wrappers import (
            SearchEvents,
            PresolveEntries,
            TaskTiming,
            SearchStatistics,
            SATStatistics,
            LNSStatistics,
            LSStatistics,
            LPStatistics,
            ObjectiveBoundsTable,
            VariableDomains,
        )

        # Wrap search_events
        if "search_events" in parsed_data and parsed_data["search_events"] is not None:
            if isinstance(parsed_data["search_events"], list):
                parsed_data["search_events"] = SearchEvents(events=parsed_data["search_events"])

        # Wrap presolve_log
        if "presolve_log" in parsed_data and parsed_data["presolve_log"] is not None:
            if isinstance(parsed_data["presolve_log"], list):
                parsed_data["presolve_log"] = PresolveEntries(entries=parsed_data["presolve_log"])

        # Wrap task_timing
        if "task_timing" in parsed_data and parsed_data["task_timing"] is not None:
            if isinstance(parsed_data["task_timing"], list):
                parsed_data["task_timing"] = TaskTiming(entries=parsed_data["task_timing"])

        # Wrap search_stats
        if "search_stats" in parsed_data and parsed_data["search_stats"] is not None:
            if isinstance(parsed_data["search_stats"], list):
                parsed_data["search_stats"] = SearchStatistics(entries=parsed_data["search_stats"])

        # Wrap sat_stats
        if "sat_stats" in parsed_data and parsed_data["sat_stats"] is not None:
            if isinstance(parsed_data["sat_stats"], list):
                parsed_data["sat_stats"] = SATStatistics(entries=parsed_data["sat_stats"])

        # Wrap lns_stats
        if "lns_stats" in parsed_data and parsed_data["lns_stats"] is not None:
            if isinstance(parsed_data["lns_stats"], list):
                parsed_data["lns_stats"] = LNSStatistics(entries=parsed_data["lns_stats"])

        # Wrap ls_stats
        if "ls_stats" in parsed_data and parsed_data["ls_stats"] is not None:
            if isinstance(parsed_data["ls_stats"], list):
                parsed_data["ls_stats"] = LSStatistics(entries=parsed_data["ls_stats"])

        # Wrap lp_stats
        if "lp_stats" in parsed_data and parsed_data["lp_stats"] is not None:
            if isinstance(parsed_data["lp_stats"], list):
                parsed_data["lp_stats"] = LPStatistics(entries=parsed_data["lp_stats"])

        # Wrap objective_bounds
        if "objective_bounds" in parsed_data and parsed_data["objective_bounds"] is not None:
            if isinstance(parsed_data["objective_bounds"], list):
                parsed_data["objective_bounds"] = ObjectiveBoundsTable(entries=parsed_data["objective_bounds"])

        # Wrap variable_domains in initial_model and presolved_model
        for model_field in ["initial_model", "presolved_model"]:
            if model_field in parsed_data and parsed_data[model_field] is not None:
                model = parsed_data[model_field]
                if hasattr(model, "variable_domains") and isinstance(model.variable_domains, list):
                    model.variable_domains = VariableDomains(domains=model.variable_domains)

        # Create and return CPSATLog model
        return CPSATLog(**parsed_data)

    def _build_metadata(
        self,
        parsed_data: dict,
        line_references: List[LineReference]
    ) -> LogMetadata:
        """
        Build metadata about the parsed log including completeness information.

        Args:
            parsed_data: Dictionary of parsed fields
            line_references: List of line references collected from components

        Returns:
            LogMetadata with completeness and line reference information
        """
        # Check if we have solver info
        solver_info = parsed_data.get("solver_info")
        has_solver_info = (
            solver_info is not None and
            solver_info.version is not None and
            solver_info.version != "unknown"
        )

        # Check if we have response
        response = parsed_data.get("response")
        has_response = (
            response is not None and
            response.status is not None and
            response.status != "UNKNOWN"
        )

        # Determine completeness - log is complete if it has both start and end markers
        is_complete = has_solver_info and has_response

        # Identify missing sections
        missing_sections = []
        if not has_solver_info:
            missing_sections.append("solver_info (log start)")
        if not has_response:
            missing_sections.append("response (log end)")

        # Sort line references by start line
        sorted_refs = sorted(line_references, key=lambda r: r.start_line)

        return LogMetadata(
            is_complete=is_complete,
            total_lines=len(self.lines),
            has_solver_info=has_solver_info,
            has_response=has_response,
            missing_sections=missing_sections,
            line_references=sorted_refs
        )
