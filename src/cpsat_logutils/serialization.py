"""
Utility functions for serializing parsed log data to JSON and other formats.

These utilities make it easy to export structured Pydantic models to formats
that are consumable by JavaScript frontends and other tools.
"""

import json
from typing import Any, Dict, List, Union
from .parser import LogParser
from .blocks import (
    SearchProgressBlock,
    SolverBlock,
    ResponseBlock,
    SearchProgress,
    SolverInfo,
    SolverResponse,
)


def log_parser_to_dict(parser: LogParser) -> Dict[str, Any]:
    """Convert a LogParser to a dictionary with structured data.

    This extracts the main components (solver info, search progress, response)
    and converts them to Pydantic models, then serializes to dictionaries.

    Args:
        parser: The LogParser instance to convert

    Returns:
        A dictionary containing structured solver information, search progress,
        and solver response (if available)
    """
    result: Dict[str, Any] = {}

    # Extract solver information
    solver_block = parser.get_block_of_type_or_none(SolverBlock)
    if solver_block:
        result["solver_info"] = solver_block.to_model().model_dump()

    # Extract search progress
    search_block = parser.get_block_of_type_or_none(SearchProgressBlock)
    if search_block:
        result["search_progress"] = search_block.to_model().model_dump()

    # Extract solver response
    response_block = parser.get_block_of_type_or_none(ResponseBlock)
    if response_block:
        result["solver_response"] = response_block.to_model().model_dump()

    # Add comments if any
    if parser.comments:
        result["comments"] = parser.comments

    return result


def log_parser_to_json(parser: LogParser, indent: int = 2) -> str:
    """Convert a LogParser to a JSON string.

    This is a convenience function that converts the parser to a dictionary
    and then serializes to JSON.

    Args:
        parser: The LogParser instance to convert
        indent: Number of spaces for JSON indentation (default: 2)

    Returns:
        A JSON string representation of the parsed log data
    """
    data = log_parser_to_dict(parser)
    return json.dumps(data, indent=indent)


def log_to_dict(log: Union[str, List[str]]) -> Dict[str, Any]:
    """Parse a log and convert it to a dictionary with structured data.

    This is a convenience function that creates a LogParser and converts it
    to a dictionary in one step.

    Args:
        log: The log as a string or list of strings

    Returns:
        A dictionary containing structured solver information, search progress,
        and solver response (if available)
    """
    parser = LogParser(log)
    return log_parser_to_dict(parser)


def log_to_json(log: Union[str, List[str]], indent: int = 2) -> str:
    """Parse a log and convert it to a JSON string.

    This is a convenience function that creates a LogParser and converts it
    to JSON in one step.

    Args:
        log: The log as a string or list of strings
        indent: Number of spaces for JSON indentation (default: 2)

    Returns:
        A JSON string representation of the parsed log data
    """
    parser = LogParser(log)
    return log_parser_to_json(parser, indent=indent)
