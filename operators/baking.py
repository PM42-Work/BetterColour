import bpy
import numpy as np
from .. import utils

class LIGHTINGMOD_OT_bake_positions(bpy.types.Operator):
    bl_idname = "lightingmod.bake_positions"
    bl_label  = "Bake Positions"
    bl_description = "Calculates and bakes absolute flight paths into the 'Absolute_Position' property"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        sc = context.scene
        drones = [o for o in bpy.data.objects if o.get("md_sphere") and o.type=='MESH']
        if not drones: return {'CANCELLED'}

        prop_name = "Absolute_Position" 
        data_path = f'["{prop_name}"]'

        for d in drones:
            d[prop_name] = [0.0, 0.0, 0.0]
            ui = d.id_properties_ui(prop_name)
            ui.update(subtype='TRANSLATION')

        wm = context.window_manager
        wm.progress_begin(sc.frame_start, sc.frame_end)
        sampled_data = {d.name: [] for d in drones}

        def get_influences(drone):
            return sorted([c for c in drone.constraints if c.type == 'COPY_LOCATION' and c.name.lower().startswith('copy done')], key=lambda c: c.name)

        for f in range(sc.frame_start, sc.frame_end + 1):
            sc.frame_set(f)
            for d in drones:
                cons = get_influences(d)
                active_idxs = [i for i, c in enumerate(cons) if getattr(c, "influence", 0.0) > 1e-6]

                if not active_idxs:
                    p = d.matrix_world.translation
                    sampled_data[d.name].append((f, p.x, p.y, p.z))
                    continue

                curr_idx = max(active_idxs)
                c_curr = cons[curr_idx]
                inf_curr = getattr(c_curr, "influence", 0.0)
                tgt_curr = getattr(c_curr, "target", None)
                empty_curr = tgt_curr if tgt_curr and getattr(tgt_curr, "type", "") == 'EMPTY' else None

                if inf_curr >= 1.0 - 1e-6 and empty_curr is not None:
                    p = empty_curr.matrix_world.translation
                    sampled_data[d.name].append((f, p.x, p.y, p.z))
                else:
                    if curr_idx > 0:
                        prev_tgt = getattr(cons[curr_idx-1], "target", None)
                        prev_empty = prev_tgt if prev_tgt and getattr(prev_tgt, "type", "") == 'EMPTY' else None
                        p0 = prev_empty.matrix_world.translation if prev_empty else d.matrix_world.translation
                    else:
                        p0 = d.matrix_world.translation
                        
                    p1 = empty_curr.matrix_world.translation if empty_curr else d.matrix_world.translation
                    a = max(0.0, min(1.0, inf_curr))
                    x = (1.0 - a) * p0.x + a * p1.x
                    y = (1.0 - a) * p0.y + a * p1.y
                    z = (1.0 - a) * p0.z + a * p1.z
                    sampled_data[d.name].append((f, x, y, z))
            if f % 10 == 0: wm.progress_update(f)

        for d_name, data in sampled_data.items():
            d = bpy.data.objects.get(d_name)
            if not d.animation_data: d.animation_data_create()
            if not d.animation_data.action: d.animation_data.action = bpy.data.actions.new(name=f"{d.name}Action")
            act = d.animation_data.action
            data_np = np.array(data, dtype=np.float32)
            frames_arr = data_np[:, 0]
            for i in range(3):
                fc = act.fcurves.find(data_path=data_path, index=i)
                if not fc: fc = act.fcurves.new(data_path=data_path, index=i)
                fc.keyframe_points.clear()
                pts = np.column_stack((frames_arr, data_np[:, i+1]))
                fc.keyframe_points.add(len(pts))
                fc.keyframe_points.foreach_set('co', pts.flatten())
                fc.update()

        wm.progress_end()
        return {'FINISHED'}

classes = (LIGHTINGMOD_OT_bake_positions,)
def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)