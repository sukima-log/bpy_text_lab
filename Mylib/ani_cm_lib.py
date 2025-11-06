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
from Common.common_top import *
#========================================================================================


# ========================================================================
# = ▼ Select Active Object & Select Armature and Bone
# ========================================================================
def active_object_select_ext(
    object_name_list=[]
,   bone_name=None
,   mode='OBJECT'
):
    # 通常オブジェクトを選択
    # active_object_select(["Cube"])
    # Armatureオブジェクトを選択（OBJECTモード）
    # active_object_select(["Armature"])
    # Armature内のボーンを選択（POSEモードで）
    # active_object_select(["Armature"], bone_name="Bone", mode="POSE")
    # Armature内のボーンを編集モードで選択
    # active_object_select(["Armature"], bone_name="Bone.001", mode="EDIT")
    
    # 指定されたオブジェクトを選択し、最後のオブジェクトをアクティブ化
    # bone_nameが指定された場合は、アーマチュアのボーンも選択
    # mode: 'OBJECT' / 'EDIT' / 'POSE'
    
    # --- Save current mode safely ---
    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    # --- Ensure OBJECT mode ---
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # --- Deselect all objects ---
    bpy.ops.object.select_all(action='DESELECT')

    active_obj = None
    for obj_name in object_name_list:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.select_set(True)
            active_obj = obj

    if not active_obj:
        print("[Warning] No object found in list:", object_name_list)
        return None

    # --- Set the active object ---
    bpy.context.view_layer.objects.active = active_obj

    # --- If bone_name is given, switch to appropriate mode ---
    if bone_name and active_obj.type == 'ARMATURE':
        try:
            bpy.ops.object.mode_set(mode=mode)
        except:
            bpy.ops.object.mode_set(mode='POSE')  # fallback

        # Select bone
        arm = active_obj
        bones = (
            arm.pose.bones if mode == 'POSE'
            else arm.data.edit_bones if mode == 'EDIT'
            else None
        )

        if bones and bone_name in bones:
            for b in bones:
                b.select = False
            bones[bone_name].select = True
            if mode == 'EDIT':
                arm.data.edit_bones.active = bones[bone_name]
            elif mode == 'POSE':
                arm.data.bones.active = bones[bone_name]
        else:
            print(f"[Error] Bone '{bone_name}' not found in Armature '{arm.name}'.")

    # --- Restore mode if bone not specified ---
    elif mode == 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass

    return active_obj

# ========================================================================
# = ▼ Select Bone HEAD or TAIL
# ========================================================================
def select_edit_bone_head_tail(
    armature_obj,
    bone_name_list,
    select_part='HEAD'
):
    # EDITモードのArmatureオブジェクトで、指定ボーンのHEADまたはTAILを選択
    # armature_obj: bpy.types.Object またはオブジェクト名 (str)
    # bone_name_list: ボーン名またはボーン名リスト
    # select_part: 'HEAD' または 'TAIL'
    
    # --- Get Object ---
    if isinstance(armature_obj, str):
        armature_obj = bpy.data.objects.get(armature_obj)
        if not armature_obj:
            print(f"[Error] Object '{armature_obj}' not found")
            return None

    if armature_obj.type != 'ARMATURE':
        print(f"[Error] Object '{armature_obj.name}' is not an Armature")
        return None

    # --- 単一指定もリストに統一 ---
    if isinstance(bone_name_list, str):
        bone_name_list = [bone_name_list]

    # --- 既存のボーン選択をすべて解除 ---
    for b in armature_obj.data.edit_bones:
        b.select = False
        b.select_head = False
        b.select_tail = False

    active_bone = None

    # --- 対象ボーンを選択 ---
    for bone_name in bone_name_list:
        edit_bone = armature_obj.data.edit_bones.get(bone_name)
        if not edit_bone:
            print(f"[Error] Bone '{bone_name}' not found in Armature '{armature_obj.name}'")
            continue

        edit_bone.select = True

        if select_part.upper() == 'HEAD':
            edit_bone.select_head = True
            edit_bone.select_tail = False
        elif select_part.upper() == 'TAIL':
            edit_bone.select_head = False
            edit_bone.select_tail = True
        else:
            print("[Error] select_part must be 'HEAD' or 'TAIL'")
            return None

        active_bone = edit_bone

    # --- アクティブボーン設定 ---
    if active_bone:
        armature_obj.data.edit_bones.active = active_bone

    return bone_name_list


# ========================================================================
# = ▼ Bone extrude
# ========================================================================
def extrude_edit_bone(
    armature_obj,          # bpy.types.Object または名前 (str)
    bone_name,             # 押し出す元ボーン名
    extrude_vec=(0,0,1),   # 押し出す方向ベクトル
    select_part='TAIL',    # 押し出し基準 'HEAD' または 'TAIL'
    symmetric=False        # 左右対称押し出しなら True
):
    # EditモードのボーンをHEAD/Tail基準で押し出し、左右対称押し出しにも対応。
    # 親子接続を保持して新しいボーンを作成。

    if (select_part == "TAIL"):
        select_edit_bone_head_tail(
            armature_obj=armature_obj
        ,   bone_name=bone_name
        ,   select_part=select_part
        )
        if (symmetric):
            # Bone 左右対称 押し出し
            bpy.ops.armature.extrude_forked(
                ARMATURE_OT_extrude={"forked":True}
            ,   TRANSFORM_OT_translate={
                    "value":extrude_vec
                ,   "orient_type":'GLOBAL'
                }
            )
        else:
            bpy.ops.armature.extrude_move(
                ARMATURE_OT_extrude={"forked":False}
            ,   TRANSFORM_OT_translate={
                    "value":extrude_vec
                ,   "orient_type":'GLOBAL'
                }
            )
    else:
        # --- Get Object ---
        if isinstance(armature_obj, str):
            obj_name = armature_obj
            armature_obj = bpy.data.objects.get(obj_name)
            if not armature_obj:
                print(f"[Error] Armature '{obj_name}' not found")
                return None
        if armature_obj.type != 'ARMATURE':
            print(f"[Error] Object '{armature_obj.name}' is not an Armature")
            return None

        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode='EDIT')
        ebones = armature_obj.data.edit_bones

        # --- 元ボーン取得 ---
        base_bone = ebones.get(bone_name)
        if not base_bone:
            print(f"[Error] Bone '{bone_name}' not found in Armature '{armature_obj.name}'")
            return None

        # --- 押し出し基準のHEAD/Tail位置を取得 ---
        if select_part.upper() == 'HEAD':
            base_pos = base_bone.head.copy()
        elif select_part.upper() == 'TAIL':
            base_pos = base_bone.tail.copy()
        else:
            print("[Error] select_part must be 'HEAD' or 'TAIL'")
            return None

        new_bones = []

        # --- 変換追加（extrude_vec をローカル座標に変換）---
        extrude_vec = armature_obj.matrix_world.inverted().to_3x3() @ Vector(extrude_vec)

        # --- 左右対称押し出しも含めて新しいボーンを作成 ---
        offsets = [Vector(extrude_vec)]
        if symmetric:
            offsets.append(Vector((-extrude_vec[0], -extrude_vec[1], extrude_vec[2])))

        for off in offsets:
            # 新しいボーン名 (Blender内部処理の命名規則で別名不可)
            new_name = f"{base_bone.name}_L"
            if symmetric and len(new_bones) == 1:
                new_name = f"{base_bone.name}_R"
            elif symmetric and len(new_bones) > 1:
                new_name += new_name + "_ext"

            # 新しいボーン作成
            new_bone = ebones.new(new_name)

            # HEAD/Tail 基準で位置を設定
            if select_part.upper() == 'HEAD':
                new_bone.head = base_pos
                new_bone.tail = base_pos + off
            else:  # TAIL 基準
                new_bone.tail = base_pos
                new_bone.head = base_pos - off

            # 親子接続
            new_bone.parent = base_bone
            new_bone.use_connect = (select_part.upper() == 'TAIL')  # Tail基準なら接続

            # 選択状態
            new_bone.select = True
            ebones.active = new_bone

            new_bones.append(new_bone)

        # --- アクティブボーンを最後に押し出したものに ---
        ebones.active = new_bones[-1]

        return new_bones if symmetric else new_bones[0]

# ========================================================================
# = ▼ Weight Paint: Bone Select
# ========================================================================
def select_bone_in_weightpaint(
    obj_name
,   bone_name
):
    # Weight Paintモードでボーン名に対応する頂点グループを選択。
    # obj : bpy.types.Object (メッシュオブジェクト)
    # bone_name : str (ボーン名 / 頂点グループ名)

    obj = bpy.data.objects[obj_name]

    # メッシュオブジェクトであることを確認
    if obj.type != 'MESH':
        print(f"[Error] Object '{obj.name}' is not a Mesh")
        return
    
    # Weight Paint モードに切り替え
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
    
    # 頂点グループをアクティブにする
    vg = obj.vertex_groups.get(bone_name)
    if not vg:
        print(f"[Error] Vertex Group '{bone_name}' not found in '{obj.name}'")
        return
    
    obj.vertex_groups.active_index = obj.vertex_groups.find(bone_name)

# ========================================================================
# = ▼ Weight Paint: Vertex Set
# ========================================================================
def set_vertex_group_weight(
    obj_name: str,              # オブジェクト名
    group_name: str,            # 頂点グループ名（ボーン名など）
    vertex_indices: list[int],  # ウェイトを設定する頂点番号リスト
    weight: float,              # ウェイト値（0.0 ～ 1.0）
    mode: str = "REPLACE"       # "REPLACE" or "ADD" or "SUBTRACT"
):
    # 頂点グループのウェイトを設定または加算
    
    # Parameters
    # ----------
    # obj_name : str
    #     対象オブジェクト名
    # group_name : str
    #     対象頂点グループ名
    # vertex_indices : list[int]
    #     ウェイトを設定する頂点インデックス
    # weight : float
    #     設定または加算するウェイト値
    # mode : str
    #     "REPLACE"（上書き）, "ADD"（加算）, "SUBTRACT"（減算）
    
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        raise ValueError(f"Object '{obj_name}' not found")

    # 頂点グループを取得または作成
    vg = obj.vertex_groups.get(group_name)
    if not vg:
        vg = obj.vertex_groups.new(name=group_name)
    
    # ウェイト設定
    for vi in vertex_indices:
        vg.add([vi], weight, mode)

# ========================================================================
# = ▼ Weight Paint: Liner gradient
# ========================================================================
def weight_gradient_along_bone_connected_only(
    obj_name,
    bone_name,
    start_weight=1.0,
    end_weight=0.0,
    radius=0.7
):
    obj = bpy.data.objects[obj_name]
    arm = obj.find_armature()
    if not arm:
        raise ValueError("Object is not bound to any armature")

    bone = arm.data.bones.get(bone_name)
    if not bone:
        raise ValueError(f"Bone '{bone_name}' not found")

    vg = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)

    # ボーンの位置情報
    head = arm.matrix_world @ bone.head_local
    tail = arm.matrix_world @ bone.tail_local
    bone_dir = (tail - head).normalized()
    bone_len = (tail - head).length

    # --- メッシュの接続コンポーネントを抽出 ---
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    islands = []
    visited = set()

    for v in bm.verts:
        if v.index in visited:
            continue
        # 接続している頂点群を取得
        island = set()
        stack = [v]
        while stack:
            vi = stack.pop()
            if vi.index in visited:
                continue
            visited.add(vi.index)
            island.add(vi.index)
            for e in vi.link_edges:
                stack.append(e.other_vert(vi))
        islands.append(island)

    # --- 各アイランドの代表点（重心）を計算 ---
    island_centers = []
    for island in islands:
        avg = Vector()
        for idx in island:
            avg += obj.matrix_world @ me.vertices[idx].co
        avg /= len(island)
        island_centers.append(avg)

    # --- ボーンに最も近いアイランドのみ選択 ---
    min_dist = float('inf')
    target_island_index = None
    for i, center in enumerate(island_centers):
        # ボーン軸への最短距離を計算
        to_center = center - head
        proj_len = max(0.0, min(to_center.dot(bone_dir), bone_len))
        closest_point = head + proj_len * bone_dir
        dist = (center - closest_point).length
        if dist < min_dist:
            min_dist = dist
            target_island_index = i

    if target_island_index is None:
        bm.free()
        raise RuntimeError("No connected mesh found near the bone")

    target_island = islands[target_island_index]

    # --- 対象アイランドの頂点にウェイト設定 ---
    for idx in target_island:
        v = me.vertices[idx]
        co_world = obj.matrix_world @ v.co
        to_v = co_world - head
        proj_len = to_v.dot(bone_dir)
        proj_len_clamped = min(max(proj_len, 0), bone_len)
        closest_point = head + proj_len_clamped * bone_dir
        dist = (co_world - closest_point).length

        if dist < radius:
            t = proj_len_clamped / bone_len
            w = (1 - t) * start_weight + t * end_weight
            fade = 1 - (dist / radius)
            vg.add([v.index], w * fade, 'REPLACE')

    bm.free()


# ========================================================================
# = ▼ Bone: Parent / Children
# ========================================================================
def set_bone_parent(
    armature_name
,   child_bone_name
,   parent_bone_name
,   use_connect=False
):
    # Armature内のボーンに親子関係を設定
    # Parameters
    # ----------
    # armature_name : str
    #     Armatureオブジェクトの名前
    # child_bone_name : str
    #     親を設定したい子ボーンの名前
    # parent_bone_name : str
    #     親となるボーンの名前
    # use_connect : bool
    #     Trueにするとボーンを物理的に接続する（親の先端と子の根元を連結）

    # --- Get Object: Armature ---
    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj or arm_obj.type != 'ARMATURE':
        print(f"[Error] 指定されたオブジェクト '{armature_name}' は存在しないかArmatureではありません。")
        return False

    # --- アクティブ設定 & Editモードに変更 ---
    bpy.context.view_layer.objects.active = arm_obj
    if bpy.context.mode != 'EDIT_ARMATURE':
        bpy.ops.object.mode_set(mode='EDIT')

    # --- Edit Bone取得 ---
    edit_bones = arm_obj.data.edit_bones
    child_bone = edit_bones.get(child_bone_name)
    parent_bone = edit_bones.get(parent_bone_name)

    if not child_bone:
        print(f"[Error] 子ボーン '{child_bone_name}' が見つかりません。")
        return False
    if not parent_bone:
        print(f"[Error] 親ボーン '{parent_bone_name}' が見つかりません。")
        return False

    # --- すでに同じ親が設定されている場合はスキップ ---
    if child_bone.parent == parent_bone and child_bone.use_connect == use_connect:
        return True

    # --- 親子設定を実行 ---
    child_bone.parent = parent_bone
    child_bone.use_connect = use_connect

    return True

# ========================================================================
# = ▼ Animation : Insert Flame
# ========================================================================
def insert_keyframe(
    obj_name="obj_name"
,   frame=1
,   data_path="location"
,   value=None # (0, 0, 0)
,   index=-1
):
    # 任意のオブジェクトにキーフレームを打つ関数
    # obj: 対象オブジェクト
    # frame: フレーム番号
    # data_path: "location", "rotation_euler", "scale" など
    # value: 値 (Noneなら現在値) (0, 0, 0)
    # index: 軸指定 [-1]:all, [0]:x, [1]:y, [2]:z
    obj = bpy.data.objects[obj_name]
    scene = bpy.context.scene
    scene.frame_set(frame)
    if value is not None:
        setattr(obj, data_path, value)
    obj.keyframe_insert(data_path=data_path, index=index)

# ========================================================================
# = ▼ Animation : Insert Flame
# ========================================================================
def insert_pose_bone_keyframe(
    armature_name="armature_name"
,   bone_name="bone_name"
,   frame=1
,   data_path="location"
,   value=None  # (0, 0, 0)
):
    arm_obj = bpy.data.objects[armature_name]
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    
    pbone = arm_obj.pose.bones[bone_name]
    bpy.context.scene.frame_set(frame)

    if value is not None:
        # rotation_euler なら Euler に変換して代入
        if data_path == "rotation_euler":
            pbone.rotation_mode = 'XYZ'
            pbone.rotation_euler = mathutils.Euler(value, 'XYZ')
        else:
            setattr(pbone, data_path, value)

    pbone.keyframe_insert(data_path=data_path)



# ================================================================
# = ▼ キーフレーム選択
# ================================================================
def select_pose_bone_keyframes(
    armature_name: str,
    bone_name: str,
    data_path: str = "rotation_euler",
    frame_list=None,
    axis: str | None = None
):
    import bpy

    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
        print(f"[Error] {armature_name} に有効なアクションがありません。")
        return []

    action = arm_obj.animation_data.action
    selected_keys = []

    axis_map = {"X": 0, "Y": 1, "Z": 2}
    target_index = axis_map.get(axis.upper()) if axis else None

    # --- すべてのボーン・F-Curveのキーフレームを deselect ---
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.select_control_point = False
            kp.select_left_handle = False
            kp.select_right_handle = False

    # --- 指定ボーン・指定軸のキーフレームを選択 ---
    for fc in action.fcurves:
        # 対象ボーンの F-Curve でない場合はスキップ
        if not fc.data_path.startswith(f'pose.bones["{bone_name}"].{data_path}'):
            continue

        # 軸指定があり対象でない場合はスキップ
        if target_index is not None and fc.array_index != target_index:
            continue

        for kp in fc.keyframe_points:
            if frame_list is None or int(round(kp.co.x)) in frame_list:
                kp.select_control_point = True
                kp.select_left_handle = True
                kp.select_right_handle = True
                selected_keys.append((fc, kp))

    return selected_keys


# ================================================================
# = ▼ キーフレーム選択（アーマチュア & 通常オブジェクト対応版）
# ================================================================
def select_object_keyframes(
    object_name: str,
    bone_name: str | None = None,
    data_path: str = "rotation_euler",
    frame_list=None,
    axis: str | None = None
):
    # 指定オブジェクト（またはアーマチュアボーン）の特定データパスに対応する
    # キーフレームを選択状態にする。

    # Parameters
    # ----------
    # object_name : str
    #     対象のオブジェクト名（通常オブジェクト or アーマチュア）
    # bone_name : str | None
    #     対象ボーン名（通常オブジェクトの場合は None）
    # data_path : str
    #     例: "rotation_euler", "location", "scale"
    # frame_list : list[int] | None
    #     選択対象とするフレーム番号リスト。Noneなら全選択。
    # axis : str | None
    #     "X" / "Y" / "Z" のいずれか。Noneなら全軸。
    
    # Returns
    # -------
    # list[(fcurve, keyframe_point)]
    #     選択されたキーフレームのリスト。
  
    obj = bpy.data.objects.get(object_name)
    if not obj or not obj.animation_data or not obj.animation_data.action:
        print(f"[Error] {object_name} に有効なアクションがありません。")
        return []

    action = obj.animation_data.action
    selected_keys = []

    axis_map = {"X": 0, "Y": 1, "Z": 2}
    target_index = axis_map.get(axis.upper()) if axis else None

    # --- 対象F-Curveのdata_pathパターンを決定 ---
    if bone_name:
        # アーマチュアボーン
        target_prefix = f'pose.bones["{bone_name}"].{data_path}'
    else:
        # 通常オブジェクト
        target_prefix = data_path

    # --- すべてのキーフレームを deselect ---
    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            kp.select_control_point = False
            kp.select_left_handle = False
            kp.select_right_handle = False

    # --- 対象のF-Curveを走査して選択 ---
    for fc in action.fcurves:
        # 対象のdata_pathでなければスキップ
        if not fc.data_path.startswith(target_prefix):
            continue

        # 軸指定がある場合
        if target_index is not None and fc.array_index != target_index:
            continue

        for kp in fc.keyframe_points:
            if frame_list is None or int(round(kp.co.x)) in frame_list:
                kp.select_control_point = True
                kp.select_left_handle = True
                kp.select_right_handle = True
                selected_keys.append((fc, kp))

    return selected_keys


# ================================================================
# = ▼ 選択したキーフレームを複製
# ================================================================
def duplicate_selected_keyframes(
    armature_name: str,
    offset_frames: int = 20
):
    # 選択されたキーフレームを offset_frames フレーム後に複製。
    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
        print(f"[Error] {armature_name} に有効なアクションがありません。")
        return

    action = arm_obj.animation_data.action
    count = 0

    for fc in action.fcurves:
        new_points = []
        for kp in fc.keyframe_points:
            if kp.select_control_point:
                new_frame = kp.co.x + offset_frames
                new_value = kp.co.y
                new_points.append((new_frame, new_value))
                count += 1

        for new_frame, new_value in new_points:
            fc.keyframe_points.insert(frame=new_frame, value=new_value, options={'FAST'})
        fc.update()

# ================================================================
# = ▼ 選択したキーフレームを移動
# ================================================================
def move_selected_keyframes(
    armature_name: str,
    offset_frames: int = 20
):
    # 選択済みキーフレームを offset_frames フレーム分だけ移動する。
    # 複製はせず、選択されたキーフレーム自体を移動。
    import bpy

    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj or not arm_obj.animation_data or not arm_obj.animation_data.action:
        print(f"[Error] {armature_name} に有効なアクションがありません。")
        return

    action = arm_obj.animation_data.action
    moved_count = 0

    for fc in action.fcurves:
        for kp in fc.keyframe_points:
            if kp.select_control_point:
                kp.co.x += offset_frames
                moved_count += 1
        fc.update()

# ================================================================
# = ▼ dopesheet モード変更
# ================================================================
def set_dopesheet_mode_to_action():
        # Dope SheetエリアがあればAction Editorモードに切り替える
        for area in bpy.context.screen.areas:
            if area.type == 'DOPESHEET_EDITOR':
                for space in area.spaces:
                    if space.type == 'DOPESHEET_EDITOR':
                        space.ui_mode = 'ACTION'
                        return


# ================================================================
# = ▼ Action Name 変更
# ================================================================
def rename_current_armature_action(
    armature_name: str
,   new_action_name: str
):
    # Parameters
    # ----------
    # armature_name : str
    #     対象のアーマチュアオブジェクト名。
    # new_action_name : str
    #     新しいアクション名。

    # Returns
    # -------
    # bool
    #     True: 成功, False: 失敗
    # アーマチュア取得
    arm_obj = bpy.data.objects.get(armature_name)
    if not arm_obj:
        print(f"[Error] Armature '{armature_name}' not found")
        return False

    # アニメーションデータとアクション確認
    if not arm_obj.animation_data or not arm_obj.animation_data.action:
        print(f"[Error] '{armature_name}' not found Active Action")
        return False

    action = arm_obj.animation_data.action
    old_name = action.name

    # 同名のアクションが存在するかチェック
    if new_action_name in bpy.data.actions and bpy.data.actions[new_action_name] != action:
        print(f"[Warning] '{new_action_name}' already exist")
        return False

    # 名前を変更
    action.name = new_action_name

    return True

# ================================================================
# = ▼ Push Down
# ================================================================
def safe_push_down(
    obj_name: str
,   track_name="Track"
):
    obj = bpy.data.objects.get(obj_name)
    if not obj or not obj.animation_data or not obj.animation_data.action:
        print(f"[Error] {obj_name} not found Action.")
        return

    act = obj.animation_data.action

    # 新しい NLA トラックを作成
    track = obj.animation_data.nla_tracks.new()
    track.name = track_name

    # ストリップとして追加
    start_frame = int(act.frame_range[0])
    strip = track.strips.new(act.name, start_frame, act)

    # push_downと同様にアクションを解放
    obj.animation_data.action = None


# ================================================================
# = ▼ NLA Strip プロパティ変換
# ================================================================
def set_nla_strip_properties(
    obj_name: str,
    strip_name: str,
    **kwargs
):
    # 指定オブジェクト内の NLA ストリップを名前で探し、
    # すべての主要プロパティを直接編集する汎用関数。

    # Parameters
    # ----------
    # obj_name : str
    #     NLAトラックを持つオブジェクト名
    # strip_name : str
    #     編集対象のストリップ名（例："RunAction"）
    # kwargs : dict
    #     設定するパラメータをキーワード引数で指定
    #     例：
    #         frame_start_ui=4.3
    #         repeat=5.9
    #         blend_type='ADD'
    #         mute=True
    #         scale=0.5
    #         use_reverse=True
    #         use_animated_influence=False

    obj = bpy.data.objects.get(obj_name)
    if not obj:
        print(f"[Error] Object '{obj_name}' not found.")
        return None

    if not obj.animation_data or not obj.animation_data.nla_tracks:
        print(f"[Error] '{obj_name}' has no NLA tracks.")
        return None

    target_strip = None
    for track in obj.animation_data.nla_tracks:
        for strip in track.strips:
            if strip.name == strip_name:
                target_strip = strip
                break
        if target_strip:
            break

    if not target_strip:
        print(f"[Error] Strip '{strip_name}' not found in '{obj_name}'.")
        return None

    # --- 設定処理 ---
    for key, value in kwargs.items():
        if hasattr(target_strip, key):
            setattr(target_strip, key, value)
        else:
            print(f"[Warn] Property '{key}' not found in NlaStrip.")

    return target_strip
