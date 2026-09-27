import bpy, os, sys, subprocess
# スクリプトディレクトリ（Text Editorのファイルパス基準）
script_path = bpy.path.abspath(bpy.context.space_data.text.filepath)
script_dir = os.path.dirname(script_path)
# Gitルート取得
git_root = subprocess.run(
    ["git", "-C", script_dir, "rev-parse", "--show-toplevel"],
    stdout=subprocess.PIPE, text=True
).stdout.strip()
# ルートの1つ上をsys.pathへ
if git_root and git_root not in sys.path:
    sys.path.append(git_root)
# 共通設定
import Common.common_top as common_top
from Common.common_top import *
#========================================================================================

#------------------------------------------------------------------
# = Auto Reload
#------------------------------------------------------------------
def get_latest_mtime_in_dir(directory):
    latest_mtime = 0
    for root, _, files in os.walk(directory):
        for f in files:
            if f.endswith(".py"):
                full_path = os.path.join(root, f)
                mtime = os.path.getmtime(full_path)
                if mtime > latest_mtime:
                    latest_mtime = mtime
    return latest_mtime

def _auto_reload_modules(modules):
    """
    モジュールリストを再帰的にリロード。
    - サブパッケージも深さ無制限で再帰的に処理
    - 未インポートのサブモジュールも import してリロード
    """
    this_mod = sys.modules[__name__]
    if not hasattr(this_mod, "_file_mtimes"):
        this_mod._file_mtimes = {}

    def reload_if_changed(mod):
        path = getattr(mod, "__file__", None)
        if not path:
            return

        if os.path.basename(path) in ("__init__.py", "__init__.pyc"):
            mtime = get_latest_mtime_in_dir(os.path.dirname(path))
        else:
            mtime = os.path.getmtime(path)

        if mtime != this_mod._file_mtimes.get(path):
            importlib.reload(mod)
            this_mod._file_mtimes[path] = mtime

    def recursive_reload(mod):
        """モジュールとサブパッケージを再帰的にリロード"""
        reload_if_changed(mod)

        if hasattr(mod, "__path__"):  # パッケージの場合のみサブモジュール探索
            for _, subname, ispkg in pkgutil.walk_packages(mod.__path__, mod.__name__ + "."):
                # sys.modules に存在するか確認
                sub_mod = sys.modules.get(subname)
                if not sub_mod:
                    try:
                        sub_mod = importlib.import_module(subname)
                    except Exception as e:
                        print(f"Failed to import {subname}: {e}")
                        continue
                # サブモジュールも再帰
                recursive_reload(sub_mod)

    for mod in modules:
        recursive_reload(mod)

#------------------------------------------------------------------
# = Import
#------------------------------------------------------------------
def import_submodules(package_name):
    """
    指定パッケージ配下のすべてのモジュールを import して辞書で返す
    例：
        modules = import_submodules("Assets.mdl.SAMPLE_MODEL")
        → modules["d00_mdl"] でアクセス可能

    再帰深度抑制 (重要):
        多数のサブモジュールが冒頭で import_submodules("Assets.parts") を呼ぶ構造の場合、
        Python が「ファイル A の冒頭 → import_submodules → ファイル B の import →
        その冒頭で import_submodules → ファイル A 再 import (sys.modules 経由)」
        と再帰的に呼び出される。 importlib.import_module は sys.modules に
        部分初期化中の module が存在してもそれを返すが、 大量の循環呼び出しが続くと
        Python の RecursionError を引き起こす。
        対策として sys.modules に既に登録されている module は import_module を再呼出せず、
        sys.modules から直接取得する (Python の標準挙動と等価だが、 余計な C スタック消費を
        節約できる)。
    """
    package = importlib.import_module(package_name)
    results = {}

    for loader, name, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        # 既に sys.modules に存在するなら importlib.import_module を呼ばずに直接取得
        # (再帰的呼び出しによるスタック消費を抑える)
        if name in sys.modules:
            mod = sys.modules[name]
        else:
            try:
                mod = importlib.import_module(name)
            except Exception as e:
                print(f"[WARN] Failed to import {name}: {e}")
                continue
        short_name = name.split(".")[-1]
        # main除外
        if short_name == "main":
            continue
        results[short_name] = mod
    return results
