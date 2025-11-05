"""
Parser for clauses shared statistics.

Example log lines:
    Clauses shared                        Num
                           'core':    1'234
                     'default_lp':       56
"""

import re
from typing import Optional
from ..models import ClausesShared
from .base import ParserComponent


class ClausesSharedParser(ParserComponent):
    """
    Parse clauses shared between subsolvers.

    Example:
        Clauses shared                        Num
                               'core':    1'234
                         'default_lp':       56
                     'lb_tree_search':       12
    """

    field_name = "clauses_shared"
    priority = 63

    def parse(self) -> Optional[ClausesShared]:
        """
        Parse clauses shared statistics.

        Returns:
            ClausesShared model or None if not found
        """
        clauses_by_subsolver = {}

        # Find section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Clauses shared\s+Num", line, re.IGNORECASE):
                section_start = i
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                section_end = i
                break

            if not in_section or not line.strip():
                continue

            # Parse entries
            if match := re.match(r"\s*'([^']+)':\s*(\d+)", line):
                subsolver = match.group(1)
                num_clauses = int(match.group(2))
                clauses_by_subsolver[subsolver] = num_clauses
                section_end = i + 1

        if not clauses_by_subsolver:
            return None

        # Track the clauses shared section
        if section_start is not None and section_end is not None:
            self.track_lines(section_start, section_end)

        return ClausesShared(clauses_by_subsolver=clauses_by_subsolver)
