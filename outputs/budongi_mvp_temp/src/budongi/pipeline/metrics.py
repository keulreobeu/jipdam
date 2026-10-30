"""Measure the worker process tree without confusing missing samples with zero."""
from __future__ import annotations

import importlib.metadata
import os
import platform
import subprocess
import time
from pathlib import Path


def environment():
    libraries = {}
    for name in ["openpyxl", "pyarrow", "duckdb", "pandas", "psutil"]:
        try:
            libraries[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            libraries[name] = None
    try:
        import psutil
        ram = psutil.virtual_memory().total
    except (ImportError, OSError):
        ram = None
    return {"python": platform.python_version(), "os": platform.platform(), "machine": platform.machine(),
            "cpu_count": os.cpu_count(), "physical_memory_bytes": ram, "storage_type": "unknown",
            "processor": platform.processor(), "libraries": libraries}


def code_version():
    root = Path(__file__).resolve().parents[5]
    try:
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=5, check=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=5, check=True).stdout)
        return {"commit": commit, "dirty": dirty}
    except (OSError, subprocess.SubprocessError):
        return {"commit": None, "dirty": None}


def observe(process, *, timeout=3600, interval=0.1):
    import psutil
    start, peak, samples, errors = time.perf_counter(), None, 0, 0
    try:
        root = psutil.Process(process.pid)
    except psutil.NoSuchProcess:
        return {"timed_out": False, "peak_rss_bytes": None, "sample_interval_ms": interval * 1000,
                "samples": 0, "sampling_errors": 1, "memory_scope": "worker_process_tree_sum_rss"}
    while process.poll() is None:
        try:
            members = [root, *root.children(recursive=True)]
            rss = 0
            observed = 0
            for member in members:
                try:
                    rss += member.memory_info().rss
                    observed += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    errors += 1
            if observed:
                peak = rss if peak is None else max(peak, rss)
                samples += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            errors += 1
        if time.perf_counter() - start > timeout:
            try:
                for child in root.children(recursive=True):
                    child.kill()
                root.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            process.wait(timeout=10)
            return {"timed_out": True, "peak_rss_bytes": peak, "sample_interval_ms": interval * 1000,
                    "samples": samples, "sampling_errors": errors, "memory_scope": "worker_process_tree_sum_rss"}
        time.sleep(interval)
    return {"timed_out": False, "peak_rss_bytes": peak, "sample_interval_ms": interval * 1000,
            "samples": samples, "sampling_errors": errors, "memory_scope": "worker_process_tree_sum_rss"}
