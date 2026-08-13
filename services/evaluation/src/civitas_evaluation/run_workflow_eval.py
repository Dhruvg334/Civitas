from __future__ import annotations

import argparse
from pathlib import Path

from civitas_evaluation.workflow_eval import write_results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["offline"], default="offline")
    parser.add_argument(
        "--output", type=Path, default=Path("services/evaluation/results/workflow")
    )
    args = parser.parse_args()
    write_results(args.output)
    print(f"offline deterministic workflow evaluation written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
