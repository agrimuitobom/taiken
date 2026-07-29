#!/usr/bin/env python3
"""写真差し替え前のプレースホルダー画像(SVG)を生成する。

用途:
    写真がまだ無い状態でもレイアウトが崩れないようにするための仮画像です。
    本物の写真を入れたら、このスクリプトを再実行する必要はありません
    （assets/css/photos.css のパスを差し替えるだけ）。

使い方:
    python3 tools/make_placeholders.py
"""

from pathlib import Path
from xml.sax.saxutils import escape

OUT_DIR = Path(__file__).resolve().parent.parent / "assets" / "img" / "placeholder"

# (ファイル名, 幅, 高さ, ラベル, 濃さ 0=明るい 1=暗い)
SLOTS = [
    ("hero",        1920, 1280, "MAIN VISUAL",        1),
    ("about",       1200,  900, "ABOUT",              0),
    ("course-crop", 1000, 1000, "CROP",               0),
    ("course-food", 1000, 1000, "FOOD PROCESSING",    0),
    ("course-data", 1000, 1000, "DATA / DX",          0),
    ("taiken",      1600, 1067, "OPEN CAMPUS",        0),
    ("dx-hero",     1920, 1080, "DX PROJECT",         1),
    ("dx-1",        1000,  750, "SMART AGRI",         0),
    ("dx-2",        1000,  750, "DRONE / SENSING",    0),
    ("dx-3",        1000,  750, "RECORD & DATA",      0),
    ("dx-4",        1000,  750, "FOOD × DATA",        0),
    ("dx-5",        1000,  750, "BRANDING",           0),
    ("dx-6",        1000,  750, "AI",                 0),
    ("students",    1400,  933, "STUDENTS",           0),
    ("campus",      1600,  900, "CAMPUS",             0),
]

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label} placeholder">
  <defs>
    <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{c1}"/>
      <stop offset="1" stop-color="{c2}"/>
    </linearGradient>
    <pattern id="p" width="24" height="24" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="24" stroke="{line}" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  <rect width="{w}" height="{h}" fill="url(#p)"/>
  <g fill="none" stroke="{stroke}" stroke-width="{sw}">
    <circle cx="{cx}" cy="{cy}" r="{r}"/>
    <path d="M{lx1} {cy} H{lx2}"/>
    <path d="M{cx} {ly1} V{ly2}"/>
  </g>
  <text x="{cx}" y="{ty}" fill="{text}" font-family="Helvetica, Arial, sans-serif" font-size="{fs}" letter-spacing="{ls}" text-anchor="middle">{label}</text>
  <text x="{cx}" y="{ty2}" fill="{text2}" font-family="Helvetica, Arial, sans-serif" font-size="{fs2}" letter-spacing="{ls2}" text-anchor="middle">PHOTO PLACEHOLDER / {w}x{h}</text>
</svg>
"""


def build(name: str, w: int, h: int, label: str, dark: int) -> str:
    if dark:
        # 暗い背景（ヒーロー）は文字が主役なので、目印は控えめにする
        c1, c2, line = "#1b3327", "#0e1c14", "rgba(255,255,255,0.05)"
        stroke, text, text2 = "rgba(255,255,255,0.13)", "rgba(255,255,255,0.24)", "rgba(255,255,255,0.15)"
    else:
        c1, c2, line = "#eae4d6", "#d9d2c0", "rgba(27,26,23,0.045)"
        stroke, text, text2 = "rgba(27,26,23,0.22)", "rgba(27,26,23,0.62)", "rgba(27,26,23,0.38)"

    cx, cy = w / 2, h / 2
    r = min(w, h) * 0.11
    fs = round(min(w, h) * 0.042)
    fs2 = round(min(w, h) * 0.022)
    return TEMPLATE.format(
        w=w, h=h, label=escape(label), c1=c1, c2=c2, line=line, stroke=stroke,
        text=text, text2=text2,
        sw=round(max(w, h) / 900, 2),
        cx=round(cx, 1), cy=round(cy - min(w, h) * 0.06, 1), r=round(r, 1),
        lx1=round(cx - r * 1.9, 1), lx2=round(cx - r * 1.25, 1),
        ly1=round(cy - min(w, h) * 0.06 - r * 1.9, 1),
        ly2=round(cy - min(w, h) * 0.06 - r * 1.25, 1),
        ty=round(cy + min(w, h) * 0.17, 1), ty2=round(cy + min(w, h) * 0.225, 1),
        fs=fs, fs2=fs2, ls=round(fs * 0.22, 1), ls2=round(fs2 * 0.16, 1),
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, w, h, label, dark in SLOTS:
        path = OUT_DIR / f"{name}.svg"
        path.write_text(build(name, w, h, label, dark), encoding="utf-8")
        print(f"generated: {path.relative_to(OUT_DIR.parents[3])}")
    print(f"\n{len(SLOTS)} 件のプレースホルダーを生成しました。")


if __name__ == "__main__":
    main()
