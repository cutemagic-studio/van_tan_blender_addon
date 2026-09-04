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



def build_wall_from_proxy(
        proxy_obj,
        brick_collection_name="Cute_Bricks",
        gap_size=0.02
):
    if proxy_obj.type != 'MESH':
        print("Vui lòng chọn một bức tường (Mesh) làm khuôn!")
        return

    if brick_collection_name not in bpy.data.collections:
        print(f"Không tìm thấy Collection tên là '{brick_collection_name}'!")
        return

    brick_col = bpy.data.collections[brick_collection_name]
    if len(brick_col.objects) == 0:
        print("Kho gạch của bạn đang trống!")
        return

    # ==========================================
    # 1. QUÉT DATA KHO GẠCH (Lưu vào mảng)
    # ==========================================
    print("Đang đo đạc kích thước kho gạch...")
    brick_library = []

    for obj in brick_col.objects:
        if obj.type == 'MESH':
            dim = obj.dimensions
            if dim.z == 0: continue

            brick_library.append({
                'obj': obj,
                'dim_x': dim.x, # Chiều Rộng gốc
                'dim_y': dim.y, # Bề Dày gốc
                'dim_z': dim.z  # Chiều Cao gốc
            })

    out_col_name = proxy_obj.name + "_Final_Wall"
    if out_col_name in bpy.data.collections:
        out_col = bpy.data.collections[out_col_name]
    else:
        out_col = bpy.data.collections.new(out_col_name)
        bpy.context.scene.collection.children.link(out_col)

    # ==========================================
    # 2. ĐỌC KHUÔN TƯỜNG
    # ==========================================
    bm = bmesh.new()
    bm.from_mesh(proxy_obj.data)
    bm.transform(proxy_obj.matrix_world)

    print(f"Bắt đầu lắp gạch cho {len(bm.faces)} ô trống...")

    for face in bm.faces:
        if len(face.verts) != 4:
            continue

        center = face.calc_center_bounds()
        normal = face.normal.normalized()
        world_up = Vector((0, 0, 1))

        if abs(normal.z) > 0.99:
            continue

        right = world_up.cross(normal).normalized()
        up = normal.cross(right).normalized()

        xs = [right.dot(v.co) for v in face.verts]
        zs = [up.dot(v.co) for v in face.verts]

        face_width = max(xs) - min(xs)
        face_height = max(zs) - min(zs)

        if face_height == 0: continue

        target_w = max(0.01, face_width - gap_size)
        target_h = max(0.01, face_height - gap_size)

        # ==========================================
        # 3. THUẬT TOÁN TÌM KIẾM VIÊN GẠCH KHỚP NHẤT
        # ==========================================
        # So sánh tổng sai số giữa Chiều Rộng và Chiều Cao của gạch với ô trống
        def calculate_size_difference(brick_data):
            diff_w = abs(brick_data['dim_x'] - target_w)
            diff_h = abs(brick_data['dim_z'] - target_h)
            return diff_w + diff_h # Viên nào có tổng sai số nhỏ nhất sẽ được chọn

        best_brick = min(brick_library, key=calculate_size_difference)

        # ==========================================
        # 4. INSTANCE VÀ ĐẶT VÀO TƯỜNG (KHÔNG SCALE)
        # ==========================================
        new_brick = bpy.data.objects.new(best_brick['obj'].name + "_clone", best_brick['obj'].data)
        new_brick.location = center

        mat_rot = Matrix.Identity(3)
        mat_rot.col[0] = right
        mat_rot.col[1] = normal
        mat_rot.col[2] = up
        new_brick.rotation_euler = mat_rot.to_euler()

        # [QUAN TRỌNG]: Giữ nguyên kích thước 100% gốc của viên gạch
        new_brick.scale = (1.0, 1.0, 1.0)

        out_col.objects.link(new_brick)

    bm.free()
    print("Xây tường hoàn tất! Tất cả gạch được giữ nguyên kích thước gốc.")


def build_wall_ultimate(
        proxy_obj,
        brick_collection_name="Cute_Bricks",
        overlap_size=0.05  # Độ cắn vào nhau (5cm)
):
    if proxy_obj.type != 'MESH':
        print("Vui lòng chọn một bức tường (Mesh) làm khuôn!")
        return

    if brick_collection_name not in bpy.data.collections:
        print(f"Không tìm thấy Collection tên '{brick_collection_name}'!")
        return

    brick_col = bpy.data.collections[brick_collection_name]
    if len(brick_col.objects) == 0:
        print("Kho gạch của bạn đang trống!")
        return

    # ==========================================
    # 1. QUÉT KHO GẠCH (Lấy kích thước thực)
    # ==========================================
    brick_library = []
    for obj in brick_col.objects:
        if obj.type == 'MESH':
            dim = obj.dimensions
            if dim.z == 0: continue
            brick_library.append({
                'obj': obj,
                'dim_x': dim.x,
                'dim_y': dim.y,
                'dim_z': dim.z
            })

    out_col_name = proxy_obj.name + "_Final_Wall"
    if out_col_name in bpy.data.collections:
        out_col = bpy.data.collections[out_col_name]
    else:
        out_col = bpy.data.collections.new(out_col_name)
        bpy.context.scene.collection.children.link(out_col)

    # ==========================================
    # 2. ĐỌC KHUÔN TƯỜNG (HỖ TRỢ MODIFIER)
    # ==========================================
    # Xin Blender bản sao của Object đã tính toán tất cả Modifiers (Bao gồm Curve Modifier)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = proxy_obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(eval_mesh)
    bm.transform(proxy_obj.matrix_world)

    # Dọn dẹp bộ nhớ tạm sau khi đã lấy xong BMesh
    eval_obj.to_mesh_clear()

    for face in bm.faces:
        if len(face.verts) != 4: continue

        center = face.calc_center_bounds()
        normal = face.normal.normalized()
        world_up = Vector((0, 0, 1))

        if abs(normal.z) > 0.99: continue

        right = world_up.cross(normal).normalized()
        up = normal.cross(right).normalized()

        xs = [right.dot(v.co) for v in face.verts]
        zs = [up.dot(v.co) for v in face.verts]

        face_width = max(xs) - min(xs)
        face_height = max(zs) - min(zs)
        if face_height == 0: continue

        # ==========================================
        # 3. YÊU CẦU 1: TÍNH KÍCH THƯỚC MỤC TIÊU CÓ OVERLAP
        # ==========================================
        # Thay vì tìm viên vừa khít ô, ta tìm viên to hơn ô 5cm
        target_w = face_width + overlap_size
        target_h = face_height + overlap_size

        # ==========================================
        # 4. YÊU CẦU 2: TÌM VIÊN KHỚP NHẤT (THEO SIZE THỰC)
        # ==========================================
        # Phải dùng kích thước thực để so sánh, vì nếu chỉ so Tỷ lệ mà không Scale,
        # thuật toán có thể bốc nhầm viên gạch khổng lồ nhét vào lỗ siêu nhỏ!
        def match_exact_size(brick_data):
            diff_w = abs(brick_data['dim_x'] - target_w)
            diff_h = abs(brick_data['dim_z'] - target_h)
            return diff_w + diff_h

        best_brick = min(brick_library, key=match_exact_size)

        # ==========================================
        # 5. ĐẶT GẠCH VÀ KHÓA SCALE
        # ==========================================
        new_brick = bpy.data.objects.new(best_brick['obj'].name + "_clone", best_brick['obj'].data)
        new_brick.location = center

        mat_rot = Matrix.Identity(3)
        mat_rot.col[0] = right
        mat_rot.col[1] = normal
        mat_rot.col[2] = up
        new_brick.rotation_euler = mat_rot.to_euler()

        # BẤT DI BẤT DỊCH: Luôn là 1.0
        new_brick.scale = (1.0, 1.0, 1.0)

        out_col.objects.link(new_brick)

    bm.free()
    print("Xây tường hoàn tất! Gạch giữ nguyên kích thước 100% và lấn nhau tự nhiên.")



def build_ultimate_cozy_wall(
        proxy_obj,
        brick_collection_name="Cute_Bricks",
        overlap_size=0.05
):
    if proxy_obj.type != 'MESH':
        print("Vui lòng chọn một bức tường (Mesh) làm khuôn!")
        return

    if brick_collection_name not in bpy.data.collections:
        print(f"Không tìm thấy Collection tên '{brick_collection_name}'!")
        return

    brick_col = bpy.data.collections[brick_collection_name]
    if len(brick_col.objects) == 0:
        print("Kho gạch của bạn đang trống!")
        return

    # ==========================================
    # 1. QUÉT KHO GẠCH
    # ==========================================
    brick_library = []
    for obj in brick_col.objects:
        if obj.type == 'MESH':
            dim = obj.dimensions
            if dim.z == 0: continue
            brick_library.append({
                'obj': obj,
                'dim_x': dim.x,
                'dim_y': dim.y,
                'dim_z': dim.z
            })

    out_col_name = proxy_obj.name + "_Final_Bricks"
    if out_col_name in bpy.data.collections:
        out_col = bpy.data.collections[out_col_name]
    else:
        out_col = bpy.data.collections.new(out_col_name)
        bpy.context.scene.collection.children.link(out_col)

    # ==========================================
    # 2. ĐỌC KHUÔN TƯỜNG (HỖ TRỢ MODIFIER UỐN CONG)
    # ==========================================
    # Đọc lưới đã bị uốn cong bởi Curve Modifier
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = proxy_obj.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()

    bm = bmesh.new()
    bm.from_mesh(eval_mesh)
    bm.transform(proxy_obj.matrix_world)

    for face in bm.faces:
        if len(face.verts) != 4: continue

        center = face.calc_center_bounds()
        normal = face.normal.normalized()
        world_up = Vector((0, 0, 1))

        if abs(normal.z) > 0.99: continue

        # Thuật toán "Dây dọi" giúp gạch luôn đứng thẳng dù khuôn có bị méo
        right = world_up.cross(normal).normalized()
        up = normal.cross(right).normalized()

        xs = [right.dot(v.co) for v in face.verts]
        zs = [up.dot(v.co) for v in face.verts]

        face_width = max(xs) - min(xs)
        face_height = max(zs) - min(zs)
        if face_height == 0: continue

        # ==========================================
        # 3. TÌM VIÊN GẠCH KHỚP NHẤT (CÓ OVERLAP)
        # ==========================================
        target_w = face_width + overlap_size
        target_h = face_height + overlap_size

        def match_exact_size(brick_data):
            diff_w = abs(brick_data['dim_x'] - target_w)
            diff_h = abs(brick_data['dim_z'] - target_h)
            return diff_w + diff_h

        best_brick = min(brick_library, key=match_exact_size)

        # ==========================================
        # 4. INSTANCE VÀ KHÓA SCALE
        # ==========================================
        new_brick = bpy.data.objects.new(best_brick['obj'].name + "_clone", best_brick['obj'].data.copy())
        new_brick.location = center

        mat_rot = Matrix.Identity(3)
        mat_rot.col[0] = right
        mat_rot.col[1] = normal
        mat_rot.col[2] = up
        new_brick.rotation_euler = mat_rot.to_euler()

        # BẤT DI BẤT DỊCH: Khóa Scale ở mức 100% để bảo toàn hình dáng gạch
        new_brick.scale = (1.0, 1.0, 1.0)

        out_col.objects.link(new_brick)

    bm.free()
    eval_obj.to_mesh_clear() # Giải phóng bộ nhớ ảo
    print("Xây tường hoàn tất! Siêu mượt, lấn nhau 5cm và uốn cong chuẩn xác.")



def generate_grass_overhang_bulge(
        self,
        context,
        soil_obj,
        min_length=0.1,
        max_length=0.4,
        wave_frequency=5.0,
        grass_thickness=0.08,
        random_seed=42.0,
        segment_length=0.1,
        bevel_width=0.02,
        bulge_amount=0.08
):
    if not soil_obj or soil_obj.type != 'MESH':
        self.report({'WARNING'}, "Cần chọn khối đất làm khuôn.")
        return

    bm = bmesh.new()
    bm.from_mesh(soil_obj.data)
    bm.transform(soil_obj.matrix_world)

    boundary_edges = []
    for edge in bm.edges:
        is_top_edge = any(f.normal.z > 0.8 for f in edge.link_faces)
        is_side_edge = any(abs(f.normal.z) < 0.2 for f in edge.link_faces)
        if is_top_edge and is_side_edge:
            boundary_edges.append(edge)

    if not boundary_edges:
        self.report({'ERROR'}, "Không tìm thấy mép biên phù hợp.")
        bm.free()
        return

    # Tính toán hướng đẩy (Normals)
    vert_out_dirs = {}
    for edge in boundary_edges:
        for v in edge.verts:
            if v not in vert_out_dirs:
                side_faces = [f for f in v.link_faces if abs(f.normal.z) < 0.2]
                avg_dir = Vector((0.0, 0.0, 0.0))
                if side_faces:
                    for f in side_faces:
                        avg_dir += f.normal
                else:
                    avg_dir = v.normal.copy()

                avg_dir.z = 0.0
                if avg_dir.length > 0:
                    avg_dir.normalize()
                else:
                    avg_dir = Vector((1.0, 0.0, 0.0))
                vert_out_dirs[v] = avg_dir

    grass_mesh = bpy.data.meshes.new("Grass_Overhang")
    grass_obj = bpy.data.objects.new("Stylized_Grass_Overhang", grass_mesh)
    context.collection.objects.link(grass_obj)

    # ==========================================
    # TẠO VERTEX GROUP ĐỂ KIỂM SOÁT ĐỘ PHỒNG
    # ==========================================
    vg = grass_obj.vertex_groups.new(name="Bulge_Weight")
    vg_idx = vg.index

    # Tính toán tỷ lệ phồng (Weights)
    max_thick = grass_thickness + bulge_amount
    if max_thick <= 0: max_thick = 0.001

    weight_top = grass_thickness / max_thick
    weight_mid = 1.0
    weight_bot = grass_thickness / max_thick   # [ĐÃ SỬA] Nhả độ dày cho đáy bằng với mép trên, để Subsurf tự bo tròn

    gbm = bmesh.new()
    dvert_lay = gbm.verts.layers.deform.verify() # Lớp dữ liệu để ghi Vertex Weights

    for edge in boundary_edges:
        v1, v2 = edge.verts[0], edge.verts[1]
        out1 = vert_out_dirs[v1]
        out2 = vert_out_dirs[v2]

        edge_len = (v2.co - v1.co).length
        num_segs = max(2, int(edge_len / segment_length))

        prev_top_v = None
        prev_mid_v = None
        prev_bot_v = None

        for i in range(num_segs + 1):
            t = i / num_segs
            curr_pos = v1.co.lerp(v2.co, t)

            curr_out = out1.lerp(out2, t)
            if curr_out.length > 0: curr_out.normalize()
            else: curr_out = Vector((1.0, 0.0, 0.0))

            wave_x = math.sin(curr_pos.x * wave_frequency + random_seed)
            wave_y = math.cos(curr_pos.y * wave_frequency + random_seed)
            raw_wave = (wave_x + wave_y) / 2.828 + 0.5
            organic_variance = math.sin(curr_pos.x * (wave_frequency * 0.4) + random_seed * 1.5)
            raw_wave += organic_variance * 0.15
            raw_wave = max(0.0, min(1.0, raw_wave))
            smooth_wave = raw_wave * raw_wave * (3.0 - 2.0 * raw_wave)

            drop_z = -(min_length + smooth_wave * (max_length - min_length))

            # ==========================================
            # DỰNG LƯỚI PHẲNG LÌ (KHÔNG CÓ BULGE AMOUNT)
            pos_top = curr_pos + curr_out * 0.002
            # [ĐÃ SỬA] Hạ điểm bụng từ 0.4 (40%) xuống 0.55 (55%) để độ phồng trĩu xuống tự nhiên hơn
            pos_mid = curr_pos + curr_out * 0.002 + Vector((0, 0, drop_z * 0.55))
            pos_bot = curr_pos + curr_out * 0.002 + Vector((0, 0, drop_z))

            v_top = gbm.verts.new(pos_top)
            v_mid = gbm.verts.new(pos_mid)
            v_bot = gbm.verts.new(pos_bot)

            # SƠN TRỌNG SỐ (WEIGHTS) CHO TỪNG ĐỈNH
            v_top[dvert_lay][vg_idx] = weight_top
            v_mid[dvert_lay][vg_idx] = weight_mid
            v_bot[dvert_lay][vg_idx] = weight_bot

            if prev_top_v and prev_mid_v and prev_bot_v:
                try:
                    f1 = gbm.faces.new((prev_top_v, v_top, v_mid, prev_mid_v))
                    f1.normal_update()
                    if f1.normal.dot(curr_out) < 0: f1.normal_flip()

                    f2 = gbm.faces.new((prev_mid_v, v_mid, v_bot, prev_bot_v))
                    f2.normal_update()
                    if f2.normal.dot(curr_out) < 0: f2.normal_flip()
                except ValueError:
                    pass

            prev_top_v = v_top
            prev_mid_v = v_mid
            prev_bot_v = v_bot

    bmesh.ops.remove_doubles(gbm, verts=gbm.verts, dist=0.005)
    bmesh.ops.recalc_face_normals(gbm, faces=gbm.faces)

    gbm.to_mesh(grass_mesh)
    gbm.free()
    bm.free()

    # ==========================================
    # CẬP NHẬT MODIFIERS ĐỂ PHỒNG ĐÚNG CHUẨN
    # ==========================================
    sol_mod = grass_obj.modifiers.new(name="Thick", type='SOLIDIFY')
    sol_mod.thickness = max_thick  # Tổng độ dày = Bề dày gốc + Độ phồng
    sol_mod.offset = 1.0           # [QUAN TRỌNG] Bắt buộc là 1.0 để đẩy toàn bộ ra mặt ngoài
    sol_mod.use_even_offset = False
    sol_mod.use_quality_normals = True
    sol_mod.vertex_group = "Bulge_Weight" # Chỉ định Vertex Group vừa tạo

    # Modifier bo cạnh (đã tắt theo yêu cầu của bạn)
    # bev_mod = grass_obj.modifiers.new(...)

    sub_mod = grass_obj.modifiers.new(name="Smooth_Block", type='SUBSURF')
    sub_mod.levels = 1

    if hasattr(grass_obj.data, "polygons"):
        grass_obj.data.polygons.foreach_set('use_smooth', [True] * len(grass_obj.data.polygons))

def generate_grass_overhang_bulge_v2(
        self,
        context,
        soil_obj,
        min_length=0.1,
        max_length=0.4,
        wave_frequency=5.0,
        grass_thickness=0.08,
        random_seed=42.0,
        segment_length=0.1,
        bevel_width=0.02, # Không dùng nhưng giữ để không lỗi UI
        bulge_amount=0.15
):
    if not soil_obj or soil_obj.type != 'MESH':
        self.report({'WARNING'}, "Cần chọn khối đất làm khuôn.")
        return

    bm = bmesh.new()
    bm.from_mesh(soil_obj.data)
    bm.transform(soil_obj.matrix_world)

    boundary_edges = []
    for edge in bm.edges:
        is_top_edge = any(f.normal.z > 0.8 for f in edge.link_faces)
        is_side_edge = any(abs(f.normal.z) < 0.2 for f in edge.link_faces)
        if is_top_edge and is_side_edge:
            boundary_edges.append(edge)

    if not boundary_edges:
        self.report({'ERROR'}, "Không tìm thấy mép biên phù hợp.")
        bm.free()
        return

    # Tính hướng đẩy
    vert_out_dirs = {}
    for edge in boundary_edges:
        for v in edge.verts:
            if v not in vert_out_dirs:
                side_faces = [f for f in v.link_faces if abs(f.normal.z) < 0.2]
                avg_dir = Vector((0.0, 0.0, 0.0))
                if side_faces:
                    for f in side_faces: avg_dir += f.normal
                else:
                    avg_dir = v.normal.copy()

                avg_dir.z = 0.0
                if avg_dir.length > 0: avg_dir.normalize()
                else: avg_dir = Vector((1.0, 0.0, 0.0))
                vert_out_dirs[v] = avg_dir

    grass_mesh = bpy.data.meshes.new("Grass_Overhang")
    grass_obj = bpy.data.objects.new("Stylized_Grass_Overhang", grass_mesh)
    context.collection.objects.link(grass_obj)

    vg = grass_obj.vertex_groups.new(name="Bulge_Weight")
    vg_idx = vg.index

    # Tính toán Trọng số (Weights)
    max_thick = grass_thickness + bulge_amount
    if max_thick <= 0: max_thick = 0.001

    # [MỚI] Thêm trọng số cho điểm Neo (Anchor)
    weight_anchor = grass_thickness / max_thick
    weight_top = grass_thickness / max_thick
    weight_mid = 1.0
    weight_bot = grass_thickness / max_thick

    gbm = bmesh.new()
    dvert_lay = gbm.verts.layers.deform.verify()

    for edge in boundary_edges:
        v1, v2 = edge.verts[0], edge.verts[1]
        out1 = vert_out_dirs[v1]
        out2 = vert_out_dirs[v2]

        edge_len = (v2.co - v1.co).length
        num_segs = max(2, int(edge_len / segment_length))

        prev_anchor_v = None # [MỚI]
        prev_top_v = None
        prev_mid_v = None
        prev_bot_v = None

        for i in range(num_segs + 1):
            t = i / num_segs
            curr_pos = v1.co.lerp(v2.co, t)

            curr_out = out1.lerp(out2, t)
            if curr_out.length > 0: curr_out.normalize()
            else: curr_out = Vector((1.0, 0.0, 0.0))

            wave_x = math.sin(curr_pos.x * wave_frequency + random_seed)
            wave_y = math.cos(curr_pos.y * wave_frequency + random_seed)
            raw_wave = (wave_x + wave_y) / 2.828 + 0.5
            organic_variance = math.sin(curr_pos.x * (wave_frequency * 0.4) + random_seed * 1.5)
            raw_wave += organic_variance * 0.15
            raw_wave = max(0.0, min(1.0, raw_wave))
            smooth_wave = raw_wave * raw_wave * (3.0 - 2.0 * raw_wave)

            drop_z = -(min_length + smooth_wave * (max_length - min_length))

            # ==========================================
            # [MỚI] CẤU TRÚC 4 ĐIỂM TẠO NGÀM MÓC (LIP)
            # ==========================================
            # 1. Anchor: Kéo giật lùi vào trong khối đất một đoạn bằng độ dày dải cỏ, nhích lên 2mm tránh lỗi chớp nháy
            pos_anchor = curr_pos - curr_out * (grass_thickness * 1.5) + Vector((0, 0, 0.002))

            # 2. Top: Đứng ngay mép góc vuông
            pos_top = curr_pos + curr_out * 0.002 + Vector((0, 0, 0.002))

            # 3. Mid: Bụng phồng trĩu xuống
            pos_mid = curr_pos + curr_out * 0.002 + Vector((0, 0, drop_z * 0.55))

            # 4. Bot: Mép dưới ôm sát đất
            pos_bot = curr_pos + curr_out * 0.002 + Vector((0, 0, drop_z))

            v_anchor = gbm.verts.new(pos_anchor)
            v_top = gbm.verts.new(pos_top)
            v_mid = gbm.verts.new(pos_mid)
            v_bot = gbm.verts.new(pos_bot)

            # Sơn Weights
            v_anchor[dvert_lay][vg_idx] = weight_anchor
            v_top[dvert_lay][vg_idx] = weight_top
            v_mid[dvert_lay][vg_idx] = weight_mid
            v_bot[dvert_lay][vg_idx] = weight_bot

            if prev_anchor_v and prev_top_v and prev_mid_v and prev_bot_v:
                try:
                    # [MỚI] Mặt đậy nắp (hướng lên trời)
                    f0 = gbm.faces.new((prev_anchor_v, v_anchor, v_top, prev_top_v))
                    f0.normal_update()
                    if f0.normal.z < 0: f0.normal_flip() # Bắt buộc phải ngửa lên trên

                    # Mặt trên của bụng phồng
                    f1 = gbm.faces.new((prev_top_v, v_top, v_mid, prev_mid_v))
                    f1.normal_update()
                    if f1.normal.dot(curr_out) < 0: f1.normal_flip()

                    # Mặt dưới của bụng phồng
                    f2 = gbm.faces.new((prev_mid_v, v_mid, v_bot, prev_bot_v))
                    f2.normal_update()
                    if f2.normal.dot(curr_out) < 0: f2.normal_flip()
                except ValueError:
                    pass

            prev_anchor_v = v_anchor
            prev_top_v = v_top
            prev_mid_v = v_mid
            prev_bot_v = v_bot

    bmesh.ops.remove_doubles(gbm, verts=gbm.verts, dist=0.005)
    bmesh.ops.recalc_face_normals(gbm, faces=gbm.faces)

    gbm.to_mesh(grass_mesh)
    gbm.free()
    bm.free()

    sol_mod = grass_obj.modifiers.new(name="Thick", type='SOLIDIFY')
    sol_mod.thickness = max_thick
    sol_mod.offset = 1.0
    sol_mod.use_even_offset = False
    sol_mod.use_quality_normals = True
    sol_mod.vertex_group = "Bulge_Weight"

    sub_mod = grass_obj.modifiers.new(name="Smooth_Block", type='SUBSURF')
    sub_mod.levels = 1

    if hasattr(grass_obj.data, "polygons"):
        grass_obj.data.polygons.foreach_set('use_smooth', [True] * len(grass_obj.data.polygons))


def generate_grass_overhang_bulge_v3(
        self,
        context,
        soil_obj,
        min_length=0.1,
        max_length=0.4,
        wave_frequency=5.0,
        grass_thickness=0.08,
        random_seed=42.0,
        segment_length=0.4,
        bevel_width=0.02, # Keeping for UI compatibility
        bulge_amount=0.15
):
    if not soil_obj or soil_obj.type != 'MESH':
        self.report({'WARNING'}, "Cần chọn khối đất làm khuôn.")
        return

    bm = bmesh.new()
    bm.from_mesh(soil_obj.data)
    bm.transform(soil_obj.matrix_world)

    boundary_edges = []
    for edge in bm.edges:
        is_top_edge = any(f.normal.z > 0.8 for f in edge.link_faces)
        is_side_edge = any(abs(f.normal.z) < 0.2 for f in edge.link_faces)
        if is_top_edge and is_side_edge:
            boundary_edges.append(edge)

    if not boundary_edges:
        self.report({'ERROR'}, "Không tìm thấy mép biên phù hợp.")
        bm.free()
        return

    # Tính hướng đẩy
    vert_out_dirs = {}
    for edge in boundary_edges:
        for v in edge.verts:
            if v not in vert_out_dirs:
                side_faces = [f for f in v.link_faces if abs(f.normal.z) < 0.2]
                avg_dir = Vector((0.0, 0.0, 0.0))
                if side_faces:
                    for f in side_faces: avg_dir += f.normal
                else:
                    avg_dir = v.normal.copy()

                avg_dir.z = 0.0
                if avg_dir.length > 0: avg_dir.normalize()
                else: avg_dir = Vector((1.0, 0.0, 0.0))
                vert_out_dirs[v] = avg_dir

    grass_mesh = bpy.data.meshes.new("Grass_Overhang")
    grass_obj = bpy.data.objects.new("Stylized_Grass_Overhang", grass_mesh)
    context.collection.objects.link(grass_obj)

    vg = grass_obj.vertex_groups.new(name="Bulge_Weight")
    vg_idx = vg.index

    # Trọng số: Top = 0 (vuốt nhọn khít mép), Mid = 1 (phồng tối đa), Bot = 0.1 (nhọn mép dưới)
    weight_top = 0.0
    weight_mid = 1.0
    weight_bot = 0.1

    gbm = bmesh.new()
    dvert_lay = gbm.verts.layers.deform.verify()

    for edge in boundary_edges:
        v1, v2 = edge.verts[0], edge.verts[1]
        out1 = vert_out_dirs[v1]
        out2 = vert_out_dirs[v2]

        edge_len = (v2.co - v1.co).length
        num_segs = max(2, int(edge_len / segment_length))

        prev_top_v = None
        prev_mid_v = None
        prev_bot_v = None

        for i in range(num_segs + 1):
            t = i / num_segs
            curr_pos = v1.co.lerp(v2.co, t)

            curr_out = out1.lerp(out2, t)
            if curr_out.length > 0: curr_out.normalize()
            else: curr_out = Vector((1.0, 0.0, 0.0))

            wave_x = math.sin(curr_pos.x * wave_frequency + random_seed)
            wave_y = math.cos(curr_pos.y * wave_frequency + random_seed)
            raw_wave = (wave_x + wave_y) / 2.828 + 0.5
            organic_variance = math.sin(curr_pos.x * (wave_frequency * 0.4) + random_seed * 1.5)
            raw_wave += organic_variance * 0.15
            raw_wave = max(0.0, min(1.0, raw_wave))
            smooth_wave = raw_wave * raw_wave * (3.0 - 2.0 * raw_wave)

            drop_z = -(min_length + smooth_wave * (max_length - min_length))

            # 1. Top: Đặt nằm sát đường biên (nhích Z 0.001 m mỏng nhẹ tránh Z-fighting)
            pos_top = curr_pos + Vector((0, 0, 0.001))

            # 2. Mid: Đẩy nhẹ ra ngoài và trĩu xuống
            pos_mid = curr_pos + curr_out * 0.005 + Vector((0, 0, drop_z * 0.45))

            # 3. Bot: Chóp dưới của dải cỏ
            pos_bot = curr_pos + Vector((0, 0, drop_z))

            v_top = gbm.verts.new(pos_top)
            v_mid = gbm.verts.new(pos_mid)
            v_bot = gbm.verts.new(pos_bot)

            # Sơn Weights
            v_top[dvert_lay][vg_idx] = weight_top
            v_mid[dvert_lay][vg_idx] = weight_mid
            v_bot[dvert_lay][vg_idx] = weight_bot

            if prev_top_v and prev_mid_v and prev_bot_v:
                try:
                    # Mặt trên (từ mép đất trãi xuống bụng phồng)
                    f1 = gbm.faces.new((prev_top_v, v_top, v_mid, prev_mid_v))
                    f1.normal_update()
                    if f1.normal.dot(curr_out) < 0: f1.normal_flip()

                    # Mặt dưới (từ bụng phồng đến đuôi cỏ)
                    f2 = gbm.faces.new((prev_mid_v, v_mid, v_bot, prev_bot_v))
                    f2.normal_update()
                    if f2.normal.dot(curr_out) < 0: f2.normal_flip()
                except ValueError:
                    pass

            prev_top_v = v_top
            prev_mid_v = v_mid
            prev_bot_v = v_bot

    bmesh.ops.remove_doubles(gbm, verts=gbm.verts, dist=0.005)
    bmesh.ops.recalc_face_normals(gbm, faces=gbm.faces)

    gbm.to_mesh(grass_mesh)
    gbm.free()
    bm.free()

    # Thêm Solidify để làm phồng bụng cỏ
    sol_mod = grass_obj.modifiers.new(name="Thick", type='SOLIDIFY')
    sol_mod.thickness = grass_thickness + bulge_amount
    sol_mod.offset = 0.0
    sol_mod.use_even_offset = True
    sol_mod.vertex_group = "Bulge_Weight"

    sub_mod = grass_obj.modifiers.new(name="Smooth_Block", type='SUBSURF')
    sub_mod.levels = 1

    if hasattr(grass_obj.data, "shade_smooth"):
        grass_obj.data.shade_smooth()
    elif hasattr(grass_obj.data, "polygons"):
        grass_obj.data.polygons.foreach_set('use_smooth', [True] * len(grass_obj.data.polygons))



def generate_grass_overhang_bulge_v4(
        self,
        context,
        soil_obj,
        min_length=0.1,
        max_length=0.4,
        wave_frequency=5.0,
        grass_thickness=0.08,
        random_seed=42.0,
        segment_length=0.4,
        bevel_width=0.02, # Keeping for UI compatibility
        bulge_amount=0.15
):
    self.report({'WARNING'}, "Đang làm. V4")
    
    if not soil_obj or soil_obj.type != 'MESH':
        self.report({'WARNING'}, "Cần chọn khối đất làm khuôn. V4")
        return

    bm = bmesh.new()
    bm.from_mesh(soil_obj.data)
    bm.transform(soil_obj.matrix_world)

    # 1. NHẬN DIỆN BIÊN (Sửa lỗi lòng hồ/suối dốc)
    boundary_edges = []
    for edge in bm.edges:
        top_faces = [f for f in edge.link_faces if f.normal.z > 0.5]
        side_faces = [f for f in edge.link_faces if f.normal.z <= 0.5]
        if top_faces and side_faces:
            boundary_edges.append(edge)

    if not boundary_edges:
        self.report({'ERROR'}, "Không tìm thấy mép biên phù hợp.")
        bm.free()
        return

    # 2. TÍNH HƯỚNG ĐẨY MỚI (Từ tâm mặt đất đẩy ra mép)
    vert_out_dirs = {}
    for edge in boundary_edges:
        for v in edge.verts:
            if v not in vert_out_dirs:
                connected_top_faces = [f for f in v.link_faces if f.normal.z > 0.5]
                avg_dir = Vector((0.0, 0.0, 0.0))
                
                if connected_top_faces:
                    # Cộng dồn hướng từ tâm các mặt đất lân cận để trung bình góc
                    for f in connected_top_faces:
                        f_center = f.calc_center_median()
                        dir_vec = v.co - f_center
                        dir_vec.z = 0.0
                        if dir_vec.length > 0:
                            avg_dir += dir_vec.normalized()
                            
                if avg_dir.length > 0: 
                    avg_dir.normalize()
                else: 
                    avg_dir = Vector((1.0, 0.0, 0.0))
                    
                vert_out_dirs[v] = avg_dir

    grass_mesh = bpy.data.meshes.new("Grass_Overhang")
    grass_obj = bpy.data.objects.new("Stylized_Grass_Overhang", grass_mesh)
    context.collection.objects.link(grass_obj)

    vg = grass_obj.vertex_groups.new(name="Bulge_Weight")
    vg_idx = vg.index

    # Trọng số: Top = 0 (vuốt nhọn khít mép), Mid = 1 (phồng tối đa), Bot = 0.1 (nhọn mép dưới)
    weight_top = 0.0
    weight_mid = 1.0
    weight_bot = 0.1

    gbm = bmesh.new()
    dvert_lay = gbm.verts.layers.deform.verify()

    for edge in boundary_edges:
        v1, v2 = edge.verts[0], edge.verts[1]
        out1 = vert_out_dirs[v1]
        out2 = vert_out_dirs[v2]

        edge_len = (v2.co - v1.co).length
        # 3. CHỐNG DÀY LƯỚI (Không ép chia đôi các cạnh quá ngắn)
        num_segs = max(1, round(edge_len / segment_length))

        prev_top_v = None
        prev_mid_v = None
        prev_bot_v = None

        for i in range(num_segs + 1):
            t = i / num_segs
            curr_pos = v1.co.lerp(v2.co, t)

            curr_out = out1.lerp(out2, t)
            if curr_out.length > 0: curr_out.normalize()
            else: curr_out = Vector((1.0, 0.0, 0.0))

            wave_x = math.sin(curr_pos.x * wave_frequency + random_seed)
            wave_y = math.cos(curr_pos.y * wave_frequency + random_seed)
            raw_wave = (wave_x + wave_y) / 2.828 + 0.5
            organic_variance = math.sin(curr_pos.x * (wave_frequency * 0.4) + random_seed * 1.5)
            raw_wave += organic_variance * 0.15
            raw_wave = max(0.0, min(1.0, raw_wave))
            smooth_wave = raw_wave * raw_wave * (3.0 - 2.0 * raw_wave)

            drop_z = -(min_length + smooth_wave * (max_length - min_length))

            # 1. Top: Đặt nằm sát đường biên (nhích Z 0.001 m mỏng nhẹ tránh Z-fighting)
            pos_top = curr_pos + Vector((0, 0, 0.001))

            # 2. Mid: Đẩy nhẹ ra ngoài và trĩu xuống
            pos_mid = curr_pos + curr_out * 0.005 + Vector((0, 0, drop_z * 0.45))

            # 3. Bot: Chóp dưới của dải cỏ
            pos_bot = curr_pos + Vector((0, 0, drop_z))

            v_top = gbm.verts.new(pos_top)
            v_mid = gbm.verts.new(pos_mid)
            v_bot = gbm.verts.new(pos_bot)

            # Sơn Weights
            v_top[dvert_lay][vg_idx] = weight_top
            v_mid[dvert_lay][vg_idx] = weight_mid
            v_bot[dvert_lay][vg_idx] = weight_bot

            if prev_top_v and prev_mid_v and prev_bot_v:
                try:
                    # Mặt trên (từ mép đất trãi xuống bụng phồng)
                    f1 = gbm.faces.new((prev_top_v, v_top, v_mid, prev_mid_v))
                    f1.normal_update()
                    if f1.normal.dot(curr_out) < 0: f1.normal_flip()

                    # Mặt dưới (từ bụng phồng đến đuôi cỏ)
                    f2 = gbm.faces.new((prev_mid_v, v_mid, v_bot, prev_bot_v))
                    f2.normal_update()
                    if f2.normal.dot(curr_out) < 0: f2.normal_flip()
                except ValueError:
                    pass

            prev_top_v = v_top
            prev_mid_v = v_mid
            prev_bot_v = v_bot

    bmesh.ops.remove_doubles(gbm, verts=gbm.verts, dist=0.005)
    bmesh.ops.recalc_face_normals(gbm, faces=gbm.faces)

    gbm.to_mesh(grass_mesh)
    gbm.free()
    bm.free()

    # Thêm Solidify để làm phồng bụng cỏ
    sol_mod = grass_obj.modifiers.new(name="Thick", type='SOLIDIFY')
    sol_mod.thickness = grass_thickness + bulge_amount
    sol_mod.offset = 0.0
    sol_mod.use_even_offset = True
    sol_mod.vertex_group = "Bulge_Weight"

    sub_mod = grass_obj.modifiers.new(name="Smooth_Block", type='SUBSURF')
    sub_mod.levels = 1

    if hasattr(grass_obj.data, "shade_smooth"):
        grass_obj.data.shade_smooth()
    elif hasattr(grass_obj.data, "polygons"):
        grass_obj.data.polygons.foreach_set('use_smooth', [True] * len(grass_obj.data.polygons))

def create_bounding_box_for_active():
    # 1. Lấy vật thể đang được chọn (Khuôn gốc)
    target_obj = bpy.context.active_object

    if not target_obj or target_obj.type not in {'MESH', 'CURVE', 'SURFACE', 'META', 'FONT'}:
        print("Vui lòng chọn một vật thể hợp lệ!")
        return None

    # 2. Đọc 8 điểm giới hạn (Bounding Box) của vật thể trong không gian Local
    bbox_corners = [Vector(v) for v in target_obj.bound_box]

    # Tìm Min, Max để tính toán Chiều dài, Rộng, Cao và Tâm thực tế
    min_x = min([v.x for v in bbox_corners])
    max_x = max([v.x for v in bbox_corners])
    min_y = min([v.y for v in bbox_corners])
    max_y = max([v.y for v in bbox_corners])
    min_z = min([v.z for v in bbox_corners])
    max_z = max([v.z for v in bbox_corners])

    size_x = max_x - min_x
    size_y = max_y - min_y
    size_z = max_z - min_z

    # Đây là Tâm thực tế của khung bao (Khắc phục lỗi Origin bị lệch)
    center_x = (max_x + min_x) / 2.0
    center_y = (max_y + min_y) / 2.0
    center_z = (max_z + min_z) / 2.0

    # 3. Khởi tạo Mesh và Object mới cho Bounding Box
    mesh = bpy.data.meshes.new(name=target_obj.name + "_BBox")
    bbox_obj = bpy.data.objects.new(name=target_obj.name + "_BBox", object_data=mesh)
    bpy.context.collection.objects.link(bbox_obj)

    # Đưa Bounding Box về trùng khớp 100% Vị trí, Góc xoay và Scale với vật thể gốc
    bbox_obj.matrix_world = target_obj.matrix_world.copy()

    # 4. Vẽ khối hộp bằng BMesh
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0) # Tạo khối vuông mặc định 1x1x1

    for v in bm.verts:
        # Scale khối vuông theo kích thước và dịch chuyển về đúng tâm Local
        v.co.x = (v.co.x * size_x) + center_x
        v.co.y = (v.co.y * size_y) + center_y
        v.co.z = (v.co.z * size_z) + center_z

    bm.to_mesh(mesh)
    bm.free()

    # 5. Tối ưu hiển thị (Biến nó thành dạng khung dây để không che mất vật thể)
    bbox_obj.display_type = 'WIRE'

    # Đổi lựa chọn sang Bounding Box vừa tạo để bạn dễ thao tác tiếp
    bpy.ops.object.select_all(action='DESELECT')
    bbox_obj.select_set(True)
    bpy.context.view_layer.objects.active = bbox_obj

    print(f"Đã tạo Bounding Box hoàn hảo cho: {target_obj.name}")
    return bbox_obj

import bpy

def replace_bounding_box_with_best_brick(brick_collection_name="Cute_Bricks"):
    # 1. KIỂM TRA ĐẦU VÀO
    bbox_obj = bpy.context.active_object
    if not bbox_obj:
        print("Vui lòng chọn một Bounding Box!")
        return

    brick_col = bpy.data.collections.get(brick_collection_name)
    if not brick_col or len(brick_col.objects) == 0:
        print(f"Không tìm thấy Collection '{brick_collection_name}' hoặc kho gạch đang trống!")
        return

    # Kích thước của Bounding Box (Khuôn mục tiêu)
    target_dim = bbox_obj.dimensions
    if target_dim.z == 0 or target_dim.x == 0 or target_dim.y == 0:
        print("Bounding Box bị dẹp lép (kích thước = 0), không thể tính toán!")
        return

    # Tỷ lệ của Bounding Box (Ví dụ: Dài / Cao và Rộng / Cao)
    target_aspect_xz = target_dim.x / target_dim.z
    target_aspect_yz = target_dim.y / target_dim.z

    # ==========================================
    # 2. TÌM VIÊN GẠCH CÓ TỶ LỆ GIỐNG NHẤT
    # ==========================================
    best_brick = None
    min_difference = float('inf')

    for obj in brick_col.objects:
        if obj.type != 'MESH':
            continue

        dim = obj.dimensions
        if dim.z == 0 or dim.x == 0 or dim.y == 0:
            continue

        # Tính tỷ lệ của viên gạch trong kho
        brick_aspect_xz = dim.x / dim.z
        brick_aspect_yz = dim.y / dim.z

        # Chấm điểm độ lệch (Càng nhỏ càng giống nhau về mặt tỷ lệ hình dáng)
        diff = abs(target_aspect_xz - brick_aspect_xz) + abs(target_aspect_yz - brick_aspect_yz)

        if diff < min_difference:
            min_difference = diff
            best_brick = obj

    if not best_brick:
        print("Không tìm thấy viên gạch nào phù hợp!")
        return

    # ==========================================
    # 3. SPAWN GẠCH VÀ ÉP KHUÔN
    # ==========================================
    # Tạo bản sao từ viên gạch tốt nhất tìm được
    new_brick = bpy.data.objects.new(best_brick.name + "_Placed", best_brick.data)
    bpy.context.collection.objects.link(new_brick)

    # Khớp Vị trí và Góc xoay 100% với Bounding Box
    new_brick.location = bbox_obj.location
    new_brick.rotation_euler = bbox_obj.rotation_euler

    # SCALE ĐỂ VỪA KHÍT 100%
    # Vì chúng ta đã chọn viên có tỷ lệ giống nhất, việc scale này sẽ rất "mượt", không làm méo gạch
    scale_x = target_dim.x / best_brick.dimensions.x
    scale_y = target_dim.y / best_brick.dimensions.y
    scale_z = target_dim.z / best_brick.dimensions.z

    new_brick.scale = (scale_x, scale_y, scale_z)

    # ==========================================
    # 4. DỌN DẸP
    # ==========================================
    # Ẩn cái Bounding Box đi (Không xóa để bạn có thể Undo/sửa lại nếu cần)
    # bbox_obj.hide_viewport = True
    # bbox_obj.hide_render = True

    # Chuyển vùng chọn sang viên gạch mới
    bpy.ops.object.select_all(action='DESELECT')
    new_brick.select_set(True)
    bpy.context.view_layer.objects.active = new_brick

    print(f"Thành công! Đã thay Bounding Box bằng viên gạch: {best_brick.name}")

# Cách chạy Tool

def drop_and_stack_objects(
        self, 
        context, 
        grid_resolution=5, 
        margin=0.002
):
    """
    Hàm xử lý thả rơi các đối tượng Mesh đang chọn và xếp chồng chúng lên nhau
    dựa trên tính toán Raycast từ thấp đến cao.
    """
    scene = context.scene
    depsgraph = context.evaluated_depsgraph_get()

    # 1. LỌC DANH SÁCH OBJECTS ĐƯỢC CHỌN (Chỉ lấy Mesh)
    selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
    
    if not selected_objs:
        self.report({'WARNING'}, "Cần chọn ít nhất 1 Mesh Object để thả rơi.")
        return

    # Hàm phụ trợ bên trong để tính tọa độ đáy thấp nhất (World Z)
    def get_bottom_z(obj):
        bbox_corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        return min([v.z for v in bbox_corners])

    # 2. SẮP XẾP TỪ THẤP ĐẾN CAO
    selected_objs.sort(key=get_bottom_z)

    self.report({'INFO'}, f"Bắt đầu thả rơi {len(selected_objs)} objects...")

    # 3. THỰC HIỆN RƠI TỪNG OBJECT
    for obj in selected_objs:
        # Tính toán Bounding Box để lấy giới hạn X, Y và Z thấp nhất
        bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        
        min_x = min([v.x for v in bbox_world])
        max_x = max([v.x for v in bbox_world])
        min_y = min([v.y for v in bbox_world])
        max_y = max([v.y for v in bbox_world])
        bottom_z = min([v.z for v in bbox_world])

        # Tạo lưới các điểm (grid) ở mặt đáy để bắn tia
        ray_origins = []
        steps = max(1, grid_resolution - 1)
        for i in range(grid_resolution):
            for j in range(grid_resolution):
                x = min_x + (max_x - min_x) * (i / steps if steps > 0 else 0.5)
                y = min_y + (max_y - min_y) * (j / steps if steps > 0 else 0.5)
                # Nâng tia lên 0.01m so với đáy để tránh tia bị kẹt ngay tại mặt phẳng xuất phát
                ray_origins.append(Vector((x, y, bottom_z + 0.01)))

        min_drop_distance = float('inf')
        direction = Vector((0.0, 0.0, -1.0)) # Bắn thẳng xuống trục -Z

        # 4. TRÁNH TỰ VA CHẠM (Tạm ẩn object hiện tại)
        original_hide = obj.hide_viewport
        obj.hide_viewport = True
        depsgraph.update() # Bắt buộc cập nhật để hệ thống nhận diện vật thể đã tàng hình

        # 5. BẮN TIA RAYCAST
        for origin in ray_origins:
            result, location, normal, index, hit_obj, matrix = scene.ray_cast(depsgraph, origin, direction)
            
            if result:
                # Khoảng cách = (Z bắt đầu bắn - Z va chạm) 
                # - 0.01 (bù khoảng nâng tia lên lúc nãy) 
                # - margin (khoảng hở an toàn chống Z-fighting)
                distance = (origin.z - location.z) - 0.01 - margin
                
                # Chỉ lấy khoảng cách va chạm ngắn nhất (> 0 để tránh bắt lỗi ngược lên trên)
                if 0 < distance < min_drop_distance:
                    min_drop_distance = distance

        # Trả lại trạng thái hiển thị ban đầu
        obj.hide_viewport = original_hide
        
        # 6. DỊCH CHUYỂN VÀ LÀM BỆ ĐỠ CHO LƯỢT SAU
        if min_drop_distance != float('inf'):
            obj.location.z -= min_drop_distance
        
        # Cập nhật khung cảnh để object vừa rơi xuống trở thành "đất" cho object tiếp theo
        depsgraph.update()

    self.report({'INFO'}, "Hoàn tất xếp chồng!")


import numpy as np

def create_oriented_bounding_box(obj):
    """
    Tạo Bounding Box xoay (OBB) ôm sát vật thể dựa trên trục hướng thực tế (PCA).
    """
    if not obj or obj.type != 'MESH':
        return None
    
    # 1. Lấy tọa độ tất cả các đỉnh trong không gian World
    matrix_world = obj.matrix_world
    verts = np.array([matrix_world @ v.co for v in obj.data.vertices])
    
    if len(verts) < 3:
        return None
    
    # 2. Tìm tâm (Mean) và đưa tập đỉnh về gốc tọa độ
    center = np.mean(verts, axis=0)
    centered_verts = verts - center
    
    # 3. Tính Ma trận hiệp phương sai (Covariance Matrix) và Ma trận xoay (Eigenvectors)
    cov = np.cov(centered_verts, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    # Sắp xếp các trục theo thứ tự từ dài nhất đến ngắn nhất (Dài -> Rộng -> Dày)
    sort_indices = np.argsort(eigenvalues)[::-1]
    u = eigenvectors[:, sort_indices[0]] # Trục dọc theo chiều dài lá
    v = eigenvectors[:, sort_indices[1]] # Trục ngang theo chiều rộng lá
    w = eigenvectors[:, sort_indices[2]] # Trục vuông góc (độ dày)
    
    # Đảm bảo hệ tọa độ thuận (Right-handed System)
    if np.dot(np.cross(u, v), w) < 0:
        w = -w
        
    rot_matrix_3x3 = np.column_stack((u, v, w))
    
    # 4. Chiếu các đỉnh lên 3 trục chính để tìm Min / Max kích thước
    projected = np.dot(centered_verts, rot_matrix_3x3)
    min_b = np.min(projected, axis=0)
    max_b = np.max(projected, axis=0)
    
    # 5. Dựng 8 góc của Bounding Box trong không gian World
    local_corners = np.array([
        [min_b[0], min_b[1], min_b[2]],
        [max_b[0], min_b[1], min_b[2]],
        [max_b[0], max_b[1], min_b[2]],
        [min_b[0], max_b[1], min_b[2]],
        [min_b[0], min_b[1], max_b[2]],
        [max_b[0], min_b[1], max_b[2]],
        [max_b[0], max_b[1], max_b[2]],
        [min_b[0], max_b[1], max_b[2]],
    ])
    
    world_corners = np.dot(local_corners, rot_matrix_3x3.T) + center
    
    # 6. Tạo Mesh và Object Wireframe Bounding Box
    mesh = bpy.data.meshes.new(f"{obj.name}_OBB_Mesh")
    obb_obj = bpy.data.objects.new(f"{obj.name}_OBB", mesh)
    
    # Danh sách 12 cạnh nối 8 góc tạo thành hình hộp
    edges = [
        (0, 1), (1, 2), (2, 3), (3, 0),
        (4, 5), (5, 6), (6, 7), (7, 4),
        (0, 4), (1, 5), (2, 6), (3, 7)
    ]
    
    mesh.from_pydata(world_corners.tolist(), edges, [])
    mesh.update()
    
    bpy.context.collection.objects.link(obb_obj)
    
    # Hiển thị dạng Wireframe khung dây trong Viewport
    obb_obj.display_type = 'WIRE'
    
    return obb_obj

# # --- VÍ DỤ CÁCH SỬ DỤNG ---
# active_obj = bpy.context.active_object
# if active_obj:
#     obb = create_oriented_bounding_box(active_obj)

def create_oriented_bounding_box_solid(obj, is_solid=True):
    """
    Tạo Bounding Box xoay (OBB) ôm sát vật thể dựa trên trục hướng thực tế (PCA).
    :param obj: Vật thể cần đo (Mesh)
    :param is_solid: True = Khối hộp đặc (Faces), False = Khung dây (Edges)
    """
    if not obj or obj.type != 'MESH':
        return None

    # 1. Lấy tọa độ tất cả các đỉnh trong không gian World
    matrix_world = obj.matrix_world
    verts = np.array([matrix_world @ v.co for v in obj.data.vertices])

    if len(verts) < 3:
        return None

    # 2. Tìm tâm (Mean) và đưa tập đỉnh về gốc tọa độ
    center = np.mean(verts, axis=0)
    centered_verts = verts - center

    # 3. Tính Ma trận hiệp phương sai (Covariance Matrix) và Ma trận xoay (Eigenvectors)
    cov = np.cov(centered_verts, rowvar=False)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    # Sắp xếp các trục theo thứ tự từ dài nhất đến ngắn nhất (Dài -> Rộng -> Dày)
    sort_indices = np.argsort(eigenvalues)[::-1]
    u = eigenvectors[:, sort_indices[0]] # Trục dọc theo chiều dài
    v = eigenvectors[:, sort_indices[1]] # Trục ngang theo chiều rộng
    w = eigenvectors[:, sort_indices[2]] # Trục vuông góc (độ dày)

    # Đảm bảo hệ tọa độ thuận (Right-handed System)
    if np.dot(np.cross(u, v), w) < 0:
        w = -w

    rot_matrix_3x3 = np.column_stack((u, v, w))

    # 4. Chiếu các đỉnh lên 3 trục chính để tìm Min / Max kích thước
    projected = np.dot(centered_verts, rot_matrix_3x3)
    min_b = np.min(projected, axis=0)
    max_b = np.max(projected, axis=0)

    # 5. Dựng 8 góc của Bounding Box trong không gian World
    local_corners = np.array([
        [min_b[0], min_b[1], min_b[2]], # 0: Đáy - Trái - Trước
        [max_b[0], min_b[1], min_b[2]], # 1: Đáy - Phải - Trước
        [max_b[0], max_b[1], min_b[2]], # 2: Đáy - Phải - Sau
        [min_b[0], max_b[1], min_b[2]], # 3: Đáy - Trái - Sau
        [min_b[0], min_b[1], max_b[2]], # 4: Nắp - Trái - Trước
        [max_b[0], min_b[1], max_b[2]], # 5: Nắp - Phải - Trước
        [max_b[0], max_b[1], max_b[2]], # 6: Nắp - Phải - Sau
        [min_b[0], max_b[1], max_b[2]], # 7: Nắp - Trái - Sau
    ])

    world_corners = np.dot(local_corners, rot_matrix_3x3.T) + center

    # 6. Tạo Mesh và Object Bounding Box
    mesh = bpy.data.meshes.new(f"{obj.name}_OBB_Mesh")
    obb_obj = bpy.data.objects.new(f"{obj.name}_OBB", mesh)

    # TÙY CHỌN: TẠO KHỐI ĐẶC HOẶC KHUNG DÂY
    if is_solid:
        # Khai báo 6 mặt (Faces). Thứ tự đỉnh đã được sắp xếp chuẩn để Normal không bị lộn ngược.
        faces = [
            (0, 3, 2, 1), # Mặt đáy (Bottom)
            (4, 5, 6, 7), # Mặt nắp (Top)
            (0, 1, 5, 4), # Mặt trước (Front)
            (1, 2, 6, 5), # Mặt phải (Right)
            (2, 3, 7, 6), # Mặt sau (Back)
            (3, 0, 4, 7)  # Mặt trái (Left)
        ]
        # Khi truyền Faces, Blender sẽ tự động nội suy ra Edges, nên list Edges để trống []
        mesh.from_pydata(world_corners.tolist(), [], faces)
        obb_obj.display_type = 'TEXTURED' # Hiển thị khối đặc có bóng râm
    else:
        # Khai báo 12 cạnh (Edges)
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]
        mesh.from_pydata(world_corners.tolist(), edges, [])
        obb_obj.display_type = 'WIRE' # Ép hiển thị dạng lưới dây

    mesh.update()
    bpy.context.collection.objects.link(obb_obj)

    return obb_obj


import bpy
import numpy as np
from mathutils import Vector, Matrix

def get_obb_transform(obj):
    """
    Sử dụng PCA để lấy Ma trận không gian (OBB) và Kích thước thực của vật thể.
    """
    verts = np.array([obj.matrix_world @ v.co for v in obj.data.vertices])
    
    if len(verts) < 3:
        return Matrix.Identity(4), Vector((1, 1, 1))
        
    center = np.mean(verts, axis=0)
    centered = verts - center
    
    cov = np.cov(centered, rowvar=False)
    evals, evecs = np.linalg.eigh(cov)
    
    # Sắp xếp theo chiều: Dài (u), Rộng (v), Dày (w)
    sort_idx = np.argsort(evals)[::-1]
    u = evecs[:, sort_idx[0]]
    v = evecs[:, sort_idx[1]]
    w = evecs[:, sort_idx[2]]
    
    # --- BỘ ỔN ĐỊNH TRỤC (STABILIZER) ---
    # Ngăn chặn việc PCA lật ngược lá ngẫu nhiên bằng cách so sánh với trục Local của Object
    local_mat = obj.matrix_world.to_3x3()
    local_z = (local_mat @ Vector((0, 0, 1))).normalized()
    local_x = (local_mat @ Vector((1, 0, 0))).normalized()
    
    # 1. Chống lật ngược mặt lá (Upside down)
    if np.dot(w, local_z) < 0:
        w = -w
        v = -v # Giữ nguyên quy tắc bàn tay phải (Right-handed)
        
    # 2. Chống lật xoay 180 độ dọc theo cuống lá
    if np.dot(u, local_x) < 0:
        u = -u
        v = -v 
    # ------------------------------------
    
    # Tạo Ma trận xoay OBB
    rot_mat = Matrix.Identity(3)
    rot_mat[0][0], rot_mat[1][0], rot_mat[2][0] = u
    rot_mat[0][1], rot_mat[1][1], rot_mat[2][1] = v
    rot_mat[0][2], rot_mat[1][2], rot_mat[2][2] = w
    
    # Đo kích thước thực tế theo OBB
    projected = np.dot(centered, np.column_stack((u, v, w)))
    min_b = np.min(projected, axis=0)
    max_b = np.max(projected, axis=0)
    dims = Vector(max_b - min_b)
    
    # Đóng gói thành Ma trận 4x4 (Chứa Vị trí và Hướng xoay của OBB)
    obb_matrix = Matrix.Translation(Vector(center)) @ rot_mat.to_4x4()
    
    return obb_matrix, dims

def replace_canopy_with_obb(context):
    new_leaf = context.active_object
    old_leaves = [obj for obj in context.selected_objects if obj != new_leaf and obj.type == 'MESH']
    
    if not new_leaf or not old_leaves:
        print("LỖI: Hãy chọn các lá cũ, sau đó Shift + Click chọn lá mới làm mẫu.")
        return

    # 1. Phân tích chiếc lá MẪU (Lấy chuẩn gốc)
    base_obb_mat, base_dims = get_obb_transform(new_leaf)
    base_dims.x = max(base_dims.x, 0.0001) # Chống lỗi chia cho 0 nếu lá quá mỏng
    base_dims.y = max(base_dims.y, 0.0001)
    base_dims.z = max(base_dims.z, 0.0001)
    
    # Tạo Collection chứa lá mới cho gọn
    new_col = bpy.data.collections.new("New_Canopy_OBB")
    context.scene.collection.children.link(new_col)

    # 2. Quét và thay thế
    for old_leaf in old_leaves:
        # Phân tích chiếc lá CŨ (Lấy mục tiêu)
        target_obb_mat, target_dims = get_obb_transform(old_leaf)
        
        # Tạo bản sao (Instance) từ lá mẫu để tối ưu RAM
        instance = bpy.data.objects.new(name="Leaf_Instance", object_data=new_leaf.data)
        new_col.objects.link(instance)
        
        # # --- BƯỚC QUAN TRỌNG NHẤT: MATH MAGIC ---
        # # Tính tỷ lệ Scale cần thiết để lá Mẫu to/nhỏ bằng lá Cũ
        # scale_vec = Vector((
        #     target_dims.x / base_dims.x,
        #     target_dims.y / base_dims.y,
        #     target_dims.z / base_dims.z
        # ))
        # scale_mat = Matrix.Diagonal((scale_vec.x, scale_vec.y, scale_vec.z, 1.0))
        
        # --- BƯỚC QUAN TRỌNG NHẤT: MATH MAGIC ---
        # Lựa chọn 1: Scale đều (Uniform Scale) dựa trên chiều dài (trục X)
        uniform_scale = target_dims.x / base_dims.x
        
        scale_vec = Vector((
            uniform_scale,
            uniform_scale,
            uniform_scale
        ))
        
        scale_mat = Matrix.Diagonal((scale_vec.x, scale_vec.y, scale_vec.z, 1.0))

        # Công thức chuyển đổi không gian:
        # Instance Mới = Đặt vào OBB Cũ -> Scale lại -> Xóa bỏ OBB Gốc của lá mẫu -> Giữ nguyên form mẫu
        transform_matrix = target_obb_mat @ scale_mat @ base_obb_mat.inverted()
        
        # Gán ma trận cuối cùng
        instance.matrix_world = transform_matrix @ new_leaf.matrix_world
        
        # Ẩn lá cũ đi
        # old_leaf.hide_viewport = True

    print(f"Thành công! Đã thay thế và căn chỉnh OBB cho {len(old_leaves)} chiếc lá.")


from mathutils import Vector, Matrix, Euler

def generate_canopy_leaves_from_sphere(
        self,
        context,
        leaf_count=50,          # Số lượng lá trên tán
        min_scale=0.8,          # Co giãn lá nhỏ nhất
        max_scale=1.2,          # Co giãn lá lớn nhất
        rotation_variance=0.35, # Độ xoay ngẫu nhiên (Radians)
        shell_thickness=0.15    # Độ dày lớp vỏ tán lá (phần trăm bán kính)
):
    """
    Sinh tán lá ngẫu nhiên dựa trên khối Sphere đại diện thể tích tán lá.
    """
    active_obj = context.active_object
    selected_objs = [obj for obj in context.selected_objects if obj.type == 'MESH']
    
    # 1. KIỂM TRA ĐẦU VÀO
    if len(selected_objs) < 2 or not active_obj:
        self.report({'WARNING'}, "Cần chọn 1 Sphere làm khuôn và 1 Mẫu Lá (Active Object)!")
        return

    leaf_template = active_obj
    sphere_obj = [obj for obj in selected_objs if obj != leaf_template][0]

    # 2. TÍNH TOÁN BÁN KÍNH VÀ TÂM KHỐI SPHERE (WORLD SPACE)
    sphere_center = sphere_obj.matrix_world.translation
    bbox_world = [sphere_obj.matrix_world @ Vector(corner) for corner in sphere_obj.bound_box]
    min_z = min(v.z for v in bbox_world)
    max_z = max(v.z for v in bbox_world)
    radius = (max_z - min_z) / 2.0

    # Tạo Collection chứa tán lá riêng biệt
    col_name = f"Canopy_{sphere_obj.name}"
    if col_name in bpy.data.collections:
        canopy_col = bpy.data.collections[col_name]
    else:
        canopy_col = bpy.data.collections.new(col_name)
        context.scene.collection.children.link(canopy_col)

    # 3. PHÂN BỔ ĐIỂM DÙNG THUẬT TOÁN FIBONACCI SPHERE (Rải điểm vừa đều vừa ngẫu nhiên)
    phi = math.pi * (math.sqrt(5.0) - 1.0) # Góc tỷ lệ vàng

    for i in range(leaf_count):
        y = 1.0 - (i / float(max(1, leaf_count - 1))) * 2.0  # y từ 1 down -1
        radius_at_y = math.sqrt(max(0.0, 1.0 - y * y))
        theta = phi * i

        x = math.cos(theta) * radius_at_y
        z = math.sin(theta) * radius_at_y

        # Vector hướng từ tâm quả cầu ra ngoài
        norm_dir = Vector((x, z, y)).normalized()

        # Tạo khoảng chênh lệch độ sâu ngẫu nhiên để tán lá có độ dày tự nhiên
        r_offset = radius * (1.0 + random.uniform(-shell_thickness, shell_thickness * 0.5))
        leaf_pos = sphere_center + norm_dir * r_offset

        # 4. TÍNH HƯỚNG XOAY LÁ BÁM THEO BỀ MẶT SPHERE
        # Đặt mặt lá (trục Z) chĩa ra ngoài, cuống lá (trục Y) xuôi theo tán
        track_quat = norm_dir.to_track_quat('Z', 'Y')
        base_rot_mat = track_quat.to_matrix().to_4x4()

        # Thêm biến thiên ngẫu nhiên cho góc xoay (Pitch, Yaw, Roll)
        rand_pitch = random.uniform(-rotation_variance, rotation_variance)
        rand_yaw = random.uniform(-rotation_variance * 2, rotation_variance * 2)
        rand_roll = random.uniform(-rotation_variance, rotation_variance)
        
        rand_rot_mat = Euler((rand_pitch, rand_yaw, rand_roll)).to_matrix().to_4x4()
        final_rot_mat = base_rot_mat @ rand_rot_mat

        # 5. NGẪU NHIÊN KÍCH THƯỚC (SCALE)
        s = random.uniform(min_scale, max_scale)
        scale_mat = Matrix.Diagonal((s, s, s, 1.0))

        # 6. TẠO INSTANCE LÁ MỚI
        new_leaf = bpy.data.objects.new(name=f"Leaf_{i:03d}", object_data=leaf_template.data)
        canopy_col.objects.link(new_leaf)

        # Gán ma trận tổng hợp (Vị trí + Xoay + Scale)
        loc_mat = Matrix.Translation(leaf_pos)
        new_leaf.matrix_world = loc_mat @ final_rot_mat @ scale_mat

    # Tạm ẩn Sphere khuôn đi sau khi hoàn tất
    sphere_obj.hide_viewport = True
    self.report({'INFO'}, f"Đã tạo thành công tán lá với {leaf_count} chiếc lá!")


def fill_container_with_physics(context, item_count=25, drop_frames=80, scale_min=0.8, scale_max=1.2, random_rot=True):
    container = context.active_object
    source_fruits = [obj for obj in context.selected_objects if obj != container and obj.type == 'MESH']

    if not container or not source_fruits:
        print("LỖI: Hãy chọn các trái cây mẫu, sau đó Shift + Click chọn thùng chứa làm active.")
        return

    # 1. TẠO HOẶC LẤY COLLECTION (Đã vá lỗi "not in View Layer")
    new_col = bpy.data.collections.get("Filled_Fruits")
    if not new_col:
        new_col = bpy.data.collections.new("Filled_Fruits")

    # Đảm bảo Collection này thực sự đang hiển thị trên Scene
    if new_col.name not in context.scene.collection.children:
        context.scene.collection.children.link(new_col)

    # 2. XÁC ĐỊNH KHÔNG GIAN CỦA THÙNG
    bbox = [container.matrix_world @ Vector(v) for v in container.bound_box]
    min_x = min(v.x for v in bbox)
    max_x = max(v.x for v in bbox)
    min_y = min(v.y for v in bbox)
    max_y = max(v.y for v in bbox)
    max_z = max(v.z for v in bbox)
    min_z = min(v.z for v in bbox) # Lấy cao độ đáy thùng

    if not context.scene.rigidbody_world:
        bpy.ops.rigidbody.world_add()

    # 3. CẤU HÌNH THÙNG CHỨA
    bpy.ops.object.select_all(action='DESELECT')
    container.select_set(True)
    context.view_layer.objects.active = container

    if not container.rigid_body:
        bpy.ops.rigidbody.object_add(type='PASSIVE')
    container.rigid_body.type = 'PASSIVE'
    container.rigid_body.collision_shape = 'MESH'
    container.rigid_body.friction = 0.8
    container.rigid_body.collision_margin = 0.01 # Thêm margin nhỏ để chống lọt mesh

    # 4. TẠO MẶT PHẲNG CHẶN ĐÁY (Tạm thời)
    bpy.ops.mesh.primitive_plane_add(size=50, location=(container.location.x, container.location.y, min_z))
    temp_floor = context.active_object
    bpy.ops.rigidbody.object_add(type='PASSIVE')
    temp_floor.rigid_body.collision_shape = 'BOX' # Dùng BOX cho mặt phẳng để block tốt nhất
    temp_floor.hide_viewport = True

    # 5. SINH VÀ CẤU HÌNH TRÁI CÂY
    spawned_fruits = []
    spawn_base_z = max_z + 0.3

    for i in range(item_count):
        source = random.choice(source_fruits)
        instance = bpy.data.objects.new(name=f"Fruit_Physics_{i}", object_data=source.data)
        new_col.objects.link(instance)

        rx = random.uniform(min_x, max_x)
        ry = random.uniform(min_y, max_y)
        rz = spawn_base_z + (i * 0.4)

        instance.location = Vector((rx, ry, rz))

        # Áp dụng Random Rotation
        if random_rot:
            instance.rotation_euler = Euler((
                random.uniform(0, 6.28),
                random.uniform(0, 6.28),
                random.uniform(0, 6.28)
            ))
        else:
            instance.rotation_euler = source.rotation_euler

        # Áp dụng Random Scale
        rand_scale = random.uniform(scale_min, scale_max)
        instance.scale = source.scale * rand_scale

        bpy.ops.object.select_all(action='DESELECT')
        instance.select_set(True)
        context.view_layer.objects.active = instance

        bpy.ops.rigidbody.object_add(type='ACTIVE')
        instance.rigid_body.collision_shape = 'CONVEX_HULL'
        instance.rigid_body.friction = 0.7
        instance.rigid_body.restitution = 0.1
        instance.rigid_body.collision_margin = 0.005 # Căn chỉnh margin

        spawned_fruits.append(instance)

    # 6. CHẠY TIMELINE MÔ PHỎNG
    scene = context.scene
    scene.frame_set(1)
    for f in range(1, drop_frames + 1):
        scene.frame_set(f)
        context.view_layer.update()

    # 7. APPLY VỊ TRÍ VÀ DỌN DẸP VẬT LÝ (Đã tối ưu hóa siêu tốc)
    bpy.ops.object.select_all(action='DESELECT')
    for f_obj in spawned_fruits:
        f_obj.select_set(True)

    # Apply toàn bộ vị trí cùng lúc
    bpy.ops.object.visual_transform_apply()

    # Gỡ bỏ Rigid Body cho toàn bộ object đang chọn CÙNG MỘT LÚC
    if spawned_fruits:
        context.view_layer.objects.active = spawned_fruits[0]
        bpy.ops.rigidbody.objects_remove()

    valid_fruits = []
    for f_obj in spawned_fruits:
        # QUÉT TRỤC Z: Tiêu hủy các object lọt lưới rớt dưới đáy thùng
        if f_obj.location.z < min_z - 0.05:
            bpy.data.objects.remove(f_obj, do_unlink=True)
        else:
            valid_fruits.append(f_obj)

    # 8. XÓA MẶT PHẲNG CHẶN ĐÁY VÀ DỌN DẸP THÙNG
    bpy.data.objects.remove(temp_floor, do_unlink=True)

    bpy.ops.object.select_all(action='DESELECT')
    context.view_layer.objects.active = container
    container.select_set(True)
    if container.rigid_body:
        bpy.ops.rigidbody.object_remove()

    scene.frame_set(1)

    print(f"Thành công! Đã giữ lại {len(valid_fruits)}/{item_count} trái cây an toàn trong thùng.")