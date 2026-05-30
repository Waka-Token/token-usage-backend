from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen


def fetch_badge(base_url: str, user_id: str, badge_type: str, style: str, color: str) -> str:
    query = urlencode({"userId": user_id, "type": badge_type, "style": style, "color": color})
    url = f"{base_url.rstrip('/')}/api/badge.svg?{query}"
    with urlopen(url, timeout=10) as response:  # noqa: S310 - user-provided local/internal URL utility.
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate static SVG badge files from a running wakatoken API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--user-id", required=True)
    parser.add_argument("--output-dir", default="badges")
    parser.add_argument("--types", nargs="+", default=["daily", "monthly", "total", "cost"])
    parser.add_argument("--style", default="flat")
    parser.add_argument("--color", default="auto")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for badge_type in args.types:
        svg = fetch_badge(args.base_url, args.user_id, badge_type, args.style, args.color)
        output_path = output_dir / f"{args.user_id}-{badge_type}.svg"
        output_path.write_text(svg, encoding="utf-8")
        print(output_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())

