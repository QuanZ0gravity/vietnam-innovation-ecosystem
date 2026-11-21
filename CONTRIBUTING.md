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

## Quy tắc nội dung

- Chỉ thông tin công khai, hoặc đã được tổ chức đồng ý công bố.
- **Tự viết mô tả**, tối đa 400 ký tự. Không sao chép từ website, báo hay tài liệu khác.
- Không thêm số điện thoại, email cá nhân hay thông tin cá nhân.
- Không thêm hồ sơ cá nhân (mentor, chuyên gia) nếu người đó chưa đồng ý bằng văn bản hoặc email.
- Không quảng cáo, không đánh giá, không xếp hạng tổ chức.
- Nhiều hồ sơ cùng sửa: mỗi Pull Request nên gom các thay đổi cùng một nguồn hoặc cùng một chủ đề.

## Khi gửi Pull Request

Bằng cách gửi, bạn xác nhận có quyền đóng góp nội dung này và đồng ý cấp phép theo MIT (mã) và CC BY 4.0 (dữ liệu). Ký mỗi commit bằng `git commit -s` (Developer Certificate of Origin).
