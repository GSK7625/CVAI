# Thí nghiệm CVAI v1

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
