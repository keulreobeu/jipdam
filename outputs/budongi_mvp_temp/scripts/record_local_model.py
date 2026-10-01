"""Record a running local Ollama model and GPU before smoke testing."""

from __future__ import annotations

import argparse
import json
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def get_json(url: str, data: dict | None = None) -> dict:
    payload = None if data is None else json.dumps(data).encode("utf-8")
    request = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", default="qwen3.5:4b-q4_K_M")
    parser.add_argument("--context-length", type=int, default=8192)
    parser.add_argument("--output", type=Path,
                        default=Path(".local_runtime/synthetic_smoke/model_runtime.json"))
    args = parser.parse_args()
    base = "http://127.0.0.1:11434"
    version = get_json(f"{base}/api/version")["version"]
    tag = next((item for item in get_json(f"{base}/api/tags")["models"]
                if item["name"].lower() == args.model.lower()), None)
    if tag is None:
        raise ValueError(f"Model is not installed: {args.model}")
    shown = get_json(f"{base}/api/show", {"model": args.model})
    gpu = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    details = shown["details"]
    info = shown["model_info"]
    record = {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "server": "Ollama", "server_version": version, "endpoint": f"{base}/v1/chat/completions",
        "model": tag["name"], "model_digest": tag["digest"], "model_bytes": tag["size"],
        "parameter_size": details["parameter_size"], "quantization": details["quantization_level"],
        "model_context_limit": info.get("qwen35.context_length"),
        "configured_context_length": args.context_length,
        "capabilities": shown.get("capabilities", []),
        "license": "Apache-2.0",
        "model_source": "https://huggingface.co/Qwen/Qwen3.5-4B",
        "runtime_model_source": "https://ollama.com/library/qwen3.5:4b",
        "gpu_name_memory_driver": gpu,
        "test_data": "fictional synthetic_toolcall_smoke_v1 only",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: record[key] for key in ("model", "model_digest", "server_version",
                                                         "quantization", "configured_context_length")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
