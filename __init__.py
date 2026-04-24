# bl_info = {
#     "name": "[VT] Ultimate Workflow System",
#     "author": "VT & Gemini",
#     "version": (2, 2, 0),
#     "blender": (3, 0, 0),
#     "location": "View3D > Ctrl+Shift+0",
#     "category": "Object",
# }
bl_info = {
    "name": "Van Tan Ultimate Tools",
    "author": "Van Tan",
    "version": (1, 0),
    "blender": (4, 0, 0), 
    "location": "View3D > Sidebar > VT_Addon",
    "description": "Hệ thống quản lý Object và Mesh tối ưu cho Unity",
    "category": "Object",
}

import bpy
from . import constants, utils, operators, keymaps, hud
from . import properties

# Cơ chế Reload để phát triển (Giữ nguyên - rất tốt cho Dev)
if "bpy" in locals():
    import importlib
    importlib.reload(constants)
    importlib.reload(operators)
    importlib.reload(keymaps)
    importlib.reload(utils)
    importlib.reload(hud)

# Danh sách các class theo đúng thứ tự ưu tiên
classes = [
    constants.VT_UI_Settings,      # Đăng ký Group dữ liệu đầu tiên
    operators.CMC_GiaoDienThucThiChucNang,  # Các lệnh thực thi
    utils.VT_OT_ShowMessage,       # Các tiện ích thông báo
    hud.VT_OT_CustomDialog,        # Hộp thoại Dashboard
    hud.VIEW3D_PT_VT_ObjectTools,  # Panel giao diện cuối cùng

    properties.CMC_SortingConfig
]

def register():
    # 1. Đăng ký các class
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 2. Khởi tạo dữ liệu vào Scene
    bpy.types.Scene.vt_ui = bpy.props.PointerProperty(type=constants.VT_UI_Settings)
    
    # 3. Đăng ký Keymaps
    keymaps.register()
    
    # 4. Đăng ký các thành phần giao diện đặc biệt
    bpy.types.STATUSBAR_HT_header.append(hud.draw_cmc_status)
    
    # 5. Kích hoạt HUD (Vẽ GPU)
    utils.toggle_hud(True)

    # Tạo một "con trỏ" (Pointer) trong Scene để chứa dữ liệu của bạn
    # Đây chính là lúc cái tên "cmc_sorting_config" được tạo ra
    bpy.types.Scene.cmc_sorting_config = bpy.props.PointerProperty(type=properties.CMC_SortingConfig)

    print("✅ Van Tan Tools đã được đăng ký!")

def unregister():
    # 1. Gỡ HUD và Status Bar trước (Tránh lỗi vẽ khi class đã mất)
    utils.toggle_hud(False)
    if hasattr(bpy.types.STATUSBAR_HT_header, "remove"):
        # Dùng try-except để tránh lỗi nếu người dùng nhấn F3 Reload nhiều lần
        try:
            bpy.types.STATUSBAR_HT_header.remove(hud.draw_cmc_status)
        except:
            pass

    # 2. Gỡ Keymaps
    keymaps.unregister()

    # 3. Xóa dữ liệu Scene
    if hasattr(bpy.types.Scene, "vt_ui"):
        del bpy.types.Scene.vt_ui
    
    # Xóa con trỏ khi tắt Add-on
    del bpy.types.Scene.cmc_sorting_config

    # 4. Gỡ đăng ký các class
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("❌ Van Tan Tools đã gỡ đăng ký!")

if __name__ == "__main__":
    register()