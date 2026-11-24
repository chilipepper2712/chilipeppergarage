# Garage Demo — Model Spec v0.1 (draft)

## 1. Quy ước chung
- Đơn vị: 1 unit = 1 m. Kích thước lấy từ thông số nhà sản xuất (ưu tiên bản bán tại VN).
- Trục: Z lên, xe hướng +Y, X sang phải người lái.
- Gốc tọa độ: mặt đất, chính giữa 2 trục bánh (theo trục Y), giữa xe (theo trục X).
- Bánh: tâm bánh đặt tại (±track/2, ±wheelbase/2, tire_diameter/2).
- Poly budget: 500–800 đỉnh/xe (đã tách panel), bánh ≤ 64 đỉnh/cái.

## 2. Texture
- UV1 = atlas cố định 512×512/xe (kính, đèn, lưới, gầm, nội thất). Texel density 64 px/m.
- UV2 = wrap layout, **khuôn chung cho cả 5 xe**: hông trái, hông phải, capo, mui, cốp/đuôi, cản trước, cản sau — vị trí cố định trên canvas, scale theo kích thước thật, cùng texel density.
- Filtering: point/nearest, không mipmap blur (hoặc mipmap nearest).

## 3. Panel tách rời (cho sửa chữa)
`body_core`, `hood`, `trunk|tailgate|bed`, `door_FL/FR(/RL/RR)`, `fender_FL/FR`, `bumper_F/R`, `mirror_L/R`, `light_F/R`.
Mỗi panel: state `ok / dented / missing`, mesh dented là biến thể cùng UV.

## 4. Socket (điểm gắn)
`wheel_FL/FR/RL/RR`, `bumper_F/R`, `hood`, `spoiler`, `roof`, `exhaust`, `skirt_L/R`, `grille`.
Empty object trong Blender, tên đúng như trên, export kèm FBX/GLB.

## 5. Mâm & lốp (tham số)
- Mâm: `diameter_in`, `width_in`, `offset_mm`, `spoke_count`, `spoke_style`, `dish_depth`.
- Lốp: `width_mm / aspect / rim_in` → đường kính ngoài = rim_in·25.4 + 2·width·aspect/100.
- Mọi mâm lắp được mọi xe; chỉ đổi scale theo cỡ.

## 6. Dàn xe

| Xe | Dài | Rộng | Cao | Cơ sở | Vệt T/S | Lốp gốc | Ø lốp (mm) | Nguồn / ghi chú |
|---|---|---|---|---|---|---|---|---|
| Honda Civic 1.8 MT (FD, 2008) | 4540 | 1750 | 1450 | 2700 | 1500 / 1530 | 195/65R15 | 634.5 | bonbanh (đời 2007, cùng gen) |
| Mazda CX-5 (2020) | 4550 | 1840 | 1680 | 2700 | TBD | 225/55R19 | 730.1 | bonbanh 2.0 Premium |
| Mazda 2 hatch 1.5 MT (2013) | 3885 | 1695 | 1475 | 2490 | TBD | 185/55R15 | 584.5 | bonbanh, lắp ráp VN |
| Ford Ranger Wildtrak (T6 FL, 2018) | 5362 | 1860 | 1830 | 3220 | TBD / 1560 | 265/60R18 | 775.2 | bonbanh — **gen chưa chốt** |
| Mini Cooper S (R56, ~2010) | 3729 | 1683 | 1407 | 2467 | 1453 / 1461 | 195/55R16? | 620.9 | **gen chưa chốt**, lốp cần xác nhận |
| Mini Cooper S (F56, 2014+) | 3850 | 1727 | 1414 | 2495 | 1485 / 1485 | 195/55R16? | 620.9 | phương án thay R56 |

TBD = chưa có số. Tạm tính vệt bánh ≈ rộng − ~250 mm nếu không tìm được.

## 7. Việc còn mở
- [ ] Chốt gen Ranger (T6 2015–2022 vs Next-gen 2022+)
- [ ] Chốt gen Mini (R56 vs F56)
- [ ] Điền vệt bánh CX-5, Mazda 2, Ranger trước
- [ ] Blueprint 3 view cho từng xe (side/front/top, cùng scale)
