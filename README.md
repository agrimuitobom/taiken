# 一日体験入学サイト｜愛媛県立西条農業高等学校 食農科学科

Raspberry Pi を校内に置いて、体験入学に来た生徒のスマートフォンやタブレットから
**資料をダウンロードしてもらう**ためのサイトです。
あわせて、食農科学科が取り組んでいる DX 事業の紹介ページも入っています。

- 外部のサーバーやインターネット接続は不要です（校内ネットワークだけで動きます）
- 追加インストールなし。Raspberry Pi OS に最初から入っている `python3` だけで動きます
- 配布ファイルは `files/` に置くだけ。HTMLの編集は必要ありません

---

## 1. とりあえず動かしてみる

```bash
git clone <このリポジトリのURL> taiken
cd taiken
python3 server.py
```

起動すると、案内するアドレスが表示されます。

```
──────────────────────────────────────────────────────────
  西条農業高校 食農科学科 一日体験入学サイト
──────────────────────────────────────────────────────────
  次のアドレスを生徒に案内してください:
    ・http://192.168.1.23:8000/
    ・http://raspberrypi.local:8000/  (mDNS対応端末)

  配布ファイル: 3 件  (/home/pi/taiken/files)
```

同じWi-Fiにつないだスマートフォンのブラウザで、表示されたアドレスを開けば完了です。
止めるときは `Ctrl+C`。

> **アドレスを短くしたい場合**は 80番ポートで起動します（`:8000` が不要になります）。
> `sudo python3 server.py --port 80` → `http://192.168.1.23/`

---

## 2. 当日の準備（3ステップ）

### ステップ1　配布ファイルを置く

`files/` の中にコピーするだけです。フォルダ名が一覧の見出しになります。

```
files/
├── 01_配布資料/
│   ├── ワークシート.pdf
│   └── 記録用紙.xlsx
├── 02_スライド/
│   └── 学科紹介.pdf
└── 03_学科案内/
    └── パンフレット.pdf
```

先頭の `01_` は並び順のためのもので、画面には「配布資料」と表示されます。
詳しくは [`files/README.md`](files/README.md) を参照してください。

**サーバーを再起動する必要はありません。** ページを再読み込みすれば新しいファイルが並びます。

### ステップ2　写真を入れ替える

写真の指定は [`assets/css/photos.css`](assets/css/photos.css) の**1ファイルだけ**にまとめてあります。

1. 写真を `assets/img/` に入れる（例：`assets/img/hero.jpg`）
2. `photos.css` の該当行を書き換える

```css
/* 変更前 */
.ph-hero { --photo: url("../img/placeholder/hero.svg"); }

/* 変更後 */
.ph-hero { --photo: url("../img/hero.jpg"); }
```

3. ブラウザを強制再読み込み（`Ctrl+Shift+R` / `Cmd+Shift+R`）

写真を用意していない場所は、そのままプレースホルダー画像が表示されるのでレイアウトは崩れません。
どのスロットがどこに出るかは `photos.css` のコメントに書いてあります。

### ステップ3　文章を実際の内容に直す

仮の内容には `<!-- TODO: ... -->` とコメントを入れてあります。以下は必ず差し替えてください。

| 場所 | 内容 |
| --- | --- |
| `index.html` の `hero__meta` | 日程・受付時間・会場 |
| `index.html` の `.timeline` | 当日のタイムテーブル |
| `index.html` の `#access` | 住所・電話番号・交通手段・駐車場 |
| `dx.html` の `.stats` | センサー台数などの実績値（不要なら項目ごと削除してOK） |
| `dx.html` の「使っている道具」 | 実際の機材名・ソフト名 |
| 各ページのフッター | 住所・電話番号 |

まとめて探すなら:

```bash
grep -rn "TODO\|●" *.html
```

---

## 3. Raspberry Pi に常設する

電源を入れたら自動で配信が始まる状態にします。

```bash
sudo PORT=80 bash scripts/install-raspi.sh
```

これで `systemd` にサービスが登録され、再起動後も自動で立ち上がります。

```bash
systemctl status taiken-site      # 動いているか確認
sudo systemctl restart taiken-site
journalctl -u taiken-site -f      # アクセスログを流し見る
```

### 生徒への案内のしかた

`http://192.168.1.23/` のようなIPアドレスは口頭で伝えにくいので、
QRコードを作って教室に貼るのがおすすめです。

```bash
sudo apt install -y qrencode
qrencode -o qr.png "http://$(hostname -I | awk '{print $1}')/"
```

`raspberrypi.local` のような名前で開けるようにするには avahi を入れておきます
（iPhone・Mac・最近のAndroidで使えます）。

```bash
sudo apt install -y avahi-daemon
sudo systemctl enable --now avahi-daemon
```

### 校内Wi-Fiが無い / 借りられない場合

Raspberry Pi 自身をアクセスポイントにする方法もあります。
`NetworkManager` が入った Raspberry Pi OS（Bookworm以降）なら次の一行で作れます。

```bash
sudo nmcli device wifi hotspot ssid taiken-2026 password xxxxxxxx ifname wlan0
```

このとき、Piのアドレスは通常 `http://10.42.0.1/` になります。
**インターネットには出られない**点だけ生徒に伝えておくと混乱がありません。

---

## 4. 静的配信する場合（サーバーを使わない）

Apache / nginx / 校内のファイルサーバー / GitHub Pages などにそのまま置くこともできます。
この場合 `server.py` が動いていないので、**ファイル一覧の情報（`files/manifest.json`）が別途必要**です。

### GitHubにpush・アップロードする場合 → 自動です

`.github/workflows/update-manifest.yml` が、`files/` に変更があると
`files/manifest.json` を作り直して自動でコミットします。

**GitHubのWeb画面から「Add file → Upload files」でアップロードした場合も対象です。**
アップロードの1〜2分後に一覧へ反映されるので、ページを再読み込みしてください。
（進行状況は Actions タブで確認できます）

### 手元のファイルをそのままコピーして使う場合

```bash
python3 tools/make_manifest.py
```

`files/manifest.json` が作られ、サイトがそれを読んで一覧を表示します。
**ファイルを追加・削除したら、そのつど実行し直してください。**

> 一覧に「配布ファイルの一覧を取得できませんでした」と出るときは、
> この `manifest.json` が古い（または無い）状態です。

---

## 5. ファイル構成

```
.
├── index.html                トップ（体験入学の案内・学科紹介・資料への導線）
├── dx.html                   DX事業の紹介
├── download.html             資料ダウンロード（検索・カテゴリ絞り込みつき）
├── server.py                 配信サーバー（標準ライブラリのみ / files/ を自動一覧化）
├── files/                    ★ 配布ファイルを置く場所
│   └── README.md             置き方の説明
├── assets/
│   ├── css/style.css         デザイン一式
│   ├── css/photos.css        ★ 写真の差し替えはここだけ
│   ├── js/main.js            メニュー・スクロール演出
│   ├── js/files.js           ファイル一覧の描画
│   └── img/placeholder/      仮画像（差し替え前の表示用）
├── scripts/
│   ├── install-raspi.sh      ラズパイ常設セットアップ
│   └── taiken-site.service   systemd サービス定義
├── tools/
│   ├── make_manifest.py      静的配信用のファイル一覧生成
│   └── make_placeholders.py  仮画像の再生成
└── docs/
    └── 運用マニュアル.md       当日の手順・トラブル対応
```

---

## 6. 技術的な補足

- **外部通信ゼロ**：Webフォント・CDN・アクセス解析を一切使っていません。
  オフラインの校内ネットワークでも、見た目・動作が変わりません。
- **フォント**：閲覧端末に入っている明朝・ゴシックを指定しています（`style.css` の `--f-serif` / `--f-sans`）。
- **`/api/files`**：`server.py` が `files/` を走査して返すJSONです。
  `/api/files.zip` は全ファイルをまとめたZIPを生成します。
- **キャッシュ**：当日の差し替えが確実に反映されるよう、`no-cache` を付けています。
- **セキュリティ**：閲覧・ダウンロード専用で、アップロード機能はありません。
  ただし校内ネットワークに繋がった端末からは誰でも見られるため、
  `files/` に個人情報を含むファイルを置かないでください。

## 7. 動作確認済みの範囲

- Python 3.9 以降（Raspberry Pi OS Bookworm の `python3` で動作）
- iOS Safari / Android Chrome / PC の Chrome・Edge・Firefox
- 画面幅 320px 〜 2560px

---

トラブル時の対応は [`docs/運用マニュアル.md`](docs/運用マニュアル.md) にまとめています。
