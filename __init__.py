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
    "blender": (4, 0, 0), # Hoặc (5, 0, 0) tùy phiên bản bạn dùng
    "location": "View3D > Sidebar > VT_Addon",
    "description": "Hệ thống quản lý Object và Mesh tối ưu cho Unity",
    "category": "Object",
}

import bpy
from . import constants, utils
from . import operators, keymaps, hud

# Cơ chế Reload để phát triển
if "bpy" in locals():
    import importlib
    importlib.reload(constants) # Thêm dòng này
    importlib.reload(operators)
    importlib.reload(keymaps)
    importlib.reload(utils)
    importlib.reload(hud)

def register(): 
    operators.register()
    keymaps.register()
    hud.register()

def unregister():
    hud.unregister()
    keymaps.unregister()
    operators.unregister()

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

# Danh sách các class theo đúng thứ tự ưu tiên
classes = [
    constants.VT_UI_Settings,         # 1. Đăng ký Group lưu trữ dữ liệu trước
    operators.VT_OT_ObjectAction,    # 2. Đăng ký lệnh thực thi
    hud.VIEW3D_PT_VT_ObjectTools,    # 3. Đăng ký giao diện hiển thị
]

def register():
    # Bước A: Đăng ký các class vào hệ thống Blender
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Bước B: Khởi tạo PointerProperty vào Scene
    # Điều này cho phép context.scene.vt_ui tồn tại để HUD có thể vẽ được
    bpy.types.Scene.vt_ui = bpy.props.PointerProperty(type=constants.VT_UI_Settings)
    
    print("✅ Van Tan Tools đã được đăng ký!")

def unregister():
    # Bước A: Xóa PointerProperty trước để tránh lỗi dữ liệu mồ côi
    del bpy.types.Scene.vt_ui
    
    # Bước B: Gỡ đăng ký các class theo thứ tự ngược lại (An toàn hơn)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("❌ Van Tan Tools đã gỡ đăng ký!")

# Cho phép chạy script trực tiếp từ Text Editor của Blender để test nhanh
if __name__ == "__main__":
    register()