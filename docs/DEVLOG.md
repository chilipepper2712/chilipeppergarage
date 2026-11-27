# Chili Pepper Garage · Dev log (24–27/11/2026)

App tham khảo độ xe cho xe đời thường ở Việt Nam. Chọn xe, để garage tên **Ớt** lên đồ theo ngân sách, rồi xem số liệu thay đổi thế nào: giá đồ, cờ đăng kiểm, dyno, drag 1/4 dặm, tốc độ tối đa, so sánh trước/sau khi độ. 3D low-poly, texture pixel, lớp lọc PS1 chỉ là nền tạo không khí garage; dữ liệu mới là phần chính.

Bản có ảnh: trang artifact "Chili Pepper Garage Devlog". Ảnh gốc (3840×2160, khung PC 1920×1080 ở độ nét gấp đôi) nằm trong `docs/showcase/`.

| | |
|---|---|
| Xe | 10 xe phổ thông, từ Vios đến Ranger |
| Model 3D | 6 model đại diện 6 kiểu thân |
| Không gian | Xưởng, Phụ tùng độ, Dyno, Hầm gió |
| Mâm | 8 mẫu × 4 màu |
| Kích thước | một file HTML ~3,6 MB tự chứa mọi model |

## Các không gian

**Mở đầu** (`01_mo-dau.png`, `02_ot-len-do.png`). Garage tối, chưa có xe: "Anh em đang đi xe gì?". Chọn xe xong, đèn neon và đèn trần chớp sáng lần lượt, rồi Ớt hỏi ngân sách (10–200 triệu) và mục tiêu: êm hơn, lái vui hơn, nhanh hơn, ngầu hơn. Ớt tính theo giá cao của từng món nên không vượt ngân sách. Có nút bỏ qua để tự chọn.

**Xưởng** (`03`, `04`, `05`). Ớt chọn xong thì bảng Hiệu năng hiện ra: món đã chọn, giá tạm tính, cờ đăng kiểm. Trên xe chỉ đổi mâm, hạ gầm, màu sơn; các món khác treo lên pegboard. Mâm có 8 mẫu theo dáng mâm phổ biến (không logo), mặt lõm vào trong lốp, 4 màu: chrome xám, đồng, đen, trắng. Giá: Phổ thông 6–9,5 triệu/bộ, Premium 50–85 triệu/bộ.

**Phụ tùng độ** (`06`). Một tấm pegboard liền dưới dải cửa sổ. Món đã chọn treo lên bảng, hộp và lốp đứng dưới chân. Rê chuột hoặc chạm để hiện thẻ tên, giá, cờ đăng kiểm; trong thẻ có nút thùng rác để gỡ.

**Hiệu năng** (`07`). Đồ chia ba nhóm: thay đổi số liệu, độ êm, cảm giác. Mỗi món có thương hiệu theo mức Phổ thông / Premium, khoảng giá và cờ đăng kiểm (qua, tuỳ trạm, nên gỡ). Số ước lượng có dấu `~`.

**Dyno** (`08`–`11`). Phòng riêng. Bấm Dyno là xe lái từ cửa cuốn thẳng lên con lăn, bánh lăn theo quãng đường. Màn console và màn treo tường là canvas tự vẽ: lúc chờ tự chuyển trang, lúc đo vẽ đường công suất thật từ bộ mô phỏng, bánh quay trên con lăn. Bảng kết quả nền trong suốt. Drag 1/4 dặm so zin với bản độ theo từng mốc.

**So sánh** (`12`). Bản độ so với bản zin, thêm tối đa 3 xe zin khác. Thông số thực tách riêng với thang điểm ước lượng của tiệm.

**Hầm gió** (`13`, `14`). Quạt lớn, bàn xoay, đèn LED. Dòng khói nắn theo đường bao của xe (minh hoạ, không phải mô phỏng chất lưu). Bên dưới là Cd·A, lực nâng/ép, zin so với độ. Tắt đèn để chỉ còn khói.

## Nhật ký

### 24/11 · Nền móng
- Pipeline tạo xe bằng Blender chạy như module Python: loft thân xe theo đường bao đo trên blueprint, khoét hốc đèn và lưới tản nhiệt, texture pixel 64 px/m.
- Garage 3D trên web bằng three.js, bộ mô phỏng dyno và drag.
- Gộp bảng benchmark đồ độ: danh mục theo mức giá, 7 trục điểm, tab So sánh.
- Hầm gió tự chế với khói bám theo dáng xe; lực nâng/ép tính vào tải trên cầu chủ động khi chạy drag.
- Database 10 xe: mỗi thông số có nguồn hoặc mang dấu `~`. Nguồn và cách tính gói vào nút bấm.
- Bố cục tab dưới, icon outline thay chữ. Thêm Xpander làm model đại diện MPV.

### 25/11 · Ớt lên tiếng
- Màn mở đầu: garage trống, chọn xe, đèn chớp lần lượt.
- Bộ chọn đồ theo ngân sách và mục tiêu, tính theo giá cao.

### 26/11 · Pegboard và góc garage
- Khung sedan mẫu kèm hướng dẫn để tự dựng model mới.
- Thử nhập xe từ Kenney Car Kit (CC0); nhìn cục mịch so với phong cách chung nên không dùng.
- Pegboard qua 4 vòng chỉnh: từ hai kệ thành một tấm liền canh giữa dưới cửa sổ, đồ treo to hơn cỡ thật ~1,55 lần. Body kit rời khỏi xe để lên bảng.
- Góc ngồi: thử sofa rồi bỏ, giữ bàn két nước và hai ghế lưới sắt.
- Bốn vị trí camera do người dùng tự chọn.

### 27/11 · Dyno, số liệu, mâm
- Dyno tách thành phòng riêng. Trong xưởng không có đường cho xe lái vào: cầu thang gác lửng nằm đúng trục làn, chỗ đỗ lệch ngang 3,9 m nên đi chữ S kiểu gì bánh cũng đè khối chắn.
- Phòng dyno dùng vật liệu xưởng: vữa chân tường, gạch, mái dốc trên vì kèo và xà gồ, đèn sàn chiếu đuôi xe, thùng carton.
- Rà nguồn số liệu: Civic FD hết số ước lượng; Ranger, Xpander, CX-5, Mazda 3, Accent thêm nguồn; chạy hiệu chỉnh lại.
- 8 mẫu mâm, mặt lõm, 4 màu; giá theo mức Phổ thông / Premium.
- Sửa vạch vàng chỗ đỗ cho khớp nền epoxy đã dời.

## Cách làm
- **Model xe:** 6 model loft cho 6 kiểu thân. Xe không có model riêng mượn model cùng kiểu thân rồi kéo theo kích thước thật; lốp đúng cỡ của xe.
- **Màu bằng dải màu khoá:** texture sơn vẽ bằng dải màu khoá, viewer đổi sang màu thật. Mâm làm cùng kiểu, rồi dựng lại độ bóng / độ kim loại theo màu.
- **Mô phỏng:** đường mô-men qua hộp số tới bánh, giới hạn bởi độ bám. Cd·A hiệu chỉnh khớp tốc độ tối đa công bố, hệ số thời gian kT khớp 0–100 có nguồn.
- **Một file:** mọi model và texture nhúng vào một file HTML ~3,6 MB, chỉ tải three.js từ CDN. Lọc PS1 giảm màu 15-bit với dither Bayer.

## Còn dở
- Vios, City chưa có nguồn tỉ số hộp số và cầu; MINI thiếu gầm, lốp, các số giữa.
- Cd hiệu chỉnh của Xpander (0,298) và CX-5 (0,371) lệch khỏi mức hợp lý; nghi tốc độ tối đa đo được không phải giới hạn do cản gió.
- Chưa test thao tác chạm trên tablet thật.
- Chia sẻ bản độ qua link.
- Góc trước bên trái garage trống; đồ body kit trên pegboard còn khó nhận ra.
