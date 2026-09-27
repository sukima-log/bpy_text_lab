# CONTRIBUTING

このリポジトリでモデル・アセットを追加/改修する際のルールをまとめます。
コードのコメント・変数名は日本語主体ですが、これは制作者の作業ログを兼ねているためです。

---

## 配置先の判断基準

| 種類 | 配置先 | 判断基準 |
|---|---|---|
| 部品的・再利用可能なオブジェクト単体 | `Assets/parts/model/<CATEGORY>_ASSETS/` | 別プロジェクトから wrap 経由で呼び出して組み合わせる前提 |
| シーン全体・複数アセット組合せ | `Assets/mdl/<PROJECT_NAME>/` | 部屋・建物など、複数アセットを組み合わせて一つの場面を構成するもの |

命名規約: parts のカテゴリ名は `<CATEGORY>_ASSETS`（大文字 + 末尾 `_ASSETS`）。
新規カテゴリ / プロジェクトが必要になったときは、手動で `mkdir` せず必ず以下を使います。

```bash
# parts (部品アセット) を新規作成する場合
cd Assets/parts/model && bash 00_gen_project_dir.sh <CATEGORY>_ASSETS

# mdl (シーンプロジェクト) を新規作成する場合
cd Assets/mdl && bash 00_gen_project_dir.sh <PROJECT_NAME>
```

自動生成された `sample_obj_mdl.py` / `sample_obj_wrap.py` は、実装が終わったら削除してください。

---

## モデル作成のルール

### 1. 1 アセット = 1 ファイル 1 関数で完結

- 1 つの完成オブジェクトの生成処理は、`d00_mdl/<asset_name>_<variant>_mdl.py` の中の **1 関数に閉じ込める**
- サブメッシュごとにファイルを分割せず、1 関数の中で順番に作って結合 / Empty 統合まで終える
- 命名規約: `<asset_name>_<variant_id>_mdl.py` / 関数名も同名
- 参考: [Assets/mdl/SAMPLE_MODEL/d00_mdl/sukima_logo_mdl.py](Assets/mdl/SAMPLE_MODEL/d00_mdl/sukima_logo_mdl.py)

### 2. 原子的な単体アセットは 1 Mesh、複合アセンブリは部品分離を維持

- `Assets/parts` の原子的な単体アセットは、制作途中では部位別サブメッシュに分けてよいが、完成時は原則として全サブメッシュを **1 つの Mesh オブジェクト**へ結合する
- 結合後の Mesh 名は原則 `obj_name` とし、`{obj_name}_anchor` という Empty を 1 つだけ作って、その子要素にする
- マテリアルを複数使用する場合も、Material Slot と面ごとの割当を保持したまま 1 Mesh へ結合する
- join 前に各サブメッシュへ `mdl_cm_lib.initialize_transform_apply(...)` を実行し、CustomID の衝突を `mdl_cm_lib.offset_join_object_custom_ids(...)` で回避する
- join 後は `mdl_cm_lib.fix_duplicate_ids(obj_name)`、法線統一などの整合性チェックを行う
- 利用側プロジェクトでは Empty を 1 個動かすだけで全体が動くようにすること
- ただし、独立した意味や再利用単位を持つ既存アセットを組み合わせる wrap は「複合アセンブリ」として扱い、1 Mesh 化を強制しない（壁 + 窓 + 柱のように、差し替え・個別マテリアル・部品単位の表示制御が必要な場合は、別々の Mesh と Anchor のまま維持してよい）
- 複合アセンブリでは構成部品名と Anchor 名を安定させ、想定階層を追跡可能にする
- Armature、独立可動部、LOD、衝突判定など技術上の理由による複数 Mesh も許容する（分離理由はコードコメントに残す）
- 使用関数:
  - `mm_cm_lib.join_objects(obj_list, join_name)`
  - `mdl_cm_lib.offset_join_object_custom_ids(base_obj_name, join_obj_name)`
  - `mdl_cm_lib.add_object_anchor_empty(obj_name, location, suffix="_anchor")`
  - `mdl_cm_lib.add_objects_to_existing_empty(empty_name, obj_name_list)`
- シェイプキーを使う場合、原則として Mesh 結合とトポロジ確定を先に終えてから `d06_shape_key` を実行する

### 3. マテリアル設定まで wrap で完了させる（UV / Bake は省略可）

- `wrap/<asset_name>_<variant>_wrap.py` の中で **mdl + mtal を呼び出して 1 関数にまとめる**
- アセット固有のマテリアル割当・ノード構築は `d02_mtal/<asset_name>_<variant>_mtal.py` に書く
- **`Assets/parts/material/` への共通化は「他アセットでも使い回しが見込める場合のみ」**
  - 単発でしか使わないマテリアル（そのアセット固有のロゴ、特殊な質感など）は d02_mtal 内で完結させる
  - 使い回しが見込めるもの（一般的な木、金属、土、ガラス、漆喰など）のみ `Assets/parts/material/` に切り出す
  - 共通マテリアル関数の典型シグネチャ:
    ```python
    def mtal_<material_name>_00(
        mtal_name   = "MT_..."
    ,   base_color  = (R, G, B, 1.0)
    ,   shade_color = (R, G, B, 1.0)
    ,   roughness   = 0.85
        # 他のテクスチャ/Bumpパラメータ
    ):
        # 既存マテリアル前提でノード追加・設定
        # 既に同名ノードがあれば再追加せず、値だけ更新する(再実行安全)
        ...
    ```
- ノード構成は Principled BSDF + TexCoord + Mapping + Noise/Voronoi + ColorRamp + MixRGB + Bump などを組み合わせて「リアルな質感」を作る（単色 BSDF だけで済ませない）
- UV unwrap（`d01_uv_unwrap`）と Bake（`d03_bake`）は、そのアセットがどのプロジェクトでどう使われるか次第なので、必要になるまで実装しない
- 参考: [Assets/mdl/SAMPLE_MODEL/wrap/sukima_logo_wrap.py](Assets/mdl/SAMPLE_MODEL/wrap/sukima_logo_wrap.py)

#### 3-A. メッシュ作成は bmesh の編集を主体に（必須）

**プリミティブをそのまま並べて終わらせない。** 必ず以下のどれか以上を組み合わせて形を整える。

- 頂点・辺・面の **押し出し (extrude)**
- 内側に押し込む **inset / extrude（反対方向）**
- 形のメリハリのための **ループカット**、**ベベル**
- 個別頂点を選択して **微調整**（xyz オフセット、proportional editing）
- 連続体は **同一メッシュから extrude で延長** する
- 別パーツを「join」で物理的に結合してから、結合部の頂点を merge / smooth
- ハイポリ表現が必要なら Subsurf や remesh も使ってよい

形の指針:
- 球は UV 球そのままで終わらず、押し出し・頂点摂動で個性を出す
- 円柱もそのままでなく、上下端を inset / scale で形を整える
- 自然物（植物、石、土）は **不規則性が命**。ランダム摂動・複数回の編集を重ねて単調さを排除する

#### 3-B. マテリアル: パラメータ変更を確実に反映する `_ensure_material` パターン

共通マテリアル関数は内部で「既存ノードがあれば再追加せず値だけ更新する」設計になっている場合が多く、ノード構造自体を変更した場合は既存マテリアルのノードが優先されて修正が反映されないことがあります。

**対処**: mtal ファイル内で以下のヘルパーを定義して、各サブメッシュ毎に「既存マテリアル削除 → 新規作成」してから共通マテリアル関数を呼びます。

```python
# d02_mtal/<asset>_<variant>_mtal.py の冒頭に置く共通ヘルパー
#
# Input :
#   target_obj : 対象オブジェクト名 (str)
#   mtal_name  : 作成/再利用するマテリアル名 (str)
# Output:
#   target_obj に mtal_name のマテリアルが新規割当される(既存があれば一旦削除)
#   戻り値: True = 割当成功 / False = オブジェクト不在
def _ensure_material(target_obj, mtal_name):
    if not bpy.data.objects.get(target_obj):
        return False
    bpy.ops.object.mode_set(mode='OBJECT')
    mdl_cm_lib.active_object_select(object_name_list=[target_obj])
    # 既存マテリアルがあれば一旦削除(関数引数を変更したらノードも作り直すため)
    existing_mat = bpy.data.materials.get(mtal_name)
    if existing_mat is not None:
        try:
            bpy.data.materials.remove(existing_mat, do_unlink=True)
        except Exception:
            pass
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    mtal_cm_lib.add_new_material(material_name=mtal_name)
    bpy.ops.object.mode_set(mode='OBJECT')
    return True
```

### 4. 別プロジェクトから呼び出せる構造を担保

- 利用側プロジェクトから `wrap/<asset>_wrap.py` の関数を呼ぶだけで完成オブジェクトが生成されること
- wrap の引数は最低限 `obj_name` を受け取り、サイズ等の任意パラメータは `None` 既定で「未指定なら mdl 既定値」を許す形にすること
- `glb_defs.py` には「アンカー Empty 名」「サブメッシュ名」「マテリアル名」を全て登録する（別プロジェクトから参照しやすくするため）

### 5. 軽量化（WebGL / Three.js 想定）

- プリミティブの分割数は控えめに（円柱/球の vertices/segments を 16 以下推奨）
- Subdivision Surface・パーティクル・物理演算（Cloth 等）は極力避ける（結果メッシュを使う場合のみ）
- 葉や枝などの量物は **必ず join して 1 メッシュに結合** する（draw call を抑える）
- 同一カテゴリ内で繰り返し使われるマテリアルは `glb_defs.py` で名前を共有する

### 6. 既存ファイルがあれば再生成スキップ

- `mm_cm_lib.glb_exist_obj_chk(obj_list, EXIST_FLAG_DICT, gen_flag=True)` を mdl 関数の最初に置き、全サブオブジェクト名を `obj_list` に並べる
- `gen_flag=True` なら未生成のものだけ生成する（差分実行）

### 7. 部品アセット間の依存呼び出し

ある部品アセットが他の部品を内部で生成したい場合は、**wrap 関数名を文字列引数で受け取り、動的に呼び出す**パターンを使います。

```python
from Assets.parts.model.<OTHER_CATEGORY>_ASSETS import wrap as _other_wrap_pkg
wrap_module = getattr(_other_wrap_pkg, <part>_type)
wrap_func   = getattr(wrap_module, <part>_type)
wrap_func(obj_name=..., **kwargs)
```

呼ばれる側は内寸情報等を `obj["<key>"] = value` の **custom property** に格納し、呼ぶ側がそれを読み取って配置を合わせます。

---

## コーディングスタイル

- 関数呼び出しの際は **キーワード引数** を用いる
- コンマ「,」で引数を区切る場合、コンマは行末ではなく **行の先頭側で揃える**

```python
# 良い例
model = create_new_model(
    data      = raw_data
,   threshold = 15
)
```

- コメント・識別子は日本語主体で構わない（制作ログを兼ねるため）

---

## Blender バージョン互換に関する注意

- 実行環境は **Blender 5.2.0 LTS** を正式ベースラインとする
- Blender 5.x で廃止/改名された API（5.2.0 で確認済み）
  - `bpy.ops.mesh.inset_faces` → `bpy.ops.mesh.inset` に書き換える
  - `obj.data.use_auto_smooth` / `auto_smooth_angle` は try/except で囲む
  - `bpy.ops.mesh.loop_multi_select(ring=False)` → `bpy.ops.mesh.select_edge_loop_multi()` に分離・改名された（`ring=True` 相当は `select_edge_ring_multi()`）。挙動は同一
- API の存在有無は Blender バージョン間で変わりうるため、`hasattr()` によるフィーチャー検出や try/except で吸収すること
- 実機での API 存在確認が必要な場合は、Blender を `--background --factory-startup --python <script>` で直接起動し、`dir(bpy.ops.mesh)` 等でオペレーター一覧を調べると確実（推測で API 名を書き換えない）

---

## 主要ライブラリリファレンス（抜粋）

| 関数 | 用途 |
|---|---|
| `cm_lib.import_submodules(package_name)` | パッケージ配下のサブモジュールを一括import（"main" は除外） |
| `cm_lib._auto_reload_modules(module_list)` | 更新されたモジュールを自動 reload |
| `mm_cm_lib.bpy_modeling_initialize_common(...)` | シーン/表示設定などの共通初期化 |
| `mm_cm_lib.glb_exist_obj_chk(obj_list, EXIST_FLAG_DICT, gen_flag)` | 既存オブジェクトの有無をチェックし差分生成を制御 |
| `mm_cm_lib.join_objects(obj_list, join_name)` | 複数オブジェクトの結合 |
| `mm_cm_lib.collection_create_or_move(...)` | コレクション作成/移動 |
| `mdl_cm_lib.active_object_select(object_name_list)` | オブジェクト選択・アクティブ化 |
| `mdl_cm_lib.add_object_anchor_empty(obj_name, location, suffix)` | アンカー Empty の作成 |
| `mdl_cm_lib.change_preview(key)` | ビュー切替（MATERIAL/SOLID 等） |
| `mtal_cm_lib.add_new_material(material_name)` | 新規マテリアル + 割当 |
| `mtal_cm_lib.allocate_material(material_name)` | 既存マテリアル割当 |
| `mtal_cm_lib.add_new_texture(material_name, texture_name, ...)` | ノード追加 |
| `mtal_cm_lib.node_link_func(...)` | ノード間リンク |
| `mtal_cm_lib.node_value_change(...)` | ノードプロパティ変更 |
