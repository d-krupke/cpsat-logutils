"""
Parser for presolve summary section.

Example log lines:
    Presolve summary:
      - 0 affine relations were detected.
      - rule 'deductions: 19503 stored' was applied 1 time.
      - rule 'exactly_one: simplified objective' was applied 136 times.
      - rule 'linear: empty' was applied 1 time.
"""

import re
from typing import Optional
from ..models import PresolveSummary
from .base import ParserComponent
from .utils import parse_number


class PresolveSummaryParser(ParserComponent):
    """
    Parse presolve summary with affine relations and rules applied.

    Example:
        Presolve summary:
          - 0 affine relations were detected.
          - rule 'deductions: 19503 stored' was applied 1 time.
          - rule 'exactly_one: simplified objective' was applied 136 times.
          - rule 'incompatible linear: add implication' was applied 14'553 times.
          - rule 'linear: empty' was applied 1 time.
    """

    field_name = "presolve_summary"
    priority = 30

    def parse(self) -> Optional[PresolveSummary]:
        """
        Parse presolve summary.

        Returns:
            PresolveSummary model or None if not found
        """
        # Find summary section
        start_idx = None
        for i, line in enumerate(self.lines):
            if re.match(r"Presolve summary:", line, re.IGNORECASE):
                start_idx = i
                break

        if start_idx is None:
            return None

        affine_relations = 0
        rules_applied = {}
        solved_during_presolve = False
        end_idx = start_idx + 1

        for i in range(start_idx + 1, len(self.lines)):
            line = self.lines[i]

            # Stop at empty line or next section
            if not line.strip() or re.match(
                r"(Presolved|Preloading|Starting)", line
            ):
                end_idx = i
                break

            # Affine relations
            if match := re.match(r"\s*-\s*([\d']+)\s+affine relations", line):
                affine_relations = parse_number(match.group(1))

            # Rules applied
            elif match := re.match(
                r"\s*-\s*rule\s+'([^']+)'\s+was applied\s+([\d']+)\s+times?", line
            ):
                rule_name = match.group(1)
                count = parse_number(match.group(2))
                rules_applied[rule_name] = count

            # Check for solved during presolve
            elif "Problem closed by presolve" in line or "solved by presolve" in line.lower():
                solved_during_presolve = True

            end_idx = i + 1

        # Track the presolve summary section
        self.track_lines(start_idx, end_idx)

        return PresolveSummary(
            affine_relations=affine_relations,
            rules_applied=rules_applied,
            solved_during_presolve=solved_during_presolve,
        )
