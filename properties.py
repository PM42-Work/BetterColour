import bpy
from bpy.props import (StringProperty, EnumProperty, FloatProperty, BoolProperty, FloatVectorProperty, CollectionProperty, IntProperty)
from . import utils

class LightingModEffectorColorItem(bpy.types.PropertyGroup):
    color: FloatVectorProperty(
        name="Color", subtype='COLOR', size=4,
        min=0.0, max=1.0, default=(1,1,1,1)
    )

class LightingModTemporalStage(bpy.types.PropertyGroup):
    name: StringProperty(name="Name", default="Stage")
    transition: IntProperty(name="Transition", min=1, default=10)
    influence: FloatProperty(name="Influence", min=0, max=1, default=0.5)
    colors: CollectionProperty(type=LightingModEffectorColorItem)
    colors_index: IntProperty(default=0)

class LightingModSparkProfile(bpy.types.PropertyGroup):
    name: StringProperty(name="Profile Name", default="Profile")
    style: EnumProperty(
        name="Style",
        items=[('PULSE', 'Pulse', ''), ('TWINKLE', 'Twinkle', '')],
        default='PULSE'
    )
    weight: FloatProperty(name="Weight", min=0.0, default=1.0)
    lifespan: IntProperty(name="Lifespan", min=1, default=10)
    colors: CollectionProperty(type=LightingModEffectorColorItem)
    colors_index: IntProperty(default=0)

class LightingModDroneRef(bpy.types.PropertyGroup):
    object_name: StringProperty(name="Object")

class LightingModDroneGroup(bpy.types.PropertyGroup):
    name: StringProperty(name="Group Name", default="Group")
    drones: CollectionProperty(type=LightingModDroneRef)
    drones_index: IntProperty(default=0)

class LightingModFormation(bpy.types.PropertyGroup):
    name: StringProperty(name="Formation Name", default="Formation")
    groups: CollectionProperty(type=LightingModDroneGroup)
    groups_index: IntProperty(default=0)

classes = (
    LightingModEffectorColorItem,
    LightingModTemporalStage,
    LightingModSparkProfile, 
    LightingModDroneRef,
    LightingModDroneGroup,
    LightingModFormation,
)

def register():
    for cls in classes: bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes): bpy.utils.unregister_class(cls)