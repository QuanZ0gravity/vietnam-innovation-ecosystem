# Mô hình dữ liệu

Quy tắc chính xác nằm trong [`schema/actor.schema.json`](../schema/actor.schema.json). Tài liệu này giải thích ý nghĩa.

## Tác nhân (`data/<tỉnh>/actors/<id>.yaml`)

| Trường | Bắt buộc | Ý nghĩa |
| --- | --- | --- |
| `id` | có | Mã cố định, không đổi khi tổ chức đổi tên. Trùng tên tệp. |
| `name.vi`, `name.en` | `vi` | Tên tiếng Việt, tên tiếng Anh nếu có |
| `type` | có | `startup`, `creator`, `company`, `fund`, `incubator`, `accelerator`, `space`, `university`, `government`, `support_org`, `international`, `community`, `media` |
| `categories` | | Lĩnh vực hoặc phân loại chi tiết |
| `stage` | | Giai đoạn startup: `idea` … `mature` |
| `founded` | | Năm thành lập |
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

`from, type, to, since, source`. Loại quan hệ: `incubated_by`, `accelerated_by`, `invested_by`, `mentored_by`, `co_organized`, `referred`, `funded_by`, `member_of`, `related` (chưa phân loại).

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
