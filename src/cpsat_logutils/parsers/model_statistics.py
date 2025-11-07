"""
Parser for model statistics (initial and presolved models).

Example log lines:
    Initial optimization model '': (model_fingerprint: 0xa2a90169c5e94a12)
    #Variables: 10'000 (#bools: 9'900 in objective)
      - 9'900 Booleans in [0,1]
      - 100 in [0,99]
    #kExactlyOne: 200 (#literals: 19'800)
    #kLinear1: 1
    #kLinear2: 9'801 (#enforced: 9'801)
"""

import re
from typing import Optional
from ..models import ModelStatistics, VariableDomain, ConstraintStats
from .base import ParserComponent
from .utils import parse_number


class ModelStatisticsParser(ParserComponent):
    """
    Parse model statistics for both initial and presolved models.

    Example for Initial Model:
        Initial optimization model '': (model_fingerprint: 0xa2a90169c5e94a12)
        #Variables: 10'000 (#bools: 9'900 in objective)
          - 9'900 Booleans in [0,1]
          - 100 in [0,99]
        #kExactlyOne: 200 (#literals: 19'800)
        #kLinear1: 1
        #kLinear2: 9'801 (#enforced: 9'801)

    Example for Presolved Model:
        Presolved optimization model '': (model_fingerprint: 0x76bff0c14238d173)
        #Variables: 9'999 (#bools: 9'740 in objective)
          - 9'900 Booleans in [0,1]
          - 99 in [1,99]
        #kBoolAnd: 9'702 (#enforced: 9'702) (#literals: 19'404)
    """

    # This component is used for both initial and presolved models
    field_name = None  # Will be set dynamically
    priority = 20

    def __init__(self, lines, start_pattern: str):
        """
        Initialize with a specific pattern to match.

        Args:
            lines: List of log lines
            start_pattern: Regex pattern to identify the start of this model block
        """
        super().__init__(lines)
        self.start_pattern = start_pattern

    def parse(self) -> Optional[ModelStatistics]:
        """
        Parse a model statistics block.

        Returns:
            ModelStatistics model or None if not found
        """
        # Find the starting line
        start_idx = None
        for i, line in enumerate(self.lines):
            if re.match(self.start_pattern, line, re.IGNORECASE):
                start_idx = i
                break

        if start_idx is None:
            return None

        # Determine if optimization or satisfaction
        first_line = self.lines[start_idx]
        is_optimization = "optimization" in first_line.lower()

        # Extract model name and fingerprint
        cpsat_model_name = ""
        cpsat_model_fingerprint = None
        if match := re.search(r"model '([^']*)'", first_line):
            cpsat_model_name = match.group(1)
        if match := re.search(r"model_fingerprint:\s*(0x[\da-fA-F]+)", first_line):
            cpsat_model_fingerprint = match.group(1)

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
                r"\s*-\s*([\d']+)\s+(Booleans?|in|constants)\s+(?:in\s+)?(.+)",
                line,
            ):
                count = parse_number(match.group(1))
                var_type = match.group(2)
                domain_part = match.group(3).strip()

                # Parse domain ranges
                # Format examples:
                # [0,1] → [[0, 1]]
                # [0][10][20] → [[0,0], [10,10], [20,20]]
                # [0,1][34][67][100] → [[0,1], [34,34], [67,67], [100,100]]
                domain_ranges = []
                min_val = None
                max_val = None

                # Extract all bracket contents (handles both [] and {})
                bracket_pattern = r'[\[{]([^\]\}]+)[\]}]'
                for bracket_match in re.finditer(bracket_pattern, domain_part):
                    range_str = bracket_match.group(1)

                    if ',' in range_str:
                        # Continuous range like [0,6]
                        parts = range_str.split(',')
                        if len(parts) >= 2:
                            range_min = parse_number(parts[0])
                            range_max = parse_number(parts[-1])
                            domain_ranges.append([range_min, range_max])

                            # Update overall min/max
                            if min_val is None or range_min < min_val:
                                min_val = range_min
                            if max_val is None or range_max > max_val:
                                max_val = range_max
                    else:
                        # Single value like [10]
                        val = parse_number(range_str)
                        domain_ranges.append([val, val])

                        # Update overall min/max
                        if min_val is None or val < min_val:
                            min_val = val
                        if max_val is None or val > max_val:
                            max_val = val

                variable_domains.append(
                    VariableDomain(
                        count=count,
                        type=var_type,
                        domain_ranges=domain_ranges if domain_ranges else None,
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

        # Track this model block
        self.track_lines(start_idx, i)

        return ModelStatistics(
            is_optimization=is_optimization,
            cpsat_model_name=cpsat_model_name,
            cpsat_model_fingerprint=cpsat_model_fingerprint,
            num_variables=num_variables,
            num_booleans_in_objective=num_booleans_in_objective,
            variable_domains=variable_domains,
            constraints=constraints,
        )


class InitialModelParser(ModelStatisticsParser):
    """Parser for initial model statistics."""

    field_name = "initial_model"
    priority = 21

    def __init__(self, lines):
        super().__init__(lines, r"Initial (optimization|satisfaction) model")


class PresolvedModelParser(ModelStatisticsParser):
    """Parser for presolved model statistics."""

    field_name = "presolved_model"
    priority = 31

    def __init__(self, lines):
        super().__init__(lines, r"Presolved (optimization|satisfaction) model")
