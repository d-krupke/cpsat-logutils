# cpsat-logutils

Utilities to parse and work with the logs of
[OR‑Tools](https://developers.google.com/optimization) **CP‑SAT**.

> This library extracts key information from CP‑SAT logs (solutions, bounds,
> presolve stats, subsolver activity, search progress, conflicts, etc.) and
> exposes them in structured Python objects you can analyze or visualize.

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

Below is a step-by-step parsing workflow. For each block, explore its
**block-specific methods** in the
[blocks/ directory](https://github.com/d-krupke/cpsat-logutils/tree/main/src/cpsat_logutils/blocks),
and adapt the calls shown here to your needs.

#### a) Instantiate the parser

Create the parser instance from the raw log string.

```python
from cpsat_logutils import LogParser

parser = LogParser(raw_log)
```

#### b) Retrieve solver-level info

Get high-level solver metadata such as version, number of workers, and
parameters.

```python
from cpsat_logutils.blocks import SolverBlock

if solver_block := parser.get_block_of_type_or_none(SolverBlock):
    print("CP-SAT version:", solver_block.get_version())
    print("Workers:", solver_block.get_number_of_workers())
    print("Parameters:", solver_block.get_parameters())
```

#### c) Inspect model statistics

Display the number of variables and constraints before and after presolve.

```python
from cpsat_logutils.blocks import InitialModelBlock, PresolvedModelBlock

if initial := parser.get_block_of_type_or_none(InitialModelBlock):
    print(
        "Initial model:",
        initial.get_num_variables(),
        "vars,",
        initial.get_num_constraints(),
        "constraints",
    )

if presolved := parser.get_block_of_type_or_none(PresolvedModelBlock):
    print(
        "Presolved model:",
        presolved.get_num_variables(),
        "vars,",
        presolved.get_num_constraints(),
        "constraints",
    )
```

#### d) Check presolve outcome

Determine whether the problem was solved during presolve.

```python
from cpsat_logutils.blocks import PresolveSummaryBlock

solved_by_presolve = False
if ps := parser.get_block_of_type_or_none(PresolveSummaryBlock):
    solved_by_presolve = ps.is_solved_by_presolve()
    print("Solved by presolve:", solved_by_presolve)
```

#### e) Explore search progress and stats

If presolve did not solve the problem, inspect search progress events, task
timing, search statistics, and objective bounds.

```python
from cpsat_logutils.blocks import (
    SearchProgressBlock,
    SearchStatsBlock,
    TaskTimingBlock,
    ObjectiveBoundsBlock,
)

if not solved_by_presolve:
    if sp := parser.get_block_of_type_or_none(SearchProgressBlock):
        print("Presolve time (s):", sp.get_presolve_time())
        print(sp.get_events())  # list of events, see BoundEvent, ObjEvent, ModelEvent

    if tt := parser.get_block_of_type_or_none(TaskTimingBlock):
        print(tt.to_pandas().head())

    if ss := parser.get_block_of_type_or_none(SearchStatsBlock):
        print(ss.to_pandas().head())

    if ob := parser.get_block_of_type_or_none(ObjectiveBoundsBlock):
        print(ob.to_pandas().head())
```

#### f) Get final solver response

Access the solver’s final response, including status and objective value.

```python
from cpsat_logutils.blocks import ResponseBlock

if resp := parser.get_block_of_type_or_none(ResponseBlock):
    print(resp.to_dict())
```

### 3) Save or visualize

`cpsat-logutils` focuses on parsing and structuring; you can:

- export DataFrames to
  [CSV](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_csv.html)/[JSON](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html)
  for dashboards,
- plot progress/bounds over time with
  [matplotlib](https://matplotlib.org/stable/index.html)/[plotly](https://plotly.com/python/),
- feed the output into your own analyzers.

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
