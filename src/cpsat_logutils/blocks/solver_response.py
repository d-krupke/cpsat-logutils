from .log_block import LogBlock
import typing
from pydantic import BaseModel, Field, computed_field, ConfigDict
from typing import Optional, Dict, Any


class SolverResponse(BaseModel):
    """Structured representation of CP-SAT solver response.

    Attributes:
        status: Solver status (e.g., "OPTIMAL", "FEASIBLE", "INFEASIBLE")
        objective: Objective value of the best solution found
        best_bound: Best bound on the objective value
        num_booleans: Number of boolean variables
        num_conflicts: Number of conflicts during search
        num_branches: Number of branches explored
        num_binary_propagations: Number of binary propagations
        num_integer_propagations: Number of integer propagations
        wall_time: Wall clock time in seconds
        user_time: User CPU time in seconds
        deterministic_time: Deterministic time measure
        primal_integral: Primal integral metric
    """
    status: str = Field(..., description="Solver status")
    objective: Optional[float] = Field(None, description="Objective value")
    best_bound: Optional[float] = Field(None, description="Best bound")
    num_booleans: Optional[int] = Field(None, description="Number of boolean variables")
    num_conflicts: Optional[int] = Field(None, description="Number of conflicts")
    num_branches: Optional[int] = Field(None, description="Number of branches")
    num_binary_propagations: Optional[int] = Field(None, description="Number of binary propagations")
    num_integer_propagations: Optional[int] = Field(None, description="Number of integer propagations")
    wall_time: Optional[float] = Field(None, description="Wall clock time in seconds")
    user_time: Optional[float] = Field(None, description="User CPU time in seconds")
    deterministic_time: Optional[float] = Field(None, description="Deterministic time")
    primal_integral: Optional[float] = Field(None, description="Primal integral")
    additional_fields: Dict[str, Any] = Field(default_factory=dict, description="Additional response fields")

    @computed_field
    @property
    def gap(self) -> Optional[float]:
        """Calculate the optimality gap percentage."""
        if self.objective is None or self.best_bound is None:
            return None
        try:
            obj = float(self.objective)
            bound = float(self.best_bound)
            return 100 * (abs(obj - bound) / max(1, abs(obj)))
        except (TypeError, ValueError):
            return None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "OPTIMAL",
                "objective": 42.0,
                "best_bound": 42.0,
                "num_booleans": 1000,
                "num_conflicts": 5000,
                "num_branches": 10000,
                "wall_time": 12.5,
                "user_time": 11.8,
                "gap": 0.0
            }
        }
    )


class ResponseBlock(LogBlock):
    def __init__(self, lines: typing.List[str]) -> None:
        super().__init__(lines)

    @staticmethod
    def matches(lines: typing.List[str]) -> bool:
        return lines[0].startswith("CpSolverResponse") if lines else False

    def get_title(self) -> str:
        return "CpSolverResponse"

    def to_dict(self) -> dict:
        d = {}
        for line in self.lines:
            if line.startswith("CpSolverResponse"):
                continue
            key, value = line.split(":")
            key = key.strip()
            value = value.strip()
            if key == "status":
                value = value.split(" ")[0]
            d[key] = value
        return d

    def get_gap(self):
        vals = self.to_dict()
        try:
            obj = float(vals["objective"])
            bound = float(vals["best_bound"])
        except (TypeError, ValueError):
            return None
        return 100 * (abs(obj - bound) / max(1, abs(obj)))

    def to_model(self) -> SolverResponse:
        """Convert the ResponseBlock to a structured SolverResponse Pydantic model.

        Returns:
            SolverResponse: A Pydantic model with structured solver response information
        """
        data = self.to_dict()

        # Map known fields
        known_fields = {
            'status', 'objective', 'best_bound', 'num_booleans',
            'num_conflicts', 'num_branches', 'num_binary_propagations',
            'num_integer_propagations', 'wall_time', 'user_time',
            'deterministic_time', 'primal_integral'
        }

        model_data = {}
        additional = {}

        for key, value in data.items():
            if key in known_fields:
                # Try to convert to appropriate type
                if key == 'status':
                    model_data[key] = value
                elif key in ['objective', 'best_bound', 'wall_time', 'user_time',
                             'deterministic_time', 'primal_integral']:
                    try:
                        model_data[key] = float(value)
                    except (ValueError, TypeError):
                        model_data[key] = None
                else:  # integer fields
                    try:
                        model_data[key] = int(value)
                    except (ValueError, TypeError):
                        model_data[key] = None
            else:
                additional[key] = value

        model_data['additional_fields'] = additional

        # Ensure status is always present
        if 'status' not in model_data:
            model_data['status'] = 'UNKNOWN'

        return SolverResponse(**model_data)

    def get_help(self) -> typing.Optional[str]:
        return """
        This final block of the log contains a summary by the solver.
        Here you find the most important information, such as how successful the search was.

        You can find the original documentation [here](https://github.com/google/or-tools/blob/8768ed7a43f8899848effb71295a790f3ecbe2f2/ortools/sat/cp_model.proto#L720).
        """
