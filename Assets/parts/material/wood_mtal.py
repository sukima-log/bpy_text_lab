# Sub Code
import bpy, os, sys, subprocess
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
# Common Setting
from Common.common_top import *
#========================================================================================

# =====================================================
# マテリアル 木素材 フローリング
# =====================================================
def mtal_wood_00(
    mtal_name="mtal_name"
,   TX_Brick_00_Color1=(0.802, 0.619, 0.433, 1)
,   TX_Brick_00_Color2=(0.402, 0.176, 0.095, 1)
,   TX_Brick_00_Mortar=(0.06, 0.04, 0.035, 1)
,   TX_Brick_00_Mortar_Size=0.005
,   Mapping_01_Scale=(1, 1, 0.2)
,   TX_Noise_00_Scale=16.5
,   TX_Noise_00_Distortion=2.2
,   TX_Noise_00_Detail=15
,   Mix_RGB_00_Factor=1.0
,   Bump_00_Strength=0.15
):
    # Save : Curren Mode
    current_mode = bpy.context.object.mode
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeTexBrick"
    ,   texture_node_name="TX_Brick_00"
    ,   node_location=(-200, 300)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="TX_Brick_00"
    ,   texture_node_name_in="Principled BSDF"
    ,   output_link="Color"
    ,   input_link="Base Color"
    )
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeMapping"
    ,   texture_node_name="Mapping_00"
    ,   node_location=(-400, 300)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Mapping_00"
    ,   texture_node_name_in="TX_Brick_00"
    ,   output_link="Vector"
    ,   input_link="Vector"
    )
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeTexCoord"
    ,   texture_node_name="TX_Coord_00"
    ,   node_location=(-600, 300)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="TX_Coord_00"
    ,   texture_node_name_in="Mapping_00"
    ,   output_link="Object"
    ,   input_link="Vector"
    )
    # 溝のサイズ
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Brick_00"
    ,   element_name="Mortar Size"
    ,   set_value=TX_Brick_00_Mortar_Size
    )
    # レンガの色変更
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Brick_00"
    ,   element_name="Color1"
    ,   set_value=TX_Brick_00_Color1
    )
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Brick_00"
    ,   element_name="Color2"
    ,   set_value=TX_Brick_00_Color2
    )
    # 溝の色
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Brick_00"
    ,   element_name="Mortar"
    ,   set_value=TX_Brick_00_Mortar
    )
    # --------------------
    # 木の模様を付ける
    # --------------------
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeTexNoise"
    ,   texture_node_name="TX_Noise_00"
    ,   node_location=(-200, -100)
    )
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeMix"
    ,   texture_node_name="Mix_RGB_00"
    ,   node_location=(0, -100)
    ,   settings=[{"name": "data_type", "value": 'RGBA'}]
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="TX_Brick_00"
    ,   texture_node_name_in="Mix_RGB_00"
    ,   output_link="Color"
    ,   input_link="A"
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Mix_RGB_00"
    ,   texture_node_name_in="Principled BSDF"
    ,   output_link="Result"
    ,   input_link="Base Color"
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="TX_Noise_00"
    ,   texture_node_name_in="Mix_RGB_00"
    ,   output_link="Fac"
    ,   input_link="B"
    )
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeMapping"
    ,   texture_node_name="Mapping_01"
    ,   node_location=(-400, -100)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Mapping_01"
    ,   texture_node_name_in="TX_Noise_00"
    ,   output_link="Vector"
    ,   input_link="Vector"
    )
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeTexCoord"
    ,   texture_node_name="TX_Coord_01"
    ,   node_location=(-600, -100)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="TX_Coord_01"
    ,   texture_node_name_in="Mapping_01"
    ,   output_link="Object"
    ,   input_link="Vector"
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Mapping_01"
    ,   texture_node_name_in="TX_Noise_00"
    ,   output_link="Vector"
    ,   input_link="Vector"
    )
    # -----------------------------
    # 木目のような歪みを追加する
    # -----------------------------
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="Mapping_01"
    ,   element_name="Scale"
    ,   set_value=Mapping_01_Scale
    )
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Noise_00"
    ,   element_name="Scale"
    ,   set_value=TX_Noise_00_Scale
    )
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Noise_00"
    ,   element_name="Distortion"
    ,   set_value=TX_Noise_00_Distortion
    )
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="TX_Noise_00"
    ,   element_name="Detail"
    ,   set_value=TX_Noise_00_Detail
    )
    # Mix
    bpy.data.materials[mtal_name].node_tree.nodes["Mix_RGB_00"].blend_type = 'OVERLAY'
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="Mix_RGB_00"
    ,   element_name="Factor"
    ,   set_value=Mix_RGB_00_Factor
    )
    # ----------------------------
    # 木目の質感を加える
    # ----------------------------
    # テクスチャ追加
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name
    ,   texture_name="ShaderNodeBump"
    ,   texture_node_name="Bump_00"
    ,   node_location=(200, -100)
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Mix_RGB_00"
    ,   texture_node_name_in="Bump_00"
    ,   output_link="Result"
    ,   input_link="Height"
    )
    # ノードのリンク
    mtal_cm_lib.node_link_func(
        material_name=mtal_name
    ,   texture_node_name_out="Bump_00"
    ,   texture_node_name_in="Principled BSDF"
    ,   output_link="Normal"
    ,   input_link="Normal"
    )
    # ノード 値変更
    mtal_cm_lib.node_value_change(
        material_name=mtal_name
    ,   node_name="Bump_00"
    ,   element_name="Strength"
    ,   set_value=Bump_00_Strength
    )
    # Change Origin Mode
    bpy.ops.object.mode_set(mode=current_mode)


# =====================================================
# マテリアル 木素材 一枚板
# =====================================================
def mtal_wood_01(
    mtal_name="mtal_wood_01",

    # ------------------------------------------
    # 木目方向（やや誇張、情報整理）
    # ------------------------------------------
    Mapping_00_Scale=(1.0, 10.0, 1.0),

    # ------------------------------------------
    # 年輪（低周波・穏やか）
    # ------------------------------------------
    Ring_Noise_Scale=1.4,
    Ring_Noise_Detail=1.2,
    Ring_Noise_Distortion=0.6,

    # ------------------------------------------
    # 導管（高周波・抑制）
    # ------------------------------------------
    Grain_Noise_Scale=18.0,
    Grain_Noise_Detail=6.0,
    Grain_Noise_Distortion=0.12,

    # ------------------------------------------
    # 色（少し彩度寄り）
    # ------------------------------------------
    Color_Dark=(0.18, 0.12, 0.07, 1.0),
    Color_Light=(0.42, 0.30, 0.20, 1.0),

    # ------------------------------------------
    # Roughness（均質寄り）
    # ------------------------------------------
    Roughness_Dark=0.45,
    Roughness_Light=0.7,

    # ------------------------------------------
    # 凹凸（陰影重視）
    # ------------------------------------------
    Bump_Strength=0.35,
    Bump_Distance=0.08,
):
    current_mode = bpy.context.object.mode

    # =====================================================
    # Texture Coordinate
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeTexCoord",
        texture_node_name="TX_Coord_00",
        node_location=(-1300, 300),
    )

    # =====================================================
    # Mapping
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeMapping",
        texture_node_name="Mapping_00",
        node_location=(-1100, 300),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="TX_Coord_00",
        texture_node_name_in="Mapping_00",
        output_link="Object",
        input_link="Vector",
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Mapping_00",
        element_name="Scale",
        set_value=Mapping_00_Scale,
    )

    # =====================================================
    # 年輪 Noise（低周波）
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeTexNoise",
        texture_node_name="Noise_Ring",
        node_location=(-850, 450),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Mapping_00",
        texture_node_name_in="Noise_Ring",
        output_link="Vector",
        input_link="Vector",
    )

    mtal_cm_lib.node_value_change(mtal_name, "Noise_Ring", "Scale", Ring_Noise_Scale)
    mtal_cm_lib.node_value_change(mtal_name, "Noise_Ring", "Detail", Ring_Noise_Detail)
    mtal_cm_lib.node_value_change(mtal_name, "Noise_Ring", "Distortion", Ring_Noise_Distortion)

    # =====================================================
    # 導管 Noise（高周波）
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeTexNoise",
        texture_node_name="Noise_Grain",
        node_location=(-850, 150),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Mapping_00",
        texture_node_name_in="Noise_Grain",
        output_link="Vector",
        input_link="Vector",
    )

    mtal_cm_lib.node_value_change(mtal_name, "Noise_Grain", "Scale", Grain_Noise_Scale)
    mtal_cm_lib.node_value_change(mtal_name, "Noise_Grain", "Detail", Grain_Noise_Detail)
    mtal_cm_lib.node_value_change(mtal_name, "Noise_Grain", "Distortion", Grain_Noise_Distortion)

    # =====================================================
    # Math：年輪 × 導管
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeMath",
        texture_node_name="Math_Multiply",
        node_location=(-600, 300),
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Math_Multiply",
        element_name="operation",
        set_value="MULTIPLY",
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Noise_Ring",
        texture_node_name_in="Math_Multiply",
        output_link="Fac",
        input_link=0,
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Noise_Grain",
        texture_node_name_in="Math_Multiply",
        output_link="Fac",
        input_link=1,
    )

    # =====================================================
    # Math：中心を -0.5（段差化）
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeMath",
        texture_node_name="Math_Center",
        node_location=(-420, 100),
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Math_Center",
        element_name="operation",
        set_value="SUBTRACT",
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Math_Multiply",
        texture_node_name_in="Math_Center",
        output_link="Value",
        input_link=0,
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Math_Center",
        element_name=1,
        set_value=0.5,
    )

    # =====================================================
    # Math：段差を強制増幅
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeMath",
        texture_node_name="Math_Amplify",
        node_location=(-260, 100),
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Math_Amplify",
        element_name="operation",
        set_value="MULTIPLY",
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Math_Center",
        texture_node_name_in="Math_Amplify",
        output_link="Value",
        input_link=0,
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Math_Amplify",
        element_name=1,
        set_value=6.0,
    )

    # =====================================================
    # ColorRamp：Base Color
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeValToRGB",
        texture_node_name="Color_Ramp_Color",
        node_location=(-250, 450),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Math_Multiply",
        texture_node_name_in="Color_Ramp_Color",
        output_link="Value",
        input_link="Fac",
    )

    mtal_cm_lib.node_color_ramp_setting(
        material_name=mtal_name,
        node_name="Color_Ramp_Color",
        color_0=Color_Dark,
        color_1=Color_Light,
        position_0=0.0,
        position_1=1.0,
        interpolation="EASE",
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Color_Ramp_Color",
        texture_node_name_in="Principled BSDF",
        output_link="Color",
        input_link="Base Color",
    )

    # =====================================================
    # ColorRamp：Roughness
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeValToRGB",
        texture_node_name="Color_Ramp_Rough",
        node_location=(-250, 200),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Math_Multiply",
        texture_node_name_in="Color_Ramp_Rough",
        output_link="Value",
        input_link="Fac",
    )

    mtal_cm_lib.node_color_ramp_setting(
        material_name=mtal_name,
        node_name="Color_Ramp_Rough",
        color_0=(Roughness_Dark,) * 3 + (1.0,),
        color_1=(Roughness_Light,) * 3 + (1.0,),
        position_0=0.0,
        position_1=1.0,
        interpolation="LINEAR",
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Color_Ramp_Rough",
        texture_node_name_in="Principled BSDF",
        output_link="Color",
        input_link="Roughness",
    )

    # =====================================================
    # Bump（★ Blender 5.1 対応）
    # =====================================================
    mtal_cm_lib.add_new_texture(
        material_name=mtal_name,
        texture_name="ShaderNodeBump",
        texture_node_name="Bump_00",
        node_location=(-80, -50),
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Math_Amplify",
        texture_node_name_in="Bump_00",
        output_link="Value",
        input_link="Height",
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Bump_00",
        element_name="Strength",
        set_value=Bump_Strength,
    )

    mtal_cm_lib.node_value_change(
        material_name=mtal_name,
        node_name="Bump_00",
        element_name="Distance",
        set_value=Bump_Distance,
    )

    mtal_cm_lib.node_link_func(
        material_name=mtal_name,
        texture_node_name_out="Bump_00",
        texture_node_name_in="Principled BSDF",
        output_link="Normal",
        input_link="Normal",
    )

    bpy.ops.object.mode_set(mode=current_mode)
