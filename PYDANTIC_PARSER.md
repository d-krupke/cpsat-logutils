# New Pydantic-Based Parser

This document describes the new Pydantic-based parser for CP-SAT logs, which provides clean, structured, and JSON-serializable models perfect for web frontends and data analysis.

## Overview

The new parser (`LogParserNew`) uses regular expressions to extract data from CP-SAT logs and structures it into Pydantic models. This approach offers several advantages:

- **Type Safety**: All fields are strongly typed with Pydantic validation
- **JSON Serialization**: Direct export to JSON for web frontends
- **Clean API**: Simple, intuitive access to all log data
- **Robust Parsing**: Handles variations in log formats across CP-SAT versions
- **Easy to Extend**: Simple model structure makes it easy to add new fields

## Quick Start

```python
from cpsat_logutils import LogParserNew

# Read your CP-SAT log
with open("solver_log.txt", "r") as f:
    log_content = f.read()

# Parse it
parser = LogParserNew(log_content)
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
parser = LogParserNew(log_content)
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

The new parser is efficient:

- **Fast Parsing**: Regex-based extraction is quick
- **Low Memory**: Structured models are memory-efficient
- **Incremental Access**: You don't need to parse everything at once

## Comparison with Original Parser

| Feature | Original Parser | New Pydantic Parser |
|---------|----------------|---------------------|
| Type Safety | ❌ | ✅ Strong typing |
| JSON Export | ⚠️ Via pandas | ✅ Native support |
| API Style | Block-based | Unified structure |
| Validation | ❌ | ✅ Pydantic validation |
| Documentation | Good | Excellent (self-documenting) |
| Frontend Use | ⚠️ Requires conversion | ✅ Direct JSON export |

## Migration Guide

If you're using the old parser, here's how to migrate:

### Old API:
```python
from cpsat_logutils import LogParser
from cpsat_logutils.blocks import SolverBlock, ResponseBlock

parser = LogParser(log_content)
solver_block = parser.get_block_of_type(SolverBlock)
version = solver_block.get_version()
response_block = parser.get_block_of_type(ResponseBlock)
response_dict = response_block.to_dict()
```

### New API:
```python
from cpsat_logutils import LogParserNew

parser = LogParserNew(log_content)
parsed_log = parser.parse()
version = parsed_log.solver_info.version
response = parsed_log.response  # Already structured!
```

## Contributing

To add new fields or models:

1. Add the field to the appropriate model in `models.py`
2. Update the parser method in `parser_new.py`
3. Add tests in `tests/test_new_parser.py`
4. Update this documentation

## See Also

- [Main README](README.md) - General package information
- [Example Usage](example_usage.py) - Complete working example
- [Test Suite](tests/test_new_parser.py) - Comprehensive test examples
