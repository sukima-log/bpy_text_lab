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
import Common.common_top as common_top
from Common.common_top import *
#========================================================================================
# ==================================================================
# = Pre Process
# ==================================================================
modules = common_top.import_submodules(f"Assets.mdl.SAMPLE_MODEL") 
parts = common_top.import_submodules("Assets.parts")

globals().update(modules)

# ==================================================================
# = Modeling
# ==================================================================
#-------------------------------
# Modeling
#-------------------------------
def sukima_logo_mdl(
    sukima_logo=glb.glb_defs.sukima_logo
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[sukima_logo], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=True)):
        # オブジェクト追加
        bpy.ops.mesh.primitive_cube_add(
            size=1                  # 1辺長
        ,   location=(0, 0, 0)      # 配置場所
        ,   scale=(1.0, 1.0, 1.0)   # x, y, y
        )
        # 名前設定
        bpy.context.object.name = sukima_logo
        # サイズ変更
        bpy.ops.transform.resize(
            value=(
                glb.glb_defs.GP_CUBE_SIZE
            ,   glb.glb_defs.GP_CUBE_SIZE
            ,   glb.glb_defs.GP_CUBE_SIZE
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
        # 変数
        line_width_0p1  = glb.glb_defs.GP_CUBE_SIZE/150  # ライン幅
        line_width_0    = glb.glb_defs.GP_CUBE_SIZE/40   # ライン幅
        line_width_1    = glb.glb_defs.GP_CUBE_SIZE/30   # ライン幅
        line_width_2    = glb.glb_defs.GP_CUBE_SIZE/20   # ライン幅
        bump_value      = glb.glb_defs.GP_CUBE_SIZE/100  # 面 移動 値
        #----------------------------------------
        # 縁
        #----------------------------------------
        # ループカット
        ao_l=[
            sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ]
        bl_l=[
            (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[0], obj1_point=2, obj2_name=ao_l[0], obj2_point=0, coordinate="Y"))()
        ,   (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[1], obj1_point=4, obj2_name=ao_l[1], obj2_point=0, coordinate="X"))()
        ,   (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[1], obj1_point=1, obj2_name=ao_l[1], obj2_point=0, coordinate="Z"))()
        ]
        i_l=[
            [0, 0]
        ,   [5, 5]
        ,   [1, 1]
        ]
        s_l=[
            [bl_l[0]-(line_width_0p1),  bl_l[0]-((line_width_0p1)*2)]
        ,   [bl_l[1]-(line_width_0p1),  bl_l[1]-((line_width_0p1)*2)]
        ,   [bl_l[2]-(line_width_0p1),  bl_l[2]-((line_width_0p1)*2)]
        ]
        d_l=[
            [+1 , -1]
        ,   [+1 , +1]
        ,   [+1 , -1]
        ]
        for i in range(len(ao_l)):
            # Mode切り替え
            bpy.ops.object.mode_set(mode='OBJECT')
            mdl_cm_lib.active_object_select(object_name_list=[ao_l[i]])
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bl=bl_l[i]
            mdl_cm_lib.multi_value_loopcut_slide(
                bl=bl
            ,   i_a=i_l[i]
            ,   s_a=s_l[i]
            ,   d_a=d_l[i]
            )
        # 面 移動
        o_l=[
            sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ]
        i_l=[
            15
        ,   26
        ,   46
        ,   48
        ,   42
        ,   45
        ]
        x_l=[
            0
        ,   0
        ,   +bump_value
        ,   -bump_value
        ,   0
        ,   0
        ]
        y_l=[
            0
        ,   0
        ,   0
        ,   0
        ,   +bump_value
        ,   -bump_value
        ]
        z_l=[
            +bump_value
        ,   -bump_value
        ,   0
        ,   0
        ,   0
        ,   0
        ]
        for i in range(len(o_l)):
            mdl_cm_lib.element_select(
                element_list=[i_l[i]]
            ,   select_mode="FACE"
            ,   object_name_list=[o_l[i]]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            # 値を取得（lambdaなら実行）
            x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
            y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
            z_value = z_l[i]() if callable(z_l[i]) else z_l[i]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='GLOBAL'
            )
        # 頂点 移動
        o_l=[
            sukima_logo, sukima_logo, sukima_logo, sukima_logo
        ,   sukima_logo, sukima_logo, sukima_logo, sukima_logo
        ]
        i_l=[
            1, 3, 5, 7
        ,   0, 2, 4, 6
        ]
        x_l=[
            0, 0, 0, 0
        ,   0, 0, 0, 0
        ]
        y_l=[
            0, 0, 0, 0
        ,   0, 0, 0, 0
        ]
        z_l=[
            -bump_value/2, -bump_value/2, -bump_value/2, -bump_value/2
        ,   -bump_value/2, -bump_value/2, -bump_value/2, -bump_value/2
        ]
        for i in range(len(o_l)):
            mdl_cm_lib.element_select(
                element_list=[i_l[i]]
            ,   select_mode="VERT"
            ,   object_name_list=[o_l[i]]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            # 値を取得（lambdaなら実行）
            x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
            y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
            z_value = z_l[i]() if callable(z_l[i]) else z_l[i]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='NORMAL'
            )
        #----------------------------------------
        # 面 Line
        #----------------------------------------
        # ループカット
        ao_l=[
            sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ]
        bl_l=[
            (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[0], obj1_point=27, obj2_name=ao_l[0], obj2_point=22, coordinate="X"))()
        ,   (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[0], obj1_point=20, obj2_name=ao_l[0], obj2_point=22, coordinate="Y"))()
        ,   (lambda:mdl_cm_lib.point_diff_length(obj1_name=ao_l[0], obj1_point=52, obj2_name=ao_l[0], obj2_point=40, coordinate="Z"))()
        ]
        i_l=[
            [31, 31, 31]
        ,   [13, 13, 13]
        ,   [68, 68, 68, 68, 68]
        ]
        s_l=[
            [bl_l[0]-(bl_l[0]*5/11), bl_l[0]-((bl_l[0]*5/11)+(bl_l[0]*5/11/2)), bl_l[0]-((bl_l[0]*5/11)+(bl_l[0]*5/11/2)+(bl_l[0]*5/11/2))]
        ,   [bl_l[1]-(bl_l[1]*5.5/12), bl_l[1]-((bl_l[1]*5.5/12)+(bl_l[1]*2.5/12)), bl_l[1]-((bl_l[1]*5.5/12)+(bl_l[1]*2.5/12)*2)]
        ,   [bl_l[2]-(bl_l[2]*2.0/20), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2+(bl_l[2]*4/20)), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2+(bl_l[2]*4/20)*2)]
        ]
        d_l=[
            [-1, -1, -1]
        ,   [-1, -1, -1]
        ,   [-1, -1, -1, -1, -1]
        ]
        for i in range(len(ao_l)):
            # Mode切り替え
            bpy.ops.object.mode_set(mode='OBJECT')
            mdl_cm_lib.active_object_select(object_name_list=[ao_l[i]])
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bl=bl_l[i]
            mdl_cm_lib.multi_value_loopcut_slide(
                bl=bl
            ,   i_a=i_l[i]
            ,   s_a=s_l[i]
            ,   d_a=d_l[i]
            )
        #----------------------------------------
        # 面 Line 幅
        #----------------------------------------
        o_l=[
            #
            sukima_logo
        ,   sukima_logo
        ,   sukima_logo
            #
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
            #
        ,   sukima_logo
            #
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
            #
        ,   sukima_logo
        ,   sukima_logo
        ]
        e_l=[
            [265, 229, 193, 131]
        ,   [227, 235, 551]
        ,   [148, 172, 244, 246, 532, 550, 552, 555, 557, 564, 566, 568, 569]
        ,   [264, 311, 359, 407, 455, 160, 277, 279, 282]
        ,   [139, 310, 313, 335, 380, 425, 651, 654, 665, 667, 691, 697, 698, 699]
        ,   [632, 633, 654, 770, 774]
        ,   [703, 709, 725, 728, 731]
        ,   [166, 201, 230, 247, 250, 252, 284, 287, 289, 321, 324, 326, 333, 343, 364, 367, 369, 376, 386, 389, 407, 410, 412, 429]
        ,   [131, 227, 257, 263, 271, 272, 273, 285, 317, 349]
        ,   [133, 220, 227, 236, 289, 318, 1038, 1040, 1053, 1055, 1056, 1059, 1081, 1083, 1084, 1089]
        ,   [1116, 1120, 1183, 1189, 1190]
        ,   [115, 143, 144, 145, 146, 147, 148, 166, 176, 177, 178, 192, 193, 194, 197]
        ,   [135, 152, 176, 177, 178, 179, 195, 196, 204, 205, 212, 213, 215, 216, 237, 243, 249, 250, 251, 263, 264, 267, 268, 269, 276]
        ]
        b_l=[
            line_width_1
        ,   line_width_2
        ,   line_width_0
        ,   line_width_0
        ,   line_width_2
        ,   line_width_1
        ,   line_width_0
        ,   line_width_0
        ,   line_width_2
        ,   line_width_0
        ,   line_width_1
        ,   line_width_0
        ,   line_width_0
        ]
        for i in range(len(o_l)):
            # 辺 選択
            mdl_cm_lib.element_select(
                element_list=e_l[i]
            ,   select_mode="EDGE"
            ,   object_name_list=[o_l[i]]
            )
            # 辺 増加 ベベル
            bpy.ops.mesh.bevel(
                offset=b_l[i]           # ベベル オフセット処理、エッジ to エッジ 距離（値が大きいほど面取り幅大）
            ,   offset_pct=0            # オフセット距離 %
            ,   segments=2              # 追加 セグメント数（値が大きいほど滑らか）
            ,   affect='EDGES'          # 辺/頂点
            )
        #----------------------------------------
        # 面 Line 溝
        #----------------------------------------
        common_value = bump_value/4
        o_l=[
            sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ,   sukima_logo
        ]
        i_l=[
            [234, 237, 240, 243, 261, 289, 290, 293, 300, 303, 308, 312, 316, 320, 324, 325, 327, 331, 336, 337, 339, 343, 347, 350, 353, 356, 381, 382, 383, 384]
        ,   [402, 403, 406, 411, 415, 420, 423, 453, 455, 460, 463, 466, 468, 472, 476, 484, 487, 522, 523, 524, 534, 539, 544, 545, 548, 549, 554, 558, 561, 564, 571, 576, 582, 583, 589, 590, 591, 592, 593, 594, 595, 596, 597, 598, 599, 600, 601, 602, 603, 606, 607, 609, 613, 617, 620, 622, 623, 624, 632, 635, 640, 641]
        ,   [685, 686, 689, 694, 695, 698, 713, 714, 717, 720, 725, 726, 729, 734, 735, 738, 748, 749, 752, 757, 762, 766, 770, 775, 780, 785, 790, 795, 799, 803, 807, 810, 813, 816, 819, 822, 825, 828, 831, 834, 837, 840, 843]
        ,   [1155, 1156, 1159, 1164, 1165, 1168, 1173, 1174, 1177, 1187, 1188, 1191, 1196, 1197, 1200, 1205, 1206, 1209, 1224, 1225, 1228, 1232, 1235, 1238, 1241, 1244, 1247, 1250, 1253, 1256, 1259, 1262, 1266, 1271, 1275, 1278]
        ,   [903, 906, 909, 913, 916, 919, 923, 926, 929, 964, 965, 968, 971, 983, 986, 987, 990, 993, 998, 1002, 1005, 1009, 1013, 1017, 1018, 1020, 1024, 1029, 1033, 1037, 1041, 1044, 1046, 1049, 1076, 1077, 1082, 1093, 1098, 1103, 1104, 1107, 1108, 1113, 1117, 1120, 1123, 1131, 1135, 1141, 1142]
        ,   [1329, 1330, 1333, 1338, 1339, 1342, 1345, 1355, 1356, 1359, 1364, 1365, 1368, 1371, 1381, 1382, 1385, 1390, 1391, 1394, 1409, 1410, 1413, 1418, 1419, 1422, 1425, 1440, 1441, 1444, 1447, 1452, 1453, 1456, 1459, 1463, 1466, 1469, 1472, 1475, 1478, 1481, 1484, 1487, 1490, 1493, 1496, 1499, 1502, 1505, 1508, 1511, 1515, 1519, 1522, 1525, 1529, 1533, 1536, 1539]
        ]
        x_l=[
            0
        ,   0
        ,   +common_value
        ,   0
        ,   0
        ,   -common_value
        ]
        y_l=[
            0
        ,   +common_value
        ,   0
        ,   0
        ,   -common_value
        ,   0
        ]
        z_l=[
            -common_value
        ,   0
        ,   0
        ,   +common_value
        ,   0
        ,   0
        ]
        for i in range(len(o_l)):
            mdl_cm_lib.element_select(
                element_list=i_l[i]
            ,   select_mode="EDGE"
            ,   object_name_list=[o_l[i]]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            # 値を取得（lambdaなら実行）
            x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
            y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
            z_value = z_l[i]() if callable(z_l[i]) else z_l[i]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='GLOBAL'
            )
        # 要素選択
        mdl_cm_lib.element_select(
            element_list=["all"]
        ,   select_mode="FACE"
        ,   object_name_list=[sukima_logo]
        )
        # 全ての選択メッシュを外側に向ける
        bpy.ops.mesh.normals_make_consistent(inside=False)

#-------------------------------
# Duplicate
#-------------------------------
def sukima_logo_duplicate(
    sukima_logo=glb.glb_defs.sukima_logo
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[sukima_logo], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT)):
        obj_name=sukima_logo
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        x_l=[
            0
        ,   0
        ,   +(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20))
        ,   +(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20) + glb.glb_defs.GP_CUBE_SIZE)
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20))
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20) + glb.glb_defs.GP_CUBE_SIZE)
        ,   +(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ,   +(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ,   +(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ,   -(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ,   -(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ,   -(glb.glb_defs.GP_CUBE_SIZE/2 + (glb.glb_defs.GP_CUBE_SIZE/40))
        ]
        y_l=[
            0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ,   0
        ]
        z_l=[
            -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10))
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)) + glb.glb_defs.GP_CUBE_SIZE)
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10))
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10))
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10))
        ,   -(glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10))
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)))
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)) + glb.glb_defs.GP_CUBE_SIZE)
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)) + glb.glb_defs.GP_CUBE_SIZE*2)
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)))
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)) + glb.glb_defs.GP_CUBE_SIZE)
        ,   -((glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/20)) + glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE + (glb.glb_defs.GP_CUBE_SIZE/10)) + glb.glb_defs.GP_CUBE_SIZE*2)
        ]
        r_l=[
            -90
        ,   -180
        ,   -90
        ,   -180
        ,   +90
        ,   +180
        ,   -90
        ,   -180
        ,   +90
        ,   +90
        ,   +180
        ,   -90
        ]
        o_l=[
            "Z"
        ,   "Z"
        ,   "X"
        ,   "X"
        ,   "X"
        ,   "X"
        ,   "Z"
        ,   "Z"
        ,   "Z"
        ,   "Z"
        ,   "Z"
        ,   "Z"
        ]
        for i in range(len(x_l)):
            # アクティブオブジェクト
            mdl_cm_lib.active_object_select(object_name_list=[obj_name])
            # 「Shift」+「Ｄ」：オブジェクト複製
            bpy.ops.object.duplicate_move(
                OBJECT_OT_duplicate={
                    "linked":False              # オリジナルのオブジェクトにリンクされない（編集してもオリジナルに影響しない）
                ,   "mode":'TRANSLATION'        # 複製後にオブジェクトが移動
                }, 
                TRANSFORM_OT_translate={
                    "value":(0, 0, 0)
                ,   "orient_type":'GLOBAL'
            })
            # 値を取得（lambdaなら実行）
            x_value = x_l[i]() if callable(x_l[i]) else x_l[i]
            y_value = y_l[i]() if callable(y_l[i]) else y_l[i]
            z_value = z_l[i]() if callable(z_l[i]) else z_l[i]
            # 複製されたオブジェクトをアクティブオブジェクトとして取得
            duplicated_element = bpy.context.active_object
            # 名前変更
            duplicated_element.name = obj_name + "_" + str(i)
            # オブジェクト回転
            mdl_cm_lib.object_rotate_func(
                object_list=[obj_name + "_" + str(i)]
            ,   transform_pivot_point="INDIVIDUAL_ORIGINS"
            ,   radians_num=r_l[i]
            ,   orient_axis=o_l[i]
            ,   orient_type="GLOBAL"
            )
            # オブジェクト移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='GLOBAL'
            )
        # ------------------------------------
        # オブジェクト結合
        # ------------------------------------
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        temp_list=[obj_name]
        for i in range(len(x_l)):
            temp_list.append(obj_name + "_" + str(i))
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(
            object_name_list=temp_list
        )
        # オブジェクト結合
        bpy.ops.object.join()
        # 名前変更
        bpy.context.object.name = obj_name
        # ----------------------------------
        # オブジェクト全適用
        # ----------------------------------
        object_list=[obj_name]
        # 全適用
        # オブジェクト位置, サイズ, 回転, 中心点初期化
        for i in range(len(object_list)):
            mdl_cm_lib.initialize_transform_apply(
                object_name_list=[object_list[i]]
            )
