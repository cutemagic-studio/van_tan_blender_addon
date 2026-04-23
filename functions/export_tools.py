import bpy
import json
import os

#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____
#|||||_____|||||_____
#|||||_____||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||_____

def export_positions_to_json(context):

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
