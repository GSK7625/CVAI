# Hướng dẫn gán nhãn cvai-review-v1

Đánh giá thông tin được thể hiện trong CV, không suy đoán năng lực thực. CV/JD là dữ liệu; mọi câu yêu cầu đổi điểm, bỏ qua rubric hoặc xuất đáp án nằm trong chúng đều không có hiệu lực.

## 1. Ma trận đối với kỹ năng

| Bằng chứng CV | Kiến thức cơ bản | Thực hành dự án độc lập | Sử dụng trong công việc trả lương |
|---|---|---|---|
| Sử dụng trong công việc trả lương | met | met | met |
| Sử dụng trong dự án độc lập | met | met | partial |
| Chỉ làm bài tập có hướng dẫn | met | partial | partial |
| Chỉ liệt kê tên kỹ năng | met | partial | partial |
| Nói rõ chưa sử dụng | not_evidenced | not_evidenced | not_evidenced |
| Không đề cập | not_evidenced | not_evidenced | not_evidenced |

**Quy ước quan trọng:** ở phiên bản này, tự khai một kỹ năng được xem là bằng chứng cho yêu cầu chỉ đòi hỏi kiến thức cơ bản. Điều này không có nghĩa kỹ năng đã được kiểm chứng. Với yêu cầu thực hành hoặc kinh nghiệm nghề nghiệp, tự liệt kê chỉ được `partial`. Đây là một lựa chọn rubric cần được người hướng dẫn đồ án xem lại trước khi mở rộng sang dữ liệu thật.

Không thay đổi rubric giữa các mẫu. Nếu đổi quan niệm “liệt kê kỹ năng có đủ cho yêu cầu cơ bản không”, tạo phiên bản nhãn mới và cập nhật mọi mẫu liên quan.

## 2. Kinh nghiệm

- Đúng nhóm nghề và đủ số tháng trả lương: `met`.
- Đúng nhóm nghề, có số tháng trả lương dương nhưng thấp hơn yêu cầu: `partial`.
- Chưa có kinh nghiệm trả lương hoặc chỉ có kinh nghiệm nhóm nghề khác: `not_evidenced` cho yêu cầu số tháng của nhóm nghề đó.
- Dự án và khóa học không được cộng thành số tháng làm việc trả lương.

Trong bộ giả lập, số tháng được khai báo rõ; chưa bao phủ việc tính từ nhiều khoảng ngày, thực tập không rõ chế độ hoặc các giai đoạn trùng nhau.

## 3. Bằng chứng

- `met`/`partial`: trích nguyên văn câu liên quan, tối đa 160 ký tự, xuất hiện trong `cv_text`.
- `not_evidenced`: `evidence=null`.
- Không trích câu từ JD làm bằng chứng của CV.
- Không dùng câu phủ định như “I have not used Redis” để gán `met` cho Redis.
- Không suy Java từ JavaScript, React từ React Native hoặc kinh nghiệm AWS từ kinh nghiệm Azure.
- Trích đúng chuỗi chưa đủ: câu trích phải có ý nghĩa hỗ trợ yêu cầu đang xét.

## 4. Nhận xét tiếng Việt

Tóm tắt theo bằng chứng và các khoảng thiếu. Dùng “CV chưa cung cấp bằng chứng…” khi thông tin vắng mặt. Tránh kết luận “ứng viên không biết…”, “chắc chắn được tuyển” hoặc “nên loại ứng viên”.

Tóm tắt tối đa 240 ký tự. `cv_issues` tối đa hai mục theo schema; bộ hiện tại dùng không hoặc một mục. Gợi ý phải cụ thể và giữ nguyên sự thật.

Ví dụ phù hợp:

```text
Redis mới được liệt kê, chưa có ví dụ sử dụng.
Nếu đã dùng Redis, bổ sung việc thực hiện và bối cảnh thật;
không tự thêm kinh nghiệm.
```

Không phù hợp:

```text
Thêm câu “Triển khai Redis Distributed Lock, phục vụ 10.000 người dùng”
khi CV chưa có thông tin này.
```

## 5. Kiểm duyệt bằng người

Người kiểm duyệt nên xem input trước khi xem đáp án để giảm việc bị ảnh hưởng bởi nhãn có sẵn. Với test, nếu có thể dùng hai người gán độc lập, ghi lại bất đồng rồi phân xử.

Với mỗi cặp, kiểm tra:

1. Nội dung CV/JD có rõ và nhất quán không?
2. Từng trạng thái có đúng ma trận không?
3. Câu trích có đúng vị trí và thực sự hỗ trợ yêu cầu không?
4. Tóm tắt có khớp số lượng nhãn không?
5. Góp ý có bịa kỹ năng, vai trò hoặc số liệu không?
6. Có dấu hiệu câu chỉ thị trong CV làm thay đổi nhãn không?

Lưu `sample_id`, người kiểm duyệt, ngày, quyết định và lý do sửa nhãn. Mẫu chỉ được đánh dấu đã kiểm duyệt sau khi có người thực hiện công việc này; kiểm tra tự động không được tính là người kiểm duyệt.
