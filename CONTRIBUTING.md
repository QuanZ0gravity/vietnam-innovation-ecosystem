# Cách đóng góp

Cảm ơn bạn đã giúp bản đồ đúng hơn. Có ba cách, chọn cách nào dễ với bạn.

## 1. Không dùng Git: mở Issue

Vào tab **Issues**, chọn **Thêm hoặc sửa một hồ sơ**, điền biểu mẫu. Người duyệt sẽ chuyển thành thay đổi dữ liệu và trả lời trong Issue.

## 2. Sửa trực tiếp trên GitHub

1. Mở tệp cần sửa trong `data/<tỉnh>/actors/`, bấm biểu tượng bút chì.
2. Sửa, rồi chọn **Propose changes**. GitHub tự tạo Pull Request.
3. Chờ kiểm tra tự động chạy xong. Nếu có lỗi, thông báo sẽ chỉ rõ tệp và trường cần sửa.

## 3. Dùng Git trên máy

```bash
pip install -r requirements.txt
python tools/validate.py
```

Chạy kiểm tra trước khi gửi Pull Request.

## Thêm một hồ sơ mới

1. Tạo tệp `data/<tỉnh>/actors/<id>.yaml`. Tên tệp trùng với `id`.
2. `id` = tiền tố loại + tên không dấu, nối bằng gạch ngang: `startup-ten-startup`, `fund-ten-quy`, `space-ten-khong-gian`.
3. Bắt buộc: `id`, `name.vi`, `type`, `region`, `verification.level`, `sources`.
4. Hồ sơ mới để `verification.level: unverified`, trừ khi bạn là người của chính tổ chức đó (`org_confirmed`, kèm `verification.date`).

## Trước khi thêm, tìm xem đã có chưa

Tìm theo tên đầy đủ, tên viết tắt và tên tiếng Anh trong danh bạ. Nếu tổ chức đã có, sửa hồ sơ đó và ghi tên khác vào `alt_names`. Kiểm tra tự động sẽ chặn hồ sơ có tên gần giống một hồ sơ đã có. Nếu hai tổ chức thật sự khác nhau, thêm cặp `id` vào `data/<tỉnh>/not-duplicates.csv` kèm một dòng giải thích.

Trung tâm, viện, không gian của một trường hay tập đoàn là một hồ sơ riêng, nối với đơn vị mẹ bằng quan hệ `part_of` trong `relations.csv`.

## Thêm một cơ hội

`data/<tỉnh>/opportunities.yaml` chỉ nhận hoạt động có thể dẫn tới vốn, khách hàng hoặc hợp đồng: kêu gọi hồ sơ, cuộc thi, demo day, kết nối nhà đầu tư, kết nối khách hàng, chương trình ươm tạo, tăng tốc, thử nghiệm. Không nhận hội thảo, diễn đàn chung, tin ký kết hay đoàn công tác.

- `apply_url` và `primary_source` phải là trang của chính đơn vị tổ chức. Bài viết trên trang tổng hợp chỉ ghi ở `secondary_sources`.
- Ghi rõ hạn nộp, đối tượng và quyền lợi nếu có nguồn. Không có nguồn thì để trống; trang sẽ hiện mục “Còn thiếu” để người khác bổ sung.
- Sau khi kết thúc, cập nhật `outcome`: số hồ sơ, số dự án vào chung kết, số được chọn, số nhà đầu tư tham dự, số thỏa thuận đầu tư hoặc hợp tác, kèm nguồn.

## Quy tắc nội dung

- Chỉ thông tin công khai, hoặc đã được tổ chức đồng ý công bố.
- **Tự viết mô tả**, tối đa 400 ký tự. Không sao chép từ website, báo hay tài liệu khác.
- Thông tin liên hệ chỉ dùng kênh chung của tổ chức (info@, contact@, tổng đài). Không thêm email hay số di động của cá nhân, kể cả nhân viên của tổ chức, trừ khi người đó đồng ý.
- Không thêm hồ sơ cá nhân (mentor, chuyên gia) nếu người đó chưa đồng ý bằng văn bản hoặc email.
- Không quảng cáo, không đánh giá, không xếp hạng tổ chức.
- Nhiều hồ sơ cùng sửa: mỗi Pull Request nên gom các thay đổi cùng một nguồn hoặc cùng một chủ đề.

## Khi gửi Pull Request

Bằng cách gửi, bạn xác nhận có quyền đóng góp nội dung này và đồng ý cấp phép theo MIT (mã) và CC BY 4.0 (dữ liệu). Ký mỗi commit bằng `git commit -s` (Developer Certificate of Origin).
