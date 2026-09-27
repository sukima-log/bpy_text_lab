# ============================================================
# Main Code — プロジェクト main の呼び出しエントリ
# ============================================================
import bpy, importlib, os, sys, subprocess

# Assets/parts 配下の循環 import 対策
sys.setrecursionlimit(10000)

# git root を sys.path に追加
script_path = bpy.path.abspath(bpy.context.space_data.text.filepath)
git_root = subprocess.run(
    ["git", "-C", os.path.dirname(script_path), "rev-parse", "--show-toplevel"],
    stdout=subprocess.PIPE, text=True
).stdout.strip()
if git_root and git_root not in sys.path:
    sys.path.append(git_root)

# 共通設定 + auto reload
import Common.common_top as common_top
from Common.common_top import *
cm_lib._auto_reload_modules([Mylib, common_top])


# ====================================================================
# = プロジェクト切替 (1行だけ有効化する。複数行を有効化すると後勝ちで上書きされるので注意)
# ====================================================================
from Assets.mdl.SAMPLE_MODEL import main              # サンプルモデル (sukima_logo)

# 新規プロジェクトを Assets/mdl/00_gen_project_dir.sh <PROJECT_NAME> で作成したら
# ここに1行追加し、有効化したい行だけコメントを外して使う
# from Assets.mdl.<PROJECT_NAME> import main
# ====================================================================

# --------------------------------------------------------------------
# 自動化用オーバーライド: 環境変数 BPY_ASSET_MAIN_MODULE が設定されている場合は
# 上のスイッチボードより優先してそのモジュールを呼び出す (Assets. 配下限定)
# --------------------------------------------------------------------
_asset_main_override = os.environ.get("BPY_ASSET_MAIN_MODULE")
if _asset_main_override:
    if not _asset_main_override.startswith("Assets."):
        raise RuntimeError("BPY_ASSET_MAIN_MODULE must be inside Assets: %s" % _asset_main_override)
    main = importlib.import_module(_asset_main_override)


# 選択されたプロジェクト配下も auto reload 対象に追加する
# (import_submodules は再帰import対策で "main" モジュール自体を除外するため、ここで別途追加する)
_proj_pkg = sys.modules.get(main.__name__.rsplit(".", 1)[0])
if _proj_pkg is not None:
    cm_lib._auto_reload_modules([_proj_pkg])


if __name__ == "__main__":
    main.main()

    # Claude Code等のAIエージェントがこのスクリプトを自動実行した場合のみ
    # プレビュー画像・品質チェックレポートを生成する
    # (bpy._claude_run フラグは、エージェント側のBlender起動スクリプトが事前に設定する想定)
    if getattr(bpy, "_claude_run", False):
        from Mylib.claude_preview_lib import render_preview_for_claude
        render_preview_for_claude(
            project_name      = main.__name__.split(".")[-2]
        ,   git_root          = git_root
        ,   reference_ratios  = getattr(main, "reference_ratios", None)
        )
