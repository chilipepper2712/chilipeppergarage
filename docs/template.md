# Khung xe mẫu (sedan) để dựng các kiểu thân

File: `models/template/sedan_template.blend`, tạo lại bằng `python pipeline/make_template.py`.

## Quy ước
- Đơn vị mét, trục Z hướng lên, **đầu xe hướng +Y**, phía phải người lái là +X.
- Gốc toạ độ: mặt đất, giữa hai trục bánh.
- Kích thước khung mẫu: dài 4,50 × rộng 1,76 × cao 1,49 m, chiều dài cơ sở 2,70 m, vệt bánh 1,52 m.

## Trong file có gì
| Collection | Nội dung |
|---|---|
| SHAPE | `shape`: vỏ xe **một mesh liền**, các phần là vertex group. `mirror_L`, `mirror_R`. |
| WHEELS | `wheel_FL/FR/RL/RR`: 4 bản liên kết của cùng một mesh `wheel`. Sửa một cái là cả 4 đổi theo. |
| SOCKETS | Empty `SOCKET_*`: tâm 4 bánh, đuôi xe (spoiler), cản, ống xả, nóc, capo. |
| MODS | Đồ độ mẫu, đặt sẵn đúng chỗ: `bumper_F_lip`, `bumper_R_diffuser`, `skirt_L_skirt`, `skirt_R_skirt`, `spoiler_roof_ext`, `spoiler_gt_wing`. Mặc định ẩn. |

Vertex group của `shape`: `body`, `bumper_F`, `bumper_R`, `hood`, `tailgate`, `fender_FL/FR`, `door_FL/FR/RL/RR`, `skirt_L/R`.
Vật liệu: `paint`, `glass`, `plastic`, `light_F`, `light_R`, `chrome`, `tyre`, `rim`.

## Cách nặn ra kiểu xe khác
- Giữ vỏ là **một mesh**. Kéo đỉnh trong Edit Mode, bật Proportional Editing (phím O). X-mirror đã bật sẵn nên sửa một bên là bên kia đi theo.
- Không dùng Sculpt Mode với Dyntopo hay Remesh: lưới sẽ dày và mất vertex group. Muốn thêm chi tiết thì loop cut (Ctrl+R). Đỉnh mới tự nhận group của cạnh hai bên.
- Đổi phạm vi một phần (ví dụ cửa dài hơn): chọn đỉnh rồi Assign/Remove trong bảng Vertex Groups. Mặt thuộc phần nào là do **cả 4 đỉnh** của nó cùng nằm trong group đó.
- Đổi chiều dài cơ sở hoặc cỡ lốp: dời 4 empty `SOCKET_wheel_*` và 4 bánh cùng chỗ. Script kiểm tra sẽ báo nếu bánh lệch socket.
- Vòm bánh đang là lỗ hở hình hộp (44 cạnh biên là của 4 lỗ này). Nặn tròn lại hoặc extrude vào trong làm hốc bánh tuỳ ý.
- Đồ độ: sửa hoặc thêm object trong MODS, đặt tên `<chỗ>_<món>` (ví dụ `bumper_F_sport`). Đặt đúng vị trí trên xe, không cần đưa về gốc toạ độ.
- Số mặt nên giữ trong khoảng 500–1200 cho thân xe (khung mẫu có 260).

## Kiểm tra và xuất
```bash
python pipeline/template_export.py models/<kieu>/<kieu>.blend <kieu>
```
Script kiểm tra trục, kích thước, group, socket, bánh xe; tách `shape` theo group thành object đúng tên; xuất `out/<kieu>/<kieu>_shape.glb`. Có lỗi là dừng và in lý do.
