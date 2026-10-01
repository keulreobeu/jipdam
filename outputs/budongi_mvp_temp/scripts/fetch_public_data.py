"""Fetch one month of apartment trades or a date range of APT announcements."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from budongi.public_data import PublicDataError, fetch_applyhome, fetch_applyhome_models, fetch_molit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="source", required=True)
    trade = sub.add_parser("molit-trades", help="Apt sale transactions by district and contract month")
    trade.add_argument("--lawd-cd", required=True, help="Five-digit legal district code")
    trade.add_argument("--deal-ymd", required=True, help="Contract month YYYYMM")
    applyhome = sub.add_parser("applyhome-apts", help="APT subscription announcements by notice date")
    applyhome.add_argument("--start-date", required=True, help="Notice date YYYY-MM-DD")
    applyhome.add_argument("--end-date", required=True, help="Notice date YYYY-MM-DD")
    models = sub.add_parser("applyhome-models", help="APT housing types for one house management number")
    models.add_argument("--house-manage-no", required=True)
    for command in (trade, applyhome, models):
        command.add_argument("--per-page", type=int, default=None)
        command.add_argument("--output-dir", type=Path)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    try:
        if args.source == "molit-trades":
            output = args.output_dir or Path("data/provisional/api") / f"molit_{args.lawd_cd}_{args.deal_ymd}_{stamp}"
            manifest = fetch_molit(lawd_cd=args.lawd_cd, deal_ymd=args.deal_ymd,
                                   output_dir=output, per_page=args.per_page or 1000)
        elif args.source == "applyhome-apts":
            output = args.output_dir or Path("data/provisional/api") / f"applyhome_{args.start_date}_{args.end_date}_{stamp}"
            manifest = fetch_applyhome(start_date=args.start_date, end_date=args.end_date,
                                       output_dir=output, per_page=args.per_page or 100)
        else:
            output = args.output_dir or Path("data/provisional/api") / f"applyhome_models_{args.house_manage_no}_{stamp}"
            manifest = fetch_applyhome_models(house_manage_no=args.house_manage_no,
                                              output_dir=output, per_page=args.per_page or 100)
    except (PublicDataError, ValueError, FileExistsError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps({"output_dir": str(output), "source": manifest["source"],
                      "row_count": manifest["row_count"], "page_count": manifest["page_count"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
