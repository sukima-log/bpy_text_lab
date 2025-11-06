#!/bin/bash
set -e

# スクリプトが置かれているディレクトリに移動
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 引数チェック
if [ -z "$1" ]; then
  echo "Usage: $0 <project_name>"
  exit 1
fi

PROJECT_NAME="$1"
PROJECT_DIR="$SCRIPT_DIR/$PROJECT_NAME"

# すでにディレクトリが存在する場合は停止
if [ -d "$PROJECT_DIR" ]; then
  echo "Error: Directory '$PROJECT_DIR' already exists."
  exit 1
fi

#---------------------------------------------------
# プロジェクトディレクトリ作成
#---------------------------------------------------
mkdir -p "$PROJECT_DIR/glb"             # グローバル
mkdir -p "$PROJECT_DIR/wrap"            # Instance
mkdir -p "$PROJECT_DIR/d00_mdl"          # モデリング
mkdir -p "$PROJECT_DIR/d01_uv_unwrap"    # UV展開
mkdir -p "$PROJECT_DIR/d02_mtal"         # マテリアル
mkdir -p "$PROJECT_DIR/d03_bake"         # bake
mkdir -p "$PROJECT_DIR/d04_bone"         # bone
mkdir -p "$PROJECT_DIR/d05_animation"    # animation
mkdir -p "$PROJECT_DIR/d06_shape_key"    # shape_key

# __init__.py 作成
echo "from . import glb_defs" > "$PROJECT_DIR/glb/__init__.py"
echo "from . import sample_obj_wrap" > "$PROJECT_DIR/wrap/__init__.py"
touch "$PROJECT_DIR/wrap/__init__.py"
echo "from . import sample_obj_mdl" > "$PROJECT_DIR/d00_mdl/__init__.py"
touch "$PROJECT_DIR/d01_uv_unwrap/__init__.py"
touch "$PROJECT_DIR/d02_mtal/__init__.py"
touch "$PROJECT_DIR/d03_bake/__init__.py"
touch "$PROJECT_DIR/d04_bone/__init__.py"
touch "$PROJECT_DIR/d05_animation/__init__.py"
touch "$PROJECT_DIR/d06_shape_key/__init__.py"


# main.py 作成（テンプレートコピー + 置換）
cp "$SCRIPT_DIR/../../Common/common_top_main_template.py" "$PROJECT_DIR/main.py"
sed -i "s/{\$PROJECT_NAME}/$PROJECT_NAME/g" "$PROJECT_DIR/main.py"

# README.md 作成（空ファイル）
touch "$PROJECT_DIR/README.md"
echo "from . import wrap" > "$PROJECT_DIR/__init__.py"

#---------------------------------------------------
# テンプレートコピー + 追記 + 置換
#---------------------------------------------------
# glb_defs.py 作成（テンプレートコピー + 追記 + 置換）
cp "$SCRIPT_DIR/../../Common/common_top_sub_template.py" "$PROJECT_DIR/glb/glb_defs.py"
cat "$SCRIPT_DIR/../../Common/common_glb_template.py" >> "$PROJECT_DIR/glb/glb_defs.py"
sed -i "s/{\$PROJECT_NAME}/$PROJECT_NAME/g" "$PROJECT_DIR/glb/glb_defs.py"

# sample_obj_mdl.py 作成（テンプレートコピー + 追記 + 置換）
cp "$SCRIPT_DIR/../../Common/common_top_sub_template.py" "$PROJECT_DIR/d00_mdl/sample_obj_mdl.py"
cat "$SCRIPT_DIR/../../Common/common_sub_template.py" >> "$PROJECT_DIR/d00_mdl/sample_obj_mdl.py"
sed -i "s/{\$PROJECT_NAME}/$PROJECT_NAME/g" "$PROJECT_DIR/d00_mdl/sample_obj_mdl.py"

# sample_obj_wrap.py 作成（テンプレートコピー + 追記 + 置換）
cp "$SCRIPT_DIR/../../Common/common_top_sub_template.py" "$PROJECT_DIR/wrap/sample_obj_wrap.py"
cat "$SCRIPT_DIR/../../Common/common_wrap_template.py" >> "$PROJECT_DIR/wrap/sample_obj_wrap.py"
sed -i "s/{\$PROJECT_NAME}/$PROJECT_NAME/g" "$PROJECT_DIR/wrap/sample_obj_wrap.py"

echo "Project '$PROJECT_NAME' created successfully in $PROJECT_DIR"
