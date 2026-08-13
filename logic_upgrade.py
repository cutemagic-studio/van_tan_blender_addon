import bpy
import math
import random
import bmesh
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree

def get_world_bounds(obj):
    """Trả về tọa độ Min và Max của vật thể trong không gian thế giới"""
    local_coords = [Vector(corner) for corner in obj.bound_box]
    world_coords = [obj.matrix_world @ coord for coord in local_coords]

    min_x = min(c.x for c in world_coords)
    max_x = max(c.x for c in world_coords)
    min_y = min(c.y for c in world_coords)
    max_y = max(c.y for c in world_coords)
    min_z = min(c.z for c in world_coords)
    max_z = max(c.z for c in world_coords)

    return {"x": (min_x, max_x), "y": (min_y, max_y), "z": (min_z, max_z)}

def is_inside_mesh(p, bvh_tree):
    """Kiểm tra điểm p có nằm trong mesh không bằng cách đếm số lần chạm tia"""
    hit_count = 0
    curr_p = p.copy()
    ray_dir = Vector((0, 0, 1)) 
    
    while True:
        loc, norm, idx, dist = bvh_tree.ray_cast(curr_p, ray_dir)
        if loc is None:
            break
        hit_count += 1
        curr_p = loc + ray_dir * 0.0001 
    
    return (hit_count % 2) == 1

def fill_canopy_stylized_v2(self, context, volume_obj, leaf_samples, density_factor=1.0):
    """
    Thuật toán tạo tán lá V2 Nâng Cấp:
    - density_factor: Hệ số điều chỉnh mật độ lá (mặc định 1.0)
    """
    if not volume_obj or not leaf_samples:
        return

    # 1. KHỞI TẠO BVH TREE
    depsgraph = context.view_layer.depsgraph
    eval_obj = volume_obj.evaluated_get(depsgraph)
    mesh_data = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(volume_obj.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    
    # 2. THÔNG SỐ KHỐI
    bounds = get_world_bounds(volume_obj)
    min_v = Vector((bounds['x'][0], bounds['y'][0], bounds['z'][0]))
    max_v = Vector((bounds['x'][1], bounds['y'][1], bounds['z'][1]))
    center_v = (min_v + max_v) / 2
    vol_h = max_v.z - min_v.z
    
    # Ước lượng số lượng lá (Áp dụng hệ số mật độ)
    avg_leaf_dim = sum(max(o.dimensions) for o in leaf_samples) / len(leaf_samples)
    target_count = int(((max_v - min_v).length / avg_leaf_dim) ** 2 * 10.0 * density_factor)
    target_count = max(10, min(target_count, 5000)) # Nâng giới hạn tối đa lên 5000
    
    new_leaves = []
    attempts = 0
    max_attempts = target_count * 20

    # Tạm ẩn mẫu
    original_hides = {obj: obj.hide_get() for obj in leaf_samples}
    for obj in leaf_samples: obj.hide_set(True)

    # 3. PHÂN BỔ LÁ
    while len(new_leaves) < target_count and attempts < max_attempts:
        attempts += 1
        
        # Chọn điểm ngẫu nhiên trong BBox
        sample_p = Vector((
            random.uniform(min_v.x, max_v.x),
            random.uniform(min_v.y, max_v.y),
            random.uniform(min_v.z, max_v.z)
        ))
        
        if is_inside_mesh(sample_p, bvh):
            nearest_p, normal, face_idx, dist = bvh.find_nearest(sample_p)
            
            # ƯU TIÊN LỚP VỎ (Chỉ lấy các điểm gần bề mặt)
            if dist < (max_v - min_v).length * 0.12:
                
                source = random.choice(leaf_samples)
                new_l = source.copy()
                new_l.data = source.data.copy()
                context.collection.objects.link(new_l)
                new_leaves.append(new_l)
                
                new_l.location = sample_p
                
                # --- LOGIC XOAY STYLIZED CHUẨN ---
                
                # A. Hướng tỏa ra từ tâm (Radial Dir trên mặt phẳng XY)
                radial_dir = (sample_p - Vector((center_v.x, center_v.y, sample_p.z)))
                if radial_dir.length < 0.01: radial_dir = Vector((1, 0, 0))
                radial_dir.normalize()
                
                # B. Xác định độ cao tương đối (0.0 -> 1.0)
                z_factor = (sample_p.z - min_v.z) / vol_h if vol_h > 0 else 0.5
                
                # C. Tính toán góc nghiêng (Tilt) dựa trên độ cao
                # Thấp: Rủ xuống (-45 đến -20 độ)
                # Cao: Vươn lên (15 đến 40 độ)
                if z_factor < 0.4:
                    # Nội suy góc rủ từ đáy lên giữa
                    t = z_factor / 0.4
                    tilt_deg = -45 * (1-t) + (-10 * t) 
                elif z_factor > 0.6:
                    # Nội suy góc vươn từ giữa lên đỉnh
                    t = (z_factor - 0.6) / 0.4
                    tilt_deg = 10 * (1-t) + 45 * t
                else:
                    tilt_deg = random.uniform(-10, 10)
                
                # D. Tạo hướng cơ bản (Mặt lá Z hướng lên, Đầu lá Y hướng ra ngoài)
                # 1. Hướng Y theo radial_dir, hướng Z (mặt dẹt) theo Normal bề mặt (để lá bám form)
                # Nhưng ta muốn lá nằm ngang nhiều hơn, nên ta blend Normal với Vector Up
                up_vec = Vector((0, 0, 1))
                blended_normal = (normal * 0.4 + up_vec * 0.6).normalized()
                
                q_base = radial_dir.to_track_quat('Y', 'Z') # Y hướng ra, Z hướng lên
                
                # 2. Áp dụng Tilt (xoay quanh trục X local của lá)
                m_tilt = Matrix.Rotation(math.radians(tilt_deg), 4, 'X')
                
                # 3. Random nhẹ quanh trục Z local để lá không bị quá đều
                m_rand_z = Matrix.Rotation(math.radians(random.uniform(-15, 15)), 4, 'Z')
                
                # Tổng hợp ma trận xoay và chuyển về Quaternion để gán cho vật thể
                rot_matrix = q_base.to_matrix().to_4x4() @ m_tilt @ m_rand_z
                new_l.rotation_mode = 'QUATERNION'
                new_l.rotation_quaternion = rot_matrix.to_quaternion()
                
                # E. SCALE (Giảm nhẹ dần từ dưới lên trên)
                # z_factor = 0 (đáy) -> scale multiplier 1.1
                # z_factor = 1 (ngọn) -> scale multiplier 0.85
                height_scale_multiplier = 1.1 - (z_factor * 0.25)
                new_l.scale *= height_scale_multiplier * random.uniform(0.9, 1.1)

    # 4. DỌN DẸP
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
    
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã nâng cấp tán lá Stylized: {len(new_leaves)} lá (Form rủ/vươn).")

def fill_circular_pavement(self, context, stone_obj, inner_r=1.2, outer_r=4.0):
    """
    Lát gạch vòng tròn đồng tâm (Circular Radial Pavement).
    Tự động điều chỉnh Scale X để các viên gạch khép kín vòng tròn với Gap 1cm.
    """
    if not stone_obj:
        return

    GAP = 0.01
    
    # 1. PHÂN TÍCH KÍCH THƯỚC VIÊN GẠCH GỐC
    # Giả định Y là chiều dọc (radial), X là chiều ngang (arc)
    stone_w = stone_obj.dimensions.x
    stone_l = stone_obj.dimensions.y
    
    # 2. TÍNH SỐ VÒNG (RINGS)
    ring_width = stone_l + GAP
    num_rings = int((outer_r - inner_r) / ring_width)
    
    new_stones = []
    
    for r_idx in range(num_rings):
        # Bán kính tại trung tâm hàng gạch này
        curr_r = inner_r + (r_idx * ring_width) + (stone_l / 2)
        
        # Chu vi tại bán kính này
        circumference = 2 * math.pi * curr_r
        
        # Số lượng viên gạch tối ưu để khép kín vòng (có tính đến GAP)
        # N * (StoneW + GAP) = Circumference
        num_stones = round(circumference / (stone_w + GAP))
        if num_stones < 3: num_stones = 3
        
        # Tính toán góc thực tế cho mỗi viên (bao gồm cả phần gạch và phần GAP)
        angle_step = (2 * math.pi) / num_stones
        
        # Tính toán chiều dài cung thực tế mà viên gạch phải chiếm (sau khi trừ GAP)
        # S = R * theta
        target_arc_w = (curr_r * angle_step) - GAP
        
        # Hệ số scale X để gạch khớp với cung tròn
        scale_x_factor = target_arc_w / stone_w
        
        # So le (Staggered): Xoay lệch hàng lẻ một nửa góc step
        start_angle = (angle_step / 2) if r_idx % 2 != 0 else 0
        
        for s_idx in range(num_stones):
            angle = start_angle + (s_idx * angle_step)
            
            # VỊ TRÍ: Chuyển từ tọa độ cực sang tọa độ Đề-các
            pos_x = curr_r * math.cos(angle)
            pos_y = curr_r * math.sin(angle)
            
            # Tạo bản sao
            new_s = stone_obj.copy()
            new_s.data = stone_obj.data.copy()
            context.collection.objects.link(new_s)
            new_stones.append(new_s)
            
            new_s.location = Vector((pos_x, pos_y, stone_obj.location.z))
            
            # XOAY: Luôn hướng mặt về tâm (hoặc vuông góc với bán kính)
            # Trong Blender, mặc định Y hướng lên. Ta xoay quanh Z.
            # Ta cần trục X uốn theo vòng tròn, Y hướng ra ngoài tâm.
            new_s.rotation_euler.z = angle + math.pi/2 # Xoay thêm 90 độ để Y hướng tâm
            
            # SCALE: Chỉ scale X và Y, giữ nguyên Z
            new_s.scale.x *= scale_x_factor
            # Y giữ nguyên theo mẫu (đã tính trong ring_width)
            
    context.view_layer.update()
    self.report({'INFO'}, f"Đã hoàn thành sân tròn: {len(new_stones)} viên gạch ({num_rings} vòng).")

def generate_stone_house(self, context, house_obj, bricks):
    """
    Xây dựng nhà đá hoàn chỉnh bằng cách gọi 2 hàm cột và tường đã tinh chỉnh.
    """
    if not house_obj or not bricks:
        return

    # Xây cột trước
    generate_corner_pillars(self, context, house_obj, bricks)
    # Rải gạch trang trí sau
    generate_wall_accents(self, context, house_obj, bricks)
    
    self.report({'INFO'}, "Đã xây xong nhà đá stylized hoàn chỉnh (Refined).")

def generate_corner_pillars(self, context, house_obj, bricks):
    """Xây 4 cột đá tại 4 góc của khối nhà Cube, căn lề mép ngoài."""
    if not house_obj or not bricks:
        return

    bounds = get_world_bounds(house_obj)
    min_x, max_x = bounds['x']
    min_y, max_y = bounds['y']
    min_z, max_z = bounds['z']
    
    corners = [
        (min_x, min_y, (-1, -1)),
        (max_x, min_y, (1, -1)),
        (max_x, max_y, (1, 1)),
        (min_x, max_y, (-1, 1))
    ]

    new_bricks = []
    for cx, cy, align_dir in corners:
        curr_z = min_z
        while curr_z < max_z:
            # TÍNH KHOẢNG CÁCH CÒN LẠI
            remaining_h = max_z - curr_z
            
            source = random.choice(bricks)
            new_b = source.copy()
            new_b.data = source.data.copy()
            context.collection.objects.link(new_b)
            new_bricks.append(new_b)
            
            new_b.rotation_euler.z += random.choice([0, math.pi/2, math.pi, 3*math.pi/2])
            context.view_layer.update()
            dim = new_b.dimensions
            
            # NẾU LÀ VIÊN CUỐI CÙNG (hoặc gần cuối): Scale Z để khớp nóc nhà
            # Nếu khoảng cách còn lại nhỏ hơn 1.3 lần chiều cao viên gạch hiện tại
            if remaining_h < dim.z * 1.3:
                # Scale Z để khít 100%
                new_b.scale.z *= (remaining_h / dim.z)
                context.view_layer.update()
                dim = new_b.dimensions
                # Đánh dấu để thoát vòng lặp sau viên này
                force_finish = True
            else:
                force_finish = False

            loc_x = cx - (align_dir[0] * dim.x / 2)
            loc_y = cy - (align_dir[1] * dim.y / 2)
            loc_x += random.uniform(-0.005, 0.005) # Giảm jitter để cột vuông hơn
            loc_y += random.uniform(-0.005, 0.005)
            
            new_b.location = Vector((loc_x, loc_y, curr_z + dim.z/2))
            
            if force_finish:
                break
                
            curr_z += dim.z - 0.005 # Chồng lấp cực nhẹ 5mm

    context.view_layer.update()
    self.report({'INFO'}, f"Đã xây xong 4 cột góc: {len(new_bricks)} viên.")

def generate_wall_accents(self, context, house_obj, bricks):
    """Rải gạch trang trí rải rác trên thân tường khối nhà Cube."""
    if not house_obj or not bricks:
        return

    bounds = get_world_bounds(house_obj)
    min_x, max_x = bounds['x']
    min_y, max_y = bounds['y']
    min_z, max_z = bounds['z']
    
    wall_configs = [
        (Vector((0, -1, 0)), min_y, 'X', (min_x, max_x), (min_z, max_z)),
        (Vector((1, 0, 0)), max_x, 'Y', (min_y, max_y), (min_z, max_z)),
        (Vector((0, 1, 0)), max_y, 'X', (min_x, max_x), (min_z, max_z)),
        (Vector((-1, 0, 0)), min_x, 'Y', (min_y, max_y), (min_z, max_z))
    ]

    new_bricks = []
    for normal, coord, axis_name, range_coord, range_z in wall_configs:
        area = (range_coord[1] - range_coord[0]) * (range_z[1] - range_z[0])
        stone_count = int(area * 0.45) 
        stone_count = max(1, min(stone_count, 10))
        
        # Danh sách lưu các tâm đã đặt trên mặt tường này để chống chồng lấp
        placed_centers = []
        
        for _ in range(stone_count):
            source = random.choice(bricks)
            
            # Tìm vị trí hợp lệ (thử tối đa 10 lần)
            valid_pos = None
            for _attempt in range(10):
                # 1. Tính toán margin dựa trên kích thước gạch để không lòi ra ngoài
                b_w = source.dimensions.x
                b_h = source.dimensions.z
                
                h_margin = 0.8 # Tránh cột góc
                v_margin = b_h * 0.6 # Tránh nóc/đáy
                
                if (range_coord[1] - range_coord[0]) < h_margin * 2: h_margin = 0.1
                
                pos_main = random.uniform(range_coord[0] + h_margin, range_coord[1] - h_margin)
                pos_z = random.uniform(range_z[0] + v_margin, range_z[1] - v_margin)
                
                # 2. KIỂM TRA CHỒNG LẤP (Overlap Check)
                is_overlapping = False
                new_center = Vector((pos_main, pos_z))
                # Khoảng cách tối thiểu bằng đường chéo gạch
                min_dist = math.sqrt(b_w**2 + b_h**2) * 0.8 
                
                for existing_center in placed_centers:
                    if (new_center - existing_center).length < min_dist:
                        is_overlapping = True
                        break
                
                if not is_overlapping:
                    valid_pos = (pos_main, pos_z)
                    break
            
            if valid_pos:
                pm, pz = valid_pos
                placed_centers.append(Vector((pm, pz)))
                
                new_b = source.copy()
                new_b.data = source.data.copy()
                context.collection.objects.link(new_b)
                new_bricks.append(new_b)
                
                if axis_name == 'X':
                    new_b.location = Vector((pm, coord, pz))
                else:
                    new_b.location = Vector((coord, pm, pz))
                    
                new_b.rotation_mode = 'QUATERNION'
                new_b.rotation_quaternion = normal.to_track_quat('Y', 'Z')
                new_b.scale *= random.uniform(0.8, 1.1)
                
                # CHỈ TẠO CỤM SO LE KHI CÓ XÁC SUẤT THẤP (20%)
                if random.random() < 0.2:
                    # Đảm bảo viên 2 cũng không vượt biên đứng
                    if pz + new_b.dimensions.z + 0.1 < range_z[1]:
                        new_b2 = new_b.copy()
                        new_b2.data = new_b.data.copy()
                        context.collection.objects.link(new_b2)
                        new_bricks.append(new_b2)
                        
                        offset_z = new_b.dimensions.z + 0.005
                        offset_main = new_b.dimensions.x * 0.3 * random.choice([-1, 1])
                        
                        placed_centers.append(Vector((pm + offset_main, pz + offset_z)))
                        
                        if axis_name == 'X':
                            new_b2.location += Vector((offset_main, 0, offset_z))
                        else:
                            new_b2.location += Vector((0, offset_main, offset_z))

    context.view_layer.update()
    self.report({'INFO'}, f"Đã rải gạch trang trí thưa: {len(new_bricks)} viên.")

def generate_stylized_roof(self, context, roof_obj, tiles):
    """
    Lợp mái ngói Stylized lên một mặt phẳng nghiêng - Bản sửa lỗi dàn đều.
    """
    if not roof_obj or not tiles:
        return

    # 1. PHÂN TÍCH KÍCH THƯỚC THỰC (LOCAL) CỦA PLANE
    # Dùng Mesh Data để lấy kích thước thật, tránh sai số do Rotation/Scale
    depsgraph = context.view_layer.depsgraph
    eval_obj = roof_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    
    # Lấy min/max tọa độ local của các đỉnh
    local_verts = [v.co for v in mesh.vertices]
    if not local_verts: return
    
    l_min_x = min(v.x for v in local_verts)
    l_max_x = max(v.x for v in local_verts)
    l_min_y = min(v.y for v in local_verts)
    l_max_y = max(v.y for v in local_verts)
    
    # Kích thước thật của bề mặt (đã bao gồm scale của object)
    real_w = (l_max_x - l_min_x) * roof_obj.scale.x
    real_l = (l_max_y - l_min_y) * roof_obj.scale.y
    
    mw = roof_obj.matrix_world
    rot_roof = roof_obj.rotation_quaternion if roof_obj.rotation_mode == 'QUATERNION' else roof_obj.rotation_euler.to_quaternion()

    # 2. THÔNG SỐ NGÓI
    # Lấy mẫu trung bình
    avg_w = sum(t.dimensions.x for t in tiles) / len(tiles)
    avg_l = sum(t.dimensions.y for t in tiles) / len(tiles)
    
    MAX_GAP_X = 0.02 # Tối đa 2cm theo yêu cầu
    OVERLAP = 0.35   # Chồng mí 35%
    
    # TÍNH TOÁN SỐ CỘT ĐỂ TRẢI ĐỀU (FIT WIDTH)
    # real_w = num_cols * avg_w + (num_cols - 1) * gap
    num_cols = math.ceil(real_w / (avg_w + 0.01))
    if num_cols < 1: num_cols = 1
    
    # Tính lại step_x thực tế để gạch khít từ mép này sang mép kia
    # step_x = real_w / num_cols
    actual_step_x = real_w / num_cols
    
    # Tính số hàng
    step_y = avg_l * (1.0 - OVERLAP)
    num_rows = math.ceil(real_l / step_y) + 1

    new_tiles = []
    
    # Tạm ẩn mẫu
    original_hides = {obj: obj.hide_get() for obj in tiles}
    for obj in tiles: obj.hide_set(True)

    for r in range(num_rows):
        is_staggered = (r % 2 != 0)
        
        # Số lượng cột: Hàng so le sẽ có thêm 1 viên (vì 2 viên ở đầu là nửa viên)
        current_num_cols = num_cols + 1 if is_staggered else num_cols
        
        for c in range(current_num_cols):
            # Tính toán vị trí và tỷ lệ Scale X cho từng viên
            if not is_staggered:
                # Hàng bình thường: Ngói nguyên khổ
                lx = (c * actual_step_x) - (real_w / 2) + (actual_step_x / 2)
                tile_scale_x_factor = 1.0
            else:
                # Hàng so le: Xử lý 2 đầu
                if c == 0:
                    # Viên đầu hàng: Nửa viên bên trái
                    lx = -(real_w / 2) + (actual_step_x / 4)
                    tile_scale_x_factor = 0.5
                elif c == current_num_cols - 1:
                    # Viên cuối hàng: Nửa viên bên phải
                    lx = (real_w / 2) - (actual_step_x / 4)
                    tile_scale_x_factor = 0.5
                else:
                    # Các viên ở giữa: Nguyên khổ, dịch chuyển
                    lx = -(real_w / 2) + (c * actual_step_x)
                    tile_scale_x_factor = 1.0

            ly = (r * step_y) - (real_l / 2) + (avg_l / 2)
            
            # Vị trí thế giới
            pos_local = Vector((lx / roof_obj.scale.x, ly / roof_obj.scale.y, 0))
            pos_world = mw @ pos_local
            
            # Tạo ngói
            source = random.choice(tiles)
            new_t = source.copy()
            new_t.data = source.data.copy()
            context.collection.objects.link(new_t)
            new_tiles.append(new_t)
            
            new_t.location = pos_world
            
            # XOAY
            new_t.rotation_mode = 'QUATERNION'
            m_base = mw.to_3x3().to_4x4()
            m_tilt = Matrix.Rotation(math.radians(-10), 4, 'X')
            m_jitter = Matrix.Rotation(math.radians(random.uniform(-1.5, 1.5)), 4, 'Z')
            new_t.rotation_quaternion = (m_base @ m_tilt @ m_jitter).to_quaternion()
            
            # SCALE: Khớp khít chiều ngang
            # Scale gốc để fit width mái
            base_scale_x = (actual_step_x * 0.99) / source.dimensions.x
            new_t.scale.x *= base_scale_x * tile_scale_x_factor
            new_t.scale.y *= random.uniform(0.98, 1.02)

    # Dọn dẹp
    eval_obj.to_mesh_clear()
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
        
    context.view_layer.update()
    self.report({'INFO'}, f"Đã lợp mái trải đều: {len(new_tiles)} viên ngói.")
            
    context.view_layer.update()
    self.report({'INFO'}, f"Đã lợp mái: {len(new_tiles)} viên ngói.")

def fill_rounded_square_pavement(self, context, floor_obj, bricks, inner_size=2.0, outer_size=8.0, corner_radius=1.5, gap=0.02):
    """
    Tạo khuôn viên lát đá hình vuông bo góc theo mẫu ảnh.
    - inner_size: Kích thước cạnh lỗ trống ở giữa.
    - outer_size: Kích thước cạnh tổng thể của sân.
    - corner_radius: Bán kính bo góc của hình vuông.
    """
    if not floor_obj or not bricks:
        return

    # 1. THÔNG SỐ CƠ BẢN
    avg_stone_w = sum(b.dimensions.x for b in bricks) / len(bricks)
    avg_stone_l = sum(b.dimensions.y for b in bricks) / len(bricks)
    
    # Số lượng vòng gạch (Rings)
    total_width = (outer_size - inner_size) / 2
    num_rings = int(total_width / (avg_stone_l + gap))
    
    new_stones = []
    
    # 2. VÒNG LẶP QUA TỪNG LỚP (TỪ TRONG RA NGOÀI)
    for r_idx in range(num_rings):
        # Kích thước của "đường dẫn" ở giữa hàng gạch hiện tại
        current_ring_offset = (r_idx * (avg_stone_l + gap)) + (avg_stone_l / 2)
        side_half = (inner_size / 2) + current_ring_offset
        
        # Bán kính bo góc cho lớp này (tăng dần ra ngoài để giữ độ dày đều)
        r_radius = corner_radius + (r_idx * (avg_stone_l + gap))
        
        # Chiều dài đoạn thẳng của hình vuông bo góc
        straight_len = (side_half * 2) - (r_radius * 2)
        if straight_len < 0: straight_len = 0
        
        # Chu vi của hình vuông bo góc: 4 cạnh thẳng + 1 hình tròn (4 góc cung)
        arc_len = (2 * math.pi * r_radius) / 4 # Chiều dài 1 góc cung
        total_perimeter = (straight_len * 4) + (arc_len * 4)
        
        # 3. TÍNH TOÁN SỐ VIÊN GẠCH CHO LỚP NÀY
        # N * (avg_w + gap) = total_perimeter
        num_stones = round(total_perimeter / (avg_stone_w + gap))
        if num_stones < 4: num_stones = 4
        
        # Khoảng cách bước nhảy thực tế trên chu vi (tính theo đơn vị 0.0 -> 1.0)
        step_t = 1.0 / num_stones
        
        # So le: Xoay điểm bắt đầu của mỗi hàng
        start_t = (r_idx * 0.13) % 1.0
        
        for s_idx in range(num_stones):
            t = (start_t + s_idx * step_t) % 1.0
            
            # --- HÀM LẤY VỊ TRÍ & HƯỚNG TRÊN HÌNH VUÔNG BO GÓC ---
            pos, tangent = get_point_on_rounded_square(t, side_half, r_radius)
            
            source = random.choice(bricks)
            new_s = source.copy()
            new_s.data = source.data.copy()
            context.collection.objects.link(new_s)
            new_stones.append(new_s)
            
            # VỊ TRÍ
            new_s.location = floor_obj.location + pos
            new_s.location.z += 0.01 # Nổi nhẹ lên mặt sàn
            
            # XOAY: Theo hướng tiếp tuyến của đường dẫn
            align_quat = tangent.to_track_quat('X', 'Z') # X là chiều dài viên gạch
            new_s.rotation_euler = align_quat.to_euler()
            
            # RANDOM NHẸ: Thêm jitter Stylized
            new_s.rotation_euler.z += math.radians(random.uniform(-1.5, 1.5))
            new_s.scale *= random.uniform(0.95, 1.05)
            
            # ĐIỀU CHỈNH SCALE X: Để các viên gạch khép kín mạch (Optional)
            # current_w = new_s.dimensions.x
            # target_w = (total_perimeter / num_stones) - gap
            # new_s.scale.x *= (target_w / current_w)

    context.view_layer.update()
    self.report({'INFO'}, f"Đã tạo sân gạch Stylized: {len(new_stones)} viên.")

def get_point_on_rounded_square(t, side_half, radius):
    """
    Trả về (Vị trí, Tiếp tuyến) tại tham số t (0.0 -> 1.0) trên hình vuông bo góc.
    """
    # Chiều dài cạnh thẳng
    s_len = (side_half * 2) - (radius * 2)
    # Chiều dài 1 cung (1/4 hình tròn)
    a_len = (math.pi * radius) / 2
    
    one_side_total = s_len + a_len
    total_len = one_side_total * 4
    
    curr_dist = t * total_len
    
    # Xác định chúng ta đang ở cạnh nào (0, 1, 2, 3)
    side_idx = int(curr_dist / one_side_total)
    dist_in_side = curr_dist % one_side_total
    
    # Tọa độ các góc (trước khi bo) để tính toán hướng
    # 0: Top-Right, 1: Bottom-Right, 2: Bottom-Left, 3: Top-Left
    
    # Logic: Đi từ cạnh thẳng phía trên, sau đó đến cung góc...
    # Để đơn giản, ta chia mỗi "Side" thành 2 phần: Đoạn thẳng và Cung tròn
    
    # Hướng xoay của 4 cạnh
    rotations = [0, -math.pi/2, -math.pi, -3*math.pi/2]
    base_rot = rotations[side_idx]
    
    if dist_in_side <= s_len:
        # ĐANG Ở ĐOẠN THẲNG
        # Giả sử bắt đầu từ cạnh trên (Y dương), chạy từ trái sang phải (X tăng)
        local_x = dist_in_side - (s_len / 2)
        local_y = side_half
        pos = Vector((local_x, local_y, 0))
        tangent = Vector((1, 0, 0))
    else:
        # ĐANG Ở ĐOẠN CUNG
        arc_t = (dist_in_side - s_len) / a_len # 0.0 -> 1.0 trong cung
        angle = (math.pi / 2) * (1.0 - arc_t)
        
        # Tâm của cung tròn góc đó
        center_x = (side_half - radius)
        center_y = (side_half - radius)
        
        pos = Vector((center_x + radius * math.cos(angle), 
                      center_y + radius * math.sin(angle), 0))
        
        # Tiếp tuyến của đường tròn: (-sin(a), cos(a))
        tangent = Vector((-math.sin(angle), math.cos(angle), 0))

    # XOAY VECTOR THEO CẠNH TƯƠNG ỨNG
    rot_mat = Matrix.Rotation(base_rot, 4, 'Z')
    return rot_mat @ pos, rot_mat @ tangent

def generate_stone_house_v2(self, context, house_obj, bricks):
    """Xây dựng nhà tháp đá V2 nâng cao (Tapered Tower)."""
    if not house_obj or not bricks:
        return
    generate_corner_pillars_v2(self, context, house_obj, bricks)
    generate_wall_accents_v2(self, context, house_obj, bricks)
    self.report({'INFO'}, "Đã xây xong tháp đá V2.")

def generate_corner_pillars_v2(self, context, house_obj, bricks):
    """
    Xây cột tháp V2 - Sửa lỗi: Gạch bám góc tháp kiểu Zipper (Interlocking).
    """
    if not house_obj or not bricks:
        return

    # 1. PHÂN TÍCH HÌNH HỌC THÁP
    mw = house_obj.matrix_world
    depsgraph = context.view_layer.depsgraph
    eval_obj = house_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    
    verts_world = [mw @ v.co for v in mesh.vertices]
    min_z = min(v.z for v in verts_world)
    max_z = max(v.z for v in verts_world)
    
    bottom_verts = [v for v in verts_world if v.z - min_z < 0.01]
    top_verts = [v for v in verts_world if v.z - max_z > -0.01]
    
    if len(bottom_verts) < 4 or len(top_verts) < 4:
        return

    def get_corners(v_list):
        center = sum(v_list, Vector()) / len(v_list)
        return sorted(v_list, key=lambda v: math.atan2(v.y - center.y, v.x - center.x))

    b_corners = get_corners(bottom_verts)
    t_corners = get_corners(top_verts)

    new_bricks = []
    
    # 2. XÂY 4 CỘT (0:Bottom-Left, 1:Bottom-Right, 2:Top-Right, 3:Top-Left)
    # Tương ứng với các góc phần tư để biết hướng "ép" mép gạch
    align_dirs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]

    for i in range(4):
        p_start = b_corners[i]
        p_end = t_corners[i]
        ad_x, ad_y = align_dirs[i]
        
        pillar_vec = p_end - p_start
        total_h = p_end.z - p_start.z
        
        curr_z_local = 0.0
        layer_idx = 0
        
        while curr_z_local < total_h:
            layer_idx += 1
            source = random.choice(bricks)
            new_b = source.copy()
            new_b.data = source.data.copy()
            context.collection.objects.link(new_b)
            new_bricks.append(new_b)
            
            # --- TÍNH TOÁN KÍCH THƯỚC SO LE (ZIPPER) ---
            # Random kích thước cơ bản
            base_sc = random.uniform(0.9, 1.1)
            new_b.scale *= base_sc
            
            # Đan xen chiều dài: Tầng chẵn dài X, tầng lẻ dài Y
            if layer_idx % 2 == 0:
                new_b.scale.x *= 1.4
                new_b.scale.y *= 0.8
            else:
                new_b.scale.x *= 0.8
                new_b.scale.y *= 1.4
            
            context.view_layer.update()
            dim = new_b.dimensions

            # --- VỊ TRÍ NỘI SUY ---
            t = (curr_z_local + dim.z / 2) / total_h
            # Điểm mốc trên cạnh nghiêng của tháp
            edge_point = p_start + (pillar_vec * t)
            
            # Ép mép ngoài của gạch vào edge_point
            # loc = edge_point - (hướng ép * nửa kích thước gạch)
            loc_x = edge_point.x - (ad_x * dim.x / 2)
            loc_y = edge_point.y - (ad_y * dim.y / 2)
            
            # Thêm jitter cực nhỏ cho tự nhiên
            loc_x += random.uniform(-0.005, 0.005)
            loc_y += random.uniform(-0.005, 0.005)
            
            new_b.location = Vector((loc_x, loc_y, edge_point.z))
            
            # XOAY: Giữ nguyên hướng vuông góc với tháp (mặc định)
            # Có thể thêm random xoay 180 độ để đổi mặt đá
            if random.random() > 0.5:
                new_b.rotation_euler.z += math.pi
            
            # XỬ LÝ VIÊN CUỐI
            if curr_z_local + dim.z > total_h:
                new_b.scale.z *= (total_h - curr_z_local) / dim.z
                break
                
            curr_z_local += dim.z - 0.005 # Chồng lấp nhẹ 5mm

    eval_obj.to_mesh_clear()
    context.view_layer.update()
    self.report({'INFO'}, f"Đã xây cột tháp Zipper: {len(new_bricks)} viên.")

    context.view_layer.update()
    self.report({'INFO'}, f"Đã xây xong cột tháp Stylized (So le & Nghiêng).")

    eval_obj.to_mesh_clear()
    context.view_layer.update()
    self.report({'INFO'}, f"Đã xây 4 cột nghiêng V2: {len(new_bricks)} viên.")

def generate_wall_accents_v2(self, context, house_obj, bricks):
    """Rải gạch lên thân tường nghiêng của khối tháp V2."""
    if not house_obj or not bricks:
        return

    # 1. KHỞI TẠO BVH ĐỂ TÌM MẶT NGHIÊNG
    mw = house_obj.matrix_world
    depsgraph = context.view_layer.depsgraph
    eval_obj = house_obj.evaluated_get(depsgraph)
    mesh_data = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(mw)
    bvh = BVHTree.FromBMesh(bm)
    
    # 2. LẤY GIỚI HẠN
    bounds = get_world_bounds(house_obj)
    min_z, max_z = bounds['z']
    
    # 3. RẢI TRANG TRÍ
    new_stones = []
    placed_centers = []
    
    # Chúng ta thử rải ngẫu nhiên quanh tháp và dùng Raycast bắn vào mặt
    target_count = 25 # Tổng số điểm nhấn cho tháp
    attempts = 0
    
    while len(new_stones) < target_count and attempts < 200:
        attempts += 1
        
        # Chọn độ cao ngẫu nhiên (tránh nóc/đáy)
        z = random.uniform(min_z + 0.5, max_z - 0.5)
        
        # Chọn góc quay ngẫu nhiên quanh tâm tháp để bắn tia
        angle = random.uniform(0, math.pi * 2)
        dist_out = 10.0 # Khoảng cách bắn từ ngoài vào
        
        origin_ray = Vector((math.cos(angle) * dist_out, math.sin(angle) * dist_out, z))
        direction_ray = Vector((-math.cos(angle), -math.sin(angle), 0))
        
        loc, norm, idx, dist = bvh.ray_cast(origin_ray, direction_ray)
        
        if loc:
            # Kiểm tra khoảng cách chống chồng lấp
            is_overlap = False
            for prev_loc in placed_centers:
                if (loc - prev_loc).length < 1.0: # 1 mét khoảng cách an toàn
                    is_overlap = True
                    break
            
            if not is_overlap:
                source = random.choice(bricks)
                new_s = source.copy()
                new_s.data = source.data.copy()
                context.collection.objects.link(new_s)
                new_stones.append(new_s)
                
                new_s.location = loc
                placed_centers.append(loc.copy())
                
                # XOAY: Áp sát mặt nghiêng (Dùng Normal)
                new_s.rotation_mode = 'QUATERNION'
                new_s.rotation_quaternion = norm.to_track_quat('Y', 'Z')
                
                # SCALE & JITTER
                new_s.scale *= random.uniform(0.7, 1.1)
                
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    self.report({'INFO'}, f"Đã trang trí tháp nghiêng: {len(new_stones)} viên gạch.")

def generate_wooden_plank_walls(self, context, house_obj, planks, gap=0.015):
    """
    Tạo các bức tường gỗ bao quanh khối Cube (Sửa lỗi Scale nhầm trục dày).
    """
    if not house_obj or not planks:
        return

    # 1. THÔNG SỐ KHỐI NHÀ
    bounds = get_world_bounds(house_obj)
    min_x, max_x = bounds['x']
    min_y, max_y = bounds['y']
    min_z, max_z = bounds['z']
    
    house_w = max_x - min_x
    house_d = max_y - min_y
    house_h = max_z - min_z
    
    # 2. PHÂN TÍCH THANH GỖ MẪU (Để biết trục nào là chiều dài, trục nào là độ dày)
    ref_plank = planks[0]
    # Giả định Z là chiều cao. Ta so sánh X và Y để tìm trục dài nhất.
    is_x_long = ref_plank.dimensions.x >= ref_plank.dimensions.y
    length_axis = 'X' if is_x_long else 'Y'
    thickness_axis = 'Y' if is_x_long else 'X'
    
    avg_plank_h = sum(p.dimensions.z for p in planks) / len(planks)
    
    # 3. TÍNH TOÁN FIT CHIỀU CAO
    num_rows = math.ceil(house_h / (avg_plank_h + gap))
    if num_rows < 1: num_rows = 1
    
    actual_plank_h = (house_h / num_rows) - gap
    scale_z_multiplier = actual_plank_h / avg_plank_h
    
    # 4. CẤU HÌNH 4 MẶT TƯỜNG
    wall_configs = [
        (Vector((0, -1, 0)), min_y, 'X', house_w), # Trước
        (Vector((1, 0, 0)), max_x, 'Y', house_d),  # Phải
        (Vector((0, 1, 0)), max_y, 'X', house_w),  # Sau
        (Vector((-1, 0, 0)), min_x, 'Y', house_d)  # Trái
    ]

    new_planks = []
    
    # Tạm ẩn mẫu
    original_hides = {obj: obj.hide_get() for obj in planks}
    for obj in planks: obj.hide_set(True)

    for normal, face_coord, axis_name, face_width in wall_configs:
        for r in range(num_rows):
            source = random.choice(planks)
            new_p = source.copy()
            new_p.data = source.data.copy()
            context.collection.objects.link(new_p)
            new_planks.append(new_p)

            # --- SỬA LỖI VỊ TRÍ: ĐƯA ORIGIN VỀ TÂM HÌNH HỌC ---
            # Điều này đảm bảo khi đặt vào tâm mặt Cube, thanh gỗ không bị lệch sang một bên
            context.view_layer.objects.active = new_p
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            
            # --- SCALE CHIỀU CAO (Z) ---
            new_p.scale.z *= scale_z_multiplier
            
            # --- SCALE CHIỀU DÀI (Fit ngang mặt Cube) ---
            curr_len = new_p.dimensions.x if is_x_long else new_p.dimensions.y
            if is_x_long:
                new_p.scale.x *= (face_width / curr_len)
            else:
                new_p.scale.y *= (face_width / curr_len)
            
            # --- TÍNH TOÁN VỊ TRÍ & OFFSET ĐỘ DÀY ---
            thickness = new_p.dimensions.y if is_x_long else new_p.dimensions.x
            offset_dist = thickness / 2
            
            z_pos = min_z + (r * (actual_plank_h + gap)) + (actual_plank_h / 2)
            
            if axis_name == 'X':
                base_loc = Vector(((min_x + max_x)/2, face_coord, z_pos))
            else:
                base_loc = Vector((face_coord, (min_y + max_y)/2, z_pos))
            
            # Gán vị trí chuẩn (Tâm mặt + đẩy ra ngoài theo độ dày)
            new_p.location = base_loc + (normal * offset_dist)
            
            # --- XOAY ---
            track_axis = 'Y' if is_x_long else 'X'
            new_p.rotation_mode = 'QUATERNION'
            new_p.rotation_quaternion = normal.to_track_quat(track_axis, 'Z')

    # Dọn dẹp
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
        
    context.view_layer.update()
    self.report({'INFO'}, f"Đã tạo tường gỗ Fit Height: {len(new_planks)} thanh.")

def generate_vertical_plank_walls(self, context, house_obj, planks, gap=0.01):
    """
    Tạo các bức tường gỗ đứng bao quanh khối Cube.
    """
    if not house_obj or not planks:
        return

    # 1. THÔNG SỐ KHỐI NHÀ
    bounds = get_world_bounds(house_obj)
    min_x, max_x = bounds['x']
    min_y, max_y = bounds['y']
    min_z, max_z = bounds['z']
    
    house_w = max_x - min_x
    house_d = max_y - min_y
    house_h = max_z - min_z
    
    # 2. PHÂN TÍCH MẪU
    ref_plank = planks[0]
    # Trục Z là chiều cao. Tìm trục rộng (width) và dày (thickness)
    is_x_wide = ref_plank.dimensions.x >= ref_plank.dimensions.y
    width_axis = 'X' if is_x_wide else 'Y'
    thickness_axis = 'Y' if is_x_wide else 'X'
    
    avg_plank_w = sum(p.dimensions.x if is_x_wide else p.dimensions.y for p in planks) / len(planks)
    
    # 3. CẤU HÌNH 4 MẶT TƯỜNG
    wall_configs = [
        (Vector((0, -1, 0)), min_y, 'X', house_w), # Trước
        (Vector((1, 0, 0)), max_x, 'Y', house_d),  # Phải
        (Vector((0, 1, 0)), max_y, 'X', house_w),  # Sau
        (Vector((-1, 0, 0)), min_x, 'Y', house_d)  # Trái
    ]

    new_planks = []
    original_hides = {obj: obj.hide_get() for obj in planks}
    for obj in planks: obj.hide_set(True)

    for normal, face_coord, axis_name, face_width in wall_configs:
        # TÍNH TOÁN FIT CHIỀU NGANG MẶT TƯỜNG
        num_cols = math.ceil(face_width / (avg_plank_w + gap))
        if num_cols < 1: num_cols = 1
        
        # Độ rộng thực tế để khít mặt
        actual_plank_w = (face_width / num_cols) - gap
        
        for c in range(num_cols):
            source = random.choice(planks)
            new_p = source.copy()
            new_p.data = source.data.copy()
            context.collection.objects.link(new_p)
            new_planks.append(new_p)

            # Đưa Origin về tâm
            context.view_layer.objects.active = new_p
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            
            # --- SCALE CHIỀU CAO (FIT CUBE HEIGHT) ---
            new_p.scale.z *= (house_h / source.dimensions.z)
            
            # --- SCALE ĐỘ RỘNG (FIT FACE WIDTH) ---
            orig_w = source.dimensions.x if is_x_wide else source.dimensions.y
            if is_x_wide:
                new_p.scale.x *= (actual_plank_w / orig_w)
            else:
                new_p.scale.y *= (actual_plank_w / orig_w)
            
            # --- VỊ TRÍ ---
            thickness = new_p.dimensions.y if is_x_wide else new_p.dimensions.x
            offset_dist = thickness / 2
            
            # Tọa độ ngang trên mặt tường
            start_coord = (min_x if axis_name == 'X' else min_y)
            pos_main = start_coord + (c * (actual_plank_w + gap)) + (actual_plank_w / 2)
            
            z_pos = (min_z + max_z) / 2
            
            if axis_name == 'X':
                base_loc = Vector((pos_main, face_coord, z_pos))
            else:
                base_loc = Vector((face_coord, pos_main, z_pos))
            
            new_p.location = base_loc + (normal * offset_dist)
            
            # --- XOAY ---
            track_axis = 'Y' if is_x_wide else 'X'
            new_p.rotation_mode = 'QUATERNION'
            new_p.rotation_quaternion = normal.to_track_quat(track_axis, 'Z')

    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
        
    context.view_layer.update()
    self.report({'INFO'}, f"Đã tạo tường gỗ đứng: {len(new_planks)} thanh.")

def snap_planks_to_segments(self, context, segments, material_bar):
    """
    Snap và Scale thanh vật liệu khớp vào các đoạn thẳng được chọn.
    """
    if not material_bar or not segments:
        return

    # 1. PHÂN TÍCH THANH VẬT LIỆU MẪU
    # Tìm trục dài nhất của thanh vật liệu
    dims = material_bar.dimensions
    max_dim = max(dims)
    if max_dim < 0.001: return
    
    if dims.x == max_dim:
        length_axis = 'X'
        track_axis = 'X'
    elif dims.y == max_dim:
        length_axis = 'Y'
        track_axis = 'Y'
    else:
        length_axis = 'Z'
        track_axis = 'Z'
        
    new_objs = []
    
    # 2. DUYỆT QUA CÁC ĐOẠN THẲNG
    for seg_obj in segments:
        # Lấy tọa độ 2 điểm đầu mút
        # Hỗ trợ Mesh (lấy 2 đỉnh đầu tiên) hoặc Curve (lấy 2 điểm đầu tiên)
        p1, p2 = None, None
        
        mw = seg_obj.matrix_world
        
        if seg_obj.type == 'MESH':
            if len(seg_obj.data.vertices) < 2: continue
            p1 = mw @ seg_obj.data.vertices[0].co
            p2 = mw @ seg_obj.data.vertices[1].co
        elif seg_obj.type == 'CURVE':
            if not seg_obj.data.splines: continue
            points = seg_obj.data.splines[0].bezier_points if seg_obj.data.splines[0].type == 'BEZIER' else seg_obj.data.splines[0].points
            if len(points) < 2: continue
            p1 = mw @ points[0].co.xyz
            p2 = mw @ points[1].co.xyz
            
        if p1 is None or p2 is None: continue
        
        # 3. TÍNH TOÁN VÉC-TƠ VÀ CHIỀU DÀI
        vec = p2 - p1
        length = vec.length
        center = (p1 + p2) / 2
        
        if length < 0.0001: continue
        
        # 4. TẠO VÀ CĂN CHỈNH THANH VẬT LIỆU
        new_obj = material_bar.copy()
        new_obj.data = material_bar.data.copy()
        context.collection.objects.link(new_obj)
        new_objs.append(new_obj)
        
        # Đưa Origin về tâm để quay cho chuẩn
        context.view_layer.objects.active = new_obj
        bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
        
        # Vị trí
        new_obj.location = center
        
        # Xoay theo hướng đoạn thẳng
        new_obj.rotation_mode = 'QUATERNION'
        new_obj.rotation_quaternion = vec.to_track_quat(track_axis, 'Z' if track_axis != 'Z' else 'Y')
        
        # Scale chiều dài khớp đoạn thẳng
        # Tính tỉ lệ scale: Chiều dài đích / Chiều dài hiện tại
        if length_axis == 'X':
            current_len = new_obj.dimensions.x
            if current_len > 0: new_obj.scale.x *= (length / current_len)
        elif length_axis == 'Y':
            current_len = new_obj.dimensions.y
            if current_len > 0: new_obj.scale.y *= (length / current_len)
        else:
            current_len = new_obj.dimensions.z
            if current_len > 0: new_obj.scale.z *= (length / current_len)

    context.view_layer.update()
    self.report({'INFO'}, f"Đã Snap & Fit {len(new_objs)} thanh vật liệu.")

def create_stylized_tree(self, context):
    """
    Tạo cây Stylized với logic Phân nhánh đa điểm và Cành dẫn đầu vươn cao.
    """
    
    # --- BẢNG ĐIỀU KHIỂN NÂNG CAO (DNA CỦA CÂY) ---
    cfg = {
        'depth': 4,                  # Cấp độ đệ quy của tán lá.
        'trunk_h': 4.0,              # Chiều cao tổng của thân chính.
        'trunk_segs': 6,             # Số đốt xương trên thân.
        'branch_forks': 2,           # Số nhánh con ở các cấp phía trên.
        'first_split_forks': 3,      # [MỚI] Ép lần rẽ đầu tiên từ thân phải có 3 nhánh chính.
        'trunk_side_branches': False, # [MỚI] Cho phép mọc nhánh chính dọc thân khi đang vươn cao.
        'spread_base': 0.85,          # Độ xòe của tán phía dưới.
        'spread_top': 0.35,          # Độ xòe phía ngọn (càng nhỏ càng chụm vươn cao).
        'length_mult': 0.8,         # Tỉ lệ giảm chiều dài cành con.
        'radius_mult': 0.7,          # Tỉ lệ thu nhỏ bán kính cành con.
        'leader_bias': 0.2,          # Độ thẳng của trục dẫn đầu (càng nhỏ càng thẳng).
        'noise_strength': 0.1        # Độ cong vẹo tự nhiên.
    }

    mesh_data = bpy.data.meshes.new("StylizedTreeMesh")
    tree_obj = bpy.data.objects.new("Stylized_Tree", mesh_data)
    context.collection.objects.link(tree_obj)
    
    bm = bmesh.new()
    skin_layer = bm.verts.layers.skin.verify()

    # Hàm đệ quy mọc cành
    def grow_branch(start_v, direction, length, radius, depth, is_leader=True):
        if depth == 0 or radius < 0.01:
            return

        noise = Vector((random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(0.02, 0.08)))
        new_pos_dir = (direction + noise).normalized()
        end_v = bm.verts.new(start_v.co + new_pos_dir * length)
        end_v[skin_layer].radius = (radius, radius)
        bm.edges.new((start_v, end_v))

        # LUẬT RẼ NHÁNH: Cấp đầu tiên ép 3 nhánh, các cấp sau dùng cfg['branch_forks']
        num_forks = cfg['first_split_forks'] if depth == cfg['depth'] else cfg['branch_forks']
        
        new_length = length * cfg['length_mult']
        new_radius = radius * cfg['radius_mult']
        base_angle = random.uniform(0, math.pi * 2) 

        for i in range(num_forks):
            t_progress = (cfg['depth'] - depth) / cfg['depth']
            current_spread = cfg['spread_base'] * (1 - t_progress) + cfg['spread_top'] * t_progress
            
            # Nhánh Leader (thân vươn)
            if i == 0:
                spread_factor = cfg['leader_bias']
                child_is_leader = True
            else:
                spread_factor = current_spread
                child_is_leader = False
            
            angle = base_angle + (i * (math.pi * 2 / num_forks))
            radial_dir = Vector((math.cos(angle), math.sin(angle), 0))
            out_dir = (Vector((0, 0, 1)) * (1 - spread_factor) + radial_dir * spread_factor).normalized()
            
            grow_branch(end_v, out_dir, new_length, new_radius, depth - 1, child_is_leader)

    # --- THỰC THI DỰNG THÂN CHÍNH (Vươn cao và sinh nhánh dọc thân) ---
    root_v = bm.verts.new((0, 0, 0))
    root_v[skin_layer].radius = (0.6, 0.6)
    
    curr_trunk_v = root_v
    side_branch_count = 0
    
    for i in range(1, cfg['trunk_segs'] + 1):
        t = i / cfg['trunk_segs']
        # Thân chính vươn lên
        pos = Vector((math.sin(t*1.5)*0.1, math.cos(t*1.5)*0.05, cfg['trunk_h'] * t))
        v = bm.verts.new(pos)
        rad = 0.6 * (1.0 - t * 0.3)
        v[skin_layer].radius = (rad, rad)
        bm.edges.new((curr_trunk_v, v))
        curr_trunk_v = v
        
        # LOGIC NHÁNH DỌC THÂN: Mọc nhánh tại 40% và 70% chiều cao thân
        if cfg['trunk_side_branches'] and i in [int(cfg['trunk_segs']*0.4), int(cfg['trunk_segs']*0.7)]:
            side_branch_count += 1
            # Nhánh mọc xiên ra ngoài
            side_angle = random.uniform(0, math.pi * 2)
            side_dir = Vector((math.cos(side_angle), math.sin(side_angle), 0.5)).normalized()
            # Mọc một nhánh đơn lẻ từ vị trí này, depth thấp hơn tán chính một chút
            grow_branch(v, side_dir, 1.8, rad * 0.7, cfg['depth'] - 1, False)

    # --- TẠO TÁN CHÍNH TẠI ĐỈNH ---
    grow_branch(curr_trunk_v, Vector((0, 0, 1)), 2.0, 0.3, cfg['depth'], True)

    bm.to_mesh(mesh_data)
    bm.free()

    # MODIFIERS
    context.view_layer.objects.active = tree_obj
    skin_mod = tree_obj.modifiers.new(name="Skin", type='SKIN')
    skin_mod.branch_smoothing = 0.8
    
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    tree_obj.data.vertices[0].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.object.skin_root_mark()
    bpy.ops.object.mode_set(mode='OBJECT')

    sub_mod = tree_obj.modifiers.new(name="Subdiv", type='SUBSURF')
    sub_mod.levels = 2
    bpy.ops.object.shade_smooth()
    
    tree_obj.location = context.scene.cursor.location
    self.report({'INFO'}, f"Đã tạo cây đa điểm phân nhánh ({side_branch_count} nhánh phụ dọc thân).")

def deform_stylized_canopy(self, context, canopy_objs):
    """
    Biến dạng các khối Sphere được chọn thành tán cây Stylized (Bumpy look).
    Đảm bảo tính độc bản (Unique) cho mỗi tán cây bằng cách ngẫu nhiên hóa tọa độ Texture.
    """
    if not canopy_objs:
        return

    for obj in canopy_objs:
        if obj.type != 'MESH': continue
        
        # 1. BIẾN DẠNG KHUNG (SQUASH & STRETCH)
        # Bóp méo nhẹ hình dáng tổng thể của quả cầu
        obj.scale.x *= random.uniform(0.9, 1.1)
        obj.scale.y *= random.uniform(0.9, 1.1)
        obj.scale.z *= random.uniform(0.85, 1.05)
        
        # 2. TẠO TEXTURE NHIỄU RIÊNG BIỆT (Để đảm bảo không trùng lặp)
        tex_name = f"Tex_Canopy_{obj.name}_{random.randint(100, 999)}"
        tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
        tex.noise_scale = random.uniform(0.9, 1.4)
        tex.noise_depth = 2
            
        # 3. ÁP DỤNG DISPLACE MODIFIER VỚI TỌA ĐỘ NGẪU NHIÊN
        disp_mod = obj.modifiers.new(name="Canopy_Bumps", type='DISPLACE')
        disp_mod.texture = tex
        
        # SỬ DỤNG MAPPING 'GLOBAL' HOẶC 'OBJECT' ĐỂ TẠO SỰ KHÁC BIỆT
        # Chúng ta dùng 'LOCAL' nhưng sẽ xoay nhẹ dữ liệu mesh ngầm hoặc đổi Midlevel
        disp_mod.texture_coords = 'LOCAL'
        disp_mod.strength = random.uniform(0.4, 0.65)
        disp_mod.mid_level = random.uniform(0.45, 0.55)
        
        # 4. LÀM MƯỢT (SMOOTH)
        smooth_mod = obj.modifiers.new(name="Canopy_Smooth", type='SMOOTH')
        smooth_mod.iterations = random.randint(20, 30) # Ngẫu nhiên độ mượt
        
        # 5. LÀM MƯỢT BỀ MẶT
        context.view_layer.objects.active = obj
        bpy.ops.object.shade_smooth()

    context.view_layer.update()
    self.report({'INFO'}, f"Đã tạo {len(canopy_objs)} tán cây độc bản.")

def deform_stylized_trunk(self, context, trunk_objs):
    """
    Biến dạng trực tiếp khối trụ mesh (đã được uốn dáng) thành thân cây Stylized.
    - Làm mượt dáng uốn lượn.
    - Tạo móp méo bề mặt vỏ cây.
    - Tự động bóp dáng phình gốc thu ngọn.
    """
    if not trunk_objs: return

    for obj in trunk_objs:
        if obj.type != 'MESH': continue
        
        context.view_layer.objects.active = obj
        
        # 1. TỰ ĐỘNG PHÌNH GỐC - THU NGỌN (DỰA TRÊN TỌA ĐỘ LOCAL)
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        
        # Tìm giới hạn Z để xác định gốc và ngọn
        z_coords = [v.co.z for v in bm.verts]
        if z_coords:
            min_z = min(z_coords)
            max_z = max(z_coords)
            height = max_z - min_z
            
            if height > 0:
                for v in bm.verts:
                    # Tỉ lệ cao độ từ 0 (đáy) đến 1 (ngọn)
                    t = (v.co.z - min_z) / height
                    # Gốc phình 1.3, ngọn thu 0.4
                    f = 1.3 * (1.0 - t)**0.5 + 0.4 * t
                    v.co.x *= f
                    v.co.y *= f
        
        bm.to_mesh(obj.data)
        bm.free()

        # 2. LÀM MƯỢT DÁNG TỔNG THỂ (Gỡ bỏ sự gãy khúc nếu uốn tay)
        lap_smooth = obj.modifiers.new(name="Trunk_Relax", type='LAPLACIANSMOOTH')
        lap_smooth.iterations = 5
        lap_smooth.lambda_border = 0.5
        
        # 3. TẠO MÓP MÉO VỎ CÂY (LOGIC TÁN CÂY)
        tex_name = f"Tex_Trunk_{obj.name}_{random.randint(10, 99)}"
        tex = bpy.data.textures.new(name=tex_name, type='CLOUDS')
        tex.noise_scale = 1.3
        
        disp = obj.modifiers.new(name="Trunk_Bumps", type='DISPLACE')
        disp.texture = tex
        disp.strength = 0.15 # Móp méo nhẹ
        disp.mid_level = 0.5
        
        # 4. LÀM MƯỢT HOÀN THIỆN
        smooth = obj.modifiers.new(name="Trunk_Final_Smooth", type='SMOOTH')
        smooth.iterations = 15
        
        bpy.ops.object.shade_smooth()

    context.view_layer.update()
    self.report({'INFO'}, f"Đã hô biến {len(trunk_objs)} thân cây Stylized.")

def attach_leaves_to_canopy(self, context, leaf_samples, canopy_obj, leaf_density=1.0):
    """
    Đính lá lên tán cây với mật độ có thể điều chỉnh.
    - leaf_density: Hệ số mật độ (0.1 -> 5.0). Mặc định 1.0.
    """
    if not canopy_obj or canopy_obj.type != 'MESH' or not leaf_samples:
        return

    # 1. KHỞI TẠO DỮ LIỆU BỀ MẶT
    mw = canopy_obj.matrix_world
    depsgraph = context.view_layer.depsgraph
    eval_obj = canopy_obj.evaluated_get(depsgraph)
    mesh_data = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(mw)
    
    face_centers = [f.calc_center_median() for f in bm.faces]
    face_normals = [f.normal.copy() for f in bm.faces]
    
    # 2. THÔNG SỐ KHỐI VÀ TÍNH TOÁN SỐ LƯỢNG LÁ
    bounds = get_world_bounds(canopy_obj)
    min_z, max_z = bounds['z']
    vol_h = max_z - min_z
    
    # Ước lượng diện tích bề mặt (dựa trên BBox) để tính target_count
    area_estimate = (bounds['x'][1]-bounds['x'][0]) * (bounds['y'][1]-bounds['y'][0])
    target_leaf_count = int(area_estimate * 5 * leaf_density)
    target_leaf_count = max(5, min(target_leaf_count, 300)) # Giới hạn an toàn

    # Xáo trộn danh sách điểm
    combined = []
    for i in range(len(face_centers)):
        combined.append((face_centers[i], face_normals[i]))
    random.shuffle(combined)
    
    new_leaves = []
    # Khoảng cách tối thiểu tỉ lệ nghịch với mật độ để lá chen nhau được khi cần dày
    min_dist_base = sum(max(s.dimensions) for s in leaf_samples) / len(leaf_samples) * 0.75
    min_dist = min_dist_base / math.sqrt(leaf_density) 
    
    placed_locations = []

    # Tạm ẩn mẫu
    original_hides = {obj: obj.hide_get() for obj in leaf_samples}
    for obj in leaf_samples: obj.hide_set(True)

    # 3. THỰC HIỆN ĐÍNH LÁ
    for pos, normal in combined:
        if len(new_leaves) >= target_leaf_count:
            break
            
        z_factor = (pos.z - min_z) / vol_h if vol_h > 0 else 0.5
        # Không mọc lá ở 25% phần dưới đáy
        # if z_factor < 0.25: continue
        if z_factor < 0.15: continue

        # KIỂM TRA CHỒNG LẤP
        is_too_close = False
        for p in placed_locations:
            if (pos - p).length < min_dist:
                is_too_close = True
                break
        if is_too_close: continue
            
        # ĐẶT LÁ
        source = random.choice(leaf_samples)
        new_l = source.copy()
        new_l.data = source.data.copy()
        context.collection.objects.link(new_l)
        new_leaves.append(new_l)
        placed_locations.append(pos.copy())
        
        # --- LOGIC VỊ TRÍ: Đẩy nhẹ lá ra ngoài 1.5cm để chống lún tuyệt đối ---
        new_l.location = pos + normal * 0.015
        
        # --- LOGIC XOAY: Ma trận hướng chuẩn (X-Y-Z Alignment) ---
        leaf_up = normal.normalized()
        canopy_center = canopy_obj.location
        outward_vec = (pos - canopy_center).normalized()
        world_down = Vector((0, 0, -1))
        
        # Hướng rủ: Ưu tiên chúi xuống và hơi đẩy ra ngoài
        target_droop_dir = (world_down * 0.75 + outward_vec * 0.25).normalized()
        leaf_forward = (target_droop_dir - target_droop_dir.dot(leaf_up) * leaf_up).normalized()
        if leaf_forward.length < 0.1: leaf_forward = outward_vec
        
        z_axis = leaf_up
        y_axis = leaf_forward
        x_axis = y_axis.cross(z_axis).normalized()
        y_axis = z_axis.cross(x_axis).normalized()
        mat_base = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
        
        # --- ĐỘ VÊNH (LIFT): Luôn dương, giảm dần theo cao độ ---
        lift_angle = math.radians(10 + (1.0 - z_factor) * 35)
        lift_angle = max(math.radians(5.0), lift_angle) # TUYỆT ĐỐI KHÔNG ÂM
        
        m_lift = Matrix.Rotation(lift_angle, 4, 'X')
        m_jitter = Matrix.Rotation(math.radians(random.uniform(-15, 15)), 4, 'Z')
        
        new_l.rotation_mode = 'QUATERNION'
        new_l.rotation_quaternion = (mat_base @ m_jitter @ m_lift).to_quaternion()
        new_l.scale *= random.uniform(0.85, 1.25)

    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã đính {len(new_leaves)} lá (Density: {leaf_density}).")

    # 4. DỌN DẸP
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã hoàn thành đính {len(new_leaves)} lá (Gradient Lift applied).")

    # 4. DỌN DẸP
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
    
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã đính {len(new_leaves)} lá rủ tự nhiên.")

    # 4. DỌN DẸP
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
    
    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã đính {len(new_leaves)} lá lên tán cây.")

def generate_stylized_stream(self, context, curve_obj, ground_obj, stones, width=1.5, stone_gap=-0.1):
    """
    Tạo dòng suối Stylized bằng cách đắp 2 bờ đá dọc theo đường Curve (Fix Error: Path Sampling).
    """
    if not curve_obj or curve_obj.type != 'CURVE' or not stones:
        return

    # 1. TẠO SAMPLER ĐỂ LẤY DỮ LIỆU ĐƯỜNG CONG CHÍNH XÁC
    temp_empty = bpy.data.objects.new("Stream_Sampler", None)
    context.collection.objects.link(temp_empty)
    constraint = temp_empty.constraints.new('FOLLOW_PATH')
    constraint.target = curve_obj
    constraint.use_fixed_location = True

    def get_curve_info(factor):
        constraint.offset_factor = max(0.0, min(1.0, factor))
        context.view_layer.update()
        pos = temp_empty.matrix_world.to_translation()
        
        # Tính hướng Forward (Tangent)
        delta = 0.005
        constraint.offset_factor = max(0.0, factor - delta)
        context.view_layer.update()
        pos_prev = temp_empty.matrix_world.to_translation()
        
        forward = (pos - pos_prev).normalized()
        if forward.length < 0.001: forward = Vector((0, 1, 0))
        return pos, forward

    # 2. TÍNH CHIỀU DÀI VÀ SỐ BƯỚC
    curve_len = sum(s.calc_length() for s in curve_obj.data.splines)
    avg_stone_w = sum(s.dimensions.x for s in stones) / len(stones)
    num_steps = int(curve_len / (avg_stone_w + stone_gap))
    num_steps = max(2, num_steps)

    left_bank_pts = []
    right_bank_pts = []
    original_hides = {obj: obj.hide_get() for obj in stones}
    for obj in stones: obj.hide_set(True)

    # 3. ĐẮP BỜ ĐÁ
    for i in range(num_steps + 1):
        t = i / num_steps
        pos_world, forward = get_curve_info(t)
        
        # Véc-tơ vuông góc (Right)
        right = Vector((forward.y, -forward.x, 0)).normalized()
        
        # Biến thiên độ rộng lòng suối (Stylized jitter)
        var_width = width * (1.0 + random.uniform(-0.15, 0.15))
        
        p_left = pos_world + right * (var_width / 2)
        p_right = pos_world - right * (var_width / 2)
        
        left_bank_pts.append(p_left)
        right_bank_pts.append(p_right)
        
        # Đặt đá 2 bên
        for p, side_norm in [(p_left, right), (p_right, -right)]:
            source = random.choice(stones)
            new_s = source.copy()
            new_s.data = source.data.copy()
            context.collection.objects.link(new_s)
            
            context.view_layer.objects.active = new_s
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            
            new_s.location = p
            new_s.location.z += source.dimensions.z / 5 # Nổi nhẹ
            
            new_s.rotation_mode = 'QUATERNION'
            new_s.rotation_quaternion = side_norm.to_track_quat('Y', 'Z')
            new_s.rotation_euler.z += math.radians(random.uniform(-15, 15))
            new_s.scale *= random.uniform(0.85, 1.25)

    # 4. TẠO MẶT NƯỚC
    water_mesh = bpy.data.meshes.new("Stream_Water")
    water_obj = bpy.data.objects.new("Stylized_Water", water_mesh)
    context.collection.objects.link(water_obj)
    
    verts = []
    faces = []
    for i in range(len(left_bank_pts)):
        z_water = (left_bank_pts[i].z + right_bank_pts[i].z) / 2 + 0.01 
        verts.append((left_bank_pts[i].x, left_bank_pts[i].y, z_water))
        verts.append((right_bank_pts[i].x, right_bank_pts[i].y, z_water))
        if i > 0:
            v = i * 2
            faces.append((v-2, v-1, v+1, v))
            
    water_mesh.from_pydata(verts, [], faces)
    water_mesh.update()

    # DỌN DẸP
    bpy.data.objects.remove(temp_empty, do_unlink=True)
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
        
    context.view_layer.update()
    self.report({'INFO'}, "Đã hoàn thành suối Stylized.")

def generate_shingled_canopy(self, context, volume_obj, leaf_samples):
    """
    Tạo tán lá kiểu lợp ngói (Shingled/Layered) bám theo khối volume.
    Lá xếp tầng ngăn nắp, hàng trên gối hàng dưới.
    """
    if not volume_obj or not leaf_samples:
        return

    # 1. KHỞI TẠO BVH TREE TỪ VOLUME
    mw = volume_obj.matrix_world
    depsgraph = context.view_layer.depsgraph
    eval_obj = volume_obj.evaluated_get(depsgraph)
    mesh_data = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(mw)
    bvh = BVHTree.FromBMesh(bm)
    
    # 2. THÔNG SỐ KHỐI & LÁ
    bounds = get_world_bounds(volume_obj)
    min_z, max_z = bounds['z']
    center_v = (Vector((bounds['x'][0], bounds['y'][0], 0)) + Vector((bounds['x'][1], bounds['y'][1], 0))) / 2
    vol_h = max_z - min_z
    
    source_leaf = random.choice(leaf_samples)
    leaf_w = source_leaf.dimensions.x
    leaf_l = source_leaf.dimensions.y # Chiều dài lá (hướng ra ngoài)
    
    # Khoảng cách giữa các tầng (Tăng mật độ để khít hơn)
    layer_step = leaf_l * 0.4
    # Thêm 2 vòng để lấp đỉnh hoàn toàn
    num_layers = math.ceil(vol_h / layer_step) + 2
    
    new_leaves = []
    
    # 3. QUÉT THEO TỪNG TẦNG Z
    for l_idx in range(num_layers):
        # Nội suy vị trí Z: đảm bảo tầng cuối cùng chạm đúng đỉnh
        t_z = min(1.0, (l_idx * layer_step) / vol_h)
        curr_z = min_z + (t_z * vol_h)
        
        # Độ cao tương đối cho các thông số khác
        z_factor = t_z
        
        # --- LOGIC RỦ XUỐNG ĐỒNG BỘ ---
        tilt_deg = -45 * (1.0 - z_factor) + (-10 * z_factor)
        
        # --- SCALE GIẢM DẦN THEO ĐỘ CAO ---
        # Đáy: 1.1x, Đỉnh: 0.8x
        height_sc = 1.1 - (z_factor * 0.3)

        # Số lượng lá trên vòng tròn (Ước lượng chu vi tại tầng này)
        # Bắn 4 tia hướng chính để tìm bán kính trung bình
        test_dirs = [Vector((1,0,0)), Vector((-1,0,0)), Vector((0,1,0)), Vector((0,-1,0))]
        radius_sum = 0
        hits = 0
        for td in test_dirs:
            loc, norm, idx, dist = bvh.ray_cast(Vector((center_v.x, center_v.y, curr_z)), td)
            if loc:
                radius_sum += (loc - Vector((center_v.x, center_v.y, curr_z))).length
                hits += 1
        
        avg_r = (radius_sum / hits) if hits > 0 else 0.5
        circumference = 2 * math.pi * avg_r
        
        # Số lá = Chu vi / (Chiều rộng lá + Gap)
        num_leaves_in_ring = math.ceil(circumference / (leaf_w * 0.9))
        if num_leaves_in_ring < 3: num_leaves_in_ring = 3
        
        angle_step = (math.pi * 2) / num_leaves_in_ring
        # So le: Hàng lẻ xoay lệch nửa bước
        angle_offset = (angle_step / 2) if l_idx % 2 != 0 else 0
        
        for s_idx in range(num_leaves_in_ring):
            angle = angle_offset + (s_idx * angle_step)
            ray_dir = Vector((math.cos(angle), math.sin(angle), 0))
            ray_origin = Vector((center_v.x, center_v.y, curr_z))
            
            # Bắn tia tìm điểm đặt lá trên mặt khối
            loc, norm, idx, dist = bvh.ray_cast(ray_origin, ray_dir)
            
            if loc:
                source = random.choice(leaf_samples)
                new_l = source.copy()
                new_l.data = source.data.copy()
                context.collection.objects.link(new_l)
                new_leaves.append(new_l)
                
                new_l.location = loc
                
                # XOAY:
                # 1. Hướng Y (dài) ra ngoài theo Ray Dir
                # 2. Hướng Z (mặt dẹt) theo Normal để bám form
                # Blend Normal với Vector Up để lá nằm ngang nhiều hơn
                up_vec = Vector((0, 0, 1))
                blended_normal = (norm * 0.3 + up_vec * 0.7).normalized()
                
                q_base = ray_dir.to_track_quat('Y', 'Z')
                
                # Áp dụng Tilt (xoay quanh trục X local của lá)
                m_tilt = Matrix.Rotation(math.radians(tilt_deg), 4, 'X')
                # Random jitter nhẹ
                m_jitter = Matrix.Rotation(math.radians(random.uniform(-3, 3)), 4, 'Z')
                
                new_l.rotation_mode = 'QUATERNION'
                new_l.rotation_quaternion = (q_base.to_matrix().to_4x4() @ m_tilt @ m_jitter).to_quaternion()
                
                # SCALE: Co giãn theo độ cao + Biến thiên ngẫu nhiên chiều dài (Y)
                new_l.scale *= height_sc * random.uniform(0.9, 1.1)
                new_l.scale.y *= random.uniform(0.85, 1.2) # Jitter chiều dài tạo sự tự nhiên

    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    self.report({'INFO'}, f"Đã tạo tán lá lợp ngói: {len(new_leaves)} lá ({num_layers} tầng).")

def cut_objects_by_volume(self, context, cutter_obj, target_objs):
    """
    Cắt hàng loạt vật thể (ngói, gạch) theo khối khuôn (Cutter)
    mà không join chúng lại, sử dụng Boolean Intersect.
    """
    if not cutter_obj or not target_objs:
        self.report({'WARNING'}, "Cần chọn các vật thể mục tiêu và khối khuôn Active.")
        return

    # Tạm thời chuyển sang Object Mode nếu đang ở chế độ khác
    if context.active_object and context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')

    # Đảm bảo khối khuôn có dữ liệu mesh
    if cutter_obj.type != 'MESH':
        self.report({'ERROR'}, "Khối khuôn (Active) phải là một Mesh.")
        return

    processed_count = 0
    removed_count = 0
    
    # Ẩn khối khuôn để dễ quan sát (tùy chọn)
    # original_cutter_hide = cutter_obj.hide_viewport
    # cutter_obj.hide_viewport = True

    # Danh sách các object sẽ bị xóa nếu rỗng sau khi cắt
    to_remove = []

    for obj in target_objs:
        if obj == cutter_obj or obj.type != 'MESH':
            continue
            
        # Thêm Boolean Modifier
        bool_mod = obj.modifiers.new(name="Auto_Cut", type='BOOLEAN')
        bool_mod.operation = 'INTERSECT'
        bool_mod.object = cutter_obj
        bool_mod.solver = 'EXACT' # Sửa lỗi: Dùng EXACT cho Blender 5.0
        
        # Áp dụng (Apply) modifier
        context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)
        
        # Kiểm tra nếu mesh rỗng sau khi cắt (nằm ngoài hoàn toàn)
        if len(obj.data.vertices) == 0:
            to_remove.append(obj)
            removed_count += 1
        else:
            processed_count += 1

    # Xóa các object rỗng
    if to_remove:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in to_remove:
            obj.select_set(True)
        bpy.ops.object.delete()
    
    # Khôi phục vật thể Active ban đầu
    context.view_layer.objects.active = cutter_obj
    cutter_obj.select_set(True)

    self.report({'INFO'}, f"Đã cắt xong: {processed_count} viên giữ lại, {removed_count} viên bị loại bỏ.")

def generate_smart_bridge(self, context, curve_obj, bridge_samples):
    """
    Trải các tấm ván mẫu dọc theo đường Curve (Chỉ ván sàn).
    """
    if not curve_obj or len(bridge_samples) < 1:
        self.report({'WARNING'}, "Cần chọn ít nhất 1 mẫu ván sàn và 1 đường Curve (Active).")
        return

    deck_sample = bridge_samples[0]

    # 1. SAMPLING ĐƯỜNG CONG
    temp_empty = bpy.data.objects.new("Bridge_Sampler", None)
    context.collection.objects.link(temp_empty)
    constraint = temp_empty.constraints.new('FOLLOW_PATH')
    constraint.target = curve_obj
    constraint.use_fixed_location = True

    def get_curve_info(factor):
        constraint.offset_factor = max(0.0, min(1.0, factor))
        context.view_layer.update()
        pos = temp_empty.matrix_world.to_translation()
        
        delta = 0.005
        constraint.offset_factor = max(0.0, factor - delta)
        context.view_layer.update()
        pos_prev = temp_empty.matrix_world.to_translation()
        tangent = (pos - pos_prev).normalized()
        return pos, tangent

    # 2. PHÂN TÍCH KÍCH THƯỚC MẪU VÁN
    d_dims = deck_sample.dimensions
    # Xác định trục nào là chiều rộng (hướng đi của cầu)
    if d_dims.x < d_dims.y:
        plank_w = d_dims.x
        deck_track_axis = 'X'
    else:
        plank_w = d_dims.y
        deck_track_axis = 'Y'

    curve_len = 0
    for spline in curve_obj.data.splines: curve_len += spline.calc_length()
    
    # 3. THỰC THI TRẢI VÁN
    GAP = 0.01 # Khoảng hở 1cm
    step_deck = plank_w + GAP
    num_planks = int(curve_len / step_deck)
    if num_planks < 2: num_planks = 2
    
    for i in range(num_planks):
        factor = i / (num_planks - 1)
        pos, tan = get_curve_info(factor)
        
        new_d = deck_sample.copy()
        new_d.data = deck_sample.data.copy()
        context.collection.objects.link(new_d)
        
        new_d.location = pos
        new_d.rotation_mode = 'QUATERNION'
        # Xoay ván: Trục rộng hướng theo Curve, mặt phẳng dẹt hướng lên
        new_d.rotation_quaternion = tan.to_track_quat(deck_track_axis, 'Z')
        
        # Random nhẹ tỷ lệ cho tự nhiên
        new_d.scale.y *= random.uniform(0.95, 1.05)

    bpy.data.objects.remove(temp_empty, do_unlink=True)
    self.report({'INFO'}, f"Đã trải xong {num_planks} tấm ván dọc theo Curve.")

    bpy.data.objects.remove(temp_empty, do_unlink=True)
    self.report({'INFO'}, f"Đã hoàn thành cầu: {num_planks} ván, dầm bám sát Curve.")

    bpy.data.objects.remove(temp_empty, do_unlink=True)
    self.report({'INFO'}, f"Đã hoàn thành cầu đơn giản: {num_steps} phân đoạn.")
