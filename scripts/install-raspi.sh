#!/usr/bin/env bash
# ==========================================================================
#  Raspberry Pi にこのサイトを常時配信させるセットアップスクリプト
#
#    $ bash scripts/install-raspi.sh          # 8000番で配信
#    $ PORT=80 bash scripts/install-raspi.sh  # 80番で配信（アドレスが短くなる）
#
#  やっていること:
#    1. systemd のサービスを登録して、電源を入れると自動で配信が始まるようにする
#    2. avahi（mDNS）を確認して <ホスト名>.local でアクセスできるようにする
#    3. 生徒に案内するアドレスを表示する
# ==========================================================================
set -euo pipefail

PORT="${PORT:-8000}"
SERVICE_NAME="taiken-site"
SITE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${SUDO_USER:-$(id -un)}"
TEMPLATE="${SITE_DIR}/scripts/${SERVICE_NAME}.service"
UNIT="/etc/systemd/system/${SERVICE_NAME}.service"

say()  { printf '\n\033[1;32m▸ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m  ! %s\033[0m\n' "$*"; }
die()  { printf '\033[1;31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

# --- 事前チェック --------------------------------------------------------
[ -f "${SITE_DIR}/server.py" ] || die "server.py が見つかりません（${SITE_DIR}）"
[ -f "${TEMPLATE}" ]           || die "${TEMPLATE} が見つかりません"
command -v python3 >/dev/null  || die "python3 が入っていません: sudo apt install -y python3"
command -v systemctl >/dev/null || die "systemd がありません。手動で 'python3 server.py' を実行してください"

if [ "$(id -u)" -ne 0 ]; then
  die "管理者権限が必要です:  sudo PORT=${PORT} bash scripts/install-raspi.sh"
fi

say "設定内容"
cat <<EOM
  サイトの場所 : ${SITE_DIR}
  実行ユーザー : ${RUN_USER}
  ポート       : ${PORT}
  サービス名   : ${SERVICE_NAME}
EOM

# --- サービス登録 -------------------------------------------------------
say "systemd サービスを登録します"
sed -e "s|__SITE_DIR__|${SITE_DIR}|g" \
    -e "s|__USER__|${RUN_USER}|g" \
    -e "s|__PORT__|${PORT}|g" \
    "${TEMPLATE}" > "${UNIT}"

systemctl daemon-reload
systemctl enable "${SERVICE_NAME}" >/dev/null
systemctl restart "${SERVICE_NAME}"
sleep 1

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  say "配信を開始しました（電源投入時にも自動で起動します）"
else
  warn "起動に失敗しました。次のコマンドで原因を確認してください:"
  echo "    sudo journalctl -u ${SERVICE_NAME} -n 30 --no-pager"
  exit 1
fi

# --- mDNS（<ホスト名>.local） -------------------------------------------
if ! systemctl is-active --quiet avahi-daemon 2>/dev/null; then
  warn "avahi-daemon が動いていません。「$(hostname).local」で開きたい場合:"
  echo "    sudo apt install -y avahi-daemon && sudo systemctl enable --now avahi-daemon"
fi

# --- 案内 ---------------------------------------------------------------
SUFFIX=""
[ "${PORT}" != "80" ] && SUFFIX=":${PORT}"

say "生徒に案内するアドレス"
for ip in $(hostname -I 2>/dev/null || true); do
  case "$ip" in *:*) continue ;; esac   # IPv6 は案内から除く
  echo "    http://${ip}${SUFFIX}/"
done
echo "    http://$(hostname).local${SUFFIX}/   （iPhone / Mac / 最近のAndroid）"

cat <<EOM

  ── よく使うコマンド ────────────────────────────────
    状態を見る   : systemctl status ${SERVICE_NAME}
    再起動する   : sudo systemctl restart ${SERVICE_NAME}
    止める       : sudo systemctl stop ${SERVICE_NAME}
    自動起動やめ : sudo systemctl disable ${SERVICE_NAME}
    ログを見る   : journalctl -u ${SERVICE_NAME} -f
  ────────────────────────────────────────────────

  配布ファイルは ${SITE_DIR}/files/ に置くだけで一覧に反映されます。
  （QRコードを作りたいときは: sudo apt install -y qrencode
     qrencode -o qr.png "http://\$(hostname -I | awk '{print \$1}')${SUFFIX}/" ）

EOM
