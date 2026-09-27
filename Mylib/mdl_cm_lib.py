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
# = ▼ Select Active Object
# ========================================================================
def active_object_select(object_name_list=[]):
    # 指定されたオブジェクトを選択し、最後に見つかったオブジェクトをアクティブにする
    # アクティブオブジェクトが存在しなくても安全に動作
    # Save current mode safely
    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    # Ensure OBJECT mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')

    active_obj = None
    for obj_name in object_name_list:
        obj = bpy.data.objects.get(obj_name)
        if obj:
            obj.select_set(True)
            active_obj = obj  # 最後に見つかったオブジェクトを保存

    # Set the last found object as active
    if active_obj:
        bpy.context.view_layer.objects.active = active_obj

    # Restore previous mode
    if bpy.context.object and bpy.context.object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except Exception:
            pass

    return active_obj

# ========================================================================
# = ▼ Select Active Object recursively hierarchy 再帰的 親子関係選択
# ========================================================================
def active_object_select_recursively(object_name_list=[]):
    # Select objects by name.
    # - If an object has children, select it and all its hierarchy.
    # - If no children, select only itself.
    # Returns the last active object.
    def select_hierarchy(obj):
        # Recursively select object and its children
        obj.select_set(True)
        for child in obj.children:
            select_hierarchy(child)

    # Save current mode (if object exists)
    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'

    # Ensure OBJECT mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')

    myobject = None
    for object_name in object_name_list:
        myobject = bpy.data.objects.get(object_name)
        if myobject:
            if myobject.children:  
                # Has children → select full hierarchy
                select_hierarchy(myobject)
            else:
                # No children → select only itself
                myobject.select_set(True)

            # Set active to the object itself (not child)
            bpy.context.view_layer.objects.active = myobject

    # Restore previous mode if the active object is not Empty
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass

    return myobject

# ========================================================================
# = ▼ Rename Object at key word (recursively/hierarchy) 再帰的 親子関係選択
# ========================================================================
def rename_hierarchy_recursively(base_name: str, new_base_name: str):
    # Rename duplicated objects after bpy.ops.object.duplicate_move().
    # - Replace base_name with new_base_name
    # - Remove Blender's auto suffix (.001, .002...)
    for obj in bpy.context.selected_objects:
        if obj.name.startswith(base_name):
            # サフィックスを取り除き、置換
            clean_name = obj.name.split(".")[0]  
            new_name = clean_name.replace(base_name, new_base_name)
            obj.name = new_name


# ========================================================================
# = ▼ 辺、面、頂点 選択
# ========================================================================
def element_select(
        element_list                # 要素 Index List
,       select_mode                 # Mode（VERT/EDGE/FACE）
,       object_name_list=["NaN"]    # Object Name List
,       loop_select=False           # Loop選択
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Ensure OBJECT mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')
    if (object_name_list[0] != "NaN"):
        # Current Active Object
        for i in range(len(object_name_list)):
            object_name = object_name_list[i]
            obj = bpy.data.objects.get(object_name)
            if obj:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
    # Get Active Object
    obj = bpy.context.object
    # Check Mesh
    if obj and obj.type == 'MESH':
        mesh = obj.data
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type=select_mode)
        # Release Select Index
        bpy.ops.mesh.select_all(action='DESELECT')
        # Change Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Select Element
        if ((len(element_list) >= 1) and (element_list[0] == "all")):
            # Select All
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type=select_mode)
            bpy.ops.mesh.select_all(action='SELECT')
        else:
            # Select Element
            for i in range(len(element_list)):
                target_ele_index = element_list[i]
                if (select_mode == "FACE"):
                    mesh.polygons[target_ele_index].select = True
                elif (select_mode == "EDGE"):
                    mesh.edges[target_ele_index].select = True
                elif (select_mode == "VERT"):
                    mesh.vertices[target_ele_index].select = True
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        if (loop_select == True):
            # Loop Select (Alt+Click)
            # Blender 5.2 で mesh.loop_multi_select(ring=False) が
            # mesh.select_edge_loop_multi() に分離・改名された
            bpy.ops.mesh.select_edge_loop_multi()
    else:
        print("No mesh object selected.")
    # Return Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# 辺、面、頂点選択解除
# ========================================================================
def element_deselect(
        object_name_list    # Object Name List
    ,   element_list        # Index List
    ,   select_mode         # Mode  ("VERT", "EDGE", "FACE")
):
    if not object_name_list or not object_name_list[0]:
        print("Invalid object_name_list.")
        return
    obj = bpy.data.objects.get(object_name_list[0])
    if not obj or obj.type != 'MESH':
        print(f"{object_name_list[0]} is not a valid mesh object.")
        return
    bpy.context.view_layer.objects.active = obj
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh
    bm = bmesh.from_edit_mesh(obj.data)
    # Update Index Table
    bm.verts.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    # Release
    if select_mode == "VERT":
        for index in element_list:
            if 0 <= index < len(bm.verts):
                bm.verts[index].select = False
    elif select_mode == "EDGE":
        for index in element_list:
            if 0 <= index < len(bm.edges):
                bm.edges[index].select = False
    elif select_mode == "FACE":
        for index in element_list:
            if 0 <= index < len(bm.faces):
                bm.faces[index].select = False
    else:
        print(f"Invalid select_mode: {select_mode}")
        return
    # Update Mesh & Update
    bmesh.update_edit_mesh(obj.data, loop_triangles=True)



# ========================================================================
# 視点をZ視点真上に変更
# ========================================================================
def set_view_custom_position(
    point=(0, 0, 0)
,   rotate=(0, 0, 0)
,   distance=3
):
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    region_3d = space.region_3d
                    region_3d.view_perspective = 'ORTHO' # 'PERSP'/'CAMERA'
                    # 視点位置/向き設定
                    region_3d.view_location = mathutils.Vector(point)                   # 位置
                    region_3d.view_distance = distance                                  # 距離
                    region_3d.view_rotation = mathutils.Euler(rotate).to_quaternion()   # 回転
                    # View更新
                    bpy.context.view_layer.update()

# ========================================================================
# = ▼ オブジェクトの表示/非表示
# ========================================================================
def hide_obj_tgl(
    object_list=[]
,   key=False
):
    for i in range(len(object_list)):
        obj = bpy.data.objects.get(object_list[i])
        obj.hide_set(key)


# ========================================================================
# = ▼ プレビュー切り替え
# ========================================================================
def change_preview(key='SOLID'):
    # 'SOLID'       : ソリッドプレビュー
    # 'MATERIAL'    : マテリアルプレビュー
    # 'RENDERED'    : レンダープレビュー
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = key
                    return


# ========================================================================
# = ▼ オブジェクト/メッシュ回転
# ========================================================================
def object_rotate_func(
        object_list=["mesh"]                        # 回転対象 Object List
    ,   transform_pivot_point='INDIVIDUAL_ORIGINS'  # 回転中心 (ピボットポイント)
    ,   degrees_num=0                               # 回転角度 (度)
    ,   orient_axis="Z"                             # 回転軸
    ,   orient_type="GLOBAL"                        # 回転軸座標
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Check Mesh
    if (object_list[0] != "mesh"):
        # Change Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Release All Object
        bpy.ops.object.select_all(action='DESELECT')
        # Select Active Object
        my_active_element = active_object_select(object_name_list=object_list)
        # オブジェクトのオリジンをジオメトリの中心に移動
        # オブジェクト中心(回転の中心)をオブジェクトに追従させる
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS', center='BOUNDS')
    # Set Pivot point
    #-------------------------------------------------
    # Options
    # bpy.context.scene.tool_settings.transform_pivot_point = 'MEDIAN_POINT'        # オブジェクトの中点（複数オブジェクトの中心）
    # bpy.context.scene.tool_settings.transform_pivot_point = 'ACTIVE_ELEMENT'      # アクティブなオブジェクトの中心
    # bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'              # 3Dカーソル位置
    # bpy.context.scene.tool_settings.transform_pivot_point = 'INDIVIDUAL_ORIGINS'  # 個々のオブジェクトの中心
    # bpy.context.scene.tool_settings.transform_pivot_point = 'BOUNDING_BOX_CENTER' # バウンディングボックスと呼ばれる枠の中心
    #-------------------------------------------------
    bpy.context.scene.tool_settings.transform_pivot_point = transform_pivot_point

    # --------------------
    # 自動符号補正（複数オブジェクト同時回転対応）
    # --------------------
    if degrees_num != 0:
        ref_obj = bpy.data.objects.get(object_list[0])
        if ref_obj:
            # delta 判定用の基準点取得（Mesh or Empty 共通）
            if ref_obj.type == 'MESH' and len(ref_obj.data.vertices) > 0:
                bm = bmesh.new()
                bm.from_mesh(ref_obj.data)
                bm.verts.ensure_lookup_table()
                ref_point = ref_obj.matrix_world @ bm.verts[0].co
                bm.free()
            else:
                # Empty の場合や原点でも回転方向判定可能にする微小オフセット
                offset = 1e-5
                ref_point = ref_obj.matrix_world.translation.copy() + {
                    "X": Vector((0, offset, 0)),
                    "Y": Vector((offset, 0, 0)),
                    "Z": Vector((0, 0, offset))
                }.get(orient_axis.upper(), Vector((0, 0, offset)))
            orig_co = ref_point.copy()

            # 選択して一時回転（正の degrees_num）で Blender の回転方向確認
            bpy.ops.object.select_all(action='DESELECT')
            for obj_name in object_list:
                obj = bpy.data.objects.get(obj_name)
                if obj:
                    obj.select_set(True)
            bpy.context.view_layer.objects.active = ref_obj

            bpy.ops.transform.rotate(
                value=math.radians(abs(degrees_num)),
                orient_axis=orient_axis,
                orient_type=orient_type
            )

            # 回転後の delta 計算
            if ref_obj.type == 'MESH' and len(ref_obj.data.vertices) > 0:
                bm = bmesh.new()
                bm.from_mesh(ref_obj.data)
                bm.verts.ensure_lookup_table()
                new_co = ref_obj.matrix_world @ bm.verts[0].co
                bm.free()
            else:
                new_co = ref_obj.matrix_world.translation.copy() + {
                    "X": Vector((0, offset, 0)),
                    "Y": Vector((offset, 0, 0)),
                    "Z": Vector((0, 0, offset))
                }.get(orient_axis.upper(), Vector((0, 0, offset)))

            axis_map = {"X": 0, "Y": 1, "Z": 2}
            idx = axis_map.get(orient_axis.upper(), 2)
            delta = new_co[idx] - orig_co[idx]

            # 符号補正（呼び出し側指定の符号を尊重し、Blender のバージョン差も吸収）
            desired_sign = 1 if degrees_num >= 0 else -1
            actual_sign = 1 if delta >= 0 else -1
            corrected_radians = desired_sign * abs(degrees_num) * actual_sign

            # 元に戻す
            bpy.ops.transform.rotate(
                value=math.radians(-abs(degrees_num)),
                orient_axis=orient_axis,
                orient_type=orient_type
            )

            # 選択して最終回転
            bpy.ops.object.select_all(action='DESELECT')
            for obj_name in object_list:
                obj = bpy.data.objects.get(obj_name)
                if obj:
                    obj.select_set(True)
            bpy.context.view_layer.objects.active = ref_obj
            bpy.ops.transform.rotate(
                value=math.radians(corrected_radians),
                orient_axis=orient_axis,
                orient_type=orient_type
            )

    # Change Original Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass

# ----------------------------
# 要素 回転
# ----------------------------
def mesh_elements_rotate_customid(
        object_list=["mesh"],
        element_type="FACE",
        custom_ids=[0],
        transform_pivot_point='INDIVIDUAL_ORIGINS',
        degrees_num=0.0,
        orient_axis="Z",
        orient_type="GLOBAL"
):

    if degrees_num == 0:
        return

    current_mode = bpy.context.object.mode

    if bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')

    # -------------------------------------------------
    # オブジェクト取得
    # -------------------------------------------------
    obj = None
    for name in object_list:
        o = bpy.data.objects.get(name)
        if o and o.type == 'MESH':
            o.select_set(True)
            bpy.context.view_layer.objects.active = o
            obj = o

    if obj is None:
        return

    mesh = obj.data

    # -------------------------------------------------
    # EDITモードへ
    # -------------------------------------------------
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type=element_type)
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')

    element_indices = custom_id_to_index(
        obj_name=obj.name,
        elem_type=element_type,
        custom_id_list=custom_ids
    )

    for idx in element_indices:
        if element_type == "FACE":
            mesh.polygons[idx].select = True
        elif element_type == "EDGE":
            mesh.edges[idx].select = True
        elif element_type == "VERT":
            mesh.vertices[idx].select = True

    bpy.ops.object.mode_set(mode='EDIT')

    bpy.context.scene.tool_settings.transform_pivot_point = transform_pivot_point

    # -------------------------------------------------
    # 毎回方向検証（キャッシュ無し）
    # -------------------------------------------------

    axis_dict = {
        "X": Vector((1,0,0)),
        "Y": Vector((0,1,0)),
        "Z": Vector((0,0,1))
    }

    axis_vec = axis_dict.get(orient_axis.upper(), Vector((0,0,1)))

    if orient_type == "LOCAL":
        axis_vec = obj.matrix_world.to_3x3() @ axis_vec

    axis_vec.normalize()

    # 軸に直交するベクトル生成
    ref_vec = axis_vec.orthogonal()
    ref_vec.normalize()

    test_angle = 5.0  # 小さな仮回転角

    # 仮回転（常に正方向でテスト）
    bpy.ops.transform.rotate(
        value=math.radians(test_angle),
        orient_axis=orient_axis,
        orient_type=orient_type
    )

    # 回転後のベクトル取得
    rot_mat = obj.matrix_world.to_3x3()
    rotated_vec = rot_mat @ ref_vec

    # 外積で回転方向判定
    cross = ref_vec.cross(rotated_vec)
    dot = axis_vec.dot(cross)

    # Blenderが「右ねじ系」かどうか判定
    blender_sign = 1 if dot > 0 else -1

    # 元に戻す
    bpy.ops.transform.rotate(
        value=math.radians(-test_angle),
        orient_axis=orient_axis,
        orient_type=orient_type
    )

    # -------------------------------------------------
    # 指定仕様に合わせた補正
    # -------------------------------------------------

    desired_sign = 1 if degrees_num > 0 else -1

    # 負→正方向から見て時計回りを正にする
    # Blenderの右ねじ基準と一致させる補正
    corrected_angle = desired_sign * abs(degrees_num) * blender_sign

    # -------------------------------------------------
    # 最終回転
    # -------------------------------------------------

    bpy.ops.transform.rotate(
        value=math.radians(corrected_angle),
        orient_axis=orient_axis,
        orient_type=orient_type
    )

    try:
        bpy.ops.object.mode_set(mode=current_mode)
    except:
        pass


# ========================================================================
# = ▼ 面押し出し インデックス固定
# ========================================================================
def fix_index_extrude_region(
    vert_idx_list=[0,1,2,3]     # Index List
,   mv_value=(-5,0,0)           # Move Value
,   object_name="obj_name"      # Active Object Name
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Get Number of Angles (角数)
    li_len = len(vert_idx_list)
    # Save Data
    ei_a=[] # Extrude Index
    # Vert Extrude
    for i in range(li_len):
        # Select Element
        element_select(
            element_list=[vert_idx_list[i]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # 押し出し、引き込み
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={
            }, 
            TRANSFORM_OT_translate={
                "value":mv_value
            ,   "orient_type":'GLOBAL'
        })
        # Select Add Vertex Index (追加された頂点 選択)
        new_vertex_index = len(bpy.context.object.data.vertices) - 1
        bpy.context.object.data.vertices[new_vertex_index].select = True
        # Update Mesh
        bpy.context.view_layer.objects.active = bpy.context.object
        # Change Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        # Get Active Object
        obj = bpy.context.object
        # Get Mesh Data
        mesh = obj.data
        # Get the index of the selected vertex
        selected_vertex_indices = [v.index for v in mesh.vertices if v.select]
        # Add List
        ei_a.append(selected_vertex_indices[0])
    # Add Face
    for i in range(li_len-1):
        element_select(
            element_list=[vert_idx_list[i], ei_a[i], vert_idx_list[i+1], ei_a[i+1]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # 面 追加・埋める・貼る (F)
        bpy.ops.mesh.edge_face_add()
    # Add Face
    element_select(
        element_list=[vert_idx_list[0], ei_a[0], vert_idx_list[li_len-1], ei_a[li_len-1]]
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    bpy.ops.mesh.edge_face_add()
    # Add Face
    element_select(
        element_list=ei_a
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    bpy.ops.mesh.edge_face_add()
    # Delete Face
    element_select(
        element_list=vert_idx_list
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ 面押し出し インデックス固定 円系
# ========================================================================
def fix_index_extrude_region_move(
    obj_name="obj_name"         # Object Name
,   represent_edge=0            # Represent Edge Index (代表エッジ)
,   resize_values=(1, 1, 1)     # Change Size Value
,   move_values=(0, 0, 0)       # Move Value
,   face_add_flag=True          # If True: Add Face
,   loop_flag=True              # ?
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Select Element
    element_select(
        element_list=[represent_edge]
    ,   select_mode="EDGE"
    ,   object_name_list=[obj_name]
    )
    if (loop_flag):
        # エッジループ 選択 ループ選択(Alt+Click)
        # Blender 5.2 で mesh.loop_multi_select(ring=False) が
        # mesh.select_edge_loop_multi() に分離・改名された
        bpy.ops.mesh.select_edge_loop_multi()
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Get Mesh Data
    mesh = bpy.context.object.data
    # Get the index of the selected vertex
    selected_vertex_indices = [v.index for v in mesh.vertices if v.select]
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    tmp_l=[]
    for i in range(len(selected_vertex_indices)):
        # Select Element
        element_select(
            element_list=[selected_vertex_indices[i]]
        ,   select_mode="VERT"
        ,   object_name_list=[obj_name]
        )
        # Create Face (面の作成 外/内側へ拡大(押し込み(押し出し)引き込み/差し込み))
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={}, 
            TRANSFORM_OT_translate={
            }
        )
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # Get Mesh Data
        mesh = bpy.context.object.data
        # Get the index of the selected vertex
        tmp_l.append([v.index for v in mesh.vertices if v.select][0])
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
    # Select Element
    element_select(
        element_list=tmp_l
    ,   select_mode="VERT"
    ,   object_name_list=[obj_name]
    )
    # Change Size
    bpy.ops.transform.resize(
        value=resize_values
    ,   orient_type='GLOBAL'
    )
    # Move Object/Element
    bpy.ops.transform.translate(
        value=move_values
    ,   orient_type='GLOBAL'
    )
    # Add Face
    if (face_add_flag):
        for i in range(1, len(tmp_l)):
            # Select Element
            element_select(
                element_list=[tmp_l[i], selected_vertex_indices[i], tmp_l[i-1], selected_vertex_indices[i-1]]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # Add Face (面 追加・埋める・貼る) (F)
            bpy.ops.mesh.edge_face_add()
        if (loop_flag):
            # Connect First and Last Point (最初と最後部分をつなぐ)
            element_select(
                element_list=[tmp_l[0], selected_vertex_indices[0], tmp_l[len(tmp_l)-1], selected_vertex_indices[len(tmp_l)-1]]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # Add Face (面 追加・埋める・貼る) (F)
            bpy.ops.mesh.edge_face_add()
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)


# ========================================================================
# = ▼ 筒状 面指定 面貼り インデックス固定
# ========================================================================
def fix_index_connect_vert(
    vert_list_1=[0,1,2,3]       # Vertex Index 1
,   vert_list_2=[0,1,2,3]       # Vertex Index 2
,   object_name="object_name"   # Object Name
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Delete Face
    element_select(
        element_list=vert_list_1
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    element_select(
        element_list=vert_list_2
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    # Add Face
    for i in range(len(vert_list_1)-1):
        element_select(
            element_list=[vert_list_1[i], vert_list_2[i], vert_list_1[i+1], vert_list_2[i+1]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # Add Face (面 追加・埋める・貼る) (F)
        bpy.ops.mesh.edge_face_add()
    # Add Face
    element_select(
        element_list=[vert_list_1[0], vert_list_2[0], vert_list_1[-1], vert_list_2[-1]]
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    bpy.ops.mesh.edge_face_add()
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ ループカット 数値指定 複数
# ========================================================================
def multi_value_loopcut_slide(
    bl=20                                                               # Target Edge Size
,   i_a=[0]                                                             # Index List
,   s_a=[0]                                                             # Slide Value List
,   d_a=[1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,]    # direction List (1 or -1)
):
    # Save Current Mode
    obj = bpy.context.active_object
    current_mode = obj.mode
    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    bl_tmp = bl
    for i in range(len(i_a)):
        # Calculation Ration (割合)
        ratio = bl_tmp / bl
        # Calculation Move Point (移動位置計算)
        value = ((1/((bl*ratio)/2)) * s_a[i]) - 1
        # Calculation Update Value更新
        bl_tmp = bl - (bl - s_a[i])
        # Loop Cut
        bpy.ops.mesh.loopcut_slide(
            MESH_OT_loopcut={
                "number_cuts":1             # 追加ループ数
            ,   "smoothness":0              # 0~1：スムージング強さ
            ,   "falloff":'INVERSE_SQUARE'  # カット減衰 "INVERSE_SQUARE":逆2乗フォールオフ（例：SHARP）
            ,   "object_index":0            # オブジェクトインデックス(通常0：最初のオブジェクト)
            ,   "edge_index":i_a[i]         # エッジインデックス
            }
        ,   TRANSFORM_OT_edge_slide={
                "value":value*d_a[i]        # スライド位置（0:スライドなし） 
            ,   "single_side":False         # 片側スライド（False:両側スライド）
            ,   "use_even":False            # スライド均等（False:均等にしない）
            }
        )
    # Change Original Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass


# ========================================================================
# = ▼ 指定頂点 絶対座標取得
# ========================================================================
def get_vert_point(vert_index=0):
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH':
        print("メッシュオブジェクトが選択されていません。")
        return None
    # Save Current Mode
    current_mode = obj.mode
    # Chaneg Mode
    if current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Index Check
    if vert_index < 0 or vert_index >= len(obj.data.vertices):
        print(f"頂点インデックス {vert_index} は存在しません")
        if current_mode != 'OBJECT':
            bpy.ops.object.mode_set(mode=current_mode)
        return None
    # Local coordinate -> World coordinate (指定インデックスのローカル座標を取得し、ワールド座標に変換)
    v = obj.data.vertices[vert_index]
    world_co = obj.matrix_world @ v.co
    point_list = [round(world_co.x, 7), round(world_co.y, 7), round(world_co.z, 7)]
    # Change Original Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass
    return point_list


# ========================================================================
# = ▼ 指定したオブジェクト頂点間 距離取得
# ========================================================================
def point_diff_length(
    obj1_name="obj1_name"   # オブジェクト名またはEmpty名
,   obj1_point=0            # Vert Index（メッシュの場合のみ使用）
,   obj2_name="obj2_name"   # オブジェクト名またはEmpty名
,   obj2_point=0            # Vert Index（メッシュの場合のみ使用）
,   coordinate="X"          # X, Y, Z
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # Save: Get Current Active Object
    current_obj = bpy.context.object
    # -------------------------
    # Get Point (OBJ1)
    # -------------------------
    obj1 = bpy.data.objects[obj1_name]
    if obj1.type == 'MESH':
        active_object_select([obj1_name])
        point1 = get_vert_point(vert_index=obj1_point)
    else:
        # Emptyやカメラなど → オブジェクト原点を使用
        point1 = obj1.matrix_world.translatio
    # -------------------------
    # Get Point (OBJ2)
    # -------------------------
    obj2 = bpy.data.objects[obj2_name]
    if obj2.type == 'MESH':
        active_object_select([obj2_name])
        point2 = get_vert_point(vert_index=obj2_point)
    else:
        point2 = obj2.matrix_world.translation
    # -------------------------
    # Get Diff Length
    # -------------------------
    coord_idx = {"X": 0, "Y": 1, "Z": 2}
    if coordinate not in coord_idx:
        print("Error: coordinate must be X, Y, or Z")
        return None
    axis = coord_idx[coordinate]
    diff_length = abs(point1[axis] - point2[axis])
    # -------------------------
    # Return Status
    # -------------------------
    bpy.ops.object.select_all(action='DESELECT')
    current_obj.select_set(True)
    bpy.context.view_layer.objects.active = current_obj
    # Return Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass

    return diff_length



# ========================================================================
# = ▼ ベジェ曲線/ベジエ曲線のハンドル/コントロールポイント選択
# ========================================================================
def bezier_point_select(
    element_list                 # Point or Handle List
,   select_mode='CONTROL_POINT'  # Mode（CONTROL_POINT/HANDLE_LEFT/HANDLE_RIGHT）
,   object_name_list=["NaN"]     # Object Name
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    if object_name_list[0] != "NaN":
        for object_name in object_name_list:
            # Select Current Active Object
            obj = bpy.data.objects.get(object_name)
            if obj:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
    # Get Active Object
    obj = bpy.context.object
    # Check Curve Object
    if obj and obj.type == 'CURVE':
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        # Get Object Data
        curve = obj.data
        # Release Point
        for spline in curve.splines:
            if spline.type == 'BEZIER':
                for bezier_point in spline.bezier_points:
                    bezier_point.select_control_point = False
                    bezier_point.select_left_handle = False
                    bezier_point.select_right_handle = False
        # Select Point or Handle
        for idx in element_list:
            for spline in curve.splines:
                if spline.type == 'BEZIER':
                    if idx < len(spline.bezier_points):
                        bezier_point = spline.bezier_points[idx]
                        if select_mode == 'CONTROL_POINT':
                            bezier_point.select_control_point = True
                        elif select_mode == 'HANDLE_LEFT':
                            bezier_point.select_left_handle = True
                        elif select_mode == 'HANDLE_RIGHT':
                            bezier_point.select_right_handle = True
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
    else:
        print("No curve object selected.")
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)



# ========================================================================
# = ▼ 長方形 オブジェクト頂点移動
# ========================================================================
def make_cube_move_relative_position(
    cube_name="default_name"                    # Object Name
,   cube_size=(0.1, 0.1, 1.0)                   # Object Size
,   cube_vert=6                                 # Vert Index
,   destination_obj_name="destination_obj_name" # Base Object Name
,   destination_vert=0                          # Vert Index
):
    # Save: Current Mode
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # Release Select
    bpy.ops.object.select_all(action='DESELECT')
    # Add Cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    cube_obj = bpy.context.object
    cube_obj.name = cube_name
    # Change Size
    bpy.ops.transform.resize(value=cube_size, orient_type='GLOBAL')
    bpy.ops.object.transform_apply(scale=True)  # スケール適用（頂点座標に反映）
    # Get Destination Object
    des_obj = bpy.data.objects.get(destination_obj_name)
    if not des_obj:
        print(f"Object '{destination_obj_name}' not found.")
        return
    # Get World coordinate (ワールド座標取得)
    des_vert = des_obj.data.vertices[destination_vert]
    des_world_co = des_obj.matrix_world @ des_vert.co
    cube_vert_co = cube_obj.data.vertices[cube_vert].co
    cube_world_co = cube_obj.matrix_world @ cube_vert_co
    # 相対移動量
    dx = des_world_co.x - cube_world_co.x
    dy = des_world_co.y - cube_world_co.y
    dz = des_world_co.z - cube_world_co.z
    # 編集モードに入って頂点移動
    bpy.context.view_layer.objects.active = cube_obj
    cube_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(cube_obj.data)
    for v in bm.verts:
        v.co.x += dx
        v.co.y += dy
        v.co.z += dz
    bmesh.update_edit_mesh(cube_obj.data)

    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ オブジェクトの位置, サイズ, 回転, 中心点初期化(全適用)
# ========================================================================
def initialize_transform_apply(
    object_name_list=[] # object_name_list
):
    # Change List
    if not isinstance(object_name_list, list):
        object_name_list = [object_name_list]
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # Activate Object
    active_object_select(
        object_name_list=object_name_list
    )
    # All Transforms（全トランスフォーム）(適用)
    bpy.ops.object.transform_apply(
        location=True   # 位置適用、現在の位置が新しい基準点(原点)
    ,   rotation=True   # 回転適用、現在の回転が新しい基準点(0度)
    ,   scale=True      # スケール適用、現在のスケールが新しい基準点(1.0)
    )
    # 0度ローテーション -> オブジェクトの原点を中心に移動
    object_rotate_func(
        object_list=object_name_list
    ,   degrees_num=0
    )
    # Change Original Mode
    # Return Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass


# ========================================================================
# = ▼ 左半分の頂点を全て選択
# ========================================================================
def select_left_half_vertices(obj_name):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    obj = bpy.data.objects[obj_name]
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    active_object_select(
        object_name_list=obj_name
    )
    bpy.ops.object.mode_set(mode='EDIT')
    # Release All Vertex
    bpy.ops.mesh.select_all(action='DESELECT')
    # Change Mode
    bpy.ops.mesh.select_mode(type='VERT')
    # Get Vertex Point
    bm = bmesh.from_edit_mesh(obj.data)
    for vert in bm.verts:
        if vert.co.x < -0.00001:    # 調整
            vert.select = True
    # Update
    bmesh.update_edit_mesh(obj.data)
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)



# ========================================================================
# オブジェクトに以下のクリーンアップを実行
# ・大きさ０を融解：面積が０の面を削除し、１つの頂点にまとめる
# ・孤立を削除：どの面にもつながっていない辺や頂点を削除する
# ・重複頂点を削除：重複している頂点を１つの頂点にまとめる
# 引数   arg_objectname：指定オブジェクト名
# ========================================================================
def cleanup_mesh_object():
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT', toggle=False)
    # 頂点をSelect Allした状態とする
    bpy.ops.mesh.select_all(action='SELECT') 
    # 大きさ0を融解（結合距離 0.0001）
    bpy.ops.mesh.dissolve_degenerate(threshold=0.0001)
    # 変更を反映するため再び頂点をSelect All
    bpy.ops.mesh.select_all(action='SELECT') 
    # 孤立を削除（頂点、辺のみ）
    bpy.ops.mesh.delete_loose(use_verts=True, use_edges=True, use_faces=False)
    # 孤立を削除でSelect Allが解除されるので再び頂点をSelect All
    bpy.ops.mesh.select_all() 
    # 重複頂点を削除（結合距離 0.0001、非選択部の結合無効）
    bpy.ops.mesh.remove_doubles(threshold=0.0001, use_unselected=False)
    # オブジェクトモードに移行する
    bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
    # Change Original Mode
    # Return Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass
    return




# ========================================================================
# = 選択頂点どうしをつなぐ辺を追加
# ========================================================================
def add_edge_between_vert(
    obj_name="obj_name"
,   index_list=[[1,0], [2,3]]
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Get Object
    obj = bpy.data.objects.get(obj_name)
    if obj is None:
        raise ValueError(f"オブジェクト '{obj_name}' が見つかりません。")
    if obj.type != 'MESH':
        raise ValueError(f"オブジェクト '{obj_name}' はメッシュではありません。")
    # Change Mode
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    mesh = obj.data
    # Get Edge List
    existing_edges = set(tuple(sorted(e.vertices)) for e in mesh.edges)
    # New Edge List
    new_edges = []
    for pair in index_list:
        # Index Check
        if pair[0] >= len(mesh.vertices) or pair[1] >= len(mesh.vertices):
            print(f"エラー: インデックス {pair} が範囲外です。")
            continue
        # Sort Check
        edge_key = tuple(sorted(pair))
        if edge_key not in existing_edges:
            new_edges.append(pair)
        else:
            print(f"頂点 {pair[0]} と {pair[1]} は既に辺で結ばれています。")
    # Add Edge
    if new_edges:
        mesh.edges.add(len(new_edges))
        for i, edge in enumerate(new_edges):
            mesh.edges[-len(new_edges) + i].vertices = edge
    else:
        print("新しい辺は追加されませんでした。")
    # Update Mesh Data
    mesh.update()
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)


# ========================================================================
# = 辺を削除して面を統合
# ========================================================================
def dissolve_edges(
    obj_name=None       # Object Name
,   index_list=[]       # Delete Index
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    element_select(
        element_list=index_list
    ,   select_mode="EDGE"
    ,   object_name_list=[obj_name]
    )
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Dissolve Edge and Merge Face
    bpy.ops.mesh.dissolve_edges()
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)


# ========================================================================
# 頂点間の相対距離を求める
# ========================================================================
def get_relative_distance():
    # Get Active Object
    obj = bpy.context.active_object
    if obj is None or obj.type != 'MESH':
        print("エラー: アクティブなメッシュオブジェクトがありません。")
        return
    # Change Mode
    if bpy.context.mode != 'EDIT_MESH':
        bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh
    bm = bmesh.from_edit_mesh(obj.data)
    # Get Select Vertex Point
    selected_verts = [v for v in bm.verts if v.select]
    if len(selected_verts) != 2:
        print("エラー: 2つの頂点を選択してください。")
        return
    # Get Vertex coordinate
    co1 = selected_verts[1].co
    co2 = selected_verts[0].co
    # Calucurate Distance
    dx = co2.x - co1.x
    dy = co2.y - co1.y
    dz = co2.z - co1.z
    # Output
    print("")
    print(f"X方向の相対距離: {dx}")
    print(f"Y方向の相対距離: {dy}")
    print(f"Z方向の相対距離: {dz}")
    return dx, dy, dz


# ========================================================================
# アンカー用 Emptyの追加 結びつけ
# ========================================================================
def add_object_anchor_empty(
    obj_name="obj_name"
,   location=(0,0,0)
,   suffix="_anchor"
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # ============================
    # Add Base Empty
    # ============================
    empty_name = obj_name + suffix
    empty = bpy.data.objects.new(empty_name, None)
    bpy.context.collection.objects.link(empty)
    empty.location = location
    # empty.matrix_world をこの直後に読み取るため、ここで一度デプスグラフを更新して
    # 直前に設定した location を matrix_world に反映させておく
    # (更新しないまま読むと matrix_world が単位行列のまま返ってくることがある)
    bpy.context.view_layer.update()
    # Parent-Child 親子付け（Emptyを親とする）
    active_object_select(object_name_list=[obj_name])
    bpy.context.object.parent = empty
    # 親子付け時点のオフセットを打ち消す補正行列を設定し、
    # 子オブジェクトのワールド座標(見た目の位置)が変化しないようにする
    # (matrix_parent_inverse を設定しないと、Emptyが原点以外の位置にある場合
    #  子オブジェクトがEmptyの位置に引っ張られて移動してしまう)
    bpy.context.object.matrix_parent_inverse = empty.matrix_world.inverted()
    active_object_select(object_name_list=[obj_name])
    # Change Original Mode
    if bpy.context.active_object and bpy.context.active_object.type != 'EMPTY':
        try:
            bpy.ops.object.mode_set(mode=current_mode)
        except RuntimeError:
            pass


# ========================================================================
#  既存のEmptyに既存のオブジェクトを追加して親子関係を設定する
#  （元の親がEmptyで子がいなくなった場合は自動削除）
#
#  Input:
#    empty_name    : 統合先 Empty のオブジェクト名 (str)
#                    例: "fance_anchor"
#    obj_name_list : Empty の子に紐づけたいオブジェクト名のリスト (list[str])
#                    例: ["fance_base", "fance_wood", "fance_roof"]
#  Output:
#    戻り値なし。副作用として bpy.data.objects 上で
#      - obj_name_list の各オブジェクトの parent を target_empty に張り替える
#      - 元の親が空になった Empty は自動削除する
#        (ただし統合先 target_empty 自身は除外。これを消すと後段で参照不能になり
#         RuntimeError: StructRNA ... has been removed が出るため)
# ========================================================================
def add_objects_to_existing_empty(empty_name, obj_name_list):
    # 統合先 Empty を名前検索 (見つからなければ何もしない)
    target_empty = bpy.data.objects.get(empty_name)
    if not target_empty:
        return

    # 親子付け操作は OBJECT モード前提のためモード切替
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj_name in obj_name_list:
        # 子に付けたいオブジェクトを名前で取得 (存在しなければスキップ)
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            continue

        # 既に target_empty を親としている場合は何もしない
        # 理由:
        #   この後の「元の親が空になったら削除」ロジックが target_empty 自身を
        #   消してしまうのを防ぐため。 obj が target_empty の唯一の子だった場合、
        #   親を一旦外すと target_empty の children が 0 個になり削除分岐に入る。
        #   その結果 target_empty.select_set() で StructRNA removed 例外が発生する。
        #   既に正しく親子付けされているなら処理不要なので continue で抜ける。
        if obj.parent is target_empty:
            continue

        # 既存の親があれば一旦解除する
        if obj.parent:
            prev_parent = obj.parent
            # 親をクリア (この時点で prev_parent.children から obj が外れる)
            obj.parent = None
            # 元の親が Empty で 子がいなくなったら自動削除する
            # ただし target_empty と同一の Empty は絶対に消さない (防御的二重ガード:
            # 上の早期 continue で弾かれているはずだが、コードが将来変更された場合の安全弁)
            if (
                prev_parent.type == 'EMPTY'
                and len(prev_parent.children) == 0
                and prev_parent is not target_empty
            ):
                bpy.data.objects.remove(prev_parent)

        # 子オブジェクトのみを選択状態にする (他オブジェクトは選択解除)
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # 親となる target_empty も選択して アクティブに設定
        # (bpy.ops.object.parent_set はアクティブオブジェクトを親として扱う仕様のため)
        target_empty.select_set(True)
        bpy.context.view_layer.objects.active = target_empty

        # トランスフォームを保ったまま 親子付けを実行
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)


# ========================================================================
#  2つの基準点のワールド座標がぴったり一致するように、
#  移動する側のオブジェクトのルートアンカーを平行移動する
#  基準点は「アンカー(Empty)」「メッシュの特定頂点(カスタムID)」のどちらでもよく、
#  アンカー同士・アンカーと頂点・頂点同士、どの組み合わせにも対応する
#  (get_vert_point_customid が Empty ならその位置、Mesh ならカスタムIDの頂点の
#   ワールド座標を返す仕様を利用して、同じロジックで両方を扱っている)
# ========================================================================
def align_point_to_point(
    move_obj_name
,   move_point_obj_name     = None                     # 動かす側で位置の基準にするオブジェクト名 (Empty/Mesh どちらも可)。省略時は move_obj_name 自身
,   move_point_vert_id      = 0                         # move_point_obj_name が Mesh の場合に基準にする頂点のカスタムID (Emptyの場合は無視される)
,   target_point_obj_name   = "target_point_obj_name"  # 位置を合わせる先の基準オブジェクト名 (Empty/Mesh どちらも可)
,   target_point_vert_id    = 0                         # target_point_obj_name が Mesh の場合に基準にする頂点のカスタムID (Emptyの場合は無視される)
,   root_anchor_suffix      = "_anchor"                 # move_obj_name側の、実際に移動させるルートアンカーのsuffix
):
    """
    move_point_obj_name 側の基準位置(Emptyならその位置、Meshならmove_point_vert_idの頂点)が、
    target_point_obj_name 側の基準位置(同様のルール)とワールド座標でぴったり一致するように、
    move_obj_name のルートアンカー(move_obj_name + root_anchor_suffix)を平行移動する。
    (target 側は動かさない)

    ---- 使用例 ----
    ・アンカー同士:
        align_point_to_point(
            move_obj_name          = "tatedoi_obj"
        ,   move_point_obj_name    = "tatedoi_obj_upper_anchor"
        ,   target_point_obj_name  = "erubo_obj_lower_anchor"
        )
    ・アンカーとメッシュの頂点(カスタムID):
        align_point_to_point(
            move_obj_name          = "tatedoi_obj"
        ,   move_point_obj_name    = "tatedoi_obj_upper_anchor"
        ,   target_point_obj_name  = "arch_main_1_roof_bg"
        ,   target_point_vert_id   = 5
        )
    ・メッシュの頂点同士(カスタムID):
        align_point_to_point(
            move_obj_name          = "tatedoi_obj"
        ,   move_point_obj_name    = "tatedoi_obj"
        ,   move_point_vert_id     = 10
        ,   target_point_obj_name  = "arch_main_1_roof_bg"
        ,   target_point_vert_id   = 5
        )

    ---- 前提条件 ----
    ・move_obj_name は add_object_anchor_empty / add_objects_to_existing_empty によって、
      ルートアンカー(root_anchor_suffix)を親としたアンカー構成になっていること
        (move_obj_name + root_anchor_suffix を動かすと、move_obj_name本体および
         move_point_obj_name(move_obj_nameの子である場合)も子として追従して一緒に動く前提)
    ・回転は合わせない(位置のみ)。向きも合わせたい場合は別途 object_rotate_func 等で調整すること

    ---- Input ----
    move_obj_name          : str : 位置を合わせるために動かす側のオブジェクト名(ルートアンカーの特定に使用)
    move_point_obj_name    : str : 動かす側で位置の基準にするオブジェクト名 (省略時は move_obj_name)
    move_point_vert_id     : int : move_point_obj_name が Mesh の場合の基準頂点カスタムID
    target_point_obj_name  : str : 位置を合わせる先の基準オブジェクト名
    target_point_vert_id   : int : target_point_obj_name が Mesh の場合の基準頂点カスタムID
    root_anchor_suffix     : str : move_obj_name側の、実際に移動させるルートアンカーのsuffix

    ---- Output ----
    なし (move_obj_name + root_anchor_suffix を平行移動する、戻り値なし)
    """
    if move_point_obj_name is None:
        move_point_obj_name = move_obj_name

    root_anchor = bpy.data.objects.get(move_obj_name + root_anchor_suffix)
    if root_anchor is None:
        raise ValueError(f"オブジェクトが見つかりません: {move_obj_name + root_anchor_suffix}")

    # 親子付け操作は OBJECT モード前提のためモード切替
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # matrix_world を最新状態にしてからワールド座標を取得する
    bpy.context.view_layer.update()

    move_point   = mdl_cm_lib.get_vert_point_customid(obj_name=move_point_obj_name,   vert_index=move_point_vert_id)
    target_point = mdl_cm_lib.get_vert_point_customid(obj_name=target_point_obj_name, vert_index=target_point_vert_id)

    if move_point is None:
        raise ValueError(f"基準位置を取得できませんでした: {move_point_obj_name} (vert_index={move_point_vert_id})")
    if target_point is None:
        raise ValueError(f"基準位置を取得できませんでした: {target_point_obj_name} (vert_index={target_point_vert_id})")

    offset = Vector(target_point) - Vector(move_point)

    # ルートアンカーを差分だけ移動 (子である move_obj_name 本体・各アンカーも追従する)
    bpy.ops.object.select_all(action='DESELECT')
    root_anchor.select_set(True)
    bpy.context.view_layer.objects.active = root_anchor
    bpy.ops.transform.translate(
        value=(offset.x, offset.y, offset.z)
    ,   orient_type='GLOBAL'
    )


# ========================================================================
# 1. オブジェクトをまとめる処理（親子関係にする）
# ========================================================================
def group_objects_under_base(base_name: str, object_name_list: list[str]) -> dict:
    # 指定したオブジェクトをベースオブジェクトの子にまとめる。
    # まとめる前の親子関係を辞書で返す。
    base_obj = bpy.data.objects.get(base_name)
    if not base_obj:
        print(f"Base object '{base_name}' not found.")
        return {}

    # Change Object Mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    base_obj.select_set(True)
    bpy.context.view_layer.objects.active = base_obj

    # 元の親子関係を記録
    original_parent_map = {}

    for name in object_name_list:
        obj = bpy.data.objects.get(name)
        if obj and obj != base_obj:
            original_parent_map[obj.name] = obj.parent.name if obj.parent else None
            obj.select_set(True)

    # 親子付け（ワールド座標を維持）
    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)

    return original_parent_map


# ========================================================================
# 2. オブジェクトを元の親子関係に戻す処理
# ========================================================================
def ungroup_objects(original_parent_map=None):
    """
    original_parent_map がある場合 → 元の親子関係へ復元
    original_parent_map が None / 空の場合 →
        アクティブオブジェクトの属する親階層のみフラット化
    """

    # OBJECTモード保証
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # -------------------------------------------------
    # original_parent_map が無い場合
    # -------------------------------------------------
    if not original_parent_map:

        active_obj = bpy.context.active_object
        if not active_obj:
            print("No active object.")
            return

        # ルートオブジェクト取得
        root = active_obj
        while root.parent:
            root = root.parent

        # ルート配下を取得（再帰）
        def collect_children(obj):
            objs = [obj]
            for child in obj.children:
                objs.extend(collect_children(child))
            return objs

        hierarchy_objects = collect_children(root)

        # フラット化（root以外）
        for obj in hierarchy_objects:
            if obj.parent is not None:

                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj

                bpy.ops.object.parent_clear(
                    type='CLEAR_KEEP_TRANSFORM'
                )

        return

    # -------------------------------------------------
    # original_parent_map がある場合 → 復元
    # -------------------------------------------------
    for obj_name, parent_name in original_parent_map.items():

        obj = bpy.data.objects.get(obj_name)
        if not obj:
            continue

        if parent_name:
            parent_obj = bpy.data.objects.get(parent_name)

            if parent_obj:
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                bpy.context.view_layer.objects.active = parent_obj

                bpy.ops.object.parent_set(
                    type='OBJECT',
                    keep_transform=True
                )
        else:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj

            bpy.ops.object.parent_clear(
                type='CLEAR_KEEP_TRANSFORM'
            )


# --------------------
# メッシュ属性を確認・作成する関数
# --------------------
def ensure_mesh_attribute(mesh, name, atype='INT', domain='POINT'):
    """
    指定したメッシュに属性が存在するか確認し、存在しなければ作成する。

    Parameters
    ----------
    mesh : bpy.types.Mesh
        対象のメッシュデータ
    name : str
        作成/確認する属性名（例: 'vid', 'eid', 'fid'）
    atype : str
        属性のデータ型 ('INT', 'FLOAT', 'FLOAT_VECTOR', 'STRING' など)
    domain : str
        属性を付与する対象の要素タイプ
        'POINT' -> 頂点, 'EDGE' -> 辺, 'FACE' -> 面
    """
    # Polygon domain は FACE に変換（Blender内部での表記揺れ対応）
    if domain == "POLYGON":
        domain = "FACE"
    # すでに属性が存在する場合はそれを返す
    if name in mesh.attributes:
        return mesh.attributes[name]
    else:
        # 属性が存在しなければ新規作成
        # mesh.attributes.new() は新しいカスタム属性を作成する
        # domain で頂点・辺・面のどれに付与するか指定
        # atype で属性の型を指定（ここでは整数）
        return mesh.attributes.new(name=name, type=atype, domain=domain)

# --------------------
# メッシュに VID/EID/FID を割り当てる初期化関数
# --------------------
def init_assign_all_ids(obj_name):
    """
    指定したオブジェクトのメッシュに対して
    - VID (Vertex ID)
    - EID (Edge ID)
    - FID (Polygon ID)
    を付与し、連番を割り当てる。

    Parameters
    ----------
    obj_name : str
        メッシュオブジェクト名（bpy.data.objects に登録されている名前）
    """
    # オブジェクトを取得
    obj = bpy.data.objects[obj_name]
    # メッシュデータを取得
    me = obj.data
    # --- 属性を確認・作成 ---
    # 頂点用属性 "vid" を作成または取得
    ensure_mesh_attribute(me, "vid", atype='INT', domain='POINT')
    # 辺用属性 "eid" を作成または取得
    ensure_mesh_attribute(me, "eid", atype='INT', domain='EDGE')
    # 面用属性 "fid" を作成または取得
    ensure_mesh_attribute(me, "fid", atype='INT', domain='FACE')
    # --- 各要素に連番を割り当て ---
    # 頂点に VID を割り当て
    for i in range(len(me.vertices)):
        me.attributes["vid"].data[i].value = 0
    # 辺に EID を割り当て
    for i in range(len(me.edges)):
        me.attributes["eid"].data[i].value = 0
    # 面に FID を割り当て
    for i in range(len(me.polygons)):
        me.attributes["fid"].data[i].value = 0
    # メッシュデータの更新（属性変更を反映）
    me.update()

    # 重複IDを座標順で修正
    fix_duplicate_ids(obj_name)

# --------------------
# カスタムID -> インデックス 変換
# --------------------
def custom_id_to_index(obj_name, custom_id_list, elem_type='EDGE'):
    """
    カスタム ID から bmesh 上の index を取得する (read-only 検索)。

    Input :
        obj_name        : 対象オブジェクト名 (str)。MESH 型である必要がある
        custom_id_list  : 検索したいカスタム ID のリスト (list[int])
                          例: [3, 7, 12]
        elem_type       : 要素種別 ('VERT' | 'EDGE' | 'FACE')。
                          それぞれ vid / eid / fid レイヤーを参照する
    Output:
        indices         : 各カスタム ID に対応する bmesh の index リスト (list[int])
                          見つからなかった ID は -1 となる
                          例: [5, 8, -1]  ← 12 は見つからなかった

    仕様メモ:
        - 本関数は BMesh の中身を一切変更しない (read-only)。
          したがって `bm.to_mesh(mesh)` での書き戻しは行わない。
          (旧実装は不要な書き戻しで、 target が EDIT モードのとき
           ValueError: to_mesh(): Mesh '...' is in editmode を発生させていた)
        - 対象オブジェクトのモード (OBJECT / EDIT) に応じて BMesh の取得方法を
          切り替える。 これにより 呼び出し側がアクティブオブジェクトを別オブジェクト
          に切り替えていて、 obj_name が EDIT モード のまま残っていても安全に動く
          (旧実装は active と obj_name が同一である暗黙前提だった)。
        - モード切り替え (bpy.ops.object.mode_set) は副作用が大きく、 active と
          obj_name が異なる場合に意図しないオブジェクトを EDIT 化してしまうため
          本関数では行わない。
    """
    # 対象オブジェクトを名前で取得
    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        raise ValueError(f"オブジェクト '{obj_name}' が見つからないかメッシュではありません")

    # 対象 mesh データブロック
    mesh = obj.data

    # ------------------------------------------------------------
    # BMesh 取得 (対象 obj の mode に応じて取り方を切り替え)
    # ------------------------------------------------------------
    # 対象 obj が EDIT モード:
    #   BMEditMesh が保持している live な bmesh を直接取得する。
    #   この bmesh は EDIT モード側が所有しているため bm.free() しない。
    # 対象 obj が EDIT モード以外 (OBJECT 等):
    #   通常の Mesh データから 新規 bmesh を生成する。
    #   この bmesh は本関数の所有物なので 最後に bm.free() する。
    # 同じ分岐パターンは get_vert_point_customid に揃えてある。
    if obj.mode == 'EDIT':
        bm       = bmesh.from_edit_mesh(mesh)
        owns_bm  = False    # EDIT 側所有のため free 不要
    else:
        bm       = bmesh.new()
        bm.from_mesh(mesh)
        owns_bm  = True     # この関数が生成したので 末尾で free 必須

    # ------------------------------------------------------------
    # 要素種別に応じて 検索対象のカスタム ID レイヤーと イテレータを取得
    # ------------------------------------------------------------
    if elem_type == 'VERT':
        layer    = bm.verts.layers.int.get("vid")
        elements = bm.verts
    elif elem_type == 'EDGE':
        layer    = bm.edges.layers.int.get("eid")
        elements = bm.edges
    elif elem_type == 'FACE':
        layer    = bm.faces.layers.int.get("fid")
        elements = bm.faces
    else:
        # 異常系: 自前で確保した bmesh のみ解放してから例外送出
        if owns_bm:
            bm.free()
        raise ValueError("elem_type は 'VERT', 'EDGE', 'FACE' のいずれかにしてください")

    # カスタム ID レイヤーが未設定のメッシュには対応できない
    if layer is None:
        if owns_bm:
            bm.free()
        raise ValueError(f"オブジェクトに '{elem_type.lower()}id' レイヤーが存在しません")

    # ------------------------------------------------------------
    # 各カスタム ID について bmesh 上の index を線形検索で求める
    # (要素数が多いと O(N*M) になるが、 ID 数 M は数件想定なので許容)
    # ------------------------------------------------------------
    indices = []
    for target_id in custom_id_list:
        # 見つからなかった場合の既定値 -1 (呼び出し側で異常検知に使える)
        index_found = -1
        for ele in elements:
            if ele[layer] == target_id:
                # ★重要★ bmesh の index を返す (Mesh 側 index と一致する前提)
                index_found = ele.index
                break
        indices.append(index_found)

    # ------------------------------------------------------------
    # 後始末: 自前で確保した bmesh のみ解放
    # (read-only のため bm.to_mesh は呼ばない)
    # ------------------------------------------------------------
    if owns_bm:
        bm.free()

    return indices

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

# --------------------------------------
# 座標条件 → カスタムID リスト 取得
# --------------------------------------
def get_custom_ids_by_coord(obj_name, predicate, elem_type='VERT'):
    """
    指定した predicate(coord) が True になる 要素 の カスタムID (vid/eid/fid) を返す.

    Blender GUI で 「ある領域 (Y < 0.1 等) の vertex を 矩形選択」 する操作 を、
    後続の element_select_customid / mesh_elements_rotate_customid に 渡せる
    custom_id リスト として 取得する用途.

    使用例:
        # Y < -0.15 の頂点 vid を取得 → 折れ部 vert として 選択
        fold_vids = mdl_cm_lib.get_custom_ids_by_coord(
            obj_name  = "my_obj"
        ,   predicate = lambda c: c.y < -0.15
        ,   elem_type = 'VERT'
        )
        mdl_cm_lib.element_select_customid(
            element_list      = fold_vids
        ,   select_mode       = 'VERT'
        ,   object_name_list  = ["my_obj"]
        )

    Input:
        obj_name  : 対象オブジェクト名 (str)
        predicate : 関数 (mathutils.Vector) -> bool. True を返す要素のみ収集
        elem_type : 'VERT' / 'EDGE' / 'FACE'
                    EDGE → 中点座標 で 判定
                    FACE → 面 中央座標 (calc_center_median) で 判定
    Output:
        custom_id (int) のリスト. 該当なし or 失敗時 は [].
    """
    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        return []

    # OBJECT モードに 切替 (bmesh.from_mesh は OBJECT モード前提)
    current_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
    if current_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 要素タイプ ごとに レイヤー / 座標取得関数 を 設定
    if elem_type == 'VERT':
        layer = bm.verts.layers.int.get("vid")
        elements = bm.verts
        get_coord = lambda e: e.co
    elif elem_type == 'EDGE':
        layer = bm.edges.layers.int.get("eid")
        elements = bm.edges
        get_coord = lambda e: (e.verts[0].co + e.verts[1].co) * 0.5
    elif elem_type == 'FACE':
        layer = bm.faces.layers.int.get("fid")
        elements = bm.faces
        get_coord = lambda e: e.calc_center_median()
    else:
        bm.free()
        if current_mode != 'OBJECT':
            try: bpy.ops.object.mode_set(mode=current_mode)
            except: pass
        return []

    if layer is None:
        bm.free()
        if current_mode != 'OBJECT':
            try: bpy.ops.object.mode_set(mode=current_mode)
            except: pass
        return []

    ids = []
    for ele in elements:
        if predicate(get_coord(ele)):
            ids.append(ele[layer])

    bm.free()

    # 元 mode に 復帰
    if current_mode != 'OBJECT':
        try: bpy.ops.object.mode_set(mode=current_mode)
        except: pass

    return ids

# --------------------------------------
# カスタムID: 面追加 新規作成メッシュ -> カスタムID 0
# --------------------------------------
def edge_face_add_bmesh_with_zero_customid(obj_name):
    """
    bpy.ops.mesh.edge_face_add() の完全置換
    新規作成された Face / Edge の customID を 0 にする
    """

    obj = bpy.data.objects[obj_name]
    mesh = obj.data

    bm = bmesh.from_edit_mesh(mesh)

    vid_layer = bm.verts.layers.int.get("vid")
    eid_layer = bm.edges.layers.int.get("eid")
    fid_layer = bm.faces.layers.int.get("fid")

    # --- 選択 geom ---
    geom_input = []
    geom_input.extend([v for v in bm.verts if v.select])
    geom_input.extend([e for e in bm.edges if e.select])

    if not geom_input:
        return

    # --- スナップショット ---
    faces_before = set(bm.faces)
    edges_before = set(bm.edges)

    # --- 面生成 ---
    bmesh.ops.contextual_create(
        bm,
        geom=geom_input
    )

    # --- 差分抽出 ---
    faces_after = set(bm.faces)
    edges_after = set(bm.edges)

    new_faces = faces_after - faces_before
    new_edges = edges_after - edges_before

    # --- customID = 0 ---
    if fid_layer:
        for f in new_faces:
            f[fid_layer] = 0
            f.select = True

    if eid_layer:
        for e in new_edges:
            e[eid_layer] = 0
            e.select = True

    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)

# --------------------------------------
# カスタムID: 頂点押し出し -> カスタムID 0
# --------------------------------------
def extrude_single_vertex_bmesh_zero_id(
    obj_name,
    vert_custom_id,
    move_vec
):
    obj = bpy.data.objects[obj_name]
    mesh = obj.data

    bm = bmesh.from_edit_mesh(mesh)

    # カスタムIDレイヤ
    vid_layer = bm.verts.layers.int.get("vid")
    eid_layer = bm.edges.layers.int.get("eid")

    if not vid_layer:
        raise RuntimeError("vid layer not found")

    # 対象頂点（customIDで特定）
    src_verts = [v for v in bm.verts if v[vid_layer] == vert_custom_id]
    if not src_verts:
        raise RuntimeError(f"Vertex with customID {vert_custom_id} not found")

    src_vert = src_verts[0]

    # --- 押し出し ---
    res = bmesh.ops.extrude_vert_indiv(
        bm,
        verts=[src_vert]
    )

    new_verts = res.get("verts", [])
    new_edges = res.get("edges", [])

    # --- ★グローバル → ローカル変換★ ---
    move_vec_local = obj.matrix_world.inverted().to_3x3() @ Vector(move_vec)

    # --- 移動 ---
    for v in new_verts:
        v.co += move_vec_local

    # --- 新規要素の customID を 0 ---
    for v in new_verts:
        v[vid_layer] = 0

    if eid_layer:
        for e in new_edges:
            e[eid_layer] = 0

    # 表示・後続処理のため選択（任意だが今の構造では必要）
    for v in bm.verts:
        v.select = False
    for v in new_verts:
        v.select = True

    bmesh.update_edit_mesh(mesh)

# ------------------------------------------------------------
# ループカット専用：
# 選択されている頂点・辺・面の customID をすべて 0 にする
# ------------------------------------------------------------
def zero_selected_elements_customid(obj_name):
    """
    loopcut / loopcut_slide 後に呼ぶことを想定。
    選択されている VERT / EDGE / FACE の customID を 0 にする。
    非選択要素は一切変更しない。
    """

    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        raise ValueError(f"{obj_name} はメッシュオブジェクトではありません")

    if bpy.context.object.mode != 'EDIT':
        raise RuntimeError("EDIT モードで実行してください")

    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)

    vid_layer = bm.verts.layers.int.get("vid")
    eid_layer = bm.edges.layers.int.get("eid")
    fid_layer = bm.faces.layers.int.get("fid")

    # 頂点
    if vid_layer is not None:
        for v in bm.verts:
            if v.select:
                v[vid_layer] = 0

    # 辺
    if eid_layer is not None:
        for e in bm.edges:
            if e.select:
                e[eid_layer] = 0

    # 面
    if fid_layer is not None:
        for f in bm.faces:
            if f.select:
                f[fid_layer] = 0

    bmesh.update_edit_mesh(mesh, loop_triangles=False, destructive=False)

# ------------------------------
# 重複IDを座標順に修正する
# ------------------------------
def fix_duplicate_ids(obj_name, epsilon=1e-6):
    """
    重複カスタムIDを安定的に解消する。
    - ID=0 は常に再割り当て対象
    - 既存ID(>0)は可能な限り保持
    - 再割り当ては maxID+1 以降のみ
    - 順序は Z→Y→X、小さい順（完全一致時のみ index）
    """

    # Save mode
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    obj = bpy.data.objects[obj_name]
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    vid_layer = bm.verts.layers.int.get("vid")
    eid_layer = bm.edges.layers.int.get("eid")
    fid_layer = bm.faces.layers.int.get("fid")

    # --- Utility ---
    def round_coords(coords):
        return tuple(round(c / epsilon) for c in coords)

    def sort_key(elem, coords):
        r = round_coords(coords)
        return (r, coords, elem.index)

    def fix_elements(elements, layer, get_coords):
        # 現在のID一覧（0除外）
        existing_ids = sorted(
            {ele[layer] for ele in elements if ele[layer] is not None and ele[layer] > 0}
        )
        next_id = (max(existing_ids) + 1) if existing_ids else 1

        # IDごとに要素を集約
        id_map = {}
        zero_elements = []

        for ele in elements:
            cid = ele[layer]
            if cid is None:
                continue
            if cid == 0:
                zero_elements.append(ele)
            else:
                id_map.setdefault(cid, []).append(ele)

        # 再割り当て対象
        reassign_targets = []

        # --- 重複ID（>0）の処理 ---
        for cid, elems in id_map.items():
            if len(elems) == 1:
                continue

            elems.sort(key=lambda e: sort_key(e, get_coords(e)))
            # 先頭は保持、残りを再割り当て
            reassign_targets.extend(elems[1:])

        # --- ID=0 は全て再割り当て ---
        zero_elements.sort(key=lambda e: sort_key(e, get_coords(e)))
        reassign_targets.extend(zero_elements)

        # --- 再割り当て ---
        for ele in reassign_targets:
            ele[layer] = next_id
            next_id += 1

    # Vert
    if vid_layer:
        fix_elements(
            bm.verts,
            vid_layer,
            lambda v: (v.co.z, v.co.y, v.co.x)
        )

    # Edge
    if eid_layer:
        fix_elements(
            bm.edges,
            eid_layer,
            lambda e: ((e.verts[0].co + e.verts[1].co) / 2).to_tuple()
        )

    # Face
    if fid_layer:
        fix_elements(
            bm.faces,
            fid_layer,
            lambda f: f.calc_center_median().to_tuple()
        )

    bm.to_mesh(mesh)
    mesh.update()
    bm.free()

    bpy.ops.object.mode_set(mode=current_mode)



# ------------------------------
# カスタムID版: ループカット + カスタムID処理
# ------------------------------
def multi_value_loopcut_slide_customid(
    bl=20,
    cid_list=[0],
    slide_list=[0],
    direction_list=None
):
    obj = bpy.context.active_object
    obj_name = obj.name

    if direction_list is None:
        direction_list = [1] * len(cid_list)

    current_mode = obj.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')

    bl_tmp = bl
    for i in range(len(cid_list)):
        # カスタムIDからインデックス取得
        idx = custom_id_to_index(
            obj_name=obj_name,
            elem_type='EDGE',
            custom_id_list=[cid_list[i]]
        )
        ratio = bl_tmp / bl
        value = ((1 / ((bl*ratio)/2)) * slide_list[i]) - 1
        bl_tmp = bl - (bl - slide_list[i])

        bpy.ops.mesh.loopcut_slide(
            MESH_OT_loopcut={
                "number_cuts": 1,
                "smoothness": 0,
                "falloff": 'INVERSE_SQUARE',
                "object_index": 0,
                "edge_index": idx[0]
            },
            TRANSFORM_OT_edge_slide={
                "value": value * direction_list[i],
                "single_side": False,
                "use_even": False
            }
        )

        # 選択メッシュ カスタムID 0
        zero_selected_elements_customid(obj_name)

        # 重複IDを座標順で修正
        fix_duplicate_ids(obj_name)

    try:
        bpy.ops.object.mode_set(mode=current_mode)
    except RuntimeError:
        pass


# ========================================================================
# = ▼ カスタムID版: 辺、面、頂点 選択
# ========================================================================
def element_select_customid(
        element_list                # 要素 Index List
,       select_mode                 # Mode（VERT/EDGE/FACE）
,       object_name_list=["NaN"]    # Object Name List
,       loop_select=False           # Loop選択
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Ensure OBJECT mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    # Deselect all first
    bpy.ops.object.select_all(action='DESELECT')
    if (object_name_list[0] != "NaN"):
        # Current Active Object
        for i in range(len(object_name_list)):
            object_name = object_name_list[i]
            obj = bpy.data.objects.get(object_name)
            if obj:
                obj.select_set(True)
                bpy.context.view_layer.objects.active = obj
    # Get Active Object
    obj = bpy.context.object
    # Check Mesh
    if obj and obj.type == 'MESH':
        mesh = obj.data
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type=select_mode)
        # Release Select Index
        bpy.ops.mesh.select_all(action='DESELECT')
        # Change Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        # Select Element
        if ((len(element_list) >= 1) and (element_list[0] == "all")):
            # Select All
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type=select_mode)
            bpy.ops.mesh.select_all(action='SELECT')
        else:
            # カスタムIDからインデックス取得
            element_list = custom_id_to_index(
                obj_name=object_name
            ,   elem_type=select_mode
            ,   custom_id_list=element_list
            )
            # Select Element
            for i in range(len(element_list)):
                target_ele_index = element_list[i]
                if (select_mode == "FACE"):
                    mesh.polygons[target_ele_index].select = True
                elif (select_mode == "EDGE"):
                    mesh.edges[target_ele_index].select = True
                elif (select_mode == "VERT"):
                    mesh.vertices[target_ele_index].select = True
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        if (loop_select == True):
            # Loop Select (Alt+Click)
            # Blender 5.2 で mesh.loop_multi_select(ring=False) が
            # mesh.select_edge_loop_multi() に分離・改名された
            bpy.ops.mesh.select_edge_loop_multi()
    else:
        print("No mesh object selected.")
    # Return Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ カスタムID版: 面 のカスタムIDから構成する頂点のカスタムIDを取得 (時計回り/半時計回り)
# ========================================================================
def get_outer_vertex_custom_ids(
    obj_name: str,
    face_custom_ids: list,
    clockwise: bool = False,
    epsilon: float = 1e-6,
):
    """
    指定した複数の面（fid のリスト）だけを対象にし、
    それらの面群が形成する「最も大きい外周ループ」の頂点カスタムIDを返す。
    - 複数ループがある場合は最大のループ（頂点数が最大）を返す（外側想定）
    - epsilon: 座標丸めの精度（誤差を同一扱いにする）
    """

    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        raise RuntimeError(f"Object '{obj_name}' not found or not a mesh")

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    try:
        fid_layer = bm.faces.layers.int.get("fid")
        vid_layer = bm.verts.layers.int.get("vid")
        if fid_layer is None:
            raise RuntimeError("fid レイヤーがありません")
        if vid_layer is None:
            raise RuntimeError("vid レイヤーがありません")

        # 対象 face の集合（face_custom_ids に含まれるもの）
        target_faces = {f for f in bm.faces if f[fid_layer] in face_custom_ids}
        if not target_faces:
            raise RuntimeError("指定された fid の面がありません")

        # 境界エッジを抽出（target_faces に所属しており、隣接 target_faces は1つだけ）
        boundary_edges = []
        for f in target_faces:
            for e in f.edges:
                adjacent_target = [fa for fa in e.link_faces if fa in target_faces]
                if len(adjacent_target) == 1:
                    boundary_edges.append(e)

        if not boundary_edges:
            raise RuntimeError("外周エッジがありません（面が閉じている可能性）")

        # 頂点 -> 境界エッジ 隣接マップ
        vert_to_edges = defaultdict(list)
        for e in boundary_edges:
            for v in e.verts:
                vert_to_edges[v].append(e)

        # エッジ接続成分（fragment）を抽出（各 fragment は境界エッジの塊）
        unvisited_edges = set(boundary_edges)
        fragments = []  # list of sets of edges
        while unvisited_edges:
            start_e = unvisited_edges.pop()
            comp = set([start_e])
            q = deque([start_e])
            while q:
                ee = q.popleft()
                for v in ee.verts:
                    for nb in vert_to_edges.get(v, []):
                        if nb not in comp:
                            comp.add(nb)
                            if nb in unvisited_edges:
                                unvisited_edges.remove(nb)
                            q.append(nb)
            fragments.append(comp)

        # ヘルパー：座標キー（丸め）と tie-break に要素.index を使う
        def rounded_key_vec(co):
            return (round(co.z / epsilon), round(co.y / epsilon), round(co.x / epsilon))

        def other_vertex_key(edge, v):
            v1, v2 = edge.verts
            other = v2 if v1 == v else v1
            return rounded_key_vec(other.co) + (other.index,)

        # 各 fragment について「順序付けた頂点ループ」を作成（決定論的に）
        def build_ordered_loop_from_edge_component(edge_comp):
            # collect vertices in this fragment
            verts = set()
            for ee in edge_comp:
                verts.update(ee.verts)

            # adjacency: vertex -> list(edges) (sorted deterministically)
            local_vert_edges = {}
            for v in verts:
                es = [ee for ee in vert_to_edges.get(v, []) if ee in edge_comp]
                # sort by other-vertex key to make traversal deterministic
                es.sort(key=lambda ee: other_vertex_key(ee, v))
                local_vert_edges[v] = es

            # pick deterministic start vertex: minimal rounded (Z,Y,X), then min index
            sorted_verts = sorted(list(verts), key=lambda v: (rounded_key_vec(v.co), v.index))
            start_v = sorted_verts[0]

            # traverse to form a loop / chain
            loop_vids = []
            visited_e = set()
            current_v = start_v
            prev_e = None

            # safety guard iterations
            max_steps = len(edge_comp) * 4 + 100
            steps = 0
            while True:
                steps += 1
                if steps > max_steps:
                    break

                loop_vids.append(current_v[vid_layer])

                # choose next edge from local_vert_edges[current_v]
                candidate = None
                for ee in local_vert_edges.get(current_v, []):
                    if ee is prev_e:
                        continue
                    if ee not in visited_e:
                        candidate = ee
                        break
                if candidate is None:
                    # fallback: pick any other edge deterministically (if exists)
                    for ee in local_vert_edges.get(current_v, []):
                        if ee is not prev_e:
                            candidate = ee
                            break

                if candidate is None:
                    # dead end
                    break

                visited_e.add(candidate)
                # step to next vertex
                v1, v2 = candidate.verts
                next_v = v2 if current_v == v1 else v1

                if next_v == start_v:
                    # closed loop detected; stop after adding start (we don't append start again)
                    break

                prev_e = candidate
                current_v = next_v

            # deduplicate while preserving order (edge case safety)
            seen = set()
            uniq_vids = []
            for vid in loop_vids:
                if vid not in seen:
                    seen.add(vid)
                    uniq_vids.append(vid)

            return uniq_vids

        # 各 fragment からループを作り、最大長のものを採用（外周想定）
        loops = []
        for frag in fragments:
            loop_vids = build_ordered_loop_from_edge_component(frag)
            if loop_vids:
                loops.append(loop_vids)

        if not loops:
            raise RuntimeError("外周ループが構築できませんでした")

        # pick the longest loop (most vertices)
        loops.sort(key=len, reverse=True)
        best_loop = loops[0]

        if clockwise:
            best_loop = list(reversed(best_loop))

        return best_loop

    finally:
        bm.free()

# ========================================================================
# = ▼ カスタムID版: 削除された頂点の削除 リスト整理
# ========================================================================
def cleanup_vertex_customid_list(obj_name, custom_id_list):
    """
    削除後に存在しなくなった頂点のカスタムIDを除去し、
    元の順序はそのまま保つ。

    Parameters
    ----------
    obj_name : str
    custom_id_list : List[int]

    Returns
    -------
    List[int]
        生存している頂点のみのカスタムIDのリスト
    """

    obj = bpy.data.objects[obj_name]
    mesh = obj.data

    bm = bmesh.new()
    bm.from_mesh(mesh)
    vid_layer = bm.verts.layers.int.get("vid")

    if vid_layer is None:
        bm.free()
        raise RuntimeError("vid レイヤーが存在しません")

    # (1) 現在存在している vid をセット化
    alive_vids = {v[vid_layer] for v in bm.verts}

    # (2) 消滅した vid を除外（順序は維持）
    cleaned = [cid for cid in custom_id_list if cid in alive_vids]

    bm.free()
    return cleaned

# ========================================================================
# = ▼ カスタムID版: 面押し出し インデックス固定
# ========================================================================
def fix_index_extrude_region_customid(
    face_cid=[0]                # Custom ID Face List
,   mv_value=(-5,0,0)           # Move Value
,   object_name="obj_name"      # Active Object Name
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Get Vert Index List from Face Custom ID
    vert_idx_list = get_outer_vertex_custom_ids(
        obj_name=object_name
    ,   face_custom_ids=face_cid
    )
    # Convert Extrude Index to Custom ID
    vert_idx_list_i = custom_id_to_index(
        obj_name=object_name
    ,   custom_id_list=vert_idx_list
    ,   elem_type='VERT'
    )
    # Convert Extrude Index to Custom ID
    face_idx_list_i = custom_id_to_index(
        obj_name=object_name
    ,   custom_id_list=face_cid
    ,   elem_type='FACE'
    )
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Get Number of Angles (角数)
    li_len = len(vert_idx_list)
    # Save Data
    ei_a=[] # Extrude Index
    # Vert Extrude
    for i in range(li_len):
        # Select Element
        element_select_customid(
            element_list=[vert_idx_list[i]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # 押し出し、引き込み（bmesh版・新規ID=0保証）
        extrude_single_vertex_bmesh_zero_id(
            obj_name=object_name,
            vert_custom_id=vert_idx_list[i],
            move_vec=mv_value
        )
        # 重複IDを座標順で修正
        fix_duplicate_ids(object_name)
        # Select Add Vertex Index (追加された頂点 選択)
        new_vertex_index = len(bpy.context.object.data.vertices) - 1
        bpy.context.object.data.vertices[new_vertex_index].select = True
        # Update Mesh
        bpy.context.view_layer.objects.active = bpy.context.object
        # Change Mode
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        # Get Active Object
        obj = bpy.context.object
        # Get Mesh Data
        mesh = obj.data
        # Get the index of the selected vertex
        selected_vertex_indices = [v.index for v in mesh.vertices if v.select]
        # Add List
        ei_a.append(selected_vertex_indices[0])
    # index to customID
    ei_a_ci = index_to_custom_id(
        obj_name=object_name
    ,   index_list=ei_a
    ,   elem_type='VERT'
    )
    vert_idx_list = index_to_custom_id(
        obj_name=object_name
    ,   index_list=vert_idx_list_i
    ,   elem_type='VERT'
    )
    # Delete Face
    element_select(
        element_list=face_idx_list_i
    ,   select_mode="FACE"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    # Add Face
    for i in range(li_len-1):
        element_select_customid(
            element_list=[vert_idx_list[i], ei_a_ci[i], vert_idx_list[i+1], ei_a_ci[i+1]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # 面 追加・埋める・貼る (F)
        edge_face_add_bmesh_with_zero_customid(object_name)
        # 重複IDを座標順で修正
        fix_duplicate_ids(object_name)
    # Add Face
    element_select_customid(
        element_list=[vert_idx_list[0], ei_a_ci[0], vert_idx_list[li_len-1], ei_a_ci[li_len-1]]
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    edge_face_add_bmesh_with_zero_customid(object_name)
    # 重複IDを座標順で修正
    fix_duplicate_ids(object_name)
    # Add Face
    element_select_customid(
        element_list=ei_a_ci
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    edge_face_add_bmesh_with_zero_customid(object_name)
    # 重複IDを座標順で修正
    fix_duplicate_ids(object_name)
    # モード変更
    bpy.ops.mesh.select_mode(type='FACE')
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ カスタムID版: 頂点列 (線状) 押し出し インデックス固定
# ========================================================================
# fix_index_extrude_region_customid の 頂点列 (= 順序付き 線状) 入力 版。
# face を 経由せず 頂点 customID リスト を 直接 受け取り、
# 各頂点 を mv_value だけ extrude (押し出し移動) して、
# 隣接ペア (vi, vi+1, vi+1', vi') で 側面 四角形 を 連続 貼る。
#
# 入力 が 線状 のため:
#   - 両端 接続 (最後と最初 を 結ぶ 四角形) は 行わない
#   - 蓋面 (新頂点 全体 で 1 枚) も 貼らない
#   - 元 face の 削除 も 行わない (= 入力 頂点列 が face を 構成 している かは 関知 しない)
#
# 元頂点 は extrude 後 も 元位置 に 残る (extrude_single_vertex_bmesh_zero_id の 既存挙動)。
# ------------------------------------------------------------------------
# Input :
#   vert_cid     : 押し出し対象 頂点 customID リスト (順序付き、線状を 想定)
#                  例: [3, 7, 12]  → 頂点 v3, v7, v12 を 順 に 押し出し、
#                                    四角形 (v3, v7) ペア + (v7, v12) ペア の 2 枚 を 貼る
#   mv_value     : 押し出し移動 ベクトル (x, y, z) ※ グローバル座標
#                  extrude_single_vertex_bmesh_zero_id が 内部 で
#                  obj.matrix_world.inverted() を かけて ローカル に 変換 する
#   object_name  : 対象 オブジェクト名 (str)
# Output:
#   各 元頂点 vi に対して 新頂点 vi' が 追加 され、
#   側面 四角形 [vi, vi', vi+1', vi+1] が li_len-1 枚 貼られる。
#   新頂点 と 側面 四角形 の customID は edge_face_add_bmesh_with_zero_customid と
#   fix_duplicate_ids により 0 → 連番 採番 される (既存 ID と 衝突 しない)。
#   関数 終了時 の モード は 入力時 の モード に 戻す。
# ========================================================================
def fix_index_extrude_vert_customid(
    vert_cid    = [0]               # Custom ID Vert List (順序付き 線状)
,   mv_value    = (-5, 0, 0)        # Move Value (グローバル 座標 ベクトル)
,   object_name = "obj_name"        # Active Object Name
):
    # Save Current Mode (関数 終了時 に 戻す ため)
    current_mode = bpy.context.object.mode
    # CustomID → Index 変換 (extrude 中 の ID 再採番 で customID 値 が 変わる
    # 可能性 が あるため、 順序保持 用 に index で 保持)
    vert_idx_list_i = custom_id_to_index(
        obj_name        = object_name
    ,   custom_id_list  = vert_cid
    ,   elem_type       = 'VERT'
    )
    # Mode 切替: VERT 選択モード で 操作 する
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # 入力 頂点 数
    li_len = len(vert_cid)
    # 押し出し で 追加 された 新頂点 の index 配列 (順序保持)
    ei_a = []
    # Vert Extrude (各 元頂点 を 個別 に 押し出し)
    for i in range(li_len):
        # 元 頂点 を customID で 選択
        element_select_customid(
            element_list      = [vert_cid[i]]
        ,   select_mode       = "VERT"
        ,   object_name_list  = [object_name]
        )
        # 押し出し、引き込み (bmesh版・新規 ID = 0 保証)
        # 元頂点 vi は 元位置 に 残り、 新頂点 vi' が mv_value だけ 移動 した 位置 に 追加 される
        extrude_single_vertex_bmesh_zero_id(
            obj_name        = object_name
        ,   vert_custom_id  = vert_cid[i]
        ,   move_vec        = mv_value
        )
        # 重複ID を 座標順 で 修正 (新頂点 の ID = 0 を 連番 に 振り直す)
        fix_duplicate_ids(object_name)
        # 追加された 頂点 (= 最大 index) を 選択 (face版 と 同じ 取得 ロジック)
        new_vertex_index = len(bpy.context.object.data.vertices) - 1
        bpy.context.object.data.vertices[new_vertex_index].select = True
        # Update Mesh
        bpy.context.view_layer.objects.active = bpy.context.object
        # Mode リフレッシュ (選択状態 を bmesh 側 に 反映)
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='VERT')
        # Get Active Object
        obj  = bpy.context.object
        # Get Mesh Data
        mesh = obj.data
        # Get the index of the selected vertex (新頂点 vi' の index)
        selected_vertex_indices = [v.index for v in mesh.vertices if v.select]
        # 新頂点 index を 配列 に 追加
        ei_a.append(selected_vertex_indices[0])
    # Index → CustomID (新頂点)
    ei_a_ci = index_to_custom_id(
        obj_name    = object_name
    ,   index_list  = ei_a
    ,   elem_type   = 'VERT'
    )
    # Index → CustomID (元頂点 順序保持: extrude 中 の 再採番 で customID 値 が 変わって いる
    # 可能性 が あるため、 保持 した index 経由 で 最新 の customID を 再取得 する)
    vert_cid_after = index_to_custom_id(
        obj_name    = object_name
    ,   index_list  = vert_idx_list_i
    ,   elem_type   = 'VERT'
    )
    # 隣接 ペア (vi, vi', vi+1', vi+1) で 側面 四角形 を 貼る
    # 線状 のため ペア 数 は li_len - 1 (両端 接続 は しない)
    for i in range(li_len - 1):
        # 4頂点 を 選択 (vi → vi' → vi+1' → vi+1 の 巡回 順 で 渡す)
        # edge_face_add_bmesh_with_zero_customid 内部 で 適切 な 頂点順 に 並べ替え られて
        # 平面 四角形 が 貼られる
        element_select_customid(
            element_list      = [vert_cid_after[i], ei_a_ci[i], vert_cid_after[i+1], ei_a_ci[i+1]]
        ,   select_mode       = "VERT"
        ,   object_name_list  = [object_name]
        )
        # 面 追加・埋める・貼る (F)
        edge_face_add_bmesh_with_zero_customid(object_name)
        # 重複ID を 座標順 で 修正 (新規面 / 新規辺 の ID = 0 を 連番 に 振り直す)
        fix_duplicate_ids(object_name)
    # 選択モード を FACE に 切替 (face版 と 同じ 終了状態)
    bpy.ops.mesh.select_mode(type='FACE')
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ カスタムID版: 最大値取得
# ========================================================================
def _get_max_custom_id(obj, layer_name, elem_type):
    """
    指定オブジェクトの最大カスタムIDを取得
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if elem_type == 'VERT':
        layer = bm.verts.layers.int.get(layer_name)
        elements = bm.verts
    elif elem_type == 'EDGE':
        layer = bm.edges.layers.int.get(layer_name)
        elements = bm.edges
    elif elem_type == 'FACE':
        layer = bm.faces.layers.int.get(layer_name)
        elements = bm.faces
    else:
        bm.free()
        raise ValueError("elem_type must be 'VERT', 'EDGE', or 'FACE'")

    if layer is None or not elements:
        bm.free()
        return -1

    max_id = max(ele[layer] for ele in elements)
    bm.free()
    return max_id

# ========================================================================
# = ▼ カスタムID版: 加算
# ========================================================================
def _offset_custom_id(obj, layer_name, elem_type, offset):
    """
    指定オブジェクトのカスタムIDを offset 分加算
    """
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    if elem_type == 'VERT':
        layer = bm.verts.layers.int.get(layer_name)
        elements = bm.verts
    elif elem_type == 'EDGE':
        layer = bm.edges.layers.int.get(layer_name)
        elements = bm.edges
    elif elem_type == 'FACE':
        layer = bm.faces.layers.int.get(layer_name)
        elements = bm.faces
    else:
        bm.free()
        raise ValueError("elem_type must be 'VERT', 'EDGE', or 'FACE'")

    if layer is None:
        bm.free()
        return

    for ele in elements:
        ele[layer] += offset

    bm.to_mesh(mesh)
    bm.free()

# ========================================================================
# = ▼ カスタムID版: カスタムID結合前準備
# ========================================================================
def offset_join_object_custom_ids(
    base_obj_name: str,
    join_obj_name: str,
    vert_layer="vid",
    edge_layer="eid",
    face_layer="fid",
):
    """
    base_obj より join_obj のカスタムIDが必ず大きくなるように調整する
    """
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')

    base_obj = bpy.data.objects.get(base_obj_name)
    join_obj = bpy.data.objects.get(join_obj_name)

    if base_obj is None or join_obj is None:
        raise ValueError("指定されたオブジェクトが見つかりません")

    if base_obj.type != 'MESH' or join_obj.type != 'MESH':
        raise ValueError("両方とも MESH オブジェクトである必要があります")

    # base 側の最大ID取得
    max_vid = _get_max_custom_id(base_obj, vert_layer, 'VERT')
    max_eid = _get_max_custom_id(base_obj, edge_layer, 'EDGE')
    max_fid = _get_max_custom_id(base_obj, face_layer, 'FACE')

    base_max = max(max_vid, max_eid, max_fid)

    # すべて -1 の場合（= base にIDが無い）
    if base_max < 0:
        base_max = 0

    offset = base_max + 1

    # join 側にオフセット適用
    _offset_custom_id(join_obj, vert_layer, 'VERT', offset)
    _offset_custom_id(join_obj, edge_layer, 'EDGE', offset)
    _offset_custom_id(join_obj, face_layer, 'FACE', offset)

    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

    return offset


# ========================================================================
# = ▼ リスト 循環回転
# ========================================================================
def rotate_list_by_offset(lst, offset):
    """
    lst を offset 個ぶん循環回転する
    offset > 0 : 左回転
    offset < 0 : 右回転
    """
    if not lst:
        return lst

    n = len(lst)
    offset = offset % n  # 長さ超え・負数対策

    return lst[offset:] + lst[:offset]

# ========================================================================
# = ▼ カスタムID版: 筒状 面指定 面貼り インデックス固定
# ========================================================================
def fix_index_connect_vert_customid(
    face_id_1=[0]       # Face Index
,   face_id_2=[1]       # Face Index
,   object_name="object_name"   # Object Name
,   clockwise=False             # 循環リスト向き
,   offset=0                    # 循環リストオフセット
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Get Vert Index List from Face Custom ID
    vert_list_1 = get_outer_vertex_custom_ids(
        obj_name=object_name
    ,   face_custom_ids=face_id_1
    )
    vert_list_2 = get_outer_vertex_custom_ids(
        obj_name=object_name
    ,   face_custom_ids=face_id_2
    ,   clockwise=clockwise
    )
    vert_list_2 = rotate_list_by_offset(
        lst=vert_list_2
    ,   offset=offset
    )
    # Convert Extrude Index to Custom ID
    vert_list_1_i = custom_id_to_index(
        obj_name=object_name
    ,   custom_id_list=vert_list_1
    ,   elem_type='VERT'
    )
    vert_list_2_i = custom_id_to_index(
        obj_name=object_name
    ,   custom_id_list=vert_list_2
    ,   elem_type='VERT'
    )
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Add Face
    for i in range(len(vert_list_1)-1):
        element_select_customid(
            element_list=[vert_list_1[i], vert_list_2[i], vert_list_1[i+1], vert_list_2[i+1]]
        ,   select_mode="VERT"
        ,   object_name_list=[object_name]
        )
        # Add Face (面 追加・埋める・貼る) (F)
        edge_face_add_bmesh_with_zero_customid(object_name)
        # 重複IDを座標順で修正
        fix_duplicate_ids(object_name)
    # Add Face
    element_select_customid(
        element_list=[vert_list_1[0], vert_list_2[0], vert_list_1[-1], vert_list_2[-1]]
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    # Add Face (面 追加・埋める・貼る) (F)
    edge_face_add_bmesh_with_zero_customid(object_name)
    # 重複IDを座標順で修正
    fix_duplicate_ids(object_name)

    # Delete Face
    element_select(
        element_list=vert_list_1_i
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    element_select(
        element_list=vert_list_2_i
    ,   select_mode="VERT"
    ,   object_name_list=[object_name]
    )
    bpy.ops.mesh.delete(type='FACE')
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)


# ========================================================================
# = ▼ 指定頂点（customID）絶対座標取得
# ========================================================================
def get_vert_point_customid(vert_index=0, obj_name=None):
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    else:
        obj = bpy.context.active_object

    if not obj:
        print("オブジェクトが存在しません")
        return None

    # Emptyならその位置を返す
    if obj.type == 'EMPTY':
        p = obj.matrix_world.translation
        return [
            round(p.x, 7),
            round(p.y, 7),
            round(p.z, 7),
        ]

    # Mesh以外
    if obj.type != 'MESH':
        print("メッシュまたはEmptyではありません")
        return None

    # Save Current Mode
    current_mode = obj.mode

    # BMesh 取得（mode 非依存）
    if current_mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        free_bm = False
    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        free_bm = True

    # customID layer
    vid_layer = bm.verts.layers.int.get("vid")
    if not vid_layer:
        if free_bm:
            bm.free()
        print("vid layer が存在しません")
        return None

    # customID で頂点検索
    target = None
    for v in bm.verts:
        if v[vid_layer] == vert_index:
            target = v
            break

    if not target:
        if free_bm:
            bm.free()
        print(f"customID {vert_index} の頂点が見つかりません")
        return None

    # Local → World
    world_co = obj.matrix_world @ target.co
    point_list = [
        round(world_co.x, 7),
        round(world_co.y, 7),
        round(world_co.z, 7),
    ]

    if free_bm:
        bm.free()

    return point_list

# ========================================================================
# = ▼ 指定面（customID）絶対座標取得
# ========================================================================
def get_face_point_customid(face_index=0, obj_name=None):
    if obj_name:
        obj = bpy.data.objects.get(obj_name)
    else:
        obj = bpy.context.active_object

    if not obj:
        print("オブジェクトが存在しません")
        return None

    # Emptyならその位置を返す
    if obj.type == 'EMPTY':
        p = obj.matrix_world.translation
        return [
            round(p.x, 7),
            round(p.y, 7),
            round(p.z, 7),
        ]

    # Mesh以外
    if obj.type != 'MESH':
        print("メッシュまたはEmptyではありません")
        return None

    # Save Current Mode
    current_mode = obj.mode

    # BMesh取得（mode非依存）
    if current_mode == 'EDIT':
        bm = bmesh.from_edit_mesh(obj.data)
        free_bm = False
    else:
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        free_bm = True

    # Face customID layer
    fid_layer = bm.faces.layers.int.get("fid")
    if not fid_layer:
        if free_bm:
            bm.free()
        print("fid layer が存在しません")
        return None

    # customIDで面検索
    target = None
    for f in bm.faces:
        if f[fid_layer] == face_index:
            target = f
            break

    if target is None:
        if free_bm:
            bm.free()
        print(f"customID {face_index} の面が見つかりません")
        return None

    # 面中心（ローカル座標）
    local_center = target.calc_center_median()

    # World座標へ変換
    world_center = obj.matrix_world @ local_center

    point_list = [
        round(world_center.x, 7),
        round(world_center.y, 7),
        round(world_center.z, 7),
    ]

    if free_bm:
        bm.free()

    return point_list

# ========================================================================
# = ▼ カスタムID版: 指定したオブジェクト頂点間 距離取得
# ========================================================================
def point_diff_length_customid(
    obj1_name="obj1_name",   # オブジェクト名またはEmpty名
    obj1_point=0,            # Vert Custom ID
    obj2_name="obj2_name",   # オブジェクト名またはEmpty名
    obj2_point=0,            # Vert Custom ID
    coordinate="X"           # X, Y, Z
):
    # -------------------------
    # Get Objects
    # -------------------------
    obj1 = bpy.data.objects.get(obj1_name)
    obj2 = bpy.data.objects.get(obj2_name)

    if not obj1 or not obj2:
        print("オブジェクトが存在しません")
        return None

    # -------------------------
    # Get Point (OBJ1)
    # -------------------------
    if obj1.type == 'MESH':
        bpy.context.view_layer.objects.active = obj1
        point1 = get_vert_point_customid(obj1_point)
        if point1 is None:
            return None
    else:
        p = obj1.matrix_world.translation
        point1 = [p.x, p.y, p.z]

    # -------------------------
    # Get Point (OBJ2)
    # -------------------------
    if obj2.type == 'MESH':
        bpy.context.view_layer.objects.active = obj2
        point2 = get_vert_point_customid(obj2_point)
        if point2 is None:
            return None
    else:
        p = obj2.matrix_world.translation
        point2 = [p.x, p.y, p.z]

    # -------------------------
    # Get Diff Length
    # -------------------------
    coord_idx = {"X": 0, "Y": 1, "Z": 2}
    if coordinate not in coord_idx:
        print("Error: coordinate must be X, Y, or Z")
        return None

    axis = coord_idx[coordinate]
    diff_length = abs(point1[axis] - point2[axis])

    return diff_length

# ========================================================================
# = ▼ 長方形 オブジェクト頂点移動
# ========================================================================
def make_cube_move_relative_position_customid(
    cube_name="default_name"                    # Object Name
,   cube_size=(0.1, 0.1, 1.0)                   # Object Size
,   cube_vert=6                                 # Vert Index
,   destination_obj_name="destination_obj_name" # Base Object Name
,   destination_vert=0                          # Vert Index
):
    # Save: Current Mode
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # Release Select
    bpy.ops.object.select_all(action='DESELECT')
    # Add Cube
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    cube_obj = bpy.context.object
    cube_obj.name = cube_name
    # Init Custom ID
    mdl_cm_lib.init_assign_all_ids(cube_name)
    # Change Size
    bpy.ops.transform.resize(value=cube_size, orient_type='GLOBAL')
    bpy.ops.object.transform_apply(scale=True)  # スケール適用（頂点座標に反映）
    # Get Destination Object
    des_obj = bpy.data.objects.get(destination_obj_name)
    if not des_obj:
        print(f"Object '{destination_obj_name}' not found.")
        return
    # Convert Extrude Index to Custom ID
    cube_vert = custom_id_to_index(
        obj_name=cube_name
    ,   custom_id_list=[cube_vert]
    ,   elem_type='VERT'
    )
    destination_vert = custom_id_to_index(
        obj_name=destination_obj_name
    ,   custom_id_list=[destination_vert]
    ,   elem_type='VERT'
    )
    # Get World coordinate (ワールド座標取得)
    des_vert = des_obj.data.vertices[destination_vert[0]]
    des_world_co = des_obj.matrix_world @ des_vert.co
    cube_vert_co = cube_obj.data.vertices[cube_vert[0]].co
    cube_world_co = cube_obj.matrix_world @ cube_vert_co
    # 相対移動量
    dx = des_world_co.x - cube_world_co.x
    dy = des_world_co.y - cube_world_co.y
    dz = des_world_co.z - cube_world_co.z
    # 編集モードに入って頂点移動
    bpy.context.view_layer.objects.active = cube_obj
    cube_obj.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(cube_obj.data)
    for v in bm.verts:
        v.co.x += dx
        v.co.y += dy
        v.co.z += dz
    bmesh.update_edit_mesh(cube_obj.data)

    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)


# ========================================================================
# = ▼ 面押し出し インデックス固定 円系
# ========================================================================
# --------------------
# 選択済み辺(loop_multi_select等)の隣接関係を辿り、頂点を周回順(隣接順)に並べ替える
# --------------------
# Input :
#   obj_name  : 対象オブジェクト名 (str)
#               呼び出し時点で EDIT モード かつ 対象の辺群が選択済みであること
#   loop_flag : True の場合、選択が「閉じた1周ループ」であることを要求する
#               (各頂点の次数が全て2でなければ異常とみなし例外を送出)
# Output:
#   選択されている辺だけを辿って得られる、頂点インデックスの周回順(隣接順)リスト (list[int])
#   ループが分岐/枝分かれしている、または1周に閉じていない等トポロジ異常時は RuntimeError
#
# 背景:
#   [v.index for v in mesh.vertices if v.select] は「頂点インデックス順」であり、
#   Alt+クリック相当のループ選択(bpy.ops.mesh.loop_multi_select)が返す「周回順」を
#   保証しない。この順序のまま面貼り(edge_face_add)に使うと、実際には隣接していない
#   頂点同士を結んでねじれた面を作ってしまい、メッシュが崩壊して見える原因になる。
#   そこで選択されている「辺」の頂点連結関係(bmeshの辺リンク)をたどり、
#   実際に隣接している順序で頂点を並べ直す。
def _order_loop_vertices_by_edge_adjacency(obj_name, loop_flag=True):
    obj = bpy.data.objects[obj_name]
    bm = bmesh.from_edit_mesh(obj.data)
    # 選択中の辺のみを対象にする(未選択の辺は周回順の判定に含めない)
    selected_edges = [e for e in bm.edges if e.select]
    if not selected_edges:
        raise RuntimeError(
            f"[_order_loop_vertices_by_edge_adjacency] "
            f"選択された辺が1本もありません(obj_name={obj_name})。"
            f" ループ選択の起点となる代表エッジの指定を確認してください。"
        )
    # 頂点Index -> 隣接する(選択済み辺で直結された)頂点Indexのリスト
    adjacency = {}
    for e in selected_edges:
        v1, v2 = e.verts
        adjacency.setdefault(v1.index, []).append(v2.index)
        adjacency.setdefault(v2.index, []).append(v1.index)
    # 次数が1(鎖の端点)/2(通常のループ構成点)以外の頂点があれば、
    # ループが分岐/枝分かれしており「1周選択」になっていないと判断する
    branch_verts = [vidx for vidx, nb in adjacency.items() if len(nb) not in (1, 2)]
    if branch_verts:
        raise RuntimeError(
            f"[_order_loop_vertices_by_edge_adjacency] "
            f"選択された辺群に分岐点が見つかりました (vertex index={branch_verts}, obj_name={obj_name})。"
            f" ループが1周のみを構成していない可能性があります。"
        )
    if loop_flag:
        # 閉じたループなら全頂点の次数が2になっているはず
        if any(len(nb) != 2 for nb in adjacency.values()):
            raise RuntimeError(
                f"[_order_loop_vertices_by_edge_adjacency] "
                f"loop_flag=True ですが選択結果が閉じた1周ループになっていません(obj_name={obj_name})。"
                f" 代表エッジ周辺のトポロジ、または面削除/ループカット後の形状を確認してください。"
            )
        start_vidx = next(iter(adjacency))
    else:
        # 開いた鎖の場合は端点(次数1)から辿り始める
        endpoints = [vidx for vidx, nb in adjacency.items() if len(nb) == 1]
        start_vidx = endpoints[0] if endpoints else next(iter(adjacency))
    # 辺の隣接関係を1つずつ辿り、頂点を周回順(隣接順)に並べる
    ordered_vertex_indices = [start_vidx]
    prev_vidx = None
    current_vidx = start_vidx
    while True:
        next_candidates = [n for n in adjacency[current_vidx] if n != prev_vidx]
        if not next_candidates:
            # 端点に到達(開いた鎖の終端)
            break
        next_vidx = next_candidates[0]
        if next_vidx == start_vidx:
            # 開始点まで1周して戻ってきた(閉じたループの終端)
            break
        ordered_vertex_indices.append(next_vidx)
        prev_vidx, current_vidx = current_vidx, next_vidx
        # 保険: 想定外のトポロジによる無限ループを防止
        if len(ordered_vertex_indices) > len(adjacency):
            raise RuntimeError(
                f"[_order_loop_vertices_by_edge_adjacency] "
                f"頂点の周回順序付けが収束しませんでした(obj_name={obj_name})。"
            )
    return ordered_vertex_indices

def fix_index_extrude_region_move_customid(
    obj_name="obj_name"         # Object Name
,   represent_edges=[0]         # Represent Edge Index List (代表エッジ、複数指定可)
,   resize_values=(1, 1, 1)     # Change Size Value
,   move_values=(0, 0, 0)       # Move Value
,   face_add_flag=True          # If True: Add Face
,   loop_flag=True              # loop enable
):
    # represent_edges は「1周(または1本の鎖)を構成する辺の customID リスト」
    # 要素数が1の場合のみ、従来通り loop_multi_select で自動的にループへ拡張する
    # （2個以上指定された場合は、自動ループ選択を使わず指定された辺をそのまま1周分の構成として扱う）
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Select Element
    element_select_customid(
        element_list=represent_edges
    ,   select_mode="EDGE"
    ,   object_name_list=[obj_name]
    )
    if (loop_flag and len(represent_edges) == 1):
        # エッジループ 選択 ループ選択(Alt+Click)
        # ※ 代表エッジが1本のみ指定された場合の従来互換動作
        # Blender 5.2 で mesh.loop_multi_select(ring=False) が
        # mesh.select_edge_loop_multi() に分離・改名された
        bpy.ops.mesh.select_edge_loop_multi()
    # 選択された辺の隣接関係(bmeshの辺リンク)を辿って、頂点を周回順(隣接順)に並べ替える
    # (mesh.vertices の単純なインデックス順では周回順にならず、後段の面貼りが崩れるため)
    selected_vertex_indices = _order_loop_vertices_by_edge_adjacency(
        obj_name=obj_name
    ,   loop_flag=loop_flag
    )
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Change index to custom ID
    selected_vertex_indices=index_to_custom_id(
        obj_name=obj_name
    ,   index_list=selected_vertex_indices
    ,   elem_type="VERT"
    )
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    tmp_l=[]
    for i in range(len(selected_vertex_indices)):
        # Select Element
        element_select_customid(
            element_list=[selected_vertex_indices[i]]
        ,   select_mode="VERT"
        ,   object_name_list=[obj_name]
        )
        # Create Face (面の作成 外/内側へ拡大(押し込み(押し出し)引き込み/差し込み))
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={}, 
            TRANSFORM_OT_translate={
            }
        )
        # 選択メッシュ カスタムID 0
        mdl_cm_lib.zero_selected_elements_customid(obj_name)
        # 重複IDを座標順で修正
        mdl_cm_lib.fix_duplicate_ids(obj_name)
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')
        # Get Mesh Data
        mesh = bpy.context.object.data
        # Get the index of the selected vertex
        tmp_l.append([v.index for v in mesh.vertices if v.select][0])
        # Change Mode
        bpy.ops.object.mode_set(mode='EDIT')
    # Change index to custom ID
    tmp_l=index_to_custom_id(
        obj_name=obj_name
    ,   index_list=tmp_l
    ,   elem_type="VERT"
    )
    # Select Element
    element_select_customid(
        element_list=tmp_l
    ,   select_mode="VERT"
    ,   object_name_list=[obj_name]
    )
    # Change Size
    bpy.ops.transform.resize(
        value=resize_values
    ,   orient_type='GLOBAL'
    )
    # Move Object/Element
    bpy.ops.transform.translate(
        value=move_values
    ,   orient_type='GLOBAL'
    )
    # Add Face
    if (face_add_flag):
        for i in range(1, len(tmp_l)):
            # Select Element
            element_select_customid(
                element_list=[tmp_l[i], selected_vertex_indices[i], tmp_l[i-1], selected_vertex_indices[i-1]]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # Add Face (面 追加・埋める・貼る) (F)
            edge_face_add_bmesh_with_zero_customid(obj_name)
            # 重複IDを座標順で修正
            fix_duplicate_ids(obj_name)
        if (loop_flag):
            # Connect First and Last Point (最初と最後部分をつなぐ)
            element_select_customid(
                element_list=[tmp_l[0], selected_vertex_indices[0], tmp_l[len(tmp_l)-1], selected_vertex_indices[len(tmp_l)-1]]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # Add Face (面 追加・埋める・貼る) (F)
            edge_face_add_bmesh_with_zero_customid(obj_name)
            # 重複IDを座標順で修正
            fix_duplicate_ids(obj_name)
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ 面に沿わせてオブジェクトを配置
# ========================================================================
def apply_tiles_to_face_multi(
    face_cid            = [0, 1]
,   base_obj_name       = "base_obj_name"
,   tiles_obj_name      = "tiles_obj_name"
,   tiles_anchor_name   = "tiles_anchor_name" + "_anchor"
):
    bpy.ops.object.mode_set(mode='OBJECT')

    base_obj = bpy.data.objects.get(base_obj_name)
    anchor   = bpy.data.objects.get(tiles_anchor_name)

    if base_obj is None:
        raise RuntimeError(f"{base_obj_name} not found")
    if anchor is None:
        raise RuntimeError(f"{tiles_anchor_name} not found")

    # ============================================================
    # ▼ bmesh
    # ============================================================
    bm = bmesh.new()
    bm.from_mesh(base_obj.data)

    fid_layer = bm.faces.layers.int.get("fid")
    if fid_layer is None:
        bm.free()
        raise RuntimeError("fid レイヤーが必要")

    faces = [f for f in bm.faces if f[fid_layer] in face_cid]

    if not faces:
        bm.free()
        raise RuntimeError("face not found")

    mw = base_obj.matrix_world

    # ============================================================
    # ▼ 法線（平均・ワールド空間）
    # ============================================================
    normal = mathutils.Vector((0, 0, 0))

    for f in faces:
        normal += mw.to_3x3() @ f.normal

    if normal.length == 0:
        bm.free()
        raise RuntimeError("normal calc failed")

    normal.normalize()

    # ============================================================
    # ▼ tangent（固定軸ベース ← ここが安定の鍵）
    # ============================================================
    # 基準軸（Zと平行ならXに逃がす）
    up = mathutils.Vector((0, 0, 1))

    if abs(normal.dot(up)) > 0.999:
        up = mathutils.Vector((1, 0, 0))

    tangent = up.cross(normal).normalized()

    # ============================================================
    # ▼ bitangent
    # ============================================================
    bitangent = normal.cross(tangent).normalized()

    # ============================================================
    # ▼ 回転行列
    # ============================================================
    rot_mat = mathutils.Matrix((
        tangent,
        bitangent,
        normal
    )).transposed()

    # ============================================================
    # ▼ 中心位置（面積重心）
    # ============================================================
    center = mathutils.Vector((0, 0, 0))
    area_sum = 0.0

    for f in faces:
        c = mw @ f.calc_center_median()
        a = f.calc_area()

        center += c * a
        area_sum += a

    if area_sum == 0:
        bm.free()
        raise RuntimeError("area calc failed")

    center /= area_sum

    # ============================================================
    # ▼ 適用（回転＋移動）
    # ============================================================
    anchor.matrix_world = (
        mathutils.Matrix.Translation(center) @
        rot_mat.to_4x4()
    )

    bm.free()

# ========================================================================
# = ▼ 面に沿わせてオブジェクトをカット
# ========================================================================
def cut_tiles_by_face_clean(
    face_cid=[0]
,   base_obj_name="base_obj_name"
,   tiles_obj_name="tiles_obj_name"
):
    bpy.ops.object.mode_set(mode='OBJECT')

    base_obj  = bpy.data.objects.get(base_obj_name)
    tiles_obj = bpy.data.objects.get(tiles_obj_name)

    if base_obj is None:
        raise RuntimeError(f"{base_obj_name} not found")
    if tiles_obj is None:
        raise RuntimeError(f"{tiles_obj_name} not found")

    # ============================================================
    # ▼ 面取得
    # ============================================================
    bm = bmesh.new()
    bm.from_mesh(base_obj.data)

    fid_layer = bm.faces.layers.int.get("fid")
    if fid_layer is None:
        bm.free()
        raise RuntimeError("fid レイヤーが必要")

    faces = [f for f in bm.faces if f[fid_layer] in face_cid]

    if not faces:
        bm.free()
        raise RuntimeError("face not found")

    mw = base_obj.matrix_world

    # ============================================================
    # ▼ 法線
    # ============================================================
    normal = mathutils.Vector((0, 0, 0))
    for f in faces:
        normal += mw.to_3x3() @ f.normal
    normal.normalize()

    # ============================================================
    # ▼ 外周エッジ抽出
    # ============================================================
    edge_count = {}

    for f in faces:
        for e in f.edges:
            key = tuple(sorted([v.index for v in e.verts]))
            edge_count[key] = edge_count.get(key, 0) + 1

    boundary_edges = []
    for f in faces:
        for e in f.edges:
            key = tuple(sorted([v.index for v in e.verts]))
            if edge_count[key] == 1:
                boundary_edges.append(e)

    # ============================================================
    # ▼ ループ生成
    # ============================================================
    loop = []

    e0 = boundary_edges[0]
    v_start = e0.verts[0]
    v_current = e0.verts[1]

    loop.append(mw @ v_start.co)
    loop.append(mw @ v_current.co)

    used = {e0}

    while len(loop) < len(boundary_edges):
        for e in boundary_edges:
            if e in used:
                continue

            if e.verts[0] == v_current:
                v_current = e.verts[1]
            elif e.verts[1] == v_current:
                v_current = e.verts[0]
            else:
                continue

            loop.append(mw @ v_current.co)
            used.add(e)
            break

    bm.free()

    # ============================================================
    # ▼ カッター生成（完全修正版）
    # ============================================================
    cutter_mesh = bpy.data.meshes.new("tile_cutter_mesh")
    cutter_obj  = bpy.data.objects.new("tile_cutter", cutter_mesh)
    bpy.context.collection.objects.link(cutter_obj)

    bm_cut = bmesh.new()

    # ----------------------------
    # ベース面
    # ----------------------------
    verts = [bm_cut.verts.new(v) for v in loop]
    face = bm_cut.faces.new(verts)

    # ----------------------------
    # 押し出し（1回だけ）
    # ----------------------------
    extrude = bmesh.ops.extrude_face_region(bm_cut, geom=[face])

    verts_ex = [e for e in extrude["geom"] if isinstance(e, bmesh.types.BMVert)]

    thickness = 1000.0  # 十分大きく

    bmesh.ops.translate(
        bm_cut,
        verts=verts_ex,
        vec=normal * thickness
    )

    # ----------------------------
    # 中央に配置（両側カバー）
    # ----------------------------
    bmesh.ops.translate(
        bm_cut,
        verts=bm_cut.verts,
        vec=-normal * (thickness * 0.5)
    )

    # ----------------------------
    # 法線修正（超重要）
    # ----------------------------
    bmesh.ops.recalc_face_normals(bm_cut, faces=bm_cut.faces)

    bm_cut.to_mesh(cutter_mesh)
    bm_cut.free()

    # ============================================================
    # ▼ Transform適用（超重要）
    # ============================================================
    bpy.context.view_layer.objects.active = tiles_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    bpy.context.view_layer.objects.active = cutter_obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    # ============================================================
    # ▼ Boolean（INTERSECT）
    # ============================================================
    bpy.context.view_layer.objects.active = tiles_obj
    tiles_obj.select_set(True)

    bool_mod = tiles_obj.modifiers.new(name="TileTrim", type='BOOLEAN')
    bool_mod.operation = 'INTERSECT'
    bool_mod.object = cutter_obj
    bool_mod.solver = 'EXACT'
    bool_mod.use_self = False
    bool_mod.use_hole_tolerant = True

    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    # ============================================================
    # ▼ カッター削除
    # ============================================================
    bpy.data.objects.remove(cutter_obj, do_unlink=True)


# ========================================================================
# = ▼ 面に沿わせてオブジェクトを貼り付け
# ========================================================================
def fit_tiles_to_face(
    face_cid            = [0, 1]
,   base_obj_name       = "base_obj_name"
,   tiles_obj_name      = "tiles_obj_name"
,   tiles_anchor_name   = "tiles_anchor_name" + "_anchor"
#   移動
,   move_local_x        = +0.00
,   move_local_y        = +0.00
,   move_local_z        = +0.00
#   回転
,   rotate_local_x      = +0.00
,   rotate_local_y      = +0.00
,   rotate_local_z      = +0.00
#   カットオプション
,   cut_option          = True
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    # ========================================================================
    # = ▼ 面に沿わせてオブジェクトを配置
    # ========================================================================
    apply_tiles_to_face_multi(
        face_cid            = face_cid
    ,   base_obj_name       = base_obj_name
    ,   tiles_obj_name      = tiles_obj_name
    ,   tiles_anchor_name   = tiles_anchor_name
    )
    # オブジェクト 回転
    mdl_cm_lib.object_rotate_func(
        object_list=[tiles_anchor_name]
    ,   transform_pivot_point='INDIVIDUAL_ORIGINS'
    ,   degrees_num=rotate_local_x
    ,   orient_axis="X"
    ,   orient_type="LOCAL"
    )
    mdl_cm_lib.object_rotate_func(
        object_list=[tiles_anchor_name]
    ,   transform_pivot_point='INDIVIDUAL_ORIGINS'
    ,   degrees_num=rotate_local_y
    ,   orient_axis="Y"
    ,   orient_type="LOCAL"
    )
    mdl_cm_lib.object_rotate_func(
        object_list=[tiles_anchor_name]
    ,   transform_pivot_point='INDIVIDUAL_ORIGINS'
    ,   degrees_num=rotate_local_z
    ,   orient_axis="Z"
    ,   orient_type="LOCAL"
    )
    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    active_object_select(object_name_list=[tiles_anchor_name])
    # オブジェクト 移動
    bpy.ops.transform.translate(
        value=(
            move_local_x
        ,   move_local_y
        ,   move_local_z
        )
    ,   orient_type='LOCAL'
    )
    # ========================================================================
    # = ▼ 面に沿わせてオブジェクトをカット
    # ========================================================================
    if (cut_option):
        cut_tiles_by_face_clean(
            face_cid=face_cid
        ,   base_obj_name=base_obj_name
        ,   tiles_obj_name=tiles_obj_name
        )
        # 重複IDを座標順で修正
        mdl_cm_lib.fix_duplicate_ids(tiles_obj_name)
    
    # Change Original Mode
    bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# 同じcustomIDの全頂点を取得
# ========================================================================
def get_all_vertices_by_vid(obj_name, target_vid):
    obj = bpy.data.objects[obj_name]

    bm = bmesh.new()
    bm.from_mesh(obj.data)

    vid_layer = bm.verts.layers.int.get("vid")
    if not vid_layer:
        bm.free()
        return []

    points = []

    for v in bm.verts:
        if v[vid_layer] == target_vid:
            world = obj.matrix_world @ v.co
            points.append((world.x, world.y, world.z))

    bm.free()
    return points

# ========================================================================
# 傾き（回転角）を求める（任意軸対応）
# ========================================================================
def compute_flatten_rotation_angle(points, target_axis='Z', rotate_axis='X'):
    """
    target_axis: 揃えたい軸 ('X','Y','Z')
    rotate_axis: 回転軸 ('X','Y','Z')
    """

    if len(points) < 2:
        return 0.0

    # 軸インデックス
    axis_map = {'X': 0, 'Y': 1, 'Z': 2}

    t = axis_map[target_axis]
    r = axis_map[rotate_axis]

    # 回転軸に応じて使う2軸を決定
    # X回転 → YZ
    # Y回転 → XZ
    # Z回転 → XY
    plane_axes = {
        0: (1, 2),
        1: (0, 2),
        2: (0, 1)
    }

    a1, a2 = plane_axes[r]

    # target_axisがa2になるように並び替え
    if t == a1:
        a1, a2 = a2, a1

    # 最小二乗で傾き計算
    sum_x = sum(p[a1] for p in points)
    sum_y = sum(p[a2] for p in points)
    sum_xx = sum(p[a1] * p[a1] for p in points)
    sum_xy = sum(p[a1] * p[a2] for p in points)

    n = len(points)

    denom = (n * sum_xx - sum_x * sum_x)
    if abs(denom) < 1e-8:
        return 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denom

    # 傾き → 角度
    angle_rad = math.atan(slope)

    return -math.degrees(angle_rad)


# ==================================================================
# = 3D点群に円をフィッティングし、その中心座標を求める
# ==================================================================
def fit_circle_center_3d(points_3d):
    """
    3次元空間上の点群(円周上、または円弧の一部)に対して、それらが乗っている
    平面を最小二乗フィットで求めたうえで、その平面内で円フィッティング(Kasa法)
    を行い、円の中心のワールド/ローカル座標(点群と同じ座標系)を返す。

    点群が完全な円周を成していなくても(円弧の一部だけでも)、3点以上あれば
    その円弧が乗っていた円の中心を復元できる。これにより、メッシュの一部が
    削除されて実際には存在しない「元の円の中心」のような点でも、
    残っている頂点群から逆算して求めることができる。

    ---- Input ----
    points_3d : list[Vector] : 円周(の一部)上にあると仮定する3点以上の座標

    ---- Output ----
    Vector : フィッティングした円の中心座標 (points_3d と同じ座標系)
    """
    pts = np.array([[p.x, p.y, p.z] for p in points_3d])
    centroid = pts.mean(axis=0)
    centered = pts - centroid
    # 点群が乗っている平面を特異値分解(SVD)で求める
    # (第1・第2特異ベクトルが平面内の基底、第3特異ベクトルが法線に相当する)
    _, _, vt = np.linalg.svd(centered)
    basis_u = vt[0]
    basis_v = vt[1]
    # 各点を平面内の2D座標へ投影
    uv = centered @ np.vstack([basis_u, basis_v]).T
    # 円フィッティング(Kasa法): u^2+v^2 = 2*a*u + 2*b*v + c の形の線形最小二乗で解く
    # (a, b) が2D平面内での円の中心、c は r^2 - a^2 - b^2 に相当する定数項
    coeff_matrix = np.column_stack([2*uv[:, 0], 2*uv[:, 1], np.ones(len(uv))])
    rhs = uv[:, 0]**2 + uv[:, 1]**2
    solution, *_ = np.linalg.lstsq(coeff_matrix, rhs, rcond=None)
    center_a, center_b, _ = solution
    # 2D中心座標を3D座標へ戻す
    center_3d = centroid + center_a*basis_u + center_b*basis_v
    return Vector((float(center_3d[0]), float(center_3d[1]), float(center_3d[2])))


# ==================================================================
# = パイプ状オブジェクトを指定軸・指定角度で滑らかに曲げる (vertex_warp 使用)
# ==================================================================
def bend_object_vertex_warp(
    obj_name
,   angle_deg       = 90     # 曲げ角度 (度単位) 例：90 ※符号を反転させると曲げ方向も反転する
,   bend_axis       = "Z"    # 曲げ後にパイプが向く方向のグローバル軸 "X" / "Y" / "Z" のいずれか
,   loopcut_num     = 7      # 曲げを滑らかにするためのループカット追加本数
,   bend_zone_ratio = 1.0    # 曲げが実際に及ぶ範囲の割合 (0<ratio<=1)。1.0=全体が滑らかに曲がる(デフォルト)。
                                # 値を小さくするほどオブジェクト中央の狭い範囲だけが曲がり、
                                # 前後は真っ直ぐなまま直角に近い鋭い曲げになる
,   pre_twist_deg   = 0      # 曲げる前にパイプの長さ方向(Y軸)を軸としてオブジェクトを
                                # あらかじめ回転(ひねる)しておく角度(度単位)。
                                # 断面の非対称な形状(雨樋の側溝の開口方向など)を
                                # 曲げ平面に対して正しい向きに合わせたい場合に使用する
,   companion_anchor_names = []   # 曲げに追従させたいアンカー(Empty)オブジェクト名のリスト。
                                    # 指定すると、各アンカーに最も近いメッシュ表面上の点を
                                    # BVHTree で求め、その点が属する面の頂点群を
                                    # 重心座標(重み)付きで追跡し、曲げ後の位置へ
                                    # アンカーも一緒に移動させる(メッシュの形状・頂点数に
                                    # 依存しない汎用的な方式)
):
    """
    直線状のパイプ形状オブジェクト(Y軸方向に伸びている前提)を指定角度だけ曲げる。
    (bpy.ops.transform.vertex_warp を使用した「曲線的な曲げ」表現。
        bend_zone_ratio を 1.0 に近づけるほど全体が滑らかに曲がり、
        0 に近づけるほど中央の狭い範囲だけが曲がって直角に近い鋭い曲げになる)

    ---- 実装メモ ----
    ・vertex_warp は viewmat の行(ヒンジ軸/カーブ軸/パイプ長さ軸)を
        単純にワールド軸へ入れ替えるだけでは正しく機能しない(実機検証で確認済み)。
        そのため曲げ処理そのものは常に「ヒンジ=Z, カーブ=X, パイプ長さ=Y」の
        検証済み配置のみで行い、bend_axis が Z 以外の場合は
        曲げ終わったオブジェクト全体をその場で回転させることで、
        見た目上 X 軸 / Y 軸方向に曲げたのと同じ結果を作る。
        bend_axis="X" → 曲げ後に Y軸回りに +90度 回転
        bend_axis="Y" → 曲げ後に X軸回りに -90度 回転
        (この回転により、曲げていない側のまっすぐな区間の向きも
        一緒に回転する点に注意。例えば bend_axis="Y" の場合、
        元々Y軸方向を向いていたまっすぐな区間は -Z軸方向を向くようになる)
    ・曲げ処理中、実際に「曲がらず固定される断面方向」は bend_axis="Z"(既定)の場合は
        X軸、bend_axis="X"の場合はZ軸、bend_axis="Y"の場合もZ軸になる。
        断面が非対称なオブジェクト(雨樋の側溝の開口方向がある等)では、
        この「固定される軸」と実際の開口方向が一致していないと、
        意図と違う平面で曲がって見える(横に曲げたいのに縦にブリッジ状に曲がる 等)。
        その場合は pre_twist_deg で断面をあらかじめ回転させ、
        開口方向を「固定される軸」に合わせること。
    ・ループカットは、パイプ長さ方向(Y軸)にほぼ平行な全エッジを bmesh で検出し
        一括で分割する(特定のカスタムIDエッジ1本からの loopcut_slide ではない)。
        これにより、後から join したパーツ(溶接されていない別ジオメトリ)が
        混在していても、それぞれのパーツが個別に曲げに追従できる。
    ・companion_anchor_names を指定した場合、各アンカーとパイプ長さ方向(Y)座標が
        ほぼ一致する頂点群(=元の円形断面の残存リング)を集めておき、曲げ処理
        全体を通してこの頂点群を追跡する。曲げ後は、fit_circle_center_3d で
        この頂点群に円をフィッティングし直し、その中心座標へアンカーを移動する。
        アンカーは元々 get_face_point_customid で「円形断面の頂点群の中心
        (=円の中心)」に配置されているが、この中心はメッシュ表面上には無い
        (パイプの空洞の中心)。そのため「メッシュ表面上の最も近い点」を探す
        方式(BVHTree等)では原理的に再現できず、側溝の壁面など別の場所に
        引き寄せられてしまう。円形断面が側溝の開口などで一部失われていても、
        残っている円弧状の頂点群さえあれば円の中心は数学的に復元できるため、
        面の有無や頂点数、円周の分割数によらず汎用的に機能する。

    ---- 前提条件 ----
    ・obj_name はあらかじめ Y軸方向に伸びた直線状のパイプ形状であること

    ---- Input ----
    obj_name                : str       : 曲げ対象オブジェクト名
    angle_deg                : float     : 曲げ角度 (度単位、符号で曲げ方向を反転可能)
    bend_axis                : str       : 曲げ後にパイプが向く方向のグローバル軸 ("X" / "Y" / "Z")
    loopcut_num              : int       : 曲げを滑らかにするためのループカット追加本数
    bend_zone_ratio          : float     : 曲げが実際に及ぶ範囲の割合 (0<ratio<=1、小さいほど鋭い曲げ)
    pre_twist_deg            : float     : 曲げる前にパイプ長さ方向(Y軸)回りにひねる角度 (度単位)
    companion_anchor_names   : list[str] : 曲げに追従させたいアンカー(Empty)オブジェクト名のリスト

    ---- Output ----
    なし (obj_name のメッシュ形状と companion_anchor_names の各アンカーの位置を直接変更する、戻り値なし)
    """
    if not (0.0 < bend_zone_ratio <= 1.0):
        raise ValueError(f"bend_zone_ratio は 0 より大きく 1.0 以下で指定してください: {bend_zone_ratio}")
    if bend_axis not in ("X", "Y", "Z"):
        raise ValueError(f"bend_axis は 'X'/'Y'/'Z' のいずれかを指定してください: {bend_axis}")

    bend_obj = bpy.data.objects[obj_name]

    # 曲げ処理そのものは常にヒンジ=Z, カーブ=X, パイプ長さ=Y の検証済み配置で行う
    hinge_vec = Vector((0,0,1))  # 曲げのヒンジ(回転軸)方向ベクトル
    curve_vec = Vector((1,0,0))  # 曲げでパイプが向きを変えていく方向ベクトル
    depth_vec = Vector((0,1,0))  # 曲げ前のパイプの長さ方向ベクトル

    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')

    if pre_twist_deg != 0:
        # 断面をパイプ長さ方向(Y軸)回りに事前にひねっておく
        bpy.ops.object.select_all(action='DESELECT')
        bend_obj.select_set(True)
        bpy.context.view_layer.objects.active = bend_obj
        bpy.ops.transform.rotate(value=math.radians(pre_twist_deg), orient_axis='Y', orient_type='GLOBAL')
        bpy.ops.object.transform_apply(rotation=True)

    # ==================================================================
    # companion_anchor_names で指定されたアンカーそれぞれについて、
    # 現時点(曲げ開始前、まだオブジェクト移動前)でのローカル座標を記録しておく
    #   → オブジェクトレベルの平行移動(この後の bend_radius 分の移動)は
    #     頂点のローカル座標(v.co)には影響しないため、ここで求めたローカル座標は
    #     ループカット分割後もそのまま比較に使える
    #   → 実際に「どの頂点群を追跡するか」は、ループカットで分割された後の
    #     頂点から選ぶ(分割前は頂点の間隔が広く、Y座標の差も大きいままなので、
    #     曲げ後の中心座標の近似誤差が大きくなるため)
    # ==================================================================
    anchor_world_before = {}
    anchor_local_before  = {}
    if companion_anchor_names:
        bpy.context.view_layer.update()
        for anchor_name in companion_anchor_names:
            anchor_obj = bpy.data.objects.get(anchor_name)
            if anchor_obj is None:
                continue
            world_pos = anchor_obj.matrix_world.translation.copy()
            anchor_world_before[anchor_name] = world_pos
            anchor_local_before[anchor_name] = bend_obj.matrix_world.inverted() @ world_pos

    # ==================================================================
    # オブジェクトのバウンディングボックスから、パイプ長さ方向の座標範囲(min/max)を算出
    #   → vertex_warp の min/max 引数に使用する
    #   → length 等の寸法パラメータが変わっても、常にオブジェクト全体を覆う範囲を自動算出できる
    #   → bend_zone_ratio < 1.0 の場合は、範囲を中央に向かって狭めることで
    #     曲げ範囲外(前後の区間)を直線のまま残し、鋭い曲げを表現する
    #     (vertex_warp は min/max の範囲外の頂点を「回転のみ・曲げなし」で
    #      角度0 または warp_angle に固定するため、狭めるだけで前後が直線化する)
    # ==================================================================
    world_coords = [bend_obj.matrix_world @ Vector(corner) for corner in bend_obj.bound_box]
    depth_values = [co.y for co in world_coords]
    full_range_min = min(depth_values)
    full_range_max = max(depth_values)
    range_center   = (full_range_min + full_range_max) / 2.0
    half_zone_size = (full_range_max - full_range_min) * bend_zone_ratio / 2.0
    bend_range_min = range_center - half_zone_size
    bend_range_max = range_center + half_zone_size
    # 端部まで確実に曲げが行き渡るよう、範囲の5%分だけ余白(マージン)を追加
    margin = (bend_range_max - bend_range_min) * 0.05
    bend_range_min -= margin
    bend_range_max += margin

    # ==================================================================
    # 曲げ半径(bend_radius)を算出
    #   vertex_warp は「ヒンジ軸方向の距離(=center からのオフセット)」を
    #   曲げの半径として扱うため、この半径を固定値(例:1)にしてしまうと
    #   オブジェクトの長さに関係なく曲げ後のサイズが半径依存で決まってしまい、
    #   小さいオブジェクトほど曲げた際に不自然に伸びて見える原因になる。
    #   弧長 = 半径 × 角度(ラジアン) の関係を保つように半径を逆算することで、
    #   曲げ前後でオブジェクトの全体サイズが概ね維持されるようにする。
    # ==================================================================
    warp_angle_rad = math.radians(angle_deg)
    if warp_angle_rad == 0:
        return  # 曲げ角度が 0 度の場合は変形不要のため何もしない
    bend_radius = (bend_range_max - bend_range_min) / abs(warp_angle_rad)

    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    # オブジェクト移動 (ヒンジ軸方向に bend_radius だけ移動し、warpのcenter(0,0,0)との位置関係を合わせる)
    bpy.ops.transform.translate(
        value=(
            hinge_vec.x * bend_radius
        ,   hinge_vec.y * bend_radius
        ,   hinge_vec.z * bend_radius
        )
    ,   orient_type='GLOBAL'
    )
    # Mode切り替え
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='EDGE')
    # ==================================================================
    # パイプ長さ方向(ローカルY軸)にほぼ平行な全エッジを検出し、bmeshで一括分割する
    #   → 特定のカスタムIDエッジ1本を起点にした loopcut_slide だと、
    #     join後に非連結(未溶接)な別ジオメトリにはループが伝播せず、
    #     そのパーツだけ分割されずに直線のまま曲げに追従しない問題が起きる。
    #   → 全エッジを直接検出して分割することで、joinされた各パーツが
    #     それぞれ独立して曲げに追従できるようにする。
    # ==================================================================
    bm = bmesh.from_edit_mesh(bend_obj.data)
    bm.edges.ensure_lookup_table()
    # エッジの向き(ローカル座標系)をワールド座標系に変換してから depth_vec と比較する
    # (object_rotate_func 等はオブジェクトの回転を matrix_world 側に持たせるだけで
    #  メッシュのローカル座標には焼き込まない(transform_apply しない)ため、
    #  ローカル座標のまま比較すると回転済みオブジェクトで判定がずれてしまう)
    world_rotation_matrix = bend_obj.matrix_world.to_3x3()
    length_edges = []
    for e in bm.edges:
        edge_vector = e.verts[1].co - e.verts[0].co
        if edge_vector.length < 1e-9:
            continue
        edge_direction_world = (world_rotation_matrix @ edge_vector).normalized()
        if abs(edge_direction_world.dot(depth_vec)) > 0.9:
            length_edges.append(e)
    bmesh.ops.subdivide_edges(
        bm
    ,   edges = length_edges
    ,   cuts  = loopcut_num
    )
    bmesh.update_edit_mesh(bend_obj.data)

    # ==================================================================
    # companion_anchor_names で指定されたアンカーそれぞれについて、
    # アンカーとパイプ長さ方向(Y)座標がほぼ一致する頂点群(=元の円形断面の
    # 残存リング)を集め、そのインデックスを記録しておく
    #   → アンカーは元々 get_face_point_customid で「切り取られる前の円形断面の
    #     頂点群の中心(=円の中心)」に配置されている。この中心はメッシュの
    #     表面上には無い(空洞の中心)ため、表面上の最近傍点を探す方式では
    #     原理的に再現できず、代わりに側溝の壁面などメッシュ表面上の
    #     別の点に引き寄せられてしまう。
    #     そこで、アンカーと同じY座標(パイプ長さ方向の同じ位置)にある頂点群
    #     (側溝の開口で一部が失われていても、残っている円弧状の頂点群)を集め、
    #     曲げ後にその頂点群へ円フィッティング(_fit_circle_center_3d)を
    #     適用することで、実在しない「円の中心」を毎回再構築して追跡する。
    # ==================================================================
    tracked_ring_indices = {}
    if companion_anchor_names:
        bm.verts.ensure_lookup_table()
        for anchor_name, local_pos in anchor_local_before.items():
            ring_indices = [v.index for v in bm.verts if abs(v.co.y - local_pos.y) < 1e-4]
            if len(ring_indices) < 3:
                # 同じY座標の頂点が3個未満(円フィット不可)の場合は、
                # 念のため最も近い頂点だけでも追跡できるようにフォールバックする
                nearest = min(bm.verts, key=lambda v: (v.co - local_pos).length_squared)
                ring_indices = [nearest.index]
            tracked_ring_indices[anchor_name] = ring_indices

    # 選択メッシュ カスタムID 0 (分割によって増えた要素のIDをリセット)
    bpy.ops.mesh.select_all(action='SELECT')
    mdl_cm_lib.zero_selected_elements_customid(obj_name)
    # 重複IDを座標順で修正
    mdl_cm_lib.fix_duplicate_ids(obj_name)
    # 要素選択
    mdl_cm_lib.element_select(
        element_list=["all"]
    ,   select_mode="FACE"
    ,   object_name_list=[obj_name]
    )
    # オブジェクト 曲げ
    bpy.ops.transform.vertex_warp(
        warp_angle=warp_angle_rad
    ,   min=bend_range_min
    ,   max=bend_range_max
    ,   viewmat=(
            (hinge_vec.x, hinge_vec.y, hinge_vec.z, 0)
        ,   (curve_vec.x, curve_vec.y, curve_vec.z, 0)
        ,   (depth_vec.x, depth_vec.y, depth_vec.z, 0)
        ,   (0, 0, 0, 1)
            )
    ,   center=(0, 0, 0)
    )

    # companion_anchor_names の追跡対象頂点の、曲げ直後(まだEDITモード中)のワールド座標を取得する
    # (vertex_warp は bpy.ops 呼び出しのため、直前に保持していた bmesh 参照は無効になるので再取得する)
    # ここで「ワールド座標」に変換しておくのがポイント:
    #   この後 transform_apply(rotation=True) が呼ばれるとメッシュのローカル座標系が
    #   変わってしまう(回転がローカル座標へ焼き込まれる)ため、ローカル座標のまま保持すると
    #   矛盾したフレームで matrix_world を掛けることになり位置がずれる。
    #   ワールド座標に変換しておけば、この時点での bend_obj.matrix_world (M_checkpoint) と
    #   最終的な bend_obj.matrix_world (M_final) の相対変換を後から掛けるだけで、
    #   以降の translate / 回転+apply がどんな処理でも正しく追従できる。
    checkpoint_world_pos = {}
    matrix_checkpoint = bend_obj.matrix_world.copy()
    if companion_anchor_names:
        bm = bmesh.from_edit_mesh(bend_obj.data)
        bm.verts.ensure_lookup_table()
        for anchor_name, ring_indices in tracked_ring_indices.items():
            ring_coords = [bm.verts[i].co for i in ring_indices]
            if len(ring_coords) >= 3:
                # 曲げによって湾曲した後のリング頂点群に円フィッティングし直し、
                # (実在しない)円の中心の新しい位置を再構築する
                local_co = mdl_cm_lib.fit_circle_center_3d(ring_coords)
            else:
                local_co = ring_coords[0]
            checkpoint_world_pos[anchor_name] = matrix_checkpoint @ local_co

    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    # オブジェクト移動 (最初の移動を打ち消す)
    bpy.ops.transform.translate(
        value=(
            -hinge_vec.x * bend_radius
        ,   -hinge_vec.y * bend_radius
        ,   -hinge_vec.z * bend_radius
        )
    ,   orient_type='GLOBAL'
    )

    # companion_anchor_names のワールド座標を、ここまでの移動(translate)分だけ進めておく
    # (この後の transform_apply でメッシュのローカル座標系が変わってしまう前に、
    #  現時点までの相対変換を確定させて反映しておく必要があるため)
    if companion_anchor_names:
        bpy.context.view_layer.update()
        matrix_now = bend_obj.matrix_world.copy()
        relative_transform = matrix_now @ matrix_checkpoint.inverted()
        for anchor_name in list(checkpoint_world_pos.keys()):
            checkpoint_world_pos[anchor_name] = relative_transform @ checkpoint_world_pos[anchor_name]
        matrix_checkpoint = matrix_now

    # ==================================================================
    # bend_axis が Z 以外の場合、曲げ終わったオブジェクト全体を回転させて
    # 見た目上その軸方向に曲げたのと同じ結果にする
    #   (曲げ処理自体は常に「Z方向へ曲がる」形で行っているため、
    #    その結果を丸ごと回転させるだけで X/Y 方向の曲げを再現できる)
    # ==================================================================
    bpy.ops.object.mode_set(mode='OBJECT')
    if bend_axis == "X":
        bpy.ops.transform.rotate(value=math.radians(90), orient_axis='Y', orient_type='GLOBAL')
        # transform_apply で回転がローカル座標へ焼き込まれ matrix_world の回転成分が
        # 失われる前に、現時点の matrix_world との相対変換を確定させて反映しておく
        if companion_anchor_names:
            matrix_now = bend_obj.matrix_world.copy()
            relative_transform = matrix_now @ matrix_checkpoint.inverted()
            for anchor_name in list(checkpoint_world_pos.keys()):
                checkpoint_world_pos[anchor_name] = relative_transform @ checkpoint_world_pos[anchor_name]
            matrix_checkpoint = matrix_now
        bpy.ops.object.transform_apply(rotation=True)
    elif bend_axis == "Y":
        bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='X', orient_type='GLOBAL')
        if companion_anchor_names:
            matrix_now = bend_obj.matrix_world.copy()
            relative_transform = matrix_now @ matrix_checkpoint.inverted()
            for anchor_name in list(checkpoint_world_pos.keys()):
                checkpoint_world_pos[anchor_name] = relative_transform @ checkpoint_world_pos[anchor_name]
            matrix_checkpoint = matrix_now
        bpy.ops.object.transform_apply(rotation=True)

    # ==================================================================
    # companion_anchor_names の各アンカーを、最終的なワールド座標へ移動する
    # ==================================================================
    if companion_anchor_names:
        for anchor_name, final_world_pos in checkpoint_world_pos.items():
            anchor_obj = bpy.data.objects.get(anchor_name)
            if anchor_obj is None:
                continue
            offset = final_world_pos - anchor_world_before[anchor_name]
            bpy.ops.object.select_all(action='DESELECT')
            anchor_obj.select_set(True)
            bpy.context.view_layer.objects.active = anchor_obj
            bpy.ops.transform.translate(
                value=(offset.x, offset.y, offset.z)
            ,   orient_type='GLOBAL'
            )
        # アクティブオブジェクトを曲げ対象オブジェクトへ戻す
        bpy.ops.object.select_all(action='DESELECT')
        bend_obj.select_set(True)
        bpy.context.view_layer.objects.active = bend_obj