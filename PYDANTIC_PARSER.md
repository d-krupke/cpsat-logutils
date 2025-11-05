# Pydantic-Based Parser

This document describes the Pydantic-based parser for CP-SAT logs, which provides clean, structured, and JSON-serializable models perfect for web frontends and data analysis.

## Overview

The parser (`LogParser`) uses a component-based architecture to extract data from CP-SAT logs and structures it into Pydantic models. This approach offers several advantages:

- **Type Safety**: All fields are strongly typed with Pydantic validation
- **JSON Serialization**: Direct export to JSON for web frontends
- **Clean API**: Simple, intuitive access to all log data
- **Robust Parsing**: Handles variations in log formats across CP-SAT versions
- **Easy to Extend**: Component-based architecture makes it easy to add new parsers
- **Extensible**: Register custom parser components for domain-specific needs

## Quick Start

```python
from cpsat_logutils import LogParser

# Read your CP-SAT log
with open("solver_log.txt", "r") as f:
    log_content = f.read()

# Parse it
parser = LogParser(log_content)
parsed_log = parser.parse()

# Access structured data
print(f"Solver version: {parsed_log.solver_info.version}")
print(f"Status: {parsed_log.response.status}")
print(f"Objective: {parsed_log.response.objective}")

# Export to JSON for your frontend
json_data = parsed_log.model_dump_json(indent=2)
```

## Model Structure

The parser produces a `CPSATLog` model with the following structure:

```
CPSATLog
├── solver_info: SolverInfo                    # Version, parameters, workers
├── initial_model: ModelStatistics             # Model before presolve
├── presolve_log: List[PresolveEntry]          # Presolve operations
├── presolve_summary: PresolveSummary          # Presolve summary
├── presolved_model: ModelStatistics           # Model after presolve
├── preloading_info: PreloadingInfo            # Preloading phase data
├── search_info: SearchInfo                    # Search configuration
├── search_events: List[SearchEvent]           # Search progress events
│   ├── BoundEvent                             # Bound improvements
│   ├── ObjectiveEvent                         # New solutions
│   └── ModelEvent                             # Model updates
├── task_timing: List[TaskTimingEntry]         # Subsolver timing
├── search_stats: List[SearchStatEntry]        # Search statistics
├── sat_stats: List[SATStatEntry]              # SAT statistics
├── lns_stats: List[LNSStatEntry]              # LNS statistics
├── ls_stats: List[LSStatEntry]                # Local search statistics
├── lp_stats: List[LPStatEntry]                # LP statistics
├── solution_repositories: SolutionRepositories # Solution repos stats
├── objective_bounds: List[ObjectiveBoundEntry] # Bounds by subsolver
├── improving_bounds_shared: ImprovingBoundsShared # Shared bounds
├── clauses_shared: ClausesShared              # Shared clauses
├── response: CPSolverResponse                 # Final solver response
└── comments: List[str]                        # // comments from log
```

## Usage Examples

### Analyzing Search Progress

```python
parser = LogParser(log_content)
parsed_log = parser.parse()

# Get all objective improvements
objective_events = [
    e for e in parsed_log.search_events
    if e.event_type == "objective"
]

for event in objective_events[:10]:  # First 10 solutions
    print(f"Solution #{event.solution_number} at {event.time:.2f}s:")
    print(f"  Objective: {event.objective}")
    print(f"  Gap: {event.gap_percent:.2f}%")
    print(f"  Subsolver: {event.subsolver}")
```

### Exporting for Web Frontends

```python
# Export to JSON
json_str = parsed_log.model_dump_json(indent=2)

# Or as a Python dict
data_dict = parsed_log.model_dump()

# Save to file
with open("log_data.json", "w") as f:
    f.write(json_str)

# In your JavaScript frontend:
# fetch('log_data.json')
#   .then(response => response.json())
#   .then(data => {
#     console.log(`Solver version: ${data.solver_info.version}`);
#     console.log(`Status: ${data.response.status}`);
#   });
```

### Analyzing Model Statistics

```python
if parsed_log.initial_model and parsed_log.presolved_model:
    initial = parsed_log.initial_model
    presolved = parsed_log.presolved_model

    print(f"Variables reduced: {initial.num_variables} → {presolved.num_variables}")

    initial_constraints = sum(c.count for c in initial.constraints)
    presolved_constraints = sum(c.count for c in presolved.constraints)
    print(f"Constraints reduced: {initial_constraints} → {presolved_constraints}")
```

### Plotting Search Progress

```python
import matplotlib.pyplot as plt

# Extract objective values over time
times = []
objectives = []
bounds = []

for event in parsed_log.search_events:
    if event.event_type == "objective":
        times.append(event.time)
        objectives.append(event.objective)
        bounds.append(event.bound)

# Plot
plt.figure(figsize=(10, 6))
plt.plot(times, objectives, 'b-', label='Best Objective')
plt.plot(times, bounds, 'r--', label='Best Bound')
plt.xlabel('Time (s)')
plt.ylabel('Value')
plt.title('CP-SAT Search Progress')
plt.legend()
plt.grid(True)
plt.savefig('search_progress.png')
```

### Analyzing Subsolver Performance

```python
from collections import defaultdict

# Count solutions by subsolver
solutions_by_subsolver = defaultdict(int)

for event in parsed_log.search_events:
    if event.event_type == "objective":
        solutions_by_subsolver[event.subsolver] += 1

# Print top performers
for subsolver, count in sorted(
    solutions_by_subsolver.items(),
    key=lambda x: x[1],
    reverse=True
)[:10]:
    print(f"{subsolver}: {count} solutions")
```

## Type Safety and Validation

All models use Pydantic for validation:

```python
# All fields are validated
solver_info = SolverInfo(
    version="9.8.3296",
    parameters={"log_search_progress": True},
    num_workers=24
)

# Invalid data raises validation errors
try:
    solver_info = SolverInfo(
        version=123,  # Should be string!
        parameters="invalid"  # Should be dict!
    )
except ValidationError as e:
    print(e)
```

## Robustness

The parser is designed to handle variations in CP-SAT log formats:

- **Version Compatibility**: Works with CP-SAT 9.3 through 9.11+
- **Spelling Variations**: Handles minor spelling differences
- **Missing Sections**: Gracefully handles logs with missing sections
- **Extra Lines**: Robust to extra whitespace and formatting changes
- **Scientific Notation**: Properly handles large numbers

## Performance

The parser is efficient:

- **Fast Parsing**: Component-based extraction is quick
- **Low Memory**: Structured models are memory-efficient
- **Extensible**: Register only the components you need

## Extensibility

The parser uses a component-based architecture that makes it easy to extend:

```python
from cpsat_logutils.parsers.base import ParserComponent, ParserRegistry
from typing import Optional

# Create a custom parser component
class CustomParser(ParserComponent):
    """Parse custom information from logs."""

    field_name = "my_custom_data"
    priority = 50  # Controls execution order

    def parse(self) -> Optional[dict]:
        # Your parsing logic here
        for line in self.lines:
            if "MY_CUSTOM_TAG:" in line:
                return {"value": line.split(":")[1].strip()}
        return None

# Register your custom component
from cpsat_logutils.parser import default_registry
default_registry.register(CustomParser)

# Now parse as usual - your custom data will be included
parser = LogParser(log_content)
result = parser.parse()
print(result.my_custom_data)  # Access your custom parsed data
```

See [parsers/README.md](src/cpsat_logutils/parsers/README.md) for detailed documentation on creating custom parser components.

## Contributing

To add new fields or models:

1. Add the field to the appropriate model in `models.py`
2. Create a new parser component in `src/cpsat_logutils/parsers/`
3. Register the component in `parser.py`
4. Add tests in `tests/test_parser.py`
5. Update this documentation

## See Also

- [Main README](README.md) - General package information
- [Example Usage](example_usage.py) - Complete working example
- [Parser Components README](src/cpsat_logutils/parsers/README.md) - Component architecture guide
- [Test Suite](tests/test_parser.py) - Comprehensive test examples
