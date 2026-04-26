import bpy
import blf
from mathutils import Vector
from .functions import object_tools

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

# def show_detailed_message(lines, title="Thông báo", icon='INFO'):
#     """Hiển thị hộp thoại Popup nhiều dòng"""
#     def draw(self, context):
#         layout = self.layout
#         for line in lines:
#             layout.label(text=line) 

#     bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)


# def show_detailed_message(lines, title="Thông báo", icon='INFO'):
#     # Kiểm tra xem hàm có thực sự được gọi không
#     print(f"DEBUG: Đang gọi Popup với {len(lines)} dòng") 

#     def draw(self, context):
#         layout = self.layout
#         # Nếu lines không phải list, hãy ép nó thành list
#         content = lines if isinstance(lines, list) else [str(lines)]
#         for line in content:
#             layout.label(text=line)

#     # Quan trọng: Kiểm tra xem window_manager có tồn tại không
#     if hasattr(bpy.context, 'window_manager'):
#         bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
#     else:
#         print("DEBUG: Không tìm thấy Window Manager")

def show_detailed_message(lines, title="Thông báo", icon='INFO'):
    def draw(self, context):
        layout = self.layout
        
        # Tạo một khung bao quanh để giao diện gọn gàng hơn
        main_col = layout.column(align=True)
        
        for line in lines:
            row = main_col.row()
            
            # TỰ ĐỘNG PHÂN LOẠI MÀU SẮC VÀ ICON
            if "Lỗi" in line or "Error" in line or "thất bại" in line:
                row.label(text=line, icon='ERROR')
                row.alert = True  # Biến dòng này thành màu đỏ
            
            elif "Thành công" in line or "Done" in line or "✅" in line:
                row.label(text=line, icon='CHECKMARK')
                # Lưu ý: Blender không có màu xanh lá cho text, 
                # nhưng icon CHECKMARK sẽ giúp nhận diện nhanh.
            
            elif "-" in line: # Dòng liệt kê chi tiết
                row.label(text=f"  {line}", icon='DOT')
            
            else:
                row.label(text=line)

    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

class VT_OT_ShowMessage(bpy.types.Operator):
    bl_idname = "vt.show_message"
    bl_label = "Thông báo hệ thống"
    bl_options = {'INTERNAL'}

    lines: bpy.props.CollectionProperty(type=bpy.types.PropertyGroup) # type: ignore # Không dùng được list trực tiếp ở đây
    message: bpy.props.StringProperty() # type: ignore # Dùng tạm string nếu thông báo ngắn

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        # Điều chỉnh chiều rộng hộp thoại
        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        # Vẽ nội dung thông báo của bạn ở đây
        layout.label(text=self.message, icon='CHECKMARK')

# Hàm gọi nhanh
def show_message_box(message):
    bpy.ops.vt.show_message('INVOKE_DEFAULT', message=message)

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

_handle = None
hud_text = "VT SYSTEM: READY"
hud_color = (1.0, 1.0, 1.0, 1.0) # Mặc định màu trắng

# Biến toàn cục lưu trữ kết quả để HUD chỉ việc lấy ra vẽ
hud_data = {
    "name": "",
    "type": "",
    "props": {},
    "refs": [],

    "CMC_Id": "",
    "CMC_IsRootObject": False,
    "CMC_IsReferenceObject": False,
    "CMC_RootObjectName": "",

    "CMC_ReferenceNumber": 0,

    # X: Ngang (Width)
    # Y: Sâu (Depth)
    # Z: Cao (Height)
    "CMC_Width": 0,
    "CMC_Depth": 0,
    "CMC_Height": 0,

    "CMC_Rotation_X": 0,
    "CMC_Rotation_Y": 0,
    "CMC_Rotation_Z": 0,

    # Biến đếm làm mới dữ liệu
    "currentRefreshIndexCount": 0,
    "neededRefreshIndexCount": 0
}

# Hàm hỗ trợ đánh dấu có sự thay đổi dữ liệu, chạy để hiển thị dữ liệu mới
def refresh_hud_data(obj, op_name="Update"):
    global hud_data
    if not obj: return
    
    # 1. Reset
    reset_hud_data(hud_data)

    # 2. Chủ động gọi hàm cập nhật dữ liệu luôn
    update_object_stats(bpy.context.scene)

    # 3. Vẫn nên tag_redraw để chữ trên màn hình nhảy số ngay
    bpy.context.area.tag_redraw()

    print(f"HUD - refresh_hud_data: '{hud_data.get('neededRefreshIndexCount')}'")

# --- HÀM TÍNH TOÁN (Chỉ chạy khi có thay đổi) ---
def update_object_stats(scene):
    try:
        # Code xử lý của bạn ở đây
        
        global hud_data
        # 1. Lấy object active và danh sách đang chọn
        obj = bpy.context.active_object
        selected = bpy.context.selected_objects

        print("HUD - Cập nhật dữ liệu") 

        # ĐIỀU KIỆN: Nếu không có object nào được chọn (click ra ngoài)
        # Hoặc object active không nằm trong danh sách đang chọn
        if not selected or (obj not in selected):
            if hud_data.get("name") != "":
                reset_hud_data(hud_data)
            print("Không Có Object Nào Được Chọn")
            
            return
        else:
            print("Đang Có Object Được Chọn")

        # TRƯỜNG HỢP 2: Kiểm tra xem có cần Update không
        # Cần update khi: Đổi tên Object HOẶC Chỉ số Refresh bị lệch
        is_new_object = obj.name != hud_data.get("name")
        is_forced_refresh = hud_data["neededRefreshIndexCount"] != hud_data["currentRefreshIndexCount"]

        if not (is_new_object or is_forced_refresh):
            return

        # --- BẮT ĐẦU TÍNH TOÁN (Chỉ chạy khi lọt qua các bộ lọc trên) ---
        
        # Đồng bộ lại chỉ số đệm
        hud_data["currentRefreshIndexCount"] = hud_data["neededRefreshIndexCount"]
        
        # Đồng bộ lại dữ liệu Object
        object_tools.sync_object_data(bpy.context, obj)

        # Đồng bộ lại dữ liệu Hud
        sync_hud_data(hud_data, obj)
        
        ##### Các hàm phức tạp và tốn nhiều chi phí để xử lý

        #
        find_Reference_Object(hud_data)

        #
        find_Root_Object(hud_data)

        pass
    except Exception as e:
        print(f"Hàm Cập Nhật HUD Xảy Ra Lỗi: {e}")

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def sync_hud_data(hud_data, obj):
    
    hud_data["name"] = obj.name
    hud_data["type"] = obj.type

    hud_data["CMC_Width"] = obj.get("CMC_Width")
    hud_data["CMC_Depth"] = obj.get("CMC_Depth")
    hud_data["CMC_Height"] = obj.get("CMC_Height")

    hud_data["CMC_Rotation_X"] = obj.get("CMC_Rotation_X")
    hud_data["CMC_Rotation_Y"] = obj.get("CMC_Rotation_Y")
    hud_data["CMC_Rotation_Z"] = obj.get("CMC_Rotation_Z")

    # Lấy Custom Properties an toàn 
    hud_data["props"] = {k: obj[k] for k in obj.keys() if k not in '_RNA_UI'}
    hud_data["CMC_Id"] = hud_data["props"].get("CMC_Id", "None")
    hud_data["CMC_IsRootObject"] = hud_data["props"].get("CMC_IsRootObject", False)
    
    hud_data["CMC_RootObjectName"] = obj.get("CMC_RootObjectName")

    if hud_data["props"].get("CMC_IsRootObject", False) == False and hud_data["props"].get("CMC_RootObjectId", -1) != -1:
        hud_data["CMC_IsReferenceObject"] = True
    else:
        hud_data["CMC_IsReferenceObject"] = False

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def reset_hud_data(hud_data):
    hud_data["name"] = ""
    hud_data["props"] = {}
    hud_data["CMC_Id"] = "None"
    hud_data["CMC_IsRootObject"] = False
    hud_data["CMC_IsReferenceObject"] = False
    hud_data["CMC_RootObjectName"] = ""
    hud_data["CMC_ReferenceNumber"] = 0,

    hud_data["CMC_Width"] = 0,
    hud_data["CMC_Depth"] = 0,
    hud_data["CMC_Height"] = 0,

    hud_data["CMC_Rotation_X"] = 0,
    hud_data["CMC_Rotation_Y"] = 0,
    hud_data["CMC_Rotation_Z"] = 0,

    print(f"DEBUG: HUD Cleared | Name: '{hud_data.get('name')}'")

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def find_Root_Object(hud_data):

    root_name_found = "Unknown_Root"
    reference_root_id = -1

    if hud_data["props"].get("CMC_IsRootObject", False) == False and hud_data["props"].get("CMC_RootObjectId", -1) != -1:
        reference_root_id = hud_data["props"].get("CMC_RootObjectId", -1)
        
        # Duyệt qua toàn bộ object trong file để tìm object có ID khớp với RootObjectId
        for object in bpy.data.objects:
            # Kiểm tra nếu object đó có ID và IsRootObject = True
            if object.get("CMC_Id") == reference_root_id and (object.get("CMC_IsRootObject") is True or object.get("CMC_IsRootObject") == 1):
                root_name_found = object.name
                hud_data["CMC_RootObjectName"] = root_name_found
                break
    
    if root_name_found == "Unknown_Root":
        print(f"Cảnh báo: Không tìm thấy Root Object có ID {reference_root_id} trong file này.")

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def find_Reference_Object(hud_data):

    # Tính số lượng Reference hiện có
    reference_number = 0

    if hud_data["CMC_IsRootObject"] == True:
        # Duyệt qua toàn bộ object trong file để tìm object có RootObjectId khớp với Id
        for object in bpy.data.objects:
            # Kiểm tra nếu object đó có ID và IsRootObject = True
            if object.get("CMC_IsRootObject") == False and object.get("CMC_RootObjectId") == hud_data["CMC_Id"]:
                reference_number += 1

    hud_data["CMC_ReferenceNumber"] = reference_number

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____



# ---  HÀM VẼ HUD (Chỉ lấy dữ liệu từ hud_data ra vẽ) ---
def draw_callback_px(self, context):
    if check_change_active_object(context) == False:
        return
    
    #####
    global hud_data

    try:
        font_id = 0
        blf.size(font_id, 18)
        x_pos, y_pos = 30, 200

        # 1. Thiết lập màu trắng xám nhẹ cho chữ "Đang chọn:"
        blf.color(font_id, 0.8, 0.8, 0.8, 1.0) 
        blf.position(font_id, x_pos, y_pos, 0)
        blf.draw(font_id, "Đang chọn: ")
        # 2. Tính toán độ dài của chữ vừa vẽ để không bị đè lên nhau
        # blf.dimensions trả về (width, height) của chuỗi text
        text_width, text_height = blf.dimensions(font_id, "Đang chọn: ")
        # 3. Thiết lập màu xanh cho tên Object
        blf.color(font_id, 0.2, 1.0, 0.2, 1.0)
        blf.position(font_id, x_pos + text_width, y_pos, 0) # Cộng thêm độ rộng của chữ trước đó
        blf.draw(font_id, hud_data['name'])
        
        # Vẽ Custom Properties (Màu Cyan)
        if hud_data["CMC_Id"]:
            y_pos -= 25
            # blf.color(font_id, 0.0, 0.8, 1.0, 1.0)
            # blf.position(font_id, x_pos, y_pos, 0)
            # blf.draw(font_id, f"Id: {hud_data['CMC_Id']}")

            # 1. Thiết lập màu trắng xám nhẹ cho chữ "Id: "
            blf.color(font_id, 0.8, 0.8, 0.8, 1.0) 
            blf.position(font_id, x_pos, y_pos, 0)
            blf.draw(font_id, "Id: ")
            # 2. Tính toán độ dài của chữ vừa vẽ để không bị đè lên nhau
            # blf.dimensions trả về (width, height) của chuỗi text
            text_width, text_height = blf.dimensions(font_id, "Id: ")
            # 3. Thiết lập màu xanh cho Id Object
            blf.color(font_id, 0.0, 0.8, 1.0, 1.0)
            blf.position(font_id, x_pos + text_width, y_pos, 0) # Cộng thêm độ rộng của chữ trước đó
            blf.draw(font_id, f"{hud_data['CMC_Id']}")
            
        #
        if hud_data["CMC_IsRootObject"] == True:
            y_pos -= 25
            blf.color(font_id, 0.8, 0.2, 0.2, 1.0)
            blf.position(font_id, x_pos, y_pos, 0)
            blf.draw(font_id, "Obj gốc")
            if hud_data["CMC_ReferenceNumber"] != 0:
                
                text_width, text_height = blf.dimensions(font_id, "Obj gốc")
                blf.color(font_id, 0.82, 0.88, 0.9, 1.0)
                blf.position(font_id, x_pos + text_width, y_pos, 0)
                blf.draw(font_id, f" ({hud_data['CMC_ReferenceNumber']})")

        elif hud_data["CMC_IsReferenceObject"] == True:
            y_pos -= 25
            blf.color(font_id, 1.0, 0.8, 0.1, 1.0)
            blf.position(font_id, x_pos, y_pos, 0)
            blf.draw(font_id, f"Obj tham chiếu ({hud_data['CMC_RootObjectName']})")

        if hud_data["CMC_RootObjectName"]:
            y_pos -= 25
            blf.color(font_id, 0.8, 0.8, 0.8, 1.0) 
            blf.position(font_id, x_pos, y_pos, 0)
            blf.draw(font_id, "Tên Prefab: ")
            
            text_width, text_height = blf.dimensions(font_id, "Tên Prefab: ")
            blf.color(font_id, 0.9, 0.8, 0.2, 1.0)
            blf.position(font_id, x_pos + text_width, y_pos, 0)
            blf.draw(font_id, f"{hud_data['CMC_RootObjectName']}")

        y_pos -= 25
        blf.color(font_id, 0.5, 0.9, 0.5, 1.0)
        blf.position(font_id, x_pos, y_pos, 0)
        blf.draw(font_id, f"(sX): {hud_data['CMC_Width']:.2f}m x (sY): {hud_data['CMC_Depth']:.2f}m x (sZ): {hud_data['CMC_Height']:.2f}m")

        y_pos -= 25
        blf.color(font_id, 0.4, 0.8, 0.9, 1.0)
        blf.position(font_id, x_pos, y_pos, 0)
        blf.draw(font_id, f"(rX): {hud_data['CMC_Rotation_X']:.2f}m x (rY): {hud_data['CMC_Rotation_Y']:.2f}m x (rZ): {hud_data['CMC_Rotation_Z']:.2f}m")

        #
        y_pos -= 25
        blf.size(font_id, 12)
        blf.color(font_id, 0.8, 0.8, 0.8, 1.0)
        blf.position(font_id, x_pos, y_pos, 0)
        blf.draw(font_id, f"Refresh Time: {hud_data['currentRefreshIndexCount']} / {hud_data['neededRefreshIndexCount']}")
        pass

    except Exception as e:
        print(f"Hàm Vẽ HUD Xảy Ra Lỗi: {e}")

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

last_active_obj = None

def check_change_active_object(context):
    global last_active_obj
    
    current_obj = bpy.context.active_object
    selected = bpy.context.selected_objects

    # 1. TRƯỜNG HỢP: Đổi từ Object này sang Object khác
    if current_obj and current_obj != last_active_obj:
        # Chỉ cập nhật khi object nằm trong danh sách chọn (tránh lag khi click nhầm)
        if current_obj in selected:
            update_object_stats(bpy.context.scene)
            last_active_obj = current_obj
            # print(f"Đã cập nhật dữ liệu cho: {current_obj.name}")
            print(f"Bạn Click chọn object {current_obj.name} - đã cập nhật dữ liệu HUD (Select)")

    # 2. TRƯỜNG HỢP: Click ra ngoài hoặc Object Active không còn được chọn
    if not selected or (current_obj not in selected):
        if last_active_obj is not None: # Chỉ reset một lần duy nhất để tiết kiệm CPU
            reset_hud_data(hud_data)
            last_active_obj = None
            print("Bạn Click khỏi tất cả object - đã xóa dữ liệu HUD (Deselect)")
        return False

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def toggle_hud(enable):
    global _handle
    if enable and _handle is None:
        # 1. Đăng ký vẽ GPU
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL'
        )
        # 2. Đăng ký sự kiện thay đổi lựa chọn
        # if update_object_stats not in bpy.app.handlers.depsgraph_update_post:
        #     bpy.app.handlers.depsgraph_update_post.append(update_object_stats)
            
    elif not enable and _handle is not None:
        # 1. Gỡ vẽ GPU
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
        # 2. Gỡ sự kiện
        # if update_object_stats in bpy.app.handlers.depsgraph_update_post:
        #     bpy.app.handlers.depsgraph_update_post.remove(update_object_stats)

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def get_world_dimensions(obj):
    """
    Trả về kích thước thực tế của Object trong không gian thế giới (World Space).
    Tính toán dựa trên Bounding Box và Matrix World.
    """
    if not obj or obj.type == 'GPENCIL':
        return Vector((0.0, 0.0, 0.0))

    # Lấy tọa độ 8 góc của Bounding Box và nhân với ma trận thế giới
    # matrix_world giúp tính cả Location, Rotation và Scale
    bbox_world = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]

    # Khởi tạo giá trị cực đại/cực tiểu từ điểm đầu tiên
    first_corner = bbox_world[0]
    min_x, min_y, min_z = first_corner
    max_x, max_y, max_z = first_corner

    # Duyệt qua các góc còn lại để tìm phạm vi bao phủ (Min/Max)
    for corner in bbox_world[1:]:
        if corner.x < min_x: min_x = corner.x
        if corner.x > max_x: max_x = corner.x
        
        if corner.y < min_y: min_y = corner.y
        if corner.y > max_y: max_y = corner.y
        
        if corner.z < min_z: min_z = corner.z
        if corner.z > max_z: max_z = corner.z

    return Vector((max_x - min_x, max_y - min_y, max_z - min_z))