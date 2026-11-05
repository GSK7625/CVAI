# Vòng gán nhãn độc lập CVAI

## Bắt đầu ngay

1. Giải nén `START_HERE.zip`, mở **reviewer.html** bằng Chrome/Edge, không cần
   Colab hoặc cài Python. Nội dung CV/JD tiếng Anh; giao diện/rubric tiếng Việt.
2. Đọc RUBRIC.md. Nhập mã như `reviewer-A`, chọn lô 1 (12 CV / 48 yêu cầu).
3. Với mỗi yêu cầu: chọn nhãn, độ tự tin, evidence nguyên văn; ghi lý do khi
   chưa rõ hoặc không đồng ý rubric. Không sửa weight. Chọn “Cần xem lại”
   nếu input mơ hồ, không phải bỏ qua bằng cách đoán.
4. Bấm **Xuất nhãn để lưu** sau mỗi lô. Gửi file JSON xuất ra để đối chiếu.
   “Nhập nhãn để làm tiếp” khôi phục file cũ. File xuất chứa tất cả tiến độ,
   nên giữ các bản theo ngày/lô thay vì ghi đè bản đã khóa.
5. **Chưa mở reference_sealed.zip hoặc holdout_sealed.zip.** Không đọc
   generator trước khi gán độc lập nếu muốn giảm việc bị ảnh hưởng quy tắc.

Chỉ cần làm lô đầu trước để phát hiện vấn đề rubric. Chưa có nhãn nào được
đánh dấu do người chấm. Việc kiểm tra bằng code không được tính là kiểm duyệt.

## Trong gói có gì?

- **240 CV tổng hợp mới**, mỗi CV ghép một JD → 240 cặp, 960 yêu cầu.
- 6 nhóm nghề; 60 JD riêng; 6 kiểu trình bày văn bản; ba mức độ dài.
- 144 CV train, 48 validation, **48 holdout** được chia trước. CV/JD group
  không dùng chéo các split. Không trùng CV text hoặc CV/JD group với v1.
- `reviewer.html` / `inputs_blind.jsonl`: 192 CV train + validation xáo trộn,
  không có label, case nguồn, facts hoặc split trong dữ liệu reviewer.
- `reference_sealed.zip`: nhãn đề xuất sinh bằng **quy tắc**, không phải dự
  đoán của E5/Qwen hoặc nhãn chuyên gia; kèm source register và split.
- `holdout_sealed.zip`: input + trang gán nhãn riêng của 48 holdout. ZIP chỉ
  giúp tách quy trình, **không mã hóa và không chặn quyền truy cập**.
- `manifest.json`: seed, hash của gói và generator; lưu lại trước khi chấm.

## Nguồn và giới hạn

Toàn bộ vòng này là **dữ liệu tổng hợp do mã tạo cho dự án**; không có tên,
điện thoại, email hay công ty thật được sinh. Không lấy CV từ web/CSV gốc,
không tuyên bố đã có 240 CV thật có phép hoặc đã kiểm chứng năng lực.

240 CV là 240 nội dung/nhóm tổng hợp khác nhau, không phải 240 cá nhân thật.
Chúng vẫn chia sẻ template/ontology/generator; việc tách group chỉ ngăn rò
rỉ group và trùng nguyên văn, không tạo ra một real-world test độc lập.
Nhận xét và văn phong của CV vẫn còn tính công thức. Không có PDF/OCR trong vòng này.

CSV cũ có nguồn/quyền chưa xác minh, vì vậy không được lén bổ sung vào vòng
này. Khi có CV thật được phép dùng, tạo vòng riêng và dùng
`training/annotation/source_intake.template.json` để ghi nguồn, phạm vi cho
phép, bằng chứng đồng ý và kiểm tra ẩn danh. Không ghi thông tin định danh
hoặc giấy tờ đồng ý vào repo công khai. Báo metrics real/synthetic riêng.

## Khóa nhãn, đối chiếu, phân xử

Các lệnh chạy từ thư mục gốc FutureCV, cần Python 3.10+ và thư viện chuẩn.
Đổi `NHAN_CUA_BAN.json` thành đường dẫn file bạn xuất:

```powershell
python training/annotation/compare_labels.py freeze NHAN_CUA_BAN.json
python training/annotation/compare_labels.py compare NHAN_CUA_BAN.json --inputs training/datasets/human_review_round1/inputs_blind.jsonl --reference training/datasets/human_review_round1/reference_sealed.zip --output training/datasets/human_review_round1/doi_chieu_lo_1
```

`freeze` tạo biên nhận SHA-256. Không sửa bản đã khóa; nếu cần, xuất bản mới.
Đây là kiểm tra toàn vẹn cục bộ, không chứng minh reviewer chưa xem đáp án.

Kết quả: `comparison.json` báo coverage, đồng thuận, Cohen's kappa, confusion,
macro-F1 lấy người làm tham chiếu; khoảng bootstrap theo CV (mẫu nhỏ có thể
rất bất định). `evidence_comparison.jsonl` chỉ đo trùng chuỗi/từ ở các nhãn
dương đồng thuận. `adjudication.jsonl` để điền final label/evidence, người
phân xử và lý do. Không tự động chọn nhãn máy khi có bất đồng.

Đồng thuận người–quy tắc **không phải độ chính xác** và không chứng minh
tính xác thực/quyền sử dụng nguồn. Một người so quy tắc không phải độ tin
cậy giữa hai người. Để kiểm tra thêm, nhờ người B gán độc lập cùng một gói
trong hồ sơ trình duyệt riêng, không nhập nhãn A; sau đó mới thảo luận.

Giữ bản gán độc lập, bản sau phân xử và phiên bản rubric riêng. Sau phân xử,
kiểm tra lại một mẫu các trường hợp đồng thuận để phát hiện lỗi cùng mắc.
Chỉ nhãn đã được kiểm duyệt/phân xử mới được chuyển thành dữ liệu train.
Vòng này không tự sửa các file train/validation/test cũ, không train model.

## Holdout

Chốt rubric/quy trình trên train + validation trước. Nhờ người giữ holdout
gán độc lập bằng trang trong ZIP, không gửi nội dung/nhãn holdout cho người
chọn cấu hình. Khóa model/prompt/preprocessing trước lần đánh giá cuối.
Nếu bạn tự làm cả hai vai thì phải ghi giới hạn này trong báo cáo.

Sau khi đã mở phân tích lỗi holdout để sửa model, tập đó trở thành test đã
quan sát; cần một holdout mới cho kết luận xác nhận tiếp theo. Vòng synthetic
này không thay thế kiểm thử ngoài trên CV thật.

## Tái tạo

```powershell
python training/annotation/build_round.py --output training/datasets/human_review_round1_copy
python -m unittest discover -s training/annotation/tests -v
```

Generator từ chối ghi đè thư mục đã có để bảo vệ nhãn bạn đã làm.
