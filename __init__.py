bl_info = {
    "name": "BetterColour",
    "author": "Raghuvansh Agarwal",
    "version": (2, 0, 5),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > Better Colour",
    "description": "Improved drone color & effector controls with Palettes",
    "category": "3D View",
}

import sys
import os
import platform
import bpy

current_dir = os.path.dirname(os.path.realpath(__file__))
system_platform = platform.system().lower() 

if system_platform == 'windows':
    dep_folder = "win"
elif system_platform == 'darwin':
    dep_folder = "mac"
else:
    dep_folder = "linux"

dep_path = os.path.join(current_dir, "dependencies", dep_folder)
if dep_path not in sys.path:
    sys.path.insert(0, dep_path)

from bpy.props import (StringProperty, EnumProperty, FloatProperty, IntProperty,
                       FloatVectorProperty, CollectionProperty, BoolProperty, PointerProperty)

from . import utils
from . import properties
from . import ui
from . import operators

class LightingModPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    use_experimental_updates: BoolProperty(name="Opt-in to Experimental Beta Updates", default=False)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "use_experimental_updates")
        btn_text = "Check for Beta Updates" if self.use_experimental_updates else "Check for Stable Updates"
        layout.operator("lightingmod.update_addon", text=btn_text, icon='FILE_REFRESH')

def _on_effector_type_changed(self, context):
    if context.scene.effector_type == 'SPARKLE' and not context.scene.spark_profiles:
        p = context.scene.spark_profiles.add()
        p.name = "Base Profile"

def _trigger_noise_preview(self, context):
    from . import utils
    utils.update_noise_preview(context)

def _update_gradient_preview(self, context):
    sc = context.scene
    if not sc.gradient_palettes: return
    item = sc.gradient_palettes[sc.gradient_palettes_index]
    
    ng = utils.ensure_gradient_preview_nodegroup()
    ramp = ng.nodes["Ramp"].color_ramp
    
    for i in range(len(ramp.elements)-1, 0, -1):
        ramp.elements.remove(ramp.elements[i])
        
    ramp.elements[0].position = item.stops[0].pos
    ramp.elements[0].color = list(item.stops[0].color) + [1.0]
    
    for i in range(1, len(item.stops)):
        el = ramp.elements.new(item.stops[i].pos)
        el.color = list(item.stops[i].color) + [1.0]

def register():
    bpy.utils.register_class(LightingModPreferences)
    properties.register()
    ui.register()
    operators.register()

    sc = bpy.types.Scene
    sc.batch_primary_color = FloatVectorProperty(subtype='COLOR',size=4,default=(1,1,1,1),min=0,max=1)
    sc.batch_secondary_color = FloatVectorProperty(subtype='COLOR',size=4,default=(0,0,0,1),min=0,max=1)
    
    # --- Palette Props ---
    sc.color_palettes = CollectionProperty(type=properties.LightingModColorPaletteItem)
    sc.color_palettes_index = IntProperty(default=0)
    sc.show_color_palettes = BoolProperty(default=False)
    
    sc.gradient_palettes = CollectionProperty(type=properties.LightingModGradientPaletteItem)
    sc.gradient_palettes_index = IntProperty(default=0, update=_update_gradient_preview)
    sc.show_gradient_palettes = BoolProperty(default=False)
    
    sc.effector_selection_mode = EnumProperty(
        name="Target", items=[('SELECTED', "Selected Objects", ""), ('GROUP', "Active Group", "")], default='SELECTED'
    )
    sc.effector_type = EnumProperty(
        name="Type",
        items=[
          ('GRADIENT','Gradient',''), ('SPARKLE','Sparkle',''), ('TEMPORAL_SPARKLE','Temporal Sparkle',''),
          ('NOISE', 'Noise', ''), ('DOMAIN','Domain',''), ('MOVIE','Movie UV',''), ('OFFSET','Offset',''),
        ], default='SPARKLE', update=_on_effector_type_changed
    )
    sc.sparkle_style = EnumProperty(
        name="Style", items=[('PULSE', 'Pulse (Smooth Fade)', ''), ('TWINKLE', 'Twinkle (Sharp Pop)', '')], default='PULSE'
    )

    sc.effector_start = IntProperty(name="Start", default=1)
    sc.effector_end = IntProperty(name="End", default=250)
    sc.effector_transition = IntProperty(name="Transition", default=10, min=0)
    sc.effector_influence = FloatProperty(name="Influence", min=0, max=1, default=0.5)
    sc.effector_selected_only = BoolProperty(name="Selected Only", default=False)
    sc.domain_object = PointerProperty(name="Domain Object", type=bpy.types.Object)
    sc.effector_duration = IntProperty(name="Duration", default=10, min=0)
    sc.effector_colors = CollectionProperty(type=properties.LightingModEffectorColorItem)
    sc.effector_colors_index = IntProperty(default=0)
    sc.movie_step = IntProperty(name="Step", default=1, min=1)

    sc.gradient_mode = EnumProperty(
        name="Mode",
        items=[
          ('LINEAR','Linear',''), ('SPLIT','Split Linear',''), ('RADIAL_2D','2D Radial',''),
          ('RADIAL_3D','3D Radial',''), ('CURVE','Curve',''),
        ], default='LINEAR'
    )
    sc.gradient_ng = PointerProperty(type=bpy.types.NodeTree)
    sc.curve_object = PointerProperty(name="Curve", type=bpy.types.Object)
    sc.curve_radius = FloatProperty(name="Radius", default=0.5)
    sc.curve_mode   = EnumProperty(items=[('PER_CURVE', 'Each Curve 0-1', ''), ('GLOBAL', 'Relative to Longest', '')], default='PER_CURVE')
    sc.offset_line_start = FloatVectorProperty(name="Offset Line Start", size=3, subtype='XYZ', default=(0.0, 0.0, 0.0))
    sc.offset_line_end = FloatVectorProperty(name="Offset Line End", size=3, subtype='XYZ', default=(0.0, 0.0, 0.0))
    sc.drone_formations = CollectionProperty(type=properties.LightingModFormation)
    sc.drone_formations_index = IntProperty()
    sc.temporal_stages = CollectionProperty(type=properties.LightingModTemporalStage)
    sc.temporal_stages_index = IntProperty()
    sc.spark_profiles = CollectionProperty(type=properties.LightingModSparkProfile)
    sc.spark_profiles_index = IntProperty(default=0)
    sc.use_advanced_spark_profiles = BoolProperty(name="Use Multiple Profiles", default=False)

    sc.noise_type = bpy.props.EnumProperty(
        name="Noise Type", items=[('PERLIN', 'Perlin (Clouds)', ''), ('VORONOI', 'Voronoi (Cells)', '')], 
        default='PERLIN', update=_trigger_noise_preview
    )
    sc.noise_scale = bpy.props.FloatProperty(name="Scale", default=0.02, min=0.001, update=_trigger_noise_preview)
    sc.noise_contrast = bpy.props.FloatProperty(name="Contrast", default=0.0, min=0.0, max=1.0, update=_trigger_noise_preview)
    sc.noise_direction = bpy.props.FloatVectorProperty(name="Direction", default=(0.0, 0.0, 1.0), subtype='XYZ', update=_trigger_noise_preview)
    sc.noise_speed = bpy.props.FloatProperty(name="Speed", default=1.0, update=_trigger_noise_preview)
    sc.noise_fade_in = bpy.props.IntProperty(name="Fade In", default=0, min=0)
    sc.noise_fade_out = bpy.props.IntProperty(name="Fade Out", default=0, min=0)

    try:
        if bpy.context: utils.set_editor_filter_for_layer(bpy.context, utils.TARGET_COLOR_PROP)
    except: pass

def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()
    bpy.utils.unregister_class(LightingModPreferences)
    
    del bpy.types.Scene.batch_primary_color
    del bpy.types.Scene.batch_secondary_color
    del bpy.types.Scene.color_palettes
    del bpy.types.Scene.color_palettes_index
    del bpy.types.Scene.show_color_palettes
    del bpy.types.Scene.gradient_palettes
    del bpy.types.Scene.gradient_palettes_index
    del bpy.types.Scene.show_gradient_palettes
    del bpy.types.Scene.effector_selection_mode
    del bpy.types.Scene.effector_type
    del bpy.types.Scene.effector_start
    del bpy.types.Scene.effector_end
    del bpy.types.Scene.effector_transition
    del bpy.types.Scene.effector_influence
    del bpy.types.Scene.effector_selected_only
    del bpy.types.Scene.domain_object
    del bpy.types.Scene.effector_duration
    del bpy.types.Scene.effector_colors
    del bpy.types.Scene.effector_colors_index
    del bpy.types.Scene.movie_step
    del bpy.types.Scene.gradient_mode
    del bpy.types.Scene.gradient_ng
    del bpy.types.Scene.curve_object
    del bpy.types.Scene.curve_radius
    del bpy.types.Scene.curve_mode
    del bpy.types.Scene.offset_line_start
    del bpy.types.Scene.offset_line_end
    del bpy.types.Scene.drone_formations
    del bpy.types.Scene.drone_formations_index
    del bpy.types.Scene.temporal_stages
    del bpy.types.Scene.temporal_stages_index
    del bpy.types.Scene.spark_profiles
    del bpy.types.Scene.spark_profiles_index
    del bpy.types.Scene.use_advanced_spark_profiles
    del bpy.types.Scene.noise_type
    del bpy.types.Scene.noise_scale
    del bpy.types.Scene.noise_contrast
    del bpy.types.Scene.noise_direction
    del bpy.types.Scene.noise_speed
    del bpy.types.Scene.noise_fade_in
    del bpy.types.Scene.noise_fade_out

if __name__ == "__main__":
    register()