"""
Examples of using DataFrame export for CP-SAT log analysis.

This module demonstrates how to use the DataFrame export functionality
to analyze CP-SAT solver logs with pandas and matplotlib.

To run these examples:
    pip install cpsat-logutils[dataframes] matplotlib
"""

from pathlib import Path
from cpsat_logutils import LogParser

try:
    import pandas as pd
    import matplotlib.pyplot as plt
    PANDAS_AVAILABLE = True
except ImportError:
    print("Please install pandas and matplotlib:")
    print("  pip install cpsat-logutils[dataframes] matplotlib")
    PANDAS_AVAILABLE = False
    exit(1)


def example_1_plot_convergence():
    """
    Example 1: Plot optimization convergence (bounds and objectives).

    This example shows how to visualize the convergence of the solver
    by plotting both the objective values and the proven bounds over time.
    """
    print("\n" + "="*70)
    print("Example 1: Plotting Optimization Convergence")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Get bounds and solutions as DataFrame
    df = result.search_events.bounds_and_solutions_df()

    print(f"\nParsed {len(df)} search events")
    print(f"\nFirst few events:")
    print(df.head())

    # Separate objective events and bound events
    objectives = df[df['event_type'] == 'objective'].copy()
    bounds = df[df['event_type'] == 'bound'].copy()

    print(f"\nFound {len(objectives)} solution improvements")
    print(f"Found {len(bounds)} bound improvements")

    # Plot convergence
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot objective values (solutions found)
    if len(objectives) > 0:
        ax.scatter(
            objectives['time_seconds'],
            objectives['value'],
            label='Objective (solutions)',
            color='blue',
            marker='o',
            s=50,
            zorder=3
        )

    # Plot bounds
    if len(bounds) > 0:
        ax.scatter(
            bounds['time_seconds'],
            bounds['value'],
            label='Proven bound',
            color='red',
            marker='x',
            s=50,
            alpha=0.6,
            zorder=2
        )

    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Objective Value', fontsize=12)
    ax.set_title('CP-SAT Optimization Convergence', fontsize=14)
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save plot
    output_path = Path("convergence_plot.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")

    plt.close()


def example_2_analyze_presolve():
    """
    Example 2: Analyze presolve operations.

    Shows which presolve operations took the most time and how many
    were performed.
    """
    print("\n" + "="*70)
    print("Example 2: Analyzing Presolve Operations")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Get presolve operations as DataFrame
    df = result.presolve_log.to_dataframe()

    if len(df) == 0:
        print("No presolve data available")
        return

    print(f"\nFound {len(df)} presolve operations")

    # Show most time-consuming operations
    df_sorted = df.sort_values('wall_time_seconds', ascending=False)

    print("\nTop 10 most time-consuming presolve operations:")
    print(df_sorted[['operation', 'wall_time_seconds']].head(10).to_string(index=False))

    # Count operations by type
    operation_counts = df['operation'].value_counts()

    print(f"\nMost frequently applied operations:")
    print(operation_counts.head(10))

    # Plot time distribution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Top operations by time
    top_ops = df_sorted.head(15)
    ax1.barh(range(len(top_ops)), top_ops['wall_time_seconds'])
    ax1.set_yticks(range(len(top_ops)))
    ax1.set_yticklabels(top_ops['operation'], fontsize=8)
    ax1.set_xlabel('Wall Time (seconds)')
    ax1.set_title('Top 15 Presolve Operations by Time')
    ax1.invert_yaxis()

    # Cumulative time
    df_sorted['cumulative_time'] = df_sorted['wall_time_seconds'].cumsum()
    ax2.plot(range(len(df_sorted)), df_sorted['cumulative_time'], linewidth=2)
    ax2.set_xlabel('Operation Index (sorted by time)')
    ax2.set_ylabel('Cumulative Time (seconds)')
    ax2.set_title('Cumulative Presolve Time')
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    output_path = Path("presolve_analysis.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")

    plt.close()


def example_3_subsolver_performance():
    """
    Example 3: Analyze subsolver performance.

    Shows which subsolvers found the most solutions and bounds.
    """
    print("\n" + "="*70)
    print("Example 3: Analyzing Subsolver Performance")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Get search events
    df = result.search_events.bounds_and_solutions_df()

    if len(df) == 0:
        print("No search events available")
        return

    # Analyze by subsolver
    solutions = df[df['event_type'] == 'objective']
    bounds = df[df['event_type'] == 'bound']

    print(f"\nSolutions by subsolver:")
    if len(solutions) > 0:
        sol_counts = solutions['subsolver'].value_counts()
        for subsolver, count in sol_counts.head(10).items():
            print(f"  {subsolver}: {count} solutions")

    print(f"\nBounds by subsolver:")
    if len(bounds) > 0:
        bound_counts = bounds['subsolver'].value_counts()
        for subsolver, count in bound_counts.head(10).items():
            print(f"  {subsolver}: {count} bounds")

    # Get objective bounds table
    bounds_df = result.objective_bounds.to_dataframe()

    if len(bounds_df) > 0:
        print(f"\nObjective bounds improvements by subsolver:")
        bounds_sorted = bounds_df.sort_values('num_bounds', ascending=False)
        print(bounds_sorted.head(10).to_string(index=False))


def example_4_task_timing_breakdown():
    """
    Example 4: Task timing breakdown.

    Shows where the solver spent its time across different strategies.
    """
    print("\n" + "="*70)
    print("Example 4: Task Timing Breakdown")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Get task timing
    df = result.task_timing.to_dataframe()

    if len(df) == 0:
        print("No task timing data available")
        return

    # Filter out None values and sort by time
    df_valid = df[df['time_spent_seconds'].notna()].copy()

    if len(df_valid) == 0:
        print("No valid timing data available")
        return

    df_sorted = df_valid.sort_values('time_spent_seconds', ascending=False)

    print(f"\nTop tasks by time spent:")
    print(df_sorted[['task_name', 'time_spent_seconds', 'num_runs']].head(15).to_string(index=False))

    # Calculate percentages
    total_time = df_valid['time_spent_seconds'].sum()
    df_sorted['percentage'] = (df_sorted['time_spent_seconds'] / total_time * 100)

    # Plot pie chart for top tasks
    top_n = 10
    top_tasks = df_sorted.head(top_n)
    other_time = df_valid['time_spent_seconds'].sum() - top_tasks['time_spent_seconds'].sum()

    fig, ax = plt.subplots(figsize=(10, 8))

    sizes = list(top_tasks['time_spent_seconds']) + ([other_time] if other_time > 0 else [])
    labels = list(top_tasks['task_name']) + (['Other'] if other_time > 0 else [])

    ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title(f'Time Distribution Across Top {top_n} Tasks')

    output_path = Path("task_timing.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")

    plt.close()


def example_5_gap_over_time():
    """
    Example 5: Plot optimality gap over time.

    Shows how the optimality gap closes during the search.
    """
    print("\n" + "="*70)
    print("Example 5: Plotting Optimality Gap Over Time")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Get bounds and solutions
    df = result.search_events.bounds_and_solutions_df()

    # Filter for objectives with gap information
    objectives = df[df['event_type'] == 'objective'].copy()
    objectives = objectives[objectives['gap_percent'].notna()]

    if len(objectives) == 0:
        print("No gap data available")
        return

    print(f"\nFound {len(objectives)} solutions with gap information")
    print(f"\nGap reduction:")
    print(f"  Initial gap: {objectives['gap_percent'].iloc[0]:.2f}%")
    print(f"  Final gap: {objectives['gap_percent'].iloc[-1]:.2f}%")

    # Plot gap over time
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(
        objectives['time_seconds'],
        objectives['gap_percent'],
        marker='o',
        linewidth=2,
        markersize=6
    )

    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('Optimality Gap (%)', fontsize=12)
    ax.set_title('Optimality Gap Over Time', fontsize=14)
    ax.grid(True, alpha=0.3)

    # Add horizontal line at 0
    ax.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='Optimal')
    ax.legend()

    output_path = Path("gap_over_time.png")
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to: {output_path}")

    plt.close()


def example_6_export_to_html():
    """
    Example 6: Export statistics as HTML tables.

    Shows how to create nicely formatted HTML tables from the parsed data.
    """
    print("\n" + "="*70)
    print("Example 6: Exporting Statistics as HTML Tables")
    print("="*70)

    # Load example log
    example_dir = Path(__file__).parent.parent / "example_logs"
    log_path = example_dir / "98_01.txt"

    if not log_path.exists():
        print(f"Example log not found: {log_path}")
        return

    # Parse log
    with open(log_path) as f:
        parser = LogParser(f.read())
    result = parser.parse()

    # Create HTML report
    html_parts = []
    html_parts.append("<html><head><style>")
    html_parts.append("table { border-collapse: collapse; margin: 20px 0; }")
    html_parts.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
    html_parts.append("th { background-color: #4CAF50; color: white; }")
    html_parts.append("h2 { color: #333; }")
    html_parts.append("</style></head><body>")
    html_parts.append("<h1>CP-SAT Solver Analysis Report</h1>")

    # Solver info
    html_parts.append("<h2>Solver Information</h2>")
    html_parts.append(f"<p><strong>Version:</strong> {result.solver_info.version}</p>")
    html_parts.append(f"<p><strong>Workers:</strong> {result.solver_info.num_workers}</p>")
    html_parts.append(f"<p><strong>Status:</strong> {result.response.status}</p>")

    # Search statistics
    html_parts.append("<h2>Search Statistics</h2>")
    stats_df = result.search_stats.to_dataframe()
    if len(stats_df) > 0:
        html_parts.append(stats_df.head(10).to_html(index=False))

    # Task timing
    html_parts.append("<h2>Top Tasks by Time</h2>")
    timing_df = result.task_timing.to_dataframe()
    if len(timing_df) > 0:
        timing_valid = timing_df[timing_df['time_spent_seconds'].notna()]
        if len(timing_valid) > 0:
            timing_sorted = timing_valid.sort_values('time_spent_seconds', ascending=False)
            html_parts.append(timing_sorted.head(10).to_html(index=False))

    # Objective bounds
    html_parts.append("<h2>Objective Bounds by Subsolver</h2>")
    bounds_df = result.objective_bounds.to_dataframe()
    if len(bounds_df) > 0:
        bounds_sorted = bounds_df.sort_values('num_bounds', ascending=False)
        html_parts.append(bounds_sorted.head(10).to_html(index=False))

    html_parts.append("</body></html>")

    # Write to file
    output_path = Path("solver_report.html")
    with open(output_path, 'w') as f:
        f.write('\n'.join(html_parts))

    print(f"\nHTML report saved to: {output_path}")


if __name__ == "__main__":
    if not PANDAS_AVAILABLE:
        print("Pandas and matplotlib are required to run these examples")
        exit(1)

    print("\n" + "="*70)
    print("CP-SAT Log Analysis Examples")
    print("="*70)

    # Run all examples
    example_1_plot_convergence()
    example_2_analyze_presolve()
    example_3_subsolver_performance()
    example_4_task_timing_breakdown()
    example_5_gap_over_time()
    example_6_export_to_html()

    print("\n" + "="*70)
    print("All examples completed successfully!")
    print("="*70)
