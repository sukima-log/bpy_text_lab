# ==================================================================
# = Pre Process
# ==================================================================
from Assets.mdl.{$PROJECT_NAME} import (
    glb, wrap, d00_mdl, d01_uv_unwrap, d02_mtal, d03_bake, d04_bone, d05_animation, d06_shape_key
)
from Assets.parts import (
    model, material
)
# ==================================================================
# Modeling
# ==================================================================

#-------------------------------
# sample_obj Modeling
#-------------------------------
def sample_obj_mdl(
    obj_name
):
    if (glb.glb.glb_exist_obj_chk(obj_list=[obj_name], gen_flag=True)):
        # オブジェクト追加
        bpy.ops.mesh.primitive_cube_add(
            size=1                  # 1辺長
        ,   location=(0, 0, 0)      # 配置場所
        ,   scale=(1.0, 1.0, 1.0)   # x, y, y
        )
        # 名前設定
        bpy.context.object.name = obj_name
        # サイズ変更
        bpy.ops.transform.resize(
            value=(
                1
            ,   1
            ,   1
            )
        ,   orient_type='GLOBAL'
        )
        # オブジェクト移動
        bpy.ops.transform.translate(
            value=(
                0
            ,   0
            ,   0
            )
        ,   orient_type='GLOBAL'
        )
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        # 要素選択
        mdl_cm_lib.element_select(
            element_list=["all"]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # 全ての選択メッシュを外側に向ける
        bpy.ops.mesh.normals_make_consistent(inside=False)


