# CP-SAT Log Analysis Examples

This directory contains examples demonstrating how to use the DataFrame export functionality for analyzing CP-SAT solver logs.

## Installation

Install the package with DataFrame support:

```bash
pip install cpsat-logutils[dataframes] matplotlib
```

## Running the Examples

```bash
cd examples
python dataframe_analysis.py
```

## Examples Included

### 1. Plot Convergence

Visualizes the convergence of the optimization by plotting:
- Objective values (solutions found)
- Proven bounds over time

**Output:** `convergence_plot.png`

![Example convergence plot](https://via.placeholder.com/800x400?text=Convergence+Plot)

### 2. Analyze Presolve

Analyzes presolve operations to understand:
- Which operations took the most time
- How frequently each operation was applied
- Cumulative presolve time

**Output:** `presolve_analysis.png`

### 3. Subsolver Performance

Analyzes which subsolvers were most effective:
- Solutions found by each subsolver
- Bounds improved by each subsolver
- Objective bounds table

### 4. Task Timing Breakdown

Shows where the solver spent its time:
- Top tasks by time spent
- Number of times each task was run
- Percentage distribution pie chart

**Output:** `task_timing.png`

### 5. Gap Over Time

Plots how the optimality gap closes during the search:
- Gap percentage over time
- Initial vs final gap

**Output:** `gap_over_time.png`

### 6. Export to HTML

Creates an HTML report with formatted tables:
- Solver information
- Search statistics
- Task timing
- Objective bounds

**Output:** `solver_report.html`

## Using DataFrames in Your Code

### Basic Usage

```python
from cpsat_logutils import LogParser

# Parse a log
with open("my_log.txt") as f:
    parser = LogParser(f.read())
result = parser.parse()

# Export to DataFrame
df = result.search_events.bounds_and_solutions_df()
print(df.head())
```

### Available DataFrame Methods

#### Search Events

```python
# Bounds and solutions (compatible events)
bounds_df = result.search_events.bounds_and_solutions_df()
# Columns: time_seconds, event_type, value, solution_number,
#          gap_percent, subsolver, additional_info

# Model events (structure changes)
model_df = result.search_events.model_events_df()
# Columns: time_seconds, vars_remaining, vars_total,
#          constraints_remaining, constraints_total, additional_info
```

#### Presolve

```python
presolve_df = result.presolve_log.to_dataframe()
# Columns: operation, wall_time_seconds, deterministic_time, details
```

#### Statistics

```python
# Task timing
timing_df = result.task_timing.to_dataframe()
# Columns: task_name, time_spent_seconds, num_runs, deterministic_time

# Search statistics
search_df = result.search_stats.to_dataframe()
# Columns: subsolver, booleans, conflicts, branches, restarts, ...

# SAT statistics
sat_df = result.sat_stats.to_dataframe()

# LNS statistics
lns_df = result.lns_stats.to_dataframe()

# LS statistics
ls_df = result.ls_stats.to_dataframe()

# LP statistics
lp_df = result.lp_stats.to_dataframe()

# Objective bounds
bounds_df = result.objective_bounds.to_dataframe()
# Columns: subsolver, num_bounds
```

### Custom Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Get data
df = result.search_events.bounds_and_solutions_df()

# Filter for objectives only
objectives = df[df['event_type'] == 'objective']

# Plot objective values over time
plt.figure(figsize=(10, 6))
plt.plot(objectives['time_seconds'], objectives['value'])
plt.xlabel('Time (seconds)')
plt.ylabel('Objective Value')
plt.title('Objective Improvement Over Time')
plt.grid(True)
plt.savefig('my_plot.png')
```

### Analyzing Multiple Logs

```python
import pandas as pd
from pathlib import Path
from cpsat_logutils import LogParser

results = []
for log_file in Path('logs').glob('*.txt'):
    with open(log_file) as f:
        result = LogParser(f.read()).parse()

    # Extract final metrics
    results.append({
        'file': log_file.name,
        'status': result.response.status,
        'objective': result.response.objective,
        'walltime': result.response.walltime,
        'conflicts': result.response.conflicts,
        'num_solutions': len([e for e in result.search_events.events
                             if e.event_type == 'objective'])
    })

# Create comparison DataFrame
comparison_df = pd.DataFrame(results)
print(comparison_df.to_string())
```

## Column Naming Convention

All DataFrames use **snake_case** column naming:
- `time_seconds` (not `Time`, `timeSeconds`, or `time`)
- `solution_number` (not `SolutionNumber` or `solution_num`)
- `event_type` (not `EventType` or `type`)

This ensures consistency and follows pandas best practices.

## Tips

1. **Check for empty data**: Some logs may not have all types of events
   ```python
   df = result.lns_stats.to_dataframe()
   if len(df) == 0:
       print("No LNS stats available")
   ```

2. **Handle None values**: Some fields may be None
   ```python
   df = result.task_timing.to_dataframe()
   df_valid = df[df['time_spent_seconds'].notna()]
   ```

3. **Use describe() for quick stats**:
   ```python
   print(df.describe())
   ```

4. **Export to various formats**:
   ```python
   df.to_csv('output.csv', index=False)
   df.to_excel('output.xlsx', index=False)
   df.to_html('output.html', index=False)
   ```

## Further Reading

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Tutorials](https://matplotlib.org/stable/tutorials/index.html)
- [CP-SAT Solver Documentation](https://developers.google.com/optimization/cp/cp_solver)
