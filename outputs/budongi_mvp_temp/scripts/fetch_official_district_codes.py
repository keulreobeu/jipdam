"""Download the official legal district code archive for address mapping."""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from budongi.district_codes import official_districts


SOURCE_URL = "https://www.code.go.kr/etc/codeFullDown.do"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("data/provisional/legal_district_codes"))
    args = parser.parse_args()
    request = urllib.request.Request(
        SOURCE_URL,
        data=urllib.parse.urlencode({"codeseId": "00002"}).encode("ascii"),
        headers={"User-Agent": "budongi-mvp/0.1"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        archive = response.read()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    target = args.output_dir / "code_go_kr_full_download.bin"
    if target.exists() and target.read_bytes() != archive:
        raise ValueError("The existing official code copy differs; select another output directory")
    target.write_bytes(archive)
    districts, digest = official_districts(target)
    metadata = {
        "source": SOURCE_URL,
        "source_page": "https://www.code.go.kr/stdcode/regCodeL.do",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "sha256": digest,
        "district_name_count": len(districts),
        "note": "Current download includes active/abolished flags without effective dates.",
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"sha256": hashlib.sha256(archive).hexdigest(),
                      "district_name_count": len(districts)}))


if __name__ == "__main__":
    main()
