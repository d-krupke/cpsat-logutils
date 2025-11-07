"""
Comprehensive tests for the Pydantic-based parser.

These tests verify that important values are properly parsed from various
CP-SAT log formats, including different versions and variations.
"""

import os
import json
import pytest
from cpsat_logutils.parser import LogParser
from cpsat_logutils.models import CPSATLog
from cpsat_logutils.parsers import (
    SolverInfoParser,
    InitialModelParser,
    PresolvedModelParser,
    PresolveLogParser,
    PresolveSummaryParser,
    SearchInfoParser,
    SearchEventsParser,
    SearchStatsParser,
    SolutionRepositoriesParser,
    ObjectiveBoundsParser,
    ResponseParser,
)


EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../example_logs")


def get_example_files():
    """Get all example log files."""
    files = []
    for file in os.listdir(EXAMPLE_DIR):
        if file.endswith(".txt"):
            files.append(os.path.join(EXAMPLE_DIR, file))
    return sorted(files)


class TestParserBasics:
    """Test basic parser functionality."""

    def test_parser_initialization_with_string(self):
        """Test parser can be initialized with a string."""
        log_content = "Starting CP-SAT solver v9.8.3296"
        parser = LogParser(log_content)
        assert len(parser.lines) >= 1
        assert parser.lines[0] == "Starting CP-SAT solver v9.8.3296"

    def test_parser_initialization_with_list(self):
        """Test parser can be initialized with a list of lines."""
        log_lines = ["Starting CP-SAT solver v9.8.3296", "Parameters: log_search_progress: true"]
        parser = LogParser(log_lines)
        assert len(parser.lines) == 2

    def test_parse_returns_cpsat_log(self):
        """Test that parse() returns a CPSATLog instance."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true
Setting number of workers to 8

CpSolverResponse summary:
status: OPTIMAL
"""
        parser = LogParser(log_content)
        result = parser.parse()
        assert isinstance(result, CPSATLog)
        assert result.solver_info.version == "9.8.3296"


class TestSolverInfo:
    """Test solver information parsing."""

    def test_parse_version(self):
        """Test version parsing."""
        log_content = "Starting CP-SAT solver v9.8.3296\n"
        lines = log_content.split("\n")
        component = SolverInfoParser(lines)
        solver_info = component.parse()
        assert solver_info.version == "9.8.3296"

    def test_parse_version_without_v_prefix(self):
        """Test version parsing without 'v' prefix."""
        log_content = "Starting CP-SAT solver 9.8.3296\n"
        lines = log_content.split("\n")
        component = SolverInfoParser(lines)
        solver_info = component.parse()
        assert solver_info.version == "9.8.3296"

    def test_parse_parameters(self):
        """Test parameters parsing."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: max_time_in_seconds: 90 log_search_progress: true relative_gap_limit: 0.25
"""
        lines = log_content.split("\n")
        component = SolverInfoParser(lines)
        solver_info = component.parse()
        assert solver_info.parameters["max_time_in_seconds"] == 90
        assert solver_info.parameters["log_search_progress"] is True
        assert solver_info.parameters["relative_gap_limit"] == 0.25

    def test_parse_num_workers(self):
        """Test number of workers parsing."""
        log_content = """Starting CP-SAT solver v9.8.3296
Setting number of workers to 24
"""
        lines = log_content.split("\n")
        component = SolverInfoParser(lines)
        solver_info = component.parse()
        assert solver_info.num_workers == 24


class TestModelStatistics:
    """Test model statistics parsing."""

    def test_parse_initial_optimization_model(self):
        """Test parsing initial optimization model."""
        log_content = """Initial optimization model '': (model_fingerprint: 0xa2a90169c5e94a12)
#Variables: 10'000 (#bools: 9'900 in objective)
  - 9'900 Booleans in [0,1]
  - 100 in [0,99]
#kExactlyOne: 200 (#literals: 19'800)
#kLinear1: 1
#kLinear2: 9'801 (#enforced: 9'801)
"""
        lines = log_content.split("\n")
        component = InitialModelParser(lines)
        model = component.parse()

        assert model is not None
        assert model.is_optimization is True
        assert model.cpsat_model_fingerprint == "0xa2a90169c5e94a12"
        assert model.num_variables == 10000
        assert model.num_booleans_in_objective == 9900
        assert len(model.variable_domains.domains) == 2
        assert model.variable_domains.domains[0].count == 9900
        assert model.variable_domains.domains[0].type == "Booleans"
        assert len(model.constraints) == 3

    def test_parse_initial_satisfaction_model(self):
        """Test parsing initial satisfaction model."""
        log_content = """Initial satisfaction model '': (model_fingerprint: 0xbc34aec982cbd687)
#Variables: 560
  - 468 Booleans in [0,1]
  - 39 in [0,20]
"""
        lines = log_content.split("\n")
        component = InitialModelParser(lines)
        model = component.parse()

        assert model is not None
        assert model.is_optimization is False
        assert model.num_variables == 560

    def test_parse_presolved_model(self):
        """Test parsing presolved model."""
        log_content = """Presolved optimization model '': (model_fingerprint: 0x76bff0c14238d173)
#Variables: 9'999 (#bools: 9'740 in objective)
  - 9'900 Booleans in [0,1]
  - 99 in [1,99]
#kBoolAnd: 9'702 (#enforced: 9'702) (#literals: 19'404)
"""
        lines = log_content.split("\n")
        component = PresolvedModelParser(lines)
        model = component.parse()

        assert model is not None
        assert model.is_optimization is True
        assert model.num_variables == 9999
        assert model.num_booleans_in_objective == 9740


class TestPresolve:
    """Test presolve parsing."""

    def test_parse_presolve_entries(self):
        """Test parsing presolve log entries."""
        log_content = """Starting presolve at 0.00s
  2.30e-03s  0.00e+00d  [DetectDominanceRelations]
  1.90e-02s  0.00e+00d  [PresolveToFixPoint] #num_loops=2 #num_dual_strengthening=1

Presolve summary:
"""
        lines = log_content.split("\n")
        component = PresolveLogParser(lines)
        entries = component.parse()

        assert len(entries) >= 2
        assert entries[0].operation == "DetectDominanceRelations"
        assert entries[0].wall_time == 0.0023
        assert entries[1].operation == "PresolveToFixPoint"
        assert entries[1].details.get("num_loops") == 2

    def test_parse_presolve_summary(self):
        """Test parsing presolve summary."""
        log_content = """Presolve summary:
  - 0 affine relations were detected.
  - rule 'deductions: 19503 stored' was applied 1 time.
  - rule 'exactly_one: simplified objective' was applied 136 times.
  - rule 'linear: empty' was applied 1 time.
"""
        lines = log_content.split("\n")
        component = PresolveSummaryParser(lines)
        summary = component.parse()

        assert summary is not None
        assert summary.affine_relations == 0
        assert summary.rules_applied["deductions: 19503 stored"] == 1
        assert summary.rules_applied["exactly_one: simplified objective"] == 136


class TestSearchInfo:
    """Test search information parsing."""

    def test_parse_search_info_parallel(self):
        """Test parsing parallel search information."""
        log_content = """Starting search at 0.68s with 24 workers.
15 full problem subsolvers: [core, default_lp, lb_tree_search]
7 first solution subsolvers: [fj_long_default, fj_short_default]
10 incomplete subsolvers: [feasibility_pump, graph_arc_lns]
3 helper subsolvers: [neighborhood_helper, synchronization_agent]
"""
        lines = log_content.split("\n")
        component = SearchInfoParser(lines)
        search_info = component.parse()

        assert search_info is not None
        assert search_info.start_time == 0.68
        assert search_info.num_workers == 24
        assert search_info.search_type == "parallel"
        assert len(search_info.subsolvers.full_problem) == 3
        assert "core" in search_info.subsolvers.full_problem

    def test_parse_search_info_sequential(self):
        """Test parsing sequential search information."""
        log_content = """Starting sequential search at 0.01s
"""
        lines = log_content.split("\n")
        component = SearchInfoParser(lines)
        search_info = component.parse()

        # Sequential search may not parse workers the same way
        # This is just to ensure no crashes
        assert search_info is None or search_info.search_type == "sequential"


class TestSearchEvents:
    """Test search event parsing."""

    def test_parse_bound_event(self):
        """Test parsing bound events."""
        log_content = "Starting search at 0.68s with 24 workers.\n#Bound   0.73s best:inf   next:[48676021,3.15794931e+11] objective_shaving_search_no_lp (vars=9999 csts=19704)"
        lines = log_content.split("\n")
        component = SearchEventsParser(lines)
        events = component.parse()

        assert len(events) >= 1
        bound_event = events[0]
        assert bound_event.event_type == "bound"
        assert bound_event.time == 0.73
        assert bound_event.best_objective is None  # inf
        assert bound_event.next_min == 48676021
        assert bound_event.proven_bound == 48676021  # For minimization with no solution yet
        assert "objective_shaving_search_no_lp" in bound_event.subsolver

    def test_parse_objective_event(self):
        """Test parsing objective events."""
        log_content = "Starting search at 0.68s with 24 workers.\n#1       1.52s best:3.15168966e+09 next:[65445416,3.15168966e+09] quick_restart_no_lp (fixed_bools=0/9999)\n#2       1.59s best:2.03193872e+09 next:[65445416,2.03193872e+09] core (fixed_bools=0/10035)"
        lines = log_content.split("\n")
        component = SearchEventsParser(lines)
        events = component.parse()

        assert len(events) >= 2
        obj_event1 = events[0]
        assert obj_event1.event_type == "objective"
        assert obj_event1.solution_number == 1
        assert obj_event1.time == 1.52
        assert abs(obj_event1.objective - 3.15168966e+09) < 1e6
        assert "quick_restart_no_lp" in obj_event1.subsolver

    def test_parse_model_event(self):
        """Test parsing model events."""
        log_content = "Starting search at 0.68s with 24 workers.\n#Model   4.63s var:9993/9999 constraints:19691/19703\n#Model   4.74s var:9987/9999 constraints:19679/19703"
        lines = log_content.split("\n")
        component = SearchEventsParser(lines)
        events = component.parse()

        assert len(events) >= 2
        model_event = events[0]
        assert model_event.event_type == "model"
        assert model_event.time == 4.63
        assert model_event.vars_remaining == 9993
        assert model_event.vars_total == 9999
        assert model_event.constraints_remaining == 19691
        assert model_event.constraints_total == 19703


class TestStatistics:
    """Test statistics parsing."""

    def test_parse_search_stats(self):
        """Test parsing search statistics."""
        log_content = """Search stats    Bools  Conflicts   Branches  Restarts  BoolPropag  IntegerPropag
    'default':    642    918'873  1'780'404       944  65'749'379     36'871'867
"""
        lines = log_content.split("\n")
        component = SearchStatsParser(lines)
        stats = component.parse()

        assert len(stats) == 1
        assert stats[0].subsolver == "default"
        assert stats[0].booleans == 642
        assert stats[0].conflicts == 918873
        assert stats[0].branches == 1780404

    def test_parse_solution_repositories(self):
        """Test parsing solution repositories."""
        log_content = """Solution repositories    Added  Queried  Ignored  Synchro
  'feasible solutions':    222      731        0      209
        'lp solutions':     42        0        0       37
"""
        lines = log_content.split("\n")
        component = SolutionRepositoriesParser(lines)
        repos = component.parse()

        assert repos is not None
        assert "feasible solutions" in repos.repositories
        assert repos.repositories["feasible solutions"]["added"] == 222
        assert repos.repositories["feasible solutions"]["synchro"] == 209

    def test_parse_objective_bounds(self):
        """Test parsing objective bounds."""
        log_content = """Objective bounds                      Num
                     'am1_presolve':    1
                   'initial_domain':    1
                           'max_lp':    6
"""
        lines = log_content.split("\n")
        component = ObjectiveBoundsParser(lines)
        bounds = component.parse()

        assert len(bounds) == 3
        assert bounds[0].subsolver == "am1_presolve"
        assert bounds[0].num_bounds == 1
        assert bounds[2].subsolver == "max_lp"
        assert bounds[2].num_bounds == 6


class TestResponse:
    """Test response parsing."""

    def test_parse_response_optimal(self):
        """Test parsing optimal response."""
        log_content = """CpSolverResponse summary:
status: OPTIMAL
objective: 91326902
best_bound: 68751309
integers: 9939
booleans: 9999
conflicts: 0
branches: 23607
propagations: 2000795
integer_propagations: 2016550
restarts: 19998
lp_iterations: 0
walltime: 13.017
usertime: 13.017
deterministic_time: 65.5825
gap_integral: 1167.26
solution_fingerprint: 0x3f5c435d9453c6d6
"""
        lines = log_content.split("\n")
        component = ResponseParser(lines)
        response = component.parse()

        assert response.status == "OPTIMAL"
        assert response.objective == 91326902
        assert response.best_bound == 68751309
        assert response.num_integers == 9939
        assert response.num_booleans == 9999
        assert response.walltime == 13.017
        assert response.solution_fingerprint == "0x3f5c435d9453c6d6"

    def test_parse_response_unknown(self):
        """Test parsing unknown status response."""
        log_content = """CpSolverResponse summary:
status: UNKNOWN
objective: NA
best_bound: NA
"""
        lines = log_content.split("\n")
        component = ResponseParser(lines)
        response = component.parse()

        assert response.status == "UNKNOWN"
        assert response.objective is None
        assert response.best_bound is None


class TestExampleLogs:
    """Test parsing all example logs."""

    @pytest.mark.parametrize("log_file", get_example_files())
    def test_parse_example_log(self, log_file):
        """Test that each example log can be parsed without errors."""
        with open(log_file, "r") as f:
            log_content = f.read()

        parser = LogParser(log_content)
        result = parser.parse()

        # Basic assertions that should hold for all logs
        assert isinstance(result, CPSATLog)
        assert result.solver_info is not None
        assert result.solver_info.version is not None
        assert result.response is not None
        assert result.response.status is not None

        # Log should be JSON-serializable
        json_str = result.model_dump_json()
        assert len(json_str) > 0

        # Should be able to reconstruct from JSON
        reconstructed = CPSATLog.model_validate_json(json_str)
        assert reconstructed.solver_info.version == result.solver_info.version

    @pytest.mark.parametrize("log_file", get_example_files())
    def test_important_values_parsed(self, log_file):
        """Test that important values are properly extracted."""
        with open(log_file, "r") as f:
            log_content = f.read()

        parser = LogParser(log_content)
        result = parser.parse()

        # Version should be parsed
        assert result.solver_info.version != "unknown"

        # If model exists, should have some statistics
        if result.initial_model is not None:
            assert result.initial_model.num_variables is not None or len(result.initial_model.variable_domains.domains) > 0

        # Response should have status
        assert result.response.status in [
            "OPTIMAL",
            "FEASIBLE",
            "INFEASIBLE",
            "UNKNOWN",
            "MODEL_INVALID",
        ]

        # If search happened, should have some events or stats
        if result.search_info is not None:
            assert len(result.search_events.events) > 0 or len(result.search_stats.entries) > 0


class TestJSONSerialization:
    """Test JSON serialization for frontend use."""

    def test_full_log_serialization(self):
        """Test that a full log can be serialized to JSON."""
        log_file = get_example_files()[0]
        with open(log_file, "r") as f:
            log_content = f.read()

        parser = LogParser(log_content)
        result = parser.parse()

        # Serialize to JSON
        json_data = result.model_dump()
        assert isinstance(json_data, dict)
        assert "solver_info" in json_data
        assert "response" in json_data

        # JSON string should be valid
        json_str = result.model_dump_json(indent=2)
        assert len(json_str) > 100

        # Should be able to parse back
        parsed_back = json.loads(json_str)
        assert parsed_back["solver_info"]["version"] == result.solver_info.version

    def test_search_events_in_json(self):
        """Test that search events are properly represented in JSON."""
        log_content = """Starting CP-SAT solver v9.8.3296
Starting search at 0.68s with 24 workers.
#1       1.52s best:100 next:[10,100] quick_restart
#Bound   1.90s best:100 next:[20,100] max_lp

CpSolverResponse summary:
status: OPTIMAL
"""
        parser = LogParser(log_content)
        result = parser.parse()

        json_data = result.model_dump()
        search_events = json_data["search_events"]
        # search_events is now a dict with "events" key due to wrapper
        events = search_events["events"]

        assert len(events) >= 2
        # Events should have discriminator field
        assert events[0]["event_type"] in ["objective", "bound"]


class TestRobustness:
    """Test parser robustness to variations."""

    def test_handles_missing_sections(self):
        """Test parser handles logs with missing sections."""
        log_content = """Starting CP-SAT solver v9.8.3296

CpSolverResponse summary:
status: OPTIMAL
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.solver_info.version == "9.8.3296"
        assert result.initial_model is None
        assert result.search_info is None
        assert result.response.status == "OPTIMAL"

    def test_handles_extra_whitespace(self):
        """Test parser handles extra whitespace."""
        log_content = """Starting CP-SAT solver v9.8.3296


Parameters: log_search_progress: true


CpSolverResponse summary:
status: OPTIMAL
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.solver_info.version == "9.8.3296"
        assert result.solver_info.parameters["log_search_progress"] is True

    def test_handles_comments(self):
        """Test parser extracts comments."""
        log_content = """// This is a comment
// Another comment
Starting CP-SAT solver v9.8.3296

CpSolverResponse summary:
status: OPTIMAL
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert len(result.comments) == 2
        assert result.comments[0] == "This is a comment"
        assert result.comments[1] == "Another comment"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
