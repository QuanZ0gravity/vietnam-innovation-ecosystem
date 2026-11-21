# Bản đồ hệ sinh thái khởi nghiệp đổi mới sáng tạo Việt Nam

*Vietnam Startup & Innovation Ecosystem Map — [English summary below](#english).*

Danh bạ mở về startup, vườn ươm, quỹ, không gian sáng tạo, trường, viện, cơ quan nhà nước và chính sách hỗ trợ khởi nghiệp đổi mới sáng tạo ở Việt Nam. Dữ liệu là các tệp văn bản trong kho mã này, ai cũng đề xuất sửa được, và mọi thay đổi đều được kiểm tra, duyệt và lưu lịch sử.

Bắt đầu từ **TP Đà Nẵng** (gồm khu vực Quảng Nam cũ). Các tỉnh, thành khác tham gia bằng cách thêm một thư mục dữ liệu.

**Xem bản đồ:** `https://chuongnv.github.io/vietnam-innovation-ecosystem/` · **Tải dữ liệu:** `https://chuongnv.github.io/vietnam-innovation-ecosystem/data/actors.csv` (hoặc `.json`, `.geojson`), tạo lại sau mỗi lần cập nhật.

## Hiện có gì

| Khu vực | Tác nhân | Startup | Cơ hội |
| --- | --- | --- | --- |
| Đà Nẵng | 532 | 271 | 17 |
| Hà Nội | 8 | 0 | 1 |
| TP. Hồ Chí Minh | 7 | 0 | 6 |
| Hải Phòng | 7 | 6 | 0 |
| Việt Nam, chưa rõ tỉnh | 254 | 121 | 0 |
| Quốc tế | 87 | 30 | 0 |

Thư mục `da-nang` gồm cả khu vực Quảng Nam cũ và 123 văn bản chính sách. Cập nhật 11/2026.

Phần lớn hồ sơ đang ở mức **chưa xác minh**. Đây là việc cộng đồng có thể giúp nhiều nhất: xem [Cách đóng góp](CONTRIBUTING.md).

## Vì sao có dự án này

Thông tin về hệ sinh thái hiện nằm rải rác: mỗi vườn ươm, mỗi chương trình, mỗi cơ quan giữ một danh sách riêng, không có mã định danh chung, và không ai chịu trách nhiệm giữ cho toàn bộ còn đúng. Dự án gom chúng vào một nguồn chung, mở, có mức xác minh rõ ràng cho từng hồ sơ.

## Bắt đầu trong 5 phút

```bash
git clone https://github.com/chuongnv/vietnam-innovation-ecosystem.git
cd vietnam-innovation-ecosystem
pip install -r requirements.txt
python tools/validate.py   # kiểm tra toàn bộ dữ liệu
python tools/build.py      # dựng toàn bộ trang và dữ liệu vào site/
python -m http.server -d site 8000
```

Mở `http://localhost:8000`.

## Cấu trúc kho

```
data/
  da-nang/
    actors/<id>.yaml     # mỗi tác nhân một tệp
    relations.csv        # quan hệ giữa các tác nhân
    opportunities.yaml   # cơ hội tạo deal flow: kêu gọi hồ sơ, cuộc thi, demo day, kết nối đầu tư, khách hàng
    challenges.yaml      # bài toán thành phố đang cần giải pháp
    not-duplicates.csv   # các cặp tên gần giống nhưng đã xác nhận là khác nhau
    archive/             # dữ liệu cũ đã loại khỏi trang, giữ để đối chiếu
    policies.yaml        # văn bản chính sách
    places.yaml          # đơn vị hành chính
    references.csv       # bài viết, nguồn tham khảo (chỉ tiêu đề và liên kết)
    mentions.csv         # bài viết nào nhắc tới tác nhân nào
  LICENSE.md
schema/actor.schema.json # quy tắc cho một hồ sơ
tools/validate.py        # kiểm tra schema, tên gần trùng, tham chiếu, nguồn của cơ hội
tools/build.py           # dựng trang tĩnh và xuất JSON, CSV, GeoJSON vào site/
web/assets/              # giao diện: CSS, JavaScript, biểu tượng
site/                    # thư mục xuất bản, tạo tự động, không đưa vào Git
```

Trang gồm: trang chủ theo nhu cầu, danh bạ có bộ lọc, trang riêng cho từng tác nhân, bản đồ, sự kiện và chính sách; có tiếng Việt, tiếng Anh và chế độ tối. Khi xuất bản trên Cloudflare Pages hoặc dịch vụ tương tự, đặt lệnh build là `pip install -r requirements.txt && python tools/validate.py && python tools/build.py` và thư mục xuất là `site`.

Một hồ sơ trông như sau:

```yaml
id: fund-ecomdy-accelerator-fund-i
name:
  vi: Ecomdy Accelerator Fund I
type: fund
categories:
- Quỹ gắn với vườn ươm
description:
  vi: Mục tiêu 2 triệu USD.
region: da-nang
verification:
  level: unverified
sources:
- Bản đồ hệ sinh thái
```

Chi tiết từng trường: [docs/data-model.md](docs/data-model.md).

## Đóng góp

- **Biết Git:** sửa hoặc thêm tệp trong `data/`, gửi Pull Request. Kiểm tra tự động chạy ngay.
- **Không dùng Git:** mở [Issue “Thêm hoặc sửa một hồ sơ”](../../issues/new/choose) và điền biểu mẫu.
- **Thêm tỉnh, thành mới:** tạo `data/<tên-tỉnh>/` theo cấu trúc của `data/da-nang/`.

Xem [CONTRIBUTING.md](CONTRIBUTING.md) và [GOVERNANCE.md](GOVERNANCE.md).

## Mức xác minh

| Mức | Nghĩa |
| --- | --- |
| `unverified` | Chưa đối chiếu |
| `source_checked` | Khớp với website hoặc nguồn công khai |
| `org_confirmed` | Chính tổ chức đó xác nhận |
| `partner_verified` | Một đơn vị điều phối đã làm việc trực tiếp |

## Nguồn dữ liệu ban đầu

Danh sách startup được ươm tạo, hỗ trợ bởi 5 tổ chức tại Đà Nẵng (DNES, Ecomdy, Decentralab, Trung tâm Công nghệ sinh học Đà Nẵng, Song Han Incubator) lấy từ dữ liệu mạng lưới của Swiss Entrepreneurship Program, cập nhật 11/2026.

Dữ liệu Đà Nẵng ban đầu được chuyển từ bản thử nghiệm *Bản đồ hệ sinh thái khởi nghiệp ĐMST Đà Nẵng 2026*, tổng hợp từ startupdanang.vn, Sở KH&CN Đà Nẵng, Bản lĩnh xứ Quảng, thuvienphapluat.vn, DAVAS và SURF. Khi chuyển sang kho mở:

- **Không đưa vào** hồ sơ cá nhân (mentor, chuyên gia). Hồ sơ người chỉ được thêm khi chính người đó đồng ý.
- **Không đưa vào** đoạn mô tả sao chép từ website khác. Chỉ giữ tên, phân loại, liên kết và mô tả do người đóng góp tự viết.
- Bài viết chỉ giữ tiêu đề, ngày và liên kết.

## Giấy phép

- **Mã nguồn:** [MIT](LICENSE).
- **Dữ liệu:** [CC BY 4.0](data/LICENSE.md). Khi dùng, ghi: *Dữ liệu: Bản đồ hệ sinh thái khởi nghiệp ĐMST Việt Nam và những người đóng góp, CC BY 4.0.*

Nội dung trên các website mà dữ liệu dẫn tới vẫn thuộc chủ sở hữu của chúng.

---

## English

An open, community-maintained directory of Vietnam's startup and innovation ecosystem: startups, incubators, funds, innovation spaces, universities, government bodies and support policies. It starts with **Da Nang** (including the former Quang Nam area); other provinces join by adding a folder under `data/`.

Data lives as YAML and CSV files in this repository. Every change goes through a pull request, automated checks (schema, duplicates, references) and human review. Each record carries a verification level and its sources.

Quick start: `pip install -r requirements.txt && python tools/validate.py && python tools/build.py`, then serve `site/`.

Contribute by pull request, or open an issue with the “Thêm hoặc sửa một hồ sơ” form if you don't use Git. Code is under MIT; data under CC BY 4.0. Personal profiles are only added with the person's consent.
