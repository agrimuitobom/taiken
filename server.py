#!/usr/bin/env python3
"""一日体験入学サイト用の簡易配信サーバー。

Python標準ライブラリだけで動きます（pip install 不要）。
Raspberry Pi OS に最初から入っている python3 でそのまま起動できます。

  $ python3 server.py                # http://<ラズパイのIP>:8000/
  $ python3 server.py --port 80      # 80番で配信（sudo が必要）
  $ python3 server.py --no-open      # 起動時の案内表示のみ

やっていること:
  * サイト（index.html など）を配信
  * files/ フォルダの中身を読んで /api/files で一覧を返す
    → 先生はファイルを files/ に置くだけ。HTMLの編集は不要です
  * /api/files.zip で files/ の中身をまとめてダウンロード
"""

from __future__ import annotations

import argparse
import datetime as _dt
import io
import json
import os
import socket
import zipfile
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

ROOT = Path(__file__).resolve().parent
FILES_DIR = ROOT / "files"
ZIP_NAME = "食農科学科_配布資料.zip"

# 一覧に出さないもの
SKIP_NAMES = {"manifest.json", "README.md", ".gitkeep", ".DS_Store", "Thumbs.db", "desktop.ini"}
SKIP_SUFFIXES = {".tmp", ".part", ".crdownload", ".swp"}


# --------------------------------------------------------------------------
# files/ の走査
# --------------------------------------------------------------------------
def _visible(path: Path) -> bool:
    if path.name.startswith(".") or path.name.startswith("~$"):
        return False
    if path.name in SKIP_NAMES:
        return False
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    return True


def _category_label(name: str) -> str:
    """フォルダ名 "01_配布資料" → "配布資料"（並び順用の接頭辞を落とす）。"""
    head, sep, tail = name.partition("_")
    if sep and head.isdigit():
        return tail or name
    head, sep, tail = name.partition("-")
    if sep and head.isdigit():
        return tail or name
    return name


def scan_files(base: Path = FILES_DIR) -> list[dict]:
    """files/ 以下を走査して一覧データを作る。

    files/直下のフォルダ名がカテゴリになります。
      files/01_配布資料/資料.pdf → カテゴリ「配布資料」
      files/メモ.txt             → カテゴリ「その他」
    """
    if not base.is_dir():
        return []

    items: list[dict] = []
    for path in sorted(base.rglob("*"), key=lambda p: (str(p.parent).lower(), p.name.lower())):
        if not path.is_file() or not _visible(path):
            continue
        if any(not _visible(parent) for parent in path.relative_to(base).parents if parent.name):
            continue

        rel = path.relative_to(base)
        category = _category_label(rel.parts[0]) if len(rel.parts) > 1 else "その他"
        try:
            stat = path.stat()
        except OSError:
            continue

        items.append({
            "name": path.name,
            "title": path.stem,
            "path": "files/" + rel.as_posix(),
            "category": category,
            "size": stat.st_size,
            "mtime": _dt.datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(timespec="seconds"),
            # 並び順用（フォルダ名の "01_" を活かす。直置きファイルは最後）
            "_sort": ("￿" if len(rel.parts) == 1 else rel.parts[0], rel.as_posix().lower()),
        })

    items.sort(key=lambda it: it["_sort"])
    for it in items:
        del it["_sort"]
    return items


def build_payload() -> dict:
    items = scan_files()
    return {
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": "server",
        "zip": "api/files.zip" if items else "",
        "count": len(items),
        "items": items,
    }


def build_zip() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in scan_files():
            src = ROOT / item["path"]
            if src.is_file():
                zf.write(src, arcname=str(Path(item["path"]).relative_to("files")))
    return buf.getvalue()


# --------------------------------------------------------------------------
# ハンドラ
# --------------------------------------------------------------------------
class SiteHandler(SimpleHTTPRequestHandler):
    server_version = "TaikenSite/1.0"

    def do_GET(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path in ("/api/files", "/api/files.json"):
            self._send_json(build_payload())
            return
        if path == "/api/files.zip":
            self._send_zip()
            return
        super().do_GET()

    def do_HEAD(self) -> None:  # noqa: N802
        path = unquote(urlparse(self.path).path)
        if path.startswith("/api/"):
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            return
        super().do_HEAD()

    # --- 応答の組み立て --------------------------------------------------
    def _send_json(self, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=1).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _send_zip(self) -> None:
        try:
            body = build_zip()
        except OSError as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"zip failed: {exc}")
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/zip")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Disposition",
            "attachment; filename=materials.zip; filename*=UTF-8''" + quote(ZIP_NAME),
        )
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self) -> None:
        # 当日の差し替えが即反映されるようにキャッシュを抑える
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, fmt: str, *args) -> None:
        stamp = _dt.datetime.now().strftime("%H:%M:%S")
        print(f"  [{stamp}] {self.address_string()} {fmt % args}")


# --------------------------------------------------------------------------
# 起動
# --------------------------------------------------------------------------
def local_ips() -> list[str]:
    ips: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(0.2)
            s.connect(("8.8.8.8", 80))  # 送信はしない。経路から自分のIPを知るだけ
            ips.append(s.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except OSError:
        pass
    return ips


def banner(port: int) -> None:
    items = scan_files()
    host = socket.gethostname()
    line = "─" * 58
    print(f"\n{line}")
    print("  西条農業高校 食農科学科 一日体験入学サイト")
    print(f"{line}")
    print("  次のアドレスを生徒に案内してください:")
    for ip in local_ips():
        print(f"    ・http://{ip}{'' if port == 80 else f':{port}'}/")
    print(f"    ・http://{host}.local{'' if port == 80 else f':{port}'}/  (mDNS対応端末)")
    print(f"\n  配布ファイル: {len(items)} 件  ({FILES_DIR})")
    if items:
        for it in items[:8]:
            print(f"    - [{it['category']}] {it['name']}")
        if len(items) > 8:
            print(f"    …ほか {len(items) - 8} 件")
    else:
        print("    ※ files/ にファイルを置くと自動で一覧に並びます")
    print(f"\n  終了: Ctrl+C")
    print(f"{line}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="一日体験入学サイトを配信します")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8000)),
                        help="待ち受けポート（既定: 8000 / 80番は sudo が必要）")
    parser.add_argument("--host", default="0.0.0.0", help="待ち受けアドレス（既定: 0.0.0.0）")
    parser.add_argument("--quiet", action="store_true", help="アクセスログを表示しない")
    args = parser.parse_args()

    FILES_DIR.mkdir(exist_ok=True)

    handler = partial(SiteHandler, directory=str(ROOT))
    if args.quiet:
        handler = partial(_QuietHandler, directory=str(ROOT))

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), handler)
    except PermissionError:
        print(f"エラー: ポート {args.port} は管理者権限が必要です。"
              f"\n      sudo python3 server.py --port {args.port}  で起動してください。")
        return 1
    except OSError as exc:
        print(f"エラー: ポート {args.port} を使用できません（{exc}）。"
              f"\n      別のポートを指定してください: python3 server.py --port 8080")
        return 1

    banner(args.port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n配信を終了しました。")
    finally:
        httpd.server_close()
    return 0


class _QuietHandler(SiteHandler):
    def log_message(self, fmt: str, *args) -> None:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
