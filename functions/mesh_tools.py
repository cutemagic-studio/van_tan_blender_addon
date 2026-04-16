import bpy
import bmesh
import math
from mathutils import Vector, Matrix

##### || ##### || #####

def smart_inset(context, thickness=0.05, outset=False):

    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False

    bm = bmesh.from_edit_mesh(obj.data)

    # check nhanh
    if not any(f.select for f in bm.faces):
        return False

    # inset
    bpy.ops.mesh.inset(
        thickness=thickness,
        use_relative_offset=False,
        use_boundary=True,
        use_outset=outset
    )

    return True

##### || ##### || #####

##### [STATE_MESH] => [STATE_PIVOT_LIST]

def pivot_to_edge_center(context, set_pivot=False):
    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False

    bm = bmesh.from_edit_mesh(obj.data)
    selected_edges = [e for e in bm.edges if e.select]

    if not selected_edges:
        return False

    world_matrix = obj.matrix_world

    # Dùng set để lấy các đỉnh duy nhất từ danh sách cạnh (tránh tính lặp)
    unique_verts = {v for e in selected_edges for v in e.verts}
    
    # Tính toán trọng tâm (Centroid)
    center = sum((world_matrix @ v.co for v in unique_verts), Vector()) / len(unique_verts)

    # Thực thi
    context.scene.cursor.location = center

    if set_pivot:
        context.scene.tool_settings.transform_pivot_point = 'CURSOR'

    return True

##### || ##### || #####

##### [STATE_MESH] => [STATE_PIVOT_LIST]

def pivot_to_vert_midpoint(context, set_pivot=False):

    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False

    bm = bmesh.from_edit_mesh(obj.data)
    selected_verts = [v for v in bm.verts if v.select]

    if len(selected_verts) == 0:
        return False

    world_matrix = obj.matrix_world

    # centroid
    coords = [world_matrix @ v.co for v in selected_verts]
    midpoint = sum(coords, Vector()) / len(coords)

    # apply
    context.scene.cursor.location = midpoint

    if set_pivot:
        context.scene.tool_settings.transform_pivot_point = 'CURSOR'

    return True

##### || ##### || #####

##### [STATE_MESH] => [STATE_PIVOT_LIST]

def merge_points_at_last(context):
    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False
    
    bm = bmesh.from_edit_mesh(obj.data)

    # 1. Xác định Active vertex
    active_vert = bm.select_history.active

    if not isinstance(active_vert, bmesh.types.BMVert):
        selected = [v for v in bm.verts if v.select]
        if len(selected) < 2:
            return False
        active_vert = selected[-1]

    # 2. Gom danh sách đỉnh
    verts_to_merge = [v for v in bm.verts if v.select and v != active_vert]

    if not verts_to_merge:
        return False

    # 3. Thực hiện Merge tại tọa độ điểm Active
    bmesh.ops.pointmerge(
        bm,
        verts=verts_to_merge + [active_vert],
        merge_co=active_vert.co
    )

    # --- BỔ SUNG ĐỂ HOÀN THIỆN ---
    bm.verts.ensure_lookup_table()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces) # Giúp model AI mượt hơn
    # -----------------------------

    # 4. Cập nhật dữ liệu vào Mesh
    bmesh.update_edit_mesh(obj.data)

    return True

##### || ##### || #####

##### [STATE_MESH] => [STATE_SPIN_LIST]

def spin_mesh(context, axis_name, steps, angle=90):
    """
    Hàm tổng quát để gọi từ Operators.
    axis_name: 'X', 'Y', hoặc 'Z'
    steps: 2, 3, 4, 5, 6
    """
    axis_map = {
        'X':  (1, 0, 0),
        '-X': (-1, 0, 0),
        'Y':  (0, 1, 0),
        '-Y': (0, -1, 0),
        'Z':  (0, 0, 1),
        '-Z': (0, 0, -1)
    }
    
    if axis_name not in axis_map:
        return False
        
    return _execute_spin(context, axis=axis_map[axis_name], steps=steps, angle=angle, axis_label=axis_name)

def _execute_spin(context, axis, steps, angle, axis_label):

    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False

    if steps < 1:
        return False

    bm = bmesh.from_edit_mesh(obj.data)

    # check selection
    if not any(e.select for e in bm.edges):
        return False

    try:
        # Trong Blender mới, bạn không cần use_duplicate=False nữa 
        # vì đó là hành vi mặc định (duplicating tắt).
        bpy.ops.mesh.spin(
            steps=steps,
            angle=math.radians(angle),
            axis=axis,
            center=context.scene.cursor.location
            # Xóa dòng use_duplicate=False ở đây
        )

        
        return True
    except Exception as e:
        print(f"Spin Error: {e}")
        return False

    return True

def connect_face_centers(context):
    if context.mode != 'EDIT_MESH':
        return False

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        return False

    bm = bmesh.from_edit_mesh(obj.data)

    selected_faces = [f for f in bm.faces if f.select]
    if len(selected_faces) < 2:
        return False

    # 1. Xác định Active/Other
    active = bm.select_history.active
    if not isinstance(active, bmesh.types.BMFace) or active not in selected_faces:
        active = selected_faces[-1]

    try:
        other = next(f for f in selected_faces if f != active)
    except StopIteration:
        return False

    # 2. Tính toán Center (Chỉ cần World Space khi so sánh hoặc nối xuyên Object)
    c1 = active.calc_center_median()
    c2 = other.calc_center_median()

    # Kiểm tra khoảng cách dựa trên World Space để chính xác tuyệt đối về tỉ lệ (Scale)
    c1_world = obj.matrix_world @ c1
    c2_world = obj.matrix_world @ c2

    if (c1_world - c2_world).length < 1e-4:
        return False

    # 3. Tạo Geometry (Dùng tọa độ Local)
    v1 = bm.verts.new(c1)
    v2 = bm.verts.new(c2)
    
    # Cập nhật Index ngay để tránh lỗi truy xuất
    bm.verts.index_update()
    
    try:
        new_edge = bm.edges.new((v1, v2))
    except ValueError: # Đề phòng cạnh đã tồn tại
        return False

    # 4. Highlight & Cleanup
    # Nếu mesh nặng, hãy thay 3 vòng for này bằng bpy.ops.mesh.select_all(action='DESELECT')
    for v in bm.verts: v.select = False
    for e in bm.edges: e.select = False
    for f in bm.faces: f.select = False

    v1.select = True
    v2.select = True
    new_edge.select = True

    bm.select_history.clear()
    bm.select_history.add(v2)

    # 5. Đẩy dữ liệu về Mesh
    bmesh.update_edit_mesh(obj.data)
    context.area.tag_redraw() # Quan trọng để thấy kết quả ngay

    return True

import bpy
import bmesh
import math
from mathutils import Vector, Matrix

def create_plane_at_vertex(context, size=0.01, offset=0.0005):
    obj = context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return False

    bm = bmesh.from_edit_mesh(obj.data)
    bm.normal_update()

    # --- Active vertex ---
    active_vert = bm.select_history.active
    if not isinstance(active_vert, bmesh.types.BMVert):
        selected = [v for v in bm.verts if v.select]
        if not selected:
            return False
        active_vert = selected[-1]

    # Vẫn dùng Normal gốc để đẩy mặt phẳng ra ngoài (tránh z-fighting)
    normal = active_vert.normal
    center = active_vert.co + normal * offset

    # --- THAY ĐỔI TẠI ĐÂY: Khóa xoay hoàn toàn theo World ---
    # Thay vì tính theo horizontal_normal, ta dùng ma trận xoay cố định.
    # Matrix.Rotation(math.radians(90), 3, 'X') giúp mặt phẳng dựng đứng lên,
    # mặt phẳng sẽ luôn "nhìn" về hướng trục Y của World (Z rotate = 0).
    rot_matrix = Matrix.Rotation(math.radians(90), 3, 'X')

    half = size / 2
    coords = [
        Vector((-half, -half, 0)),
        Vector(( half, -half, 0)),
        Vector(( half,  half, 0)),
        Vector((-half,  half, 0)),
    ]

    # Tạo verts mới dựa trên ma trận xoay cố định + vị trí tâm
    new_verts = [bm.verts.new(rot_matrix @ co + center) for co in coords]

    bm.verts.ensure_lookup_table()

    try:
        new_face = bm.faces.new(new_verts)

        # Cập nhật Normal cho riêng mặt này để tránh màu đen
        new_face.normal_update()

        # Deselect nhanh bằng Ops (tiện dùng trong View3D)
        bpy.ops.mesh.select_all(action='DESELECT')

        # Select mặt mới tạo
        new_face.select = True
        for v in new_face.verts:
            v.select = True

        bm.select_history.clear()
        bm.select_history.add(new_face)

    except ValueError:
        return False

    # Cập nhật Normal cho toàn bộ mesh trước khi ghi đè dữ liệu
    bm.normal_update()
    bmesh.update_edit_mesh(obj.data)

    return True