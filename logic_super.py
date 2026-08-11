import bpy
import math
import random
import bmesh
from mathutils import Vector, Matrix

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

def generate_island_base_from_proxies(self, context, proxy_objs, stones, density=1.0):
    """
    Tạo đế đảo từ 9 khối Proxy chủ với hình dáng nhọn dần về đáy (Tapered & Faceted).
    """
    if not proxy_objs or not stones:
        return

    # Tạm ẩn mẫu
    original_hides = {obj: obj.hide_get() for obj in stones}
    for obj in stones: obj.hide_set(True)

    processed_count = 0

    for proxy in proxy_objs:
        if proxy.type != 'MESH': continue
        
        # 1. LẤY THÔNG SỐ KHỐI PROXY
        bounds = get_world_bounds(proxy)
        width = bounds['x'][1] - bounds['x'][0]
        length = bounds['y'][1] - bounds['y'][0]
        height = bounds['z'][1] - bounds['z'][0]
        center = Vector(((bounds['x'][0] + bounds['x'][1])/2, 
                         (bounds['y'][0] + bounds['y'][1])/2, 
                         (bounds['z'][0] + bounds['z'][1])/2))

        # 2. SINH ĐÁ CON (Số lượng ít, khối lớn, nhọn đáy)
        stone_count = int(max(3, (width * length) * 0.4 * density))
        stone_count = min(stone_count, 7) 

        for i in range(stone_count):
            source = random.choice(stones)
            new_s = source.copy()
            new_s.data = source.data.copy()
            context.collection.objects.link(new_s)
            
            # PHÂN LOẠI: Viên đầu tiên là Leader
            is_leader = (i == 0)
            
            # --- THUẬT TOÁN TAPER THỦ CÔNG ---
            if is_leader:
                bm = bmesh.new()
                bm.from_mesh(new_s.data)
                z_coords = [v.co.z for v in bm.verts]
                min_z_loc = min(z_coords)
                max_z_loc = max(z_coords)
                h_loc = max_z_loc - min_z_loc
                
                if h_loc > 0:
                    for v in bm.verts:
                        t = (v.co.z - min_z_loc) / h_loc
                        factor = 0.35 + (t * 0.65) 
                        v.co.x *= factor
                        v.co.y *= factor
                bm.to_mesh(new_s.data)
                bm.free()

            # --- CĂN CHỈNH PIVOT LÊN ĐỈNH ---
            context.view_layer.objects.active = new_s
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
            max_z_final = max(v.co.z for v in new_s.data.vertices)
            for v in new_s.data.vertices:
                v.co.z -= max_z_final
            
            # VỊ TRÍ (Cộng thêm center của Proxy)
            if is_leader:
                new_s.location = center + Vector((random.uniform(-0.05, 0.1), random.uniform(-0.05, 0.1), 0))
            else:
                new_s.location = center + Vector((
                    random.uniform(-width/2.6, width/2.6),
                    random.uniform(-length/2.6, length/2.6),
                    random.uniform(-height/4, 0)
                ))
            
            # XOAY VUÔNG VỨC
            new_s.rotation_mode = 'XYZ'
            new_s.rotation_euler.z = math.radians(random.choice([0, 90, 180, 270]))
            
            # SCALE
            if is_leader:
                new_s.scale = Vector((width/1.9, length/1.9, height * 1.1))
            else:
                sc = random.uniform(0.7, 1.1)
                new_s.scale = Vector((sc*(width/2.5), sc*(length/2.5), sc*(height/1.3)))
            
            # --- MODIFIER STYLIZED ---
            tex = bpy.data.textures.new(name=f"Rock_Noise_{new_s.name}", type='CLOUDS')
            tex.noise_scale = 1.8
            disp = new_s.modifiers.new(name="Rock_Deform", type='DISPLACE')
            disp.texture = tex
            disp.strength = 0.12 if is_leader else 0.18
            
            dec_mod = new_s.modifiers.new(name="Rock_Faceted", type='DECIMATE')
            dec_mod.ratio = 0.08 if is_leader else 0.15 
            
            bpy.ops.object.shade_flat()

        processed_count += 1

    # Khôi phục mẫu
    for obj, hidden in original_hides.items():
        obj.hide_set(hidden)
        
    context.view_layer.update()
    self.report({'INFO'}, f"Đã xây dựng đáy đảo nhọn từ {processed_count} Proxy chủ.")

def highlight_occluded_objects(self, context, objects, threshold=0.7):
    """
    Kiểm tra và highlight các vật thể bị che khuất phần lớn bởi các vật thể khác.
    - threshold: Tỉ lệ điểm bị nằm trong vật thể khác (0.0 -> 1.0).
    """
    if len(objects) < 2:
        self.report({'WARNING'}, "Vui lòng chọn ít nhất 2 vật thể để kiểm tra.")
        return

    # Chuyển Viewport sang hiển thị Object Color để thấy màu đỏ
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.color_type = 'OBJECT'

    occluded_list = []
    mesh_objs = [o for o in objects if o.type == 'MESH']

    for target in mesh_objs:
        # 1. LẤY MẪU ĐIỂM CỐ ĐỊNH (CHỐNG NGẪU NHIÊN)
        verts = target.data.vertices
        num_verts = len(verts)
        target_samples = 20
        
        # Lấy mẫu đỉnh theo bước nhảy cố định thay vì random
        step = max(1, num_verts // target_samples)
        sample_points = [target.matrix_world @ verts[i].co for i in range(0, num_verts, step)[:target_samples]]
        
        # Luôn thêm Tâm vật thể
        sample_points.append(target.matrix_world @ Vector((0,0,0)))
        
        # Thêm 8 góc Bounding Box để tăng độ chính xác khung hình
        mw = target.matrix_world
        for corner in target.bound_box:
            sample_points.append(mw @ Vector(corner))
        
        inside_count = 0
        total_samples = len(sample_points)

        # 2. KIỂM TRA TỪNG ĐIỂM MẪU
        for p_world in sample_points:
            is_inside_any = False
            for other in mesh_objs:
                if other == target: continue
                
                mw_inv = other.matrix_world.inverted()
                p_local = mw_inv @ p_world
                
                hit_count = 0
                curr_p = p_local
                ray_dir = Vector((0, 0, 1))
                
                while True:
                    hit, loc, norm, idx = other.ray_cast(curr_p + ray_dir * 0.0001, ray_dir)
                    if hit:
                        hit_count += 1
                        curr_p = loc
                    else:
                        break
                
                if (hit_count % 2) == 1: 
                    is_inside_any = True
                    break
            
            if is_inside_any:
                inside_count += 1

        # 3. ĐÁNH GIÁ VÀ HIGHLIGHT THEO CẤP ĐỘ
        occlusion_ratio = inside_count / total_samples
        
        if occlusion_ratio > 0.9:
            # CẤP ĐỘ 1: > 90% (Nguy hiểm - Đỏ rực)
            target.color = (1.0, 0.0, 0.0, 1.0)
            target.show_wire = True
            target.select_set(True)
            occluded_list.append(target)
        elif occlusion_ratio > 0.8:
            # CẤP ĐỘ 2: 80% - 90% (Nghiêm trọng - Cam)
            target.color = (1.0, 0.4, 0.0, 1.0)
            target.show_wire = True
            target.select_set(True)
            occluded_list.append(target)
        elif occlusion_ratio > 0.6:
            # CẤP ĐỘ 3: 60% - 80% (Cảnh báo - Vàng)
            target.color = (1.0, 1.0, 0.0, 1.0)
            target.show_wire = True
            target.select_set(True)
            occluded_list.append(target)
        else:
            # Bình thường
            target.color = (1.0, 1.0, 1.0, 1.0)
            target.show_wire = False
            target.select_set(False)

    self.report({'INFO'}, f"Đã phân loại {len(occluded_list)} vật thể theo cấp độ che khuất.")

def attach_vines_to_merged_island(self, context, island_obj, vine_samples, density=1.0):
    """Đính dây leo chỉ ở lớp vỏ ngoài, tuyệt đối không đâm vào trong."""
    if not island_obj or not vine_samples: return
    
    from mathutils.bvhtree import BVHTree
    depsgraph = context.view_layer.depsgraph
    eval_island = island_obj.evaluated_get(depsgraph)
    mesh_data = eval_island.to_mesh()
    bm_island = bmesh.new()
    bm_island.from_mesh(mesh_data)
    bm_island.transform(island_obj.matrix_world)
    bvh = BVHTree.FromBMesh(bm_island)

    target_count = int(12 * density)
    island_center = island_obj.location
    
    # Lọc mặt đứng lộ thiên
    vertical_faces = [f for f in bm_island.faces if abs(f.normal.z) < 0.5]
    if not vertical_faces: return

    for _ in range(target_count):
        source = random.choice(vine_samples)
        face = random.choice(vertical_faces)
        
        new_v = source.copy()
        new_v.data = source.data.copy()
        context.collection.objects.link(new_v)
        
        # Đặt gốc tại mặt đá
        pos_start = face.calc_center_median()
        new_v.location = pos_start
        
        # LOGIC CHỐNG ĐÂM XUYÊN
        for spline in new_v.data.splines:
            spline.resolution_u = 12
            for p in spline.points:
                p_world = new_v.matrix_world @ p.co.to_3d()
                
                # Bắn tia từ bên ngoài vào tâm đảo để đảm bảo chạm mặt ngoài
                outward_dir = (p_world - island_center).normalized()
                ray_origin = p_world + outward_dir * 2.0 # Đứng từ ngoài 2m
                ray_dir = -outward_dir
                
                hit_loc, hit_norm, hit_idx, hit_dist = bvh.ray_cast(ray_origin, ray_dir)
                
                if hit_loc:
                    # Ép điểm bám vào mặt ngoài + hở 0.03m để an toàn tuyệt đối
                    target_p = hit_loc + hit_norm * 0.03
                    p.co = (new_v.matrix_world.inverted() @ target_p).to_4d()
                    p.co.w = 1.0

        for spline in new_v.data.splines:
            spline.type = 'NURBS'
            spline.use_endpoint_u = True

    bm_island.free()
    eval_island.to_mesh_clear()
    self.report({'INFO'}, f"Đã đính dây leo bám mặt ngoài thành công.")

def attach_roots_to_merged_island(self, context, island_obj, root_samples, density=1.0):
    """
    Tạo rễ mọc từ các đường giao nhau (mép đá hoặc kẽ đá) và rủ thẳng xuống.
    """
    if not island_obj or not root_samples: return
    
    bm = bmesh.new()
    bm.from_mesh(island_obj.data)
    bm.transform(island_obj.matrix_world)
    
    # 1. TÌM CÁC ĐƯỜNG GIAO NHAU (CHỈ MẶT BÊN VÀ DƯỚI)
    feature_points = []
    for edge in bm.edges:
        if not edge.is_boundary and len(edge.link_faces) == 2:
            # Tính pháp tuyến trung bình của 2 mặt giao nhau
            avg_normal = (edge.link_faces[0].normal + edge.link_faces[1].normal) / 2
            
            # ĐIỀU KIỆN: Chỉ lấy mặt bên (Z thấp) hoặc mặt dưới (Z âm)
            # Loại bỏ các mặt hướng lên (Z > 0.4)
            if avg_normal.z < 0.4:
                angle = abs(edge.calc_face_angle_signed())
                if angle > 0.3: # Độ gập đủ để tạo khe/mép
                    pos = (edge.verts[0].co + edge.verts[1].co) / 2
                    feature_points.append(pos)
    
    if not feature_points:
        # Dự phòng: Lấy các mặt có normal hướng xuống hoặc ngang
        feature_points = [f.calc_center_median() for f in bm.faces if f.normal.z < 0.4]
    
    if not feature_points:
        # Nếu không tìm thấy đường giao, lấy ngẫu nhiên các mặt hông
        feature_points = [f.calc_center_median() for f in bm.faces if abs(f.normal.z) < 0.5]

    target_count = int(15 * density)
    random.shuffle(feature_points)
    new_roots = []
    placed_horiz_locations = []
    # Khoảng cách tối thiểu theo phương ngang (X, Y) để tránh mọc cụm
    min_horiz_dist = 1.0 / math.sqrt(density) 

    # 2. ĐÍNH RỄ RỦ THẲNG VÀ PHÂN BỔ ĐỀU
    for pos in feature_points:
        if len(new_roots) >= target_count:
            break
            
        # KIỂM TRA KHOẢNG CÁCH NGANG (X, Y)
        pos_horiz = Vector((pos.x, pos.y, 0))
        is_too_close = False
        for prev_p in placed_horiz_locations:
            if (pos_horiz - prev_p).length < min_horiz_dist:
                is_too_close = True
                break
        
        if is_too_close:
            continue
            
        source = random.choice(root_samples)
        new_r = source.copy()
        if source.data: new_r.data = source.data.copy()
        context.collection.objects.link(new_r)
        
        new_r.location = pos
        placed_horiz_locations.append(pos_horiz)
        
        # XOAY: Đảm bảo rễ rủ xuống dưới
        new_r.rotation_mode = 'QUATERNION'
        world_up = Vector((0, 0, 1))
        new_r.rotation_quaternion = world_up.to_track_quat('Z', 'X') 
        
        # Jitter ngẫu nhiên
        new_r.rotation_mode = 'XYZ'
        new_r.rotation_euler.x += math.radians(random.uniform(-15, 15))
        new_r.rotation_euler.y += math.radians(random.uniform(-15, 15))
        new_r.rotation_euler.z = math.radians(random.uniform(0, 360))

        new_r.scale *= random.uniform(1.0, 2.0)
        new_roots.append(new_r)

    bm.free()
    self.report({'INFO'}, f"Đã đính {len(new_roots)} rễ phân bổ đều theo phương ngang.")

def attach_minerals_to_merged_island(self, context, island_obj, mineral_samples, density=1.0):
    """Đính khoáng sản (Mesh) chỉ lên bề mặt bên ngoài của hòn đảo."""
    if not island_obj or not mineral_samples: return
    
    target_count = int(15 * density)
    new_mins = []

    mw = island_obj.matrix_world
    # Sử dụng BVH Tree để kiểm tra va chạm nhanh
    from mathutils.bvhtree import BVHTree
    depsgraph = context.view_layer.depsgraph
    eval_island = island_obj.evaluated_get(depsgraph)
    mesh_data = eval_island.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(mw)
    bvh = BVHTree.FromBMesh(bm)
    
    all_faces = list(bm.faces)
    random.shuffle(all_faces)

    attempts = 0
    while len(new_mins) < target_count and attempts < len(all_faces):
        face = all_faces[attempts]
        attempts += 1
        
        pos_world = face.calc_center_median()
        norm_world = face.normal.copy()
        
        # --- KIỂM TRA TẦM NHÌN ---
        test_origin = pos_world + norm_world * 5.0
        test_dir = -norm_world
        hit_loc, hit_norm, hit_idx, hit_dist = bvh.ray_cast(test_origin, test_dir)
        
        if hit_loc and (hit_loc - pos_world).length > 0.05:
            continue

        # --- ĐẶT KHOÁNG SẢN ---
        source = random.choice(mineral_samples)
        new_m = source.copy()
        new_m.data = source.data.copy()
        context.collection.objects.link(new_m)
        
        min_z_local = min(v.co.z for v in new_m.data.vertices)
        new_m.location = pos_world - norm_world * min_z_local * new_m.scale.z
        
        q_align = norm_world.to_track_quat('Z', 'Y')
        m_rand = Matrix.Rotation(math.radians(random.uniform(0, 360)), 4, 'Z')
        new_m.rotation_mode = 'QUATERNION'
        new_m.rotation_quaternion = (q_align.to_matrix().to_4x4() @ m_rand).to_quaternion()
        
        new_m.scale *= random.uniform(0.6, 1.2)
        new_mins.append(new_m)

    bm.free()
    eval_island.to_mesh_clear()
    self.report({'INFO'}, f"Đã đính {len(new_mins)} khoáng sản lên bề mặt ngoài.")
