"""
Parser for LS (Local Search) statistics.

Example log lines:
    LS stats               Improv/Calls
      'violation_ls':              5
"""

import re
from typing import List
from ..models import LSStatEntry
from .base import ParserComponent


class LSStatsParser(ParserComponent):
    """
    Parse Local Search statistics.

    Example:
        LS stats               Improv/Calls
          'violation_ls':              5
          'rnd_var_lns':               3
    """

    field_name = "ls_stats"
    priority = 54

    def parse(self) -> List[LSStatEntry]:
        """
        Parse LS statistics.

        Returns:
            List of LSStatEntry models
        """
        entries = []

        # Find LS stats section
        in_section = False
        section_start = None
        section_end = None
        header_fields = []

        for i, line in enumerate(self.lines):
            if re.match(r"LS stats", line, re.IGNORECASE):
                section_start = i
                in_section = True
                # Extract header fields
                header_fields = re.findall(r"(\w+)", line)[2:]  # Skip "LS stats"
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                section_end = i
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'violation_ls':  133  0  1  205'997  ...
            if match := re.match(r"\s*'([^']+)':\s*([\d']+(?:\s+[\d']+)*)", line):
                subsolver = match.group(1)
                values_str = match.group(2)
                values = [int(v.replace("'", "")) for v in values_str.split()]

                # Create dict of stats
                stats = {}
                for j, field in enumerate(header_fields):
                    if j < len(values):
                        stats[field] = values[j]

                entries.append(LSStatEntry(subsolver=subsolver, stats=stats))
                section_end = i + 1

        # Track the LS stats section
        if section_start is not None and section_end is not None:
            self.track_lines(section_start, section_end)

        return entries
