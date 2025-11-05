"""
Parser for LP (Linear Programming) statistics.

Example log lines:
    LP stats               Iterations  AddedCuts
      'max_lp':                  456        12
"""

import re
from typing import List
from ..models import LPStatEntry
from .base import ParserComponent


class LPStatsParser(ParserComponent):
    """
    Parse LP statistics for linear programming solvers.

    Example:
        LP stats               Iterations  AddedCuts
          'max_lp':                  456        12
          'default_lp':              234         8
    """

    field_name = "lp_stats"
    priority = 55

    def parse(self) -> List[LPStatEntry]:
        """
        Parse LP statistics.

        Returns:
            List of LPStatEntry models
        """
        entries = []

        # Find LP-related sections
        section_start = None
        section_end = None
        in_section = False
        header_fields = []

        for i, line in enumerate(self.lines):
            if re.match(r"Lp stats", line, re.IGNORECASE):
                section_start = i
                in_section = True
                # Extract header fields (skip "Lp stats" and "Component")
                header_fields = re.findall(r"(\w+(?:\.\w*)?)", line)[2:]
                continue
            elif in_section:
                # Check if we've left the LP section entirely
                # Stay in section if we see any "Lp " subsection (Lp dimension, Lp debug, Lp pool, etc.)
                if line.strip() and not line.startswith(" ") and not re.match(r"Lp ", line, re.IGNORECASE):
                    section_end = i
                    break
                # Skip subsection headers (Lp dimension, Lp debug, etc.) - they're part of same section
                if re.match(r"Lp ", line, re.IGNORECASE):
                    section_end = i + 1
                    continue

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'subsolver':   3   392'389   863  ...
            if match := re.match(r"\s*'([^']+)':\s*([\d']+(?:\s+[\d']+)*)", line):
                subsolver = match.group(1)
                values_str = match.group(2)
                values = [int(v.replace("'", "")) for v in values_str.split()]

                # Create dict of stats
                stats = {}
                for j, field in enumerate(header_fields):
                    if j < len(values):
                        stats[field] = values[j]

                entries.append(LPStatEntry(subsolver=subsolver, stats=stats))
                section_end = i + 1

        # Track the entire LP stats section (including all Lp subsections)
        if section_start is not None:
            if section_end is None:
                section_end = len(self.lines)
            self.track_lines(section_start, section_end)

        return entries
