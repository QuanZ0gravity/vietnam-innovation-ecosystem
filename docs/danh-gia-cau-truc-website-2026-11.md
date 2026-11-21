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
