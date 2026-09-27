"""
Claude Code 用 Blender 永続実行ブートストラップ
============================================================

役割:
    Blender を起動しっぱなしにして、トリガーファイル経由で
    main.py の再実行を受け付ける。
    起動コスト (約 5 秒) を毎回支払うのではなく初回のみ支払い、
    以降の反復ループは Blender 起動済みの状態で実行する。

仕組み:
    1. Blender 起動 (このスクリプトが --python で読み込まれる)
    2. UI 初期化を待ってからポーリングタイマー登録 (0.5 秒間隔)
    3. タイマーが以下を実行:
       - heartbeat ファイル更新 (ラッパーが生存確認に使う)
       - stop ファイル検出 → Blender 終了
       - trigger ファイル検出 → main.py 1 回実行 + 結果書出
    4. ラッパー終了後も Blender は稼働継続 (次のトリガー待ち)

シーン状態:
    各イテレーションの開始時に bpy.ops.wm.read_factory_settings(use_empty=True)
    でシーンを完全リセットする。これにより:
      - 前回イテレーションの副作用 (生成済オブジェクト等) が残らない
      - コード修正後の再実行で「glb_exist_obj_chk による生成スキップ」が
        起きずに新しいモデリングが走る
      - 手動 Run Script の「閉じて再起動して実行」と同等の状態

通信プロトコル (PROJECT_ROOT/.claude_blender_comm/):
    - heartbeat.txt : ブートストラップが ~0.5 秒ごとに更新する Unix タイムスタンプ
                      ラッパー側はこの値が古ければ Blender 死亡と判断
    - trigger.txt   : ラッパーが書き込む実行リクエスト (内容は任意、存在自体がトリガー)
    - result.txt    : ブートストラップが書き込む実行結果 JSON
                      {"status": "ok"|"error", "error": null|str, "elapsed_sec": float}
    - stop.txt      : ラッパーが書き込む停止リクエスト (存在で Blender 終了)
    - bootstrap.log : ブートストラップの自前ログ (デバッグ用)
============================================================
"""

import bpy
import os
import sys
import time
import json
import traceback
import threading


# ============================================================
# パス解決
# ============================================================
THIS_FILE = os.path.abspath(__file__)
TOOLS_DIR = os.path.dirname(THIS_FILE)
PROJECT_ROOT = os.path.dirname(TOOLS_DIR)
MAIN_PY = os.path.join(PROJECT_ROOT, "Assets", "main.py")

# main.py の存在チェック
if not os.path.isfile(MAIN_PY):
    print(
        f"[ブートストラップエラー] main.py が見つかりません: {MAIN_PY}"
    ,   file=sys.stderr
    )
    sys.exit(1)

# 通信ディレクトリ (プロジェクト内、WSL/Windows 両側からアクセス可能)
COMM_DIR = os.path.join(PROJECT_ROOT, ".claude_blender_comm")
os.makedirs(COMM_DIR, exist_ok=True)

# 通信ファイル定義
HEARTBEAT_FILE = os.path.join(COMM_DIR, "heartbeat.txt")
TRIGGER_FILE   = os.path.join(COMM_DIR, "trigger.txt")
RESULT_FILE    = os.path.join(COMM_DIR, "result.txt")
STOP_FILE      = os.path.join(COMM_DIR, "stop.txt")
BOOT_LOG_FILE  = os.path.join(COMM_DIR, "bootstrap.log")


# ============================================================
# ブートストラップ自身のログ書き出し (デバッグ用)
# ============================================================
def _log(msg):
    """通信ディレクトリの bootstrap.log にタイムスタンプ付きでログを追記する

    Input:
        msg (str): ログメッセージ

    Output:
        None (ファイル書き出し失敗時は無視)
    """
    try:
        with open(BOOT_LOG_FILE, mode="a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        # ログ書き失敗で本体を止めない
        pass


# ============================================================
# Python レベルのシーンクリア (read_factory_settings は使わない)
# ============================================================
# read_factory_settings(use_empty=True) は Blender 状態を完全リセットするが
# bpy.app.timers も消去してしまうため、本ブートストラップのポーリングが止まる。
# (persistent=True を指定しても 5.0.1 では消える事象を観測した)
# よって Python レベルで bpy.data.* を逐次削除する方式でシーンを空にする。
def _clear_blender_data():
    """シーン内の全データブロックを削除する (Blender 内部のタイマーには影響なし)

    Input:
        なし

    Output:
        None (bpy.data.* を空にする副作用)
    """
    # 全オブジェクトを削除 (Object data block)
    for obj in list(bpy.data.objects):
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass

    # マスターコレクション以外のコレクションを削除
    scene = bpy.context.scene
    master_collection = scene.collection if scene else None
    for col in list(bpy.data.collections):
        if col != master_collection:
            try:
                bpy.data.collections.remove(col)
            except Exception:
                pass

    # 各種データブロックを削除 (孤立したものも含めて完全に消す)
    # 順番: 上位 (オブジェクト依存元) から消す
    for collection_attr in (
        "meshes"        # メッシュ
    ,   "materials"     # マテリアル
    ,   "textures"      # テクスチャ
    ,   "images"        # 画像
    ,   "lights"        # ライト
    ,   "cameras"       # カメラ
    ,   "armatures"     # アーマチュア
    ,   "curves"        # カーブ
    ,   "actions"       # アクション
    ,   "lattices"      # ラティス
    ,   "metaballs"     # メタボール
    ,   "fonts"         # フォント
    ,   "speakers"      # スピーカー
    ,   "particles"     # パーティクル
    ,   "node_groups"   # ノードグループ
    ,   "shape_keys"    # シェイプキー
    ,   "texts"         # テキストデータ (main.py の Text data block も含む)
    ):
        coll = getattr(bpy.data, collection_attr, None)
        if coll is None:
            continue
        for item in list(coll):
            try:
                coll.remove(item)
            except Exception:
                # 削除できない (まだ参照されている等) ものはスキップ
                pass


def _clear_python_module_state():
    """既存モデリングコードが Python レベルで保持する状態 (EXIST_FLAG_DICT 等) をクリア

    Input:
        なし

    Output:
        None
    """
    # sys.modules を走査して EXIST_FLAG_DICT を持つモジュールを見つけてクリア
    # (glb_defs.py 等に含まれる「生成済みオブジェクト記録用 dict」をリセット)
    for mod_name in list(sys.modules.keys()):
        mod = sys.modules.get(mod_name)
        if mod is None:
            continue
        # 既知のステートフル属性を順にチェック
        for attr_name in ("EXIST_FLAG_DICT",):
            if hasattr(mod, attr_name):
                try:
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, dict):
                        attr.clear()
                except Exception:
                    pass


# ============================================================
# Factory startup のデフォルトオブジェクトを削除 (起動直後に1回だけ呼ぶ)
# ============================================================
def _delete_factory_defaults():
    """factory-startup の Cube / Light / Camera を削除

    Input:
        なし

    Output:
        None (bpy.data.objects から該当オブジェクトを削除する副作用)
    """
    for default_name in ("Cube", "Light", "Camera"):
        obj = bpy.data.objects.get(default_name)
        if obj is not None:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception:
                pass


# ============================================================
# 1 イテレーション分の main.py 実行
# ============================================================
def _execute_main_iteration(delete_objects=None, clear_all=False):
    """事前のオブジェクト削除 (任意) → main.py を text.run_script で実行

    既存コードの選択的再生成パターン (glb_exist_obj_chk) を活かすため、
    既定では何もシーン操作を行わず main.py をそのまま実行する。
    呼び出し側 (ラッパー) が削除指定した場合のみ、対象オブジェクトを
    bpy.data.objects から削除する → 再実行時に該当オブジェクトのみ再生成される。

    Input:
        delete_objects (list[str] | None): 削除対象オブジェクト名のリスト
                                           (None や空なら削除なし、現状維持)
        clear_all      (bool): True なら全シーン状態をクリア (フル再生成)
                               False (既定) なら既存オブジェクトは維持

    Output:
        bool : True = 成功 (run_script が FINISHED を返した)
               False = 失敗 (run_script が CANCELLED 等)
    """
    # ----------------------------------------------------------------
    # シーン状態の調整 (オプション)
    # ----------------------------------------------------------------
    if clear_all:
        # フル再生成モード: 全データ削除 + Python 側ステート初期化
        _clear_blender_data()
        _clear_python_module_state()
    elif delete_objects:
        # 選択削除モード: 指定オブジェクトのみ bpy.data.objects から削除
        # (削除されたオブジェクトは glb_exist_obj_chk が「無し」と判定するため
        #  main.py 実行時に該当部分のみ再生成される)
        for obj_name in delete_objects:
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                try:
                    bpy.data.objects.remove(obj, do_unlink=True)
                except Exception:
                    pass
    # else: 何もしない (既存オブジェクトはそのまま、main.py 実行で差分のみ更新)

    # ----------------------------------------------------------------
    # Claude 実行マーカー (毎回明示的に設定)
    # ----------------------------------------------------------------
    # main.py 側がプレビュー出力分岐に使う
    bpy._claude_run = True

    # ----------------------------------------------------------------
    # main.py を Text data block としてロード
    # ----------------------------------------------------------------
    # 各イテレーションでファイルから読み直すため、main.py への変更は確実に反映される
    text = bpy.data.texts.load(filepath=MAIN_PY)

    # ----------------------------------------------------------------
    # TEXT_EDITOR エリアを準備
    # ----------------------------------------------------------------
    # factory_settings リセット後はデフォルトレイアウト (TEXT_EDITOR が無い) のため
    # 毎回エリア準備が必要
    wm = bpy.context.window_manager
    if not wm.windows:
        raise RuntimeError(
            "Blender ウィンドウが存在しません (GUI モードで起動されていない可能性)"
        )

    target_window = wm.windows[0]
    target_screen = target_window.screen

    # TEXT_EDITOR エリアを探す or 作る
    text_area = None
    for area in target_screen.areas:
        if area.type == "TEXT_EDITOR":
            text_area = area
            break
    if text_area is None:
        # 最初のエリアを TEXT_EDITOR に変換
        text_area = target_screen.areas[0]
        text_area.type = "TEXT_EDITOR"

    # アクティブテキスト設定 (これが bpy.context.space_data.text の元になる)
    text_area.spaces.active.text = text

    # WINDOW タイプの region を取得 (text editor 内の文字表示領域)
    text_region = None
    for region in text_area.regions:
        if region.type == "WINDOW":
            text_region = region
            break

    # ----------------------------------------------------------------
    # text editor コンテキストで run_script を実行
    # ----------------------------------------------------------------
    # 「テキストエディタで Alt+P 押下」と等価
    with bpy.context.temp_override(
        window     = target_window
    ,   area       = text_area
    ,   region     = text_region
    ,   space_data = text_area.spaces.active
    ,   edit_text  = text
    ):
        result = bpy.ops.text.run_script()

    # run_script は Python 例外時 {'CANCELLED'} を返す
    # (例外の traceback は Blender が stderr に出力済み)
    return result == {"FINISHED"}


# ============================================================
# ポーリングループ (0.5 秒間隔)
# ============================================================
def _claude_persistent_loop():
    """Blender イベントループ上で 0.5 秒ごとに呼ばれる監視タイマー

    Input:
        なし (各種ファイルパスはグローバル変数を参照)

    Output:
        float : 次回呼出までの秒数 (0.5 秒固定でループ継続)
        None  : タイマー解除 (Blender 終了処理時)
    """
    try:
        # heartbeat 更新は専用スレッド (_heartbeat_writer) 側で常時行われる
        # (main.py 実行中で本タイマーが停止していてもスレッドは動き続ける)

        # ------------------------------------------------------------
        # stop トリガー検出 → Blender 終了
        # ------------------------------------------------------------
        if os.path.exists(STOP_FILE):
            try:
                os.remove(STOP_FILE)
            except Exception:
                pass
            _log("stop ファイル検出: Blender を終了します")
            try:
                bpy.ops.wm.quit_blender()
            except Exception:
                # quit_blender 失敗時は強制終了
                os._exit(0)
            return None  # タイマー解除

        # ------------------------------------------------------------
        # 実行トリガー検出
        # ------------------------------------------------------------
        if os.path.exists(TRIGGER_FILE):
            # トリガーファイルの中身 (JSON) を読み取ってから削除
            # 想定フォーマット:
            #   - 空 / 数値タイムスタンプ            → 削除なし、main.py 実行のみ
            #   - {"delete": ["obj1", "obj2", ...]}  → 指定オブジェクトを削除して main.py 実行
            #   - {"clear": true}                    → 全シーン状態クリアしてから main.py 実行
            trigger_content = ""
            try:
                with open(TRIGGER_FILE, mode="r", encoding="utf-8") as f:
                    trigger_content = f.read().strip()
            except Exception:
                pass
            try:
                os.remove(TRIGGER_FILE)
            except Exception:
                pass

            # トリガー JSON のパース (失敗時は空 dict 扱いで「削除なし実行」)
            spec = {}
            if trigger_content and trigger_content.startswith("{"):
                try:
                    spec = json.loads(trigger_content)
                    if not isinstance(spec, dict):
                        spec = {}
                except Exception:
                    spec = {}

            delete_objects = spec.get("delete") if isinstance(spec.get("delete"), list) else None
            clear_all      = bool(spec.get("clear"))

            _log(f"trigger 検出: main.py 実行開始 (clear={clear_all}, delete={delete_objects})")
            t_start = time.time()
            result_data = {
                "status":      "ok"
            ,   "error":       None
            ,   "elapsed_sec": 0.0
            }

            try:
                ok = _execute_main_iteration(
                    delete_objects = delete_objects
                ,   clear_all      = clear_all
                )
                result_data["elapsed_sec"] = round(time.time() - t_start, 2)
                if not ok:
                    result_data["status"] = "error"
                    result_data["error"]  = "main.py 実行で Python 例外が発生 (詳細は Blender stderr 参照)"
            except Exception as e:
                # ブートストラップ側での想定外例外
                traceback.print_exc()
                result_data["status"]      = "error"
                result_data["error"]       = f"{type(e).__name__}: {e}"
                result_data["elapsed_sec"] = round(time.time() - t_start, 2)

            # 結果ファイル書出
            try:
                with open(RESULT_FILE, mode="w", encoding="utf-8") as f:
                    json.dump(
                        obj          = result_data
                    ,   fp           = f
                    ,   ensure_ascii = False
                    )
                _log(f"main.py 実行完了: {result_data}")
            except Exception:
                traceback.print_exc()

    except Exception:
        # タイマー内例外で停止しないよう全例外を捕捉
        traceback.print_exc()

    # ループ継続: 0.5 秒後に再呼出
    return 0.5


# ============================================================
# 起動時処理
# ============================================================
# 古い heartbeat / result / trigger / stop を消す
# (前回 Blender の残骸でラッパーが誤判定しないように)
for _f in (HEARTBEAT_FILE, RESULT_FILE, TRIGGER_FILE, STOP_FILE):
    if os.path.exists(_f):
        try:
            os.remove(_f)
        except Exception:
            pass

# bootstrap.log は append 運用なので起動時にクリアする
try:
    open(BOOT_LOG_FILE, mode="w").close()
except Exception:
    pass

_log(f"ブートストラップ起動: PROJECT_ROOT={PROJECT_ROOT}")


# ============================================================
# heartbeat 更新スレッド (Blender メインスレッドと独立して動作)
# ============================================================
# bpy.app.timers は main.py 実行中 (= text.run_script ブロック中) に止まるため
# heartbeat 更新を timers 内に置くと「実行中は heartbeat が止まる」状態になる。
# ラッパー側はこれを「Blender 死亡」と誤判定し再起動してしまう。
#
# 対策として heartbeat 更新を専用デーモンスレッドに分離する。
# main.py 実行中もスレッドは動き続け、heartbeat が定期的に更新される。
# (ファイル書き込みのみで bpy API は呼ばないためスレッド安全)
_heartbeat_stop_event = threading.Event()


def _heartbeat_writer_thread():
    """0.5 秒間隔で HEARTBEAT_FILE に現在時刻を書き続ける常駐スレッド

    Input:
        なし

    Output:
        None (HEARTBEAT_FILE を継続更新する副作用)
    """
    while not _heartbeat_stop_event.is_set():
        try:
            # 現在の Unix タイムスタンプを書き込む
            with open(HEARTBEAT_FILE, mode="w", encoding="utf-8") as f:
                f.write(str(int(time.time())))
        except Exception:
            # I/O 失敗は無視 (次回試行)
            pass
        # 0.5 秒待機 (stop event がセットされたら即座に抜ける)
        _heartbeat_stop_event.wait(0.5)


# デーモンスレッドとして起動 (Blender 終了時に自動停止)
_heartbeat_thread = threading.Thread(
    target = _heartbeat_writer_thread
,   daemon = True
,   name   = "claude_heartbeat"
)
_heartbeat_thread.start()
_log("heartbeat スレッド起動")


# ============================================================
# UI 初期化を待ってからポーリングループ登録
# ============================================================
def _start_loop():
    """UI 初期化完了後に呼ばれ、本ポーリングループをタイマー登録する

    Input:
        なし

    Output:
        None (1 回限り、再登録なし)
    """
    # ----------------------------------------------------------------
    # factory-startup のデフォルトオブジェクト (Cube, Light, Camera) を削除
    # ----------------------------------------------------------------
    # これらが残ったままだとプレビューレンダリングや BB 計算に影響するため
    # 起動時に1度だけ削除する。Python レベル削除なのでタイマーには影響しない。
    _delete_factory_defaults()
    _log("factory-startup default オブジェクト削除完了")

    _log("UI 初期化完了: ポーリングループ開始")
    # ポーリングループを 0.0 秒後 (=次のイベントループ tick) から開始
    # persistent=True で各種リセット操作を生き延びる
    bpy.app.timers.register(
        _claude_persistent_loop
    ,   first_interval = 0.0
    ,   persistent     = True
    )
    return None  # 1 回限り


# UI 初期化完了を 0.5 秒待機してから _start_loop を呼ぶ
# persistent=True を指定: read_factory_settings() で Blender 状態がリセットされても
# このタイマーは生き残る (永続モードでイテレーション間にシーンリセットを行うため必須)
bpy.app.timers.register(
    _start_loop
,   first_interval = 0.5
,   persistent     = True
)
