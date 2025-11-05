"""
Parser for LNS (Large Neighborhood Search) statistics.

Example log lines:
    LNS stats              Improv/Calls  Closed  Difficulty  TimeLimit
      'graph_arc_lns':              13 [16,92]
      'graph_cst_lns':               7 [24,88]
"""

import re
from typing import List
from ..models import LNSStatEntry
from .base import ParserComponent


class LNSStatsParser(ParserComponent):
    """
    Parse LNS statistics showing improvements and difficulty ranges.

    Example:
        LNS stats              Improv/Calls  Closed  Difficulty  TimeLimit
          'graph_arc_lns':              13 [16,92]
          'graph_cst_lns':               7 [24,88]
          'rins_lns':                    2 [10,45]
    """

    field_name = "lns_stats"
    priority = 53

    def parse(self) -> List[LNSStatEntry]:
        """
        Parse LNS statistics.

        Returns:
            List of LNSStatEntry models
        """
        entries = []

        # Find LNS stats section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"LNS stats", line, re.IGNORECASE):
                section_start = i
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'graph_arc_lns':   13  [16,92]
            if match := re.match(
                r"\s*'([^']+)':\s*(\d+)\s+\[(\d+),(\d+)\]", line
            ):
                subsolver = match.group(1)
                num_solutions = int(match.group(2))
                min_improvement = int(match.group(3))
                max_improvement = int(match.group(4))

                entries.append(
                    LNSStatEntry(
                        subsolver=subsolver,
                        num_solutions=num_solutions,
                        improvement_range=[min_improvement, max_improvement],
                    )
                )

        return entries
