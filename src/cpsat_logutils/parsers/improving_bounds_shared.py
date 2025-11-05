"""
Parser for improving bounds shared statistics.

Example log lines:
    Improving bounds shared               Num
                           'core':    4'886
                     'default_lp':      123
"""

import re
from typing import Optional
from ..models import ImprovingBoundsShared
from .base import ParserComponent
from .utils import parse_number


class ImprovingBoundsSharedParser(ParserComponent):
    """
    Parse improving bounds shared between subsolvers.

    Example:
        Improving bounds shared               Num
                               'core':    4'886
                         'default_lp':      123
                     'lb_tree_search':       45
    """

    field_name = "improving_bounds_shared"
    priority = 62

    def parse(self) -> Optional[ImprovingBoundsShared]:
        """
        Parse improving bounds shared statistics.

        Returns:
            ImprovingBoundsShared model or None if not found
        """
        bounds_by_subsolver = {}

        # Find section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Improving bounds shared\s+Num", line, re.IGNORECASE):
                section_start = i
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                section_end = i
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'core':  4'886
            if match := re.match(r"\s*'([^']+)':\s*([\d']+)", line):
                subsolver = match.group(1)
                num_bounds = parse_number(match.group(2))
                bounds_by_subsolver[subsolver] = num_bounds
                section_end = i + 1

        if not bounds_by_subsolver:
            return None

        # Track the improving bounds shared section
        if section_start is not None and section_end is not None:
            self.track_lines(section_start, section_end)

        return ImprovingBoundsShared(bounds_by_subsolver=bounds_by_subsolver)
