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
    random.seed()

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
    random.seed()

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
    random.seed()

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



def generate_procedural_stone_wall(
        self,
        context,
        target_curve,          # Đối tượng Curve làm đường dẫn
        num_layers=3,          # Số lớp đá ngang (như hình của bạn là 3)
        layer_height=0.4,      # Chiều cao mỗi lớp
        wall_thickness=0.3,    # Bề dày của bức tường
        min_width=0.4,         # Chiều dài NGẮN NHẤT của 1 viên đá
        max_width=1.0,         # Chiều dài DÀI NHẤT của 1 viên đá
        gap_size=0.03,         # Khe hở vữa giữa các viên
        random_seed=0
):
    if not target_curve or target_curve.type != 'CURVE':
        self.report({'WARNING'}, "Vui lòng chọn một đường Curve làm khuôn dẫn!")
        return None

    random.seed()

    # 1. TÍNH CHIỀU DÀI TỔNG THỂ CỦA ĐƯỜNG CURVE
    try:
        total_length = sum(s.calc_length() for s in target_curve.data.splines)
    except AttributeError:
        # Fallback cho các bản Blender rất cũ
        total_length = 10.0

        # 2. THUẬT TOÁN TÍNH TOÁN VỊ TRÍ CẮT SO LE NGẪU NHIÊN
    layer_cuts = []
    min_stagger = min_width * 0.35 # Mạch cắt phải lệch nhau ít nhất 35% so với viên nhỏ nhất

    for i in range(num_layers):
        cuts = []
        current_x = 0.0

        while current_x < total_length:
            # Random chiều dài viên đá
            stone_len = random.uniform(min_width, max_width)
            proposed_cut = current_x + stone_len

            if proposed_cut >= total_length:
                proposed_cut = total_length

            # Ép So Le: Kiểm tra với lớp ngay bên dưới (i-1)
            if i > 0 and proposed_cut < total_length:
                prev_cuts = layer_cuts[i-1]
                # Tìm mạch cắt gần nhất ở lớp dưới
                closest_cut = min(prev_cuts, key=lambda x: abs(x - proposed_cut))
                distance = abs(closest_cut - proposed_cut)

                # Nếu mạch cắt trùng nhau hoặc quá gần -> Ép viên đá dài thêm ra để lệch đi
                if distance < min_stagger:
                    proposed_cut = closest_cut + min_stagger
                    if proposed_cut >= total_length:
                        proposed_cut = total_length

            cuts.append(proposed_cut)
            current_x = proposed_cut

        layer_cuts.append(cuts)

    # 3. DỰNG LƯỚI BỨC TƯỜNG (Dựng thẳng tắp dọc theo trục X)
    mesh = bpy.data.meshes.new(target_curve.name + "_Wall")
    obj = bpy.data.objects.new(target_curve.name + "_Wall", mesh)
    context.collection.objects.link(obj)

    # Khớp toạ độ khối đá vào toạ độ của đường Curve
    obj.matrix_world = target_curve.matrix_world.copy()

    bm = bmesh.new()

    for i, cuts in enumerate(layer_cuts):
        z_start = i * layer_height
        z_end = (i + 1) * layer_height
        start_x = 0.0

        for end_x in cuts:
            # Tạo 8 đỉnh cho mỗi viên đá (Có trừ hao Gap Size)
            x0 = start_x + (gap_size / 2)
            x1 = end_x - (gap_size / 2)
            y0 = -(wall_thickness / 2) + (gap_size / 2)
            y1 = (wall_thickness / 2) - (gap_size / 2)
            z0 = z_start + (gap_size / 2)
            z1 = z_end - (gap_size / 2)

            # Bỏ qua nếu viên đá quá nhỏ do lỗi nén mảng
            if x1 <= x0:
                start_x = end_x
                continue

            verts = [
                bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
                bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
                bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
                bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1))
            ]

            bm.faces.new((verts[0], verts[3], verts[2], verts[1])) # Đáy
            bm.faces.new((verts[4], verts[5], verts[6], verts[7])) # Đỉnh
            bm.faces.new((verts[0], verts[1], verts[5], verts[4])) # Mặt trước
            bm.faces.new((verts[2], verts[3], verts[7], verts[6])) # Mặt sau
            bm.faces.new((verts[1], verts[2], verts[6], verts[5])) # Cạnh phải
            bm.faces.new((verts[3], verts[0], verts[4], verts[7])) # Cạnh trái

            start_x = end_x

    bm.to_mesh(mesh)
    bm.free()

    # 4. GẮN MODIFIERS ĐỂ UỐN CONG VÀ LÀM ĐẸP
    # Cắt lưới dọc (Simple Subsurf) để đá đủ mềm dẻo khi bẻ cong ở góc chữ L
    subsurf = obj.modifiers.new(name="Bending_Resolution", type='SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 3

    # Uốn cong tường theo đường dẫn Curve của bạn
    curve_mod = obj.modifiers.new(name="Bend_Along_Path", type='CURVE')
    curve_mod.object = target_curve
    curve_mod.deform_axis = 'POS_X'

    # Bo góc Stylized
    bevel = obj.modifiers.new(name="Stylized_Bevel", type='BEVEL')
    bevel.width = 0.04
    bevel.segments = 2
    bevel.use_clamp_overlap = True

    return obj


def generate_procedural_stone_wall_v2(
        self,
        context,
        target_curve,          # Đối tượng Curve làm đường dẫn
        num_layers=3,          # Số lớp đá ngang (như hình của bạn là 3)
        layer_height=0.4,      # Chiều cao mỗi lớp
        wall_thickness=0.3,    # Bề dày của bức tường
        min_width=0.4,         # Chiều dài NGẮN NHẤT của 1 viên đá
        max_width=1.0,         # Chiều dài DÀI NHẤT của 1 viên đá
        gap_size=0.03,         # Khe hở vữa giữa các viên
        alignment='CENTER',    # [MỚI] Căn lề: 'CENTER' (Giữa), 'LEFT' (Trái), 'RIGHT' (Phải)
        random_seed=0
):
    if not target_curve or target_curve.type != 'CURVE':
        self.report({'WARNING'}, "Vui lòng chọn một đường Curve làm khuôn dẫn!")
        return None

    random.seed()

    # 1. TÍNH CHIỀU DÀI TỔNG THỂ CỦA ĐƯỜNG CURVE
    try:
        total_length = sum(s.calc_length() for s in target_curve.data.splines)
    except AttributeError:
        # Fallback cho các bản Blender rất cũ
        total_length = 10.0

    # 2. THUẬT TOÁN TÍNH TOÁN VỊ TRÍ CẮT SO LE NGẪU NHIÊN
    layer_cuts = []
    min_stagger = min_width * 0.35 # Mạch cắt phải lệch nhau ít nhất 35% so với viên nhỏ nhất

    for i in range(num_layers):
        cuts = []
        current_x = 0.0

        while current_x < total_length:
            # Random chiều dài viên đá
            stone_len = random.uniform(min_width, max_width)
            proposed_cut = current_x + stone_len

            if proposed_cut >= total_length:
                proposed_cut = total_length

            # Ép So Le: Kiểm tra với lớp ngay bên dưới (i-1)
            if i > 0 and proposed_cut < total_length:
                prev_cuts = layer_cuts[i-1]
                # Tìm mạch cắt gần nhất ở lớp dưới
                closest_cut = min(prev_cuts, key=lambda x: abs(x - proposed_cut))
                distance = abs(closest_cut - proposed_cut)

                # Nếu mạch cắt trùng nhau hoặc quá gần -> Ép viên đá dài thêm ra để lệch đi
                if distance < min_stagger:
                    proposed_cut = closest_cut + min_stagger
                    if proposed_cut >= total_length:
                        proposed_cut = total_length

            cuts.append(proposed_cut)
            current_x = proposed_cut

        layer_cuts.append(cuts)

    # 3. DỰNG LƯỚI BỨC TƯỜNG (Dựng thẳng tắp dọc theo trục X)
    mesh = bpy.data.meshes.new(target_curve.name + "_Wall")
    obj = bpy.data.objects.new(target_curve.name + "_Wall", mesh)
    context.collection.objects.link(obj)

    # Khớp toạ độ khối đá vào toạ độ của đường Curve
    obj.matrix_world = target_curve.matrix_world.copy()

    bm = bmesh.new()

    for i, cuts in enumerate(layer_cuts):
        z_start = i * layer_height
        z_end = (i + 1) * layer_height
        start_x = 0.0

        for end_x in cuts:
            # Tạo 8 đỉnh cho mỗi viên đá (Có trừ hao Gap Size)
            x0 = start_x + (gap_size / 2)
            x1 = end_x - (gap_size / 2)

            # [THAY ĐỔI NHỎ TẠI ĐÂY] Tính trục Y dựa trên alignment thay vì luôn ở giữa
            if alignment == 'LEFT':
                y0 = 0.0 + (gap_size / 2)
                y1 = wall_thickness - (gap_size / 2)
            elif alignment == 'RIGHT':
                y0 = -wall_thickness + (gap_size / 2)
                y1 = 0.0 - (gap_size / 2)
            else: # Mặc định là CENTER - Trùng khớp 100% với code gốc của bạn
                y0 = -(wall_thickness / 2) + (gap_size / 2)
                y1 = (wall_thickness / 2) - (gap_size / 2)

            z0 = z_start + (gap_size / 2)
            z1 = z_end - (gap_size / 2)

            # Bỏ qua nếu viên đá quá nhỏ do lỗi nén mảng
            if x1 <= x0:
                start_x = end_x
                continue

            verts = [
                bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
                bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
                bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
                bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1))
            ]

            bm.faces.new((verts[0], verts[3], verts[2], verts[1])) # Đáy
            bm.faces.new((verts[4], verts[5], verts[6], verts[7])) # Đỉnh
            bm.faces.new((verts[0], verts[1], verts[5], verts[4])) # Mặt trước
            bm.faces.new((verts[2], verts[3], verts[7], verts[6])) # Mặt sau
            bm.faces.new((verts[1], verts[2], verts[6], verts[5])) # Cạnh phải
            bm.faces.new((verts[3], verts[0], verts[4], verts[7])) # Cạnh trái

            start_x = end_x

    bm.to_mesh(mesh)
    bm.free()

    # 4. GẮN MODIFIERS ĐỂ UỐN CONG VÀ LÀM ĐẸP
    # Cắt lưới dọc (Simple Subsurf) để đá đủ mềm dẻo khi bẻ cong ở góc chữ L
    subsurf = obj.modifiers.new(name="Bending_Resolution", type='SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 3

    # Uốn cong tường theo đường dẫn Curve của bạn
    curve_mod = obj.modifiers.new(name="Bend_Along_Path", type='CURVE')
    curve_mod.object = target_curve
    curve_mod.deform_axis = 'POS_X'

    # Bo góc Stylized
    bevel = obj.modifiers.new(name="Stylized_Bevel", type='BEVEL')
    bevel.width = 0.04
    bevel.segments = 2
    bevel.use_clamp_overlap = True

    return obj



def apply_stone_surface_damage(
        self,
        context,
        inset_thickness=0.02,
        noise_strength=0.04,   # Có thể tăng nhẹ thông số này lên vì sóng nhiễu rất mượt
        noise_scale=2.5,       # [MỚI] Bước sóng: Càng nhỏ thì sóng lượn càng to (càng mềm mại)
        random_seed=0
):
    random.seed()

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        self.report({'WARNING'}, "Vui lòng chuyển sang Edit Mode và chọn các mặt cần làm móp!")
        return {'CANCELLED'}

    bm = bmesh.from_edit_mesh(obj.data)

    # 1. LẤY MẶT CHỌN BAN ĐẦU
    initial_faces = [f for f in bm.faces if f.select]
    if not initial_faces:
        self.report({'WARNING'}, "Vui lòng bôi đen (select) các mặt phẳng cần làm gồ ghề!")
        return {'CANCELLED'}

    # Tính hướng Pháp tuyến trung bình
    avg_normal = mathutils.Vector((0, 0, 0))
    for f in initial_faces:
        avg_normal += f.normal
    if avg_normal.length > 0:
        avg_normal.normalize()

    for f in bm.faces:
        f.select = False

    # 2. INSET BỀ MẶT (Viền an toàn)
    bmesh.ops.inset_region(
        bm,
        faces=initial_faces,
        thickness=inset_thickness,
        use_even_offset=True
    )

    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # 3. LỌC LẤY CHÍNH XÁC VÙNG LÕI
    inner_faces = [f for f in initial_faces if f.is_valid]
    if not inner_faces:
        return {'FINISHED'}

    # 4. CHỌN ĐỈNH AN TOÀN TRONG LÕI
    inner_edges = set()
    for f in inner_faces:
        for e in f.edges:
            inner_edges.add(e)

    boundary_verts = set()
    for e in inner_edges:
        linked_inner = [f for f in e.link_faces if f in inner_faces]
        if len(linked_inner) == 1:
            boundary_verts.add(e.verts[0])
            boundary_verts.add(e.verts[1])

    all_inner_verts = set()
    for f in inner_faces:
        for v in f.verts:
            all_inner_verts.add(v)

    safe_internal_verts = all_inner_verts - boundary_verts

    # 5. CẮT TAM GIÁC (Triangulate để bề mặt biến dạng mượt hơn)
    bmesh.ops.triangulate(bm, faces=inner_faces)

    # ========================================================
    # 6. ĐẬP MÓP BẰNG NHIỄU KHÔNG GIAN (SMOOTH NOISE)
    # ========================================================
    # Sinh một offset ngẫu nhiên cho thuật toán Noise để mỗi viên đá móp một kiểu
    noise_offset = mathutils.Vector((
        random.uniform(-100, 100),
        random.uniform(-100, 100),
        random.uniform(-100, 100)
    ))

    for v in safe_internal_verts:
        if v.is_valid:
            # Tính toán vị trí đỉnh trong không gian 3D
            # Chuyển đổi toạ độ Local của đỉnh sang toạ độ World (nếu cần thiết để móp đồng bộ toàn tường)
            world_co = obj.matrix_world @ v.co

            # Tính mẫu nhiễu (Dùng toạ độ thế giới + tỷ lệ phóng to)
            sample_point = (world_co * noise_scale) + noise_offset

            # mathutils.noise.noise trả về giá trị lượn sóng mềm mại từ -1.0 đến 1.0
            n_val = mathutils.noise.noise(sample_point)

            # Ép phần lớn giá trị về ÂM để mặt đá chủ yếu bị LÚN vào trong, thỉnh thoảng mới hơi lồi lên
            # n_val (từ -1 đến 1) -> n_val - 0.5 (từ -1.5 đến 0.5)
            biased_val = n_val - 0.5

            # Dịch chuyển đỉnh theo hướng Pháp tuyến
            v.co += avg_normal * (biased_val * noise_strength)

    # Cập nhật Viewport
    bmesh.update_edit_mesh(obj.data)

    return {'FINISHED'}

def apply_stone_surface_damage_upgrade(
        self,
        context,
        inset_thickness=0.02,
        noise_strength=0.04,
        noise_scale=2.5,
):
    random.seed()

    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        self.report({'WARNING'}, "Vui lòng chuyển sang Edit Mode và chọn các mặt cần làm móp!")
        return {'CANCELLED'}

    bm = bmesh.from_edit_mesh(obj.data)

    # ========================================================
    # 1. LẤY MẶT CHỌN VÀ CHIA THÀNH TỪNG CỤM ĐÁ (ISLANDS)
    # ========================================================
    selected_faces = set(f for f in bm.faces if f.select)
    if not selected_faces:
        self.report({'WARNING'}, "Vui lòng bôi đen (select) các mặt phẳng cần làm gồ ghề!")
        return {'CANCELLED'}

    islands = [] # Lưu trữ các cụm đá riêng biệt

    # Thuật toán loang (Flood-fill) để tìm các mặt dính liền nhau (1 cụm = 1 viên đá)
    while selected_faces:
        start_face = selected_faces.pop()
        island = {start_face}
        queue = [start_face]

        while queue:
            current_face = queue.pop(0)
            for e in current_face.edges:
                for linked_face in e.link_faces:
                    if linked_face in selected_faces:
                        selected_faces.remove(linked_face)
                        island.add(linked_face)
                        queue.append(linked_face)

        islands.append(list(island))

    # Gán Pháp tuyến và Tung đồng xu (Lồi/Lõm) RIÊNG CHO TỪNG VIÊN ĐÁ
    island_data = {}
    initial_faces_list = []

    for idx, island_faces in enumerate(islands):
        initial_faces_list.extend(island_faces)

        avg_normal = mathutils.Vector((0, 0, 0))
        for f in island_faces:
            avg_normal += f.normal
        if avg_normal.length > 0:
            avg_normal.normalize()

        island_data[idx] = {
            'normal': avg_normal,
            'is_convex': random.choice([True, False]), # Mỗi viên tung đồng xu 1 lần!
            'noise_offset': mathutils.Vector((random.uniform(-100, 100), random.uniform(-100, 100), random.uniform(-100, 100))),
            'faces': set(island_faces)
        }

    for f in bm.faces:
        f.select = False

    # ========================================================
    # 2. INSET BỀ MẶT TẤT CẢ CÙNG LÚC
    # ========================================================
    inset_res = bmesh.ops.inset_region(
        bm,
        faces=initial_faces_list,
        thickness=inset_thickness,
        use_even_offset=True
    )
    # Lưu lại các mặt viền mới sinh ra để lát nữa bôi đen lại
    rim_faces = inset_res.get('faces', [])

    bm.faces.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # ========================================================
    # 3. LỌC LẤY CHÍNH XÁC VÙNG LÕI CHO TỪNG VIÊN
    # ========================================================
    inner_faces = [f for f in initial_faces_list if f.is_valid]
    if not inner_faces:
        return {'FINISHED'}

    island_safe_verts = {idx: set() for idx in island_data.keys()}

    for idx, data in island_data.items():
        valid_island_faces = [f for f in data['faces'] if f.is_valid]

        inner_edges = set()
        for f in valid_island_faces:
            for e in f.edges:
                inner_edges.add(e)

        boundary_verts = set()
        for e in inner_edges:
            linked_inner = [f for f in e.link_faces if f in valid_island_faces]
            if len(linked_inner) == 1:
                boundary_verts.add(e.verts[0])
                boundary_verts.add(e.verts[1])

        all_inner_verts = set()
        for f in valid_island_faces:
            for v in f.verts:
                all_inner_verts.add(v)

        safe_verts = all_inner_verts - boundary_verts
        island_safe_verts[idx] = safe_verts

    # ========================================================
    # 4. CẮT TAM GIÁC VÙNG LÕI
    # ========================================================
    tri_res = bmesh.ops.triangulate(bm, faces=inner_faces)
    # Lưu lại các mặt tam giác lõi mới sinh ra để lát nữa bôi đen lại
    core_faces = tri_res.get('faces', [])

    # ========================================================
    # 5. ĐẬP MÓP NGẪU NHIÊN ĐỘC LẬP TỪNG VIÊN
    # ========================================================
    for idx, safe_verts in island_safe_verts.items():
        data = island_data[idx]
        avg_normal = data['normal']
        is_convex = data['is_convex']
        noise_offset = data['noise_offset']

        for v in safe_verts:
            if v.is_valid:
                world_co = obj.matrix_world @ v.co
                sample_point = (world_co * noise_scale) + noise_offset

                n_val = mathutils.noise.noise(sample_point)
                normalized_noise = (n_val + 1.0) / 2.0

                if is_convex:
                    biased_val = normalized_noise
                else:
                    biased_val = -normalized_noise

                v.co += avg_normal * (biased_val * noise_strength)

    # ========================================================
    # 6. KHÔI PHỤC VÙNG CHỌN BAN ĐẦU (RESTORE SELECTION)
    # ========================================================
    for f in rim_faces:
        if f.is_valid:
            f.select = True

    for f in core_faces:
        if f.is_valid:
            f.select = True

    # Bắt buộc gọi lệnh này để giao diện Blender bật màu cam cả cho Cạnh (Edge) và Đỉnh (Verts)
    bm.select_flush(True)

    # Cập nhật Viewport
    bmesh.update_edit_mesh(obj.data)

    return {'FINISHED'}

def remove_redundant_edges(self, context, angle_limit_degrees=1.0):
    obj = context.edit_object
    if not obj or obj.type != 'MESH':
        if self:
            self.report({'WARNING'}, "Vui lòng chuyển sang Edit Mode để tối ưu lưới!")
        return {'CANCELLED'}

    bm = bmesh.from_edit_mesh(obj.data)
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()

    # Xác định vùng quét (chọn một phần hoặc toàn bộ)
    selected_edges = [e for e in bm.edges if e.select]
    edges_to_clean = selected_edges if selected_edges else list(bm.edges)
    verts_to_clean = list(set(v for e in edges_to_clean for v in e.verts))

    if not edges_to_clean:
        return {'CANCELLED'}

    # ========================================================
    # BƯỚC 1: DỌN DẸP TRIỆT ĐỂ (Cho phép sinh N-Gon)
    # ========================================================
    bmesh.ops.dissolve_limit(
        bm,
        angle_limit=math.radians(angle_limit_degrees),
        use_dissolve_boundaries=False,
        edges=edges_to_clean,
        verts=verts_to_clean
    )

    bm.faces.ensure_lookup_table()

    # ========================================================
    # BƯỚC 2: TÌM DIỆT N-GON (Đa giác từ 5 cạnh trở lên)
    # ========================================================
    # Mặt đỉnh gạch (hình chữ nhật) chỉ có 4 cạnh -> An toàn, bị bỏ qua.
    # Vành đai chữ C (8 cạnh) -> Bị bắt giữ.
    ngons = [f for f in bm.faces if len(f.verts) > 4]

    if ngons:
        # Băm nát cái N-Gon đa giác lõm đó thành các hình tam giác
        bmesh.ops.triangulate(bm, faces=ngons)

        # ========================================================
        # BƯỚC 3: TRIS TO QUADS (Gom tam giác lại thành Lưới Vuông)
        # ========================================================
        # Dùng chuẩn góc 40 độ giống hệt cấu hình mặc định của Blender
        bmesh.ops.join_triangles(
            bm,
            faces=bm.faces,
            angle_face_threshold=math.radians(40.0),
            angle_shape_threshold=math.radians(40.0)
        )

    bmesh.update_edit_mesh(obj.data)

    if self:
        self.report({'INFO'}, "Đã tối ưu lưới trực diện (Chỉ giữ lại Quads và Tris)!")

    return {'FINISHED'}


def generate_procedural_stone_path(
        self,
        context,
        target_curve,          # Đối tượng Curve làm đường dẫn
        num_lanes=3,           # Tương đương 'num_layers': Số làn đá ghép ngang lại thành đường
        lane_width=0.4,        # Tương đương 'layer_height': Bề rộng của mỗi làn đá
        stone_thickness=0.15,  # Tương đương 'wall_thickness': Độ dày của viên đá (nhô lên khỏi mặt đất)
        min_length=0.4,        # Chiều dài NGẮN NHẤT của 1 viên đá dọc theo đường
        max_length=1.0,        # Chiều dài DÀI NHẤT của 1 viên đá dọc theo đường
        gap_size=0.03          # Khe hở giữa các viên đá (mạch vữa/đất)
):
    if not target_curve or target_curve.type != 'CURVE':
        if self:
            self.report({'WARNING'}, "Vui lòng chọn một đường Curve làm đường dẫn!")
        return None

    random.seed()

    # 1. TÍNH CHIỀU DÀI TỔNG THỂ CỦA ĐƯỜNG CURVE
    try:
        total_length = sum(s.calc_length() for s in target_curve.data.splines)
    except AttributeError:
        total_length = 10.0

    # ========================================================
    # 2. THUẬT TOÁN TÍNH TOÁN VỊ TRÍ CẮT SO LE NGẪU NHIÊN
    # ========================================================
    lane_cuts = []
    min_stagger = min_length * 0.35

    for i in range(num_lanes):
        cuts = []
        current_x = 0.0

        while current_x < total_length:
            stone_len = random.uniform(min_length, max_length)
            proposed_cut = current_x + stone_len

            if proposed_cut >= total_length:
                proposed_cut = total_length

            # Ép So Le: Kiểm tra với làn đá ngay bên cạnh (i-1)
            if i > 0 and proposed_cut < total_length:
                prev_cuts = lane_cuts[i-1]
                closest_cut = min(prev_cuts, key=lambda x: abs(x - proposed_cut))
                distance = abs(closest_cut - proposed_cut)

                if distance < min_stagger:
                    proposed_cut = closest_cut + min_stagger
                    if proposed_cut >= total_length:
                        proposed_cut = total_length

            cuts.append(proposed_cut)
            current_x = proposed_cut

        lane_cuts.append(cuts)

    # ========================================================
    # 3. DỰNG LƯỚI CON ĐƯỜNG (Dàn ngang theo trục Y)
    # ========================================================
    mesh = bpy.data.meshes.new(target_curve.name + "_Path")
    obj = bpy.data.objects.new(target_curve.name + "_Path", mesh)
    context.collection.objects.link(obj)

    obj.matrix_world = target_curve.matrix_world.copy()

    bm = bmesh.new()

    # Tính toán để tâm con đường nằm chính giữa đường Curve
    total_path_width = num_lanes * lane_width
    y_offset = -total_path_width / 2.0

    for i, cuts in enumerate(lane_cuts):
        # [THAY ĐỔI CHÍNH]: Dàn trải đá theo trục Y (Chiều rộng) thay vì trục Z (Chiều cao)
        y_start = y_offset + (i * lane_width)
        y_end = y_offset + ((i + 1) * lane_width)
        start_x = 0.0

        for end_x in cuts:
            x0 = start_x + (gap_size / 2)
            x1 = end_x - (gap_size / 2)
            y0 = y_start + (gap_size / 2)
            y1 = y_end - (gap_size / 2)

            # Trục Z bây giờ chỉ đơn giản là độ dày của viên đá (từ 0 lên stone_thickness)
            z0 = 0.0
            z1 = stone_thickness

            if x1 <= x0 or y1 <= y0:
                start_x = end_x
                continue

            verts = [
                bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
                bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
                bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
                bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1))
            ]

            bm.faces.new((verts[0], verts[3], verts[2], verts[1])) # Đáy
            bm.faces.new((verts[4], verts[5], verts[6], verts[7])) # Mặt đường (Đỉnh)
            bm.faces.new((verts[0], verts[1], verts[5], verts[4])) # Mặt trước
            bm.faces.new((verts[2], verts[3], verts[7], verts[6])) # Mặt sau
            bm.faces.new((verts[1], verts[2], verts[6], verts[5])) # Cạnh phải
            bm.faces.new((verts[3], verts[0], verts[4], verts[7])) # Cạnh trái

            start_x = end_x

    bm.to_mesh(mesh)
    bm.free()

    # ========================================================
    # 4. GẮN MODIFIERS ĐỂ UỐN CONG THEO PATH
    # ========================================================
    subsurf = obj.modifiers.new(name="Bending_Resolution", type='SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 3

    curve_mod = obj.modifiers.new(name="Bend_Along_Path", type='CURVE')
    curve_mod.object = target_curve
    curve_mod.deform_axis = 'POS_X'

    bevel = obj.modifiers.new(name="Stylized_Bevel", type='BEVEL')
    bevel.width = 0.04
    bevel.segments = 2
    bevel.use_clamp_overlap = True

    return obj

def generate_procedural_stone_path_v2(
        self,
        context,
        target_curve,          # Đối tượng Curve làm đường dẫn
        num_lanes=3,           # Tương đương 'num_layers': Số làn đá ghép ngang lại thành đường
        lane_width=0.4,        # Tương đương 'layer_height': Bề rộng của mỗi làn đá
        stone_thickness=0.15,  # Tương đương 'wall_thickness': Độ dày của viên đá (nhô lên khỏi mặt đất)
        min_length=0.4,        # Chiều dài NGẮN NHẤT của 1 viên đá dọc theo đường
        max_length=1.0,        # Chiều dài DÀI NHẤT của 1 viên đá dọc theo đường
        gap_size=0.03,         # Khe hở giữa các viên đá (mạch vữa/đất)
        alignment='CENTER'     # [MỚI] Căn lề: 'CENTER' (Giữa), 'LEFT' (Trái), 'RIGHT' (Phải)
):
    if not target_curve or target_curve.type != 'CURVE':
        if self:
            self.report({'WARNING'}, "Vui lòng chọn một đường Curve làm đường dẫn!")
        return None

    random.seed()

    # 1. TÍNH CHIỀU DÀI TỔNG THỂ CỦA ĐƯỜNG CURVE
    try:
        total_length = sum(s.calc_length() for s in target_curve.data.splines)
    except AttributeError:
        total_length = 10.0

    # ========================================================
    # 2. THUẬT TOÁN TÍNH TOÁN VỊ TRÍ CẮT SO LE NGẪU NHIÊN
    # ========================================================
    lane_cuts = []
    min_stagger = min_length * 0.35

    for i in range(num_lanes):
        cuts = []
        current_x = 0.0

        while current_x < total_length:
            stone_len = random.uniform(min_length, max_length)
            proposed_cut = current_x + stone_len

            if proposed_cut >= total_length:
                proposed_cut = total_length

            # Ép So Le: Kiểm tra với làn đá ngay bên cạnh (i-1)
            if i > 0 and proposed_cut < total_length:
                prev_cuts = lane_cuts[i-1]
                closest_cut = min(prev_cuts, key=lambda x: abs(x - proposed_cut))
                distance = abs(closest_cut - proposed_cut)

                if distance < min_stagger:
                    proposed_cut = closest_cut + min_stagger
                    if proposed_cut >= total_length:
                        proposed_cut = total_length

            cuts.append(proposed_cut)
            current_x = proposed_cut

        lane_cuts.append(cuts)

    # ========================================================
    # 3. DỰNG LƯỚI CON ĐƯỜNG (Dàn ngang theo trục Y)
    # ========================================================
    mesh = bpy.data.meshes.new(target_curve.name + "_Path")
    obj = bpy.data.objects.new(target_curve.name + "_Path", mesh)
    context.collection.objects.link(obj)

    obj.matrix_world = target_curve.matrix_world.copy()

    bm = bmesh.new()

    # Tính toán tổng bề rộng của đường
    total_path_width = num_lanes * lane_width

    # [THAY ĐỔI NHỎ TẠI ĐÂY] Tính điểm bắt đầu của con đường dựa trên căn lề
    if alignment == 'LEFT':
        y_offset = 0.0                     # Đường sẽ lấn toàn bộ sang bên trái
    elif alignment == 'RIGHT':
        y_offset = -total_path_width       # Đường sẽ lấn toàn bộ sang bên phải
    else: # Mặc định là 'CENTER'
        y_offset = -total_path_width / 2.0 # Đường nằm ngay chính giữa trục Curve

    for i, cuts in enumerate(lane_cuts):
        # Dàn trải đá theo trục Y (Chiều rộng) thay vì trục Z (Chiều cao)
        y_start = y_offset + (i * lane_width)
        y_end = y_offset + ((i + 1) * lane_width)
        start_x = 0.0

        for end_x in cuts:
            x0 = start_x + (gap_size / 2)
            x1 = end_x - (gap_size / 2)
            y0 = y_start + (gap_size / 2)
            y1 = y_end - (gap_size / 2)

            # Trục Z bây giờ chỉ đơn giản là độ dày của viên đá (từ 0 lên stone_thickness)
            z0 = 0.0
            z1 = stone_thickness

            if x1 <= x0 or y1 <= y0:
                start_x = end_x
                continue

            verts = [
                bm.verts.new((x0, y0, z0)), bm.verts.new((x1, y0, z0)),
                bm.verts.new((x1, y1, z0)), bm.verts.new((x0, y1, z0)),
                bm.verts.new((x0, y0, z1)), bm.verts.new((x1, y0, z1)),
                bm.verts.new((x1, y1, z1)), bm.verts.new((x0, y1, z1))
            ]

            bm.faces.new((verts[0], verts[3], verts[2], verts[1])) # Đáy
            bm.faces.new((verts[4], verts[5], verts[6], verts[7])) # Mặt đường (Đỉnh)
            bm.faces.new((verts[0], verts[1], verts[5], verts[4])) # Mặt trước
            bm.faces.new((verts[2], verts[3], verts[7], verts[6])) # Mặt sau
            bm.faces.new((verts[1], verts[2], verts[6], verts[5])) # Cạnh phải
            bm.faces.new((verts[3], verts[0], verts[4], verts[7])) # Cạnh trái

            start_x = end_x

    bm.to_mesh(mesh)
    bm.free()

    # ========================================================
    # 4. GẮN MODIFIERS ĐỂ UỐN CONG THEO PATH
    # ========================================================
    subsurf = obj.modifiers.new(name="Bending_Resolution", type='SUBSURF')
    subsurf.subdivision_type = 'SIMPLE'
    subsurf.levels = 3

    curve_mod = obj.modifiers.new(name="Bend_Along_Path", type='CURVE')
    curve_mod.object = target_curve
    curve_mod.deform_axis = 'POS_X'

    bevel = obj.modifiers.new(name="Stylized_Bevel", type='BEVEL')
    bevel.width = 0.04
    bevel.segments = 2
    bevel.use_clamp_overlap = True

    return obj