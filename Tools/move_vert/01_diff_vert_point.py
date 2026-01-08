import bpy
import json
import os
import sys
import bmesh

# Get the current script being executed
script_text = bpy.context.space_data.text

# Get the directory of the current script
script_dir = os.path.dirname(bpy.path.abspath(script_text.filepath))


# --------------------
# インデックス -> カスタムID 変換
# --------------------
def index_to_custom_id(
    obj_name
,   index_list
,   elem_type='EDGE'
):
    """
    インデックス → カスタムID（vid/eid/fid）へ変換する関数
    """

    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        raise ValueError(f"オブジェクト '{obj_name}' が見つからないかメッシュではありません")

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # --- 要素タイプごとにレイヤー設定 ---
    if elem_type == 'VERT':
        layer = bm.verts.layers.int.get("vid")
        elements = bm.verts
        elements.ensure_lookup_table()
    elif elem_type == 'EDGE':
        layer = bm.edges.layers.int.get("eid")
        elements = bm.edges
        elements.ensure_lookup_table()
    elif elem_type == 'FACE':
        layer = bm.faces.layers.int.get("fid")
        elements = bm.faces
        elements.ensure_lookup_table()
    else:
        bm.free()
        raise ValueError("elem_type は 'VERT', 'EDGE', 'FACE' のいずれかにしてください")

    if layer is None:
        bm.free()
        raise ValueError(f"カスタムIDレイヤー '{elem_type.lower()}id' が存在しません")

    # --- インデックスからIDを取得 ---
    ids = []
    N = len(elements)

    for idx in index_list:
        if 0 <= idx < N:
            ids.append(elements[idx][layer])
        else:
            ids.append(-1)

    bm.free()
    return ids

#=================================
# Output Vertex Position Differences
#=================================
def compare_vertex_positions(filepath, output_path):
    # 現在のモードを保存
    current_mode = bpy.context.object.mode

    # Object モードに切り替え
    bpy.ops.object.mode_set(mode='OBJECT')

    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        print("No mesh object is selected.")
        return

    if not os.path.exists(filepath):
        print("Saved vertex file not found.")
        return

    # 以前保存した頂点座標をロード
    with open(filepath, 'r', encoding='utf-8') as f:
        old_coords_dict = json.load(f)

    current_coords = obj.data.vertices
    i_array, x_array, y_array, z_array = [], [], [], []

    for i, v in enumerate(current_coords):
        key = str(i)
        if key in old_coords_dict:
            old = old_coords_dict[key]

            # ワールド座標に変換
            world_co = obj.matrix_world @ v.co

            # 差分計算
            dx = round(world_co.x - old['x'], 4)
            dy = round(world_co.y - old['y'], 4)
            dz = round(world_co.z - old['z'], 4)

            # 微小誤差を0に
            dx = 0.0 if abs(dx) < 1e-4 else dx
            dy = 0.0 if abs(dy) < 1e-4 else dy
            dz = 0.0 if abs(dz) < 1e-4 else dz

            if (dx != 0) or (dy != 0) or (dz != 0):
                i_array.append(i)  # ここは一旦インデックス
                x_array.append(f"{dx:+.4f}")
                y_array.append(f"{dy:+.4f}")
                z_array.append(f"{dz:+.4f}")

    # -----------------------------
    # インデックス → カスタムID に変換
    # mdl_cm_lib.index_to_custom_id を使用
    # -----------------------------
    try:
        i_array = index_to_custom_id(
            obj_name=obj.name,
            index_list=i_array,
            elem_type='VERT'
        )
    except Exception as e:
        print(f"[Warn] index_to_custom_id failed: {e}")
        # 失敗したらそのままインデックスを使う

    # 配列を文字列化
    def format_array(name, array):
        joined = ",".join(str(x) for x in array)
        return f"{name}=[" + joined + "]\n"

    # ファイル出力
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(format_array("i_array", i_array))
        f.write(format_array("x_array", x_array))
        f.write(format_array("y_array", y_array))
        f.write(format_array("z_array", z_array))

    # 元のモードに戻す
    bpy.ops.object.mode_set(mode=current_mode)


filepath = os.path.join(script_dir, "point.json")
output_path = os.path.join(script_dir, "move.py")

# 実行
compare_vertex_positions(filepath, output_path)