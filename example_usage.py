"""
Example usage of the Pydantic-based CP-SAT log parser.

This script demonstrates how to use the parser to extract structured
data from CP-SAT logs, which can then be easily used in web frontends,
data analysis, or exported to JSON.
"""

from cpsat_logutils import LogParser
import json


def main():
    # Example: Read a log file
    with open("example_logs/98_01.txt", "r") as f:
        log_content = f.read()

    # Parse the log
    parser = LogParser(log_content)
    parsed_log = parser.parse()

    # Access solver information
    print("=" * 60)
    print("SOLVER INFORMATION")
    print("=" * 60)
    print(f"Version: {parsed_log.solver_info.version}")
    print(f"Workers: {parsed_log.solver_info.num_workers}")
    print(f"Parameters: {parsed_log.solver_info.parameters}")
    print()

    # Access model statistics
    if parsed_log.initial_model:
        print("=" * 60)
        print("INITIAL MODEL")
        print("=" * 60)
        print(f"Type: {'Optimization' if parsed_log.initial_model.is_optimization else 'Satisfaction'}")
        print(f"Variables: {parsed_log.initial_model.num_variables}")
        print(f"Booleans in objective: {parsed_log.initial_model.num_booleans_in_objective}")
        print(f"Number of constraint types: {len(parsed_log.initial_model.constraints)}")
        print()

    # Access presolve summary
    if parsed_log.presolve_summary:
        print("=" * 60)
        print("PRESOLVE SUMMARY")
        print("=" * 60)
        print(f"Affine relations: {parsed_log.presolve_summary.affine_relations}")
        print(f"Rules applied: {len(parsed_log.presolve_summary.rules_applied)}")
        print(f"Solved during presolve: {parsed_log.presolve_summary.solved_during_presolve}")
        print()

    # Access search information
    if parsed_log.search_info:
        print("=" * 60)
        print("SEARCH CONFIGURATION")
        print("=" * 60)
        print(f"Start time: {parsed_log.search_info.start_time}s")
        print(f"Workers: {parsed_log.search_info.num_workers}")
        print(f"Search type: {parsed_log.search_info.search_type}")
        print(f"Full problem subsolvers: {len(parsed_log.search_info.subsolvers.full_problem)}")
        print(f"First solution subsolvers: {len(parsed_log.search_info.subsolvers.first_solution)}")
        print(f"Incomplete subsolvers: {len(parsed_log.search_info.subsolvers.incomplete)}")
        print()

    # Access search events
    print("=" * 60)
    print("SEARCH EVENTS")
    print("=" * 60)
    print(f"Total events: {len(parsed_log.search_events)}")

    # Show first few objective improvements
    objective_events = [e for e in parsed_log.search_events if e.event_type == "objective"]
    print(f"Objective improvements: {len(objective_events)}")
    for i, event in enumerate(objective_events[:5]):
        print(f"  #{event.solution_number} at {event.time:.2f}s: "
              f"obj={event.objective:.2e}, gap={event.gap_percent:.2f}% ({event.subsolver})")

    # Show bound improvements
    bound_events = [e for e in parsed_log.search_events if e.event_type == "bound"]
    print(f"Bound improvements: {len(bound_events)}")
    print()

    # Access final response
    print("=" * 60)
    print("FINAL RESPONSE")
    print("=" * 60)
    print(f"Status: {parsed_log.response.status}")
    print(f"Objective: {parsed_log.response.objective}")
    print(f"Best bound: {parsed_log.response.best_bound}")
    print(f"Wall time: {parsed_log.response.walltime}s")
    print(f"Conflicts: {parsed_log.response.conflicts}")
    print(f"Branches: {parsed_log.response.branches}")
    print()

    # Export to JSON for frontend use
    print("=" * 60)
    print("JSON EXPORT")
    print("=" * 60)
    json_data = parsed_log.model_dump_json(indent=2)
    print(f"JSON size: {len(json_data)} bytes")

    # Save to file
    with open("parsed_log.json", "w") as f:
        f.write(json_data)
    print("Saved to: parsed_log.json")
    print()

    # Show a sample of the JSON
    print("Sample JSON structure:")
    json_obj = json.loads(json_data)
    print(json.dumps({
        "solver_info": json_obj["solver_info"],
        "search_events_count": len(json_obj["search_events"]),
        "response": json_obj["response"]
    }, indent=2))


if __name__ == "__main__":
    main()
