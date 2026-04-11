"""Terminal entrypoint for the FanDraGen demo."""

from __future__ import annotations

import argparse
import json

from utils.file_utils import read_yaml
from utils.logging_utils import summarize_logs
from utils.trace_utils import build_trace_snapshot
from workflows.orchestrator import WorkflowOrchestrator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the FanDraGen NBA demo in mocked mode.")
    parser.add_argument("--prompt", help="Run a custom prompt.")
    parser.add_argument("--sample", type=int, default=None, help="Run one of the configured sample prompts by index.")
    return parser.parse_args()


def main() -> None:
    config = read_yaml(__import__("pathlib").Path("configs/default_config.yaml"))
    prompts = config["demo"]["prompts"]
    args = parse_args()
    if args.prompt:
        query = args.prompt
    elif args.sample is not None:
        query = prompts[args.sample]
    else:
        query = prompts[config["demo"]["default_prompt_index"]]

    orchestrator = WorkflowOrchestrator()
    state = orchestrator.run(query)

    print("=== Query ===")
    print(query)
    print("\n=== Trace Snapshot ===")
    print(json.dumps(build_trace_snapshot(state), indent=2))
    print("\n=== Log Summary ===")
    print(summarize_logs(state))
    print("\n=== Final JSON ===")
    print(json.dumps(state.final_delivery_payload.json_payload if state.final_delivery_payload else {}, indent=2))
    print("\n=== Markdown Response ===")
    print(state.final_delivery_payload.markdown_summary if state.final_delivery_payload else "No final response.")


if __name__ == "__main__":
    main()
