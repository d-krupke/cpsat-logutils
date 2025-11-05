"""
Base classes for parser components and the parser registry.

This module provides the foundation for the extensible parser architecture.
"""

from typing import List, Dict, Any, Optional, Type, Callable, Tuple
from abc import ABC, abstractmethod


class ParserComponent(ABC):
    """
    Base class for all parser components.

    Each parser component is responsible for parsing a specific section
    of the CP-SAT log and converting it to structured data.
    """

    # The field name where this component's result will be stored in CPSATLog
    field_name: str = None

    # Optional: Priority for parsing order (lower = earlier)
    priority: int = 100

    def __init__(self, lines: List[str]):
        """
        Initialize the parser component.

        Args:
            lines: List of log lines to parse
        """
        self.lines = lines
        self.line_references: List[Tuple[int, int]] = []  # List of (start, end) line ranges

    def track_lines(self, start: int, end: int) -> None:
        """
        Track a range of lines that were used during parsing.

        Args:
            start: Starting line number (0-indexed)
            end: Ending line number (0-indexed, exclusive)
        """
        self.line_references.append((start, end))

    def get_line_ranges(self) -> List[Tuple[int, int]]:
        """
        Get all line ranges that were used during parsing.

        Returns:
            List of (start, end) tuples representing line ranges
        """
        return self.line_references

    @abstractmethod
    def parse(self) -> Any:
        """
        Parse the log lines and return structured data.

        Components should call track_lines() to record which lines they parse.

        Returns:
            The parsed data structure (model, list, dict, etc.)
        """
        pass

    @classmethod
    def get_example(cls) -> str:
        """
        Get an example of what this parser component handles.

        Returns:
            A string showing example log lines that this parser handles
        """
        return cls.__doc__ or "No example available"


class ParserRegistry:
    """
    Registry for parser components.

    This allows users to register custom parser components or replace
    existing ones to extend or customize the parser behavior.
    """

    def __init__(self):
        self._components: Dict[str, Type[ParserComponent]] = {}

    def register(
        self,
        component_class: Type[ParserComponent],
        field_name: Optional[str] = None
    ) -> None:
        """
        Register a parser component.

        Args:
            component_class: The parser component class to register
            field_name: Optional field name override (uses component's field_name if not provided)
        """
        name = field_name or component_class.field_name
        if name is None:
            raise ValueError(
                f"Parser component {component_class.__name__} must have a field_name"
            )
        self._components[name] = component_class

    def unregister(self, field_name: str) -> None:
        """
        Unregister a parser component.

        Args:
            field_name: The field name of the component to unregister
        """
        if field_name in self._components:
            del self._components[field_name]

    def get(self, field_name: str) -> Optional[Type[ParserComponent]]:
        """
        Get a registered parser component.

        Args:
            field_name: The field name of the component

        Returns:
            The parser component class, or None if not found
        """
        return self._components.get(field_name)

    def get_all(self) -> Dict[str, Type[ParserComponent]]:
        """
        Get all registered parser components.

        Returns:
            Dictionary mapping field names to parser component classes
        """
        return self._components.copy()

    def get_sorted_components(self) -> List[tuple[str, Type[ParserComponent]]]:
        """
        Get all components sorted by priority.

        Returns:
            List of (field_name, component_class) tuples sorted by priority
        """
        return sorted(
            self._components.items(),
            key=lambda x: x[1].priority
        )


# Global registry instance
default_registry = ParserRegistry()
