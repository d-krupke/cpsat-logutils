"""
Metadata models for CP-SAT log parsing.

This module contains models that provide metadata about the parsed log,
including completeness information and references to line ranges for
each parsed section.
"""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class LineReference(BaseModel):
    """
    Reference to a range of lines in the original log that correspond to a semantic block.

    Line references enable tools to:
    - Highlight specific sections in log viewers
    - Build interactive log exploration tools
    - Map parsed data back to original log lines
    - Explain what each section means

    All line numbers are 0-indexed, following Python convention.

    Example:
        >>> ref = LineReference(
        ...     start_line=0,
        ...     end_line=3,
        ...     section_name="SolverInfo",
        ...     field_name="solver_info"
        ... )
        >>> # Lines 0, 1, 2 contain solver info
        >>> lines = log.split('\\n')[ref.start_line:ref.end_line]
    """

    model_config = ConfigDict(extra="forbid")

    start_line: int = Field(
        ...,
        description="Starting line number (0-indexed, inclusive)",
        ge=0
    )
    end_line: int = Field(
        ...,
        description="Ending line number (0-indexed, exclusive)",
        ge=0
    )
    section_name: str = Field(
        ...,
        description="Human-readable name of the semantic section (e.g., 'SolverInfo', 'Response')",
        min_length=1
    )
    field_name: Optional[str] = Field(
        None,
        description="Corresponding field name in the CPSATLog model (e.g., 'solver_info', 'response')"
    )


class LogMetadata(BaseModel):
    """
    Metadata about the parsed CP-SAT log.

    Provides information about:
    - Log completeness (whether it has start and end markers)
    - Missing sections that would normally be expected
    - Line references mapping parsed sections back to original lines
    - Basic statistics about the log

    A log is considered **complete** if it contains both:
    1. Solver information at the start (indicating solver version)
    2. CpSolverResponse at the end (indicating the solver finished)

    Incomplete logs might result from:
    - Solver still running (log captured mid-execution)
    - Solver crashed or was interrupted
    - Log file truncated or corrupted
    - Log output redirected incorrectly

    Example:
        >>> metadata = result.metadata
        >>> if not metadata.is_complete:
        ...     print(f"Warning: Incomplete log!")
        ...     print(f"Missing: {metadata.missing_sections}")
        ...
        >>> # Find where presolve section is in the log
        >>> presolve_refs = [r for r in metadata.line_references
        ...                  if 'presolve' in r.section_name.lower()]
    """

    model_config = ConfigDict(extra="forbid")

    is_complete: bool = Field(
        ...,
        description=(
            "Whether the log appears to be complete. "
            "True if both solver_info (log start) and response (log end) are present. "
            "False indicates the log may be truncated, from a still-running solver, "
            "or missing critical sections."
        )
    )

    total_lines: int = Field(
        ...,
        description="Total number of lines in the original log",
        ge=0
    )

    has_solver_info: bool = Field(
        ...,
        description=(
            "Whether solver information was found at the log start. "
            "This includes the solver version line (e.g., 'Starting CP-SAT solver v9.8.3296'). "
            "Missing solver info typically indicates a truncated log or incorrect log capture."
        )
    )

    has_response: bool = Field(
        ...,
        description=(
            "Whether the final CpSolverResponse section was found at the log end. "
            "Missing response typically indicates the solver is still running, "
            "was interrupted, or crashed before completion."
        )
    )

    missing_sections: List[str] = Field(
        default_factory=list,
        description=(
            "List of expected sections that appear to be missing from the log. "
            "Common missing sections: 'solver_info (log start)', 'response (log end)'. "
            "This helps users understand why a log might be incomplete."
        )
    )

    line_references: List[LineReference] = Field(
        default_factory=list,
        description=(
            "References to line ranges for each parsed section, sorted by start_line. "
            "Each reference maps a semantic block (like 'SolverInfo' or 'Response') "
            "back to the original line numbers in the log. "
            "Useful for building interactive log viewers and explanation tools."
        )
    )
