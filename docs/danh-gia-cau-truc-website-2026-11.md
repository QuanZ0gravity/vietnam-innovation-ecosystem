# Đánh giá cấu trúc website và đề xuất (11/2026)

Tham chiếu: StartupBlink (trang quốc gia và thành phố), Algeria Ecosystem, Crunchbase, Dealroom.

## Đã làm trong đợt này

| Hạng mục | Thay đổi |
| --- | --- |
| Tìm kiếm | Ô tìm lớn ở đầu danh bạ, gợi ý tức thì có logo (tối đa 7 kết quả, dùng phím mũi tên); tìm trên tên, tên khác, lĩnh vực, mô tả, website; tìm nhiều từ. Nút tìm nhanh trên mọi trang, mở bằng phím "/" |
| Bộ lọc | Hai hàng chip có biểu tượng: loại tác nhân và 13 lĩnh vực, kèm số lượng cập nhật theo bộ lọc khác. Bộ lọc phụ (khu vực, tình trạng, mức xác minh, có logo, website, mô tả, LinkedIn) gom vào "Bộ lọc khác", hiện thành nhãn có nút xoá |
| Kết quả | Mặc định dạng thẻ: logo, tên, loại, khu vực, mô tả ngắn, lĩnh vực, mức xác minh. Sắp xếp mặc định "thông tin đầy đủ trước". Dạng danh sách có logo nhỏ |
| Logo | 415 logo (128 px, WebP) trong `logos/`, lấy từ website chính thức, trang sự kiện công khai và bản thử nghiệm; đã loại ảnh chụp sự kiện, ảnh tòa nhà và logo mặc định (WordPress). Hồ sơ không có logo hiện chữ cái đầu |
| Lĩnh vực | 13 lĩnh vực chuẩn hóa tính từ phân loại và mô tả khi dựng trang (không sửa dữ liệu gốc) |
| Trang thành phố | `/thanh-pho/` và trang riêng từng thành phố, theo cấu trúc của StartupBlink |

## Đề xuất tiếp theo, theo thứ tự ưu tiên

### 1. Kiến trúc thông tin
- **Trang chủ nói về Việt Nam, không chỉ Đà Nẵng.** Tiêu đề hiện là "Ai đang làm gì cho khởi nghiệp ở Đà Nẵng?". Đổi sang câu chung, thêm bộ chọn thành phố và khối "Cơ hội đang mở" lên trên cùng.
- **Gộp "Bản đồ" vào trang thành phố và danh bạ** (nút "Xem trên bản đồ"), vì bản đồ mới có 13 điểm. Giữ đường dẫn cũ.
- **Chính sách theo thành phố**: hiện 123 văn bản đều của Đà Nẵng; đưa vào trang Đà Nẵng và để trang Chính sách lọc theo tỉnh, thành.
- **Trang tổ chức hỗ trợ (PO, vườn ươm)** nên có chỉ số danh mục: số startup đã hỗ trợ, đang hoạt động, đã gọi vốn, giống mục "Startups supported" của StartupBlink.

### 2. Dữ liệu
- **Phân loại lĩnh vực trong dữ liệu gốc**: thêm trường `sectors` vào schema để người đóng góp chọn, thay cho việc đoán bằng từ khóa (hiện 295 hồ sơ chưa xếp được lĩnh vực).
- **Giai đoạn và vốn** (`stage`, khoản gọi vốn có nguồn) để lọc theo giai đoạn như Dealroom.
- **Tọa độ**: chỉ 13 tác nhân có tọa độ; cần địa chỉ từ chính tổ chức.
- **Chuẩn hóa tên**: còn khoảng 60 tên pháp lý dài kiểu "Công ty TNHH…"; nên đặt tên thương hiệu làm tên chính.
- **254 tác nhân "Việt Nam, chưa rõ tỉnh"** cần gán tỉnh, thành.

### 3. Trải nghiệm
- **Trang tác nhân**: thêm khối "Tương tự" (cùng lĩnh vực, cùng khu vực), dòng thời gian (thành lập, ươm tạo, cuộc thi, gọi vốn) và nút chia sẻ.
- **Xuất dữ liệu**: nút tải CSV theo bộ lọc hiện tại (StartupBlink thu phí phần này; ở đây mở miễn phí là điểm khác biệt).
- **SEO**: thẻ Open Graph có logo cho từng hồ sơ, `sitemap.xml` theo thành phố, dữ liệu có cấu trúc `Organization`.
- **Hiệu năng**: `actors.json` đã gần 1 MB; tách bản rút gọn cho tìm kiếm (tên, loại, khu vực, lĩnh vực, logo) và tải mô tả khi cần.

### 4. Quy trình
- **Biểu mẫu tự khai cho tổ chức** có ô tải logo, LinkedIn, website, lĩnh vực; duyệt qua Pull Request.
- **Kiểm tra tự động logo** khi có Pull Request (đúng kích thước, nền trong suốt, không phải ảnh chụp).

## Cập nhật 21/11/2026: đã thực hiện

- Trang chủ nói về cả Việt Nam: tiêu đề mới, bộ chọn thành phố (Toàn quốc, TP.HCM, Hà Nội, Đà Nẵng, Hải Phòng) kèm số tác nhân, số cơ hội và hạng, khối "Cơ hội đang mở" ngay dưới phần đầu trang, startup có hồ sơ đầy đủ kèm logo.
- Bản đồ gộp vào Danh bạ (chế độ xem thứ ba, theo đúng bộ lọc đang chọn) và vào trang từng thành phố. Mục "Bản đồ" bỏ khỏi thanh điều hướng; đường dẫn `/ban-do/` tự chuyển sang Danh bạ.
- Trường `sectors` trong schema (13 mã), biểu mẫu Issue có ô chọn lĩnh vực, 468 hồ sơ được gán gợi ý ban đầu.
- Nút **Tải CSV** trong Danh bạ, xuất đúng các hồ sơ theo bộ lọc hiện tại.

## Đợt 1 sau audit (21/11/2026): đã thực hiện

- Mọi trang có `canonical`, Open Graph (`og:url`, `og:title`, `og:description`, `og:image`, `og:locale`) và thẻ Twitter. Ảnh chia sẻ mặc định `assets/og-default.png` (1200 × 630).
- Trang chuyển hướng (`/ban-do/`, `/su-kien/`) và 404 có `noindex`, không vào sitemap.
- Hồ sơ tổ chức có dữ liệu có cấu trúc schema.org (`Organization`, `EducationalOrganization`, `GovernmentOrganization`): tên, logo, mô tả, website và LinkedIn (`sameAs`), năm thành lập, địa phương, lĩnh vực. Trang chủ có `WebSite` kèm ô tìm kiếm (`SearchAction`).
- Mô tả trang riêng cho từng trang; hồ sơ chưa có mô tả hoặc mô tả quá ngắn được ghép câu tự sinh (loại, địa phương, lĩnh vực).
- Hồ sơ có hai khối "Cùng lĩnh vực" và "Cùng địa phương" (mỗi khối 6 hồ sơ, ưu tiên có logo và mô tả). Mỗi khối gồm 4 hồ sơ đầy đủ thông tin nhất và 2 hồ sơ kế cận theo tên, để cả hồ sơ ít thông tin cũng được liên kết tới. Trung bình mỗi hồ sơ giờ có 10.8 liên kết trỏ tới; hồ sơ chỉ có tối đa một liên kết giảm từ 538 xuống 2.
- Sitemap chia thành tệp chỉ mục `sitemap.xml` và các tệp con `sitemap-trang.xml`, `sitemap-thanh-pho.xml`, `sitemap-to-chuc-N.xml` (tối đa 500 trang mỗi tệp). `lastmod` của hồ sơ lấy theo lần sửa gần nhất của tệp dữ liệu trong git.

## Đợt 2 (21/11/2026): đã thực hiện

- Thanh điều hướng mới: Danh bạ · Địa phương · Lĩnh vực · Cơ hội · Chính sách · Dữ liệu (logo dẫn về trang chủ). Chân trang: Giới thiệu, Phương pháp, Đóng góp, Dữ liệu, GitHub.
- 8 trang đích theo loại trong `/danh-ba/`: `startup/`, `quy-dau-tu/`, `ho-tro-khoi-nghiep/`, `truong-vien/`, `co-quan-nha-nuoc/`, `doanh-nghiep/`, `doi-tac-quoc-te/`, `du-an-sang-tao/`. Mỗi trang: giới thiệu, chỉ số, 24 hồ sơ nổi bật, phân bố theo địa phương và lĩnh vực, nút lọc và tải CSV, nút xem bản đồ.
- `/linh-vuc/` và 13 trang lĩnh vực, cùng cấu trúc, kèm cơ hội liên quan.
- 24 trang chi tiết cơ hội `/co-hoi/<mã>/`: thông tin đầy đủ, đơn vị tổ chức, toàn bộ đơn vị tham gia có logo, cơ hội cùng loại, dữ liệu có cấu trúc `Event`.
- 123 trang chi tiết văn bản `/chinh-sach/<mã>/`: số hiệu, loại văn bản, cơ quan ban hành, ngày, tóm tắt, đường dẫn toàn văn, văn bản cùng loại cùng năm, dữ liệu có cấu trúc `Legislation`.
- `/du-lieu/`: tải CSV toàn bộ (`data/actors.csv`), JSON, GeoJSON; bảng chất lượng dữ liệu theo địa phương (tỷ lệ có logo, mô tả, website, LinkedIn, lĩnh vực, vị trí, đã xác minh); đường dẫn mô hình dữ liệu, schema, giấy phép, lịch sử thay đổi.
- `/gioi-thieu/`, `/gioi-thieu/phuong-phap/`, `/gioi-thieu/dong-gop/`.
- Sitemap thêm các tệp `sitemap-linh-vuc.xml`, `sitemap-co-hoi.xml`, `sitemap-chinh-sach.xml`.
