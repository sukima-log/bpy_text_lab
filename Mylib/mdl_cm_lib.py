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
            bpy.ops.mesh.loop_multi_select(ring=False)
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
        bpy.ops.mesh.loop_multi_select(ring=False)
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
    # Parent-Child 親子付け（Emptyを親とする）
    active_object_select(object_name_list=[obj_name])
    bpy.context.object.parent = empty
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
# ========================================================================
def add_objects_to_existing_empty(empty_name, obj_name_list):
    target_empty = bpy.data.objects.get(empty_name)
    if not target_empty:
        return

    # Switch to OBJECT mode
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj_name in obj_name_list:
        obj = bpy.data.objects.get(obj_name)
        if not obj:
            continue

        # Clear previous parent if exists
        if obj.parent:
            prev_parent = obj.parent
            obj.parent = None
            # Delete Empty if it has no children left
            if prev_parent.type == 'EMPTY' and len(prev_parent.children) == 0:
                bpy.data.objects.remove(prev_parent)

        # Select the object to be parented
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)

        # Activate the target Empty as parent
        target_empty.select_set(True)
        bpy.context.view_layer.objects.active = target_empty

        # Set parent while keeping transforms
        bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
    

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
    カスタムIDから mesh 上のインデックスを取得する（正しい実装版）
    """
    # Save Current Mode
    current_mode = bpy.context.object.mode
    bpy.ops.object.mode_set(mode='OBJECT')

    obj = bpy.data.objects.get(obj_name)
    if obj is None or obj.type != 'MESH':
        raise ValueError(f"オブジェクト '{obj_name}' が見つからないかメッシュではありません")

    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)

    # 要素タイプに応じた取得
    if elem_type == 'VERT':
        layer = bm.verts.layers.int.get("vid")
        elements = bm.verts
    elif elem_type == 'EDGE':
        layer = bm.edges.layers.int.get("eid")
        elements = bm.edges
    elif elem_type == 'FACE':
        layer = bm.faces.layers.int.get("fid")
        elements = bm.faces
    else:
        bm.free()
        raise ValueError("elem_type は 'VERT', 'EDGE', 'FACE' のいずれかにしてください")

    if layer is None:
        bm.free()
        raise ValueError(f"オブジェクトに '{elem_type.lower()}id' レイヤーが存在しません")

    indices = []
    for target_id in custom_id_list:
        index_found = -1
        for ele in elements:
            if ele[layer] == target_id:
                index_found = ele.index   # ★重要★ bmesh の本来の index を返す
                break
        indices.append(index_found)

    bm.to_mesh(mesh)  # 変更がある場合は更新
    bm.free()

    bpy.ops.object.mode_set(mode=current_mode)
    
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
            bpy.ops.mesh.loop_multi_select(ring=False)
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
    if not obj or obj.type != 'MESH':
        print("メッシュオブジェクトが選択されていません。")
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
def fix_index_extrude_region_move_customid(
    obj_name="obj_name"         # Object Name
,   represent_edge=0            # Represent Edge Index (代表エッジ)
,   resize_values=(1, 1, 1)     # Change Size Value
,   move_values=(0, 0, 0)       # Move Value
,   face_add_flag=True          # If True: Add Face
,   loop_flag=True              # loop enable
):
    # Save Current Mode
    current_mode = bpy.context.object.mode
    # Change Mode
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='VERT')
    # Select Element
    element_select_customid(
        element_list=[represent_edge]
    ,   select_mode="EDGE"
    ,   object_name_list=[obj_name]
    )
    if (loop_flag):
        # エッジループ 選択 ループ選択(Alt+Click)
        bpy.ops.mesh.loop_multi_select(ring=False)
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.mode_set(mode='OBJECT')
    # Get Mesh Data
    mesh = bpy.context.object.data
    # Get the index of the selected vertex
    selected_vertex_indices = [v.index for v in mesh.vertices if v.select]
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
):
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
    cut_tiles_by_face_clean(
        face_cid=face_cid
    ,   base_obj_name=base_obj_name
    ,   tiles_obj_name=tiles_obj_name
    )
    # 重複IDを座標順で修正
    mdl_cm_lib.fix_duplicate_ids(tiles_obj_name)

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