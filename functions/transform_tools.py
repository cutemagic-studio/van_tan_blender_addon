import bpy
import mathutils

def origin_to_bottom():
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
            
        old_cursor_loc = bpy.context.scene.cursor.location.copy()
        matrix_w = obj.matrix_world
        bbox = [matrix_w @ mathutils.Vector(v) for v in obj.bound_box]
        
        min_z = min(v.z for v in bbox)
        center_x = sum(v.x for v in bbox) / 8
        center_y = sum(v.y for v in bbox) / 8
        
        bpy.context.scene.cursor.location = (center_x, center_y, min_z)
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.scene.cursor.location = old_cursor_loc

def drop_to_floor():
    obj = bpy.context.active_object
    if obj and obj.type == 'MESH':
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        matrix_w = obj.matrix_world
        min_z = min((matrix_w @ v.co).z for v in obj.data.vertices)
        obj.location.z -= min_z