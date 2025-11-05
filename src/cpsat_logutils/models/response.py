"""
Response model for CP-SAT solver results.

This module contains the CPSolverResponse model, which represents the final
summary of the solver's execution, including:
- Status (OPTIMAL, FEASIBLE, INFEASIBLE, etc.)
- Final objective value and best bound
- Performance metrics (time, conflicts, branches)
- Solution statistics
"""

from typing import Optional, Dict
from pydantic import BaseModel, Field, ConfigDict


class CPSolverResponse(BaseModel):
    """
    Final solver response summary from CP-SAT.

    This is the last section of the CP-SAT log, containing the complete
    summary of the solver's execution. It includes the solution status,
    objective value, bounds, and various performance metrics.

    **Status values:**
    - **OPTIMAL**: Found and proved optimal solution
    - **FEASIBLE**: Found feasible solution but not proved optimal (usually hit time limit)
    - **INFEASIBLE**: Proved no solution exists
    - **UNKNOWN**: Solver couldn't determine status (rare)

    **Key metrics for performance analysis:**
    - **conflicts**: Number of conflicts - higher means harder problem
    - **branches**: Number of branching decisions - indicates search tree size
    - **propagations**: Constraint deductions - shows constraint activity
    - **walltime**: Real time elapsed - what users care about
    - **deterministic_time**: Reproducible across runs - for benchmarking

    Example:
        >>> response = result.response
        >>> print(f"Status: {response.status}")
        >>> print(f"Objective: {response.objective}")
        >>> print(f"Best bound: {response.best_bound}")
        >>> print(f"Wall time: {response.walltime}s")
        >>>
        >>> # Check if optimal
        >>> if response.status == "OPTIMAL":
        ...     print("Solution is proven optimal!")
        >>> elif response.status == "FEASIBLE":
        ...     gap = abs(response.objective - response.best_bound) / abs(response.objective)
        ...     print(f"Feasible with {gap*100:.2f}% gap")

    Example:
        >>> # Analyze solver performance
        >>> if response.conflicts and response.branches:
        ...     ratio = response.branches / response.conflicts
        ...     print(f"Branching ratio: {ratio:.2f} branches per conflict")
        >>>
        >>> # Check LP usage
        >>> if response.lp_iterations:
        ...     print(f"LP solver used: {response.lp_iterations} iterations")
    """

    model_config = ConfigDict(extra="forbid")

    status: str = Field(
        ...,
        description=(
            "Solver status indicating the result. "
            "Common values: 'OPTIMAL' (found and proved optimal solution), "
            "'FEASIBLE' (found solution but not proved optimal), "
            "'INFEASIBLE' (proved no solution exists), "
            "'UNKNOWN' (couldn't determine status)"
        ),
        min_length=1
    )

    objective: Optional[float] = Field(
        None,
        description=(
            "Final objective value of the best solution found. "
            "None for satisfaction problems or if no solution was found. "
            "For minimization, lower is better. For maximization, higher is better."
        )
    )

    best_bound: Optional[float] = Field(
        None,
        description=(
            "Best bound on the optimal objective value. "
            "For minimization: best_bound ≤ optimal_value. "
            "For maximization: best_bound ≥ optimal_value. "
            "Gap = |objective - best_bound| shows remaining optimization potential."
        )
    )

    num_integers: Optional[int] = Field(
        None,
        description="Number of integer variables in the (presolved) model",
        ge=0
    )

    num_booleans: Optional[int] = Field(
        None,
        description="Number of boolean variables in the (presolved) model",
        ge=0
    )

    conflicts: Optional[int] = Field(
        None,
        description=(
            "Total number of conflicts across all workers. "
            "A conflict occurs when the solver reaches an impossible state. "
            "Higher conflicts indicate a harder problem or more search effort."
        ),
        ge=0
    )

    branches: Optional[int] = Field(
        None,
        description=(
            "Total number of branching decisions made across all workers. "
            "Each branch represents a choice point in the search tree. "
            "Roughly indicates search tree size."
        ),
        ge=0
    )

    propagations: Optional[int] = Field(
        None,
        description=(
            "Total number of boolean propagations (constraint deductions). "
            "Propagations find implied variable values without branching. "
            "Higher values indicate active constraint propagation."
        ),
        ge=0
    )

    integer_propagations: Optional[int] = Field(
        None,
        description=(
            "Total number of integer propagations. "
            "Similar to bool propagations but for integer constraints."
        ),
        ge=0
    )

    restarts: Optional[int] = Field(
        None,
        description=(
            "Total number of search restarts across all workers. "
            "Restarts help escape poor search regions while keeping learned clauses."
        ),
        ge=0
    )

    lp_iterations: Optional[int] = Field(
        None,
        description=(
            "Total number of LP solver iterations. "
            "Present if linear programming relaxations were used. "
            "LP provides bounds by solving continuous relaxations."
        ),
        ge=0
    )

    walltime: Optional[float] = Field(
        None,
        description=(
            "Total wall clock time in seconds from solver start to end. "
            "This is the real-world time users experience. "
            "Includes all phases: presolve, search, and finalization."
        ),
        ge=0.0
    )

    usertime: Optional[float] = Field(
        None,
        description=(
            "Total CPU time in seconds (user time). "
            "Sum of CPU time across all threads. "
            "Can exceed walltime in parallel execution."
        ),
        ge=0.0
    )

    deterministic_time: Optional[float] = Field(
        None,
        description=(
            "Deterministic time measure that's reproducible across runs. "
            "Useful for benchmarking since it's independent of hardware/parallelism. "
            "Not directly comparable to wall time."
        ),
        ge=0.0
    )

    gap_integral: Optional[float] = Field(
        None,
        description=(
            "Integral of the optimality gap over time. "
            "Measures solution quality throughout the solve. "
            "Lower is better. Used to compare solver configurations."
        ),
        ge=0.0
    )

    solution_fingerprint: Optional[str] = Field(
        None,
        description=(
            "Fingerprint (hash) of the solution. "
            "Can be used to verify solution consistency across runs."
        )
    )

    additional_fields: Dict[str, str] = Field(
        default_factory=dict,
        description=(
            "Additional fields from the CpSolverResponse that don't have "
            "dedicated attributes. Captures version-specific or rare fields."
        )
    )
