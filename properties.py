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

    bulge_amount: bpy.props.FloatProperty(
        name="Độ Phồng Bụng (Bulge Amount)",
        description="Đẩy phần giữa của dải cỏ phồng ra ngoài tạo cảm giác múp míp (Cozy/Stylized)",
        default=0.15,  # Mặc định là 0.15 (15cm) để cỏ phồng rõ rệt hơn
        min=0.0,
        max=1.0,
        step=1         # Tăng giảm từng 0.01m khi kéo chuột
    )

    random_seed: bpy.props.IntProperty(
        name="Thay Đổi Ngẫu Nhiên (Seed)", default=0, min=0, max=9999
    )
    """Tạo dải cỏ rủ Stylized bao quanh khối đất"""

    # --- PHẦN LOGIC TẠO SÂN ĐÁ STYLIZED (PAVEMENT) ---
    # --- PHẦN LOGIC TẠO SÂN ĐÁ STYLIZED (PAVEMENT) ---
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

    # --- PHẦN TƯỜNG ĐÁ ---
    # --- PHẦN TƯỜNG ĐÁ ---
    # --- PHẦN TƯỜNG ĐÁ ---
    stone_wall_num_layers: bpy.props.IntProperty(
        name="Số Lớp Đá",
        description="Số lớp đá xếp chồng theo chiều ngang",
        default=3,
        min=1,
        max=20
    ) # type: ignore

    stone_wall_wall_alignment: bpy.props.EnumProperty(
        name="Căn Lề Curve",
        description="Vị trí của bức tường so với đường dẫn Curve",
        items=[
            ('CENTER', "Ở Giữa", "Đường Curve chạy xuyên qua chính giữa tường"),
            ('LEFT', "Bên Trái", "Tường nằm hoàn toàn về bên trái của Curve"),
            ('RIGHT', "Bên Phải", "Tường nằm hoàn toàn về bên phải của Curve")
        ],
        default='CENTER'
    ) # type: ignore

    stone_wall_layer_height: bpy.props.FloatProperty(
        name="Chiều Cao Lớp",
        description="Chiều cao của mỗi lớp đá",
        default=0.4,
        min=0.05,
        max=5.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_wall_wall_thickness: bpy.props.FloatProperty(
        name="Bề Dày Tường",
        description="Độ dày của bức tường đá",
        default=0.3,
        min=0.05,
        max=5.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_wall_min_width: bpy.props.FloatProperty(
        name="Chiều Dài Min",
        description="Chiều dài ngắn nhất của một viên đá",
        default=0.4,
        min=0.05,
        max=5.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_wall_max_width: bpy.props.FloatProperty(
        name="Chiều Dài Max",
        description="Chiều dài dài nhất của một viên đá",
        default=1.0,
        min=0.1,
        max=10.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_wall_gap_size: bpy.props.FloatProperty(
        name="Khe Hở (Vữa)",
        description="Khoảng cách khe hở giữa các viên đá",
        default=0.03,
        min=0.0,
        max=0.2,
        precision=3,
        unit='LENGTH'
    ) # type: ignore

    # LÀM GỒ GHỀ MẶT PHẲNG
    # LÀM GỒ GHỀ MẶT PHẲNG
    # LÀM GỒ GHỀ MẶT PHẲNG

    stone_surface_damage_inset_thickness: bpy.props.FloatProperty(
        name="Độ Dày Viền (Inset)",
        description="Độ rộng của vành đai an toàn giữ cho mép đá không bị rách",
        default=0.02,
        min=0.001,
        max=0.2,
        precision=3,
        unit='LENGTH'
    ) # type: ignore

    stone_surface_damage_noise_strength: bpy.props.FloatProperty(
        name="Cường Độ Lồi / Lõm",
        description="Độ sâu của vết lõm hoặc độ nhô cao của phần lồi",
        default=0.04,
        min=0.0,
        max=1.0,
        precision=3,
        unit='LENGTH'
    ) # type: ignore

    stone_surface_damage_noise_scale: bpy.props.FloatProperty(
        name="Độ Chi Tiết (Noise Scale)",
        description="Kích thước của dải sóng nhiễu. Số nhỏ = Sóng to thoai thoải; Số lớn = Gồ ghề lắt nhắt",
        default=2.5,
        min=0.1,
        max=50.0,
        precision=2
    ) # type: ignore


    # TẠO ĐƯỜNG LÁT ĐÁ
    # TẠO ĐƯỜNG LÁT ĐÁ
    # TẠO ĐƯỜNG LÁT ĐÁ

    stone_path_alignment: bpy.props.EnumProperty(
        name="Căn Lề",
        description="Vị trí của con đường so với đường Curve",
        items=[
            ('CENTER', "Ở Giữa", "Đường Curve chạy xuyên qua chính giữa con đường"),
            ('LEFT', "Bên Trái", "Con đường lấn sang trái đường Curve"),
            ('RIGHT', "Bên Phải", "Con đường lấn sang phải đường Curve")
        ],
        default='CENTER'
    ) # type: ignore

    stone_path_num_lanes: bpy.props.IntProperty(
        name="Số Làn Đá",
        description="Số làn đá ghép ngang lại thành đường",
        default=3,
        min=1,
        max=30
    ) # type: ignore

    stone_path_lane_width: bpy.props.FloatProperty(
        name="Bề Rộng Làn",
        description="Bề rộng của mỗi làn đá",
        default=0.4,
        min=0.05,
        max=5.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_path_stone_thickness: bpy.props.FloatProperty(
        name="Độ Dày Đá",
        description="Độ dày của viên đá (phần nhô lên khỏi mặt đất)",
        default=0.15,
        min=0.01,
        max=2.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_path_min_length: bpy.props.FloatProperty(
        name="Chiều Dài Min",
        description="Chiều dài ngắn nhất của 1 viên đá dọc theo đường",
        default=0.4,
        min=0.05,
        max=5.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_path_max_length: bpy.props.FloatProperty(
        name="Chiều Dài Max",
        description="Chiều dài dài nhất của 1 viên đá dọc theo đường",
        default=1.0,
        min=0.1,
        max=20.0,
        precision=2,
        unit='LENGTH'
    ) # type: ignore

    stone_path_gap_size: bpy.props.FloatProperty(
        name="Khe Hở (Vữa)",
        description="Khoảng cách mạch vữa/đất giữa các viên đá",
        default=0.03,
        min=0.0,
        max=0.5,
        precision=3,
        unit='LENGTH'
    ) # type: ignore

    # --- PHẦN LOGIC LƯỚI (GRID) ---
    # --- PHẦN LOGIC LƯỚI (GRID) ---
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