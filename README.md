# Chili Pepper Garage

Demo game garage xe đời thường ở Việt Nam: low-poly, texture pixel, ánh sáng hiện đại, lớp filter PS1.
Sửa xe, độ ngoại thất và hiệu năng, chạy dyno và drag 1/4 dặm.

**Xe:** Mazda 2 DE 2013 · Honda Civic FD 2008 · Mazda CX-5 2020 · MINI Cooper S 5 cửa 2018 · Ford Ranger Raptor 2019

## Xem ngay
Mở `viewer/index.html` trong trình duyệt. File tự chứa toàn bộ model và texture, chỉ tải three.js từ CDN.

## Cấu trúc
| Thư mục | Nội dung |
|---|---|
| `cars/` | Profile từng xe: kích thước, đường bao đo trên blueprint, hốc grill/đèn, decal, biến thể đồ độ |
| `pipeline/` | Bộ dựng xe bằng Blender (bpy): loft, khoét hốc, UV1 atlas 64 px/m, UV2 wrap chung, vẽ texture pixel, tách panel, socket, mâm, cánh gió, kiểm tra chồng blueprint |
| `env/` | Bộ dựng garage (tường gạch, gác lửng, đèn công trình, neon) |
| `perf/` | Mô phỏng dyno/drag/tốc độ tối đa (`sim.js`), model bản độ → 7 trục điểm, giá, đăng kiểm (`model.js`), thông số gốc từng xe (`cars.json`), danh mục đồ độ gộp từ bảng benchmark Chili Paprika (`parts.json`), script hiệu chỉnh |
| `viewer/` | Garage 3D trên web (three.js). Sửa `index.src.html` / `perf-ui.js`, rồi build ra `index.html` |
| `out/` | Model đã build: `.glb`, `.fbx`, texture, món độ trong `parts/` |
| `blueprints/` | `calib.json` căn tỉ lệ từng bản vẽ (ảnh blueprint không commit) |
| `docs/` | Spec chuẩn model |

## Build
```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python pipeline/build_car.py mazda2_2013            # xe gốc + panel zin + mâm + cánh gió
python pipeline/build_car.py mazda2_2013 sport      # một biến thể đồ độ (lip | sport | diffuser | skirt)
python env/garage_env.py                            # garage
python3 viewer/build_bundle.py                      # nhúng toàn bộ vào viewer/index.html
node perf/calibrate.js                              # 0–100 xe zin so với số hãng
```

## Quy ước
1 unit = 1 m, Z lên, xe hướng +Y, gốc tọa độ ở mặt đất giữa hai trục. Texture xe vẽ bằng dải màu khóa (xanh),
viewer đổi sang màu thật. Chi tiết trong `docs/model_spec.md`.
Số liệu chưa xác nhận được đánh dấu `TBD` / `tbd` trong profile xe và `perf/cars.json`.
