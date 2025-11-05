"""
Parser for search progress events.

Example log lines:
    #1       1.52s best:3.15168966e+09 next:[65445416,3.15168966e+09] quick_restart_no_lp (fixed_bools=0/9999)
    #2       1.59s best:2.03193872e+09 next:[65445416,2.03193872e+09] core (fixed_bools=0/10035)
    #Bound   0.73s best:inf   next:[48676021,3.15794931e+11] objective_shaving_search_no_lp (vars=9999 csts=19704)
    #Model   4.63s var:9993/9999 constraints:19691/19703
"""

import re
from typing import List
from ..models import SearchEvent, BoundEvent, ObjectiveEvent, ModelEvent
from .base import ParserComponent
from .utils import parse_time, parse_number


class SearchEventsParser(ParserComponent):
    """
    Parse search progress events (solutions, bounds, model updates).

    Example:
        #1       1.52s best:3.15168966e+09 next:[65445416,3.15168966e+09] quick_restart_no_lp (fixed_bools=0/9999)
        #2       1.59s best:2.03193872e+09 next:[65445416,2.03193872e+09] core (fixed_bools=0/10035)
        #Bound   0.73s best:inf   next:[48676021,3.15794931e+11] objective_shaving_search_no_lp
        #Model   4.63s var:9993/9999 constraints:19691/19703
    """

    field_name = "search_events"
    priority = 41

    def parse(self) -> List[SearchEvent]:
        """
        Parse search progress events.

        Returns:
            List of SearchEvent models (BoundEvent, ObjectiveEvent, ModelEvent)
        """
        events = []

        # Find search section
        in_search = False
        for line in self.lines:
            if re.match(r"Starting\s+(?:search|Search)", line, re.IGNORECASE):
                in_search = True
                continue

            # Stop at statistics sections
            if re.match(
                r"(Search stats|Task timing|SAT stats|LNS stats|Solution repositories|Objective bounds|CpSolverResponse)",
                line,
                re.IGNORECASE,
            ):
                break

            if not in_search:
                continue

            # Parse bound events: #Bound
            if match := re.match(
                r"#Bound\s+([\d.]+[smh])\s+best:(\S+)\s+next:\[(\S+),(\S+)\]\s+(.*)",
                line,
            ):
                time = parse_time(match.group(1))
                best_obj_str = match.group(2)
                best_obj = None if best_obj_str == "inf" else parse_number(best_obj_str)
                lower_bound = parse_number(match.group(3))
                upper_bound = parse_number(match.group(4))
                info = match.group(5).strip()

                # Extract subsolver name
                subsolver = info.split("(")[0].strip() if "(" in info else info.split()[0] if info else ""

                # Determine which bound is active
                if best_obj is None or (lower_bound is not None and best_obj > lower_bound):
                    bound = lower_bound
                else:
                    bound = upper_bound

                events.append(
                    BoundEvent(
                        time=time,
                        best_objective=best_obj,
                        bound=bound,
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        subsolver=subsolver,
                        additional_info=info,
                    )
                )

            # Parse objective events: #1, #2, etc.
            elif match := re.match(
                r"#(\d+)\s+([\d.]+[smh])\s+best:(\S+)\s+next:\[(\S+)?,?(\S+)?\]\s+(.*)",
                line,
            ):
                solution_num = int(match.group(1))
                time = parse_time(match.group(2))
                objective = parse_number(match.group(3))
                # Handle optional bounds
                lower_str = match.group(4)
                upper_str = match.group(5)

                # Sometimes the bounds are like [1,2] and sometimes like []
                lower_bound = None
                upper_bound = None

                if lower_str and lower_str.strip() and lower_str != "inf":
                    # Remove comma if present
                    lower_str = lower_str.rstrip(',')
                    if lower_str:
                        lower_bound = parse_number(lower_str)

                if upper_str and upper_str.strip() and upper_str != "inf":
                    # Remove closing bracket if present
                    upper_str = upper_str.rstrip(']')
                    if upper_str:
                        upper_bound = parse_number(upper_str)

                info = match.group(6).strip()

                # Extract subsolver name
                subsolver = info.split("(")[0].strip() if "(" in info else info.split()[0] if info else ""

                # Determine bound and gap
                if lower_bound is not None and upper_bound is not None:
                    # The "next" range shows where we're searching
                    # For minimization (positive objective), the lower bound is the target
                    # For maximization (negative objective), the upper bound is the target
                    if lower_bound <= objective <= upper_bound:
                        bound = lower_bound if objective >= 0 else upper_bound
                    else:
                        bound = lower_bound if abs(objective - lower_bound) < abs(objective - upper_bound) else upper_bound
                else:
                    bound = lower_bound if lower_bound is not None else (upper_bound if upper_bound is not None else objective)

                gap = None
                if bound is not None and objective != 0:
                    gap = 100 * abs(objective - bound) / max(1, abs(objective))

                events.append(
                    ObjectiveEvent(
                        solution_number=solution_num,
                        time=time,
                        objective=objective,
                        bound=bound,
                        lower_bound=lower_bound,
                        upper_bound=upper_bound,
                        gap_percent=gap,
                        subsolver=subsolver,
                        additional_info=info,
                    )
                )

            # Parse model events: #Model
            elif match := re.match(
                r"#Model\s+([\d.]+[smh])\s+var:(\d+)/(\d+)\s+constraints:(\d+)/(\d+)(.*)",
                line,
            ):
                time = parse_time(match.group(1))
                vars_remaining = int(match.group(2))
                vars_total = int(match.group(3))
                constr_remaining = int(match.group(4))
                constr_total = int(match.group(5))
                info = match.group(6).strip()

                events.append(
                    ModelEvent(
                        time=time,
                        vars_remaining=vars_remaining,
                        vars_total=vars_total,
                        constraints_remaining=constr_remaining,
                        constraints_total=constr_total,
                        additional_info=info,
                    )
                )

        return events
