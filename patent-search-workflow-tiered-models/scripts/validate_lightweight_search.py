from __future__ import annotations

import argparse
import sys
from pathlib import Path

import validate_model_orchestration as validator


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate quick/standard patent-search handoffs")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    errors: list[str] = []
    profile = validator.lightweight_profile(args.run_dir.resolve(), errors)
    if profile is None:
        errors.append("run_dir is not a quick/standard lightweight search profile")
    else:
        validator.validate_lightweight_runtime(args.run_dir.resolve(), errors)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print(f"Lightweight {profile} search checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
