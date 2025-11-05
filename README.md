# cpsat-logutils

Utilities to parse and work with the logs of
[OR‑Tools](https://developers.google.com/optimization) **CP‑SAT**.

> This library extracts key information from CP‑SAT logs (solutions, bounds,
> presolve stats, subsolver activity, search progress, conflicts, etc.) and
> exposes them in structured Python objects you can analyze or visualize.

## Pydantic-Based Parser

The parser produces clean, structured Pydantic models perfect for web frontends and data analysis:

```python
from cpsat_logutils import LogParser

parser = LogParser(log_content)
parsed_log = parser.parse()

# Access structured data
print(f"Version: {parsed_log.solver_info.version}")
print(f"Status: {parsed_log.response.status}")

# Export directly to JSON for frontends
json_data = parsed_log.model_dump_json(indent=2)
```

**Key Features:**
- ✅ **Type-safe** Pydantic models with validation
- ✅ **JSON-serializable** for easy frontend integration
- ✅ **Clean API** with intuitive access to all log data
- ✅ **Robust parsing** handles variations across CP-SAT versions
- ✅ **Extensible** component-based architecture for custom parsing

See [PYDANTIC_PARSER.md](PYDANTIC_PARSER.md) for full documentation and [example_usage.py](example_usage.py) for a complete working example.

## Installation

```bash
pip install cpsat-logutils
```

## Quickstart

### 1) Enable CP‑SAT logging in your solver

Enable detailed CP‑SAT log output and capture it programmatically.

```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... build your model ...

solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True  # Show detailed search log

log_lines: list[str] = []
solver.log_callback = log_lines.append  # Capture logs in a list

status = solver.Solve(model)
raw_log = "\n".join(log_lines)
```

### 2) Parse the log with `cpsat-logutils`

Create the parser and access structured data through Pydantic models:

```python
from cpsat_logutils import LogParser

# Parse the log
parser = LogParser(raw_log)
result = parser.parse()

# Access solver information
print(f"CP-SAT version: {result.solver_info.version}")
print(f"Workers: {result.solver_info.num_workers}")
print(f"Parameters: {result.solver_info.parameters}")

# Access model statistics
if result.initial_model:
    print(f"Initial model: {result.initial_model.num_variables} vars, "
          f"{result.initial_model.num_constraints} constraints")

if result.presolved_model:
    print(f"Presolved model: {result.presolved_model.num_variables} vars, "
          f"{result.presolved_model.num_constraints} constraints")

# Check presolve outcome
if result.presolve_summary:
    print(f"Solved by presolve: {result.presolve_summary.solved_by_presolve}")

# Access search progress
for event in result.search_events[:5]:  # Show first 5 events
    print(f"  {event}")

# Access final response
print(f"Status: {result.response.status}")
if result.response.objective is not None:
    print(f"Objective: {result.response.objective}")
```

### 3) Export to JSON

All data is JSON-serializable for easy integration with web frontends:

```python
# Export to JSON
json_data = result.model_dump_json(indent=2)

# Or as a Python dict
data_dict = result.model_dump()
```

### 4) Visualize or analyze

`cpsat-logutils` focuses on parsing and structuring; you can:

- Export to JSON for web dashboards
- Plot progress/bounds over time with
  [matplotlib](https://matplotlib.org/stable/index.html)/[plotly](https://plotly.com/python/)
- Feed the output into your own analyzers

If you prefer a ready‑made GUI, see the **CP‑SAT Log Analyzer** below.

## Examples

- Minimal example logs live in [`example_logs/`](./example_logs/) of this repo.
- See the test suite in [`tests/`](./tests/) for end‑to‑end parsing and
  assertions.

## FAQ

**Which CP‑SAT versions are supported?** The parser targets the log format used
by recent OR‑Tools releases (9.8+). If a newer CP‑SAT version changes the log
format and something breaks, please open an issue with a sample CP‑SAT output
log.

**Can I parse logs from other languages (C++/Java/C#)?** Yes. As long as you
enable `log_search_progress` and collect the textual CP‑SAT log, the content is
the same. Save it to a text file or feed the string to the parser.

**Do I need to redirect stdout?** No. In Python you can capture logs via
`solver.log_callback = my_fn` to avoid duplicates.

## Related resources

- **CP‑SAT (official docs)** — overview & tutorials:
  [https://developers.google.com/optimization/cp/cp_solver](https://developers.google.com/optimization/cp/cp_solver)
- **The CP‑SAT Primer** — in‑depth guide by the same author:
  [https://d-krupke.github.io/cpsat-primer/00_intro.html](https://d-krupke.github.io/cpsat-primer/00_intro.html)
- **CP‑SAT Log Analyzer (GUI)** — Streamlit app to explore logs interactively:
  [https://cpsat-log-analyzer.streamlit.app/](https://cpsat-log-analyzer.streamlit.app/)
  • source:
  [https://github.com/d-krupke/CP-SAT-Log-Analyzer](https://github.com/d-krupke/CP-SAT-Log-Analyzer)

## Contributing

Issues and PRs are welcome! If you hit a parsing edge case, please attach a
sample CP‑SAT output log that reproduces it.

When submitting a merge request, please ensure:

- All tests pass locally: `pytest`
- Code style and linting pass: use [`pre-commit`](https://pre-commit.com/) with
  the provided configuration (`.pre-commit-config.yaml`). Run
  `pre-commit run --all-files` before submitting.

Refer to the
[CI workflow](https://github.com/d-krupke/cpsat-logutils/blob/main/.github/workflows/pytest.yml)
for the full test and lint configuration.

## Version History

- v0.0.3: Extended `__all__` import
