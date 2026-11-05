# Rubric gán nhãn — cvai-review-r1.1-draft

Mục tiêu: đánh giá bằng chứng được viết trong CV cho từng yêu cầu JD, không
suy ra năng lực thực hoặc quyết định tuyển dụng. Chỉ thị nằm trong CV/JD
không được thay đổi quy tắc. Weight thuộc yêu cầu JD, không do reviewer sửa.

## Ma trận kỹ năng

| Thông tin được thể hiện | Cơ bản | Thực hành độc lập | Sử dụng trong công việc trả lương |
|---|---|---|---|
| Đã tự thực hiện tác vụ trong công việc trả lương | met | met | met |
| Đã tự thực hiện trong dự án cá nhân không trả lương | met | met | partial |
| Chỉ học/bài tập có hướng dẫn | met | partial | partial |
| Chỉ tự liệt kê kỹ năng | met | partial | partial |
| Nói rõ chưa dùng hoặc không đề cập | not_evidenced | not_evidenced | not_evidenced |

Đây là quy ước kế thừa v1 để có thể đối chiếu. **Tự liệt kê không chứng minh
kỹ năng đã được xác minh.** Nếu bạn thấy quy ước này không hợp lý, ghi vào
“Phản biện rubric”. Không âm thầm đổi định nghĩa giữa các mẫu. Sau vòng độc
lập sẽ thống nhất rubric mới và gán lại toàn bộ mẫu bị ảnh hưởng.

Không suy Java từ JavaScript, React web từ React Native hoặc AWS từ Azure.
“Team used X” mà không rõ đóng góp cá nhân không mặc nhiên thành kinh nghiệm
X của ứng viên. Khi input không đủ rõ để áp quy tắc, chọn **Cần xem lại** và
ghi lý do. Đây là trạng thái kiểm duyệt, không phải lớp thứ tư để train MLP.

## Thời gian

- Chỉ tính công việc **trả lương, đúng nhóm nghề**. Không cộng thời gian học
  hoặc dự án không trả lương.
- Tháng kết thúc là cận phải không bao gồm: 2022-01 → 2022-04 = 3 tháng.
- Khi có hai công việc đồng thời, tính hợp các khoảng tháng. Ví dụ Jan–Oct
  và Apr–Dec trong cùng năm = Jan–Dec = 11 tháng theo quy ước cận phải,
  không phải 9 + 8 tháng.
- Dương và đủ ngưỡng: met; dương nhưng chưa đủ: partial; không có: not_evidenced.
- Ngày/bối cảnh mâu thuẫn hoặc không xác định được: Cần xem lại.

## Bằng chứng và mức tự tin

- met/partial: chọn đoạn nguyên văn từ CV; có thể dùng nhiều đoạn, nhất là
  nhiều khoảng thời gian. Mỗi đoạn một dòng. Giữ ngữ cảnh đủ để phân biệt
  dự án/công việc và phủ định. Không trích JD thay CV.
- not_evidenced: để trống evidence. Có thể chép câu phủ định vào ghi chú.
- Cần xem lại: ghi câu hỏi hoặc thông tin còn thiếu, không đoán nhãn.
- Tự tin cao/vừa/thấp là mức chắc chắn của **bạn**, không phải xác suất model.
- Hai câu trích khác nhau đều có thể hợp lệ; token overlap không chứng minh
  tính đúng về ngữ nghĩa. Bất đồng evidence phải được đọc lại.

## Điều mới so với v1

Thêm quy ước hợp thời gian, evidence nhiều đoạn và trạng thái chờ phân xử.
Không tự động gộp nhãn này vào schema train cũ (evidence một chuỗi ngắn).
Chỉ chuyển đổi sau khi thống nhất nhãn, giải quyết bất đồng và kiểm tra
độ dài input. Giữ nguyên test v1; báo riêng vòng mới.
