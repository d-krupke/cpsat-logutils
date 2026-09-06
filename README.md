# cpsat-logutils

Parse [CP-SAT](https://developers.google.com/optimization/cp/cp_solver)
(OR-Tools) solver logs into **line-anchored, JSON-serializable pydantic
models**.

```bash
pip install cpsat-logutils
```

```python
from cpsat_logutils import parse_log

log = parse_log(open("solver.log").read())

log.solver.version.value  # "9.15.6755"
log.solver.parameters.value  # {"max_time_in_seconds": 5, "num_workers": 8, ...}
log.response.status.value  # "OPTIMAL"
log.response.status.line  # 346  <- every value knows its line
log.search.events[0].objective  # first solution value
log.stats.search_stats.row("core").values["Conflicts"]
log.block_at(line=42)  # -> BlockRef(kind="presolve", span=..., path="/presolve")
log.model_dump_json(indent=2)  # plain JSON
```

Sections that do not occur in a log are simply `None`. Nothing raises on a log
the parser does not fully understand: unknown sections are kept verbatim in
`log.unparsed`.

## Getting a log

```python
from ortools.sat.python import cp_model

solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True
solver.parameters.log_to_stdout = False
lines: list[str] = []
solver.log_callback = lines.append
solver.solve(model)

log = parse_log("\n".join(lines))
```

A log copied out of a terminal works just as well, including one that was
clipped, prefixed by a logging framework, or has your own prints mixed in.

## Why line anchors?

Log analyzers want to show the raw text next to the parsed data. Every scalar is
a `Loc[T]` (`value` + `line`), table rows carry their `line`, every section has
a `span`, and `CpSatLog.blocks` is an ordered index (`kind`, `span`, JSON
pointer `path`) that maps any line back to the parsed section.

## Supported versions

OR-Tools 9.3 to 9.15. Known format traps (older `[Name] ... time=` presolve
lines, `Solutions found per subsolver:` lists, progress lines inside the
presolve block, `LRAT_status`, renamed table columns) are handled. Every release
is tested against the example logs in `example_logs/` and against 295 real logs
from public instance libraries in `corpus/`.

## Extending

- `splitter.py` cuts text into chunks; add forced cut points there when a new
  version glues sections together.
- `parsers/` holds one `BlockParser` per section; register new ones in
  `parsers/__init__.py` (first match wins).
- `parsers/tables.py::TABLE_IDS` maps table titles to stable ids; add a line for
  a new table and give it a field in `schema/tables.py::FinalStats`.
- `assemble.py` places blocks into the root model and merges multi-chunk
  sections.

## Development

```bash
uv sync
uv run pytest
uv run ruff check . && uv run ty check
```

## Related

The [CP-SAT Log Analyzer](https://github.com/d-krupke/CP-SAT-Log-Analyzer) is
built on this library: it explains a parsed log section by section in a web UI,
and is hosted at <https://cpsat-loganalyzer.krupke-algorithms.de/>.

## History

Version 1.0 is a rewrite. Up to 0.0.4 this package exposed a block-based API
(`LogParser`, `SolverBlock`, `SearchProgressBlock`, ...) that returned loosely
typed dictionaries; it is gone. The parser now produces one validated pydantic
model per log, in which every value carries the line it was read from. Pin
`cpsat-logutils<1` if you depend on the old API.

## License

MIT, see [LICENSE](LICENSE).
