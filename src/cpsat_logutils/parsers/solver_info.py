"""
Parser for CP-SAT solver information.

Example log lines:
    Starting CP-SAT solver v9.8.3296
    Parameters: max_time_in_seconds: 90 log_search_progress: true
    Setting number of workers to 24
"""

import re
from ..models import SolverInfo
from .base import ParserComponent
from .utils import parse_parameters


class SolverInfoParser(ParserComponent):
    """
    Parse solver version, parameters, and worker configuration.

    Example:
        Starting CP-SAT solver v9.8.3296
        Parameters: max_time_in_seconds: 90 log_search_progress: true relative_gap_limit: 0.25
        Setting number of workers to 24
    """

    field_name = "solver_info"
    priority = 10

    def parse(self) -> SolverInfo:
        """
        Parse solver information from log lines.

        Returns:
            SolverInfo model with version, parameters, and worker count
        """
        version = None
        parameters = {}
        num_workers = None

        for i, line in enumerate(self.lines):
            # Version line
            if match := re.match(r"Starting CP-SAT solver v?([\d.]+)", line, re.IGNORECASE):
                version = match.group(1)
                self.track_lines(i, i + 1)

            # Parameters line
            elif line.startswith("Parameters:"):
                parameters = parse_parameters(line)
                self.track_lines(i, i + 1)

            # Workers line
            elif match := re.match(r"Setting number of workers to (\d+)", line):
                num_workers = int(match.group(1))
                self.track_lines(i, i + 1)

        # Extract num_workers from parameters if not in separate line
        if num_workers is None and "num_workers" in parameters:
            num_workers = parameters.get("num_workers")
        elif num_workers is None and "num_search_workers" in parameters:
            num_workers = parameters.get("num_search_workers")

        if version is None:
            version = "unknown"

        return SolverInfo(
            version=version, parameters=parameters, num_workers=num_workers
        )
