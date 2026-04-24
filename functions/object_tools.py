import bpy
import time
import json
import os
from .. import utils

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def create_custom_property(obj, prop_name, default_value, force_update=False):
    """
    Tạo một Custom Property cho object nếu nó chưa tồn tại.
    """
    # 1. Kiểm tra xem đối tượng có hợp lệ không
    if obj is None:
        print("Thất bại: Không có object nào được chỉ định.")
        return False

    try:
        # 2. Kiểm tra xem property đã tồn tại chưa
        if prop_name in obj.keys():
            print(f"Thông báo: Property '{prop_name}' đã tồn tại trên '{obj.name}'. Không tạo mới.")
            return True
        
        # 3. Tiến hành tạo mới
        # Blender sẽ tự động xác định kiểu dữ liệu (String, Int, Float) dựa trên default_value
        obj[prop_name] = default_value
        
        # 4. (Tùy chọn) Thiết lập thêm metadata cho property (min, max, description)
        # Lưu ý: Chỉ áp dụng được cho kiểu số (int/float)
        if isinstance(default_value, (int, float)):
            obj.id_properties_ui(prop_name).update(description="Mô tả cho " + prop_name)

        print(f"Thành công: Đã tạo property '{prop_name}' cho '{obj.name}'.")
        return True

    except Exception as e:
        print(f"Thất bại: Có lỗi xảy ra khi tạo property: {e}")
        return False

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def generate_unique_id(index_offset=0):
    """
    Tạo một ID duy nhất dựa trên timestamp (giây) + số thứ tự.
    Kết quả trả về kiểu Int.
    """
    # Lấy timestamp hiện tại (ví dụ: 1713770000)
    timestamp = int(time.time())
    # Cộng thêm index_offset để phân biệt các object xử lý cùng 1 lúc
    return timestamp + index_offset

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def make_root(context, force = False):
    selected_objs = context.selected_objects
    if not selected_objs:
        return False

    for i, obj in enumerate(selected_objs):

        # Nếu Object được tạo từ Shift D => force = true
        if force == False:
            # Nếu ID đã tồn tại và có giá trị lớn hơn 0, bỏ qua object này
            if "CMC_Id" in obj.keys() and obj["CMC_Id"] > 0:
                print(f"Bỏ qua '{obj.name}': Đã có ID {obj['CMC_Id']}")
                continue

        unique_id = generate_unique_id(i)
        
        # 1. Thiết lập ID
        obj["CMC_Id"] = unique_id

        # 2. Thiết lập IsRootObject = True (Trong Blender Bool được lưu là Int 1 hoặc 0)
        obj["CMC_IsRootObject"] = True
        
        # 3. Thiết lập RootObjectId (Gán mặc định là -1 để chờ set sau)
        obj["CMC_RootObjectId"] = -1

        # 4. RootObjectName
        obj["CMC_RootObjectName"] = ""

        # 5. Thiết lập Kích thước
        dims = utils.get_world_dimensions(obj)
        obj["CMC_X_Width"] = dims.x
        obj["CMC_Y_Depth"] = dims.y
        obj["CMC_Z_Height"] = dims.z

        #
        id_ui = obj.id_properties_ui("CMC_Id")
        id_ui.update(
            min=unique_id,
            max=unique_id,
            description="DỮ LIỆU HỆ THỐNG: Không thể chỉnh sửa"
        )
        
        root_ui = obj.id_properties_ui("CMC_IsRootObject")
        root_ui.update(description="Mark this object as a Root reference")

        # ----------
        # ----------
        # THÔNG BÁO - Start

        # Chuẩn bị nội dung thông báo
        msg = [
            "Tạo Bản Gốc Thành Công",
            f"Id: {obj['CMC_Id']}",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thông Báo Tối Thượng", icon='CHECKMARK')

        # THÔNG BÁO _ Finish
        # ----------
        # ----------

        # ----------
        # ----------
        # Cập nhật HUD - Start
        utils.refresh_hud_data(obj, op_name="MAKE ROOT")
        # Cập nhật HUD - Finish
        # ----------
        # ----------

    print(f"✅ Đã thực hiện MakeRoot cho {len(selected_objs)} objects.")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def make_reference(context):
    selected_objs = context.selected_objects
    if not selected_objs:
        return False

    for i, obj in enumerate(selected_objs):
        unique_id = generate_unique_id(i)
        
        # 1. Thiết lập ID duy nhất cho bản thân nó
        obj["CMC_Id"] = unique_id
        
        # 2. Thiết lập IsRootObject = False
        obj["CMC_IsRootObject"] = False
        
        # 3. Thiết lập RootObjectId (Gán mặc định là -1 để chờ set sau)
        obj["CMC_RootObjectId"] = -1

        # 4. RootObjectName
        obj["CMC_RootObjectName"] = ""

        # 5. Thiết lập Kích thước
        dims = utils.get_world_dimensions(obj)
        obj["CMC_X_Width"] = dims.x
        obj["CMC_Y_Depth"] = dims.y
        obj["CMC_Z_Height"] = dims.z
        
        # Cập nhật UI metadata
        id_ui = obj.id_properties_ui("CMC_Id")
        id_ui.update(
            min=unique_id,
            max=unique_id,
            description="DỮ LIỆU HỆ THỐNG: Không thể chỉnh sửa"
        )

        obj.id_properties_ui("CMC_IsRootObject").update(description="This is a reference object")
        obj.id_properties_ui("CMC_RootObjectId").update(description="ID of the parent Root object")

    # ----------
    # ----------
    # Cập nhật HUD - Start
    utils.refresh_hud_data(obj, op_name="MAKE ROOT")
    # Cập nhật HUD - Finish
    # ----------
    # ---------- 

    print(f"✅ Đã thực hiện MakeReference cho {len(selected_objs)} objects.")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def make_root_from_reference(context):
    selected_objs = context.selected_objects
    active_obj = context.active_object

    # 1. Kiểm tra điều kiện: Phải chọn đúng 2 object
    if len(selected_objs) != 2 or active_obj is None:
        print("Lỗi: Hãy chọn đúng 2 object (A và A_Root), chọn A_Root sau cùng.")
        return False

    # Xác định object còn lại (Object A - Reference)
    other_obj = next(obj for obj in selected_objs if obj != active_obj)

    # 2. Kiểm tra điều kiện ID phải giống nhau (chứng tỏ vừa Alt+D xong)
    if "CMC_Id" not in active_obj.keys() or "CMC_Id" not in other_obj.keys():
        print("Lỗi: Một trong hai object chưa có ID.")

        # ----------
        # ---------- || ----------
        # ---------- || ---------- || ----------
        # THÔNG BÁO - Start

        # Chuẩn bị nội dung thông báo
        msg = [
            "Tạo Bản Gốc Không Thành Công",
            "Một trong hai Object chưa có ID",
            f"Bản Gốc:        [{active_obj['CMC_Id']}] - {active_obj.name}",
            f"Bản Tham Chiếu: [{other_obj['CMC_Id']}] - {other_obj.name}",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thông Báo Tối Thượng", icon='ERROR')

        # THÔNG BÁO _ Finish
        # ---------- || ---------- || ----------
        # ---------- || ----------
        # ----------

        return False
    
    shared_id = active_obj["CMC_Id"]
    if shared_id != other_obj["CMC_Id"]:
        print("Lỗi: ID của hai object không giống nhau. Không thể thiết lập liên kết Root.")
        
        # ----------
        # ---------- || ----------
        # ---------- || ---------- || ----------
        # THÔNG BÁO - Start

        # Chuẩn bị nội dung thông báo
        msg = [
            "Tạo Bản Gốc Không Thành Công",
            "ID của hai Object không giống nhau. Không thể thiết lập liên kết Root",
            f"Bản Gốc:        [{active_obj['CMC_Id']}] - {active_obj.name}",
            f"Bản Tham Chiếu: [{other_obj['CMC_Id']}] - {other_obj.name}",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thông Báo Tối Thượng", icon='ERROR')

        # THÔNG BÁO _ Finish
        # ---------- || ---------- || ----------
        # ---------- || ----------
        # ----------
        
        return False

    # --- TIẾN HÀNH CHUYỂN ĐỔI ---

    # A. Thiết lập cho A_Root (Active Object)
    # Giữ nguyên ID cũ làm ID gốc
    active_obj["CMC_IsRootObject"] = True
    active_obj["CMC_RootObjectId"] = -1 # Root thì không tham chiếu ai cả
    
    # Cập nhật UI cho A_Root
    active_obj.id_properties_ui("CMC_Id").update(min=shared_id, max=shared_id)
    active_obj.id_properties_ui("CMC_IsRootObject").update(description="This is the Library Root")

    # B. Thiết lập cho A (Other Object - Reference)
    # 1. Tạo ID mới cho A để nó là duy nhất
    new_id_for_a = int(time.time()) + 7 # +7 để chắc chắn khác biệt hoàn toàn
    
    # Trước khi đổi ID mới, phải reset khóa min/max cũ
    other_obj.id_properties_ui("CMC_Id").update(min=0, max=2000000000) 
    
    other_obj["CMC_Id"] = new_id_for_a
    other_obj["CMC_IsRootObject"] = False
    other_obj["CMC_RootObjectId"] = shared_id # Tham chiếu về ID của A_Root
    
    # Khóa ID mới của A
    other_obj.id_properties_ui("CMC_Id").update(min=new_id_for_a, max=new_id_for_a)
    other_obj.id_properties_ui("CMC_RootObjectId").update(min=shared_id, max=shared_id)

    # ----------
    # ---------- || ----------
    # ---------- || ---------- || ----------
    # THÔNG BÁO - Start

    # Chuẩn bị nội dung thông báo
    msg = [
        "Tạo Bản Gốc Thành Công",
        f"Bản Gốc:        [{active_obj['CMC_Id']}] - {active_obj.name}",
        f"Bản Tham Chiếu: [{other_obj['CMC_Id']}] - {other_obj.name}",
    ]
    # Gọi hàm hiển thị Popup nổi bật
    utils.show_detailed_message(msg, title="Thông Báo Tối Thượng", icon='CHECKMARK')

    # THÔNG BÁO _ Finish
    # ---------- || ---------- || ----------
    # ---------- || ----------
    # ----------

    # ----------
    # ----------
    # Cập nhật HUD - Start
    utils.refresh_hud_data(active_obj, op_name="MAKE ROOT")
    # Cập nhật HUD - Finish
    # ----------
    # ----------

    print(f"✅ Thành công! '{active_obj.name}' đã thành Root của '{other_obj.name}'")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ Hàm đồng bộ hóa sau khi Alt + D những Object Reference (Tạo group nhiểu Object trong Scene)
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_reference_instances(context):
    selected_objs = context.selected_objects
    if not selected_objs:
        return False

    # --- BƯỚC 1: KIỂM TRA ĐIỀU KIỆN ---
    
    # Lấy thông tin từ object đầu tiên làm mẫu để so sánh
    first_obj = selected_objs[0]
    
    # Kiểm tra xem có đủ các thuộc tính cần thiết không
    required_keys = ["CMC_Id", "CMC_IsRootObject", "CMC_RootObjectId"]
    if not all(k in first_obj.keys() for k in required_keys):
        print("Lỗi: Object mẫu không có đủ thuộc tính ID/Root.")
        return False

    reference_root_id = first_obj["CMC_RootObjectId"]

    for obj in selected_objs:
        # Điều kiện 1: Tất cả phải là Reference (IsRootObject = False)
        # Trong Blender, False được lưu là 0 hoặc False tùy cách bạn gán, ta kiểm tra cả hai
        if obj.get("CMC_IsRootObject") is True or obj.get("CMC_IsRootObject") == 1:
            print(f"Lỗi: Object '{obj.name}' là Root. Hàm này chỉ dành cho Reference.")
            return False
            
        # Điều kiện 2: Phải cùng ID và RootObjectId gốc
        # if obj.get("CMC_Id") != reference_id:
        #     print(f"Lỗi: Object '{obj.name}' có ID khác biệt. Chỉ đồng bộ các vật cùng nhóm Alt+D.")
        #     return False
            
        if obj.get("CMC_RootObjectId") != reference_root_id:
            print(f"Lỗi: Object '{obj.name}' trỏ về Root khác. Không thể đồng bộ chung.")
            return False

    # --- BƯỚC 2: TÌM TÊN CỦA ROOT OBJECT ---
    root_name_found = "Unknown_Root"
    # Duyệt qua toàn bộ object trong file để tìm object có ID khớp với RootObjectId
    for o in bpy.data.objects:
        # Kiểm tra nếu object đó có ID và IsRootObject = True
        if o.get("CMC_Id") == reference_root_id and (o.get("CMC_IsRootObject") is True or o.get("CMC_IsRootObject") == 1):
            root_name_found = o.name
            break
    
    if root_name_found == "Unknown_Root":
        print(f"Cảnh báo: Không tìm thấy Root Object có ID {reference_root_id} trong file này.")

    # --- BƯỚC 3: THỰC THI (Nếu vượt qua hết các kiểm tra trên) ---

    count = 0
    # Lấy timestamp cơ sở
    base_time = int(time.time())

    for i, obj in enumerate(selected_objs):
        # Chỉ xử lý các object đã có ID (để tránh gán nhầm cho object rác)
        if "CMC_Id" in obj.keys():
            # 1. Tạo ID mới duy nhất
            new_unique_id = base_time + i
            
            # 2. Mở khóa tạm thời (vì trước đó ta đã set min = max)
            id_ui = obj.id_properties_ui("CMC_Id")
            id_ui.update(min=0, max=2147483647) # Max của kiểu Int32
            
            # 3. Gán ID mới
            obj["CMC_Id"] = new_unique_id
            
            # 4. Khóa lại ngay lập tức để bảo vệ dữ liệu
            id_ui.update(min=new_unique_id, max=new_unique_id)
            
            # 5. Cập nhật RootObjectName
            obj["CMC_RootObjectName"] = root_name_found

            count += 1

    # ----------
    # ----------
    # Cập nhật HUD - Start
    utils.refresh_hud_data(obj, op_name="MAKE ROOT")
    # Cập nhật HUD - Finish
    # ----------
    # ----------

    print(f"✅ Đã đồng bộ (Sync) và làm mới ID cho {count} objects.")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_root_instances(context):
    """
    Chỉ đồng bộ hóa cho các Root Object: 
    Cập nhật RootObjectName khớp với tên object hiện tại.
    """
    updated_count = 0
    
    # Duyệt qua toàn bộ object trong file
    for obj in bpy.data.objects:
        # Kiểm tra xem có phải là Root Object không
        is_root = obj.get("CMC_IsRootObject")
        
        if is_root is True or is_root == 1:
            # Lấy tên hiện tại trong Outliner
            current_name = obj.name
            
            # Cập nhật vào thuộc tính RootObjectName
            if obj.get("CMC_RootObjectName") != current_name:
                obj["CMC_RootObjectName"] = current_name
                
                # Cập nhật UI để người dùng biết đây là tên định danh
                obj.id_properties_ui("CMC_RootObjectName").update(
                    description=f"IDENTIFIER: Matches object name for Unity linking"
                )
                updated_count += 1
                
    # ----------
    # ----------
    # Cập nhật HUD - Start
    utils.refresh_hud_data(obj, op_name="MAKE ROOT")
    # Cập nhật HUD - Finish
    # ----------
    # ----------

    print(f"✅ Đã đồng bộ RootObjectName cho {updated_count} Root Objects.")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def get_or_create_collection(name):
    """Lấy collection đã có hoặc tạo mới nếu chưa tồn tại"""
    collection = bpy.data.collections.get(name)
    if not collection:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def move_to_collection(obj, target_col):
    """
    Di chuyển object vào collection đích một cách thông minh.
    """
    # 1. Kiểm tra xem object đã nằm trong collection đích chưa
    if obj.name in target_col.objects:
        # Nếu đã ở đúng chỗ, ta chỉ cần đảm bảo nó không nằm ở collection nào khác
        # (Tránh tình trạng một object hiện ở 2 nơi)
        for col in list(obj.users_collection):
            if col != target_col:
                col.objects.unlink(obj)
        return # Thoát sớm để tiết kiệm tài nguyên

    # 2. Nếu chưa có trong collection đích, tiến hành link
    target_col.objects.link(obj)

    # 3. Xóa khỏi tất cả các collection cũ
    for col in list(obj.users_collection):
        if col != target_col:
            col.objects.unlink(obj)

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_position_data(context):

    # 1. Khởi tạo/Lấy các Collection
    demo_col = get_or_create_collection("CMC_Demo_Scene")
    library_col = get_or_create_collection("CMC_Library_Scene")
    
    root_objects = []
    
    # 2. Duyệt qua toàn bộ object trong file để phân loại
    # Sử dụng list() để tránh lỗi khi thay đổi collection trong lúc duyệt
    all_objs = list(bpy.data.objects)
    
    for obj in all_objs:
        is_root = obj.get("CMC_IsRootObject")
        root_id = obj.get("CMC_RootObjectId")
        
        # KIỂM TRA ĐIỀU KIỆN REFERENCE
        # (Lưu ý: Blender lưu bool là 0/1 hoặc True/False tùy cách gán)
        if (is_root is False or is_root == 0) and (root_id is not None and root_id != -1):
            move_to_collection(obj, demo_col)
            
        # KIỂM TRA ĐIỀU KIỆN ROOT
        elif is_root is True or is_root == 1:
            move_to_collection(obj, library_col)
            root_objects.append(obj)

    # 3. SẮP XẾP ROOT OBJECT VÀO KHU VỰC LIBRARY
    # Config vị trí: Bạn có thể thay đổi các thông số này
    start_x = 20.0  # Đẩy khu vực Library ra xa trục tọa độ (Demo thường ở 0,0,0)
    spacing = 5.0   # Khoảng cách giữa mỗi object trong hàng
    
    # Sắp xếp danh sách root theo tên để hàng đợi luôn ổn định
    root_objects.sort(key=lambda o: o.name)
    
    for i, root_obj in enumerate(root_objects):
        # Sắp xếp thành một hàng dọc theo trục X
        root_obj.location.x = start_x + (i * spacing)
        root_obj.location.y = 0.0
        root_obj.location.z = 0.0
        
        # Khóa vị trí này lại nếu bạn muốn (tùy chọn)
        # root_obj.lock_location = (True, True, True)

    # ----------
    # ----------
    # Cập nhật HUD - Start
    utils.refresh_hud_data(obj, op_name="MAKE ROOT")
    # Cập nhật HUD - Finish
    # ----------
    # ----------

    print(f"✅ Đã dọn dẹp xong: {len(root_objects)} Roots trong Library, các Ref đã vào DemoScene.")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def export_position_data_to_json(context):

    # Đường dẫn xuất file
    output_path = "E:/Unity_Projects/My_First_Game/Assets/TestImportAssetFromBlender/Scripts/JSON_Data/positions.json"
    
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    selected_objects = context.selected_objects
    if not selected_objects: 
        return False, 0

    data = []
    for obj in selected_objects:
        # 1. Lấy tọa độ World Space
        pos = obj.matrix_world.translation
        
        # 2. Thu thập dữ liệu Custom Properties (với giá trị mặc định nếu thiếu)
        custom_props = {
            "CMC_Id": obj.get("CMC_Id", -1),
            "CMC_IsRootObject": bool(obj.get("CMC_IsRootObject", False)),
            "CMC_RootObjectId": obj.get("CMC_RootObjectId", -1),
            "CMC_RootObjectName": obj.get("CMC_RootObjectName", "")
        }

        # 3. Đóng gói dữ liệu
        data.append({
            "name": obj.name.rsplit('.', 1)[0],
            # Toạ độ đã đảo trục Blender (Z-up) -> Unity (Y-up) theo công thức của bạn
            "pos": {
                "x": pos.x * (-1),
                "y": pos.z,
                "z": pos.y * (-1)
            },
            # Đưa toàn bộ metadata vào mục "properties"
            "properties": custom_props
        })

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Đã xuất {len(data)} đối tượng sang JSON tại: {output_path}")
        return True, len(data)
    except Exception as e:
        print(f"❌ Lỗi khi xuất file: {e}")
        return False, 0
    
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
