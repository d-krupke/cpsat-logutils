"""
Parser for presolve log entries.

Example log lines:
    Starting presolve at 0.00s
      2.30e-03s  0.00e+00d  [DetectDominanceRelations]
      1.90e-02s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1
      6.69e-05s  0.00e+00d  [ExtractEncodingFromLinear] #potential_supersets=200
    [Symmetry] Graph for symmetry has 20'099 nodes and 49'202 arcs.
    [SAT presolve] num removable Booleans: 0 / 9900
"""

import re
from typing import List
from ..models import PresolveEntry
from .base import ParserComponent
from .utils import parse_number


class PresolveLogParser(ParserComponent):
    """
    Parse presolve operation log entries.

    Example:
        Starting presolve at 0.00s
          2.30e-03s  0.00e+00d  [DetectDominanceRelations]
          1.90e-02s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1
          6.69e-05s  0.00e+00d  [ExtractEncodingFromLinear] #potential_supersets=200
        [Symmetry] Graph for symmetry has 20'099 nodes and 49'202 arcs.
        [Symmetry] Symmetry computation done. time: 0.00169353 dtime: 0.00499563
        [SAT presolve] num removable Booleans: 0 / 9900
        [SAT presolve] num trivial clauses: 0
    """

    field_name = "presolve_log"
    priority = 22

    def parse(self) -> List[PresolveEntry]:
        """
        Parse presolve log entries.

        Returns:
            List of PresolveEntry models
        """
        entries = []

        # Find presolve section
        in_presolve = False
        for line in self.lines:
            if re.match(r"Starting presolve", line, re.IGNORECASE):
                in_presolve = True
                continue
            elif re.match(r"Presolve summary", line, re.IGNORECASE):
                break

            if not in_presolve:
                continue

            # Parse presolve entries like:
            # 2.30e-03s  0.00e+00d  [DetectDominanceRelations]
            if match := re.match(
                r"\s*([\d.]+e[+-]\d+)s\s+([\d.]+e[+-]\d+)d\s+\[([^\]]+)\](.*)",
                line,
            ):
                wall_time = float(match.group(1))
                det_time = float(match.group(2))
                operation = match.group(3)
                details_str = match.group(4).strip()

                # Parse details
                details = {}
                for detail_match in re.finditer(r"#(\w+)=([\d']+)", details_str):
                    key = detail_match.group(1)
                    value = parse_number(detail_match.group(2))
                    details[key] = value

                entries.append(
                    PresolveEntry(
                        wall_time=wall_time,
                        deterministic_time=det_time,
                        operation=operation,
                        details=details,
                    )
                )

            # Handle Symmetry and SAT presolve lines
            elif "[Symmetry]" in line or "[SAT presolve]" in line:
                # Extract operation name
                if match := re.match(r"\[([\w\s]+)\](.*)", line):
                    operation = match.group(1)
                    details_str = match.group(2).strip()
                    entries.append(
                        PresolveEntry(
                            operation=operation,
                            details={"raw": details_str} if details_str else {},
                        )
                    )

        return entries
