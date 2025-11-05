"""
Utility functions shared across parser components.
"""

import re
from typing import Union, Dict, Any


def parse_time(time_str: str) -> float:
    """
    Parse time string to seconds.

    Args:
        time_str: Time string like "1.5s", "2.3m", or "500ms"

    Returns:
        Time in seconds
    """
    time_str = time_str.strip()
    if match := re.match(r"([\d.]+)s", time_str):
        return float(match.group(1))
    elif match := re.match(r"([\d.]+)m", time_str):
        return float(match.group(1)) * 60
    elif match := re.match(r"([\d.]+)ms", time_str):
        return float(match.group(1)) / 1000
    return 0.0


def parse_number(num_str: str) -> Union[int, float, None]:
    """
    Parse number string, handling thousands separators and scientific notation.

    Args:
        num_str: Number string like "1'000", "1.5e6", "inf", or "NA"

    Returns:
        Parsed number, or None if invalid
    """
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
    """
    Parse the parameters line.

    Args:
        line: Parameters line from log

    Returns:
        Dictionary of parameter key-value pairs
    """
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
