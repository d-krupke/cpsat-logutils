"""
Parser for the final CpSolverResponse.

Example log lines:
    CpSolverResponse summary:
    status: OPTIMAL
    objective: 91326902
    best_bound: 68751309
    integers: 9939
    booleans: 9999
    conflicts: 0
    branches: 23607
    walltime: 13.017
    usertime: 13.017
"""

import re
from ..models import CPSolverResponse
from .base import ParserComponent
from .utils import parse_number


class ResponseParser(ParserComponent):
    """
    Parse the final CpSolverResponse section.

    Example:
        CpSolverResponse summary:
        status: OPTIMAL
        objective: 91326902
        best_bound: 68751309
        integers: 9939
        booleans: 9999
        conflicts: 0
        branches: 23607
        propagations: 2000795
        integer_propagations: 2016550
        restarts: 19998
        lp_iterations: 0
        walltime: 13.017
        usertime: 13.017
        deterministic_time: 65.5825
        gap_integral: 1167.26
        solution_fingerprint: 0x3f5c435d9453c6d6
    """

    field_name = "response"
    priority = 100

    def parse(self) -> CPSolverResponse:
        """
        Parse the final CpSolverResponse.

        Returns:
            CPSolverResponse model
        """
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
