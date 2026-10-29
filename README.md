# CVAI

Ứng dụng CV/tuyển dụng với ASP.NET Core, React và Python AI service.

## Model v1: E5 + bộ phân loại

JD thô → tách yêu cầu, tự gán weight → E5 tìm đoạn CV → MLP phân loại
`met / partial / not_evidenced` → code tính điểm và nhận xét tiếng Việt.

| Thành phần | Vị trí |
|---|---|
| Code train/inference/API v1 | [training/lightweight_cv](training/lightweight_cv) |
| Notebook Colab | [train_e5_classifier.ipynb](training/lightweight_cv/train_e5_classifier.ipynb) |
| Dữ liệu tổng hợp và rubric | [training/datasets/cvai_v1](training/datasets/cvai_v1) |
| Trọng số classifier + manifest | [artifact](training/lightweight_cv/artifact) |
| Encoder đầy đủ để chạy offline | [GitHub Release](https://github.com/GSK7625/CVAI/releases/tag/cvai-e5-v1.0.0) |
| Đánh giá Colab | [evaluation/e5-v1](evaluation/e5-v1) |

## Chạy thử CPU

Dùng Python 3.10–3.12 và môi trường ảo riêng:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r training/lightweight_cv/requirements.txt
python training/lightweight_cv/fetch_model.py
python training/lightweight_cv/predict.py --artifact-dir training/lightweight_cv/artifact --input training/lightweight_cv/example_raw_input.json
```

`fetch_model.py` tải model từ Release, kiểm tra SHA-256 rồi bổ sung encoder
vào artifact. Classifier nhỏ được lưu trực tiếp trong Git; encoder lớn ở
Release để repository dễ clone. [Hướng dẫn chi tiết](training/lightweight_cv/README.md).

## Kết quả và giới hạn

150 cặp test tổng hợp, 600 yêu cầu: **macro-F1 0,7636**, accuracy theo yêu cầu
**82,17%**, MAE điểm phù hợp **13,27/100**. Chỉ 70/150 cặp đúng cả bốn nhãn.
Xem [phân tích lỗi](evaluation/e5-v1/README.md), không suy ra độ chính xác trên
CV/JD thật từ các số liệu này.

Module E5 chạy độc lập; các endpoint/giao diện hiện có chưa tự chuyển sang
model này. Không dùng điểm máy làm quyết định tuyển dụng tự động.

## Các ứng dụng hiện có

- [Backend ASP.NET Core](backend)
- [Python AI service hiện có](backend-ai/README.md)
- [Frontend](frontend/README.md)

Nguồn encoder và ghi nhận bên thứ ba: [THIRD_PARTY.md](training/lightweight_cv/THIRD_PARTY.md).
