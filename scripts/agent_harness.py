"""Repository entrypoint for the offline portable Jipdam developer harness."""
from pathlib import Path
import sys

WORKSPACE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKSPACE / "outputs/budongi_mvp_temp/src"))

from jipdam_harness.cli import main

if __name__ == "__main__":
    sys.exit(main(workspace=WORKSPACE))
