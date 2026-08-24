import bpy
import math
import random
import bmesh
import mathutils  # THÊM DÒNG NÀY VÀO ĐÂY
from mathutils import Vector, Quaternion, Matrix, noise
from mathutils.bvhtree import BVHTree

# def generate_stylized_pavement(
#         self,
#         context,
#         area_size=5.0,
#         subdivisions=12,
#         gap_size=0.04,
#         thickness=0.15,
#         bevel_h=0.015,
#         bevel_v=0.04,
#         random_seed=0
# ):
#     bevel_width=0.03
#     mesh = bpy.data.meshes.new("Stylized_Pavement")
#     obj = bpy.data.objects.new("Pavement_Courtyard", mesh)
#     context.collection.objects.link(obj)
#
#     bm = bmesh.new()
#
#     # 1. Tạo mặt phẳng lưới (Grid)
#     bmesh.ops.create_grid(bm, x_segments=subdivisions, y_segments=subdivisions, size=area_size/2)
#
#     # 2. Jitter - Làm nhiễu các đỉnh để tạo hình dáng đá tự nhiên
#     max_jitter = (area_size / subdivisions) * 0.4
#     for v in bm.verts:
#         if not v.is_boundary:  # Giữ cho viền ngoài cùng vuông vức
#             v.co.x += random.uniform(-max_jitter, max_jitter)
#             v.co.y += random.uniform(-max_jitter, max_jitter)
#
#     # 3. Tách toàn bộ các mặt thành các đa giác độc lập
#     bmesh.ops.split_edges(bm, edges=bm.edges)
#
#     # 4. Thu nhỏ từng mặt để tạo khe hở
#     for f in bm.faces:
#         center = f.calc_center_median()
#         for v in f.verts:
#             direction = v.co - center
#             dist = direction.length
#             # Chỉ thu nhỏ nếu khoảng cách từ tâm đến đỉnh lớn hơn khe hở
#             if dist > gap_size:
#                 v.co = center + direction.normalized() * (dist - gap_size)
#
#     # Cập nhật và xuất lưới
#     bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
#     bm.to_mesh(mesh)
#     bm.free()
#
#     # 5. Thêm Modifiers để hoàn thiện hình dáng Stylized
#     sol_mod = obj.modifiers.new(name="Thick", type='SOLIDIFY')
#     sol_mod.thickness = thickness
#     sol_mod.offset = 0.0  # Nở đều ra 2 bên mặt phẳng
#
#     bev_mod = obj.modifiers.new(name="Round_Edges", type='BEVEL')
#     bev_mod.width = bevel_width
#     bev_mod.segments = 3
#     bev_mod.limit_method = 'ANGLE'
#     bev_mod.angle_limit = math.radians(30)
#
#     sub_mod = obj.modifiers.new(name="Smooth_Stone", type='SUBSURF')
#     sub_mod.levels = 2
#
#     # Shade Smooth
#     if hasattr(obj.data, "polygons"):
#         obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))
#
#     return obj


def generate_stylized_pavement(
        self,
        context,
        area_size=5.0,
        subdivisions=12,
        gap_size=0.04,
        thickness=0.15,
        bevel_h=0.015,
        bevel_v=0.04,
        random_seed=0
):
    # Cố định tính ngẫu nhiên
    random.seed(random_seed)

    mesh = bpy.data.meshes.new("Stylized_Pavement")
    obj = bpy.data.objects.new("Pavement_Courtyard", mesh)
    context.collection.objects.link(obj)

    bm = bmesh.new()

    # ========================================================
    # 1. CẮT LƯỚI BẢN CŨ CỦA BẠN (Grid -> Jitter -> Shrink)
    # ========================================================
    bmesh.ops.create_grid(bm, x_segments=subdivisions, y_segments=subdivisions, size=area_size/2)

    max_jitter = (area_size / subdivisions) * 0.4
    for v in bm.verts:
        if not v.is_boundary:
            v.co.x += random.uniform(-max_jitter, max_jitter)
            v.co.y += random.uniform(-max_jitter, max_jitter)

    bmesh.ops.split_edges(bm, edges=bm.edges)

    for f in bm.faces:
        center = f.calc_center_median()
        for v in f.verts:
            direction = v.co - center
            dist = direction.length
            if dist > gap_size:
                v.co = center + direction.normalized() * (dist - gap_size)

    # ========================================================
    # 2. TẠO KHỐI & GÁN TRỌNG SỐ CHO CẠNH DỌC
    # ========================================================
    bw_layer = bm.edges.layers.float.get('bevel_weight_edge')
    if bw_layer is None:
        bw_layer = bm.edges.layers.float.new('bevel_weight_edge')

    # Lưu lại mặt đáy
    bottom_faces_verts = [[v for v in f.verts] for f in bm.faces]

    # Dựng độ dày (Z)
    res = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in res['geom'] if isinstance(elem, bmesh.types.BMVert)]
    for v in extruded_verts:
        v.co.z += thickness

    # Đánh dấu cạnh dọc (Weight = 1.0) để lát gọt góc
    extruded_edges = [elem for elem in res['geom'] if isinstance(elem, bmesh.types.BMEdge)]
    for e in extruded_edges:
        if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.001:
            e[bw_layer] = 1.0
        else:
            e[bw_layer] = 0.0

            # Vá mặt đáy để thành khối hộp đặc ruột
    for verts in bottom_faces_verts:
        try:
            bm.faces.new(reversed(verts))
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # ========================================================
    # 3. MODIFIERS (TẠO LƯỚI Y HỆT ẢNH BẠN GỬI)
    # ========================================================
    # Áp dụng quy tắc của bạn: Chỉ số càng lớn -> Số lưới càng tăng
    # Hệ số (100 và 150) được tinh chỉnh để tạo ra lưới Low-poly y hệt ảnh.
    # Ví dụ: bevel_v = 0.04 -> tạo 4 segments dọc
    #        bevel_h = 0.015 -> tạo 2 segments ngang
    segments_v = max(2, int(bevel_v * 100))
    segments_h = max(2, int(bevel_h * 150))

    # BƯỚC 1: Bo các góc đứng trước
    bev_v_mod = obj.modifiers.new(name="Bevel_Vertical", type='BEVEL')
    bev_v_mod.limit_method = 'WEIGHT'
    bev_v_mod.width = bevel_v
    bev_v_mod.segments = segments_v
    bev_v_mod.use_clamp_overlap = True # Giữ an toàn không cho lưới chéo nhau

    # BƯỚC 2: Bo mặt trên/đáy chạy đè ngang qua góc đã bo
    bev_h_mod = obj.modifiers.new(name="Bevel_Horizontal", type='BEVEL')
    bev_h_mod.limit_method = 'ANGLE'
    bev_h_mod.angle_limit = math.radians(45)
    bev_h_mod.width = bevel_h
    bev_h_mod.segments = segments_h
    bev_h_mod.use_clamp_overlap = True

    # Làm mượt bề mặt
    if hasattr(obj.data, "polygons"):
        obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))

    return obj

def generate_stylized_pavement_theo_hinh_dang_yeu_cau(
        self,
        context,
        target_obj,      # [MỚI] Yêu cầu truyền tấm plane hình chữ U (khuôn) vào đây
        area_size=5.0,
        subdivisions=12,
        gap_size=0.04,
        thickness=0.15,
        bevel_h=0.015,
        bevel_v=0.04,
        random_seed=0
):
    # Cố định tính ngẫu nhiên
    random.seed(random_seed)

    if not target_obj or target_obj.type != 'MESH':
        self.report({'WARNING'}, "Cần chọn một mặt phẳng (Mesh) làm khuôn.")
        return None

    mesh = bpy.data.meshes.new(target_obj.name + "_Stones")
    obj = bpy.data.objects.new(target_obj.name + "_Stones", mesh)
    context.collection.objects.link(obj)

    # Đưa tọa độ của sân đá khớp 100% với tọa độ của tấm plane khuôn
    obj.matrix_world = target_obj.matrix_world.copy()

    bm = bmesh.new()

    # ========================================================
    # 1. TẠO LƯỚI THEO CÁCH CỦA BẠN (NHƯNG BAO TRÙM LÊN KHUÔN)
    # ========================================================
    # Tính toán độ lớn của khuôn để tạo Grid khổng lồ bao trùm vừa đủ
    depsgraph = context.evaluated_depsgraph_get()
    target_eval = target_obj.evaluated_get(depsgraph)
    bbox = [mathutils.Vector(v) for v in target_eval.bound_box]

    min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
    min_y, max_y = min(v.y for v in bbox), max(v.y for v in bbox)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    size_x = max_x - min_x
    size_y = max_y - min_y
    grid_size = max(size_x, size_y) + 1.0 # Cộng 1m viền an toàn

    # Tính toán phân chia lưới để kích thước 1 viên đá luôn không đổi
    stone_size = area_size / max(1, subdivisions)
    actual_subs = max(2, int(grid_size / stone_size))

    # Chạy lệnh tạo Grid CỦA BẠN
    bmesh.ops.create_grid(bm, x_segments=actual_subs, y_segments=actual_subs, size=grid_size/2)

    # Dịch tâm cái Grid khổng lồ về đúng chính giữa cái khuôn
    for v in bm.verts:
        v.co.x += center_x
        v.co.y += center_y

    # JITTER - Làm nhiễu CỦA BẠN
    max_jitter = stone_size * 0.4
    for v in bm.verts:
        if not v.is_boundary:
            v.co.x += random.uniform(-max_jitter, max_jitter)
            v.co.y += random.uniform(-max_jitter, max_jitter)

    # ========================================================
    # 2. KHUÔN DẬP (COOKIE CUTTER) - XOÁ ĐÁ NGOÀI ĐƯỜNG
    # ========================================================
    bvh = mathutils.bvhtree.BVHTree.FromObject(target_obj, depsgraph)
    faces_to_delete = []

    for f in bm.faces:
        center = f.calc_center_median()
        # Bắn tia từ độ cao 100m giáng thẳng xuống tâm viên đá
        hit, _, _, _ = bvh.ray_cast(center + mathutils.Vector((0, 0, 100)), mathutils.Vector((0, 0, -1)))

        # Nếu tia trượt (tâm viên đá không nằm trên khuôn plane) -> Băm!
        if hit is None:
            faces_to_delete.append(f)

    # Xoá tất cả những mặt dư thừa, chỉ giữ lại đá nằm trên khuôn chữ U
    bmesh.ops.delete(bm, geom=faces_to_delete, context='FACES')

    # ========================================================
    # 3. TÁCH & THU NHỎ CỦA BẠN (Split -> Shrink)
    # ========================================================
    bmesh.ops.split_edges(bm, edges=bm.edges)

    for f in bm.faces:
        center = f.calc_center_median()
        for v in f.verts:
            direction = v.co - center
            dist = direction.length
            if dist > gap_size:
                v.co = center + direction.normalized() * (dist - gap_size)

    # ========================================================
    # 4. TẠO KHỐI & GÁN TRỌNG SỐ CHO CẠNH DỌC
    # ========================================================
    bw_layer = bm.edges.layers.float.get('bevel_weight_edge')
    if bw_layer is None:
        bw_layer = bm.edges.layers.float.new('bevel_weight_edge')

    bottom_faces_verts = [[v for v in f.verts] for f in bm.faces]

    res = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    extruded_verts = [elem for elem in res['geom'] if isinstance(elem, bmesh.types.BMVert)]
    for v in extruded_verts:
        v.co.z += thickness

    extruded_edges = [elem for elem in res['geom'] if isinstance(elem, bmesh.types.BMEdge)]
    for e in extruded_edges:
        if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.001:
            e[bw_layer] = 1.0
        else:
            e[bw_layer] = 0.0

    # Vá mặt đáy
    for verts in bottom_faces_verts:
        try:
            bm.faces.new(reversed(verts))
        except ValueError:
            pass

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()

    # ========================================================
    # 5. MODIFIERS (TẠO LƯỚI Y HỆT ẢNH BẠN GỬI)
    # ========================================================
    segments_v = max(2, int(bevel_v * 100))
    segments_h = max(2, int(bevel_h * 150))

    bev_v_mod = obj.modifiers.new(name="Bevel_Vertical", type='BEVEL')
    bev_v_mod.limit_method = 'WEIGHT'
    bev_v_mod.width = bevel_v
    bev_v_mod.segments = segments_v
    bev_v_mod.use_clamp_overlap = True

    bev_h_mod = obj.modifiers.new(name="Bevel_Horizontal", type='BEVEL')
    bev_h_mod.limit_method = 'ANGLE'
    bev_h_mod.angle_limit = math.radians(45)
    bev_h_mod.width = bevel_h
    bev_h_mod.segments = segments_h
    bev_h_mod.use_clamp_overlap = True

    if hasattr(obj.data, "polygons"):
        obj.data.polygons.foreach_set('use_smooth', [True] * len(obj.data.polygons))

    return obj


def generate_island_blockout():
    coll_name = "Island_Blockout_Spaced"
    if coll_name in bpy.data.collections:
        coll = bpy.data.collections[coll_name]
    else:
        coll = bpy.data.collections.new(coll_name)
        bpy.context.scene.collection.children.link(coll)

    mesh = bpy.data.meshes.new("BoundBox_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(mesh)
    bm.free()

    # ÁNH XẠ TOẠ ĐỘ TỪ ẢNH RA KHÔNG GIAN 40x40m
    # Tâm (0,0) là đài phun nước. Các trục kéo dài từ -20m đến 20m
    objects_data = [
        # --- HẠ TẦNG CƠ BẢN ---
        {"name": "01_Island_Ground",   "size": (40, 40, 4),    "loc": (0, 0, -2.1)},
        {"name": "02_Central_Plaza",   "size": (14, 14, 0.2),  "loc": (0, 0, 0)},
        {"name": "03_Fountain",        "size": (4, 4, 3),      "loc": (0, 0, 1.5)},

        # --- KIẾN TRÚC CHÍNH (Đã đẩy dãn ra xa tâm) ---
        # Quán Cà Phê (Góc trái phía sau - Đẩy xa ra rìa)
        {"name": "10_Cafe_Shop",       "size": (6.5, 5.5, 6),  "loc": (-10, 8, 3.1)},

        # Xưởng Gốm (Góc trái phía trước)
        {"name": "12_Pottery_Shop",    "size": (5.5, 6.5, 6),  "loc": (-12, -7, 3.1)},

        # Hiệu Sách (Góc phải phía sau)
        {"name": "11_Book_Store",      "size": (5.5, 6.5, 6),  "loc": (8, 12, 3.1)},

        # Ngôi nhà mái hồng (Góc xa bên phải)
        {"name": "13_Pink_House",      "size": (5.5, 5.5, 5.5),"loc": (15, 2, 2.85)},

        # --- KIẾN TRÚC CAO TẦNG ---
        # Tháp Đồng Hồ (Giữa phía sau - Lùi sâu sát mép)
        {"name": "14_Clock_Tower",     "size": (2.5, 2.5, 9),  "loc": (-3, 16, 4.5)},

        # Cối Xay Gió (Có đồi cao góc trên bên phải)
        {"name": "15_Windmill_Hill",   "size": (7, 7, 2),      "loc": (14, 16, 1)},
        {"name": "15_Windmill",        "size": (3.5, 3.5, 8),  "loc": (14, 16, 6)},

        # --- KHU VỰC HỒ NƯỚC & CẦU ---
        {"name": "04_Pond",            "size": (8, 5, 0.2),    "loc": (12, -10, -0.1)},
        {"name": "05_Bridge",          "size": (5, 2.5, 1.5),  "loc": (9, -8, 0.75)},

        # --- ĐẠO CỤ & QUẦY HÀNG (Tiền cảnh) ---
        {"name": "20_Signboard",       "size": (3, 0.5, 2),    "loc": (4, -16, 1)},
        {"name": "21_Fruit_Stall",     "size": (2.5, 3.5, 2.5),"loc": (-6, -14, 1.25)},
        {"name": "22_Blue_Stall",      "size": (3, 2.5, 2.5),  "loc": (-1, -11, 1.25)}
    ]

    for data in objects_data:
        obj = bpy.data.objects.new(data["name"], mesh)
        obj.location = data["loc"]
        obj.scale = data["size"]

        obj.display_type = 'BOUNDS'
        obj.show_bounds = True

        coll.objects.link(obj)

    # THIẾT LẬP CAMERA ISOMETRIC CHUẨN
    cam_data = bpy.data.cameras.new("Iso_Camera")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = 45 # Scale 45m để bao trọn góc nhìn 40x40m

    cam_obj = bpy.data.objects.new("Camera_Isometric_View", cam_data)
    cam_obj.location = (40, -40, 40)
    cam_obj.rotation_euler = (math.radians(54.736), 0, math.radians(45))
    coll.objects.link(cam_obj)

    bpy.context.scene.camera = cam_obj
    print("Đã tạo xong Blockout Đảo phiên bản rộng rãi!")

def generate_chunky_stylized_rock(
        self,
        context,
        rock_size=1.0,
        num_faces=25,          # CHÌA KHÓA Ở ĐÂY: Số lượng mặt mục tiêu (Càng thấp mảng càng to)
        deform_strength=0.35,  # Độ lồi lõm của các khối
        elongation=0.3,        # Kéo giãn đá
        random_seed=0
):
    random.seed(random_seed)

    mesh = bpy.data.meshes.new(f"Rock_Faceted_{random_seed}")
    obj = bpy.data.objects.new(f"Rock_Faceted_{random_seed}", mesh)
    context.collection.objects.link(obj)

    bm = bmesh.new()

    # 1. TẠO PHÔI: Icosphere cấp 3 (320 mặt) - Đủ lưới để làm méo mịn màng
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=rock_size)

    # 2. LÀM MÉO KHỐI TỔNG THỂ (Dùng Noise mảng lớn để không sinh gai nhọn)
    noise_offset = mathutils.Vector((
        random.uniform(-100, 100),
        random.uniform(-100, 100),
        random.uniform(-100, 100)
    ))

    for v in bm.verts:
        # Scale = 1.2 để bước sóng nhiễu rất to
        sample_point = (v.co * 1.2) + noise_offset
        n_val = mathutils.noise.noise(sample_point)
        # Đẩy lồi/lõm dọc theo hướng của đỉnh
        v.co += v.normal * (n_val * deform_strength * rock_size)

    # Kéo giãn để đá không bị tròn đều (Thường dẹt nhẹ ở trục Z trông sẽ tự nhiên hơn)
    scale_vec = (
        random.uniform(1.0 - elongation, 1.0 + elongation),
        random.uniform(1.0 - elongation, 1.0 + elongation),
        random.uniform(1.0 - elongation, 1.0) # Ép nhẹ trục Z
    )
    bmesh.ops.scale(bm, vec=scale_vec, verts=bm.verts)

    bm.to_mesh(mesh)
    bm.free()

    # 3. ÉP LOW-POLY ĐỂ TẠO MẢNG CẮT (FACETS) LỚN
    decimate = obj.modifiers.new(name="Create_Facets", type='DECIMATE')
    decimate.decimate_type = 'COLLAPSE'
    # Tính toán để nó nén đúng về số lượng mặt mục tiêu (VD: 25 mặt)
    ratio = max(0.02, min(1.0, num_faces / 320.0))
    decimate.ratio = ratio

    # 4. GỌT TÙ CÁC MÉP BÉN (Chamfer Edge)
    # Đây là bước chặn các góc nhọn, tạo mép chuyển mượt mà bắt sáng tốt
    bevel = obj.modifiers.new(name="Soften_Edges", type='BEVEL')
    bevel.limit_method = 'ANGLE'
    bevel.angle_limit = math.radians(20)  # Bắt các cạnh gập trên 20 độ
    bevel.width = rock_size * 0.06        # Độ vát mép vừa đủ không làm mất khối
    bevel.segments = 2
    bevel.use_clamp_overlap = True

    # Bật Flat Shading để tôn vinh các mảng miếng
    for p in mesh.polygons:
        p.use_smooth = False

    return obj
