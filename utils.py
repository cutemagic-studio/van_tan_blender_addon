import bpy

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

import bpy

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
