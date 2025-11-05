"""
Regex-based parser for CP-SAT logs that produces Pydantic models.

This parser is designed to be robust to variations in log formats,
including spelling errors and extra lines in different CP-SAT versions.
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
from .models import (
    CPSATLog,
    SolverInfo,
    ModelStatistics,
    VariableDomain,
    ConstraintStats,
    PresolveEntry,
    PresolveSummary,
    PreloadingInfo,
    SearchInfo,
    SubsolverInfo,
    BoundEvent,
    ObjectiveEvent,
    ModelEvent,
    SearchEvent,
    TaskTimingEntry,
    SearchStatEntry,
    SATStatEntry,
    LNSStatEntry,
    LSStatEntry,
    LPStatEntry,
    SolutionRepositories,
    ObjectiveBoundEntry,
    ImprovingBoundsShared,
    ClausesShared,
    CPSolverResponse,
)


def parse_time(time_str: str) -> float:
    """Parse time string to seconds."""
    time_str = time_str.strip()
    if match := re.match(r"([\d.]+)s", time_str):
        return float(match.group(1))
    elif match := re.match(r"([\d.]+)m", time_str):
        return float(match.group(1)) * 60
    elif match := re.match(r"([\d.]+)ms", time_str):
        return float(match.group(1)) / 1000
    return 0.0


def parse_number(num_str: str) -> Union[int, float]:
    """Parse number string, handling thousands separators and scientific notation."""
    num_str = num_str.replace("'", "").replace(",", "").strip()
    if num_str.lower() in ["inf", "infinity"]:
        return float("inf")
    if num_str.lower() == "na":
        return None
    try:
        if "." in num_str or "e" in num_str.lower():
            return float(num_str)
        return int(num_str)
    except ValueError:
        return None


def parse_parameters(line: str) -> Dict[str, Any]:
    """Parse the parameters line."""
    params = {}
    if not line.startswith("Parameters:"):
        return params

    # Remove "Parameters: " prefix
    param_str = line[len("Parameters:") :].strip()

    # Handle quoted strings and nested structures
    tokens = re.findall(r'(\w+):\s*("(?:[^"\\]|\\.)*"|\{[^}]*\}|[^\s]+)', param_str)

    for key, value in tokens:
        # Remove quotes if present
        if value.startswith('"') and value.endswith('"'):
            params[key] = value[1:-1]
        elif value == "true":
            params[key] = True
        elif value == "false":
            params[key] = False
        elif value.replace(".", "").replace("-", "").isdigit():
            try:
                params[key] = int(value) if "." not in value else float(value)
            except ValueError:
                params[key] = value
        else:
            params[key] = value

    return params


class LogParser:
    """Parser for CP-SAT logs that produces structured Pydantic models."""

    def __init__(self, log: Union[str, List[str]]):
        """
        Initialize the parser with a log string or list of lines.

        Args:
            log: CP-SAT log as a string or list of lines
        """
        if isinstance(log, list):
            self.lines = log
        else:
            self.lines = log.split("\n")

        # Normalize lines
        self.lines = [line.rstrip() for line in self.lines]

    def parse(self) -> CPSATLog:
        """
        Parse the complete log and return a structured CPSATLog model.

        Returns:
            CPSATLog: Structured log data
        """
        # Extract comments first
        comments = self._extract_comments()

        # Parse each section
        solver_info = self._parse_solver_info()
        initial_model = self._parse_initial_model()
        presolve_log = self._parse_presolve_log()
        presolve_summary = self._parse_presolve_summary()
        presolved_model = self._parse_presolved_model()
        preloading_info = self._parse_preloading_info()
        search_info = self._parse_search_info()
        search_events = self._parse_search_events()
        task_timing = self._parse_task_timing()
        search_stats = self._parse_search_stats()
        sat_stats = self._parse_sat_stats()
        lns_stats = self._parse_lns_stats()
        ls_stats = self._parse_ls_stats()
        lp_stats = self._parse_lp_stats()
        solution_repositories = self._parse_solution_repositories()
        objective_bounds = self._parse_objective_bounds()
        improving_bounds_shared = self._parse_improving_bounds_shared()
        clauses_shared = self._parse_clauses_shared()
        response = self._parse_response()

        return CPSATLog(
            solver_info=solver_info,
            initial_model=initial_model,
            presolve_log=presolve_log,
            presolve_summary=presolve_summary,
            presolved_model=presolved_model,
            preloading_info=preloading_info,
            search_info=search_info,
            search_events=search_events,
            task_timing=task_timing,
            search_stats=search_stats,
            sat_stats=sat_stats,
            lns_stats=lns_stats,
            ls_stats=ls_stats,
            lp_stats=lp_stats,
            solution_repositories=solution_repositories,
            objective_bounds=objective_bounds,
            improving_bounds_shared=improving_bounds_shared,
            clauses_shared=clauses_shared,
            response=response,
            comments=comments,
        )

    def _extract_comments(self) -> List[str]:
        """Extract // comments from the log."""
        comments = []
        for line in self.lines:
            if line.startswith("//"):
                comments.append(line[2:].strip())
        return comments

    def _parse_solver_info(self) -> SolverInfo:
        """Parse solver information."""
        version = None
        parameters = {}
        num_workers = None

        for line in self.lines:
            # Version line
            if match := re.match(r"Starting CP-SAT solver v?([\d.]+)", line, re.IGNORECASE):
                version = match.group(1)

            # Parameters line
            elif line.startswith("Parameters:"):
                parameters = parse_parameters(line)

            # Workers line
            elif match := re.match(r"Setting number of workers to (\d+)", line):
                num_workers = int(match.group(1))

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

    def _parse_model_block(
        self, start_pattern: str
    ) -> Optional[ModelStatistics]:
        """Parse a model statistics block (initial or presolved)."""
        # Find the starting line
        start_idx = None
        for i, line in enumerate(self.lines):
            if re.match(start_pattern, line, re.IGNORECASE):
                start_idx = i
                break

        if start_idx is None:
            return None

        # Determine if optimization or satisfaction
        first_line = self.lines[start_idx]
        is_optimization = "optimization" in first_line.lower()

        # Extract model name and fingerprint
        model_name = ""
        model_fingerprint = None
        if match := re.search(r"model '([^']*)'", first_line):
            model_name = match.group(1)
        if match := re.search(r"model_fingerprint:\s*(0x[\da-fA-F]+)", first_line):
            model_fingerprint = match.group(1)

        # Parse variables and constraints
        num_variables = None
        num_booleans_in_objective = None
        variable_domains = []
        constraints = []

        for i in range(start_idx + 1, len(self.lines)):
            line = self.lines[i]

            # Stop at empty line or next section
            if not line.strip() or re.match(
                r"(Starting presolve|Preloading model|Starting [Ss]earch|Presolve summary)",
                line,
            ):
                break

            # Variables line
            if match := re.match(
                r"#Variables:\s*([\d']+)(?:\s*\(#bools:\s*([\d']+)(?:\s+in objective)?\))?",
                line,
            ):
                num_variables = parse_number(match.group(1))
                if match.group(2):
                    num_booleans_in_objective = parse_number(match.group(2))

            # Variable domain lines
            elif match := re.match(
                r"\s*-\s*([\d']+)\s+(Booleans?|in|constants)\s+(?:in\s+)?[\[{]([^\]}\n]+)[\]}]",
                line,
            ):
                count = parse_number(match.group(1))
                var_type = match.group(2)
                domain_str = match.group(3)

                # Parse domain range
                min_val, max_val = None, None
                if "," in domain_str:
                    # Range like [0,1] or constants like {1,2,3}
                    parts = domain_str.split(",")
                    if len(parts) >= 2:
                        min_val = parse_number(parts[0])
                        max_val = parse_number(parts[-1])

                variable_domains.append(
                    VariableDomain(
                        count=count,
                        type=var_type,
                        min_value=min_val,
                        max_value=max_val,
                    )
                )

            # Constraint lines
            elif match := re.match(r"#(k\w+):\s*([\d']+)(.*)", line):
                constraint_type = match.group(1)
                count = parse_number(match.group(2))
                additional = match.group(3).strip()

                # Parse additional info
                additional_info = {}
                if additional:
                    # Extract key:value or key=value pairs
                    for item_match in re.finditer(
                        r"[#(](\w+)[:\s=]+([\d']+)[),]?", additional
                    ):
                        key = item_match.group(1)
                        value = parse_number(item_match.group(2))
                        additional_info[key] = value

                constraints.append(
                    ConstraintStats(
                        type=constraint_type,
                        count=count,
                        additional_info=additional_info,
                    )
                )

        return ModelStatistics(
            is_optimization=is_optimization,
            model_name=model_name,
            model_fingerprint=model_fingerprint,
            num_variables=num_variables,
            num_booleans_in_objective=num_booleans_in_objective,
            variable_domains=variable_domains,
            constraints=constraints,
        )

    def _parse_initial_model(self) -> Optional[ModelStatistics]:
        """Parse initial model statistics."""
        return self._parse_model_block(r"Initial (optimization|satisfaction) model")

    def _parse_presolved_model(self) -> Optional[ModelStatistics]:
        """Parse presolved model statistics."""
        return self._parse_model_block(r"Presolved (optimization|satisfaction) model")

    def _parse_presolve_log(self) -> List[PresolveEntry]:
        """Parse presolve log entries."""
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

    def _parse_presolve_summary(self) -> Optional[PresolveSummary]:
        """Parse presolve summary."""
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

        for i in range(start_idx + 1, len(self.lines)):
            line = self.lines[i]

            # Stop at empty line or next section
            if not line.strip() or re.match(
                r"(Presolved|Preloading|Starting)", line
            ):
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

        return PresolveSummary(
            affine_relations=affine_relations,
            rules_applied=rules_applied,
            solved_during_presolve=solved_during_presolve,
        )

    def _parse_preloading_info(self) -> Optional[PreloadingInfo]:
        """Parse preloading information."""
        symmetry_info = {}
        encoding_info = {}

        in_preloading = False
        for line in self.lines:
            if "Preloading model" in line:
                in_preloading = True
                continue
            elif re.match(r"Starting", line):
                if in_preloading:
                    break

            if not in_preloading:
                continue

            # Symmetry info
            if "[Symmetry]" in line:
                # Extract symmetry details
                if match := re.search(r"time:\s*([\d.]+)", line):
                    symmetry_info["time"] = float(match.group(1))
                if match := re.search(r"dtime:\s*([\d.]+)", line):
                    symmetry_info["dtime"] = float(match.group(1))
                if match := re.search(r"(\d+)\s+nodes\s+and\s+(\d+)\s+arcs", line):
                    symmetry_info["nodes"] = parse_number(match.group(1))
                    symmetry_info["arcs"] = parse_number(match.group(2))
                if match := re.search(r"#generators:\s*(\d+)", line):
                    symmetry_info["generators"] = parse_number(match.group(1))

            # Encoding info
            elif "[Encoding]" in line or "[EncodingLinearRelaxation]" in line:
                # Store raw encoding info
                if match := re.match(r"\[(\w+)\](.*)", line):
                    key = match.group(1)
                    value = match.group(2).strip()
                    encoding_info[key] = value

        if not symmetry_info and not encoding_info:
            return None

        return PreloadingInfo(
            symmetry_info=symmetry_info, encoding_info=encoding_info
        )

    def _parse_search_info(self) -> Optional[SearchInfo]:
        """Parse search information."""
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

    def _parse_search_events(self) -> List[SearchEvent]:
        """Parse search progress events."""
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

    def _parse_task_timing(self) -> List[TaskTimingEntry]:
        """Parse task timing statistics."""
        entries = []

        # Find task timing section
        in_section = False
        for line in self.lines:
            if re.match(r"Task timing", line, re.IGNORECASE):
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

    def _parse_search_stats(self) -> List[SearchStatEntry]:
        """Parse search statistics."""
        entries = []

        # Find search stats section
        in_section = False
        for line in self.lines:
            if re.match(r"Search stats\s+Bools", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries
            if match := re.match(r"\s*'([^']+)':\s*([\d']+(?:\s+[\d']+)*)", line):
                subsolver = match.group(1)
                values_str = match.group(2)
                values = [parse_number(v) for v in values_str.split()]

                # Map to fields (order: Bools, Conflicts, Branches, Restarts, BoolPropag, IntegerPropag)
                entries.append(
                    SearchStatEntry(
                        subsolver=subsolver,
                        booleans=values[0] if len(values) > 0 else None,
                        conflicts=values[1] if len(values) > 1 else None,
                        branches=values[2] if len(values) > 2 else None,
                        restarts=values[3] if len(values) > 3 else None,
                        bool_propagations=values[4] if len(values) > 4 else None,
                        integer_propagations=values[5] if len(values) > 5 else None,
                    )
                )

        return entries

    def _parse_sat_stats(self) -> List[SATStatEntry]:
        """Parse SAT statistics."""
        entries = []

        # Find SAT stats section
        in_section = False
        header_fields = []
        for line in self.lines:
            if re.match(r"SAT stats", line, re.IGNORECASE):
                in_section = True
                # Extract header fields
                header_fields = re.findall(r"(\w+)", line)[2:]  # Skip "SAT stats"
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries
            if match := re.match(r"\s*'([^']+)':\s*([\d']+(?:\s+[\d']+)*)", line):
                subsolver = match.group(1)
                values_str = match.group(2)
                values = [parse_number(v) for v in values_str.split()]

                # Create dict of stats
                stats = {}
                for i, field in enumerate(header_fields):
                    if i < len(values):
                        stats[field] = values[i]

                entries.append(SATStatEntry(subsolver=subsolver, stats=stats))

        return entries

    def _parse_lns_stats(self) -> List[LNSStatEntry]:
        """Parse LNS statistics."""
        entries = []

        # Find LNS stats section
        in_section = False
        for line in self.lines:
            if re.match(r"LNS stats", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'graph_arc_lns':   13  [16,92]
            if match := re.match(
                r"\s*'([^']+)':\s*(\d+)\s+\[(\d+),(\d+)\]", line
            ):
                subsolver = match.group(1)
                num_solutions = int(match.group(2))
                min_improvement = int(match.group(3))
                max_improvement = int(match.group(4))

                entries.append(
                    LNSStatEntry(
                        subsolver=subsolver,
                        num_solutions=num_solutions,
                        improvement_range=[min_improvement, max_improvement],
                    )
                )

        return entries

    def _parse_ls_stats(self) -> List[LSStatEntry]:
        """Parse LS (Local Search) statistics."""
        entries = []

        # Similar structure to LNS
        # Usually appears as "violation_ls" in search progress

        return entries

    def _parse_lp_stats(self) -> List[LPStatEntry]:
        """Parse LP statistics."""
        entries = []

        # Find LP-related sections
        for line in self.lines:
            if re.match(r"LP stats", line, re.IGNORECASE):
                # Parse LP stats if present
                pass

        return entries

    def _parse_solution_repositories(self) -> Optional[SolutionRepositories]:
        """Parse solution repositories statistics."""
        repositories = {}

        # Find section
        in_section = False
        for line in self.lines:
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

    def _parse_objective_bounds(self) -> List[ObjectiveBoundEntry]:
        """Parse objective bounds statistics."""
        entries = []

        # Find section
        in_section = False
        for line in self.lines:
            if re.match(r"Objective bounds\s+Num", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'max_lp':    6
            if match := re.match(r"\s*'([^']+)':\s*(\d+)", line):
                subsolver = match.group(1)
                num_bounds = int(match.group(2))

                entries.append(
                    ObjectiveBoundEntry(subsolver=subsolver, num_bounds=num_bounds)
                )

        return entries

    def _parse_improving_bounds_shared(self) -> Optional[ImprovingBoundsShared]:
        """Parse improving bounds shared statistics."""
        bounds_by_subsolver = {}

        # Find section
        in_section = False
        for line in self.lines:
            if re.match(r"Improving bounds shared\s+Num", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries like: 'core':  4'886
            if match := re.match(r"\s*'([^']+)':\s*([\d']+)", line):
                subsolver = match.group(1)
                num_bounds = parse_number(match.group(2))
                bounds_by_subsolver[subsolver] = num_bounds

        if not bounds_by_subsolver:
            return None

        return ImprovingBoundsShared(bounds_by_subsolver=bounds_by_subsolver)

    def _parse_clauses_shared(self) -> Optional[ClausesShared]:
        """Parse clauses shared statistics."""
        clauses_by_subsolver = {}

        # Find section
        in_section = False
        for line in self.lines:
            if re.match(r"Clauses shared\s+Num", line, re.IGNORECASE):
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                break

            if not in_section or not line.strip():
                continue

            # Parse entries
            if match := re.match(r"\s*'([^']+)':\s*(\d+)", line):
                subsolver = match.group(1)
                num_clauses = int(match.group(2))
                clauses_by_subsolver[subsolver] = num_clauses

        if not clauses_by_subsolver:
            return None

        return ClausesShared(clauses_by_subsolver=clauses_by_subsolver)

    def _parse_response(self) -> CPSolverResponse:
        """Parse the final CpSolverResponse."""
        # Find response section
        start_idx = None
        for i, line in enumerate(self.lines):
            if re.match(r"CpSolverResponse", line, re.IGNORECASE):
                start_idx = i
                break

        if start_idx is None:
            # Return a minimal response if not found
            return CPSolverResponse(status="UNKNOWN")

        # Parse response fields
        response_data = {}
        for i in range(start_idx + 1, len(self.lines)):
            line = self.lines[i]

            # Stop at empty line
            if not line.strip():
                break

            # Parse key: value lines
            if ":" in line:
                parts = line.split(":", 1)
                key = parts[0].strip()
                value = parts[1].strip()

                # Map common fields
                if key == "status":
                    response_data["status"] = value.split()[0] if value else "UNKNOWN"
                elif key == "objective":
                    obj_val = parse_number(value)
                    response_data["objective"] = obj_val if obj_val != "NA" else None
                elif key == "best_bound":
                    bound_val = parse_number(value)
                    response_data["best_bound"] = bound_val if bound_val != "NA" else None
                elif key == "integers":
                    response_data["num_integers"] = parse_number(value)
                elif key == "booleans":
                    response_data["num_booleans"] = parse_number(value)
                elif key in [
                    "conflicts",
                    "branches",
                    "propagations",
                    "integer_propagations",
                    "restarts",
                    "lp_iterations",
                ]:
                    response_data[key] = parse_number(value)
                elif key == "walltime":
                    response_data["walltime"] = parse_number(value)
                elif key == "usertime":
                    response_data["usertime"] = parse_number(value)
                elif key == "deterministic_time":
                    response_data["deterministic_time"] = parse_number(value)
                elif key == "gap_integral":
                    response_data["gap_integral"] = parse_number(value)
                elif key == "solution_fingerprint":
                    response_data["solution_fingerprint"] = value
                else:
                    if "additional_fields" not in response_data:
                        response_data["additional_fields"] = {}
                    response_data["additional_fields"][key] = value

        # Ensure status is present
        if "status" not in response_data:
            response_data["status"] = "UNKNOWN"

        return CPSolverResponse(**response_data)
