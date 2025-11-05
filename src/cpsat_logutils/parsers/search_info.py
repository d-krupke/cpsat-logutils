"""
Parser for search configuration information.

Example log lines:
    Starting search at 0.68s with 24 workers.
    15 full problem subsolvers: [core, default_lp, lb_tree_search]
    7 first solution subsolvers: [fj_long_default, fj_short_default]
    10 incomplete subsolvers: [feasibility_pump, graph_arc_lns]
    3 helper subsolvers: [neighborhood_helper, synchronization_agent]
"""

import re
from typing import Optional
from ..models import SearchInfo, SubsolverInfo
from .base import ParserComponent
from .utils import parse_time


class SearchInfoParser(ParserComponent):
    """
    Parse search start information and subsolver configuration.

    Example:
        Starting search at 0.68s with 24 workers.
        15 full problem subsolvers: [core, default_lp, lb_tree_search, max_lp, pseudo_costs, reduced_costs]
        7 first solution subsolvers: [fj_long_default, fj_short_default, fs_random, fs_random_quick_restart]
        10 incomplete subsolvers: [feasibility_pump, graph_arc_lns, graph_cst_lns, graph_dec_lns]
        3 helper subsolvers: [neighborhood_helper, synchronization_agent, update_gap_integral]
    """

    field_name = "search_info"
    priority = 40

    def parse(self) -> Optional[SearchInfo]:
        """
        Parse search information.

        Returns:
            SearchInfo model or None if not found
        """
        # Find search start line
        for i, line in enumerate(self.lines):
            # Handle both "Starting search" and "Starting Search"
            if match := re.match(
                r"Starting\s+(?:search|Search)\s+at\s+([\d.]+s)\s+with\s+(\d+)\s+workers?",
                line,
                re.IGNORECASE,
            ):
                start_time = parse_time(match.group(1))
                num_workers = int(match.group(2))

                # Parse subsolvers from following lines
                subsolvers = SubsolverInfo()
                search_type = "parallel"

                # Check for sequential search
                for j in range(i, min(i + 10, len(self.lines))):
                    if "sequential search" in self.lines[j].lower():
                        search_type = "sequential"
                        break

                # Parse subsolver lines
                for j in range(i + 1, min(i + 10, len(self.lines))):
                    line = self.lines[j]

                    # Full problem subsolvers
                    if match := re.match(
                        r"(\d+)\s+full\s+(?:problem\s+)?subsolvers?:\s*\[([^\]]+)\]",
                        line,
                        re.IGNORECASE,
                    ):
                        subsolvers.full_problem = [
                            s.strip() for s in match.group(2).split(",")
                        ]

                    # First solution subsolvers
                    elif match := re.match(
                        r"(\d+)\s+first\s+solution\s+subsolvers?:\s*\[([^\]]+)\]",
                        line,
                        re.IGNORECASE,
                    ):
                        subsolvers.first_solution = [
                            s.strip() for s in match.group(2).split(",")
                        ]

                    # Incomplete subsolvers
                    elif match := re.match(
                        r"(\d+)\s+incomplete\s+subsolvers?:\s*\[([^\]]+)\]",
                        line,
                        re.IGNORECASE,
                    ):
                        subsolvers.incomplete = [
                            s.strip() for s in match.group(2).split(",")
                        ]

                    # Helper subsolvers
                    elif match := re.match(
                        r"(\d+)\s+helper\s+subsolvers?:\s*\[([^\]]+)\]",
                        line,
                        re.IGNORECASE,
                    ):
                        subsolvers.helper = [
                            s.strip() for s in match.group(2).split(",")
                        ]

                    # Interleaved subsolvers (older versions)
                    elif match := re.match(
                        r"Interleaved\s+subsolvers?:\s*\[([^\]]+)\]",
                        line,
                        re.IGNORECASE,
                    ):
                        subsolvers.interleaved = [
                            s.strip() for s in match.group(1).split(",")
                        ]

                return SearchInfo(
                    start_time=start_time,
                    num_workers=num_workers,
                    subsolvers=subsolvers,
                    search_type=search_type,
                )

        return None
