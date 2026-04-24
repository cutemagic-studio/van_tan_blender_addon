import bpy

class CMC_SortingConfig(bpy.types.PropertyGroup):
    # --- PHẦN KHOẢNG CÁCH ---
    spacing: bpy.props.FloatProperty(
        name="Khoảng Cách", 
        description="Khoảng cách giữa các bề mặt object",
        default=0.1, 
        min=0.0,
        unit='LENGTH'
    ) # type: ignore

    # --- PHẦN LOGIC LƯỚI (GRID) ---
    max_per_row: bpy.props.IntProperty(
        name="Max Hàng", 
        description="Số lượng object tối đa trên một hàng trước khi nhảy cột/tầng",
        default=5, 
        min=1
    ) # type: ignore
    
    max_per_col: bpy.props.IntProperty(
        name="Max Cột", 
        description="Số lượng hàng tối đa trước khi nhảy tầng (Z)",
        default=5, 
        min=1
    ) # type: ignore

    # --- PHẦN KIỂM SOÁT TÂM (ORIGIN) ---
    # Rất quan trọng để tránh việc object bị lún hoặc bay lơ lửng khi kích thước khác nhau
    align_to_bottom: bpy.props.BoolProperty(
        name="Căn lề đáy",
        description="Luôn giữ các object bằng mặt sàn (Z=0 tương đối)",
        default=True
    ) # type: ignore

    # --- PHẦN GIỚI HẠN KHÔNG GIAN ---
    use_limit_boundary: bpy.props.BoolProperty(
        name="Giới Hạn Vùng", 
        default=False
    ) # type: ignore
    
    boundary_size: bpy.props.FloatVectorProperty(
        name="Vùng Chứa", 
        subtype='XYZ', 
        default=(10.0, 10.0, 10.0)
    ) # type: ignore