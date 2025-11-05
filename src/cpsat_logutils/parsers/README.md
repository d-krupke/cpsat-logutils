# CP-SAT Log Parser Components

This directory contains the extensible parser architecture for CP-SAT logs. The parser uses a registration-based system that allows you to easily customize or extend parsing behavior.

## Architecture Overview

The parser is built around three main concepts:

1. **ParserComponent**: Base class for all parser components
2. **ParserRegistry**: Registry for managing parser components
3. **LogParser**: Main parser that orchestrates all components

Each parser component is responsible for parsing a specific section of the CP-SAT log.

## Available Parser Components

| Component | File | Description | Example Log Lines |
|-----------|------|-------------|-------------------|
| `CommentsParser` | `comments.py` | Extracts // comments | `// This is a comment` |
| `SolverInfoParser` | `solver_info.py` | Parses solver version and parameters | `Starting CP-SAT solver v9.8.3296` |
| `InitialModelParser` | `model_statistics.py` | Parses initial model statistics | `Initial optimization model '':` |
| `PresolvedModelParser` | `model_statistics.py` | Parses presolved model statistics | `Presolved optimization model '':` |
| `PresolveLogParser` | `presolve_log.py` | Parses presolve operations | `2.30e-03s 0.00e+00d [DetectDominanceRelations]` |
| `PresolveSummaryParser` | `presolve_summary.py` | Parses presolve summary | `Presolve summary:` |
| `PreloadingInfoParser` | `preloading_info.py` | Parses preloading information | `[Symmetry] Graph for symmetry...` |
| `SearchInfoParser` | `search_info.py` | Parses search configuration | `Starting search at 0.68s with 24 workers` |
| `SearchEventsParser` | `search_events.py` | Parses search progress events | `#1 1.52s best:3.15e+09...` |
| `TaskTimingParser` | `task_timing.py` | Parses task timing statistics | `Task timing n` |
| `SearchStatsParser` | `search_stats.py` | Parses search statistics | `Search stats Bools Conflicts...` |
| `SATStatsParser` | `sat_stats.py` | Parses SAT statistics | `SAT stats Constraints...` |
| `LNSStatsParser` | `lns_stats.py` | Parses LNS statistics | `LNS stats Improv/Calls...` |
| `LSStatsParser` | `ls_stats.py` | Parses Local Search statistics | `LS stats Improv/Calls...` |
| `LPStatsParser` | `lp_stats.py` | Parses LP statistics | `LP stats Iterations...` |
| `SolutionRepositoriesParser` | `solution_repositories.py` | Parses solution repositories | `Solution repositories Added...` |
| `ObjectiveBoundsParser` | `objective_bounds.py` | Parses objective bounds | `Objective bounds Num` |
| `ImprovingBoundsSharedParser` | `improving_bounds_shared.py` | Parses improving bounds shared | `Improving bounds shared Num` |
| `ClausesSharedParser` | `clauses_shared.py` | Parses clauses shared | `Clauses shared Num` |
| `ResponseParser` | `response.py` | Parses final CpSolverResponse | `CpSolverResponse summary:` |

## Basic Usage

```python
from cpsat_logutils import LogParser

# Parse a log file
with open("cpsat.log", "r") as f:
    log_content = f.read()

parser = LogParser(log_content)
result = parser.parse()

# Access parsed data
print(f"Solver version: {result.solver_info.version}")
print(f"Final status: {result.response.status}")
print(f"Number of search events: {len(result.search_events)}")
```

## Extending the Parser

### 1. Creating a Custom Parser Component

To create a new parser component, extend the `ParserComponent` base class:

```python
from cpsat_logutils.parsers.base import ParserComponent
from typing import List

class MyCustomParser(ParserComponent):
    """
    Parse custom section from CP-SAT log.

    Example log lines:
        [MyFeature] Starting custom feature
        [MyFeature] Progress: 50%
    """

    # Field name in CPSATLog model
    field_name = "my_custom_data"

    # Priority (lower = parsed earlier)
    priority = 200

    def parse(self) -> List[str]:
        """Parse custom section and return data."""
        results = []
        for line in self.lines:
            if "[MyFeature]" in line:
                results.append(line)
        return results
```

### 2. Registering a Custom Component

Register your component with the default registry:

```python
from cpsat_logutils.parsers import default_registry
from cpsat_logutils import LogParser

# Register your custom parser
default_registry.register(MyCustomParser)

# Now use the parser as normal
parser = LogParser(log_content)
result = parser.parse()

# Access your custom data
print(result.my_custom_data)
```

### 3. Replacing an Existing Component

You can replace existing components to customize parsing behavior:

```python
from cpsat_logutils.parsers import SolverInfoParser, default_registry
from cpsat_logutils.models import SolverInfo

class MySolverInfoParser(SolverInfoParser):
    """Custom solver info parser with additional logic."""

    def parse(self) -> SolverInfo:
        # Call parent implementation
        result = super().parse()

        # Add custom processing
        result.parameters['custom_flag'] = True

        return result

# Replace the default component
default_registry.register(MySolverInfoParser)
```

### 4. Using a Custom Registry

For complete control, create your own registry:

```python
from cpsat_logutils.parsers import ParserRegistry
from cpsat_logutils import LogParser

# Create custom registry
my_registry = ParserRegistry()

# Register only the components you want
my_registry.register(SolverInfoParser)
my_registry.register(ResponseParser)
my_registry.register(MyCustomParser)

# Use custom registry
parser = LogParser(log_content, registry=my_registry)
result = parser.parse()
```

## Parser Component Priority

Components are executed in priority order (lower priority = earlier execution):

- **1-10**: Comments and metadata
- **10-30**: Solver info and initial model
- **30-40**: Presolve information
- **40-50**: Search configuration and events
- **50-70**: Statistics (search, SAT, LNS, LP, etc.)
- **100+**: Final response

You can set custom priorities to control execution order.

## Component Structure

Each parser component should:

1. **Inherit from `ParserComponent`**
2. **Set `field_name`** - the field in CPSATLog where results are stored
3. **Optionally set `priority`** - controls parsing order
4. **Implement `parse()`** - returns structured data
5. **Include docstring with examples** - shows what log lines it handles

Example structure:

```python
class MyParser(ParserComponent):
    """
    Short description.

    Example:
        Log line 1
        Log line 2
    """

    field_name = "my_field"
    priority = 100

    def parse(self):
        # Parsing logic
        return result
```

## Viewing Examples

Each parser component includes examples in its docstring. You can view them:

```python
from cpsat_logutils.parsers import SolverInfoParser

# Get example log lines
print(SolverInfoParser.get_example())
```

## Best Practices

1. **Keep components focused** - Each component should handle one logical section
2. **Use appropriate priorities** - Ensure components run in the right order
3. **Handle errors gracefully** - Return None or empty results if section not found
4. **Document with examples** - Show what log lines the component handles
5. **Test thoroughly** - Verify your component works with different log versions

## Utility Functions

Common utilities are available in `utils.py`:

```python
from cpsat_logutils.parsers.utils import parse_time, parse_number, parse_parameters

# Parse time strings
seconds = parse_time("1.5s")  # 1.5
seconds = parse_time("2m")    # 120.0

# Parse numbers with separators
num = parse_number("1'000")   # 1000
num = parse_number("1.5e6")   # 1500000.0

# Parse parameters line
params = parse_parameters("Parameters: max_time: 90 log_search: true")
# {'max_time': 90, 'log_search': True}
```

## Contributing

When adding new parser components:

1. Create a new file in `src/cpsat_logutils/parsers/`
2. Implement your component class
3. Add imports to `__init__.py`
4. Register in `parser.py`
5. Add tests in `tests/test_parser.py`
6. Update this README

## Support

For questions or issues with the parser architecture, please file an issue on GitHub.
