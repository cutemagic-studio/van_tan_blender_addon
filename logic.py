import bpy
from mathutils import Vector

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

def arrange_objects_grid(obj_list, config, direction='X++'):
    """
    Sắp xếp các object theo dạng lưới 3D thông minh.
    """
    if not obj_list:
        return

    print(f"{direction}")

    # Lấy object đầu tiên làm mốc vị trí (Gốc của ngăn xếp) 
    origin_loc = Vector(obj_list[0].location)
    
    # Biến lưu trữ kích thước lớn nhất của từng hàng/cột để tránh đè lên nhau
    # (Hữu ích khi các object có kích thước không đồng đều)
    max_dims = Vector((0, 0, 0))
    for obj in obj_list:
        d = get_world_dimensions(obj)
        if d.x > max_dims.x: max_dims.x = d.x
        if d.y > max_dims.y: max_dims.y = d.y
        if d.z > max_dims.z: max_dims.z = d.z

    # Khoảng cách bước nhảy (Kích thước lớn nhất + Padding)
    step_x = max_dims.x + config.spacing
    step_y = max_dims.y + config.spacing
    step_z = max_dims.z + config.spacing

    for i, obj in enumerate(obj_list):
        if i == 0: continue # Giữ nguyên vị trí object đầu tiên
        
        # Tính toán tọa độ lưới (Grid Coordinates)
        # Giả sử chúng ta ưu tiên lấp đầy Hàng (X) -> Cột (Y) -> Tầng (Z)
        grid_x = i % config.max_per_row
        grid_y = (i // config.max_per_row) % config.max_per_col
        grid_z = i // (config.max_per_row * config.max_per_col)
        
        offset = Vector((0, 0, 0))

        # Áp dụng hướng di chuyển dựa trên direction
        if direction == '+X++':
            offset.x = grid_x * step_x
            offset.y = -grid_y * step_y # -Y-- theo giao diện của bạn
            offset.z = grid_z * step_z
            print("Áp dụng hướng di chuyển +X++")
            
        elif direction == '-Y--':
            offset.y = -grid_x * step_y
            offset.x = grid_y * step_x
            offset.z = grid_z * step_z
            print("Áp dụng hướng di chuyển -Y--")

        # Cập nhật vị trí mới 
        obj.location = origin_loc + offset

        print(f"{obj.location.x}x{obj.location.y}x{obj.location.z}")

        # Căn lề đáy (Align to bottom) nếu config yêu cầu
        if config.align_to_bottom:
            current_dims = get_world_dimensions(obj)
            # Đẩy object lên một khoảng bằng nửa chiều cao của nó để "chạm sàn"
            # (Lưu ý: Cách này giả định Origin nằm ở tâm hình học)
            # Nếu origin ở đáy sẵn thì không cần dòng này.
            pass