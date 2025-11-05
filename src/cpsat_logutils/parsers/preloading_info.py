"""
Parser for preloading information.

Example log lines:
    Preloading model.
    [Symmetry] Graph for symmetry has 39'503 nodes and 78'308 arcs.
    [Symmetry] Symmetry computation done. time: 0.00305173 dtime: 0.00995105
    [Encoding] #Boolean: 1'940'400 (#in_objective: 19'800)
"""

import re
from typing import Optional
from ..models import PreloadingInfo
from .base import ParserComponent
from .utils import parse_number


class PreloadingInfoParser(ParserComponent):
    """
    Parse preloading information including symmetry and encoding details.

    Example:
        Preloading model.
        [Symmetry] Graph for symmetry has 39'503 nodes and 78'308 arcs.
        [Symmetry] Symmetry computation done. time: 0.00305173 dtime: 0.00995105
        [Encoding] #Boolean: 1'940'400 (#in_objective: 19'800)
        [EncodingLinearRelaxation] #Bounds: 1'940'400
    """

    field_name = "preloading_info"
    priority = 32

    def parse(self) -> Optional[PreloadingInfo]:
        """
        Parse preloading information.

        Returns:
            PreloadingInfo model or None if not found
        """
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
