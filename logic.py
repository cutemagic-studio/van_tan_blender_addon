import bpy
from mathutils import Vector
from .functions import object_tools

def get_world_dimensions(obj):
    """Lấy kích thước thực tế của Object trong World Space"""
    if not obj or obj.type == 'GPENCIL':
        return Vector((0.0, 0.0, 0.0))
    
    bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    min_coords = Vector((min(c[0] for c in bbox_world), 
                         min(c[1] for c in bbox_world), 
                         min(c[2] for c in bbox_world)))
    max_coords = Vector((max(c[0] for c in bbox_world), 
                         max(c[1] for c in bbox_world), 
                         max(c[2] for c in bbox_world)))
    
    return max_coords - min_coords


def arrange_objects_grid(context, config, direction='X++', is_make_lastest_create = False):
    """
    Sắp xếp các object theo dạng lưới 3D thông minh (Cố định bước nhảy).
    """

    active_obj = context.active_object
    selected_objs = context.selected_objects

    if not active_obj or len(selected_objs) < 2:
        return

    # TẠO DANH SÁCH MỚI: Đưa Active Object lên đầu, các cái còn lại xếp sau
    objs = [active_obj]
    for obj in selected_objs:
        if obj != active_obj:
            objs.append(obj)

    print(f"Bắt đầu sắp xếp hướng: {direction}")

    # Lấy object đầu tiên làm mốc vị trí (Gốc của ngăn xếp) 
    origin_loc = Vector(objs[0].location)
    
    # Tính toán kích thước lớn nhất để làm "ô lưới"
    max_dims = Vector((0, 0, 0))
    for obj in objs:
        d = get_world_dimensions(obj)
        if d.x > max_dims.x: max_dims.x = d.x
        if d.y > max_dims.y: max_dims.y = d.y
        if d.z > max_dims.z: max_dims.z = d.z

    # Khoảng cách bước nhảy
    step_x = max_dims.x + config.spacing
    step_y = max_dims.y + config.spacing
    step_z = max_dims.z + config.spacing

    if direction == '+X++' or direction == '-Y--':

        # Khoảng cách bước nhảy
        step_x = max_dims.x + config.spacing_xy_axis
        step_y = max_dims.y + config.spacing_xy_axis
        step_z = max_dims.z + config.spacing_xy_axis

        for i, obj in enumerate(objs):
            if i == 0: continue # Giữ nguyên vị trí object đầu tiên
            
            # Tọa độ lưới dựa trên số lượng tối đa
            grid_primary = i % config.max_per_row_xy_axis
            grid_secondary = (i // config.max_per_row_xy_axis) % config.max_per_col_xy_axis
            grid_tertiary = i // (config.max_per_row_xy_axis * config.max_per_col_xy_axis)
            
            offset = Vector((0, 0, 0))

            # --- PHÂN TÍCH HƯỚNG ---
            if direction == '+X++':
                offset.x = grid_primary * step_x
                offset.y = -grid_secondary * step_y # Ưu tiên hàng X, cột lùi Y-
                offset.z = grid_tertiary * step_z   # Tầng cao Z+
                
            elif direction == '-Y--':
                offset.y = -grid_primary * step_y   # Ưu tiên lùi Y-
                offset.x = grid_secondary * step_x  # Cột tiến X+
                offset.z = grid_tertiary * step_z   # Tầng cao Z+ 

            # Áp dụng vị trí
            obj.location = origin_loc + offset

            # Căn lề đáy (Align to bottom)
            if config.align_to_bottom:
                current_dims = get_world_dimensions(obj)
                # Nếu origin ở giữa, ta phải bù trừ để đáy các object nằm trên cùng mặt phẳng
                # Object đầu tiên là mốc, nên ta căn theo vị trí tương đối của nó
                # (Phần này bạn có thể viết thêm tùy vào vị trí Origin thực tế của Model)
                pass

            print(f"Object {obj.name}: {obj.location}")

            if is_make_lastest_create == True and i == (len(objs) - 1):
                obj["CMC_IsLastestCreate"] = True
                object_tools.set_as_unique_anchor(context, obj)

    elif direction == '+Z++' or direction == '-Z--':
        # Khoảng cách bước nhảy
        step_x = max_dims.x + config.spacing_z_axis
        step_y = max_dims.y + config.spacing_z_axis
        step_z = max_dims.z + config.spacing_z_axis

        for i, obj in enumerate(objs):
            if i == 0: continue # Giữ nguyên vị trí object đầu tiên
            
            # Tọa độ lưới dựa trên số lượng tối đa
            grid_primary = i % config.max_per_row_z_axis
            grid_secondary = (i // config.max_per_row_z_axis) % config.max_per_col_z_axis
            grid_tertiary = i // (config.max_per_row_z_axis * config.max_per_col_z_axis)
            
            offset = Vector((0, 0, 0))

            # --- PHÂN TÍCH HƯỚNG ---
            if direction == '+Z++':
                offset.z = grid_primary * step_z    # Ưu tiên chồng cao Z+
                offset.x = grid_secondary * step_x  # Hàng tiến X+
                offset.y = -grid_tertiary * step_y  # Cột lùi Y-

            elif direction == '-Z--':
                offset.z = -grid_primary * step_z   # Ưu tiên hạ thấp Z-
                offset.x = grid_secondary * step_x  # Hàng tiến X+
                offset.y = -grid_tertiary * step_y  # Cột lùi Y-

            # Áp dụng vị trí
            obj.location = origin_loc + offset

            # Căn lề đáy (Align to bottom)
            if config.align_to_bottom:
                current_dims = get_world_dimensions(obj)
                # Nếu origin ở giữa, ta phải bù trừ để đáy các object nằm trên cùng mặt phẳng
                # Object đầu tiên là mốc, nên ta căn theo vị trí tương đối của nó
                # (Phần này bạn có thể viết thêm tùy vào vị trí Origin thực tế của Model)
                pass
 
            print(f"Object {obj.name}: {obj.location}")

    # Sắp Xếp Thành Lưới Đứng
    elif direction == 'REARRANGE_INTO_GRID':
        # Khoảng cách bước nhảy
        step_x = max_dims.x + config.spacing_standing_grid
        step_y = max_dims.y + config.spacing_standing_grid
        step_z = max_dims.z + config.spacing_standing_grid

        for i, obj in enumerate(objs):
            if i == 0: continue # Giữ nguyên vị trí object đầu tiên 
            
            # Tọa độ lưới dựa trên số lượng tối đa 
            # grid_primary = i % config.max_per_row_standing_grid
            # grid_secondary = (i // config.max_per_row_standing_grid) % config.max_per_col_standing_grid
            # grid_tertiary = i // (config.max_per_row_standing_grid * config.max_per_col_standing_grid)
            
            offset = Vector((0, 0, 0))

            # --- PHÂN TÍCH HƯỚNG ---
            # 1. Trái qua Phải (Trục X dương)
            offset.x = (i % config.max_per_row_standing_grid) * step_x
            
            # 2. Trên xuống Dưới (Trục Z âm)
            # Dùng max_per_row để biết khi nào thì "xuống hàng"
            offset.z = -(i // config.max_per_row_standing_grid) * step_z
            
            # 3. Nếu muốn có thêm chiều sâu (độ dày của khối lưới)
            # Ta dùng max_per_col để biết khi nào nhảy sang lớp Y mới
            offset.y = -(i // (config.max_per_row_standing_grid * config.max_per_col_standing_grid)) * step_y
            
            print("Áp dụng hệ lưới đứng: Trái -> Phải, Trên -> Xuống")

            # Áp dụng vị trí
            obj.location = origin_loc + offset