import bpy
from . import utils

class LIGHTINGMOD_UL_color_palettes(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row(align=True)
        row.prop(item, "color", text="", emboss=True)
        row.prop(item, "name", text="", emboss=False)

class LIGHTINGMOD_UL_gradient_palettes(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "name", text="", emboss=False, icon='COLOR')

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
        
        # --- NEW: Color Palette ---
        icon = 'TRIA_DOWN' if sc.show_color_palettes else 'TRIA_RIGHT'
        box.prop(sc, "show_color_palettes", icon=icon, text="Color Palette", emboss=False)
        if sc.show_color_palettes:
            pbox = box.box()
            pbox.template_list("LIGHTINGMOD_UL_color_palettes", "", sc, "color_palettes", sc, "color_palettes_index", rows=3)
            row = pbox.row(align=True)
            row.operator("lightingmod.save_color", icon='ADD', text="Save Primary")
            row.operator("lightingmod.remove_color", icon='REMOVE', text="")
            pbox.operator("lightingmod.apply_color", icon='RESTRICT_COLOR_OFF', text="Set as Primary")

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
                    
                # --- NEW: Gradient Library ---
                icon = 'TRIA_DOWN' if sc.show_gradient_palettes else 'TRIA_RIGHT'
                box.prop(sc, "show_gradient_palettes", icon=icon, text="Gradient Library", emboss=False)
                
                if sc.show_gradient_palettes:
                    gbox = box.box()
                    if not sc.gradient_palettes:
                        gbox.operator("lightingmod.load_presets", text="Load Defaults", icon='FILE_TICK')
                    else:
                        gbox.template_list("LIGHTINGMOD_UL_gradient_palettes", "", sc, "gradient_palettes", sc, "gradient_palettes_index", rows=4)
                        row = gbox.row(align=True)
                        row.operator("lightingmod.save_gradient", icon='ADD', text="Save Active")
                        row.operator("lightingmod.remove_gradient", icon='REMOVE', text="")
                        
                        # Live Preview
                        png = utils.ensure_gradient_preview_nodegroup()
                        pramp = png.nodes["Ramp"]
                        pcol = gbox.column(align=True)
                        pcol.label(text="Preview:")
                        pcol.template_color_ramp(pramp, "color_ramp")
                        gbox.operator("lightingmod.apply_gradient", icon='CHECKMARK', text="Apply to Active")

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
        
        # Formations
        box = main_col.box()
        box.label(text="Formations & Groups", icon='GROUP')
        box.template_list("LIGHTINGMOD_UL_formations", "", sc, "drone_formations", sc, "drone_formations_index", rows=2)
        row = box.row(align=True)
        row.operator("lightingmod.formation_add", icon='ADD', text=""); row.operator("lightingmod.formation_remove", icon='REMOVE', text="")

        if sc.drone_formations:
            f = sc.drone_formations[sc.drone_formations_index]
            sub = box.box(); sub.label(text=f"Groups in {f.name}")
            sub.template_list("LIGHTINGMOD_UL_groups", "", f, "groups", f, "groups_index", rows=2)
            row = sub.row(align=True)
            row.operator("lightingmod.group_add", icon='ADD', text=""); row.operator("lightingmod.group_remove", icon='REMOVE', text="")

            if f.groups:
                g = f.groups[f.groups_index]
                sub2 = sub.box(); sub2.label(text=f"Drones in {g.name}")
                sub2.template_list("LIGHTINGMOD_UL_group_drones", "", g, "drones", g, "drones_index", rows=4)
                row = sub2.row(align=True)
                row.operator("lightingmod.group_add_selected", icon='IMPORT', text="Add"); row.operator("lightingmod.group_remove_selected", icon='TRASH', text="Remove")
                row = sub2.row(align=True)
                op = row.operator("lightingmod.group_select", icon='RESTRICT_SELECT_OFF', text="Select"); op.additive = False
                op = row.operator("lightingmod.group_select", icon='ADD', text="+"); op.additive = True

        # --- JSON Import/Export ---
        box = main_col.box()
        box.label(text="JSON Palettes", icon='OUTLINER_DATA_GPENCIL')
        row = box.row(align=True)
        row.operator("lightingmod.import_palettes", text="Import", icon='IMPORT')
        row.operator("lightingmod.export_palettes", text="Export", icon='EXPORT')

classes = (
    LIGHTINGMOD_UL_color_palettes, LIGHTINGMOD_UL_gradient_palettes,
    LIGHTINGMOD_UL_effector_colors, LIGHTINGMOD_UL_formations, 
    LIGHTINGMOD_UL_groups, LIGHTINGMOD_UL_group_drones, LIGHTINGMOD_UL_temporal_stages,
    LIGHTINGMOD_UL_spark_profiles, LIGHTINGMOD_PT_panel,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)
def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)