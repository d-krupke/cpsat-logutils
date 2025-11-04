"""
Example demonstrating how to parse CP-SAT logs and export to JSON
for consumption by JavaScript frontends and other tools.
"""
import json
from cpsat_logutils import log_to_dict, log_to_json, LogParser

# Example CP-SAT log (truncated for brevity)
EXAMPLE_LOG = """
Starting CP-SAT solver v9.7.2996
Parameters: log_search_progress: true
Setting number of workers to 16

Initial optimization model '': (model_fingerprint: 0x68818998b4c0a611)
#Variables: 1000 (#bools: 1000 in objective)
  - 1000 Booleans in [0,1]
#kLinearN: 100 (#terms: 5000)

Starting presolve at 0.03s

Presolve summary:
  - 0 affine relations were detected.
  - rule 'presolve: iteration' was applied 3 times.

Presolved optimization model '': (model_fingerprint: 0x301e2e572c48f057)
#Variables: 980 (#bools: 980 in objective)
  - 980 Booleans in [0,1]
#kLinearN: 95 (#terms: 4900)

Starting search at 1.5s with 16 workers.
10 full problem subsolvers: [core, default_lp, max_lp, no_lp]
#1      2.0s best:100   next:[101,500] no_lp fixed_bools:0/980
#Bound  2.5s best:100   next:[101,300] max_lp initial_propagation
#2      3.0s best:150   next:[151,300] rnd_cst_lns(d=0.12)
#Bound  3.5s best:150   next:[151,200] max_lp
#3      4.0s best:180   next:[181,200] graph_var_lns(d=0.15)

CpSolverResponse
status: FEASIBLE
objective: 180
best_bound: 181
num_booleans: 980
num_conflicts: 5000
num_branches: 10000
wall_time: 4.5
user_time: 4.2
"""


def example_1_simple_dict_export():
    """Example 1: Simple conversion to dictionary."""
    print("=" * 60)
    print("Example 1: Convert log to dictionary")
    print("=" * 60)

    result = log_to_dict(EXAMPLE_LOG)

    print(f"Solver version: {result['solver_info']['version']}")
    print(f"Number of workers: {result['solver_info']['num_workers']}")
    print(f"Number of solutions found: {result['search_progress']['num_solutions']}")
    print(f"Final objective: {result['search_progress']['final_objective']}")
    print(f"Final bound: {result['search_progress']['final_bound']}")
    print(f"Final gap: {result['search_progress']['final_gap']:.2f}%")
    print(f"Solver status: {result['solver_response']['status']}")
    print()


def example_2_json_export():
    """Example 2: Export to JSON string."""
    print("=" * 60)
    print("Example 2: Convert log to JSON string")
    print("=" * 60)

    json_str = log_to_json(EXAMPLE_LOG, indent=2)
    print("JSON output (truncated):")
    print(json_str[:500] + "...")
    print()


def example_3_detailed_event_analysis():
    """Example 3: Detailed analysis of search events."""
    print("=" * 60)
    print("Example 3: Detailed event analysis")
    print("=" * 60)

    parser = LogParser(EXAMPLE_LOG)

    # Get search progress block and convert to model
    from cpsat_logutils.blocks import SearchProgressBlock
    search_block = parser.get_block_of_type(SearchProgressBlock)
    search_progress = search_block.to_model()

    print(f"Presolve time: {search_progress.presolve_time:.2f}s")
    print(f"Total events: {len(search_progress.events)}")
    print(f"Solution events: {search_progress.num_solutions}")
    print(f"Bound update events: {search_progress.num_bound_updates}")
    print(f"Model update events: {search_progress.num_model_updates}")
    print()

    print("Event timeline:")
    for i, event in enumerate(search_progress.events[:5]):  # Show first 5 events
        event_type = type(event).__name__
        if event_type == "ObjEvent":
            print(f"  [{event.time:.2f}s] Solution #{i+1}: obj={event.obj}, gap={event.gap:.2f}%")
        elif event_type == "BoundEvent":
            print(f"  [{event.time:.2f}s] Bound update: bound={event.bound}")
        elif event_type == "ModelEvent":
            print(f"  [{event.time:.2f}s] Model update: {event.vars_fixed}/{event.vars} vars fixed")
    print()


def example_4_json_schema_export():
    """Example 4: Export JSON schemas for TypeScript/OpenAPI."""
    print("=" * 60)
    print("Example 4: Export JSON schemas")
    print("=" * 60)

    from cpsat_logutils import SolverInfo, SearchProgress, SolverResponse

    # Generate JSON schemas
    solver_info_schema = SolverInfo.model_json_schema()
    search_progress_schema = SearchProgress.model_json_schema()
    solver_response_schema = SolverResponse.model_json_schema()

    print("SolverInfo schema (truncated):")
    print(json.dumps(solver_info_schema, indent=2)[:400] + "...")
    print()

    print("These schemas can be used to:")
    print("  - Generate TypeScript interfaces")
    print("  - Validate data in JavaScript/Python")
    print("  - Auto-generate API documentation")
    print("  - Create form validation schemas")
    print()


def example_5_frontend_integration():
    """Example 5: How to use in a web frontend."""
    print("=" * 60)
    print("Example 5: Frontend integration example")
    print("=" * 60)

    # Convert to JSON for frontend
    data = log_to_dict(EXAMPLE_LOG)

    # Example of what you'd send to frontend
    frontend_payload = {
        "solver": {
            "version": data["solver_info"]["version"],
            "workers": data["solver_info"]["num_workers"]
        },
        "results": {
            "status": data["solver_response"]["status"],
            "objective": data["search_progress"]["final_objective"],
            "bound": data["search_progress"]["final_bound"],
            "gap": data["search_progress"]["final_gap"]
        },
        "timeline": [
            {
                "time": event["time"],
                "type": "solution" if "obj" in event else "bound",
                "value": event.get("obj") or event.get("bound"),
                "message": event["msg"]
            }
            for event in data["search_progress"]["events"]
        ]
    }

    print("Payload ready for frontend:")
    print(json.dumps(frontend_payload, indent=2))
    print()

    print("Example React/Vue.js usage:")
    print("""
    // JavaScript/TypeScript example
    const data = await fetch('/api/solve-log').then(r => r.json());

    // Display solver info
    console.log(`Solver: ${data.solver.version}`);
    console.log(`Workers: ${data.solver.workers}`);

    // Display results
    console.log(`Status: ${data.results.status}`);
    console.log(`Objective: ${data.results.objective}`);
    console.log(`Gap: ${data.results.gap.toFixed(2)}%`);

    // Plot timeline
    const chart = new Chart(ctx, {
        data: data.timeline.map(e => ({x: e.time, y: e.value}))
    });
    """)
    print()


def main():
    """Run all examples."""
    example_1_simple_dict_export()
    example_2_json_export()
    example_3_detailed_event_analysis()
    example_4_json_schema_export()
    example_5_frontend_integration()

    print("=" * 60)
    print("Key Benefits of Pydantic Models:")
    print("=" * 60)
    print("✓ Type-safe data structures with validation")
    print("✓ Automatic JSON serialization/deserialization")
    print("✓ JSON Schema generation for TypeScript/OpenAPI")
    print("✓ Computed fields for derived metrics")
    print("✓ IDE auto-completion and type hints")
    print("✓ Easy integration with web frameworks (FastAPI, Flask, etc.)")
    print("✓ Frontend-friendly JSON format")
    print()


if __name__ == "__main__":
    main()
