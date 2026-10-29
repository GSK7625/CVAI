# CV + JD thô → điểm theo rubric

## Khi đăng tin

Nhà tuyển dụng nhập JD bình thường. Backend gọi `/jobs/prepare`, lưu profile
cùng Job ID. Parser tự tách các yêu cầu trong phạm vi IT đã huấn luyện:

| Dấu hiệu ưu tiên | Weight |
|---|---:|
| must / required / bắt buộc | 3 |
| không nêu ưu tiên rõ | 2 |
| preferred / ưu tiên / lợi thế | 1 |

Weight là quy ước `jd-priority-v1`, không phải mức quan trọng khách quan do
model tự học. `priority` độc lập với mức cần đạt: basic/practical/professional.
Các suy diễn mặc định được ghi trong warnings. Mỗi tiêu chí có câu JD gốc,
offsets, profile_id và fingerprint parser. Sửa JD tạo phiên bản mới.

Parser v1 xử lý headings/list EN/VI đơn giản và các kỹ năng trong SKILLS.
Không đổi OR thành AND, không đổi số năm kỹ năng thành số năm toàn vai trò,
không bỏ bằng cấp/chứng chỉ/điều kiện chưa hiểu rồi vẫn chấm một phần JD.
Các trường hợp đó trả `needs_review` cùng `unresolved` và không có điểm tổng.
Đây là bước kiểm tra ngoại lệ, không bắt nhà tuyển dụng tự tính weight.

## Khi ứng tuyển

Backend trích text CV và gửi `/review`:

```json
{"sample_id":"application-123","cv_text":"...","job_profile":{"...":"profile nguyên vẹn đã lưu"}}
```

Cũng có thể gửi `{cv_text, jd_text, job_title}` để chạy một bước. Không trộn
jd_text/job_profile/requirements trong cùng request. Input requirements cũ
được giữ để tái lập benchmark, không nhận weight tùy ý từ ứng viên.

E5 tìm top-3 ngữ cảnh, classifier dự đoán trạng thái, code tính:

```text
score = 100 × Σ(weight × status_value) / Σ(weight)
met = 1; partial = 0,5; not_evidenced = 0
```

Weight cao không phải điều kiện loại tự động. Trích đoạn nguyên văn không
đồng nghĩa bằng chứng đã được xác minh. Nhận xét là câu mẫu dựa trên dự đoán,
không tự phát hiện mọi lỗi CV hoặc chứng minh năng lực thực của ứng viên.

401: sai khóa; 422: input/criteria chưa hợp lệ; 429: đang xử lý CV khác.
API không lưu database; dữ liệu và lịch sử thuộc trách nhiệm backend.
