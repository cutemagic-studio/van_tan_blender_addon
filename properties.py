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

    # --- PHẦN LOGIC LÁ

    # Mật độ lá cây trên tán cây
    mat_do_la_cay_tren_tan_cay: bpy.props.FloatProperty(
        name="Mật độ lá cây",
        description="Mật độ lá cây",
        default=1,
        min=0.1,
        unit='LENGTH'
    ) # type: ignore


    """Tạo dải cỏ rủ Stylized bao quanh khối đất"""
    # bl_idname = "mesh.generate_stylized_grass"
    # bl_label = "Generate Grass Overhang"
    # bl_options = {'REGISTER', 'UNDO'}

    # # 1. Tham số: Chiều dài dải cỏ rủ
    # grass_length: bpy.props.FloatProperty(
    #     name="Độ Dài Cỏ (Length)",
    #     description="Chiều dài cơ bản của dải cỏ rủ xuống",
    #     default=0.3,
    #     min=0.05,
    #     max=2.0,
    #     step=5 # Bước nhảy khi kéo chuột
    # )
    #
    # # 2. Tham số: Biên độ vấp nhô
    # wave_amplitude: bpy.props.FloatProperty(
    #     name="Biên Độ (Amplitude)",
    #     description="Độ nhấp nhô mạnh hay yếu của viền cỏ",
    #     default=0.15,
    #     min=0.0,
    #     max=1.0,
    #     step=2
    # )
    #
    # # 3. Tham số: Quãng sóng (Độ thoải/dốc)
    # wave_frequency: bpy.props.FloatProperty(
    #     name="Quãng Sóng (Frequency)",
    #     description="Tần số sóng. Số nhỏ = sóng thoải, rộng. Số lớn = sóng nhấp nhô liên tục",
    #     default=5.0, # Giảm mặc định xuống 5.0 để sóng trông thoải và mập mạp hơn
    #     min=0.5,
    #     max=30.0,
    #     step=10
    # )
    grass_min_length: bpy.props.FloatProperty(
        name="Độ Rủ Tối Thiểu (Min)", default=0.1, min=0.01, max=2.0
    )

    grass_max_length: bpy.props.FloatProperty(
        name="Độ Rủ Tối Đa (Max)", default=0.4, min=0.01, max=2.0
    )

    wave_frequency: bpy.props.FloatProperty(
        name="Nhịp Sóng (Thoải <-> Dốc)", default=3.0, min=0.5, max=15.0
    )

    # THÊM THAM SỐ ĐỘ DÀY VÀO GIAO DIỆN
    grass_thickness: bpy.props.FloatProperty(
        name="Độ Dày (Thickness)",
        description="Độ phồng/bề ngang của dải cỏ",
        default=0.08,
        min=0.01,
        max=0.5,
        step=1 # Tăng giảm từng 0.01m khi kéo
    )

    # THAM SỐ MỚI: MẬT ĐỘ LƯỚI
    segment_length: bpy.props.FloatProperty(
        name="Độ Giãn Lưới (Segment Length)",
        description="Khoảng cách giữa các điểm. Tăng lên để lưới thưa (low poly), giảm để lưới dày",
        default=0.1, # Đặt mặc định là 0.1 (10cm) để lưới thưa và sạch sẽ hơn
        min=0.02,
        max=1.0,
        step=2
    )

    # THAM SỐ MỚI: ĐỘ BO CẠNH
    bevel_width: bpy.props.FloatProperty(
        name="Độ Bo Cạnh (Bevel Amount)",
        description="Kiểm soát độ tròn của mép cỏ trên và mép dưới",
        default=0.02,
        min=0.0,
        max=0.5,
        step=1
    )

    random_seed: bpy.props.IntProperty(
        name="Thay Đổi Ngẫu Nhiên (Seed)", default=0, min=0, max=9999
    )
    """Tạo dải cỏ rủ Stylized bao quanh khối đất"""

    # --- PHẦN LOGIC TẠO SÂN ĐÁ STYLIZED (PAVEMENT) ---

    pavement_area_size: bpy.props.FloatProperty(
        name="Kích Thước Sân",
        description="Kích thước tổng thể của vùng sân đá",
        default=5.0,
        min=1.0,
        unit='LENGTH'
    ) # type: ignore

    pavement_random_seed: bpy.props.FloatProperty(
        name="Độ Ngẫu Nhiên",
        description="Thay đổi hình dáng sắp xếp ngẫu nhiên",
        default=0.04,
        min=0.0,
        max=0.5,
        step=1
    ) # type: ignore

    pavement_subdivisions: bpy.props.IntProperty(
        name="Mật Độ Đá",
        description="Số lượng phân chia lưới (chia càng nhiều, đá càng nhỏ và nhiều)",
        default=12,
        min=2,
        max=100
    ) # type: ignore

    pavement_gap_size: bpy.props.FloatProperty(
        name="Khe Hở (Gap)",
        description="Khoảng cách giữa các viên đá",
        default=0.04,
        min=0.0,
        max=0.5,
        step=1
    ) # type: ignore

    pavement_thickness: bpy.props.FloatProperty(
        name="Độ Dày Đá",
        description="Độ nổi/chiều cao của viên đá",
        default=0.15,
        min=0.01,
        max=1.0,
        step=1
    ) # type: ignore

    pavement_bevel_h: bpy.props.FloatProperty(
        name="Bo Cạnh Ngang",
        description="Độ bo tròn cho mặt trên và mặt đáy của viên đá",
        default=0.015,
        min=0.0,
        max=0.5,
        step=1
    ) # type: ignore

    pavement_bevel_v: bpy.props.FloatProperty(
        name="Bo Cạnh Dọc",
        description="Độ bo tròn cho các góc dựng đứng bao quanh viên đá",
        default=0.04,
        min=0.0,
        max=0.5,
        step=1
    ) # type: ignore

    # --- PHẦN LOGIC LƯỚI (GRID) ---
    
    # TRỤC NGANG
    spacing_xy_axis: bpy.props.FloatProperty(
        name="Khoảng Cách", 
        description="Khoảng cách giữa các bề mặt object",
        default=0.1, 
        min=0.0,
        unit='LENGTH'
    ) # type: ignore

    max_per_row_xy_axis: bpy.props.IntProperty(
        name="Max Hàng", 
        description="Số lượng object tối đa trên một hàng trước khi nhảy cột/tầng",
        default=5, 
        min=1
    ) # type: ignore
    
    max_per_col_xy_axis: bpy.props.IntProperty(
        name="Max Cột", 
        description="Số lượng hàng tối đa trước khi nhảy tầng (Z)",
        default=5, 
        min=1
    ) # type: ignore

    # TRỤC ĐỨNG
    spacing_z_axis: bpy.props.FloatProperty(
        name="Khoảng Cách", 
        description="Khoảng cách giữa các bề mặt object",
        default=0.1, 
        min=0.0,
        unit='LENGTH'
    ) # type: ignore

    max_per_row_z_axis: bpy.props.IntProperty(
        name="Max Hàng", 
        description="Số lượng object tối đa trên một hàng trước khi nhảy cột/tầng",
        default=5, 
        min=1
    ) # type: ignore
    
    max_per_col_z_axis: bpy.props.IntProperty(
        name="Max Cột", 
        description="Số lượng hàng tối đa trước khi nhảy tầng (Z)",
        default=5, 
        min=1
    ) # type: ignore

    # LƯỚI ĐỨNG - StandingGrid
    spacing_standing_grid: bpy.props.FloatProperty(
        name="Khoảng Cách", 
        description="Khoảng cách giữa các bề mặt object",
        default=0.1, 
        min=0.0,
        unit='LENGTH'
    ) # type: ignore

    max_per_row_standing_grid: bpy.props.IntProperty(
        name="Max Hàng", 
        description="Số lượng object tối đa trên một hàng trước khi nhảy cột/tầng",
        default=10, 
        min=1
    ) # type: ignore
    
    max_per_col_standing_grid: bpy.props.IntProperty(
        name="Max Cột", 
        description="Số lượng hàng tối đa trước khi nhảy tầng (Z)",
        default=10, 
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