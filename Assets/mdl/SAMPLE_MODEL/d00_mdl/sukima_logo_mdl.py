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
modules = cm_lib.import_submodules(f"Assets.mdl.SAMPLE_MODEL") 
parts = cm_lib.import_submodules("Assets.parts")

globals().update(modules)

# ==================================================================
# = Modeling
# ==================================================================
#-------------------------------
# Modeling
#-------------------------------
def sukima_logo_mdl(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT, gen_flag=True)):
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        # オブジェクト追加
        bpy.ops.mesh.primitive_cube_add(
            size=1                  # 1辺長
        ,   location=(0, 0, 0)      # 配置場所
        ,   scale=(1.0, 1.0, 1.0)   # x, y, y
        )
        # 名前設定
        bpy.context.object.name = obj_name
        # カスタムID 初期化
        mdl_cm_lib.init_assign_all_ids(obj_name)
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
        # 縁部分
        #----------------------------------------
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])
        # Mode切り替え
        bpy.ops.object.mode_set(mode='EDIT')
        bl_l=[
            (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=2, obj2_name=obj_name, obj2_point=8, coordinate="Y"))()
        ,   (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=4, obj2_name=obj_name, obj2_point=8, coordinate="X"))()
        ,   (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=1, obj2_name=obj_name, obj2_point=8, coordinate="Z"))()
        ]
        l_l=[
            [[12,   12],    [bl_l[0]-(line_width_0p1),    bl_l[0]-((line_width_0p1)*2)],  [+1,    -1],  ]
        ,   [[5,    5],     [bl_l[1]-(line_width_0p1),    bl_l[1]-((line_width_0p1)*2)],  [-1,    -1],  ]
        ,   [[1,    1],     [bl_l[2]-(line_width_0p1),    bl_l[2]-((line_width_0p1)*2)],  [-1,    +1],  ]
        ]
        for i in range(len(l_l)):
            # ループカット
            mdl_cm_lib.multi_value_loopcut_slide_customid(
                bl=bl_l[0]
            ,   cid_list          =l_l[i][0]
            ,   slide_list        =l_l[i][1]
            ,   direction_list    =l_l[i][2]
            )
        # 面 移動 (四方面移動 -> 縁部分 角とり)
        l_l=[
            [[26],  [0, 0, +bump_value],]
        ,   [[27],  [0, 0, -bump_value],]
        ,   [[47],  [+bump_value, 0, 0],]
        ,   [[49],  [-bump_value, 0, 0],]
        ,   [[45],  [0, +bump_value, 0],]
        ,   [[43],  [0, -bump_value, 0],]
        ]
        for i in range(len(l_l)):
            mdl_cm_lib.element_select_customid(
                element_list=l_l[i][0]
            ,   select_mode="FACE"
            ,   object_name_list=[obj_name]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            # 値を取得（lambdaなら実行）
            x_value = l_l[i][1][0]() if callable(l_l[i][1][0]) else l_l[i][1][0]
            y_value = l_l[i][1][1]() if callable(l_l[i][1][1]) else l_l[i][1][1]
            z_value = l_l[i][1][2]() if callable(l_l[i][1][2]) else l_l[i][1][2]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='GLOBAL'
            )
        # 頂点 移動 (縁 角部分 角とり 法線方向 (NORMAL))
        l_l=[
            [[1],   [0, 0, -bump_value/2],  ]
        ,   [[3],   [0, 0, -bump_value/2],  ]
        ,   [[5],   [0, 0, -bump_value/2],  ]
        ,   [[7],   [0, 0, -bump_value/2],  ]
        ,   [[8],   [0, 0, -bump_value/2],  ]
        ,   [[2],   [0, 0, -bump_value/2],  ]
        ,   [[4],   [0, 0, -bump_value/2],  ]
        ,   [[6],   [0, 0, -bump_value/2],  ]
        ]
        for i in range(len(l_l)):
            mdl_cm_lib.element_select_customid(
                element_list=l_l[i][0]
            ,   select_mode="VERT"
            ,   object_name_list=[obj_name]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='VERT')
            # 値を取得（lambdaなら実行）
            x_value = l_l[i][1][0]() if callable(l_l[i][1][0]) else l_l[i][1][0]
            y_value = l_l[i][1][1]() if callable(l_l[i][1][1]) else l_l[i][1][1]
            z_value = l_l[i][1][2]() if callable(l_l[i][1][2]) else l_l[i][1][2]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='NORMAL'
            )
        #----------------------------------------
        # 面 Line ループカット
        #----------------------------------------
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])
        # Mode切り替え
        bpy.ops.object.mode_set(mode='EDIT')
        bl_l=[
            (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=30, obj2_name=obj_name, obj2_point=22, coordinate="X"))()
        ,   (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=30, obj2_name=obj_name, obj2_point=31, coordinate="Y"))()
        ,   (lambda:mdl_cm_lib.point_diff_length_customid(obj1_name=obj_name, obj1_point=34, obj2_name=obj_name, obj2_point=46, coordinate="Z"))()
        ]
        l_l=[
            [[52, 52, 52],    [bl_l[0]-(bl_l[0]*5/11), bl_l[0]-((bl_l[0]*5/11)+(bl_l[0]*5/11/2)), bl_l[0]-((bl_l[0]*5/11)+(bl_l[0]*5/11/2)+(bl_l[0]*5/11/2))],  [+1, -1, -1],  ]
        ,   [[57, 188, 226],  [bl_l[1]-(bl_l[1]*5.5/12), bl_l[1]-((bl_l[1]*5.5/12)+(bl_l[1]*2.5/12)), bl_l[1]-((bl_l[1]*5.5/12)+(bl_l[1]*2.5/12)*2)],  [-1, -1, -1],  ]
        ,   [[95, 95, 95, 95, 95],  [bl_l[2]-(bl_l[2]*2.0/20), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2+(bl_l[2]*4/20)), bl_l[2]-((bl_l[2]*2.0/20)+(bl_l[2]*3.8/20)*2+(bl_l[2]*4/20)*2)],  [-1, -1, -1, -1, -1],]
        ]
        for i in range(len(l_l)):
            # ループカット
            mdl_cm_lib.multi_value_loopcut_slide_customid(
                bl=bl_l[0]
            ,   cid_list          =l_l[i][0]
            ,   slide_list        =l_l[i][1]
            ,   direction_list    =l_l[i][2]
            )
        #----------------------------------------
        # 面 Line 幅 付け ベベル
        #----------------------------------------
        l_l=[
            # 上面
            [line_width_1, [265, 229, 193, 128]]
        ,   [line_width_2, [241, 243, 245]]
        ,   [line_width_0, [175, 270, 565, 566, 234, 198]]
        ,   [line_width_0, [151, 268, 570, 571, 196, 232]]
        ,   [line_width_0, [281]]
            # 前面
        ,   [line_width_0, [306, 353, 401, 449, 497, 169]]
        ,   [line_width_2, [375, 373, 679, 696, 369, 371]]
        ,   [line_width_2, [145, 304, 447, 495, 731, 730, 399, 351]]
        ,   [line_width_1, [302, 349]]
        ,   [line_width_0, [419]]
        ,   [line_width_0, [771, 770]]
        ,   [line_width_0, [728]]
        ,   [line_width_0, [323, 797, 806, 327, 325, 837, 828, 760, 781]]
            # 左面
        ,   [line_width_0, [312, 359, 407, 455, 503, 271]]
        ,   [line_width_0, [310, 357, 405, 453, 501, 235]]
        ,   [line_width_0, [307, 354, 402, 450, 498, 199]]
        ,   [line_width_0, [412, 460, 508]]
        ,   [line_width_0, [458, 1005, 992, 457]]
        ,   [line_width_0, [409]]
            # 右面
        ,   [line_width_0, [309, 356, 404, 452, 500, 252, 477, 478, 479, 480, 525, 526, 527, 528]]
        ,   [line_width_0, [499, 1131, 1130, 216]]
        ,   [line_width_0, [335, 336, 383, 384, 431, 432]]
        ,   [line_width_0, [1278, 1277, 1276, 1275, 311, 358, 406]]
            # 裏面
        ,   [line_width_2, [303, 350, 398, 446, 494, 156]]
        ,   [line_width_0, [305, 352, 400, 448, 496, 180]]
        ,   [line_width_0, [328, 1367, 1350, 326, 1405, 1388, 322, 324]]
        ,   [line_width_2, [376, 374]]
        ,   [line_width_0, [348]]
        ,   [line_width_0, [372, 1404, 1387, 370]]
        ,   [line_width_0, [420, 1403, 1386, 418]]
            # 下面
        ,   [line_width_0, [276, 278, 280, 282]]
        ,   [line_width_0, [123, 194, 230]]
        ,   [line_width_0, [204, 206, 208]]
        ,   [line_width_0, [240, 242, 244]]
        ,   [line_width_0, [197]]
        ,   [line_width_0, [195]]
        ]
        for i in range(len(l_l)):
            # 要素選択
            mdl_cm_lib.element_select_customid(
                element_list=l_l[i][1]
            ,   select_mode="EDGE"
            ,   object_name_list=[obj_name]
            )
            # メッシュベベル
            bpy.ops.mesh.bevel(
                offset=l_l[i][0]        # ベベルのオフセット処理、エッジからエッジまでの距離（値が大きいほど面取り幅が大きい）
            ,   offset_pct=0            # オフセット距離を%で指定
            ,   segments=2              # ベベルに追加するセグメント数（値が大きいほど滑らかになる）
            ,   affect='EDGES'          # エッジに適用されるか頂点に適用されるか指定
            )
            # 選択メッシュ カスタムID 0
            mdl_cm_lib.zero_selected_elements_customid(obj_name)
            # 重複IDを座標順で修正
            mdl_cm_lib.fix_duplicate_ids(obj_name)
        #----------------------------------------
        # 面 Line 溝
        #----------------------------------------
        common_value = bump_value/2
        l_l=[
            [[0, 0, -common_value], [541, 542, 543, 544, 578, 596, 601, 607, 598, 590, 599, 600, 597, 563, 634, 639, 645, 636, 628, 637, 635, 638, 568, 573, 667, 657, 662, 537]]
        ,   [[0, +common_value, 0], [684, 689, 686, 685, 738, 720, 721, 688, 687, 764, 766, 765, 779, 768, 767, 733, 800, 736, 812, 822, 817, 756, 826, 769, 844, 854, 849, 758, 856, 861, 893, 891, 894, 896, 901, 886, 876, 868, 871, 869, 866, 881, 825, 824, 802, 801, 832, 848]]
        ,   [[+common_value, 0, 0], [921, 926, 925, 924, 923, 922, 959, 964, 963, 962, 961, 960, 997, 1002, 1001, 1000, 1029, 1026, 1023, 1038, 1044, 1041, 1084, 1071, 1074, 1072, 1069, 1064, 1079, 999, 998, 1097, 1092]]
        ,   [[0, 0, +common_value], [1554, 1559, 1564, 1569, 1589, 1586, 1587, 1588, 1620, 1605, 1610, 1615, 1643, 1633, 1628, 1638, 1650, 1652, 1651, 1663, 1665, 1664]]
        ,   [[0, -common_value, 0], [1354, 1357, 1356, 1355, 1392, 1393, 1454, 1441, 1444, 1442, 1439, 1449, 1426, 1429, 1427, 1424, 1419, 1434, 1359, 1358, 1397, 1462, 1472, 1467, 1486, 1484, 1485, 1470, 1518, 1505, 1508, 1506, 1503, 1498, 1513, 1349, 1396, 1546, 1533, 1536, 1534, 1531, 1526, 1541, 1348, 1395, 1394]]
        ,   [[-common_value, 0, 0], [1166, 1176, 1155, 1165, 1162, 1152, 1173, 1163, 1161, 1170, 1169, 1168, 1167, 1128, 1138, 1196, 1206, 1164, 1203, 1193, 1229, 1221, 1227, 1232, 1226, 1225, 1228, 1135, 1125, 1256, 1253, 1250, 1280, 1265, 1313, 1310, 1319, 1327, 1318, 1307, 1316, 1324, 1315, 1320, 1317, 1314, 1286, 1271, 1283, 1268]]
        ]
        for i in range(len(l_l)):
            mdl_cm_lib.element_select_customid(
                element_list=l_l[i][1]
            ,   select_mode="EDGE"
            ,   object_name_list=[obj_name]
            )
            # Mode切り替え
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            # 値を取得（lambdaなら実行）
            x_value = l_l[i][0][0]() if callable(l_l[i][0][0]) else l_l[i][0][0]
            y_value = l_l[i][0][1]() if callable(l_l[i][0][1]) else l_l[i][0][1]
            z_value = l_l[i][0][2]() if callable(l_l[i][0][2]) else l_l[i][0][2]    
            # 移動
            bpy.ops.transform.translate(
                value=(x_value, y_value, z_value)
            ,   orient_type='GLOBAL'
            )
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=["all"]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # 全ての選択メッシュを外側に向ける
        bpy.ops.mesh.normals_make_consistent(inside=False)

#-------------------------------
# Duplicate
#-------------------------------
def sukima_logo_duplicate(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT)):
        obj_name=obj_name
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
        mm_cm_lib.join_objects(
            obj_list=temp_list
        ,   join_name=obj_name
        )
        # 重複IDを座標順で修正
        mdl_cm_lib.fix_duplicate_ids(obj_name)
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
