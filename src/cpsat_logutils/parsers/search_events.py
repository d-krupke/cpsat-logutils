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
                next_min = parse_number(match.group(3))
                next_max = parse_number(match.group(4))
                info = match.group(5).strip()

                # Extract subsolver name
                subsolver = info.split("(")[0].strip() if "(" in info else info.split()[0] if info else ""

                # Detect problem type and extract proven bound
                # If best_obj is close to next_max → minimization (proven_bound = next_min)
                # If best_obj is close to next_min → maximization (proven_bound = next_max)
                # If no solution yet (best_obj = inf/None) → assume minimization
                if best_obj is None or (next_min is not None and next_max is not None and
                                       abs(best_obj - next_max) < abs(best_obj - next_min)):
                    # Minimization: searching in [proven_lower, ~objective]
                    proven_bound = next_min
                else:
                    # Maximization: searching in [~objective, proven_upper]
                    proven_bound = next_max

                events.append(
                    BoundEvent(
                        time=time,
                        best_objective=best_obj,
                        proven_bound=proven_bound,
                        next_min=next_min,
                        next_max=next_max,
                        subsolver=subsolver,
                        additional_info=info,
                    )
                )

            # Parse objective events: #1, #2, etc.
            # Handle both next:[min,max] and next:[] formats
            elif match := re.match(
                r"#(\d+)\s+([\d.]+[smh])\s+best:(\S+)\s+next:\[([^\]]*)\]\s+(.*)",
                line,
            ):
                solution_num = int(match.group(1))
                time = parse_time(match.group(2))
                objective = parse_number(match.group(3))
                bounds_str = match.group(4).strip()  # May be empty or "min,max"

                # Parse next_min and next_max from comma-separated string
                next_min = None
                next_max = None

                if bounds_str:  # Non-empty bounds
                    parts = bounds_str.split(',')
                    if len(parts) >= 1:
                        min_str = parts[0].strip()
                        if min_str and min_str != "inf":
                            next_min = parse_number(min_str)

                    if len(parts) >= 2:
                        max_str = parts[1].strip()
                        if max_str and max_str != "inf":
                            next_max = parse_number(max_str)

                info = match.group(5).strip()

                # Extract subsolver name
                subsolver = info.split("(")[0].strip() if "(" in info else info.split()[0] if info else ""

                # Detect problem type and extract proven bound
                # If next:[] → optimal solution (proven_bound = objective)
                # If objective ≈ next_max → minimization (proven_bound = next_min)
                # If objective ≈ next_min or objective < next_min → maximization (proven_bound = next_max)
                if next_min is None and next_max is None:
                    # next:[] means proven optimal
                    proven_bound = objective
                elif next_min is not None and next_max is not None:
                    # Detect based on which bound is closer to objective
                    distance_to_min = abs(objective - next_min)
                    distance_to_max = abs(objective - next_max)

                    # Also check if objective is below next_min (indicates maximization)
                    if objective < next_min or distance_to_min < distance_to_max:
                        # Objective is close to or below next_min → maximization
                        # proven_bound is next_max (the upper limit)
                        proven_bound = next_max
                    else:
                        # Objective is close to next_max → minimization
                        # proven_bound is next_min (the lower limit)
                        proven_bound = next_min
                elif next_min is not None:
                    # Only next_min present → assume minimization
                    proven_bound = next_min
                else:
                    # Only next_max present → assume maximization
                    proven_bound = next_max

                # Calculate gap percentage
                gap = None
                if proven_bound != objective and objective != 0:
                    gap = 100 * abs(objective - proven_bound) / abs(objective)

                events.append(
                    ObjectiveEvent(
                        solution_number=solution_num,
                        time=time,
                        objective=objective,
                        proven_bound=proven_bound,
                        next_min=next_min,
                        next_max=next_max,
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
