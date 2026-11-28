# Chili Pepper Garage

App độ xe tham khảo cho xe đời thường ở Việt Nam: low-poly, texture pixel, ánh sáng hiện đại, lớp filter PS1.
Sửa xe, độ ngoại thất và hiệu năng, chạy dyno và drag 1/4 dặm.

**Xe:** Vios, Accent, City, Mazda 3, Civic FD (sedan) · Mazda 2, Swift (hatchback) · MINI Cooper S (hatchback thể thao) · CX-5, Corolla Cross (SUV / crossover) · Xpander, XL7 (MPV) · Ranger (bán tải). Xe không có model riêng dùng model đại diện của kiểu xe, kéo theo kích thước thật.

## Xem ngay
Mở `viewer/index.html` trong trình duyệt. File tự chứa toàn bộ model và texture, chỉ tải three.js từ CDN.

## Cấu trúc
| Thư mục | Nội dung |
|---|---|
| `cars/` | Profile từng xe: kích thước, đường bao đo trên blueprint, hốc grill/đèn, decal, biến thể đồ độ |
| `pipeline/` | Bộ dựng xe bằng Blender (bpy): loft, khoét hốc, UV1 atlas 64 px/m, UV2 wrap chung, vẽ texture pixel, tách panel, socket, mâm, cánh gió, kiểm tra chồng blueprint |
| `env/` | Bộ dựng garage (tường gạch, gác lửng, đèn công trình, neon) phòng thử gió tự chế (`tunnel_env.py`) và phòng dyno (`dyno_env.py`) |
| `data/` | `garage-db.json`: 13 xe, mỗi thông số có nguồn (`src`) hoặc đánh dấu ước lượng (`est`), danh sách nguồn, kiểu xe → model đại diện, disclaimer |
| `perf/` | Mô phỏng dyno/drag/tốc độ tối đa (`sim.js`), model bản độ → 7 trục điểm, giá, đăng kiểm (`model.js`), chuyển database thành đầu vào mô phỏng (`db.js`), danh mục đồ độ gộp từ bảng benchmark Chili Paprika (`parts.json`), script hiệu chỉnh |
| `viewer/` | Garage 3D trên web (three.js). Sửa `index.src.html`, `perf-ui.js`, `tunnel.js` (hầm gió), `wall.js` (pegboard đồ độ), `dyno.js` (phòng dyno, xe lái vào), `views.js` (điều phối 4 nút), rồi build ra `index.html` |
| `out/` | Model đã build: `.glb`, `.fbx`, texture, món độ trong `parts/` |
| `blueprints/` | `calib.json` căn tỉ lệ từng bản vẽ (ảnh blueprint không commit) |
| `docs/` | Spec chuẩn model, khung xe mẫu (`template.md`), bàn giao session (`HANDOFF.md`) |

## Build
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python pipeline/build_car.py mazda2_2013            # xe gốc + panel zin + mâm + cánh gió
python pipeline/build_car.py mazda2_2013 sport      # một biến thể đồ độ (lip | sport | diffuser | skirt)
python env/garage_env.py                            # garage
python env/tunnel_env.py                            # phòng thử gió
python env/dyno_env.py                              # phòng dyno
python env/wall_items.py                            # đồ treo pegboard
python3 viewer/build_bundle.py                      # nhúng toàn bộ vào viewer/index.html
node perf/calibrate.js --write                      # khớp Cd·A theo tốc độ tối đa, tính hệ số thời gian theo 0–100 có nguồn
```

## Quy ước
1 unit = 1 m, Z lên, xe hướng +Y, gốc tọa độ ở mặt đất giữa hai trục. Texture xe vẽ bằng dải màu khóa (xanh),
viewer đổi sang màu thật. Chi tiết trong `docs/model_spec.md`.
Số liệu chưa xác nhận được đánh dấu `TBD` / `tbd` trong profile xe và `perf/cars.json`.
