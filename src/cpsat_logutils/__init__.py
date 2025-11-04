from .parser import LogParser
from .blocks import (
    BoundEvent,
    ObjEvent,
    ModelEvent,
    SearchProgress,
    SolverInfo,
    SolverResponse,
)
from .serialization import (
    log_parser_to_dict,
    log_parser_to_json,
    log_to_dict,
    log_to_json,
)

__all__ = [
    "LogParser",
    # Pydantic models for structured data - easy to serialize to JSON
    "BoundEvent",
    "ObjEvent",
    "ModelEvent",
    "SearchProgress",
    "SolverInfo",
    "SolverResponse",
    # Serialization utilities for JSON export
    "log_parser_to_dict",
    "log_parser_to_json",
    "log_to_dict",
    "log_to_json",
]
