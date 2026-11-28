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
/home/user/.venv/bin/python env/dyno_env.py          # phòng dyno -> out/env/dyno.glb
/home/user/.venv/bin/python pipeline/build_car.py <car> [lip|sport|diffuser|skirt]
node perf/calibrate.js --write                       # khớp Cd·A + hệ số thời gian kT vào data/garage-db.json
python3 viewer/build_bundle.py                       # gói mọi thứ vào viewer/index.html (~2.95 MB)
```

**Môi trường:**
- Blender là module Python `bpy` (bản 5.2) nằm trong `/home/user/.venv`. Container mới thì tạo lại: `python3.13 -m venv /home/user/.venv && /home/user/.venv/bin/pip install -r requirements.txt`.
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
`viewer/index.src.html` cộng các module, `build_bundle.py` gói tất cả thành `index.html`. Thứ tự nạp: `perf/*.js` (script thường) → `perf-ui.js` → `tunnel.js` → `wall.js` → `dyno.js` → `views.js`.

**Từng file:**
- `index.src.html`:
  - cảnh, đèn có bộ điều độ sáng (`dimReg`, các nhóm `amb / neon / tube0 / tube1 / key / work / fill`);
  - màn mở đầu: garage trống → chọn xe → đèn chớp lần lượt → thẻ ngân sách **Ớt lên đồ**;
  - layout: thông tin xe góc trái trên, nút hiển thị (PS1 / 15-bit / Đèn / Xoay) góc phải trên (không còn biển số), 4 nút vị trí góc phải dưới, các tab bên dưới (Ngoại thất / Hiệu năng / So sánh / Khí động). Cột 4 tab Ngoại thất là cụm tạm tính, chép từ tab Hiệu năng (`priceTotalX`…);
  - khổ ≤ 1280 px (iPad ngang): thanh tab giữ một hàng, dải chip gói độ cuộn ngang.
- `perf-ui.js`: tab Hiệu năng và So sánh, chạy dyno và drag (bảng kết quả `#results`), các gói độ, gọi bộ chọn đồ theo ngân sách.
- `tunnel.js`: hầm gió (luồng khói, số khí động). Chỉ nhận nút `tunnel`; xuất ra `window.__tunnel.setRoom`.
- `wall.js`: pegboard. Món được chọn treo lên bảng, hộp và lốp đứng dưới chân bảng. Rê chuột hoặc chạm hiện thẻ; chạm để ghim, trong thẻ có nút thùng rác để gỡ.
- `dyno.js`: phòng dyno riêng (như hầm gió). Vào phòng là xe lái từ cửa cuốn thẳng lên con lăn (thời gian tính theo frame, chặn dt để lần đầu biên dịch shader không làm xe nhảy cóc), bánh quay theo quãng đường. Màn hình console và màn treo tường là canvas tự vẽ (lúc chờ tự chuyển trang, lúc đo hiện số thật từ `window.__dynoRun`); bánh quay khi đo. Xuất `window.__dyno` (`enter`, `leave`, `ready`).
- `views.js`: điều phối 4 nút. Xưởng / Phụ tùng độ là camera lướt trong garage; Dyno giao cho `dyno.js`, Hầm gió cho `tunnel.js`.

**Biến toàn cục dùng chung giữa các module:**

| Biến | Nội dung |
|---|---|
| `__garage` | `BAY_X`, camera, controls, scene, state, CARS, apply, carRoot, wheelGroup, load, prepMaterials, dimReg, HOOKS (frame / change), GARAGE_OBJS… |
| `__perf` | cars, plan, applyBuild, selected, info, bodyPrice, drop |
| `__wall` | trạng thái pegboard, `unpin` |
| `__views` | `go`, `current` |
| `__tunnel` | `setRoom` |
| `__dyno` | `enter`, `leave`, `ready` (promise: xe đã dừng trên con lăn) |
| `__dynoRun` | dữ liệu lần chạy dyno đang diễn ra |

**Quy ước toạ độ:**
- Blender (x, y, z) → three.js (x, z, −y).
- Xe hướng +Y trong Blender. Trong garage `carRoot.rotation.y = π` (đầu xe hướng ra cửa garage).

**Các mốc trong garage (toạ độ Blender):**
- **Chỗ đỗ:** tâm `x = 0.5`, tức `BAY_X`, đã dời một ô gạch 0,5 m về phía pegboard.
- **Pegboard:** tường phải `x = 5.48`, `y` từ −3.6 đến 1.8, `z` từ 0.3 đến 2.34. Nằm dưới dải cửa sổ (z 2.4–4.1).
- **Góc ngồi trước pegboard:** bàn két nước và 2 ghế lưới sắt. Sofa đã bỏ.
- **Góc trước bên trái** (chỗ khu dyno cũ): đang trống.

**Phòng dyno** (`env/dyno_env.py`, toạ độ Blender): rộng 7,2 m, cửa cuốn ở `y = 7`, con lăn ở `y = −1.35`, quạt thổi trước mũi xe, console và màn treo tường bên trái. Vật liệu giống xưởng (vữa chân tường, gạch phía trên, mái dốc trên vì kèo + xà gồ). Đèn sàn vàng (dùng chung `floor_flood()` với xưởng) đặt sau xe bên phải, chiếu vào đuôi; ống hút khói và chồng carton bên trái. Viewer đặt xe sao cho trục trước nằm trên con lăn (gốc xe `y = ROLL + wheelbase/2`).
- **Camera mặc định:** (−3.1, 2.4, 5.6), nhìn vào (1.4, 0.75, −0.5).

**Dữ liệu:**
- `data/garage-db.json`: 13 xe (tên xe không kèm trim; trim nằm ở field `trim`, hiện ở dòng phụ "Số liệu bản …"), nguồn từng thông số, danh sách kiểu thân → model đại diện.
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
| Dyno | Phòng riêng, không nằm trong garage (garage chật, cầu thang chắn làn vào). Xe lái thẳng từ cửa vào băng |
| Panel kết quả | Nền trong suốt (alpha .74) để nhìn thấy phòng phía sau |
| Màn mở đầu | Garage trống → "Anh em đang đi xe gì?" → đèn neon chớp lần lượt → ngân sách 10–200 triệu + mục tiêu (Êm / Vui / Nhanh / Ngầu), có nút bỏ qua |
| Mâm | 8 mẫu độ theo ảnh user gửi (6 chấu, 8 chấu, 5 chấu lip, chữ Y, lưới, rally, lỗ thoáng, 3 chấu) + zin. Chỉ lấy dáng, không logo, tên chung. Mặt mâm độ lõm (concave: vành thụt 3 cm, tâm 6 cm); zin phẳng |
| Giá mâm | Theo mức: Phổ thông 6–9,5 tr/bộ (hàng TQ / Thái), Premium 50–85 tr/bộ (hàng Nhật chính hãng, gồm cả mâm 2 mảnh). Nhãn ghi xuất xứ, không ghi tên hãng |
| Màu mâm | 4 màu: Chrome xám (mặc định), Đồng, Đen, Trắng. Mặt mâm vẽ bằng dải màu khoá `rimkey`, viewer đổi màu + dựng lại độ bóng/kim loại (`recolorRims`). Vành lip của 5 chấu và 3 chấu giữ kim loại đánh bóng. Mâm zin không đổi màu |
| Sprite stacking | Đã thử, chưa dùng (ý tưởng: icon trong ô chọn xe) |

## 6. Việc còn dở
- **Bảng kết quả dyno** vẫn nằm giữa khung, đã làm trong suốt hơn. Phương án thu nhỏ, dạt sang một bên vẫn còn để ngỏ.
- **Góc trước bên trái garage** trống sau khi dời dyno đi, chưa bày gì.
- **Đồ body kit trên pegboard** chỉ là những thanh xám, khó nhận ra. User chưa phàn nàn.
- **Chưa test trên tablet thật** (thao tác chạm). Đã kiểm tra bố cục ở 1024 / 1180 / 1280 px.
- **VinFast VF3** user muốn thêm, đang chờ quyết: là xe điện, bộ mô phỏng chưa có động cơ điện (một cấp số, mô-men phẳng rồi công suất không đổi) và phần lớn đồ độ hiệu năng không áp được; dáng hộp dài ~3,2 m, model hatchback kéo ra sẽ sai dáng.
- **Số liệu xe mới:** Swift (CVT, 0–100, tối đa ước lượng; nguồn VN lệch mô-men 108–113 Nm, lốp R16/R17), Corolla Cross (CVT, 0–100, tối đa ước lượng; Cd hiệu chỉnh 0,399 cao), XL7 (đủ nguồn trừ vòng tua tối đa).
- **Số liệu còn ước lượng** (sau đợt rà 11/2026, mạng container chặn PDF hãng nên chỉ dựa vào kết quả search): Vios và City (tỉ số truyền + cầu), Accent (khối lượng, cầu), Mazda 3 và CX-5 (cầu), MINI (gầm, lốp, số giữa + cầu), Ranger (tỉ số hộp số). Cd hiệu chỉnh của Xpander (0,298) và CX-5 (0,371) lệch khỏi mức hợp lý, nghi vmax đo không phải giới hạn do cản gió.
- **Đề xuất cũ chưa làm:**
  - chia sẻ bản độ qua link (`#hash`);
  - bổ sung nguồn số liệu để bớt dấu `~` (tỉ số truyền phần lớn chưa có nguồn; Ranger XLS là xe yếu dữ liệu nhất);
  - rà điều khoản các nguồn dữ liệu trước khi chia sẻ rộng.
- **Debug hook:** `window.__wall` đang dùng cho test Playwright.
