bl_info = {
    "name": "Import QV-Pen Line Data to Blender",
    "author": "Hiyakake/ひやかけ",
    "version": (0, 1),
    "blender": (2, 80, 0),
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
                bsdf = nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = rgba
                    bsdf.inputs["Metallic"].default_value = 0.0
                    bsdf.inputs["Roughness"].default_value = 1.0
                    bsdf.inputs["IOR"].default_value = 0.5
                    if "Alpha" in bsdf.inputs:
                        bsdf.inputs["Alpha"].default_value = 1.0
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
        layout.separator()
        layout.prop(scene, "json_extrude")
        layout.prop(scene, "json_add_solidify")
        if scene.json_add_solidify:
            layout.prop(scene, "json_solidify_thickness")
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

if __name__ == "__main__":
    register()
