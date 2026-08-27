import bpy
import math
import random
import bmesh
from . import logic_upgrade
from . import logic_super
from . import logic_high_upgrade
from mathutils import Vector, Quaternion, Matrix
from mathutils.bvhtree import BVHTree
from .functions import object_tools

# Xóa bỏ các dòng import math hay Vector ở giữa file hoặc trong hàm

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

    selected_objs = sorted(selected_objs, key=lambda obj: obj.location.x)

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


def arrange_only(self, context, config, direction='Z', alignMethod='CENTER_BETWEEN'):
    print("alignMethod - {alignMethod}")

    if alignMethod == 'CENTER_BETWEEN':
        if len(context.selected_objects) != 3:
            print("Cần chọn đúng 3 vật thể: A, B và C (C là vật thể Active sẽ nhảy vào giữa)")
            return

        # C là vật thể đang active (được chọn cuối cùng)
        obj_c = context.active_object
        # Hai vật thể còn lại là A và B
        others = [obj for obj in context.selected_objects if obj != obj_c]

        obj_a = others[0]
        obj_b = others[1]

        if direction == 'Z':
            # Công thức trung điểm: (Vị trí A + Vị trí B) / 2
            # Nó tự động xử lý mọi trường hợp âm/dương, trên/dưới
            midpoint_z = (obj_a.location.z + obj_b.location.z) / 2
            obj_c.location.z = midpoint_z

            print(f"Centered {obj_c.name} between {obj_a.name} and {obj_b.name} at Z: {midpoint_z}")
            return

        elif direction == 'X':
            midpoint_x = (obj_a.location.x + obj_b.location.x) / 2
            obj_c.location.x = midpoint_x
            return

        elif direction == 'Y':
            midpoint_y = (obj_a.location.y + obj_b.location.y) / 2
            obj_c.location.y = midpoint_y
            return

    elif alignMethod == 'ARRAY_BY_DISTANCE':
        if len(context.selected_objects) != 3:
            print("Cần chọn đúng 3 vật thể: A (gốc), B (bước) và C (Active)")
            return

        obj_c = context.active_object
        others = [obj for obj in context.selected_objects if obj != obj_c]

        loc_c = obj_c.location

        if direction == 'Z':
            # 1. Xác định A và B (A xa C nhất, B nằm giữa)
            others.sort(key=lambda obj: abs(obj.location.z - loc_c.z), reverse=True)
            obj_a = others[0]
            obj_b = others[1]

            # 2. Áp dụng bước nhảy trên trục Z
            step_z = obj_b.location.z - obj_a.location.z
            obj_c.location.z = obj_b.location.z + step_z

            # 3. ĐỒNG BỘ 2 TRỤC CÒI LẠI (X, Y) theo vật thể B
            obj_c.location.x = obj_b.location.x
            obj_c.location.y = obj_b.location.y

            print(f"Step Z Applied & Synced XY to {obj_b.name}")

        elif direction == 'X':
            # 1. Xác định A và B trên trục X
            others.sort(key=lambda obj: abs(obj.location.x - loc_c.x), reverse=True)
            obj_a, obj_b = others[0], others[1]

            # 2. Áp dụng bước nhảy trên trục X
            step_x = obj_b.location.x - obj_a.location.x
            obj_c.location.x = obj_b.location.x + step_x

            # 3. ĐỒNG BỘ 2 TRỤC CÒN LẠI (Y, Z) theo vật thể B
            obj_c.location.y = obj_b.location.y
            obj_c.location.z = obj_b.location.z

            print(f"Step X Applied & Synced YZ to {obj_b.name}")

        elif direction == 'Y':
            # 1. Xác định A và B trên trục Y
            others.sort(key=lambda obj: abs(obj.location.y - loc_c.y), reverse=True)
            obj_a, obj_b = others[0], others[1]

            # 2. Áp dụng bước nhảy trên trục Y
            step_y = obj_b.location.y - obj_a.location.y
            obj_c.location.y = obj_b.location.y + step_y

            # 3. ĐỒNG BỘ 2 TRỤC CÒN LẠI (X, Z) theo vật thể B
            obj_c.location.x = obj_b.location.x
            obj_c.location.z = obj_b.location.z

            print(f"Step Y Applied & Synced XZ to {obj_b.name}")

        return

    elif alignMethod == 'ALIGN_KEEP':
        print('ALIGN_KEEP')
        # if len(context.selected_objects) < 2:
        #     print("Cần chọn ít nhất 1 vật thể mục tiêu và 1 vật thể Active")
        #     return

        # C là vật thể đang active (được chọn cuối cùng) - Vật thể sẽ di chuyển
        obj_c = context.active_object

        # Lấy vật thể mục tiêu (Thằng đầu tiên trong danh sách chọn mà không phải là C)
        others = [obj for obj in context.selected_objects if obj != obj_c]
        target = others[0]

        if direction == 'Z':
            print('ALIGN_KEEP - Z')
            # Giữ Z của C, đồng bộ X và Y theo Target
            obj_c.location.x = target.location.x
            obj_c.location.y = target.location.y
            print(f"Snap XY: {obj_c.name} -> {target.name} (Keep Z)")

        elif direction == 'X':
            print('ALIGN_KEEP - X')
            # Giữ X của C, đồng bộ Y và Z theo Target
            obj_c.location.y = target.location.y
            obj_c.location.z = target.location.z
            print(f"Snap YZ: {obj_c.name} -> {target.name} (Keep X)")

        elif direction == 'Y':
            print('ALIGN_KEEP - Y')
            # Giữ Y của C, đồng bộ X và Z theo Target
            obj_c.location.x = target.location.x
            obj_c.location.z = target.location.z
            print(f"Snap XZ: {obj_c.name} -> {target.name} (Keep Y)")

        return

    # --- CHỨC NĂNG: KHỚP TỌA ĐỘ TRỤC (Match Axis) ---
    elif alignMethod == 'MATCH_TRANSFORM':
        if len(context.selected_objects) < 2:
            print("Cần ít nhất 2 vật thể để khớp tọa độ")
            return

        # Lấy vật thể chọn cuối cùng (Active) làm mốc
        active_obj = context.active_object
        # Danh sách các vật thể cần được căn chỉnh (không bao gồm chính nó)
        others = [obj for obj in context.selected_objects if obj != active_obj]

        for obj in others:
            if direction == 'X':
                # Ép tọa độ X của các vật thể khác bằng với Active Object
                obj.location.x = active_obj.location.x
            elif direction == 'Y':
                # Ép tọa độ Y của các vật thể khác bằng với Active Object
                obj.location.y = active_obj.location.y
            elif direction == 'Z':
                # Ép tọa độ Z của các vật thể khác bằng với Active Object
                obj.location.z = active_obj.location.z

        print(f"Đã khớp {len(others)} vật thể theo trục {direction} của {active_obj.name}")
        return

    elif alignMethod == 'RIGHT_ISOSCELES_TRIANGLE':
        if len(context.selected_objects) != 3:
            print("Cần chọn đúng 3 vật thể: A, C và B (Vật thể Active chọn cuối là đỉnh Góc Vuông)")
            return

        # 1. XÁC ĐỊNH VAI TRÒ
        # obj_b (Active) là đỉnh góc vuông, đứng yên để 2 đỉnh kia theo nó
        obj_b = context.active_object
        others = [obj for obj in context.selected_objects if obj != obj_b]
        obj_a = others[0]
        obj_c = others[1]

        # 2. PHẲNG HÓA (FLATTEN) THEO ĐỈNH B
        # Theo yêu cầu: Direction nào thì trục tương ứng của A và C phải bằng B
        if direction == 'X':
            # Phẳng hóa trên mặt ZOx (Y cố định theo B)
            obj_a.location.y = obj_c.location.y = obj_b.location.y
        elif direction == 'Y':
            # Phẳng hóa trên mặt YZ (X cố định theo B)
            obj_a.location.x = obj_c.location.x = obj_b.location.x
        elif direction == 'Z':
            # Phẳng hóa trên mặt XY (Z cố định theo B)
            obj_a.location.z = obj_c.location.z = obj_b.location.z

        # 3. TÍNH ĐỘ DÀI CẠNH CHUẨN (Cạnh AB hiện tại)
        dist = (obj_a.location - obj_b.location).length
        if dist < 0.001: dist = 1.0 # Tránh lỗi trùng điểm

        # 4. TẠO TAM GIÁC VUÔNG CÂN TẠI B
        if direction == 'Z':
            # Mặt phẳng XY: Cạnh 1 dọc X, Cạnh 2 dọc Y
            # Đỉnh A: Snap Y về B, đẩy X ra
            side_a = 1 if obj_a.location.x >= obj_b.location.x else -1
            obj_a.location.x = obj_b.location.x + (dist * side_a)
            obj_a.location.y = obj_b.location.y

            # Đỉnh C: Snap X về B, đẩy Y ra
            side_c = 1 if obj_c.location.y >= obj_b.location.y else -1
            obj_c.location.y = obj_b.location.y + (dist * side_c)
            obj_c.location.x = obj_b.location.x

        elif direction == 'X':
            # Mặt phẳng XZ (Y cố định): Cạnh 1 dọc X, Cạnh 2 dọc Z
            # Đỉnh A: Snap Z về B, đẩy X ra
            side_a = 1 if obj_a.location.x >= obj_b.location.x else -1
            obj_a.location.x = obj_b.location.x + (dist * side_a)
            obj_a.location.z = obj_b.location.z

            # Đỉnh C: Snap X về B, đẩy Z ra
            side_c = 1 if obj_c.location.z >= obj_b.location.z else -1
            obj_c.location.z = obj_b.location.z + (dist * side_c)
            obj_c.location.x = obj_b.location.x

        elif direction == 'Y':
            # Mặt phẳng YZ (X cố định): Cạnh 1 dọc Y, Cạnh 2 dọc Z
            # Đỉnh A: Snap Z về B, đẩy Y ra
            side_a = 1 if obj_a.location.y >= obj_b.location.y else -1
            obj_a.location.y = obj_b.location.y + (dist * side_a)
            obj_a.location.z = obj_b.location.z

            # Đỉnh C: Snap Y về B, đẩy Z ra
            side_c = 1 if obj_c.location.z >= obj_b.location.z else -1
            obj_c.location.z = obj_b.location.z + (dist * side_c)
            obj_c.location.y = obj_b.location.y

        print(f"Triangle Created: {obj_b.name} is Corner. Sides = {dist:.3f}")
        return

        # --- CHỨC NĂNG OPPOSITE (Đối xứng qua Active Object) ---
    elif alignMethod == 'OPPOSITE':
        if len(context.selected_objects) < 2:
            print("Cần chọn ít nhất 2 vật thể (A và B Active)")
            return

        obj_b = context.active_object
        # Lấy tất cả các vật thể được chọn ngoại trừ B
        others = [obj for obj in context.selected_objects if obj != obj_b]

        for obj_a in others:
            if direction == 'X':
                # Khoảng cách từ A đến B trên trục X
                diff_x = obj_b.location.x - obj_a.location.x
                # Nhảy sang phía đối diện: B + diff_x
                obj_a.location.x = obj_b.location.x + diff_x
                obj_a.location.y = obj_b.location.y

            elif direction == 'Y':
                diff_y = obj_b.location.y - obj_a.location.y
                obj_a.location.y = obj_b.location.y + diff_y
                obj_a.location.x = obj_b.location.x

            elif direction == 'Z':
                diff_z = obj_b.location.z - obj_a.location.z
                obj_a.location.z = obj_b.location.z + diff_z


        return
#
    elif alignMethod == 'OPPOSITE_NOT_FLATTEN':
        if len(context.selected_objects) < 2:
            print("Cần chọn ít nhất 2 vật thể (A và B Active)")
            return

        obj_b = context.active_object
        # Lấy tất cả các vật thể được chọn ngoại trừ B
        others = [obj for obj in context.selected_objects if obj != obj_b]

        for obj_a in others:
            if direction == 'X':
                # Khoảng cách từ A đến B trên trục X
                diff_x = obj_b.location.x - obj_a.location.x
                # Nhảy sang phía đối diện: B + diff_x
                obj_a.location.x = obj_b.location.x + diff_x


            elif direction == 'Y':
                diff_y = obj_b.location.y - obj_a.location.y
                obj_a.location.y = obj_b.location.y + diff_y


            elif direction == 'Z':
                diff_z = obj_b.location.z - obj_a.location.z
                obj_a.location.z = obj_b.location.z + diff_z


        return

    # --- CHỨC NĂNG RESET TO ZERO (Dịch chuyển cả cụm sao cho Active Object về 0) ---
    elif alignMethod == 'RESET_TO_ZERO_BASE_ACTIVE':
        if not context.active_object:
            print("Cần có một vật thể Active")
            return

        obj_active = context.active_object

        # Xác định khoảng dịch chuyển (Offset) dựa trên vị trí của vật thể Active
        offset = 0

        if direction == 'X':
            # Offset âm của vị trí hiện tại sẽ đưa nó về 0
            offset = -obj_active.location.x
            for obj in context.selected_objects:
                obj.location.x += offset
            print(f"Toàn bộ cụm đã dịch chuyển {offset:.3f} trên trục X để {obj_active.name} về 0")

        elif direction == 'Y':
            offset = -obj_active.location.y
            for obj in context.selected_objects:
                obj.location.y += offset
            print(f"Toàn bộ cụm đã dịch chuyển {offset:.3f} trên trục Y để {obj_active.name} về 0")

        elif direction == 'Z':
            offset = -obj_active.location.z
            for obj in context.selected_objects:
                obj.location.z += offset
            print(f"Toàn bộ cụm đã dịch chuyển {offset:.3f} trên trục Z để {obj_active.name} về 0")

        return

        # --- CHỨC NĂNG RESET TO ZERO (Ép từng vật thể về 0 trên trục chỉ định) ---
    elif alignMethod == 'RESET_TO_ZERO':
        if not context.selected_objects:
            print("Không có vật thể nào được chọn")
            return

        for obj in context.selected_objects:
            if direction == 'X':
                obj.location.x = 0
            elif direction == 'Y':
                obj.location.y = 0
            elif direction == 'Z':
                obj.location.z = 0

        print(f"Đã đưa {len(context.selected_objects)} vật thể về 0 trên trục {direction}")
        return

    # --- CHỨC NĂNG: HÍT NHAU THEO MÉP (Snap to Bounds) ---
    elif alignMethod == 'SNAP_TO_BOUNDS':
        if len(context.selected_objects) < 2:
            print("Cần ít nhất 2 vật thể: A và B (Active)")
            return

        obj_b = context.active_object
        others = [obj for obj in context.selected_objects if obj != obj_b]

        # Lấy giới hạn (mép) của vật thể mốc B
        bounds_b = get_world_bounds(obj_b)

        for obj_a in others:
            bounds_a = get_world_bounds(obj_a)

            if direction == 'X':
                # Nếu A đang ở bên phải B -> Hít mép trái A vào mép phải B
                if obj_a.location.x > obj_b.location.x:
                    offset = bounds_b['x'][1] - bounds_a['x'][0]
                # Nếu A đang ở bên trái B -> Hít mép phải A vào mép trái B
                else:
                    offset = bounds_b['x'][0] - bounds_a['x'][1]
                obj_a.location.x += offset

            elif direction == 'Y':
                # Nếu A đang ở phía trước B -> Hít mép sau A vào mép trước B
                if obj_a.location.y > obj_b.location.y:
                    offset = bounds_b['y'][1] - bounds_a['y'][0]
                # Nếu A đang ở phía sau B -> Hít mép trước A vào mép sau B
                else:
                    offset = bounds_b['y'][0] - bounds_a['y'][1]
                obj_a.location.y += offset

            elif direction == 'Z':
                # Nếu A đang ở trên B -> Hít đáy A vào đỉnh B
                if obj_a.location.z > obj_b.location.z:
                    offset = bounds_b['z'][1] - bounds_a['z'][0]
                # Nếu A đang ở dưới B -> Hít đỉnh A vào đáy B
                else:
                    offset = bounds_b['z'][0] - bounds_a['z'][1]
                obj_a.location.z += offset

        return

        # --- CHỨC NĂNG: TRƯỢT VÀ CĂN GIỮA MẶT ĐÍCH (Align to Face Center - No Rotation) ---
    elif alignMethod == 'ALIGN_TO_SURFACE':
        if len(context.selected_objects) < 2:
            print("Chọn các vật thể con và vật thể đích (Active) cuối cùng")
            return

        active_obj = context.active_object
        others = [obj for obj in context.selected_objects if obj != active_obj]
        depsgraph = context.view_layer.depsgraph

        # 1. Tạm ẩn để tia Raycast không đâm trúng chính vật thể con
        original_hides = {obj: obj.hide_get() for obj in others}
        for obj in others: obj.hide_set(True)
        context.view_layer.update()

        try:
            for obj in others:
                # 2. Xác định hướng trượt dựa trên trục UI
                if direction == 'X':
                    side = 1 if active_obj.location.x > obj.location.x else -1
                    ray_dir = Vector((side, 0, 0))
                elif direction == 'Y':
                    side = 1 if active_obj.location.y > obj.location.y else -1
                    ray_dir = Vector((0, side, 0))
                else: # Trục Z
                    side = 1 if active_obj.location.z > obj.location.z else -1
                    ray_dir = Vector((0, 0, side))

                # 3. Bắn tia tìm điểm chạm trên mặt phẳng đích
                success, hit_loc, normal, index, hit_obj, matrix = context.scene.ray_cast(
                    depsgraph, obj.location, ray_dir
                )

                # Dự phòng: Bắn về tâm nếu bắn trục không trúng
                if not success or hit_obj != active_obj:
                    ray_dir_back = (active_obj.location - obj.location).normalized()
                    success, hit_loc, normal, index, hit_obj, matrix = context.scene.ray_cast(
                        depsgraph, obj.location, ray_dir_back
                    )

                if success and hit_obj == active_obj:
                    # 4. THIẾT LẬP VỊ TRÍ (Căn giữa mặt)
                    # Giữ nguyên Rotation hiện tại của vật thể con

                    if direction == 'X':
                        # Trượt X đến mặt, nhưng Y và Z lấy theo tâm của vật thể đích
                        obj.location.x = hit_loc.x
                        obj.location.y = active_obj.location.y
                        obj.location.z = active_obj.location.z
                    elif direction == 'Y':
                        # Trượt Y đến mặt, nhưng X và Z lấy theo tâm của vật thể đích
                        obj.location.y = hit_loc.y
                        obj.location.x = active_obj.location.x
                        obj.location.z = active_obj.location.z
                    else: # Z
                        # Trượt Z đến mặt, nhưng X và Y lấy theo tâm của vật thể đích
                        obj.location.z = hit_loc.z
                        obj.location.x = active_obj.location.x
                        obj.location.y = active_obj.location.y

        finally:
            for obj, hidden in original_hides.items():
                obj.hide_set(hidden)
            context.view_layer.update()

        print(f"Đã đưa {len(others)} vật thể về chính giữa mặt {direction} của {active_obj.name}")
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

    # --- CHỨC NĂNG: CO GIÃN ĐỒNG NHẤT (Fit Uniform - No Distortion) ---
    elif alignMethod == 'FIT_UNIFORM':
        active_obj = context.active_object
        others = [obj for obj in context.selected_objects if obj != active_obj]

        if not active_obj or not others:
            return

        # 1. Lấy kích thước mục tiêu (Box đích)
        # Dimensions của Blender trả về kích thước thực sau Scale
        target_dim = active_obj.dimensions

        for obj in others:
            # 2. Tính toán tỉ lệ (Ratio) cho từng trục
            # Tránh chia cho 0 nếu object không có bề dày
            curr_dim = obj.dimensions

            ratios = []
            if curr_dim.x > 0: ratios.append(target_dim.x / curr_dim.x)
            if curr_dim.y > 0: ratios.append(target_dim.y / curr_dim.y)
            if curr_dim.z > 0: ratios.append(target_dim.z / curr_dim.z)

            if not ratios: continue

            # 3. CHÌA KHÓA: Lấy tỉ lệ NHỎ NHẤT (min)
            # Để đảm bảo sau khi scale, không có trục nào vượt quá Box đích
            fit_ratio = min(ratios)

            # 4. Áp dụng scale đồng nhất lên cả 3 trục của vật thể con
            obj.scale *= fit_ratio

            # Cập nhật lại view layer để Blender tính toán lại ma trận vị trí mới
            context.view_layer.update()

            # 5. ĐƯA VÀO CHÍNH GIỮA (Center Align)
            # Sau khi scale xong, ta thường muốn vật thể nằm gọn ở giữa Box
            obj.location = active_obj.location

            # Nếu bạn muốn vật thể nằm "chạm đáy" Box đích thay vì ở giữa:
            # z_offset = (target_dim.z - obj.dimensions.z) / 2
            # obj.location.z -= z_offset

        self.report({'INFO'}, f"Đã Fit đồng nhất {len(others)} vật thể vào {active_obj.name}")
        return

    # --- CHỨC NĂNG: SCALE LẤP ĐẦY KHOẢNG TRỐNG (Stretch to Fit Gap) ---
    elif alignMethod == 'STRETCH_TO_FIT_GAP':
        if len(context.selected_objects) != 3:
            self.report({'WARNING'}, "Chọn đúng 3 vật thể (Vật thể ở giữa cần scale là Active)")
            return

        active_obj = context.active_object
        others = [obj for obj in context.selected_objects if obj != active_obj]

        # Xác định chỉ số trục: X=0, Y=1, Z=2
        axis_idx = 0 if direction == 'X' else 1 if direction == 'Y' else 2
        axis_key = direction.lower()

        # 1. Sắp xếp 2 vật thể còn lại theo vị trí trên trục để biết bên nào trái, bên nào phải
        others_sorted = sorted(others, key=lambda o: o.location[axis_idx])
        obj_low = others_sorted[0]   # Vật thể có tọa độ thấp hơn
        obj_high = others_sorted[1]  # Vật thể có tọa độ cao hơn

        # 2. Lấy Bounds của 2 vật thể rìa
        bounds_low = get_world_bounds(obj_low)
        bounds_high = get_world_bounds(obj_high)

        # 3. Tìm tọa độ "mép trong"
        # Mép trong của vật thấp là Max của nó, mép trong của vật cao là Min của nó
        inner_min = bounds_low[axis_key][1]
        inner_max = bounds_high[axis_key][0]

        target_width = inner_max - inner_min

        if target_width <= 0:
            self.report({'ERROR'}, "Không có khoảng trống giữa 2 vật thể rìa trên trục này")
            return

        # 4. Tính toán Scale
        # Lưu ý: Blender dùng dimensions để tính kích thước thực tế (đã bao gồm scale)
        current_width = active_obj.dimensions[axis_idx]

        if current_width > 0:
            # Tính tỉ lệ cần bù vào scale hiện tại
            scale_multiplier = target_width / current_width

            if direction == 'X':
                active_obj.scale.x *= scale_multiplier
            elif direction == 'Y':
                active_obj.scale.y *= scale_multiplier
            elif direction == 'Z':
                active_obj.scale.z *= scale_multiplier

            # 5. Đưa vật thể vào chính giữa khoảng trống
            active_obj.location[axis_idx] = (inner_min + inner_max) / 2

            self.report({'INFO'}, f"Đã lấp đầy khoảng trống: {target_width:.4f}m")
        else:
            self.report({'ERROR'}, "Vật thể Active không có kích thước để scale")

        return

        # --- CHỨC NĂNG SÂU: DÀN HÀNG BẬC THANG THÔNG MINH (Smart Diagonal Step) ---
    elif alignMethod == 'SMART_STEP_DISTRIBUTE':
        if len(context.selected_objects) < 3:
            self.report({'WARNING'}, "Cần ít nhất 3 vật thể (Cái đầu và cuối làm mốc)")
            return

        # 1. Sắp xếp các vật thể theo thứ tự vị trí trên trục chỉ định (UI Direction)
        # Việc này giúp máy nhận diện đâu là bậc thấp nhất, đâu là bậc cao nhất
        axis_idx = 0 if direction == 'X' else 1 if direction == 'Y' else 2
        objs = sorted(context.selected_objects, key=lambda o: o.location[axis_idx])

        start_obj = objs[0]
        end_obj = objs[-1]
        count = len(objs) - 1

        # 2. Tính toán Vector dịch chuyển tổng thể (Vector từ A đến B)
        delta_pos = end_obj.location - start_obj.location
        step_vector = delta_pos / count

        # 3. TÍNH TOÁN ĐỘ DỐC (Dành cho việc xoay vật thể theo hướng dốc)

        # Tính khoảng cách mặt phẳng (ngang)
        horizontal_dist = math.sqrt(delta_pos.x**2 + delta_pos.y**2)
        # Tính góc nghiêng (radians)
        slope_angle = math.atan2(delta_pos.z, horizontal_dist) if horizontal_dist > 0 else 0

        # 4. Thực thi dàn hàng
        for i in range(1, count):
            obj = objs[i]

            # A. Dàn vị trí chính xác trên không gian 3D (Đường chéo tuyệt đối)
            obj.location = start_obj.location + (i * step_vector)

            # B. Xoay vật thể (Tùy chọn)
            # Mặc định: Đồng bộ xoay theo vật thể bắt đầu
            obj.rotation_euler = start_obj.rotation_euler

            # NÂNG CAO: Nếu bạn muốn vật thể nghiêng theo hướng dốc (ví dụ làm ramp)
            # Hãy bỏ comment dòng dưới đây:
            # obj.rotation_euler.y += slope_angle

        self.report({'INFO'}, f"Đã dàn bậc thang: Khoảng cách bước {step_vector.length:.3f}m")
        return

        # --- CHỨC NĂNG SIÊU CẤP: DÀN CẦU THANG XOẮN "CONG" (Arc Interpolated Stair) ---
    elif alignMethod == 'SMART_STEP_DISTRIBUTE_2':
        if len(context.selected_objects) < 3:
            self.report({'WARNING'}, "Cần ít nhất 3 vật thể (Bậc đầu và cuối làm mốc)")
            return

        # 1. Sắp xếp theo vị trí trục chỉ định
        axis_idx = 0 if direction == 'X' else 1 if direction == 'Y' else 2
        objs = sorted(context.selected_objects, key=lambda o: o.location[axis_idx])

        start_obj = objs[0]
        end_obj = objs[-1]
        count = len(objs) - 1

        # Dữ liệu gốc
        p1 = start_obj.location.copy()
        p2 = end_obj.location.copy()

        # Lấy góc xoay (chỉ tính xoay quanh trục Z để làm đường cong mặt bằng)
        angle_start = start_obj.rotation_euler.z
        angle_end = end_obj.rotation_euler.z
        delta_angle = angle_end - angle_start

        # 2. TÍNH TOÁN ĐƯỜNG CONG (ARC LOGIC)
        # Nếu góc xoay khác nhau, chúng ta tính toán bán kính và tâm ảo
        is_curved = abs(delta_angle) > 0.01

        if is_curved:
            # Khoảng cách XY giữa 2 điểm
            vec_xy = (p2 - p1)
            vec_xy.z = 0
            dist_xy = vec_xy.length

            # Tính bán kính cung tròn dựa trên dây cung và góc ở tâm
            # R = (dist/2) / sin(delta_angle/2)
            try:
                radius = (dist_xy / 2) / math.sin(delta_angle / 2)
            except ZeroDivisionError:
                is_curved = False

        # 3. THỰC THI NỘI SUY
        rot_start = start_obj.rotation_euler.to_quaternion()
        rot_end = end_obj.rotation_euler.to_quaternion()
        scale_start = start_obj.scale.copy()
        scale_end = end_obj.scale.copy()

        for i in range(1, count):
            obj = objs[i]
            t = i / count  # Tiến trình từ 0.0 đến 1.0

            if is_curved:
                # NỘI SUY ĐƯỜNG CONG (Circular Path)
                # Tính góc hiện tại của bậc thang này
                current_angle = angle_start + (delta_angle * t)

                # Tính toán vị trí dựa trên phép quay quanh tâm ảo
                # Cách đơn giản: Lerp Z, nhưng quay XY theo góc
                # Chúng ta tạo một vector bán kính và xoay nó

                # Tìm vector hướng từ tâm đến điểm đầu
                # (Toán học: Vector vuông góc với dây cung tại trung điểm)
                chord_mid = (p1 + p2) / 2
                perp_dir = Vector((-(p2.y - p1.y), (p2.x - p1.x), 0)).normalized()

                # Tìm vị trí tâm ảo (Virtual Center)
                h = math.sqrt(max(0, radius**2 - (dist_xy/2)**2))
                # Đảm bảo hướng của cung (lồi hay lõm) theo dấu của delta_angle
                center = chord_mid + perp_dir * (h if delta_angle > 0 else -h)

                # Vị trí XY mới = Tâm + Vector bán kính đã xoay
                radial_vec = p1 - center
                radial_vec.z = 0

                # Xoay vector bán kính theo góc tương ứng

                rot_mtx = Matrix.Rotation(delta_angle * t, 4, 'Z')
                new_pos_xy = center + (rot_mtx @ radial_vec)

                # Gán vị trí: XY cong, Z thẳng
                obj.location.x = new_pos_xy.x
                obj.location.y = new_pos_xy.y
                obj.location.z = p1.z + (p2.z - p1.z) * t
            else:
                # Nếu không xoay -> Đi thẳng (Linear)
                obj.location = p1.lerp(p2, t)

            # NỘI SUY XOAY (SLERP) - Luôn cần thiết để các bậc tự xoay hướng
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = rot_start.slerp(rot_end, t)

            # NỘI SUY TỈ LỆ
            obj.scale = scale_start.lerp(scale_end, t)

            context.view_layer.update()
            obj.rotation_mode = 'XYZ'

        self.report({'INFO'}, "Đã dàn hàng xoắn ốc theo đường cong chuẩn")
        return



    # --- CHỨC NĂNG SÁNG TẠO: NỐI ĐUÔI BẬC THANG (Step Sequence Snap) ---
    # Chức năng này dành cho các bậc thang có kích thước khác nhau (cái to cái nhỏ)
    elif alignMethod == 'STEP_SEQUENCE_SNAP':
        axis_idx = 0 if direction == 'X' else 1 if direction == 'Y' else 2
        axis_key = direction.lower()

        # Sắp xếp theo vị trí
        objs = sorted(context.selected_objects, key=lambda o: o.location[axis_idx])

        for i in range(1, len(objs)):
            prev_obj = objs[i-1]
            curr_obj = objs[i]

            # Lấy mép ngoài của vật trước và mép trong của vật sau
            b_prev = get_world_bounds(prev_obj)
            b_curr = get_world_bounds(curr_obj)

            # Đẩy vật sau chạm khít mép vật trước trên trục ngang
            offset = b_prev[axis_key][1] - b_curr[axis_key][0]
            curr_obj.location[axis_idx] += offset

            # Đồng thời nâng cao độ lên (bậc thang) dựa trên chiều cao của vật trước
            # (Giả sử bạn muốn mỗi bậc cao lên đúng bằng chiều cao vật trước)
            if direction != 'Z':
                h_prev = b_prev['z'][1] - b_prev['z'][0]
                curr_obj.location.z = prev_obj.location.z + h_prev

        return

        # --- CHỨC NĂNG: XÂY TƯỜNG TRONG BOX (Bản sửa lỗi treo máy) ---
    elif alignMethod == 'FILL_WALL_BOX':

        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]

        if not active_obj or not bricks:
            self.report({'WARNING'}, "Chọn các viên gạch và chọn Wall Box cuối cùng (Active)")
            return

        # --- THIẾT LẬP KHE HỞ (MORTAR GAP) ---
        MAX_GAP = 0.01  # Khoảng cách tối đa 1cm theo yêu cầu của bạn

        # 1. PHÂN TÍCH MẪU
        sample_bricks = bricks
        avg_h = sum(b.dimensions.z for b in sample_bricks) / len(sample_bricks)
        avg_w = sum(b.dimensions.x for b in sample_bricks) / len(sample_bricks)

        # 2. THÔNG SỐ BOX
        wall_bounds = get_world_bounds(active_obj)
        w_min_x, w_max_x = wall_bounds['x']
        w_min_y, w_max_y = wall_bounds['y']
        w_min_z, w_max_z = wall_bounds['z']
        wall_d = w_max_y - w_min_y

        new_bricks = []
        curr_z = w_min_z
        row_idx = 0

        while curr_z < w_max_z:
            # Chiều cao hàng ổn định để đảm bảo chạm mặt viên dưới
            row_h = avg_h * random.uniform(0.9, 1.1)
            if curr_z + row_h > w_max_z: row_h = w_max_z - curr_z

            # Độ sole dựa trên chiều rộng trung bình
            row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0
            curr_x = w_min_x - row_offset

            while curr_x < w_max_x:
                if len(new_bricks) > 5000: break

                source = random.choice(sample_bricks)
                # Chiều rộng ngẫu nhiên dự kiến
                target_w = source.dimensions.x * random.uniform(0.8, 1.2)

                # Xác định điểm bắt đầu và kết thúc thực tế trong Box
                r_start_x = max(w_min_x, curr_x)
                r_end_x = min(w_max_x, curr_x + target_w)
                actual_w = r_end_x - r_start_x

                if actual_w > 0.01: # Chỉ tạo nếu viên đá đủ lớn
                    new_b = source.copy()
                    new_b.data = source.data.copy()
                    context.collection.objects.link(new_b)
                    new_bricks.append(new_b)

                    # --- TÍNH TOÁN SCALE ---
                    scale_z = (row_h / source.dimensions.z)
                    new_b.scale.z *= scale_z
                    new_b.scale.x *= (actual_w / source.dimensions.x)
                    new_b.scale.y *= (wall_d / source.dimensions.y)

                    # --- GIẢI PHÁP CHO LỖI HỞ CHÂN TƯỜNG ---
                    # Tìm điểm thấp nhất của lưới (local space) để bù đắp Origin
                    local_z_min = min(v[2] for v in source.bound_box)
                    z_offset = -(local_z_min * scale_z)

                    # VỊ TRÍ
                    new_b.location.x = r_start_x + (actual_w / 2)
                    new_b.location.z = curr_z + z_offset # Đáy chạm đúng curr_z
                    new_b.location.y = (w_min_y + w_max_y) / 2

                    # Ngẫu nhiên mặt đá
                    if random.random() > 0.5: new_b.rotation_euler.z += 3.14159

                    # CẬP NHẬT CURR_X: Nhảy đến sát mép viên vừa đặt + gap nhỏ
                    gap = random.uniform(0, MAX_GAP)
                    curr_x = r_start_x + actual_w + gap
                else:
                    curr_x += 0.05

            # Nhảy hàng: Đảm bảo hàng trên chạm sát hàng dưới
            curr_z += row_h
            row_idx += 1

        context.view_layer.update()
        self.report({'INFO'}, f"Đã xây xong: {len(new_bricks)} viên gạch khít và sát sàn.")
        return

        # --- CHỨC NĂNG: LÁT GẠCH HÌNH TRÒN (Fill Circle with Bricks) ---
    elif alignMethod == 'FILL_CIRCLE_BOUNDS':
        active_obj = context.active_object  # Đây là cái khuôn Circle/Cylinder
        bricks = [obj for obj in context.selected_objects if obj != active_obj]

        if not active_obj or not bricks:
            self.report({'WARNING'}, "Chọn các mẫu gạch và chọn Circle khuôn cuối cùng")
            return

        # 1. THÔNG SỐ VÒNG TRÒN
        center = active_obj.location.copy()
        radius = active_obj.dimensions.x / 2
        radius_sq = radius ** 2

        # 2. PHÂN TÍCH MẪU GẠCH
        sample_bricks = bricks
        avg_h = sum(b.dimensions.y for b in sample_bricks) / len(sample_bricks)
        avg_w = sum(b.dimensions.x for b in sample_bricks) / len(sample_bricks)

        MAX_GAP = 0.01
        new_bricks = []

        # Bắt đầu quét từ biên dưới lên biên trên theo trục Y
        curr_y = -radius
        row_idx = 0

        while curr_y < radius:
            row_h = avg_h * random.uniform(0.9, 1.1)
            if curr_y + row_h > radius: row_h = radius - curr_y

            # TÍNH TOÁN ĐỘ DÀI HÀNG (Pythagoras: x = sqrt(R^2 - y^2))
            # Ta tính y tại điểm xa tâm nhất trong hàng để đảm bảo gạch không lòi ra ngoài
            y_edge = curr_y if abs(curr_y) > abs(curr_y + row_h) else curr_y + row_h
            if abs(y_edge) > radius: y_edge = radius * (1 if y_edge > 0 else -1)

            half_row_width = math.sqrt(max(0, radius_sq - y_edge**2))
            row_start_x = -half_row_width
            row_end_x = half_row_width

            # So le
            row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0
            curr_x = row_start_x - row_offset

            while curr_x < row_end_x:
                if len(new_bricks) > 4000: break # Cầu chì chống treo máy

                source = random.choice(sample_bricks)
                target_w = source.dimensions.x * random.uniform(0.8, 1.2)

                # Xác định vùng giao nhau giữa viên gạch và biên vòng tròn
                r_start_x = max(row_start_x, curr_x)
                r_end_x = min(row_end_x, curr_x + target_w)
                actual_w = r_end_x - r_start_x

                if actual_w > 0.005:
                    new_b = source.copy()
                    new_b.data = source.data.copy()
                    context.collection.objects.link(new_b)
                    new_bricks.append(new_b)

                    # SCALE
                    s_y = (row_h / source.dimensions.y)
                    new_b.scale.y *= s_y
                    new_b.scale.x *= (actual_w / source.dimensions.x)

                    # FIX ORIGIN (Sát sàn)
                    local_z_min = min(v[2] for v in source.bound_box)
                    z_offset = -(local_z_min * new_b.scale.z)

                    # VỊ TRÍ
                    new_b.location.x = center.x + r_start_x + (actual_w / 2)
                    new_b.location.y = center.y + curr_y + (row_h / 2)
                    new_b.location.z = center.z + z_offset

                    if random.random() > 0.5:
                        new_b.rotation_euler.z += math.pi # Xoay 180 độ

                    # Cập nhật curr_x khít nhau
                    gap = random.uniform(0, MAX_GAP)
                    curr_x = r_start_x + actual_w + gap
                else:
                    curr_x += 0.05 # Nhảy bước nhỏ để thoát vòng lặp

            curr_y += row_h
            row_idx += 1

        context.view_layer.update()
        self.report({'INFO'}, f"Đã lát xong hình tròn với {len(new_bricks)} viên gạch.")
        return

        # --- CHỨC NĂNG: LỢP MÁI NGÓI ÂM DƯƠNG (Yin-Yang Roof Tiles) ---
    elif alignMethod == 'FILL_ROOF_YIN_YANG':

        active_obj = context.active_object # Cái khuôn mái nhà (Box hoặc Plane)
        # Yêu cầu chọn 2 mẫu ngói: Viên Âm (ngửa) và Viên Dương (úp)
        selected_tiles = [obj for obj in context.selected_objects if obj != active_obj]

        if len(selected_tiles) < 2:
            self.report({'WARNING'}, "Chọn ít nhất 2 mẫu: 1 viên ngói Âm (ngửa) và 1 viên Dương (úp)")
            return

        # Giả định viên 0 là Âm, viên 1 là Dương (hoặc ngược lại dựa trên tên/kích thước)
        tile_yin = selected_tiles[0]
        tile_yang = selected_tiles[1]

        # 1. THÔNG SỐ KHUÔN MÁI
        bounds = get_world_bounds(active_obj)
        w_min_x, w_max_x = bounds['x']
        w_min_y, w_max_y = bounds['y']
        w_min_z, w_max_z = bounds['z']

        roof_w = w_max_x - w_min_x
        roof_l = w_max_y - w_min_y

        # 2. THÔNG SỐ NGÓI & TÍNH TOÁN ĐỘ NGHIÊNG THỰC TẾ
        OVERLAP_FACTOR = 0.45  # Độ chồng mí 45% chiều dài viên ngói

        t_w = tile_yin.dimensions.x
        t_l = tile_yin.dimensions.y
        t_h = tile_yin.dimensions.z # Độ dày này quyết định độ dốc chồng mí

        # Khoảng cách bước nhảy thực tế theo chiều Y (trục dốc)
        # Vì ngói gối đầu nên bước nhảy sẽ ngắn hơn chiều dài viên ngói
        step_y = t_l * (1 - OVERLAP_FACTOR)

        # TÍNH GÓC NGHIÊNG TỰ THÂN (Tilt Angle):
        # Viên sau gối lên viên trước tạo ra góc nghiêng alpha
        # tan(alpha) = độ dày / đoạn chồng mí
        tilt_angle = math.atan2(t_h * 0.7, step_y)

        # 3. LẶP XẾP NGÓI
        num_cols = int(roof_w / t_w) + 1
        num_rows = int(roof_l / step_y) + 1
        new_tiles = []

        for c in range(num_cols):
            for r in range(num_rows):
                # Tọa độ X: Chạy ngang mái
                base_x = w_min_x + (c * t_w) + (t_w / 2)

                # Tọa độ Y: Chạy từ sau (w_max_y) về trước (w_min_y) để "đổ" vào màn hình
                # r=0 là hàng thấp nhất (gần màn hình nhất)
                base_y = w_min_y + (r * step_y) + (t_l / 2)

                # Tọa độ Z: Mỗi hàng càng xa (r càng lớn) thì càng phải cao hơn
                # base_z = điểm thấp nhất + (số hàng * độ dày viên ngói để chồng lên nhau)
                # Chúng ta dùng t_h * 0.8 để chúng "ôm" khít vào nhau hơn
                base_z = w_min_z + (r * t_h * 0.7)

                # --- LỚP ÂM (YIN) - Viên ngửa ---
                new_yin = tile_yin.copy()
                new_yin.data = tile_yin.data.copy()
                context.collection.objects.link(new_yin)
                new_tiles.append(new_yin)

                new_yin.location = Vector((base_x, base_y, base_z))
                # XOAY: Xoay quanh trục X để chúi đầu về phía -Y (Front View)
                # Nếu ngói của bạn đang nằm ngang, tilt_angle âm sẽ làm nó chúi xuống
                new_yin.rotation_euler.x = -tilt_angle

                # --- LỚP DƯƠNG (YANG) - Viên úp ---
                if c < num_cols - 1:
                    new_yang = tile_yang.copy()
                    new_yang.data = tile_yang.data.copy()
                    context.collection.objects.link(new_yang)
                    new_tiles.append(new_yang)

                    # Lớp dương nằm đè lên khe nối của 2 viên âm (lệch nửa cột)
                    yang_x = base_x + (t_w / 2)
                    yang_y = base_y
                    # Lớp dương nằm cao hơn lớp âm một chút
                    yang_z = base_z + (t_h * 0.6)

                    new_yang.location = Vector((yang_x, yang_y, yang_z))
                    new_yang.rotation_euler.x = -tilt_angle

        context.view_layer.update()
        self.report({'INFO'}, f"Đã lợp mái Front View: {len(new_tiles)} viên, dốc {math.degrees(tilt_angle):.1f}°")
        return

        # --- CHỨC NĂNG: XÂY TƯỜNG HÌNH CHỮ L / PHỨC TẠP (Smart L-Wall / Mesh Mask) ---
    elif alignMethod == 'FILL_WALL_BOX_LEAVE_TEETH':
        # --- THÔNG SỐ CẤU HÌNH GÓC ---
        # Chế độ: 'NORMAL' (thẳng), 'LEAVE_TEETH' (để lại răng lược), 'FILL_TEETH' (lấp răng lược)
        # Bạn có thể điều chỉnh biến này hoặc thêm vào UI sau
        mode = 'LEAVE_TEETH'

        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]

        if not active_obj or not bricks:
            self.report({'WARNING'}, "Chọn các viên gạch và chọn Wall Box cuối cùng")
            return

        MAX_GAP = 0.01
        sample_bricks = bricks
        avg_h = sum(b.dimensions.z for b in sample_bricks) / len(sample_bricks)
        avg_w = sum(b.dimensions.x for b in sample_bricks) / len(sample_bricks)

        wall_bounds = get_world_bounds(active_obj)
        w_min_x, w_max_x = wall_bounds['x']
        w_min_y, w_max_y = wall_bounds['y']
        w_min_z, w_max_z = wall_bounds['z']
        wall_d = w_max_y - w_min_y

        new_bricks = []
        curr_z = w_min_z
        row_idx = 0

        while curr_z < w_max_z:
            row_h = avg_h * random.uniform(0.95, 1.05)
            if curr_z + row_h > w_max_z: row_h = w_max_z - curr_z

            # --- LOGIC SO LE & RĂNG LƯỢC ---
            row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0

            # Giới hạn biên X cho hàng này
            current_min_x = w_min_x - row_offset
            current_max_x = w_max_x

            # LẤP RĂNG LƯỢC Ở ĐẦU TƯỜNG Và Ở CUỐI TƯỜNG
            if mode == 'LEAVE_TEETH':
                # Hàng chẵn: Bắt đầu lùi lại để nhường chỗ cho răng lược tường 1
                if row_idx % 2 == 0:
                    current_min_x = w_min_x
                else:
                    current_min_x = w_min_x - wall_d
                    current_max_x = w_max_x - wall_d

            curr_x = current_min_x

            while curr_x < current_max_x:
                if len(new_bricks) > 5000: break

                source = random.choice(sample_bricks)
                target_w = source.dimensions.x * random.uniform(0.9, 1.1)

                # Cắt gạch theo biên động (current_min/max)
                r_start_x = max(current_min_x, curr_x)
                r_end_x = min(current_max_x, curr_x + target_w)
                actual_w = r_end_x - r_start_x

                if actual_w > 0.01:
                    new_b = source.copy()
                    new_b.data = source.data.copy()
                    context.collection.objects.link(new_b)
                    new_bricks.append(new_b)

                    scale_z = (row_h / source.dimensions.z)
                    new_b.scale.z *= scale_z
                    new_b.scale.x *= (actual_w / source.dimensions.x)
                    new_b.scale.y *= (wall_d / source.dimensions.y)

                    # Fix Origin Z
                    local_z_min = min(v[2] for v in source.bound_box)
                    z_offset = -(local_z_min * scale_z)

                    new_b.location.x = r_start_x + (actual_w / 2)
                    new_b.location.z = curr_z + z_offset
                    new_b.location.y = (w_min_y + w_max_y) / 2

                    gap = random.uniform(0, MAX_GAP)
                    curr_x = r_start_x + actual_w + gap
                else:
                    curr_x += 0.05

            curr_z += row_h
            row_idx += 1

        context.view_layer.update()
        return

    elif alignMethod == 'FILL_WALL_BOX_FILL_TEETH':
        # --- THÔNG SỐ CẤU HÌNH GÓC ---
        # Chế độ: 'NORMAL' (thẳng), 'LEAVE_TEETH' (để lại răng lược), 'FILL_TEETH' (lấp răng lược)
        # Bạn có thể điều chỉnh biến này hoặc thêm vào UI sau
        mode = 'FILL_TEETH'

        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]

        if not active_obj or not bricks:
            self.report({'WARNING'}, "Chọn các viên gạch và chọn Wall Box cuối cùng")
            return

        MAX_GAP = 0.01
        sample_bricks = bricks
        avg_h = sum(b.dimensions.z for b in sample_bricks) / len(sample_bricks)
        avg_w = sum(b.dimensions.x for b in sample_bricks) / len(sample_bricks)

        wall_bounds = get_world_bounds(active_obj)
        w_min_x, w_max_x = wall_bounds['x']
        w_min_y, w_max_y = wall_bounds['y']
        w_min_z, w_max_z = wall_bounds['z']
        wall_d = w_max_y - w_min_y

        new_bricks = []
        curr_z = w_min_z
        row_idx = 0

        while curr_z < w_max_z:
            row_h = avg_h * random.uniform(0.95, 1.05)
            if curr_z + row_h > w_max_z: row_h = w_max_z - curr_z

            # --- LOGIC SO LE & RĂNG LƯỢC ---
            row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0

            # Giới hạn biên X cho hàng này
            current_min_x = w_min_x - row_offset
            current_max_x = w_max_x

            # LẤP RĂNG LƯỢC Ở ĐẦU TƯỜNG (Dành cho bức tường thứ 2)
            if mode == 'FILL_TEETH':
                # Hàng chẵn: Bắt đầu lùi lại để nhường chỗ cho răng lược tường 1
                if row_idx % 2 == 0:
                    current_min_x = w_min_x

                else:
                    current_min_x = w_min_x - wall_d

            curr_x = current_min_x

            while curr_x < current_max_x:
                if len(new_bricks) > 5000: break

                source = random.choice(sample_bricks)
                target_w = source.dimensions.x * random.uniform(0.9, 1.1)

                # Cắt gạch theo biên động (current_min/max)
                r_start_x = max(current_min_x, curr_x)
                r_end_x = min(current_max_x, curr_x + target_w)
                actual_w = r_end_x - r_start_x

                if actual_w > 0.01:
                    new_b = source.copy()
                    new_b.data = source.data.copy()
                    context.collection.objects.link(new_b)
                    new_bricks.append(new_b)

                    scale_z = (row_h / source.dimensions.z)
                    new_b.scale.z *= scale_z
                    new_b.scale.x *= (actual_w / source.dimensions.x)
                    new_b.scale.y *= (wall_d / source.dimensions.y)

                    # Fix Origin Z
                    local_z_min = min(v[2] for v in source.bound_box)
                    z_offset = -(local_z_min * scale_z)

                    new_b.location.x = r_start_x + (actual_w / 2)
                    new_b.location.z = curr_z + z_offset
                    new_b.location.y = (w_min_y + w_max_y) / 2

                    gap = random.uniform(0, MAX_GAP)
                    curr_x = r_start_x + actual_w + gap
                else:
                    curr_x += 0.05

            curr_z += row_h
            row_idx += 1

        context.view_layer.update()
        return

    elif alignMethod == 'FILL_STONE_WALL_STYLIZED':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            fill_stone_wall_advanced(self, context, active_obj, bricks)
        return

    elif alignMethod == 'FILL_PAVEMENT_STYLIZED':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            fill_pavement_advanced(self, context, active_obj, bricks)
        return

    elif alignMethod == 'ARRANGE_ON_CURVE':
        active_obj = context.active_object
        target_objs = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and active_obj.type == 'CURVE' and target_objs:
            arrange_on_curve(self, context, target_objs, active_obj)
        return

    elif alignMethod == 'FILL_CANOPY':
        active_obj = context.active_object
        leaves = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and leaves:
            # Sử dụng hàm nâng cấp từ logic_upgrade
            logic_upgrade.fill_canopy_stylized_v2(self, context, active_obj, leaves, density_factor=0.5)
        return

    elif alignMethod == 'create_stylized_bear':
        create_stylized_bear(context)

    elif alignMethod == 'FILL_CIRCULAR_PAVEMENT':
        # Mặc định inner_r=1.2, outer_r=4.0 như trong sơ đồ
        active_obj = context.active_object
        if active_obj:
            logic_upgrade.fill_circular_pavement(self, context, active_obj, inner_r=12, outer_r=40)
        return

    elif alignMethod == 'FILL_ROUNDED_SQUARE_PAVEMENT':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.fill_rounded_square_pavement(self, context, active_obj, bricks, inner_size=40.0, outer_size=120.0, corner_radius=3.0)
        return

    elif alignMethod == 'FILL_WOODEN_WALLS':
        active_obj = context.active_object
        planks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and planks:
            logic_upgrade.generate_wooden_plank_walls(self, context, active_obj, planks, gap=0.015)
        return

    elif alignMethod == 'FILL_WOODEN_WALLS_VERTICAL':
        active_obj = context.active_object
        planks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and planks:
            logic_upgrade.generate_vertical_plank_walls(self, context, active_obj, planks, gap=0.01)
        return

    elif alignMethod == 'SNAP_PLANKS_TO_SEGMENTS':
        active_obj = context.active_object
        segments = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and segments:
            logic_upgrade.snap_planks_to_segments(self, context, segments, active_obj)
        return

    elif alignMethod == 'CREATE_STYLIZED_TREE':
        logic_upgrade.create_stylized_tree(self, context)
        return

    elif alignMethod == 'GENERATE_STYLIZED_STREAM':
        # Lấy Active Object làm đường dẫn (Curve)
        # Lấy Ground (thường là plane được chọn cùng)
        # Các vật thể còn lại là đá
        active_obj = context.active_object
        selected = context.selected_objects
        if active_obj and active_obj.type == 'CURVE':
            stones = [obj for obj in selected if obj != active_obj and obj.type == 'MESH']
            # Giả định vật thể to nhất trong đám chọn là Ground, nếu không mặc định dùng z=0
            ground_obj = None # Có thể bổ sung logic tìm ground sau
            logic_upgrade.generate_stylized_stream(self, context, active_obj, ground_obj, stones)
        return

    elif alignMethod == 'DEFORM_CANOPY':
        selected = context.selected_objects
        if selected:
            logic_upgrade.deform_stylized_canopy(self, context, selected)
        return
    elif alignMethod == 'DEFORM_CANOPY_2':
        selected = context.selected_objects
        if selected:
            logic_upgrade.deform_stylized_canopy_2(self, context, selected)
        return

    elif alignMethod == 'ATTACH_LEAVES':
        active_obj = context.active_object
        selected = context.selected_objects
        if active_obj and active_obj.type == 'MESH':
            leaf_samples = [obj for obj in selected if obj != active_obj and obj.type == 'MESH']
            if leaf_samples:
                logic_upgrade.attach_leaves_to_canopy(self, context, leaf_samples, active_obj)
        return
    elif alignMethod == 'GENERATE_CHUNKY_FOLIAGE':
        active_obj = context.active_object
        selected = context.selected_objects
        if active_obj and active_obj.type == 'MESH':
            leaf_samples = [obj for obj in selected if obj != active_obj and obj.type == 'MESH']
            if leaf_samples:
                logic_upgrade.attach_leaves_to_canopy(self, context, leaf_samples, active_obj, config.mat_do_la_cay_tren_tan_cay)
        return

    elif alignMethod == 'FILL_SHINGLED_CANOPY':
        active_obj = context.active_object
        leaves = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and leaves:
            logic_upgrade.generate_shingled_canopy(self, context, active_obj, leaves)
        return

    elif alignMethod == 'FILL_STONE_HOUSE':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_stone_house(self, context, active_obj, bricks)
        return

    elif alignMethod == 'FILL_CORNER_PILLARS':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_corner_pillars(self, context, active_obj, bricks)
        return

    elif alignMethod == 'FILL_WALL_ACCENTS':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_wall_accents(self, context, active_obj, bricks)
        return

    elif alignMethod == 'GENERATE_ISLAND_BASE':
        selected = context.selected_objects
        if len(selected) < 2: return
        
        # Tự động phân loại: 9 vật thể to nhất là Proxy, còn lại là Stone Samples
        sorted_objs = sorted(selected, key=lambda o: o.dimensions.length, reverse=True)
        proxies = sorted_objs[:9]  
        stones = sorted_objs[9:]   
        
        if not stones: 
            stones = [sorted_objs[-1]]
            proxies = sorted_objs[:-1]

        logic_super.generate_island_base_from_proxies(self, context, proxies, stones, density=1.0)
        return

    elif alignMethod == 'HIGHLIGHT_OCCLUDED':
        selected = context.selected_objects
        if selected:
            logic_super.highlight_occluded_objects(self, context, selected)
        return

    elif alignMethod == 'ATTACH_ISLAND_VINE':
        active_obj = context.active_object
        # Chọn các vật thể Mesh làm mẫu (không phải active object)
        selected_samples = [o for o in context.selected_objects if o != active_obj and o.type == 'MESH']
        if active_obj and active_obj.type == 'MESH' and selected_samples:
            logic_super.attach_vines_to_merged_island(self, context, active_obj, selected_samples)
        return

    elif alignMethod == 'ATTACH_ISLAND_ROOT':
        active_obj = context.active_object
        # Chọn các vật thể Mesh làm mẫu (không phải active object)
        selected_samples = [o for o in context.selected_objects if o != active_obj and o.type == 'MESH']
        if active_obj and active_obj.type == 'MESH' and selected_samples:
            logic_super.attach_roots_to_merged_island(self, context, active_obj, selected_samples)
        return

    elif alignMethod == 'ATTACH_ISLAND_MINERAL':
        active_obj = context.active_object
        selected_meshes = [o for o in context.selected_objects if o != active_obj and o.type == 'MESH']
        if active_obj and active_obj.type == 'MESH' and selected_meshes:
            logic_super.attach_minerals_to_merged_island(self, context, active_obj, selected_meshes)
        return

    elif alignMethod == 'DEFORM_TRUNK':
        selected = [o for o in context.selected_objects if o.type == 'MESH']
        if selected:
            logic_upgrade.deform_stylized_trunk(self, context, selected)
        else:
            self.report({'WARNING'}, "Vui lòng chọn ít nhất 1 Mesh (thân cây) để thực hiện.")
        return

    elif alignMethod == 'FILL_CORNER_PILLARS_V2':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_corner_pillars_v2(self, context, active_obj, bricks)
        return

    elif alignMethod == 'FILL_WALL_ACCENTS_V2':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_wall_accents_v2(self, context, active_obj, bricks)
        return

    elif alignMethod == 'CUT_BY_VOLUME':
        cutter = context.active_object
        targets = [obj for obj in context.selected_objects if obj != cutter]
        if cutter and targets:
            logic_upgrade.cut_objects_by_volume(self, context, cutter, targets)
        return

    elif alignMethod == 'GENERATE_SMART_BRIDGE':
        active_obj = context.active_object
        samples = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and active_obj.type == 'CURVE' and samples:
            logic_upgrade.generate_smart_bridge(self, context, active_obj, samples)
        return

    elif alignMethod == 'FILL_STONE_HOUSE_V2':
        active_obj = context.active_object
        bricks = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and bricks:
            logic_upgrade.generate_stone_house_v2(self, context, active_obj, bricks)
        return

    elif alignMethod == 'FILL_STYLIZED_ROOF':
        active_obj = context.active_object
        tiles = [obj for obj in context.selected_objects if obj != active_obj]
        if active_obj and tiles:
            logic_upgrade.generate_stylized_roof(self, context, active_obj, tiles)
        return

    elif alignMethod == 'FILL_GRASS_OVERHANG':
        active_obj = context.active_object
        if active_obj and active_obj.type == 'MESH':

            safe_max = max(config.grass_min_length, config.grass_max_length)

            logic_upgrade.generate_grass_overhang(
            # logic_upgrade.generate_grass_overhang_upgrade(
                self, context, active_obj,
                config.grass_min_length, safe_max,
                config.wave_frequency,
                config.grass_thickness,
                config.random_seed,
                config.segment_length,
                config.bevel_width,
        )
        return

    elif alignMethod == 'generate_grass_overhang_bulge':
        active_obj = context.active_object
        if active_obj and active_obj.type == 'MESH':

            safe_max = max(config.grass_min_length, config.grass_max_length)

            # logic_high_upgrade.generate_grass_overhang_bulge(
            logic_high_upgrade.generate_grass_overhang_bulge_v3(
                self, context,
                soil_obj = active_obj,
                min_length = config.grass_min_length,
                max_length = safe_max,
                wave_frequency = config.wave_frequency,
                grass_thickness = config.grass_thickness,
                random_seed = config.random_seed,
                # segment_length = config.segment_length,
                segment_length = 0.4, # <--- Tăng từ 0.1 lên 0.2 để thưa lưới gấp đôi
                bevel_width = config.bevel_width,
                bulge_amount = config.bulge_amount,
            )
        return

    elif alignMethod == 'GENERATE_PAVEMENT':
        # Gọi hàm từ module chứa logic (giả sử là logic_upgrade)
        logic_high_upgrade.generate_stylized_pavement(
            self,
            context,
            area_size = config.pavement_area_size,           # Ví dụ: 5.0
            subdivisions = config.pavement_subdivisions,     # Ví dụ: 12 (số lượng chia lưới)
            gap_size = config.pavement_gap_size,             # Ví dụ: 0.04 (khoảng cách giữa các viên đá)
            thickness = config.pavement_thickness,           # Ví dụ: 0.15 (độ dày viên đá)
            bevel_h = config.pavement_bevel_h,
            bevel_v = config.pavement_bevel_v,
            random_seed = config.pavement_random_seed,
        )
        return

    elif alignMethod == 'GENERATE_PAVEMENT_THEO_HINH_DANG_YEU_CAU':
        active_obj = context.active_object
        # Gọi hàm từ module chứa logic (giả sử là logic_upgrade)
        logic_high_upgrade.generate_stylized_pavement_theo_hinh_dang_yeu_cau(
            self,
            context,
            active_obj,
            area_size = config.pavement_area_size,           # Ví dụ: 5.0
            subdivisions = config.pavement_subdivisions,     # Ví dụ: 12 (số lượng chia lưới)
            gap_size = config.pavement_gap_size,             # Ví dụ: 0.04 (khoảng cách giữa các viên đá)
            thickness = config.pavement_thickness,           # Ví dụ: 0.15 (độ dày viên đá)
            bevel_h = config.pavement_bevel_h,
            bevel_v = config.pavement_bevel_v,
            random_seed = config.pavement_random_seed,
        )
        return

    elif alignMethod == 'generate_island_blockout':
        logic_high_upgrade.generate_island_blockout()
        return

    elif alignMethod == 'generate_chunky_stylized_rock':
        logic_high_upgrade.generate_chunky_stylized_rock(self, context)
        return

    elif alignMethod == 'generate_procedural_stone_wall':
        active_obj = context.active_object
        # logic_high_upgrade.generate_procedural_stone_wall(
        logic_high_upgrade.generate_procedural_stone_wall_v2(
            self, context,
            target_curve = active_obj,
            alignment = config.stone_wall_wall_alignment,
            num_layers = config.stone_wall_num_layers,
            layer_height = config.stone_wall_layer_height,
            wall_thickness = config.stone_wall_wall_thickness,
            min_width = config.stone_wall_min_width,
            max_width = config.stone_wall_max_width,
            gap_size = config.stone_wall_gap_size,
        )
        return

    elif alignMethod == 'generate_procedural_stone_path':
        active_obj = context.active_object
        # logic_high_upgrade.generate_procedural_stone_path(
        logic_high_upgrade.generate_procedural_stone_path_v2(
            self, context,
            target_curve = active_obj,
            alignment= config.stone_path_alignment,
            num_lanes = config.stone_path_num_lanes,
            lane_width = config.stone_path_lane_width,
            stone_thickness = config.stone_path_stone_thickness,
            min_length = config.stone_path_min_length,
            max_length = config.stone_path_max_length,
            gap_size = config.stone_path_gap_size,
        )
        return

    elif alignMethod == 'build_ultimate_cozy_wall':
        active_obj = context.active_object
        # logic_high_upgrade.build_wall_ultimate(active_obj, brick_collection_name="Cute_Bricks", overlap_size=0.05)
        logic_high_upgrade.build_ultimate_cozy_wall(active_obj, brick_collection_name="Cute_Bricks", overlap_size=0.05)
        return

    elif alignMethod == 'create_bounding_box_for_active':
        active_obj = context.active_object
        logic_high_upgrade.create_bounding_box_for_active()
        return

    elif alignMethod == 'replace_bounding_box_with_best_brick':
        active_obj = context.active_object
        logic_high_upgrade.replace_bounding_box_with_best_brick(brick_collection_name="Cute_Bricks")
        return



    elif alignMethod == 'apply_stone_surface_damage':
        # logic_high_upgrade.apply_stone_surface_damage(self, context)
        logic_high_upgrade.apply_stone_surface_damage_upgrade(self, context,
              inset_thickness = config.stone_surface_damage_inset_thickness,
              noise_strength = config.stone_surface_damage_noise_strength,
              noise_scale = config.stone_surface_damage_noise_scale
        )
        return

    elif alignMethod == 'remove_redundant_edges':
        logic_high_upgrade.remove_redundant_edges(self, context)
        return


    return

def fill_stone_wall_advanced(self, context, active_obj, bricks):
    """
    Lấp đầy đá vào khối Mesh uốn lượn (Stylized Stone Wall).
    Dùng BVHTree để check Inside và tìm Normal để xoay đá.
    """
    if not active_obj or not bricks:
        return

    # 1. TẠO BVH TREE TỪ MESH CỦA ACTIVE OBJECT
    depsgraph = context.view_layer.depsgraph
    eval_obj = active_obj.evaluated_get(depsgraph)
    mesh_data = eval_obj.to_mesh()
    
    bm = bmesh.new()
    bm.from_mesh(mesh_data)
    bm.transform(active_obj.matrix_world) # Chuyển sang World Space
    bvh = BVHTree.FromBMesh(bm)
    
    # 2. THÔNG SỐ TƯỜNG & ĐÁ
    wall_bounds = get_world_bounds(active_obj)
    min_v = Vector((wall_bounds['x'][0], wall_bounds['y'][0], wall_bounds['z'][0]))
    max_v = Vector((wall_bounds['x'][1], wall_bounds['y'][1], wall_bounds['z'][1]))
    
    avg_w = sum(b.dimensions.x for b in bricks) / len(bricks)
    avg_h = sum(b.dimensions.z for b in bricks) / len(bricks)
    
    MAX_GAP = 0.02
    new_bricks = []
    
    curr_z = min_v.z
    row_idx = 0
    
    # Chúng ta quét một lưới XY bao quanh BBox của tường
    # Tường có độ dày (Y axis), ta sẽ tìm điểm trên bề mặt Y để đặt đá
    
    while curr_z < max_v.z:
        row_h = avg_h * random.uniform(0.95, 1.05)
        if curr_z + row_h > max_v.z: row_h = max_v.z - curr_z
        
        row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0
        curr_x = min_v.x - row_offset
        
        while curr_x < max_v.x:
            # Điểm trung tâm dự kiến của viên gạch
            sample_pos = Vector((curr_x + avg_w/2, (min_v.y + max_v.y)/2, curr_z + row_h/2))
            
            # Tìm điểm gần nhất trên Mesh để gạch "hít" vào bề mặt
            nearest_pos, normal, face_idx, dist = bvh.find_nearest(sample_pos)
            
            if dist is not None and dist < (max_v.y - min_v.y):
                source = random.choice(bricks)
                target_w = source.dimensions.x * random.uniform(0.8, 1.2)
                
                new_b = source.copy()
                new_b.data = source.data.copy()
                context.collection.objects.link(new_b)
                new_bricks.append(new_b)
                
                # VỊ TRÍ: Đưa về điểm trên bề mặt
                new_b.location = nearest_pos
                
                # XOAY: Xoay theo Normal của mặt tường
                # Giả định đá mẫu có mặt trước hướng trục Y+
                align_quat = normal.to_track_quat('Y', 'Z')
                new_b.rotation_euler = align_quat.to_euler()
                
                # Random xoay nhẹ để tự nhiên
                new_b.rotation_euler.y += random.uniform(-0.1, 0.1)
                new_b.rotation_euler.z += random.uniform(-0.05, 0.05)
                
                # SCALE
                new_b.scale.x *= (target_w / source.dimensions.x)
                new_b.scale.z *= (row_h / source.dimensions.z)
                
                # Cập nhật curr_x
                curr_x += target_w + random.uniform(0, MAX_GAP)
            else:
                curr_x += avg_w * 0.5 # Nhảy bước nếu không chạm mesh
            
            if len(new_bricks) > 4000: break
            
        curr_z += row_h
        row_idx += 1
        if len(new_bricks) > 4000: break

    bm.free()
    eval_obj.to_mesh_clear()
    context.view_layer.update()
    
    self.report({'INFO'}, f"Đã tạo {len(new_bricks)} viên đá stylized ôm theo tường uốn lượn.")

def arrange_on_curve(self, context, target_objs, curve_obj):
    """
    Sắp xếp vật thể dọc theo đường cong (Curve).
    """
    # 1. TẠO SAMPLER EMPTY (Tối ưu: tạo 1 lần dùng cho cả vòng lặp)
    temp_empty = bpy.data.objects.new("Temp_Sampler", None)
    context.collection.objects.link(temp_empty)
    constraint = temp_empty.constraints.new('FOLLOW_PATH')
    constraint.target = curve_obj
    constraint.use_fixed_location = True # Sửa lỗi ở đây: dùng use_fixed_location thay vì use_path

    def get_curve_data(factor):
        constraint.offset_factor = max(0.0, min(1.0, factor))
        context.view_layer.update()
        pos = temp_empty.matrix_world.to_translation()
        
        # Tính Tangent (hướng tiến)
        delta = 0.001
        constraint.offset_factor = max(0.0, factor - delta)
        context.view_layer.update()
        pos_prev = temp_empty.matrix_world.to_translation()
        
        tangent = (pos - pos_prev).normalized()
        if tangent.length < 0.0001:
            constraint.offset_factor = min(1.0, factor + delta)
            context.view_layer.update()
            pos_next = temp_empty.matrix_world.to_translation()
            tangent = (pos_next - pos).normalized()
        return pos, tangent

    # 2. TÍNH CHIỀU DÀI
    curve_length = 0
    for spline in curve_obj.data.splines:
        curve_length += spline.calc_length()
    if curve_length == 0: curve_length = 1.0

    # 3. THỰC THI
    if len(target_objs) == 1:
        # TRƯỜNG HỢP 1: Nhân bản 1 vật mẫu
        source = target_objs[0]
        obj_dim = get_world_dimensions(source)
        step_len = obj_dim.y if obj_dim.y > 0 else 1.0
        
        count = max(2, int(curve_length / step_len))
        for i in range(count):
            factor = i / (count - 1)
            pos, tangent = get_curve_data(factor)
            
            new_obj = source.copy()
            new_obj.data = source.data.copy()
            context.collection.objects.link(new_obj)
            
            new_obj.location = pos
            new_obj.rotation_mode = 'QUATERNION'
            new_obj.rotation_quaternion = tangent.to_track_quat('Y', 'Z')
    else:
        # TRƯỜNG HỢP 2: Dàn danh sách hiện có
        count = len(target_objs)
        for i, obj in enumerate(target_objs):
            factor = i / (count - 1)
            pos, tangent = get_curve_data(factor)
            
            obj.location = pos
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = tangent.to_track_quat('Y', 'Z')

    # DỌN DẸP
    bpy.data.objects.remove(temp_empty, do_unlink=True)
    self.report({'INFO'}, "Đã hoàn thành bố trí trên đường cong.")

def fill_pavement_advanced(self, context, active_obj, bricks):
    """
    Lát đá nền trên diện tích đa giác (Polygon Pavement) - Phiên bản Ngăn nắp.
    Dùng Raycast để lấp đầy diện tích bên trong đa giác với khoảng hở cố định 1cm.
    """
    if not active_obj or not bricks:
        return

    depsgraph = context.view_layer.depsgraph
    
    # 1. THÔNG SỐ PLANE & ĐÁ
    bounds = get_world_bounds(active_obj)
    min_x, max_x = bounds['x']
    min_y, max_y = bounds['y']
    min_z, max_z = bounds['z']
    
    GAP = 0.01 # Khoảng cách cố định 1cm
    avg_w = sum(b.dimensions.x for b in bricks) / len(bricks)
    avg_l = sum(b.dimensions.y for b in bricks) / len(bricks)
    
    new_stones = []
    curr_y = min_y
    row_idx = 0
    
    # 2. TẠM ẨN CÁC VIÊN ĐÁ MẪU
    original_hides = {obj: obj.hide_get() for obj in bricks}
    for obj in bricks: obj.hide_set(True)
    context.view_layer.update()

    try:
        while curr_y < max_y:
            # Chiều cao hàng ổn định (có một chút biến động nhẹ để tự nhiên)
            row_h = avg_l * random.uniform(0.9, 1.1)
            if curr_y + row_h > max_y: row_h = max_y - curr_y
            
            # Sole (Staggered) - Dịch chuyển hàng lẻ
            row_offset = (avg_w * 0.5) if row_idx % 2 != 0 else 0
            curr_x = min_x - row_offset
            
            while curr_x < max_x:
                # Kiểm tra điểm tâm dự kiến
                check_pos = Vector((curr_x + avg_w/2, curr_y + row_h/2, max_z + 1.0))
                ray_dir = Vector((0, 0, -1))
                
                success, hit_loc, normal, face_idx, hit_obj, matrix = context.scene.ray_cast(
                    depsgraph, check_pos, ray_dir
                )
                
                if success and hit_obj == active_obj:
                    source = random.choice(bricks)
                    
                    # Tính toán scale để khớp chiều cao hàng
                    s_y = row_h / source.dimensions.y
                    
                    # Chiều rộng sau khi scale Y (giả sử scale đồng nhất ban đầu)
                    scaled_w = source.dimensions.x * s_y
                    
                    new_s = source.copy()
                    new_s.data = source.data.copy()
                    context.collection.objects.link(new_s)
                    new_stones.append(new_s)
                    
                    # THIẾT LẬP SCALE: Khớp Y với hàng, X giữ tỉ lệ hoặc ngẫu nhiên nhẹ
                    new_s.scale.y *= s_y
                    # Bù trừ X một chút để lấp đầy tốt hơn
                    s_x_rand = random.uniform(0.9, 1.1)
                    new_s.scale.x *= (s_y * s_x_rand)
                    
                    # Cập nhật kích thước thực sau scale
                    actual_w = source.dimensions.x * new_s.scale.x / source.scale.x
                    
                    # VỊ TRÍ (Căn giữa hàng và cột, bám sát GAP)
                    new_s.location = hit_loc
                    
                    # XOAY: Vuông vức 90 độ + jitter cực nhỏ
                    angles = [0, math.pi/2, math.pi, 3*math.pi/2]
                    base_rot = random.choice(angles)
                    jitter = math.radians(random.uniform(-1, 1))
                    
                    align_quat = normal.to_track_quat('Z', 'Y')
                    new_s.rotation_euler = align_quat.to_euler()
                    new_s.rotation_euler.z += (base_rot + jitter)
                    
                    # Nhảy bước tiếp theo: Chiều rộng thực + GAP
                    curr_x += actual_w + GAP
                else:
                    # Nếu không chạm, nhảy một bước nhỏ để tìm điểm tiếp theo
                    curr_x += avg_w * 0.2
                
                if len(new_stones) > 6000: break
                
            curr_y += row_h + GAP # Hàng tiếp theo cách hàng cũ 1 GAP
            row_idx += 1
            if len(new_stones) > 6000: break
            
    finally:
        for obj, hidden in original_hides.items():
            obj.hide_set(hidden)
        context.view_layer.update()

    self.report({'INFO'}, f"Đã lát ngăn nắp {len(new_stones)} viên đá (Gap 1cm).")

def get_world_bounds(obj):
    """Trả về tọa độ Min và Max của vật thể trong không gian thế giới (World Space)"""
    local_coords = [Vector(corner) for corner in obj.bound_box]
    world_coords = [obj.matrix_world @ coord for coord in local_coords]

    min_x = min(c.x for c in world_coords)
    max_x = max(c.x for c in world_coords)
    min_y = min(c.y for c in world_coords)
    max_y = max(c.y for c in world_coords)
    min_z = min(c.z for c in world_coords)
    max_z = max(c.z for c in world_coords)

    return {"x": (min_x, max_x), "y": (min_y, max_y), "z": (min_z, max_z)}

def get_or_create_material(name, color):
    """Lấy material đã có hoặc tạo mới với màu chỉ định"""
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        # Tìm node Principled BSDF
        bsdf = nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs[0].default_value = color
    return mat

def create_stylized_bear(context):
    """Dựng hình chú gấu Stylized từ các khối Mesh cơ bản"""
    # 1. THIẾT LẬP MÀU SẮC (RGBA)
    fur_color = (0.35, 0.2, 0.1, 1.0)      # Nâu
    snout_color = (0.85, 0.75, 0.55, 1.0) # Kem
    clothes_color = (0.2, 0.4, 0.8, 1.0)  # Xanh dương
    black_color = (0.02, 0.02, 0.02, 1.0) # Đen
    white_color = (0.9, 0.9, 0.9, 1.0)    # Trắng

    mat_fur = get_or_create_material("Mat_Bear_Fur", fur_color)
    mat_snout = get_or_create_material("Mat_Bear_Snout", snout_color)
    mat_clothes = get_or_create_material("Mat_Bear_Clothes", clothes_color)
    mat_black = get_or_create_material("Mat_Black", black_color)
    mat_white = get_or_create_material("Mat_White", white_color)

    # 2. TẠO EMPTY ĐỂ LÀM GỐC (Root)
    bear_root = bpy.data.objects.new("Stylized_Bear_Root", None)
    context.collection.objects.link(bear_root)
    bear_root.location = context.scene.cursor.location

    def add_part(name, loc, sc, mat, rotation=(0, 0, 0)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=1.0)
        obj = context.active_object
        obj.name = name
        obj.location = bear_root.location + Vector(loc)
        obj.scale = Vector(sc)
        obj.rotation_euler = [math.radians(r) for r in rotation]
        obj.data.materials.append(mat)
        obj.parent = bear_root
        # Làm mượt (Smooth Shade)
        bpy.ops.object.shade_smooth()
        return obj

    # 3. DỰNG CÁC BỘ PHẬN
    # Thân (Mặc yếm xanh)
    body = add_part("Bear_Body", (0, 0, 0.7), (0.8, 0.75, 0.9), mat_clothes)
    
    # Đầu (Nâu)
    head = add_part("Bear_Head", (0, 0.1, 1.8), (0.75, 0.7, 0.7), mat_fur)
    
    # Tai
    ear_l = add_part("Bear_Ear_L", (0.5, 0.2, 2.3), (0.2, 0.1, 0.2), mat_fur, (0, 30, 0))
    ear_r = add_part("Bear_Ear_R", (-0.5, 0.2, 2.3), (0.2, 0.1, 0.2), mat_fur, (0, -30, 0))
    
    # Mõm (Kem)
    snout = add_part("Bear_Snout", (0, 0.6, 1.7), (0.35, 0.35, 0.3), mat_snout)
    
    # Mũi (Đen)
    nose = add_part("Bear_Nose", (0, 0.9, 1.75), (0.08, 0.08, 0.06), mat_black)

    # Mắt
    eye_l = add_part("Bear_Eye_L", (0.25, 0.7, 1.95), (0.07, 0.05, 0.08), mat_black)
    eye_r = add_part("Bear_Eye_R", (-0.25, 0.7, 1.95), (0.07, 0.05, 0.08), mat_black)

    # Tay
    arm_l = add_part("Bear_Arm_L", (0.85, 0.2, 1.1), (0.25, 0.25, 0.5), mat_fur, (20, 0, -20))
    arm_r = add_part("Bear_Arm_R", (-0.85, 0.2, 1.1), (0.25, 0.25, 0.5), mat_fur, (20, 0, 20))

    # Chân
    leg_l = add_part("Bear_Leg_L", (0.4, 0.1, 0.15), (0.3, 0.3, 0.35), mat_fur)
    leg_r = add_part("Bear_Leg_R", (-0.4, 0.1, 0.15), (0.3, 0.3, 0.35), mat_fur)

    # Cúc áo (Trắng)
    button_l = add_part("Button_L", (0.3, 0.6, 1.3), (0.05, 0.03, 0.05), mat_white)
    button_r = add_part("Button_R", (-0.3, 0.6, 1.3), (0.05, 0.03, 0.05), mat_white)

    print(f"Chú gấu Stylized đã xuất hiện tại {bear_root.location}!")
    return bear_root

def create_custom_mesh(name, vertices, faces, edges=[]):
    """
    Tạo một Mesh Object từ danh sách tọa độ các điểm và các mặt.
    - vertices: List of (x, y, z)
    - faces: List of vertex indices (e.g. [(0, 1, 2), (0, 2, 3)])
    - edges: (Tùy chọn) List of vertex index pairs
    """
    # 1. Tạo dữ liệu Mesh
    mesh = bpy.data.meshes.new(name)
    
    # 2. Nạp tọa độ vào Mesh
    # from_pydata(vertices, edges, faces)
    mesh.from_pydata(vertices, edges, faces)
    
    # Cập nhật mesh để tính toán các thông số hình học
    mesh.update()
    
    # 3. Tạo Object chứa Mesh đó
    obj = bpy.data.objects.new(name, mesh)
    
    # 4. Liên kết Object vào Scene hiện tại (Active Collection)
    bpy.context.collection.objects.link(obj)
    
    return obj

def create_sample_pyramid(context):
    """Ví dụ tạo một hình Kim Tự Tháp từ danh sách tọa độ"""
    # Tọa độ 5 đỉnh
    verts = [
        (1.0, 1.0, 0.0),   # 0: Góc đáy 1
        (-1.0, 1.0, 0.0),  # 1: Góc đáy 2
        (-1.0, -1.0, 0.0), # 2: Góc đáy 3
        (1.0, -1.0, 0.0),  # 3: Góc đáy 4
        (0.0, 0.0, 1.5)    # 4: Đỉnh chóp
    ]
    
    # Danh sách các mặt (mỗi bộ là index của đỉnh trong list verts)
    faces = [
        (0, 1, 2, 3), # Mặt đáy (Square)
        (0, 4, 1),    # Mặt bên 1 (Triangle)
        (1, 4, 2),    # Mặt bên 2
        (2, 4, 3),    # Mặt bên 3
        (3, 4, 0)     # Mặt bên 4
    ]
    
    obj = create_custom_mesh("Stylized_Pyramid", verts, faces)
    
    # Đặt vị trí tại 3D Cursor cho tiện quan sát
    obj.location = context.scene.cursor.location
    print(f"Đã tạo {obj.name} từ danh sách tọa độ.")
