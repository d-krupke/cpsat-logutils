"""
Parser for solution repositories statistics.

Example log lines:
    Solution repositories    Added  Queried  Ignored  Synchro
      'feasible solutions':    222      731        0      209
            'lp solutions':     42        0        0       37
"""

import re
from typing import Optional
from ..models import SolutionRepositories
from .base import ParserComponent
from .utils import parse_number


class SolutionRepositoriesParser(ParserComponent):
    """
    Parse solution repositories statistics.

    Example:
        Solution repositories    Added  Queried  Ignored  Synchro
          'feasible solutions':    222      731        0      209
                'lp solutions':     42        0        0       37
    """

    field_name = "solution_repositories"
    priority = 60

    def parse(self) -> Optional[SolutionRepositories]:
        """
        Parse solution repositories statistics.

        Returns:
            SolutionRepositories model or None if not found
        """
        repositories = {}

        # Find section
        in_section = False
        section_start = None

        section_end = None

        for i, line in enumerate(self.lines):
            if re.match(r"Solution repositories\s+Added", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'feasible solutions':    222      731        0      209
            if match := re.match(
                r"\s*'([^']+)':\s*([\d']+)\s+([\d']+)\s+([\d']+)(?:\s+([\d']+))?",
                line,
            ):
                repo_name = match.group(1)
                added = parse_number(match.group(2))
                queried = parse_number(match.group(3))
                ignored = parse_number(match.group(4))
                synchro = parse_number(match.group(5)) if match.group(5) else None

                repositories[repo_name] = {
                    "added": added,
                    "queried": queried,
                    "ignored": ignored,
                }
                if synchro is not None:
                    repositories[repo_name]["synchro"] = synchro

        if not repositories:
            return None

        return SolutionRepositories(repositories=repositories)
