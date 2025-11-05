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
        for line in self.lines:
            if re.match(r"Improving bounds shared\s+Num", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'core':  4'886
            if match := re.match(r"\s*'([^']+)':\s*([\d']+)", line):
                subsolver = match.group(1)
                num_bounds = parse_number(match.group(2))
                bounds_by_subsolver[subsolver] = num_bounds

        if not bounds_by_subsolver:
            return None

        return ImprovingBoundsShared(bounds_by_subsolver=bounds_by_subsolver)
