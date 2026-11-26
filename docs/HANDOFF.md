# Handoff: Chili Pepper Garage

Tài liệu bàn giao cho một session mới. Đọc file này trước, rồi `README.md`.

## 1. Sản phẩm là gì
App **độ xe tham khảo** cho xe đời thường ở Việt Nam. Đây là app, không phải game.

- **Dữ liệu là phần chính:**
  - giá đồ độ, cờ đăng kiểm;
  - số liệu dyno, drag và tốc độ tối đa từ bộ mô phỏng;
  - so sánh trước và sau khi độ.
- **3D là nền tạo không khí garage,** không cần đúng từng chi tiết xe.
- **Phong cách:** low-poly, texture pixel, ánh sáng hiện đại, filter PS1 (dither màu 15-bit).
- **Thiết bị:** ưu tiên tablet và PC. Điện thoại là phụ; màn hẹp hơn 1024 px hiện cảnh báo kèm nút "Vẫn mở".
- **Giọng trong app:** garage tên là **Ớt**, gọi người dùng là **"anh em"**.
- **Nơi xem:**
  - artifact: https://claude.ai/artifact/K6PwJcChpgR9K8uemVn39f (cập nhật bằng cách publish lại `viewer/index.html`);
  - repo: `chilipepper2712/chilipeppergarage`, nhánh `main`, đang public. GitHub Pages user tự bật.

## 2. Cách user muốn làm việc
- **Xưng hô:** mày / tao, ngang hàng.
- **Thái độ:**
  - nói thẳng hay hoặc dở, chỉ ra chỗ hở, không khen máy móc;
  - giữ lập trường, chỉ đổi ý khi có lý lẽ.
- **Giao diện:**
  - ưu tiên icon outline hoặc flat, ít chữ;
  - thông tin phụ (nguồn, cách tính) gói vào nút bấm để mở;
  - số ước lượng đánh dấu bằng `~`.
- **Bản quyền:**
  - không dùng tên hay logo thương hiệu trên đồ trang trí (ví dụ két nước để trơn, không in Coca-Cola);
  - kiểm tra license trước khi dùng asset ngoài. Repo đang public.
- **Sau mỗi thay đổi:**
  1. build;
  2. test bằng Playwright, chụp màn hình;
  3. commit và push lên `main`;
  4. publish lại artifact;
  5. báo lại ngắn gọn.

## 3. Build và test
```bash
/home/user/.venv/bin/python env/garage_env.py        # garage -> out/env/garage.glb (+ anchors.json)
/home/user/.venv/bin/python env/wall_items.py        # đồ treo pegboard -> out/env/wall_items.glb
/home/user/.venv/bin/python env/tunnel_env.py        # hầm gió
/home/user/.venv/bin/python pipeline/build_car.py <car> [lip|sport|diffuser|skirt]
node perf/calibrate.js --write                       # khớp Cd·A + hệ số thời gian kT vào data/garage-db.json
python3 viewer/build_bundle.py                       # gói mọi thứ vào viewer/index.html (~2.95 MB)
```

**Môi trường:**
- Blender là module Python `bpy` (bản 5.2) nằm trong `/home/user/.venv`.
- Viewer dùng three.js 0.160 qua importmap trỏ tới jsDelivr.

**Test Playwright:**
- Route `https://cdn.jsdelivr.net/npm/three@0.160.0/**` sang một bản three.js cài local:
  ```bash
  npm i three@0.160.0
  ```
  chạy trong thư mục scratchpad.
- Route trang `index.html` sang nội dung file trên đĩa.
- Chạy Chromium với `--use-gl=swiftshader`.
- Luồng thử: chờ `#intro` hiện ra → bấm `.carbtn` → bấm `#budgetSkip` (hoặc chọn mục tiêu rồi bấm `#budgetGo`) → bấm các nút `[data-room=garage|parts|dyno|tunnel]`.
- Kiểm tra cú pháp module:
  ```bash
  node --input-type=module --check < viewer/<file>.js
  ```

## 4. Kiến trúc viewer
`viewer/index.src.html` cộng các module, `build_bundle.py` gói tất cả thành `index.html`. Thứ tự nạp: `perf/*.js` (script thường) → `perf-ui.js` → `tunnel.js` → `wall.js` → `views.js`.

**Từng file:**
- `index.src.html`:
  - cảnh, đèn có bộ điều độ sáng (`dimReg`, các nhóm `amb / neon / tube0 / tube1 / key / work / fill`);
  - màn mở đầu: garage trống → chọn xe → đèn chớp lần lượt → thẻ ngân sách **Ớt lên đồ**;
  - layout: thông tin xe góc trái trên, 4 nút vị trí góc phải dưới, các tab bên dưới (Ngoại thất / Hiệu năng / So sánh / Khí động).
- `perf-ui.js`: tab Hiệu năng và So sánh, chạy dyno và drag (bảng kết quả `#results`), các gói độ, gọi bộ chọn đồ theo ngân sách.
- `tunnel.js`: hầm gió (luồng khói, số khí động). Chỉ nhận nút `tunnel`; xuất ra `window.__tunnel.setRoom`.
- `wall.js`: pegboard. Món được chọn treo lên bảng, hộp và lốp đứng dưới chân bảng. Rê chuột hoặc chạm hiện thẻ; chạm để ghim, trong thẻ có nút thùng rác để gỡ.
- `views.js`:
  - 3 vị trí Xưởng / Phụ tùng độ / Dyno, camera lướt giữa các vị trí;
  - xe trượt sang băng dyno;
  - màn hình khu dyno là canvas tự vẽ (lúc chờ tự chuyển trang, lúc đo hiện số thật từ `window.__dynoRun`);
  - bánh xe quay khi đang đo.

**Biến toàn cục dùng chung giữa các module:**

| Biến | Nội dung |
|---|---|
| `__garage` | `BAY_X`, camera, controls, scene, state, CARS, apply, carRoot, wheelGroup, load, prepMaterials, dimReg, HOOKS (frame / change), GARAGE_OBJS… |
| `__perf` | cars, plan, applyBuild, selected, info, bodyPrice, drop |
| `__wall` | trạng thái pegboard, `unpin` |
| `__views` | `go`, `current` |
| `__tunnel` | `setRoom` |
| `__dynoRun` | dữ liệu lần chạy dyno đang diễn ra |

**Quy ước toạ độ:**
- Blender (x, y, z) → three.js (x, z, −y).
- Xe hướng +Y trong Blender. Trong garage `carRoot.rotation.y = π` (đầu xe hướng ra cửa garage).

**Các mốc trong garage (toạ độ Blender):**
- **Chỗ đỗ:** tâm `x = 0.5`, tức `BAY_X`, đã dời một ô gạch 0,5 m về phía pegboard.
- **Pegboard:** tường phải `x = 5.48`, `y` từ −3.6 đến 1.8, `z` từ 0.3 đến 2.34. Nằm dưới dải cửa sổ (z 2.4–4.1).
- **Góc ngồi trước pegboard:** bàn két nước và 2 ghế lưới sắt. Sofa đã bỏ.
- **Khu dyno:** góc trước bên trái, `x = −3.4`, con lăn ở `y = −5.0`, ngay dưới neon đỏ.
- **Camera mặc định:** (−3.1, 2.4, 5.6), nhìn vào (1.4, 0.75, −0.5).

**Dữ liệu:**
- `data/garage-db.json`: 10 xe, nguồn từng thông số, danh sách kiểu thân → model đại diện.
- `perf/parts.json`: danh mục đồ độ, các gói độ, đồ ngoại thất.
- `perf/planner.js`: Ớt chọn đồ theo ngân sách và mục tiêu, tính theo giá cao của từng món.

**Model:**
- 6 model loft đại diện 6 kiểu thân: Civic, Mazda 2, Mini, CX-5, Xpander, Ranger Raptor.
- `CAR_KIT = false`: body kit không gắn lên xe mà treo trên pegboard. Trên xe chỉ còn mâm, hạ gầm và màu sơn.

**Công cụ phụ:**
- `pipeline/make_template.py` + `template_export.py`: khung sedan mẫu cho user tự dựng model, hướng dẫn ở `docs/template.md`.
- `pipeline/kenney_import.py`: nhập xe từ Kenney Car Kit (CC0). Đã thử và user **không dùng** cho xe (nhìn cục mịch). Gói zip nằm ở máy user, không có trong repo.

## 5. Các quyết định đã chốt
| Chủ đề | Quyết định |
|---|---|
| Model xe | Giữ 6 model loft. Không trộn với bộ khác. User sẽ mua bộ low-poly retro khi có tiền |
| Đồ độ trên xe | Chỉ mâm, hạ gầm, sơn. Mọi món khác treo trên pegboard, dạng chung, không theo từng xe |
| Pegboard | Một tấm liền, không đường nối, canh giữa dưới cửa sổ. Đồ treo to khoảng 1,55 lần cỡ thật. Không vẽ ô trống. Thẻ thông tin dùng lá cờ màu thay cho chữ đăng kiểm |
| Camera | Không tự chạy theo thao tác. Người dùng tự chọn bằng 4 nút: Xưởng / Phụ tùng độ / Dyno / Hầm gió |
| Màn mở đầu | Garage trống → "Anh em đang đi xe gì?" → đèn neon chớp lần lượt → ngân sách 10–200 triệu + mục tiêu (Êm / Vui / Nhanh / Ngầu), có nút bỏ qua |
| Sprite stacking | Đã thử, chưa dùng (ý tưởng: icon trong ô chọn xe) |

## 6. Việc còn dở
- **Mâm:** user sẽ gửi ảnh 6–7 mẫu mâm phổ thông. Thay 5 mẫu tạm hiện tại (`stock`, `mesh`, `dish`, `steel`, `black6`). Mâm nằm trong `out/<model>/parts/wheel_*.glb`, dựng bằng `pipeline/wheel.py`.
- **Bảng kết quả dyno** đang che khu dyno lúc đo. Đã đề xuất thu nhỏ, dạt sang một bên; **user chưa trả lời**.
- **Xe sang băng dyno** đang trượt ngang. Có thể làm cảnh lái vào.
- **Đồ body kit trên pegboard** chỉ là những thanh xám, khó nhận ra. User chưa phàn nàn.
- **Chưa test trên tablet thật** (thao tác chạm).
- **Đề xuất cũ chưa làm:**
  - chia sẻ bản độ qua link (`#hash`);
  - bổ sung nguồn số liệu để bớt dấu `~` (tỉ số truyền phần lớn chưa có nguồn; Ranger XLS là xe yếu dữ liệu nhất);
  - rà điều khoản các nguồn dữ liệu trước khi chia sẻ rộng.
- **Debug hook:** `window.__wall` đang dùng cho test Playwright.
