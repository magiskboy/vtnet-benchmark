#!/usr/bin/env python3
"""CLI: compare multi-config LLM benchmark results and generate summary + plots."""
import argparse
import json
import os
import sys

from bench_analysis import analyze_configs, print_markdown_table, save_plots, save_summary


def default_project_root() -> str:
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze & compare LLM benchmark configs")
    parser.add_argument(
        "--project-root",
        default=default_project_root(),
        help="Repository root; config dir paths are relative to this (default: parent of bench-analysis/)",
    )
    parser.add_argument(
        "--config",
        required=True,
        help="JSON file with title, configs[] (dir relative to project root), and optional colors{}",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for summary.json and images/ (default: bench-analysis/output/<config-stem>)",
    )
    args = parser.parse_args()

    project_root = os.path.abspath(args.project_root)
    config_path = os.path.abspath(args.config)
    output_dir = os.path.abspath(
        args.output_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "output",
            os.path.splitext(os.path.basename(config_path))[0],
        )
    )
    with open(config_path) as f:
        cfg = json.load(f)

    os.makedirs(output_dir, exist_ok=True)
    rows = analyze_configs(project_root, cfg["configs"])
    print_markdown_table(rows)
    summary_path = save_summary(rows, output_dir)
    plot_paths = save_plots(rows, output_dir, cfg.get("title", "Benchmark"), cfg.get("colors"))
    print(f"\nSaved {summary_path}")
    print("Saved images/:", ", ".join(os.path.basename(p) for p in plot_paths))
    return 0


if __name__ == "__main__":
    sys.exit(main())
