import blf
import bpy
from . import constants

def draw_hud(op, context):
    font_id = 0
    x, y = 90, 350  # Đẩy Y lên cao một chút (350) để có chỗ cho danh sách dài
    line_height = 25 # Khoảng cách giữa các dòng

    # 1. Định nghĩa bảng màu theo State 
    colors = {
        constants.STATE_MAIN: (0.2, 0.8, 1.0, 1.0),
        constants.STATE_TRANSFORM: (1.0, 0.8, 0.0, 1.0),
        constants.STATE_CREATE: (0.1, 1.0, 0.5, 1.0),
        constants.STATE_MESH: (1.0, 0.4, 0.7, 1.0),
        constants.STATE_SPIN_LIST: (0.7, 0.5, 1.0, 1.0),
        constants.STATE_SPIN_STEPS: (0.7, 0.5, 1.0, 1.0)
    }
    
    # 2. Vẽ Tiêu đề
    blf.size(font_id, 22)
    current_color = colors.get(op.state, (1, 1, 1, 1))
    blf.color(font_id, *current_color)
    blf.position(font_id, x, y, 0)
    blf.draw(font_id, f"--- VT SYSTEM: {op.state} ---")

    # 3. Vẽ Nội dung (Màu trắng)
    blf.color(font_id, 1, 1, 1, 1)
    
    if op.state == constants.STATE_MAIN:
        blf.position(font_id, x, y - 35, 0)
        blf.draw(font_id, f"{constants.KEY_OBJECT}: Object | {constants.KEY_TRANSFORM}: Transform | {constants.KEY_MESH}: Mesh")
        footer_y = y - 75 # Vị trí dòng Cancel cho menu ngắn

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    elif op.state == constants.STATE_OBJECT:
        blf.position(font_id, x, y - 35, 0)
        # blf.draw(font_id, 
        #          f"{constants.LABEL_EXEC_1}: {constants.LABEL_OBJECT_MAKE_ROOT_OBJECT} | "
        #          f"{constants.LABEL_EXEC_2}: {constants.LABEL_OBJECT_MAKE_REFERENCE_OBJECT} | "
        #          f"{constants.LABEL_EXEC_3}: {constants.LABEL_OBJECT_SYNC_REFERENCE_OBJECT} | "
        #          )
        # footer_y = y - 75

        object_commands = [
            (constants.LABEL_EXEC_1, constants.LABEL_OBJECT_MAKE_ROOT_OBJECT),
            (constants.LABEL_EXEC_2, constants.LABEL_OBJECT_MAKE_ROOT_OBJECT_FORCE),
            (constants.LABEL_EXEC_3, constants.LABEL_OBJECT_MAKE_ROOT_OBJECT_FROM_REFERENCE),
            (constants.LABEL_EXEC_4, constants.LABEL_OBJECT_MAKE_REFERENCE_OBJECT),
            (constants.LABEL_EXEC_5, constants.LABEL_OBJECT_SYNC_ROOT_OBJECT),
            (constants.LABEL_EXEC_6, constants.LABEL_OBJECT_SYNC_REFERENCE_OBJECT),
            (constants.LABEL_EXEC_7, constants.LABEL_OBJECT_SYNC_OBJECT_POSITION_DATA),
        ]

        for i, (label, name) in enumerate(object_commands):
            row_y = (y - 45) - (i * line_height)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1) # Màu vàng cho phím
            blf.draw(font_id, f"[{label}]")
            
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 45) - (len(object_commands) * line_height) - 25

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    elif op.state == constants.STATE_TRANSFORM:
        blf.position(font_id, x, y - 35, 0)
        # blf.draw(font_id, f"{constants.LABEL_EXEC_1}: Origin to Bottom | {constants.KEY_EXEC_2}: Drop to Floor")
        blf.draw(font_id, 
                 f"{constants.LABEL_EXEC_1}: Xuất tất cả Fbx"
                 f"{constants.LABEL_EXEC_2}: Di chuyển Obj xuống mặt đất"
                 )
        footer_y = y - 75

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    elif op.state == constants.STATE_CREATE:
        blf.position(font_id, x, y - 35, 0)
        blf.draw(font_id, f"{constants.KEY_EXEC_1}: Cylinder")
        footer_y = y - 75

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    ##### [STATE_MESH]
    elif op.state == constants.STATE_MESH:
        blf.position(font_id, x, y - 35, 0)
        blf.draw(font_id, 
                f"{constants.KEY_MENU_INSET}: Inset Menu | "
                f"{constants.KEY_MENU_PIVOT}: Pivot Menu | "
                f"{constants.KEY_MENU_MERGE}: Merge Menu | "
                f"{constants.KEY_MENU_SPIN}: Spin Menu | "
                f"{constants.KEY_CONNECT}: Connect Menu | "
                f"{constants.KEY_MENU_NEW_MESH}: New Mesh Menu |"
                f"{constants.KEY_MENU_EXPORT}: Export Menu |"
                f"{constants.KEY_MENU_REPLACE}: Replace Menu |"
                 )
        footer_y = y - 75

    ##### [STATE_MESH] => [STATE_INSET_LIST]
    elif op.state == constants.STATE_INSET_LIST:
        inset_list = [
            (constants.LABEL_EXEC_0, constants.INSET_THICKNESS_DEFAULT),
            (constants.LABEL_EXEC_1, constants.INSET_THICKNESS_001),
            (constants.LABEL_EXEC_2, constants.INSET_THICKNESS_002),
            (constants.LABEL_EXEC_3, constants.INSET_THICKNESS_003),
            (constants.LABEL_EXEC_4, constants.INSET_THICKNESS_004),
            (constants.LABEL_EXEC_5, constants.INSET_THICKNESS_005),
            (constants.LABEL_EXEC_6, constants.INSET_THICKNESS_006),
            (constants.LABEL_EXEC_7, constants.INSET_THICKNESS_007),
            (constants.LABEL_EXEC_8, constants.INSET_THICKNESS_008),
            (constants.LABEL_EXEC_9, constants.INSET_THICKNESS_009),
        ]

        # Vẽ danh sách Inset
        for i, (label, thickness) in enumerate(inset_list):
            row_y = (y - 45) - (i * line_height) # Tăng khoảng cách dòng đầu thành 45
            
            # 1. Vẽ Nhãn Phím (Màu vàng)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{label}]")
            
            # 2. Vẽ Giá trị (Màu trắng) - Nới rộng X ra 100 đơn vị
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0) # Tăng từ 35 -> 100 để không bị đè
            blf.draw(font_id, f": Inset {thickness}m")
        
        # Đẩy dòng Cancel xuống thấp hơn một chút
        footer_y = (y - 45) - (len(inset_list) * line_height) - 25

    ##### [STATE_MESH] => [STATE_PIVOT_LIST]
    elif op.state == constants.STATE_PIVOT_LIST:
        # Danh sách các lệnh Pivot
        pivot_commands = [
            (constants.LABEL_EXEC_1, constants.LABEL_PIVOT_EDGE_CENTER),
            (constants.LABEL_EXEC_2, constants.NAME_PIVOT_VERTS),
        ]

        for i, (label, name) in enumerate(pivot_commands):
            row_y = (y - 45) - (i * line_height)
            
            # Vẽ Nhãn [1], [2]
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{label}]")
            
            # Vẽ Tên chức năng bằng hằng số
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 45) - (len(pivot_commands) * line_height) - 25

    ##### [STATE_MESH] => [STATE_MERGE_LIST]
    elif op.state == constants.STATE_MERGE_LIST:
        merge_commands = [
            (constants.LABEL_EXEC_1, constants.LABEL_MERGE_AT_LAST)
        ]

        for i, (label, name) in enumerate(merge_commands):
            row_y = (y - 45) - (i * line_height)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1) # Màu vàng cho phím
            blf.draw(font_id, f"[{label}]")
            
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 45) - (len(merge_commands) * line_height) - 25

    ##### [STATE_SPIN_LIST] - Chọn Trục
    elif op.state == constants.STATE_SPIN_LIST:
        spin_axes = [
            ("1", "Trục X"),
            ("2", "Trục Y"),
            ("3", "Trục Z"),
        ]
        
        for i, (label, name) in enumerate(spin_axes):
            row_y = (y - 45) - (i * line_height)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{label}]")
            
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": Spin 90° quanh {name}")
            
        footer_y = (y - 45) - (len(spin_axes) * line_height) - 25

    ##### [STATE_SPIN_AXIS]
    elif op.state == constants.STATE_SPIN_AXIS:
        axis_display = [
            ("1", "X (+)"), ("2", "X (-)"),
            ("3", "Y (+)"), ("4", "Y (-)"),
            ("5", "Z (+)"), ("6", "Z (-)")
        ]
        
        blf.size(font_id, 20)
        blf.draw(font_id, "--- CHỌN HƯỚNG SPIN ---")
        
        for i, (key, label) in enumerate(axis_display):
            row_y = (y - 45) - (i * line_height)
            blf.color(font_id, 1, 0.8, 0.2, 1) # Màu vàng cho phím
            blf.position(font_id, x, row_y, 0)
            blf.draw(font_id, f"[{key}]")
            
            blf.color(font_id, 1, 1, 1, 1) # Màu trắng cho tên
            blf.position(font_id, x + 60, row_y, 0)
            blf.draw(font_id, f": {label}")
            
        footer_y = (y - 45) - (len(axis_display) * line_height) - 25

    ##### [STATE_SPIN_STEPS] - Chọn độ mượt
    elif op.state == constants.STATE_SPIN_STEPS:
        # Tiêu đề phụ hiển thị trục đang chọn
        blf.size(font_id, 18)
        blf.color(font_id, 0.7, 0.5, 1.0, 1)
        blf.position(font_id, x, y - 45, 0)
        blf.draw(font_id, f"Axis: {op.selected_axis} | Chọn số phân đoạn (Steps):")
        
        # Sử dụng hằng số KEY_EXEC để hiển thị nhãn phím bấm
        steps_commands = [
            (constants.KEY_EXEC_2, "2 Steps"),
            (constants.KEY_EXEC_3, "3 Steps"),
            (constants.KEY_EXEC_4, "4 Steps"),
            (constants.KEY_EXEC_5, "5 Steps"),
            (constants.KEY_EXEC_6, "6 Steps"),
        ]
        
        for i, (key_label, name) in enumerate(steps_commands):
            row_y = (y - 80) - (i * line_height)
            
            # Vẽ Nhãn Phím [2], [3]... lấy từ constants
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{key_label}]")
            
            # Vẽ Tên chức năng
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 80) - (len(steps_commands) * line_height) - 25

    ##### [STATE_CONNECT_LIST] - Menu Connect mới
    elif op.state == constants.STATE_CONNECT_LIST:
        # Tiêu đề chính
        blf.size(font_id, 20)
        blf.color(font_id, 0.2, 1.0, 0.8, 1.0) 
        blf.position(font_id, x, y - 45, 0)
        blf.draw(font_id, "--- CONNECT TOOLS ---")

        connect_commands = [
            (constants.LABEL_EXEC_1, constants.NAME_CONNECT_FACE_CENTERS),
        ]

        # Bắt đầu vẽ danh sách từ y - 45 (vì menu này không có tiêu đề phụ như Spin)
        for i, (label, name) in enumerate(connect_commands):
            row_y = (y - 80) - (i * line_height)
            
            # Phím bấm (Vàng)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{label}]")
            
            # Tên chức năng (Trắng)
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 80) - (len(connect_commands) * line_height) - 25

    ##### [STATE_MESH] => [STATE_NEW_MESH_LIST]
    elif op.state == constants.STATE_NEW_MESH_LIST:
        blf.size(font_id, 20)
        blf.color(font_id, 0.1, 1.0, 0.5, 1.0) # Màu xanh lá giống STATE_CREATE
        blf.position(font_id, x, y - 45, 0)
        blf.draw(font_id, "--- NEW MESH TOOLS ---")

        new_mesh_commands = [
            (constants.LABEL_EXEC_1, constants.NAME_CREATE_PLANE_AT_VERT),
        ]

        for i, (label, name) in enumerate(new_mesh_commands):
            row_y = (y - 80) - (i * line_height)
            blf.position(font_id, x, row_y, 0)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.draw(font_id, f"[{label}]")
            
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 80) - (len(new_mesh_commands) * line_height) - 25

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    ##### [STATE_EXPORT_LIST]
    elif op.state == constants.STATE_EXPORT_LIST:
        blf.size(font_id, 20)
        blf.color(font_id, 0.4, 0.7, 1.0, 1.0) # Màu xanh dương cho Export
        blf.position(font_id, x, y - 45, 0)
        blf.draw(font_id, "--- EXPORT TOOLS ---")

        export_commands = [
            (constants.LABEL_EXEC_1, constants.NAME_EXPORT_POSITIONS_UNITY),
        ]

        for i, (label, name) in enumerate(export_commands):
            row_y = (y - 80) - (i * line_height)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.position(font_id, x, row_y, 0)
            blf.draw(font_id, f"[{label}]")
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 80) - (len(export_commands) * line_height) - 25

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    ##### [STATE_REPLACE_LIST]
    elif op.state == constants.STATE_REPLACE_LIST:
        blf.size(font_id, 20)
        blf.color(font_id, 0.4, 0.7, 1.0, 1.0) # Màu xanh dương cho Export
        blf.position(font_id, x, y - 45, 0)
        blf.draw(font_id, "--- REPLACE TOOLS ---")

        export_commands = [
            (constants.LABEL_EXEC_1, constants.NAME_REPLACE_NAME_OBJECT),
            (constants.LABEL_EXEC_2, constants.NAME_REPLACE_NAME_OBJECT_REMOVE_SPACE),
        ]

        for i, (label, name) in enumerate(export_commands):
            row_y = (y - 80) - (i * line_height)
            blf.color(font_id, 1, 0.8, 0.2, 1)
            blf.position(font_id, x, row_y, 0)
            blf.draw(font_id, f"[{label}]")
            blf.color(font_id, 1, 1, 1, 1)
            blf.position(font_id, x + 100, row_y, 0)
            blf.draw(font_id, f": {name}")
            
        footer_y = (y - 80) - (len(export_commands) * line_height) - 25

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

    # 4. Vẽ Hướng dẫn thoát (Dòng chữ đỏ)
    blf.size(font_id, 15)
    blf.color(font_id, 1, 0.3, 0.3, 0.8)
    blf.position(font_id, x, footer_y, 0)
    blf.draw(font_id, "[ESC / RMB] to Cancel")

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ 
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

class VIEW3D_PT_VT_ObjectTools(bpy.types.Panel):
    bl_label = "Công Cụ Tối Thượng"
    bl_idname = "Cute_Magic_Ultimate"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'CuteMagic'

    def draw(self, context):
        layout = self.layout
        ui = context.scene.vt_ui
        
        # LEVEL 1:
        # =========================================================================
        # NHÓM 1: OBJECT
        # =========================================================================
        main_box = layout.box()
        row = main_box.row(align=True)
        
        # Nút Dropdown chính
        prop_icon = 'TRIA_DOWN' if ui.show_object_group else 'TRIA_RIGHT'
        row.prop(ui, "show_object_group", text="ĐỐI TƯỢNG SIÊU CẤP", icon='NODE_COMPOSITING', emboss=False)
        row.label(text="", icon=prop_icon)

        if ui.show_object_group:
            # --- LEVEL 2: NHÓM CON 1 (Identity) ---
            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_identity_sub else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_identity_sub", text="Bản Gốc - Bản Tham Chiếu", icon='LINKED', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_identity_sub:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01 = col.operator("vt.object_action", text="Tạo Bản Gốc (Thuần Mới Tạo)", icon='ADD')
                thaoTacQuanTrong02 = col.operator("vt.object_action", text="Tạo Bản Gốc (Shift + D)", icon='DUPLICATE')
                thaoTacQuanTrong03 = col.operator("vt.object_action", text="Tạo Bản Gốc (Alt + D)", icon='LINKED')

                thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.MAKE_ROOT' 
                col.scale_y = 1.5

                thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.MAKE_ROOT_OBJECT_FORCE'
                col.scale_y = 1.5

                thaoTacQuanTrong03.action = 'FUNCTION.OBJECT.MAKE_ROOT_OBJECT_FROM_REFERENCE'
                col.scale_y = 1.5

            if ui.show_identity_sub:
                col = sub_box.column(align=True)
                # col.separator()
                col.operator("vt.object_action", text="Tạo Bản Tham Chiếu", icon='RESTRICT_SELECT_OFF').action = 'FUNCTION.OBJECT.MAKE_REFERENCE_OBJECT'
                col.scale_y = 1.2

            # 
            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_clear_data_group else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_clear_data_group", text="Xóa Dữ Liệu", icon='TRASH', emboss=False)
            sub_row.label(text="", icon=sub_icon)

            if ui.show_clear_data_group:
                col = sub_box.column(align=True)
                # col.separator()
                col.operator("vt.object_action", text="Xóa Dữ Liệu Object", icon='TRASH').action = 'FUNCTION.OBJECT.CLEAR_OBJECT_DATA'
                col.scale_y = 0.8

            if ui.show_clear_data_group:
                col = sub_box.column(align=True)
                # col.separator()
                col.operator("vt.object_action", text="Xóa Dữ Liệu Object (Danh Sách Chọn)", icon='TRASH').action = 'FUNCTION.OBJECT.CLEAR_OBJECT_DATA_FOR_LIST'
                col.scale_y = 0.8

            # --- LEVEL 2: NHÓM CON 2 (Sync & Clean) --- 
            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_sync_sub else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_sync_sub", text="Đồng Bộ Hóa", icon='FILE_REFRESH', emboss=False)
            sub_row.label(text="", icon=sub_icon)
             
            if ui.show_sync_sub:
                col = sub_box.column(align=True)

                # thaoTacQuanTrong01 = col.operator("vt.object_action", text="Bản Gốc (List Tự Động)", icon='FILE_REFRESH')
                # thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.SYNC_ROOT_OBJECT'
                # col.scale_y = 1.5

                # col.separator()

                # thaoTacQuanTrong02 = col.operator("vt.object_action", text="Bản Tham Chiếu (List Chọn)", icon='FILE_REFRESH')
                # thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.SYNC_REFERENCE_OBJECT'
                # col.scale_y = 1.5

                # col.separator()

                # thaoTacQuanTrong03 = col.operator("vt.object_action", text="Vị Trí (Collection & Transform)", icon='ORIENTATION_GIMBAL')
                # thaoTacQuanTrong03.action = 'FUNCTION.OBJECT.SYNC_OBJECT_POSITION_DATA'
                # col.scale_y = 1.5

                thaoTacQuanTrong01 = col.operator("vt.object_action", text="Gán Vị Trí Sắp Xếp Mới", icon='ORIENTATION_GIMBAL')
                thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.ASSIGN_NEW_ARRANG_POSITION'
                col.scale_y = 1.5

                col.separator()

                thaoTacQuanTrong02 = col.operator("vt.object_action", text="Hủy Gán Vị Trí Sắp Xếp Mới", icon='ORIENTATION_GIMBAL')
                thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.CANCEL_ASSIGN_NEW_ARRANG_POSITION'
                col.scale_y = 1.5

                col.separator()

                thaoTacQuanTrong03 = col.operator("vt.object_action", text="Đưa Pivot Point Xuống Bottom", icon='DOWNARROW_HLT')
                thaoTacQuanTrong03.action = 'FUNCTION.OBJECT.MOVE_PIVOT_POINT_TO_BOTTOM'
                col.scale_y = 1.5

                col.separator()

                thaoTacQuanTrong04 = col.operator("vt.object_action", text="Đồng Bộ Tên", icon='ALIGN_BOTTOM')
                thaoTacQuanTrong04.action = 'FUNCTION.OBJECT.SYNC_OBJECT_NAME'
                col.scale_y = 1.5

                col.separator()

                thaoTacQuanTrong05 = col.operator("vt.object_action", text="Đồng Bộ Tất Cả", icon='FILE_REFRESH')
                thaoTacQuanTrong05.action = 'FUNCTION.OBJECT.SYNC_ALL_DATA'
                col.scale_y = 1.5

            # --- LEVEL 2: NHÓM CON 2 (Sync & Clean) ---
            # sub_box = main_box.box()
            # sub_row = sub_box.row(align=True)
            
            # sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_export_sub else 'DISCLOSURE_TRI_RIGHT'
            # sub_row.prop(ui, "show_export_sub", text="Xuất Dữ Liệu", icon='EXPORT', emboss=False)
            # sub_row.label(text="", icon=sub_icon)
             
            # if ui.show_export_sub:
            #     col = sub_box.column(align=True)

            #     thaoTacQuanTrong01 = col.operator("vt.object_action", text="Vị Trí Trong Scene", icon='OUTLINER_COLLECTION')
            #     thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.EXPORT_POSITION_DATA_TO_JSON'
            #     col.scale_y = 1.5

            #     col.separator()

        # LEVEL 1:
        # =========================================================================
        # NHÓM 2: SẮP XẾP
        # =========================================================================
        layout.separator() # Khoảng cách nhỏ giữa 2 nhóm chính
        
        main_box = layout.box()
        row = main_box.row(align=True)
        
        #
        util_icon = 'TRIA_DOWN' if ui.show_arrange_group else 'TRIA_RIGHT'
        row.prop(ui, "show_arrange_group", text="SẮP XẾP VÀ EXPORT", icon='COLLAPSEMENU', emboss=False)
        row.label(text="", icon=util_icon)
        
        if ui.show_arrange_group:

            # --- CHÈN CONFIG VÀO ĐÂY ---
            cfg = context.scene.cmc_sorting_config

            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_can_chinh_theo_truc_xyz else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_can_chinh_theo_truc_xyz", text="Căn chỉnh theo trục XYZ", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)

            if ui.show_can_chinh_theo_truc_z:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01d = col.operator("vt.object_action", text="Fit Uniform (XYZ)", icon='BACK')
                thaoTacQuanTrong02d = col.operator("vt.object_action", text="Smart Diagonal Step (XYZ)", icon='BACK')
                thaoTacQuanTrong03d = col.operator("vt.object_action", text="Interpolated Stair Distribution (XYZ)", icon='BACK')
                thaoTacQuanTrong04d = col.operator("vt.object_action", text="Fill Wall Box with Bricks (XYZ)", icon='BACK')
                thaoTacQuanTrong04d1 = col.operator("vt.object_action", text="Fill L-Wall Box with Bricks A (XYZ)", icon='BACK')
                thaoTacQuanTrong04d2 = col.operator("vt.object_action", text="Fill L-Wall Box with Bricks B (XYZ)", icon='BACK')
                thaoTacQuanTrong04d3 = col.operator("vt.object_action", text="fill_stone_wall_advanced (XYZ)", icon='BACK')
                thaoTacQuanTrong05d = col.operator("vt.object_action", text="Fill Circle Bounds with Bricks (XYZ)", icon='BACK')
                thaoTacQuanTrong05d1 = col.operator("vt.object_action", text="FILL_PAVEMENT_STYLIZED (XYZ)", icon='BACK')
                thaoTacQuanTrong06d = col.operator("vt.object_action", text="Yin-Yang Roof Tiles (XYZ)", icon='BACK')
                thaoTacQuanTrong07d = col.operator("vt.object_action", text="ARRANGE_ON_CURVE (XYZ)", icon='BACK')
                thaoTacQuanTrong08d = col.operator("vt.object_action", text="FILL_CANOPY (XYZ)", icon='BACK')
                thaoTacQuanTrong09d = col.operator("vt.object_action", text="FILL_CIRCULAR_PAVEMENT (XYZ)", icon='BACK')
                thaoTacQuanTrong09d1 = col.operator("vt.object_action", text="FILL_ROUNDED_SQUARE_PAVEMENT (XYZ)", icon='BACK')
                thaoTacQuanTrong10d = col.operator("vt.object_action", text="FILL_STONE_HOUSE (XYZ)", icon='BACK')
                thaoTacQuanTrong10d1 = col.operator("vt.object_action", text="FILL_CORNER_PILLARS (XYZ)", icon='BACK')
                thaoTacQuanTrong10d2 = col.operator("vt.object_action", text="FILL_WALL_ACCENTS (XYZ)", icon='BACK')

                thaoTacQuanTrong11d = col.operator("vt.object_action", text="FILL_STONE_HOUSE_V2 (XYZ)", icon='BACK')
                thaoTacQuanTrong11d1 = col.operator("vt.object_action", text="FILL_CORNER_PILLARS_V2 (XYZ)", icon='BACK')
                thaoTacQuanTrong11d2 = col.operator("vt.object_action", text="FILL_WALL_ACCENTS_V2 (XYZ)", icon='BACK')

                thaoTacQuanTrong12d = col.operator("vt.object_action", text="FILL_STYLIZED_ROOF (XYZ)", icon='BACK')
                thaoTacQuanTrong13d = col.operator("vt.object_action", text="FILL_WOODEN_WALLS (XYZ)", icon='BACK')
                thaoTacQuanTrong13d1 = col.operator("vt.object_action", text="FILL_WOODEN_WALLS_VERTICAL (XYZ)", icon='BACK')
                thaoTacQuanTrong14d = col.operator("vt.object_action", text="SNAP_PLANKS_TO_SEGMENTS (XYZ)", icon='BACK')

                thaoTacQuanTrong15d = col.operator("vt.object_action", text="FILL_SHINGLED_CANOPY (XYZ)", icon='BACK')
                thaoTacQuanTrong16d = col.operator("vt.object_action", text="CUT_BY_VOLUME (XYZ)", icon='BACK')
                thaoTacQuanTrong17d = col.operator("vt.object_action", text="GENERATE_SMART_BRIDGE (XYZ)", icon='BACK')

                thaoTacQuanTrong18d = col.operator("vt.object_action", text="GENERATE_STYLIZED_STREAM (XYZ)", icon='BACK')
                thaoTacQuanTrong19d = col.operator("vt.object_action", text="DEFORM_CANOPY (XYZ)", icon='BACK')
                thaoTacQuanTrong20d = col.operator("vt.object_action", text="ATTACH_LEAVES_TO_CANOPY (XYZ)", icon='BACK')

                thaoTacQuanTrong99 = col.operator("vt.object_action", text="Chức Năng Test", icon='BACK')

                thaoTacQuanTrong01d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FIT_UNIFORM.Z'
                thaoTacQuanTrong02d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SMART_STEP_DISTRIBUTE.Z'
                thaoTacQuanTrong03d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SMART_STEP_DISTRIBUTE_2.Z'
                thaoTacQuanTrong04d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WALL_BOX.Z'
                thaoTacQuanTrong04d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WALL_BOX_LEAVE_TEETH.Z'
                thaoTacQuanTrong04d2.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WALL_BOX_FILL_TEETH.Z'
                thaoTacQuanTrong04d3.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_STONE_WALL_STYLIZED.Z'
                thaoTacQuanTrong05d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_CIRCLE_BOUNDS.Z'
                thaoTacQuanTrong05d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_PAVEMENT_STYLIZED.Z'
                thaoTacQuanTrong06d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_ROOF_YIN_YANG.Z'
                thaoTacQuanTrong07d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ARRANGE_ON_CURVE.Z'
                thaoTacQuanTrong08d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_CANOPY.Z'
                thaoTacQuanTrong09d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_CIRCULAR_PAVEMENT.Z'
                thaoTacQuanTrong09d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_ROUNDED_SQUARE_PAVEMENT.Z'

                thaoTacQuanTrong10d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_STONE_HOUSE.Z'
                thaoTacQuanTrong10d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_CORNER_PILLARS.Z'
                thaoTacQuanTrong10d2.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WALL_ACCENTS.Z'

                thaoTacQuanTrong11d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_STONE_HOUSE_V2.Z'
                thaoTacQuanTrong11d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_CORNER_PILLARS_V2.Z'
                thaoTacQuanTrong11d2.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WALL_ACCENTS_V2.Z'

                thaoTacQuanTrong12d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_STYLIZED_ROOF.Z'
                thaoTacQuanTrong13d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WOODEN_WALLS.Z'
                thaoTacQuanTrong13d1.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_WOODEN_WALLS_VERTICAL.Z'
                thaoTacQuanTrong14d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SNAP_PLANKS_TO_SEGMENTS.Z'

                thaoTacQuanTrong15d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.FILL_SHINGLED_CANOPY.Z'
                thaoTacQuanTrong16d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.CUT_BY_VOLUME.Z'
                thaoTacQuanTrong17d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.GENERATE_SMART_BRIDGE.Z'

                thaoTacQuanTrong18d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.GENERATE_STYLIZED_STREAM.Z'
                thaoTacQuanTrong19d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.DEFORM_CANOPY.Z'
                thaoTacQuanTrong20d.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ATTACH_LEAVES.Z'

                thaoTacQuanTrong99.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.CREATE_STYLIZED_TREE.Z'


                col.scale_y = 1.5
            #

            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_can_chinh_theo_truc_z else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_can_chinh_theo_truc_z", text="Căn chỉnh theo trục Z", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_can_chinh_theo_truc_z:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01a = col.operator("vt.object_action", text="Center Between (Z)", icon='BACK')
                thaoTacQuanTrong02a = col.operator("vt.object_action", text="Array By Distance (Z)", icon='BACK')
                thaoTacQuanTrong03a = col.operator("vt.object_action", text="Align XY (Keep Z)", icon='BACK')
                thaoTacQuanTrong04a = col.operator("vt.object_action", text="Match Transform (Z)", icon='BACK')
                thaoTacQuanTrong05a = col.operator("vt.object_action", text="Right Isosceles Triangle (Z)", icon='BACK')
                thaoTacQuanTrong06a = col.operator("vt.object_action", text="Opposite Flatten (Z)", icon='BACK')
                thaoTacQuanTrong07a = col.operator("vt.object_action", text="Opposite Not Flatten (Z)", icon='BACK')
                thaoTacQuanTrong08a = col.operator("vt.object_action", text="Reset To Zero Base Active (Z)", icon='BACK')
                thaoTacQuanTrong09a = col.operator("vt.object_action", text="Reset To Zero (Z)", icon='BACK')
                thaoTacQuanTrong10a = col.operator("vt.object_action", text="Snapping (Z)", icon='BACK')
                thaoTacQuanTrong11a = col.operator("vt.object_action", text="Align To Face Center (Z)", icon='BACK')
                thaoTacQuanTrong12a = col.operator("vt.object_action", text="Measure Distance (Z)", icon='BACK')
                thaoTacQuanTrong13a = col.operator("vt.object_action", text="Stretch to Fit Gap (Z)", icon='BACK')


                thaoTacQuanTrong01a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.CENTER_BETWEEN.Z'
                thaoTacQuanTrong02a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ARRAY_BY_DISTANCE.Z'
                thaoTacQuanTrong03a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_KEEP.Z'
                thaoTacQuanTrong04a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MATCH_TRANSFORM.Z'
                thaoTacQuanTrong05a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RIGHT_ISOSCELES_TRIANGLE.Z'
                thaoTacQuanTrong06a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE.Z'
                thaoTacQuanTrong07a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE_NOT_FLATTEN.Z'
                thaoTacQuanTrong08a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RESET_TO_ZERO_BASE_ACTIVE.Z'
                thaoTacQuanTrong09a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RESET_TO_ZERO.Z'
                thaoTacQuanTrong10a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SNAP_TO_BOUNDS.Z'
                thaoTacQuanTrong11a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_TO_SURFACE.Z'
                thaoTacQuanTrong12a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MEASURE_DISTANCE.Z'
                thaoTacQuanTrong13a.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.STRETCH_TO_FIT_GAP.Z'

                col.scale_y = 1.5
            #

            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_can_chinh_theo_truc_x else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_can_chinh_theo_truc_x", text="Căn chỉnh theo trục X", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_can_chinh_theo_truc_x:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01b = col.operator("vt.object_action", text="Center Between (X)", icon='BACK')
                thaoTacQuanTrong02b = col.operator("vt.object_action", text="Array By Distance (X)", icon='BACK')
                thaoTacQuanTrong03b = col.operator("vt.object_action", text="Align YZ (Keep X)", icon='BACK')
                thaoTacQuanTrong04b = col.operator("vt.object_action", text="Match Transform (X)", icon='BACK')
                thaoTacQuanTrong05b = col.operator("vt.object_action", text="Right Isosceles Triangle (X)", icon='BACK')
                thaoTacQuanTrong06b = col.operator("vt.object_action", text="Opposite Flatten (X)", icon='BACK')
                thaoTacQuanTrong07b = col.operator("vt.object_action", text="Opposite Not Flatten (X)", icon='BACK')
                thaoTacQuanTrong08b = col.operator("vt.object_action", text="Reset To Zero Base Active (X)", icon='BACK')
                thaoTacQuanTrong09b = col.operator("vt.object_action", text="Reset To Zero (X)", icon='BACK')
                thaoTacQuanTrong10b = col.operator("vt.object_action", text="Snapping (X)", icon='BACK')
                thaoTacQuanTrong11b = col.operator("vt.object_action", text="Align To Face Center (X)", icon='BACK')
                thaoTacQuanTrong12b = col.operator("vt.object_action", text="Measure Distance (X)", icon='BACK')
                thaoTacQuanTrong13b = col.operator("vt.object_action", text="Stretch to Fit Gap (X)", icon='BACK')

                thaoTacQuanTrong01b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.CENTER_BETWEEN.X'
                thaoTacQuanTrong02b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ARRAY_BY_DISTANCE.X'
                thaoTacQuanTrong03b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_KEEP.X'
                thaoTacQuanTrong04b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MATCH_TRANSFORM.X'
                thaoTacQuanTrong05b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RIGHT_ISOSCELES_TRIANGLE.X'
                thaoTacQuanTrong06b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE.X'
                thaoTacQuanTrong07b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE_NOT_FLATTEN.X'
                thaoTacQuanTrong08b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RESET_TO_ZERO_BASE_ACTIVE.X'
                thaoTacQuanTrong09b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RESET_TO_ZERO.X'
                thaoTacQuanTrong10b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SNAP_TO_BOUNDS.X'
                thaoTacQuanTrong11b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_TO_SURFACE.X'
                thaoTacQuanTrong12b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MEASURE_DISTANCE.X'
                thaoTacQuanTrong13b.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.STRETCH_TO_FIT_GAP.X'

                col.scale_y = 1.5
            #

            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_can_chinh_theo_truc_y else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_can_chinh_theo_truc_y", text="Căn chỉnh theo trục Y", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_can_chinh_theo_truc_y:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01c = col.operator("vt.object_action", text="Center Between (Y)", icon='BACK')
                thaoTacQuanTrong02c = col.operator("vt.object_action", text="Array By Distance (Y)", icon='BACK')
                thaoTacQuanTrong03c = col.operator("vt.object_action", text="Align XZ (Keep Y)", icon='BACK')
                thaoTacQuanTrong04c = col.operator("vt.object_action", text="Match Transform (Y)", icon='BACK')
                thaoTacQuanTrong05c = col.operator("vt.object_action", text="Right Isosceles Triangle (Y)", icon='BACK')
                thaoTacQuanTrong06c = col.operator("vt.object_action", text="Opposite Flatten (Y)", icon='BACK')
                thaoTacQuanTrong07c = col.operator("vt.object_action", text="Opposite Not Flatten (Y)", icon='BACK')
                thaoTacQuanTrong09c = col.operator("vt.object_action", text="Reset To Zero (Y)", icon='BACK')
                thaoTacQuanTrong10c = col.operator("vt.object_action", text="Snapping (Y)", icon='BACK')
                thaoTacQuanTrong11c = col.operator("vt.object_action", text="Align To Face Center (Y)", icon='BACK')
                thaoTacQuanTrong12c = col.operator("vt.object_action", text="Measure Distance (Y)", icon='BACK')
                thaoTacQuanTrong13c = col.operator("vt.object_action", text="Stretch to Fit Gap (Y)", icon='BACK')

                thaoTacQuanTrong01c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.CENTER_BETWEEN.Y'
                thaoTacQuanTrong02c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ARRAY_BY_DISTANCE.Y'
                thaoTacQuanTrong03c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_KEEP.Y'
                thaoTacQuanTrong04c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MATCH_TRANSFORM.Y'
                thaoTacQuanTrong05c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RIGHT_ISOSCELES_TRIANGLE.Y'
                thaoTacQuanTrong06c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE.Y'
                thaoTacQuanTrong07c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.OPPOSITE_NOT_FLATTEN.Y'
                thaoTacQuanTrong09c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.RESET_TO_ZERO.Y'
                thaoTacQuanTrong10c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.SNAP_TO_BOUNDS.Y'
                thaoTacQuanTrong11c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.ALIGN_TO_SURFACE.Y'
                thaoTacQuanTrong12c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.MEASURE_DISTANCE.Y'
                thaoTacQuanTrong13c.action = 'FUNCTION.OBJECT.ARRANGE_ONLY.STRETCH_TO_FIT_GAP.Y'

                col.scale_y = 1.5
            #
            
            settings_box = main_box.box()
            settings_box.label(text="Config Sắp Xếp Trục Ngang (XY):", icon='LINENUMBERS_ON')
            
            row_settings = settings_box.row(align=True)
            row_settings.prop(cfg, "spacing_xy_axis", text="Cách")
            row_settings.prop(cfg, "max_per_row_xy_axis", text="Hàng")
            row_settings.prop(cfg, "max_per_col_xy_axis", text="Cột")
            
            #####

            settings_box2 = main_box.box()
            settings_box2.label(text="Config Sắp Xếp Trục Dọc (Z):", icon='LINENUMBERS_ON')
            
            row_settings2 = settings_box2.row(align=True)
            row_settings2.prop(cfg, "spacing_z_axis", text="Cách")
            row_settings2.prop(cfg, "max_per_row_z_axis", text="Hàng")
            row_settings2.prop(cfg, "max_per_col_z_axis", text="Cột")

            #####

            settings_box3 = main_box.box()
            settings_box3.label(text="Config Sắp Xếp Lưới Đứng:", icon='LINENUMBERS_ON')
            
            row_settings3 = settings_box3.row(align=True)
            row_settings3.prop(cfg, "spacing_standing_grid", text="Cách")
            row_settings3.prop(cfg, "max_per_row_standing_grid", text="Hàng")
            row_settings3.prop(cfg, "max_per_col_standing_grid", text="Cột")

            # settings_box.prop(cfg, "align_to_bottom") # Option căn lề đáy
            # ---------------------------

            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_into_current_stack_sub else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_into_current_stack_sub", text="Đẩy Vào Ngăn Xếp Tuần Tự", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_into_current_stack_sub:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01 = col.operator("vt.object_action", text="(Hàng) Hướng đi vào +X++", icon='BACK')
                thaoTacQuanTrong02 = col.operator("vt.object_action", text="(Hàng) Hướng đi vào -Y--", icon='BACK')
                thaoTacQuanTrong03 = col.operator("vt.object_action", text="(Cột)  Hướng đi vào +Z++", icon='BACK')
                thaoTacQuanTrong04 = col.operator("vt.object_action", text="(Cột)  Hướng đi vào -Z--", icon='BACK')

                thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.ARRANGE.INTO_CURRENT_STACK.+X++' 
                

                thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.ARRANGE.INTO_CURRENT_STACK.-Y--'
                

                thaoTacQuanTrong03.action = 'FUNCTION.OBJECT.ARRANGE.INTO_CURRENT_STACK.+Z++'
                

                thaoTacQuanTrong04.action = 'FUNCTION.OBJECT.ARRANGE.INTO_CURRENT_STACK.-Z--'
                
                col.scale_y = 1.5

            #####
            

            thisValue = False

            if thisValue:
                sub_box = main_box.box()
                sub_row = sub_box.row(align=True)
                
                sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_into_new_stack_sub else 'DISCLOSURE_TRI_RIGHT'
                sub_row.prop(ui, "show_into_new_stack_sub", text="Đẩy Vào Ngăn Xếp Mới", icon='LINENUMBERS_ON', emboss=False)
                sub_row.label(text="", icon=sub_icon)
                
                if ui.show_into_new_stack_sub:
                    col = sub_box.column(align=True)
                    thaoTacQuanTrong01 = col.operator("vt.object_action", text="(Hàng) Hướng đi vào +X++", icon='BACK')
                    thaoTacQuanTrong02 = col.operator("vt.object_action", text="(Hàng) Hướng đi vào -Y--", icon='BACK')
                    thaoTacQuanTrong03 = col.operator("vt.object_action", text="(Cột)  Hướng đi vào +Z++", icon='BACK')
                    thaoTacQuanTrong04 = col.operator("vt.object_action", text="(Cột)  Hướng đi vào -Z--", icon='BACK')

                    thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.ARRANGE.INTO_NEW_STACK.+X++' 
                    

                    thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.ARRANGE.INTO_NEW_STACK.-Y--'
                    

                    thaoTacQuanTrong03.action = 'FUNCTION.OBJECT.ARRANGE.INTO_NEW_STACK.+Z++'
                    

                    thaoTacQuanTrong04.action = 'FUNCTION.OBJECT.ARRANGE.INTO_NEW_STACK.-Z--'
                    
                    col.scale_y = 1.5

            #####
            
            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_rearrange_into_grid_sub else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_rearrange_into_grid_sub", text="Sắp Xếp Lưới", icon='LINENUMBERS_ON', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_rearrange_into_grid_sub:
                col = sub_box.column(align=True)
                thaoTacQuanTrong01 = col.operator("vt.object_action", text="Xếp Thành Lưới Đứng", icon='BACK')

                thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.ARRANGE.REARRANGE_INTO_GRID' 
                
                col.scale_y = 1.5

            #####
            
            sub_box = main_box.box()
            sub_row = sub_box.row(align=True)
            
            sub_icon = 'DISCLOSURE_TRI_DOWN' if ui.show_export_all_object_to_fbx else 'DISCLOSURE_TRI_RIGHT'
            sub_row.prop(ui, "show_export_all_object_to_fbx", text="Export", icon='EXPORT', emboss=False)
            sub_row.label(text="", icon=sub_icon)
            
            if ui.show_export_all_object_to_fbx:

                col = sub_box.column(align=True)
                thaoTacQuanTrong01 = col.operator("vt.object_action", text="Export Dữ Liệu Vị Trí Trong Scene", icon='EXPORT')
                thaoTacQuanTrong01.action = 'FUNCTION.OBJECT.EXPORT_POSITION_DATA_TO_JSON'
                col.scale_y = 1.5

                col.separator()

                col = sub_box.column(align=True)
                thaoTacQuanTrong02 = col.operator("vt.object_action", text="Export Tất Cả Object Sang Fbx", icon='EXPORT')
                thaoTacQuanTrong02.action = 'FUNCTION.OBJECT.EXPORT_ALL_OBJECT_TO_FBX' 
                col.scale_y = 1.5


#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ 
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____


#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ 1. Persistent Header Info (Ghi vào thanh trạng thái)
# Loại này sẽ luôn hiển thị ở dưới đáy màn hình Blender, rất nhẹ nhàng và không làm phiền người dùng.#
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
def draw_cmc_status(self, context):
    layout = self.layout
    # Chỉ hiển thị khi có object được chọn
    if context.active_object:
        row = layout.row(align=True)
        row.separator(factor=2.0)
        row.label(text="CMC:", icon='NODE_COMPOSITING')
        row.label(text=f"Target: {context.active_object.name}", icon='OBJECT_DATA')

# Thêm vào cuối hàm register() trong __init__.py:
# bpy.types.STATUSBAR_HT_header.append(draw_cmc_status)

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ 4. Custom Floating Dialog (Hộp thoại tùy biến)
# Dùng để hiển thị các bảng thông tin chi tiết mà không có nút OK/Cancel mặc định.
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
class VT_OT_CustomDialog(bpy.types.Operator):
    bl_idname = "vt.custom_dialog"
    bl_label = "Thông Báo Tối Thượng"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="System Log", icon='INFO')
        col = box.column(align=True)
        col.label(text="- Sync: Success", icon='CHECKMARK')
        col.label(text="- Memory: Stable", icon='DRIVER_DISTANCE')
        
    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=250)
    
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____  
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def draw_cmc_status(self, context):
    layout = self.layout
    # Chỉ hiển thị khi có đối tượng đang được chọn
    obj = context.active_object
    if obj:
        row = layout.row(align=True)
        row.separator(factor=2.0) # Tạo khoảng cách với các thông tin mặc định của Blender
        
        # Hiển thị icon và tên đối tượng đang xử lý
        row.label(text="CMC System:", icon='NODE_COMPOSITING')
        row.label(text=f"Target: {obj.name}", icon='OBJECT_DATA')
        
        # Nếu muốn hiển thị trạng thái Sync (ví dụ từ biến global hoặc scene property)
        if hasattr(context.scene, "vt_ui"):
            status_text = "Ready" if not context.scene.vt_ui.show_sync_sub else "Syncing..."
            row.label(text=status_text)

    
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____ 
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
