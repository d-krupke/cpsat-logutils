"""
Parser for search statistics.

Example log lines:
    Search stats    Bools  Conflicts   Branches  Restarts  BoolPropag  IntegerPropag
        'default':    642    918'873  1'780'404       944  65'749'379     36'871'867
           'core':  9'939    329'488    634'326       326  32'654'215     13'482'079
"""

import re
from typing import List
from ..models import SearchStatEntry
from .base import ParserComponent
from .utils import parse_number


class SearchStatsParser(ParserComponent):
    """
    Parse search statistics for each subsolver.

    Example:
        Search stats    Bools  Conflicts   Branches  Restarts  BoolPropag  IntegerPropag
            'default':    642    918'873  1'780'404       944  65'749'379     36'871'867
               'core':  9'939    329'488    634'326       326  32'654'215     13'482'079
    """

    field_name = "search_stats"
    priority = 51

    def parse(self) -> List[SearchStatEntry]:
        """
        Parse search statistics.

        Returns:
            List of SearchStatEntry models
        """
        entries = []

        # Find search stats section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Search stats\s+Bools", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries
            if match := re.match(r"\s*'([^']+)':\s*([\d']+(?:\s+[\d']+)*)", line):
                subsolver = match.group(1)
                values_str = match.group(2)
                values = [parse_number(v) for v in values_str.split()]

                # Map to fields (order: Bools, Conflicts, Branches, Restarts, BoolPropag, IntegerPropag)
                entries.append(
                    SearchStatEntry(
                        subsolver=subsolver,
                        booleans=values[0] if len(values) > 0 else None,
                        conflicts=values[1] if len(values) > 1 else None,
                        branches=values[2] if len(values) > 2 else None,
                        restarts=values[3] if len(values) > 3 else None,
                        bool_propagations=values[4] if len(values) > 4 else None,
                        integer_propagations=values[5] if len(values) > 5 else None,
                    )
                )

        return entries
