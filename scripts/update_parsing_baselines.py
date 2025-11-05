#!/usr/bin/env python3
"""
Update parsing baseline JSON files for all example logs.

Use this script when you've made intentional changes to the parser
that affect the output format.
"""

from pathlib import Path
from cpsat_logutils import LogParser

def main():
    project_root = Path(__file__).parent.parent
    example_dir = project_root / "example_logs"
    output_dir = example_dir / "parsed_json"

    output_dir.mkdir(exist_ok=True)

    print("Updating parsing baselines...")
    print("=" * 70)

    updated = 0
    errors = 0

    for log_file in sorted(example_dir.glob("*.txt")):
        print(f"Processing {log_file.name}...", end=" ")

        try:
            with open(log_file) as f:
                content = f.read()

            parser = LogParser(content)
            result = parser.parse()

            # Save as JSON
            output_file = output_dir / f"{log_file.stem}.json"
            with open(output_file, 'w') as f:
                f.write(result.model_dump_json(indent=2))

            print(f"✓")
            updated += 1

        except Exception as e:
            print(f"✗ Error: {e}")
            errors += 1

    print("=" * 70)
    print(f"Updated: {updated} files")
    if errors:
        print(f"Errors: {errors} files")
    print("\nBaselines updated successfully!")
    print("Run tests to verify: pytest tests/test_parsing_regression.py")

if __name__ == "__main__":
    main()
