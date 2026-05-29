from . import baking, batch, effectors, groups, updater, palettes

def register():
    baking.register()
    batch.register()
    effectors.register()
    groups.register()
    updater.register()
    palettes.register()

def unregister():
    palettes.unregister()
    updater.unregister()
    groups.unregister()
    effectors.unregister()
    batch.unregister()
    baking.unregister()