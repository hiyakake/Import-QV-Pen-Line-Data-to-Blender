bl_info = {
    "name": "Import QV-Pen Line Data to Blender",
    "author": "ひやかけ/Hiyakake",
    "website": "https://github.com/hiyakake/Import-QV-Pen-Line-Data-to-Blender",
    "version": (0, 3),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > QV Pen Importer",
    "description": "This plugin imports QV-Pen line data to Blender. Export QV-Pen data from the world where Dolphiiiin's \"QvPen Exporter / Importer\" (https://booth.pm/ja/items/6499949) is installed, and use \"QvPen Export Formatter\" (https://dolphiiiin.github.io/qvpen-export-formatter/) to convert it into a JSON file. This tool can import the converted JSON file as a mesh path. The color and thickness are inherited. The coordinates correspond to the location where the line is drawn on the VRC world.",
    "category": "Import-Export",
}

import bpy
import json
import os

# シーンに各種プロパティを追加
bpy.types.Scene.json_filepath = bpy.props.StringProperty(
    name="JSON File Path",
    description="Path to the JSON file containing stroke data",
    subtype='FILE_PATH',
    default=""
)

# JSON に width がない場合のデフォルト値（カーブの extrude と bevel 用）
bpy.types.Scene.json_extrude = bpy.props.FloatProperty(
    name="Default Extrude",
    description="Default extrude amount if JSON stroke does not include width (in meters)",
    default=0.005,
    unit='LENGTH'
)

# ソリッド化モディファイアの厚み用のパネルプロパティ（JSON に width がない場合）
bpy.types.Scene.json_solidify_thickness = bpy.props.FloatProperty(
    name="Default Solidify Thickness",
    description="Default solidify thickness if JSON stroke does not include width (in meters)",
    default=0.005,
    unit='LENGTH'
)

bpy.types.Scene.json_add_solidify = bpy.props.BoolProperty(
    name="Add Solidify Modifier",
    description="Apply a Solidify modifier to the generated curves",
    default=False
)

# シェーダータイプの選択（EnumProperty）
bpy.types.Scene.json_shader_type = bpy.props.EnumProperty(
    name="シェーダータイプ",
    description="使用するシェーダーのタイプを選択",
    items=[
        ('PRINCIPLED', 'Principled BSDF', 'メッシュの形が目立ち陰影がはっきり出やすいシェーダーです。リアルな質感を表現します。'),
        ('EMISSION', '放射シェーダー', 'どの角度からも均一に見えるシェーダーです。QVPenとの見え方に近いですが、発光するため色が異なります。')
    ],
    default='PRINCIPLED'
)

# 放射シェーダーの強度
bpy.types.Scene.json_emission_strength = bpy.props.FloatProperty(
    name="放射強度",
    description="放射シェーダーの強度",
    default=1.0,
    min=0.0,
    soft_max=10.0
)

# データ準備説明の表示/非表示を切り替えるプロパティ
bpy.types.Scene.show_data_preparation = bpy.props.BoolProperty(
    name="データの準備についての説明を表示",
    description="QVペンデータの準備方法に関する説明を表示/非表示",
    default=False
)

# JSON ファイルを選択するオペレーター
class IMPORT_OT_JSONFile(bpy.types.Operator):
    bl_idname = "import.json_file"
    bl_label = "Select JSON File"
    
    filepath: bpy.props.StringProperty(subtype="FILE_PATH")
    
    def execute(self, context):
        context.scene.json_filepath = self.filepath
        self.report({'INFO'}, f"Selected file: {self.filepath}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# JSON からパス（カーブ）を生成するオペレーター
class OBJECT_OT_GeneratePaths(bpy.types.Operator):
    bl_idname = "object.generate_json_paths"
    bl_label = "Generate Paths from JSON"
    
    def execute(self, context):
        filepath = context.scene.json_filepath
        if not os.path.exists(filepath):
            self.report({'ERROR'}, "JSON file not found or invalid path")
            return {'CANCELLED'}
        
        # JSONファイル読み込み
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            self.report({'ERROR'}, f"Failed to load JSON: {e}")
            return {'CANCELLED'}
        
        exported_data = data.get("exportedData", [])
        collection = context.collection
        
        # 親オブジェクトを作成（すべてのパスの親となる）
        parent_obj = bpy.data.objects.new("QVPen_Paths_Parent", None)  # Noneはオブジェクトデータなし（Empty）を意味する
        parent_obj.location = (0, 0, 0)  # 原点に配置
        collection.objects.link(parent_obj)
        
        # 16進数カラーを RGBA タプル (0～1) に変換する関数
        def hex_to_rgba(hex_str):
            r = int(hex_str[0:2], 16) / 255.0
            g = int(hex_str[2:4], 16) / 255.0
            b = int(hex_str[4:6], 16) / 255.0
            return (r, g, b, 1.0)
        
        # マテリアルキャッシュ（キー：カラーの16進文字列）
        material_cache = {}
        
        for i, stroke in enumerate(exported_data):
            positions = stroke.get("positions", [])
            if len(positions) < 6:  # 点が2点未満の場合はスキップ
                continue
            
            color_info = stroke.get("color", {})
            color_values = color_info.get("value", [])
            color_hex = color_values[0] if color_values else "FFFFFF"
            rgba = hex_to_rgba(color_hex)
            
            num_points = len(positions) // 3
            
            # JSON に含まれる width があればその値を使用し、なければパネルの値を使用
            stroke_width_for_curve = stroke.get("width", context.scene.json_extrude)
            
            # 新しいカーブデータの作成
            curve_data = bpy.data.curves.new(name=f"StrokeCurve_{i}", type="CURVE")
            curve_data.dimensions = '3D'
            # JSON の width を extrude と bevel_depth に反映
            curve_data.extrude = stroke_width_for_curve
            curve_data.bevel_depth = stroke_width_for_curve
            
            # POLY スプラインを追加（必要に応じて BEZIER などに変更可能）
            spline = curve_data.splines.new(type="POLY")
            spline.points.add(num_points - 1)
            
            for j in range(num_points):
                x = positions[j*3]
                y = positions[j*3 + 1]
                z = positions[j*3 + 2]
                spline.points[j].co = (x, y, z, 1)
            
            # カーブオブジェクトの作成およびシーンへのリンク
            curve_obj = bpy.data.objects.new(name=f"Stroke_{i}", object_data=curve_data)
            collection.objects.link(curve_obj)
            
            # 親オブジェクトの子として設定
            curve_obj.parent = parent_obj
            
            # ソリッド化モディファイアの追加
            if context.scene.json_add_solidify:
                mod = curve_obj.modifiers.new(name="Solidify", type='SOLIDIFY')
                # JSON に width があればその値を、なければパネルの値を使用
                mod.thickness = stroke.get("width", context.scene.json_solidify_thickness)
            
            # 同じ色のマテリアルがあれば再利用、なければ新規作成
            if color_hex in material_cache:
                mat = material_cache[color_hex]
            else:
                mat = bpy.data.materials.new(name=f"StrokeMaterial_{color_hex}")
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                links = mat.node_tree.links
                
                # デフォルトのノードを削除
                for node in nodes:
                    nodes.remove(node)
                
                # マテリアル出力ノードを追加
                output_node = nodes.new(type='ShaderNodeOutputMaterial')
                output_node.location = (300, 0)
                
                if context.scene.json_shader_type == 'EMISSION':
                    # 放射シェーダーを使用する場合
                    emission_node = nodes.new(type='ShaderNodeEmission')
                    emission_node.location = (0, 0)
                    emission_node.inputs["Color"].default_value = rgba
                    emission_node.inputs["Strength"].default_value = context.scene.json_emission_strength
                    
                    # ノードを接続
                    links.new(emission_node.outputs["Emission"], output_node.inputs["Surface"])
                else:
                    # Principled BSDFを使用する場合
                    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
                    bsdf.location = (0, 0)
                    bsdf.inputs["Base Color"].default_value = rgba
                    bsdf.inputs["Metallic"].default_value = 0.0
                    bsdf.inputs["Roughness"].default_value = 1.0
                    bsdf.inputs["IOR"].default_value = 0.5
                    if "Alpha" in bsdf.inputs:
                        bsdf.inputs["Alpha"].default_value = 1.0
                    
                    # ノードを接続
                    links.new(bsdf.outputs["BSDF"], output_node.inputs["Surface"])
                
                material_cache[color_hex] = mat
            
            # オブジェクトにマテリアルを割り当て
            if curve_obj.data.materials:
                curve_obj.data.materials[0] = mat
            else:
                curve_obj.data.materials.append(mat)
        
        self.report({'INFO'}, "Paths generated successfully")
        return {'FINISHED'}

# Nパネルに表示するパネルクラス
class VIEW3D_PT_QVPenPanel(bpy.types.Panel):
    bl_label = "QV Pen Importer"
    bl_idname = "VIEW3D_PT_qv_pen_importer"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "QV Pen"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene, "json_filepath")
        layout.operator("import.json_file", text="Select JSON File")
        
        # データの準備について（折りたたみ可能なボックス）
        box = layout.box()
        row = box.row()
        row.prop(scene, "show_data_preparation", icon="DISCLOSURE_TRI_DOWN" if scene.show_data_preparation else "DISCLOSURE_TRI_RIGHT", 
                 icon_only=True, emboss=False)
        row.label(text="データの準備について")
        
        if scene.show_data_preparation:
            column = box.column()
            column.scale_y = 0.7
            column.label(text="QV ペンのデータを Dolphiiiin 様作成の「QvPen Exporter / Importer」")
            column.label(text="（https://booth.pm/ja/items/6499949）が設置された")
            column.label(text="ワールドでエクスポートし、「QvPen Export Formatter」")
            column.label(text="（https://dolphiiiin.github.io/qvpen-export-formatter/）を")
            column.label(text="使ってJSONファイルに変換したものを本ツールに読み込ませると")
            column.label(text="メッシュ化したパスとしてインポートできます。")
            
            # URLをクリック可能なオペレーターとして追加
            box.operator("wm.url_open", text="QvPen Exporter / Importer（Booth）").url = "https://booth.pm/ja/items/6499949"
            box.operator("wm.url_open", text="QvPen Export Formatter（Web）").url = "https://dolphiiiin.github.io/qvpen-export-formatter/"
            
        layout.separator()
        
        # 曲線設定
        box = layout.box()
        box.label(text="曲線設定")
        box.prop(scene, "json_extrude")
        box.prop(scene, "json_add_solidify")
        if scene.json_add_solidify:
            box.prop(scene, "json_solidify_thickness")
        
        # マテリアル設定
        box = layout.box()
        box.label(text="マテリアル設定")
        
        # シェーダータイプ選択（トグルボタンとして表示）
        box.prop(scene, "json_shader_type", expand=True)
        
        # シェーダータイプに応じた説明文を追加
        if scene.json_shader_type == 'PRINCIPLED':
            box.label(text="※ メッシュの形が目立ち、陰影がはっきり出ます")
        else:  # EMISSION
            box.label(text="※ どの角度からも均一に見えます（QVPenに近い）")
            box.label(text="※ 発光するため色合いが原画と異なります")
            box.prop(scene, "json_emission_strength")
            
        layout.separator()
        layout.operator("object.generate_json_paths", text="Generate Paths")

# 登録するクラスのリスト
classes = (
    IMPORT_OT_JSONFile,
    OBJECT_OT_GeneratePaths,
    VIEW3D_PT_QVPenPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.json_filepath
    del bpy.types.Scene.json_extrude
    del bpy.types.Scene.json_add_solidify
    del bpy.types.Scene.json_solidify_thickness
    del bpy.types.Scene.json_emission_strength
    del bpy.types.Scene.json_shader_type
    del bpy.types.Scene.show_data_preparation

if __name__ == "__main__":
    register()
