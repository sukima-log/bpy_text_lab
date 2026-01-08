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

# =====================================================
# シーム マーク
# =====================================================
def sukima_logo_mark_seam(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT)):
        # ビューへ切り替え
        mdl_cm_lib.change_preview(key="MATERIAL")
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
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
        # ----------------------------------
        # シーム(切れ目を入れる)
        # ----------------------------------
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='EDGE')
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                40, 41, 47, 48, 57, 118, 83, 90, 92, 93, 94, 95, 119, 115, 120, 135, 159, 160, 185
                , 186, 224, 260, 262, 264, 294, 295, 296, 300, 341, 342, 343, 391, 440, 441, 443, 488
                , 489, 490, 491, 529, 553, 554, 555, 556, 111, 112, 188, 226, 530, 580, 612, 585, 617
                , 616, 584, 613, 581, 51, 52, 562, 564, 618, 650, 623, 619, 651, 622, 165, 141, 166, 142
                , 572, 567, 574, 569, 661, 663, 531, 654, 532, 655, 669, 701, 674, 671, 670, 702, 78, 102
                , 710, 711, 737, 715, 716, 392, 673, 347, 395, 672, 745, 785, 787, 746, 786, 788, 161, 138
                , 162, 729, 732, 117, 137, 739, 734, 818, 816, 704, 748, 703, 747, 838, 782, 780, 847, 725
                , 749, 860, 862, 900, 902, 885, 887, 877, 880, 882, 297, 810, 344, 809, 705, 706, 751, 752
                , 793, 794, 840, 833, 908, 939, 913, 938, 912, 911, 910, 909, 255, 256, 972, 946, 977, 951
                , 976, 950, 975, 949, 974, 973, 219, 220, 1010, 984, 1015, 989, 1014, 988, 1013, 74, 190, 98
                , 191, 1039, 1037, 1043, 1045, 1040, 1042, 937, 389, 437, 936, 485, 935, 934, 89, 1063, 1065
                , 1078, 1080, 486, 985, 947, 948, 1011, 1012, 1091, 1093, 390, 987, 438, 986, 1140, 1182, 1149
                , 1148, 1147, 1146, 1129, 1139, 1197, 1195, 1207, 1205, 1143, 1185, 1204, 1202, 1194, 1192, 189
                , 228, 484, 439, 487, 88, 91, 1215, 1236, 1239, 1218, 107, 1124, 192, 1134, 1137, 1136, 1127, 1126
                , 1279, 1264, 293, 340, 1191, 1190, 388, 1189, 436, 1188, 1303, 1336, 1300, 1333, 1297, 1330, 1287
                , 263, 227, 1272, 1270, 1285, 1269, 1284, 1267, 1282, 1266, 1281, 1369, 1337, 1371, 1370, 1338, 143
                , 144, 1407, 1375, 1408, 1376, 79, 167, 103, 168, 1455, 1450, 1418, 1420, 1433, 1435, 298, 299
                , 1380, 1374, 1342, 1412, 1471, 1466, 345, 393, 1372, 1373, 1479, 1491, 1448, 1468, 1453, 1473
                , 1497, 1499, 1512, 1514, 346, 1379, 1341, 1411, 1525, 1527, 1540, 1542, 394, 442, 1377, 1378
                , 1340, 1339, 1409, 1410, 1553, 1555, 1558, 1560, 1565, 1570, 223, 259, 261, 1596, 1597, 1598
                , 116, 136, 1563, 1568, 1604, 1609, 1614, 56, 1576, 1634, 1629, 1639, 187, 225, 1578, 1577, 1657
                , 1645, 1606, 1627, 1670, 1658, 1611, 1616, 1637, 1632
            ]
        ,   select_mode="EDGE"
        ,   object_name_list=[obj_name]
        )
        # # エッジループを選択
        # # ループ選択(Alt+Click) / 一周選択
        # bpy.ops.mesh.loop_multi_select(ring=False)

        # シームをマーク
        bpy.ops.mesh.mark_seam(clear=False)

        # ----------------------------------
        # ベースマテリアル追加
        # ----------------------------------
        # アクティブオブジェクト
        mdl_cm_lib.active_object_select(object_name_list=[obj_name])
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=glb.glb_defs.MT_SUKIMA_LOGO_BASE)
        # -----------------------
        # 黒
        # -----------------------
        mtl_name = glb.glb_defs.MT_SUKIMA_LOGO_BLACK
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                31, 32, 33, 34, 17, 5, 10, 20, 35, 37, 13, 22, 38, 21, 56, 19, 18, 39, 58, 41, 4, 9, 150, 153, 154
                , 156, 7, 15, 2, 3, 8, 6, 16, 65, 1, 66, 77, 86, 87, 29, 28, 96, 93, 122, 138, 134, 130, 181, 183, 187
                , 202, 230, 232, 237, 242, 244, 249, 251, 53, 51, 48, 46, 44, 270, 272, 271, 269, 265, 273, 274, 275, 276
                , 60, 61, 277, 278, 286, 285, 92, 126, 266, 294, 296, 295, 293, 287, 297, 292, 302, 299, 289, 300, 290, 301
                , 291, 298, 288, 25, 24, 279, 280, 310, 312, 311, 309, 303, 313, 308, 315, 305, 316, 306, 304, 314, 307, 80
                , 68, 81, 69, 281, 283, 282, 284, 324, 323, 319, 320, 321, 322, 267, 268, 317, 318, 332, 334, 333, 331, 325
                , 335, 330, 327, 326, 336, 42, 23, 356, 355, 341, 342, 353, 345, 346, 196, 184, 201, 329, 328, 367, 365, 357
                , 369, 371, 358, 370, 373, 372, 82, 72, 84, 351, 380, 382, 381, 379, 62, 70, 354, 352, 385, 386, 390, 389, 388
                , 387, 338, 337, 360, 359, 394, 396, 395, 393, 368, 366, 374, 399, 400, 404, 403, 401, 402, 347, 348, 350, 362
                , 361, 426, 425, 405, 406, 407, 408, 419, 420, 421, 422, 423, 424, 417, 418, 413, 414, 411, 412, 409, 410, 415
                , 416, 148, 189, 339, 340, 364, 363, 378, 377, 383, 384, 391, 392, 397, 442, 440, 439, 441, 427, 438, 432, 437
                , 431, 430, 429, 428, 127, 129, 458, 456, 455, 457, 449, 443, 454, 448, 453, 447, 452, 446, 451, 450, 109, 111
                , 474, 472, 471, 473, 465, 459, 470, 464, 469, 463, 468, 36, 91, 14, 101, 491, 492, 489, 490, 487, 488, 480, 479
                , 478, 477, 476, 475, 482, 481, 485, 486, 483, 484, 204, 229, 252, 54, 436, 435, 434, 433, 504, 503, 501, 502, 497
                , 498, 495, 496, 493, 494, 499, 500, 246, 444, 445, 467, 466, 460, 510, 509, 507, 508, 505, 506, 198, 235, 461
                , 462, 516, 518, 517, 515, 522, 521, 513, 514, 546, 536, 535, 545, 520, 519, 511, 512, 532, 542, 543, 533, 531
                , 541, 540, 539, 538, 537, 526, 530, 554, 553, 558, 557, 534, 544, 556, 555, 552, 551, 94, 118, 248, 250, 231, 50
                , 52, 560, 559, 565, 566, 563, 569, 562, 568, 561, 567, 570, 564, 11, 102, 529, 525, 528, 524, 523, 527, 576, 575
                , 574, 573, 572, 571, 581, 582, 579, 580, 577, 578, 589, 583, 152, 185, 200, 233, 549, 550, 548, 547, 595, 596, 605
                , 604, 602, 611, 601, 610, 599, 608, 598, 607, 603, 612, 600, 609, 597, 606, 132, 124, 594, 588, 587, 593, 592, 586
                , 585, 591, 590, 584, 622, 620, 619, 621, 623, 613, 625, 624, 614, 75, 73, 638, 636, 635, 637, 639, 629, 640, 630, 40
                , 88, 30, 90, 663, 664, 646, 645, 662, 657, 658, 655, 656, 660, 651, 652, 649, 650, 647, 648, 653, 654, 155, 146
                , 628, 618, 644, 634, 671, 672, 666, 665, 669, 667, 203, 182, 627, 626, 677, 675, 674, 676, 673, 678, 659, 661, 668
                , 670, 680, 679, 689, 690, 685, 686, 683, 684, 681, 682, 687, 688, 191, 617, 643, 633, 692, 691, 701, 702, 697, 698
                , 695, 696, 693, 694, 699, 700, 194, 239, 616, 615, 642, 641, 632, 631, 713, 714, 704, 703, 705, 706, 707, 708, 710
                , 712, 131, 125, 135, 718, 720, 721, 719, 722, 723, 724, 57, 76, 711, 709, 726, 725, 733, 734, 727, 729, 731, 12, 715
                , 736, 735, 743, 744, 740, 738, 742, 97, 121, 716, 717, 746, 748, 749, 747, 750, 745, 728, 737, 752, 754, 755, 753, 756
                , 751, 730, 732, 739, 741
            ]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=mtl_name)
        # ベース色変更
        mtal_cm_lib.node_value_change(
            material_name=mtl_name
        ,   node_name="Principled BSDF"
        ,   element_name="Base Color"
        ,   set_value=mtal_cm_lib.hex_to_rgba(hex_color="#000000", alpha=1.0)
        )
        # -----------------------
        # オレンジ
        # -----------------------
        mtl_name = glb.glb_defs.MT_SUKIMA_LOGO_ORANGE
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                238, 243, 64, 139, 59, 103, 117, 67, 106, 210, 349, 175, 168, 110, 169, 216, 217, 264, 163, 100, 174
                , 262, 211, 245, 172, 213, 74, 228, 253, 195, 205, 176, 104
            ]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=mtl_name)
        # ベース色変更
        mtal_cm_lib.node_value_change(
            material_name=mtl_name
        ,   node_name="Principled BSDF"
        ,   element_name="Base Color"
        ,   set_value=mtal_cm_lib.hex_to_rgba(hex_color="#ed5b00", alpha=1.0)
        )
        # -----------------------
        # 灰色
        # -----------------------
        mtl_name = glb.glb_defs.MT_SUKIMA_LOGO_GRAY
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                227, 254, 63, 136, 120, 144, 112, 142, 206, 71, 208, 225, 256, 376, 160, 398, 151, 186, 199, 263, 261, 170, 45, 257, 180, 224, 27, 78, 85
            ]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=mtl_name)
        # ベース色変更
        mtal_cm_lib.node_value_change(
            material_name=mtl_name
        ,   node_name="Principled BSDF"
        ,   element_name="Base Color"
        ,   set_value=mtal_cm_lib.hex_to_rgba(hex_color="#919191", alpha=1.0)
        )
        # -----------------------
        # 黄緑
        # -----------------------
        mtl_name = glb.glb_defs.MT_SUKIMA_LOGO_LIGHT_GREEN
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                149, 188, 197, 26, 98, 114, 145, 43, 240, 241, 343, 344, 192, 193, 162, 166, 171, 214, 128, 219
                , 222, 164, 173, 212, 221, 236, 47, 99, 215, 147, 157, 209, 207, 133, 143, 140, 141, 113, 115, 116, 107
            ]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=mtl_name)
        # ベース色変更
        mtal_cm_lib.node_value_change(
            material_name=mtl_name
        ,   node_name="Principled BSDF"
        ,   element_name="Base Color"
        ,   set_value=mtal_cm_lib.hex_to_rgba(hex_color="#50d875", alpha=1.0)
        )
        # -----------------------
        # 緑
        # -----------------------
        mtl_name = glb.glb_defs.MT_SUKIMA_LOGO_GREEN
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=[
                79, 108, 83, 258, 223, 158, 179, 177, 375, 49, 234, 247, 259, 119, 137, 260, 218
                , 220, 167, 165, 89, 255, 161, 159, 190, 178, 226, 55, 95, 123, 105
            ]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # マテリアル追加
        mtal_cm_lib.add_new_material(material_name=mtl_name)
        # ベース色変更
        mtal_cm_lib.node_value_change(
            material_name=mtl_name
        ,   node_name="Principled BSDF"
        ,   element_name="Base Color"
        ,   set_value=mtal_cm_lib.hex_to_rgba(hex_color="#199f93", alpha=1.0)
        )

        # # ビューへ切り替え
        # mdl_cm_lib.change_preview(key="SOLID")



# =====================================================
# UV展開
# =====================================================
def sukima_logo_uv_unwrap(
    obj_name
):
    if (mm_cm_lib.glb_exist_obj_chk(obj_list=[obj_name], EXIST_FLAG_DICT=glb.glb_defs.EXIST_FLAG_DICT)):
        # ビューへ切り替え
        mdl_cm_lib.change_preview(key="MATERIAL")
        # Mode切り替え
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_mode(type='FACE')
        # ----------------------------------
        # UV展開
        # ----------------------------------
        # 要素選択
        mdl_cm_lib.element_select_customid(
            element_list=["all"]
        ,   select_mode="FACE"
        ,   object_name_list=[obj_name]
        )
        # UV 展開
        bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0)
        # bpy.ops.uv.smart_project(angle_limit=math.radians(89))
        # UV Editor内のすべてのUVを選択
        bpy.ops.uv.select_all(action='SELECT')
        # UVの回転を揃える
        bpy.ops.uv.align_rotation()
        # アイランドのスケールを平均化
        bpy.ops.uv.average_islands_scale()
        # アイランドをパックして整理
        bpy.ops.uv.pack_islands(rotate=True, margin=0.02) # margin Bake向け 0.01, Default: 0.001
        # UV展開後にストレッチを最小化
        bpy.ops.uv.minimize_stretch()

        # # ビューへ切り替え
        # mdl_cm_lib.change_preview(key="SOLID")
