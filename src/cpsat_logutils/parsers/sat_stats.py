"""
Parser for SAT statistics.

Example log lines:
    SAT stats          Constraints  Batches  Trivial  Singles
         'default':        1'234       56       12       89
"""

import re
from typing import List
from ..models import SATStatEntry
from .base import ParserComponent
from .utils import parse_number


class SATStatsParser(ParserComponent):
    """
    Parse SAT statistics for each subsolver.

    Example:
        SAT stats          Constraints  Batches  Trivial  Singles
             'default':        1'234       56       12       89
                'core':          987       34        5       23
    """

    field_name = "sat_stats"
    priority = 52

    def parse(self) -> List[SATStatEntry]:
        """
        Parse SAT statistics.

        Returns:
            List of SATStatEntry models
        """
        entries = []

        # Find SAT stats section
        in_section = False
        header_fields = []
        for line in self.lines:
            if re.match(r"SAT stats", line, re.IGNORECASE):
                in_section = True
                # Extract header fields
                header_fields = re.findall(r"(\w+)", line)[2:]  # Skip "SAT stats"
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

                # Create dict of stats
                stats = {}
                for i, field in enumerate(header_fields):
                    if i < len(values):
                        stats[field] = values[i]

                entries.append(SATStatEntry(subsolver=subsolver, stats=stats))

        return entries
