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

# ======================================================================
# = ▼ Blender 環境初期化
# ======================================================================
def bpy_modeling_initialize_common(
    rm_flg=False        # オブジェクト削除フラグ
,   reload_list=[]
):
    # コンテキスト オーバーライド用辞書取得
    override = get_override('VIEW_3D', 'WINDOW')
    # Blender Config
    update_3d_view_overlay()
    preferences_setting()
    # 環境初期化
    set_initial_dev(
        rm_flg
    )
    # 3Dカーソル位置初期化
    set_3d_cursor_position()
    # カスタムID表示
    enable_local_addon(
        addon_path=git_root + "/Add_on/persistent_id_overlay_fully.py",
        addon_name="persistent_id_overlay_fully",
        addon_name_head=""
    )
    # カスタムID表示有効化
    # アドオンがすでに register() 済みであることが前提
    bpy.ops.view3d.persistent_id_overlay_enable()
    # カスタムID表示サイズ
    bpy.context.scene.persistent_id_overlay_font_size = 19
    # カスタムID 選択時表示
    bpy.context.scene.persistent_id_overlay_show_only_selected = True
    # 3Dビュー スペース取得
    # 拡大縮小時 視認 処理設定
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # クリップスタート設定（e.g.0.001）
                    space.clip_start = 0.0001
    # ファイルの実行毎リロード
    cm_lib._auto_reload_modules(reload_list)
    return override


# ========================================================================
# = ▼ コンテキスト上書き
# ========================================================================
def get_override(area_type, region_type):
    for area in bpy.context.screen.areas: 
        if area.type == area_type:             
            for region in area.regions:                 
                if region.type == region_type:                    
                    override = {'area': area, 'region': region} 
                    return override
    # Error Message
    raise RuntimeError(f"Wasn't able to find {region_type} in area {area_type}. Make sure it's open while executing script.")


# ========================================================================
# = ▼ Blender 表示設定
# ========================================================================
def update_3d_view_overlay():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            space = area.spaces.active
            # 移動ギズモ表示
            area.spaces.active.show_gizmo_object_translate = True
            if space.type == 'VIEW_3D':
                overlay = space.overlay                 # オーバーレイ設定取得
                overlay.show_edge_crease        = True  # エッジクリース（強調されたエッジ）表示
                overlay.show_face_center        = False # 面中心表示
                overlay.show_face_normals       = False # 面法線表示
                overlay.show_vertex_normals     = False # 頂点法線表示
                overlay.show_edge_seams         = True  # エッジシーム（接合部表示）
                overlay.show_extra_indices      = False  # インデックス（面,エッジなど）表示
                overlay.show_face_orientation   = False  # 面 向き表示
                overlay.show_stats              = True  # メッシュ情報

                # ---- Shading settings ----
                shading = space.shading
                shading.color_type = 'RANDOM'   # ランダム色に設定
                shading.show_xray = False       # 例: Xray切替

                return


# ========================================================================
# = ▼ preference設定
# ========================================================================
def preferences_setting():
    # Orbit Sensitivity（オービット センシビリティ）設定
    # bpy.context.preferences.inputs.view_rotate_sensitivity = 1.5
    # Orbit Around Selection（選択周囲 オービット）
    bpy.context.preferences.inputs.use_rotate_around_active = True
    # Depthオプション有効
    # bpy.context.preferences.inputs.use_auto_depth = True
    # Depthオプション有効
    bpy.context.preferences.inputs.use_zoom_to_mouse = True
    # Smooth View（スムースビュー）時間（ミリ秒単位）
    bpy.context.preferences.view.smooth_view = 200
    # 回転角度ステップ設定
    # bpy.context.preferences.inputs.view_rotate_angle = 10.0  # 10度
    # ギズモ 種類設定
    # LOCAL / GLOBAL / NORMAL etc.
    bpy.context.scene.transform_orientation_slots[1].type = 'NORMAL'


# ========================================================================
# = ▼ Blender環境 初期化
# ========================================================================
def set_initial_dev(
    rm_flg=False
):
    # アクティブオブジェクト確認
    if bpy.context.active_object is None:
        # オブジェクトがない場合->キューブ追加
        bpy.ops.mesh.primitive_cube_add()
    # モード切替
    bpy.ops.object.mode_set(mode='OBJECT')
    # ------------------------------------------------------------------
    # - Delete all objects in the scene
    # ------------------------------------------------------------------
    if (rm_flg):
        # 全オブジェクト選択
        bpy.ops.object.select_all(action='SELECT')
        # 全オブジェクト削除
        bpy.ops.object.delete(use_global=False)
        # 非表示状態オブジェクト削除
        # 全オブジェクト取得
        all_objects = bpy.data.objects
        # 非表示オブジェクト含め削除
        for obj in all_objects:
            bpy.data.objects.remove(obj)
    # 仮Obj削除
    if "Cube" in bpy.context.scene.objects:
        bpy.data.objects.remove(bpy.data.objects["Cube"], do_unlink=True)
    # 未使用アイテム削除
    rm_nonused_all_items()
    # シーンに存在しないオブジェクトの削除
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    # 孤立オブジェクト削除
    cleanup_orphaned_objects()
    purge_scene_unlinked_objects()
    if (rm_flg):
        # 全コレクション削除
        for collection in bpy.data.collections:
            bpy.data.collections.remove(collection)
    # ------------------------------------------------------------------
    # - 1. 初期状態
    # ------------------------------------------------------------------
    # デフォルトコレクション作成
    # new_collection = bpy.data.collections.new(name="Collection")
    # コレクションをシーンにリンク
    # bpy.context.scene.collection.children.link(new_collection)
    # 全オブジェクトの選択解除
    bpy.ops.object.select_all(action='DESELECT')
    set_xray_view(key=False)


#-------------------------------------
# # 孤立オブジェクト削除
#-------------------------------------
def cleanup_orphaned_objects():
    # シーンにリンクされていないオブジェクトを削除
    for obj in list(bpy.data.objects):
        if not obj.users_scene:  # どのシーンにも属していない
            bpy.data.objects.remove(obj, do_unlink=True)

    # 親が存在しないのに parent が壊れている場合も削除
    for obj in list(bpy.data.objects):
        if obj.parent and obj.parent.name not in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

#-------------------------------------
# # 孤立オブジェクト削除
#-------------------------------------
def purge_scene_unlinked_objects():
    removed = 0
    # bpy.data.objects をコピーしてループ（削除中の変化を避けるため）
    for obj in list(bpy.data.objects):
        # シーンに所属していない場合
        if obj.name not in bpy.context.scene.objects:
            # 親子関係解除
            obj.parent = None
            bpy.data.objects.remove(obj, do_unlink=True)
            removed += 1


# ========================================================================
# = ▼ Shift + C（カーソル位置初期化）
# ========================================================================
def set_3d_cursor_position(
        position_list=[0, 0, 0]
):
    # 3Dカーソル位置->原点
    bpy.context.scene.cursor.location = (position_list[0], position_list[1], position_list[2])
    
    # ビュー位置, ズームレベル リセット
    # for area in bpy.context.screen.areas:
    #     if area.type == 'VIEW_3D':
    #         space = area.spaces.active
    #         region_3d = space.region_3d
            
    #         # オーソグラフィック設定
    #         region_3d.view_perspective = 'PERSP'
            
    #         # 位置, ズームレベル リセット
    #         region_3d.view_location = mathutils.Vector((0, 0, 0))
    #         region_3d.view_distance = 8
    #         region_3d.view_rotation = mathutils.Euler((0, 0, 0)).to_quaternion()
            
    # View更新
    bpy.context.view_layer.update()


# ========================================================================
# = ▼ 透過ビューのON/OFF
# ========================================================================
def set_xray_view(key=True):
    # 3Dビューエリア取得
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # 透過表示（X-ray）設定ON
                    space.shading.show_xray = key
                    # X-ray強度設定（デフォルト1.0）
                    space.shading.xray_alpha = 0.5
                    break


# ========================================================================
# = ▼ 未使用/使用アイテム削除
# ========================================================================
def rm_nonused_all_items(
    rm_flg=False
):
    # 未使用メッシュデータブロック削除
    for mesh in bpy.data.meshes:
        if not mesh.users:
            bpy.data.meshes.remove(mesh)
    # 未使用テクスチャデータブロック削除
    for texture in bpy.data.textures:
        if not texture.users:
            bpy.data.textures.remove(texture)
    # 未使用テクスチャデータブロック削除
    for texture in bpy.data.lights:
        if not texture.users:
            bpy.data.lights.remove(texture)
    # 未使用テクスチャデータブロック削除
    for texture in bpy.data.cameras:
        if not texture.users:
            bpy.data.cameras.remove(texture)
    # 未使用マテリアル削除
    for material in bpy.data.materials:
        if not material.users:
            bpy.data.materials.remove(material)
    # --- 未使用アクション削除（アニメーションデータブロック） ---
    for action in list(bpy.data.actions):
        if not action.users:
            bpy.data.actions.remove(action)
    # --- 未使用NLAトラック削除 ---
    # 各オブジェクトに animation_data がある場合のみチェック
    for obj in bpy.data.objects:
        ad = obj.animation_data
        if ad and ad.nla_tracks:
            for track in list(ad.nla_tracks):
                # トラックが空、または全ストリップが無効なら削除
                if len(track.strips) == 0 or all(not s for s in track.strips):
                    ad.nla_tracks.remove(track)

            # NLAトラックがなく、アクションも未設定なら animation_data 自体削除
            if not ad.action and not ad.nla_tracks:
                obj.animation_data_clear()
    # --- 未使用アニメーション（ドライバー付きでもない場合） ---
    # ドライバーが残っているActionを消さないようにする場合は上の処理で十分
    # 全削除を強制したいなら rm_flg によって分岐
    if rm_flg:
        # 使用マテリアル削除
        for mat in list(bpy.data.materials):
            bpy.data.materials.remove(mat)
        # 画像データ削除
        for img in list(bpy.data.images):
            bpy.data.images.remove(img)
        # すべてのアクション削除
        for action in list(bpy.data.actions):
            bpy.data.actions.remove(action)
        # すべてのNLAトラック削除（全オブジェクト）
        for obj in bpy.data.objects:
            if obj.animation_data:
                obj.animation_data_clear()
    if (rm_flg):
        # 使用マテリアル削除
        for material in bpy.data.materials:
            bpy.data.materials.remove(material)
        # 画像データ削除
        for img in bpy.data.images:
            bpy.data.images.remove(img)


# ========================================================================
# メッシュの裏表を確認する表示切替
# ========================================================================
def face_orientation(key=True):
    found = False
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.overlay.show_face_orientation = key
                    found = True
                    print("Face Orientation が有効になりました。")
                    break
        if found:
            break
    if not found:
        print("3D ビューが見つかりませんでした。")


#-------------------------------------
# オブジェクトが存在するか確認する関数
#-------------------------------------
def require_new_objects(
    obj_list=["object_name"]
,   gen_flag=False
,   rm_flag=True
):
    # オブジェクトの存在確認・削除処理を行い、
    # 新規生成が必要かどうかを判定する。

    # Parameters
    # ----------
    # obj_list : list[str]
    #     対象となるオブジェクト名のリスト
    # gen_flag : bool
    #     True の場合は常に削除して新規生成を要求する

    # Returns
    # -------
    # bool
    #     True ならオブジェクトの新規生成が必要
    #     False なら既存のオブジェクトを利用可能

    def remove_with_children(obj):
        # """オブジェクトとその子供を再帰的に削除"""
        # 子供を先に削除
        for child in list(obj.children):
            remove_with_children(child)
        # 自身を削除
        if obj.name in bpy.data.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # gen_flag=True の場合 → 強制削除
    if gen_flag:
        for name in obj_list:
            obj = bpy.data.objects.get(name)
            if obj:
                remove_with_children(obj)
        return True

    # シーンまたはデータに存在するかチェック
    for obj_name in obj_list:
        obj = bpy.data.objects.get(obj_name)
        if obj is None or obj_name not in bpy.context.scene.objects:
            # 一つでも欠けていれば削除 & True
            if rm_flag:
                for name in obj_list:
                    obj = bpy.data.objects.get(name)
                    if obj:
                        remove_with_children(obj)
            return True

    # 全て存在する場合 → False
    return False


# ========================================================================
# = ▼ アドオン・Extensionの追加
# ========================================================================
def install_and_enable_addon(
        addon_directory                         # Directory
    ,   url                                     # Download URL
    ,   addon_name                              # Addon Name
    ,   addon_name_head="bl_ext.blender_org."   # Addon Prefix (アドオン名接頭辞)
    ,   zip_flag=True                           # zipファイル 回答フラグ
):
    # 保存先ZIPファイルのパス
    local_zip_path = os.path.join(addon_directory, addon_name+'.zip')
    # アドオンのインストール先パス
    addon_path = os.path.join(addon_directory, addon_name)
    # アドオンがすでにインストールされている場合
    if os.path.exists(addon_path):
        print(f"Addon '{addon_name}' already exists. Skipping download and installation.")
        # アドオン有効化チェック
        addon_name = addon_name_head + addon_name
        if addon_name in bpy.context.preferences.addons:
            print(f"Addon '{addon_name}' is already enabled.")
        else:
            try:
                # アドオン有効化
                bpy.ops.preferences.addon_enable(module=addon_name)
                print(f"Addon '{addon_name}' enabled successfully.")
            except RuntimeError as e:
                print(f"Failed to enable addon '{addon_name}': {e}")
        return
    else:
        # URLからZIPファイルダウンロード
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()  # HTTPエラーチェック
            with open(local_zip_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print("Download completed.")
        except requests.exceptions.RequestException as e:
            print(f"Failed to download file: {e}")
            return
        if zip_flag:
            # ZIPファイル解凍
            try:
                with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                    zip_ref.extractall(addon_directory+"/"+addon_name)
                print("Extraction completed.")
            except zipfile.BadZipFile as e:
                print(f"Failed to extract ZIP file: {e}")
                return
            # ZIPファイルを削除
            os.remove(local_zip_path)
            # アドオン有効化
            addon_name = addon_name_head + addon_name
            if addon_name not in bpy.context.preferences.addons:
                try:
                    bpy.ops.preferences.addon_enable(module=addon_name)
                    print(f"Addon '{addon_name}' enabled successfully.")
                except RuntimeError as e:
                    print(f"Failed to enable addon '{addon_name}': {e}")
            else:
                print(f"Addon '{addon_name}' is already enabled.")
        else:
            # アドオンをインストール
            bpy.ops.preferences.addon_install(filepath=addon_path+".zip", overwrite=True)
            # アドオンを有効化
            bpy.ops.preferences.addon_enable(module=addon_name)
            # オプション：Preferences を保存（次回も自動有効化したい場合）
            bpy.ops.wm.save_userpref()

def enable_local_addon(addon_path, addon_name, addon_name_head="bl_ext.blender_org."):
    """
    ローカルのアドオン（ディレクトリまたは.pyファイル）をインストールして有効化する

    addon_path : str  -> アドオンのパス（ディレクトリ or ZIP or .pyファイル）
    addon_name : str  -> アドオン名（モジュール名）
    addon_name_head : str -> Blender内で有効化する際の接頭辞
    """
    full_addon_name = addon_name_head + addon_name

    # 既に有効化されていればスキップ
    if full_addon_name in bpy.context.preferences.addons:
        return

    # パスが存在するかチェック
    if not os.path.exists(addon_path):
        print(f"Addon path does not exist: {addon_path}")
        return

    try:
        # アドオンをインストール
        bpy.ops.preferences.addon_install(filepath=addon_path, overwrite=True)
        print(f"Addon '{addon_name}' installed from '{addon_path}'")
    except Exception as e:
        print(f"Failed to install addon: {e}")
        return

    # アドオン有効化
    try:
        bpy.ops.preferences.addon_enable(module=full_addon_name)
        print(f"Addon '{full_addon_name}' enabled successfully.")
    except RuntimeError as e:
        print(f"Failed to enable addon '{full_addon_name}': {e}")
        return

    # オプション：ユーザープリファレンス保存
    bpy.ops.wm.save_userpref()


# ========================================================================
# = ▼ アドオン有効化(Addon/Add-on)
# ========================================================================
def enable_add_on(addon_name="node_wrangler"):
    # Enable Addon
    if addon_name not in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_enable(module=addon_name)


# ========================================================================
# = ▼ コレクション整理
# ========================================================================
def collection_create_or_move(
        object_list=[],                  # Object List
        collection_name="NewCollection", # Collection Name
        move_to_collection_name="NaN"    # Destination Collection Name
):
    # Save Current Mode
    current_mode = None
    if bpy.context.object:
        current_mode = bpy.context.object.mode
        bpy.ops.object.mode_set(mode='OBJECT')

    # Release Object Selection
    bpy.ops.object.select_all(action='DESELECT')

    # --------- コレクション生成/取得ユーティリティ ----------
    def get_or_create_collection(name):
        col = bpy.data.collections.get(name)
        if col:
            if col.name not in bpy.context.scene.collection.children.keys():
                bpy.context.scene.collection.children.link(col)
            return col
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
        return col

    # --------- コレクション取得 ----------
    collection_1 = get_or_create_collection(collection_name)

    # 子孫も含めてオブジェクトを移動する関数
    def move_object_hierarchy_to_collection(obj, target_collection, remove_from_collection=None):
        def recursive_link(o):
            if o.name not in target_collection.objects:
                target_collection.objects.link(o)
            if remove_from_collection and o.name in remove_from_collection.objects:
                remove_from_collection.objects.unlink(o)
            for child in o.children:
                recursive_link(child)
        recursive_link(obj)

    if move_to_collection_name != "NaN":
        # 移動先コレクション取得
        collection_2 = get_or_create_collection(move_to_collection_name)
        # Move Object between collection (親子関係を維持)
        for obj_name in object_list:
            mdl_cm_lib.active_object_select(object_name_list=[obj_name])
            obj = bpy.context.active_object
            if obj:
                move_object_hierarchy_to_collection(obj, collection_2, remove_from_collection=collection_1)
    else:
        # New Object -> Store objects in collection (親子関係を維持)
        for obj_name in object_list:
            mdl_cm_lib.active_object_select(object_name_list=[obj_name])
            obj = bpy.context.active_object
            if obj:
                move_object_hierarchy_to_collection(obj, collection_1, remove_from_collection=bpy.context.scene.collection)

    # Release Active Object
    bpy.ops.object.select_all(action='DESELECT')

    # Change Original Mode
    if current_mode and bpy.context.object and bpy.context.object.type == 'MESH':
        bpy.ops.object.mode_set(mode=current_mode)

# ========================================================================
# = ▼ 参考画像読み込み
# ========================================================================
def image_reference_import(
    override
,   relative_img_path="/ref_img/sample.png"
,   img_name="img_name"
,   location=(0, 0, 0)
,   rotation=(0, 0, 0)
,   scale=(1, 1, 1)
,   exist_flg=True
,   img_alpha=0.3
,   empty_image_side='FRONT'
):
    if (exist_flg):
        # 上書きしたコンテキストでオペレーターを実行
        with bpy.context.temp_override(**override):
            # 参考画像読み込み
            bpy.ops.object.empty_image_add(
                filepath=script_dir + relative_img_path
            ,   relative_path=True
            ,   align='WORLD'
            ,   location=(0, 0, 0)
            ,   rotation=rotation
            ,   scale=(1, 1, 1)
            ,   background=False
            )
            # オブジェクト名設定
            bpy.context.object.name = img_name
            # ピボット設定
            bpy.context.scene.tool_settings.transform_pivot_point = 'CURSOR'
            # 要素サイズ変更
            bpy.ops.transform.resize(
                value=scale
            ,   orient_type='GLOBAL'
            )
        # オブジェクト移動
        bpy.ops.transform.translate(
            value=location
        ,   orient_type='GLOBAL'
        )
        # 不透明度
        bpy.context.object.use_empty_image_alpha = True
        bpy.context.object.color[3] = img_alpha
        # 表示向き設定
        bpy.context.object.empty_image_side = empty_image_side

#------------------------------------------------
# Object Existence Check
#------------------------------------------------
def glb_exist_obj_chk(obj_list=["object_name"], EXIST_FLAG_DICT=None, gen_flag=False):
    """
    Blender内のオブジェクト + ボーン存在確認 + 必要に応じ全削除 / 辞書管理
    - obj_list のどれか1つでも存在しなければ obj_list 内全削除
    - gen_flag に応じて辞書の参照/更新
    """

    if not isinstance(obj_list, list):
        print("Error: data is not a list. Program will exit.")
        sys.exit(1)   # 異常終了コード1で終了

    # --- ヘルパー関数 ---
    def object_exists(name):
        """オブジェクト（メッシュ/Empty/アーマチュア）が存在するか"""
        return bpy.data.objects.get(name) is not None

    def bone_exists(name):
        """ボーンが存在するか（すべてのアーマチュアを探索）"""
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.data.bones.get(name):
                return True
        return False

    def delete_object_or_bone(name):
        """オブジェクトまたはボーンを削除"""
        obj = bpy.data.objects.get(name)
        if obj:
            # 子オブジェクトも再帰削除
            for child in obj.children[:]:
                delete_object_or_bone(child.name)
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            # ボーン削除（アーマチュア内）
            for arm in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
                if name in arm.data.bones:
                    # ボーン削除には編集モード切替が必要
                    bpy.context.view_layer.objects.active = arm
                    bpy.ops.object.mode_set(mode='EDIT')
                    eb = arm.data.edit_bones.get(name)
                    if eb:
                        arm.data.edit_bones.remove(eb)
                    bpy.ops.object.mode_set(mode='OBJECT')

    # --- 存在チェック ---
    exist_flags = []
    for name in obj_list:
        if object_exists(name):
            exist_flags.append(True)
        elif bone_exists(name):
            exist_flags.append(True)
        else:
            exist_flags.append(False)

    # --- gen_flag = True の場合 ---
    if gen_flag:
        # どれか1つでも存在しなければ True（生成フラグ）
        if not all(exist_flags):
            # 存在しない場合、obj_list 全削除
            for name in obj_list:
                delete_object_or_bone(name)

        # 削除後の状態を登録（最新状態）
        key = tuple(obj_list)
        EXIST_FLAG_DICT[key] = all(
            (object_exists(n) or bone_exists(n)) for n in obj_list
        )
        for name in obj_list:
            EXIST_FLAG_DICT[(name,)] = object_exists(name) or bone_exists(name)

        # 戻り値（削除があったか）
        return not all(exist_flags)

    # --- gen_flag = False の場合 ---
    else:
        key = tuple(obj_list)
        if key in EXIST_FLAG_DICT:
            if EXIST_FLAG_DICT[key]:
                return False  # グループとしてすでに存在していた
            else:
                # 単品でも全て存在していれば False を返す
                if all(EXIST_FLAG_DICT.get((name,), False) for name in obj_list):
                    return False  # 全て単品で存在している
                return True       # どれか欠けている
        else:
            # グループキーが無い場合でも、単品キーを調べる
            if all(EXIST_FLAG_DICT.get((name,), False) for name in obj_list):
                return False      # 全て単品で存在している
            return True           # どれか欠けている

def reset_exist_flag_dict(EXIST_FLAG_DICT=None):
    EXIST_FLAG_DICT.clear()  # 中身だけ空にする

# ========================================================================
# = ▼ オブジェクト結合
# ========================================================================
def join_objects(obj_list, join_name="Joined_Object"):
    """
    指定されたオブジェクトを結合して新しいオブジェクトを生成する
    Args:
        obj_list (list[str]): 結合するオブジェクト名リスト
        join_name (str): 結合後のオブジェクト名
    Returns:
        bpy.types.Object | None : 結合後のオブジェクト、失敗時は None
    """

    # -------------------------------------------------------------
    # 現在のモードを保存
    # -------------------------------------------------------------
    prev_mode = bpy.context.object.mode if bpy.context.object else 'OBJECT'
    if prev_mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # -------------------------------------------------------------
    # 結合対象の存在確認
    # -------------------------------------------------------------
    existing_objs = [bpy.data.objects.get(name) for name in obj_list if bpy.data.objects.get(name)]
    missing_objs = [name for name in obj_list if not bpy.data.objects.get(name)]

    if not existing_objs:
        print("[WARN] join_objects: 有効なオブジェクトが見つかりません。")
        return None

    if missing_objs:
        print(f"[WARN] 以下のオブジェクトが存在しません: {missing_objs}")

    # -------------------------------------------------------------
    # 結合実行
    # -------------------------------------------------------------
    # すべて選択解除
    bpy.ops.object.select_all(action='DESELECT')

    # 結合対象を選択
    for obj in existing_objs:
        obj.select_set(True)

    # 最初のオブジェクトをアクティブに設定
    context_view = bpy.context.view_layer
    context_view.objects.active = existing_objs[0]

    # join 実行
    bpy.ops.object.join()

    # -------------------------------------------------------------
    # 結合後のオブジェクトを取得してリネーム
    # -------------------------------------------------------------
    joined_obj = bpy.context.object
    if joined_obj:
        joined_obj.name = join_name
    else:
        print("[ERROR] 結合処理に失敗しました。")
        return None
    
    # 重複IDを座標順で修正
    mdl_cm_lib.fix_duplicate_ids(join_name)

    # -------------------------------------------------------------
    # 元のモードに戻す
    # -------------------------------------------------------------
    if prev_mode != 'OBJECT':
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except:
            pass

    return joined_obj