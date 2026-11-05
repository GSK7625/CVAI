# CVAI augmented round 1 — 03/11/2026

Bổ sung development của human_review_round1 vào v1. Toàn bộ CV vẫn là
tổng hợp; không phải một bộ CV thật mới được kiểm chứng nguồn.

| Split | Cặp CV–JD | Yêu cầu | Phần bổ sung |
|---|---:|---:|---:|
| Train | 844 | 3.362 | 144 CV mới, 562 yêu cầu |
| Validation | 148 | 587 | 48 CV mới, 187 yêu cầu |
| Test v1 đã quan sát | 150 | 600 | Giữ nguyên từng byte |

Nguồn mới gồm 47 nhãn người chấm độc lập và đồng ý quy tắc (31 train,
16 validation), 702 nhãn quy tắc chưa được người kiểm tra. 19 yêu cầu
mơ hồ/bất đồng chưa phân xử được loại cả requirement và target khỏi bản
thí nghiệm; không âm thầm chuyển needs_review thành một lớp train khác.
Một CV có thể còn 3 yêu cầu thay vì 4, vì vậy score MAE của phần mới chỉ
áp dụng trên các yêu cầu được giữ lại. Không so MAE mới như cùng một test
với v1. Không gọi toàn bộ bộ mới là đã được người kiểm duyệt.

48 CV holdout vẫn nằm riêng trong ZIP nguồn; không dùng để train, chọn
cấu hình hoặc tính kết quả lần này. Những nhãn trong tập cũ không bị sửa.
Các kiểm tra group/content leakage của pipeline chạy lại sau khi gộp.

## Tệp

- train/validation/test.jsonl: schema MLP v1, cùng pipeline đặc trưng cũ.
- new_train/new_validation.jsonl: phần mới để báo cáo riêng theo miền dữ liệu.
- label_provenance.jsonl: nguồn và các span gốc của từng nhãn mới.
- excluded_requirements.jsonl: các khóa bị loại và lý do.
- manifest.json: hash dữ liệu, nguồn, số lượng và hash bản nhãn người đã khóa.

MLP v1 nhận evidence một chuỗi. Các evidence nhiều đoạn được biểu diễn
bằng đoạn bao từ vị trí đầu đến vị trí cuối trong CV gốc; danh sách span
ban đầu được giữ trong provenance. Evidence/nhãn/provenance không đi vào
đặc trưng E5 hay đầu vào classifier. Việc tạo đoạn bao không xác minh
ngữ nghĩa của mọi chữ nằm giữa các span.

Script tái lập: training/annotation/prepare_augmented.py. Chọn output mới
khi chạy lại để bảo vệ dữ liệu đã lưu. Test v1 là benchmark lịch sử đã
được xem trong phát triển, không được trình bày như một test giữ kín mới.
