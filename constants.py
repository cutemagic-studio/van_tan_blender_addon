KEY_BACK = 'BACK_SPACE'


# Quản lý các trạng thái Menu
STATE_MAIN = 'MAIN'
STATE_CREATE = 'CREATE'
STATE_TRANSFORM = 'TRANSFORM'
STATE_MESH = 'MESH'
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