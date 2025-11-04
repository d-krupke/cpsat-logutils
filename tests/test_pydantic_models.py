"""
Test the Pydantic models and JSON serialization functionality.
"""
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from cpsat_logutils import (
    LogParser,
    BoundEvent,
    ObjEvent,
    ModelEvent,
    SearchProgress,
    SolverInfo,
    SolverResponse,
    log_to_dict,
    log_to_json,
)
from cpsat_logutils.blocks import SearchProgressBlock, SolverBlock, ResponseBlock

EXAMPLE_DIR = os.path.join(os.path.dirname(__file__), "../example_logs")


def test_solver_info_model():
    """Test that SolverInfo Pydantic model works correctly."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()
        parser = LogParser(log)
        solver_block = parser.get_block_of_type(SolverBlock)

        # Convert to Pydantic model
        solver_info = solver_block.to_model()

        # Verify it's a SolverInfo instance
        assert isinstance(solver_info, SolverInfo)

        # Verify core fields
        assert solver_info.version == "v9.7.2996"
        assert solver_info.version_tuple == (9, 7, 2996)
        assert solver_info.num_workers == 24
        assert "log_search_progress" in solver_info.parameters
        assert solver_info.parameters["log_search_progress"] is True

        # Test JSON serialization
        json_dict = solver_info.model_dump()
        assert json_dict["version"] == "v9.7.2996"
        assert json_dict["num_workers"] == 24

        # Test JSON string conversion
        json_str = solver_info.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["version"] == "v9.7.2996"


def test_search_progress_events():
    """Test that search event models work correctly."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()
        parser = LogParser(log)
        search_block = parser.get_block_of_type(SearchProgressBlock)

        # Get events
        events = search_block.get_events()

        # Verify we have events
        assert len(events) > 0

        # Check ObjEvent
        obj_events = [e for e in events if isinstance(e, ObjEvent)]
        assert len(obj_events) > 0
        first_obj = obj_events[0]
        assert first_obj.time > 0
        assert first_obj.obj >= 0
        assert first_obj.bound >= 0
        assert first_obj.msg is not None

        # Test computed field
        gap = first_obj.gap
        assert isinstance(gap, float)

        # Test JSON serialization
        json_dict = first_obj.model_dump()
        assert "time" in json_dict
        assert "obj" in json_dict
        assert "bound" in json_dict
        assert "msg" in json_dict
        assert "gap" in json_dict

        # Check BoundEvent
        bound_events = [e for e in events if isinstance(e, BoundEvent)]
        assert len(bound_events) > 0
        first_bound = bound_events[0]
        assert first_bound.time > 0
        assert first_bound.bound is not None

        # Test computed fields
        assert first_bound.gap is not None or first_bound.obj is None

        # Check ModelEvent if present
        model_events = [e for e in events if isinstance(e, ModelEvent)]
        if model_events:
            first_model = model_events[0]
            assert first_model.time > 0
            assert first_model.vars > 0
            assert first_model.constr >= 0

            # Test computed fields
            assert first_model.vars_fixed >= 0
            assert 0 <= first_model.vars_fixed_percentage <= 100


def test_search_progress_model():
    """Test that SearchProgress Pydantic model works correctly."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()
        parser = LogParser(log)
        search_block = parser.get_block_of_type(SearchProgressBlock)

        # Convert to Pydantic model
        search_progress = search_block.to_model()

        # Verify it's a SearchProgress instance
        assert isinstance(search_progress, SearchProgress)

        # Verify computed fields
        assert search_progress.num_solutions > 0
        assert search_progress.num_bound_updates >= 0
        assert search_progress.final_objective is not None
        assert search_progress.final_bound is not None

        # Test JSON serialization
        json_dict = search_progress.model_dump()
        assert "presolve_time" in json_dict
        assert "events" in json_dict
        assert len(json_dict["events"]) > 0
        assert "num_solutions" in json_dict
        assert "final_objective" in json_dict


def test_solver_response_model():
    """Test that SolverResponse Pydantic model works correctly."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()
        parser = LogParser(log)
        response_block = parser.get_block_of_type(ResponseBlock)

        # Convert to Pydantic model
        response = response_block.to_model()

        # Verify it's a SolverResponse instance
        assert isinstance(response, SolverResponse)

        # Verify core fields
        assert response.status in ["OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN"]

        # Test JSON serialization
        json_dict = response.model_dump()
        assert "status" in json_dict

        # Test JSON string conversion
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "status" in parsed


def test_log_to_dict():
    """Test the log_to_dict convenience function."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()

        # Convert to dict
        result = log_to_dict(log)

        # Verify structure
        assert isinstance(result, dict)
        assert "solver_info" in result
        assert "search_progress" in result
        assert "solver_response" in result

        # Verify solver info
        assert result["solver_info"]["version"] == "v9.7.2996"
        assert result["solver_info"]["num_workers"] == 24

        # Verify search progress
        assert result["search_progress"]["num_solutions"] > 0
        assert len(result["search_progress"]["events"]) > 0

        # Verify solver response
        assert "status" in result["solver_response"]


def test_log_to_json():
    """Test the log_to_json convenience function."""
    with open(os.path.join(EXAMPLE_DIR, "97_01.txt")) as f:
        log = f.read()

        # Convert to JSON string
        json_str = log_to_json(log)

        # Verify it's valid JSON
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)

        # Verify structure
        assert isinstance(parsed, dict)
        assert "solver_info" in parsed
        assert "search_progress" in parsed
        assert "solver_response" in parsed


def test_multiple_logs():
    """Test that the models work with multiple different logs."""
    for filename in os.listdir(EXAMPLE_DIR):
        if not filename.endswith(".txt"):
            continue

        filepath = os.path.join(EXAMPLE_DIR, filename)
        with open(filepath) as f:
            log = f.read()

            try:
                # Parse and convert to dict
                result = log_to_dict(log)

                # Verify we got some data
                assert isinstance(result, dict)

                # Solver info should always be present
                if "solver_info" in result:
                    assert "version" in result["solver_info"]
                    assert "num_workers" in result["solver_info"]

                # Try to convert to JSON
                json_str = log_to_json(log)
                assert isinstance(json_str, str)

                # Verify it's valid JSON
                parsed = json.loads(json_str)
                assert isinstance(parsed, dict)

                print(f"✓ {filename} passed")

            except Exception as e:
                print(f"✗ {filename} failed: {e}")
                raise


def test_json_schema_generation():
    """Test that Pydantic models can generate JSON schemas."""
    # Test SolverInfo schema
    solver_info_schema = SolverInfo.model_json_schema()
    assert "properties" in solver_info_schema
    assert "version" in solver_info_schema["properties"]
    assert "num_workers" in solver_info_schema["properties"]

    # Test SearchProgress schema
    search_progress_schema = SearchProgress.model_json_schema()
    assert "properties" in search_progress_schema
    assert "presolve_time" in search_progress_schema["properties"]
    assert "events" in search_progress_schema["properties"]

    # Test SolverResponse schema
    solver_response_schema = SolverResponse.model_json_schema()
    assert "properties" in solver_response_schema
    assert "status" in solver_response_schema["properties"]


if __name__ == "__main__":
    # Run tests
    test_solver_info_model()
    print("✓ test_solver_info_model passed")

    test_search_progress_events()
    print("✓ test_search_progress_events passed")

    test_search_progress_model()
    print("✓ test_search_progress_model passed")

    test_solver_response_model()
    print("✓ test_solver_response_model passed")

    test_log_to_dict()
    print("✓ test_log_to_dict passed")

    test_log_to_json()
    print("✓ test_log_to_json passed")

    test_multiple_logs()
    print("✓ test_multiple_logs passed")

    test_json_schema_generation()
    print("✓ test_json_schema_generation passed")

    print("\n🎉 All tests passed!")
