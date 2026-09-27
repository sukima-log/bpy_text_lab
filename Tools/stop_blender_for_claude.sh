#!/usr/bin/env bash
# ============================================================
# Claude Code 用 永続 Blender 停止スクリプト
# ============================================================
# run_main_for_claude.sh で起動された永続 Blender を安全に停止する。
# (ユーザーが手動で X ボタンで閉じても OK だが、本スクリプトを使うと
#  通信ディレクトリもクリーンアップされる)
#
# 入力 (Input):
#   - 引数なし     : graceful 停止 (stop.txt 経由 で 10 秒 待ち、 ダメ なら 強制 fallback)
#   - --force / -f : graceful を 飛ばして 即 taskkill /F (ハング 復旧 用)
#
# 出力 (Output):
#   - 標準エラー: 進捗メッセージ
#   - exit code: 0 = 停止成功 (または既に停止済み)
#                1 = 停止失敗 (タイムアウト等)
# ============================================================

set -euo pipefail

# ------------------------------------------------------------
# 引数解析
# ------------------------------------------------------------
FORCE=false
while [[ $# -gt 0 ]]; do
    case "$1" in
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            sed -n '/^# 入力 (Input):/,/^# ===/p' "$0" | sed 's/^# //; s/^#$//'
            exit 0
            ;;
        *)
            echo "[stop] 不明な引数: $1 (--force or 引数なし)" >&2
            exit 1
            ;;
    esac
done

# このシェルスクリプトの絶対ディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMM_DIR="${PROJECT_ROOT}/.claude_blender_comm"

HEARTBEAT_FILE="$COMM_DIR/heartbeat.txt"
STOP_FILE="$COMM_DIR/stop.txt"

HEARTBEAT_STALE_SEC=5

# ------------------------------------------------------------
# --force モード: graceful を 飛ばして 直 taskkill
# ハング 中 (bootstrap timer 停止 中) は stop.txt を 書いても 反応 しない ので
# このパス が 唯一 の 確実 な 回復 手段。
# ------------------------------------------------------------
if [[ "$FORCE" == "true" ]]; then
    echo "[stop --force] Blender を 強制 終了 します..." >&2
    # Windows 側 blender.exe を 全て kill
    if command -v taskkill.exe >/dev/null 2>&1; then
        taskkill.exe /F /IM blender.exe >/dev/null 2>&1 || true
    fi
    # WSL 側 関連 プロセス
    WSL_PIDS=$(ps -eo pid,cmd --no-headers 2>/dev/null \
               | grep -i 'blender' \
               | grep -v 'grep' \
               | grep -v 'stop_blender_for_claude' \
               | grep -v 'run_main_for_claude' \
               | awk '{print $1}')
    if [[ -n "$WSL_PIDS" ]]; then
        # shellcheck disable=SC2086
        kill -9 $WSL_PIDS 2>/dev/null || true
    fi
    # 通信 ディレクトリ クリーンアップ
    [[ -d "$COMM_DIR" ]] && rm -rf "$COMM_DIR"
    # 残存 ラッパー の mkdir ロック も 念のため 解除
    rm -rf /tmp/claude_blender_wrapper_*.lock.d 2>/dev/null || true
    echo "[stop --force] 強制 終了 完了" >&2
    exit 0
fi

# ------------------------------------------------------------
# Blender が稼働しているか確認
# ------------------------------------------------------------
if [[ ! -f "$HEARTBEAT_FILE" ]]; then
    echo "[wrapper] Blender は起動していません (heartbeat なし)" >&2
    # 通信ディレクトリの残骸を念のためクリア
    [[ -d "$COMM_DIR" ]] && rm -rf "$COMM_DIR"
    exit 0
fi

# 直近 N 秒以内に heartbeat があるか
heartbeat=$(cat "$HEARTBEAT_FILE" 2>/dev/null || echo "0")
now=$(date +%s)
diff=$((now - heartbeat))
if [[ $diff -ge $HEARTBEAT_STALE_SEC ]]; then
    echo "[wrapper] Blender はすでに死亡しています (heartbeat ${diff}秒前)" >&2
    rm -rf "$COMM_DIR"
    exit 0
fi

# ------------------------------------------------------------
# 停止リクエスト送信
# ------------------------------------------------------------
echo "[wrapper] 停止リクエストを送信..." >&2
date +%s > "$STOP_FILE"

# 終了確認 (heartbeat 停止 = Blender 終了)
# 最大 10 秒待機
waited=0
while :; do
    sleep 0.5
    waited=$((waited + 1))
    new_heartbeat=$(cat "$HEARTBEAT_FILE" 2>/dev/null || echo "0")
    now=$(date +%s)
    diff=$((now - new_heartbeat))
    if [[ $diff -ge $HEARTBEAT_STALE_SEC ]]; then
        echo "[wrapper] Blender 停止確認" >&2
        rm -rf "$COMM_DIR"
        exit 0
    fi
    if [[ $waited -gt 20 ]]; then
        echo "[wrapper] Blender が 10 秒以内に応答しないため、強制停止フォールバックを実行" >&2

        # ---------------------------------------------------
        # 強制停止フォールバック (Claude Code から自動回復用)
        #   1) WSL 側 blender 関連 init プロセスを kill -9
        #   2) Windows 側 taskkill /IM blender.exe /F
        #   3) 通信ディレクトリ クリーンアップ
        # ---------------------------------------------------
        # 1) WSL 側プロセス kill
        # 自分自身 (このスクリプト) や run_main_for_claude.sh は除外する
        WSL_PIDS=$(ps -eo pid,cmd --no-headers 2>/dev/null \
                   | grep -i 'blender' \
                   | grep -v 'grep' \
                   | grep -v 'stop_blender_for_claude' \
                   | grep -v 'run_main_for_claude' \
                   | awk '{print $1}')
        if [[ -n "$WSL_PIDS" ]]; then
            echo "[wrapper] WSL 側 blender 関連 PID を kill: $WSL_PIDS" >&2
            # shellcheck disable=SC2086
            kill -9 $WSL_PIDS 2>/dev/null || true
        fi

        # 2) Windows 側 blender.exe を taskkill (WSL 経由で Windows プロセスを止める)
        #    ※ もしユーザーが別の Blender ウィンドウも同時に開いている場合、
        #      この手順は それらも巻き込んで終了させてしまう点に注意。
        #      Claude Code 用 永続 Blender だけに絞る確実な手段は今のところ無いため、
        #      タイムアウトでハングした永続 Blender を回復させる優先度を取る。
        if command -v taskkill.exe >/dev/null 2>&1; then
            echo "[wrapper] Windows 側 blender.exe を taskkill /F" >&2
            taskkill.exe /IM blender.exe /F >/dev/null 2>&1 || true
        fi

        # 3) 通信ディレクトリ クリーンアップ (heartbeat / stop / .pid 残骸を消す)
        sleep 1
        [[ -d "$COMM_DIR" ]] && rm -rf "$COMM_DIR"

        echo "[wrapper] 強制停止完了 (Claude Code 側からの自動回復)" >&2
        exit 0
    fi
done
