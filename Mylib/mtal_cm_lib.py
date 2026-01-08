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

# ==================================================================
# ▼ 新規マテリアル追加
# ==================================================================
def add_new_material(
    material_name="Base_Material_Name"
):
    # Create New Material
    new_material = bpy.data.materials.new(name="Material.001")
    # Set Use Node
    new_material.use_nodes = True
    # Change Material Name
    new_material.name = material_name
    # Assign a new material to an Object
    obj = bpy.context.object
    # Add New Material to an Object
    obj.data.materials.append(new_material)
    # Activate Material Slot
    for i, mat in enumerate(obj.material_slots):
        if mat.material.name == material_name:
            obj.active_material_index = i
            break
    # Assign
    bpy.ops.object.material_slot_assign()


# ==================================================================
# ▼ 既存マテリアル割り当て
# ==================================================================
def allocate_material(
    material_name="Base_Material_Name"
):
    # Get Material
    material = bpy.data.materials.get(material_name)
    # Set Use Node
    material.use_nodes = True
    if material is None:
        print(f"Material '{material_name}' not found.")
    else:
        # If not Exist Material Slot: Add New Material
        bpy.context.active_object.data.materials.append(material)
    # Activate Material Slot
    for i, mat in enumerate(bpy.context.active_object.material_slots):
        if mat.material.name == material_name:
            bpy.context.active_object.active_material_index = i
            break
    # Assign
    bpy.ops.object.material_slot_assign()



# ==================================================================
# ▼ テクスチャ追加
# ==================================================================
def add_new_texture(
    material_name="Material"                    # Material Name
,   texture_name="ShaderNodeTexNoise"           # Addd Node Type
,   texture_node_name="sample_texture_name"     # Node Name
,   node_location=(-400, 300)                   # Node Position
,   settings=None                               # Option
):
    # Get Material
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create Material
        material = bpy.data.materials.new(name=material_name)
    # Change Use Node
    material.use_nodes = True
    nodes = material.node_tree.nodes
    # Add Node
    texture_node = nodes.new(type=texture_name)
    # Set Node Name
    texture_node.name = texture_node_name
    # Set Label Name
    texture_node.label = f"{texture_node.name}"
    # Set Node Position
    texture_node.location = node_location
    # Option
    if settings:
        for setting in settings:
            if hasattr(texture_node, setting['name']):
                setattr(texture_node, setting['name'], setting['value'])
    return texture_node


# ==================================================================
# ▼ ノード間の要素リンク
# ==================================================================
def node_link_func(
    material_name="Material"
,   texture_node_name_out="ShaderNodeTexNoise"
,   texture_node_name_in="ShaderNodeTexNoise"
,   output_link="Normal"
,   input_link="Normal"
):
    # Get Material
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create Material
        material = bpy.data.materials.new(name=material_name)
    # Change Use Node
    material.use_nodes = True
    nodes = material.node_tree.nodes
    # Get Texture Node
    from_node = nodes.get(texture_node_name_out)
    if from_node is None:
        print("[MyError] テクスチャが見つかりません")
    # Get Texture Node
    to_node = nodes.get(texture_node_name_in)
    if to_node is None:
        print("[MyError] テクスチャが見つかりません")
    # Connect Texture Node Port
    material.node_tree.links.new(from_node.outputs[output_link], to_node.inputs[input_link])


# ==================================================================
# ▼ ノードエディタを探す
# ==================================================================
def ensure_node_editor():
    # Search Node Editor
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                return window, area
    return None, None

# ==================================================================
# ▼ ノードを選択状態にする
# ==================================================================
def select_node(material_name="Material", node_name="Node"):
    # Ensure Node Editor
    window, node_editor_area = ensure_node_editor()
    if node_editor_area is None:
        # Node Editorがなくてもデータ上で選択
        material = bpy.data.materials.get(material_name)
        if material is None:
            print(f"Material '{material_name}' not found.")
            return
        node_tree = material.node_tree
        node = node_tree.nodes.get(node_name)
        if node is None:
            print(f"Node '{node_name}' not found.")
            return
        for n in node_tree.nodes:
            n.select = False
        node.select = True
        node_tree.nodes.active = node
        return
    # Get Node Editor Space
    space = node_editor_area.spaces.active
    if space.type != 'NODE_EDITOR':
        print("The area is not a NODE_EDITOR.")
        return
    # Get Material
    material = bpy.data.materials.get(material_name)
    if material is None:
        print(f"Material '{material_name}' not found.")
        return
    # Get Node Tree
    node_tree = material.node_tree
    # Get Node
    node = node_tree.nodes.get(node_name)
    if node is None:
        print(f"Node '{node_name}' not found.")
        return
    # Set Node Tree in Node Editor
    space.node_tree = node_tree
    # Select Node
    for n in node_tree.nodes:
        n.select = False  # Deselect Other Node
    node.select = True
    # Activate
    node_tree.nodes.active = node


# ==================================================================
# ▼ ノードの値を変更する
# ==================================================================
def node_value_change(
    material_name: str,
    node_name: str,
    element_name,
    set_value,
):
    """
    element_name に指定可能なもの

    ▼ inputs（安全）
    - int : 入力ソケット index（最優先）
    - str : 入力ソケット名（"Scale", "Strength" 等）

    ▼ プロパティ
    - "operation"      (ShaderNodeMath / VectorMath)
    - "blend_type"     (ShaderNodeMixRGB)
    - "interpolation"  (ShaderNodeValToRGB)
    - "color_space"    (ShaderNodeTexImage)
    """

    # --------------------------------------------------
    # Material / Node
    # --------------------------------------------------
    material = bpy.data.materials.get(material_name)
    if material is None:
        print(f"[node_value_change] Material not found: {material_name}")
        return

    node = material.node_tree.nodes.get(node_name)
    if node is None:
        print(f"[node_value_change] Node not found: {node_name}")
        return

    # ==================================================
    # ① element_name が int → 入力ソケット index
    # ==================================================
    if isinstance(element_name, int):
        try:
            node.inputs[element_name].default_value = set_value
        except IndexError:
            print(
                f"[node_value_change] Input index {element_name} "
                f"not found in node '{node_name}'"
            )
        return

    # ==================================================
    # ② element_name が str
    # ==================================================
    if not isinstance(element_name, str):
        print(
            f"[node_value_change] element_name must be int or str, "
            f"got {type(element_name)}"
        )
        return

    elem = element_name.lower()

    # --------------------------------------------------
    # Image Texture : Color Space
    # --------------------------------------------------
    if node.type == 'TEX_IMAGE' and elem in {"color_space", "color space"}:
        if node.image:
            node.image.colorspace_settings.name = set_value
        else:
            print(f"[node_value_change] Image not assigned: {node_name}")
        return

    # --------------------------------------------------
    # Math / Vector Math : operation
    # --------------------------------------------------
    if elem == "operation" and hasattr(node, "operation"):
        node.operation = set_value
        return

    # --------------------------------------------------
    # MixRGB : blend_type
    # --------------------------------------------------
    if elem == "blend_type" and hasattr(node, "blend_type"):
        node.blend_type = set_value
        return

    # --------------------------------------------------
    # ColorRamp : interpolation
    # --------------------------------------------------
    if node.type == 'VALTORGB' and elem == "interpolation":
        node.color_ramp.interpolation = set_value
        return

    # --------------------------------------------------
    # Input socket by name
    # --------------------------------------------------
    if element_name in node.inputs:
        node.inputs[element_name].default_value = set_value
        return

    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------
    print(
        f"[node_value_change] Unsupported element '{element_name}' "
        f"for node '{node_name}' ({node.type})"
    )


# ==================================================================
# ▼ HEX -> RGB 変換
# ==================================================================
def srgb_to_linear(c):
    """sRGB値(0.0〜1.0)をLinear値に変換"""
    if c <= 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4

def hex_to_rgba(hex_color, alpha=1.0):
    """#RRGGBB → Linear RGBA"""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r = int(hex_color[0:2], 16) / 255.0
    g = int(hex_color[2:4], 16) / 255.0
    b = int(hex_color[4:6], 16) / 255.0
    # sRGB → Linear変換
    r, g, b = srgb_to_linear(r), srgb_to_linear(g), srgb_to_linear(b)
    return (r, g, b, alpha)

# ==================================================================
# ▼ Color_Ramp 設定
# ==================================================================
def node_color_ramp_setting(
    material_name               # Material Name
,   node_name                   # Node Name
,   color_0=(0,0,0,1)           # Color
,   color_1=(1,1,1,1)           # Color
,   position_0=0                # Position
,   position_1=1                # Position
,   interpolation="LINEAR"
):
    common_path = bpy.data.materials[material_name].node_tree.nodes[node_name]
    common_path.color_ramp.elements[0].color = color_0
    common_path.color_ramp.elements[1].color = color_1
    common_path.color_ramp.elements[0].position = position_0
    common_path.color_ramp.elements[1].position = position_1
    common_path.color_ramp.interpolation = interpolation


# ==================================================================
# ▼ 既存マテリアルコピー
# ==================================================================
def cp_exist_material(
    exist_material_name="exist_material_name"   # Materila Name
,   new_material_name="new_material_name"       # New Material Name
):
    # Get Material
    material = bpy.data.materials.get(exist_material_name)
    # Materila Copy 
    new_material = material.copy()
    # Set Material Name
    new_material.name = new_material_name
    # Assign Material to an Object
    bpy.context.active_object.data.materials.append(new_material)
    # Activate Material Slot
    for i, mat in enumerate(bpy.context.active_object.material_slots):
        if mat.material.name == new_material_name:
            bpy.context.active_object.active_material_index = i
            break
    # Assign Slot
    bpy.ops.object.material_slot_assign()


# ==================================================================
# ▼ イメージテクスチャ設定
# ==================================================================
def add_image_texture(
    material_name                   # Material Name
,   image_path=None                 # 外部ファイルパス or None
,   image_name=None                 # Blender内部Image名
,   texture_node_name="TX_Image_00" # Texture Node Name
,   node_location=(-300, 300)       # Node Location
):
    # Get Material
    material = bpy.data.materials.get(material_name)
    if material is None:
        # Create Material
        material = bpy.data.materials.new(name=material_name)
    # Set Use Node
    material.use_nodes = True
    nodes = material.node_tree.nodes

    # Check Exist Image Texture
    texture_node = nodes.get(texture_node_name)
    if texture_node is None:
        # Create Image Texture
        texture_node = nodes.new(type='ShaderNodeTexImage')
        texture_node.name = texture_node_name
    texture_node.location = node_location

    # Set Image
    img = None
    if image_name and image_name in bpy.data.images:
        img = bpy.data.images[image_name]
    elif image_path:
        for existing_img in bpy.data.images:
            if bpy.path.abspath(existing_img.filepath_raw) == bpy.path.abspath(image_path):
                img = existing_img
                break
        if img is None:
            img = bpy.data.images.load(image_path)
    else:
        raise ValueError("Set image_path or image_name")

    texture_node.image = img

    return texture_node


# ==================================================================
# ▼ UV Editor上での要素選択
# ==================================================================
def uv_editor_element_select(
    element_list=[]         # Element Index List
,   select_mode="FACE"      # Mode
,   object_name_list=[]     # Object Name List
):
    # All Select Desable
    bpy.ops.uv.select_all(action='DESELECT')
    # Enable UV Sync Selection（選択の同期）
    bpy.context.scene.tool_settings.use_uv_select_sync = False
    # Select Element in 3D View
    mdl_cm_lib.element_select(
        element_list=element_list
    ,   select_mode=select_mode
    ,   object_name_list=object_name_list
    )
    # Get BMesh Data
    bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
    # Get UV Layer
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        print("UVレイヤーが見つかりません。")
        return
    # Select Element Index in UV Editor
    for face in bm.faces:
        if face.select:
            for loop in face.loops:
                uv = loop[uv_layer]
                uv.select = True
    # Update Mesh Change
    bmesh.update_edit_mesh(bpy.context.active_object.data)


# ==================================================================
# ▼ UV Editor 移動
# ==================================================================
def move_selected_uvs(
    offset_x        # x方向
,   offset_y        # y方向
):
    obj = bpy.context.active_object
    # Check Target Object
    if obj is None or obj.type != 'MESH':
        print("アクティブなメッシュオブジェクトが必要です。")
        return
    # Change Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh Data
    bm = bmesh.from_edit_mesh(obj.data)
    # Get UV Layer
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        print("UVレイヤーが見つかりません。")
        return
    # Move Select UV
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                # UV座標を移動
                uv.uv.x += offset_x
                uv.uv.y += offset_y
    # Update Mesh
    bmesh.update_edit_mesh(obj.data)


# ==================================================================
# ▼ UV Editor 拡大・縮小
# ==================================================================
def scale_selected_uvs(
    scale_x     # x方向
,   scale_y     # y方向
):
    obj = bpy.context.active_object
    # Check Target Object
    if obj is None or obj.type != 'MESH':
        print("アクティブなメッシュオブジェクトが必要です。")
        return
    # Change Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh Data
    bm = bmesh.from_edit_mesh(obj.data)
    # Get UV Layer
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        print("UVレイヤーが見つかりません。")
        return
    # Calucurate Center Point
    uv_coords = []
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                uv_coords.append((uv.uv.x, uv.uv.y))
    if not uv_coords:
        print("選択されたUVがありません。")
        return
    center_x = sum([coord[0] for coord in uv_coords]) / len(uv_coords)
    center_y = sum([coord[1] for coord in uv_coords]) / len(uv_coords)
    # Scaling Select UV
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                uv.uv.x = center_x + (uv.uv.x - center_x) * scale_x
                uv.uv.y = center_y + (uv.uv.y - center_y) * scale_y
    # Update Mesh
    bmesh.update_edit_mesh(obj.data)

# ==================================================================
# ▼ UV Editor 回転
# ==================================================================
def rotate_selected_uvs(
    angle_degrees
):
    obj = bpy.context.active_object
    # Check Target Object
    if obj is None or obj.type != 'MESH':
        print("アクティブなメッシュオブジェクトが必要です。")
        return
    # Change Edit Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh Data
    bm = bmesh.from_edit_mesh(obj.data)
    # Get UV Layer
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        print("UVレイヤーが見つかりません。")
        return
    # Calucurate Center Point
    uv_coords = []
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                uv_coords.append((uv.uv.x, uv.uv.y))
    if not uv_coords:
        print("選択されたUVがありません。")
        return
    center_x = sum([coord[0] for coord in uv_coords]) / len(uv_coords)
    center_y = sum([coord[1] for coord in uv_coords]) / len(uv_coords)
    # Change Radian
    angle_radians = math.radians(angle_degrees)
    # Rotate Select UV
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                # Calcurate Offset Center
                dx = uv.uv.x - center_x
                dy = uv.uv.y - center_y
                # 回転行列適用
                uv.uv.x = center_x + (dx * math.cos(angle_radians) - dy * math.sin(angle_radians))
                uv.uv.y = center_y + (dx * math.sin(angle_radians) + dy * math.cos(angle_radians))
    # Update Mesh
    bmesh.update_edit_mesh(obj.data)



# ==================================================================
# ▼ UV Editor Mirror 投影
# ==================================================================
def mirror_selected_uvs(
    axis="X"
):
    obj = bpy.context.active_object    
    # Check Target Object
    if obj is None or obj.type != 'MESH':
        print("アクティブなメッシュオブジェクトが必要です。")
        return
    # Change Mode
    bpy.ops.object.mode_set(mode='EDIT')
    # Get BMesh Data
    bm = bmesh.from_edit_mesh(obj.data)
    # Get UV Layer
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        print("UVレイヤーが見つかりません。")
        return
    # Calucurate Center Point
    uv_coords = []
    for face in bm.faces:
        for loop in face.loops:
            uv = loop[uv_layer]
            if uv.select:
                uv_coords.append(uv.uv.x)
    if not uv_coords:
        print("選択されたUVがありません。")
        return
    if (axis == "X"):
        # Calculate the center of the X-axis of the UV coordinates.
        center_x = sum(uv_coords) / len(uv_coords)
        # Mirror
        for face in bm.faces:
            for loop in face.loops:
                uv = loop[uv_layer]
                if uv.select:
                    # Flip with offset from center (中心からのオフセットで反転)
                    uv.uv.x = center_x - (uv.uv.x - center_x)
    else:
        # Calculate the center of the Y-axis of the UV coordinates. (UV座標のY軸の中心を計算)
        center_y = sum(uv_coords) / len(uv_coords)
        # Mirror
        for face in bm.faces:
            for loop in face.loops:
                uv = loop[uv_layer]
                if uv.select:
                    # Flip with offset from center (中心からのオフセットで反転)
                    uv.uv.y = center_y - (uv.uv.y - center_y)
    # Update Mesh
    bmesh.update_edit_mesh(obj.data)


# ==================================================================
# ▼ Bake 画像 作成 : UVエディター上でベイク用の新規画像生成
# ==================================================================
def create_bake_texture_image(
    image_name="image_name",
    width=2048,
    height=2048,
    color=(0.0, 0.0, 0.0, 1.0),  # RGBA (黒)
    alpha=True
):
    # If Image exists
    if image_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[image_name])

    # Create Image
    img = bpy.data.images.new(
        name=image_name,
        width=width,
        height=height,
        alpha=alpha,
        float_buffer=False,
    )
    # Set Init Color
    img.generated_color = color
    # Activate Image on UV Editor
    for area in bpy.context.screen.areas:
        if area.type == 'IMAGE_EDITOR':
            for space in area.spaces:
                if space.type == 'IMAGE_EDITOR':
                    space.image = img
                    break


# ==================================================================
# ▼ Bake
# ==================================================================
def bake_image_save(
    obj_name="obj_name"                 # オブジェクト名
,   bake_image_name="bake_image_name"   # Base Bake Image 名
,   bake_type="DIFFUSE"                 # DIFFUSE/ROUGHNESS/NORMAL/GLOSSY
,   image_path="./IMAGE_NAME.jpg"       # 出力ファイルパス
,   file_format="JPEG"                  # 出力ファイルフォーマット
,   margin=4                            # 余白
,   samples=10                          # サンプル数
,   material_list=[]                    # マテリアルリスト
,   node_locate=0                       # ノード位置調整用
):
    # Mode切り替え
    bpy.ops.object.mode_set(mode='OBJECT')
    # アクティブオブジェクト
    mdl_cm_lib.active_object_select(object_name_list=[obj_name])
    # ------------------------------------
    # Add Base Image Texture
    # ------------------------------------
    for i in range(len(material_list)):
        mat_name = material_list[i]
        tx_name = "TX_Image_Base_" + bake_type
        # イメージテクスチャ追加
        add_image_texture(
            material_name=mat_name
        ,   image_name=bake_image_name
        ,   texture_node_name=tx_name
        ,   node_location=(-800,800)
        )
        # ノード 選択
        select_node(
            material_name=mat_name
        ,   node_name=tx_name
        )
    # ------------------------------------
    # Bake Render Setting (Cycles)
    # ------------------------------------
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.device = 'GPU'
    bpy.context.scene.cycles.samples = samples
    bpy.context.scene.cycles.preview_samples = 64
    bpy.context.scene.cycles.use_adaptive_sampling = True
    bpy.context.scene.cycles.use_denoising = False
    # ------------------------------------
    # Bake Setting
    # ------------------------------------
    bpy.context.scene.render.bake.use_pass_direct = False
    bpy.context.scene.render.bake.use_pass_indirect = False
    bpy.context.scene.render.bake.use_pass_color = True
    bpy.context.scene.render.bake.use_clear = True
    bpy.context.scene.render.bake.margin = margin
    bpy.context.scene.render.bake.view_from = 'ABOVE_SURFACE'
    bpy.context.scene.cycles.bake_type = bake_type

    # ------------------------------------
    # Save Path設定
    # ------------------------------------
    abs_path = bpy.path.abspath(image_path)
    os.makedirs(os.path.dirname(abs_path), exist_ok=True)

    # 画像ファイルがすでに存在する場合 → Bake処理をスキップ
    if not os.path.exists(abs_path):
        # ------------------------------------
        # Bake  -- pass_filter --
        # ------------------------------------
        if bake_type == "DIFFUSE":
            bpy.ops.object.bake(
                type='DIFFUSE',
                pass_filter={'COLOR'},
                use_clear=True,
                margin=margin
            )
        elif bake_type == "ROUGHNESS":
            bpy.ops.object.bake(
                type='ROUGHNESS',
                use_clear=True,
                margin=margin
            )
        elif bake_type == "NORMAL":
            bpy.ops.object.bake(
                type='NORMAL',
                use_clear=True,
                margin=margin
            )
        elif bake_type == "GLOSSY":
            bpy.ops.object.bake(
                type='GLOSSY',
                use_clear=True,
                margin=margin
            )
        else:
            print(f"[Error] Unsupported bake type: {bake_type}")
            return
        
        # ------------------------------------
        # Save Image
        # ------------------------------------
        # Get Image
        bake_image = bpy.data.images.get(bake_image_name)
        if not bake_image:
            print(f"[Error] Image '{bake_image_name}' not found in bpy.data.images.")
            return

        # Save Setting
        bake_image.filepath_raw = abs_path
        bake_image.file_format = file_format

        # Save
        try:
            bake_image.save()
        except Exception as e:
            print(f"[Error] Failed to save image '{bake_image_name}': {e}")
    
    # ------------------------------------
    # Set Image Texture
    # ------------------------------------
    for i in range(len(material_list)):
        mat_name = material_list[i]
        tx_name = "TX_Image_" + bake_type
        # ------------------------------------
        # Add Image Texture in Material
        # ------------------------------------
        add_image_texture(
            material_name=mat_name
        ,   image_path=image_path
        ,   texture_node_name=tx_name
        ,   node_location=(-600,600)
        )
        # ノード 選択
        select_node(
            material_name=mat_name
        ,   node_name=tx_name
        )
        # ------------------------------------
        # Connect Principled BSDF Node
        # ------------------------------------
        if bake_type == "DIFFUSE":
            node_value_change(
                material_name=mat_name
            ,   node_name=tx_name
            ,   element_name="Color Space"
            ,   set_value="sRGB"
            )
            # Base Colorへ接続
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=tx_name
            ,   texture_node_name_in="Principled BSDF"
            ,   output_link="Color"
            ,   input_link="Base Color"
            )
        elif bake_type == "ROUGHNESS":
            # Roughnessへ接続（Non-Color設定）
            node_value_change(
                material_name=mat_name
            ,   node_name=tx_name
            ,   element_name="Color Space"
            ,   set_value="Non-Color"
            )
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=tx_name
            ,   texture_node_name_in="Principled BSDF"
            ,   output_link="Color"
            ,   input_link="Roughness"
            )
        elif bake_type == "NORMAL":
            # Normal Mapノードを追加
            normal_map_node = "NormalMap_" + mat_name
            # テクスチャ追加
            add_new_texture(
                material_name=mat_name
            ,   texture_name="ShaderNodeNormalMap"
            ,   texture_node_name=normal_map_node
            ,   node_location=(-400, 400)
            )
            # ノード接続: 画像 → NormalMap → PrincipledBSDF
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=tx_name
            ,   texture_node_name_in=normal_map_node
            ,   output_link="Color"
            ,   input_link="Color"
            )
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=normal_map_node
            ,   texture_node_name_in="Principled BSDF"
            ,   output_link="Normal"
            ,   input_link="Normal"
            )
        elif bake_type == "GLOSSY":
            # Non-Color 設定
            node_value_change(
                material_name=mat_name
            ,   node_name=tx_name
            ,   element_name="Color Space"
            ,   set_value="Non-Color"
            )
            # RGB → Float 変換ノードを追加（ShaderNodeRGBToBW）
            avg_node_name = "Avg_" + tx_name
            add_new_texture(
                material_name=mat_name
            ,   texture_name="ShaderNodeRGBToBW"
            ,   texture_node_name=avg_node_name
            ,   node_location=(-400, 400)
            )
            # ノード接続: 画像 → RGBToBW → Roughness
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=tx_name
            ,   texture_node_name_in=avg_node_name
            ,   output_link="Color"
            ,   input_link="Color"
            )
            node_link_func(
                material_name=mat_name
            ,   texture_node_name_out=avg_node_name
            ,   texture_node_name_in="Principled BSDF"
            ,   output_link="Val"
            ,   input_link="Roughness"
            )
        else:
            print(f"[Warning] Unknown bake_type '{bake_type}' — skipping node connection.")
