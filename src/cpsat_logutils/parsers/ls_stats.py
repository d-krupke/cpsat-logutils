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

        # Similar structure to LNS
        # Usually appears as "violation_ls" in search progress

        return entries
