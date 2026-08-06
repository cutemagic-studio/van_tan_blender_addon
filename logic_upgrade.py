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

def create_stylized_tree(self, context):
    """
    Tạo thân cây Stylized dùng kỹ thuật Skin Modifier để có hệ lưới tối ưu.
    - Sửa lỗi: Đảm bảo có Root Vertex và tính toán lại Skin.
    """
    # 1. TẠO MESH VÀ OBJECT MỚI
    mesh_data = bpy.data.meshes.new("StylizedTreeMesh")
    tree_obj = bpy.data.objects.new("Stylized_Tree", mesh_data)
    context.collection.objects.link(tree_obj)
    
    bm = bmesh.new()
    # Skin layer chứa thông số Radius (Bán kính) cho Skin Modifier
    skin_layer = bm.verts.layers.skin.verify()
    
    # 2. THÂN CHÍNH (Trunk)
    # Gốc cây
    v_base = bm.verts.new((0, 0, 0))
    v_base[skin_layer].radius = (1.2, 1.2) # Gốc cây rất to theo ảnh mẫu
    
    curr_v = v_base
    trunk_h = 4.5
    trunk_segs = 6
    for i in range(1, trunk_segs + 1):
        t = i / trunk_segs
        vx = random.uniform(-0.4, 0.4) * (t**2) # Cong dần về phía trên
        vy = random.uniform(-0.4, 0.4) * (t**2)
        vz = trunk_h * t
        
        next_v = bm.verts.new((vx, vy, vz))
        bm.edges.new((curr_v, next_v))
        
        # Bán kính thuôn nhỏ dần lên đỉnh thân
        rad = 1.2 * (1.0 - t * 0.5)
        next_v[skin_layer].radius = (rad, rad)
        curr_v = next_v
        
    v_trunk_top = curr_v

    # 3. BỘ RỄ (Roots) - Uốn lượn và lan rộng
    num_roots = random.randint(6, 10)
    for _ in range(num_roots):
        angle = random.uniform(0, math.pi * 2)
        root_dist = random.uniform(3.0, 5.0)
        
        r_curr = v_base
        root_segs = 4
        for i in range(1, root_segs + 1):
            t = i / root_segs
            # Rễ bò lan trên mặt đất, uốn khúc XY
            rx = math.cos(angle) * root_dist * t + random.uniform(-0.5, 0.5)
            ry = math.sin(angle) * root_dist * t + random.uniform(-0.5, 0.5)
            rz = random.uniform(-0.1, 0.1) # Hơi nhấp nhô mặt đất
            
            rv = bm.verts.new((rx, ry, rz))
            bm.edges.new((r_curr, rv))
            
            # Rễ mỏng dần ra xa nhưng vẫn đủ dày ở sát gốc
            rad_r = 0.7 * (1.0 - t * 0.85)
            rv[skin_layer].radius = (rad_r, rad_r)
            r_curr = rv

    # 4. CÀNH CÂY (Branches) - Tỏa tròn từ đỉnh
    num_branches = random.randint(4, 6)
    for _ in range(num_branches):
        angle = random.uniform(0, math.pi * 2)
        b_curr = v_trunk_top
        branch_segs = 3
        for i in range(1, branch_segs + 1):
            t = i / branch_segs
            # Cành vươn ra ngoài và lên cao
            bx = b_curr.co.x + math.cos(angle) * 2.5 * t + random.uniform(-0.5, 0.5)
            by = b_curr.co.y + math.sin(angle) * 2.5 * t + random.uniform(-0.5, 0.5)
            bz = b_curr.co.z + random.uniform(1.2, 2.5) * t
            
            bv = bm.verts.new((bx, by, bz))
            bm.edges.new((b_curr, bv))
            
            # Cành nhỏ dần về phía ngọn để gắn tán lá
            rad_b = 0.5 * (1.0 - t * 0.75)
            bv[skin_layer].radius = (rad_b, rad_b)
            b_curr = bv

    bm.to_mesh(mesh_data)
    bm.free()

    # 5. ÁP DỤNG MODIFIERS VÀ ĐẶT ROOT
    context.view_layer.objects.active = tree_obj
    
    # Skin Modifier: Chuyển khung dây thành khối
    skin_mod = tree_obj.modifiers.new(name="Skin", type='SKIN')
    
    # QUAN TRỌNG: Phải vào Edit Mode để Mark Root, nếu không Skin Modifier sẽ bị lỗi
    bpy.ops.object.mode_set(mode='EDIT')
    # Chọn đỉnh gốc (thường là đỉnh 0)
    bpy.ops.mesh.select_all(action='DESELECT')
    # Chuyển về Object mode để truy cập mesh data qua bpy
    bpy.ops.object.mode_set(mode='OBJECT')
    tree_obj.data.vertices[0].select = True
    bpy.ops.object.mode_set(mode='EDIT')
    # Đánh dấu đỉnh được chọn làm Root cho Skin
    bpy.ops.object.skin_root_mark()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Subdiv Modifier: Làm mịn
    sub_mod = tree_obj.modifiers.new(name="Subdiv", type='SUBSURF')
    sub_mod.levels = 2
    
    # Shade Smooth
    bpy.ops.object.shade_smooth()
    
    # Di chuyển về 3D Cursor
    tree_obj.location = context.scene.cursor.location
    
    self.report({'INFO'}, "Đã tạo thân cây Stylized với hệ lưới tối ưu (Skin + Subdiv).")
