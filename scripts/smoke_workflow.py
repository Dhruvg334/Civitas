"""Manual safe API smoke path for a local Civitas runtime."""

from __future__ import annotations

import argparse
import json
from urllib.request import Request, urlopen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report_id")
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", required=True, help="Bearer token (never printed)")
    args = parser.parse_args()
    request = Request(
        f"{args.base_url.rstrip('/')}/api/v1/reports/{args.report_id}/workflow",
        method="POST",
        headers={"Authorization": f"Bearer {args.token}", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            data = json.loads(response.read())
    except Exception as exc:  # noqa: BLE001
        print(f"workflow smoke failed: {type(exc).__name__}")
        return 1
    safe = data.get("data", {})
    print(
        {
            key: safe.get(key)
            for key in ("workflow_id", "trace_id", "status", "interrupt_type", "state")
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
