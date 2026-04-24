import bpy

KEY_BACK = 'BACK_SPACE'

# Quản lý các trạng thái Menu
STATE_MAIN = 'MAIN'
STATE_CREATE = 'CREATE'
STATE_TRANSFORM = 'TRANSFORM'
STATE_MESH = 'MESH'
STATE_OBJECT = 'OBJECT'

##### [STATE_OBJECT]
STATE_OBJECT_LIST = 'OBJECT_LIST' 

# --- NHÃN HIỂN THỊ TRONG OBJECT ---
LABEL_OBJECT_MAKE_ROOT_OBJECT = 'Make Root Object'
LABEL_OBJECT_MAKE_ROOT_OBJECT_FORCE = 'Make Root Object (Force From Shift_D)'
LABEL_OBJECT_MAKE_ROOT_OBJECT_FROM_REFERENCE = 'Make Root Object From Reference (Alt_D)'
LABEL_OBJECT_MAKE_REFERENCE_OBJECT = 'Make Reference Object'

LABEL_OBJECT_SYNC_ROOT_OBJECT = 'Sync Root Object'
LABEL_OBJECT_SYNC_REFERENCE_OBJECT = 'Sync Reference Object'
LABEL_OBJECT_SYNC_OBJECT_POSITION_DATA = 'Sync Object Position Data (Collection & Transform)'

##### [STATE_MESH]
STATE_INSET_LIST = 'INSET_LIST' 
STATE_PIVOT_LIST = 'PIVOT_LIST'
STATE_MERGE_LIST = 'MERGE_LIST'
STATE_SPIN_LIST = "SPIN_LIST"
STATE_CONNECT_LIST = "CONNECT_LIST"
STATE_NEW_MESH_LIST = 'NEW_MESH_LIST'
STATE_EXPORT_LIST = 'EXPORT_LIST'
STATE_REPLACE_LIST = 'REPLACE_LIST'

# Quản lý các phím bấm (Keymap Mapping)
KEY_OBJECT = 'O'
KEY_CREATE = 'C'
KEY_TRANSFORM = 'T'
KEY_MESH = 'M'
KEY_MENU_EXPORT = 'E'
KEY_MENU_REPLACE = 'R'

# --- PHÍM TRUY CẬP MENU CON ---
##### [STATE_MESH]
KEY_MENU_INSET = 'I' # Nhấn I trong menu [STATE_MESH] để vào [STATE_INSET_LIST]
KEY_MENU_PIVOT = 'P' # Nhấn P trong menu Mesh để vào danh sách Pivot
KEY_MENU_MERGE = 'M' # Phím truy cập menu con trong STATE_MESH
KEY_MENU_SPIN = 'S'

KEY_CONNECT = 'C' # Hoặc phím nào bạn muốn trong menu Mesh
KEY_MENU_NEW_MESH = 'N'

# --- Các mã phím (Dùng trong logic operators.py) ---
KEY_EXEC_0 = 'ZERO'
KEY_EXEC_1 = 'ONE'
KEY_EXEC_2 = 'TWO'
KEY_EXEC_3 = 'THREE'
KEY_EXEC_4 = 'FOUR'
KEY_EXEC_5 = 'FIVE'
KEY_EXEC_6 = 'SIX'
KEY_EXEC_7 = 'SEVEN'
KEY_EXEC_8 = 'EIGHT'
KEY_EXEC_9 = 'NINE'

# --- Các nhãn hiển thị (Dùng trong hud.py) ---
# Bạn có thể đổi "1", "Phím 1", "Key 1" tùy ý ở đây
LABEL_EXEC_0 = 'Phím 0'
LABEL_EXEC_1 = 'Phím 1'
LABEL_EXEC_2 = 'Phím 2'
LABEL_EXEC_3 = 'Phím 3'
LABEL_EXEC_4 = 'Phím 4'
LABEL_EXEC_5 = 'Phím 5'
LABEL_EXEC_6 = 'Phím 6'
LABEL_EXEC_7 = 'Phím 7'
LABEL_EXEC_8 = 'Phím 8'
LABEL_EXEC_9 = 'Phím 9'

# --- NHÃN HIỂN THỊ TRONG PIVOT MENU ---
LABEL_PIVOT_EDGE_CENTER = "Lấy trung điểm làm Pivot point (Cạnh)"
NAME_PIVOT_VERTS = "Lấy trung điểm làm Pivot point (2 Điểm)"

# --- NHÃN HIỂN THỊ TRONG MERGE MENU ---
LABEL_MERGE_AT_LAST = "Gộp về điểm sau cùng (Last)"

# Menu Names
NAME_SPIN_X = "Spin 90° quanh trục X (Cursor làm tâm)"
NAME_SPIN_Y = "Spin 90° quanh trục Y (Cursor làm tâm)"
NAME_SPIN_Z = "Spin 90° quanh trục Z (Cursor làm tâm)"
STATE_SPIN_AXIS = "SPIN_AXIS"  # Chọn trục X, Y, Z
STATE_SPIN_STEPS = "SPIN_STEPS" # Chọn số Steps

# Labels
NAME_CONNECT_FACE_CENTERS = "Connect Face Centers (2 Faces)"
# Dự phòng cho tương lai
NAME_CONNECT_EDGE_MIDPOINTS = "Connect Edge Midpoints (Coming Soon)"

# Thêm vào phần Labels
NAME_CREATE_PLANE_AT_VERT = "Tạo Plane 1cm tại Vertex (Tâm)"

NAME_EXPORT_POSITIONS_UNITY = "Export Object Positions (Unity JSON)"

NAME_REPLACE_NAME_OBJECT = "Đổi tên obj - tham chiếu obj sau cùng"
NAME_REPLACE_NAME_OBJECT_REMOVE_SPACE = "Đổi tên obj - xóa khoảng trắng"

# Tham số mặc định cho công cụ
INSET_THICKNESS_DEFAULT = 0.05
INSET_THICKNESS_001 = 0.01
INSET_THICKNESS_002 = 0.02
INSET_THICKNESS_003 = 0.03
INSET_THICKNESS_004 = 0.04
INSET_THICKNESS_005 = 0.05
INSET_THICKNESS_006 = 0.06
INSET_THICKNESS_007 = 0.07
INSET_THICKNESS_008 = 0.08
INSET_THICKNESS_009 = 0.09

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

class VT_UI_Settings(bpy.types.PropertyGroup):
    # Toggle cho các nhóm chính
    show_object_group : bpy.props.BoolProperty(name="Object Database", default=True) # type: ignore
    
    # Toggle cho các nhóm con bên trong (Sub-menus)
    show_identity_sub : bpy.props.BoolProperty(name="Identity Setup", default=True) # type: ignore
    show_sync_sub : bpy.props.BoolProperty(name="Sync & Clean", default=False) # type: ignore
    show_export_sub : bpy.props.BoolProperty(name="Xuất Dữ Liệu", default=False) # type: ignore

    # Thêm biến này để điều khiển dropdown thứ 2
    show_arrange_group : bpy.props.BoolProperty(default=False) # type: ignore
    # Đặt Obj vào ngăn xếp theo Hàng/Cột một cách tuần tự:
    show_into_current_stack_sub : bpy.props.BoolProperty(name="show_into_current_stack_sub", default=False) # type: ignore
        # Theo Hàng:
            # Hướng đi vào thứ nhất: X(++)
            # Hướng đi vào thứ hai: -Y(--)
        # Theo Cột:
            # Hướng đi vào thứ nhất: Z(++)
            # Hướng đi vào thứ hai: -Z(--)
    # Đặt Obj làm điểm neo mới (Nút đầu tiên của ngăn xếp mới) theo Hàng/Cột:
    show_into_new_stack_sub : bpy.props.BoolProperty(name="show_into_new_stack_sub", default=False) # type: ignore
        # Theo Hàng:
            # Hướng đi vào thứ nhất: X(++)
            # Hướng đi vào thứ hai: -Y(--)
        # Theo Cột:
            # Hướng đi vào thứ nhất: Z(++)
            # Hướng đi vào thứ hai: -Z(--)
    # Sắp xếp lại theo hình thức lưới Ngang/Dọc
    show_rearrange_into_grid_sub : bpy.props.BoolProperty(name="show_rearrange_into_grid_sub", default=False) # type: ignore



def register():
    bpy.utils.register_class(VT_UI_Settings)
    bpy.types.Scene.vt_ui = bpy.props.PointerProperty(type=VT_UI_Settings)

def unregister():
    bpy.utils.unregister_class(VT_UI_Settings)
    del bpy.types.Scene.vt_ui