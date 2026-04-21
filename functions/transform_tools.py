import bpy
import mathutils
import os
from mathutils import Vector

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

# =========================
# Origin → Bottom (multi)
# =========================
# def origin_to_bottom_selected():
#     selected = bpy.context.selected_objects
#     if not selected:
#         print("Không có object nào được chọn")
#         return

#     # Lưu cursor
#     old_cursor = bpy.context.scene.cursor.location.copy()

#     for obj in selected:
#         if obj.type != 'MESH':
#             continue

#         bpy.context.view_layer.objects.active = obj

#         if bpy.context.mode != 'OBJECT':
#             bpy.ops.object.mode_set(mode='OBJECT')

#         # Lưu world transform
#         mw = obj.matrix_world.copy()

#         # Tính bounding box world
#         bbox = [mw @ mathutils.Vector(v) for v in obj.bound_box]

#         min_z = min(v.z for v in bbox)
#         center_x = sum(v.x for v in bbox) / 8
#         center_y = sum(v.y for v in bbox) / 8

#         # Move cursor
#         bpy.context.scene.cursor.location = (center_x, center_y, min_z)

#         # Set origin
#         bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

#         # Restore transform (🔥 quan trọng)
#         obj.matrix_world = mw

#     # Restore cursor
#     bpy.context.scene.cursor.location = old_cursor

#     print(f"Đã xử lý origin cho {len(selected)} object(s)")

def origin_to_bottom_selected():
    # 1. Lưu danh sách các object đang chọn ban đầu
    original_selection = bpy.context.selected_objects[:]
    if not original_selection:
        print("Không có object nào được chọn")
        return

    # Lưu vị trí Cursor cũ
    old_cursor = bpy.context.scene.cursor.location.copy()

    # Chuyển về Object Mode một lần duy nhất ở đầu
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    for obj in original_selection:
        if obj.type != 'MESH':
            continue

        # 🔥 QUAN TRỌNG: Cô lập object hiện tại để lệnh Origin_set chỉ tác động lên nó
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj

        # (1) Tính toán vị trí đáy trong WORLD space của RIÊNG object này
        mw = obj.matrix_world
        bbox = [mw @ mathutils.Vector(v) for v in obj.bound_box]

        min_z = min(v.z for v in bbox)
        center_x = sum(v.x for v in bbox) / 8
        center_y = sum(v.y for v in bbox) / 8

        # (2) Đặt cursor tại đáy của RIÊNG object này
        bpy.context.scene.cursor.location = (center_x, center_y, min_z)

        # (3) Di chuyển origin (Chỉ tác động lên object đang Active)
        # Blender tự bù trừ để mesh không bị nhảy
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    # --- KẾT THÚC VÒNG LẶP ---

    # 4. Khôi phục lại lựa chọn ban đầu cho người dùng
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        obj.select_set(True)
    
    # Khôi phục Cursor
    bpy.context.scene.cursor.location = old_cursor

    print(f"✅ Đã xử lý Origin độc lập cho {len(original_selection)} object(s)")

# =========================
# Drop to floor (multi)
# =========================
def drop_to_floor_selected():
    selected = bpy.context.selected_objects
    if not selected:
        print("Không có object nào được chọn")
        return

    for obj in selected:
        if obj.type != 'MESH':
            continue

        bpy.context.view_layer.objects.active = obj

        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

        # Evaluated mesh (tính modifier)
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()

        mw = obj.matrix_world

        min_z = min((mw @ v.co).z for v in mesh.vertices)

        # Move xuống sàn
        obj.location.z -= min_z

        eval_obj.to_mesh_clear()

    print(f"Đã drop {len(selected)} object(s) xuống floor")


# =========================
# Gộp lại (1-click)
# =========================
def prepare_selected_for_unity():
    origin_to_bottom_selected()
    drop_to_floor_selected() 


def export_each_object_to_fbx(context, export_folder="X:/UNITY_STORE/ALL_PACK/EXPORT_FBX_ALL"):
# def export_each_object_to_fbx(context, export_folder="G:/Blender_Export_Data_Json/"):
    # Đảm bảo thư mục tồn tại
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    # Lấy danh sách object đang chọn (để linh hoạt hơn là quét cả scene)
    selected_objs = context.selected_objects[:]
    
    if not selected_objs:
        print("Không có object nào được chọn để export.")
        return False

    # Lưu lại Cursor hoặc Mode nếu cần, nhưng ở đây ta xử lý trực tiếp
    for obj in selected_objs:
        if obj.type != 'MESH':
            continue

        # Active và Select duy nhất object này để ops hoạt động chuẩn
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # 1. Apply transform (Nướng tọa độ vào mesh)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # 2. Tính toán offset để đưa Pivot về đáy (Bottom Center)
        mesh = obj.data
        verts = [v.co for v in mesh.vertices]

        min_z = min(v.z for v in verts)
        min_x = min(v.x for v in verts)
        max_x = max(v.x for v in verts)
        min_y = min(v.y for v in verts)
        max_y = max(v.y for v in verts)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        offset = Vector((center_x, center_y, min_z))

        # 3. Di chuyển các đỉnh của Mesh ngược lại offset (Edit mode ảo)
        for v in mesh.vertices:
            v.co -= offset
        
        mesh.update()

        # 4. Đưa Object về gốc tọa độ World (để file FBX sạch sẽ khi vào Unity)
        obj.location = (0, 0, 0)

        # 5. Thực hiện Export FBX
        # Sử dụng tên object làm tên file, rsplit để bỏ đuôi .001 nếu có
        clean_name = obj.name.rsplit('.', 1)[0]
        filepath = os.path.join(export_folder, f"{clean_name}.fbx")

        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            axis_forward='-Z',
            axis_up='Y',
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=True # Tương đương "Apply Transform" trong UI
        )

    print(f"DONE EXPORT: {len(selected_objs)} files in {export_folder}")
    return True

