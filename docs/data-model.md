# Mô hình dữ liệu

Quy tắc chính xác nằm trong [`schema/actor.schema.json`](../schema/actor.schema.json). Tài liệu này giải thích ý nghĩa.

## Tác nhân (`data/<tỉnh>/actors/<id>.yaml`)

| Trường | Bắt buộc | Ý nghĩa |
| --- | --- | --- |
| `id` | có | Mã cố định, không đổi khi tổ chức đổi tên. Trùng tên tệp. |
| `name.vi`, `name.en` | `vi` | Tên tiếng Việt, tên tiếng Anh nếu có |
| `alt_names` | | Tên khác, tên cũ, cách viết khác; dùng để phát hiện trùng |
| `type` | có | `startup`, `creator`, `company`, `fund`, `incubator`, `accelerator`, `space`, `university`, `government`, `support_org`, `international`, `community`, `media` |
| `categories` | | Lĩnh vực hoặc phân loại chi tiết |
| `stage` | | Giai đoạn startup: `idea` … `mature` |
| `founded` | | Năm thành lập |
| `status` | | `active`, `inactive`, `unknown` |
| `contact_email`, `contact_phone` | | Email và số điện thoại chung của tổ chức. Không dùng email hay số di động của cá nhân |
| `website`, `linkedin` | | Trang chính thức |
| `address`, `coordinates` | | Địa chỉ; tọa độ `[kinh độ, vĩ độ]` để hiện trên bản đồ |
| `coordinates_source` | | Nguồn và độ chính xác của tọa độ, ví dụ `OpenStreetMap 11/2026, số nhà` |
| `description.vi`, `description.en` | | Mô tả tự viết, tối đa 400 ký tự |
| `region` | có | Tỉnh, thành hoặc khu vực, ví dụ `da-nang`, `former-quang-nam` |
| `place` | | Mã đơn vị hành chính trong `places.yaml` |
| `verification.level` | có | `unverified`, `source_checked`, `org_confirmed`, `partner_verified` |
| `verification.date`, `verification.by` | | Ngày và người, đơn vị xác minh |
| `maintainer` | | `id` của tổ chức chịu trách nhiệm hồ sơ |
| `sources` | có | Nguồn thông tin |
| `source_url` | | Liên kết tới nguồn |
| `legacy_id` | | Mã trong bản thử nghiệm, để đối chiếu |

## Quan hệ (`relations.csv`)

`from, type, to, since, source`. Loại quan hệ: `incubated_by`, `accelerated_by`, `invested_by`, `mentored_by`, `co_organized`, `referred`, `funded_by`, `member_of`, `partner` (đối tác công nghệ, thương mại), `incubated_by` (startup được tổ chức đó ươm tạo, hỗ trợ; `since` là ngày vào chương trình), `part_of` (đơn vị trực thuộc, ví dụ trung tâm khởi nghiệp của một trường), `related` (chưa phân loại).

## Tham chiếu (`references.csv`, `mentions.csv`)

Bài viết chỉ lưu tiêu đề, ngày, liên kết và nguồn. `mentions.csv` nối bài viết với tác nhân được nhắc tới.

## Thêm tọa độ để hiện trên bản đồ

1. Mở [openstreetmap.org](https://www.openstreetmap.org), tìm đúng tòa nhà, bấm chuột phải và chọn “Hiển thị địa chỉ”. Thanh bên trái hiện vĩ độ và kinh độ.
2. Thêm vào hồ sơ, **kinh độ trước, vĩ độ sau**:

```yaml
coordinates:
- 108.219734
- 16.070912
coordinates_source: OpenStreetMap 11/2026, số nhà
```

Tác nhân chưa có tọa độ nhưng có trường `place` sẽ hiện ở vị trí của phường, xã đó, nếu phường, xã đã có tọa độ trong `places.yaml`.

## Cơ hội (`opportunities.yaml`)

Quy tắc chính xác: [`schema/opportunity.schema.json`](../schema/opportunity.schema.json).

| Trường | Ý nghĩa |
| --- | --- |
| `type` | `call_for_applications`, `competition`, `demo_day`, `investor_matching`, `accelerator_program`, `buyer_matching`, `pilot_program` |
| `organizer`, `organizer_ids` | Tên đơn vị tổ chức; `id` của họ trong danh bạ nếu có |
| `opens`, `deadline`, `event_date` | Ngày mở nhận hồ sơ, hạn nộp, ngày diễn ra |
| `eligibility`, `benefits`, `funding` | Đối tượng, quyền lợi, số vốn hoặc giải thưởng công bố |
| `apply_url`, `primary_source` | Trang đăng ký và trang của đơn vị tổ chức; không dùng trang tổng hợp |
| `secondary_sources` | Bài viết liên quan trên trang tổng hợp, báo chí |
| `participants` | `id` các tác nhân được chọn, tham gia hoặc đoạt giải |
| `outcome` | Kết quả sau khi kết thúc: `applicants`, `finalists`, `selected`, `investors`, `deals`, `note`, `source` |

Trạng thái (đang nhận hồ sơ, sắp diễn ra, đã kết thúc) được tính tự động từ ngày khi dựng trang.

## Bài toán (`challenges.yaml`)

Hướng có nhu cầu thật mà thành phố hoặc doanh nghiệp đặt ra, để startup cân nhắc. Mỗi mục gồm `id`, `title` (vi, en), `summary` (vi, en), `source`. Đây không phải kêu gọi hồ sơ; khi có chương trình cụ thể, thêm vào `opportunities.yaml`.
