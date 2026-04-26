import bpy
import time
import json
import os
from .. import utils
from .. import logic
import mathutils
from mathutils import Vector

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

        # Kiểm Tra Object Có Đang Có Tham Chiếu Nào Không
        exist_reference_object = check_exist_reference_object(context, obj)
        if exist_reference_object != None:
            # ----------
            # ----------
            # THÔNG BÁO - Start

            # Chuẩn bị nội dung thông báo
            msg = [
                f"Tạo Bản Gốc Thất Bại [Id: {obj['CMC_Id']}]",
                "Nguyên nhân: Bản Gốc Đang Có Tham Chiếu Sau:"
                f"{exist_reference_object}"
            ]
            # Gọi hàm hiển thị Popup nổi bật
            utils.show_detailed_message(msg, title="Có Gì Đó Xảy Ra!", icon='CHECKMARK')

            # THÔNG BÁO _ Finish
            # ----------
            # ----------
            return False

        # Nếu Object được tạo từ Shift D => force = true
        if force == False:
            # Nếu ID đã tồn tại và có giá trị lớn hơn 0, bỏ qua object này
            if "CMC_Id" in obj.keys() and obj["CMC_Id"] > 0:
                print(f"Bỏ qua '{obj.name}': Đã có ID {obj['CMC_Id']}")

                # ----------
                # ----------
                # THÔNG BÁO - Start

                # Chuẩn bị nội dung thông báo
                msg = [
                    f"Tạo Bản Gốc Thất Bại [Id: {obj['CMC_Id']}]",
                    "Nguyên nhân: Bản Gốc Đã Được Tạo Trước Đó"
                ]
                # Gọi hàm hiển thị Popup nổi bật
                utils.show_detailed_message(msg, title="Có Gì Đó Xảy Ra!", icon='CHECKMARK')

                # THÔNG BÁO _ Finish
                # ----------
                # ----------

                return False

        unique_id = generate_unique_id(i)
        
        # 1. Thiết lập ID
        obj["CMC_Id"] = unique_id

        # 2. Thiết lập IsRootObject = True (Trong Blender Bool được lưu là Int 1 hoặc 0)
        obj["CMC_IsRootObject"] = True
        
        # 3. Thiết lập RootObjectId (Gán mặc định là -1 để chờ set sau)
        obj["CMC_RootObjectId"] = unique_id

        # 4. RootObjectName
        obj["CMC_RootObjectName"] = obj.name

        # 5. Đồng bộ hóa dữ liệu Object
        sync_object_data(context, obj)

        # 6. 
        obj["CMC_IsLastestCreate"] = False

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
            f"Tạo Bản Gốc Thành Công [Id: {obj['CMC_Id']}]",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thành Công Không Có Gì Sai!", icon='CHECKMARK')

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

def clear_object_data(context):

    obj = context.active_object

    if obj:
        # Lấy danh sách các key (tên thuộc tính)
        # Cần ép kiểu list() vì nếu xóa trực tiếp khi đang lặp sẽ bị lỗi logic
        keys = list(obj.keys())
        
        for key in keys:
            # Bỏ qua các thuộc tính hệ thống của Blender (thường bắt đầu bằng '_')
            # hoặc các thuộc tính đặc biệt như '_RNA_UI'
            del obj[key]
            
        print(f"✅ Đã xóa sạch Custom Properties của {obj.name}")

        # ----------
        # ----------
        # THÔNG BÁO - Start

        # Chuẩn bị nội dung thông báo
        msg = [
            f"Clear Data Của Object {obj.name} Thành Công",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thành Công Không Có Gì Sai!", icon='CHECKMARK')

        # THÔNG BÁO _ Finish
        # ----------
        # ----------  

        # ----------
        # ----------
        # Cập nhật HUD - Start
        utils.refresh_hud_data(obj, op_name="CLEAR DATA")
        # Cập nhật HUD - Finish
        # ----------
        # ----------

        return True
    else:
        msg = [
                f"Chưa Chọn Bất Kỳ Object Nào Trong Scene Để Clear Data!",
            ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Có Gì Đó Xảy Ra!", icon='ERROR')

        # THÔNG BÁO _ Finish
        # ----------
        # ---------- 
        return False



#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ Đồng bộ hóa dữ liệu Object
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_object_data(context, obj):
    dims = utils.get_world_dimensions(obj)
    obj["CMC_Width"] = dims.x
    obj["CMC_Depth"] = dims.y
    obj["CMC_Height"] = dims.z

    # Lấy Quaternion từ ma trận thế giới
    objQuaternionRotation = obj.matrix_world.to_quaternion()
    obj["CMC_Rotation_X"] = objQuaternionRotation.x
    obj["CMC_Rotation_Y"] = objQuaternionRotation.y
    obj["CMC_Rotation_Z"] = objQuaternionRotation.z
    obj["CMC_Rotation_Scalar_Part"] = objQuaternionRotation.w

    objPosition = obj.matrix_world.translation
    obj["CMC_Transform_X"] = objPosition.x
    obj["CMC_Transform_Y"] = objPosition.y
    obj["CMC_Transform_Z"] = objPosition.z

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ Kiểm Tra Có Tham Chiếu Tồn Tại
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def check_exist_reference_object(context, target_obj):
    global reference_object_list
    if target_obj.get("CMC_Id", "") and target_obj.get("CMC_IsRootObject", False) == True:
        get_reference_object_list()
        if len(reference_object_list) > 0:
            for reference_object in reference_object_list:
                if reference_object.get("CMC_RootObjectId") == target_obj.get("CMC_Id", ""):
                    return f"Tên: {reference_object.name} [Id: {reference_object.get('CMC_Id')}]"

    return None

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

        # 5. Đồng bộ hóa dữ liệu Object
        sync_object_data(context, obj)

        # 6.
        obj["CMC_IsLastestCreate"] = False
        
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

def make_reference_from_root(context):
    selected_objs = context.selected_objects
    active_obj = context.active_object # Đây sẽ là bản Reference (chọn sau cùng)

    # 1. Kiểm tra điều kiện: Phải chọn đúng 2 object
    if len(selected_objs) != 2 or active_obj is None:
        msg = ["Lỗi: Chọn đúng 2 object", "Chọn bản GỐC trước, bản THAM CHIẾU sau cùng."]
        utils.show_detailed_message(msg, title="Sai Quy Trình", icon='ERROR')
        return False

    # Xác định object còn lại (Đây sẽ là bản Gốc - Root)
    root_obj = next(obj for obj in selected_objs if obj != active_obj)
    ref_obj = active_obj

    # 2. Kiểm tra tồn tại ID
    if "CMC_Id" not in root_obj.keys() or "CMC_Id" not in ref_obj.keys():
        msg = ["Lỗi: Thiếu ID", "Một trong hai object chưa có ID định danh."]
        utils.show_detailed_message(msg, title="Lỗi Dữ Liệu", icon='ERROR')
        return False
    
    # 3. Kiểm tra ID trùng khớp (Để xác nhận chúng là bản sao của nhau)
    shared_id = root_obj["CMC_Id"]
    if shared_id != ref_obj["CMC_Id"]:
        msg = [
            "ID Không Khớp", 
            "Hai object phải là bản sao Alt+D của nhau trước đó.",
            f"ID Gốc: {shared_id}",
            f"ID Tham Chiếu: {ref_obj['CMC_Id']}"
        ]
        utils.show_detailed_message(msg, title="Liên Kết Thất Bại", icon='ERROR')
        return False

    # --- TIẾN HÀNH CHUYỂN ĐỔI ---

    # A. Thiết lập cho BẢN GỐC (root_obj)
    root_obj["CMC_IsRootObject"] = True
    root_obj["CMC_RootObjectId"] = -1
    root_obj["CMC_RootObjectName"] = root_obj.name # Lưu tên để Unity tìm prefab
    
    # Khóa UI cho bản Gốc
    root_obj.id_properties_ui("CMC_Id").update(min=shared_id, max=shared_id)
    root_obj.id_properties_ui("CMC_IsRootObject").update(description="Đây là bản gốc trong Library")

    # B. Thiết lập cho BẢN THAM CHIẾU (ref_obj - Active Object)
    # Tạo ID mới duy nhất cho bản tham chiếu
    new_id_for_ref = int(time.time()) + 10 
    
    # Reset khóa cũ để ghi đè
    ref_obj.id_properties_ui("CMC_Id").update(min=0, max=2000000000) 
    
    ref_obj["CMC_Id"] = new_id_for_ref
    ref_obj["CMC_IsRootObject"] = False
    ref_obj["CMC_RootObjectId"] = shared_id # Trỏ về ID của bản Gốc
    ref_obj["CMC_RootObjectName"] = root_obj.name # Lưu tên bản gốc để Unity biết cần spawn prefab nào
    
    # Khóa ID mới cho bản Tham chiếu
    ref_obj.id_properties_ui("CMC_Id").update(min=new_id_for_ref, max=new_id_for_ref)
    ref_obj.id_properties_ui("CMC_RootObjectId").update(min=shared_id, max=shared_id)

    # 4. Thông báo và Cập nhật HUD
    msg = [
        "Thiết Lập Tham Chiếu Thành Công",
        f"Gốc (Root): {root_obj.name}",
        f"Tham Chiếu (Ref): {ref_obj.name}",
        f"Kết nối qua ID: {shared_id}"
    ]
    utils.show_detailed_message(msg, title="Thành Công", icon='CHECKMARK')
    
    # Cập nhật HUD cho Object đang chọn (Ref)
    utils.refresh_hud_data(ref_obj, op_name="MAKE REF")

    print(f"✅ Đã biến {ref_obj.name} thành bản tham chiếu của {root_obj.name}")
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


def sync_all_data(context):
    get_reference_object_list()
    get_root_object_list()

    # Đồng Bộ Hóa Danh Sách Object Tham Chiếu
        # Lấy Danh Sách Object Tham Chiếu

    # Đồng bộ hóa Danh Sách Object Gốc
        # Lấy Danh Sách Object Gốc

        # Đồng Bộ Từng Object Gốc
            
    if len(root_object_list) > 0:
        for object in root_object_list:
            sync_root_instance(object)

    # Đồng Bộ Hóa Tên + Vị Trí

        # root nếu đang nằm ngoài Collection =>
            # => Đưa vào một List tạm, sắp xếp theo thứ tự tạo root object (id)
                # => Đánh dấu root cuối cùng được đồng bộ đó là Lastest

    sync_position(context)

    return True

reference_object_list = []
def get_reference_object_list():
    global reference_object_list
    reference_object_list = []
    for object in bpy.data.objects:
        # Kiểm tra nếu object đó có ID và IsRootObject == False và CMC_RootObjectId != -1
        if object.get("CMC_Id") != "" and object.get("CMC_IsRootObject") == False and object.get("CMC_RootObjectId") != -1:
            reference_object_list.append(object)

    # Sắp Xếp Theo Thứ Tự Tăng Dần Của ID
    reference_object_list.sort(key=lambda x: x["CMC_Id"])

    return reference_object_list

root_object_list = []
def get_root_object_list():
    global root_object_list
    root_object_list = []
    for object in bpy.data.objects:
        # Kiểm tra nếu object đó có ID và IsRootObject = True
        if object.get("CMC_Id") != "" and object.get("CMC_IsRootObject") == True:
            root_object_list.append(object)

    # Sắp Xếp Theo Thứ Tự Tăng Dần Của ID
    root_object_list.sort(key=lambda x: x["CMC_Id"])

    return root_object_list

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_root_instance(root_object):
    root_object["CMC_RootObjectName"] = root_object.name

    # Duyệt Qua Danh Sách Object Tham Chiếu Để Đồng Bộ
    for reference_object in reference_object_list:
        if reference_object.get("CMC_RootObjectId", -1) == root_object.get("CMC_Id"):
            sync_reference_instance(reference_object, root_object)

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def sync_reference_instance(reference_object, root_object):

    reference_object["CMC_RootObjectName"] = root_object["CMC_RootObjectName"]

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def clear_lastest_create(context):

    for root_object in root_object_list:
        root_object["CMC_IsLastestCreate"] = False

    for reference_object in reference_object_list:
        reference_object["CMC_IsLastestCreate"] = False

    return True

def make_lastest_create(context):
    active_obj = context.active_object

    clear_lastest_create(context)

    active_obj["CMC_IsLastestCreate"] = True

    set_as_unique_anchor(context, active_obj)

    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def set_as_unique_anchor(context, target_obj):
    """
    Thiết lập một object làm điểm neo duy nhất, xóa bỏ các điểm neo cũ.
    """
    # 1. DỌN DẸP: Duyệt qua tất cả object trong cảnh
    # Chỉ duyệt trong scene hiện tại để tối ưu hiệu suất
    for obj in context.scene.objects:
        obj.show_name = False
        
        # Nếu object nào đang có màu của "Điểm neo" cũ (màu xanh dương nhẹ/lá)
        # thì reset về màu trắng mặc định (1, 1, 1, 1)
        if obj.color[0:3] == (0.5, 0.9, 0.5) or obj.get("CMC_IsLastestCreate", False) == False: 
            obj.color = (1.0, 1.0, 1.0, 1.0)

    # 2. THIẾT LẬP NEO MỚI
    if target_obj:
        target_obj.show_name = True
        # Dùng màu xanh lá nhẹ bạn thích (0.5, 0.9, 0.5)
        target_obj.color = (0.5, 0.9, 0.5, 1.0)
        
        # Đặt nó làm Active Object để các công cụ sắp xếp biết đường mà "bám" vào
        context.view_layer.objects.active = target_obj
        
        print(f"⚓ Đã đặt '{target_obj.name}' làm Điểm Neo duy nhất.")

    # 3. CẬP NHẬT VIEWPORT (Force Shading Mode)
    # Việc này giúp người dùng thấy ngay màu sắc mà không cần chỉnh tay
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Chuyển chế độ hiển thị màu sang 'OBJECT'
                    if space.shading.color_type != 'OBJECT':
                        space.shading.color_type = 'OBJECT'

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def sync_position(context):

    # 1. Khởi tạo/Lấy các Collection
    demo_scene_collection = get_or_create_collection("CMC_Demo_Scene")
    library_scene_collection = get_or_create_collection("CMC_Library_Scene")

    lastest_create_object = None
    if len(root_object_list) > 0:
        for r_object in root_object_list:
            if r_object.get("CMC_IsLastestCreate", False) == True:
                lastest_create_object = r_object
                break
        
        # Nếu chưa có Object nào được đánh dấu là tạo cuối cùng
        # Lấy Object đầu tiên làm Object này => Nhằm sắp xếp từ Object này
        if lastest_create_object == None:
            lastest_create_object = root_object_list[0]

    # Nếu lastest_create chưa có trong Library Collection 
    # => Set vị trí bắt đầu cho việc sắp xếp               
        if lastest_create_object.name in library_scene_collection.objects:
            # Nếu đã ở đúng chỗ, ta chỉ cần đảm bảo nó không nằm ở collection nào khác
            # (Tránh tình trạng một object hiện ở 2 nơi)
            for col in list(lastest_create_object.users_collection):
                if col != library_scene_collection:
                    col.objects.unlink(lastest_create_object)
        else:
            start_position_x = 5.0
            start_position_y = 0.0
            start_position_z = 0.0
            lastest_create_object.location.x = start_position_x
            lastest_create_object.location.y = start_position_y
            lastest_create_object.location.z = start_position_z

    # Lấy danh sách Root Object chưa có trong Library Collection 
    # => Sắp xếp chúng dựa trên lastest_create_object làm vị trí bắt đầu
    root_object_not_in_library_collection_list = []
    if len(root_object_list) > 0:
        for r_object in root_object_list:
            if r_object.name in library_scene_collection.objects:
                continue
            else:
                root_object_not_in_library_collection_list.append(r_object)

    if len(root_object_not_in_library_collection_list) > 0:
        # Loại bỏ lastest_create_object 
        for r_object in root_object_not_in_library_collection_list:
            if r_object["CMC_Id"] == lastest_create_object["CMC_Id"]:
                root_object_not_in_library_collection_list.remove(lastest_create_object)
                break

        # 1. Hủy chọn tất cả các object đang có để làm sạch scene
        bpy.ops.object.select_all(action='DESELECT')

        # 2. Thiết lập Active Object (Vật thể có viền vàng)
        bpy.context.view_layer.objects.active = lastest_create_object

        # 3. Chọn Active Object đó (Để nó có viền)
        lastest_create_object.select_set(True)

        # 4. Chọn danh sách các object khác (Vật thể có viền cam)
        for obj in root_object_not_in_library_collection_list:
            obj.select_set(True)

        # 5. Sắp xếp
        cfg = context.scene.cmc_sorting_config
        clear_lastest_create(context)
        logic.arrange_objects_grid(context, cfg, "+X++", True)

    # Đưa tất cả vào Collection 

    if len(root_object_list) > 0:
        for root_object in root_object_list:
            move_to_collection(root_object, library_scene_collection)
            sync_object_data(context,root_object)

    if len(reference_object_list) > 0:
        for reference_object in reference_object_list:
            move_to_collection(reference_object, demo_scene_collection)
            sync_object_data(context,reference_object)

    print(f"OBJECT TẠO CUỐI CÙNG: {lastest_create_object.name} ; {len(root_object_not_in_library_collection_list)}")

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
        print("Không có object nào được chọn để export.")

        # Lấy toàn bộ object thuộc về Scene mà bạn đang mở
        selected_objects = bpy.context.scene.objects
        print("Đã Chọn Toàn Bộ Object Trong Scene Để Export.")

        if len(selected_objects) == 0:
            # ----------
            # ----------
            # THÔNG BÁO - Start

            # Chuẩn bị nội dung thông báo
            msg = [
                f"Không Có Bất Kỳ Object Nào Trong Scene Để Export!",
            ]
            # Gọi hàm hiển thị Popup nổi bật
            utils.show_detailed_message(msg, title="Có Gì Đó Xảy Ra!", icon='ERROR')

            # THÔNG BÁO _ Finish
            # ----------
            # ---------- 
            return False

    data = []
    # for obj in selected_objects:
    #     # 1. Lấy tọa độ World Space
    #     pos = obj.matrix_world.translation
        
    #     # 2. Thu thập dữ liệu Custom Properties (với giá trị mặc định nếu thiếu)
    #     custom_props = {
    #         "CMC_Id": obj.get("CMC_Id", -1),
    #         "CMC_IsRootObject": bool(obj.get("CMC_IsRootObject", False)),
    #         "CMC_RootObjectId": obj.get("CMC_RootObjectId", -1),
    #         "CMC_RootObjectName": obj.get("CMC_RootObjectName", "")
    #     }

    #     # 3. Đóng gói dữ liệu
    #     data.append({
    #         "name": obj.name.rsplit('.', 1)[0],
    #         # Toạ độ đã đảo trục Blender (Z-up) -> Unity (Y-up) theo công thức của bạn
    #         "pos": {
    #             "x": pos.x * (-1),
    #             "y": pos.z,
    #             "z": pos.y * (-1)
    #         },
    #         # Đưa toàn bộ metadata vào mục "properties"
    #         "properties": custom_props
    #     })
    for obj in selected_objects:
        # 1. Lấy tọa độ World Space
        pos = obj.matrix_world.translation
        
        rotation_X = obj.get("CMC_Rotation_X", 0)
        rotation_Y = obj.get("CMC_Rotation_Y", 0)
        rotation_Z = obj.get("CMC_Rotation_Z", 0)
        rotation_Scalar_Part = obj.get("CMC_Rotation_Scalar_Part", 0)

        # 2. Thu thập dữ liệu Custom Properties (với giá trị mặc định nếu thiếu)
        custom_props = {
            "CMC_Id": obj.get("CMC_Id", -1),
            "CMC_IsRootObject": bool(obj.get("CMC_IsRootObject", False)),
            "CMC_RootObjectId": obj.get("CMC_RootObjectId", -1),
            "CMC_RootObjectName": obj.get("CMC_RootObjectName", ""),

            "CMC_Rotation_X" : obj.get("CMC_Rotation_X", 0),
            "CMC_Rotation_Y" : obj.get("CMC_Rotation_Y", 0),
            "CMC_Rotation_Z" : obj.get("CMC_Rotation_Z", 0),
            "CMC_Rotation_Scalar_Part" : obj.get("CMC_Rotation_Scalar_Part", 0),
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
            "rotation": {
                "x": rotation_X,
                "y": rotation_Z,
                "z": rotation_Y,
                "w": rotation_Scalar_Part * (-1)
            },
            # Đưa toàn bộ metadata vào mục "properties"
            "properties": custom_props
        })

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        print(f"✅ Đã xuất {len(data)} đối tượng sang JSON tại: {output_path}")
        
        # ----------
        # ----------
        # THÔNG BÁO - Start

        # Chuẩn bị nội dung thông báo
        msg = [
            f"Export Thành Công Dữ Liệu Vị Trí Của {len(selected_objects)} Object]",
        ]
        # Gọi hàm hiển thị Popup nổi bật
        utils.show_detailed_message(msg, title="Thành Công Không Có Gì Sai!", icon='CHECKMARK')

        # THÔNG BÁO _ Finish
        # ----------
        # ----------
        
        return True, len(data)
    except Exception as e:
        print(f"❌ Lỗi khi xuất file: {e}")
        return False, 0
    
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def rename_with_smart_suffix(context):
    active_obj = context.active_object
    selected_objs = context.selected_objects
    
    if not active_obj or not selected_objs:
        return False

    # 1. Làm sạch tên: Xóa đuôi .001 VÀ xóa toàn bộ khoảng trắng
    # Ví dụ: "Tall Table .001" -> "TallTable"
    raw_name = active_obj.name.rsplit('.', 1)[0]
    base_name = raw_name.replace(" ", "")
    
    alphabet = "abcdefghijklmnopqrstuvwxyz"

    # Sắp xếp để đảm bảo thứ tự đổi tên logic (ví dụ theo vị trí X)
    objs_to_rename = sorted(selected_objs, key=lambda o: o.location.x)

    # TRƯỜNG HỢP 2: Nếu tên gốc đã có "_" (Ví dụ: TallTable_01)
    if "_" in base_name:
        print(f"Case 2: Suffix a,b,c... for {base_name}")
        for i, obj in enumerate(objs_to_rename):
            if i < len(alphabet):
                char_suffix = alphabet[i]
                obj.name = f"{base_name}{char_suffix}"
            else:
                # Nếu vượt quá 26 chữ cái (a1, a2...)
                obj.name = f"{base_name}{alphabet[i % 26]}{i // 26}"

    # TRƯỜNG HỢP 1: Tên thuần Text (Ví dụ: TallTable)
    else:
        print(f"Case 1: Suffix _01, _02... for {base_name}")
        for i, obj in enumerate(objs_to_rename):
            obj.name = f"{base_name}_{i+1:02d}"

    # Đổi tên Mesh Data bên trong luôn cho sạch sẽ
    for obj in objs_to_rename:
        if obj.type == 'MESH':
            obj.data.name = f"Data_{obj.name}"

    print(f"✅ Rename hoàn tất (Không khoảng trắng): {base_name}")
    return True
    
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def export_all_object_to_fbx(context, export_folder="G:/Blender_Export_Data_Json/"):
    # Đảm bảo thư mục tồn tại
    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    # Lấy danh sách object đang chọn (để linh hoạt hơn là quét cả scene)
    selected_objs = context.selected_objects[:]
    
    if not selected_objs:
        print("Không có object nào được chọn để export.")

        # Lấy toàn bộ object thuộc về Scene mà bạn đang mở
        selected_objs = bpy.context.scene.objects
        print("Đã Chọn Toàn Bộ Object Trong Scene Để Export.")

        if len(selected_objs) == 0:
            # ----------
            # ----------
            # THÔNG BÁO - Start

            # Chuẩn bị nội dung thông báo
            msg = [
                f"Không Có Bất Kỳ Object Nào Trong Scene Để Export!",
            ]
            # Gọi hàm hiển thị Popup nổi bật
            utils.show_detailed_message(msg, title="Có Gì Đó Xảy Ra!", icon='ERROR')

            # THÔNG BÁO _ Finish
            # ----------
            # ---------- 
            return False

    # Lưu lại Cursor hoặc Mode nếu cần, nhưng ở đây ta xử lý trực tiếp
    for obj in selected_objs:
        if obj.type != 'MESH':
            continue

        # Active và Select duy nhất object này để ops hoạt động chuẩn
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj

        # 1. Apply transform (Nướng tọa độ vào mesh)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # 2. Tính toán offset để đưa Pivot về đáy (Bottom Center)
        mesh = obj.data
        verts = [v.co for v in mesh.vertices]

        min_z = min(v.z for v in verts)
        min_x = min(v.x for v in verts)
        max_x = max(v.x for v in verts)
        min_y = min(v.y for v in verts)
        max_y = max(v.y for v in verts)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        offset = Vector((center_x, center_y, min_z))

        # 3. Di chuyển các đỉnh của Mesh ngược lại offset (Edit mode ảo)
        for v in mesh.vertices:
            v.co -= offset
        
        mesh.update()

        # 4. Đưa Object về gốc tọa độ World (để file FBX sạch sẽ khi vào Unity)
        obj.location = (0, 0, 0)

        # 5. Thực hiện Export FBX
        # Sử dụng tên object làm tên file, rsplit để bỏ đuôi .001 nếu có
        clean_name = obj.name.rsplit('.', 1)[0]
        filepath = os.path.join(export_folder, f"{clean_name}.fbx")

        bpy.ops.export_scene.fbx(
            filepath=filepath,
            use_selection=True,
            axis_forward='-Z',
            axis_up='Y',
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=True # Tương đương "Apply Transform" trong UI
        )

    # ----------
    # ----------
    # THÔNG BÁO - Start

    # Chuẩn bị nội dung thông báo
    msg = [
        f"Export Thành Công {len(selected_objs)} File FBX]",
    ]
    # Gọi hàm hiển thị Popup nổi bật
    utils.show_detailed_message(msg, title="Thành Công Không Có Gì Sai!", icon='CHECKMARK')

    # THÔNG BÁO _ Finish
    # ----------
    # ----------    

    print(f"DONE EXPORT: {len(selected_objs)} files in {export_folder}")
    return True

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
