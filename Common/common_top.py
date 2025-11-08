#------------------------------------------------------------------
# = Define (環境毎に変更)
#------------------------------------------------------------------
# Extensions Download Dir
__addon_directory = "C:/Users/..."
#------------------------------------------------------------------
# = Import
#------------------------------------------------------------------
import bpy
import math
import random
import numpy as np
from mathutils import Matrix, Vector
import mathutils
import os
import sys
import bmesh
import requests
import urllib.request
import zipfile
import importlib
import time
import json
import pkgutil
import subprocess
from itertools import combinations
#------------------------------------------------------------------
# = Set Path
#------------------------------------------------------------------
# Get File Path
script_path = bpy.path.abspath(bpy.context.space_data.text.filepath)
script_dir = os.path.dirname(script_path)
# Get Git Root
git_root = subprocess.run(
    ["git", "-C", script_dir, "rev-parse", "--show-toplevel"],
    stdout=subprocess.PIPE, text=True
).stdout.strip()
# Add the parent directory of the root to sys.path
if git_root and git_root not in sys.path:
    sys.path.append(git_root)

import Mylib
# Common Lib
from Mylib import *
import Assets.parts
from Assets.parts import *

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

def import_submodules(package_name):
    """
    指定パッケージ配下のすべてのモジュールを import して辞書で返す
    例：
        modules = import_submodules("Assets.mdl.SAMPLE_MODEL")
        → modules["d00_mdl"] でアクセス可能
    """
    package = importlib.import_module(package_name)
    results = {}

    for loader, name, ispkg in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            short_name = name.split(".")[-1]
            results[short_name] = mod
        except Exception as e:
            print(f"[WARN] Failed to import {name}: {e}")
    return results
#------------------------------------------------------------------
# = Pre Process
#------------------------------------------------------------------
