from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "outputs/budongi_mvp_temp/src"))
if len(sys.argv) > 1 and sys.argv[1] == "git":
    from jipdam_harness.git_cli import main
    sys.argv.pop(1)
else:
    from jipdam_harness.managed_cli import main

if __name__ == "__main__":
    sys.exit(main())
