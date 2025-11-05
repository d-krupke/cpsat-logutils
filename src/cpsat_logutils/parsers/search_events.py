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
            # Handle both next:[lower,upper] and next:[] formats
            elif match := re.match(
                r"#(\d+)\s+([\d.]+[smh])\s+best:(\S+)\s+next:\[([^\]]*)\]\s+(.*)",
                line,
            ):
                solution_num = int(match.group(1))
                time = parse_time(match.group(2))
                objective = parse_number(match.group(3))
                bounds_str = match.group(4).strip()  # May be empty or "lower,upper"

                # Parse lower and upper bounds from comma-separated string
                lower_bound = None
                upper_bound = None

                if bounds_str:  # Non-empty bounds
                    parts = bounds_str.split(',')
                    if len(parts) >= 1:
                        lower_str = parts[0].strip()
                        if lower_str and lower_str != "inf":
                            lower_bound = parse_number(lower_str)

                    if len(parts) >= 2:
                        upper_str = parts[1].strip()
                        if upper_str and upper_str != "inf":
                            upper_bound = parse_number(upper_str)

                info = match.group(5).strip()

                # Extract subsolver name
                subsolver = info.split("(")[0].strip() if "(" in info else info.split()[0] if info else ""

                # For minimization: lower_bound is the best known bound
                # For maximization: upper_bound is the best known bound (but represented as negative)
                # In CP-SAT logs, minimization is standard, so we use lower_bound as the bound
                # If next:[] (both bounds are None), use objective as bound (optimal solution)
                if lower_bound is not None:
                    bound = lower_bound
                elif upper_bound is not None:
                    bound = upper_bound
                else:
                    bound = objective  # next:[] means optimal, so objective = bound

                # Calculate gap percentage
                gap = None
                if bound is not None and objective is not None and objective != 0 and bound != objective:
                    gap = 100 * abs(objective - bound) / abs(objective)

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
