"""
Parser for task timing statistics.

Example log lines:
    Task timing                   n
                   'core':    223
         'default_lp':    223
    'lb_tree_search':    223
"""

import re
from typing import List
from ..models import TaskTimingEntry
from .base import ParserComponent


class TaskTimingParser(ParserComponent):
    """
    Parse task timing statistics showing how many times each task ran.

    Example:
        Task timing                   n
                       'core':    223
             'default_lp':    223
        'lb_tree_search':    223
              'objective_lb_search_no_lp':     47
    """

    field_name = "task_timing"
    priority = 50

    def parse(self) -> List[TaskTimingEntry]:
        """
        Parse task timing statistics.

        Returns:
            List of TaskTimingEntry models
        """
        entries = []

        # Find task timing section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Task timing", line, re.IGNORECASE):
                section_start = i
                in_section = True
                continue
            elif in_section and (not line.strip() or line[0] not in " '"):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'task_name':  123  [1,99]
            if match := re.match(r"\s*'([^']+)':\s*(\d+)(?:\s+\[([^\]]+)\])?", line):
                task_name = match.group(1)
                num_runs = int(match.group(2))

                entries.append(
                    TaskTimingEntry(task_name=task_name, num_runs=num_runs)
                )

        return entries
