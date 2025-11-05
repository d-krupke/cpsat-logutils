"""
Parser for Solutions section.

Example log lines:
    Solutions (18)                   Num     Rank
        'graph_arc_lns':    1  [15,15]
        'quick_restart':    1  [11,11]
"""

import re
from typing import List
from ..models.statistics import SolutionEntry
from .base import ParserComponent


class SolutionsParser(ParserComponent):
    """
    Parse Solutions section showing which subsolvers found solutions.
    
    Example:
        Solutions (18)                   Num     Rank
            'graph_arc_lns':    1  [15,15]
            'quick_restart':    1  [11,11]
    """
    
    field_name = "solutions"
    priority = 59
    
    def parse(self) -> List[SolutionEntry]:
        """
        Parse solutions section.
        
        Returns:
            List of SolutionEntry models
        """
        entries = []
        
        in_section = False
        section_start = None
        section_end = None
        
        for i, line in enumerate(self.lines):
            if re.match(r"Solutions\s+\(\d+\)", line, re.IGNORECASE):
                section_start = i
                in_section = True
                continue
            elif in_section and (not line.strip() or not line.startswith(" ")):
                section_end = i
                break
            
            if not in_section or not line.strip():
                continue
            
            # Parse entries like: 'subsolver':  1  [15,15]
            if match := re.match(r"\s*'([^']+)':\s*(\d+)\s+\[(\d+),(\d+)\]", line):
                subsolver = match.group(1)
                num_solutions = int(match.group(2))
                rank_min = int(match.group(3))
                rank_max = int(match.group(4))
                
                entries.append(
                    SolutionEntry(
                        subsolver=subsolver,
                        num_solutions=num_solutions,
                        rank_range=[rank_min, rank_max]
                    )
                )
                section_end = i + 1
        
        # Track the solutions section
        if section_start is not None and section_end is not None:
            self.track_lines(section_start, section_end)
        
        return entries
