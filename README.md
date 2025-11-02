# 🧱 bpy_text_lab : BPY Text-Based 3D Modeling

**Blender Python API（BPY）を用いた、フルテキストベースの 3D CG デザイン環境**

Blender上でのすべての操作を Python スクリプトで制御することで、  
- **再現性の高い 3D 制作フロー**
- **Gitなどのバージョン管理システム(VCS)で行程/成果物を管理**
- **複数人での共同作業**
- **コピペで他プロジェクトへ流用**
- **Blender特有の操作感に慣れる手間の削減**
- **作成途中段階への変更作業容易化**
- **3D制作ノウハウの共有・再現基盤**

の実現を目指します。

---

## 📦 Project Structure
```
Git Root
.
├── Assets
│   ├── mdl
│   │   ├── 00_gen_project_dir.sh       // プロジェクトを生成するためのスクリプト
│   │   └── SAMPLE_MODEL                // サンプルプロジェクトディレクトリ
│   │       ├── bake_texture                // ベイクした画像格納ディレクトリ
│   │       ├── d00_mdl                     // モデリング作業ディレクトリ
│   │       ├── d01_uv_unwrap               // UV展開作業ディレクトリ
│   │       ├── d02_mtal                    // マテリアル作業ディレクトリ
│   │       ├── d03_bake                    // ベイク作業ディレクトリ
│   │       ├── d04_bone                    // アーマチュア(ボーン)作業ディレクトリ
│   │       ├── d05_animation               // アニメーション作業ディレクトリ
│   │       ├── d06_shape_key               // シェイプキー作業ディレクトリ
│   │       ├── glb                         // グローバルファイル格納ディレクトリ
│   │       ├── __init__.py                 // プロジェクト外流用用
│   │       ├── main.py                     // Mainファイル (★これをBlenderで実行)
│   │       ├── README.md                   // README
│   │       └── wrap                        // 上記作業整理用ファイル格納ディレクトリ
│   └── parts
│       ├── material                    // 汎用マテリアル/テクスチャノード格納用ディレクトリ
│       └── model                       // 汎用モデル格納用ディレクトリ(00_gen_project_dir.shで生成できるプロジェクト単位で格納)
├── Common                              // 共通設定等
│   ├── common_glb_template.py              // 00_gen_project_dir.sh で用いるファイル
│   ├── common_sub_template.py              // 00_gen_project_dir.sh で用いるファイル
│   ├── common_top_main_template.py         // 00_gen_project_dir.sh で用いるファイル
│   ├── common_top.py                       // 共通ファイルトップ(ライブラリのインポート等)
│   ├── common_top_sub_template.py          // 00_gen_project_dir.sh で用いるファイル
│   └── common_wrap_template.py             // 00_gen_project_dir.sh で用いるファイル
├── Mylib                               // 自作共通関数とりまとめ
│   ├── ani_cm_lib.py                       // アニメーション用共通関数とりまとめ用
│   ├── mdl_cm_lib.py                       // モデリング用共通関数とりまとめ用
│   ├── mm_cm_lib.py                        // その他共通関数とりまとめ用
│   └── mtal_cm_lib.py                      // マテリアル/テクスチャ用共通関数とりまとめ用
├── Output                              // モデルの出力用
│   └── exports
├── README.md                           // このREADMEファイル
├── requirements.txt
├── Setting                             // Blenderの設定ファイルなど保存用 (任意)
└── Tools                               // あると便利な自作ツール格納場所
    ├── Export
    │   └── export_glb_gltf.py              // モデルのExport用
    ├── get_index_list.py                   // モデルの面/辺/点インデックスリストの出力
    └── move_vert
        ├── 00_save_vert_point.py           // 全ての頂点座標保存 -> point.json
        ├── 01_diff_vert_point.py           // マウスで移動後、保存した座標との差分出力 -> move.py
        ├── move.py
        └── point.json
```

---

## 🎁 Sample Model

このリポジトリに含まれる **「SAMPLE_MODEL」** から生成できるサンプルモデルを以下で確認できます。

👉 [サンプルモデルを表示する](https://sukima-log.github.io/Pages_bpy-text-lab_sample/)
（作成できる3Dモデルの例を確認できます）


## 🧩 Supported Versions

- **Blender 4.2** : 動作確認

---

## ⚙️ Setup

1. **Blender** をインストール  

2. **Git** をインストール  
   → インストール後、システム環境変数にパスを設定。  
   例: 「Windows Git path 設定方法」で検索。

---

## 🚀 Create New Project

1. 以下を実行してプロジェクトを生成します。

   ```bash
   ./Assets/mdl/00_gen_project_dir.sh プロジェクト名
   ```
例: `./Assets/mdl/00_gen_project_dir.sh SAMPLE_PROJECT`
Assets/mdl/ 以下に、空のプロジェクト構成が生成されます。

## 🖥️ Blender Workspaces
主に以下のワークスペースを使用します：

- 🟣 UV Editing
- 🟢 Shading
- 🔵 Animation

## 🧭 Blender Workflow

```

モデリング
    ↓
モディファイア設定（Mirror / Subdivision / Array など）
    ↓
モディファイア適用（形状確定系：Mirror / Subdivision など）
    ↓
モデル結合・最適化（前処理）
    ↓
UV展開
    ↓
マテリアル設定
    ↓
テクスチャ作成・ベイク
    ↓
アーマチュア設定（ボーン／リギング）
    ↓
アニメーション設定（ボーン／シェイプキー／トランスフォーム）
    ↓
glTF / glb エクスポート
```


## 🎨 Texture Types

| 名称                   | 別名         | 説明            | 注意点            |
| -------------------- | ---------- | ------------- | -------------- |
| ディフューズマップ (DIFFUSE)  | アルベド／Color | モデルの色や模様を表現   | 通常カラー空間        |
| ラフネスマップ (ROUGHNESS)  | -          | 表面の粗さ・反射特性を制御 | 色空間を「非カラー」に設定  |
| ノーマルマップ (NORMAL)     | 法線マップ      | 疑似的な凹凸感を付与    | 色空間を「非カラー」に設定  |
| ディスプレイスメントマップ (DISP) | -          | メッシュ形状を実際に変形  | Eevee対応済・処理負荷大 |

## 🎞️ Animation Overview
| 機能名	| 対象	| 仕組み	| 主な用途	| glTF上での名前 |
|----------|----------|----------|----------|----------|
| シェイプキー (Shape Key)	| 頂点（Vertex）	| 頂点位置を直接補間	| 表情・細かい変形	| Morph | Target |
| アーマチュア (Armature)	| ボーン＋メッシュ	| 骨（Bone）で頂点をスキニング	| 全身の動き・ポーズ	| Skin / Skeleton |
| アニメーション (Animation)	| シェイプキー・ボーン・トランスフォームなど	| 時間経過で値を変化させる	| 動作全般（走る、しゃべる、瞬きなど）| 	Animation |

### 構造イメージ:

```
[ メッシュ ]
   ├─ シェイプキー ... 頂点を直接動かす（例：表情）
   ├─ アーマチュア ... ボーンで動かす（例：体の動き）
   └─ アニメーション ... 時間軸で制御（例：歩行・瞬き）
```

- 💡 リグ (Rig): ボーンを効率的に制御する仕組み。複数ボーンを一括制御可能。
- ▶️ 再生: [Space] キーでアニメーションを再生。

## 📤 Model Export
モデル出力スクリプト:

```
Tools/Export/export_glb_gltf.py
```

## ⚠️ Disclaimer
- 本リポジトリを利用したことによる損害・不利益について、作者は一切の責任を負いません。すべて自己責任でご利用ください。
- 改良提案・フィードバックを歓迎します。

## 📜 利用規約 / License

- **Blender**
    - 本プロジェクトは **Blender**（[https://www.blender.org/](https://www.blender.org/)）を利用して制作されています。  
      Blenderおよびその機能を使用する際は、**Blender Foundation** の [ライセンスおよび利用規約（GPL v3）](https://www.blender.org/about/license/) に従ってください。

- **Model**
    - 本リポジトリ内の3Dモデルおよびテクスチャは **CC0 1.0 Universal (Public Domain)** ライセンスのもとで公開します。  
    - 個人・商用問わずご利用いただけます。
    - クレジット表記は任意です。
    - 再配布・改変も自由ですが、可能であれば出典として本リポジトリへのリンクを記載してください。
    - ※ 他のライブラリや外部アセットを含む場合は、それぞれのライセンスに従ってください。

- **Repository**
    - This project is licensed under the **MIT License** — see the [LICENSE](./LICENSE) file for details.

## 📚 References
（今後追記予定）


| Version | Date       | Type    | Description                          | Author |
|---------|------------|---------|--------------------------------------|-----------|
| 0.1   | 2025-11-01 | Added   | 初回リリース <br/> テンプレート追加 | sukimalog.com |
| 0.11   | 2025-11-02 | Added | 参考画像読み込み関数追加 <br /> image_reference_import | sukimalog.com |
| 0.12   | 2025-11-02 | Modify   | サンプル動作確認ミス <br /> 修正済 | sukimalog.com |
| x.x.x   | xxxx-xx-xx | xxxxx   | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | |
| x.x.x   | xxxx-xx-xx | xxxxx   | xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx | |


