import bpy
from . import utils

class LIGHTINGMOD_UL_effector_colors(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "color", text="", emboss=True)

class LIGHTINGMOD_UL_formations(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='OUTLINER_COLLECTION')

class LIGHTINGMOD_UL_groups(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='GROUP')

class LIGHTINGMOD_UL_group_drones(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.label(text=item.object_name, icon='MESH_UVSPHERE')

class LIGHTINGMOD_UL_temporal_stages(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='TIME')

class LIGHTINGMOD_UL_spark_profiles(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "name", text="", emboss=False, icon='SHADERFX')
        row.label(text=item.style.capitalize())

class LIGHTINGMOD_PT_panel(bpy.types.Panel):
    bl_label="Better Colour"; bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category="Better Colour"

    def draw(self, context):
        sc=context.scene; layout=self.layout
        main_col = layout.column()

        # Tools
        box = main_col.box(); box.label(text="Tools")
        box.operator("lightingmod.bake_positions", icon='CON_LOCLIKE', text="Bake Positions")

        # Batch Color
        box=main_col.box(); box.label(text=f"Batch Color ({utils.TARGET_COLOR_PROP})")
        row=box.row(align=True)
        row.prop(sc,"batch_primary_color",text="")
        row.operator("lightingmod.swap_batch_colors",icon='FILE_REFRESH',text="")
        row.prop(sc,"batch_secondary_color",text="")
        col=box.column(align=True)
        col.operator("lightingmod.batch_color_keyframe",text="Color & Keyframe")
        col.operator("lightingmod.batch_color",       text="Color Only")
        col.operator("lightingmod.keyframe_current",  text="Keyframe Current")
        col.operator("lightingmod.undo_last_edit",    text="Undo Last Edit")

        # Effectors
        box=main_col.box(); box.label(text="Effectors")
        box.prop(sc,"effector_type",       text="Type")
        box.prop(sc,"effector_selection_mode", text="Apply To")

        tp = sc.effector_type
        if tp not in {'GRADIENT','OFFSET'}:
            row=box.row(align=True)
            row.prop(sc,"effector_start",text="Start")
            row.prop(sc,"effector_end",  text="End")
            row=box.row(align=True)
            row.operator("lightingmod.set_start_frame",icon='PREV_KEYFRAME',text="")
            row.operator("lightingmod.set_end_frame",  icon='NEXT_KEYFRAME',text="")

        if tp=='SPARKLE':
            box.prop(sc, "effector_influence", text="Density")
            box.prop(sc, "use_advanced_spark_profiles", text="Use Multiple Profiles", icon='TRIA_DOWN' if sc.use_advanced_spark_profiles else 'TRIA_RIGHT')
            
            if not sc.spark_profiles:
                box.operator("lightingmod.spark_profile_add", text="Initialize Base Profile", icon='ADD')
            else:
                if sc.use_advanced_spark_profiles:
                    box.label(text="Profiles")
                    box.template_list("LIGHTINGMOD_UL_spark_profiles", "", sc, "spark_profiles", sc, "spark_profiles_index", rows=3)
                    row = box.row(align=True)
                    row.operator("lightingmod.spark_profile_add", icon='ADD', text="")
                    row.operator("lightingmod.spark_profile_remove", icon='REMOVE', text="")

                    if sc.spark_profiles:
                        prof = sc.spark_profiles[sc.spark_profiles_index]
                        p_box = box.box()
                        p_box.label(text=f"Editing: {prof.name}")
                        p_box.prop(prof, "style", text="Style")
                        p_box.prop(prof, "weight", text="Relative Weight")
                        p_box.prop(prof, "lifespan", text="Lifespan (Frames)")
                        p_box.template_list("LIGHTINGMOD_UL_effector_colors", "", prof, "colors", prof, "colors_index", rows=2)
                        row = p_box.row(align=True)
                        op = row.operator("lightingmod.effector_color_add", icon='ADD', text=""); op.target = 'SPARK_PROFILE'
                        op = row.operator("lightingmod.effector_color_remove", icon='REMOVE', text=""); op.target = 'SPARK_PROFILE'
                else:
                    prof = sc.spark_profiles[0]
                    box.prop(prof, "style", text="Style")
                    box.prop(prof, "lifespan", text="Lifespan (Frames)")
                    box.label(text="Colors")
                    box.template_list("LIGHTINGMOD_UL_effector_colors", "", prof, "colors", prof, "colors_index", rows=3)
                    row = box.row(align=True)
                    op = row.operator("lightingmod.effector_color_add", icon='ADD', text=""); op.target = 'SPARK_PROFILE'
                    op = row.operator("lightingmod.effector_color_remove", icon='REMOVE', text=""); op.target = 'SPARK_PROFILE'

        elif tp=='TEMPORAL_SPARKLE':
            box.prop(sc, "sparkle_style")
            box.label(text="Temporal Stages")
            box.template_list("LIGHTINGMOD_UL_temporal_stages", "", sc, "temporal_stages", sc, "temporal_stages_index", rows=2)
            row = box.row(align=True)
            row.operator("lightingmod.stage_add", icon='ADD', text=""); row.operator("lightingmod.stage_remove", icon='REMOVE', text="")
            if sc.temporal_stages:
                stage = sc.temporal_stages[sc.temporal_stages_index]
                box.prop(stage, "transition", text="Lifespan"); box.prop(stage, "influence")
                box.template_list("LIGHTINGMOD_UL_effector_colors", "", stage, "colors", stage, "colors_index", rows=3)
                row=box.row(align=True)
                op=row.operator("lightingmod.effector_color_add",icon='ADD',text=""); op.target='TEMPORAL_STAGE'
                op=row.operator("lightingmod.effector_color_remove",icon='REMOVE',text=""); op.target='TEMPORAL_STAGE'

        elif tp == 'NOISE':
            box.label(text="Shape")
            box.prop(sc, "noise_type", text="")
            box.prop(sc, "noise_scale")
            box.prop(sc, "noise_contrast")
            box.label(text="Motion")
            row = box.row()
            col = row.column(align=True)
            col.prop(sc, "noise_direction", index=0, text="Flow X")
            col.prop(sc, "noise_direction", index=1, text="Flow Y")
            col.prop(sc, "noise_direction", index=2, text="Flow Z")
            row.operator("lightingmod.draw_noise_flow", icon='BRUSH_DATA', text="Draw")
            box.prop(sc, "noise_speed")
            box.label(text="Fading (Frames)")
            row = box.row(align=True)
            row.prop(sc, "noise_fade_in", text="Fade In")
            row.prop(sc, "noise_fade_out", text="Fade Out")
            box.label(text="Colors")
            ng = bpy.data.node_groups.get("LightingModNoiseRamp")
            if ng and "Ramp" in ng.nodes: 
                ramp_node = ng.nodes["Ramp"]
                row = box.row(align=True)
                row.prop(ramp_node.color_ramp, "color_mode", text="")
                row.prop(ramp_node.color_ramp, "interpolation", text="")
                box.template_color_ramp(ramp_node, "color_ramp")
            else: 
                box.operator("lightingmod.create_noise_nodegroup", text="Create Ramp")

        elif tp in {'GRADIENT', 'OFFSET'}:
            box.prop(sc, "gradient_mode", text="Mode")
            if sc.gradient_mode == 'CURVE':
                box.prop(sc, "curve_object"); box.prop(sc, "curve_radius"); box.prop(sc, "curve_mode")
            if tp == 'GRADIENT':
                ng = bpy.data.node_groups.get("LightingModGradient")
                if ng and "Ramp" in ng.nodes: 
                    ramp_node = ng.nodes["Ramp"]
                    row = box.row(align=True)
                    row.prop(ramp_node.color_ramp, "color_mode", text="")
                    row.prop(ramp_node.color_ramp, "interpolation", text="")
                    box.template_color_ramp(ramp_node, "color_ramp")
                else: 
                    box.operator("lightingmod.create_gradient_nodegroup", text="Create Ramp")
                box.operator("lightingmod.flip_color_ramp", icon='FILE_REFRESH', text="Flip Gradient Colors")
                if sc.gradient_mode != 'CURVE': box.operator("lightingmod.draw_gradient", icon='BRUSH_DATA', text="Draw Gradient")
            else:
                box.prop(sc, "effector_duration")
                if sc.gradient_mode != 'CURVE': box.operator("lightingmod.draw_offset_line", icon='BRUSH_DATA', text="Draw Offset Line")

        if tp=='DOMAIN':
            box.prop(sc,"domain_object"); box.template_list("LIGHTINGMOD_UL_effector_colors","",sc,"effector_colors",sc,"effector_colors_index",rows=3)
            row=box.row(align=True); row.operator("lightingmod.effector_color_add",icon='ADD',text=""); row.operator("lightingmod.effector_color_remove",icon='REMOVE',text="")

        elif tp == 'MOVIE':
            box.label(text="Viewport Projection", icon='RESTRICT_VIEW_OFF')
            box.label(text="Note: Bakes based on your current 3D camera angle.", icon='INFO')
            box.prop(sc, "movie_step")

        box.operator("lightingmod.apply_effectors", text="Apply")


class LIGHTINGMOD_PT_drone_groups(bpy.types.Panel):
    bl_label="Formations & Groups"; bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category="Better Colour"
    
    def draw(self, context):
        sc = context.scene; layout = self.layout
        layout.label(text="Formations")
        layout.template_list("LIGHTINGMOD_UL_formations", "", sc, "drone_formations", sc, "drone_formations_index", rows=2)
        row = layout.row(align=True)
        row.operator("lightingmod.formation_add", icon='ADD', text=""); row.operator("lightingmod.formation_remove", icon='REMOVE', text="")

        if sc.drone_formations:
            f = sc.drone_formations[sc.drone_formations_index]
            box = layout.box(); box.label(text=f"Groups in {f.name}")
            box.template_list("LIGHTINGMOD_UL_groups", "", f, "groups", f, "groups_index", rows=2)
            row = box.row(align=True)
            row.operator("lightingmod.group_add", icon='ADD', text=""); row.operator("lightingmod.group_remove", icon='REMOVE', text="")

            if f.groups:
                g = f.groups[f.groups_index]
                sub = box.box(); sub.label(text=f"Drones in {g.name}")
                sub.template_list("LIGHTINGMOD_UL_group_drones", "", g, "drones", g, "drones_index", rows=4)
                row = sub.row(align=True)
                row.operator("lightingmod.group_add_selected", icon='IMPORT', text="Add"); row.operator("lightingmod.group_remove_selected", icon='TRASH', text="Remove")
                row = sub.row(align=True)
                op = row.operator("lightingmod.group_select", icon='RESTRICT_SELECT_OFF', text="Select"); op.additive = False
                op = row.operator("lightingmod.group_select", icon='ADD', text="+"); op.additive = True

class LIGHTINGMOD_PT_export(bpy.types.Panel):
    bl_label="Export Colors"; bl_space_type='VIEW_3D'; bl_region_type='UI'; bl_category="Better Colour"
    def draw(self, context):
        sc=context.scene; layout=self.layout
        layout.prop(sc,"export_folder",text="CSV Folder")
        layout.prop(sc, "export_filename", text="Filename")
        col = layout.column(align=True)
        col.operator("lightingmod.export_csv_colors", text="Overwrite CSV Colors", icon='FILE_TEXT')
        col.operator("lightingmod.export_color_transfer", text="Export Colour Transfer", icon='EXPORT')

classes = (
    LIGHTINGMOD_UL_effector_colors, LIGHTINGMOD_UL_formations, 
    LIGHTINGMOD_UL_groups, LIGHTINGMOD_UL_group_drones, LIGHTINGMOD_UL_temporal_stages,
    LIGHTINGMOD_UL_spark_profiles, LIGHTINGMOD_PT_panel, LIGHTINGMOD_PT_drone_groups, LIGHTINGMOD_PT_export,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)