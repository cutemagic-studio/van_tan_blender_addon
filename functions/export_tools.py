import bpy
import json
import os

def export_positions_to_json(context):
    # Đường dẫn xuất file (Bạn có thể tùy biến hoặc dùng biến môi trường sau này)
    # output_path = "E:/Unity_Projects/My_First_Game/Assets/TestImportAssetFromBlender/Scripts/JSON_Data/positions.json"
    
    output_path = "X:/UNITY_STORE/ALL_PACK/PACK_03_room/blender/FILE_blender_xuat_FBX/position_data/positions.json"
    
    # Đảm bảo thư mục tồn tại
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    selected_objects = context.selected_objects
    if not selected_objects: 
        return False, 0

    data = []
    for obj in selected_objects:
        # Lấy vị trí World Space
        pos = obj.matrix_world.translation

        data.append({
            # Lấy tên gốc (loại bỏ .001, .002...)
            "name": obj.name.rsplit('.', 1)[0],
            # Chuyển đổi hệ trục: Blender (Z-up) -> Unity (Y-up)
            "pos": {
                "x": pos.x,
                "y": pos.z,  # Z lên trên
                "z": pos.y   # Y thành chiều sâu
            }

            # "pos": {
            #     "x": pos.x,
            #     "y": pos.y,
            #     "z": pos.z
            # }
        })

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        return True, len(data)
    except Exception as e:
        print(f"Export Error: {e}")
        return False, 0