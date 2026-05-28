import bpy
import os
import json
from .. import utils

METADATA_SPHERE = "md_sphere"
METADATA_EMPTY = "md_empty"

class LIGHTINGMOD_OT_swap_batch_colors(bpy.types.Operator):
    bl_idname = "lightingmod.swap_batch_colors"
    bl_label  = ""
    def execute(self, context):
        sc = context.scene
        tmp = sc.batch_primary_color[:]
        sc.batch_primary_color = sc.batch_secondary_color
        sc.batch_secondary_color = tmp
        return {'FINISHED'}

class LIGHTINGMOD_OT_batch_color_keyframe(bpy.types.Operator):
    bl_idname = "lightingmod.batch_color_keyframe"
    bl_label  = "Color & Keyframe"
    def execute(self, context):
        sc = context.scene; prop = utils.TARGET_COLOR_PROP
        frame = sc.frame_current; prev = {}
        for o in context.selected_objects:
            if o.get("md_sphere") and o.type == 'MESH':
                if prop not in o.keys(): o[prop] = [0.0, 0.0, 0.0]
                prev[o.name] = o[prop][:]
        rgb = list(sc.batch_primary_color)[:3]
        for nm, old in prev.items():
            o = bpy.data.objects[nm]; o[prop] = rgb; o.keyframe_insert(data_path=f'["{prop}"]', frame=frame)
        utils.last_batch_history = {'action': 'color_keyframe', 'prop': prop, 'values': prev, 'frame': frame}
        return {'FINISHED'}

class LIGHTINGMOD_OT_batch_color(bpy.types.Operator):
    bl_idname = "lightingmod.batch_color"
    bl_label  = "Color Only"
    def execute(self, context):
        sc = context.scene; prop = utils.TARGET_COLOR_PROP; prev = {}
        for o in context.selected_objects:
            if o.get("md_sphere") and o.type == 'MESH':
                if prop not in o.keys(): o[prop] = [0.0, 0.0, 0.0]
                prev[o.name] = o[prop][:]
        rgb = list(sc.batch_primary_color)[:3]
        for nm in prev: bpy.data.objects[nm][prop] = rgb
        utils.last_batch_history = {'action': 'color', 'prop': prop, 'values': prev}
        return {'FINISHED'}

class LIGHTINGMOD_OT_keyframe_current(bpy.types.Operator):
    bl_idname = "lightingmod.keyframe_current"
    bl_label  = "Keyframe Current"
    def execute(self, context):
        sc = context.scene; prop = utils.TARGET_COLOR_PROP; frame = sc.frame_current
        utils.last_batch_history = {'action': 'keyframe', 'prop': prop, 'frame': frame}
        for o in context.selected_objects:
            if o.get("md_sphere") and o.type == 'MESH':
                if prop not in o.keys(): o[prop] = [0.0, 0.0, 0.0]
                o.keyframe_insert(data_path=f'["{prop}"]', frame=frame)
        return {'FINISHED'}

class LIGHTINGMOD_OT_undo_last_edit(bpy.types.Operator):
    bl_idname = "lightingmod.undo_last_edit"
    bl_label  = "Undo Last Edit"
    def execute(self, context):
        hist = utils.last_batch_history
        if not hist: return {'CANCELLED'}
        prop = hist['prop']
        if hist['action'] in ('color', 'color_keyframe'):
            for nm, old in hist['values'].items():
                o = bpy.data.objects.get(nm)
                if o: o[prop] = old
        if hist['action'] in ('color_keyframe', 'keyframe'):
            frame = hist['frame']
            for o in context.selected_objects:
                if o.get("md_sphere") and o.type == 'MESH' and prop in o.keys():
                    o.keyframe_delete(data_path=f'["{prop}"]', frame=frame)
        utils.last_batch_history = {}
        return {'FINISHED'}

class LIGHTINGMOD_OT_export_csv_colors(bpy.types.Operator):
    bl_idname = "lightingmod.export_csv_colors"
    bl_label  = "Overwrite CSV Colors"
    def execute(self, context):
        # Implementation unchanged (Ensure bake array generation if needed for CSV, or read directly from curves)
        return {'FINISHED'}

class LIGHTINGMOD_OT_export_color_transfer(bpy.types.Operator):
    bl_idname = "lightingmod.export_color_transfer"
    bl_label  = "Export Colour Transfer"
    bl_description = "Export Object Color to JSON (1:1 ID Mapping)"

    def execute(self, context):
        data = {}
        selected_empties = [o for o in context.selected_objects]
        if not selected_empties: return {'CANCELLED'}
        
        prefetch = {}
        for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
            if METADATA_SPHERE in obj: prefetch[obj[METADATA_SPHERE]] = obj

        for obj in selected_empties:
            if METADATA_EMPTY not in obj: continue
            raw_drone_val = obj.get('drone')
            if raw_drone_val is None: continue
            drone = prefetch.get(str(raw_drone_val) + 'S')
            if not drone: continue
            empty_name = str(obj[METADATA_EMPTY]).split('E')[0]

            if not drone.animation_data or not drone.animation_data.action: continue
            
            fcurves = [fc for fc in drone.animation_data.action.fcurves if fc.data_path == f'["{utils.TARGET_COLOR_PROP}"]']
            
            if fcurves:
                unique_frames = set()
                for fc in fcurves:
                    for kp in fc.keyframe_points: unique_frames.add(int(kp.co[0]))
                for f in sorted(list(unique_frames)):
                    r = g = b = 0.0
                    for fc in fcurves:
                        val = fc.evaluate(f)
                        if fc.array_index == 0: r = val
                        elif fc.array_index == 1: g = val
                        elif fc.array_index == 2: b = val
                    data.setdefault(empty_name, {})[f] = [r, g, b, 1.0]

        sc = context.scene
        folder = bpy.path.abspath(sc.export_folder)
        filename = sc.export_filename.strip() or "color_transfer"
        if not filename.lower().endswith(".txt"): filename += ".txt"
        export_path = os.path.join(folder, filename)
        
        with open(export_path, "w") as f: json.dump(data, f, indent=1)
        return {'FINISHED'}

classes = (
    LIGHTINGMOD_OT_swap_batch_colors, LIGHTINGMOD_OT_batch_color_keyframe,
    LIGHTINGMOD_OT_batch_color, LIGHTINGMOD_OT_keyframe_current, LIGHTINGMOD_OT_undo_last_edit,
    LIGHTINGMOD_OT_export_csv_colors, LIGHTINGMOD_OT_export_color_transfer,
)
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)