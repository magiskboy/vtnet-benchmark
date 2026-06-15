from __future__ import annotations

import json
import os
import re


def resolve_config_dir(project_root: str, dir_path: str) -> str:
    if os.path.isabs(dir_path):
        return dir_path
    return os.path.join(project_root, dir_path)


def load_multi_turn_stats(project_root: str, config_dir: str) -> list[dict]:
    path = os.path.join(resolve_config_dir(project_root, config_dir), "perf", "multi_turn_stats.json")
    with open(path) as f:
        return json.load(f)


def load_runtime_rps(project_root: str, config_dir: str) -> tuple[float, float]:
    path = os.path.join(resolve_config_dir(project_root, config_dir), "perf", "load_test.log")
    with open(path) as f:
        log = f.read()
    runtime = float(re.search(r"runtime_sec = ([\d.]+)", log).group(1))
    rps = float(re.search(r"requests_per_sec = ([\d.]+)", log).group(1))
    return runtime, rps
