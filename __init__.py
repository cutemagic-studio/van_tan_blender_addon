bl_info = {
    "name": "[VT] Ultimate Workflow System",
    "author": "VT & Gemini",
    "version": (2, 2, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Ctrl+Shift+0",
    "category": "Object",
}

import bpy
from . import constants
from . import operators, keymaps, hud

# Cơ chế Reload để phát triển
if "bpy" in locals():
    import importlib
    importlib.reload(constants) # Thêm dòng này
    importlib.reload(operators)
    importlib.reload(keymaps)
    importlib.reload(hud)

def register():
    operators.register()
    keymaps.register()

def unregister():
    keymaps.unregister()
    operators.unregister()