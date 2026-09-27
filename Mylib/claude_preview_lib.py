"""
Claude Code 用プレビュー出力ライブラリ (拡張版)
============================================================

役割:
    Blender ヘッドレス実行 (./Tools/run_main_for_claude.sh) の終端で呼ばれ
    現在のシーンを複数アングルからレンダリング + 数値検証して出力する。
    Claude Code が画像と数値情報を Read ツールで読み取り、モデリング結果の
    妥当性を判定する。

出力先 (Output Path):
    <git_root>/Output/preview/<project_name>/

【全景画像 (6 アングル)】
    front.png      : 正面     (-Y 方向から見る、正投影)
    back.png       : 背面     (+Y 方向から見る、正投影)
    side_right.png : 右側面   (+X 方向から見る、正投影)
    side_left.png  : 左側面   (-X 方向から見る、正投影)
    top.png        : 上面     (+Z 方向から見下ろす、正投影)
    persp.png      : 斜め45度 (汎用パース)

【一次形状評価用シルエット (6 アングル)】
    silhouette_<view>.png : 全景と同じカメラ、透明背景、完全不透明の単色材質。
                            色抽出を介さず alpha を形状比較に使用する。

【ワイヤーフレーム/トポロジ確認】
    wireframe.png      : 全体ワイヤー (Wireframe modifier 一時適用)
    wireframe_top.png  : 真上ワイヤー (上面の閉じを確認)

【クローズアップ画像 (シーンを上下半身/側面で切り取り)】
    closeup_upper.png  : 全体の上 60% (塊根上端〜葉束の確認に最適)
    closeup_lower.png  : 全体の下 60% (鉢〜土の確認に最適)
    closeup_left.png   : 左側面拡大
    closeup_right.png  : 右側面拡大

【個別オブジェクトレンダ (E)】
    single_<obj_name>.png : 各メッシュを単独でレンダリング
                            他オブジェクトを hide_render = True で隠して撮影
                            (各メッシュ固有の問題を分離して確認可能)

【数値レポート】
    info.json           : シーン統計 (オブジェクト数/頂点数/面数/BB/マテリアル)
    check_report.json   : メッシュ検証結果
                          (manifold/open_hole/隣接メッシュZ隙間/重なり等)

レンダリングエンジン:
    既定: BLENDER_EEVEE_NEXT (Blender 5.0系の高速エンジン)
        失敗時は BLENDER_EEVEE / BLENDER_WORKBENCH にフォールバック

============================================================
"""

import bpy
import bmesh
import os
import json
import math
import colorsys
from collections import Counter
from datetime import datetime
from mathutils import Vector
from mathutils.bvhtree import BVHTree


# ============================================================
# プレビュー出力エントリポイント
# ============================================================
def render_preview_for_claude(
    project_name
,   git_root
,   resolution = (1280, 1280)
,   reference_ratios = None
,   semantic_region_closeups = None
):
    """
    現在のシーンを複数アングル + クローズアップ + 個別オブジェクトでレンダ
    + 数値検証レポートを出力する

    Input:
        project_name      (str): プロジェクト名 (例: "BONSAI_ASSETS")
                                 出力先サブディレクトリ名として使われる
        git_root          (str): Git リポジトリルートの絶対パス
        resolution        (tuple[int, int]): 出力解像度 (横, 縦) 既定 1280x1280
        reference_ratios  (dict | None): 参考画像から計測したパーツ比率
            形式:
                {
                    "reference_part":   "pot",   # 比率の基準 (= 1.0)
                    "reference_dim":    "diameter",  # diameter / height / max
                    "parts": {
                        "pot":    { "match": "pot$",     "diameter": 1.0, "height": 0.65 },
                        "caudex": { "match": "caudex$",  "diameter": 0.68, "height": 0.51 },
                        "branch": { "match": "branch$",  "length":   0.34, "diameter": 0.11 },
                        ...
                    }
                }
            これを渡すと check_report.json 内の size_ratios.expected_vs_actual に
            「参考画像比率」と「実モデル比率」と「差分(%)」が出力される。
            None なら従来通り「最大bbox基準の相対比率」のみ。

    Output:
        None (副作用: <git_root>/Output/preview/<project_name>/ に画像と JSON 出力)
    """
    output_dir = os.path.join(git_root, "Output", "preview", project_name)
    os.makedirs(output_dir, exist_ok=True)

    # ----------------------------------------------------------------
    # 数値情報収集 (画像生成前にまず書き出す。途中失敗しても残る)
    # ----------------------------------------------------------------
    scene_bb = _compute_scene_bounding_box()
    info = _collect_scene_info(project_name=project_name, scene_bb=scene_bb)
    with open(os.path.join(output_dir, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    # check_report.json (A: 数値検証レポート)
    check = _generate_check_report(
        project_name     = project_name
    ,   reference_ratios = reference_ratios
    ,   scene_bb         = scene_bb
    )
    # B-2: 参考画像比較は check_report に後追加するので、ここでは保留
    check_first_pass_path = os.path.join(output_dir, "check_report.json")
    with open(check_first_pass_path, "w", encoding="utf-8") as f:
        json.dump(check, f, ensure_ascii=False, indent=2)

    # ----------------------------------------------------------------
    # レンダ設定の保存 (最後に復元)
    # ----------------------------------------------------------------
    scene = bpy.context.scene
    saved = {
        "engine":         scene.render.engine
    ,   "res_x":          scene.render.resolution_x
    ,   "res_y":          scene.render.resolution_y
    ,   "filepath":       scene.render.filepath
    ,   "file_format":    scene.render.image_settings.file_format
    ,   "camera":         scene.camera
    ,   "shading":        scene.display.shading.type
    ,   "view_transform": scene.view_settings.view_transform
    ,   "look":           scene.view_settings.look
    ,   "exposure":       scene.view_settings.exposure
    ,   "film_transparent": scene.render.film_transparent
    ,   "material_override": bpy.context.view_layer.material_override
    }
    # マテリアル評価のため view transform を Standard (線形) に切替える。
    # デフォルトの "AgX" / "Filmic" は HDR シーン向けに 暗色を 明るめに、 明色を 暗めに
    # 補正するため、 BSDF.Base Color が 0.2 程度の マテリアルが 視覚的に 0.6-0.7 程度に
    # 見え 「ほぼ白」 と誤認しやすい。 Standard は補正なしの線形表示。
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look           = 'None'
    scene.view_settings.exposure       = 0.0
    saved_hide_render = {obj.name: obj.hide_render for obj in scene.objects}

    # シーンに既存の LIGHT を一時的に hide_render する。
    # 各 ASSETS の main.py は サンプル用 base_light を energy=50000 などの強い値で
    # シーンに作る習慣があり、 これが preview 専用の弱い sun と共存すると過剰露光に
    # なる (マテリアル評価不能)。 preview の間だけ hide_render し、 後で復元する。
    saved_existing_light_hide = {}
    for obj in scene.objects:
        if obj.type == 'LIGHT':
            saved_existing_light_hide[obj.name] = obj.hide_render
            obj.hide_render = True

    temp_camera = None
    temp_light = None
    temp_mask_material = None
    wire_modifier_objs = []   # Wireframe modifier を一時適用したオブジェクト名リスト

    try:
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
        scene.render.image_settings.file_format = "PNG"

        temp_camera = _create_temp_camera()
        temp_light  = _create_temp_light()
        scene.camera = temp_camera

        # ============================================================
        # 1. 全景 6 アングル (EEVEE)
        # ============================================================
        _set_render_engine(scene, ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "BLENDER_WORKBENCH"])
        angles = [
            ("front",      Vector(( 0, -1,    0  )))
        ,   ("back",       Vector(( 0,  1,    0  )))
        ,   ("side_right", Vector(( 1,  0,    0  )))
        ,   ("side_left",  Vector((-1,  0,    0  )))
        ,   ("top",        Vector(( 0,  0,    1  )))
        ,   ("bottom",     Vector(( 0,  0,   -1  )))
        ,   ("persp",      Vector((-1, -1,    0.7)))
        ,   ("persp_back", Vector(( 1,  1,     0.7)))
        ]
        for name, direction in angles:
            _position_camera(
                camera=temp_camera
            ,   direction=direction
            ,   scene_bb=scene_bb
            ,   orthographic=(name not in {"persp", "persp_back"})
            )
            scene.render.filepath = os.path.join(output_dir, f"{name}.png")
            bpy.ops.render.render(write_still=True)

        # ============================================================
        # 1.5. 一次形状評価用の true-alpha シルエット
        # ============================================================
        # beauty render の色しきい値から輪郭を作ると、暗い縁・透過・照明で
        # 輪郭が欠ける。全景と同一のカメラ配置で背景だけを透明にし、全メッシュを
        # 完全不透明の単色材質へ override して、alpha を直接評価できる画像を残す。
        temp_mask_material = bpy.data.materials.new(name="_claude_silhouette_mask")
        temp_mask_material.use_nodes = True
        mask_bsdf = temp_mask_material.node_tree.nodes.get("Principled BSDF")
        if mask_bsdf is not None:
            mask_bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
            mask_bsdf.inputs["Roughness"].default_value = 1.0
            mask_bsdf.inputs["Alpha"].default_value = 1.0
        scene.render.film_transparent = True
        bpy.context.view_layer.material_override = temp_mask_material
        for name, direction in angles:
            _position_camera(
                camera=temp_camera
            ,   direction=direction
            ,   scene_bb=scene_bb
            ,   orthographic=(name not in {"persp", "persp_back"})
            )
            scene.render.filepath = os.path.join(output_dir, f"silhouette_{name}.png")
            bpy.ops.render.render(write_still=True)
        bpy.context.view_layer.material_override = saved["material_override"]
        scene.render.film_transparent = saved["film_transparent"]
        bpy.data.materials.remove(temp_mask_material)
        temp_mask_material = None

        # ============================================================
        # 1.6. 汎用形状観察パス
        # ============================================================
        # Beauty画像だけでは、照明・色・透明度と形状差を分離できない。
        # 同じcamera/cropでpart owner、world normal、camera depthを出し、
        # reference comparisonと局所最適脱出の客観証拠にする。
        _render_geometry_observation_passes(
            output_dir = output_dir
        ,   scene_bb   = scene_bb
        ,   camera     = temp_camera
        ,   angles     = angles
        )

        # Small but identity-critical controls and natural subforms can occupy
        # too few pixels in a whole-asset packet to support causal review.  A
        # caller may therefore request region-ID-owned closeups.  The ROI comes
        # from rendered mesh ownership, not from a hand-authored image crop.
        if semantic_region_closeups:
            _render_semantic_region_closeups(
                output_dir = output_dir
            ,   camera     = temp_camera
            ,   closeups   = semantic_region_closeups
            )

        # ============================================================
        # 2. クローズアップ (B): シーン全体を上/下/左/右 に切り取って撮影
        # ============================================================
        # 各クローズアップは scene_bb の指定領域だけを画面に収めるよう
        # カメラ位置・距離を調整 (= 仮想的な ROI bbox を作って撮影)
        closeups = _build_closeup_rois(scene_bb)
        for closeup_name, roi_bb, direction in closeups:
            _position_camera(camera=temp_camera, direction=direction, scene_bb=roi_bb)
            scene.render.filepath = os.path.join(output_dir, f"closeup_{closeup_name}.png")
            bpy.ops.render.render(write_still=True)

        # ============================================================
        # 3. 個別オブジェクトレンダ (E): 各メッシュを単独で撮影
        # ============================================================
        # 全メッシュをいったん hide_render=True にして、対象だけ False に
        # 戻して撮影 → 各メッシュ固有の品質を分離して確認可能
        all_mesh_objs = [obj for obj in scene.objects if obj.type == "MESH"]
        for tgt in all_mesh_objs:
            for obj in all_mesh_objs:
                obj.hide_render = (obj is not tgt)
            # 対象メッシュ単独の bbox でカメラ配置
            tgt_bb = _compute_object_bounding_box(tgt)
            _position_camera(camera=temp_camera, direction=Vector((-1, -1, 0.7)), scene_bb=tgt_bb)
            safe_name = "".join(c if c.isalnum() or c in "_-." else "_" for c in tgt.name)
            scene.render.filepath = os.path.join(output_dir, f"single_{safe_name}.png")
            bpy.ops.render.render(write_still=True)
            # High-risk representation candidates opt in to a local observation
            # packet.  A single beauty angle cannot prove a part's section or
            # rear/top continuity, while rendering every object from every view
            # would make normal asset previews unnecessarily expensive.
            if bool(tgt.get("evidence_multiview", False)):
                local_angles = (
                    ("front", Vector((0, -1, 0))),
                    ("back", Vector((0, 1, 0))),
                    ("side_left", Vector((-1, 0, 0))),
                    ("top", Vector((0, 0, 1))),
                    ("persp", Vector((-1, -1, 0.7))),
                )
                for local_name, local_direction in local_angles:
                    _position_camera(
                        camera=temp_camera,
                        direction=local_direction,
                        scene_bb=tgt_bb,
                        orthographic=(local_name != "persp"),
                    )
                    scene.render.filepath = os.path.join(
                        output_dir,
                        f"single_{safe_name}_{local_name}.png",
                    )
                    bpy.ops.render.render(write_still=True)
        # 全メッシュの hide_render を復元
        for obj_name, was_hidden in saved_hide_render.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                obj.hide_render = was_hidden

        # ============================================================
        # 3.5. face_orientation 可視化 (C-2): viewport overlay の
        #      show_face_orientation=True 状態を opengl render で出力。
        #      表向き=青、裏向き=赤 で人間が一目で「赤い面」を確認できる。
        # ============================================================
        try:
            _render_face_orientation_overlay(
                output_dir   = output_dir
            ,   scene_bb     = scene_bb
            ,   camera       = temp_camera
            ,   resolution   = resolution
            )
        except Exception as e:
            print(f"[claude_preview] face_orientation render skipped: {e}")

        # ============================================================
        # 4. ワイヤーフレーム (C): Wireframe modifier 一時適用で撮影
        # ============================================================
        # 全メッシュに Wireframe modifier を一時的に追加 → render → 削除
        # (workbench の WIREFRAME shading は Blender 5.x で動作不安定なため)
        for obj in all_mesh_objs:
            try:
                wmod = obj.modifiers.new(name="_claude_wire", type='WIREFRAME')
                wmod.thickness = max(scene_bb["diagonal"] * 0.0008, 0.0005)
                wmod.use_replace = False    # 元メッシュも残す
                wire_modifier_objs.append(obj.name)
            except Exception:
                pass
        # 斜めアングル
        _position_camera(camera=temp_camera, direction=Vector((-1, -1, 0.7)), scene_bb=scene_bb)
        scene.render.filepath = os.path.join(output_dir, "wireframe.png")
        bpy.ops.render.render(write_still=True)
        # 真上アングル
        _position_camera(camera=temp_camera, direction=Vector((0, 0, 1)), scene_bb=scene_bb)
        scene.render.filepath = os.path.join(output_dir, "wireframe_top.png")
        bpy.ops.render.render(write_still=True)
        # Wireframe modifier 削除
        for obj_name in wire_modifier_objs:
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                wmod = obj.modifiers.get("_claude_wire")
                if wmod is not None:
                    obj.modifiers.remove(wmod)
        wire_modifier_objs = []

    finally:
        # ----------------------------------------------------------------
        # 後始末
        # ----------------------------------------------------------------
        # Wireframe modifier の取り残しを削除
        for obj_name in wire_modifier_objs:
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                wmod = obj.modifiers.get("_claude_wire")
                if wmod is not None:
                    obj.modifiers.remove(wmod)
        # 一時カメラ・ライト削除
        if temp_camera is not None and temp_camera.name in bpy.data.objects:
            bpy.data.objects.remove(temp_camera, do_unlink=True)
        if temp_light is not None and temp_light.name in bpy.data.objects:
            bpy.data.objects.remove(temp_light, do_unlink=True)
        # シルエット描画の途中で失敗した場合も override と透明背景を戻す。
        try:
            bpy.context.view_layer.material_override = saved["material_override"]
            scene.render.film_transparent = saved["film_transparent"]
        except Exception:
            pass
        if temp_mask_material is not None and temp_mask_material.name in bpy.data.materials:
            bpy.data.materials.remove(temp_mask_material)

        # ----------------------------------------------------------------
        # B-2: 参考画像との色味比較 (レンダ完了後に実行)
        # ----------------------------------------------------------------
        # ref_img/ ディレクトリ内の同名画像 (例: persp.png) と現出力を比較し
        # 中央 50% 領域の平均 RGB / HSV 差分を出して check_report.json に追記する。
        try:
            ref_comparison = _compare_with_reference_images(
                project_name = project_name
            ,   git_root     = git_root
            ,   output_dir   = output_dir
            )
            if ref_comparison:
                # 既存 check_report.json を読み直して追記
                if os.path.exists(check_first_pass_path):
                    with open(check_first_pass_path, "r", encoding="utf-8") as f:
                        check = json.load(f)
                    check["reference_image_comparison"] = ref_comparison
                    # 大きな色差は issues に追加
                    for fname, diff in ref_comparison.items():
                        if isinstance(diff, dict) and "diff_hsv" in diff:
                            h_diff_abs = abs(diff["diff_hsv"][0])
                            # 色相差が 0.10 (= 36 度相当) 超えで warning
                            if h_diff_abs > 0.10:
                                check.setdefault("issues", []).append({
                                    "severity": "warning"
                                ,   "category": "color_mismatch"
                                ,   "object":   fname
                                ,   "detail":   (f"Color hue differs from reference by "
                                                f"{h_diff_abs:.2f} (HSV scale 0-1, ~{h_diff_abs*360:.0f} deg). "
                                                f"ref_HSV={diff['ref_hsv']}, cur_HSV={diff['cur_hsv']}")
                                })
                    with open(check_first_pass_path, "w", encoding="utf-8") as f:
                        json.dump(check, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[claude_preview] reference image comparison failed: {e}")
        # hide_render 復元
        for obj_name, was_hidden in saved_hide_render.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                obj.hide_render = was_hidden
        # レンダ設定復元
        scene.render.engine = saved["engine"]
        scene.render.resolution_x = saved["res_x"]
        scene.render.resolution_y = saved["res_y"]
        scene.render.filepath = saved["filepath"]
        scene.render.image_settings.file_format = saved["file_format"]
        scene.render.film_transparent = saved["film_transparent"]
        scene.camera = saved["camera"]
        scene.display.shading.type = saved["shading"]
        # view transform 復元
        try:
            scene.view_settings.view_transform = saved["view_transform"]
            scene.view_settings.look           = saved["look"]
            scene.view_settings.exposure       = saved["exposure"]
        except Exception:
            pass
        # 既存 LIGHT の hide_render 復元
        for ln, was_hidden in saved_existing_light_hide.items():
            obj = bpy.data.objects.get(ln)
            if obj is not None:
                obj.hide_render = was_hidden


# ============================================================
# A: 数値検証レポート (check_report.json)
# ============================================================
def _generate_check_report(project_name, reference_ratios=None, scene_bb=None):
    """
    各メッシュと隣接ペアの整合性を bmesh で検証し、報告 dict を返す

    検出する問題:
        - non_manifold_edges: トポロジ破綻 (T字/X字/穴の縁)
        - open_boundary_edges: 1面のみのエッジ数 (= open hole の縁の総数)
        - isolated_vertices: 孤立頂点
        - inverted_faces: 中心から見て法線が内向きの面
        - 隣接オブジェクトペアの bbox 重なり量 / Z 隙間
            (枝が浮いている等の検出に使う)

    Output:
        dict {
            "project_name": str
        ,   "executed_at":  str
        ,   "objects": [
                {
                    "name": str
                ,   "vertices": int
                ,   "faces": int
                ,   "non_manifold_edges": int
                ,   "open_boundary_edges": int
                ,   "isolated_vertices": int
                ,   "inverted_faces": int
                ,   "is_clean": bool   (上記が全て 0 なら True)
                }
            ]
        ,   "object_pairs": [
                {
                    "obj_a": str, "obj_b": str
                ,   "bbox_overlap": [x, y, z]  (負値 = 隙間量)
                ,   "z_gap_above": float       (a.max.z - b.min.z, 正=隙間)
                ,   "z_gap_below": float       (b.max.z - a.min.z)
                ,   "warning":  str | null
                }
            ]
        ,   "issues": [
                { "severity": "...", "category": "...", "object": "...", "detail": "..." }
            ]
        }
    """
    issues = []
    object_reports = []

    mesh_objs = [obj for obj in bpy.context.scene.objects
                 if obj.type == "MESH" and obj.data is not None]

    # --- 各メッシュごとの検証 ---
    for obj in mesh_objs:
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        # 1. non-manifold エッジ数 (3面以上接続 or 0面接続のエッジ含む)
        non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
        # 2. open boundary edges (1面のみのエッジ = 穴の縁の総和)
        open_boundary_edges = sum(1 for e in bm.edges if len(e.link_faces) == 1)
        # 3. 孤立頂点 (どの edge にも属さない)
        isolated_vertices = sum(1 for v in bm.verts if len(v.link_edges) == 0)
        # 4. inverted faces:
        #    bmesh をコピーして recalc_face_normals(外向きへ正規化) を適用し、
        #    元の法線と反転している面の数 = 真の inverted faces としてカウント
        #    (旧版の "中心からの放射方向比較" は複合形状で偽陽性が大量発生したため変更)
        original_normals = [f.normal.copy() for f in bm.faces]
        bm_copy = bm.copy()
        try:
            bmesh.ops.recalc_face_normals(bm_copy, faces=list(bm_copy.faces))
            inverted = 0
            for orig_n, f_new in zip(original_normals, bm_copy.faces):
                if orig_n.length > 1e-9 and f_new.normal.length > 1e-9:
                    if orig_n.dot(f_new.normal) < -0.5:
                        inverted += 1
        except Exception:
            inverted = 0
        bm_copy.free()
        bm.free()

        # 5. self_intersections (B-1):
        #    同一メッシュ内で「貫通している」「クロスしている」face ペアを推定。
        #    枝が塊根を貫通している、葉同士がクロスしている等を検出可能。
        #    BVHTree.overlap で bbox 重なり判定 + 隣接面除外 で近似 (高速だが厳密ではない)。
        self_intersection_report = _count_self_intersections(obj)
        self_intersections = self_intersection_report["count"]

        # 6. viewport_inverted_stats (A-1):
        #    6 アングルの標準カメラから「視認可能 face の中で何 % が裏向き (= 赤)」
        #    を計測する。Blender の overlay.show_face_orientation で
        #    人間が目視している「赤い面」を直接的に数値化。
        #    各アングル別に集計し、最悪 (= 最も裏向き率が高い) アングルを記録。
        #    球面のような閉じた形状でも、各アングルごとに「画面に映る面」のみ
        #    を分母にするため、人間の見た目と一致した有用な指標になる。
        viewport_stats = _compute_viewport_inverted_stats(obj, scene_bb) if scene_bb else {
            "worst_angle_name": None
        ,   "worst_inverted_ratio": 0.0
        ,   "worst_visible_inverted_ratio": 0.0
        ,   "worst_visible_inverted_world_area_ratio": 0.0
        ,   "per_angle": {}
        }
        worst_inv_ratio = viewport_stats["worst_inverted_ratio"]
        # occlusion 考慮版: 画面に実際に映る face のうち裏向き比率
        # こちらを主指標とする (= 「人間が画面で気付く赤」を直接示す)
        worst_visible_ratio = viewport_stats["worst_visible_inverted_ratio"]
        worst_visible_area_ratio = viewport_stats[
            "worst_visible_inverted_world_area_ratio"
        ]

        is_clean = (non_manifold_edges == 0
                    and isolated_vertices == 0
                    and worst_visible_area_ratio < 0.005)

        report = {
            "name":                obj.name
        ,   "vertices":            len(mesh.vertices)
        ,   "faces":               len(mesh.polygons)
        ,   "non_manifold_edges":  non_manifold_edges
        ,   "open_boundary_edges": open_boundary_edges
        ,   "isolated_vertices":   isolated_vertices
        ,   "inverted_faces":      inverted
        ,   "self_intersections":  self_intersections   # B-1
        ,   "self_intersection_examples": self_intersection_report["examples"]
        ,   "viewport_inverted":   viewport_stats   # A-1 (per_angle 含む)
        ,   "is_clean":            is_clean
        }
        object_reports.append(report)

        # 問題を issues に追加
        if non_manifold_edges > 0:
            issues.append({
                "severity": "warning"
            ,   "category": "non_manifold"
            ,   "object":   obj.name
            ,   "detail":   f"{non_manifold_edges} edges are non-manifold (T-junction, hole rim, isolated)"
            })
        if open_boundary_edges > 0:
            issues.append({
                "severity": "warning"
            ,   "category": "open_hole"
            ,   "object":   obj.name
            ,   "detail":   f"{open_boundary_edges} boundary edges (= open hole rim length)"
            })
        if isolated_vertices > 0:
            issues.append({
                "severity": "error"
            ,   "category": "isolated_vertex"
            ,   "object":   obj.name
            ,   "detail":   f"{isolated_vertices} isolated vertices"
            })
        if inverted > 0:
            issues.append({
                "severity": "warning"
            ,   "category": "inverted_face"
            ,   "object":   obj.name
            ,   "detail":   f"{inverted}/{len(mesh.polygons)} faces appear inverted (normal pointing inward)"
            })
        # B-1 issue: 自己交差ペアが多いと「メッシュが絡んでいる/破綻」
        # しきい値: face 数の 1% を超えたら warning
        if self_intersections > max(2, len(mesh.polygons) * 0.01):
            issues.append({
                "severity": "warning"
            ,   "category": "self_intersection"
            ,   "object":   obj.name
            ,   "detail":   (f"{self_intersections} face pairs may be self-intersecting "
                            f"(non-adjacent faces with overlapping bbox). "
                            f"Possible mesh penetration or fold-over.")
            })
        # A-1 issue (occlusion 考慮版):
        # worst_visible_inverted_ratio = 「実際に画面に映る face のうち裏向きの比率」
        # 閉じた正常メッシュなら 0、局所的な反転 (= 枝の側面が裏向き 等) があれば > 0
        # しきい値 5% 以上で warning、20% 以上で error
        if worst_visible_area_ratio >= 0.02:
            severity = "error"
        elif worst_visible_area_ratio >= 0.005:
            severity = "warning"
        else:
            severity = None
        if severity is not None:
            wn = viewport_stats["worst_angle_name"]
            wd = viewport_stats["per_angle"].get(wn, {})
            issues.append({
                "severity": severity
            ,   "category": "viewport_inverted_face"
            ,   "object":   obj.name
            ,   "detail":   (f"From '{wn}' angle: {wd.get('visible_inverted', 0)} of "
                            f"{wd.get('visible_faces', 0)} actually-visible faces are RED "
                            f"(back-facing, {worst_visible_ratio*100:.1f}% by face count; "
                            f"{worst_visible_area_ratio*100:.3f}% by visible world area). "
                            f"Confirm with face_orientation_{wn}.png — likely local normal flip "
                            f"(e.g., a few faces of a branch / leaf are inverted).")
            })
            is_clean = False
            report["is_clean"] = False

    # --- ペア間の bbox 重なり/隙間チェック + mesh-to-mesh 最短距離 (A-2) ---
    # 全ペアを総当たり (パーツ間の浮きを検出するため)
    pair_reports = []
    # mesh-to-mesh 距離の判定しきい値: シーン bbox 対角の 2%
    floating_threshold = (scene_bb["diagonal"] * 0.02) if scene_bb else 0.005
    for i, oa in enumerate(mesh_objs):
        bb_a = _compute_object_bounding_box(oa)
        for ob in mesh_objs[i+1:]:
            bb_b = _compute_object_bounding_box(ob)
            # bbox overlap (負値 = 隙間、正値 = 重なり量)
            overlap = [
                min(bb_a["max"][k], bb_b["max"][k]) - max(bb_a["min"][k], bb_b["min"][k])
                for k in range(3)
            ]
            z_gap_above = bb_a["max"].z - bb_b["min"].z   # a の上端と b の下端の差
            z_gap_below = bb_b["max"].z - bb_a["min"].z

            # A-2: 実体 (面) 同士の最短距離を BVHTree で計算
            # bbox は重なっていても、実メッシュは離れている (= 浮き) を検出
            mesh_dist = _compute_min_mesh_distance(oa, ob)

            # 警告判定: bbox の XY が重なるが Z が離れている、または mesh 実距離が
            # 「明らかに離れている」(= floating_threshold 超え)
            xy_overlap = (overlap[0] > 0 and overlap[1] > 0)
            z_overlap  = overlap[2] > 0
            warning = None
            if xy_overlap and not z_overlap:
                warning = f"XY bbox overlaps but Z gap = {abs(overlap[2]):.4f}m (one of {oa.name}/{ob.name} may be floating)"
                issues.append({
                    "severity": "warning"
                ,   "category": "z_gap"
                ,   "object":   f"{oa.name} <-> {ob.name}"
                ,   "detail":   warning
                })
            # A-2 issue: bbox が重なるのに mesh 実距離が大きい = メッシュ的に浮いている
            if (mesh_dist is not None and mesh_dist > floating_threshold
                    and overlap[0] > 0 and overlap[1] > 0 and overlap[2] > 0):
                detail = (f"bbox overlaps but actual mesh-to-mesh distance is "
                         f"{mesh_dist:.4f}m (> threshold {floating_threshold:.4f}m). "
                         f"One of {oa.name}/{ob.name} is hollow / floating inside the other's bbox.")
                issues.append({
                    "severity": "warning"
                ,   "category": "mesh_floating"
                ,   "object":   f"{oa.name} <-> {ob.name}"
                ,   "detail":   detail
                })
            pair_reports.append({
                "obj_a":             oa.name
            ,   "obj_b":             ob.name
            ,   "bbox_overlap":      [round(o, 5) for o in overlap]
            ,   "z_gap_above":       round(z_gap_above, 5)
            ,   "z_gap_below":       round(z_gap_below, 5)
            ,   "mesh_min_distance": (round(mesh_dist, 5) if mesh_dist is not None else None)
            ,   "warning":           warning
            })

    # ----- パーツ間サイズ比率レポート (各オブジェクトの size を一覧+比率で) -----
    # 最大の bbox を持つオブジェクトを基準 (= シーンの主役) として、
    # 他オブジェクトの size 比率を計算
    size_ratios = _compute_size_ratios(mesh_objs)

    # ----- 参考画像比率との比較 (reference_ratios 指定時のみ) -----
    if reference_ratios is not None:
        comparison = _compare_with_reference_ratios(mesh_objs, reference_ratios)
        size_ratios["expected_vs_actual"] = comparison
        # 大きく外れた項目は issue に追加
        for row in comparison.get("rows", []):
            diff_pct = abs(row["diff_percent"])
            if diff_pct > 25.0:
                issues.append({
                    "severity": "warning"
                ,   "category": "size_ratio_mismatch"
                ,   "object":   row["part_name"]
                ,   "detail":   (f"{row['part_name']}.{row['dimension']} "
                                f"expected ratio {row['expected_ratio']:.3f} "
                                f"but actual {row['actual_ratio']:.3f} "
                                f"(diff {row['diff_percent']:+.1f}%)")
                })

    return {
        "project_name": project_name
    ,   "executed_at":  datetime.now().isoformat(timespec="seconds")
    ,   "objects":      object_reports
    ,   "object_pairs": pair_reports
    ,   "size_ratios":  size_ratios
    ,   "issues":       issues
    ,   "summary": {
            "total_issues":     len(issues)
        ,   "errors":           sum(1 for i in issues if i["severity"] == "error")
        ,   "warnings":         sum(1 for i in issues if i["severity"] == "warning")
        ,   "clean_objects":    sum(1 for r in object_reports if r["is_clean"])
        ,   "total_objects":    len(object_reports)
        }
    }


# ============================================================
# B-2: 参考画像との色味比較 (HSV 平均差分)
# ============================================================
# ref_img/ ディレクトリ内の同名画像 (例: persp.png, single_caudex.png) と
# 現出力を比較し、中央 50% 領域の平均 RGB を計算 → HSV 変換 → 差分を出力。
# 「テクスチャ色が参考と違う」を数値化できる。
#
# 期待ディレクトリ位置:
#   <git_root>/Assets/parts/model/<project_name>/ref_img/  (新版)
#   <git_root>/Assets/mdl/<project_name>/ref_img/          (旧版)
#
# Input :
#   project_name : プロジェクト名
#   git_root     : git ルート (= Assets/ の親)
#   output_dir   : 現出力先 (= Output/preview/<project_name>/)
# Output:
#   dict { fname: { ref_rgb, cur_rgb, diff_rgb, ref_hsv, cur_hsv, diff_hsv } }
#   または None (ref_img 不在時)
def _compare_with_reference_images(project_name, git_root, output_dir):
    # ref_img/ ディレクトリを探す (新旧 2 通り)
    candidates = [
        os.path.join(git_root, "Assets", "parts", "model", project_name, "ref_img")
    ,   os.path.join(git_root, "Assets", "mdl",   project_name, "ref_img")
    ]
    ref_dir = None
    for c in candidates:
        if os.path.isdir(c):
            ref_dir = c
            break
    if ref_dir is None:
        return None
    # 比較可能な画像 (= 同名で存在するもの) を探す
    results = {}
    for fname in os.listdir(ref_dir):
        if not fname.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        ref_path = os.path.join(ref_dir, fname)
        cur_path = os.path.join(output_dir, fname)
        if not os.path.exists(cur_path):
            continue
        try:
            results[fname] = _compute_image_color_diff(ref_path, cur_path)
        except Exception as e:
            results[fname] = {"error": str(e)}
    return results if results else None


# 2 つの画像の中央 50% 領域の平均 RGB / HSV を比較する
# Input  : ref_path, cur_path - 画像ファイルパス
# Output : dict {ref_rgb, cur_rgb, diff_rgb, ref_hsv, cur_hsv, diff_hsv}
def _compute_image_color_diff(ref_path, cur_path):
    ref_rgb = _avg_color_center(ref_path)
    cur_rgb = _avg_color_center(cur_path)
    if ref_rgb is None or cur_rgb is None:
        return {"error": "image load failed"}
    diff_rgb = [round(c - r, 4) for c, r in zip(cur_rgb, ref_rgb)]
    import colorsys
    ref_hsv = colorsys.rgb_to_hsv(*ref_rgb)
    cur_hsv = colorsys.rgb_to_hsv(*cur_rgb)
    diff_hsv = [round(c - r, 4) for c, r in zip(cur_hsv, ref_hsv)]
    return {
        "ref_rgb":  [round(c, 4) for c in ref_rgb]
    ,   "cur_rgb":  [round(c, 4) for c in cur_rgb]
    ,   "diff_rgb": diff_rgb
    ,   "ref_hsv":  [round(c, 4) for c in ref_hsv]
    ,   "cur_hsv":  [round(c, 4) for c in cur_hsv]
    ,   "diff_hsv": diff_hsv
    }


# 画像の中央 50% 領域の平均 RGB を取得 (アルファ 0.1 未満は背景として除外)
# Input  : path - 画像ファイルパス
# Output : (r, g, b) tuple in [0, 1] or None on failure
def _avg_color_center(path):
    img = None
    try:
        img = bpy.data.images.load(path, check_existing=False)
        w, h = img.size
        if w == 0 or h == 0:
            return None
        # pixels: flat [r0, g0, b0, a0, r1, g1, b1, a1, ...]
        # 1 度だけ list 化 (繰り返しアクセスは遅い)
        pixels = list(img.pixels)
        x_start = int(w * 0.25)
        x_end   = int(w * 0.75)
        y_start = int(h * 0.25)
        y_end   = int(h * 0.75)
        r_sum = g_sum = b_sum = 0.0
        count = 0
        for y in range(y_start, y_end):
            row_base = y * w * 4
            for x in range(x_start, x_end):
                idx = row_base + x * 4
                # アルファが小さいピクセルはスキップ (= 背景透過部分)
                if pixels[idx + 3] < 0.1:
                    continue
                r_sum += pixels[idx]
                g_sum += pixels[idx + 1]
                b_sum += pixels[idx + 2]
                count += 1
        if count == 0:
            return None
        return (r_sum / count, g_sum / count, b_sum / count)
    except Exception:
        return None
    finally:
        if img is not None and img.name in bpy.data.images:
            try:
                bpy.data.images.remove(img)
            except Exception:
                pass


# ============================================================
# B-1: 同一メッシュ内の 自己交差 (self-intersection) 検出
# ============================================================
# BVHTree.overlap(self) で「自分自身の face 同士のバウンディングが重なる
# ペア」を取得し、頂点共有していない (= 隣接していない) ペアだけを残す。
# これが「貫通」「クロス」している candidate (近似)。
# 正確な交差判定 (面同士の幾何学的交差) はコスト高なので、bbox 重なり
# + 非隣接 で代用 (誤検出はあり得るが、目視確認用としては十分)。
#
# Input :
#   obj : MESH オブジェクト
# Output:
#   int : 推定自己交差ペア数
def _strict_point_in_triangle(point, a, b, c, normal, epsilon=1.0e-7):
    """Return True only when point lies strictly inside a 3D triangle."""
    signs = (
        normal.dot((b - a).cross(point - a)),
        normal.dot((c - b).cross(point - b)),
        normal.dot((a - c).cross(point - c)),
    )
    return (all(value > epsilon for value in signs)
            or all(value < -epsilon for value in signs))


def _segment_pierces_triangle(p0, p1, a, b, c, epsilon=1.0e-7):
    """Detect an interior segment/triangle penetration, excluding contact."""
    normal = (b - a).cross(c - a)
    if normal.length_squared < epsilon * epsilon:
        return False
    d0 = normal.dot(p0 - a)
    d1 = normal.dot(p1 - a)
    # Same side, coplanar, or merely touching the plane is not penetration.
    if d0 * d1 >= -epsilon * epsilon:
        return False
    denominator = d0 - d1
    if abs(denominator) < epsilon:
        return False
    t = d0 / denominator
    if t <= epsilon or t >= 1.0 - epsilon:
        return False
    point = p0 + (p1 - p0) * t
    return _strict_point_in_triangle(point, a, b, c, normal, epsilon)


def _triangles_pierce(face_a, face_b):
    """Exact non-coplanar interior intersection for two triangulated faces."""
    a = [vertex.co for vertex in face_a.verts]
    b = [vertex.co for vertex in face_b.verts]
    if len(a) != 3 or len(b) != 3:
        return False
    normal_a = (a[1] - a[0]).cross(a[2] - a[0])
    normal_b = (b[1] - b[0]).cross(b[2] - b[0])
    if normal_a.length_squared < 1.0e-14 or normal_b.length_squared < 1.0e-14:
        return False
    # Coplanar contacts and laminated surfaces are not through-penetrations.
    if normal_a.cross(normal_b).length_squared < 1.0e-14:
        plane_distance = abs(normal_a.normalized().dot(b[0] - a[0]))
        if plane_distance < 1.0e-7:
            return False
    for index in range(3):
        if _segment_pierces_triangle(
            a[index], a[(index + 1) % 3], b[0], b[1], b[2]
        ):
            return True
        if _segment_pierces_triangle(
            b[index], b[(index + 1) % 3], a[0], a[1], a[2]
        ):
            return True
    return False


def _count_self_intersections(obj):
    if obj is None or obj.type != "MESH":
        return {"count": 0, "examples": []}
    try:
        deps = bpy.context.evaluated_depsgraph_get()
        bm = bmesh.new()
        bm.from_object(obj, deps)
        bm.transform(obj.matrix_world)
        # BVH face indices must address triangles for exact candidate tests.
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        # A final Asset object intentionally contains many disconnected closed
        # islands (sheet metal, label, cap thread, rib, shelf, fastener).  A
        # crossing between two such islands is an assembly contact, not a face
        # folding back through its own connected surface.  Build connected
        # component IDs so the self-intersection metric keeps that distinction.
        component_by_face = {}
        component_id = 0
        for seed in bm.faces:
            if seed.index in component_by_face:
                continue
            stack = [seed]
            component_by_face[seed.index] = component_id
            while stack:
                current = stack.pop()
                for edge in current.edges:
                    for linked in edge.link_faces:
                        if linked.index not in component_by_face:
                            component_by_face[linked.index] = component_id
                            stack.append(linked)
            component_id += 1
        bvh = BVHTree.FromBMesh(bm)
        # overlap(other) : self.tree との bbox 重なりペアを返す
        # (face_idx_self, face_idx_other) のリスト
        overlaps = bvh.overlap(bvh)
    except Exception:
        return {"count": 0, "examples": []}
    # 自分自身 (idx 同一) と 隣接 (頂点共有) を除外
    intersection_pairs = 0
    examples = []
    seen = set()
    for ia, ib in overlaps:
        if ia == ib:
            continue
        # ペアを順序固定 (重複カウント防止)
        key = (min(ia, ib), max(ia, ib))
        if key in seen:
            continue
        seen.add(key)
        try:
            fa = bm.faces[ia]
            fb = bm.faces[ib]
        except (IndexError, ReferenceError):
            continue
        if component_by_face.get(ia) != component_by_face.get(ib):
            continue
        # 頂点共有 (= 隣接 face) なら自己交差ではない
        verts_a = set(v.index for v in fa.verts)
        verts_b = set(v.index for v in fb.verts)
        if verts_a & verts_b:
            continue
        if _triangles_pierce(fa, fb):
            intersection_pairs += 1
            if len(examples) < 32:
                points = [vertex.co for vertex in fa.verts] + [
                    vertex.co for vertex in fb.verts
                ]
                center = sum(points, Vector((0.0, 0.0, 0.0))) / len(points)
                examples.append({
                    "component": component_by_face.get(ia),
                    "face_a": ia,
                    "face_b": ib,
                    "material_a": fa.material_index,
                    "material_b": fb.material_index,
                    "center": [round(value, 6) for value in center],
                })
    bm.free()
    return {"count": intersection_pairs, "examples": examples}


# ============================================================
# A-2: メッシュ間 最短距離 (mesh-to-mesh distance)
# ============================================================
# bbox 重なり判定だけでは「bbox は重なるが実メッシュは離れている」
# (= 葉が枝から数 mm 浮いている等) を見逃す。BVHTree.find_nearest を
# 使って実 face 同士の最短距離を厳密に計算する。
#
# 実装:
#   1. obj_a / obj_b の depsgraph 評価メッシュを world 座標で BVH 化
#   2. obj_a の各頂点から obj_b BVH へ find_nearest → 最短距離
#   3. 同様に obj_b → obj_a BVH (対称化、片側だけだと vertex 配置の偏りで
#      見落とす可能性があるため)
#   4. 両方向の最小値を返す
#
# Input :
#   obj_a, obj_b : MESH オブジェクト
# Output:
#   float | None : メッシュ間の最短距離 (m)、計算失敗時は None
def _compute_min_mesh_distance(obj_a, obj_b):
    if obj_a is None or obj_b is None:
        return None
    if obj_a.type != "MESH" or obj_b.type != "MESH":
        return None
    try:
        deps = bpy.context.evaluated_depsgraph_get()
        # world 座標の BVH を作る
        # BVHTree.FromObject は obj のローカル座標で BVH を作るので、
        # 以下の手順で world 座標化:
        #   1. bmesh.from_object(obj, deps) で評価済みメッシュを取り込み
        #   2. bm.transform(obj.matrix_world) で world に変換
        #   3. BVHTree.FromBMesh(bm)
        bm_a = bmesh.new()
        bm_a.from_object(obj_a, deps)
        bm_a.transform(obj_a.matrix_world)
        bvh_a = BVHTree.FromBMesh(bm_a)

        bm_b = bmesh.new()
        bm_b.from_object(obj_b, deps)
        bm_b.transform(obj_b.matrix_world)
        bvh_b = BVHTree.FromBMesh(bm_b)
    except Exception:
        return None

    min_dist = float('inf')
    # obj_a の頂点 → obj_b BVH (= obj_a の各頂点が obj_b にどれだけ近いか)
    for v in bm_a.verts:
        loc, norm, idx, dist = bvh_b.find_nearest(v.co)
        if loc is not None and dist is not None and dist < min_dist:
            min_dist = dist
    # obj_b の頂点 → obj_a BVH (対称化)
    for v in bm_b.verts:
        loc, norm, idx, dist = bvh_a.find_nearest(v.co)
        if loc is not None and dist is not None and dist < min_dist:
            min_dist = dist
    bm_a.free()
    bm_b.free()
    if min_dist == float('inf'):
        return None
    return min_dist


# ============================================================
# A-1: viewport で「赤く見える面」 (back-facing face) の検出
# ============================================================
# Blender の overlay.show_face_orientation = True 時に
# 「カメラに対して裏向き」の面が赤く表示される。これと同じ判定を
# 6 標準アングルで行い「視認可能 face 中の裏向き比率」を計算する。
# (球面のような閉じた形状では「6 アングル和集合」では 100% になってしまうため、
#  各アングル別に「画面に映る面の中で何 % が赤いか」を計測する方が
#  人間の目視と一致した有用な指標になる)
# Input :
#   obj      : 対象 MESH オブジェクト
#   scene_bb : シーン全体の bbox (= カメラ距離計算用)
#   fov_deg  : 仮想カメラの視野角 (デフォルト 50 度)
# Output:
#   dict {
#       "worst_angle_name":  str (最も裏向き率が高いアングル名)
#   ,   "worst_inverted_ratio": float (= worst_angle で見える face の中の裏向き比率, 0.0-1.0)
#   ,   "per_angle": {
#           "front":      {"visible_faces": int, "inverted_faces": int, "ratio": float}
#       ,   "back":       {...}
#       ,   ...
#       }
#   }
def _compute_viewport_inverted_stats(obj, scene_bb, fov_deg=50.0):
    if obj is None or obj.type != "MESH" or scene_bb is None:
        return {
            "worst_angle_name": None
        ,   "worst_inverted_ratio": 0.0
        ,   "worst_visible_inverted_ratio": 0.0
        ,   "worst_visible_inverted_world_area_ratio": 0.0
        ,   "per_angle": {}
        }
    # 6 標準アングル (front/back/side_right/side_left/top/persp、全景レンダと同じ)
    angles = [
        ("front",      Vector(( 0, -1,    0  )))
    ,   ("back",       Vector(( 0,  1,    0  )))
    ,   ("side_right", Vector(( 1,  0,    0  )))
    ,   ("side_left",  Vector((-1,  0,    0  )))
    ,   ("top",        Vector(( 0,  0,    1  )))
    ,   ("bottom",     Vector(( 0,  0,   -1  )))
    ,   ("persp",      Vector((-1, -1,    0.7)))
    ,   ("persp_back", Vector(( 1,  1,     0.7)))
    ]
    # カメラ距離 (= シーン bbox 対角長 × 1.8、最低 0.3m、_position_camera と同じ)
    distance = max(scene_bb["diagonal"] * 1.8, 0.3)
    scene_center = scene_bb["center"]
    # 視野角内かどうかの判定用 cos(半角)
    cos_half_fov = math.cos(math.radians(fov_deg * 0.5))

    # オブジェクトの world matrix (頂点・法線変換用)
    mat_world = obj.matrix_world
    # 法線変換用 (回転成分のみの逆転置)
    nmat = mat_world.to_3x3().inverted_safe().transposed()
    polygons = obj.data.polygons
    polygon_region_ids = _polygon_region_ids(obj.data)
    polygon_world_areas = []
    for poly in polygons:
        world_points = [
            mat_world @ obj.data.vertices[index].co
            for index in poly.vertices
        ]
        area = 0.0
        if len(world_points) >= 3:
            origin = world_points[0]
            for index in range(1, len(world_points) - 1):
                area += ((world_points[index] - origin).cross(
                    world_points[index + 1] - origin
                )).length * 0.5
        polygon_world_areas.append(area)

    # === occlusion 判定用: world 座標の BVHTree を構築 ===
    # face center からカメラへのレイで「自分の face が最初にヒットするか」を判定
    # = この face が実際に画面に映るか
    bvh = None
    try:
        deps = bpy.context.evaluated_depsgraph_get()
        bm_bvh = bmesh.new()
        bm_bvh.from_object(obj, deps)
        bm_bvh.transform(mat_world)
        bvh = BVHTree.FromBMesh(bm_bvh)
        bm_bvh.free()
    except Exception:
        bvh = None

    per_angle = {}
    for name, direction in angles:
        direction_n = direction.normalized()
        cam_pos = scene_center + direction_n * distance
        # カメラの forward = scene_center - cam_pos (= シーン中心を見る方向)
        cam_forward = (scene_center - cam_pos).normalized()

        in_view_total    = 0    # 視野内 face 数 (occlusion 無視、全 face)
        in_view_inverted = 0    # 視野内 + 裏向き face 数 (occlusion 無視)
        visible_total    = 0    # occlusion 考慮: 実際に画面に映る face 数
        visible_inverted = 0    # occlusion 考慮: 画面に映る face のうち裏向き
        visible_world_area = 0.0
        visible_inverted_world_area = 0.0
        visible_by_region = Counter()
        visible_inverted_by_region = Counter()
        visible_world_area_by_region = Counter()
        visible_inverted_world_area_by_region = Counter()
        visible_inverted_examples = []
        for poly in polygons:
            # face center を world 座標に変換
            face_center_world = mat_world @ poly.center
            # face normal を world 座標に変換
            face_normal_world = (nmat @ poly.normal).normalized()
            # カメラから face への方向ベクトル
            cam_to_face = face_center_world - cam_pos
            cam_to_face_len = cam_to_face.length
            if cam_to_face_len < 1e-9:
                continue
            cam_to_face_n = cam_to_face / cam_to_face_len
            # 視錐台内判定: カメラ前方 (forward と同方向) かつ視野角内
            forward_dot = cam_to_face_n.dot(cam_forward)
            if forward_dot < cos_half_fov:
                continue   # 画面外 (視野角外 or 後方)
            in_view_total += 1
            # 裏向き判定: facing_dot > 0 = 法線が視線方向と同じ = 裏向き
            facing_dot = face_normal_world.dot(cam_to_face_n)
            is_inverted = (facing_dot > 0.05)
            if is_inverted:
                in_view_inverted += 1

            # === occlusion 判定: カメラ位置から face center に向けてレイキャスト ===
            # 自身の face が最初にヒットすれば「画面に映る」
            # 別の face が手前にあれば「occluded」
            if bvh is not None:
                # face center からカメラに向けて少しオフセットした位置から逆方向にレイ
                # (= カメラ位置からのレイで自身を hit させやすくするため、
                #    オフセット起点で「カメラ → face」方向にレイを撃つ)
                ray_origin = cam_pos + cam_to_face_n * 0.00001
                hit_loc, hit_norm, hit_idx, hit_dist = bvh.ray_cast(ray_origin, cam_to_face_n)
                if hit_loc is not None and hit_idx is not None:
                    # 自身の face が最初に hit すれば見える
                    # = hit 位置と face center の距離が小さい。旧 0.1% 許容は
                    # 1.83 m の筐体で約 2 mm となり、板金の裏面や重なった部品まで
                    # 「同じ可視面」と誤認していた。50 µm 程度へ絞り、実際の
                    # face-center hit だけを採用する（基準を緩める変更ではない）。
                    pos_diff = (Vector(hit_loc) - face_center_world).length
                    threshold = max(scene_bb["diagonal"] * 0.000001, 0.00005)
                    if pos_diff < threshold:
                        visible_total += 1
                        region_id = polygon_region_ids[poly.index]
                        face_world_area = polygon_world_areas[poly.index]
                        visible_world_area += face_world_area
                        visible_by_region[region_id] += 1
                        visible_world_area_by_region[region_id] += face_world_area
                        if is_inverted:
                            visible_inverted += 1
                            visible_inverted_world_area += face_world_area
                            visible_inverted_by_region[region_id] += 1
                            visible_inverted_world_area_by_region[region_id] += face_world_area
                            if len(visible_inverted_examples) < 64:
                                material_index = int(poly.material_index)
                                material_name = ""
                                if 0 <= material_index < len(obj.data.materials):
                                    material = obj.data.materials[material_index]
                                    material_name = material.name if material else ""
                                visible_inverted_examples.append({
                                    "face_index": int(poly.index),
                                    "region_id": int(region_id),
                                    "material_index": material_index,
                                    "material_name": material_name,
                                    "center_world": [
                                        round(float(value), 6)
                                        for value in face_center_world
                                    ],
                                    "normal_world": [
                                        round(float(value), 6)
                                        for value in face_normal_world
                                    ],
                                    "camera_facing_dot": round(float(facing_dot), 6),
                                    "first_hit_distance_to_center": round(float(pos_diff), 8),
                                })

        ratio = (in_view_inverted / in_view_total) if in_view_total > 0 else 0.0
        # occlusion 考慮版: 実際に画面に見える face のうち裏向きの比率
        # 閉じた正常メッシュなら 0、局所的な反転がある場合だけ > 0 になる
        visible_ratio = (visible_inverted / visible_total) if visible_total > 0 else 0.0
        visible_world_area_ratio = (
            visible_inverted_world_area / visible_world_area
            if visible_world_area > 1.0e-15 else 0.0
        )
        per_angle[name] = {
            "in_view_faces":          in_view_total
        ,   "in_view_inverted":       in_view_inverted
        ,   "in_view_inverted_ratio": round(ratio, 4)
        ,   "visible_faces":          visible_total      # occlusion 後
        ,   "visible_inverted":       visible_inverted
        ,   "visible_inverted_ratio": round(visible_ratio, 4)
        ,   "visible_world_area": round(visible_world_area, 9)
        ,   "visible_inverted_world_area": round(visible_inverted_world_area, 9)
        ,   "visible_inverted_world_area_ratio": round(visible_world_area_ratio, 6)
        ,   "visible_by_region": {
                str(region_id): count
                for region_id, count in sorted(visible_by_region.items())
            }
        ,   "visible_inverted_by_region": {
                str(region_id): count
                for region_id, count in sorted(visible_inverted_by_region.items())
            }
        ,   "visible_world_area_by_region": {
                str(region_id): round(area, 9)
                for region_id, area in sorted(visible_world_area_by_region.items())
            }
        ,   "visible_inverted_world_area_by_region": {
                str(region_id): round(area, 9)
                for region_id, area in sorted(visible_inverted_world_area_by_region.items())
            }
        ,   "visible_inverted_examples": visible_inverted_examples
        }

    # 最悪アングル (= 視認可能 face のうち裏向き比率が最大)
    # occlusion 考慮版を主指標にする
    if per_angle:
        worst_name, worst_data = max(
            per_angle.items()
        ,   key=lambda kv: kv[1]["visible_inverted_world_area_ratio"]
        )
        worst_ratio = worst_data["in_view_inverted_ratio"]
        worst_visible_ratio = worst_data["visible_inverted_ratio"]
        worst_visible_area_ratio = worst_data["visible_inverted_world_area_ratio"]
    else:
        worst_name = None
        worst_ratio = 0.0
        worst_visible_ratio = 0.0
        worst_visible_area_ratio = 0.0
    return {
        "worst_angle_name":             worst_name
    ,   "worst_inverted_ratio":         worst_ratio          # 旧指標 (occlusion 無し、参考)
    ,   "worst_visible_inverted_ratio": worst_visible_ratio  # 主指標 (occlusion 考慮)
    ,   "worst_visible_inverted_world_area_ratio": worst_visible_area_ratio
    ,   "per_angle":                    per_angle
    }


def _compute_size_ratios(mesh_objs):
    """
    各メッシュの bbox から「最大寸法」を取り、
    最大の reference_size を 1.0 として比率計算する

    Output:
        {
            "reference_object": str (基準オブジェクト名)
        ,   "reference_size":   float (XYZ 最大値の中で最大、メートル単位)
        ,   "objects": [
                {
                    "name":     str
                ,   "size_x":   float (絶対値、メートル)
                ,   "size_y":   float
                ,   "size_z":   float
                ,   "max_dim":  float (XYZ 最大値)
                ,   "ratio_to_ref": float (max_dim / reference_size)
                }
            ]
        }
    """
    if not mesh_objs:
        return {"reference_object": None, "reference_size": 0.0, "objects": []}

    obj_sizes = []
    for obj in mesh_objs:
        bb = _compute_object_bounding_box(obj)
        sx, sy, sz = bb["size"].x, bb["size"].y, bb["size"].z
        max_dim = max(sx, sy, sz)
        obj_sizes.append({
            "name":     obj.name
        ,   "size_x":   round(sx, 5)
        ,   "size_y":   round(sy, 5)
        ,   "size_z":   round(sz, 5)
        ,   "max_dim":  round(max_dim, 5)
        })

    # 基準 = 最大 max_dim を持つオブジェクト
    ref = max(obj_sizes, key=lambda o: o["max_dim"])
    ref_size = ref["max_dim"]
    ref_name = ref["name"]
    if ref_size <= 0:
        ref_size = 1.0

    for o in obj_sizes:
        o["ratio_to_ref"] = round(o["max_dim"] / ref_size, 4)

    return {
        "reference_object": ref_name
    ,   "reference_size":  round(ref_size, 5)
    ,   "objects":         obj_sizes
    }


def _compare_with_reference_ratios(mesh_objs, reference_ratios):
    """
    参考画像から計測したパーツ比率 (reference_ratios) と
    現モデルの実比率を比較し、各パーツ・寸法ごとの差分を返す

    reference_ratios の形式:
        {
            "reference_part":   "pot",
            "reference_dim":    "diameter",   # diameter/height/length/max
            "parts": {
                "pot":    { "match": "_pot$",   "diameter": 1.0, "height": 0.65 },
                "caudex": { "match": "_caudex$","diameter": 0.68 },
                ...
            }
        }
        - "match" は対象オブジェクトの名前末尾正規表現 (簡易: substring 一致)
        - 各 part に対して期待値 (鉢直径=1.0 を基準とした比率) を辞書で指定
        - "diameter" = X/Y のうち大きい方、"height" = Z、"length" = max
        - "max" = XYZ最大

    Output:
        {
            "reference_part":  str
        ,   "reference_dim":   str
        ,   "reference_size":  float (m単位、基準パーツの実寸)
        ,   "rows": [
                {
                    "part_name":     str
                ,   "matched_obj":   str (実オブジェクト名)
                ,   "dimension":     "diameter" | "height" | "length"
                ,   "expected_ratio": float
                ,   "actual_size":   float (m単位)
                ,   "actual_ratio":  float (実寸 / reference_size)
                ,   "diff_percent":  float (signed % diff)
                }, ...
            ]
        }
    """
    import re
    parts_def = reference_ratios.get("parts", {})
    ref_part_key = reference_ratios.get("reference_part")
    ref_dim_key  = reference_ratios.get("reference_dim", "diameter")

    # 各 part_key に対して該当する実オブジェクトを名前マッチで探す
    def find_obj(match_pattern):
        for obj in mesh_objs:
            if re.search(match_pattern, obj.name):
                return obj
        return None

    def get_dimension(obj, dim_key):
        bb = _compute_object_bounding_box(obj)
        sx, sy, sz = bb["size"].x, bb["size"].y, bb["size"].z
        if dim_key == "height":
            return sz
        elif dim_key == "diameter":
            return max(sx, sy)
        elif dim_key == "length":
            return max(sx, sy, sz)
        elif dim_key == "max":
            return max(sx, sy, sz)
        else:
            return max(sx, sy, sz)

    # 基準パーツの実寸取得
    ref_part_def = parts_def.get(ref_part_key, {})
    ref_obj = find_obj(ref_part_def.get("match", "")) if ref_part_def else None
    ref_size = get_dimension(ref_obj, ref_dim_key) if ref_obj else 1.0
    if ref_size <= 0:
        ref_size = 1.0

    rows = []
    for part_key, part_def in parts_def.items():
        match_pat = part_def.get("match", part_key)
        obj = find_obj(match_pat)
        if obj is None:
            rows.append({
                "part_name":     part_key
            ,   "matched_obj":   None
            ,   "dimension":     "(unmatched)"
            ,   "expected_ratio": None
            ,   "actual_size":   None
            ,   "actual_ratio":  None
            ,   "diff_percent":  None
            })
            continue
        # 各寸法 (diameter / height / length) ごとに比較
        for dim_key in ["diameter", "height", "length"]:
            if dim_key not in part_def:
                continue
            expected = part_def[dim_key]
            actual_size = get_dimension(obj, dim_key)
            actual_ratio = actual_size / ref_size if ref_size > 0 else 0
            if expected != 0:
                diff_percent = (actual_ratio - expected) / expected * 100.0
            else:
                diff_percent = 0
            rows.append({
                "part_name":     part_key
            ,   "matched_obj":   obj.name
            ,   "dimension":     dim_key
            ,   "expected_ratio": round(expected, 4)
            ,   "actual_size":   round(actual_size, 5)
            ,   "actual_ratio":  round(actual_ratio, 4)
            ,   "diff_percent":  round(diff_percent, 1)
            })

    return {
        "reference_part":  ref_part_key
    ,   "reference_dim":   ref_dim_key
    ,   "reference_size":  round(ref_size, 5)
    ,   "rows":            rows
    }


# ============================================================
# B: クローズアップ ROI 自動算出
# ============================================================
def _build_closeup_rois(scene_bb):
    """
    シーン bbox を上/下/左/右半分に切って、それぞれをカメラ ROI とする
    ROI ごとの (名前, ROI bbox dict, カメラ方向) を返す

    Output:
        list[(name: str, roi_bb: dict, direction: Vector)]
    """
    closeups = []
    bb_min = scene_bb["min"]
    bb_max = scene_bb["max"]
    bb_size = scene_bb["size"]
    bb_center = scene_bb["center"]

    # 上 60% (z 上) - 塊根上端〜葉束 を確認
    upper_min = Vector((bb_min.x, bb_min.y, bb_min.z + bb_size.z * 0.40))
    upper_max = Vector(bb_max)
    closeups.append(("upper", _make_roi_bb(upper_min, upper_max), Vector((-1, -1, 0.5))))

    # 下 60% (z 下) - 鉢〜土 を確認
    lower_min = Vector(bb_min)
    lower_max = Vector((bb_max.x, bb_max.y, bb_min.z + bb_size.z * 0.60))
    closeups.append(("lower", _make_roi_bb(lower_min, lower_max), Vector((-1, -1, 0.5))))

    # 左半分 (x 負側) - 左側の枝/葉束を確認
    left_min = Vector(bb_min)
    left_max = Vector((bb_min.x + bb_size.x * 0.55, bb_max.y, bb_max.z))
    closeups.append(("left", _make_roi_bb(left_min, left_max), Vector((0, -1, 0.3))))

    # 右半分 (x 正側) - 右側の枝/葉束を確認
    right_min = Vector((bb_min.x + bb_size.x * 0.45, bb_min.y, bb_min.z))
    right_max = Vector(bb_max)
    closeups.append(("right", _make_roi_bb(right_min, right_max), Vector((0, -1, 0.3))))

    # ▼ 細部 (= 質感/テクスチャ評価用) closeup
    #   bb 中心付近の 25% × 25% 領域 を切り出し → カメラが ROI に近寄り 約 4x 拡大
    #   従来 closeup_*.png ではブロック 1 個が 30〜40px しか映らないため、
    #   マテリアル/テクスチャ評価 (互い違いの溝、押縁石の凸み 等) には不十分.
    #   この detail_* で 1 ブロックが 100px 程度に映る前提で 質感を判定する.
    detail_w = bb_size.x * 0.25      # X 25%
    detail_h = bb_size.z * 0.25      # Z 25%
    detail_d = bb_size.y             # Y 全体 (奥行は薄いオブジェクトでも切らない)
    # 上半分 中央付近 (= 塀の切石部 等の上半身に焦点)
    du_center_z = bb_min.z + bb_size.z * 0.75
    du_min = Vector((
        bb_center.x - detail_w * 0.5
    ,   bb_min.y
    ,   du_center_z - detail_h * 0.5
    ))
    du_max = Vector((
        bb_center.x + detail_w * 0.5
    ,   bb_max.y
    ,   du_center_z + detail_h * 0.5
    ))
    closeups.append(("detail_upper", _make_roi_bb(du_min, du_max), Vector((0, -1, 0.15))))
    # 下半分 中央付近 (= 鉢 / コンクリ部 等の下半身に焦点)
    dl_center_z = bb_min.z + bb_size.z * 0.25
    dl_min = Vector((
        bb_center.x - detail_w * 0.5
    ,   bb_min.y
    ,   dl_center_z - detail_h * 0.5
    ))
    dl_max = Vector((
        bb_center.x + detail_w * 0.5
    ,   bb_max.y
    ,   dl_center_z + detail_h * 0.5
    ))
    closeups.append(("detail_lower", _make_roi_bb(dl_min, dl_max), Vector((0, -1, 0.15))))

    return closeups


def _make_roi_bb(bb_min, bb_max):
    """指定 min/max からカメラ配置可能な bbox dict を作る"""
    size = bb_max - bb_min
    return {
        "min":      bb_min
    ,   "max":      bb_max
    ,   "center":   (bb_min + bb_max) * 0.5
    ,   "size":     size
    ,   "diagonal": size.length
    }


# ============================================================
# 内部: シーンバウンディングボックス計算
# ============================================================
def _compute_scene_bounding_box():
    """シーン全メッシュ (hide_render=False) のワールド空間 BB"""
    min_co = Vector((float("inf"),) * 3)
    max_co = Vector((float("-inf"),) * 3)
    found = False
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render:
            continue
        for corner in obj.bound_box:
            world_co = obj.matrix_world @ Vector(corner)
            min_co.x = min(min_co.x, world_co.x); max_co.x = max(max_co.x, world_co.x)
            min_co.y = min(min_co.y, world_co.y); max_co.y = max(max_co.y, world_co.y)
            min_co.z = min(min_co.z, world_co.z); max_co.z = max(max_co.z, world_co.z)
            found = True
    if not found:
        min_co = Vector((-1.0, -1.0, -1.0))
        max_co = Vector(( 1.0,  1.0,  1.0))
    return _make_roi_bb(min_co, max_co)


def _compute_object_bounding_box(obj):
    """指定 1 オブジェクトのワールド空間 BB を bbox dict 形式で返す"""
    min_co = Vector((float("inf"),) * 3)
    max_co = Vector((float("-inf"),) * 3)
    for corner in obj.bound_box:
        wc = obj.matrix_world @ Vector(corner)
        min_co.x = min(min_co.x, wc.x); max_co.x = max(max_co.x, wc.x)
        min_co.y = min(min_co.y, wc.y); max_co.y = max(max_co.y, wc.y)
        min_co.z = min(min_co.z, wc.z); max_co.z = max(max_co.z, wc.z)
    return _make_roi_bb(min_co, max_co)


# ============================================================
# 内部: シーン統計収集 (info.json)
# ============================================================
def _collect_scene_info(project_name, scene_bb):
    objects_info = []
    total_vertices = 0
    total_faces = 0
    materials_set = set()
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and obj.data is not None:
            n_verts = len(obj.data.vertices)
            n_faces = len(obj.data.polygons)
            total_vertices += n_verts
            total_faces += n_faces
            mat_names = [m.name for m in obj.data.materials if m is not None]
            materials_set.update(mat_names)
        else:
            n_verts = 0; n_faces = 0; mat_names = []
        bb_min = [float("inf")] * 3
        bb_max = [float("-inf")] * 3
        for corner in obj.bound_box:
            wc = obj.matrix_world @ Vector(corner)
            for i in range(3):
                bb_min[i] = min(bb_min[i], wc[i])
                bb_max[i] = max(bb_max[i], wc[i])
        objects_info.append({
            "name":         obj.name
        ,   "type":         obj.type
        ,   "vertices":     n_verts
        ,   "faces":        n_faces
        ,   "materials":    mat_names
        ,   "location":     [round(v, 4) for v in obj.location]
        ,   "bounding_box": {
                "min": [round(v, 4) for v in bb_min]
            ,   "max": [round(v, 4) for v in bb_max]
            }
        })
    scene_bb_out = {
        "min":  [round(v, 4) for v in scene_bb["min"]]
    ,   "max":  [round(v, 4) for v in scene_bb["max"]]
    ,   "size": [round(v, 4) for v in scene_bb["size"]]
    }
    return {
        "project_name": project_name
    ,   "executed_at":  datetime.now().isoformat(timespec="seconds")
    ,   "scene_stats": {
            "object_count":   len(objects_info)
        ,   "total_vertices": total_vertices
        ,   "total_faces":    total_faces
        ,   "bounding_box":   scene_bb_out
        }
    ,   "objects":   objects_info
    ,   "materials": sorted(materials_set)
    }


# ============================================================
# C-2: face orientation overlay (青=表 / 赤=裏) 可視化レンダ
# ============================================================
# Blender の viewport overlay 「Face Orientation」(show_face_orientation)
# を有効にした状態で OpenGL レンダ (workbench/SOLID) を行い、
# face の向きを色付きで可視化した画像を出力する。
# 人間が画像 1 枚で「赤い面が見える範囲にあるか」を確認できる。
#
# Input :
#   output_dir : 出力ディレクトリ
#   scene_bb   : シーン bbox (カメラ配置用)
#   camera     : 一時カメラ (= 全景レンダで使うのと同じ)
#   resolution : (横, 縦) ピクセル
# Output:
#   <output_dir>/face_orientation_persp.png
#   <output_dir>/face_orientation_top.png
def _render_face_orientation_overlay(output_dir, scene_bb, camera, resolution):
    scene = bpy.context.scene
    # VIEW_3D area を探して、その overlay と shading を一時的に変更する
    view3d_area = None
    view3d_region = None
    view3d_space = None
    for area in bpy.context.window.screen.areas:
        if area.type == 'VIEW_3D':
            view3d_area = area
            for region in area.regions:
                if region.type == 'WINDOW':
                    view3d_region = region
                    break
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    view3d_space = space
                    break
            if view3d_region and view3d_space:
                break
    if view3d_area is None or view3d_region is None or view3d_space is None:
        print("[claude_preview] No VIEW_3D area found (headless?). Skipping face_orientation render.")
        return

    # 設定を保存 (復元用)
    saved_show_face_orient = view3d_space.overlay.show_face_orientation
    saved_show_overlay     = view3d_space.overlay.show_overlays
    saved_shading_type     = view3d_space.shading.type
    saved_view_perspective = view3d_space.region_3d.view_perspective
    saved_camera           = scene.camera
    # 不要オーバーレイ (グリッド等) も一時 OFF にして、向き色だけ見やすく
    saved_show_floor       = view3d_space.overlay.show_floor
    saved_show_axis_x      = view3d_space.overlay.show_axis_x
    saved_show_axis_y      = view3d_space.overlay.show_axis_y

    try:
        # face orientation overlay を有効化、shading を SOLID (workbench) に
        view3d_space.overlay.show_overlays         = True
        view3d_space.overlay.show_face_orientation = True
        view3d_space.overlay.show_floor            = False
        view3d_space.overlay.show_axis_x           = False
        view3d_space.overlay.show_axis_y           = False
        view3d_space.shading.type                  = 'SOLID'
        # 解像度を保証
        scene.render.resolution_x = resolution[0]
        scene.render.resolution_y = resolution[1]
        scene.camera = camera
        # viewport view を camera 視点に切り替え (= temp_camera からの view を使う)
        view3d_space.region_3d.view_perspective = 'CAMERA'

        # 6 アングル全て出力 (= A-1 の per_angle と一致させる、worst angle を必ず確認可能)
        # view_context=True にすると viewport の overlay 設定が反映される (= 青/赤 見える)
        angles = [
            ("front",      Vector(( 0, -1,    0  )))
        ,   ("back",       Vector(( 0,  1,    0  )))
        ,   ("side_right", Vector(( 1,  0,    0  )))
        ,   ("side_left",  Vector((-1,  0,    0  )))
        ,   ("top",        Vector(( 0,  0,    1  )))
        ,   ("bottom",     Vector(( 0,  0,   -1  )))
        ,   ("persp",      Vector((-1, -1,    0.7)))
        ,   ("persp_back", Vector(( 1,  1,     0.7)))
        ]
        for name, direction in angles:
            _position_camera(
                camera       = camera
            ,   direction    = direction
            ,   scene_bb     = scene_bb
            ,   orthographic = (name not in {"persp", "persp_back"})
            )
            scene.render.filepath = os.path.join(output_dir, f"face_orientation_{name}.png")
            try:
                with bpy.context.temp_override(area=view3d_area, region=view3d_region):
                    bpy.ops.render.opengl(write_still=True, view_context=True)
            except Exception as e:
                print(f"[claude_preview] face_orientation_{name} render failed: {e}")
    finally:
        # 設定を復元
        view3d_space.overlay.show_face_orientation = saved_show_face_orient
        view3d_space.overlay.show_overlays         = saved_show_overlay
        view3d_space.overlay.show_floor            = saved_show_floor
        view3d_space.overlay.show_axis_x           = saved_show_axis_x
        view3d_space.overlay.show_axis_y           = saved_show_axis_y
        view3d_space.shading.type                  = saved_shading_type
        view3d_space.region_3d.view_perspective    = saved_view_perspective
        scene.camera = saved_camera


# ============================================================
# 内部: 一時カメラ生成
# ============================================================
def _create_temp_camera():
    cam_data = bpy.data.cameras.new(name="_claude_preview_cam")
    cam_obj  = bpy.data.objects.new(name="_claude_preview_cam", object_data=cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    return cam_obj


# ============================================================
# 内部: 一時 SUN ライト + 補助 World 環境光 設定
# ============================================================
# マテリアル評価向けに sun + world ambient の組み合わせで明度を調整する。
#
# 設計方針:
#   - sun energy = 1.8: 拡散反射率 ~0.5 までを「中明度」として識別できる強さ
#                       これより低いと暗いマテリアル (鉢黒 0.05 等) も識別不能になる
#                       これより高いと いぶし銀 (0.21) や石材 (0.8) が白飛びする
#   - world ambient = 0.30: 影側が完全に黒くならず 形状が認識できる程度の補光
#                            (これより高いと 全体が眠くなり 立体感が失われる)
#   - sun の角度 (45°, 0°, 45°): 上から斜めに照射して 形状の凹凸が出るよう
#
# 過去設定 (energy=7.0) は屋外晴天並みの強さで、 暗いマテリアル評価には適していたが
# 中明度マテリアル (Base Color 0.2 以上) が一律で白飛びしていたため 1.8 に下げた。
def _create_temp_light():
    # SUN ライト
    # energy=1.0 は実質太陽光基準値。 view_transform=Standard (線形表示) と組合せて
    # 反射率 0.21 のマテリアルが 表示で sRGB 0.50 (中グレー) に見える設定。
    # マテリアル色そのものに近い見え方になる。
    light_data = bpy.data.lights.new(name="_claude_preview_light", type="SUN")
    light_data.energy = 1.0
    light_obj = bpy.data.objects.new(name="_claude_preview_light", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.rotation_euler = (math.radians(45), 0, math.radians(45))

    # World 補助光 (影側補光)
    # color=0.20, strength=1.0 で 影側が完全に黒くならず 形状が認識できる程度
    # (これより高いと 影部の マテリアル色が ほぼ ambient で薄く 立体感が失われる)
    world = bpy.context.scene.world
    if world is not None and world.use_nodes and world.node_tree is not None:
        bg = world.node_tree.nodes.get("Background")
        if bg is not None:
            bg.inputs[0].default_value = (0.20, 0.20, 0.20, 1.0)
            bg.inputs[1].default_value = 1.0

    return light_obj


# ============================================================
# 内部: カメラ配置
# ============================================================
def _create_observation_emission_material(material_name):
    """
    Input: 一時material名。
    Output: Color入力をEmissionへ直結した、照明非依存の一時material。
    """
    material = bpy.data.materials.new(name=material_name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    nodes.clear()
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    emission_node = nodes.new(type="ShaderNodeEmission")
    links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])
    return material, emission_node


def _scene_camera_distance_range(camera, scene_bb):
    """
    Input: cameraと評価対象bbox。
    Output: bbox 8隅のcamera距離から求めたnear/far。depth表示だけに使う。
    """
    corners = []
    for x in (scene_bb["min"].x, scene_bb["max"].x):
        for y in (scene_bb["min"].y, scene_bb["max"].y):
            for z in (scene_bb["min"].z, scene_bb["max"].z):
                corners.append(Vector((x, y, z)))
    distances = [(corner - camera.location).length for corner in corners]
    near_distance = min(distances)
    far_distance = max(distances)
    if far_distance - near_distance < 1.0e-6:
        far_distance = near_distance + max(scene_bb["diagonal"], 1.0)
    return near_distance, far_distance


def _render_part_id_observation_pass(
    output_dir
,   scene_bb
,   camera
,   angles
,   legend_filename = "part_id_legend.json"
):
    """
    Input: 現scene、固定camera群。
    Output: part_id_<view>.pngとpart_id_legend.json。

    G2～G6で意味partを別Meshとして保持する規則を利用し、object単位のflat ID色を出す。
    共有mesh dataや元materialを壊さないよう、render中だけdata copyへ差し替える。
    G7 join後のregion_id評価は別のattribute検査を正本とし、このpassだけで代用しない。
    """
    scene = bpy.context.scene
    mesh_objects = [
        obj for obj in scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ]
    saved_data = {}
    temporary_data = []
    temporary_materials = []
    legend = {}
    try:
        color_index = 0
        for obj in sorted(mesh_objects, key=lambda item: item.name):
            saved_data[obj.name] = obj.data
            data_copy = obj.data.copy()
            temporary_data.append(data_copy)
            obj.data = data_copy
            obj.data.materials.clear()

            polygon_region_ids = _polygon_region_ids(obj.data)
            region_attribute_name = _polygon_region_attribute_name(obj.data)
            polygon_region_counts = Counter(polygon_region_ids)
            region_ids = sorted(set(polygon_region_ids))
            material_by_region = {}
            for region_id in region_ids:
                hue = (color_index * 0.6180339887498949) % 1.0
                rgb = colorsys.hsv_to_rgb(hue, 0.72, 1.0)
                material, emission_node = _create_observation_emission_material(
                    material_name="_claude_part_id_%04d" % color_index
                )
                emission_node.inputs["Color"].default_value = (
                    rgb[0], rgb[1], rgb[2], 1.0
                )
                emission_node.inputs["Strength"].default_value = 1.0
                temporary_materials.append(material)
                obj.data.materials.append(material)
                material_by_region[region_id] = len(obj.data.materials) - 1
                legend_key = "%s::region_%s" % (obj.name, region_id)
                legend[legend_key] = {
                    "index": color_index
                ,   "rgb": [round(component, 6) for component in rgb]
                ,   "object": obj.name
                ,   "region_id": region_id
                ,   "attribute_name": region_attribute_name
                ,   "polygon_count": polygon_region_counts[region_id]
                ,   "region_id_note": (
                        "Uses FACE/POINT/CORNER region_id when present; "
                        "falls back to one object-owned region."
                    )
                }
                color_index += 1
            for polygon, region_id in zip(obj.data.polygons, polygon_region_ids):
                polygon.material_index = material_by_region[region_id]

        for name, direction in angles:
            _position_camera(
                camera       = camera
            ,   direction    = direction
            ,   scene_bb     = scene_bb
            ,   orthographic = (name not in {"persp", "persp_back"})
            )
            scene.render.filepath = os.path.join(output_dir, "part_id_%s.png" % name)
            bpy.ops.render.render(write_still=True)
        with open(os.path.join(output_dir, legend_filename), "w", encoding="utf-8") as handle:
            json.dump(legend, handle, ensure_ascii=False, indent=2)
    finally:
        for obj_name, original_data in saved_data.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is not None:
                obj.data = original_data
        for data in temporary_data:
            if data.users == 0:
                bpy.data.meshes.remove(data)
        for material in temporary_materials:
            if material.name in bpy.data.materials:
                bpy.data.materials.remove(material)


def _polygon_region_ids(mesh):
    """
    Input: 一時copy済みMesh。
    Output: polygon順のregion ID。FACEを最優先し、POINT/CORNERはface内modeへ集約する。

    region_idがなければ0を返す。平均は異なるIDの中間値を作るため使わない。
    """
    attribute = None
    # asset_part_id is the authored semantic ownership used by the v2 part
    # contract.  A reference-shape operator may also emit an internal
    # region_id (often the same value on every generated face); preferring it
    # collapses an otherwise valid assembled asset to one diagnostic colour.
    for attribute_name in ("asset_part_id", "semantic_part_id", "region_id"):
        attribute = mesh.attributes.get(attribute_name)
        if attribute is not None:
            break
    if attribute is None:
        return [0 for _polygon in mesh.polygons]

    def item_value(item):
        value = getattr(item, "value", 0)
        if isinstance(value, bool):
            return int(value)
        try:
            return int(round(float(value)))
        except (TypeError, ValueError):
            return 0

    if attribute.domain == "FACE" and len(attribute.data) == len(mesh.polygons):
        return [item_value(item) for item in attribute.data]
    if attribute.domain == "POINT" and len(attribute.data) == len(mesh.vertices):
        point_values = [item_value(item) for item in attribute.data]
        return [
            Counter(point_values[index] for index in polygon.vertices).most_common(1)[0][0]
            for polygon in mesh.polygons
        ]
    if attribute.domain == "CORNER" and len(attribute.data) == len(mesh.loops):
        corner_values = [item_value(item) for item in attribute.data]
        result = []
        for polygon in mesh.polygons:
            loop_values = corner_values[
                polygon.loop_start:polygon.loop_start + polygon.loop_total
            ]
            result.append(Counter(loop_values).most_common(1)[0][0])
        return result
    return [0 for _polygon in mesh.polygons]


def _polygon_region_attribute_name(mesh):
    """Return the semantic attribute selected for the part-ID pass."""
    for attribute_name in ("asset_part_id", "semantic_part_id", "region_id"):
        if mesh.attributes.get(attribute_name) is not None:
            return attribute_name
    return "object_fallback"


def _render_geometry_observation_passes(
    output_dir
,   scene_bb
,   camera
,   angles
,   part_id_legend_filename = "part_id_legend.json"
):
    """
    Input: beauty/silhouetteと同じcamera群。
    Output: part-ID、world-normal、正規化camera-depthのPNG群。

    形状比較用の診断画像であり、normal/depth画像を材質正本として使用しない。
    """
    scene = bpy.context.scene
    saved_override = bpy.context.view_layer.material_override
    saved_transparent = scene.render.film_transparent
    normal_material = None
    depth_material = None
    try:
        scene.render.film_transparent = True
        _render_part_id_observation_pass(
            output_dir = output_dir
        ,   scene_bb   = scene_bb
        ,   camera     = camera
        ,   angles     = angles
        ,   legend_filename = part_id_legend_filename
        )

        # World normalを[-1, 1]から[0, 1] RGBへ写像する。
        normal_material, normal_emission = _create_observation_emission_material(
            material_name="_claude_world_normal"
        )
        normal_nodes = normal_material.node_tree.nodes
        normal_links = normal_material.node_tree.links
        geometry_node = normal_nodes.new(type="ShaderNodeNewGeometry")
        multiply_node = normal_nodes.new(type="ShaderNodeVectorMath")
        multiply_node.operation = "MULTIPLY"
        multiply_node.inputs[1].default_value = (0.5, 0.5, 0.5)
        add_node = normal_nodes.new(type="ShaderNodeVectorMath")
        add_node.operation = "ADD"
        add_node.inputs[1].default_value = (0.5, 0.5, 0.5)
        normal_links.new(geometry_node.outputs["Normal"], multiply_node.inputs[0])
        normal_links.new(multiply_node.outputs["Vector"], add_node.inputs[0])
        normal_links.new(add_node.outputs["Vector"], normal_emission.inputs["Color"])
        normal_emission.inputs["Strength"].default_value = 1.0
        bpy.context.view_layer.material_override = normal_material
        for name, direction in angles:
            _position_camera(
                camera       = camera
            ,   direction    = direction
            ,   scene_bb     = scene_bb
            ,   orthographic = (name not in {"persp", "persp_back"})
            )
            scene.render.filepath = os.path.join(output_dir, "normal_%s.png" % name)
            bpy.ops.render.render(write_still=True)

        # Camera distanceを各viewのbbox near/farへ正規化する。
        depth_material, depth_emission = _create_observation_emission_material(
            material_name="_claude_camera_depth"
        )
        depth_nodes = depth_material.node_tree.nodes
        depth_links = depth_material.node_tree.links
        camera_data_node = depth_nodes.new(type="ShaderNodeCameraData")
        map_range_node = depth_nodes.new(type="ShaderNodeMapRange")
        map_range_node.clamp = True
        map_range_node.inputs["To Min"].default_value = 0.0
        map_range_node.inputs["To Max"].default_value = 1.0
        depth_links.new(camera_data_node.outputs["View Distance"], map_range_node.inputs["Value"])
        depth_links.new(map_range_node.outputs["Result"], depth_emission.inputs["Color"])
        depth_emission.inputs["Strength"].default_value = 1.0
        bpy.context.view_layer.material_override = depth_material
        for name, direction in angles:
            _position_camera(
                camera       = camera
            ,   direction    = direction
            ,   scene_bb     = scene_bb
            ,   orthographic = (name not in {"persp", "persp_back"})
            )
            near_distance, far_distance = _scene_camera_distance_range(
                camera   = camera
            ,   scene_bb = scene_bb
            )
            map_range_node.inputs["From Min"].default_value = near_distance
            map_range_node.inputs["From Max"].default_value = far_distance
            scene.render.filepath = os.path.join(output_dir, "depth_%s.png" % name)
            bpy.ops.render.render(write_still=True)
    finally:
        bpy.context.view_layer.material_override = saved_override
        scene.render.film_transparent = saved_transparent
        for material in (normal_material, depth_material):
            if material is not None and material.name in bpy.data.materials:
                bpy.data.materials.remove(material)


def _region_id_bounding_box(region_ids):
    """Return a world-space bbox owned by the requested FACE region IDs."""
    wanted = {int(value) for value in region_ids}
    minimum = Vector((float("inf"),) * 3)
    maximum = Vector((float("-inf"),) * 3)
    found = False
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH" or obj.hide_render or obj.data is None:
            continue
        polygon_ids = _polygon_region_ids(obj.data)
        for polygon, region_id in zip(obj.data.polygons, polygon_ids):
            if int(region_id) not in wanted:
                continue
            for vertex_index in polygon.vertices:
                world = obj.matrix_world @ obj.data.vertices[vertex_index].co
                minimum.x = min(minimum.x, world.x)
                minimum.y = min(minimum.y, world.y)
                minimum.z = min(minimum.z, world.z)
                maximum.x = max(maximum.x, world.x)
                maximum.y = max(maximum.y, world.y)
                maximum.z = max(maximum.z, world.z)
                found = True
    return _make_roi_bb(minimum, maximum) if found else None


def _expanded_roi_bb(scene_bb, margin_ratio):
    size = scene_bb["size"]
    # Keep a non-zero front/back envelope so perspective and depth passes remain
    # stable even for nearly planar profile carriers.
    floor = max(size.x, size.z, 0.01) * 0.08
    margin = Vector((
        max(size.x * margin_ratio, floor),
        max(size.y * margin_ratio, floor),
        max(size.z * margin_ratio, floor),
    ))
    return _make_roi_bb(scene_bb["min"] - margin, scene_bb["max"] + margin)


def _render_semantic_region_closeups(output_dir, camera, closeups):
    """Render high-resolution beauty/ID/normal/depth packets for semantic ROIs.

    This proves observation coverage and semantic layout only.  It is not a
    visual-quality score and may not be used as a 0.99 claim by itself.
    """
    scene = bpy.context.scene
    saved_resolution = (scene.render.resolution_x, scene.render.resolution_y)
    packet = {
        "schema": "bpy_semantic_region_closeup_packet/v1",
        "quality_claim": False,
        "interpretation": (
            "Region-owned high-resolution observations; coverage and layout evidence only. "
            "Beauty/reference comparison remains an independent human-visible gate."
        ),
        "closeups": {},
    }
    try:
        for name, raw_spec in sorted(closeups.items()):
            spec = raw_spec if isinstance(raw_spec, dict) else {"region_ids": raw_spec}
            region_ids = [int(value) for value in spec["region_ids"]]
            roi = _region_id_bounding_box(region_ids)
            if roi is None:
                packet["closeups"][name] = {
                    "region_ids": region_ids,
                    "gate": "fail",
                    "reason": "no rendered mesh faces own the requested region IDs",
                }
                continue
            roi = _expanded_roi_bb(roi, float(spec.get("margin_ratio", 0.20)))
            resolution = spec.get("resolution", (1024, 1024))
            scene.render.resolution_x = int(resolution[0])
            scene.render.resolution_y = int(resolution[1])
            angles = (
                (f"roi_{name}_front", Vector((0, -1, 0))),
                (f"roi_{name}_persp", Vector((-1, -1, 0.35))),
            )
            for view_name, direction in angles:
                _position_camera(
                    camera=camera,
                    direction=direction,
                    scene_bb=roi,
                    orthographic=view_name.endswith("_front"),
                )
                scene.render.filepath = os.path.join(output_dir, f"{view_name}.png")
                bpy.ops.render.render(write_still=True)
            _render_geometry_observation_passes(
                output_dir=output_dir,
                scene_bb=roi,
                camera=camera,
                angles=angles,
                part_id_legend_filename=f"part_id_legend_roi_{name}.json",
            )
            packet["closeups"][name] = {
                "region_ids": region_ids,
                "resolution": [scene.render.resolution_x, scene.render.resolution_y],
                "world_bbox": {
                    "min": [float(value) for value in roi["min"]],
                    "max": [float(value) for value in roi["max"]],
                    "size": [float(value) for value in roi["size"]],
                },
                "views": [item[0] for item in angles],
                "gate": "pass",
            }
    finally:
        scene.render.resolution_x, scene.render.resolution_y = saved_resolution
        with open(os.path.join(output_dir, "semantic_region_closeups.json"), "w", encoding="utf-8") as handle:
            json.dump(packet, handle, ensure_ascii=False, indent=2)


def _position_camera(camera, direction, scene_bb, orthographic=False):
    """
    指定 bbox の中心を見るようにカメラを direction 方向に距離調整して配置
    固定方向の形状評価は正投影を使用する。persp/closeup 等は従来通り透視投影。
    正投影時は bbox 8頂点をカメラのright/up軸へ投影して画角を決めるため、
    奥行きによって正面シルエットの縦横比が変わらない。
    """
    direction_norm = direction.normalized()
    # 縦長オブジェクト (LPガスボンベ等) が フレームアウトしないよう
    # 係数を 0.95 → 1.1 → 1.4 に変更 (アンテナ等のワイドオブジェクト対応)
    distance = max(scene_bb["diagonal"] * 1.4, 0.3)
    camera.location = scene_bb["center"] + direction_norm * distance
    look_dir = (scene_bb["center"] - camera.location).normalized()
    rotation = look_dir.to_track_quat("-Z", "Y")
    camera.rotation_euler = rotation.to_euler()
    if not orthographic:
        camera.data.type = 'PERSP'
        return

    camera.data.type = 'ORTHO'
    right = rotation @ Vector((1.0, 0.0, 0.0))
    up = rotation @ Vector((0.0, 1.0, 0.0))
    center = scene_bb["center"]
    minimum = scene_bb["min"]
    maximum = scene_bb["max"]
    projected_right = []
    projected_up = []
    for x in (minimum.x, maximum.x):
        for y in (minimum.y, maximum.y):
            for z in (minimum.z, maximum.z):
                offset = Vector((x, y, z)) - center
                projected_right.append(offset.dot(right))
                projected_up.append(offset.dot(up))
    visible_width = max(projected_right) - min(projected_right)
    visible_height = max(projected_up) - min(projected_up)
    render_aspect = (
        bpy.context.scene.render.resolution_x
        / max(1, bpy.context.scene.render.resolution_y)
    )
    camera.data.ortho_scale = max(
        visible_height
    ,   visible_width / max(1.0e-6, render_aspect)
    ,   1.0e-4
    ) * 1.10


# ============================================================
# 内部: レンダリングエンジン設定 (フォールバック付き)
# ============================================================
def _set_render_engine(scene, candidates):
    for name in candidates:
        try:
            scene.render.engine = name
            if scene.render.engine == name:
                return name
        except Exception:
            continue
    return scene.render.engine
