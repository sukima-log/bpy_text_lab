import bpy

#-----------------------------------------------------
# 選択された頂点、エッジ、面の【カスタムID】を取得して表示
#-----------------------------------------------------
def get_selected_elements_by_custom_id(
    vid_name="vid",
    eid_name="eid",
    fid_name="fid",
):
    # アクティブオブジェクト取得
    obj = bpy.context.object

    if obj and obj.type == 'MESH':
        me = obj.data

        # 一旦 EDIT → OBJECT に切り替えて選択を確定
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.object.mode_set(mode='OBJECT')

        # -------------------------------------------------
        # カスタム属性の存在チェック
        # -------------------------------------------------
        vid_attr = me.attributes.get(vid_name)
        eid_attr = me.attributes.get(eid_name)
        fid_attr = me.attributes.get(fid_name)

        # -------------------------------------------------
        # 頂点の選択された「カスタムID」を取得
        # -------------------------------------------------
        selected_vertex_ids = []
        if vid_attr:
            data = vid_attr.data
            for v in me.vertices:
                if v.select:
                    selected_vertex_ids.append(data[v.index].value)
        else:
            print(f"[警告] 頂点属性 '{vid_name}' が存在しません")
            selected_vertex_ids = ["<未設定>"]

        # -------------------------------------------------
        # エッジの選択された「カスタムID」を取得
        # -------------------------------------------------
        selected_edge_ids = []
        if eid_attr:
            data = eid_attr.data
            for e in me.edges:
                if e.select:
                    selected_edge_ids.append(data[e.index].value)
        else:
            print(f"[警告] エッジ属性 '{eid_name}' が存在しません")
            selected_edge_ids = ["<未設定>"]

        # -------------------------------------------------
        # 面の選択された「カスタムID」を取得
        # -------------------------------------------------
        selected_face_ids = []
        if fid_attr:
            data = fid_attr.data
            for f in me.polygons:
                if f.select:
                    selected_face_ids.append(data[f.index].value)
        else:
            print(f"[警告] 面属性 '{fid_name}' が存在しません")
            selected_face_ids = ["<未設定>"]

        # -------------------------------------------------
        # 結果表示
        # -------------------------------------------------
        print("--------------------------------------------------------------")
        print("Selected Vertex IDs:", selected_vertex_ids)
        print("--------------------------------------------------------------")
        print("Selected Edge IDs  :", selected_edge_ids)
        print("--------------------------------------------------------------")
        print("Selected Face IDs  :", selected_face_ids)

        if selected_vertex_ids == [] and selected_edge_ids == [] and selected_face_ids == []:
            print("No vertices, edges, or faces selected.")

    else:
        print("No mesh object selected.")


# 実行
get_selected_elements_by_custom_id()
