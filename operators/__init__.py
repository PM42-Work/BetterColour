from . import baking, batch, effectors, groups, updater

def register():
    baking.register()
    batch.register()
    effectors.register()
    groups.register()
    updater.register()

def unregister():
    updater.unregister()
    groups.unregister()
    effectors.unregister()
    batch.unregister()
    baking.unregister()