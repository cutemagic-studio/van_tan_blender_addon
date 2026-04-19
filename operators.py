import bpy
from . import hud
from .functions import transform_tools
from .functions import mesh_tools

import bpy
from . import hud, constants  # Import constants
from .functions import transform_tools, mesh_tools

class OBJECT_OT_vt_ultimate_tool(bpy.types.Operator):
    bl_idname = "object.vt_ultimate_tool"
    bl_label = "VT System"
    bl_options = {'REGISTER', 'UNDO'}

    _handle = None
    state = constants.STATE_MAIN  # Sử dụng hằng số

    def modal(self, context, event):
        if context.area:
            context.area.tag_redraw()

        if event.value == 'PRESS':
            if event.type in {'ESC', 'RIGHTMOUSE'}:
                return self.finish(context, True)

            # ĐIỀU HƯỚNG
            if self.state == constants.STATE_MAIN:
                if event.type == constants.KEY_CREATE: 
                    self.state = constants.STATE_CREATE
                elif event.type == constants.KEY_TRANSFORM: 
                    self.state = constants.STATE_TRANSFORM
                elif event.type == constants.KEY_MESH: 
                    self.state = constants.STATE_MESH
            
            # THỰC THI (Ví dụ nhánh Mesh)
            ##### [STATE_MESH] 
            elif self.state == constants.STATE_MESH:
                # Nếu nhấn I, chuyển sang trạng thái hiện danh sách Inset
                if event.type == constants.KEY_MENU_INSET:
                    self.state = constants.STATE_INSET_LIST
                    return {'RUNNING_MODAL'}
                # Nhấn P để vào Menu Pivot
                if event.type == constants.KEY_MENU_PIVOT:
                    self.state = constants.STATE_PIVOT_LIST
                    return {'RUNNING_MODAL'}
                # Nhấn M để vào Menu Merge
                if event.type == constants.KEY_MENU_MERGE:
                    self.state = constants.STATE_MERGE_LIST
                    return {'RUNNING_MODAL'}
                # Nhấn S để vào menu Spin
                if event.type == constants.KEY_MENU_SPIN:
                    # self.state = constants.STATE_SPIN_LIST
                    self.state = constants.STATE_SPIN_AXIS
                    return {'RUNNING_MODAL'}
                # Nhấn 'C' để vào menu Connect
                if event.type == 'C':
                    self.state = constants.STATE_CONNECT_LIST
                    return {'RUNNING_MODAL'}
                # Nhấn 'N' để vào menu New Mesh
                if event.type == constants.KEY_MENU_NEW_MESH:
                    self.state = constants.STATE_NEW_MESH_LIST
                    return {'RUNNING_MODAL'}
                
                # Nhấn 'E' để vào menu Export
                if event.type == constants.KEY_MENU_EXPORT:
                    self.state = constants.STATE_EXPORT_LIST
                    return {'RUNNING_MODAL'}
                
                # Bạn có thể thêm các lệnh mesh khác ở đây (ví dụ: Mirror)
                if event.type == constants.KEY_EXEC_1:
                    bpy.ops.object.modifier_add(type='MIRROR')
                    return self.finish(context)

            ##### [STATE_MESH] => [STATE_INSET_LIST]
            elif self.state == constants.STATE_INSET_LIST:
                # Mapping phím bấm với giá trị độ dày tương ứng
                inset_map = {
                    constants.KEY_EXEC_0: constants.INSET_THICKNESS_DEFAULT,
                    constants.KEY_EXEC_1: constants.INSET_THICKNESS_001,
                    constants.KEY_EXEC_2: constants.INSET_THICKNESS_002,
                    constants.KEY_EXEC_3: constants.INSET_THICKNESS_003,
                    constants.KEY_EXEC_4: constants.INSET_THICKNESS_004,
                    constants.KEY_EXEC_5: constants.INSET_THICKNESS_005,
                    constants.KEY_EXEC_6: constants.INSET_THICKNESS_006,
                    constants.KEY_EXEC_7: constants.INSET_THICKNESS_007,
                    constants.KEY_EXEC_8: constants.INSET_THICKNESS_008,
                    constants.KEY_EXEC_9: constants.INSET_THICKNESS_009,
                }
                
                if event.type in inset_map:
                    success = mesh_tools.smart_inset(context, thickness=inset_map[event.type])
                    if success:
                        self.report({'INFO'}, "Inset applied!")
                    else:
                        self.report({'WARNING'}, "Please select faces first!")
                    
                    # Cập nhật lại giao diện trước khi thoát
                    context.area.tag_redraw()    

                    return self.finish(context)
                
            ##### [STATE_MESH] => [STATE_PIVOT_LIST]    
            elif self.state == constants.STATE_PIVOT_LIST:
                # Thực thi chức năng trong menu Pivot
                # Phím 1: Trung điểm cạnh
                if event.type == constants.KEY_EXEC_1:
                    success = mesh_tools.pivot_to_edge_center(context, set_pivot=True)
                    if success:
                        self.report({'INFO'}, "Pivot set to Edge Center")
                    else:
                        self.report({'WARNING'}, "Please select at least 1 edge")
                    
                    # Cập nhật lại giao diện trước khi thoát
                    context.area.tag_redraw()

                    return self.finish(context)
                # Phím 2: Trung điểm 2 đỉnh
                elif event.type == constants.KEY_EXEC_2:
                    success = mesh_tools.pivot_to_vert_midpoint(context, set_pivot=True)

                    if success:
                        # Thông báo khi thành công
                        self.report({'INFO'}, "Cursor set to Centroid & Pivot mode: CURSOR")
                    else:
                        # Thông báo khi người dùng chưa chọn điểm nào
                        self.report({'WARNING'}, "Please select at least 1 vertex")

                    # Cập nhật lại giao diện trước khi thoát
                    context.area.tag_redraw()

                    return self.finish(context)
                
            ##### [STATE_MESH] => [STATE_MERGE_LIST]
            elif self.state == constants.STATE_MERGE_LIST:
                if event.type == constants.KEY_EXEC_1:
                    
                    success = mesh_tools.merge_points_at_last(context)
                    if success:
                        self.report({'INFO'}, "Merged successfully!")
                    else:
                        self.report({'WARNING'}, "Please select at least 2 vertices")

                    # Cập nhật lại giao diện trước khi thoát
                    context.area.tag_redraw()

                    return self.finish(context)
                    

            elif self.state == constants.STATE_SPIN_LIST:
                # Nhấn phím 1: Spin X
                if event.type == constants.KEY_EXEC_1:
                    self.selected_axis = 'X'
                    self.state = constants.STATE_SPIN_STEPS

                # Nhấn phím 2: Spin Y
                elif event.type == constants.KEY_EXEC_2:
                    self.selected_axis = 'Y'
                    self.state = constants.STATE_SPIN_STEPS

                # Nhấn phím 3: Spin Z
                elif event.type == constants.KEY_EXEC_3:
                    self.selected_axis = 'Z'
                    self.state = constants.STATE_SPIN_STEPS

                # Cập nhật lại giao diện
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            
            # BƯỚC 1: CHỌN TRỤC VÀ HƯỚNG
            elif self.state == constants.STATE_SPIN_AXIS:
                # Mapping phím bấm với hướng
                axis_key_map = {
                    constants.KEY_EXEC_1: 'X',  constants.KEY_EXEC_2: '-X',
                    constants.KEY_EXEC_3: 'Y',  constants.KEY_EXEC_4: '-Y',
                    constants.KEY_EXEC_5: 'Z',  constants.KEY_EXEC_6: '-Z'
                } 
                
                if event.type in axis_key_map:
                    self.selected_axis = axis_key_map[event.type] # Lưu hướng (vd: '-X')
                    self.state = constants.STATE_SPIN_STEPS
                    context.area.tag_redraw()
                    return {'RUNNING_MODAL'}
                    
                elif event.type == constants.KEY_BACK:
                    self.state = constants.STATE_MESH # Quay lại menu Mesh
                    context.area.tag_redraw()
                    return {'RUNNING_MODAL'}

            elif self.state == constants.STATE_SPIN_STEPS:
                # Danh sách các phím hợp lệ lấy từ constants
                
                # Tạo bảng tra cứu giá trị steps
                steps_map = {
                    constants.KEY_EXEC_2: 2, 'NUMPAD_2': 2,
                    constants.KEY_EXEC_3: 3, 'NUMPAD_3': 3,
                    constants.KEY_EXEC_4: 4, 'NUMPAD_4': 4,
                    constants.KEY_EXEC_5: 5, 'NUMPAD_5': 5,
                    constants.KEY_EXEC_6: 6, 'NUMPAD_6': 6,
                }
                
                # Kiểm tra xem phím bấm có nằm trong khoảng từ 2 đến 6 không
                if event.type in steps_map:
                    steps_val = steps_map[event.type]
                    
                    # Gọi hàm xử lý từ mesh_tools
                    success = mesh_tools.spin_mesh(context, axis_name=self.selected_axis, steps=steps_val)
                    
                    if success:
                        self.report({'INFO'}, f"Spin {self.selected_axis} | Steps: {steps_val}")
                    else:
                        self.report({'WARNING'}, "Spin failed. Check selection/cursor!")
                        
                    return self.finish(context)

                elif event.type == constants.KEY_BACK:
                    self.state = constants.STATE_SPIN_LIST # Quay lại bước chọn trục
                
                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            elif self.state == constants.STATE_CONNECT_LIST:
                # Nhấn '1' để nối trọng tâm mặt
                if event.type == constants.KEY_EXEC_1:
                    success = mesh_tools.connect_face_centers(context)
                    if success:
                        self.report({'INFO'}, "Faces Connected at Centers")
                    return self.finish(context)

                # Nút quay lại
                elif event.type == constants.KEY_BACK:
                    self.state = constants.STATE_MESH

                context.area.tag_redraw()
                return {'RUNNING_MODAL'}

            ##### [STATE_MESH] => [STATE_NEW_MESH_LIST] 
            elif self.state == constants.STATE_NEW_MESH_LIST:
                # Nhấn '1' để tạo Plane 1cm tại Vertex
                if event.type == constants.KEY_EXEC_1:
                    success = mesh_tools.create_plane_at_vertex(context, size=0.05)
                    if success:
                        self.report({'INFO'}, "Plane 1cm created!")
                    return self.finish(context)

                # Nút quay lại
                elif event.type == constants.KEY_BACK:
                    self.state = constants.STATE_MESH

                context.area.tag_redraw()
                return {'RUNNING_MODAL'}
            
            ##### Trong STATE_EXPORT_LIST
            elif self.state == constants.STATE_EXPORT_LIST:
                if event.type == constants.KEY_EXEC_1:
                    from .functions import export_tools
                    success, count = export_tools.export_positions_to_json(context)
                    if success:
                        self.report({'INFO'}, f"Exported {count} objects to Unity JSON")
                    else:
                        self.report({'WARNING'}, "Export failed! Check console or selection.")
                    return self.finish(context)

                elif event.type == constants.KEY_BACK:
                    self.state = constants.STATE_MESH

            # Tương tự cho TRANSFORM...
            elif self.state == constants.STATE_TRANSFORM:
                if event.type == constants.KEY_EXEC_1:
                    success = transform_tools.export_each_object_to_fbx(context)
                    if success:
                        self.report({'INFO'}, "Exported FBX files successfully!")

                    return self.finish(context)

                # if event.type == constants.KEY_EXEC_1:
                #     transform_tools.origin_to_bottom_selected()
                #     return self.finish(context)
                # elif event.type == constants.KEY_EXEC_2:
                #     transform_tools.drop_to_floor_selected()
                #     return self.finish(context)

        return {'RUNNING_MODAL'}
    
    # ... các hàm invoke/finish giữ nguyên

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            self._handle = bpy.types.SpaceView3D.draw_handler_add(
                hud.draw_hud, (self, context), 'WINDOW', 'POST_PIXEL'
            )
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        return {'CANCELLED'}

    def finish(self, context, cancelled=False):
        if self._handle:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        return {'CANCELLED'} if cancelled else {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_vt_ultimate_tool)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_vt_ultimate_tool)