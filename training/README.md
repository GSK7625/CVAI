# Thí nghiệm CVAI

## R2 · E5 truy xuất top 3 và MLP đọc ngữ cảnh

Mở [notebook R2](lightweight_cv/train_retrieval_r2.ipynb) trong Colab GPU và tải lên `cvai_retrieval_r2.zip`. Dựng lại gói bằng `python training/lightweight_cv/build_retrieval_bundle.py --context`. Nếu đã train R1 trên Drive, điền `base_path` tới thư mục model chứa `manifest.json`. Để trống thì notebook train từ đầu. [Script train MLP R2](lightweight_cv/improve_retrieval_mlp.py)

R2 dùng encoder R1 và cùng công thức điểm. MLP nhận embedding, độ tương đồng, loại yêu cầu và các dấu hiệu lấy từ top 3, kể cả mục CV chứa từng đoạn. Model chỉ dùng tiêu đề mục làm gợi ý ngữ cảnh. Các nhãn tham chiếu, đoạn gold và weight không nằm trong vector dự đoán.

| Tập tổng hợp tiếng Anh | Số yêu cầu | Macro-F1 R1 → R2 | MAE điểm CV trên 100, R1 → R2 |
|---|---:|---:|---:|
| Validation R1 | 587 | 0,901 → 1,000 | 4,39 → 0,00 |
| Jake pilot đã dùng phân tích lỗi | 30 | 0,694 → 0,856 | 23,08 → 8,97 |
| [Jake bổ sung](datasets/jake_pdf_followup/cases.json), cùng bố cục, hồ sơ và câu JD mới | 36 | 0,815 → 0,899 | 8,33 → 7,74 |

Lần chạy CPU chọn model theo validation trước khi đo hai bộ PDF. Top 3 của hai model giống nhau trên cả 66 yêu cầu. Bản R2 sai 4 nhãn trên pilot và 3 nhãn trên tập PDF bổ sung. Phép đo PDF dùng các yêu cầu JD đã tách sẵn. Test v1 đã dùng trong nghiên cứu trước đây đạt 600/600 nhãn trên dữ liệu cùng bộ sinh. Độ chính xác trên CV thực tế còn cần được đo riêng.

## Thí nghiệm CVAI v1

- [Code, inference và API](lightweight_cv/README.md)
- [Notebook Colab](lightweight_cv/train_e5_classifier.ipynb)
- [Dataset card](datasets/cvai_v1/DATASET_CARD.md)
- [Rubric gán nhãn](datasets/cvai_v1/LABELING_GUIDE.md)
- [Kết quả Colab](../evaluation/e5-v1/README.md)

## Dữ liệu

700 train / 100 validation / 150 test, CV/JD tiếng Anh và nhận xét theo mẫu
tiếng Việt. Bộ dữ liệu **tổng hợp có kiểm soát**, không phải nhãn chuyên gia
trên CV thật. Không dùng CSV resume gốc làm nhãn chuẩn.

Giữ nguyên split theo CV và JD group. Trọng số JD có sẵn trong dữ liệu phục
vụ thí nghiệm; khi chạy JD thô, parser gán trọng số theo chính sách riêng và
ghi dấu vết nguồn. Xem hướng dẫn module để biết phạm vi parser.

Tái tạo dữ liệu vào thư mục mới, không ghi đè mẫu đã kiểm duyệt:

```bash
python training/build_dataset.py --output /path/to/new_dataset
```

## Kiểm tra

```bash
python -m unittest discover -s training/tests -v
```

Model đã phát hành tương ứng manifest trong `lightweight_cv/artifact` và
metric trong `evaluation/e5-v1`; không thay bằng kết quả từ run local khác.

## Huấn luyện E5 truy xuất và MLP trên R1

Mở [notebook R1](lightweight_cv/train_retrieval_r1.ipynb) trong Colab, chọn GPU rồi chạy các ô theo thứ tự. Khi được hỏi, tải lên `cvai_retrieval_r1.zip`. Để dựng lại ZIP từ checkout, chạy `python training/lightweight_cv/build_retrieval_bundle.py` ở thư mục gốc. Notebook lưu hai model và báo cáo vào một thư mục riêng trong Google Drive.

Script [train_retrieval_mlp.py](lightweight_cv/train_retrieval_mlp.py) train hai MLP độc lập với cùng cấu hình. Lần thứ hai cập nhật hai block cuối của E5 trong một epoch, dùng 1.531 bộ ba duy nhất lấy từ train R1. Query là yêu cầu JD. Đoạn dương lấy từ bằng chứng của nhãn met hoặc partial. Đoạn âm lấy từ cùng CV, đã được trích cho yêu cầu khác và có kỹ năng khác. Với dữ liệu bổ sung R1, script ưu tiên span trong provenance. MLP nhận embedding và độ tương đồng của các đoạn E5 thực sự tìm được. Trọng số JD chỉ tham gia công thức tính điểm.

Lần chạy CPU trên 844 cặp train và 148 cặp validation cho macro-F1 0,7351 với E5 đóng băng và 0,9012 với E5 fine-tune. Chọn model theo macro-F1 validation trước khi kiểm tra PDF. Test v1 là benchmark lịch sử đã quan sát, macro-F1 của model được chọn là 0,8613.

[Bộ PDF Jake thử nghiệm](datasets/jake_pdf_pilot/cases.json) có 6 CV tiếng Anh tổng hợp và 30 yêu cầu, với SHA-256 của PDF, text trích xuất, nhãn, đoạn trích, vị trí ký tự và tên mục. Các PDF chỉ dùng đánh giá với yêu cầu JD đã tách. Model được chọn tìm đủ 24/24 bằng chứng trong top 3 và gán đúng 21/30 nhãn. Kết quả này chỉ mô tả sáu CV mẫu. Có thể chạy lại riêng bước đánh giá bằng `evaluate_jake.py --artifact-dir <model> --pdf-dir <thu_muc_pdf> --output <ket_qua.json>`.
