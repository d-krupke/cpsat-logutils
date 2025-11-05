"""
Parser for extracting comments from CP-SAT logs.

Example log lines:
    // This is a user comment
    // Another comment line
"""

from typing import List
from .base import ParserComponent


class CommentsParser(ParserComponent):
    """
    Extract // comments from the log.

    Example:
        // This is a user comment
        // Another comment line
    """

    field_name = "comments"
    priority = 1  # Parse early

    def parse(self) -> List[str]:
        """
        Extract all comments from the log.

        Returns:
            List of comment strings (without the // prefix)
        """
        comments = []
        for line in self.lines:
            if line.startswith("//"):
                comments.append(line[2:].strip())
        return comments
