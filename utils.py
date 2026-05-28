import bpy

# --- CONFIGURATION ---
# The name of the custom property on the objects where color is written.
TARGET_COLOR_PROP = "md_layer_1" 

last_batch_history = {}
baked_colors = {}

# --- Helper Functions ---
def set_editor_filter_for_layer(context, prop_name: str):
    for win in context.window_manager.windows:
        for area in win.screen.areas:
            if area.type in {'GRAPH_EDITOR', 'DOPESHEET_EDITOR'}:
                space = area.spaces.active
                ds = getattr(space, "dopesheet", None)
                if ds:
                    ds.show_only_selected = True
                    ds.use_multi_word_filter = False
                    ds.filter_text = prop_name
                area.tag_redraw()

def ensure_gradient_nodegroup():
    ng = bpy.data.node_groups.get("LightingModGradient")
    if not ng:
        ng = bpy.data.node_groups.new("LightingModGradient", 'ShaderNodeTree')
    if "Ramp" not in ng.nodes:
        ramp = ng.nodes.new('ShaderNodeValToRGB')
        ramp.name = "Ramp"
        ramp.label = "Gradient Ramp"
    return ng

def ensure_noise_nodegroup():
    ng = bpy.data.node_groups.get("LightingModNoiseRamp")
    if not ng:
        ng = bpy.data.node_groups.new("LightingModNoiseRamp", 'ShaderNodeTree')
        ng.interface.new_socket(name="Value", in_out='INPUT', socket_type='NodeSocketFloat')
        ng.interface.new_socket(name="Color", in_out='OUTPUT', socket_type='NodeSocketColor')
        
        ramp = ng.nodes.new('ShaderNodeValToRGB')
        ramp.name = "Ramp"
        ramp.color_ramp.color_mode = 'OKLAB'
        ramp.color_ramp.interpolation = 'EASE'
        
        inp = ng.nodes.new('NodeGroupInput')
        outp = ng.nodes.new('NodeGroupOutput')
        
        ng.links.new(inp.outputs[0], ramp.inputs['Fac'])
        ng.links.new(ramp.outputs['Color'], outp.inputs[0])
    return ng

def update_noise_preview(context):
    sc = context.scene
    mat = bpy.data.materials.get("drone colour") 
    if not mat or not mat.use_nodes: return
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    
    if not getattr(sc, "noise_preview", False):
        for n in list(nodes):
            if n.name.startswith("LM_NoisePreview_"): nodes.remove(n)
        return

    rebuild = False
    mix = nodes.get("LM_NoisePreview_Mix")
    tex = nodes.get("LM_NoisePreview_Tex")
    if not mix or not tex: 
        rebuild = True
    else:
        if sc.noise_type == 'PERLIN' and tex.bl_idname != 'ShaderNodeTexNoise': rebuild = True
        if sc.noise_type == 'VORONOI' and tex.bl_idname != 'ShaderNodeTexVoronoi': rebuild = True

    if rebuild:
        for n in list(nodes):
            if n.name.startswith("LM_NoisePreview_"): nodes.remove(n)
        
        out_node = next((n for n in nodes if n.type == 'EMISSION'), None)
        if not out_node: return

        obj_info = nodes.new('ShaderNodeObjectInfo')
        obj_info.name = "LM_NoisePreview_Obj"; obj_info.location = (-1000, 200)
        
        add_node = nodes.new('ShaderNodeVectorMath')
        add_node.name = "LM_NoisePreview_Add"; add_node.operation = 'ADD'; add_node.location = (-800, 200)

        ramp_grp = nodes.new('ShaderNodeGroup')
        ramp_grp.name = "LM_NoisePreview_RampGrp"
        ramp_grp.node_tree = ensure_noise_nodegroup(); ramp_grp.location = (-400, 200)
        
        if sc.noise_type == 'PERLIN':
            tex = nodes.new('ShaderNodeTexNoise')
            tex.noise_dimensions = '3D'; tex.inputs['Detail'].default_value = 0.0
            if hasattr(tex, 'normalize'): tex.normalize = False
            links.new(tex.outputs['Fac'], ramp_grp.inputs['Value'])
        elif sc.noise_type == 'VORONOI':
            tex = nodes.new('ShaderNodeTexVoronoi')
            tex.voronoi_dimensions = '3D'; tex.feature = 'F1'; tex.distance = 'EUCLIDEAN'
            links.new(tex.outputs['Distance'], ramp_grp.inputs['Value'])
            
        tex.name = "LM_NoisePreview_Tex"; tex.location = (-600, 200)
        
        mix = nodes.new('ShaderNodeMix')
        mix.name = "LM_NoisePreview_Mix"; mix.data_type = 'RGBA'; mix.inputs[0].default_value = 1.0; mix.location = (-200, 200)
        
        links.new(obj_info.outputs['Location'], add_node.inputs[0])
        links.new(add_node.outputs['Vector'], tex.inputs['Vector'])
        
        orig_socket = out_node.inputs[0]
        if orig_socket.links: links.new(orig_socket.links[0].from_socket, mix.inputs[6]) 
        links.new(ramp_grp.outputs['Color'], mix.inputs[7]) 
        links.new(mix.outputs[2], orig_socket)

    tex = nodes.get("LM_NoisePreview_Tex")
    if tex: tex.inputs['Scale'].default_value = sc.noise_scale
    
    add_node = nodes.get("LM_NoisePreview_Add")
    if add_node:
        for i, axis in enumerate(['x', 'y', 'z']):
            d = add_node.inputs[1].driver_add("default_value", i)
            d.driver.expression = f"frame / 24.0 * {getattr(sc.noise_direction, axis)} * {sc.noise_speed}"