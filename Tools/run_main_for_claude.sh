#!/usr/bin/env bash
# ============================================================
# Claude Code 用 Blender 永続実行ラッパー
# ============================================================
# 役割:
#   - Blender が起動していなければ永続モードで起動
#   - 起動済みなら既存プロセスにトリガー送信
#   - main.py の実行結果 (成功/失敗) を待って exit code に反映
#
# Blender が起動しっぱなしのため、反復ループでの起動コストが発生しない:
#   - 初回呼出: Blender 起動 (~5 秒) + main.py 実行 + 結果取得
#   - 2回目以降: トリガー送信 + main.py 実行 + 結果取得 (起動コスト 0)
#
# 使い方 (USAGE):
#   ./Tools/run_main_for_claude.sh
#       既存オブジェクトを維持したまま main.py を実行 (削除なし)
#       既存オブジェクトは glb_exist_obj_chk によりスキップされ、
#       不在オブジェクトのみが新規生成される (差分実行)
#
#   ./Tools/run_main_for_claude.sh --delete OBJ1 OBJ2 ...
#       指定オブジェクトを bpy.data.objects から削除してから main.py 実行
#       → 削除されたオブジェクトのみ再生成される (選択的再生成)
#       使用例: コードを修正した結果に応じて該当オブジェクトを更新したいとき
#
#   ./Tools/run_main_for_claude.sh --clear
#       全シーン状態をリセット (Python ステート含む) してから main.py 実行
#       → フル再生成 (時間がかかるが完全な作り直し)
#       使用例: 構造的な大きな変更や、まっさらな状態で再構築したいとき
#
#   ./Tools/run_main_for_claude.sh --help
#       このヘルプを表示
#
# 通信プロトコル:
#   ラッパーとブートストラップ (Tools/_persistent_bootstrap.py) の間で
#   PROJECT_ROOT/.claude_blender_comm/ 内のファイルを介して同期する。
#   詳細は _persistent_bootstrap.py のドキュメントコメント参照。
#
# Blender ウィンドウについて:
#   GUI モードで起動するのでウィンドウが Windows デスクトップに表示される。
#   ユーザーは X ボタンで手動で閉じても問題ない (次回呼出で再起動)。
#   永続 Blender を明示的に停止したい場合は ./Tools/stop_blender_for_claude.sh
#
# 環境変数 (任意で上書き可能):
#   - BLENDER_BIN : Blender 実行ファイルへのパス
#                   既定: Blender 5.2.0 LTS (Windows 側)
# ============================================================

set -euo pipefail

# ------------------------------------------------------------
# 引数解析
# ------------------------------------------------------------
DELETE_OBJECTS=()
CLEAR_ALL=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --delete)
            shift
            # --delete の後ろのトークンを次のフラグ (--*) まで取り込む
            while [[ $# -gt 0 && "$1" != --* ]]; do
                DELETE_OBJECTS+=("$1")
                shift
            done
            ;;
        --clear)
            CLEAR_ALL=true
            shift
            ;;
        --help|-h)
            sed -n '/^# 使い方 (USAGE):/,/^# 通信プロトコル:/p' "$0" | sed 's/^# //; s/^#$//'
            exit 0
            ;;
        *)
            echo "[エラー] 不明な引数: $1" >&2
            echo "        ./Tools/run_main_for_claude.sh --help でヘルプを表示" >&2
            exit 1
            ;;
    esac
done

# ------------------------------------------------------------
# 設定
# ------------------------------------------------------------
BLENDER_BIN="${BLENDER_BIN:-/mnt/c/Users/PC_User/Documents/Blender_lunch/stable/blender-5.2.0-lts.fbe6228777e7/blender.exe}"

# WSL does not pass arbitrary Linux environment variables to Windows
# executables.  Register only the explicit asset-routing variables used by
# reproducible Blender automation; ordinary interactive runs remain unchanged.
for passthrough_name in BPY_ASSET_MAIN_MODULE BPY_SEMANTIC_SNAPSHOT_REQUEST; do
    if [[ -n "${!passthrough_name:-}" ]]; then
        case ":${WSLENV:-}:" in
            *":${passthrough_name}:"*) ;;
            *) WSLENV="${WSLENV:+${WSLENV}:}${passthrough_name}" ;;
        esac
    fi
done
export WSLENV

# このシェルスクリプトの絶対ディレクトリ
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# プロジェクトルート = Tools/ の親ディレクトリ
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MAIN_PY="${PROJECT_ROOT}/Assets/main.py"
# 永続モード用ブートストラップ
BOOTSTRAP_PY="${SCRIPT_DIR}/_persistent_bootstrap.py"

# 通信ディレクトリ (Python 側 _persistent_bootstrap.py と同じ場所)
COMM_DIR="${PROJECT_ROOT}/.claude_blender_comm"
mkdir -p "$COMM_DIR"

HEARTBEAT_FILE="$COMM_DIR/heartbeat.txt"
TRIGGER_FILE="$COMM_DIR/trigger.txt"
RESULT_FILE="$COMM_DIR/result.txt"
STOP_FILE="$COMM_DIR/stop.txt"
BLENDER_LOG="$COMM_DIR/blender.log"
# ロックは mkdir ベース (atomic、FD 継承の影響を受けない)
# /tmp 配下に置く: NTFS マウント /mnt/c/... では mkdir の atomic 性に問題が出る場合がある
PROJECT_HASH=$(echo -n "$PROJECT_ROOT" | md5sum | cut -c1-8)
LOCK_DIR="/tmp/claude_blender_wrapper_${PROJECT_HASH}.lock.d"

# タイムアウト設定 (秒)
READY_TIMEOUT=30          # Blender 起動完了待ち
# main.py 実行 最大 待ち 秒数。 これ を 超えた ら ハング 判定 → 強制 終了。
# 旧設定 600 (10 分) は ハング 時 の 待ち が 長すぎ た ため 240 (4 分) に 短縮。
# 環境変数 RUN_TIMEOUT で 上書き 可能 (重い アセット で 必要 な 場合)。
RUN_TIMEOUT="${RUN_TIMEOUT:-240}"
HEARTBEAT_STALE_SEC=5     # heartbeat がこの秒数以上古ければ Blender 死亡判定

# ハング 検出 設定
# blender.log が この 秒数 以上 更新 されなければ 「main.py が 進捗 していない」 と 判定。
# (render.render() / bmesh ops 等 が 完了 すれば blender.log に 出力 が 出る ため、
#  ある程度 まとまった 時間 出力 が 無い = ハング と 推定 できる)
LOG_STALE_SEC="${LOG_STALE_SEC:-90}"
# 何 秒 ごと に ハング 検出 チェック を 走らせる か (0.5s 間隔 の 結果 待ち とは 別)
HANG_CHECK_INTERVAL_SEC=5
# Blender クラッシュ ダンプ ファイル (Windows AppData / Temp)
# 存在 + mtime が 「実行 開始 後」 なら 今回 の 実行 で クラッシュ した と 判定。
BLENDER_CRASH_DUMP="${BLENDER_CRASH_DUMP:-/mnt/c/Users/PC_User/AppData/Local/Temp/blender.crash.txt}"

# ------------------------------------------------------------
# 事前チェック
# ------------------------------------------------------------
if [[ ! -f "$BLENDER_BIN" ]]; then
    echo "[エラー] Blender バイナリが見つかりません: $BLENDER_BIN" >&2
    echo "        環境変数 BLENDER_BIN で正しいパスを指定してください" >&2
    exit 1
fi

if [[ ! -f "$MAIN_PY" ]]; then
    echo "[エラー] main.py が見つかりません: $MAIN_PY" >&2
    exit 1
fi

if [[ ! -f "$BOOTSTRAP_PY" ]]; then
    echo "[エラー] ブートストラップが見つかりません: $BOOTSTRAP_PY" >&2
    exit 1
fi

# ------------------------------------------------------------
# 並行実行防止のロック (mkdir ベース、FD 継承の影響なし)
# ------------------------------------------------------------
# mkdir は atomic 操作。同時に複数プロセスが mkdir しても 1 つだけ成功する。
# Blender バックグラウンドプロセスがロックを継承する問題を回避するため
# flock ではなく mkdir を採用する。
acquire_lock() {
    local waited=0
    while ! mkdir "$LOCK_DIR" 2>/dev/null; do
        sleep 0.5
        waited=$((waited + 1))
        if [[ $waited -gt 120 ]]; then
            return 1
        fi
        # ステイル ロック検出 (前回ラッパーが異常終了して残った場合の救済)
        # 30 分以上経過したロックは古いと判断して強制解除
        if [[ -d "$LOCK_DIR" ]]; then
            local lock_age
            lock_age=$(( $(date +%s) - $(stat -c %Y "$LOCK_DIR" 2>/dev/null || echo 0) ))
            if [[ $lock_age -gt 1800 ]]; then
                echo "[wrapper] ステイルロック検出 (${lock_age}秒経過): 強制解除" >&2
                rmdir "$LOCK_DIR" 2>/dev/null || true
            fi
        fi
    done
    return 0
}

if ! acquire_lock; then
    echo "[エラー] 別のラッパーが実行中です (60秒待機タイムアウト)" >&2
    exit 1
fi

# 終了時にロック解除 (正常/異常終了どちらでも)
trap 'rmdir "$LOCK_DIR" 2>/dev/null || true' EXIT

# ------------------------------------------------------------
# Blender 生存確認 (heartbeat ファイルの新鮮度をチェック)
# ------------------------------------------------------------
# Input:  なし
# Output: 0 = 生存, 非 0 = 死亡
is_blender_alive() {
    [[ -f "$HEARTBEAT_FILE" ]] || return 1
    local heartbeat
    heartbeat=$(cat "$HEARTBEAT_FILE" 2>/dev/null || echo "0")
    # BlenderやWSLの異常終了時に途中書き込み・不正文字列が残る場合がある。
    # 算術式へ渡す前にUnix時刻形式か検証し、不正値は停止中として扱う。
    [[ "$heartbeat" =~ ^[0-9]+$ ]] || return 1
    local now
    now=$(date +%s)
    local diff=$((now - heartbeat))
    [[ $diff -lt $HEARTBEAT_STALE_SEC ]]
}

# ------------------------------------------------------------
# Blender 起動 (未起動の場合のみ)
# ------------------------------------------------------------
if ! is_blender_alive; then
    echo "[wrapper] Blender を永続モードで起動します..." >&2

    # 古い通信ファイルクリーンアップ (前回プロセスの残骸排除)
    rm -f "$HEARTBEAT_FILE" "$TRIGGER_FILE" "$RESULT_FILE" "$STOP_FILE"

    # Linux パスを Windows パスに変換 (blender.exe に渡すため)
    BOOTSTRAP_PY_WIN="$(wslpath -w "$BOOTSTRAP_PY")"

    # nohup でバックグラウンド起動 (このシェル終了後も生き残る)
    # disown でジョブ制御から外す
    nohup "$BLENDER_BIN" \
        --factory-startup \
        --python-exit-code 1 \
        --python "$BOOTSTRAP_PY_WIN" \
        > "$BLENDER_LOG" 2>&1 &
    disown

    # heartbeat 待ち (Blender 起動 + bootstrap タイマー登録完了)
    waited=0
    while ! is_blender_alive; do
        sleep 0.5
        waited=$((waited + 1))
        if [[ $waited -gt $((READY_TIMEOUT * 2)) ]]; then
            echo "[wrapper エラー] Blender 起動タイムアウト (${READY_TIMEOUT}秒)" >&2
            echo "                  ログ: $BLENDER_LOG" >&2
            exit 1
        fi
    done

    echo "[wrapper] Blender 起動完了 (永続モード)" >&2
fi

# ------------------------------------------------------------
# トリガー送信 + 結果待機
# ------------------------------------------------------------
# 古い結果ファイルを削除 (新しい実行の結果と区別するため)
rm -f "$RESULT_FILE"

# ------------------------------------------------------------
# トリガー JSON を構築
# ------------------------------------------------------------
# 形式:
#   - {"clear": true}                    : フル再生成
#   - {"delete": ["obj1", "obj2", ...]}  : 選択削除して再実行
#   - {}                                  : 削除なし (既存維持で実行)
if [[ "$CLEAR_ALL" == "true" ]]; then
    TRIGGER_JSON='{"clear": true}'
elif [[ ${#DELETE_OBJECTS[@]} -gt 0 ]]; then
    # 配列要素を JSON 配列要素に整形 (各要素を "..." で括ってカンマ区切り)
    DELETE_JSON_ITEMS=""
    for obj in "${DELETE_OBJECTS[@]}"; do
        if [[ -n "$DELETE_JSON_ITEMS" ]]; then
            DELETE_JSON_ITEMS="$DELETE_JSON_ITEMS,"
        fi
        DELETE_JSON_ITEMS="${DELETE_JSON_ITEMS}\"${obj}\""
    done
    TRIGGER_JSON="{\"delete\": [${DELETE_JSON_ITEMS}]}"
else
    TRIGGER_JSON='{}'
fi

# ------------------------------------------------------------
# ハング 検出 用 ベース ライン 記録
# ------------------------------------------------------------
# トリガー 投入 直前 の Unix 時刻 を 記録。
# - crash dump (BLENDER_CRASH_DUMP) の mtime が この 時刻 以降 なら 今回 実行 で クラッシュ
# - blender.log の mtime が LOG_STALE_SEC 以上 更新 されない なら ハング
RUN_START_TS=$(date +%s)
LAST_HANG_CHECK_TS=$RUN_START_TS

# 強制 終了 + クリーンアップ 関数 (ハング / クラッシュ 検出 時 に 呼ぶ)
# Input :  reason = ログ 出力 用 理由 文字列
# Output:  この 関数 内 で exit 1 する (戻らない)
force_kill_blender_and_exit() {
    local reason="$1"
    echo "[wrapper エラー] ${reason}" >&2
    echo "[wrapper] Blender を 強制 終了 します..." >&2
    if command -v taskkill.exe >/dev/null 2>&1; then
        taskkill.exe /F /IM blender.exe >/dev/null 2>&1 || true
    fi
    # WSL 側 init プロセス も 念のため kill
    local wsl_pids
    wsl_pids=$(ps -eo pid,cmd --no-headers 2>/dev/null \
               | grep -i 'blender' \
               | grep -v 'grep' \
               | grep -v 'stop_blender_for_claude' \
               | grep -v 'run_main_for_claude' \
               | awk '{print $1}')
    if [[ -n "$wsl_pids" ]]; then
        # shellcheck disable=SC2086
        kill -9 $wsl_pids 2>/dev/null || true
    fi
    # 通信 残骸 クリア (次回 起動 時 に 確実 に 新規 Blender を 立ち上げる ため)
    rm -f "$HEARTBEAT_FILE" "$TRIGGER_FILE" "$RESULT_FILE" "$STOP_FILE" 2>/dev/null || true
    exit 1
}

# トリガー書き込み (ブートストラップ側がこの JSON をパースして処理を分岐)
echo "$TRIGGER_JSON" > "$TRIGGER_FILE"

# 結果待ち (タイムアウト + ハング 検出 で 判定)
# 注: 実行中はブートストラップタイマーが main.py 完了まで停止しているため
# この期間中の bootstrap timer は heartbeat 更新 を 出さない (が、 別 スレッド の
# _heartbeat_writer_thread が 動き続け て いる ので heartbeat ファイル は 生きる)。
# ハング 検出 は (1) crash dump 出現 (2) blender.log 停滞 (3) blender.exe 不在
# の 3 観点 で 早期 検知 する。
waited=0
while [[ ! -f "$RESULT_FILE" ]]; do
    sleep 0.5
    waited=$((waited + 1))

    # 全体 タイムアウト (旧 ロジック の 保険)
    if [[ $waited -gt $((RUN_TIMEOUT * 2)) ]]; then
        force_kill_blender_and_exit "main.py 実行 タイムアウト (${RUN_TIMEOUT}秒)"
    fi

    # HANG_CHECK_INTERVAL_SEC ごと に ハング 検出 を 走らせる
    NOW_TS=$(date +%s)
    if [[ $((NOW_TS - LAST_HANG_CHECK_TS)) -lt $HANG_CHECK_INTERVAL_SEC ]]; then
        continue
    fi
    LAST_HANG_CHECK_TS=$NOW_TS

    # (1) クラッシュ ダンプ 出現 検知 (今回 実行 開始 後 に 書かれた もの のみ)
    if [[ -f "$BLENDER_CRASH_DUMP" ]]; then
        crash_mtime=$(stat -c %Y "$BLENDER_CRASH_DUMP" 2>/dev/null || echo 0)
        if [[ "$crash_mtime" -gt "$RUN_START_TS" ]]; then
            force_kill_blender_and_exit "Blender が クラッシュ しました (crash.txt 更新 検出: ${BLENDER_CRASH_DUMP} mtime=${crash_mtime})"
        fi
    fi

    # (2) blender.log 停滞 検知 (LOG_STALE_SEC 以上 出力 が 止まって いれば ハング)
    if [[ -f "$BLENDER_LOG" ]]; then
        log_mtime=$(stat -c %Y "$BLENDER_LOG" 2>/dev/null || echo 0)
        log_stale=$((NOW_TS - log_mtime))
        # ただし 起動 直後 は log 出力 が 少ない ので、 RUN_START_TS から 一定 時間 は 様子見
        elapsed_since_start=$((NOW_TS - RUN_START_TS))
        if [[ $elapsed_since_start -gt $LOG_STALE_SEC && $log_stale -gt $LOG_STALE_SEC ]]; then
            force_kill_blender_and_exit "Blender 出力 停滞 (blender.log が ${log_stale}秒 更新 なし、 ハング 判定)"
        fi
    fi

    # (3) blender.exe プロセス 不在 検知 (taskkill 等 で 外部 から 落とされた / クラッシュ 後 自動 終了)
    # 起動 直後 は 検知 を 飛ばす (Blender 起動 と heartbeat 出現 の タイムラグ で 誤検知 する)
    if [[ $((NOW_TS - RUN_START_TS)) -gt 10 ]] && command -v tasklist.exe >/dev/null 2>&1; then
        # `/FI "IMAGENAME ..."` のフィルター名はWindowsの表示言語によって
        # 解釈に失敗することがあるため、全一覧の実行ファイル名を直接検索する。
        # プロセス名自体はASCIIなので、ヘッダーが日本語でも判定できる。
        # tasklist.exe can transiently return an empty list across the WSL
        # boundary.  Only declare process loss when the independent heartbeat
        # has also gone stale.
        if ! is_blender_alive && ! tasklist.exe 2>/dev/null | tr -d '\r' | grep -qi 'blender.exe'; then
            force_kill_blender_and_exit "Blender プロセス が 消滅 しました (tasklist で blender.exe が 見つから ない)"
        fi
    fi
done

# ------------------------------------------------------------
# 結果読出
# ------------------------------------------------------------
RESULT_JSON=$(cat "$RESULT_FILE")
echo "[wrapper] 実行結果: $RESULT_JSON" >&2

# JSON の status を抽出 (jq があれば jq、なければ簡易 grep)
if command -v jq >/dev/null 2>&1; then
    STATUS=$(echo "$RESULT_JSON" | jq -r '.status')
else
    # フォールバック: 単純な文字列パース
    STATUS=$(echo "$RESULT_JSON" | grep -o '"status"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
fi

# exit code 反映 (ok = 0, それ以外 = 1)
if [[ "$STATUS" == "ok" ]]; then
    exit 0
else
    exit 1
fi
