import bpy
import numpy as np
import os
import mathutils

from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty
from ... import utils

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

class LIGHTINGMOD_OT_movie_sampler(bpy.types.Operator, ImportHelper):
    """Project video through the viewport onto dynamic drone positions"""
    bl_idname = "lightingmod.movie_sampler"
    bl_label  = "Project Video"
    bl_options = {'REGISTER', 'UNDO'}
    
    filter_glob: StringProperty(default="*.mp4;*.mov;*.avi;*.mkv;*.webm", options={'HIDDEN'}, maxlen=255)

    @classmethod
    def poll(cls, context):
        # We must be in the 3D viewport to grab the projection matrix
        return context.area and context.area.type == 'VIEW_3D'

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        if not HAS_OPENCV:
            self.report({'ERROR'}, "OpenCV not found. Please check addon dependencies.")
            return {'CANCELLED'}

        if not os.path.exists(self.filepath): return {'CANCELLED'}

        sc = context.scene
        start, end, step = sc.effector_start, sc.effector_end, sc.movie_step
        frames = list(range(start, end + 1, max(1, step)))

        # 1. IDENTIFY DRONES
        objs = []
        if sc.effector_selection_mode == 'GROUP' and sc.drone_formations:
             if sc.drone_formations[sc.drone_formations_index].groups:
                 g = sc.drone_formations[sc.drone_formations_index].groups[sc.drone_formations[sc.drone_formations_index].groups_index]
                 objs = [bpy.data.objects.get(d.object_name) for d in g.drones if bpy.data.objects.get(d.object_name)]
        else:
             objs = context.selected_objects

        drones = [o for o in objs if o.get("md_sphere") and o.type=='MESH' and "Absolute_Position" in o.keys()]
        if not drones:
            self.report({'ERROR'}, "No valid drones found. (Did you Bake Positions first?)")
            return {'CANCELLED'}

        # 2. LOAD VIDEO & GET ASPECT RATIOS
        cap = cv2.VideoCapture(self.filepath)
        if not cap.isOpened(): return {'CANCELLED'}
        
        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        vid_aspect = vid_w / max(1, vid_h)

        # 3. CACHE FLIGHT PATHS & FIND 2D BOUNDING BOX
        # We use the region's perspective matrix to flatten 3D points to the user's screen
        proj_matrix = context.region_data.perspective_matrix
        
        drone_paths = {} # { drone_name: { frame: (x_ndc, y_ndc) } }
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        self.report({'INFO'}, "Calculating Projection Bounds...")
        
        for d in drones:
            drone_paths[d.name] = {}
            anim = getattr(d, "animation_data", None)
            
            # Fetch F-Curves for position
            fcurves = [None, None, None]
            if anim and anim.action:
                fcurves = [anim.action.fcurves.find('["Absolute_Position"]', index=i) for i in range(3)]
                
            px_base, py_base, pz_base = d["Absolute_Position"]

            for f in frames:
                px = fcurves[0].evaluate(f) if fcurves[0] else px_base
                py = fcurves[1].evaluate(f) if fcurves[1] else py_base
                pz = fcurves[2].evaluate(f) if fcurves[2] else pz_base
                
                # Multiply 3D vector by Viewport Projection Matrix (4x4)
                vec4 = proj_matrix @ mathutils.Vector((px, py, pz, 1.0))
                
                # Normalize Device Coordinates (NDC) -> Maps to range [-1.0, 1.0]
                if vec4.w != 0:
                    nx, ny = vec4.x / vec4.w, vec4.y / vec4.w
                else:
                    nx, ny = 0.0, 0.0
                    
                drone_paths[d.name][f] = (nx, ny)
                
                min_x = min(min_x, nx)
                max_x = max(max_x, nx)
                min_y = min(min_y, ny)
                max_y = max(max_y, ny)

        # 4. CALCULATE "COVER" MAPPING
        # Swarm Dimensions in Viewport space
        swarm_w = max_x - min_x
        swarm_h = max_y - min_y
        if swarm_w == 0: swarm_w = 1.0
        if swarm_h == 0: swarm_h = 1.0
        swarm_aspect = swarm_w / swarm_h
        
        # Center of the swarm in NDC
        cx = (min_x + max_x) / 2.0
        cy = (min_y + max_y) / 2.0
        
        # "Cover" Logic: We scale the video's normalized bounds to fully encompass the swarm
        if vid_aspect > swarm_aspect:
            # Video is wider. Match height, let width bleed off edges.
            map_h = swarm_h
            map_w = swarm_h * vid_aspect
        else:
            # Video is taller. Match width, let height bleed off edges.
            map_w = swarm_w
            map_h = swarm_w / vid_aspect

        # Mapping Boundaries for UV interpolation
        map_min_x = cx - (map_w / 2.0)
        map_min_y = cy - (map_h / 2.0)

        # 5. SAMPLE VIDEO PIXELS
        self.report({'INFO'}, "Sampling Video Frames...")
        drone_colors = {d.name: [] for d in drones}
        
        for f in frames:
            video_frame = max(0, f - 1)
            cap.set(cv2.CAP_PROP_POS_FRAMES, video_frame)
            ret, frame_img = cap.read()
            
            for d in drones:
                if not ret:
                    drone_colors[d.name].append((0.0, 0.0, 0.0))
                    continue
                
                nx, ny = drone_paths[d.name][f]
                
                # Interpolate from Map Bounds to 0.0-1.0
                u = (nx - map_min_x) / map_w
                v = (ny - map_min_y) / map_h
                
                # Convert to Pixel Coordinates (OpenCV Y is inverted)
                px_x = int(u * (vid_w - 1))
                px_y = int((1.0 - v) * (vid_h - 1))
                
                if 0 <= px_x < vid_w and 0 <= px_y < vid_h:
                    b, g, r = frame_img[px_y, px_x]
                    drone_colors[d.name].append((r/255.0, g/255.0, b/255.0))
                else:
                    drone_colors[d.name].append((0.0, 0.0, 0.0)) # Out of bounds (Black)
        
        cap.release()
        
        # 6. INJECT F-CURVES
        self.save_keyframes(context, drones, frames, drone_colors)
        self.report({'INFO'}, f"Successfully projected video onto {len(drones)} drones.")
        return {'FINISHED'}

    def save_keyframes(self, context, drones, frames, drone_colors):
        prop_name = utils.TARGET_COLOR_PROP
        data_path = f'["{prop_name}"]'
        
        for d in drones:
            colors = drone_colors.get(d.name)
            if not colors: continue
            
            if prop_name not in d.keys(): d[prop_name] = [0.0, 0.0, 0.0, 1.0]
            if not d.animation_data: d.animation_data_create()
            if not d.animation_data.action: d.animation_data.action = bpy.data.actions.new(name=f"{d.name}Action")
            action = d.animation_data.action
            
            c_np = np.array(colors, dtype=np.float32)
            f_np = np.array(frames, dtype=np.float32)
            
            for i in range(3):
                fc = action.fcurves.find(data_path=data_path, index=i)
                if not fc: fc = action.fcurves.new(data_path=data_path, index=i)
                
                # Combine old keys (outside our range) with new keys
                existing = []
                for kp in fc.keyframe_points:
                    if kp.co[0] < frames[0] or kp.co[0] > frames[-1]:
                        existing.append((kp.co[0], kp.co[1]))
                
                new_keys = np.column_stack((f_np, c_np[:, i]))
                if existing:
                    all_keys = np.vstack((existing, new_keys))
                    all_keys = all_keys[all_keys[:, 0].argsort()]
                else:
                    all_keys = new_keys
                
                fc.keyframe_points.clear()
                fc.keyframe_points.add(len(all_keys))
                fc.keyframe_points.foreach_set('co', all_keys.flatten())
                fc.update()