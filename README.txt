    # --- CHỨC NĂNG: DÀN ĐỀU (Distribute) ---
    elif alignMethod == 'DISTRIBUTE_LINEAR':
        if len(context.selected_objects) < 3:
            print("Cần ít nhất 3 vật thể để dàn đều")
            return

        # Sắp xếp danh sách vật thể theo vị trí trên trục chỉ định
        objs = sorted(context.selected_objects, key=lambda o: getattr(o.location, direction.lower()))

        pos_start = getattr(objs[0].location, direction.lower())
        pos_end = getattr(objs[-1].location, direction.lower())

        step = (pos_end - pos_start) / (len(objs) - 1)

        for i, obj in enumerate(objs):
            setattr(obj.location, direction.lower(), pos_start + (i * step))

        print(f"Đã dàn đều {len(objs)} vật thể trên trục {direction}")
        return

    # --- CHỨC NĂNG: ĐO KHOẢNG CÁCH GIỮA 2 VẬT THỂ ---
    elif alignMethod == 'MEASURE_DISTANCE':
        objs = context.selected_objects
        if len(objs) != 2:
            print("Hãy chọn đúng 2 vật thể để đo")
            return

        v1 = objs[0].location
        v2 = objs[1].location

        if direction == 'X':
            dist = abs(v1.x - v2.x)
        elif direction == 'Y':
            dist = abs(v1.y - v2.y)
        else:
            dist = abs(v1.z - v2.z)

        # Hiển thị thông báo trên Header của Blender
        self.report({'INFO'}, f"Khoảng cách trục {direction}: {dist:.4f}m")
        return

    # --- CHỨC NĂNG: LẤY KÍCH THƯỚC BAO CỦA CỤM (Bounding Box Selection) ---
    elif alignMethod == 'GET_SELECTION_BOUNDS':
        objs = context.selected_objects
        if not objs: return

        all_coords = []
        for obj in objs:
            all_coords.extend([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])

        min_c = Vector((min(c.x for c in all_coords), min(c.y for c in all_coords), min(c.z for c in all_coords)))
        max_c = Vector((max(c.x for c in all_coords), max(c.y for c in all_coords), max(c.z for c in all_coords)))

        dims = max_c - min_c
        self.report({'INFO'}, f"Kích thước cụm - X: {dims.x:.3f}, Y: {dims.y:.3f}, Z: {dims.z:.3f}")
        return

    # --- CHỨC NĂNG: ĐỒNG BỘ XOAY VÀ TỈ LỆ ---
    elif alignMethod == 'MATCH_ROT_SCALE':
        active_obj = context.active_object
        others = [obj for obj in context.selected_objects if obj != active_obj]

        for obj in others:
            obj.rotation_euler = active_obj.rotation_euler
            obj.scale = active_obj.scale
        return

    # --- CHỨC NĂNG: NGẪU NHIÊN HÓA XOAY (Scatter) ---
    elif alignMethod == 'SCATTER_RANDOM':
        import random
        for obj in context.selected_objects:
            # Xoay ngẫu nhiên quanh trục chỉ định
            val = random.uniform(-3.14159, 3.14159)
            if direction == 'X': obj.rotation_euler.x += val
            elif direction == 'Y': obj.rotation_euler.y += val
            else: obj.rotation_euler.z += val
        return