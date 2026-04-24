import bpy
import blf
from mathutils import Vector

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

    "": 0,

    # X: Ngang (Width)
    # Y: Sâu (Depth)
    # Z: Cao (Height)
    "CMC_X_Width": 0,
    "CMC_Y_Depth": 0,
    "CMC_Z_Height": 0,

    # Biến đếm làm mới dữ liệu
    "currentRefreshIndexCount": 0,
    "neededRefreshIndexCount": 0
}

# Hàm hỗ trợ đánh dấu có sự thay đổi dữ liệu, chạy để hiển thị dữ liệu mới
def refresh_hud_data(obj, op_name="Update"):
    global hud_data
    if not obj: return
    
    # 1. Tăng chỉ số, ép chỉ số cần cập nhật tăng lên
    hud_data["neededRefreshIndexCount"] += 1

    # 2. Chủ động gọi hàm cập nhật dữ liệu luôn
    update_object_stats(bpy.context.scene)

    # 3. Vẫn nên tag_redraw để chữ trên màn hình nhảy số ngay
    bpy.context.area.tag_redraw()

    print(f"HUD - refresh_hud_data: '{hud_data.get('neededRefreshIndexCount')}'")

# --- BƯỚC 1: HÀM TÍNH TOÁN (Chỉ chạy khi có thay đổi) ---
def update_object_stats(scene):
    global hud_data
    # 1. Lấy object active và danh sách đang chọn
    obj = bpy.context.active_object
    selected = bpy.context.selected_objects

    print(f"HUD - update_object_stats: '{hud_data.get('name')}'")

    # ĐIỀU KIỆN: Nếu không có object nào được chọn (click ra ngoài)
    # Hoặc object active không nằm trong danh sách đang chọn
    if not selected or (obj not in selected):
        if hud_data.get("name") != "":
            hud_data["name"] = ""
            hud_data["props"] = {}
            hud_data["CMC_Id"] = "None"
            hud_data["CMC_IsRootObject"] = False
            hud_data["CMC_IsReferenceObject"] = False
            hud_data["CMC_RootObjectName"] = ""
            hud_data["CMC_X_Width"] = 0,
            hud_data["CMC_Y_Depth"] = 0,
            hud_data["CMC_Z_Height"] = 0,
            print(f"DEBUG: HUD Cleared | Name: '{hud_data.get('name')}'")
        return

    # TRƯỜNG HỢP 2: Kiểm tra xem có cần Update không
    # Cần update khi: Đổi tên Object HOẶC Chỉ số Refresh bị lệch
    is_new_object = obj.name != hud_data.get("name")
    is_forced_refresh = hud_data["neededRefreshIndexCount"] != hud_data["currentRefreshIndexCount"]

    if not (is_new_object or is_forced_refresh):
        return

    # --- BẮT ĐẦU TÍNH TOÁN (Chỉ chạy khi lọt qua các bộ lọc trên) ---
    
    # Đồng bộ lại chỉ số đệm
    hud_data["currentRefreshIndexCount"] = hud_data["neededRefreshIndexCount"]
    
    hud_data["name"] = obj.name
    hud_data["type"] = obj.type
    
    # Lấy Custom Properties an toàn
    hud_data["props"] = {k: obj[k] for k in obj.keys() if k not in '_RNA_UI'}
    hud_data["CMC_Id"] = hud_data["props"].get("CMC_Id", "None")
    hud_data["CMC_IsRootObject"] = hud_data["props"].get("CMC_IsRootObject", False)
    
    if hud_data["props"].get("CMC_IsRootObject", False) == False and hud_data["props"].get("CMC_RootObjectId", -1) != -1:
        hud_data["CMC_IsReferenceObject"] = True
    else:
        hud_data["CMC_IsReferenceObject"] = False
     
    dims = get_world_dimensions(obj)
    hud_data["CMC_X_Width"] = dims.x
    hud_data["CMC_Y_Depth"] = dims.y
    hud_data["CMC_Z_Height"] = dims.z
    if "CMC_X_Width" in obj.keys():
        if obj.get("CMC_X_Width") != dims.x:
            obj["CMC_X_Width"] = dims.x
    if "CMC_Y_Depth" in obj.keys():
        if obj.get("CMC_Y_Depth") != dims.y:
            obj["CMC_Y_Depth"] = dims.y
    if "CMC_Z_Height" in obj.keys():
        if obj.get("CMC_Z_Height") != dims.z:
            obj["CMC_Z_Height"] = dims.z
    
    # 2. Tìm Object tham chiếu (Vòng lặp nặng nằm ở đây)
    # found_refs = []
    # for o in scene.objects:
    #     if o != obj and obj.name in o.name:
    #         found_refs.append(o.name)
    # hud_data["CMC_Id"] = found_refs

    # --- BƯỚC 2: TÌM TÊN CỦA ROOT OBJECT ---
    root_name_found = "Unknown_Root"
    reference_root_id = -1
    if hud_data["props"].get("CMC_IsRootObject", False) == False and hud_data["props"].get("CMC_RootObjectId", -1) != -1:
        reference_root_id = hud_data["props"].get("CMC_RootObjectId", -1)
        
        # Duyệt qua toàn bộ object trong file để tìm object có ID khớp với RootObjectId
        for o in bpy.data.objects:
            # Kiểm tra nếu object đó có ID và IsRootObject = True
            if o.get("CMC_Id") == reference_root_id and (o.get("CMC_IsRootObject") is True or o.get("CMC_IsRootObject") == 1):
                root_name_found = o.name
                hud_data["CMC_RootObjectName"] = root_name_found
                break
    
    if root_name_found == "Unknown_Root":
        print(f"Cảnh báo: Không tìm thấy Root Object có ID {reference_root_id} trong file này.")


#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

# def draw_callback_px(self, context):
#     # Lấy thông tin từ bpy.context thay vì tham số truyền vào để tránh lỗi Restrict
#     region = bpy.context.region
#     if not region: return

#     obj = bpy.context.active_object
#     if not obj: return

#     font_id = 0
#     blf.size(font_id, 18)
#     blf.color(font_id, 1.0, 0.8, 0.1, 1.0) # Màu vàng cam CMC

#     # Tọa độ vẽ (Góc dưới bên trái)
#     x_pos = 25 
#     y_pos = 50 # Cách đáy màn hình 50 pixel

#     # Vẽ thông tin Object
#     blf.position(font_id, x_pos, y_pos, 0)
#     blf.draw(font_id, f"Obj đang chọn: {obj.name}")

#     blf.color(font_id, 0.4, 1.0, 0.4, 1.0)
#     blf.position(font_id, x_pos, y_pos - 25, 0)
#     blf.draw(font_id, f"Loại: {obj.type}") 

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

# --- BƯỚC 2: HÀM VẼ HUD (Chỉ lấy dữ liệu từ hud_data ra vẽ) ---
def draw_callback_px(self, context):
    global hud_data

    # Nếu name là rỗng (đã được clear ở bước trên), ngừng vẽ ngay
    if not hud_data.get("name"):

        # print(f"DEBUG: '{hud_data.get('name')}'")
        return

    font_id = 0
    blf.size(font_id, 18)
    x_pos, y_pos = 30, 200
    
    # Vẽ tên (Màu xanh lá)
    # blf.color(font_id, 0.0, 1.0, 0.0, 1.0)
    # blf.position(font_id, x_pos, y_pos, 0)
    # blf.draw(font_id, f"Đang chọn: {hud_data['name']}")

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
    elif hud_data["CMC_IsReferenceObject"] == True:
        y_pos -= 25
        blf.color(font_id, 1.0, 0.8, 0.1, 1.0)
        blf.position(font_id, x_pos, y_pos, 0)
        blf.draw(font_id, f"Obj tham chiếu ({hud_data['CMC_RootObjectName']})")

    y_pos -= 25
    blf.color(font_id, 0.5, 0.9, 0.5, 1.0)
    blf.position(font_id, x_pos, y_pos, 0)
    blf.draw(font_id, f"(X): {hud_data['CMC_X_Width']:.2f}m x (Y): {hud_data['CMC_Y_Depth']:.2f}m x (Z): {hud_data['CMC_Z_Height']:.2f}m")

    #
    y_pos -= 25
    blf.size(font_id, 12)
    blf.color(font_id, 0.8, 0.8, 0.8, 1.0)
    blf.position(font_id, x_pos, y_pos, 0)
    blf.draw(font_id, f"Refresh Time: {hud_data['currentRefreshIndexCount']} / {hud_data['neededRefreshIndexCount']}")
    

# def toggle_hud(enable):
#     global _handle
#     if enable and _handle is None:
#         # Sử dụng 'WINDOW' để vẽ đè lên toàn bộ cửa sổ làm việc
#         _handle = bpy.types.SpaceView3D.draw_handler_add(
#             draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL'
#         )
#     elif not enable and _handle is not None:
#         bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
#         _handle = None

def toggle_hud(enable):
    global _handle
    if enable and _handle is None:
        # 1. Đăng ký vẽ GPU
        _handle = bpy.types.SpaceView3D.draw_handler_add(
            draw_callback_px, (None, None), 'WINDOW', 'POST_PIXEL'
        )
        # 2. Đăng ký sự kiện thay đổi lựa chọn
        if update_object_stats not in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.append(update_object_stats)
            
    elif not enable and _handle is not None:
        # 1. Gỡ vẽ GPU
        bpy.types.SpaceView3D.draw_handler_remove(_handle, 'WINDOW')
        _handle = None
        # 2. Gỡ sự kiện
        if update_object_stats in bpy.app.handlers.depsgraph_update_post:
            bpy.app.handlers.depsgraph_update_post.remove(update_object_stats)

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