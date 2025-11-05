"""
Tests for incomplete log handling and line references.

These tests verify that the parser correctly identifies incomplete logs
and provides line references for each semantic block.
"""

import pytest
from cpsat_logutils.parser import LogParser


class TestIncompleteLogDetection:
    """Test that incomplete logs are properly detected."""

    def test_complete_log(self):
        """Test that a complete log is marked as complete."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true
Setting number of workers to 24

CpSolverResponse summary:
status: OPTIMAL
objective: 100
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.is_complete is True
        assert result.metadata.has_solver_info is True
        assert result.metadata.has_response is True
        assert len(result.metadata.missing_sections) == 0

    def test_incomplete_log_missing_start(self):
        """Test log without solver info (missing start)."""
        log_content = """Some random log lines
without proper header

CpSolverResponse summary:
status: OPTIMAL
objective: 100
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.is_complete is False
        assert result.metadata.has_solver_info is False
        assert result.metadata.has_response is True
        assert "solver_info (log start)" in result.metadata.missing_sections

    def test_incomplete_log_missing_end(self):
        """Test log without response (missing end)."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true
Setting number of workers to 24

Some log content but no response section
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.is_complete is False
        assert result.metadata.has_solver_info is True
        assert result.metadata.has_response is False
        assert "response (log end)" in result.metadata.missing_sections

    def test_incomplete_log_missing_both(self):
        """Test log without solver info or response."""
        log_content = """Some random log content
without header or footer
just middle stuff
"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.is_complete is False
        assert result.metadata.has_solver_info is False
        assert result.metadata.has_response is False
        assert len(result.metadata.missing_sections) == 2

    def test_truncated_log(self):
        """Test log that appears to be truncated mid-execution."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true

Initial optimization model '':
#Variables: 10000
#Constraints: 5000

Starting search at 0.5s with 8 workers
#1 0.7s best:1000 next:[900,1000] (solver_name)
#2 0.8s best:950 next:[900,950] (solver_name)
"""
        # Log ends abruptly without response
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.is_complete is False
        assert result.metadata.has_solver_info is True
        assert result.metadata.has_response is False
        assert result.solver_info.version == "9.8.3296"
        # Should have parsed initial model even though log is incomplete
        assert result.initial_model is not None
        assert result.initial_model.num_variables == 10000


class TestLineReferences:
    """Test that line references are correctly tracked."""

    def test_line_references_present(self):
        """Test that line references are recorded for parsed sections."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true
Setting number of workers to 24

CpSolverResponse summary:
status: OPTIMAL
objective: 100
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Should have line references
        assert len(result.metadata.line_references) > 0

        # Check that we have references for key sections
        section_names = [ref.section_name for ref in result.metadata.line_references]
        assert "SolverInfo" in section_names
        assert "Response" in section_names

    def test_line_references_sorted(self):
        """Test that line references are sorted by start line."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true

CpSolverResponse summary:
status: OPTIMAL
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Line references should be sorted by start_line
        refs = result.metadata.line_references
        for i in range(len(refs) - 1):
            assert refs[i].start_line <= refs[i + 1].start_line

    def test_line_references_match_content(self):
        """Test that line references point to correct content."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true
Setting number of workers to 24

CpSolverResponse summary:
status: OPTIMAL
objective: 100
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Find the solver info reference
        solver_refs = [
            ref for ref in result.metadata.line_references
            if ref.section_name == "SolverInfo"
        ]
        assert len(solver_refs) > 0

        # Check that the referenced lines contain expected content
        lines = log_content.split("\n")
        for ref in solver_refs:
            line_content = lines[ref.start_line]
            # Should contain solver-related content
            assert any(keyword in line_content.lower() for keyword in
                      ["starting", "parameters", "workers"])

    def test_line_references_with_field_names(self):
        """Test that line references have correct field names."""
        log_content = """Starting CP-SAT solver v9.8.3296
Parameters: log_search_progress: true

CpSolverResponse summary:
status: OPTIMAL
walltime: 1.5
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Check that field names are set
        for ref in result.metadata.line_references:
            assert ref.field_name is not None
            assert isinstance(ref.field_name, str)

        # Check specific field names
        field_names = [ref.field_name for ref in result.metadata.line_references]
        assert "solver_info" in field_names
        assert "response" in field_names

    def test_metadata_total_lines(self):
        """Test that total_lines is correctly reported."""
        log_content = """Line 1
Line 2
Line 3
Line 4
Line 5"""
        parser = LogParser(log_content)
        result = parser.parse()

        assert result.metadata.total_lines == 5


class TestIncompleteLogUseCases:
    """Test practical use cases with incomplete logs."""

    def test_parse_while_solving(self):
        """Simulate parsing a log file while solver is still running."""
        # This is like reading a log file that's still being written to
        log_content = """Starting CP-SAT solver v9.10.4010
Parameters: max_time_in_seconds: 300 log_search_progress: true

Initial optimization model 'problem':
#Variables: 50000
#Constraints: 25000

Starting search at 1.2s with 16 workers
"""
        parser = LogParser(log_content)
        result = parser.parse()

        # Should parse successfully even though incomplete
        assert result.metadata.is_complete is False
        assert result.solver_info.version == "9.10.4010"
        assert result.initial_model is not None
        assert result.initial_model.num_variables == 50000

        # Response should be UNKNOWN since solver hasn't finished
        assert result.response.status == "UNKNOWN"

    def test_parse_interrupted_solver(self):
        """Test parsing log from a solver that was killed/interrupted."""
        log_content = """Starting CP-SAT solver v9.9.3963
Parameters: log_search_progress: true

Initial optimization model:
#Variables: 1000
#Constraints: 500

Presolved optimization model:
#Variables: 800
#Constraints: 400

Starting search at 0.5s with 8 workers
"""
        # No response - solver was interrupted
        parser = LogParser(log_content)
        result = parser.parse()

        # Log should be marked incomplete
        assert result.metadata.is_complete is False
        assert "response (log end)" in result.metadata.missing_sections

        # But we should still extract useful information
        assert result.solver_info.version == "9.9.3963"
        assert result.initial_model.num_variables == 1000
        assert result.presolved_model.num_variables == 800


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
