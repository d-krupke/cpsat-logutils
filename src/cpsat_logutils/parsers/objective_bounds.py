"""
Parser for objective bounds statistics.

Example log lines:
    Objective bounds                      Num
                     'am1_presolve':    1
                   'initial_domain':    1
                           'max_lp':    6
"""

import re
from typing import List
from ..models import ObjectiveBoundEntry
from .base import ParserComponent


class ObjectiveBoundsParser(ParserComponent):
    """
    Parse objective bounds statistics showing which subsolvers improved bounds.

    Example:
        Objective bounds                      Num
                         'am1_presolve':    1
                       'initial_domain':    1
                               'max_lp':    6
                           'reduced_costs':    3
    """

    field_name = "objective_bounds"
    priority = 61

    def parse(self) -> List[ObjectiveBoundEntry]:
        """
        Parse objective bounds statistics.

        Returns:
            List of ObjectiveBoundEntry models
        """
        entries = []

        # Find section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Objective bounds\s+Num", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'max_lp':    6
            if match := re.match(r"\s*'([^']+)':\s*(\d+)", line):
                subsolver = match.group(1)
                num_bounds = int(match.group(2))

                entries.append(
                    ObjectiveBoundEntry(subsolver=subsolver, num_bounds=num_bounds)
                )

        return entries
