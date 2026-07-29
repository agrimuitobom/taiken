#!/usr/bin/env python3
"""files/ の中身から files/manifest.json を作る。

server.py で配信する場合は不要です（サーバーが自動で一覧を作ります）。
Apache / nginx / GitHub Pages などで「静的に」置くときだけ実行してください。

  $ python3 tools/make_manifest.py
"""

from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server import FILES_DIR, scan_files  # noqa: E402


def main() -> int:
    FILES_DIR.mkdir(exist_ok=True)
    items = scan_files()
    payload = {
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "manifest",
        "zip": "",
        "count": len(items),
        "items": items,
    }
    out = FILES_DIR / "manifest.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"{out.relative_to(ROOT)} を更新しました（{len(items)} 件）")
    for it in items:
        print(f"  - [{it['category']}] {it['name']}")
    if not items:
        print("  ※ files/ が空です。配布したいファイルを置いてから実行してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
