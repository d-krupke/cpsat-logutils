"""

```
Preloading model.
#Bound   0.45s best:inf   next:[1,17]     initial_domain

Starting Search at 0.47s with 16 workers.
9 full subsolvers: [default_lp, no_lp, max_lp, reduced_costs, pseudo_costs, quick_restart, quick_restart_no_lp, lb_tree_search, probing]
Interleaved subsolvers: [feasibility_pump, rnd_var_lns_default, rnd_cst_lns_default, graph_var_lns_default, graph_cst_lns_default, rins_lns_default, rens_lns_default]
#1       0.71s best:17    next:[1,16]     quick_restart_no_lp fixed_bools:0/11849
#2       0.72s best:16    next:[1,15]     quick_restart_no_lp fixed_bools:289/11849
#3       0.74s best:15    next:[1,14]     no_lp fixed_bools:867/11849
#Bound   1.30s best:15    next:[8,14]     max_lp initial_propagation
#Done    3.40s max_lp
#Done    3.40s probing
```

Since OR-Tools 9.11 it looks like
```
Starting search at 16.85s with 14 workers.
10 full problem subsolvers: [core, default_lp, lb_tree_search, max_lp, no_lp, probing, pseudo_costs, quick_restart, quick_restart_no_lp, reduced_costs]
4 first solution subsolvers: [fj(2), fs_random, fs_random_no_lp]
10 interleaved subsolvers: [feasibility_pump, graph_arc_lns, graph_cst_lns, graph_dec_lns, graph_var_lns, ls(2), rins/rens, rnd_cst_lns, rnd_var_lns]
3 helper subsolvers: [neighborhood_helper, synchronization_agent, update_gap_integral]

#1      16.87s best:-0    next:[1,456769] fj_restart(batch:1 lin{mvs:0 evals:0} #w_updates:0 #perturb:0)
#Bound  16.89s best:-0    next:[1,456714] fs_random (initial_propagation)
#Bound  16.94s best:-0    next:[1,456294] core (initial_propagation)
#Bound  16.94s best:-0    next:[1,456180] am1_presolve (num_literals=8767 num_am1=1 increase=114 work_done=416330)
#2      16.95s best:28917 next:[28918,456180] core (fixed_bools=11/8779)
```

"""

import logging
import re
import typing
from typing import Optional
from pydantic import BaseModel, Field, computed_field, ConfigDict
from .log_block import LogBlock


def parse_time(time: str):
    # seconds
    if re.match(r"\d+\.\d+s", time):
        return float(time[:-1])
    # minutes
    if re.match(r"\d+\.\d+m", time):
        return float(time[:-1]) * 60
    # ms
    if re.match(r"\d+\.\d+ms", time):
        return float(time[:-2]) / 1000
    raise ValueError(f"Unknown time format: {time}")


def _get_bound(match: re.Match) -> float:
    """
    Extract the bound from a match object.
    Needs to differ between upper and lower bound.
    """
    if "next_lb" not in match.groupdict():
        return float(match["obj"])
    next_lb = match["next_lb"]
    next_ub = match["next_ub"]
    if next_lb is None or next_ub is None:
        return float(match["obj"])
    bound_lb, bound_ub = float(next_lb), float(next_ub)
    obj = float(match["obj"])
    return bound_ub if obj < bound_lb else bound_lb


def calculate_gap(obj: Optional[float], bound: Optional[float]) -> Optional[float]:
    if obj is None or bound is None:
        return None
    return 100 * (abs(obj - bound) / max(1, abs(obj)))


class BoundEvent(BaseModel):
    """Represents a bound improvement event during search.

    Attributes:
        time: Time in seconds when the bound was found
        obj: Current best objective value (None if no solution yet)
        bound: The new bound value
        msg: Description of how the bound was found
    """
    time: float = Field(..., description="Time in seconds when the bound was found")
    obj: Optional[float] = Field(None, description="Current best objective value")
    bound: float = Field(..., description="The new bound value")
    msg: str = Field(..., description="Description of how the bound was found")

    @computed_field
    @property
    def is_upper_bound(self) -> Optional[bool]:
        """Check if this is an upper bound event."""
        return None if self.obj is None else self.bound > self.obj

    @computed_field
    @property
    def is_lower_bound(self) -> Optional[bool]:
        """Check if this is a lower bound event."""
        return None if self.obj is None else self.bound < self.obj

    @computed_field
    @property
    def gap(self) -> Optional[float]:
        """Calculate the optimality gap percentage."""
        return calculate_gap(self.obj, self.bound)

    @staticmethod
    def parse(line: str) -> Optional["BoundEvent"]:
        # bound events start with #Bound
        # TODO: Allow more than just seconds
        bound_pattern = r"#Bound\s+(?P<time>\d+\.\d+s)\s+(best:(?P<obj>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf)))\s+next:\[(?P<next_lb>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf)),(?P<next_ub>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf))\]\s+(?P<msg>.*)"
        if not (m := re.match(bound_pattern, line)):
            return None
        obj = float(m["obj"]) if m["obj"] != "inf" else None
        return BoundEvent(
            time=parse_time(m["time"]),
            obj=obj,
            bound=_get_bound(m),
            msg=m["msg"],
        )

    # Maintain backward compatibility
    def get_gap(self):
        """Deprecated: Use .gap property instead."""
        return self.gap


class ObjEvent(BaseModel):
    """Represents a new solution (objective) event during search.

    Attributes:
        time: Time in seconds when the solution was found
        obj: The objective value of the new solution
        bound: The current bound value
        msg: Description of how the solution was found
    """
    time: float = Field(..., description="Time in seconds when the solution was found")
    obj: float = Field(..., description="The objective value of the new solution")
    bound: float = Field(..., description="The current bound value")
    msg: str = Field(..., description="Description of how the solution was found")

    @computed_field
    @property
    def gap(self) -> float:
        """Calculate the optimality gap percentage."""
        return 100 * (abs(self.obj - self.bound) / max(1, abs(self.obj)))

    @staticmethod
    def parse(line: str) -> Optional["ObjEvent"]:
        # obj events start with # and a number
        # TODO: Allow more than just seconds
        obj_pattern = r"#(-?\d+)\s+(?P<time>\d+\.\d+s)\s+(best:(?P<obj>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf)))\s+next:\[((?P<next_lb>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf)),(?P<next_ub>[-+]?([0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|inf)))?\]\s+(?P<msg>.*)"
        if m := re.match(obj_pattern, line):
            return ObjEvent(
                time=parse_time(m["time"]),
                obj=float(m["obj"]),
                bound=_get_bound(m),
                msg=m["msg"],
            )
        else:
            return None

    # Maintain backward compatibility
    def get_gap(self) -> float:
        """Deprecated: Use .gap property instead."""
        return self.gap


class ModelEvent(BaseModel):
    """Represents a model modification event during search.

    These events indicate changes to the model structure during search,
    such as fixing variables or removing constraints.

    Example log lines:
        #Model  24.75s var:39921/39999 constraints:79247/79403
        #Model   9.71s var:37230/39800 constraints:1/1 [skipped_logs=5]

    Attributes:
        time: Time in seconds when the model was modified
        vars_remaining: Number of unfixed variables remaining
        vars: Total number of variables
        constr_remaining: Number of active constraints remaining
        constr: Total number of constraints
        msg: Optional message with additional details
    """
    time: float = Field(..., description="Time in seconds when the model was modified")
    vars_remaining: int = Field(..., description="Number of unfixed variables remaining")
    vars: int = Field(..., description="Total number of variables")
    constr_remaining: int = Field(..., description="Number of active constraints remaining")
    constr: int = Field(..., description="Total number of constraints")
    msg: Optional[str] = Field(None, description="Optional message with additional details")

    @computed_field
    @property
    def vars_fixed(self) -> int:
        """Number of variables that have been fixed."""
        return self.vars - self.vars_remaining

    @computed_field
    @property
    def vars_fixed_percentage(self) -> float:
        """Percentage of variables that have been fixed."""
        return 100.0 * self.vars_fixed / self.vars if self.vars > 0 else 0.0

    @computed_field
    @property
    def constr_removed(self) -> int:
        """Number of constraints that have been removed."""
        return self.constr - self.constr_remaining

    @computed_field
    @property
    def constr_removed_percentage(self) -> float:
        """Percentage of constraints that have been removed."""
        return 100.0 * self.constr_removed / self.constr if self.constr > 0 else 0.0

    @staticmethod
    def parse(line: str) -> Optional["ModelEvent"]:
        # Model events start with #Model
        model_pattern = r"#Model\s+(?P<time>\d+\.\d+s)\s+var:(?P<vars_remaining>\d+)/(?P<vars>\d+)\s+constraints:(?P<constr_remaining>\d+)/(?P<constr>\d+)\s*(\[(?P<msg>.*)\])?"
        if m := re.match(model_pattern, line):
            return ModelEvent(
                time=parse_time(m["time"]),
                vars_remaining=int(m["vars_remaining"]),
                vars=int(m["vars"]),
                constr_remaining=int(m["constr_remaining"]),
                constr=int(m["constr"]),
                msg=line,
            )
        else:
            return None


def _parse_version(lines: typing.List[str]) -> typing.Tuple[int, int, int]:
    """
    Parse the version of OR-Tools from log lines.

    Args:
        lines (list[str]): List of log lines containing version information.

    Returns:
        tuple[int, int, int]: Version number as (major, minor, build).

    Raises:
        ValueError: If the version cannot be parsed from the lines.
    """
    version_pattern = (
        r"Starting CP-SAT solver v(?P<version>\d+)\.(?P<subversion>\d+)\.(?P<build>\d+)"
    )

    for line in lines:
        match = re.match(version_pattern, line)
        if match:
            return int(match["version"]), int(match["subversion"]), int(match["build"])

    raise ValueError("Could not parse version from log")


def apply_ortools911_workaround(lines: typing.List[str]) -> typing.List[str]:
    """
    Workaround for OR-Tools 9.11 to remove empty lines before the search progress block.

    Args:
        lines (list[str]): List of log lines to process.

    Returns:
        list[str]: Modified log lines without empty lines before the search progress.

    This is a temporary fix. In future versions, the parser should be adapted properly.
    """
    try:
        version = _parse_version(lines)
        if version < (9, 11, 0):
            return lines  # No changes needed for older versions

        # Initialize variables
        search_block_start_seen = False
        empty_line_index = None

        # Process log lines
        for i, line in enumerate(lines):
            if "Starting search" in line:
                search_block_start_seen = True
                continue

            if not search_block_start_seen:
                continue

            # Check if the current line is part of a search event block
            if (
                BoundEvent.parse(line) is None
                and ObjEvent.parse(line) is None
                and ModelEvent.parse(line) is None
            ):
                if line.strip():  # If the line is not empty, reset empty line index
                    empty_line_index = i + 1
                continue

            # If search block is detected, remove empty lines before the block
            if empty_line_index is not None:
                return lines[:empty_line_index] + lines[i:]
    except ValueError as e:
        logging.warning(f"Version parsing failed: {e}")

    return lines  # Return original lines if no modifications are made


class SearchProgress(BaseModel):
    """Structured representation of search progress with all events.

    Attributes:
        presolve_time: Time taken during presolve phase (seconds)
        events: List of all search events (BoundEvent, ObjEvent, ModelEvent)
        num_solutions: Total number of solutions found
        num_bound_updates: Total number of bound improvements
        num_model_updates: Total number of model modifications
        final_objective: Best objective value found (if any)
        final_bound: Best bound found (if any)
        final_gap: Final optimality gap percentage (if applicable)
    """
    presolve_time: float = Field(..., description="Time taken during presolve phase in seconds")
    events: typing.List[typing.Union[BoundEvent, ObjEvent, ModelEvent]] = Field(
        default_factory=list,
        description="List of all search events"
    )

    @computed_field
    @property
    def num_solutions(self) -> int:
        """Number of solution events."""
        return sum(1 for e in self.events if isinstance(e, ObjEvent))

    @computed_field
    @property
    def num_bound_updates(self) -> int:
        """Number of bound update events."""
        return sum(1 for e in self.events if isinstance(e, BoundEvent))

    @computed_field
    @property
    def num_model_updates(self) -> int:
        """Number of model modification events."""
        return sum(1 for e in self.events if isinstance(e, ModelEvent))

    @computed_field
    @property
    def final_objective(self) -> Optional[float]:
        """Best objective value found."""
        obj_events = [e for e in self.events if isinstance(e, ObjEvent)]
        if not obj_events:
            return None
        # Assuming minimization - take the last objective
        return obj_events[-1].obj

    @computed_field
    @property
    def final_bound(self) -> Optional[float]:
        """Best bound found."""
        # Check both ObjEvent and BoundEvent for the latest bound
        events_with_bounds = [e for e in self.events if hasattr(e, 'bound')]
        if not events_with_bounds:
            return None
        return events_with_bounds[-1].bound

    @computed_field
    @property
    def final_gap(self) -> Optional[float]:
        """Final optimality gap percentage."""
        return calculate_gap(self.final_objective, self.final_bound)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "presolve_time": 0.47,
                "events": [
                    {
                        "time": 0.71,
                        "obj": 17.0,
                        "bound": 1.0,
                        "msg": "quick_restart_no_lp fixed_bools:0/11849"
                    }
                ],
                "num_solutions": 3,
                "num_bound_updates": 2,
                "num_model_updates": 1,
                "final_objective": 15.0,
                "final_bound": 8.0,
                "final_gap": 46.67
            }
        }
    )


class SearchProgressBlock(LogBlock):
    def __init__(self, lines: typing.List[str], check: bool = True) -> None:
        lines = [line.strip() for line in lines if line.strip()]
        if not lines:
            raise ValueError("No lines to parse")
        if check and not self.matches(lines):
            raise ValueError("Lines do not match SearchProgressBlock")
        self.lines = lines

    @staticmethod
    def matches(lines: typing.List[str]) -> bool:
        if not lines:
            return False
        return lines[0].strip().lower().startswith("Starting search".lower())

    def get_events(
        self,
    ) -> typing.List[typing.Union[BoundEvent, ObjEvent, ModelEvent]]:
        """
        Parse the log file into a list of BoundEvent and ObjEvent.
        """
        events = []
        for line in self.lines:
            if obj_event := ObjEvent.parse(line):
                events.append(obj_event)
                continue
            if bound_event := BoundEvent.parse(line):
                events.append(bound_event)
                continue
            if model_event := ModelEvent.parse(line):
                events.append(model_event)
                continue
        return events

    def get_presolve_time(self) -> float:
        if m := re.match(
            r"Starting [Ss]earch at (?P<time>\d+\.\d+s) with \d+ workers.",
            self.lines[0],
        ):
            return parse_time(m["time"])
        raise ValueError(f"Could not parse presolve time from '{self.lines[0]}'")

    def get_title(self) -> str:
        return "Search progress:"

    def to_model(self) -> SearchProgress:
        """Convert the SearchProgressBlock to a structured SearchProgress Pydantic model.

        Returns:
            SearchProgress: A Pydantic model with structured search progress information
        """
        return SearchProgress(
            presolve_time=self.get_presolve_time(),
            events=self.get_events(),
        )

    def get_help(self) -> typing.Optional[str]:
        return """
The search progress log is an essential element of the overall log, crucial for identifying performance bottlenecks. It clearly demonstrates the solver's progression over time and pinpoints where it faces significant challenges. It is important to discern whether the upper or lower bounds are causing issues, or if the solver initially finds a near-optimal solution but struggles to minimize a small remaining gap.

The structure of the log entries is standardized as follows:

`EVENT NAME\t|\tTIME\t|\tBEST SOLUTION\t|\tRANGE OF THE SEARCH\t|\tCOMMENT`

For instance, an event marked `#2` indicates the discovery of the second solution. Here, you will observe an improvement in the `BEST SOLUTION` metric. A notation like `best:16` confirms that the solver has found a solution with a value of 16.

An event with `#Bound` denotes an enhancement in the bound, as seen by a reduction in the `RANGE OF THE SEARCH`. A detail such as `next:[7,14]` signifies that the solver is now focused on finding a solution valued between 7 and 14.

The `COMMENT` section provides essential information about the strategies that led to these improvements.

Events labeled `#Model` signal modifications to the model, such as fixing certain variables.

To fully grasp the nuances, zooming into the plot is necessary, especially since the initial values can be quite large. A thorough examination of which sections of the process converge quickest is crucial for a comprehensive understanding.
        """
